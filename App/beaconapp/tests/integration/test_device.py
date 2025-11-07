import pytest
import serial.tools.list_ports
import time
import threading

from beaconapp.device import Device
from beaconapp.data_wrappers import ActiveTXMode, Band, TransmitEvery, TXMode
from beaconapp.data_wrappers import ConnectionStatus, WiFiCredentials, WiFiData
from enum import Enum


# VID and PID for ESP32-C3
DEVICE_VID = 0x303A
DEVICE_PID = 0x1001

# Device response timeout in seconds
DEVICE_RESPONSE_TIMEOUT = 2.0


def find_device():
    """
    Find WSPR-beacon device by VID/PID.
    Returns device port name if found, None otherwise.
    """
    for port in serial.tools.list_ports.comports():
        if port.vid == DEVICE_VID and port.pid == DEVICE_PID:
            return port.device
    return None


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_concurrent_connect_calls():
    """
    Checks that concurrent connect() calls don't cause race conditions.
    """
    device = Device()
    results = []

    def attempt_connect():
        """
        Each thread attempts to connect. Lock ensures only one succeeds.
        """
        try:
            device.connect()
            results.append(True)
        except Device.AlreadyConnectedError:
            results.append(False)

    # Launch multiple threads that attempt to connect simultaneously
    num_threads = 3
    threads = [threading.Thread(target=attempt_connect) for _ in range(num_threads)]

    # Start all threads and wait for completion
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # All threads completed successfully
    assert len(results) == num_threads

    # Only one thread should have connected successfully
    assert results.count(True) == 1
    assert results.count(False) == 2

    # Terminate device connection
    device.disconnect()


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_device_reconnection():
    """
    Checks that device can reconnect without issues.
    """
    device = Device()

    # First device connection
    device.connect()
    time.sleep(DEVICE_RESPONSE_TIMEOUT)
    # Verify first connection is via USB
    assert device.active_transport is Device.Transport.USB
    # Terminate device connection
    device.disconnect()

    # Verify transport is reset after disconnect
    assert device.active_transport is None

    # Wait for the serial port to be fully released
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Second device connection
    device.connect()
    time.sleep(DEVICE_RESPONSE_TIMEOUT)
    # Verify reconnection via USB
    assert device.active_transport is Device.Transport.USB
    # Terminate device connection
    device.disconnect()


@pytest.fixture(scope="function")
def device():
    """
    Create a fresh Device instance for testing.
    """
    device_instance = Device()
    device_instance.connect()
    # Allow more time for device to be ready and transport to be established
    time.sleep(DEVICE_RESPONSE_TIMEOUT)
    yield device_instance
    # Cleanup: ensure device is disconnected after each test
    device_instance.disconnect()


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_get_device_info(device):
    """
    Checks that get device info processed correctly.
    """
    # Arrange: Set up flags to track all expected responses
    responses = {
        Device.Message.Incoming.ACTIVE_TRANSPORT:   None,
        Device.Message.Incoming.CAL_VALUE:          None,
        Device.Message.Incoming.CAL_STATUS:         None,
        Device.Message.Incoming.GPS_STATUS:         None,
        Device.Message.Incoming.TX_STATUS:          None,
        Device.Message.Incoming.WIFI_SSID_DATA:     None,
        Device.Message.Incoming.WIFI_STATUS:        None,
        Device.Message.Incoming.FIRMWARE_INFO:      None,
        Device.Message.Incoming.HARDWARE_INFO:      None,
        Device.Message.Incoming.ACTIVE_TX_MODE:     None,
        Device.Message.Incoming.TX_ACTION_STATUS:   None
    }

    # Register callbacks for all response types
    device.set_device_response_handlers({
        Device.Message.Incoming.ACTIVE_TRANSPORT:   [
            lambda transport: responses.update({Device.Message.Incoming.ACTIVE_TRANSPORT: transport})],
        Device.Message.Incoming.CAL_VALUE:          [
            lambda value: responses.update({Device.Message.Incoming.CAL_VALUE: value})],
        Device.Message.Incoming.CAL_STATUS:         [
            lambda status: responses.update({Device.Message.Incoming.CAL_STATUS: status})],
        Device.Message.Incoming.GPS_STATUS:         [
            lambda status: responses.update({Device.Message.Incoming.GPS_STATUS: status})],
        Device.Message.Incoming.TX_STATUS:         [
            lambda status: responses.update({Device.Message.Incoming.TX_STATUS: status})],
        Device.Message.Incoming.WIFI_SSID_DATA:     [
            lambda data: responses.update({Device.Message.Incoming.WIFI_SSID_DATA: data})],
        Device.Message.Incoming.WIFI_STATUS:        [
            lambda status: responses.update({Device.Message.Incoming.WIFI_STATUS: status})],
        Device.Message.Incoming.FIRMWARE_INFO:      [
            lambda data: responses.update({Device.Message.Incoming.FIRMWARE_INFO: data})],
        Device.Message.Incoming.HARDWARE_INFO:      [
            lambda data: responses.update({Device.Message.Incoming.HARDWARE_INFO: data})],
        Device.Message.Incoming.ACTIVE_TX_MODE:     [
            lambda data: responses.update({Device.Message.Incoming.ACTIVE_TX_MODE: data})],
        Device.Message.Incoming.TX_ACTION_STATUS:   [
            lambda data: responses.update({Device.Message.Incoming.TX_ACTION_STATUS: data})]
    })

    device.get_device_info()

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    # We should have received all expected responses
    assert responses[Device.Message.Incoming.ACTIVE_TRANSPORT] is Device.Transport.USB
    assert isinstance(responses[Device.Message.Incoming.CAL_VALUE], int)
    assert isinstance(responses[Device.Message.Incoming.CAL_STATUS], bool)
    assert isinstance(responses[Device.Message.Incoming.GPS_STATUS], bool)
    assert isinstance(responses[Device.Message.Incoming.TX_STATUS], bool)
    assert isinstance(responses[Device.Message.Incoming.WIFI_SSID_DATA], WiFiData)
    assert isinstance(responses[Device.Message.Incoming.WIFI_STATUS], ConnectionStatus)
    assert isinstance(responses[Device.Message.Incoming.FIRMWARE_INFO], str)
    assert isinstance(responses[Device.Message.Incoming.HARDWARE_INFO], float)
    assert isinstance(responses[Device.Message.Incoming.ACTIVE_TX_MODE], ActiveTXMode)
    assert isinstance(responses[Device.Message.Incoming.TX_ACTION_STATUS], str)


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_run_wifi_connection(device):
    """
    Checks that Wi-Fi connection request processed correctly.

    Verifies that the device correctly handles Wi-Fi connection request to fake SSID.
    """
    # Store received data for later verification
    received_data = {Device.Message.Incoming.WIFI_STATUS: None}

    device.set_device_response_handlers({
        Device.Message.Incoming.WIFI_STATUS: [
            lambda status: received_data.update({Device.Message.Incoming.WIFI_STATUS: status})]
    })

    device.set_wifi_connection(WiFiCredentials(ssid="SSID", password="PASSWORD"))

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    assert isinstance(received_data[Device.Message.Incoming.WIFI_STATUS], ConnectionStatus)
    assert received_data[Device.Message.Incoming.WIFI_STATUS] is ConnectionStatus.INITIATED

    # Wait for device response
    time.sleep(10.0)  # Allow more time for Wi-Fi connection attempt

    # Verify received data
    assert isinstance(received_data[Device.Message.Incoming.WIFI_STATUS], ConnectionStatus)
    assert received_data[Device.Message.Incoming.WIFI_STATUS] is ConnectionStatus.FAILED


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_run_wifi_disconnection(device):
    """
    Checks that Wi-Fi disconnection request processed correctly.

    Verifies that the device correctly handles Wi-Fi disconnection request.
    """
    # Store received data for later verification
    received_data = {
        Device.Message.Incoming.WIFI_STATUS: None,
        Device.Message.Incoming.ACTIVE_TRANSPORT: None
    }

    device.set_device_response_handlers({
        Device.Message.Incoming.WIFI_STATUS: [
            lambda status: received_data.update({Device.Message.Incoming.WIFI_STATUS: status})],
        Device.Message.Incoming.ACTIVE_TRANSPORT: [
            lambda transport: received_data.update({Device.Message.Incoming.ACTIVE_TRANSPORT: transport})]
    })

    device.set_wifi_connection(None)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    assert isinstance(received_data[Device.Message.Incoming.WIFI_STATUS], ConnectionStatus)
    assert received_data[Device.Message.Incoming.WIFI_STATUS] is ConnectionStatus.DISCONNECTED
    assert isinstance(received_data[Device.Message.Incoming.ACTIVE_TRANSPORT], Device.Transport)
    assert received_data[Device.Message.Incoming.ACTIVE_TRANSPORT] is Device.Transport.USB


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
@pytest.mark.parametrize("expected_value", [
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "NOCALL",
        "qth_locator": "XX00",
        "output_power": 30,
        "transmit_every": TransmitEvery.MINUTES_2,
        "active_band": Band.BAND_20M
    },
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "TEST01",
        "qth_locator": "AA00",
        "output_power": 10,
        "transmit_every": TransmitEvery.MINUTES_10,
        "active_band": Band.BAND_2M
    },
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "AB1CDE",
        "qth_locator": "JO01",
        "output_power": 20,
        "transmit_every": TransmitEvery.MINUTES_30,
        "active_band": Band.BAND_2200M
    },
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "W1AW",
        "qth_locator": "FN31",
        "output_power": 23,
        "transmit_every": TransmitEvery.MINUTES_60,
        "active_band": Band.BAND_40M
    },
    {
        "tx_mode": None,
        "tx_call": None,
        "qth_locator": None,
        "output_power": None,
        "transmit_every": None,
        "active_band": None
    }
])
def test_set_active_tx_mode(device, expected_value):
    """
    Checks that setting the active transmission mode processed correctly.

    Verifies that the device accepts and confirms the new active TX mode settings.
    """
    # Store received data for later verification
    received_data = {Device.Message.Incoming.ACTIVE_TX_MODE: None}

    device.set_device_response_handlers({
        Device.Message.Incoming.ACTIVE_TX_MODE: [
            lambda active_tx_mode: received_data.update({Device.Message.Incoming.ACTIVE_TX_MODE: active_tx_mode})]
    })

    # Create and send active transmission mode configuration
    activeTxMode = None if expected_value['tx_mode'] is None else ActiveTXMode(**expected_value)

    device.set_active_tx_mode(activeTxMode)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify all fields match
    assert isinstance(received_data[Device.Message.Incoming.ACTIVE_TX_MODE], ActiveTXMode)
    for key, value in expected_value.items():
        assert getattr(received_data[Device.Message.Incoming.ACTIVE_TX_MODE], key) == value


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
@pytest.mark.parametrize("cal_value", [-9999, 9999, -2000, 2000, 0])
def test_set_calibration_value(device, cal_value):
    """
    Checks that setting the calibration value processed correctly.

    Verifies that the device accepts and confirms the new calibration value settings.
    """
    # Store received data for later verification
    received_data = {Device.Message.Incoming.CAL_VALUE: None}

    device.set_device_response_handlers({
        Device.Message.Incoming.CAL_VALUE: [
            lambda value: received_data.update({Device.Message.Incoming.CAL_VALUE: value})]
    })

    device.set_calibration_value(cal_value)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    assert received_data[Device.Message.Incoming.CAL_VALUE] == cal_value


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
@pytest.mark.parametrize("connect_at_startup", [True, False])
def test_set_connect_at_startup(device, connect_at_startup):
    """
    Checks that setting the connect at startup value processed correctly.

    Verifies that the device accepts and confirms the new connect at startup value settings.
    """
    # Store received data for later verification
    received_data = {Device.Message.Incoming.WIFI_SSID_DATA: None}

    def on_wifi_ssid_data_received(received_connect_at_startup):
        received_data[Device.Message.Incoming.WIFI_SSID_DATA] = received_connect_at_startup

    device.set_device_response_handlers({
        Device.Message.Incoming.WIFI_SSID_DATA: [on_wifi_ssid_data_received]
    })

    device.set_ssid_connect_at_startup(connect_at_startup)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    assert isinstance(received_data[Device.Message.Incoming.WIFI_SSID_DATA], WiFiData)
    assert any([received_data[Device.Message.Incoming.WIFI_SSID_DATA].ssid])
    assert any([received_data[Device.Message.Incoming.WIFI_SSID_DATA].password])
    assert received_data[Device.Message.Incoming.WIFI_SSID_DATA].connect_at_startup == connect_at_startup


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
@pytest.mark.parametrize("calibration_frequency", [10.0, 15.5, 28.0, 28.9])
def test_gen_cal_frequency(device, calibration_frequency):
    """
    Checks that setting the calibration frequency processed correctly.

    Verifies that the device accepts and confirms the new calibration frequency settings.
    This test trigger a RF transmission functionality from the device!
    """
    # Store received data for later verification
    received_data = {
        Device.Message.Incoming.TX_STATUS:          None,
        Device.Message.Incoming.CAL_FREQ_GENERATED: None
    }

    device.set_device_response_handlers({
        Device.Message.Incoming.TX_STATUS:          [
            lambda status: received_data.update({Device.Message.Incoming.TX_STATUS: status})],
        Device.Message.Incoming.CAL_FREQ_GENERATED: [
            lambda status: received_data.update({Device.Message.Incoming.CAL_FREQ_GENERATED: status})]
    })

    device.gen_calibration_frequency(calibration_frequency)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data (calibration frequency generation activated)
    assert received_data[Device.Message.Incoming.TX_STATUS] is True
    assert received_data[Device.Message.Incoming.CAL_FREQ_GENERATED] is True

    device.gen_calibration_frequency(None)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data (calibration frequency generation stopped)
    assert received_data[Device.Message.Incoming.TX_STATUS] is False
    assert received_data[Device.Message.Incoming.CAL_FREQ_GENERATED] is False


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_incorrect_request_type(device):
    """
    Checks that incorrect request type processed correctly.

    Verifies that the device correctly handles incorrect request type.
    """
    # Store received data for later verification
    received_data = {Device.Message.Incoming.PROTOCOL_ERROR: None}

    device.set_device_response_handlers({
        Device.Message.Incoming.PROTOCOL_ERROR: [
            lambda error: received_data.update({Device.Message.Incoming.PROTOCOL_ERROR: error})]
    })

    class DummyMessageType(Enum):
        INVALID_TYPE = "INVALID_TYPE"

    device._put(Device.Message(DummyMessageType.INVALID_TYPE))

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    assert received_data[Device.Message.Incoming.PROTOCOL_ERROR] == "Invalid message type!"


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
def test_incorrect_message(device):
    """
    Checks that non JSON messages are processed correctly.

    Verifies that the device correctly handles non JSON messages.
    """
    # Store received data for later verification
    received_data = {Device.Message.Incoming.PROTOCOL_ERROR: None}

    device.set_device_response_handlers({
        Device.Message.Incoming.PROTOCOL_ERROR: [
            lambda error: received_data.update({Device.Message.Incoming.PROTOCOL_ERROR: error})]
    })

    # Send a non-JSON message + line ending symbol directly via serial transport
    # This bypasses the usual message encoding/decoding by Device class
    device.serial_transport.send("UNEXPECTED NON-JSON MESSAGE" + "\n")

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify received data
    assert received_data[Device.Message.Incoming.PROTOCOL_ERROR] == "Non-JSON data received!"
