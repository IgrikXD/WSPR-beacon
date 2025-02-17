from beaconapp.device import Device
from beaconapp.ui.widgets import Widgets


class SelfCheckWidget:
    def __init__(self, parent, device: Device):
        """
        Initialize the SelfCheckWidget.

        Args:
            parent: The parent widget that this frame will be placed into.
            device (Device): An instance of the Device class to interact with the hardware.
        """
        self.device = device
        self.general_frame = Widgets.create_general_frame(parent)

        # Hardware test label
        Widgets.create_block_label(self.general_frame, row=0, text="Hardware test")

        # Self-check -> Hardware test -> Self-check
        self.self_check_action_label, self.run_checks_button = Widgets.create_button_with_action_status(
            self.general_frame,
            text="Self-check:",
            button_text="Run checks",
            button_command=self._run_checks_button_pressed
        )

        # Self-check -> Hardware test -> Hardware version
        self.hardware_version_entry = Widgets.create_entry_with_background_frame(
            self.general_frame,
            row=2,
            text="Hardware version:",
            placeholder_text="N/A"
        )
        self.hardware_version_entry.configure(state="disabled")

        # Self-check -> Hardware test -> Firmware version
        self.firmware_version_entry = Widgets.create_entry_with_background_frame(
            self.general_frame,
            row=3,
            text="Firmware version:",
            placeholder_text="N/A"
        )
        self.firmware_version_entry.configure(state="disabled")

    def change_state(self, state):
        """
        Enable or disable the UI components based on the given state.

        Args:
            state: The desired state ("normal" or "disabled").
        """
        self.run_checks_button.after(0, lambda: self.run_checks_button.configure(state=state))

    def update_self_check_action_status(self, status_message):
        """
        Update the status message displayed during self-check execution.

        Args:
            status_message: The status message to display.
        """
        self.self_check_action_label.after(0, lambda: self.self_check_action_label.configure(text=status_message))

    def update_self_check_status(self, is_self_check_passed):
        """
        Update the self-check status based on the result received from the device.

        Args:
            is_self_check_passed: A boolean indicating if the self-check passed or failed.
        """
        (self._self_check_pass if is_self_check_passed else self._self_check_error_handle)()

    def update_hardware_info(self, hardware_version):
        """
        Update the displayed hardware version information.

        Args:
            hardware_version: The version of the hardware to display.
        """
        self.hardware_version_entry.after(0, lambda: self.hardware_version_entry.configure(
            state="normal",
            placeholder_text=hardware_version)
        )
        self.hardware_version_entry.after(0, lambda: self.hardware_version_entry.configure(
            state="disabled")
        )

    def update_firmware_info(self, firmware_version):
        """
        Update the displayed firmware version information.

        Args:
            firmware_version: The version of the firmware to display.
        """
        self.firmware_version_entry.after(0, lambda: self.firmware_version_entry.configure(
            state="normal",
            placeholder_text=firmware_version)
        )
        self.firmware_version_entry.after(0, lambda: self.firmware_version_entry.configure(
            state="disabled")
        )

    def _run_checks_button_pressed(self):
        """
        Handle the event when the "Run checks" button is pressed.
        Disables the button, updates its appearance, and initiates the self-check process.
        """
        self.run_checks_button.focus_set()

        self.run_checks_button.configure(
            state="disabled",
            text="Running...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"])

        self.device.run_self_check()

    def _self_check_error_handle(self):
        """
        Handle the event when the self-check fails.
        Updates the button appearance to indicate failure and resets it after 2 seconds.
        """
        self.run_checks_button.after(0, self.run_checks_button.configure(
            text="FAIL!",
            fg_color=["#D9534F", "#A94442"])
        )
        # After 2 seconds, reset the "Run checks" button to its default state
        self.run_checks_button.after(2000, self._self_check_finished)

    def _self_check_finished(self):
        """
        Reset the "Run checks" button to its default state after the self-check is completed.
        """
        self.run_checks_button.configure(
            state="normal",
            text="Run checks",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#BDBDBD", "#999999"])

    def _self_check_pass(self):
        """
        Handle the event when the self-check passes.
        Updates the button appearance to indicate success and resets it after 2 seconds.
        """
        self.self_check_action_label.after(0, lambda: self.self_check_action_label.configure(text=""))
        self.run_checks_button.after(0, lambda: self.run_checks_button.configure(
            text="PASS!",
            fg_color=["#3BAA5D", "#2E8B57"])
        )
        # After 2 seconds, reset the "Run checks" button to its default state
        self.run_checks_button.after(2000, self._self_check_finished)
