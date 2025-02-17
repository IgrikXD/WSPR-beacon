import customtkinter
from PIL import Image


class Widgets:
    @staticmethod
    def _apply_validation(entry, validation):
        """
        Applies validation to an entry widget, if a validation function is provided.

        Args:
            entry (CTkEntry): The entry widget to which validation will be applied.
            validation (callable): The validation function that should be called on key events.
        """
        if validation:
            # register() wraps the validation function so Tkinter can use it
            validate_cmd = entry.register(validation)
            # validate="key": triggers validation on each keypress
            # "%P": current text in the entry if the edit is allowed
            entry.configure(validate="key", validatecommand=(validate_cmd, "%P"))

    @staticmethod
    def _apply_binding(widget, bind_actions):
        """
        Applies event bindings to a widget.

        Args:
            widget (widget): The widget to bind events to.
            bind_actions (tuple or list of tuples): Single tuple (event, callback) or list of tuples.
        """
        if bind_actions:
            # If the first element of bind_actions is a string, treat it as a single event/callback pair
            if isinstance(bind_actions[0], str):
                widget.bind(*bind_actions)
            else:
                # Otherwise, assume it's a list of event/callback pairs
                for action in bind_actions:
                    widget.bind(*action)

    @staticmethod
    def _set_default_value(entry, default_value):
        """
        Inserts a default value into an entry widget if provided.

        Args:
            entry (CTkEntry): The entry widget to set the default value in.
            default_value (str): The default text to insert.
        """
        if default_value:
            entry.insert(0, default_value)

    @staticmethod
    def create_background_frame(parent, row, padx=20, text=None, optimize_for_scrollable=False):
        """
        Creates a reusable background frame with optional label text.
        If 'optimize_for_scrollable' is True, adjusts padding for scrollability.

        Args:
            parent (widget): Parent widget in which to place the frame.
            row (int): The row index for the grid layout.
            padx (int or tuple): Horizontal padding. Can be a single int or a (left, right) tuple.
            text (str): Optional text for a label placed at the top-left of the frame.
            optimize_for_scrollable (bool): If True, adjusts padding for scrollable areas.

        Returns:
            CTkFrame: The created frame widget.
        """
        # Adjust padding for scrollable frame usage
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
        Creates a navigation frame with a specific layout used as sidebar.

        Args:
            parent (widget): Parent widget in which to place the frame.

        Returns:
            CTkFrame: The created navigation frame widget.
        """
        frame = customtkinter.CTkFrame(parent, corner_radius=0)
        frame.grid(row=0, column=0, sticky="nsew")
        # This ensures row 5 stretches to fill available space
        frame.grid_rowconfigure(5, weight=1)

        return frame

    @staticmethod
    def create_block_label(parent, row, text):
        """
        Creates a bold label with specific styling.

        Args:
            parent (widget): Parent widget in which to place the label.
            row (int): The row index for the grid layout.
            text (str): The text to display in the label.

        Returns:
            CTkLabel: The created label widget.
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

        Args:
            parent (widget): Parent widget in which to place the elements.
            row (int): The row index for the grid layout.
            text (str): The label text.
            state (str): The state of the entry and buttons (e.g., "normal" or "disabled").
            bind_action (tuple or list): Event binding(s) for the entry.
            validation (callable): Validation function for the entry.
            first_button_text (str): Text for the first button.
            first_button_command (callable): Callback function for the first button.
            second_button_text (str): Text for the second button.
            second_button_command (callable): Callback function for the second button.
            optimize_for_scrollable (bool): If True, adjusts padding for scrollable areas.

        Returns:
            tuple: (CTkEntry, CTkButton, CTkButton)
        """
        background_frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )

        entry = customtkinter.CTkEntry(background_frame, width=160, state=state)
        entry.grid(row=0, column=3, padx=(0, 10), pady=5)

        Widgets._apply_binding(entry, bind_action)
        Widgets._apply_validation(entry, validation)

        first_control_button = customtkinter.CTkButton(
            background_frame,
            width=25,
            text=first_button_text,
            state=state,
            command=first_button_command
        )
        first_control_button.grid(row=0, column=2, padx=(0, 5), pady=5)

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
        show=None,
        placeholder_text=None,
        state="normal",
        bind_action=None,
        validation=None,
        optimize_for_scrollable=False
    ):
        """
        Creates a background frame with a label and a single entry widget.

        Args:
            parent (widget): Parent widget to contain the frame and entry.
            row (int): The row in the grid layout.
            text (str): Text for the label placed in the frame.
            show (str): Character to display instead of the actual text (e.g., "*").
            placeholder_text (str): Placeholder text for the entry.
            state (str): The entry state (e.g., "normal", "disabled").
            bind_action (tuple or list): Event binding(s) for the entry.
            validation (callable): Validation function for the entry.
            optimize_for_scrollable (bool): If True, adjusts padding for scrollable areas.

        Returns:
            CTkEntry: The created entry widget.
        """
        frame = Widgets.create_background_frame(
            parent,
            row=row,
            text=text,
            optimize_for_scrollable=optimize_for_scrollable
        )

        entry = customtkinter.CTkEntry(
            frame,
            show=show,
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
        Creates and places a logo label, with an image and text side-by-side.

        Args:
            parent (widget): The parent widget in which to place the logo label.
            text (str): The text to display beside the logo.
            image_path (str): The file path to the logo image.
        """
        # Load and resize the image
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

        Args:
            parent (widget): Parent widget to contain the frame and option menu.
            row (int): The row in the grid layout.
            text (str): The label text.
            values (list): List of option values to display.
            command (callable): Callback when an option is selected.
            default_value (str): The default selected value.
            state (str): The state of the option menu (e.g., "normal", "disabled").
            optimize_for_scrollable (bool): If True, adjusts padding for scrollable areas.

        Returns:
            CTkOptionMenu: The created option menu widget.
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
        Creates a background frame with a label, an option menu, and a button in one row.

        Args:
            parent (widget): Parent widget.
            row (int): The row in the grid layout.
            text (str): Label text for the frame.
            options (list): The list of options for the option menu.
            option_command (callable): Callback for when an option is selected.
            button_text (str): The text displayed on the button.
            button_command (callable): The function called when the button is clicked.
            option_state (str): The state of the option menu (e.g., "normal", "disabled").
            option_default_value (str): Default value for the option menu.
            button_state (str): The state of the button (e.g., "normal", "disabled").
            optimize_for_scrollable (bool): If True, adjusts padding for scrollable areas.

        Returns:
            tuple: (CTkButton, CTkOptionMenu)
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
        Creates a background frame with a label, an entry, and a button in one row.

        Args:
            parent (widget): Parent widget.
            row (int): The row in the grid layout.
            text (str): Label text in the frame.
            button_text (str): Text displayed on the button.
            button_state (str): The state of the button (e.g., "normal", "disabled").
            button_command (callable): The callback function for the button.
            entry_state (str): The state of the entry (e.g., "normal", "disabled").
            entry_validation (callable): Validation function for the entry.
            entry_bind_action (tuple or list): Event binding(s) for the entry.
            entry_default_value (str): Default text inserted into the entry.
            optimize_for_scrollable (bool): If True, adjusts padding for scrollable areas.

        Returns:
            tuple: (CTkButton, CTkEntry)
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
        Widgets._apply_validation(entry, entry_validation)
        Widgets._apply_binding(entry, entry_bind_action)

        if entry_state:
            entry.configure(state=entry_state)

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
        Creates a label and an entry widget side-by-side in a single row.

        Args:
            parent (widget): Parent widget.
            row (int): The row in the grid layout.
            text (str): The text for the label.
            default_value (str): Default text inserted into the entry.
            state (str): The state of the entry (e.g., "normal", "disabled").
            validation (callable): Validation function for the entry.
            bind_action (tuple or list): Event binding(s) for the entry.

        Returns:
            CTkEntry: The created entry widget.
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
        Creates a label and an option menu widget side-by-side in a single row.

        Args:
            parent (widget): Parent widget.
            row (int): The row in the grid layout.
            text (str): The label text.
            values (list): List of values for the option menu.
            default_value (str): Default selected value for the option menu.
            state (str): The state of the option menu (e.g., "normal" or "disabled").
            command (callable): Callback function invoked when an option is selected.

        Returns:
            CTkOptionMenu: The created option menu widget.
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
        option_menu.set(default_value)

        return option_menu

    @staticmethod
    def create_general_frame(parent, row=0, scrollable=False):
        """
        Creates a general-purpose frame, which can be scrollable or static.

        Args:
            parent (widget): Parent widget.
            row (int): The row in the grid layout where this frame will be placed.
            scrollable (bool): If True, uses CTkScrollableFrame; otherwise, CTkFrame.

        Returns:
            CTkFrame or CTkScrollableFrame: The created frame widget.
        """
        # Use scrollable frame if requested, otherwise a regular frame
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
        Creates a navigation button with light/dark theme icons.

        Args:
            parent (widget): Parent widget in which to place the button.
            row (int): Grid row to place the button in.
            text (str): Text displayed on the button.
            light_image (str): File path to the icon for light theme.
            dark_image (str): File path to the icon for dark theme.
            command (callable): Callback function when the button is clicked.

        Returns:
            CTkButton: The created navigation button.
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
        Creates a tab view and adds the specified tabs.

        Args:
            parent (widget): Parent widget.
            row (int): The row in the grid layout.
            tabs (list): List of tab names to add.
            state (str): State of the tab view (e.g., "normal" or "disabled").

        Returns:
            CTkTabview: The created tab view widget.
        """
        tab_view = customtkinter.CTkTabview(parent)
        tab_view.grid(row=row, column=0, padx=20, sticky="nsew")

        # Add each tab and configure
        for tab_name in tabs:
            tab_view.add(tab_name)
            tab_view.tab(tab_name).grid_columnconfigure(0, weight=1)

        if state:
            tab_view.configure(state=state)

        return tab_view

    @staticmethod
    def create_status_label(parent, text, column, padx):
        """
        Creates a small status label in the specified column.

        Args:
            parent (widget): Parent widget.
            text (str): Text to display in the label.
            column (int): The column in the grid layout.
            padx (int or tuple): Horizontal padding.

        Returns:
            CTkLabel: The created status label widget.
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
        """
        Creates a connection status label that displays "Not connected!" by default.

        Args:
            parent (widget): Parent widget.

        Returns:
            CTkLabel: The created connection status label widget.
        """
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
        """
        Creates a background frame with a label for action status and a button.

        Args:
            parent (widget): Parent widget.
            text (str): Label text for the frame.
            button_text (str): The text on the button.
            button_command (callable): The function called when the button is clicked.

        Returns:
            tuple: (CTkLabel, CTkButton) - The action status label and the button widget.
        """
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
