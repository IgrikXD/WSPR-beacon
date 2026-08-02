import customtkinter

from beaconapp.config import Config
from beaconapp.data_validation import DataValidation
from beaconapp.data_wrappers import Status, WiFiCredentials, WiFiData
from beaconapp.device import Device
from beaconapp.ui.widgets import Widgets


class SettingsWidget:
    def __init__(self, parent, device: Device, config: Config):
        """
        Initialize the SettingsWidget.

        Args:
            parent: The parent widget that this frame will be placed into.
            device (Device): An instance of the Device class to interact with the hardware.
            config (Config): An instance of the Config class containing default calibration
                frequency, application theme, and interface scaling settings. This parameter
                is also used to update the default values if they are modified in the settings.
        """
        self.device = device
        self.config = config
        # Locally cached GPS status used to enable/disable GPS calibration
        # button depending on GPS availability
        self.gps_status = False

        self.general_frame = Widgets.create_general_frame(parent, scrollable=True)

        # Device calibration label
        Widgets.create_block_label(self.general_frame, row=0, text="Device calibration")

        # Settings -> Device calibration -> Calibration value
        self.cal_value_var = customtkinter.StringVar()
        self.cal_value_entry, cal_value_buttons = (
            Widgets.create_entry_with_background_frame_and_control_buttons(
                self.general_frame,
                row=1,
                text="Calibration value:",
                state="disabled",
                validation=DataValidation.validate_cal_value_input,
                bind_action=["<Return>", self._calibration_value_entry_enter_pressed],
                buttons=[
                    {'text': 'Auto by GPS', 'command': self._gps_calibration_button_pressed, 'width': 90},
                    {'text': '+', 'command': self._calibration_value_inc_button_pressed},
                    {'text': '-', 'command': self._calibration_value_dec_button_pressed}
                ],
                optimize_for_scrollable=True,
                textvariable=self.cal_value_var
            )
        )
        self.gps_cal_value_button = cal_value_buttons[0]
        self.inc_cal_value_button = cal_value_buttons[1]
        self.dec_cal_value_button = cal_value_buttons[2]

        # GPS calibration action mappings
        self._gps_cal_actions = {
            Status.CALIBRATED: self._gps_calibration_finished,
            Status.INITIATED: self._gps_calibration_initiated,
            Status.FAILED: self._gps_calibration_error_handle,
        }

        # Settings -> Device calibration -> Calibration frequency
        self.cal_frequency_button, self.cal_frequency_entry = Widgets.create_entry_with_button(
            self.general_frame,
            row=2,
            text="Calibration frequency, MHz:",
            entry_default_value=self.config.get_cal_frequency(),
            entry_state="disabled",
            entry_validation=DataValidation.validate_cal_frequency_input,
            entry_bind_action=[
                ("<Return>", self._calibration_frequency_entry_enter_pressed),
                ("<KeyRelease>", self._calibration_frequency_update_generate_button_state)
            ],
            button_text="Generate",
            button_state="disabled",
            button_command=self._calibration_frequency_button_pressed,
            optimize_for_scrollable=True
        )

        # Device connection settings label
        Widgets.create_block_label(self.general_frame, row=3, text="Device connection settings")

        # Settings -> Device connection settings -> SSID
        self.ssid_var = customtkinter.StringVar()
        self.wifi_connection_button, self.ssid_entry = Widgets.create_entry_with_button(
            self.general_frame,
            row=4,
            text="SSID:",
            entry_state="disabled",
            entry_bind_action=["<KeyRelease>", self._wifi_update_connection_button_state],
            button_text="Connect",
            button_state="disabled",
            button_command=self._wifi_connection_button_pressed,
            optimize_for_scrollable=True,
            entry_textvariable=self.ssid_var
        )

        # Wi-Fi connection status action mappings
        self._wifi_status_actions = {
            Status.CONNECTED: self._wifi_connection_pass,
            Status.DISCONNECTED: self._wifi_disconnected,
            Status.INITIATED: self._wifi_connection_initiated,
            Status.FAILED: self._wifi_connection_error_handle,
        }

        # Settings -> Device connection settings -> Password
        self.password_var = customtkinter.StringVar()
        self.password_entry = Widgets.create_entry_with_background_frame(
            self.general_frame,
            row=5,
            text="Password:",
            state="disabled",
            show="●",
            bind_action=["<KeyRelease>", self._wifi_update_connection_button_state],
            optimize_for_scrollable=True,
            textvariable=self.password_var
        )

        # Settings -> Device connection settings -> Auto-connect to Wi-Fi on startup
        self.wifi_auto_connect_at_startup_option = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=6,
            text="Auto-connect to Wi-Fi on startup:",
            values=["Enabled", "Disabled"],
            default_value="Enabled",
            state="disabled",
            command=self._wifi_auto_connect_at_startup_option_event,
            optimize_for_scrollable=True
        )

        # App settings label
        Widgets.create_block_label(self.general_frame, row=7, text="App settings")

        # Settings -> App settings -> App theme
        self.ui_theme = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=8,
            text="UI theme:",
            values=["Dark", "Light"],
            default_value=self.config.get_ui_theme(),
            command=self._change_ui_theme_event,
            optimize_for_scrollable=True
        )

        # Settings -> App settings -> UI scaling
        self.ui_scaling_option = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=9,
            text="UI scaling:",
            values=["80%", "90%", "100%", "110%", "120%"],
            default_value=f"{int(self.config.get_ui_scaling() * 100)}%",
            command=self._change_ui_scaling_event,
            optimize_for_scrollable=True
        )

    def change_state(self, state):
        """
        Enable or disable the UI components based on the given state.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        self._calibration_change_state(state)
        self._wifi_change_state(state)

    def set_calibration_freq_status(self, is_generated: bool):
        """
        Control the calibration frequency generation process and update UI elements accordingly.

        Args:
            is_generated (bool): Indicates if the calibration frequency is currently being generated.
        """
        if not is_generated:
            # Wi-Fi management is allowed if the calibration frequency is not being generated.
            self._wifi_change_state("normal")

        self.cal_frequency_button.configure(
            state="normal",
            text="Terminate" if is_generated else "Generate",
            fg_color=["#D9534F", "#A94442"] if is_generated else ["#3B8ED0", "#1F6AA5"],
            hover_color=["#9A2A2A", "#7A2A28"] if is_generated else ["#36719F", "#144870"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"] if is_generated else ["#BDBDBD", "#999999"]
        )

    def set_calibration_value(self, value):
        """
        Set the value in the calibration entry field.

        Args:
            value: Calibration value to display in the entry.
        """
        self.cal_value_var.set(value)

    def set_wifi_data(self, data: WiFiData):
        """
        Updates the Wi-Fi parameters in the UI with the provided Wi-Fi data.

        Args:
            data (WiFiData): An object containing the Wi-Fi data to be set, including:
                - ssid (str): The name of the Wi-Fi network.
                - password (str): The password of the Wi-Fi network.
                - connect_at_startup (bool): Whether to auto-connect to this Wi-Fi network at startup.
        """
        self.ssid_var.set(data.ssid)
        self.password_var.set(data.password)

        self._wifi_update_connection_button_state()
        self.wifi_auto_connect_at_startup_option.set("Enabled" if data.connect_at_startup else "Disabled")

    def update_gps_cal_status(self, status: Status):
        """
        Updates the GPS calibration button based on the current GPS calibration status.

        Args:
            status (Status): The current GPS calibration status.
        """
        self._gps_cal_actions[status]()

    def update_gps_status(self, status: bool):
        """
        Update the locally cached GPS status.

        Args:
            status (bool): The GPS status to set.
        """
        self.gps_status = status
        gps_button_state = "normal" if status else "disabled"
        self.gps_cal_value_button.after(0, lambda: self.gps_cal_value_button.configure(state=gps_button_state))

    def update_wifi_status(self, status: Status):
        """
        Updates the Wi-Fi connection button based on the current Wi-Fi connection status.

        Args:
            status (Status): The current Wi-Fi connection status.
        """
        self._wifi_status_actions[status]()

    def _calibration_change_state(self, state):
        """
        Change the state of the calibration-related UI components.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        if state == "normal":
            self._calibration_elements_change_state("normal")
            self._calibration_frequency_update_generate_button_state()
        else:
            self._calibration_elements_change_state("disabled")

    def _calibration_elements_change_state(self, state):
        """
        Enable or disable calibration-related UI components.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        gps_button_state = "normal" if state == "normal" and self.gps_status else "disabled"
        self.gps_cal_value_button.after(0, lambda: self.gps_cal_value_button.configure(state=gps_button_state))
        self.dec_cal_value_button.after(0, lambda: self.dec_cal_value_button.configure(state=state))
        self.inc_cal_value_button.after(0, lambda: self.inc_cal_value_button.configure(state=state))
        self.cal_value_entry.after(0, lambda: self.cal_value_entry.configure(state=state))
        self.cal_frequency_entry.after(0, lambda: self.cal_frequency_entry.configure(state=state))
        self.cal_frequency_button.after(0, lambda: self.cal_frequency_button.configure(state=state))

    def _calibration_frequency_button_pressed(self):
        """
        Handle the logic when the calibration frequency button is pressed (Generate or Terminate).
        """
        self.cal_frequency_button.focus_set()
        # Disabling the ability to control Wi-Fi while generating the calibration frequency
        self._wifi_change_state("disabled")

        if self.cal_frequency_button.cget("text") == "Terminate":
            self.device.gen_calibration_frequency(None)
        else:
            self.device.gen_calibration_frequency(float(self.cal_frequency_entry.get()))

        self.cal_frequency_button.configure(
            text="Waiting...",
            state="disabled",
            text_color_disabled=["#BDBDBD", "#999999"]
        )

    def _calibration_frequency_entry_enter_pressed(self, event=None):
        """
        Handle the <Enter> key press on the calibration frequency entry field.
        The action is the same as pressing the "Generate" or "Terminate" button.
        """
        self._calibration_frequency_button_pressed()
        self.cal_frequency_entry.focus_set()

    def _calibration_frequency_update_generate_button_state(self, event=None):
        """
        Dynamically enable or disable the "Generate" button depending on calibration
        frequency field are filled.
        """
        if (self.cal_frequency_entry.get()):
            self.cal_frequency_button.after(0, lambda: self.cal_frequency_button.configure(state="normal"))
        else:
            self.cal_frequency_button.after(0, lambda: self.cal_frequency_button.configure(state="disabled"))

    def _calibration_value_inc_button_pressed(self):
        """
        Handle the logic when the '+' button for calibration value is pressed.
        Increments the current calibration value by 1.
        """
        self.inc_cal_value_button.focus_set()
        self._calibration_value_update(1)

    def _calibration_value_dec_button_pressed(self):
        """
        Handle the logic when the '-' button for calibration value is pressed.
        Decrements the current calibration value by 1.
        """
        self.dec_cal_value_button.focus_set()
        self._calibration_value_update(-1)

    def _calibration_value_entry_enter_pressed(self, event=None):
        """
        Handle the <Enter> key press on the calibration value entry field.
        Updates the device with the new calibration value.
        """
        self.device.set_calibration_value(int(self.cal_value_entry.get()))

    def _calibration_value_update(self, change):
        """
        Update the calibration value by a specific increment/decrement amount
        and notify the device of the new value.

        Args:
            change (int): The delta (e.g., +1 or -1) to apply to the current calibration value.
        """
        new_value = int(self.cal_value_entry.get()) + change
        self.cal_value_var.set(str(new_value))
        self.device.set_calibration_value(new_value)

    def _gps_calibration_button_pressed(self):
        """
        Handle the logic when the "Auto by GPS" button is pressed.
        Requests the device to calculate the calibration value based on GPS data.
        """
        self.gps_cal_value_button.focus_set()
        # Disabling possibility to change settings while GPS calibration is running
        self.change_state("disabled")

        self.device.run_gps_calibration()

        self.gps_cal_value_button.configure(
            state="disabled",
            text="Waiting...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        )

    def _gps_calibration_initiated(self):
        """
        Handle the events when GPS calibration is initiated.
        Updates the button appearance to indicate that calibration is in progress.
        """
        self.gps_cal_value_button.after(0, lambda: self.gps_cal_value_button.configure(
            state="disabled",
            text="Calibration...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        ))

    def _gps_calibration_error_handle(self):
        """
        Handle the events when GPS calibration fails.
        Updates the button appearance to indicate failure resets it after 2 seconds.
        """
        self.gps_cal_value_button.after(0, lambda: self.gps_cal_value_button.configure(
            state="disabled",
            text="Failed!",
            fg_color=["#D9534F", "#A94442"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        ))
        # After 2 seconds, restore "Auto by GPS" button to its default state
        self.gps_cal_value_button.after(2000, self._gps_calibration_button_default_state)

    def _gps_calibration_finished(self):
        """
        Handle the events when GPS calibration is successfully completed.
        Updates the button appearance to indicate success and resets it after 2 seconds.
        """
        self.gps_cal_value_button.after(0, lambda: self.gps_cal_value_button.configure(
            state="disabled",
            text="Calibrated!",
            fg_color=["#3BAA5D", "#2E8B57"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        ))
        # After 2 seconds, restore "Auto by GPS" button to its default state
        self.gps_cal_value_button.after(2000, self._gps_calibration_button_default_state)

    def _gps_calibration_button_default_state(self):
        """
        Restore the "Auto by GPS" button to its default state after calibration is complete.
        """
        self.gps_cal_value_button.after(0, lambda: self.gps_cal_value_button.configure(
            state="normal",
            text="Auto by GPS",
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            text_color_disabled=["#BDBDBD", "#999999"]
        ))
        self.change_state("normal")

    def _wifi_change_state(self, state):
        """
        Change the state of Wi-Fi-related UI elements.
        Updates the state of the Wi-Fi connection button, SSID entry, password entry, and the Wi-Fi
        auto-connect at startup option.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(state=state))
        self.ssid_entry.after(0, lambda: self.ssid_entry.configure(state=state))
        self.password_entry.after(0, lambda: self.password_entry.configure(state=state))
        self.wifi_auto_connect_at_startup_option.after(
            0, lambda: self.wifi_auto_connect_at_startup_option.configure(state=state)
        )

    def _wifi_auto_connect_at_startup_option_event(self, value):
        """
        Event handler for changing the Wi-Fi connection at device startup option.

        Args:
            value (str): Selected option for Wi-Fi connection at device startup ("Enabled" or "Disabled").
        """
        self.device.set_ssid_connect_at_startup(value == "Enabled")

    def _wifi_connection_button_pressed(self):
        """
        Handles the event when the "Connect" button is pressed.
        Attempt to connect to the specified SSID or disconnect from the currently connected network.
        """
        self.wifi_connection_button.focus_set()
        # Disabling possibility to change settings while Wi-Fi connecting/disconnecting
        self.change_state("disabled")

        self.device.set_wifi_connection(
            None if self.wifi_connection_button.cget("text") == "Disconnect"
            else WiFiCredentials(self.ssid_entry.get(), self.password_entry.get())
        )

        self.wifi_connection_button.configure(
            state="disabled",
            text="Waiting...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        )

    def _wifi_connection_initiated(self):
        """
        Handle the events when Wi-Fi connection is initiated.
        Updates the button appearance to indicate that connection is in progress.
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(
            state="disabled",
            text="Connecting...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        ))

    def _wifi_connection_error_handle(self):
        """
        Handle the event when Wi-Fi connection fails.
        Updates the button appearance to indicate failure and resets it after 2 seconds.
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(
            state="disabled",
            text="Failed!",
            fg_color=["#D9534F", "#A94442"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        ))
        # After 2 seconds, restore "Connect" button to its default state
        self.wifi_connection_button.after(2000, self._wifi_disconnected)

    def _wifi_disconnected(self):
        """
        Handle the events when the Wi-Fi connection is terminated.
        Updates the button appearance to indicate that the device is disconnected.
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(
            state="normal",
            text="Connect",
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            text_color_disabled=["#BDBDBD", "#999999"]
        ))
        self.change_state("normal")

    def _wifi_connection_pass(self):
        """
        Handle the events when Wi-Fi connection is successful.
        Updates the button appearance to indicate that the device is connected to Wi-Fi.
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(
            state="normal",
            text="Disconnect",
            fg_color=["#D9534F", "#A94442"],
            hover_color=["#9A2A2A", "#7A2A28"],
            text_color_disabled=["#BDBDBD", "#999999"]
        ))
        self.change_state("normal")

    def _wifi_update_connection_button_state(self, event=None):
        """
        Dynamically enable or disable the Wi-Fi connect button depending on whether the SSID
        and password fields are filled.
        """
        if (self.ssid_entry.get().strip() and self.password_entry.get().strip()):
            self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(state="normal"))
        else:
            self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(state="disabled"))

    def _change_ui_theme_event(self, ui_theme):
        """
        Event handler for changing the UI theme.

        Args:
            ui_theme (str): The selected theme ("Dark" or "Light").
        """
        self.ui_theme.focus_set()
        customtkinter.set_appearance_mode(ui_theme)
        self.config.set_ui_theme(ui_theme)

    def _change_ui_scaling_event(self, scaling):
        """
        Event handler for changing the UI scaling.

        Args:
            scaling (str): The selected scaling value in percentages (e.g., "100%", "120%").
        """
        self.ui_scaling_option.focus_set()
        scaling_value = int(scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(scaling_value)
        self.config.set_ui_scaling(scaling_value)
