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
from widgets.search_query_widget import *

class SearchDialog(QtWidgets.QDialog):

    def __init__(self, fmap: FileMapCliManager ,db_map_pairs=None, parent=None):
        super().__init__(parent)
        self.fmap = fmap
        self.db_map_pairs = db_map_pairs

        self.setWindowTitle("Search")
        self.resize(1600, 950)

        self.build_ui()

    def build_ui(self):

        # ==============================================================
        # Query widget
        # ==============================================================

        self.search_widget = SearchQueryWidget(self.fmap,parent=self)
        self.search_widget.searchRequested.connect(self.on_search_requested)

        # ==============================================================
        # View filters
        # ==============================================================

        filter_group = QtWidgets.QGroupBox("View Filters")

        filter_layout = QtWidgets.QHBoxLayout(filter_group)

        self.show_files_cb = QtWidgets.QCheckBox("Files")
        self.show_files_cb.setChecked(True)

        self.show_folders_cb = QtWidgets.QCheckBox("Folders")
        self.show_folders_cb.setChecked(True)

        self.show_size_cb = QtWidgets.QCheckBox("Show Size")
        self.show_size_cb.setChecked(True)

        self.show_dates_cb = QtWidgets.QCheckBox("Show Dates")
        self.show_dates_cb.setChecked(False)

        self.show_md5_cb = QtWidgets.QCheckBox("Show MD5")
        self.show_md5_cb.setChecked(False)

        filter_layout.addWidget(self.show_files_cb)
        filter_layout.addWidget(self.show_folders_cb)
        filter_layout.addWidget(self.show_size_cb)
        filter_layout.addWidget(self.show_dates_cb)
        filter_layout.addWidget(self.show_md5_cb)

        # Keep filters on the left rather than stretching them
        filter_layout.addStretch(1)

        # ==============================================================
        # Results area
        # ==============================================================

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

        # ==============================================================
        # Statistics
        # ==============================================================

        stats_group = QtWidgets.QGroupBox("Statistics")

        stats_layout = QtWidgets.QHBoxLayout(stats_group)

        self.files_label = QtWidgets.QLabel("Files: 0")
        self.folders_label = QtWidgets.QLabel("Folders: 0")
        self.size_label = QtWidgets.QLabel("Size: 0 MB")
        self.selected_label = QtWidgets.QLabel("Selected: 0")

        stats_layout.addWidget(self.files_label)
        stats_layout.addSpacing(30)

        stats_layout.addWidget(self.folders_label)
        stats_layout.addSpacing(30)

        stats_layout.addWidget(self.size_label)
        stats_layout.addSpacing(30)

        stats_layout.addWidget(self.selected_label)

        stats_layout.addStretch(1)

        # ==============================================================
        # Action buttons
        # ==============================================================

        button_layout = QtWidgets.QHBoxLayout()

        self.selection_map_button = QtWidgets.QPushButton("Create Selection Map")

        self.export_button = QtWidgets.QPushButton("Export Tree")

        self.delete_button = QtWidgets.QPushButton("Delete")

        self.copy_button = QtWidgets.QPushButton("Copy Results")

        self.close_button = QtWidgets.QPushButton("Close")

        button_layout.addWidget(self.selection_map_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.close_button)

        # ==============================================================
        # Main layout
        # ==============================================================

        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Query widget gets the most natural amount of space
        main_layout.addWidget(self.search_widget)
        main_layout.addWidget(filter_group)

        # Results should consume all remaining vertical space
        main_layout.addWidget(results_splitter,1)
        main_layout.addWidget(stats_group)
        main_layout.addLayout(button_layout)

        # ==============================================================
        # Final sizing
        # ==============================================================

        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setUniformRowHeights(False)

        self.properties_tree.setAlternatingRowColors(True)

        self.close_button.clicked.connect(self.reject)
    
    def on_search_requested(self):
        pass

    
    # # ==============================================================
    # # UI
    # # ==============================================================
    # def build_ui(self):

    #     # ==============================================================
    #     # Compact search frame
    #     # ==============================================================

    #     self.search_frame = QtWidgets.QFrame()
    #     self.search_frame.setObjectName("SearchFrame")
    #     self.search_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
    #     self.search_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

    #     search_layout = QtWidgets.QHBoxLayout(self.search_frame)

    #     search_layout.setContentsMargins(6, 3, 6, 3)
    #     search_layout.setSpacing(4)

    #     # --------------------------------------------------------------
    #     # Search icon
    #     # --------------------------------------------------------------

    #     self.search_icon = QtWidgets.QLabel()

    #     # Replace with your own icon later:
    #     # self.search_icon.setPixmap(...)
    #     self.search_icon.setText("🔎")
    #     self.search_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    #     self.search_icon.setFixedWidth(22)
    #     search_layout.addWidget(self.search_icon)

    #     # --------------------------------------------------------------
    #     # Query edit
    #     # --------------------------------------------------------------

    #     self.query_edit = QtWidgets.QLineEdit()
    #     self.query_edit.setPlaceholderText("Search...")

    #     self.query_edit.setClearButtonEnabled(True)
    #     self.query_edit.setMinimumWidth(150)

    #     search_layout.addWidget(self.query_edit,1)

    #     # --------------------------------------------------------------
    #     # Validation indicator
    #     # --------------------------------------------------------------

    #     self.valid_icon = QtWidgets.QLabel()
    #     self.valid_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    #     self.valid_icon.setFixedWidth(22)
    #     self.valid_icon.setToolTip("Query validation")
    #     search_layout.addWidget(self.valid_icon)

    #     # --------------------------------------------------------------
    #     # History button
    #     # --------------------------------------------------------------

    #     self.history_button = QtWidgets.QToolButton()
    #     self.history_button.setText("⌄")
    #     self.history_button.setToolTip("Search history")

    #     self.history_button.setAutoRaise(True)
    #     self.history_button.setFixedWidth(26)

    #     search_layout.addWidget(self.history_button)

    #     # --------------------------------------------------------------
    #     # Search button
    #     # --------------------------------------------------------------

    #     self.search_button = QtWidgets.QToolButton()
    #     self.search_button.setText("🔍")
    #     self.search_button.setToolTip("Search")
    #     self.search_button.setAutoRaise(True)
    #     self.search_button.setFixedWidth(30)

    #     search_layout.addWidget(self.search_button)

    #     # --------------------------------------------------------------
    #     # Options button
    #     # --------------------------------------------------------------

    #     self.options_button = QtWidgets.QToolButton()
    #     self.options_button.setText("⋮")
    #     self.options_button.setToolTip("Search options")

    #     self.options_button.setAutoRaise(True)
    #     self.options_button.setFixedWidth(26)

    #     search_layout.addWidget(self.options_button)

    #     # ==============================================================
    #     # Main dialog layout
    #     # ==============================================================

    #     main_layout = QtWidgets.QVBoxLayout(self)
    #     main_layout.setContentsMargins(8, 8, 8, 8)
    #     main_layout.setSpacing(6)
    #     main_layout.addWidget(self.search_frame)

    #     # ==============================================================
    #     # View filters
    #     # ==============================================================

    #     filter_group = QtWidgets.QGroupBox("View Filters")
    #     filter_layout = QtWidgets.QHBoxLayout(filter_group)
    #     filter_layout.setContentsMargins(8, 4, 8, 4)
    #     filter_layout.setSpacing(12)

    #     self.show_files_cb = QtWidgets.QCheckBox("Files")
    #     self.show_files_cb.setChecked(True)

    #     self.show_folders_cb = QtWidgets.QCheckBox("Folders")
    #     self.show_folders_cb.setChecked(True)

    #     self.show_size_cb = QtWidgets.QCheckBox("Size")
    #     self.show_size_cb.setChecked(True)

    #     self.show_dates_cb = QtWidgets.QCheckBox("Dates")
    #     self.show_md5_cb = QtWidgets.QCheckBox("MD5")

    #     filter_layout.addWidget(self.show_files_cb)
    #     filter_layout.addWidget(self.show_folders_cb)
    #     filter_layout.addWidget(self.show_size_cb)
    #     filter_layout.addWidget(self.show_dates_cb)
    #     filter_layout.addWidget(self.show_md5_cb)
    #     filter_layout.addStretch(1)
    #     main_layout.addWidget(filter_group)

    #     # ==============================================================
    #     # Results
    #     # ==============================================================

    #     results_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
    #     self.results_tree = QtWidgets.QTreeView()

    #     self.properties_tree = QtWidgets.QTreeWidget()
    #     self.properties_tree.setHeaderLabels(["Property", "Value"])

    #     results_splitter.addWidget(self.results_tree)
    #     results_splitter.addWidget(self.properties_tree)
    #     results_splitter.setSizes([1200, 400])

    #     main_layout.addWidget(results_splitter,1)

    #     # ==============================================================
    #     # Statistics
    #     # ==============================================================
    #     stats_group = QtWidgets.QGroupBox("Statistics")
    #     stats_layout = QtWidgets.QHBoxLayout(stats_group)
    #     stats_layout.setContentsMargins(8, 3, 8, 3)

    #     self.files_label = QtWidgets.QLabel("Files: 0")
    #     self.folders_label = QtWidgets.QLabel("Folders: 0")
    #     self.size_label = QtWidgets.QLabel("Size: 0 MB")

    #     self.selected_label = QtWidgets.QLabel("Selected: 0")

    #     stats_layout.addWidget(self.files_label)

    #     stats_layout.addSpacing(20)
    #     stats_layout.addWidget(self.folders_label)
    #     stats_layout.addSpacing(20)
    #     stats_layout.addWidget(self.size_label)
    #     stats_layout.addSpacing(20)
    #     stats_layout.addWidget(self.selected_label)
    #     stats_layout.addStretch(1)
    #     main_layout.addWidget(stats_group)

    #     # ==============================================================
    #     # Actions
    #     # ==============================================================

    #     button_layout = QtWidgets.QHBoxLayout()

    #     self.selection_map_button = QtWidgets.QPushButton("Create Selection Map")
    #     self.export_button = QtWidgets.QPushButton("Export Tree")

    #     self.delete_button = QtWidgets.QPushButton("Delete")
    #     self.copy_button = QtWidgets.QPushButton("Copy Results")
    #     self.close_button = QtWidgets.QPushButton("Close")

    #     button_layout.addWidget(self.selection_map_button)
    #     button_layout.addWidget(self.export_button)
    #     button_layout.addWidget(self.delete_button)
    #     button_layout.addWidget(self.copy_button)

    #     button_layout.addStretch(1)
    #     button_layout.addWidget(self.close_button)
    #     main_layout.addLayout(button_layout)

    #     # ==============================================================
    #     # Compact styling
    #     # ==============================================================

    #     self.search_frame.setStyleSheet("""
    #         QFrame#SearchFrame {
    #             border: 1px solid palette(mid);
    #             border-radius: 4px;
    #             background: palette(base);
    #         }

    #         QFrame#SearchFrame QLineEdit {
    #             border: none;
    #             background: transparent;
    #             padding: 3px 2px;
    #         }

    #         QFrame#SearchFrame QToolButton {
    #             border: none;
    #             padding: 2px;
    #             margin: 0px;
    #         }

    #         QFrame#SearchFrame QToolButton:hover {
    #             background: palette(midlight);
    #             border-radius: 3px;
    #         }
    #     """)

    #     # ==============================================================
    #     # Initial validation state
    #     # ==============================================================
    #     self._set_validation_state(None)