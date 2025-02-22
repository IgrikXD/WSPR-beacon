import asyncio
import json
import serial_asyncio
import serial.tools.list_ports
import socket
import threading
import websockets

from beaconapp.data_wrappers import ConnectionStatus, WiFiCredentials, WiFiData, ActiveTXMode
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Device:
    class CalibrationType(Enum):
        AUTO = "auto"
        MANUAL = "manual"

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
        # Serial transport (USB)
        self.serial: asyncio.Transport = None
        # WebSocket transport (Wi-Fi)
        self.websocket: websockets = None
        # Active transport, USB by default
        self.active_transport = Device.Transport.USB
        self.mapped_callbacks = {}

    def connect(self):
        asyncio_loop = asyncio.new_event_loop()
        asyncio_loop.set_exception_handler(self._serial_exception_handler)
        asyncio.set_event_loop(asyncio_loop)

        threading.Thread(target=lambda: asyncio_loop.run_forever(), daemon=True).start()

        asyncio.run_coroutine_threadsafe(self._establish_serial_connection(), asyncio_loop)
        asyncio.run_coroutine_threadsafe(self._establish_websocket_connection(), asyncio_loop)
        asyncio.run_coroutine_threadsafe(self._handle_outgoing_messages(), asyncio_loop)

    def set_device_response_handlers(self, mapped_callbacks):
        self.mapped_callbacks = {
            key: (value if isinstance(value, list) else [value])
            for key, value in mapped_callbacks.items()
        }

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

    def _data_decoder(self, line_str: str):
        obj = json.loads(line_str)

        msg_type = Device.Message.Incoming(obj.get("type"))

        return Device.Message(msg_type, self._decode_data(msg_type, obj.get("data")))

    def _decode_data(self, msg_type: Message.Incoming, raw_data):
        if msg_type == Device.Message.Incoming.ACTIVE_TX_MODE:
            return ActiveTXMode.from_json(raw_data)

        if msg_type == Device.Message.Incoming.ACTIVE_TRANSPORT:
            if raw_data == Device.Transport.USB.value and self.serial:
                self.active_transport = Device.Transport.USB
            elif raw_data == Device.Transport.WIFI.value and self.websocket:
                self.active_transport = Device.Transport.WIFI
            elif raw_data == Device.Transport.WIFI.value and self.websocket is None and self.serial:
                self.active_transport = Device.Transport.USB
            else:
                self.active_transport = None
            return self.active_transport

        if msg_type == Device.Message.Incoming.WIFI_SSID_DATA:
            return WiFiData.from_json(raw_data)

        if msg_type == Device.Message.Incoming.WIFI_STATUS:
            return ConnectionStatus(raw_data.get("status"))

        return raw_data

    def _encode_data(self, data):
        if isinstance(data, (ActiveTXMode, WiFiCredentials)):
            return data.to_json()

        return data.value if isinstance(data, Enum) else data

    def _encode_device_message(self, message: Message):
        return json.dumps({
            "type": message.type.value,
            "data": self._encode_data(message.data)
        }) + "\n"

    async def _establish_serial_connection(self):
        while True:
            device_port = self._find_device_port()
            if device_port:
                await asyncio.sleep(0.5)
                await serial_asyncio.create_serial_connection(
                    asyncio.get_running_loop(),
                    lambda: DeviceProtocol(self),
                    device_port,
                    baudrate=115200
                )
                break
            await asyncio.sleep(0.5)

    def _find_device_port(self):
        for port in serial.tools.list_ports.comports():
            # VID and PID for ESP32-C3
            if port.vid == 0x303A and port.pid == 0x1001:
                return port.device
        return None

    async def _establish_websocket_connection(self):
        while True:
            try:
                self.websocket = await websockets.connect("ws://esp32-device:81")
                self.active_transport = Device.Transport.WIFI
                self._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.active_transport)
                asyncio.create_task(self._websocket_receiver())
                break
            except socket.gaierror:
                self.websocket = None
                await asyncio.sleep(0.5)

    async def _websocket_receiver(self):
        try:
            self.get_device_info()
            async for message in self.websocket:
                message = message.strip()
                if message:
                    msg = self._data_decoder(message)
                    print(f"RX (WebSocket): {message}")
                    self._call_handlers(msg.type, msg.data)
        except websockets.exceptions.ConnectionClosedError:
            self.websocket = None
            self.active_transport = Device.Transport.USB if self.serial else None
            self._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.active_transport)
            asyncio.create_task(self._establish_websocket_connection())

    async def _handle_outgoing_messages(self):
        while True:
            self._send_to_device(await self.tx_queue.get())

    def _put(self, message: Message):
        self.tx_queue.put_nowait(message)

    def _send_to_device(self, message: Message):
        json_str = self._encode_device_message(message)
        if self.active_transport == Device.Transport.WIFI:
            print(f"TX (WebSocket): {json_str.strip()}")
            asyncio.create_task(self.websocket.send(json_str))
        elif self.active_transport == Device.Transport.USB:
            print(f"TX (USB): {json_str.strip()}")
            self.serial.write(json_str.encode('utf-8'))

    def _serial_exception_handler(self, loop: asyncio.AbstractEventLoop, context: dict):
        if "ClearCommError failed" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device):
        self.device = device
        self.buffer = b""

    def connection_lost(self, exc):
        self.device.serial = None
        self.device.active_transport = None
        self.device._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.device.active_transport)
        asyncio.create_task(self.device._establish_serial_connection())

    def connection_made(self, transport: asyncio.Transport):
        self.device.serial = transport
        self.device.active_transport = Device.Transport.USB
        self.device._call_handlers(Device.Message.Incoming.ACTIVE_TRANSPORT, self.device.active_transport)
        self.device.get_device_info()

    def data_received(self, data: bytes):
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            message = line.decode('utf-8', errors='ignore').strip()

            if message:
                msg = self.device._data_decoder(message)
                print(f"RX (USB): {message}")

                self.device._call_handlers(msg.type, msg.data)
