# home_page.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)


class HomePage(QWidget):

    openPage = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)

        layout.setSpacing(15)


        title = QLabel(
            "File Mapping Tool"
        )
        
        title.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        title.setStyleSheet(
            """
            font-size: 28px;
            font-weight: bold;
            """
        )


        subtitle = QLabel(
            "Manage databases, maps, devices and file searches"
        )


        layout.addWidget(title)
        layout.addWidget(subtitle)


        layout.addSpacing(20)


        # -----------------------------
        # Quick actions
        # -----------------------------

        actions = QHBoxLayout()


        self.database_btn = QPushButton(
            "Databases"
        )

        self.mapping_btn = QPushButton(
            "Mapping"
        )

        self.sort_btn = QPushButton(
            "Sort Files"
        )

        self.devices_btn = QPushButton(
            "Devices"
        )


        actions.addWidget(
            self.database_btn
        )

        actions.addWidget(
            self.mapping_btn
        )

        actions.addWidget(
            self.sort_btn
        )

        actions.addWidget(
            self.devices_btn
        )


        layout.addLayout(
            actions
        )


        self.database_btn.clicked.connect(
            lambda: self.openPage.emit(
                "Databases"
            )
        )

        self.mapping_btn.clicked.connect(
            lambda: self.openPage.emit(
                "Mapping"
            )
        )

        self.sort_btn.clicked.connect(
            lambda: self.openPage.emit(
                "Sort"
            )
        )

        self.devices_btn.clicked.connect(
            lambda: self.openPage.emit(
                "Devices"
            )
        )


        layout.addSpacing(25)


        # -----------------------------
        # Information cards
        # -----------------------------

        info = QHBoxLayout()


        self.db_card = self.create_card(
            "Databases",
            "No active database"
        )

        self.map_card = self.create_card(
            "Maps",
            "No map selected"
        )

        self.device_card = self.create_card(
            "Devices",
            "No devices scanned"
        )


        info.addWidget(
            self.db_card
        )

        info.addWidget(
            self.map_card
        )

        info.addWidget(
            self.device_card
        )


        layout.addLayout(
            info
        )


        layout.addStretch()


        footer = QLabel(
            "Ready"
        )

        self.status_label = footer


        layout.addWidget(
            footer
        )


    # --------------------------------------------------
    # Cards
    # --------------------------------------------------

    def create_card(self, title, text):

        frame = QFrame()

        frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        frame.setMinimumHeight(
            120
        )

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )


        layout = QVBoxLayout(
            frame
        )


        header = QLabel(
            title
        )

        header.setStyleSheet(
            """
            font-weight:bold;
            font-size:16px;
            """
        )


        value = QLabel(
            text
        )


        layout.addWidget(
            header
        )

        layout.addWidget(
            value
        )


        return frame


    # --------------------------------------------------
    # Page lifecycle
    # --------------------------------------------------

    def activate(self):

        self.status_label.setText(
            "Ready"
        )


    def deactivate(self):

        pass