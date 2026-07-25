# settings_page.py
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFormLayout,
    QGroupBox,
)

# Settings

# +------------------------------------------------+
# | General | Maps | Search | Appearance            |
# +------------------------------------------------+

# General:
# [ ] Start with last database
# [ ] Restore last opened map
# [ ] Confirm before applying changes

# Maps:
# Default map location:
# [________________________]

# Search:
# [ ] Include deleted files
# [ ] Search file content
# [ ] Search metadata

# Appearance:
# Theme:
# [Default ▼]

class SettingsPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)


        title = QLabel(
            "Settings"
        )

        title.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            """
        )

        layout.addWidget(
            title
        )


        self.tabs = QTabWidget()


        self.general_tab = self.create_general()

        self.maps_tab = self.create_maps()

        self.search_tab = self.create_search()

        self.appearance_tab = self.create_appearance()


        self.tabs.addTab(
            self.general_tab,
            "General"
        )

        self.tabs.addTab(
            self.maps_tab,
            "Maps"
        )

        self.tabs.addTab(
            self.search_tab,
            "Search"
        )

        self.tabs.addTab(
            self.appearance_tab,
            "Appearance"
        )


        layout.addWidget(
            self.tabs
        )


        buttons = QHBoxLayout()


        self.save_button = QPushButton(
            "Save"
        )

        self.reset_button = QPushButton(
            "Reset"
        )


        buttons.addStretch()

        buttons.addWidget(
            self.reset_button
        )

        buttons.addWidget(
            self.save_button
        )


        layout.addLayout(
            buttons
        )


    # --------------------------------------------------
    # General
    # --------------------------------------------------

    def create_general(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        group = QGroupBox(
            "Application"
        )

        form = QVBoxLayout(
            group
        )


        self.restore_session = QCheckBox(
            "Restore previous session"
        )

        self.confirm_changes = QCheckBox(
            "Confirm filesystem changes"
        )

        self.start_database = QCheckBox(
            "Open last active database"
        )


        form.addWidget(
            self.restore_session
        )

        form.addWidget(
            self.confirm_changes
        )

        form.addWidget(
            self.start_database
        )


        layout.addWidget(
            group
        )

        layout.addStretch()


        return widget


    # --------------------------------------------------
    # Maps
    # --------------------------------------------------

    def create_maps(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        group = QGroupBox(
            "Map Storage"
        )

        form = QFormLayout(
            group
        )


        self.map_location = QLineEdit()

        self.map_location.setPlaceholderText(
            "Default map location"
        )


        form.addRow(
            "Map folder:",
            self.map_location
        )


        layout.addWidget(
            group
        )

        layout.addStretch()


        return widget


    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def create_search(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        group = QGroupBox(
            "Search Options"
        )

        form = QVBoxLayout(
            group
        )


        self.include_deleted = QCheckBox(
            "Include deleted files"
        )

        self.search_metadata = QCheckBox(
            "Search metadata"
        )

        self.search_content = QCheckBox(
            "Search file contents"
        )


        form.addWidget(
            self.include_deleted
        )

        form.addWidget(
            self.search_metadata
        )

        form.addWidget(
            self.search_content
        )


        layout.addWidget(
            group
        )

        layout.addStretch()


        return widget


    # --------------------------------------------------
    # Appearance
    # --------------------------------------------------

    def create_appearance(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        form = QFormLayout()


        self.theme = QComboBox()

        self.theme.addItems(
            [
                "System",
                "Light",
                "Dark",
            ]
        )


        form.addRow(
            "Theme:",
            self.theme
        )


        layout.addLayout(
            form
        )

        layout.addStretch()


        return widget


    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def activate(self):

        pass


    def deactivate(self):

        pass