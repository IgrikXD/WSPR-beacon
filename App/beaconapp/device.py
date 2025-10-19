import asyncio
import json
import logging
import serial
import serial.tools.list_ports
import serial_asyncio
import socket
import sys
import threading
import websockets

from abc import ABC, abstractmethod
from colorama import Fore, Style
from beaconapp.data_wrappers import ActiveTXMode, CalibrationType, ConnectionStatus, WiFiCredentials, WiFiData
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)
# Add handler that writes logs to sys.stdout
logger.addHandler(logging.StreamHandler())
# Set logger level to DEBUG if `--debug` is present in the command line arguments, otherwise to CRITICAL
logger.setLevel(logging.DEBUG if ('--debug' in sys.argv) else logging.CRITICAL)


class Device:
    class AlreadyConnectedError(Exception):
        """
        Raised when attempting to connect a device that is already connected.
        """
        pass

    class Transport(Enum):
        USB = "USB"
        WIFI = "WiFi"

    @dataclass
    class Message:
        class Incoming(Enum):
            ACTIVE_TRANSPORT = "ACTIVE_TRANSPORT"
            ACTIVE_TX_MODE = "ACTIVE_TX_MODE"
            CAL_FREQ_GENERATED = "CAL_FREQ_GENERATED"
            CAL_STATUS = "CAL_STATUS"
            CAL_VALUE = "CAL_VALUE"
            FIRMWARE_INFO = "FIRMWARE_INFO"
            GPS_STATUS = "GPS_STATUS"
            HARDWARE_INFO = "HARDWARE_INFO"
            QTH_LOCATOR = "QTH_LOCATOR"
            SELF_CHECK_ACTION = "SELF_CHECK_ACTION"
            SELF_CHECK_ACTIVE = "SELF_CHECK_ACTIVE"
            SELF_CHECK_STATUS = "SELF_CHECK_STATUS"
            TX_ACTION_STATUS = "TX_ACTION_STATUS"
            TX_STATUS = "TX_STATUS"
            WIFI_SSID_DATA = "WIFI_SSID_DATA"
            WIFI_STATUS = "WIFI_STATUS"

        class Outgoing(Enum):
            GEN_CAL_FREQUENCY = "GEN_CAL_FREQUENCY"
            GET_DEVICE_INFO = "GET_DEVICE_INFO"
            RUN_SELF_CHECK = "RUN_SELF_CHECK"
            RUN_WIFI_CONNECTION = "RUN_WIFI_CONNECTION"
            SET_ACTIVE_TX_MODE = "SET_ACTIVE_TX_MODE"
            SET_CAL_METHOD = "SET_CAL_METHOD"
            SET_CAL_VALUE = "SET_CAL_VALUE"
            SET_SSID_CONNECT_AT_STARTUP = "SET_SSID_CONNECT_AT_STARTUP"

        type: Incoming | Outgoing
        data: Any = None

    """
    Calibration frequency multiplier used in the GEN_CAL_FREQUENCY message.
    Needed to avoid converting float -> uint64_t on the firmware side.
    """
    __CAL_FREQ_MULTIPLIER = 100_000_000

    def __init__(self):
        self.tx_queue = asyncio.Queue()
        self.asyncio_loop: Optional[asyncio.AbstractEventLoop] = None
        self.asyncio_thread: Optional[threading.Thread] = None
        # Stop flag to signal transports and loops to terminate
        self._stop_flag = False
        
        # Lock to prevent concurrent connect/disconnect calls
        self._connection_lock = threading.Lock()

        # Active transport, None until a transport actually connects
        self.active_transport: Optional[Device.Transport] = None
        # Transport priority (if we cannot satisfy _requested_transport)
        # WiFi: priority 0 (high)
        # USB (Serial): priority 1 (low)
        self.transport_priority = [Device.Transport.WIFI, Device.Transport.USB]
        # Current "requested" (from the device) transport (default to USB preference)
        self._requested_transport: Optional[Device.Transport] = Device.Transport.USB
        # Transports that are currently connected (USB (Serial)/WebSocket)
        self._connected_transports: Set[Device.Transport] = set()

        self.mapped_callbacks: Dict[Device.Message.Incoming, List[Callable]] = {}

        self.serial_transport = SerialTransport(self)
        self.ws_transport = WebsocketTransport(self)

    def connect(self):
        """
        Create a new event loop in a separate thread and run Serial and WebSocket connections in parallel.
        Thread-safe: uses lock to prevent concurrent connect/disconnect calls.
        
        Raises:
            Device.AlreadyConnectedError: If device is already connected.
        """
        with self._connection_lock:
            # Prevent connecting if already connected
            if self.asyncio_loop is not None and self.asyncio_loop.is_running():
                raise Device.AlreadyConnectedError("Device is already connected")
            
            self._stop_flag = False
            
            # Create new asyncio loop and queue for this connection
            self.asyncio_loop = asyncio.new_event_loop()
            self.tx_queue = asyncio.Queue()
            self.asyncio_loop.set_exception_handler(self._serial_exception_handler)
            
            # Event to ensure the loop is running before scheduling coroutines
            loop_started = threading.Event()
            
            def run_loop():
                asyncio.set_event_loop(self.asyncio_loop)
                self.asyncio_loop.call_soon(loop_started.set)
                self.asyncio_loop.run_forever()
            
            self.asyncio_thread = threading.Thread(target=run_loop, daemon=True)
            self.asyncio_thread.start()
            
            # Wait for the event loop to actually start
            loop_started.wait(timeout=5.0)

            # In parallel try to connect via serial and websocket
            asyncio.run_coroutine_threadsafe(self.serial_transport.connect(), self.asyncio_loop)
            asyncio.run_coroutine_threadsafe(self.ws_transport.connect(), self.asyncio_loop)
            
            # Start message handler (tracked via cancel_tasks in disconnect)
            asyncio.run_coroutine_threadsafe(self._handle_outgoing_messages(), self.asyncio_loop)

    def disconnect(self):
        """
        Properly closes all connections (Serial and WebSocket).
        Serial connections are closed without triggering DTR/RTS signals.
        Thread-safe: uses lock to prevent concurrent connect/disconnect calls.
        """
        with self._connection_lock:
            if not self.asyncio_loop:
                return
            
            self._stop_flag = True
            
            # Cancel all pending tasks to stop all operations
            if self.asyncio_loop.is_running():
                async def cancel_tasks():
                    tasks = [t for t in asyncio.all_tasks() 
                            if not t.done() and t != asyncio.current_task()]
                    for task in tasks:
                        task.cancel()
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
                try:
                    asyncio.run_coroutine_threadsafe(cancel_tasks(), self.asyncio_loop).result(timeout=0.3)
                except Exception:
                    pass
            
            # Close Serial transport and port (non-blocking)
            try:
                if self.serial_transport.transport:
                    self.serial_transport.transport.close()
                    self.serial_transport.transport = None
                if self.serial_transport.serial_port:
                    self.serial_transport.serial_port.timeout = 0
                    self.serial_transport.serial_port.write_timeout = 0
                    if self.serial_transport.serial_port.is_open:
                        self.serial_transport.serial_port.close()
                    self.serial_transport.serial_port = None
            except Exception:
                pass
            
            # Close WebSocket
            if self.asyncio_loop.is_running() and self.ws_transport.websocket:
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.ws_transport.close(), self.asyncio_loop).result(timeout=0.3)
                except Exception:
                    self.ws_transport.websocket = None
            
            # Stop event loop and wait briefly for thread
            if self.asyncio_loop.is_running():
                try:
                    self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
                except RuntimeError:
                    pass
            
            if self.asyncio_thread and self.asyncio_thread.is_alive():
                self.asyncio_thread.join(timeout=0.1)
            
            # Reset state
            self.active_transport = None
            self._connected_transports.clear()
            self.asyncio_loop = None
            self.asyncio_thread = None

    def set_device_response_handlers(self, mapped_callbacks: Dict[Message.Incoming, List[Callable]]):
        """
        Register one or more callbacks for given incoming message types.
        Prevent duplicate callbacks for the same message type.
        """
        for key, value in mapped_callbacks.items():
            if not isinstance(value, list):
                value = [value]

            # If there is no such key, initialize with an empty list
            self.mapped_callbacks.setdefault(key, [])

            # Add callbacks that are not yet in the list
            for handler in value:
                if handler not in self.mapped_callbacks[key]:
                    self.mapped_callbacks[key].append(handler)

    def gen_calibration_frequency(self, frequency: float | None):
        """
        Sends a request to generate a calibration frequency.
        """
        self._put(Device.Message(Device.Message.Outgoing.GEN_CAL_FREQUENCY,
                                 None if frequency is None else int(frequency * self.__CAL_FREQ_MULTIPLIER)))

    def get_device_info(self):
        """
        Requests device info.
        """
        self._put(Device.Message(Device.Message.Outgoing.GET_DEVICE_INFO))

    def run_self_check(self):
        """
        Sends a request to run a self-check procedure on the device.
        """
        self._put(Device.Message(Device.Message.Outgoing.RUN_SELF_CHECK))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        """
        Sends a request to set the active TX mode.
        """
        self._put(Device.Message(Device.Message.Outgoing.SET_ACTIVE_TX_MODE, active_tx_mode))

    def set_calibration_type(self, calibration_type: CalibrationType):
        """
        Sends a request to set the calibration type (auto, manual).
        """
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value: int):
        """
        Sends a request to set a calibration value (for manual calibration).
        """
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_VALUE, value))

    def set_ssid_connect_at_startup(self, value: bool):
        """
        Sends a request to set SSID connect on startup.
        """
        self._put(Device.Message(Device.Message.Outgoing.SET_SSID_CONNECT_AT_STARTUP, value))

    def set_wifi_connection(self, wifi_credentials: WiFiCredentials | None):
        """
        Sends a request to run WiFi connection with given credentials.
        """
        self._put(Device.Message(Device.Message.Outgoing.RUN_WIFI_CONNECTION, wifi_credentials))

    def _call_handlers(self, msg_type: Enum, data):
        """
        Calls all handlers associated with the given incoming message type.
        """
        for handler in self.mapped_callbacks.get(msg_type, []):
            handler(data)

    def _on_transport_connected(self, transport_type: Transport):
        """
        Called by a transport class (Serial/WebSocket) when a successful connection is established.
        """
        self._connected_transports.add(transport_type)
        self._decide_active_transport()

    def _on_transport_disconnected(self, transport_type: Transport):
        """
        Called by a transport class (Serial/WebSocket) when a connection is lost or closed.
        """
        if transport_type in self._connected_transports:
            self._connected_transports.remove(transport_type)

        # If USB is disconnected, assume we lose device power, thus remove WiFi as well
        if transport_type == Device.Transport.USB:
            if Device.Transport.WIFI in self._connected_transports:
                self._connected_transports.remove(Device.Transport.WIFI)

        self._decide_active_transport()

    def _decide_active_transport(self):
        """
        Chooses which transport should be active based on:
            1) _requested_transport (if it is actually connected)
            2) transport_priority (e.g., WiFi first, then USB)
            3) or None if no transport is currently available
        Notifies handlers if the active transport changes.
        """
        old_transport = self.active_transport

        # If the requested transport is connected, use it
        if self._requested_transport in self._connected_transports:
            self.active_transport = self._requested_transport
        else:
            # Otherwise, pick from transport_priority
            transport_to_activate = None
            for transport in self.transport_priority:
                if transport in self._connected_transports:
                    transport_to_activate = transport
                    break
            self.active_transport = transport_to_activate

        # If the active transport changed, notify via the INCOMING.ACTIVE_TRANSPORT event
        if self.active_transport != old_transport:
            self._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.active_transport)

    def _set_active_transport(self, transport: Transport):
        """
        Callback called on an incoming ACTIVE_TRANSPORT message from the device. This sets the
        "requested" transport, and triggers a decision pass.
        """
        self._requested_transport = transport
        self._decide_active_transport()

    def _decode_device_message(self, message: str):
        """
        Decodes a message from JSON into a Device.Message, including special handling for known
        data types (ActiveTXMode, WiFiData, etc.).
        """
        obj = json.loads(message)
        msg_type = Device.Message.Incoming(obj.get("type"))
        raw_data = obj.get("data")

        if msg_type == Device.Message.Incoming.ACTIVE_TX_MODE:
            data = ActiveTXMode.from_json(raw_data)
        elif msg_type == Device.Message.Incoming.ACTIVE_TRANSPORT:
            data = Device.Transport(raw_data)
            # Switch active transport on an incoming request from the device
            self._set_active_transport(data)
        elif msg_type == Device.Message.Incoming.WIFI_SSID_DATA:
            data = WiFiData.from_json(raw_data)
        elif msg_type == Device.Message.Incoming.WIFI_STATUS:
            data = ConnectionStatus(raw_data)
        else:
            data = raw_data

        return Device.Message(msg_type, data)

    def _encode_device_message(self, message: Message):
        """
        Encodes a Device.Message into a JSON string, converting enums and data objects appropriately.
        """
        if isinstance(message.data, (ActiveTXMode, WiFiCredentials)):
            data = message.data.to_json()
        elif isinstance(message.data, Enum):
            data = message.data.value
        else:
            data = message.data

        return json.dumps({
            "type": message.type.value,
            "data": data
        }) + "\n"

    async def _handle_outgoing_messages(self):
        """
        Continuously takes messages from tx_queue and sends them to the currently active transport.
        """
        while not self._stop_flag:
            try:
                # Use wait_for with timeout to allow checking stop flag
                message = await asyncio.wait_for(self.tx_queue.get(), timeout=1.0)
                self._send_to_device(message)
            except asyncio.TimeoutError:
                # Timeout is expected, just continue to check stop flag
                continue
            except Exception as e:
                logger.error(f"{Fore.RED}[ERROR] Outgoing message sending failed: {e}{Style.RESET_ALL}")

    def _put(self, message: Message):
        """
        Places a message into the tx_queue for asynchronous sending.
        """
        self.asyncio_loop.call_soon_threadsafe(self.tx_queue.put_nowait, message)

    def _send_to_device(self, message: Message):
        """
        Sends an encoded message to the currently active transport (USB or WiFi).
        """
        json_str = self._encode_device_message(message)
        if self.active_transport == Device.Transport.WIFI:
            self.ws_transport.send(json_str)
        elif self.active_transport == Device.Transport.USB:
            self.serial_transport.send(json_str)

    def _serial_exception_handler(self, loop: asyncio.AbstractEventLoop, context: dict):
        """
        Ignores the known Windows bug "ClearCommError failed" related to abrupt disconnections.
        Otherwise, uses the default exception handler.
        """
        if "ClearCommError failed" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)


class BaseTransport(ABC):
    """
    Abstract base class for different transport implementations (Serial, WebSocket, etc.).
    """
    def __init__(self, device: Device):
        self.device = device

    @abstractmethod
    async def connect(self):
        """
        Attempts to establish a connection with the device.
        """
        pass

    @abstractmethod
    def send(self, message: str):
        """
        Sends a message string via the transport.
        """
        pass


class SerialTransport(BaseTransport):
    """
    Serial (USB) transport implementation using serial_asyncio.

    Note: We use serial.Serial directly instead of only serial_asyncio because:
    1. serial_asyncio.create_serial_connection() opens the port immediately with default DTR/RTS
    2. We need to configure flow control (dsrdtr=False, rtscts=False) before opening
    3. We must set DTR/RTS to False immediately after open() to prevent device reset
    4. Therefore, we create Serial object manually, configure it, then use connection_for_serial()
    
    DTR/RTS handling:
    - Before open(): Configure dsrdtr=False, rtscts=False
    - After open(): Immediately set DTR=False, RTS=False
    - Before close(): DTR/RTS leave as False to prevent reset
    """
    def __init__(self, device: Device):
        super().__init__(device)
        self.transport: Optional[asyncio.Transport] = None
        # Store reference to the serial port object
        self.serial_port = None
        # VID and PID for ESP32-C3
        self.vid = 0x303A
        self.pid = 0x1001

    async def connect(self):
        """
        Continuously looks for a matching COM port (ESP32-C3 PID/VID),
        and tries to establish a Serial connection.
        """
        while not self.device._stop_flag:
            device_port = self._find_device_port()
            if device_port:
                await asyncio.sleep(1)

                # Create serial port object without opening it yet
                # This allows us to configure DTR/RTS before the port is opened
                self.serial_port = serial.Serial()
                self.serial_port.port = device_port
                self.serial_port.baudrate = 115200
                self.serial_port.timeout = 1
                self.serial_port.write_timeout = 1
                
                # Disable all flow control
                self.serial_port.dsrdtr = False
                self.serial_port.rtscts = False
                self.serial_port.xonxoff = False

                # Set DTR/RTS to False before opening the port
                # This is the only way to prevent device reset on connection
                self.serial_port.dtr = False
                self.serial_port.rts = False
                
                # Use exclusive access if supported
                try:
                    self.serial_port.exclusive = True
                except (AttributeError, ValueError):
                    pass  # Not supported

                self.serial_port.open()

                self.transport, _ = await serial_asyncio.connection_for_serial(
                    asyncio.get_running_loop(),
                    lambda: DeviceProtocol(self.device, self),
                    self.serial_port
                )
                break
            await asyncio.sleep(1)

    async def close(self):
        """
        Properly closes the serial connection without triggering DTR/RTS signals.
        """
        if self.transport:
            try:
                self.transport.close()
            except Exception as e:
                logger.debug(f"{Fore.RED}[ERROR] Closing serial transport: {e}{Style.RESET_ALL}")
            self.transport = None

        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception as e:
                logger.debug(f"{Fore.RED}[ERROR] Closing serial port: {e}{Style.RESET_ALL}")
            self.serial_port = None

    def send(self, message: str):
        """
        Sends message bytes via the established Serial connection.
        """
        if self.transport:
            logger.debug(f"{Fore.GREEN}TX (USB): {message.strip()}{Style.RESET_ALL}")
            self.transport.write(message.encode('utf-8'))

    def _find_device_port(self):
        """
        Searches for a connected device by matching VID/PID.
        """
        for port in serial.tools.list_ports.comports():
            if port.vid == self.vid and port.pid == self.pid:
                return port.device
        return None


class WebsocketTransport(BaseTransport):
    """
    WebSocket (WiFi) transport implementation using asyncio and websockets library.
    """
    def __init__(self, device: Device):
        super().__init__(device)
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.hostname = "wsprbeacon"
        self.port = 81

    async def connect(self):
        """
        Continuously tries to connect to the WebSocket.
        """
        while not self.device._stop_flag:
            try:
                self.websocket = await websockets.connect(f"ws://{self.hostname}:{self.port}")
                self.device._on_transport_connected(Device.Transport.WIFI)
                # Start the message receiver task
                asyncio.create_task(self._websocket_receiver())
                break
            except socket.gaierror:
                self.websocket = None
                await asyncio.sleep(1)

    async def close(self):
        """
        Properly closes the WebSocket connection.
        """
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"{Fore.RED}[ERROR] Closing WebSocket: {e}{Style.RESET_ALL}")
            self.websocket = None

    def send(self, message: str):
        """
        Sends a text message via the active WebSocket connection.
        """
        if self.websocket is not None:
            logger.debug(f"{Fore.GREEN}TX (WebSocket): {message.strip()}{Style.RESET_ALL}")
            asyncio.create_task(self.websocket.send(message))

    async def _websocket_receiver(self):
        """
        Continuously reads messages from the WebSocket until disconnected, decoding and
        handing them over to the device's _call_handlers. On disconnection, tries to reconnect.
        """
        try:
            # Immediately request device info upon successful connection
            self.device.get_device_info()
            async for message in self.websocket:
                message = message.strip()
                if message:
                    msg = self.device._decode_device_message(message)
                    logger.debug(f"{Fore.MAGENTA}RX (WebSocket): {message}{Style.RESET_ALL}")
                    self.device._call_handlers(msg.type, msg.data)
        except websockets.exceptions.ConnectionClosedError:
            self.websocket = None
            self.device._on_transport_disconnected(Device.Transport.WIFI)
            # Only try to reconnect if we're not shutting down
            if not self.device._stop_flag:
                asyncio.create_task(self.connect())


class DeviceProtocol(asyncio.Protocol):
    """
    Asyncio Protocol handling data for the SerialTransport.
    """
    def __init__(self, device: Device, serial_transport: SerialTransport):
        self.device = device
        self.serial_transport = serial_transport
        self.buffer = b""

    def connection_made(self, transport: asyncio.Transport):
        """
        Called when a serial connection is established.
        """
        self.serial_transport.transport = transport
        self.device._on_transport_connected(Device.Transport.USB)
        # Immediately request device info after successful connection
        self.device.get_device_info()

    def data_received(self, data: bytes):
        """
        Called whenever data is received via Serial. Accumulates data until a newline
        and then processes each line.
        """
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            message = line.decode('utf-8', errors='ignore').strip()
            if message:
                try:
                    msg = self.device._decode_device_message(message)
                    logger.debug(f"{Fore.MAGENTA}RX (USB): {message}{Style.RESET_ALL}")
                    self.device._call_handlers(msg.type, msg.data)
                except json.JSONDecodeError:
                    logger.debug(f"{Fore.YELLOW}[WARNING] Non-JSON data received: {message}{Style.RESET_ALL}")
                except Exception as e:
                    logger.error(f"{Fore.RED}[ERROR] Error decoding message: {e}{Style.RESET_ALL}")

    def connection_lost(self, exc):
        """
        Called when the serial connection is lost or closed. Attempts to reconnect.
        """
        self.serial_transport.transport = None
        self.device._on_transport_disconnected(Device.Transport.USB)
        # Only try to reconnect if we're not shutting down
        if not self.device._stop_flag:
            asyncio.create_task(self.serial_transport.connect())
