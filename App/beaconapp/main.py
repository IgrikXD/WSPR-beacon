from beaconapp.config import Config
from beaconapp.data_wrappers import ConnectionStatus
from beaconapp.device import Device
from beaconapp.ui.navigation_widget import NavigationWidget
from beaconapp.ui.self_check_widget import SelfCheckWidget
from beaconapp.ui.settings_widget import SettingsWidget
from beaconapp.ui.spots_database_widget import SpotsDatabaseWidget
from beaconapp.ui.transmission_widget import TransmissionWidget

import atexit
import customtkinter
import os
import psutil
import tkinter.messagebox


LOCK_DIR = os.path.expanduser("~/.beaconapp")
LOCK_FILE = os.path.join(LOCK_DIR, "beaconapp.lock")


class BeaconApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Create a device instance
        self.device = Device()
        # Load the default configuration from a file
        self.config = Config("config.json")
        self.app_configuration(self.config)
        # Create the navigation widget
        navigation_frame = NavigationWidget(self)
        # Create the "Transmission" widget
        transmission_frame = TransmissionWidget(self, self.device, self.config)
        # Create the "Spots database" widget
        spots_database_frame = SpotsDatabaseWidget(self)
        # Create the "Self-check" widget
        self_check_frame = SelfCheckWidget(self, self.device)
        # Create the "Settings" widget
        settings_frame = SettingsWidget(self, self.device, self.config)

        # Frames for navigation by buttons
        navigation_frame.set_navigated_frames(
            transmission=transmission_frame,
            spots_database=spots_database_frame,
            self_check=self_check_frame,
            settings=settings_frame
        )

        # Set handlers for incoming messages from the device
        self.device.set_device_response_handlers({
            Device.Message.Incoming.ACTIVE_TRANSPORT:   [navigation_frame.set_connection_status,
                                                         lambda transport: (
                                                            transmission_frame.update_gps_status(False),
                                                            transmission_frame.update_cal_status(False),
                                                            transmission_frame.update_tx_status(False),
                                                            transmission_frame.change_state("disabled"),
                                                            spots_database_frame.change_state("disabled"),
                                                            self_check_frame.change_state("disabled"),
                                                            settings_frame.change_state("disabled")
                                                         ) if transport is None else None],
            Device.Message.Incoming.ACTIVE_TX_MODE:     [transmission_frame.set_active_tx_mode,
                                                         spots_database_frame.set_active_tx_mode,
                                                         lambda active_tx_mode: self_check_frame.change_state(
                                                            "disabled" if active_tx_mode.tx_mode else "normal"),
                                                         lambda active_tx_mode: settings_frame.change_state(
                                                            "disabled" if active_tx_mode.tx_mode else "normal")],
            Device.Message.Incoming.CAL_FREQ_GENERATED: [settings_frame.set_calibration_freq_status,
                                                         lambda cal_freq_generated: transmission_frame.change_state(
                                                            "disabled" if cal_freq_generated else "normal"),
                                                         lambda cal_freq_generated: self_check_frame.change_state(
                                                            "disabled" if cal_freq_generated else "normal")],
            Device.Message.Incoming.CAL_STATUS:         [transmission_frame.update_cal_status],
            Device.Message.Incoming.CAL_VALUE:          [settings_frame.set_calibration_value],
            Device.Message.Incoming.FIRMWARE_INFO:      [self_check_frame.update_firmware_info],
            Device.Message.Incoming.GPS_STATUS:         [transmission_frame.update_gps_status],
            Device.Message.Incoming.HARDWARE_INFO:      [self_check_frame.update_hardware_info],
            Device.Message.Incoming.QTH_LOCATOR:        [transmission_frame.update_qth_locator],
            Device.Message.Incoming.PROTOCOL_ERROR:     [self.protocol_error_handler],
            Device.Message.Incoming.SELF_CHECK_ACTION:  [self_check_frame.update_self_check_action_status],
            Device.Message.Incoming.SELF_CHECK_ACTIVE:  [lambda self_check_active: transmission_frame.change_state(
                                                            "disabled" if self_check_active else "normal"),
                                                         lambda self_check_active: settings_frame.change_state(
                                                            "disabled" if self_check_active else "normal")],
            Device.Message.Incoming.SELF_CHECK_STATUS:  [self_check_frame.update_self_check_status],
            Device.Message.Incoming.TX_ACTION_STATUS:   [transmission_frame.update_tx_message_action_status],
            Device.Message.Incoming.TX_STATUS:          [transmission_frame.update_tx_status],
            Device.Message.Incoming.WIFI_SSID_DATA:     [settings_frame.set_wifi_data],
            Device.Message.Incoming.WIFI_STATUS:        [settings_frame.update_wifi_status,
                                                         lambda wifi_status: transmission_frame.change_state(
                                                            "disabled" if wifi_status is
                                                            ConnectionStatus.INITIATED else "normal"),
                                                         lambda wifi_status: self_check_frame.change_state(
                                                            "disabled" if wifi_status is
                                                            ConnectionStatus.INITIATED else "normal"),
                                                         lambda wifi_status: settings_frame.change_state(
                                                            "disabled" if wifi_status is
                                                            ConnectionStatus.INITIATED else "normal")]
        })

        # Establish the connection to the device
        self.device.connect()
        # Select the default frame
        navigation_frame.select_frame_by_name("transmission")

    def app_configuration(self, config: Config):
        """
        Configure the application: title, icon, minimum window size, theme, and UI scaling.
        """
        # Application title
        self.title("BEACON.App")
        # Application icon
        self.iconbitmap(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "ui/resources/beacon-app-logo.ico"))
        # Minimum window size
        self.minsize(1100, 600)
        # Defaulf app theme
        customtkinter.set_appearance_mode(config.get_ui_theme())
        # Default app scaling
        customtkinter.set_widget_scaling(config.get_ui_scaling())

        # Main window layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Handle the window close event
        self.protocol("WM_DELETE_WINDOW", self.update_default_config_and_close_app)

    def protocol_error_handler(self, error_message: str):
        """
        Handle protocol error messages received from the device by displaying a warning message box.
        """
        tkinter.messagebox.showwarning(
            "BEACON.App - Protocol Error",
            f"Received from device: {error_message}\n\n"
            "Please ensure that you are using the latest version of BEACON.App "
            "and that your device firmware is up to date."
        )

    def update_default_config_and_close_app(self):
        """
        Save the current configuration, properly disconnect from device, and close the app.
        """
        self.config.save()
        # Properly close all active connections to the device
        self.device.disconnect()
        self.destroy()
        # Force exit to prevent hanging on resource cleanup
        os._exit(0)


def check_already_running() -> bool:
    """
    Checks if an instance of the application is already running via a PID lock file in ~/.beaconapp.
    Returns True if the application is already running, otherwise False.
    """
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                old_pid = int(f.read().strip())
            # Check if a process with this PID is still running
            if old_pid in psutil.pids():
                # A process with this PID is still active
                return True
            else:
                # The old process is not active, remove the outdated lock file
                os.remove(LOCK_FILE)
        except (ValueError, OSError):
            # If PID could not be read or something went wrong, remove the file
            os.remove(LOCK_FILE)
    return False


def create_lock_file():
    """
    Creates the ~/.beaconapp directory if it does not exist,
    then creates a lock file with the current process PID.
    """
    # Ensure the working directory exists
    if not os.path.isdir(LOCK_DIR):
        os.makedirs(LOCK_DIR, exist_ok=True)

    # Create or overwrite the lock file
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    # Remove the lock file when the program exits
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))


def main():
    # Check if the application is already running
    if check_already_running():
        tkinter.messagebox.showerror(
            "BEACON.App - Error",
            "The application is already running!"
        )
        os._exit(1)

    # Create the lock file if not running
    create_lock_file()

    # Launch the application
    app = BeaconApp()
    app.mainloop()


if __name__ == "__main__":
    main()
