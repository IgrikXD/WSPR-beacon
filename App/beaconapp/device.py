import asyncio
import threading
import serial_asyncio
import serial.tools.list_ports
from enum import Enum
from beaconapp.tx_mode import ActiveTXMode, TransmissionMode
import copy

class DeviceMessage:
    def __init__(self, message_type, data=None):
        self.message_type = message_type
        self.data = data

class WiFiCredentials:
    def __init__(self, wifi_access_point_name, wifi_access_point_password):
        self.wifi_access_point_name = wifi_access_point_name
        self.wifi_access_point_password = wifi_access_point_password

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
        # TX related messages
        ACTIVE_TX_MODE = 1
        TX_ACTION_STATUS = 2
        GPS_STATUS = 3
        CAL_STATUS = 4
        TX_STATUS = 5
        # Self-check related messages
        SELF_CHECK_ACTION = 6
        SELF_CHECK_STATUS = 7
        SELF_CHECK_ACTIVE = 8
        HARDWARE_INFO = 9
        FIRMWARE_INFO = 10
        # Settings related messages
        CAL_VALUE = 11
        CAL_FREQ_GENERATED = 12
        CONNECTION_STATUS = 13
        WIFI_STATUS = 14
        OTHER = 15

    class OutgoingMessageType(Enum):
        # General messages
        GET_DEVICE_INFO = 1
        # TX related messages
        SET_ACTIVE_TX_MODE = 2
        # Self-check related messages
        RUN_SELF_CHECK = 3
        # Settings related messages
        SET_CAL_METHOD = 4
        SET_CAL_VALUE = 5
        GEN_CAL_FREQUENCY = 6
        RUN_WIFI_CONNECTION = 7
        ALLOW_WIFI_CONNECTION = 8

    def __init__(self):
        self.tx_queue = asyncio.Queue()
        self.transport = None
        self.protocol = None
        self.mapped_callbacks = {}

        # Переменные для asyncio
        self.asyncio_loop = None
        self.async_thread = None

    # Методы для управления обработчиками сообщений остаются без изменений
    def set_device_response_handlers(self, mapped_callbacks):
        self.mapped_callbacks = {
            key: (value if isinstance(value, list) else [value])
            for key, value in mapped_callbacks.items()
        }

    def put(self, message: DeviceMessage):
        self.tx_queue.put_nowait(message)

    def get_device_info(self):
        self.put(DeviceMessage(Device.OutgoingMessageType.GET_DEVICE_INFO))

    def set_wifi_connection_allowed(self, value):
        self.put(DeviceMessage(Device.OutgoingMessageType.ALLOW_WIFI_CONNECTION, value))

    def gen_calibration_frequency(self, frequency):
        self.put(DeviceMessage(Device.OutgoingMessageType.GEN_CAL_FREQUENCY, frequency))

    def set_calibration_type(self, calibration_type):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_CAL_VALUE, value))

    def set_active_tx_mode(self, active_tx_mode):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_ACTIVE_TX_MODE, copy.deepcopy(active_tx_mode)))

    def run_self_check(self):
        self.put(DeviceMessage(Device.OutgoingMessageType.RUN_SELF_CHECK))

    def run_wifi_connection(self, name, password):
        self.put(DeviceMessage(Device.OutgoingMessageType.RUN_WIFI_CONNECTION, WiFiCredentials(name, password)))

    async def connect(self):
        await self._establish_connection()

    async def _establish_connection(self):
        while True:
            device_port = None
            for port in serial.tools.list_ports.comports():
                if port.vid == Device.VID_ESPRESSIF and port.pid == Device.PID_ESP32_C3:
                    device_port = port.device
                    break

            if device_port:
                await asyncio.sleep(0.5)
                try:
                    loop = asyncio.get_running_loop()
                    self.transport, self.protocol = await serial_asyncio.create_serial_connection(
                        loop,
                        lambda: DeviceProtocol(self),
                        device_port,
                        baudrate=115200
                    )
                    break
                except FileNotFoundError as e:
                    continue
                except Exception as e:
                    print(f"Ошибка открытия порта {device_port}: {e}")
            await asyncio.sleep(1)

        # Запускаем обработчик исходящих сообщений
        asyncio.create_task(self._handle_device_requests())

    async def _handle_device_requests(self):
        while self.transport is not None:
            message = await self.tx_queue.get()
            print(f"TX: <{message.message_type.name}> {message.data}")
            if message.message_type == Device.OutgoingMessageType.SET_ACTIVE_TX_MODE:
                if message.data.transmission_mode is not None:
                    msg_str = (
                        f"{message.message_type.name} "
                        f"{message.data.transmission_mode.name} "
                        f"{message.data.tx_call} "
                        f"{message.data.qth_locator} "
                        f"{message.data.output_power} "
                        f"{message.data.transmit_every} "
                        f"{message.data.active_band}\n"
                    )
                else:
                    msg_str = f"{message.message_type.name} None \n"
            else:
                msg_str = f"{message.message_type.name} {message.data} \n"
            if self.transport:
                self.transport.write(msg_str.encode('utf-8'))

    def serial_exception_handler(self, loop, context):
        """
        Обработчик исключений для asyncio‑цикла, который перехватывает ошибки,
        возникающие при работе с serial_asyncio.
        """
        exception = context.get("exception")
        if exception and isinstance(exception, serial.serialutil.SerialException):
            msg = str(exception)
            if "ClearCommError failed" in msg:
                return
        loop.default_exception_handler(context)
        
    # Методы для управления event loop внутри Device
    def start(self):
        """Запускает асинхронный цикл и подключение устройства."""
        self.asyncio_loop = asyncio.new_event_loop()
        self.asyncio_loop.set_exception_handler(self.serial_exception_handler)
        self.async_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.async_thread.start()
        # Планируем подключение к устройству
        asyncio.run_coroutine_threadsafe(self.connect(), self.asyncio_loop)

    def _run_loop(self):
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    async def _shutdown_tasks(self):
        tasks = [t for t in asyncio.all_tasks(self.asyncio_loop) if t is not asyncio.current_task()]
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    def shutdown(self):
        """Корректно завершает работу asyncio-цикла."""
        if self.asyncio_loop and self.asyncio_loop.is_running():
            # Запуск отмены задач
            shutdown_future = asyncio.run_coroutine_threadsafe(self._shutdown_tasks(), self.asyncio_loop)
            try:
                shutdown_future.result(timeout=5)
            except Exception as e:
                print("Ошибка при остановке задач:", e)
            # Остановка цикла
            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
            self.async_thread.join(timeout=5)
            self.asyncio_loop.close()

    def dataDecoder(self, data: str) -> DeviceMessage:
        tokens = data.split()
        try:
            if tokens[0] == Device.IncomingMessageType.ACTIVE_TX_MODE.name:
                if tokens[1] == "None":
                    message = DeviceMessage(Device.IncomingMessageType[tokens[0]], ActiveTXMode())
                else:
                    # Пример разбора сообщения – может потребоваться доработка под конкретный формат
                    message = DeviceMessage(
                        Device.IncomingMessageType[tokens[0]],
                        ActiveTXMode(
                            TransmissionMode[tokens[1]],
                            tokens[2],
                            tokens[3],
                            int(tokens[4]),
                            f"{tokens[5]} {tokens[6]}",
                            tokens[7]
                        )
                    )
            elif tokens[0] == Device.IncomingMessageType.CONNECTION_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], Device.ConnectionStatus[tokens[1]])
            elif tokens[0] == Device.IncomingMessageType.SELF_CHECK_ACTION.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], ' '.join(tokens[1:]))
            elif tokens[0] == Device.IncomingMessageType.TX_ACTION_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], ' '.join(tokens[1:]))
            elif tokens[0] == Device.IncomingMessageType.SELF_CHECK_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            elif tokens[0] == Device.IncomingMessageType.SELF_CHECK_ACTIVE.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            elif tokens[0] == Device.IncomingMessageType.CAL_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            elif tokens[0] == Device.IncomingMessageType.TX_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            elif tokens[0] == Device.IncomingMessageType.GPS_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            elif tokens[0] == Device.IncomingMessageType.CAL_VALUE.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], int(tokens[1]))
            elif tokens[0] == Device.IncomingMessageType.CAL_FREQ_GENERATED.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            elif tokens[0] == Device.IncomingMessageType.HARDWARE_INFO.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1])
            elif tokens[0] == Device.IncomingMessageType.FIRMWARE_INFO.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1])
            elif tokens[0] == Device.IncomingMessageType.WIFI_STATUS.name:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1] != "False")
            else:
                message = DeviceMessage(Device.IncomingMessageType.OTHER, data)
        except (IndexError, ValueError, KeyError) as e:
            # При ошибке разбора возвращаем сообщение с типом OTHER
            message = DeviceMessage(Device.IncomingMessageType.OTHER, data)
        return message


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device):
        self.device = device
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
                msg = self.device.dataDecoder(line_str)
                print(f"RX: <{msg.message_type.name}>: {msg.data}")
                for handler in self.device.mapped_callbacks.get(msg.message_type, []):
                    handler(msg.data)

    def connection_lost(self, exc):
        self.device.transport = None
        self.device.protocol = None
        for handler in self.device.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
            handler(Device.ConnectionStatus.NOT_CONNECTED)
        asyncio.create_task(self.device.connect())


