import pytest
import serial.tools.list_ports
import time
import threading

from beaconapp.device import Device
from beaconapp.data_wrappers import ActiveTXMode, Band, TransmitEvery, TXMode


# VID and PID for ESP32-C3
DEVICE_VID = 0x303A
DEVICE_PID = 0x1001


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
    time.sleep(2.0)
    # Verify first connection is via USB
    assert device.active_transport is Device.Transport.USB
    # Terminate device connection
    device.disconnect()

    # Verify transport is reset after disconnect
    assert device.active_transport is None

    # Wait for the serial port to be fully released
    time.sleep(2.0)

    # Second device connection
    device.connect()
    time.sleep(2.0)
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
    time.sleep(2.0)
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
    time.sleep(2.0)

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
def test_set_active_tx_mode(device):
    """
    Checks that setting the active transmission mode processed correctly.

    Verifies that the device accepts and confirms the new active TX mode settings.
    """
    # Store received data for later verification
    received_data = {'active_tx_mode': None}

    def on_active_tx_mode_received(active_tx_mode):
        received_data['active_tx_mode'] = active_tx_mode

    device.set_device_response_handlers({
        Device.Message.Incoming.ACTIVE_TX_MODE: [on_active_tx_mode_received]
    })

    # Create and send active transmission mode configuration
    activeTxMode = ActiveTXMode()
    activeTxMode.tx_mode = TXMode.WSPR
    activeTxMode.tx_call = "NOCALL"
    activeTxMode.qth_locator = "XX00"
    activeTxMode.output_power = 5
    activeTxMode.transmit_every = TransmitEvery.MINUTES_2
    activeTxMode.active_band = Band.BAND_20M

    device.set_active_tx_mode(activeTxMode)

    # Wait for device response
    time.sleep(3.0)

    # Verify that data was received
    assert received_data['active_tx_mode'] is not None
    # Verify that received data matches sent data
    assert received_data['active_tx_mode'].tx_mode == activeTxMode.tx_mode
    assert received_data['active_tx_mode'].tx_call == activeTxMode.tx_call
    assert received_data['active_tx_mode'].qth_locator == activeTxMode.qth_locator
    assert received_data['active_tx_mode'].output_power == activeTxMode.output_power
    assert received_data['active_tx_mode'].transmit_every == activeTxMode.transmit_every
    assert received_data['active_tx_mode'].active_band == activeTxMode.active_band
