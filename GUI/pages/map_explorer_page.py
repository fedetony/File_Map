# map_explorer_page.py
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
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QGroupBox,
)

# A few future ideas that this page is already ready for:

# Right-click menu

# Example:

# song.mp3

# → Open location
# → Copy path
# → Search same extension
# → Search in all maps
# → Compare versions
# File metadata panel

# Could become a third dock later:

# Properties

# Name:
# Path:
# Original device:
# Created:
# Modified:
# Hash:
# Multiple map comparison

# Your earlier idea:

# search selected maps

# fits perfectly here. The same table model can later display:

# song.mp3

# Found in:
# ✓ Music HDD
# ✓ Backup HDD
# ✓ Laptop

class MapExplorerPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)


        title = QLabel(
            "Map Explorer"
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


        # -----------------------------
        # Search bar
        # -----------------------------

        toolbar = QHBoxLayout()


        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Search files in this map..."
        )


        self.filter_box = QComboBox()

        self.filter_box.addItems(
            [
                "All files",
                "Images",
                "Audio",
                "Video",
                "Documents",
            ]
        )


        self.search_button = QPushButton(
            "Search"
        )


        toolbar.addWidget(
            self.search_box
        )

        toolbar.addWidget(
            self.filter_box
        )

        toolbar.addWidget(
            self.search_button
        )


        layout.addLayout(
            toolbar
        )


        # -----------------------------
        # Main explorer
        # -----------------------------

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )


        # Folder tree

        folder_group = QGroupBox(
            "Folders"
        )

        folder_layout = QVBoxLayout(
            folder_group
        )


        self.folder_tree = QTreeWidget()

        self.folder_tree.setHeaderHidden(
            True
        )


        folder_layout.addWidget(
            self.folder_tree
        )


        # Files

        files_group = QGroupBox(
            "Files"
        )

        files_layout = QVBoxLayout(
            files_group
        )


        self.file_table = QTableWidget()

        self.file_table.setColumnCount(
            5
        )

        self.file_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Extension",
                "Size",
                "Created",
                "Modified",
            ]
        )


        self.file_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )


        self.file_table.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )


        files_layout.addWidget(
            self.file_table
        )


        splitter.addWidget(
            folder_group
        )

        splitter.addWidget(
            files_group
        )


        splitter.setStretchFactor(
            0,
            1
        )

        splitter.setStretchFactor(
            1,
            3
        )


        layout.addWidget(
            splitter
        )


        # -----------------------------
        # Actions
        # -----------------------------

        actions = QHBoxLayout()


        self.back_button = QPushButton(
            "Back"
        )

        self.open_button = QPushButton(
            "Open"
        )

        self.search_selected_button = QPushButton(
            "Search Selected"
        )


        actions.addWidget(
            self.back_button
        )

        actions.addWidget(
            self.open_button
        )

        actions.addWidget(
            self.search_selected_button
        )

        actions.addStretch()


        layout.addLayout(
            actions
        )


        self.load_demo()


    # --------------------------------------------------
    # Demo data
    # --------------------------------------------------

    def load_demo(self):

        root = QTreeWidgetItem(
            [
                "Music"
            ]
        )

        rock = QTreeWidgetItem(
            [
                "Rock"
            ]
        )

        jazz = QTreeWidgetItem(
            [
                "Jazz"
            ]
        )

        root.addChild(
            rock
        )

        root.addChild(
            jazz
        )

        self.folder_tree.addTopLevelItem(
            root
        )

        root.setExpanded(
            True
        )


        files = [

            (
                "song.mp3",
                "mp3",
                "5 MB",
                "2021",
                "2025",
            ),

            (
                "album.flac",
                "flac",
                "80 MB",
                "2020",
                "2025",
            ),

            (
                "cover.jpg",
                "jpg",
                "2 MB",
                "2020",
                "2024",
            ),

        ]


        self.file_table.setRowCount(
            len(files)
        )


        for row, data in enumerate(files):

            for col, value in enumerate(data):

                self.file_table.setItem(
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