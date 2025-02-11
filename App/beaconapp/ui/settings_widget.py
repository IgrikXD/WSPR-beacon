from beaconapp.config import Config
from beaconapp.data_validation import DataValidation
from beaconapp.device import Device
from beaconapp.ui.widgets import Widgets

import customtkinter


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

        self.general_frame = Widgets.create_general_frame(parent, scrollable=True)

        # Device calibration label
        Widgets.create_block_label(self.general_frame, row=0, text="Device calibration")

        # Settings -> Device calibration -> SI5351 calibration mode
        self.cal_option = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=1,
            text="SI5351 calibration mode:",
            values=["Auto (by GPS)", "Manual"],
            default_value="Manual",
            state="disabled",
            command=self._calibration_change_option_event,
            optimize_for_scrollable=True
        )

        # Settings -> Device calibration -> Calibration value
        self.cal_value_entry, self.inc_cal_value_button, self.dec_cal_value_button = (
            Widgets.create_entry_with_background_frame_and_control_buttons(
                self.general_frame,
                row=2,
                text="Calibration value:",
                state="disabled",
                validation=DataValidation.validate_cal_value_input,
                bind_action=["<Return>", self._calibration_value_entry_enter_pressed],
                first_button_text="+",
                first_button_command=self._calibration_value_inc_button_pressed,
                second_button_text="-",
                second_button_command=self._calibration_value_dec_button_pressed,
                optimize_for_scrollable=True
            )
        )

        # Settings -> Device calibration -> Calibration frequency
        self.cal_frequency_button, self.cal_frequency_entry = Widgets.create_entry_with_button(
            self.general_frame,
            row=3,
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
        Widgets.create_block_label(self.general_frame, row=4, text="Device connection settings")

        # Settings -> Device connection settings -> Wi-Fi connection
        self.wifi_connection_button, self.wifi_connection_option = Widgets.create_option_menu_with_button(
            self.general_frame,
            row=5,
            text="Wi-Fi connection:",
            options=["Enable", "Disable"],
            option_default_value="Disable",
            option_state="disabled",
            option_command=self._wifi_change_option_event,
            button_text="Connect",
            button_state="disabled",
            button_command=self._wifi_connection_button_pressed,
            optimize_for_scrollable=True
        )

        # Settings -> Device connection settings -> SSID
        self.wifi_ssid_entry = Widgets.create_entry_with_background_frame(
            self.general_frame,
            row=6,
            text="SSID:",
            state="disabled",
            bind_action=["<KeyRelease>", self._wifi_update_connect_button_state],
            optimize_for_scrollable=True
        )

        # Settings -> Device connection settings -> Password
        self.wifi_password_entry = Widgets.create_entry_with_background_frame(
            self.general_frame,
            row=7,
            text="Password:",
            state="disabled",
            bind_action=["<KeyRelease>", self._wifi_update_connect_button_state],
            optimize_for_scrollable=True
        )

        # App settings label
        Widgets.create_block_label(self.general_frame, row=8, text="App settings")

        # Settings -> App settings -> App theme
        self.ui_theme = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=9,
            text="UI theme:",
            values=["Dark", "Light"],
            default_value=self.config.get_ui_theme(),
            command=self._change_ui_theme_event,
            optimize_for_scrollable=True
        )

        # Settings -> App settings -> UI scaling
        self.ui_scaling_option = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=10, text="UI scaling:",
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

    def set_calibration_freq_status(self, is_generated):
        """
        Control the calibration frequency generation process and update UI elements accordingly.

        Args:
            is_generated (bool): Indicates if the calibration frequency is currently being generated.
        """
        # The calibration mode cannot be changed while generating the calibration frequency.
        self.cal_option.configure(state="disabled" if is_generated else "normal")

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
        self.cal_value_entry.delete(0, "end")
        self.cal_value_entry.insert(0, value)

    def set_wifi_status(self, is_wifi_connected):
        """
        Update UI elements when Wi-Fi connection attempt finishes.

        Args:
            is_wifi_connected (bool): Indicates if the Wi-Fi connection was successful.
        """
        (self._wifi_connection_pass if is_wifi_connected else self._wifi_connection_error_handle)()
        # Device calibration management is allowed after the Wi-Fi connection process is completed.
        self._calibration_change_state("normal")

    def _calibration_change_option_event(self, calibration_option):
        """
        Event handler for changing the calibration mode.

        Args:
            calibration_option (str): Selected option for calibration ("Auto (by GPS)" or "Manual").
        """
        self.cal_option.focus_set()
        # The state of the "Calibration value" and "Calibration frequency" blocks depends on
        # the selected "SI5351 calibration mode" option value.
        if calibration_option == "Auto (by GPS)":
            self._calibration_elements_change_state("disabled")
            self.device.set_calibration_type(Device.CalibrationType.AUTO)
        else:
            self._calibration_elements_change_state("normal")
            self._calibration_frequency_update_generate_button_state()
            self.device.set_calibration_type(Device.CalibrationType.MANUAL)

    def _calibration_change_state(self, state):
        """
        Change the state of the calibration-related UI components.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        self.cal_option.after(0, lambda: self.cal_option.configure(state=state))
        if state == "normal":
            # The state of the "Calibration value" and "Calibration frequency" blocks depends on the selected
            # "SI5351 calibration mode" option value.
            self._calibration_elements_change_state(
                "normal" if self.cal_option.get() == "Manual" else "disabled"
            )
            self._calibration_frequency_update_generate_button_state()
        else:
            self._calibration_elements_change_state("disabled")

    def _calibration_elements_change_state(self, state):
        """
        Enable or disable calibration-related UI components.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        self.cal_value_entry.after(0, lambda: self.cal_value_entry.configure(state=state))
        self.dec_cal_value_button.after(0, lambda: self.dec_cal_value_button.configure(state=state))
        self.inc_cal_value_button.after(0, lambda: self.inc_cal_value_button.configure(state=state))
        self.cal_frequency_entry.after(0, lambda: self.cal_frequency_entry.configure(state=state))
        self.cal_frequency_button.after(0, lambda: self.cal_frequency_button.configure(state=state))

    def _calibration_frequency_button_pressed(self):
        """
        Handle the logic when the calibration frequency button is pressed (Generate or Terminate).
        """
        self.cal_frequency_button.focus_set()
        # The calibration mode cannot be changed while generating the calibration frequency.
        self.cal_option.configure(state="disabled")
        # Disabling the ability to control Wi-Fi while generating the calibration frequency
        self._wifi_change_state("disabled")

        if self.cal_frequency_button.cget("text") == "Terminate":
            self.device.gen_calibration_frequency(False)
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

        self.cal_value_entry.delete(0, "end")
        self.cal_value_entry.insert(0, str(new_value))

        self.device.set_calibration_value(new_value)

    def _wifi_change_option_event(self, wifi_option):
        """
        Event handler for changing the Wi-Fi connection option (Enable/Disable).

        Args:
            wifi_option (str): Selected Wi-Fi option ("Enable" or "Disable").
        """
        self.wifi_connection_option.focus_set()
        # The state of the "SSID" and "Password" fields depends on the selected
        # "Wi-Fi connection" option value.
        if wifi_option == "Disable":
            self._wifi_elements_change_state("disabled")
            self.device.set_wifi_connection_allowed(False)
        else:
            self._wifi_elements_change_state("normal")
            self._wifi_update_connect_button_state()
            self.device.set_wifi_connection_allowed(True)

    def _wifi_change_state(self, state):
        """
        Change the state of the Wi-Fi-related UI components.

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        self.wifi_connection_option.after(0, lambda: self.wifi_connection_option.configure(state=state))
        if state == "normal":
            # The state of the "SSID" and "Password" fields depends on the selected
            # "Wi-Fi connection" option value.
            self._wifi_elements_change_state(
                "normal" if self.wifi_connection_option.get() == "Enable" else "disabled"
            )
            self._wifi_update_connect_button_state()
        else:
            self._wifi_elements_change_state("disabled")

    def _wifi_connection_button_pressed(self):
        """
        Handle the logic when the Wi-Fi connection button is pressed.
        Attempt to connect to the specified SSID.
        """
        self.wifi_connection_button.focus_set()
        self.wifi_connection_option.configure(state="disabled")
        # Disabling the calibration feature while establishing a Wi-Fi connection.
        self._calibration_change_state("disabled")

        self.wifi_connection_button.configure(
            state="disabled",
            text="Connecting...",
            text_color_disabled=["#DCE4EE", "#DCE4EE"]
        )

        self.device.run_wifi_connection(
            self.wifi_ssid_entry.get(),
            self.wifi_password_entry.get()
        )

    def _wifi_connection_error_handle(self):
        """
        Handle UI changes if the Wi-Fi connection attempt fails.
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(
            text="FAIL!",
            fg_color=["#D9534F", "#A94442"]
        ))
        self.wifi_connection_button.after(2000, self._wifi_connection_finished)

    def _wifi_connection_finished(self):
        """
        Restore Wi-Fi connection UI elements to the default state after
        a connection attempt finishes (whether successful or not).
        """
        self.wifi_connection_option.configure(state="normal")
        self.wifi_connection_button.configure(
            state="normal",
            text="Connect",
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            text_color_disabled=["#BDBDBD", "#999999"]
        )

    def _wifi_connection_pass(self):
        """
        Handle UI changes if the Wi-Fi connection attempt is successful.
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(
            text="Connected!",
            fg_color=["#3BAA5D", "#2E8B57"]
        ))
        self.wifi_connection_button.after(2000, self._wifi_connection_finished)

    def _wifi_elements_change_state(self, state):
        """
        Enable or disable Wi-Fi-related UI fields (SSID, password, connection button).

        Args:
            state (str): The desired state ("normal" or "disabled").
        """
        self.wifi_connection_button.after(0, lambda: self.wifi_connection_button.configure(state=state))
        self.wifi_ssid_entry.after(0, lambda: self.wifi_ssid_entry.configure(state=state))
        self.wifi_password_entry.after(0, lambda: self.wifi_password_entry.configure(state=state))

    def _wifi_update_connect_button_state(self, event=None):
        """
        Dynamically enable or disable the Wi-Fi connect button
        depending on whether the SSID and password fields are filled.
        """
        if (self.wifi_ssid_entry.get().strip() and
                self.wifi_password_entry.get().strip()):
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
