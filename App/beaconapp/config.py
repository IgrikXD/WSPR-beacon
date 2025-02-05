from beaconapp.tx_mode import ActiveTXMode, TransmissionMode

import json
import os


class Config:
    def __init__(self, config_file_name):
        # Default values used in case of missing overridden values in the configuration file
        self._default_transmission_mode = TransmissionMode.WSPR.name
        self._default_tx_call = "N0CALL"
        self._default_qth_locator = "XX00"
        self._default_output_power = 23
        self._default_transmit_every = "2 minutes"
        self._default_active_band = "40m"
        self._default_cal_frequency = 28.000
        self._default_ui_theme = "Dark"
        self._default_ui_scaling = 1

        # The absolute path to the configuration file
        self._config_abs_path = self._get_config_path(config_file_name)

        # Ensure config file exists by attempting to load or creating it based on default values
        try:
            self.load()
        except FileNotFoundError:
            self.save()

    @staticmethod
    def _get_config_path(config_file_name):
        """
        Returns the path to the configuration file, creating the directory if necessary.
        """
        config_dir = os.path.join(os.path.expanduser("~"), ".beaconapp")
        os.makedirs(config_dir, exist_ok=True)

        return os.path.join(config_dir, config_file_name)

    def load(self):
        """
        Loads the configuration from the file.
        """
        with open(self._config_abs_path, 'r', encoding='UTF-8') as file:
            data = json.load(file)

        for attr in vars(self):
            if attr.lstrip("_") in data:
                setattr(self, attr, data[attr.lstrip("_")])

    def save(self):
        """
        Saves the current configuration to the file. All fields of the Config class are saved
        except for the _config_abs_path field.
        """
        config = {}

        for key, value in vars(self).items():
            if key != "_config_abs_path":
                config[key.lstrip("_")] = value

        with open(self._config_abs_path, 'w', encoding='UTF-8') as file:
            json.dump(config, file, indent=4, ensure_ascii=False)

    def get_active_mode_parameters(self):
        """
        Constructs and returns an ActiveTXMode object based on the current configuration.
        """
        return ActiveTXMode(
            TransmissionMode[self._default_transmission_mode],
            self._default_tx_call,
            self._default_qth_locator,
            self._default_output_power,
            self._default_transmit_every,
            self._default_active_band
        )

    def set_active_mode_parameters(self, active_tx_mode: ActiveTXMode):
        """
        Updates the configuration parameters based on the active transmission mode.

        Parameters:
            active_tx_mode: An object containing transmission mode parameters
        """
        self._default_transmission_mode = active_tx_mode.transmission_mode.name
        self._default_tx_call = active_tx_mode.tx_call
        self._default_qth_locator = active_tx_mode.qth_locator
        self._default_output_power = active_tx_mode.output_power
        self._default_transmit_every = active_tx_mode.transmit_every
        self._default_active_band = active_tx_mode.active_band

    def get_cal_frequency(self):
        return self._default_cal_frequency

    def set_cal_frequency(self, value):
        self._default_cal_frequency = value

    def get_ui_theme(self):
        return self._default_ui_theme

    def set_ui_theme(self, value):
        self._default_ui_theme = value

    def get_ui_scaling(self):
        return self._default_ui_scaling

    def set_ui_scaling(self, value):
        self._default_ui_scaling = value
