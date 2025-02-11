from beaconapp.tx_mode import ActiveTXMode
from beaconapp.ui.widgets import Widgets
from beaconapp.wsprlive_api import WsprLiveApi

import copy
import customtkinter
import threading


class SpotsDatabaseWidget:
    def __init__(self, parent):
        """
        Initialize the SpotsDatabaseWidget.

        Args:
            parent: The parent widget that this frame will be placed into.
        """
        # Set empty active TX mode by default
        self.active_tx_mode = ActiveTXMode()

        self.general_frame = Widgets.create_general_frame(parent)
        self.general_frame.grid_rowconfigure(5, weight=1)

        # Spots database -> Extract the spot list for the active mode label
        Widgets.create_block_label(
            self.general_frame,
            row=0,
            text="Extract the spot list for the active mode from WSPR.live"
        )

        # Spots database -> Extract spots list for active mode -> Extract latest
        self.extract_button, self.extract_latest_option = Widgets.create_option_menu_with_button(
            self.general_frame,
            row=1,
            text="Extract the latest:",
            options=["10 entries", "30 entries", "50 entries"],
            option_default_value="10 entries",
            option_state="disabled",
            option_command=None,
            button_text="Extract",
            button_state="disabled",
            button_command=self._extract_button_pressed
        )

        # Spots database -> Extract spots list for active mode -> Sort by
        self.sort_by_option = Widgets.create_option_menu_with_background_frame(
            self.general_frame,
            row=2,
            text="Sort by:",
            values=["Time", "SNR", "Drift", "Distance"],
            default_value="Distance",
            state="disabled",
            command=None
        )

        # Spots database -> Extract spots list for active mode -> Spots table header
        self.spots_table_headers = self._create_table_headers(row=4)

        # Spots database -> Extract spots list for active mode -> Spots table body
        self.spots_table_body = Widgets.create_general_frame(self.general_frame, row=5, scrollable=True)

    def change_state(self, state):
        """
        Enable or disable the UI components based on the given state.

        Args:
            state: The desired state ("normal" or "disabled").
        """
        self.extract_button.after(0, lambda: self.extract_button.configure(state=state))
        self.extract_latest_option.after(0, lambda: self.extract_latest_option.configure(state=state))
        self.sort_by_option.after(0, lambda: self.sort_by_option.configure(state=state))
        if state == "disabled":
            self.spots_table_body.after(0, self._clear_table_data)

    def set_active_tx_mode(self, active_tx_mode: ActiveTXMode):
        """
        Sets the active transmission mode for the spots data extraction.

        Args:
            active_tx_mode: An instance of the ActiveTXMode class that holds the current transmission mode details.
        """
        self.active_tx_mode = copy.deepcopy(active_tx_mode)

        self.change_state("normal" if active_tx_mode.transmission_mode else "disabled")

    def _extract_spots_data(self, active_tx_mode: ActiveTXMode):
        """
        Fetch and display spots data based on the active transmission mode.

        Args:
            active_tx_mode: An object containing active transmission mode details.
        """
        try:
            extracted_data = WsprLiveApi.get_wspr_spots_data(
                active_tx_mode.active_band,
                active_tx_mode.tx_call,
                self.sort_by_option.get().lower(),
                "ASC" if self.sort_by_option.get() == "SNR" else "DESC",
                self.extract_latest_option.get().split()[0]
            )
            self._spots_extraction_pass(extracted_data)
        except Exception:
            self._spots_extraction_error_handle()

    def _create_table_headers(self, row):
        """
        Creates table headers with specified column names and widths.

        Args:
            row: The row in the parent's grid layout to place the headers.

        Returns:
            A dictionary of labels with their keys representing column names.
        """
        columns = [
            ("Time", 140),
            ("TX call", 65),
            ("TX loc", 65),
            ("RX call", 65),
            ("RX loc", 65),
            ("Frequency", 70),
            ("PWR", 40),
            ("SNR", 50),
            ("Drift", 50),
            ("Distance", 75),
        ]

        frame = Widgets.create_background_frame(self.general_frame, row=row)
        labels = {}

        for idx, (key, width) in enumerate(columns):
            label = customtkinter.CTkLabel(
                frame,
                text=key,
                anchor="center",
                width=width,
                corner_radius=5,
                fg_color=["#BFBFBF", "#4D4D4D"],
                text_color=["#262626", "#D9D9D9"]
            )

            # Define padding for the first, last, and other labels
            padx = (10, 10) if idx == 0 else (5, 10) if idx == len(columns) - 1 else 5

            label.grid(row=0, column=idx, padx=padx, pady=5, sticky="w")
            labels[f"header_{key.lower().replace(' ', '_')}"] = label

        return labels

    def _add_wsprlive_record_to_table(self, row, rx_record):
        """
        Adds a WSPR.live record to the table.

        Args:
            row: The row in the parent's grid layout to place the record.
            rx_record: A dictionary containing the data for the record.
        """
        columns = [
            ("time", 140),
            ("tx_sign", 65),
            ("tx_loc", 65),
            ("rx_sign", 65),
            ("rx_loc", 65),
            ("frequency", 70),
            ("power", 40),
            ("snr", 50),
            ("drift", 50),
            ("distance", 75)
        ]

        frame = Widgets.create_background_frame(self.spots_table_body, row=row, optimize_for_scrollable=True)

        for idx, (key, width) in enumerate(columns):
            label = customtkinter.CTkLabel(
                frame,
                text=rx_record.get(key, ""),
                anchor="center",
                width=width,
                corner_radius=5
            )

            # Define padding for the first, last, and other labels
            padx = (10, 10) if idx == 0 else (5, 10) if idx == len(columns) - 1 else 5

            label.grid(row=0, column=idx, padx=padx, pady=5, sticky="w")

    def _clear_table_data(self):
        """
        Clear all spots records from the table body.
        """
        for spot_record in self.spots_table_body.winfo_children():
            spot_record.destroy()

    def _extract_button_pressed(self):
        """
        Handles the button press event for the "Extract" button.

        This function performs the following actions:
        - Disables the extract button to prevent multiple presses.
        - Changes the text and appearance of the extract button to show the extraction is in progress.
        - Starts a separate thread to fetch the WSPR spots data, so the UI remains responsive during
          the extraction process.
        """
        self.extract_button.focus_set()
        self.extract_button.configure(
            state="disabled",
            text="Extraction ...",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#DCE4EE", "#DCE4EE"])

        threading.Thread(
            target=self._extract_spots_data,
            args=(self.active_tx_mode, ),
            daemon=True
        ).start()

    def _spots_extraction_error_handle(self):
        """
        Handle errors that occur during the extraction of spots data.

        This function updates the UI to provide feedback to the user by changing
        the appearance of the extract button to indicate failure. It also ensures
        the button returns to its default state after a short delay.
        """
        self.extract_button.after(0, lambda: self.extract_button.configure(
            text="Extract fail!",
            fg_color=["#D9534F", "#A94442"])
        )
        # After 2 seconds, reset the extract button to its default state
        self.extract_button.after(2000, self._spots_extraction_finished)

    def _spots_extraction_finished(self):
        """
        Reset the extract button to its default state.
        """
        self.extract_button.configure(
            state="normal",
            text="Extract",
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color_disabled=["#BDBDBD", "#999999"]
        )

    def _spots_extraction_pass(self, data):
        """
        Handle the successful extraction of spots data.

        This function updates the UI with the extracted data and provides feedback
        to the user by changing the appearance of the extract button.

        Args:
            data: A list of dictionaries containing the WSPR spots data to display.
        """
        self.general_frame.after(0, lambda: self._update_spots_table_data(data))
        self.extract_button.after(0, lambda: self.extract_button.configure(
            text="Extracted!",
            fg_color=["#3BAA5D", "#2E8B57"])
        )
        # After 2 seconds, reset the extract button to its default state
        self.extract_button.after(2000, self._spots_extraction_finished)

    def _update_sorting_label(self, order_by):
        """
        Update the table headers to indicate the current sorting direction.
        """
        # Mapping sorting options to corresponding table header label
        labels = {
            "Distance": self.spots_table_headers["header_distance"],
            "Drift": self.spots_table_headers["header_drift"],
            "Time": self.spots_table_headers["header_time"],
            "SNR": self.spots_table_headers["header_snr"],
        }

        for key, label in labels.items():
            if key == order_by:
                # If active sotring option is SNR - add an upward arrow to table header label
                # If active sotring option is not SNR - add a downward arrow to table header label
                arrow = " ↑" if key == "SNR" else " ↓"
                label.configure(text=f"{key}{arrow}")
            else:
                # For other inactive sorting options display the name without an arrow
                label.configure(text=key)

    def _update_spots_table_data(self, data):
        """
        Update the table with a list of records.

        Args:
            data: A list of dictionaries containing the WSPR spots data to display.
        """
        self._update_sorting_label(self.sort_by_option.get())
        self._clear_table_data()
        for idx, rx_record in enumerate(data):
            self._add_wsprlive_record_to_table(row=idx, rx_record=rx_record)
