import pytest
import serial.tools.list_ports
import time
import threading

from beaconapp.device import Device
from beaconapp.data_wrappers import ActiveTXMode, Band, TransmitEvery, TXMode


# VID and PID for ESP32-C3
DEVICE_VID = 0x303A
DEVICE_PID = 0x1001

# Device response timeout in seconds
DEVICE_RESPONSE_TIMEOUT = 2.5


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
        Device.Message.Incoming.ACTIVE_TX_MODE:     False,
        Device.Message.Incoming.WIFI_SSID_DATA:     False,
        Device.Message.Incoming.WIFI_STATUS:        False,
        Device.Message.Incoming.ACTIVE_TRANSPORT:   False,
        Device.Message.Incoming.GPS_STATUS:         False,
        Device.Message.Incoming.CAL_VALUE:          False,
        Device.Message.Incoming.CAL_STATUS:         False,
        Device.Message.Incoming.FIRMWARE_INFO:      False,
        Device.Message.Incoming.HARDWARE_INFO:      False
    }

    # Register callbacks for all response types
    device.set_device_response_handlers({
        Device.Message.Incoming.ACTIVE_TX_MODE:     [
            lambda _: responses.update({Device.Message.Incoming.ACTIVE_TX_MODE: True})],
        Device.Message.Incoming.WIFI_SSID_DATA:     [
            lambda _: responses.update({Device.Message.Incoming.WIFI_SSID_DATA: True})],
        Device.Message.Incoming.WIFI_STATUS:        [
            lambda _: responses.update({Device.Message.Incoming.WIFI_STATUS: True})],
        Device.Message.Incoming.ACTIVE_TRANSPORT:   [
            lambda _: responses.update({Device.Message.Incoming.ACTIVE_TRANSPORT: True})],
        Device.Message.Incoming.GPS_STATUS:         [
            lambda _: responses.update({Device.Message.Incoming.GPS_STATUS: True})],
        Device.Message.Incoming.CAL_VALUE:          [
            lambda _: responses.update({Device.Message.Incoming.CAL_VALUE: True})],
        Device.Message.Incoming.CAL_STATUS:         [
            lambda _: responses.update({Device.Message.Incoming.CAL_STATUS: True})],
        Device.Message.Incoming.FIRMWARE_INFO:      [
            lambda _: responses.update({Device.Message.Incoming.FIRMWARE_INFO: True})],
        Device.Message.Incoming.HARDWARE_INFO:      [
            lambda _: responses.update({Device.Message.Incoming.HARDWARE_INFO: True})
        ]
    })

    # device.connect()
    device.get_device_info()

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Assert: We should have received all expected responses
    assert responses[Device.Message.Incoming.ACTIVE_TX_MODE]
    assert responses[Device.Message.Incoming.WIFI_SSID_DATA]
    assert responses[Device.Message.Incoming.WIFI_STATUS]
    assert responses[Device.Message.Incoming.ACTIVE_TRANSPORT]
    assert responses[Device.Message.Incoming.GPS_STATUS]
    assert responses[Device.Message.Incoming.CAL_VALUE]
    assert responses[Device.Message.Incoming.CAL_STATUS]
    assert responses[Device.Message.Incoming.FIRMWARE_INFO]
    assert responses[Device.Message.Incoming.HARDWARE_INFO]


@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
@pytest.mark.parametrize("expected_value", [
    {
        "tx_mode": None,
        "tx_call": None,
        "qth_locator": None,
        "output_power": None,
        "transmit_every": None,
        "active_band": None
    },
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "NOCALL",
        "qth_locator": "XX00",
        "output_power": 23,
        "transmit_every": TransmitEvery.MINUTES_2,
        "active_band": Band.BAND_20M
    },
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "TEST01",
        "qth_locator": "AA00",
        "output_power": 10,
        "transmit_every": TransmitEvery.MINUTES_10,
        "active_band": Band.BAND_40M
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
        "output_power": 30,
        "transmit_every": TransmitEvery.MINUTES_60,
        "active_band": Band.BAND_2M
    },
])
def test_set_active_tx_mode(device, expected_value):
    """
    Checks that setting the active transmission mode processed correctly.

    Verifies that the device accepts and confirms the new active TX mode settings.
    """
    # Store received data for later verification
    received_data = {'active_tx_mode': None, 'is_received': False}

    def on_active_tx_mode_received(active_tx_mode):
        received_data['active_tx_mode'] = active_tx_mode
        received_data['is_received'] = True

    device.set_device_response_handlers({
        Device.Message.Incoming.ACTIVE_TX_MODE: [on_active_tx_mode_received]
    })

    # Create and send active transmission mode configuration
    activeTxMode = None if expected_value['tx_mode'] is None else ActiveTXMode(**expected_value)

    device.set_active_tx_mode(activeTxMode)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Response received check
    assert received_data['is_received'] is True
    # When expected_value is not empty, verify response was received
    assert received_data['active_tx_mode'] is not None
    # Verify all fields match
    for key, value in expected_value.items():
        assert getattr(received_data['active_tx_mode'], key) == value
        

@pytest.mark.integration
@pytest.mark.skipif(not find_device(), reason="WSPR-beacon device not connected!")
@pytest.mark.parametrize("cal_value", [0, 2000, -2000, -9999, 9999])
def test_set_calibration_value(device, cal_value):
    """
    Checks that setting the calibration value processed correctly.

    Verifies that the device accepts and confirms the new calibration value settings.
    """
    # Store received data for later verification
    received_data = {'cal_value': None}

    def on_cal_value_received(received_cal_value):
        received_data['cal_value'] = received_cal_value

    device.set_device_response_handlers({
        Device.Message.Incoming.CAL_VALUE: [on_cal_value_received]
    })

    device.set_calibration_value(cal_value)

    # Wait for device response
    time.sleep(DEVICE_RESPONSE_TIMEOUT)

    # Verify that received data matches sent data
    assert received_data['cal_value'] == cal_value