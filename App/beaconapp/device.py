from enum import Enum
from beaconapp.tx_mode import ActiveTXMode

import copy
import queue
import serial.tools.list_ports
import time
import threading


class DeviceMessage:
    def __init__(self, message_type, data=None):
        self.message_type = message_type
        self.data = data


class WiFiCredentials:
    def __init__(self, wifi_access_point_name, wifi_access_point_password):
        self.wifi_access_point_name = wifi_access_point_name
        self.wifi_access_point_password = wifi_access_point_password


class Device:
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

    def __init__(self, device_name):
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()

        self.device_connected = False
        self.device_name = device_name

        threading.Thread(target=self._handle_device_response, daemon=True).start()
        threading.Thread(target=self._handle_device_requests, daemon=True).start()

    def connect(self):
        threading.Thread(target=self._establish_connection, daemon=True).start()

    def get(self) -> IncomingMessageType:
        return self.rx_queue.get()

    def get_device_info(self):
        self.put(DeviceMessage(Device.OutgoingMessageType.GET_DEVICE_INFO))

    def put(self, message):
        self.tx_queue.put(message)

    def set_wifi_connection_allowed(self, value):
        self.put(DeviceMessage(Device.OutgoingMessageType.ALLOW_WIFI_CONNECTION, value))

    def gen_calibration_frequency(self, frequency):
        self.put(DeviceMessage(Device.OutgoingMessageType.GEN_CAL_FREQUENCY, frequency))

    def set_calibration_type(self, calibration_type):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_CAL_METHOD, calibration_type))

    def set_calibration_value(self, value):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_CAL_VALUE, value))

    def set_device_response_handlers(self, mapped_callbacks):
        self.mapped_callbacks = {
            key: (value if isinstance(value, list) else [value])
            for key, value in mapped_callbacks.items()
        }

    def set_active_tx_mode(self, active_tx_mode):
        self.put(DeviceMessage(Device.OutgoingMessageType.SET_ACTIVE_TX_MODE, copy.deepcopy(active_tx_mode)))

    def run_self_check(self):
        self.put(DeviceMessage(Device.OutgoingMessageType.RUN_SELF_CHECK))

    def run_wifi_connection(self, name, password):
        self.put(DeviceMessage(Device.OutgoingMessageType.RUN_WIFI_CONNECTION, WiFiCredentials(name, password)))

    def _establish_connection(self):
        while True:
            for port in serial.tools.list_ports.comports():
                if self.device_name in port.description:
                    self.device_connected = True
                    break

            if self.device_connected:
                self.get_device_info()
                threading.Thread(target=self._handle_device_disconnect, daemon=True).start()
                break
    
    def _handle_device_disconnect(self):
        while True:
            device_found = False
            for port in serial.tools.list_ports.comports():
                if self.device_name in port.description:
                    device_found = True
                    break
            
            self.device_connected = device_found

            if not self.device_connected:
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CONNECTION_STATUS, Device.ConnectionStatus.NOT_CONNECTED))
                threading.Thread(target=self._establish_connection, daemon=True).start()
                break

    def _handle_device_response(self):
        while (True):
            try:
                received = self.get()
                if received.message_type.name == Device.IncomingMessageType.ACTIVE_TX_MODE.name:
                    print(f"RX: <{received.message_type.name}>: {received.data.transmission_mode}")
                else:
                    print(f"RX: <{received.message_type.name}>: {received.data}")
                handlers = self.mapped_callbacks.get(received.message_type, [])
                for handler in handlers:
                    handler(received.data)
            except queue.Empty:
                continue

    def _handle_device_requests(self):
        self.mode_queue = queue.Queue()
        threading.Thread(target=self.SIM_runTransmission, daemon=True).start()
        while (True):
            try:
                received = self.tx_queue.get()
                if received.message_type == Device.OutgoingMessageType.RUN_SELF_CHECK:
                    self.SIM_runSelfCheck()
                if received.message_type == Device.OutgoingMessageType.SET_ACTIVE_TX_MODE:
                    self.SIM_setActiveTxMode(received.data)
                if received.message_type == Device.OutgoingMessageType.SET_CAL_METHOD:
                    self.SIM_setCalMethod(received.data)
                if received.message_type == Device.OutgoingMessageType.SET_CAL_VALUE:
                    self.SIM_setCalValue(received.data)
                if received.message_type == Device.OutgoingMessageType.GEN_CAL_FREQUENCY:
                    self.SIM_genCalFrequency(received.data)
                if received.message_type == Device.OutgoingMessageType.ALLOW_WIFI_CONNECTION:
                    self.SIM_allowWifiConnection(received.data)
                if received.message_type == Device.OutgoingMessageType.RUN_WIFI_CONNECTION:
                    self.SIM_wifiConnection(received.data)
                if received.message_type == Device.OutgoingMessageType.GET_DEVICE_INFO:
                    self.SIM_getDeviceInfo()
            except queue.Empty:
                continue

    # Dummy functions, just for simulation
    def SIM_setActiveTxMode(self, new_tx_mode):
        print(f"TX: <SET_ACTIVE_TX_MODE> {new_tx_mode.transmission_mode}")
        # if (new_tx_mode.transmission_mode):
        #     self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.ACTIVE_TX_MODE, copy.deepcopy(new_tx_mode)))
        self.mode_queue.put(copy.deepcopy(new_tx_mode))

    def SIM_runTransmission(self):
        last_message = None
        while (True):
            try:
                message = self.mode_queue.get(timeout=1)
                last_message = message
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.ACTIVE_TX_MODE, copy.deepcopy(message)))
            except queue.Empty:
                if (last_message is None) or (message.transmission_mode is None):
                    continue
                message = last_message

            if (message.transmission_mode):
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.GPS_STATUS, True))
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CAL_STATUS, True))
                self.rx_queue.put(DeviceMessage(
                    Device.IncomingMessageType.TX_ACTION_STATUS, "- Waiting for next transmission window... -"))
                time.sleep(3)
                self.rx_queue.put(DeviceMessage(
                    Device.IncomingMessageType.TX_STATUS, True))
                self.rx_queue.put(DeviceMessage(
                    Device.IncomingMessageType.TX_ACTION_STATUS,
                    f"- WSPR transmission {message.tx_call} "
                    f"{message.qth_locator} {message.output_power} at {message.active_band} band -"))
                time.sleep(5)
                self.rx_queue.put(DeviceMessage(
                    Device.IncomingMessageType.TX_ACTION_STATUS,
                    "- WSPR transmission finished! -"))
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.TX_STATUS, False))
                time.sleep(1)
            else:
                # self.rx_queue.put(DeviceMessage(
                #   Device.IncomingMessageType.ACTIVE_TX_MODE, copy.deepcopy(ActiveTXMode())))
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.TX_ACTION_STATUS, "- No active mode -"))

    def SIM_runSelfCheck(self):
        print("TX: <RUN_SELF_CHECK>")
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.SELF_CHECK_ACTIVE, True))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.SELF_CHECK_ACTION, "- LEDs initialized! -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- SI5351 successfully initialized at address 0x60 -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- Establishing a serial connection to the GPS module ... -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- Serial connection to GPS module successfully established! -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- SI5351 successfully initialized at address 0x60 -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- GPS data synchronization test ... -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- Date & time (GMT) synchronized by GPS: 2/7/2024 17:17:44 -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(
            Device.IncomingMessageType.SELF_CHECK_ACTION,
            "- Location synchronized by GPS: 52.2285, 20.9324 -"))
        time.sleep(1)
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.SELF_CHECK_STATUS, True))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.SELF_CHECK_ACTIVE, False))
        # self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.SELF_CHECK_STATUS, False))

    def SIM_getDeviceInfo(self):
        print("TX: <GET_DEVICE_INFO>")
        # active_tx_mode = ActiveTXMode(TransmissionMode.WSPR, "HUITA2", "ZZ55", 23, "10 minutes", "20m")
        # self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.ACTIVE_TX_MODE, copy.deepcopy(active_tx_mode)))
        # self.mode_queue.put(copy.deepcopy(active_tx_mode))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.ACTIVE_TX_MODE, ActiveTXMode()))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CONNECTION_STATUS, Device.ConnectionStatus.USB))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.HARDWARE_INFO, "3.0"))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.FIRMWARE_INFO, "2.0"))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CAL_STATUS, True))
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CAL_VALUE, 2000))

    def SIM_allowWifiConnection(self, is_allowed):
        print(f"TX: <ALLOW_WIFI_CONNECTION>: {is_allowed}")

    def SIM_wifiConnection(self, wifi_credentials):
        print(f"TX: <RUN_WIFI_CONNECTION> "
              f"{wifi_credentials.wifi_access_point_name} "
              f"{wifi_credentials.wifi_access_point_password}")
        time.sleep(3)
        self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.WIFI_STATUS, False))
        # self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CONNECTION_STATUS, ConnectionStatus.WIFI))

    def SIM_genCalFrequency(self, frequency):
        if frequency:
            print(f"TX: <GEN_CAL_FREQUENCY>: {frequency}")
            self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CAL_FREQ_GENERATED, True))
        else:
            print("TX: <GEN_CAL_FREQUENCY>: False")
            self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.CAL_FREQ_GENERATED, False))

    def SIM_setCalMethod(self, method):
        print(f"TX: <SET_CAL_METHOD>: {method.name}")

    def SIM_setCalValue(self, value):
        print(f"TX: <SET_CAL_VALUE>: {value}")
