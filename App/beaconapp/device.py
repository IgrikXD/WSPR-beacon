from contextlib import contextmanager, nullcontext, redirect_stdout, redirect_stderr
from beaconapp.data_wrappers import ActiveTXMode, Status, Transport, WiFiCredentials, WiFiData
from beaconapp.logger import is_debug_mode, log_ok, log_error
from beaconapp.transports.serial_transport import SerialTransport
from beaconapp.transports.websocket_transport import WebsocketTransport
from dataclasses import dataclass
from enum import Enum
from esptool import detect_chip, attach_flash, erase_region, reset_chip, write_flash
from packaging.version import Version
from typing import Any, Callable, Dict, List, Optional, Set

import asyncio
import hashlib
import json
import os
import requests
import threading


class Device:
    class AlreadyConnectedError(Exception):
        """
        Raised when attempting to connect a device that is already connected.
        """
        pass

    class DataSendingError(Exception):
        """
        Raised when attempting to send data but no active transport is available.
        """
        pass

    class FirmwareUpdateError(Exception):
        """
        Raised when firmware update fails (download, checksum, or flash error).
        """
        pass

    @dataclass
    class Message:
        class Incoming(Enum):
            ACTIVE_TRANSPORT = "ACTIVE_TRANSPORT"
            ACTIVE_TX_MODE = "ACTIVE_TX_MODE"
            CAL_FREQ_GENERATED = "CAL_FREQ_GENERATED"
            CAL_STATUS = "CAL_STATUS"
            CAL_VALUE = "CAL_VALUE"
            FIRMWARE_INFO = "FIRMWARE_INFO"
            FIRMWARE_STATUS = "FIRMWARE_STATUS"
            GPS_STATUS = "GPS_STATUS"
            GPS_CAL_STATUS = "GPS_CAL_STATUS"
            HARDWARE_INFO = "HARDWARE_INFO"
            QTH_LOCATOR = "QTH_LOCATOR"
            PROTOCOL_ERROR = "PROTOCOL_ERROR"
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
            RUN_FIRMWARE_UPDATE = "RUN_FIRMWARE_UPDATE"
            RUN_GPS_CALIBRATION = "RUN_GPS_CALIBRATION"
            RUN_SELF_CHECK = "RUN_SELF_CHECK"
            RUN_WIFI_CONNECTION = "RUN_WIFI_CONNECTION"
            SET_ACTIVE_TX_MODE = "SET_ACTIVE_TX_MODE"
            SET_CAL_VALUE = "SET_CAL_VALUE"
            SET_SSID_CONNECT_AT_STARTUP = "SET_SSID_CONNECT_AT_STARTUP"

        type: Incoming | Outgoing
        data: Any = None

    """
    Calibration frequency multiplier used in the GEN_CAL_FREQUENCY message.
    Needed to avoid converting float -> uint64_t on the firmware side.
    """
    __CAL_FREQ_MULTIPLIER = 100_000_000

    """
    Default baudrate for Serial (USB) communication with the device.
    """
    __DEVICE_BAUDRATE = 115200

    """
    USB Vendor ID for ESP32-C3.
    """
    __DEVICE_VID = 0x303A
    """
    USB Product ID for ESP32-C3.
    """
    __DEVICE_PID = 0x1001

    """
    URL to fetch the latest firmware manifest for updates.
    """
    __FIRMWARE_MANIFEST_URL = (
        "https://raw.githubusercontent.com/IgrikXD/WSPR-beacon/master/Firmware/"
        "ESP32C3-based/latest-stable.json"
    )

    """
    Flash memory address where the firmware should be written during update.
    """
    __FLASH_ADDR = 0x10000

    """
    Flash memory address of the otadata partition.
    Used to reset boot partition selection before firmware update.
    """
    __OTADATA_ADDR = 0xE000

    """
    Size of the otadata partition in bytes.
    """
    __OTADATA_SIZE = 0x2000

    """
    Multicast DNS name for the device when connected via Wi-Fi.
    """
    __MULTICAST_DNS_NAME = "wsprbeacon.local"

    """
    TCP port for WebSocket connection over Wi-Fi.
    """
    __TCP_PORT = 81

    """
    Maximum number of outgoing messages that can be queued.
    Prevents memory overflow if messages are sent faster than they can be transmitted.
    """
    __TX_QUEUE_MAX_SIZE = 20

    def __init__(self):
        # Queue for outgoing messages transmission to the device
        self._tx_queue: Optional[asyncio.Queue] = None

        # Event loop for running asynchronous tasks (Serial/WebSocket connections, message handling)
        self._asyncio_loop: Optional[asyncio.AbstractEventLoop] = None
        # Thread for running the event loop
        self._asyncio_thread: Optional[threading.Thread] = None

        # Stop flag to signal transports and loops to terminate
        self._stop_flag = False
        # Lock to prevent concurrent connect/disconnect calls
        self._connection_lock = threading.Lock()
        # Tracked asyncio tasks for proper cancellation on disconnect
        self._tasks_tracker: Set[asyncio.Task] = set()

        # Active transport, None until a transport actually connects
        self._active_transport: Optional[Transport] = None
        # Transport priority (if we cannot satisfy _requested_transport)
        # Wi-Fi: priority 0 (high)
        # USB (Serial): priority 1 (low)
        self._transport_priority = [Transport.WIFI, Transport.USB]
        # Current "requested" (from the device) transport (default to USB preference)
        self._requested_transport: Optional[Transport] = Transport.USB
        # Transports that are currently connected (USB (Serial)/WebSocket)
        self._connected_transports: Set[Transport] = set()

        # Mapping of incoming message types to lists of registered callback handlers
        self._mapped_callbacks: Dict[Device.Message.Incoming, List[Callable]] = {}

        # Initialize transport implementations
        self._serial_transport = SerialTransport(self, self.__DEVICE_VID, self.__DEVICE_PID, self.__DEVICE_BAUDRATE)
        self._ws_transport = WebsocketTransport(self, self.__MULTICAST_DNS_NAME, self.__TCP_PORT)

        # Current firmware version reported by the device
        # Used as a reference during firmware update checks
        self._firmware_version = None

    def connect(self):
        """
        Create a new event loop in a separate thread and run connection handle tasks.
        Thread-safe: uses lock to prevent concurrent connect/disconnect calls.

        Raises:
            Device.AlreadyConnectedError: If device is already connected.
        """
        with self._connection_lock:
            # Prevent connecting if already connected
            if self._asyncio_loop is not None and self._asyncio_loop.is_running():
                raise Device.AlreadyConnectedError("Device is already connected")

            # Reset stop flag used to signal transports and loops to terminate
            self._stop_flag = False

            # Create new asyncio loop and queue for this connection
            self._asyncio_loop = asyncio.new_event_loop()
            self._asyncio_loop.set_exception_handler(self._serial_exception_handler)
            self._tx_queue = asyncio.Queue(maxsize=self.__TX_QUEUE_MAX_SIZE)

            # Event to ensure the loop is running before scheduling coroutines
            loop_started = threading.Event()

            def run_asyncio_loop():
                """
                Run the asyncio event loop.
                """
                asyncio.set_event_loop(self._asyncio_loop)
                self._asyncio_loop.call_soon(loop_started.set)
                self._asyncio_loop.run_forever()

            # Start the event loop in a separate daemon thread
            self._asyncio_thread = threading.Thread(target=run_asyncio_loop, daemon=True)
            self._asyncio_thread.start()

            # Wait for the event loop to actually start
            loop_started.wait(timeout=5.0)

            # Create and track tasks in the event loop thread
            asyncio.run_coroutine_threadsafe(self._start_connection_handle_tasks(), self._asyncio_loop)

    def disconnect(self):
        """
        Properly closes all connections (Serial and WebSocket).
        Thread-safe: uses lock to prevent concurrent connect/disconnect calls.
        """
        with self._connection_lock:
            if not self._asyncio_loop:
                return

            # Update stop flag to break all infinite loops
            self._stop_flag = True

            # Cancel all running tasks - this will trigger CancelledError in infinite loops,
            # which will then do graceful close in its exception handler.
            # WebSocket connection will be closed gracefully in its own task
            if self._asyncio_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._stop_connection_handle_tasks(), self._asyncio_loop).result(timeout=10.0)

            # Synchronously close Serial transport
            self._serial_transport.disconnect()

            # Clear connected transports and active transport
            self._connected_transports.clear()
            self._active_transport = None

            # Stop event loop and wait briefly for thread to finish
            self._asyncio_loop.call_soon_threadsafe(self._asyncio_loop.stop)
            self._asyncio_loop = None

            # Wait for asyncio thread to finish
            if self._asyncio_thread is not None and self._asyncio_thread.is_alive():
                self._asyncio_thread.join(timeout=0.1)
                self._asyncio_thread = None

    def decode_and_handle_message(self, message: str) -> bool:
        """
        Decodes a message from the device and calls registered handlers.
        Args:
            message (str): The raw message string received from the device.
        Returns:
            bool: True if the message was successfully decoded and handled, False otherwise.
        """
        msg = self._decode_device_message(message)
        if msg:
            self._call_handlers(msg.type, msg.data)
            return True
        return False

    def is_stop_flag_set(self) -> bool:
        """
        Returns the current value of the stop flag.

        Returns:
            bool: The current value of the stop flag.
        """
        return self._stop_flag

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

    def on_transport_connected(self, transport_type: Transport):
        """
        Called by a transport class (Serial/WebSocket) when a successful connection is established.
        """
        self._connected_transports.add(transport_type)
        self._decide_active_transport()

    def on_transport_disconnected(self, transport_type: Transport):
        """
        Called by a transport class (Serial/WebSocket) when a connection is lost or closed.
        If USB is disconnected, we assume the device has lost power, so we also drop the Wi-Fi
        connection. When connected to a PC via USB, both USB and Wi-Fi are available. When
        powered externally (e.g., via power bank), USB (Serial) is not physically present,
        and only Wi-Fi is available. Removing Wi-Fi on USB disconnect reflects the
        expected hardware behavior.
        """
        if transport_type in self._connected_transports:
            self._connected_transports.remove(transport_type)

        # If USB is disconnected, we assume the device has lost power, and remove Wi-Fi as well
        if transport_type == Transport.USB:
            if Transport.WIFI in self._connected_transports:
                self._connected_transports.remove(Transport.WIFI)

        self._decide_active_transport()

    def run_firmware_update(self):
        """
        Used for updating the device firmware.
        Chooses between USB (Serial) or OTA (Wi-Fi) update based on the active transport.
        """
        if self._active_transport == Transport.USB:
            log_ok("USB firmware update started!")
            # Runs in a separate thread to avoid blocking the GUI
            threading.Thread(target=self._run_usb_firmware_update, daemon=True).start()
        elif self._active_transport == Transport.WIFI:
            log_ok("OTA firmware update started!")
            self._run_ota_firmware_update()
        else:
            self._call_handlers(Device.Message.Incoming.FIRMWARE_STATUS, Status.FAILED)
            log_error("No active transport! Device is disconnected?")

    def run_gps_calibration(self):
        """
        Sends a request to run GPS-based calibration procedure.
        """
        self._put(Device.Message(Device.Message.Outgoing.RUN_GPS_CALIBRATION))

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

    def set_calibration_value(self, value: int):
        """
        Sends a request to set a calibration value (for manual calibration).
        """
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_VALUE, value))

    def set_device_response_handlers(self, mapped_callbacks: Dict[Message.Incoming, List[Callable]]):
        """
        Register one or more callbacks for given incoming message types.
        Prevent duplicate callbacks for the same message type.
        """
        for key, value in mapped_callbacks.items():
            if not isinstance(value, list):
                value = [value]

            # If there is no such key, initialize with an empty list
            self._mapped_callbacks.setdefault(key, [])

            # Add callbacks that are not yet in the list
            for handler in value:
                if handler not in self._mapped_callbacks[key]:
                    self._mapped_callbacks[key].append(handler)

    def set_ssid_connect_at_startup(self, value: bool):
        """
        Sends a request to set SSID connect on startup.
        """
        self._put(Device.Message(Device.Message.Outgoing.SET_SSID_CONNECT_AT_STARTUP, value))

    def set_wifi_connection(self, wifi_credentials: WiFiCredentials | None):
        """
        Sends a request to run Wi-Fi connection with given credentials.
        """
        self._put(Device.Message(Device.Message.Outgoing.RUN_WIFI_CONNECTION, wifi_credentials))

    def update_firmware_info(self, firmware_version: str):
        """
        Update the stored firmware version information.

        Args:
            firmware_version: Firmware version string reported by the device.
        """
        self._firmware_version = firmware_version

    def _call_handlers(self, msg_type: Enum, data):
        """
        Calls all handlers associated with the given incoming message type.
        If a handler raises an exception, it is logged but does not prevent other handlers from running.
        """
        for handler in self._mapped_callbacks.get(msg_type, []):
            try:
                handler(data)
            except Exception as e:
                log_error(f"Message type \"{msg_type}\" processing failed: {e}")

    async def _start_connection_handle_tasks(self):
        """
        Create and track all connection related tasks (Serial, WebSocket, outgoing message handler).
        """
        # Create tasks and add them to tracking set
        self._tasks_tracker.add(asyncio.create_task(self._serial_transport.connect()))
        self._tasks_tracker.add(asyncio.create_task(self._ws_transport.connect()))
        self._tasks_tracker.add(asyncio.create_task(self._handle_outgoing_messages()))

    async def _stop_connection_handle_tasks(self):
        """
        Destroy all connection related tasks that were created and tracked.
        """
        # Filter out completed and current task
        current_task = asyncio.current_task()
        tasks_to_cancel = [
            task for task in self._tasks_tracker
            if not task.done() and task != current_task
        ]

        if not tasks_to_cancel:
            return

        # Cancel tasks
        for task in tasks_to_cancel:
            task.cancel()

        # Wait for tasks to acknowledge cancellation
        await asyncio.wait(tasks_to_cancel, timeout=5.0)

        # Clear the tasks tracker
        self._tasks_tracker.clear()

    def _decide_active_transport(self):
        """
        Chooses which transport should be active based on:
            1. _requested_transport (if it is actually connected)
            2. _transport_priority (e.g., Wi-Fi first, then USB)
            3. or None if no transport is currently available
        Notifies handlers if the active transport changes.
        """
        old_transport = self._active_transport

        # If the requested transport is connected, use it
        if self._requested_transport in self._connected_transports:
            self._active_transport = self._requested_transport
        else:
            # Otherwise, pick from _transport_priority
            transport_to_activate = None
            for transport in self._transport_priority:
                if transport in self._connected_transports:
                    transport_to_activate = transport
                    break
            self._active_transport = transport_to_activate

        # If the active transport changed, notify via the INCOMING.ACTIVE_TRANSPORT event
        if self._active_transport != old_transport:
            self._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self._active_transport)

    def _decode_device_message(self, message: str):
        """
        Decodes a message from JSON into a Device.Message, including special handling for known
        data types (ActiveTXMode, WiFiData, etc.).
        Returns None if message type is unknown.
        """
        obj = json.loads(message)
        msg_type_str = obj.get("type")

        try:
            msg_type = Device.Message.Incoming(msg_type_str)
        except ValueError:
            log_error(f"Unknown message type received: {msg_type_str}")
            return None

        raw_data = obj.get("data")

        if msg_type == Device.Message.Incoming.ACTIVE_TX_MODE:
            data = ActiveTXMode.from_json(raw_data)
        elif msg_type == Device.Message.Incoming.ACTIVE_TRANSPORT:
            data = Transport(raw_data)
            # Switch active transport on an incoming request from the device
            self._set_active_transport(data)
        elif msg_type == Device.Message.Incoming.WIFI_SSID_DATA:
            data = WiFiData.from_json(raw_data)
        elif msg_type in (
                Device.Message.Incoming.FIRMWARE_STATUS,
                Device.Message.Incoming.GPS_CAL_STATUS,
                Device.Message.Incoming.WIFI_STATUS):
            data = Status(raw_data)
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
        Continuously takes messages from _tx_queue and sends them to the currently active transport.
        """
        while not self._stop_flag:
            try:
                message = await asyncio.wait_for(self._tx_queue.get(), timeout=1.0)
                self._send_to_device(message)

            except asyncio.TimeoutError:
                # Timeout is expected behaviour, just continue to check stop flag
                continue

            except asyncio.CancelledError:
                # Expected behavior on task cancellation, exit gracefully
                return

            except Exception as e:
                log_error(f"Outgoing message sending failed: {e}")

    def _put(self, message: Message):
        """
        Places a message into the _tx_queue for asynchronous sending.
        If the queue is full, the message is discarded and an error is logged.
        If the device is not connected, the message is discarded and an error is logged.
        """
        if self._asyncio_loop is None:
            log_error(f"Cannot send message {message.type}: device is not connected or initialized!")
            return

        def try_put():
            """
            Wrapper that handles QueueFull exception in the event loop thread.
            """
            try:
                self._tx_queue.put_nowait(message)
            except asyncio.QueueFull:
                log_error(
                    f"TX queue is full ({self.__TX_QUEUE_MAX_SIZE} messages), "
                    f"message discarded: {message.type}"
                )

        self._asyncio_loop.call_soon_threadsafe(try_put)

    def _run_ota_firmware_update(self):
        """
        Sends a request to run OTA firmware update procedure.
        """
        self._put(Device.Message(Device.Message.Outgoing.RUN_FIRMWARE_UPDATE))

    def _run_usb_firmware_update(self):
        """
        Used for updating the device firmware over Serial (USB).
        Performs the following steps:
            - Checks if the active transport is USB (Serial);
            - Downloads the latest firmware manifest;
            - Compares current firmware version with available version;
            - If newer version available: downloads, verifies and flashes firmware;
            - Re-establishes device connection.
        """
        try:
            # Get the current serial port from the SerialTransport
            # After disconnect(), the port will be released and used for firmware flashing
            port = self._serial_transport.get_port()

            # Download latest firmware manifest first to check version
            manifest_response = requests.get(self.__FIRMWARE_MANIFEST_URL, timeout=30)
            manifest_response.raise_for_status()
            manifest = manifest_response.json()

            # Check if firmware update is needed
            available_version = manifest.get("firmware-version")
            if not available_version:
                raise Device.FirmwareUpdateError("Invalid firmware manifest: missing 'firmware-version' key")

            if self._firmware_version is not None and Version(self._firmware_version) >= Version(available_version):
                log_ok("Firmware is already up to date!")
                self._call_handlers(Device.Message.Incoming.FIRMWARE_STATUS, Status.LATEST)
                return  # No update needed

            # Get ota_0 partition data (used for USB firmware updates)
            ota_0 = manifest.get("ota_0")
            if not ota_0 or "url" not in ota_0 or "sha256" not in ota_0:
                raise Device.FirmwareUpdateError("Invalid firmware manifest: missing 'ota_0' partition data")

            # Terminate active device connections for releasing the serial port
            self.disconnect()

            # Download firmware binary data
            firmware_response = requests.get(ota_0["url"], timeout=120)
            firmware_response.raise_for_status()
            firmware_data = firmware_response.content

            # Verify SHA256 checksum
            actual_sha256 = hashlib.sha256(firmware_data).hexdigest()
            expected_sha256 = ota_0["sha256"]
            if actual_sha256.lower() != expected_sha256.lower():
                raise Device.FirmwareUpdateError(
                    f"Firmware checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
                )

            # Notify firmware update started
            self._call_handlers(Device.Message.Incoming.FIRMWARE_STATUS, Status.UPDATING)
            log_ok("Firmware flashing started")

            # Flash firmware to the device (suppressing esptool output unless in debug mode)
            with nullcontext() if is_debug_mode() else self._suppress_output():
                with detect_chip(port) as esp:
                    attach_flash(esp)
                    # Erase otadata partition to reset boot partition selection
                    # Use "force" flag required according to enabled Flash Encryption & Secure Boot
                    erase_region(esp, self.__OTADATA_ADDR, self.__OTADATA_SIZE, force=True)
                    # Write firmware binary directly from memory (bytes)
                    # Use "force" flag required according to enabled Flash Encryption & Secure Boot
                    write_flash(esp, [(self.__FLASH_ADDR, firmware_data)], force=True)
                    reset_chip(esp, "hard-reset")

            # Notify firmware update completed
            self._call_handlers(Device.Message.Incoming.FIRMWARE_STATUS, Status.UPDATED)
            log_ok("Firmware update completed successfully!")

            # Re-establish device connections
            self.connect()

        except (Device.FirmwareUpdateError, requests.RequestException, json.JSONDecodeError, Exception) as e:
            self._call_handlers(Device.Message.Incoming.FIRMWARE_STATUS, Status.FAILED)
            log_error(f"Unexpected error during firmware update: {e}")

    def _send_to_device(self, message: Message):
        """
        Sends an encoded message to the currently active transport (USB or Wi-Fi).

        Raises:
            Device.DataSendingError: If no active transport is available or transport type is unknown.
        """
        json_str = self._encode_device_message(message)
        if self._active_transport == Transport.WIFI:
            self._ws_transport.send(json_str)
        elif self._active_transport == Transport.USB:
            self._serial_transport.send(json_str)
        else:
            raise Device.DataSendingError(f"No active transport available to send message: {message.type}")

    def _serial_exception_handler(self, loop: asyncio.AbstractEventLoop, context: dict):
        """
        Ignores the known Windows bug "ClearCommError failed" related to abrupt disconnections.
        Otherwise, uses the default exception handler.
        """
        if "ClearCommError failed" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)

    def _set_active_transport(self, transport: Transport):
        """
        Callback called on an incoming ACTIVE_TRANSPORT message from the device. This sets the
        "requested" transport, and triggers a decision pass.
        """
        self._requested_transport = transport
        self._decide_active_transport()

    @staticmethod
    @contextmanager
    def _suppress_output():
        """
        Suppress stdout and stderr output. Used to suppress output from esptool library methods.
        """
        with open(os.devnull, "w") as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                yield
