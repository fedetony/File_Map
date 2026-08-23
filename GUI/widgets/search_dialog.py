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

class SearchDialog(QtWidgets.QDialog):

    def __init__(self, db_map_pairs=None, parent=None):
        super().__init__(parent)

        self.db_map_pairs = db_map_pairs

        self.setWindowTitle("Search")
        self.resize(1600, 950)

        self.build_ui()

    def build_ui(self):
        # Query area
        query_group = QtWidgets.QGroupBox("Query")

        query_layout = QtWidgets.QGridLayout(query_group)

        self.query_edit = QtWidgets.QLineEdit()

        self.search_button = QtWidgets.QPushButton("Search")
        self.clear_button = QtWidgets.QPushButton("Clear")

        self.history_combo = QtWidgets.QComboBox()

        self.save_query_button = QtWidgets.QPushButton(
            "Save Query"
        )

        self.load_query_button = QtWidgets.QPushButton(
            "Load Query"
        )

        #validation area
        self.valid_label = QtWidgets.QLabel(
            "Query Valid: Unknown"
        )

        self.sql_preview = QtWidgets.QPlainTextEdit()
        self.sql_preview.setReadOnly(True)
        self.sql_preview.setMaximumHeight(80)

        # view filters
        filter_group = QtWidgets.QGroupBox("View Filters")

        filter_layout = QtWidgets.QHBoxLayout(filter_group)

        self.show_files_cb = QtWidgets.QCheckBox("Files")
        self.show_files_cb.setChecked(True)

        self.show_folders_cb = QtWidgets.QCheckBox("Folders")
        self.show_folders_cb.setChecked(True)

        self.show_size_cb = QtWidgets.QCheckBox("Show Size")
        self.show_size_cb.setChecked(True)

        self.show_dates_cb = QtWidgets.QCheckBox("Show Dates")

        self.show_md5_cb = QtWidgets.QCheckBox("Show MD5")

        # results area 
        results_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal
        )

        self.results_tree = QtWidgets.QTreeView()

        self.properties_tree = QtWidgets.QTreeWidget()

        self.properties_tree.setHeaderLabels(
            ["Property", "Value"]
        )

        results_splitter.addWidget(self.results_tree)

        results_splitter.addWidget(self.properties_tree)

        results_splitter.setSizes([1200, 400])

        #statistics
        stats_group = QtWidgets.QGroupBox(
            "Statistics"
        )

        stats_layout = QtWidgets.QHBoxLayout(stats_group)

        self.files_label = QtWidgets.QLabel("Files: 0")
        self.folders_label = QtWidgets.QLabel("Folders: 0")
        self.size_label = QtWidgets.QLabel("Size: 0 MB")
        self.selected_label = QtWidgets.QLabel("Selected: 0")

        # action buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.selection_map_button = QtWidgets.QPushButton("Create Selection Map")
        self.export_button = QtWidgets.QPushButton("Export Tree")
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.copy_button = QtWidgets.QPushButton("Copy Results")
        self.close_button = QtWidgets.QPushButton("Close")

        # Main structure
        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.addWidget(query_group)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(results_splitter, 1)
        main_layout.addWidget(stats_group)
        main_layout.addLayout(button_layout)
