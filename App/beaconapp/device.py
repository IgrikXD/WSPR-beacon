import asyncio
import threading
import serial_asyncio
import serial.tools.list_ports
import copy

from beaconapp.tx_mode import ActiveTXMode, TransmissionMode
from enum import Enum

class WiFiCredentials:
    def __init__(self, wifi_access_point_name, wifi_access_point_password):
        self.wifi_access_point_name = wifi_access_point_name
        self.wifi_access_point_password = wifi_access_point_password


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
        # TX related
        ACTIVE_TX_MODE = 1
        TX_ACTION_STATUS = 2
        GPS_STATUS = 3
        CAL_STATUS = 4
        TX_STATUS = 5
        # Self-check
        SELF_CHECK_ACTION = 6
        SELF_CHECK_STATUS = 7
        SELF_CHECK_ACTIVE = 8
        HARDWARE_INFO = 9
        FIRMWARE_INFO = 10
        # Settings
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
        self.protocol = None
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
        self.put(DeviceMessage(Device.OutgoingMessageType.GET_DEVICE_INFO))

    def set_wifi_connection_allowed(self, value: bool):
        self.put(DeviceMessage(Device.OutgoingMessageType.ALLOW_WIFI_CONNECTION, value))

    def gen_calibration_frequency(self, frequency: float):
        self.put(DeviceMessage(Device.OutgoingMessageType.GEN_CAL_FREQUENCY, frequency))

    def set_calibration_type(self, calibration_type: CalibrationType):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value: int):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_CAL_VALUE, value))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_ACTIVE_TX_MODE, copy.deepcopy(active_tx_mode)))

    def run_self_check(self):
        self.put(DeviceMessage(Device.OutgoingMessageType.RUN_SELF_CHECK))

    def run_wifi_connection(self, name: str, password: str):
        creds = WiFiCredentials(name, password)
        self.put(DeviceMessage(Device.OutgoingMessageType.RUN_WIFI_CONNECTION, creds))

    # -------------------------------
    # Логика подключения
    # -------------------------------
    async def connect(self):
        await self._establish_connection()

    async def _establish_connection(self):
        """
        Цикл поиска порта, соответствующего ESP32-C3, и подключения к нему.
        При разрыве соединения или ошибке — пытается подключиться заново.
        """
        while True:
            device_port = self._find_device_port()
            if device_port:
                try:
                    # Небольшая задержка, чтобы порт успел корректно открыться
                    await asyncio.sleep(0.5)

                    loop = asyncio.get_running_loop()
                    self.transport, self.protocol = await serial_asyncio.create_serial_connection(
                        loop,
                        lambda: DeviceProtocol(self),
                        device_port,
                        baudrate=115200
                    )
                    break  # успешное подключение — выходим из цикла
                except Exception as e:
                    print(f"Ошибка открытия порта {device_port}: {e}")

            # Если порт не найден или была ошибка — повтор через 1 сек.
            await asyncio.sleep(1)

        # Запуск задания на отправку сообщений из очереди
        asyncio.create_task(self._handle_device_requests())

    def _find_device_port(self):
        """
        Ищет порт по VID/PID, возвращает имя порта или None.
        """
        for port in serial.tools.list_ports.comports():
            if port.vid == self.VID_ESPRESSIF and port.pid == self.PID_ESP32_C3:
                return port.device
        return None

    # -------------------------------
    # Логика отправки сообщений из очереди
    # -------------------------------
    async def _handle_device_requests(self):
        while self.transport is not None:
            message = await self.tx_queue.get()
            self._send_to_device(message)

    def _send_to_device(self, message: DeviceMessage):
        """
        Формирует строку для отправки устройству.
        """
        print(f"TX: <{message.message_type.name}> {message.data}")
        if message.message_type == self.OutgoingMessageType.SET_ACTIVE_TX_MODE and message.data is not None:
            mode_data = message.data
            if mode_data.transmission_mode:
                msg_str = (
                    f"{message.message_type.name} "
                    f"{mode_data.transmission_mode.name} "
                    f"{mode_data.tx_call} "
                    f"{mode_data.qth_locator} "
                    f"{mode_data.output_power} "
                    f"{mode_data.transmit_every} "
                    f"{mode_data.active_band}\n"
                )
            else:
                msg_str = f"{message.message_type.name} None\n"
        else:
            msg_str = f"{message.message_type.name} {message.data}\n"

        if self.transport:
            self.transport.write(msg_str.encode('utf-8'))

    # -------------------------------
    # Shutdown
    # -------------------------------
    def shutdown(self):
        """
        Корректно завершает работу asyncio-цикла.
        """
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

    # -------------------------------
    # Логика работы в отдельном потоке
    # -------------------------------
    def start(self):
        """
        Запускает asyncio-loop в отдельном потоке и планирует подключение к устройству.
        """
        self.asyncio_loop = asyncio.new_event_loop()
        self.asyncio_loop.set_exception_handler(self.serial_exception_handler)
        self.async_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.async_thread.start()

        asyncio.run_coroutine_threadsafe(self.connect(), self.asyncio_loop)

    def _run_loop(self):
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def serial_exception_handler(self, loop, context):
        """
        Обработчик исключений для asyncio‑цикла, игнорирующий специфичные
        SerialException, если это необходимо.
        """
        exception = context.get("exception")
        if exception and "ClearCommError failed" in str(exception):
            # Игнорируем критическую ошибку, встречающуюся на Windows
            return
        loop.default_exception_handler(context)

    # -------------------------------
    # Логика декодирования входящих данных
    # -------------------------------
    def dataDecoder(self, data: str) -> DeviceMessage:
        tokens = data.split()
        if not tokens:
            return DeviceMessage(self.IncomingMessageType.OTHER, data)

        msg_type_str = tokens[0]

        # Маппинг функций парсинга
        parse_map = {
            self.IncomingMessageType.ACTIVE_TX_MODE.name:         self._parse_active_tx_mode,
            self.IncomingMessageType.CONNECTION_STATUS.name:      self._parse_connection_status,
            self.IncomingMessageType.SELF_CHECK_ACTION.name:      self._parse_str_data,
            self.IncomingMessageType.TX_ACTION_STATUS.name:       self._parse_str_data,
            self.IncomingMessageType.SELF_CHECK_STATUS.name:      self._parse_bool_data,
            self.IncomingMessageType.SELF_CHECK_ACTIVE.name:      self._parse_bool_data,
            self.IncomingMessageType.CAL_STATUS.name:             self._parse_bool_data,
            self.IncomingMessageType.TX_STATUS.name:              self._parse_bool_data,
            self.IncomingMessageType.GPS_STATUS.name:             self._parse_bool_data,
            self.IncomingMessageType.CAL_VALUE.name:              self._parse_int_data,
            self.IncomingMessageType.CAL_FREQ_GENERATED.name:     self._parse_bool_data,
            self.IncomingMessageType.HARDWARE_INFO.name:          self._parse_str_data,
            self.IncomingMessageType.FIRMWARE_INFO.name:          self._parse_str_data,
            self.IncomingMessageType.WIFI_STATUS.name:            self._parse_bool_data,
        }

        if msg_type_str in parse_map:
            try:
                return parse_map[msg_type_str](tokens)
            except (ValueError, IndexError, KeyError):
                # Любая ошибка парсинга — возвращаем как OTHER
                return DeviceMessage(self.IncomingMessageType.OTHER, data)
        else:
            # Неизвестный тип — OTHER
            return DeviceMessage(self.IncomingMessageType.OTHER, data)

    # -------------------------------
    # Вспомогательные функции парсинга
    # -------------------------------
    def _parse_active_tx_mode(self, tokens: list) -> DeviceMessage:
        """
        Пример: ACTIVE_TX_MODE CW R0XXX LO01 5 5min 20m
        """
        if tokens[1] == "None":
            return DeviceMessage(
                self.IncomingMessageType.ACTIVE_TX_MODE,
                ActiveTXMode()
            )
        # Разбираем поля согласно формату
        mode = TransmissionMode[tokens[1]]
        tx_call = tokens[2]
        qth_locator = tokens[3]
        output_power = int(tokens[4])
        transmit_every = tokens[5]
        active_band = tokens[6]

        return DeviceMessage(
            self.IncomingMessageType.ACTIVE_TX_MODE,
            ActiveTXMode(mode, tx_call, qth_locator, output_power, transmit_every, active_band)
        )

    def _parse_connection_status(self, tokens: list) -> DeviceMessage:
        status = self.ConnectionStatus[tokens[1]]
        return DeviceMessage(self.IncomingMessageType.CONNECTION_STATUS, status)

    def _parse_bool_data(self, tokens: list) -> DeviceMessage:
        # Формат: <MessageType> <True/False>
        bool_val = (tokens[1] != "False")
        return DeviceMessage(self.IncomingMessageType[tokens[0]], bool_val)

    def _parse_str_data(self, tokens: list) -> DeviceMessage:
        # Остаток строки после первого токена
        return DeviceMessage(self.IncomingMessageType[tokens[0]], " ".join(tokens[1:]))

    def _parse_int_data(self, tokens: list) -> DeviceMessage:
        # Формат: <MessageType> <int>
        int_val = int(tokens[1])
        return DeviceMessage(self.IncomingMessageType[tokens[0]], int_val)


class DeviceProtocol(asyncio.Protocol):
    def __init__(self, device: Device):
        self.device = device
        self.transport = None
        self.buffer = b""

    def connection_made(self, transport):
        self.transport = transport
        # Уведомляем колбэки о статусе подключения
        for handler in self.device.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
            handler(Device.ConnectionStatus.USB)

        # При подключении сразу запрашиваем информацию об устройстве
        self.device.get_device_info()

    def data_received(self, data: bytes):
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            line_str = line.decode('utf-8', errors='ignore').strip()
            if line_str:
                # Декодируем строку в DeviceMessage
                msg = self.device.dataDecoder(line_str)
                print(f"RX: <{msg.message_type.name}>: {msg.data}")

                # Передаём колбэкам
                for handler in self.device.mapped_callbacks.get(msg.message_type, []):
                    handler(msg.data)

    def connection_lost(self, exc):
        self.device.transport = None
        self.device.protocol = None

        # Уведомляем колбэки о том, что связь прервалась
        for handler in self.device.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
            handler(Device.ConnectionStatus.NOT_CONNECTED)

        # Пытаемся переподключиться
        asyncio.create_task(self.device.connect())
