import json
import os

CONFIG_FILE_NAME = "config.json"

class Config:
    DEFAULT_CONFIG = {
        "default_tx_call": "N0CALL",
        "default_qth_locator": "XX00",
        "default_output_power": 23,
        "default_transmit_every": "2 minutes",
        "default_active_band": "40m",
        "default_cal_value": 2000,
        "default_cal_frequency": 28
    }

    def __init__(self):
        self._config_path = self._get_config_path()
        if not self.load_config():
            self.__dict__.update(self.DEFAULT_CONFIG)
            self.save_config()

    @staticmethod
    def _get_config_path():
        """Returns the path to the configuration file, creating the directory if necessary."""
        config_dir = os.path.join(os.path.expanduser("~"), ".beaconapp")
        os.makedirs(config_dir, exist_ok=True)
        
        return os.path.join(config_dir, CONFIG_FILE_NAME)

    def load_config(self):
        """Loads the configuration from the file. Returns True if successful, False otherwise."""
        if os.path.exists(self._config_path):
            with open(self._config_path, 'r') as file:
                data = json.load(file)
                self.__dict__.update({key: data.get(key, value) for key, value in self.DEFAULT_CONFIG.items()})
            return True
        return False

    def save_config(self):
        """Saves the current configuration to the file."""
        config = {key: getattr(self, key) for key in self.DEFAULT_CONFIG}
        with open(self._config_path, 'w') as file:
            json.dump(config, file, indent=4)