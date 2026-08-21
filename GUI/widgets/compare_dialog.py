# compare_dialog.py
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer
from widgets.class_explorer_tree_widget import *

class CompareResultDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Map Comparison")
        self.resize(1800, 1000)

        self.build_ui()

    def build_ui(self):

        main_layout = QtWidgets.QVBoxLayout(self)

        filter_layout = QtWidgets.QHBoxLayout()

        self.cb_added = QtWidgets.QCheckBox("Added")
        self.cb_added.setChecked(True)

        self.cb_removed = QtWidgets.QCheckBox("Removed")
        self.cb_removed.setChecked(True)

        self.cb_modified = QtWidgets.QCheckBox("Modified")
        self.cb_modified.setChecked(True)

        self.cb_moved = QtWidgets.QCheckBox("Moved")
        self.cb_moved.setChecked(True)

        self.cb_renamed = QtWidgets.QCheckBox("Renamed")
        self.cb_renamed.setChecked(True)

        self.cb_unchanged = QtWidgets.QCheckBox("Unchanged")

        filter_layout.addWidget(self.cb_added)
        filter_layout.addWidget(self.cb_removed)
        filter_layout.addWidget(self.cb_modified)
        filter_layout.addWidget(self.cb_moved)
        filter_layout.addWidget(self.cb_renamed)
        filter_layout.addWidget(self.cb_unchanged)
        filter_layout.addStretch()

        self.tree_a = QtWidgets.QTreeView()
        self.tree_b = QtWidgets.QTreeView()
        # story pannel

        self.story_table = QtWidgets.QTreeWidget()

        self.story_table.setHeaderLabels(
            ["Property", "Value"]
        )
        
        
        center_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal
        )

        center_splitter.addWidget(self.tree_a)
        center_splitter.addWidget(self.story_table)
        center_splitter.addWidget(self.tree_b)

        center_splitter.setSizes([700, 400, 700])

        #statistics area
        stats_group = QtWidgets.QGroupBox(
            "Comparison Statistics"
        )

        stats_layout = QtWidgets.QGridLayout(stats_group)

        self.lbl_total = QtWidgets.QLabel("0")
        self.lbl_added = QtWidgets.QLabel("0")
        self.lbl_removed = QtWidgets.QLabel("0")
        self.lbl_modified = QtWidgets.QLabel("0")
        self.lbl_coverage = QtWidgets.QLabel("0%")

        # buttons area
        button_layout = QtWidgets.QHBoxLayout()

        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_export = QtWidgets.QPushButton("Export")
        self.btn_close = QtWidgets.QPushButton("Close")

        button_layout.addStretch()
        button_layout.addWidget(self.btn_refresh)
        button_layout.addWidget(self.btn_export)
        button_layout.addWidget(self.btn_close)

