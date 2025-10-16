import pytest

from beaconapp.data_wrappers import ActiveTXMode, Band, TransmitEvery, TXMode, WiFiCredentials, WiFiData


# Parameterized tests for ActiveTXMode defaults
@pytest.mark.parametrize("input_value, expected_value", [
    (
        {},
        {
            "tx_mode": None,
            "tx_call": None,
            "qth_locator": None,
            "output_power": None,
            "transmit_every": None,
            "active_band": None
        }
    )
])
def test_active_tx_mode_defaults_param(input_value, expected_value):
    active_tx_mode = ActiveTXMode(**input_value)
    result = {
        "tx_mode": active_tx_mode.tx_mode,
        "tx_call": active_tx_mode.tx_call,
        "qth_locator": active_tx_mode.qth_locator,
        "output_power": active_tx_mode.output_power,
        "transmit_every": active_tx_mode.transmit_every,
        "active_band": active_tx_mode.active_band,
    }
    assert result == expected_value


# Parameterized test for ActiveTXMode.clear() method
@pytest.mark.parametrize("input_value", [
    {
        "tx_mode": TXMode.WSPR,
        "tx_call": "N0CALL",
        "qth_locator": "XX00",
        "output_power": 23,
        "transmit_every": TransmitEvery.MINUTES_10,
        "active_band": Band.BAND_2200M
    }
])
def test_active_tx_mode_clear_param(input_value):
    active_tx_mode = ActiveTXMode(**input_value)
    active_tx_mode.clear()
    # After calling ActiveTXMode.clear(), all fields should be reset to defaults
    assert active_tx_mode.tx_mode is None
    assert active_tx_mode.tx_call is None
    assert active_tx_mode.qth_locator is None
    assert active_tx_mode.output_power is None
    assert active_tx_mode.transmit_every is None
    assert active_tx_mode.active_band is None


# Parameterized tests for ActiveTXMode.to_json() method
@pytest.mark.parametrize("input_value, expected_value", [
    (
        # Without tx_mode set
        {
            "tx_call": "N0CALL",
            "qth_locator": "XX00",
            "output_power": 23,
            "transmit_every": TransmitEvery.MINUTES_10,
            "active_band": Band.BAND_2200M
        },
        {
            "tx_mode": None,
            "tx_call": "N0CALL",
            "qth_locator": "XX00",
            "output_power": 23,
            "transmit_every": 10,
            "active_band": 2200
        }
    ),
    (
        # With tx_mode set
        {
            "tx_mode": TXMode.WSPR,
            "tx_call": "N0CALL",
            "qth_locator": "XX00",
            "output_power": 23,
            "transmit_every": TransmitEvery.MINUTES_10,
            "active_band": Band.BAND_2200M
        },
        {
            "tx_mode": 1,
            "tx_call": "N0CALL",
            "qth_locator": "XX00",
            "output_power": 23,
            "transmit_every": 10,
            "active_band": 2200
        }
    )
])
def test_active_tx_mode_to_json_param(input_value, expected_value):
    active_tx_mode = ActiveTXMode(**input_value)
    assert active_tx_mode.to_json() == expected_value


# Parameterized tests for ActiveTXMode.from_json() method
@pytest.mark.parametrize("json_data, expected_value", [
    (
        {},  # Empty dictionary should yield default values
        {
            "tx_mode": None,
            "tx_call": None,
            "qth_locator": None,
            "output_power": None,
            "transmit_every": None,
            "active_band": None
        }
    ),
    (
        {
            "tx_mode": 1,
            "tx_call": "N0CALL",
            "qth_locator": "XX00",
            "output_power": 23,
            "transmit_every": 10,
            "active_band": 2200,
        },
        {
            "tx_mode": TXMode.WSPR,
            "tx_call": "N0CALL",
            "qth_locator": "XX00",
            "output_power": 23,
            "transmit_every": TransmitEvery.MINUTES_10,
            "active_band": Band.BAND_2200M
        }
    )
])
def test_active_tx_mode_from_json_param(json_data, expected_value):
    active_tx_mode = ActiveTXMode.from_json(json_data)
    assert active_tx_mode.tx_mode == expected_value["tx_mode"]
    assert active_tx_mode.tx_call == expected_value["tx_call"]
    assert active_tx_mode.qth_locator == expected_value["qth_locator"]
    assert active_tx_mode.output_power == expected_value["output_power"]
    assert active_tx_mode.transmit_every == expected_value["transmit_every"]
    assert active_tx_mode.active_band == expected_value["active_band"]


# Parameterized tests for WiFiCredentials.to_json()
@pytest.mark.parametrize("ssid, password", [
    ("Name", "secret"),
    ("TestSSID", "TestPass"),
])
def test_wifi_credentials_to_json_param(ssid, password):
    wifi = WiFiCredentials(ssid=ssid, password=password)
    expected_value = {
        "ssid": ssid,
        "password": password,
    }
    assert wifi.to_json() == expected_value


# Parameterized tests for WiFiData.from_json()
@pytest.mark.parametrize("json_data, expected_value", [
    (
        {
            "ssid": "Name",
            "password": "secret",
            "connect_at_startup": True,
        },
        {
            "ssid": "Name",
            "password": "secret",
            "connect_at_startup": True,
        }
    ),
    (
        {
            "ssid": "TestSSID",
            "password": "TestPass",
            "connect_at_startup": False,
        },
        {
            "ssid": "TestSSID",
            "password": "TestPass",
            "connect_at_startup": False,
        }
    ),
    (
        {},  # Empty dictionary should yield default values
        {
            "ssid": None,
            "password": None,
            "connect_at_startup": False,
        }
    )
])
def test_wifi_data_from_json_param(json_data, expected_value):
    wifi_data = WiFiData.from_json(json_data)
    assert wifi_data.ssid == expected_value["ssid"]
    assert wifi_data.password == expected_value["password"]
    assert wifi_data.connect_at_startup == expected_value["connect_at_startup"]
