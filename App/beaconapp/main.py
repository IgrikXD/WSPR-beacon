from beaconapp.config import Config
from beaconapp.data_wrappers import Status
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
import sys
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
        # Track TX status for deferred tab unlocking
        self._tx_active = False
        self._unlock_pending = False
        self._app_configuration(self.config)
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
                                                         # Handle device disconnection
                                                         lambda transport: (
                                                            self._reset_tab_lock_state(),
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
                                                         lambda active_tx_mode:
                                                            self._handle_active_tx_mode_tab_lock(
                                                                active_tx_mode,
                                                                self_check_frame,
                                                                settings_frame)],
            Device.Message.Incoming.CAL_FREQ_GENERATED: [settings_frame.set_calibration_freq_status,
                                                         lambda cal_freq_generated: transmission_frame.change_state(
                                                            "disabled" if cal_freq_generated else "normal"),
                                                         lambda cal_freq_generated: self_check_frame.change_state(
                                                            "disabled" if cal_freq_generated else "normal")],
            Device.Message.Incoming.CAL_STATUS:         [transmission_frame.update_cal_status],
            Device.Message.Incoming.CAL_VALUE:          [settings_frame.set_calibration_value],
            Device.Message.Incoming.FIRMWARE_INFO:      [self_check_frame.update_firmware_info,
                                                         self.device.update_firmware_info],
            Device.Message.Incoming.FIRMWARE_STATUS:    [self_check_frame.update_firmware_status],
            Device.Message.Incoming.GPS_CAL_STATUS:     [settings_frame.update_gps_cal_status,
                                                         lambda gps_cal_status: transmission_frame.change_state(
                                                            "disabled" if gps_cal_status is
                                                            Status.INITIATED else "normal"),
                                                         lambda gps_cal_status: self_check_frame.change_state(
                                                            "disabled" if gps_cal_status is
                                                            Status.INITIATED else "normal")],
            Device.Message.Incoming.GPS_STATUS:         [transmission_frame.update_gps_status,
                                                         settings_frame.update_gps_status],
            Device.Message.Incoming.HARDWARE_INFO:      [self_check_frame.update_hardware_info],
            Device.Message.Incoming.QTH_LOCATOR:        [transmission_frame.update_qth_locator],
            Device.Message.Incoming.PROTOCOL_ERROR:     [self._protocol_error_handler],
            Device.Message.Incoming.SELF_CHECK_ACTION:  [self_check_frame.update_self_check_action_status],
            Device.Message.Incoming.SELF_CHECK_ACTIVE:  [lambda self_check_active: transmission_frame.change_state(
                                                            "disabled" if self_check_active else "normal"),
                                                         lambda self_check_active: settings_frame.change_state(
                                                            "disabled" if self_check_active else "normal")],
            Device.Message.Incoming.SELF_CHECK_STATUS:  [self_check_frame.update_self_check_status],
            Device.Message.Incoming.TX_ACTION_STATUS:   [transmission_frame.update_tx_message_action_status],
            Device.Message.Incoming.TX_STATUS:          [transmission_frame.update_tx_status,
                                                         lambda tx_status:
                                                            self._handle_tx_status_tab_unlock(
                                                                tx_status,
                                                                self_check_frame,
                                                                settings_frame)],
            Device.Message.Incoming.WIFI_SSID_DATA:     [settings_frame.set_wifi_data],
            Device.Message.Incoming.WIFI_STATUS:        [settings_frame.update_wifi_status,
                                                         lambda wifi_status: transmission_frame.change_state(
                                                            "disabled" if wifi_status is
                                                            Status.INITIATED else "normal"),
                                                         lambda wifi_status: self_check_frame.change_state(
                                                            "disabled" if wifi_status is
                                                            Status.INITIATED else "normal")]
        })

        # Establish the connection to the device
        self.device.connect()
        # Select the default frame
        navigation_frame.select_frame_by_name("transmission")

    def _app_configuration(self, config: Config):
        """
        Configure the application: title, icon, minimum window size, theme, and UI scaling.
        """
        # Application title
        self.title("BEACON.App")
        # Application icon (use .ico on Windows, .png on Linux)
        icon_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ui/resources")
        if sys.platform == "win32":
            self.iconbitmap(os.path.join(icon_dir, "beacon-app-logo.ico"))
        else:
            # On Linux, use iconphoto with PNG image
            from PIL import Image, ImageTk
            # Keep reference to prevent garbage collection
            self.icon_photo = ImageTk.PhotoImage(
                Image.open(os.path.join(icon_dir, "beacon-app-logo.png")))
            self.iconphoto(True, self.icon_photo)
        # Minimum window size
        self.minsize(1100, 600)
        # Default app theme
        customtkinter.set_appearance_mode(config.get_ui_theme())
        # Default app scaling
        customtkinter.set_widget_scaling(config.get_ui_scaling())

        # Main window layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Handle the window close event
        self.protocol("WM_DELETE_WINDOW", self._update_default_config_and_close_app)

    def _reset_tab_lock_state(self):
        """
        Reset the tab lock state tracking variables.
        """
        self._tx_active = False
        self._unlock_pending = False

    def _handle_active_tx_mode_tab_lock(self, active_tx_mode, *frames):
        """
        Handle tab locking/unlocking when ACTIVE_TX_MODE changes.
        If the mode is cleared but the device is still transmitting,
        defer unlocking until transmission completes.

        Args:
            active_tx_mode: An instance of ActiveTXMode.
            *frames: Widget frames to lock/unlock.
        """
        if active_tx_mode.tx_mode:
            self._unlock_pending = False
            for frame in frames:
                frame.change_state("disabled")
        else:
            if self._tx_active:
                self._unlock_pending = True
            else:
                self._unlock_pending = False
                for frame in frames:
                    frame.change_state("normal")

    def _handle_tx_status_tab_unlock(self, tx_status, *frames):
        """
        Track TX_STATUS and perform deferred tab unlocking when transmission ends.

        Args:
            tx_status: Boolean indicating if transmission is active.
            *frames: Widget frames to unlock when transmission ends.
        """
        self._tx_active = tx_status
        if not tx_status and self._unlock_pending:
            self._unlock_pending = False
            for frame in frames:
                frame.change_state("normal")

    def _protocol_error_handler(self, error_message: str):
        """
        Handle protocol error messages received from the device by displaying a warning message box.
        """
        tkinter.messagebox.showwarning(
            "BEACON.App - Protocol Error",
            f"Received from device: {error_message}\n\n"
            "Please ensure that you are using the latest version of BEACON.App "
            "and that your device firmware is up to date."
        )

    def _update_default_config_and_close_app(self):
        """
        Save the current configuration, properly disconnect from device, and close the app.
        """
        # Close the main window
        self.destroy()
        # Save the current app configuration
        self.config.save()
        # Properly close all active connections to the device
        self.device.disconnect()
        sys.exit(0)


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
            if psutil.pid_exists(old_pid):
                try:
                    process = psutil.Process(old_pid)
                    # Check if it's actually a Python process running BEACON.App
                    process_name = process.name().lower()
                    if "python" in process_name or "beaconapp" in process_name:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process disappeared or is inaccessible — treat as not running
                    pass
            # The old process is not active or not BEACON.App, remove the outdated lock file
            os.remove(LOCK_FILE)
        except (ValueError, OSError):
            # If PID could not be read or something went wrong, remove the file
            try:
                os.remove(LOCK_FILE)
            except OSError:
                # Lock file already removed or inaccessible — safe to ignore
                pass
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

    # Remove the lock file
    atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)


def main():
    # Check if the application is already running
    if check_already_running():
        tkinter.messagebox.showerror(
            "BEACON.App - Error",
            "The application is already running!"
        )
        sys.exit(1)

    # Create the lock file if not running
    create_lock_file()

    # Launch the application
    app = BeaconApp()
    app.mainloop()


if __name__ == "__main__":
    main()
