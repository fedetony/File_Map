# database_page.py
from PyQt6.QtCore import Qt
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSplitter,
    QTextEdit,
)

# Old:
# class DatabaseManagerDock(QDockWidget):
# becomes:
# class DatabasePage(QWidget):
# Then:
# setWidget(...) disappears
# show()/hide() disappears
# the controller stays
# The logic can move almost unchanged.

class DatabasePage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)

        # Header
        title = QLabel(
            "Database Manager"
        )

        title.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            """
        )
        title.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        layout.addWidget(title)


        # Toolbar
        toolbar = QHBoxLayout()


        self.new_btn = QPushButton(
            "New Database"
        )

        self.activate_btn = QPushButton(
            "Activate"
        )

        self.deactivate_btn = QPushButton(
            "Deactivate"
        )

        self.refresh_btn = QPushButton(
            "Refresh"
        )


        toolbar.addWidget(
            self.new_btn
        )

        toolbar.addWidget(
            self.activate_btn
        )

        toolbar.addWidget(
            self.deactivate_btn
        )

        toolbar.addWidget(
            self.refresh_btn
        )

        toolbar.addStretch()


        layout.addLayout(
            toolbar
        )


        # Main area

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )


        # Database list

        db_group = QGroupBox(
            "Databases"
        )

        db_layout = QVBoxLayout(
            db_group
        )


        self.database_table = QTableWidget()

        self.database_table.setColumnCount(
            4
        )

        self.database_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Location",
                "Maps",
                "Active"
            ]
        )


        db_layout.addWidget(
            self.database_table
        )


        # Details

        details_group = QGroupBox(
            "Database Information"
        )

        details_layout = QVBoxLayout(
            details_group
        )


        self.details = QTextEdit()

        self.details.setReadOnly(
            True
        )

        self.details.setText(
            "Select a database..."
        )


        details_layout.addWidget(
            self.details
        )


        splitter.addWidget(
            db_group
        )

        splitter.addWidget(
            details_group
        )


        splitter.setStretchFactor(
            0,
            2
        )

        splitter.setStretchFactor(
            1,
            1
        )


        layout.addWidget(
            splitter
        )


        # Demo data
        self.load_demo()


    # --------------------------------------------------
    # Demo / placeholder
    # --------------------------------------------------

    def load_demo(self):

        databases = [
            (
                "Music",
                "D:/MusicMap",
                "12",
                "Yes"
            ),
            (
                "Backup",
                "E:/BackupMap",
                "5",
                "No"
            ),
        ]


        self.database_table.setRowCount(
            len(databases)
        )


        for row, data in enumerate(databases):

            for col, value in enumerate(data):

                self.database_table.setItem(
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