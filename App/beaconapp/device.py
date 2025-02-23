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
from typing import Any, Callable, Dict, List, Optional


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
        self.mapped_callbacks: Dict[Device.Message.Incoming, List[Callable]] = {}
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

    def set_device_response_handlers(self, mapped_callbacks):
        for key, value in mapped_callbacks.items():
            if not isinstance(value, list):
                value = [value]
            self.mapped_callbacks.setdefault(key, []).extend(value)

    def get_device_info(self):
        self._put(Device.Message(Device.Message.Outgoing.GET_DEVICE_INFO))

    def gen_calibration_frequency(self, frequency: float):
        self._put(Device.Message(Device.Message.Outgoing.GEN_CAL_FREQUENCY, frequency))

    def set_calibration_type(self, calibration_type: CalibrationType):
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value: int):
        self._put(Device.Message(Device.Message.Outgoing.SET_CAL_VALUE, value))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        self._put(Device.Message(Device.Message.Outgoing.SET_ACTIVE_TX_MODE, active_tx_mode))

    def run_self_check(self):
        self._put(Device.Message(Device.Message.Outgoing.RUN_SELF_CHECK))

    def set_ssid_connect_at_startup(self, value: bool):
        self._put(Device.Message(Device.Message.Outgoing.SET_SSID_CONNECT_AT_STARTUP, value))

    def set_wifi_connection(self, wifi_credentials: WiFiCredentials):
        self._put(Device.Message(Device.Message.Outgoing.RUN_WIFI_CONNECTION, wifi_credentials))

    def _call_handlers(self, msg_type: Enum, data):
        for handler in self.mapped_callbacks.get(msg_type, []):
            handler(data)

    def _set_active_transport(self, active_transport: Transport):
        if active_transport == Device.Transport.USB:
            self.active_transport = (Device.Transport.USB if self.serial_transport.transport else None)
        elif active_transport == Device.Transport.WIFI:
            if self.ws_transport.websocket:
                self.active_transport = Device.Transport.WIFI
            elif self.serial_transport.transport:
                self.active_transport = Device.Transport.USB
            else:
                self.active_transport = None
        else:
            self.active_transport = None

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
                self.device.active_transport = Device.Transport.WIFI
                self.device._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.device.active_transport)
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
            # If the web socket connection is terminated, switch to USB (if available)
            if self.device.serial_transport.transport:
                self.device.active_transport = Device.Transport.USB
            else:
                self.device.active_transport = None

            self.device._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.device.active_transport)
            asyncio.create_task(self.connect())


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device, serial_transport: SerialTransport):
        self.device = device
        self.serial_transport = serial_transport
        self.buffer = b""

    def connection_made(self, transport: asyncio.Transport):
        self.serial_transport.transport = transport
        self.device.active_transport = Device.Transport.USB
        self.device._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.device.active_transport)
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
        self.device.active_transport = None
        self.device._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.device.active_transport)
        asyncio.create_task(self.serial_transport.connect())
