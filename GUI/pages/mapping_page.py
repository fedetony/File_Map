# mapping_page.py
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QGroupBox,
    QTextEdit,
)


class MappingPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)
        title = QLabel("Map Explorer / Mapping")
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
        layout.addWidget(title)


        # -----------------------------
        # Search toolbar
        # -----------------------------

        toolbar = QHBoxLayout()

        self.database_selector = QComboBox()
        self.database_selector.addItem("All databases")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search maps...")
        self.search_button = QPushButton("Search")


        toolbar.addWidget(self.database_selector)
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(self.search_button)

        layout.addLayout(toolbar)

        # -----------------------------
        # Main area
        # -----------------------------
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Map table
        maps_group = QGroupBox("Available Maps")
        maps_layout = QVBoxLayout(maps_group)

        self.maps_table = QTableWidget()

        self.maps_table.setColumnCount(5)

        self.maps_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Files",
                "Size",
                "Last Scan",
                "Active"
            ]
        )

        self.maps_table.setSelectionBehavior(self.maps_table.SelectionBehavior.SelectRows)
        self.maps_table.setSelectionMode(self.maps_table.SelectionMode.ExtendedSelection)

        maps_layout.addWidget(self.maps_table)

        # Details
        details_group = QGroupBox("Map Details")

        details_layout = QVBoxLayout(details_group)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setText("Select a map to see details...")

        details_layout.addWidget(self.details)

        splitter.addWidget(maps_group)
        splitter.addWidget(details_group)


        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)


        # -----------------------------
        # Bottom actions
        # -----------------------------

        buttons = QHBoxLayout()

        self.open_button = QPushButton("Open Map")
        self.search_selected_button = QPushButton("Search Selected")
        self.search_all_button = QPushButton("Search All Maps")

        buttons.addWidget(self.open_button)

        buttons.addWidget(self.search_selected_button)

        buttons.addWidget(self.search_all_button)

        buttons.addStretch()
        layout.addLayout(buttons)
        self.load_demo()

    # --------------------------------------------------
    # Demo data
    # --------------------------------------------------

    def load_demo(self):
        maps = [

            (
                "Music",
                "120000",
                "850 GB",
                "2025-01-10",
                "Yes"
            ),

            (
                "Photos",
                "90000",
                "400 GB",
                "2025-02-03",
                "Yes"
            ),

            (
                "Backup",
                "25000",
                "2 TB",
                "2024-12-01",
                "No"
            ),

        ]
        self.maps_table.setRowCount(
            len(maps)
        )


        for row, data in enumerate(maps):
            for col, value in enumerate(data):
                self.maps_table.setItem(
                    row,
                    col,
                    QTableWidgetItem(value)
                )

    # --------------------------------------------------
    # Page lifecycle
    # --------------------------------------------------

    def activate(self):
        pass

    def deactivate(self):
        pass