import asyncio
import json
import serial_asyncio
import serial.tools.list_ports
import threading
from beaconapp.wifi_credentials import WiFiCredentials

from beaconapp.tx_mode import ActiveTXMode
from enum import Enum


class DeviceMessage:
    def __init__(self, message_type, data=None):
        self.message_type = message_type
        self.data = data


class Device:
    VID_ESPRESSIF = 0x303A
    PID_ESP32_C3 = 0x1001

    class CalibrationType(Enum):
        AUTO = 1
        MANUAL = 2

    class ConnectionStatus(Enum):
        NOT_CONNECTED = 1
        USB = 2
        WIFI = 3

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
        WIFI_STATUS = 14
        OTHER = 15

    class OutgoingMessageType(Enum):
        GET_DEVICE_INFO = 1
        SET_ACTIVE_TX_MODE = 2
        RUN_SELF_CHECK = 3
        SET_CAL_METHOD = 4
        SET_CAL_VALUE = 5
        GEN_CAL_FREQUENCY = 6
        RUN_WIFI_CONNECTION = 7
        ALLOW_WIFI_CONNECTION = 8

    def __init__(self):
        self.tx_queue = asyncio.Queue()
        self.transport = None
        self.mapped_callbacks = {}

        self.asyncio_loop = None
        self.async_thread = None

    def set_device_response_handlers(self, mapped_callbacks):
        self.mapped_callbacks = {
            key: (value if isinstance(value, list) else [value])
            for key, value in mapped_callbacks.items()
        }

    def put(self, message: DeviceMessage):
        self.tx_queue.put_nowait(message)

    def get_device_info(self):
        self.put(DeviceMessage(self.OutgoingMessageType.GET_DEVICE_INFO))

    def set_wifi_connection_allowed(self, value: bool):
        self.put(DeviceMessage(self.OutgoingMessageType.ALLOW_WIFI_CONNECTION, value))

    def gen_calibration_frequency(self, frequency: float):
        self.put(DeviceMessage(self.OutgoingMessageType.GEN_CAL_FREQUENCY, frequency))

    def set_calibration_type(self, calibration_type: CalibrationType):
        self.put(DeviceMessage(self.OutgoingMessageType.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value: int):
        self.put(DeviceMessage(self.OutgoingMessageType.SET_CAL_VALUE, value))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        self.put(DeviceMessage(self.OutgoingMessageType.SET_ACTIVE_TX_MODE, active_tx_mode))

    def run_self_check(self):
        self.put(DeviceMessage(self.OutgoingMessageType.RUN_SELF_CHECK))

    def run_wifi_connection(self, wifi_credentials: WiFiCredentials):
        self.put(DeviceMessage(self.OutgoingMessageType.RUN_WIFI_CONNECTION, wifi_credentials))

    # ---------------------------------------------------------
    # Логика подключения к устройству
    # ---------------------------------------------------------
    async def connect(self):
        await self._establish_connection()

    async def _establish_connection(self):
        while True:
            device_port = self._find_device_port()
            if device_port:
                await asyncio.sleep(0.5)
                self.transport, _ = await serial_asyncio.create_serial_connection(
                    asyncio.get_running_loop(),
                    lambda: DeviceProtocol(self),
                    device_port,
                    baudrate=115200
                )
                break
            await asyncio.sleep(0.5)

        asyncio.create_task(self._handle_device_requests())

    def _find_device_port(self):
        for port in serial.tools.list_ports.comports():
            if port.vid == self.VID_ESPRESSIF and port.pid == self.PID_ESP32_C3:
                return port.device
        return None

    # ---------------------------------------------------------
    # Логика отправки сообщений (через очередь)
    # ---------------------------------------------------------
    async def _handle_device_requests(self):
        while self.transport is not None:
            message = await self.tx_queue.get()
            self._send_to_device(message)

    def _send_to_device(self, message: DeviceMessage):
        json_str = self._encode_device_message(message)
        print(f"TX: {json_str.strip()}")
        if self.transport:
            self.transport.write(json_str.encode('utf-8'))

    def _encode_device_message(self, message: DeviceMessage) -> str:
        payload = {"type": message.message_type.name, "data": self._encode_data(message.data)}
        return json.dumps(payload) + "\n"

    def _encode_data(self, data):
        if data is None:
            return None

        if isinstance(data, (ActiveTXMode, WiFiCredentials)):
            return data.to_json()
        elif isinstance(data, Enum):
            return data.name
        else:
            return data

    # ---------------------------------------------------------
    # Завершение работы
    # ---------------------------------------------------------
    def shutdown(self):
        if self.asyncio_loop and self.asyncio_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._shutdown_tasks(), self.asyncio_loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                print("Ошибка при остановке задач:", e)

            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
            self.async_thread.join(timeout=5)
            self.asyncio_loop.close()

    async def _shutdown_tasks(self):
        tasks = [t for t in asyncio.all_tasks(self.asyncio_loop) if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    # ---------------------------------------------------------
    # Запуск в отдельном потоке
    # ---------------------------------------------------------
    def start(self):
        self.asyncio_loop = asyncio.new_event_loop()
        self.asyncio_loop.set_exception_handler(self.serial_exception_handler)
        self.async_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.async_thread.start()

        asyncio.run_coroutine_threadsafe(self.connect(), self.asyncio_loop)

    def _run_loop(self):
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def serial_exception_handler(self, loop, context):
        if "ClearCommError failed" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)

    # ---------------------------------------------------------
    # Декодирование входящих данных (JSON -> DeviceMessage)
    # ---------------------------------------------------------
    def _data_decoder(self, line_str: str):
        obj = json.loads(line_str)
        msg_type = obj.get("type")
        raw_data = obj.get("data")

        if msg_type in self.IncomingMessageType.__members__:
            msg_type = self.IncomingMessageType[msg_type]
        else:
            msg_type = self.IncomingMessageType.OTHER

        return DeviceMessage(msg_type, self._decode_data(msg_type, raw_data))

    def _decode_data(self, msg_type, raw_data):
        if msg_type == self.IncomingMessageType.ACTIVE_TX_MODE:
            return self._decode_active_tx_mode(raw_data)

        if msg_type == self.IncomingMessageType.CONNECTION_STATUS:
            return self.ConnectionStatus[raw_data]

        return raw_data

    def _decode_active_tx_mode(self, raw_data):
        return ActiveTXMode.from_json(raw_data)


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device):
        self.device = device
        self.transport = None
        self.buffer = b""

    def connection_made(self, transport):
        self.transport = transport

        for handler in self.device.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
            handler(Device.ConnectionStatus.USB)

        self.device.get_device_info()

    def data_received(self, data: bytes):
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            line_str = line.decode('utf-8', errors='ignore').strip()

            if line_str:
                msg = self.device._data_decoder(line_str)
                print(f"RX: {line_str}")

                for handler in self.device.mapped_callbacks.get(msg.message_type, []):
                    handler(msg.data)

    def connection_lost(self, exc):
        self.device.transport = None

        for handler in self.device.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
            handler(Device.ConnectionStatus.NOT_CONNECTED)

        asyncio.create_task(self.device.connect())
