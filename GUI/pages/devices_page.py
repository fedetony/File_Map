# devices_page.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QGroupBox,
    QTextEdit,
)


class DevicesPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)


        title = QLabel(
            "Devices"
        )
        
        title.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed
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


        toolbar = QHBoxLayout()


        self.scan_button = QPushButton(
            "Rescan Devices"
        )


        toolbar.addWidget(
            self.scan_button
        )

        toolbar.addStretch()


        layout.addLayout(
            toolbar
        )


        splitter = QSplitter()


        # Device list

        devices_group = QGroupBox(
            "Detected Devices"
        )

        devices_layout = QVBoxLayout(
            devices_group
        )


        self.device_table = QTableWidget()

        self.device_table.setColumnCount(
            5
        )

        self.device_table.setHorizontalHeaderLabels(
            [
                "Device",
                "Mount",
                "Size",
                "Filesystem",
                "Maps"
            ]
        )


        devices_layout.addWidget(
            self.device_table
        )


        # Details

        details_group = QGroupBox(
            "Device Information"
        )

        details_layout = QVBoxLayout(
            details_group
        )


        self.details = QTextEdit()

        self.details.setReadOnly(
            True
        )

        self.details.setText(
            "Select a device..."
        )


        details_layout.addWidget(
            self.details
        )


        splitter.addWidget(
            devices_group
        )

        splitter.addWidget(
            details_group
        )


        splitter.setStretchFactor(
            0,
            3
        )

        splitter.setStretchFactor(
            1,
            1
        )


        layout.addWidget(
            splitter
        )


        self.load_demo()


    # --------------------------------------------------
    # Demo
    # --------------------------------------------------

    def load_demo(self):

        devices = [

            (
                "Samsung SSD",
                "C:\\",
                "1 TB",
                "NTFS",
                "System"
            ),

            (
                "External HDD",
                "D:\\",
                "4 TB",
                "NTFS",
                "Music, Photos"
            ),

            (
                "USB Backup",
                "E:\\",
                "512 GB",
                "exFAT",
                "Backup"
            ),

        ]


        self.device_table.setRowCount(
            len(devices)
        )


        for row, data in enumerate(devices):

            for col, value in enumerate(data):

                self.device_table.setItem(
                    row,
                    col,
                    QTableWidgetItem(value)
                )


    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def activate(self):

        pass


    def deactivate(self):

        pass