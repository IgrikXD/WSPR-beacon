from beaconapp.device import Device
from beaconapp.ui.widgets import Widgets

import os
import re
import sys


class NavigationWidget:
    def __init__(self, parent):
        """
        Initialize the NavigationWidget.

        Args:
            parent: The parent widget that this frame will be placed into.
        """
        background_frame = Widgets.create_navigation_background_frame(parent)

        # Local variable for resources directory path
        if hasattr(sys, '_MEIPASS'):
            # The application is running from an executable file generated by PyInstaller.
            resources_dir_path = os.path.join(sys._MEIPASS, "ui/resources")
        else:
            resources_dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")

        Widgets.create_logo_label(
            background_frame,
            text="BEACON.App",
            image_path=os.path.join(resources_dir_path, "beacon-app-logo.png")
        )

        # Navigation buttons configuration
        self.buttons_config = [
            (
                "Transmission",
                "transmission-mode-logo-black.png",
                "transmission-mode-logo-white.png",
                self.transmission_button_pressed,
            ),
            (
                "Spots database",
                "spots-database-logo-black.png",
                "spots-database-logo-white.png",
                self.spots_database_button_pressed,
            ),
            (
                "Self-check",
                "check-logo-black.png",
                "check-logo-white.png",
                self.self_check_button_pressed,
            ),
            (
                "Settings",
                "settings-logo-black.png",
                "settings-logo-white.png",
                self.settings_button_pressed,
            ),
        ]

        self.navigation_buttons = {}
        for idx, (text, light_img, dark_img, command) in enumerate(self.buttons_config, start=1):
            self.navigation_buttons[re.sub(r"[ -]", "_", text.lower())] = Widgets.create_navigation_button(
                parent=background_frame,
                row=idx,
                text=text,
                light_image=os.path.join(resources_dir_path, light_img),
                dark_image=os.path.join(resources_dir_path, dark_img),
                command=command
            )

        # Device connection status
        self.device_connection_status = Widgets.create_connection_status_label(background_frame)

    def set_navigated_frames(self, **frames):
        """
        Set references to the navigated frames.

        Args:
            frames: Dictionary of frame names and their general_frame attributes.
        """
        self.frames = {name: frame.general_frame for name, frame in frames.items()}

    def set_connection_status(self, connection_type: Device.ConnectionType):
        """
        Updates the device connection status label to reflect the current connection type.

        Args:
            connection_type (Device.ConnectionType): The type of connection to display (e.g., USB, WIFI).
        """
        self.device_connection_status.after(
            0,
            lambda: self.device_connection_status.configure(text=f"Connected ({connection_type.name})")
        )

    def select_frame_by_name(self, name):
        """
        Select and display a frame by its name, hiding others.

        Args:
            name: The name of the frame to display.
        """
        for element_name, button in self.navigation_buttons.items():
            button.configure(fg_color=["#BFBFBF", "#404040"] if element_name == name else "transparent")
            if element_name == name:
                self.frames[element_name].grid(row=0, column=1, sticky="nsew")
                self.frames[element_name].focus_set()
            else:
                self.frames[element_name].grid_forget()

    def transmission_button_pressed(self):
        self.select_frame_by_name("transmission")

    def spots_database_button_pressed(self):
        self.select_frame_by_name("spots_database")

    def self_check_button_pressed(self):
        self.select_frame_by_name("self_check")

    def settings_button_pressed(self):
        self.select_frame_by_name("settings")
