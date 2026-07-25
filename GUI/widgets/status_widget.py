# status_widget.py
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)


class StatusWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            5, 0, 5, 0
        )

        self.db_label = QLabel(
            "Database: None"
        )

        self.map_label = QLabel(
            "Map: None"
        )

        self.device_label = QLabel(
            "Devices: None"
        )

        self.progress = QProgressBar()

        self.progress.setRange(
            0, 100
        )

        self.progress.setValue(
            0
        )

        layout.addWidget(
            self.db_label
        )

        layout.addWidget(
            self.map_label
        )

        layout.addWidget(
            self.device_label
        )

        layout.addWidget(
            self.progress
        )


    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def set_database(self, name):

        self.db_label.setText(
            f"Database: {name}"
        )


    def set_map(self, name):

        self.map_label.setText(
            f"Map: {name}"
        )


    def set_devices(self, text):

        self.device_label.setText(
            f"Devices: {text}"
        )


    def set_progress(self, value):

        self.progress.setValue(
            value
        )


    def reset_progress(self):

        self.progress.setValue(
            0
        )