import json
import pytest
import uuid

from beaconapp.data_wrappers import ActiveTXMode, Band, TransmitEvery, TXMode
from beaconapp.config import Config


@pytest.fixture
def patch_get_config_path(monkeypatch, tmp_path):
    """
    Fixture that forces Config._get_config_path to store/read the config in tmp_path.
    """
    monkeypatch.setattr("beaconapp.config.Config._get_config_path", lambda _, filename: str(tmp_path / filename))
    return tmp_path


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Returns a unique temporary config file path for each test.
    The file is created in tmp_path and will be automatically removed.
    """
    return tmp_path / f"temp_config_{uuid.uuid4().hex}.json"


@pytest.mark.parametrize(
    "config_file_exists, file_content, expected_defaults",
    [
        # File does not exist => use default values
        (
            False,
            None,
            {
                "default_tx_mode": TXMode.WSPR,
                "default_tx_call": "N0CALL",
                "default_qth_locator": "XX00",
                "default_output_power": 23,
                "default_transmit_every": TransmitEvery.MINUTES_2,
                "default_active_band": Band.BAND_40M,
                "default_cal_frequency": 28.000,
                "default_ui_theme": "Dark",
                "default_ui_scaling": 1
            }
        ),
        # File exists but is empty => use default values
        (
            True,
            {},
            {
                "default_tx_mode": TXMode.WSPR,
                "default_tx_call": "N0CALL",
                "default_qth_locator": "XX00",
                "default_output_power": 23,
                "default_transmit_every": TransmitEvery.MINUTES_2,
                "default_active_band": Band.BAND_40M,
                "default_cal_frequency": 28.000,
                "default_ui_theme": "Dark",
                "default_ui_scaling": 1
            }
        ),
        # File exists with partial settings => some from file, some defaults
        (
            True,
            {
                "default_tx_call": "N0TTXX",
                "default_qth_locator": "AB01",
                "default_output_power": 10
            },
            {
                "default_tx_mode": TXMode.WSPR,                 # default
                "default_tx_call": "N0TTXX",
                "default_qth_locator": "AB01",
                "default_output_power": 10,
                "default_transmit_every": TransmitEvery.MINUTES_2,  # default
                "default_active_band": Band.BAND_40M,           # default
                "default_cal_frequency": 28.000,                # default
                "default_ui_theme": "Dark",                     # default
                "default_ui_scaling": 1                         # default
            }
        ),
        # Comfig file exists with all fields
        (
            True,
            {
                "default_tx_mode": 1,
                "default_tx_call": "K0ABC",
                "default_qth_locator": "FN20",
                "default_output_power": 33,
                "default_transmit_every": 10,
                "default_active_band": 20,
                "default_cal_frequency": 7.045,
                "default_ui_theme": "Light",
                "default_ui_scaling": 2
            },
            {
                "default_tx_mode": TXMode.WSPR,
                "default_tx_call": "K0ABC",
                "default_qth_locator": "FN20",
                "default_output_power": 33,
                "default_transmit_every": TransmitEvery.MINUTES_10,
                "default_active_band": Band.BAND_20M,
                "default_cal_frequency": 7.045,
                "default_ui_theme": "Light",
                "default_ui_scaling": 2
            }
        ),
    ]
)
@pytest.mark.unit
def test_config_load(patch_get_config_path, temp_config_file, config_file_exists, file_content, expected_defaults):
    """
    Verifies that when the config file is absent or partially filled, Config loads default values.
    When the file is fully populated, it loads the specified values.
    """
    if config_file_exists:
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(file_content, f)

    # The actual config path is resolved inside the Config class via the monkeypatch.
    config = Config(temp_config_file.name)

    assert config.get_active_mode_parameters() == ActiveTXMode(
        expected_defaults["default_tx_mode"],
        expected_defaults["default_tx_call"],
        expected_defaults["default_qth_locator"],
        expected_defaults["default_output_power"],
        expected_defaults["default_transmit_every"],
        expected_defaults["default_active_band"]
    )
    assert config.get_cal_frequency() == expected_defaults["default_cal_frequency"]
    assert config.get_ui_theme() == expected_defaults["default_ui_theme"]
    assert config.get_ui_scaling() == expected_defaults["default_ui_scaling"]


@pytest.mark.parametrize(
    "initial_call, new_call",
    [
        ("N0CALL", "R1ABC"),
        ("R1ABC", "K2XYZ"),
        ("N0CALL", "MYCALL")
    ]
)
@pytest.mark.unit
def test_set_get_active_mode_parameters(patch_get_config_path, temp_config_file, initial_call, new_call):
    """
    Checks that set_active_mode_parameters updates Config correctly,
    and get_active_mode_parameters returns the new values.
    Since only WSPR is available, we'll just change other parameters.
    """
    # The actual config path is resolved inside the Config class via the monkeypatch.
    config = Config(temp_config_file.name)

    # Set initial active mode parameters
    initial_active_tx_mode = ActiveTXMode(TXMode.WSPR, initial_call, "XX00", 23, TransmitEvery.MINUTES_2, Band.BAND_40M)
    config.set_active_mode_parameters(initial_active_tx_mode)

    # Update active mode parameters
    new_active_tx_mode = ActiveTXMode(TXMode.WSPR, new_call, "AB12", 10, TransmitEvery.MINUTES_10, Band.BAND_20M)
    config.set_active_mode_parameters(new_active_tx_mode)

    # Verify via get_active_mode_parameters
    assert config.get_active_mode_parameters() == new_active_tx_mode


@pytest.mark.parametrize(
    "initial_val, new_val",
    [
        (28.000, 10.100),
        (10.000, 14.055),
    ]
)
@pytest.mark.unit
def test_set_get_cal_frequency(patch_get_config_path, temp_config_file, initial_val, new_val):
    """
    Checks that set_cal_frequency and get_cal_frequency consistently set and retrieve the calibration frequency.
    """
    # The actual config path is resolved inside the Config class via the monkeypatch.
    config = Config(temp_config_file.name)

    config.set_cal_frequency(initial_val)
    assert config.get_cal_frequency() == initial_val

    config.set_cal_frequency(new_val)
    assert config.get_cal_frequency() == new_val


@pytest.mark.parametrize(
    "initial_theme, new_theme",
    [
        ("Dark", "Light"),
        ("Light", "Dark")
    ]
)
@pytest.mark.unit
def test_set_get_ui_theme(patch_get_config_path, temp_config_file, initial_theme, new_theme):
    """
    Checks that set_ui_theme and get_ui_theme are consistent.
    """
    # The actual config path is resolved inside the Config class via the monkeypatch.
    config = Config(temp_config_file.name)

    config.set_ui_theme(initial_theme)
    assert config.get_ui_theme() == initial_theme

    config.set_ui_theme(new_theme)
    assert config.get_ui_theme() == new_theme


@pytest.mark.parametrize(
    "initial_scale, new_scale",
    [
        (1, 2),
        (2, 0.8),
    ]
)
@pytest.mark.unit
def test_set_get_ui_scaling(patch_get_config_path, temp_config_file, initial_scale, new_scale):
    """
    Checks that set_ui_scaling and get_ui_scaling are consistent.
    """
    # The actual config path is resolved inside the Config class via the monkeypatch.
    config = Config(temp_config_file.name)

    config.set_ui_scaling(initial_scale)
    assert config.get_ui_scaling() == initial_scale

    config.set_ui_scaling(new_scale)
    assert config.get_ui_scaling() == new_scale


@pytest.mark.unit
def test_config_save_and_reload(patch_get_config_path, temp_config_file):
    """
    Ensures that after calling save(), the data is indeed written to the file,
    and a new Config object loads the updated values.
    """
    # The actual config path is resolved inside the Config class via the monkeypatch.
    config = Config(temp_config_file.name)

    active_tx_mode = ActiveTXMode(TXMode.WSPR, "XX0YYZZ", "ZZ99", 15, TransmitEvery.MINUTES_30, Band.BAND_80M)
    cal_frequency = 7.045
    ui_theme = "Light"
    ui_scaling = 2

    config.set_active_mode_parameters(active_tx_mode)
    config.set_cal_frequency(cal_frequency)
    config.set_ui_theme(ui_theme)
    config.set_ui_scaling(ui_scaling)

    # Save and then reload using a fresh Config instance
    config.save()
    config_reloaded = Config(temp_config_file.name)

    assert config_reloaded.get_active_mode_parameters() == active_tx_mode
    assert config_reloaded.get_cal_frequency() == cal_frequency
    assert config_reloaded.get_ui_theme() == ui_theme
    assert config_reloaded.get_ui_scaling() == ui_scaling
