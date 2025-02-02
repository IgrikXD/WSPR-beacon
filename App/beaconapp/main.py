from beaconapp.config import Config
from beaconapp.device import Device
from beaconapp.ui.navigation_widget import NavigationWidget
from beaconapp.ui.self_check_widget import SelfCheckWidget
from beaconapp.ui.settings_widget import SettingsWidget
from beaconapp.ui.spots_database_widget import SpotsDatabaseWidget
from beaconapp.ui.transmission_widget import TransmissionWidget

import customtkinter
import os


class BeaconApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Create a device instance with the name programmed into the CP2104 UART controller
        device = Device("USB-SERIAL CH340")
        # Load the default configuration from a file
        config = Config("config.json")
        self.app_configuration(config)
        # Create the navigation widget
        navigation_frame = NavigationWidget(self)
        # Create the "Transmission" widget
        transmission_frame = TransmissionWidget(self, device, config)
        # Create the "Spots database" widget
        spots_database_frame = SpotsDatabaseWidget(self)
        # Create the "Self-check" widget
        self_check_frame = SelfCheckWidget(self, device)
        # Create the "Settings" widget
        settings_frame = SettingsWidget(self, device, config)

        # Frames for navigation by buttons
        navigation_frame.set_navigated_frames(
            transmission=transmission_frame,
            spots_database=spots_database_frame,
            self_check=self_check_frame,
            settings=settings_frame
        )

        # Set handlers for incoming messages from the device
        device.set_device_response_handlers({
            Device.IncomingMessageType.ACTIVE_TX_MODE:     [transmission_frame.set_active_tx_mode,
                                                            spots_database_frame.set_active_tx_mode,
                                                            lambda tx_mode: self_check_frame.change_state(
                                                                "disabled" if tx_mode.transmission_mode else "normal"),
                                                            lambda tx_mode: settings_frame.change_state(
                                                                "disabled" if tx_mode.transmission_mode else "normal")],
            Device.IncomingMessageType.TX_ACTION_STATUS:   [transmission_frame.update_tx_message_action_status],
            Device.IncomingMessageType.GPS_STATUS:         [transmission_frame.update_gps_status],
            Device.IncomingMessageType.CAL_STATUS:         [transmission_frame.update_cal_status],
            Device.IncomingMessageType.TX_STATUS:          [transmission_frame.update_tx_status],
            Device.IncomingMessageType.SELF_CHECK_ACTION:  [self_check_frame.update_self_check_action_status],
            Device.IncomingMessageType.SELF_CHECK_STATUS:  [self_check_frame.update_self_check_status],
            Device.IncomingMessageType.SELF_CHECK_ACTIVE:  [lambda self_check_active: transmission_frame.change_state(
                                                                "disabled" if self_check_active else "normal"),
                                                            lambda self_check_active: settings_frame.change_state(
                                                                "disabled" if self_check_active else "normal")],
            Device.IncomingMessageType.HARDWARE_INFO:      [self_check_frame.update_hardware_info],
            Device.IncomingMessageType.FIRMWARE_INFO:      [self_check_frame.update_firmware_info],
            Device.IncomingMessageType.WIFI_STATUS:        [settings_frame.set_wifi_status],
            Device.IncomingMessageType.CONNECTION_STATUS:  [navigation_frame.set_connection_status,
                                                            lambda connection: transmission_frame.change_state(
                                                                "disabled" if connection is
                                                                Device.ConnectionStatus.NOT_CONNECTED else "normal"),
                                                            lambda connection: self_check_frame.change_state(
                                                                "disabled" if connection is 
                                                                Device.ConnectionStatus.NOT_CONNECTED else "normal"),
                                                            lambda connection: settings_frame.change_state(
                                                                "disabled" if connection is 
                                                                Device.ConnectionStatus.NOT_CONNECTED else "normal")],
            Device.IncomingMessageType.CAL_VALUE:          [settings_frame.set_calibration_value],
            Device.IncomingMessageType.CAL_FREQ_GENERATED: [settings_frame.set_calibration_freq_status,
                                                            lambda cal_freq_generated: transmission_frame.change_state(
                                                                "disabled" if cal_freq_generated else "normal"),
                                                            lambda cal_freq_generated: self_check_frame.change_state(
                                                                "disabled" if cal_freq_generated else "normal")]
        })

        # Establish the connection to the device
        device.connect()
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
        self.protocol("WM_DELETE_WINDOW",
                      lambda: self.update_default_config_and_close_app(config))

    def update_default_config_and_close_app(self, config: Config):
        """
        Save the current configuration and close the app.
        """
        config.save()
        self.destroy()


def main():
    app = BeaconApp()
    app.mainloop()


if __name__ == "__main__":
    main()
