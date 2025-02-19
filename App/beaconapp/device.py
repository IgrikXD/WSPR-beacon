import asyncio
import json
import serial_asyncio
import serial.tools.list_ports
import threading
import websockets

from beaconapp.tx_mode import ActiveTXMode
from beaconapp.wifi import WiFiCredentials, WiFiData
from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass
class DeviceMessage:
    message_type: Enum
    data: Any = None


class Device:
    class CalibrationType(Enum):
        AUTO = 1
        MANUAL = 2

    class Transport(Enum):
        USB = 1
        WIFI = 2

    class IncomingMessageType(Enum):
        ACTIVE_TX_MODE = 1
        TX_ACTION_STATUS = 2
        GPS_STATUS = 3
        CAL_STATUS = 4
        TX_STATUS = 5
        SELF_CHECK_ACTION = 6
        SELF_CHECK_STATUS = 7
        SELF_CHECK_ACTIVE = 8
        HARDWARE_INFO = 9
        FIRMWARE_INFO = 10
        CAL_VALUE = 11
        CAL_FREQ_GENERATED = 12
        CONNECTION_STATUS = 13
        WIFI_SSID_DATA = 14

    class OutgoingMessageType(Enum):
        GET_DEVICE_INFO = 1
        SET_ACTIVE_TX_MODE = 2
        RUN_SELF_CHECK = 3
        SET_CAL_METHOD = 4
        SET_CAL_VALUE = 5
        GEN_CAL_FREQUENCY = 6
        RUN_WIFI_CONNECTION = 7
        SET_SSID_CONNECT_AT_STARTUP = 8

    def __init__(self):
        self.tx_queue = asyncio.Queue()
        # Serial transport (USB)
        self.serial = None
        # WebSocket transport (Wi-Fi)
        self.websocket = None
        # Active transport, USB by default
        self.active_transport = self.Transport.USB
        self.mapped_callbacks = {}

        self.asyncio_loop = None
        self.async_thread = None

    def connect(self):
        self.asyncio_loop = asyncio.new_event_loop()
        self.asyncio_loop.set_exception_handler(self._serial_exception_handler)
        self.async_thread = threading.Thread(target=self._run_asyncio_loop, daemon=True)
        self.async_thread.start()

        asyncio.run_coroutine_threadsafe(self._establish_serial_connection(), self.asyncio_loop)
        asyncio.run_coroutine_threadsafe(self._establish_websocket_connection(), self.asyncio_loop)
        asyncio.run_coroutine_threadsafe(self._handle_device_requests(), self.asyncio_loop)

    def disconnect(self):
        if self.asyncio_loop and self.asyncio_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._shutdown_tasks(), self.asyncio_loop)
            future.result(timeout=5)

            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
            self.async_thread.join(timeout=5)
            self.asyncio_loop.close()

    def set_device_response_handlers(self, mapped_callbacks):
        self.mapped_callbacks = {
            key: (value if isinstance(value, list) else [value])
            for key, value in mapped_callbacks.items()
        }

    def get_device_info(self):
        self._put(DeviceMessage(self.OutgoingMessageType.GET_DEVICE_INFO))

    def gen_calibration_frequency(self, frequency: float):
        self._put(DeviceMessage(self.OutgoingMessageType.GEN_CAL_FREQUENCY, frequency))

    def set_calibration_type(self, calibration_type: CalibrationType):
        self._put(DeviceMessage(self.OutgoingMessageType.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value: int):
        self._put(DeviceMessage(self.OutgoingMessageType.SET_CAL_VALUE, value))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        self._put(DeviceMessage(self.OutgoingMessageType.SET_ACTIVE_TX_MODE, active_tx_mode))

    def run_self_check(self):
        self._put(DeviceMessage(self.OutgoingMessageType.RUN_SELF_CHECK))

    def set_ssid_connect_at_startup(self, value: bool):
        self._put(DeviceMessage(self.OutgoingMessageType.SET_SSID_CONNECT_AT_STARTUP, value))

    def set_wifi_connection(self, wifi_credentials: WiFiCredentials):
        self._put(DeviceMessage(self.OutgoingMessageType.RUN_WIFI_CONNECTION, wifi_credentials))

    def _call_handlers(self, msg_type: Enum, data):
        for handler in self.mapped_callbacks.get(msg_type, []):
            handler(data)

    def _data_decoder(self, line_str: str):
        obj = json.loads(line_str)

        msg_type = self.IncomingMessageType[obj.get("type")]

        return DeviceMessage(msg_type, self._decode_data(msg_type, obj.get("data")))

    def _decode_data(self, msg_type: IncomingMessageType, raw_data):
        if msg_type == self.IncomingMessageType.ACTIVE_TX_MODE:
            return ActiveTXMode.from_json(raw_data)

        if msg_type == self.IncomingMessageType.CONNECTION_STATUS:
            if raw_data == self.Transport.USB.name:
                self.active_transport = self.Transport.USB if self.serial else None
            elif raw_data == self.Transport.WIFI.name:
                self.active_transport = self.Transport.WIFI if self.websocket else None
            return self.active_transport

        if msg_type == self.IncomingMessageType.WIFI_SSID_DATA:
            return WiFiData.from_json(raw_data)

        return raw_data

    def _encode_data(self, data):
        if data is None:
            return None

        if isinstance(data, (ActiveTXMode, WiFiCredentials)):
            return data.to_json()
        elif isinstance(data, Enum):
            return data.name
        return data

    def _encode_device_message(self, message: DeviceMessage):
        return json.dumps({
            "type": message.message_type.name,
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
                print("Connecting to WebSocket...")
                self.websocket = await websockets.connect("ws://esp32-device:81")
                asyncio.create_task(self._websocket_receiver())
                break
            except Exception:
                continue

    async def _websocket_receiver(self):
        try:
            print("WebSocket receiver started")
            self.active_transport = self.Transport.WIFI if self.websocket else None
            self.get_device_info()
            async for message in self.websocket:
                message = message.strip()
                if message:
                    msg = self._data_decoder(message)
                    print(f"RX (WebSocket): {message}")
                    self._call_handlers(msg.message_type, msg.data)
        except Exception as e:
            print("WebSocket receiver error", e)
        finally:
            self.websocket = None
            if self.serial is None:
                self.active_transport = None
                self._call_handlers(self.IncomingMessageType.CONNECTION_STATUS, self.active_transport)
            await asyncio.sleep(1)
            asyncio.create_task(self._establish_websocket_connection())

    async def _handle_device_requests(self):
        while True:
            message = await self.tx_queue.get()
            self._send_to_device(message)

    def _put(self, message: DeviceMessage):
        self.tx_queue.put_nowait(message)

    def _run_asyncio_loop(self):
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def _send_to_device(self, message: DeviceMessage):
        json_str = self._encode_device_message(message)
        if self.active_transport == self.Transport.WIFI and self.websocket is not None:
            print(f"TX (WebSocket): {json_str.strip()}")
            asyncio.create_task(self.websocket.send(json_str))
        elif self.active_transport == self.Transport.USB and self.serial is not None:
            print(f"TX (USB): {json_str.strip()}")
            self.serial.write(json_str.encode('utf-8'))

    def _serial_exception_handler(self, loop: asyncio.AbstractEventLoop, context: dict):
        if "ClearCommError failed" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)

    async def _shutdown_tasks(self):
        tasks = [t for t in asyncio.all_tasks(self.asyncio_loop) if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device):
        self.device = device
        self.buffer = b""

    def connection_lost(self, exc):
        self.device.serial = None
        self.device.active_transport = None
        self.device._call_handlers(Device.IncomingMessageType.CONNECTION_STATUS, None)
        asyncio.create_task(self.device._establish_serial_connection())

    def connection_made(self, transport: asyncio.Transport):
        self.device.serial = transport
        self.device.active_transport = self.device.Transport.USB
        self.device._call_handlers(Device.IncomingMessageType.CONNECTION_STATUS, Device.Transport.USB)
        self.device.get_device_info()

    def data_received(self, data: bytes):
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            message = line.decode('utf-8', errors='ignore').strip()

            if message:
                msg = self.device._data_decoder(message)
                print(f"RX (USB): {message}")

                self.device._call_handlers(msg.message_type, msg.data)
