# repeated_duplicate_dialog.py
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer
from widgets.class_explorer_tree_widget import *

class RepeatedDuplicateResultDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Repeated and Duplicate Files"
        )

        self.resize(1400, 900)

        self.build_ui()

    def build_ui(self):
        # toolbar 
        toolbar_layout = QtWidgets.QHBoxLayout()

        self.btn_keep_newest = QtWidgets.QPushButton(
            "Keep Newest"
        )
        self.btn_keep_oldest = QtWidgets.QPushButton(
            "Keep Oldest"
        )

        self.btn_select_all = QtWidgets.QPushButton(
            "Select All"
        )

        self.btn_select_none = QtWidgets.QPushButton(
            "Select None"
        )
        #main result tree
        self.results_tree = QtWidgets.QTreeWidget()
        # tree structure different for repeated and duplictes
        # Repeated Files
        # └─ MD5
        #     ├─ file1
        #     ├─ file2

        # Duplicate Files
        # └─ Folder
        #     ├─ fileA
        #     ├─ fileB

        self.results_tree.setColumnCount(5)

        self.results_tree.setHeaderLabels([
            "Action",
            "File",
            "Size",
            "Modified",
            "Location"
        ])

        # summary area
        summary_group = QtWidgets.QGroupBox(
            "Selection Summary"
        )

        self.lbl_groups = QtWidgets.QLabel("Groups: 0")
        self.lbl_files = QtWidgets.QLabel("Files: 0")
        self.lbl_space = QtWidgets.QLabel("Space: 0 MB")
