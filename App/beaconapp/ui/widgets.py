import customtkinter
from PIL import Image


class Widgets:
    @staticmethod
    def _apply_validation(entry, validation):
        """Apply validation to an entry widget."""
        if validation:
            validate_cmd = entry.register(validation)
            entry.configure(validate="key", validatecommand=(validate_cmd, "%P"))

    @staticmethod
    def _apply_binding(widget, bind_actions):
        """
        Applies event bindings to a widget.
        """
        if bind_actions:
            # If the first element of bind_actions is a string,
            # it means we only have one event-callback pair.
            if isinstance(bind_actions[0], str):
                widget.bind(*bind_actions)
            else:
                # Otherwise, we assume bind_actions is a list of event-callback pairs.
                for action in bind_actions:
                    widget.bind(*action)

    @staticmethod
    def _set_default_value(entry, default_value):
        """Set a default value in an entry widget."""
        if default_value is not None:
            entry.insert(0, default_value)

    @staticmethod
    def create_background_frame(parent, row, padx=20, text=None, optimize_for_scrollable=False):
        """
        Creates a customizable frame with an optional label text.
        """
        # Adjust padding if it is intended for scrollable content
        padx = (20, 5) if optimize_for_scrollable else padx

        frame = customtkinter.CTkFrame(parent)
        frame.grid(row=row, column=0, padx=padx, pady=5, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        if text:
            customtkinter.CTkLabel(
                frame,
                text=text,
                anchor="w"
            ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        return frame

    @staticmethod
    def create_navigation_background_frame(parent):
        """
        Creates a navigation frame with a specific layout.
        """
        frame = customtkinter.CTkFrame(parent, corner_radius=0)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_rowconfigure(5, weight=1)

        return frame

    @staticmethod
    def create_block_label(parent, row, text):
        """
        Creates a bold label with specific styling.
        """
        label = customtkinter.CTkLabel(
            parent,
            text=text,
            compound="left",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        label.grid(row=row, column=0, padx=20, pady=(20, 5), sticky="nsew")
        return label

    @staticmethod
    def create_entry_with_background_frame_and_control_buttons(
        parent,
        row,
        text,
        state="normal",
        bind_action=None,
        validation=None,
        first_button_text=None,
        first_button_command=None,
        second_button_text=None,
        second_button_command=None,
        optimize_for_scrollable=False
    ):
        """
        Creates a background frame with a label, an entry field, and two control buttons.
        """
        background_frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )

        # Create the entry widget
        entry = customtkinter.CTkEntry(background_frame, width=160, state=state)
        entry.grid(row=0, column=3, padx=(0, 10), pady=5)
        Widgets._apply_binding(entry, bind_action)
        Widgets._apply_validation(entry, validation)

        # First control button
        first_control_button = customtkinter.CTkButton(
            background_frame,
            width=25,
            text=first_button_text,
            state=state,
            command=first_button_command
        )
        first_control_button.grid(row=0, column=2, padx=(0, 5), pady=5)

        # Second control button
        second_control_button = customtkinter.CTkButton(
            background_frame,
            width=25,
            text=second_button_text,
            state=state,
            command=second_button_command
        )
        second_control_button.grid(row=0, column=1, padx=(0, 5), pady=5)

        return entry, first_control_button, second_control_button

    @staticmethod
    def create_entry_with_background_frame(
        parent,
        row,
        text,
        placeholder_text=None,
        state="normal",
        bind_action=None,
        validation=None,
        optimize_for_scrollable=False
    ):
        """
        Creates a background frame with a label and an entry widget.
        """
        frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )
        entry = customtkinter.CTkEntry(
            frame,
            placeholder_text=placeholder_text,
            state=state,
            width=160
        )
        entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")

        Widgets._apply_validation(entry, validation)
        Widgets._apply_binding(entry, bind_action)

        return entry

    @staticmethod
    def create_logo_label(parent, text, image_path):
        """
        Creates and places the application logo label.
        """
        logo_image = customtkinter.CTkImage(
            Image.open(image_path), size=(45, 45)
        )
        logo_label = customtkinter.CTkLabel(
            parent,
            text=f"  {text}",
            image=logo_image,
            compound="left",
            font=customtkinter.CTkFont(size=15, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=20)

    @staticmethod
    def create_option_menu_with_background_frame(
        parent,
        row,
        text,
        values,
        command,
        default_value=None,
        state="normal",
        optimize_for_scrollable=False
    ):
        """
        Creates a background frame with a label and an option menu.
        """
        frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )
        option_menu = customtkinter.CTkOptionMenu(
            frame,
            values=values,
            command=command,
            width=160,
            anchor="w",
            state=state,
            dynamic_resizing=False
        )
        option_menu.grid(row=0, column=1, padx=(0, 10), sticky="w")

        if default_value:
            option_menu.set(default_value)

        return option_menu

    @staticmethod
    def create_option_menu_with_button(
        parent,
        row,
        text,
        options,
        option_command,
        button_text,
        button_command,
        option_state="normal",
        option_default_value=None,
        button_state="normal",
        optimize_for_scrollable=False
    ):
        """
        Creates a background frame with a label, an option menu, and a button.
        """
        frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )

        option_menu = customtkinter.CTkOptionMenu(
            frame,
            values=options,
            command=option_command,
            width=160,
            anchor="w",
            state=option_state,
            dynamic_resizing=False
        )
        option_menu.grid(row=0, column=1, padx=(0, 10), sticky="w")

        if option_default_value:
            option_menu.set(option_default_value)

        button = customtkinter.CTkButton(
            frame,
            text=button_text,
            width=90,
            state=button_state,
            command=button_command
        )
        button.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")

        return button, option_menu

    @staticmethod
    def create_entry_with_button(
        parent,
        row,
        text,
        button_text,
        button_state,
        button_command,
        entry_state="normal",
        entry_validation=None,
        entry_bind_action=None,
        entry_default_value=None,
        optimize_for_scrollable=False
    ):
        """
        Creates a background frame with a label, an entry, and a button.
        """
        frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )

        entry = customtkinter.CTkEntry(frame, width=160)
        entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")

        Widgets._set_default_value(entry, entry_default_value)
        if entry_state:
            entry.configure(state=entry_state)

        Widgets._apply_validation(entry, entry_validation)
        Widgets._apply_binding(entry, entry_bind_action)

        button = customtkinter.CTkButton(
            frame,
            text=button_text,
            width=90,
            state=button_state,
            command=button_command
        )
        button.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")

        return button, entry

    @staticmethod
    def create_entry_with_label(
        parent,
        row,
        text,
        default_value=None,
        state=None,
        validation=None,
        bind_action=None
    ):
        """
        Creates a label and an entry widget in a single row.
        """
        customtkinter.CTkLabel(
            parent,
            text=text,
            anchor="w"
        ).grid(row=row, column=0, pady=2, sticky="w")

        entry = customtkinter.CTkEntry(parent, width=160)
        entry.grid(row=row, column=1, pady=2, sticky="w")

        Widgets._set_default_value(entry, default_value)
        Widgets._apply_validation(entry, validation)
        Widgets._apply_binding(entry, bind_action)

        if state:
            entry.configure(state=state)

        return entry

    @staticmethod
    def create_option_menu_with_label(
        parent,
        row,
        text,
        values,
        default_value=None,
        state="normal",
        command=None
    ):
        """
        Creates a label and an option menu widget in a single row.
        """
        customtkinter.CTkLabel(parent, text=text, anchor="w").grid(row=row, column=0, pady=2, sticky="w")

        option_menu = customtkinter.CTkOptionMenu(
            parent,
            width=160,
            values=values,
            command=command,
            state=state
        )
        option_menu.grid(row=row, column=1, sticky="w")

        if default_value:
            option_menu.set(default_value)

        return option_menu

    @staticmethod
    def create_general_frame(parent, row=0, scrollable=False):
        """
        Creates a general-purpose frame, which can be either scrollable or static.
        """
        frame_class = customtkinter.CTkScrollableFrame if scrollable else customtkinter.CTkFrame
        frame = frame_class(
            parent,
            corner_radius=0,
            fg_color="transparent",
            height=10
        )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid(row=row, column=0, sticky="nsew")

        return frame

    @staticmethod
    def create_navigation_button(parent, row, text, light_image, dark_image, command):
        """
        Creates a navigation button with dynamic images for light and dark themes.

        Args:
            parent: The parent widget where the button will be placed.
            row: The row in the parent's grid layout to place the button.
            text: The text to display on the button.
            light_image: The image path for light theme.
            dark_image: The image path for dark theme.
            command: The function to call when the button is pressed.

        Returns:
            The created navigation button.
        """
        image = customtkinter.CTkImage(
            light_image=Image.open(light_image),
            dark_image=Image.open(dark_image),
            size=(20, 20)
        )
        button = customtkinter.CTkButton(
            parent,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text=text,
            fg_color="transparent",
            text_color=["#1A1A1A", "#E5E5E5"],
            hover_color=["#B3B3B3", "#4D4D4D"],
            image=image,
            anchor="w",
            command=command
        )
        button.grid(row=row, column=0, sticky="ew")

        return button

    @staticmethod
    def create_tab_view(parent, row, tabs, state=None):
        """
        Creates a tab view widget and adds the specified tabs.
        """
        tab_view = customtkinter.CTkTabview(parent)
        tab_view.grid(row=row, column=0, padx=20, sticky="nsew")

        for tab_name in tabs:
            tab_view.add(tab_name)
            tab_view.tab(tab_name).grid_columnconfigure(0, weight=1)

        if state:
            tab_view.configure(state=state)

        return tab_view

    @staticmethod
    def create_status_label(parent, text, column, padx):
        """
        Creates a small status label.
        """
        label = customtkinter.CTkLabel(
            parent,
            width=70,
            text=text,
            corner_radius=6,
            fg_color=["#BFBFBF", "#4D4D4D"],
            text_color=["#DCE4EE", "#DCE4EE"]
        )
        label.grid(row=0, column=column, padx=padx, sticky="w")
        return label

    @staticmethod
    def create_connection_status_label(parent):
        label = customtkinter.CTkLabel(
            parent,
            text="Not connected!",
            corner_radius=6,
            width=180,
            fg_color=["#3B8ED0", "#1F6AA5"],
            text_color=["#DCE4EE", "#DCE4EE"]
        )
        label.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        return label
    
    @staticmethod
    def create_button_with_action_status(parent, text, button_text, button_command):
        background_frame = Widgets.create_background_frame(
            parent,
            row=1,
            text=text
        )

        action_label = customtkinter.CTkLabel(
            background_frame,
            width=160,
            text="",
            anchor="w"
        )
        action_label.grid(row=0, column=0, padx=(80, 0), pady=5, sticky="w")

        button = customtkinter.CTkButton(
            background_frame,
            width=160,
            text=button_text,
            state="disabled",
            command=button_command
        )
        button.grid(row=0, column=1, padx=(0, 10), pady=5)

        return action_label, button