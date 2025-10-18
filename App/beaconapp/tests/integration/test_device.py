import pytest
import serial.tools.list_ports
import time

from beaconapp.device import Device


# VID and PID for ESP32-C3
ESP32_C3_VID = 0x303A
ESP32_C3_PID = 0x1001


def find_esp32_device():
    """
    Find ESP32-C3 device port by VID/PID.
    Returns device port name if found, None otherwise.
    """
    for port in serial.tools.list_ports.comports():
        if port.vid == ESP32_C3_VID and port.pid == ESP32_C3_PID:
            return port.device
    return None


@pytest.fixture(scope="function")
def device():
    """
    Create a Device instance for testing.
    Each test gets a fresh instance.
    Automatically disconnects after test completes.
    """
    device_instance = Device()
    yield device_instance
    # Cleanup: ensure device is disconnected after each test
    device_instance.disconnect()
    # Ensure serial port is released before next test
    time.sleep(1)


@pytest.fixture
def wait_for_connection():
    """
    Fixture that waits for device to be fully connected.
    """
    def _wait(device_instance, timeout=10.0):
        """
        Wait for device to connect with timeout.
        Waits for active transport to be established.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if device_instance.active_transport is not None:
                # Additional wait to ensure stability
                time.sleep(1.0)
                return True
            time.sleep(0.2)
        return False
    return _wait


@pytest.mark.integration
@pytest.mark.skipif(not find_esp32_device(), reason="WSPR-beacon device not connected!")
def test_serial_connection_and_dtr_rts_control(device, wait_for_connection):
    """
    Checks that DTR/RTS functionality initialized correctly and didn't cause device reset
    after closing serial connection.

    Note: Manual verification (power on LED inspection) may be required to confirm device did not reset.
    """
    device.connect()

    # Wait for connection to be established
    assert wait_for_connection(device)
    # Verify that serial transport determined correctly
    assert device.active_transport is Device.Transport.USB

    # Small delay to ensure serial port is ready
    time.sleep(1.0)

    # Assert: Check that DTR/RTS are not controlled for USB connection
    serial_port = device.serial_transport.serial_port
    assert serial_port is not None
    assert serial_port.is_open
    assert serial_port.dtr is None
    assert serial_port.rts is None

    device.disconnect()

    print("[INFO] Please verify manually that device did not reset (check power on LED)!")


@pytest.mark.integration
@pytest.mark.skipif(not find_esp32_device(), reason="WSPR-beacon device not connected!")
def test_reconnection_after_disconnect(device, wait_for_connection):
    """
    Checks that device can reconnect without issues.
    """
    # First device connection
    device.connect()

    # Verify first connection
    assert wait_for_connection(device)
    assert device.active_transport is Device.Transport.USB

    # Terminate device connection
    device.disconnect()

    # Create new Device instance for device reconnection
    reconnected_device = Device()
    reconnected_device.connect()

    # Verify reconnection
    assert wait_for_connection(reconnected_device)
    assert reconnected_device.active_transport is Device.Transport.USB

    # Terminate reconnected device
    reconnected_device.disconnect()


@pytest.mark.integration
@pytest.mark.skipif(not find_esp32_device(), reason="WSPR-beacon device not connected!")
def test_device_info_request_after_connection(device, wait_for_connection):
    """
    Checks that device info can be requested after connection is established.

    Verifies that all expected message types are received from device:
    - ACTIVE_TX_MODE
    - WIFI_SSID_DATA
    - WIFI_STATUS
    - ACTIVE_TRANSPORT
    - GPS_STATUS
    - CAL_VALUE
    - CAL_STATUS
    - FIRMWARE_INFO
    - HARDWARE_INFO
    """
    # Arrange: Set up flags to track all expected responses
    responses = {
        'ACTIVE_TX_MODE': False,
        'WIFI_SSID_DATA': False,
        'WIFI_STATUS': False,
        'ACTIVE_TRANSPORT': False,
        'GPS_STATUS': False,
        'CAL_VALUE': False,
        'CAL_STATUS': False,
        'FIRMWARE_INFO': False,
        'HARDWARE_INFO': False,
    }

    # Register callbacks for all response types
    device.set_device_response_handlers({
        Device.Message.Incoming.ACTIVE_TX_MODE:     [lambda data: responses.update(ACTIVE_TX_MODE=True)],
        Device.Message.Incoming.WIFI_SSID_DATA:     [lambda data: responses.update(WIFI_SSID_DATA=True)],
        Device.Message.Incoming.WIFI_STATUS:        [lambda data: responses.update(WIFI_STATUS=True)],
        Device.Message.Incoming.ACTIVE_TRANSPORT:   [lambda data: responses.update(ACTIVE_TRANSPORT=True)],
        Device.Message.Incoming.GPS_STATUS:         [lambda data: responses.update(GPS_STATUS=True)],
        Device.Message.Incoming.CAL_VALUE:          [lambda data: responses.update(CAL_VALUE=True)],
        Device.Message.Incoming.CAL_STATUS:         [lambda data: responses.update(CAL_STATUS=True)],
        Device.Message.Incoming.FIRMWARE_INFO:      [lambda data: responses.update(FIRMWARE_INFO=True)],
        Device.Message.Incoming.HARDWARE_INFO:      [lambda data: responses.update(HARDWARE_INFO=True)],
    })

    # Connect and request device info
    device.connect()
    assert wait_for_connection(device)
    device.get_device_info()

    # Wait for device response
    time.sleep(2.0)

    # Assert: We should have received all expected responses
    assert responses['ACTIVE_TX_MODE']
    assert responses['WIFI_SSID_DATA']
    assert responses['WIFI_STATUS']
    assert responses['ACTIVE_TRANSPORT']
    assert responses['GPS_STATUS']
    assert responses['CAL_VALUE']
    assert responses['CAL_STATUS']
    assert responses['FIRMWARE_INFO']
    assert responses['HARDWARE_INFO']
