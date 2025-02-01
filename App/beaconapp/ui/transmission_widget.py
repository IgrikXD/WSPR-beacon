from beaconapp.config import Config
from beaconapp.data_validation import DataValidation
from beaconapp.device import Device
from beaconapp.tx_mode import ActiveTXMode, TransmissionMode
from beaconapp.ui.widgets import Widgets

import copy
import customtkinter


class TransmissionWidget:
    def __init__(self, parent, device: Device, config: Config):
        """
        Initialize the TransmissionWidget.

        Args:
            parent: The parent widget that this frame will be placed into.
            device (Device): An instance of the Device class to interact with the hardware.
            config (Config): An instance of the Config class containing default transmission
            paramaters. Used also to update default transmission parameters based on the latest
            active mode parameters applied to the device.
        """
        self.device = device
        self.config = config
        # Load active TX mode from default config
        self.active_tx_mode = config.get_active_mode_parameters()

        self.general_frame = Widgets.create_general_frame(parent)

        # Transmission mode label
        Widgets.create_block_label(self.general_frame, row=0, text="Transmission mode")

        # Transmission mode selector
        self.mode_selection_view = Widgets.create_tab_view(
            self.general_frame,
            row=1,
            state="disabled",
            tabs=["WSPR"]
        )

        # WSPR mode frame
        wspr_mode_frame = Widgets.create_background_frame(self.mode_selection_view.tab("WSPR"), row=1, padx=10)

        # WSPR mode -> TX Call
        self.wspr_tx_call_entry = Widgets.create_entry_with_label(
            wspr_mode_frame,
            row=0,
            text="TX call:",
            default_value=self.active_tx_mode.tx_call,
            state="disabled",
            validation=DataValidation.validate_tx_call_input,
            bind_action=["<KeyRelease>", self._check_if_wspr_mode_parameters_changed]
        )

        # WSPR _changedmode -> QTH locator
        self.wspr_qth_locator_entry = Widgets.create_entry_with_label(
            wspr_mode_frame,
            row=1,
            text="QTH locator:",
            default_value=self.active_tx_mode.qth_locator,
            state="disabled",
            validation=DataValidation.validate_qth_locator_input,
            bind_action=["<KeyRelease>", self._check_if_wspr_mode_parameters_changed]
        )

        # WSPR _changedmode -> Output power
        self.wspr_output_power_entry = Widgets.create_entry_with_label(
            wspr_mode_frame,
            row=2,
            text="Output power, dBm:",
            default_value=self.active_tx_mode.output_power,
            state="disabled",
            validation=DataValidation.validate_output_power_input,
            bind_action=["<KeyRelease>", self._check_if_wspr_mode_parameters_changed]
        )

        # WSPR mode -> Transmit every
        self.wspr_transmit_every_option = Widgets.create_option_menu_with_label(
            wspr_mode_frame,
            row=3,
            text="Transmit every:",
            values=["2 minutes", "10 minutes", "30 minutes", "60 minutes"],
            default_value=self.active_tx_mode.transmit_every,
            state="disabled",
            command=self._check_if_wspr_mode_parameters_changed
        )

        # WSPR _changedmode -> Active band
        self.wspr_active_band_option = Widgets.create_option_menu_with_label(
            wspr_mode_frame,
            row=4,
            text="Active band:",
            values=["2200m", "600m", "160m", "80m", "60m",
                    "40m", "30m", "20m", "17m", "15m",
                    "12m", "10m", "6m", "4m", "2m"],
            default_value=self.active_tx_mode.active_band,
            state="disabled",
            command=self._check_if_wspr_mode_parameters_changed
        )

        # WSPR _changedmode -> Set as active mode
        self.wspr_set_as_active_mode_button = customtkinter.CTkButton(
            self.mode_selection_view.tab("WSPR"),
            width=200,
            text="Set as active mode",
            state="disabled",
            command=self._wspr_set_as_active_mode_button_pressed
        )
        self.wspr_set_as_active_mode_button.grid(row=5, column=0, pady=(15, 0))

        # Transmission details label
        Widgets.create_block_label(self.general_frame, row=2, text="Transmission details")

        # Transmisson -> Transmission details -> Active mode details
        tx_message_background_frame = Widgets.create_background_frame(
            self.general_frame,
            row=3,
            text="Active mode details:"
        )

        self.tx_message_entry = customtkinter.CTkEntry(
            tx_message_background_frame,
            width=220,
            state="disabled"
        )
        self.tx_message_entry.grid(row=0, column=2, padx=(0, 10), pady=5)

        # Transmisson -> Transmission details -> Active mode details -> Reset mode button
        self.reset_mode_button = customtkinter.CTkButton(
            tx_message_background_frame, width=90,
            text="Reset mode",
            state="disabled",
            command=self._reset_mode_button_pressed
        )
        self.reset_mode_button.grid(row=0, column=1, padx=(0, 5), pady=5)

        # Transmisson -> Transmission details-> TX status
        tx_status_background_frame = Widgets.create_background_frame(
            self.general_frame,
            row=4,
            text="TX status:"
        )

        # Transmisson -> Transmission details-> TX status action status label
        self.tx_status_action_label = customtkinter.CTkLabel(
            tx_status_background_frame,
            width=160,
            text="",
            anchor="w"
        )
        self.tx_status_action_label.grid(row=0, column=0, padx=(75, 0), pady=5, sticky="w")

        # Transmisson -> Transmission details -> TX status -> Calibration status
        self.cal_status = Widgets.create_status_label(
            tx_status_background_frame,
            text="CAL",
            column=1,
            padx=0
        )

        # Transmisson -> Transmission details -> TX status -> GPS status
        self.gps_status = Widgets.create_status_label(
            tx_status_background_frame,
            text="GPS",
            column=1,
            padx=(75, 0)
        )

        # Transmisson -> Transmission details -> TX status -> TX status
        self.tx_status = Widgets.create_status_label(
            tx_status_background_frame,
            text="TX",
            column=1,
            padx=(150, 10)
        )

    def change_state(self, state):
        """
        Enable or disable the UI components based on the given state.

        Args:
            state: The desired state ("normal" or "disabled").
        """
        self.mode_selection_view.after(0, lambda: self.mode_selection_view.configure(state=state))
        self.wspr_tx_call_entry.after(0, lambda: self.wspr_tx_call_entry.configure(state=state))
        self.wspr_qth_locator_entry.after(0, lambda: self.wspr_qth_locator_entry.configure(state=state))
        self.wspr_output_power_entry.after(0, lambda: self.wspr_output_power_entry.configure(state=state))
        self.wspr_transmit_every_option.after(0, lambda: self.wspr_transmit_every_option.configure(state=state))
        self.wspr_active_band_option.after(0, lambda: self.wspr_active_band_option.configure(state=state))
        self.wspr_set_as_active_mode_button.after(0, lambda: self.wspr_set_as_active_mode_button.configure(state=state))

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        """
        Set the active transmission mode and update the UI.

        Args:
            active_tx_mode: An instance of ActiveTXMode containing the transmission mode parameters.
        """
        self.change_state("normal")
        self.active_tx_mode = copy.deepcopy(active_tx_mode)

        self.general_frame.after(0, self._print_active_mode_details)

        if self.active_tx_mode.transmission_mode == TransmissionMode.WSPR:
            self.general_frame.after(0, self._print_wspr_active_mode_parameters)
            self.reset_mode_button.after(0, lambda: self.reset_mode_button.configure(state="normal"))

        self.wspr_set_as_active_mode_button.after(0, self._check_if_wspr_mode_parameters_changed)

    def update_cal_status(self, cal_status):
        """
        Update the calibration status label.

        Args:
            cal_status: Boolean indicating if calibration is valid.
        """
        fg_color = ["#3BAA5D", "#2E8B57"] if cal_status else ["#BFBFBF", "#4D4D4D"]
        self.cal_status.after(0, lambda: self.cal_status.configure(fg_color=fg_color))

    def update_gps_status(self, gps_status):
        """
        Update the GPS status label.

        Args:
            gps_status: Boolean indicating if GPS is active.
        """
        fg_color = ["#3BAA5D", "#2E8B57"] if gps_status else ["#BFBFBF", "#4D4D4D"]
        self.gps_status.after(0, lambda: self.gps_status.configure(fg_color=fg_color))

    def update_tx_message_action_status(self, text):
        """
        Update the transmission action status label.

        Args:
            text: The text to display on the label.
        """
        self.tx_status_action_label.after(0, lambda: self.tx_status_action_label.configure(text=text))

    def update_tx_status(self, tx_status):
        """
        Update the transmission status label.

        Args:
            tx_status: Boolean indicating if transmission is active.
        """
        fg_color = ["#D9534F", "#A94442"] if tx_status else ["#BFBFBF", "#4D4D4D"]
        self.tx_status.after(0, lambda: self.tx_status.configure(fg_color=fg_color))

    def _check_if_wspr_mode_parameters_changed(self, event=None):
        """
        Check if the WSPR mode parameters have been modified at UI side.

        Args:
            event: Optional event parameter for key release actions (not used).
        """
        # Check whether the new values differ from the already set values of the active transmission mode
        if (self.wspr_tx_call_entry.get() != self.active_tx_mode.tx_call or
            self.wspr_qth_locator_entry.get() != self.active_tx_mode.qth_locator or
            int(self.wspr_output_power_entry.get()) != self.active_tx_mode.output_power or
            self.wspr_transmit_every_option.get() != self.active_tx_mode.transmit_every or
                self.wspr_active_band_option.get() != self.active_tx_mode.active_band):

            self.wspr_set_as_active_mode_button.configure(
                state="normal",
                text="Set as active mode",
                fg_color=["#3B8ED0", "#1F6AA5"],
                hover_color=["#36719F", "#144870"],
                text_color_disabled=["#BDBDBD", "#999999"]
            )
        else:
            self.wspr_set_as_active_mode_button.configure(
                state="disabled",
                text="Activated!",
                fg_color=["#3BAA5D", "#2E8B57"],
                hover_color=["#34A853", "#1E7045"],
                text_color_disabled=["#DCE4EE", "#DCE4EE"]
            )

    def _print_wspr_active_mode_parameters(self):
        """
        Display the current WSPR mode parameters at the UI side.
        """
        self.wspr_tx_call_entry.delete(0, "end")
        self.wspr_tx_call_entry.insert(0, self.active_tx_mode.tx_call)

        self.wspr_qth_locator_entry.delete(0, "end")
        self.wspr_qth_locator_entry.insert(0, self.active_tx_mode.qth_locator)

        self.wspr_output_power_entry.delete(0, "end")
        self.wspr_output_power_entry.insert(0, self.active_tx_mode.output_power)

        self.wspr_transmit_every_option.set(self.active_tx_mode.transmit_every)

        self.wspr_active_band_option.set(self.active_tx_mode.active_band)

    def _print_active_mode_details(self):
        """
        Display the details of the active transmission mode at the UI side.
        """
        self.tx_message_entry.configure(state="normal")
        self.tx_message_entry.delete(0, "end")

        if self.active_tx_mode.transmission_mode:
            self.tx_message_entry.insert(0, f"{self.active_tx_mode.transmission_mode.name}: "
                                            f"{self.active_tx_mode.tx_call} "
                                            f"{self.active_tx_mode.qth_locator} "
                                            f"{self.active_tx_mode.output_power}")

        self.tx_message_entry.configure(state="disabled")

    def _reset_mode_button_pressed(self):
        """
        Reset the active mode to its default state and update the UI.
        """
        self.reset_mode_button.focus_set()
        self.reset_mode_button.configure(state="disabled")

        # Clear active TX mode info
        self.active_tx_mode.clear()

        self.change_state("disabled")
        self.wspr_set_as_active_mode_button.configure(
            state="disabled",
            text="Waiting for completion...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            text_color_disabled=["#BDBDBD", "#999999"]
        )

        # Send active TX mode to device
        self.device.set_active_tx_mode(self.active_tx_mode)

    def _wspr_set_as_active_mode_button_pressed(self):
        """
        Activate the WSPR mode with the current parameters and update the UI.
        """
        self.wspr_set_as_active_mode_button.focus_set()
        self.reset_mode_button.configure(state="disabled")

        # Update active TX mode info
        self.active_tx_mode.set(
            TransmissionMode.WSPR,
            self.wspr_tx_call_entry.get(),
            self.wspr_qth_locator_entry.get(),
            int(self.wspr_output_power_entry.get()),
            self.wspr_transmit_every_option.get(),
            self.wspr_active_band_option.get()
        )

        self.change_state("disabled")
        self.wspr_set_as_active_mode_button.configure(
            state="disabled",
            text="Waiting for activation..."
        )

        # Use current active TX mode configuration as default during next app startup
        self.config.set_active_mode_parameters(self.active_tx_mode)
        # Send active TX mode to device
        self.device.set_active_tx_mode(self.active_tx_mode)
