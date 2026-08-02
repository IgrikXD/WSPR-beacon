import asyncio
import contextlib
import json
from typing import Optional

import serial
import serial.tools.list_ports
import serial_asyncio

from beaconapp.data_wrappers import Transport
from beaconapp.logger import log_error, log_rx_message, log_tx_message, log_warning
from beaconapp.transports.base_transport import BaseTransport


class SerialTransport(BaseTransport):
    """
    Serial (USB) transport implementation using serial_asyncio.

    Note: We use serial.Serial directly instead of only serial_asyncio because:
    1. serial_asyncio.create_serial_connection() opens the port immediately with default DTR/RTS
    2. We need to configure flow control (dsrdtr=False, rtscts=False, dtr=False, rts=False) before opening
       to prevent device reset on connection.

    Therefore, we create Serial object manually, configure it, then use connection_for_serial() for
    establishing the connection.

    DTR/RTS handling:
    1. Before open(): Configure dsrdtr=False, rtscts=False, dtr=False, rts=False
    3. Before close(): DTR/RTS leave as False to prevent reset
    """
    def __init__(self, device, vid: int, pid: int, baudrate: int):
        super().__init__(device)
        self._transport: Optional[asyncio.Transport] = None
        # Store reference to the serial port object
        self._serial_port = None
        # VID and PID for ESP32-C3
        self._vid = vid
        self._pid = pid
        # Baudrate for serial communication
        self._baudrate = baudrate

    async def connect(self):
        """
        Continuously looks for a matching COM port (ESP32-C3 PID/VID),
        and tries to establish a Serial connection.
        """
        try:
            while not self._device.is_stop_flag_set():
                device_port = self._find_device_port()
                if device_port:
                    # Create serial port object without opening it yet
                    # This allows us to configure DTR/RTS before the port is opened
                    self._serial_port = serial.Serial()

                    # Configure serial port parameters
                    self._serial_port.port = device_port
                    self._serial_port.baudrate = self._baudrate
                    self._serial_port.timeout = 1
                    self._serial_port.write_timeout = 1
                    # Disable all flow control
                    self._serial_port.dsrdtr = False
                    self._serial_port.rtscts = False
                    self._serial_port.xonxoff = False
                    # Set DTR/RTS to False before opening the port
                    # This is the only way to prevent device reset on connection
                    self._serial_port.dtr = False
                    self._serial_port.rts = False
                    # Use exclusive access if supported
                    with contextlib.suppress(AttributeError, ValueError):
                        self._serial_port.exclusive = True

                    self._serial_port.open()
                    self._transport, _ = await serial_asyncio.connection_for_serial(
                        asyncio.get_running_loop(),
                        lambda: DeviceProtocol(self._device, self),
                        self._serial_port
                    )
                    break
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            # Expected behavior on task cancellation, exit gracefully
            return

    def disconnect(self):
        """
        Properly closes the serial connection without triggering DTR/RTS signals.
        """
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception as e:
                log_error(f"Closing serial transport: {e}")
            self._transport = None

        if self._serial_port is not None and self._serial_port.is_open:
            try:
                self._serial_port.timeout = 0
                self._serial_port.write_timeout = 0
                self._serial_port.close()
            except Exception as e:
                log_error(f"Closing serial port: {e}")
            self._serial_port = None

    def get_port(self):
        """
        Returns the current serial port name, or None if not connected.
        """
        if self._serial_port is not None:
            return self._serial_port.port
        return None

    def send(self, message: str):
        """
        Sends message bytes via the established Serial connection.
        """
        if self._transport:
            log_tx_message(message.strip(), Transport.USB)
            self._transport.write(message.encode('utf-8'))

    def set_transport(self, transport: asyncio.Transport):
        """
        Sets the internal transport reference (used by DeviceProtocol on connection_made).
        """
        self._transport = transport

    def _find_device_port(self):
        """
        Searches for a connected device by matching VID/PID.
        """
        for port in serial.tools.list_ports.comports():
            if port.vid == self._vid and port.pid == self._pid:
                return port.device
        return None


class DeviceProtocol(asyncio.Protocol):
    """
    Asyncio Protocol handling data for the SerialTransport.
    """
    def __init__(self, device, serial_transport: SerialTransport):
        self._device = device
        self._serial_transport = serial_transport
        self._buffer = b""

    def connection_lost(self, exc):
        """
        Called when the serial connection is lost or closed. Attempts to reconnect.
        """
        self._serial_transport.set_transport(None)
        self._device.on_transport_disconnected(Transport.USB)
        # Only try to reconnect if we're not shutting down
        if not self._device.is_stop_flag_set():
            asyncio.create_task(self._serial_transport.connect())

    def connection_made(self, transport: asyncio.Transport):
        """
        Called when a serial connection is established.
        """
        self._serial_transport.set_transport(transport)
        self._device.on_transport_connected(Transport.USB)
        # Immediately request device info after successful connection
        self._device.get_device_info()

    def data_received(self, data: bytes):
        """
        Called whenever data is received via Serial. Accumulates data until a newline
        and then processes each line.
        """
        self._buffer += data
        while b'\n' in self._buffer:
            line, self._buffer = self._buffer.split(b'\n', 1)
            message = line.decode('utf-8', errors='ignore').strip()
            if message:
                try:
                    log_rx_message(message, Transport.USB)
                    self._device.decode_and_handle_message(message)

                except json.JSONDecodeError:
                    log_warning(f"Non-JSON data received: {message}")
                except Exception as e:
                    log_error(f"Error decoding message: {e}")
