from enum import Enum
from beaconapp.tx_mode import ActiveTXMode, TransmissionMode

import copy
import queue
import serial
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

    def __init__(self, device_name):
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()

        self.device = None
        self.device_connected = False
        self.device_name = device_name

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
                    self.device = port.device
                    self.ser = serial.Serial(self.device, 115200, timeout=1)
                    break

            if self.device_connected:
                for handler in self.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
                    handler(Device.ConnectionStatus.USB)
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                self.get_device_info()
                threading.Thread(target=self._handle_device_disconnect, daemon=True).start()
                break
        
        threading.Thread(target=self._handle_device_response, daemon=True).start()

    def _handle_device_disconnect(self):
        while True:
            device_found = False
            for port in serial.tools.list_ports.comports():
                if self.device_name in port.description:
                    device_found = True
                    break

            self.device_connected = device_found

            if not self.device_connected:
                for handler in self.mapped_callbacks.get(Device.IncomingMessageType.CONNECTION_STATUS, []):
                    handler(Device.ConnectionStatus.NOT_CONNECTED)
                threading.Thread(target=self._establish_connection, daemon=True).start()
                break

    def _handle_device_response(self):
        while (True):
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    received = self.dataDecoder(data)
                    if received.message_type.name == Device.IncomingMessageType.ACTIVE_TX_MODE.name:
                        print(f"RX: <{received.message_type.name}>: {received.data.transmission_mode}")
                    else:
                        print(f"RX: <{received.message_type.name}>: {received.data}")
                    handlers = self.mapped_callbacks.get(received.message_type, [])
                    for handler in handlers:
                        handler(received.data)
            except queue.Empty:
                continue
            except serial.serialutil.SerialException:
                break

    def dataDecoder(self, data):
        tokens = data.split()
        if tokens[0] == Device.IncomingMessageType.ACTIVE_TX_MODE.name:
            if tokens[1] == "None":
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], ActiveTXMode())
            else:
                message = DeviceMessage(Device.IncomingMessageType[tokens[0]], 
                                        ActiveTXMode(
                                            TransmissionMode[tokens[1]],
                                            tokens[2],
                                            tokens[3],
                                            int(tokens[4]),
                                            f"{tokens[5]} {tokens[6]}",
                                            tokens[7]))
        elif tokens[0] == Device.IncomingMessageType.CONNECTION_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], Device.ConnectionStatus[tokens[1]])
        elif tokens[0] == Device.IncomingMessageType.SELF_CHECK_ACTION.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], ' '.join(tokens[1:]))
        elif tokens[0] == Device.IncomingMessageType.TX_ACTION_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], ' '.join(tokens[1:]))
        elif tokens[0] == Device.IncomingMessageType.SELF_CHECK_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        elif tokens[0] == Device.IncomingMessageType.SELF_CHECK_ACTIVE.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        elif tokens[0] == Device.IncomingMessageType.CAL_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        elif tokens[0] == Device.IncomingMessageType.TX_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        elif tokens[0] == Device.IncomingMessageType.GPS_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        elif tokens[0] == Device.IncomingMessageType.CAL_VALUE.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], int(tokens[1]))
        elif tokens[0] == Device.IncomingMessageType.CAL_FREQ_GENERATED.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        elif tokens[0] == Device.IncomingMessageType.HARDWARE_INFO.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1])
        elif tokens[0] == Device.IncomingMessageType.FIRMWARE_INFO.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], tokens[1])
        elif tokens[0] == Device.IncomingMessageType.WIFI_STATUS.name:
            message = DeviceMessage(Device.IncomingMessageType[tokens[0]], False if tokens[1] == "False" else True)
        else:
            message = DeviceMessage(Device.IncomingMessageType.OTHER, data)

        return message

    def _handle_device_requests(self):
        self.mode_queue = queue.Queue()
        threading.Thread(target=self.SIM_runTransmission, daemon=True).start()
        while (True):
            try:
                received = self.tx_queue.get()
                print(f"TX: <{str(received.message_type.name)}> {str(received.data)}")
                if received.message_type == Device.OutgoingMessageType.SET_ACTIVE_TX_MODE:
                    self.SIM_setActiveTxMode(received.data)
                    if received.data.transmission_mode is not None:
                        self.ser.write((f"{str(received.message_type.name)} {received.data.transmission_mode.name} {received.data.tx_call} {received.data.qth_locator} {received.data.output_power} {received.data.transmit_every} {received.data.active_band}{'\n'}").encode('utf-8'))
                    else:
                        self.ser.write((f"{str(received.message_type.name)} {None} {'\n'}").encode('utf-8'))
                else:
                    self.ser.write((f"{str(received.message_type.name)} {str(received.data)} {'\n'}").encode('utf-8'))
            except queue.Empty:
                continue

    # Dummy functions, just for simulation
    def SIM_setActiveTxMode(self, new_tx_mode):
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
                self.rx_queue.put(DeviceMessage(Device.IncomingMessageType.TX_ACTION_STATUS, "- No active mode -"))