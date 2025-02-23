import asyncio
import json
import serial_asyncio
import serial.tools.list_ports
import socket
import threading
import websockets

from abc import ABC, abstractmethod
from beaconapp.data_wrappers import ActiveTXMode, CalibrationType, ConnectionStatus, WiFiCredentials, WiFiData
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class Device:
    class Transport(Enum):
        USB = "USB"
        WIFI = "Wi-Fi"

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

    def __init__(self):
        self.tx_queue = asyncio.Queue()

        # Active transport, USB (Serial) by default
        self.active_transport: Optional[Device.Transport] = Device.Transport.USB
        # Transport priority (if we cannot satisfy _requested_transport)
        # Wi-FI: priotity 0 (high)
        # USB (Serial): priotity 1 (low)
        self.transport_priority = [Device.Transport.WIFI, Device.Transport.USB]
        # Current "requested" (from the device) transport
        self._requested_transport: Optional[Device.Transport] = self.active_transport
        # Transports that are currently connected (USB (Serial)/WebSocket)
        self._connected_transports: Set[Device.Transport] = set()

        self.mapped_callbacks: Dict[Device.Message.Incoming, List[Callable]] = {}
        # By default, set callback to switch active transport on an incoming request from the device
        self.set_device_response_handlers({Device.Message.Incoming.ACTIVE_TRANSPORT: [self._set_active_transport]})

        self.serial_transport = SerialTransport(self)
        self.ws_transport = WebsocketTransport(self)

    def connect(self):
        asyncio_loop = asyncio.new_event_loop()
        asyncio_loop.set_exception_handler(self._serial_exception_handler)
        asyncio.set_event_loop(asyncio_loop)

        threading.Thread(target=lambda: asyncio_loop.run_forever(), daemon=True).start()

        # In parallel try to connect via serial and websocket
        asyncio.run_coroutine_threadsafe(self.serial_transport.connect(), asyncio_loop)
        asyncio.run_coroutine_threadsafe(self.ws_transport.connect(), asyncio_loop)
        asyncio.run_coroutine_threadsafe(self._handle_outgoing_messages(), asyncio_loop)

    def set_device_response_handlers(self, mapped_callbacks: Dict[Message.Incoming, List[Callable]]):
        for key, value in mapped_callbacks.items():
            if not isinstance(value, list):
                value = [value]

            # If there is no such key, initialize with an empty list
            self.mapped_callbacks.setdefault(key, [])

            # Adding colbacks that don't already exist
            for handler in value:
                if handler not in self.mapped_callbacks[key]:
                    self.mapped_callbacks[key].append(handler)

    def gen_calibration_frequency(self, frequency: float):
        self._put(Device.Message(Device.Message.Outgoing.GEN_CAL_FREQUENCY, frequency))

    def get_device_info(self):
        self._put(Device.Message(Device.Message.Outgoing.GET_DEVICE_INFO))

    def run_self_check(self):
        self._put(Device.Message(Device.Message.Outgoing.RUN_SELF_CHECK))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        self._put(Device.Message(Device.Message.Outgoing.SET_ACTIVE_TX_MODE, active_tx_mode))

    def set_calibration_type(self, calibration_type: CalibrationType):
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value: int):
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_VALUE, value))

    def set_ssid_connect_at_startup(self, value: bool):
        self._put(Device.Message(Device.Message.Outgoing.SET_SSID_CONNECT_AT_STARTUP, value))

    def set_wifi_connection(self, wifi_credentials: WiFiCredentials):
        self._put(Device.Message(Device.Message.Outgoing.RUN_WIFI_CONNECTION, wifi_credentials))

    def _call_handlers(self, msg_type: Enum, data):
        for handler in self.mapped_callbacks.get(msg_type, []):
            handler(data)

    def _on_transport_connected(self, transport_type: Transport):
        self._connected_transports.add(transport_type)
        self._decide_active_transport()

    def _on_transport_disconnected(self, transport_type: Transport):
        if transport_type in self._connected_transports:
            self._connected_transports.remove(transport_type)

        if transport_type == Device.Transport.USB:
            if Device.Transport.WIFI in self._connected_transports:
                self._connected_transports.remove(Device.Transport.WIFI)

        self._decide_active_transport()

    def _decide_active_transport(self):
        old_transport = self.active_transport

        if self._requested_transport in self._connected_transports:
            self.active_transport = self._requested_transport
        else:
            transport_to_activate = None
            for transport in self.transport_priority:
                if transport in self._connected_transports:
                    transport_to_activate = transport
                    break
            self.active_transport = transport_to_activate

        if self.active_transport != old_transport:
            self._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.active_transport)

    def _set_active_transport(self, transport: Transport):
        self._requested_transport = transport
        self._decide_active_transport()

    def _decode_device_message(self, message: str):
        obj = json.loads(message)
        msg_type = Device.Message.Incoming(obj.get("type"))
        raw_data = obj.get("data")

        if msg_type == Device.Message.Incoming.ACTIVE_TX_MODE:
            data = ActiveTXMode.from_json(raw_data)
        elif msg_type == Device.Message.Incoming.ACTIVE_TRANSPORT:
            data = Device.Transport(raw_data)
        elif msg_type == Device.Message.Incoming.WIFI_SSID_DATA:
            data = WiFiData.from_json(raw_data)
        elif msg_type == Device.Message.Incoming.WIFI_STATUS:
            data = ConnectionStatus(raw_data.get("status"))
        else:
            data = raw_data

        return Device.Message(msg_type, data)

    def _encode_device_message(self, message: Message):
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
        while True:
            message = await self.tx_queue.get()
            self._send_to_device(message)

    def _put(self, message: Message):
        self.tx_queue.put_nowait(message)

    def _send_to_device(self, message: Message):
        json_str = self._encode_device_message(message)
        if self.active_transport == Device.Transport.WIFI:
            self.ws_transport.send(json_str)
        elif self.active_transport == Device.Transport.USB:
            self.serial_transport.send(json_str)

    def _serial_exception_handler(self, loop: asyncio.AbstractEventLoop, context: dict):
        # Ignore “ClearCommError failed” - bug on Windows related to emergency device disconnection
        if "ClearCommError failed" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)


class BaseTransport(ABC):
    def __init__(self, device: Device):
        self.device = device

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    def send(self, message: str):
        pass


class SerialTransport(BaseTransport):
    def __init__(self, device: Device):
        super().__init__(device)
        self.transport: Optional[asyncio.Transport] = None

    async def connect(self):
        while True:
            device_port = self._find_device_port()
            if device_port:
                await asyncio.sleep(1)
                await serial_asyncio.create_serial_connection(
                    asyncio.get_running_loop(),
                    lambda: DeviceProtocol(self.device, self),
                    device_port,
                    baudrate=115200
                )
                break
            await asyncio.sleep(1)

    def send(self, message: str):
        if self.transport:
            print(f"TX (USB): {message.strip()}")
            self.transport.write(message.encode('utf-8'))

    def _find_device_port(self):
        for port in serial.tools.list_ports.comports():
            # VID and PID for ESP32-C3
            if port.vid == 0x303A and port.pid == 0x1001:
                return port.device
        return None


class WebsocketTransport(BaseTransport):
    def __init__(self, device: Device):
        super().__init__(device)
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        while True:
            try:
                self.websocket = await websockets.connect("ws://wsprbeacon:81")
                self.device._on_transport_connected(Device.Transport.WIFI)
                asyncio.create_task(self._websocket_receiver())
                break
            except socket.gaierror:
                self.websocket = None
                await asyncio.sleep(1)

    def send(self, message: str):
        if self.websocket is not None:
            print(f"TX (WebSocket): {message.strip()}")
            asyncio.create_task(self.websocket.send(message))

    async def _websocket_receiver(self):
        try:
            self.device.get_device_info()
            async for message in self.websocket:
                message = message.strip()
                if message:
                    msg = self.device._decode_device_message(message)
                    print(f"RX (WebSocket): {message}")
                    self.device._call_handlers(msg.type, msg.data)
        except websockets.exceptions.ConnectionClosedError:
            self.websocket = None
            self.device._on_transport_disconnected(Device.Transport.WIFI)
            asyncio.create_task(self.connect())


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device, serial_transport: SerialTransport):
        self.device = device
        self.serial_transport = serial_transport
        self.buffer = b""

    def connection_made(self, transport: asyncio.Transport):
        self.serial_transport.transport = transport
        self.device._on_transport_connected(Device.Transport.USB)
        self.device.get_device_info()

    def data_received(self, data: bytes):
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            message = line.decode('utf-8', errors='ignore').strip()
            if message:
                msg = self.device._decode_device_message(message)
                print(f"RX (USB): {message}")
                self.device._call_handlers(msg.type, msg.data)

    def connection_lost(self, exc):
        self.serial_transport.transport = None
        self.device._on_transport_disconnected(Device.Transport.USB)
        asyncio.create_task(self.serial_transport.connect())
