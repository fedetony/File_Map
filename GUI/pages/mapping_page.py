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
    QTreeView,
)

from functional.class_icons import Icons
from controllers.class_filemap_cli_manager import FileMapCliManager
from widgets.ask_confirmation_dialog import ConfirmationDialog
from widgets.class_mapping_menu import MappingMenu

class MappingPage(QWidget):

    def __init__(self, fmap:FileMapCliManager, parent=None):
        super().__init__(parent)
        
        self.icons =Icons()
        self.fmap = fmap

        self.create_ui()
        self.connect_objects()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)
        # Header
        header= QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(self.icons.icon("mapping").pixmap(32, 32))
        title = QLabel("Mapping")
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
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

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

        self.mapping_tv_obj = QTreeView()
        self.mapping_menu = MappingMenu(self.fmap,self.mapping_tv_obj)

        maps_layout.addWidget(self.mapping_tv_obj)
        
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
    
    def connect_objects(self):
        #self.mapping_menu.__signal__.connect(self.change_page)
        pass

    def refresh_mapping_struct(self,activate_deactivate:bool=None):
        self.mapping_menu.generate_mapping_struct()
        
    # --------------------------------------------------
    # Page lifecycle
    # --------------------------------------------------

    def activate(self):
        pass

    def deactivate(self):
        pass