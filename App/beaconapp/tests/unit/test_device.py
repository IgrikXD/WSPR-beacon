import pytest
import json

from beaconapp.device import Device
from beaconapp.data_wrappers import ActiveTXMode, Band, TransmitEvery, TXMode
from beaconapp.data_wrappers import ConnectionStatus, WiFiData, WiFiCredentials


@pytest.mark.parametrize(
    "connected_transports, requested_transport, priority, expected_active",
    [
        # No transports connected, requested=USB => result=None
        (set(), Device.Transport.USB,
         [Device.Transport.WIFI, Device.Transport.USB], None),
        # No transports connected, requested=WIFI => result=None
        (set(), Device.Transport.WIFI,
         [Device.Transport.WIFI, Device.Transport.USB], None),
        # Only USB connected, requested=USB => result=USB
        ({Device.Transport.USB}, Device.Transport.USB,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.USB),
        # Only USB connected, requested=WIFI => result=USB
        ({Device.Transport.USB}, Device.Transport.WIFI,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.USB),
        # Only WIFI connected, requested=USB => result=WIFI
        ({Device.Transport.WIFI}, Device.Transport.USB,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.WIFI),
        # Only WIFI connected, requested=WIFI => result=WIFI
        ({Device.Transport.WIFI}, Device.Transport.WIFI,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.WIFI),
        # WIFI & USB both connected, requested=WIFI => priority=[WIFI,USB] => result=WIFI
        ({Device.Transport.USB, Device.Transport.WIFI}, Device.Transport.WIFI,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.WIFI),
        # WIFI & USB both connected, requested=WIFI, priority=[USB,WIFI] => result=WIFI
        ({Device.Transport.USB, Device.Transport.WIFI}, Device.Transport.WIFI,
         [Device.Transport.USB, Device.Transport.WIFI], Device.Transport.WIFI),
        # WIFI & USB both connected, requested=USB => priority=[WIFI,USB] => result=USB
        ({Device.Transport.USB, Device.Transport.WIFI}, Device.Transport.USB,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.USB),
        # WIFI & USB both connected, requested=USB => priority=[USB,WIFI] => result=USB
        ({Device.Transport.USB, Device.Transport.WIFI}, Device.Transport.USB,
         [Device.Transport.USB, Device.Transport.WIFI], Device.Transport.USB),
        # WIFI & USB both connected, requested=None, priority=[WIFI,USB] => result=WIFI
        ({Device.Transport.USB, Device.Transport.WIFI}, None,
         [Device.Transport.WIFI, Device.Transport.USB], Device.Transport.WIFI),
        # WIFI & USB both connected, requested=None, priority=[USB,WIFI] => result=USB
        ({Device.Transport.USB, Device.Transport.WIFI}, None,
         [Device.Transport.USB, Device.Transport.WIFI], Device.Transport.USB),
    ]
)
@pytest.mark.unit
def test_decide_active_transport(connected_transports, requested_transport, priority, expected_active):
    """
    Checks that _decide_active_transport chooses the correct active transport
    based on _requested_transport, connected_transports, and transport_priority.
    """
    device = Device()
    device._connected_transports = connected_transports
    device._requested_transport = requested_transport
    device.transport_priority = priority

    device._decide_active_transport()

    assert device.active_transport == expected_active


@pytest.mark.parametrize(
    "incoming_json, expected_type, expected_data",
    [
        # Incoming: ACTIVE_TRANSPORT: USB
        ({"type": "ACTIVE_TRANSPORT", "data": "USB"},
         Device.Message.Incoming.ACTIVE_TRANSPORT, Device.Transport.USB),
        # Incoming: ACTIVE_TRANSPORT: Wi-Fi
        ({"type": "ACTIVE_TRANSPORT", "data": "Wi-Fi"},
         Device.Message.Incoming.ACTIVE_TRANSPORT, Device.Transport.WIFI),
        # Incoming: ACTIVE_TX_MODE: ActiveTXMode
        ({"type": "ACTIVE_TX_MODE",
          "data": {
              "tx_mode": 1,
              "tx_call": "N0CALL",
              "qth_locator": "XX00",
              "output_power": 23,
              "transmit_every": 10,
              "active_band": 2200
            }
          },
         Device.Message.Incoming.ACTIVE_TX_MODE,
         ActiveTXMode(TXMode.WSPR, "N0CALL", "XX00", 23, TransmitEvery.MINUTES_10, Band.BAND_2200M)),
        # Incoming: ACTIVE_TX_MODE: empty ActiveTXMode
        ({"type": "ACTIVE_TX_MODE", "data": None},
         Device.Message.Incoming.ACTIVE_TX_MODE,
         ActiveTXMode()),
        # Incoming: CAL_FREQ_GENERATED: True
        ({"type": "CAL_FREQ_GENERATED", "data": True},
         Device.Message.Incoming.CAL_FREQ_GENERATED, True),
        # Incoming: CAL_FREQ_GENERATED: False
        ({"type": "CAL_FREQ_GENERATED", "data": False},
         Device.Message.Incoming.CAL_FREQ_GENERATED, False),
        # Incoming: CAL_STATUS: False
        ({"type": "CAL_STATUS", "data": False},
         Device.Message.Incoming.CAL_STATUS, False),
        # Incoming: CAL_STATUS: True
        ({"type": "CAL_STATUS", "data": True},
         Device.Message.Incoming.CAL_STATUS, True),
        # Incoming: CAL_VALUE: negative int
        ({"type": "CAL_VALUE", "data": -2000},
         Device.Message.Incoming.CAL_VALUE, -2000),
        # Incoming: CAL_VALUE: positive int
        ({"type": "CAL_VALUE", "data": 2000},
         Device.Message.Incoming.CAL_VALUE, 2000),
        # Incoming: FIRMWARE_INFO: str
        ({"type": "FIRMWARE_INFO", "data": -2000},
         Device.Message.Incoming.FIRMWARE_INFO, -2000),
        # Incoming: FIRMWARE_INFO: str
        ({"type": "FIRMWARE_INFO", "data": "3.0"},
         Device.Message.Incoming.FIRMWARE_INFO, "3.0"),
        # Incoming: GPS_STATUS: True
        ({"type": "GPS_STATUS", "data": True},
         Device.Message.Incoming.GPS_STATUS, True),
        # Incoming: GPS_STATUS: False
        ({"type": "GPS_STATUS", "data": False},
         Device.Message.Incoming.GPS_STATUS, False),
        # Incoming: HARDWARE_INFO: str
        ({"type": "HARDWARE_INFO", "data": "3.0"},
         Device.Message.Incoming.HARDWARE_INFO, "3.0"),
        # Incoming: QTH_LOCATOR: str
        ({"type": "QTH_LOCATOR", "data": "XX00"},
         Device.Message.Incoming.QTH_LOCATOR, "XX00"),
        # Incoming: SELF_CHECK_ACTION: str
        ({"type": "SELF_CHECK_ACTION", "data": "- LEDs initialized! -"},
         Device.Message.Incoming.SELF_CHECK_ACTION, "- LEDs initialized! -"),
        # Incoming: SELF_CHECK_ACTIVE: True
        ({"type": "SELF_CHECK_ACTIVE", "data": True},
         Device.Message.Incoming.SELF_CHECK_ACTIVE, True),
        # Incoming: SELF_CHECK_ACTIVE: False
        ({"type": "SELF_CHECK_ACTIVE", "data": False},
         Device.Message.Incoming.SELF_CHECK_ACTIVE, False),
        # Incoming: SELF_CHECK_STATUS: True
        ({"type": "SELF_CHECK_STATUS", "data": True},
         Device.Message.Incoming.SELF_CHECK_STATUS, True),
        # Incoming: SELF_CHECK_STATUS: False
        ({"type": "SELF_CHECK_STATUS", "data": False},
         Device.Message.Incoming.SELF_CHECK_STATUS, False),
        # Incoming: TX_ACTION_STATUS: str
        ({"type": "TX_ACTION_STATUS", "data": "- No active mode -"},
         Device.Message.Incoming.TX_ACTION_STATUS, "- No active mode -"),
        # Incoming: TX_STATUS: True
        ({"type": "TX_STATUS", "data": True},
         Device.Message.Incoming.TX_STATUS, True),
        # Incoming: TX_STATUS: False
        ({"type": "TX_STATUS", "data": False},
         Device.Message.Incoming.TX_STATUS, False),
        # Incoming: WIFI_SSID_DATA: WifiData(..., "connect_at_startup": False)
        ({"type": "WIFI_SSID_DATA", "data": {"ssid": "Name", "password": "Pass", "connect_at_startup": False}},
         Device.Message.Incoming.WIFI_SSID_DATA, WiFiData("Name", "Pass", False)),
        # Incoming: WIFI_SSID_DATA: WifiData(..., "connect_at_startup": True)
        ({"type": "WIFI_SSID_DATA", "data": {"ssid": "Name", "password": "Pass", "connect_at_startup": True}},
         Device.Message.Incoming.WIFI_SSID_DATA, WiFiData("Name", "Pass", True)),
        # Incoming: WIFI_STATUS: ConnectionStatus("connected")
        ({"type": "WIFI_STATUS", "data": "connected"},
         Device.Message.Incoming.WIFI_STATUS, ConnectionStatus("connected")),
        # Incoming: WIFI_STATUS: ConnectionStatus("disconnected")
        ({"type": "WIFI_STATUS", "data": "disconnected"},
         Device.Message.Incoming.WIFI_STATUS, ConnectionStatus("disconnected")),
        # Incoming: WIFI_STATUS: ConnectionStatus("initiated")
        ({"type": "WIFI_STATUS", "data": "initiated"},
         Device.Message.Incoming.WIFI_STATUS, ConnectionStatus("initiated")),
        # Incoming: WIFI_STATUS: ConnectionStatus("failed")
        ({"type": "WIFI_STATUS", "data": "failed"},
         Device.Message.Incoming.WIFI_STATUS, ConnectionStatus("failed")),
    ]
)
@pytest.mark.unit
def test_decode_device_message(incoming_json, expected_type, expected_data):
    """
    Checks that _decode_device_message correctly decodes JSON into a Device.Message
    with the right type and data object.
    """
    device = Device()
    decoded_message = device._decode_device_message(json.dumps(incoming_json))

    assert decoded_message.type == expected_type
    assert decoded_message.data == expected_data


@pytest.mark.parametrize(
    "msg_type, data, expected_json_substring",
    [
        # Outgoing: GEN_CAL_FREQUENCY: float
        (Device.Message.Outgoing.GEN_CAL_FREQUENCY, 2850000000,
         '{"type": "GEN_CAL_FREQUENCY", "data": 2850000000}'),
        # Outgoing: GEN_CAL_FREQUENCY: None
        (Device.Message.Outgoing.GEN_CAL_FREQUENCY, None,
         '{"type": "GEN_CAL_FREQUENCY", "data": null}'),
        # Outgoing: GET_DEVICE_INFO: None
        (Device.Message.Outgoing.GET_DEVICE_INFO, None,
         '{"type": "GET_DEVICE_INFO", "data": null}'),
        # Outgoing: RUN_SELF_CHECK: None
        (Device.Message.Outgoing.RUN_SELF_CHECK, None,
         '{"type": "RUN_SELF_CHECK", "data": null}'),
        # Outgoing: RUN_WIFI_CONNECTION: WiFiCredentials
        (Device.Message.Outgoing.RUN_WIFI_CONNECTION, WiFiCredentials("Name", "Pass"),
         '{"type": "RUN_WIFI_CONNECTION", "data": {"ssid": "Name", "password": "Pass"}}'),
        # Outgoing: RUN_WIFI_CONNECTION: None
        (Device.Message.Outgoing.RUN_WIFI_CONNECTION, None,
         '{"type": "RUN_WIFI_CONNECTION", "data": null}'),
        # Outgoing: SET_ACTIVE_TX_MODE: ActiveTXMode
        (
            Device.Message.Outgoing.SET_ACTIVE_TX_MODE,
            ActiveTXMode(TXMode.WSPR, "N0CALL", "XX00", 23, TransmitEvery.MINUTES_10, Band.BAND_2200M),
            (
                '{'
                '"type": "SET_ACTIVE_TX_MODE", '
                '"data": {"tx_mode": 1, '
                '"tx_call": "N0CALL", '
                '"qth_locator": "XX00", '
                '"output_power": 23, '
                '"transmit_every": 10, '
                '"active_band": 2200}'
                '}'
            )
        ),
        # Outgoing: SET_ACTIVE_TX_MODE: None
        (Device.Message.Outgoing.SET_ACTIVE_TX_MODE, None,
         '{"type": "SET_ACTIVE_TX_MODE", "data": null}'),
        # Outgoing: SET_CAL_VALUE: positive int
        (Device.Message.Outgoing.SET_CAL_VALUE, 2000,
         '{"type": "SET_CAL_VALUE", "data": 2000}'),
        # Outgoing: SET_CAL_VALUE: negative int
        (Device.Message.Outgoing.SET_CAL_VALUE, -2000,
         '{"type": "SET_CAL_VALUE", "data": -2000}'),
        # Outgoing: SET_SSID_CONNECT_AT_STARTUP: True
        (Device.Message.Outgoing.SET_SSID_CONNECT_AT_STARTUP, True,
         '{"type": "SET_SSID_CONNECT_AT_STARTUP", "data": true}'),
        # Outgoing: SET_SSID_CONNECT_AT_STARTUP: False
        (Device.Message.Outgoing.SET_SSID_CONNECT_AT_STARTUP, False,
         '{"type": "SET_SSID_CONNECT_AT_STARTUP", "data": false}'),
    ]
)
@pytest.mark.unit
def test_encode_device_message(msg_type, data, expected_json_substring):
    """
    Checks that _encode_device_message produces valid JSON containing the correct type
    and data fields.
    """
    device = Device()
    encoded_str = device._encode_device_message(Device.Message(msg_type, data))

    assert expected_json_substring in encoded_str


def dummy_handler(x):
    """
    A simple handler function for testing.
    """
    return x


def dummy_handler2(x):
    """
    A second handler function for testing difference in callbacks.
    It also returns the input argument as is.
    """
    return x


@pytest.mark.parametrize(
    "existing_handlers, new_handlers, expected_amount",
    [
        # No existing handlers, add one
        (
            {},
            {Device.Message.Incoming.TX_STATUS: dummy_handler},
            1
        ),
        # No existing handlers, add the same handler twice
        (
            {},
            {Device.Message.Incoming.TX_STATUS: [dummy_handler, dummy_handler]},
            1,
        ),
        # Add the existing handler
        (
            {Device.Message.Incoming.TX_STATUS: [dummy_handler]},
            {Device.Message.Incoming.TX_STATUS: [dummy_handler]},
            1,
        ),
        # Add a new handler with different message types
        (
            {Device.Message.Incoming.TX_STATUS: [dummy_handler]},
            {Device.Message.Incoming.WIFI_STATUS: [dummy_handler]},
            2,
        ),
        # Add a new handler with the same message type but a different handler
        (
            {Device.Message.Incoming.TX_STATUS: [dummy_handler]},
            {Device.Message.Incoming.TX_STATUS: [dummy_handler2]},
            2,
        ),
    ]
)
@pytest.mark.unit
def test_set_device_response_handlers(existing_handlers, new_handlers, expected_amount):
    """
    Checks that set_device_response_handlers attaches new callbacks without duplication.
    """
    device = Device()
    # Emulate that the device already has some callbacks registered.
    device.set_device_response_handlers(existing_handlers)

    device.set_device_response_handlers(new_handlers)

    # Verify that the total number of handlers matches the expected count
    #  (i.e., duplicates aren't added).
    total_handlers = sum(len(handlers) for handlers in device.mapped_callbacks.values())
    assert total_handlers == expected_amount


@pytest.mark.parametrize(
    "initial, disconnected, expected_active, expected_connected",
    [
        # USB only connected, disconnect USB => no transports
        ({Device.Transport.USB}, Device.Transport.USB, None, set()),
        # WIFI only connected, disconnect WIFI => no transports
        ({Device.Transport.WIFI}, Device.Transport.WIFI, None, set()),
        # USB & WIFI connected, disconnect WIFI => still have USB
        ({Device.Transport.USB, Device.Transport.WIFI},
         Device.Transport.WIFI, Device.Transport.USB, {Device.Transport.USB}),
        # USB & WIFI connected, disconnect USB => lose everything
        ({Device.Transport.USB, Device.Transport.WIFI},
         Device.Transport.USB, None, set()),
    ]
)
@pytest.mark.unit
def test_on_transport_disconnected(initial, disconnected, expected_active, expected_connected):
    """
    Checks that _on_transport_disconnected properly updates _connected_transports
    and calls _decide_active_transport, considering the special rule:
    "If USB is disconnected, assume device power is lost, thus remove Wi-Fi as well."
    """
    device = Device()
    device._connected_transports = set(initial)
    device.active_transport = next(iter(initial)) if initial else None
    device._requested_transport = device.active_transport

    device._on_transport_disconnected(disconnected)

    assert device._connected_transports == expected_connected
    assert device.active_transport == expected_active
