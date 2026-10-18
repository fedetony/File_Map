# repeated_duplicate_dialog.py
from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from PyQt6 import QtCore, QtGui, QtWidgets

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer

from widgets.class_explorer_tree_widget import *

NODE_HIDDEN_PROPERTIES = {
    "parent",
    "children",
}


class RepeatedDuplicateResultDialog(QtWidgets.QDialog): 
    """
    Presents the result of find_repeated_duplicates_in_map().

    The calculation itself is performed elsewhere.

    Expected result format:

        {
            md5: [
                (db_map_pair_index, record_id),
                (db_map_pair_index, record_id),
                ...
            ],
            ...
        }

    The dialog is responsible only for presentation and selection.
    """

    refresh_mapping_tree = QtCore.pyqtSignal()
    mapping_is_running_signal = QtCore.pyqtSignal()
    mapping_is_not_running_signal = QtCore.pyqtSignal()
    dialog_exit = QtCore.pyqtSignal(str)

    def __init__(
        self,
        fmap: FileMapCliManager,
        db_map_pair_list: list,
        result: list,
        mode: str,
        worker_manager: WorkerManager = None,
        parent=None,
    ):
        super().__init__(parent)

        self.fmap = fmap
        self.db_map_pair_list = db_map_pair_list
        self.groups = result or {} # list of dicts md5 -> [(db_map_index, record_id), ...]
        self.mode = mode.lower()
        self.worker_manager = worker_manager

        self.icons = Icons()
        self.text_renderer = TextRenderer()

        # ----------------------------------------------------------
        # Internal state
        # ----------------------------------------------------------
        # Ordered list of MD5s.
        # Useful because dict ordering becomes the presentation order.
        self.group_md5_list = list(self.groups.keys())

        # Current group selected in the table.
        self.current_group_index = None

        # Selection state.
        #
        # Key:
        #     (db_map_index, record_id)
        #
        # Value:
        #     True  -> selected for removal
        #     False -> kept
        #
        # Initially empty because defaults can be applied later.
        self.selected_occurrences = set()

        self.resize(1500, 950)
        styles_dict={
            "explorer_style":RepDupExplorerStyle(), # text, tooltips, icons
            "tree_style":RepDupTreeStyle(), # role formatting by node, treemana
        }
        self.setter= RepeatedDuplicateSetter(self.fmap,
                                             self.db_map_pair_list,
                                             {"mode":self.mode},
                                             self.groups,
                                             rep_dup_result_dbmap_pair=None,
                                             lazy_defaults=None,
                                             styles_dict=styles_dict,
                                             parent=self
                                             )

        self.build_ui()
        self.populate_table()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        mode_ui = {
            "repeated": ("find repeated", "<b>Repeated Files</b> — "
                "Same MD5, different folders."),
            "duplicates": ("find duplicates", "<b>Duplicate Files</b> — "
                "Same MD5, same folder, different filenames."),
        }

        icon_name, title_text = mode_ui.get(self.mode.lower(),
            ("???",f"xxx"))
        
        self.setWindowTitle(
            "Repeated Files" if self.mode == "repeated"
            else "Duplicate Files"
        )
        self.setWindowIcon(self.icons.icon(icon_name))

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ==========================================================
        # Header
        # ==========================================================
        # Header
        header= QtWidgets.QHBoxLayout()
        icon = QtWidgets.QLabel()
        

        self.setWindowIcon(self.icons.icon(icon_name))

        icon.setPixmap(self.icons.icon(icon_name).pixmap(32, 32))
        title = QtWidgets.QLabel(title_text)

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
        header.addStretch(1)

        main_layout.addLayout(header)

        # ==========================================================
        # Toolbar
        # ==========================================================

        toolbar_group = QtWidgets.QGroupBox("Selection")
        toolbar_layout = QtWidgets.QHBoxLayout(toolbar_group)

        self.btn_keep_newest = QtWidgets.QPushButton("Keep Newest")
        self.btn_keep_oldest = QtWidgets.QPushButton("Keep Oldest")

        self.btn_select_all = QtWidgets.QPushButton("Select All")
        self.btn_select_none = QtWidgets.QPushButton("Select None")
        self.btn_invert = QtWidgets.QPushButton("Invert Selection")

        toolbar_layout.addWidget(self.btn_keep_newest)
        toolbar_layout.addWidget(self.btn_keep_oldest)

        toolbar_layout.addSpacing(20)

        toolbar_layout.addWidget(self.btn_select_all)
        toolbar_layout.addWidget(self.btn_select_none)
        toolbar_layout.addWidget(self.btn_invert)

        toolbar_layout.addStretch(1)

        main_layout.addWidget(toolbar_group)

        # ==========================================================
        # Results splitter
        # ==========================================================

        results_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical
        )

        # ----------------------------------------------------------
        # Group table
        # ----------------------------------------------------------

        table_group = QtWidgets.QGroupBox(
            "Groups"
        )

        table_layout = QtWidgets.QVBoxLayout(table_group)

        self.results_table = QtWidgets.QTableView()

        self.results_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.results_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )

        self.results_table.setSortingEnabled(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)

        self.results_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.results_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )

        table_layout.addWidget(self.results_table)

        # ----------------------------------------------------------
        # File tree
        # ----------------------------------------------------------
        tree_group = QtWidgets.QGroupBox()
        tree_layout = QtWidgets.QVBoxLayout(tree_group)

        # Header
        self.files_header = QLabel(
            f"{TEXT_ICONS['selected']}  Selected to KEEP"
        )
        self.files_header.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #72D6A0;
                padding: 4px 2px;
            }
        """)
        self.files_header.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed,
            )
        self.files_header.setFixedHeight(self.files_header.sizeHint().height())

        tree_layout.addWidget(self.files_header, 0)

        # Splitter: file tree + properties
        result_properties_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal
        )

        # Explorer widget
        self.results_etw = ExplorerTreeWidget(self.setter.config)
        self.results_tree = self.results_etw.tree
        # # self.results_etw.actionEvaluated.connect(self.on_action_evaluated)
        # self.results_etw.exportRequested.connect(self.on_export_requested)
        # self.results_etw.exportFormatChanged.connect(self.on_export_format_changed)

        # self.results_etw.lazyLoading.connect(self.on_lazy_loading)
        
        # self.results_etw.currentSelectionChanged.connect(self._on_current_selection_changed)
        # # Exporter widget
        # self._set_export_default_configuration()


        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setUniformRowHeights(False)

        # Properties tree
        self.properties_tree = QtWidgets.QTreeWidget()
        self.properties_tree.setHeaderLabels(["Property", "Value"])
        self.properties_tree.setAlternatingRowColors(True)

        self.ptv = PropertiesTreeWidget(
            self.fmap,
            self.properties_tree,
            parent=self,
            set_statistics_callback=self._set_statistics_node,
        )

        self.results_etw.nodeClicked.connect(
            self.ptv._show_node_properties
        )

        # Add widgets to splitter
        result_properties_splitter.addWidget(self.results_etw)
        result_properties_splitter.addWidget(self.properties_tree)
        result_properties_splitter.setSizes([600, 300])

        # Add splitter below header
        tree_layout.addWidget(result_properties_splitter)

        # Add group to the main splitter
        results_splitter.addWidget(table_group)
        results_splitter.addWidget(tree_group)
        results_splitter.setSizes([350, 500])

        main_layout.addWidget(results_splitter, 1)

        # ==========================================================
        # Summary
        # ==========================================================
        summary_group = QtWidgets.QGroupBox("Selection Summary")
        summary_layout = QtWidgets.QHBoxLayout(summary_group)
        self.lbl_groups = QtWidgets.QLabel("Groups: 0")
        self.lbl_occurrences = QtWidgets.QLabel("Occurrences: 0")
        self.lbl_selected = QtWidgets.QLabel("Selected: 0")
        self.lbl_space = QtWidgets.QLabel("Selected Space: 0 B")
        self.lbl_potential = QtWidgets.QLabel("Potential Save: 0 B")

        summary_layout.addWidget(self.lbl_groups)
        summary_layout.addSpacing(20)

        summary_layout.addWidget(self.lbl_occurrences)
        summary_layout.addSpacing(20)

        summary_layout.addWidget(self.lbl_selected)
        summary_layout.addSpacing(20)

        summary_layout.addWidget(self.lbl_space)
        summary_layout.addSpacing(20)

        summary_layout.addWidget(self.lbl_potential)

        summary_layout.addStretch(1)

        main_layout.addWidget(summary_group)

        # ==========================================================
        # Buttons
        # ==========================================================

        button_layout = QtWidgets.QHBoxLayout()
        self.btn_create_selection_map = QtWidgets.QPushButton("Create Selection Map")

        self.btn_export = QtWidgets.QPushButton("Export")
        self.btn_close = QtWidgets.QPushButton("Close")
        button_layout.addWidget(self.btn_create_selection_map)
        button_layout.addWidget(self.btn_export)

        button_layout.addStretch(1)

        button_layout.addWidget(self.btn_close)

        main_layout.addLayout(button_layout)

        # ==========================================================
        # Signals
        # ==========================================================

        self.results_table.clicked.connect(self._on_group_clicked)
        self.results_table.doubleClicked.connect(self._on_group_double_clicked)
        self.btn_select_all.clicked.connect(self._select_all)
        self.btn_select_none.clicked.connect(self._select_none)
        self.btn_invert.clicked.connect(self._invert_selection)
        self.btn_keep_newest.clicked.connect(self._keep_newest)
        self.btn_keep_oldest.clicked.connect(self._keep_oldest)
        self.btn_close.clicked.connect(self.reject)

    # ==============================================================
    # Table
    # ==============================================================

    def populate_table(self):
        model = RepeatedDuplicateTableModel(self.groups,self.mode,self)

        self.results_table.setModel(model)
        self.results_table.setColumnWidth(RepeatedDuplicateTableModel.COL_GROUP, 70)
        self.results_table.setColumnWidth(RepeatedDuplicateTableModel.COL_MD5, 260)
        self.results_table.setColumnWidth(RepeatedDuplicateTableModel.COL_OCCURRENCES,110)
        self.results_table.setColumnWidth(RepeatedDuplicateTableModel.COL_LOCATIONS, 100)
        self.results_table.setColumnWidth(RepeatedDuplicateTableModel.COL_SIZE, 100)
        self.results_table.setColumnWidth(RepeatedDuplicateTableModel.COL_POTENTIAL, 140)

        self.lbl_groups.setText(f"Groups: {len(self.groups):,}")

        total_occurrences = sum(
            len(items)
            for items in self.groups.values()
        )

        self.lbl_occurrences.setText(f"Occurrences: {total_occurrences:,}")

    # ==============================================================
    # Table -> Tree
    # ==============================================================

    def _on_group_clicked(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return
        row = index.row()
        self.current_group_index = row
        md5 = self.group_md5_list[row]
        node_list=self.results_etw.t_m.get_nodes_by_attribute("path",md5)
        if node_list:
            node=node_list[0]
            self.results_etw.expand_node(node)
            self.results_etw.set_current_node(node)

    def _on_group_double_clicked(self,index: QtCore.QModelIndex):
        self.results_tree.collapseAll()
        self._on_group_clicked(index)

    # ==============================================================
    # Tree
    # ==============================================================

    def on_selection_changed(self,nodes_list):
        if isinstance(nodes_list,list) and len(nodes_list)>0:
            node=nodes_list[0]
            if isinstance(node,TreeNode):
                self._set_statistics_node(node)
    
    def _set_statistics_node(self, node: TreeNode):
        if not node:
            return
        # db_total_matches=self.statistic_dict.get(f"Total_{node.db}",0)
        # map_total_matches=self.statistic_dict.get((node.db,node.map),0)
        # # sel_node_list=self.results_tree.selected_nodes()
        # all_selected=len(self.results_tree.selected_ids())

        # self.files_label.setText(f"Node Files: {node.num_files or 0}")
        # self.folders_label.setText(f"Node Folders: {node.num_dirs or 0}")
        # self.quantity_label.setText(f"Node Quantity: {node.quantity or 0}")
        # if node.size:
        #     value = self.fmap.fm.get_size_str_formatted(node.size)
        # else:
        #     value = 0
        # self.size_label.setText(f"Size: {value}")
        # self.db_matches_label.setText(f"DB Matches: {db_total_matches}")
        # self.map_matches_label.setText(f"Map Matches: {map_total_matches}")
        # self.selected_label.setText(f"Selected: {all_selected}")

    

    # ==============================================================
    # Selection
    # ==============================================================

    def _select_all(self):
        for md5, occurrences in self.groups.items():
            for occurrence in occurrences:
                self.selected_occurrences.add(occurrence)
        self._refresh_selection_summary()

    def _select_none(self):
        self.selected_occurrences.clear()
        self._refresh_selection_summary()

    def _invert_selection(self):
        all_occurrences = {
            occurrence
            for occurrences in self.groups.values()
            for occurrence in occurrences
        }
        self.selected_occurrences.symmetric_difference_update(
            all_occurrences)

        self._refresh_selection_summary()

    # ==============================================================
    # Default policies
    # ==============================================================

    def _keep_newest(self):
        """
        Placeholder.

        This should eventually use the file metadata loaded
        from the database.
        """

        pass

    def _keep_oldest(self):
        """
        Placeholder.

        This should eventually use the file metadata loaded
        from the database.
        """

        pass

    # ==============================================================
    # Statistics
    # ==============================================================

    def _refresh_selection_summary(self):

        selected_count = len(
            self.selected_occurrences
        )

        self.lbl_selected.setText(
            f"Selected: {selected_count:,}"
        )

        # Size will be calculated once the occurrence metadata
        # is available through the lazy loader.

    # ==============================================================
    # Public API
    # ==============================================================

    def get_selection(self):
        """
        Returns the selected occurrences.

        Example:

            {
                (0, 161299),
                (0, 161640),
            }
        """

        return set(self.selected_occurrences)
    

class PropertiesTreeWidget:
    def __init__(
            self,fmap:FileMapCliManager,
            properties_tree:QtWidgets.QTreeWidget,
            parent=None,
            set_statistics_callback=None,
            ):
        self.parent_widget=parent
        self.fmap=fmap
        self.properties_tree=properties_tree
        self.text_renderer = TextRenderer()
        self.set_statistics_callback = set_statistics_callback
    
    def is_dark_theme(self):
        if self.parent_widget:
            try:
                color = self.parent_widget.palette().color(QtGui.QPalette.ColorRole.Window)
                return color.lightness() < 128
            except AttributeError:
                return False
        return False

    def _show_node_properties(self, node: TreeNode):
        self.properties_tree.clear()
        add_info_at_end=False
        for name, value in vars(node).items():
            if name in NODE_HIDDEN_PROPERTIES:
                continue
            if value is None:
                continue

            if name == "size":
                value = self.fmap.fm.get_size_str_formatted(value)
            if name == "i_am":
                value = TEXT_ICONS.get(value, "") + " " + value

            # Set to strings
            value = self._format_property_value(value)

            # add colors and formats
            if name in ("quantity","num_dirs", "num_files","size"):
                value = "[cyan]" + value +"[/]"
            if name in ("mount","serial") and node.i_exist:
                value = "[bright_green]" + value +"[/]"
            if name in ("mount","serial") and not node.i_exist:
                value = "[red]" + value +"[/]"
            if name in ("map","db") and node.i_exist:
                value = "[magenta]" + value +"[/]"
            if name in ("path","name") and node.i_exist:
                if self.is_dark_theme():
                    value = "[bright_yellow]" + value +"[/]"
                else:
                    value = "[bright_blue]" + value +"[/]"

            if name == "info" and node.i_am == "file":
                add_info_at_end=True        
            else:
                self._add_property(name, value)
                
        if add_info_at_end:   
            info_dict=self._parse_node_info(node)
            self._add_property("Database Properties", "[bright_red]"+"-"*33+"[/]")
            for prop,val in info_dict.items(): 
                val = self._format_db_file_property_value(prop,val,node)
                if prop == "id":
                    prop = "id_in_db"
                self._add_property(prop, val)
        self.properties_tree.resizeColumnToContents(0)
        # set the statistics
        self._set_statistics_node(node)
    
    def _format_property_value(self, value):
        if isinstance(value, bool):
            return "[bold]✓ Yes[/]" if value else "✕ No"

        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(x) for x in value)

        if isinstance(value, dict):
            return ", ".join(
                f"{key}: {val}"
                for key, val in value.items()
            )

        return str(value)
    
    def _parse_node_info(self, node: TreeNode) -> dict:
        if not node:
            return {}
        if node.i_am != "file":
            return {}
        if not node.info:
            return {}
        fields = self._get_fields_on_db(node)
        if not fields:
            return {}
        return dict(zip(fields, node.info))
    
    def _set_statistics_node(self, node: TreeNode):
        if not self.set_statistics_callback:
            return
        else:
            self.set_statistics_callback(node)
        if not node:
            return
        
    
    def _format_db_file_property_value(self, name:str, value, node:TreeNode):
        if value is None:
            return None

        # ISO datetime fields
        if name.startswith("dt_"):
            try:
                value = datetime.fromisoformat(value).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )[:-3]
            except (TypeError, ValueError):
                # Keep the original value if it isn't a valid ISO date
                pass

        elif name == "size":
            value = self.fmap.fm.get_size_str_formatted(value)
        else:
            value = self._format_property_value(value)

        # Styling
        if name in ("id", "size"):
            value = f"[cyan]{value}[/]"

        elif name == "md5":
            value = f"[red]{value}[/]"

        elif name in ("filepath", "filename") and node.i_exist:
            if self.is_dark_theme():
                value = f"[bright_yellow]{value}[/]"
            else:
                value = f"[bright_blue]{value}[/]"
            
        elif name.startswith("dt_"):
            value = f"[magenta]{value}[/]"

        return value

    def _add_property(self, name, value):
        item = QtWidgets.QTreeWidgetItem(self.properties_tree, [name])
        label = QtWidgets.QLabel()
        label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        label.setText(self.text_renderer.to_html(value))
        label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.properties_tree.setItemWidget(item, 1, label)

    def _get_fields_on_db(self, node:TreeNode)->list[str]:
        if not node:
            return []
        if node.db and node.map:
            fm=self.fmap.cma.get_file_map(node.db)
            if fm:
                return fm.db.get_column_list_of_table(node.map)
        return []

# ==================================================================
# Table model
# ==================================================================

class RepeatedDuplicateTableModel(QtCore.QAbstractTableModel):
    """
    Lightweight model containing one row per group.

    It does NOT load the files belonging to the group.
    """

    COL_GROUP = 0
    COL_MD5 = 1
    COL_OCCURRENCES = 2
    COL_LOCATIONS = 3
    COL_SIZE = 4
    COL_POTENTIAL = 5

    HEADERS = [
        "Group",
        "MD5",
        "Occurrences",
        "Locations",
        "Size",
        "Potential Save",
    ]

    def __init__(
        self,
        groups: dict,
        mode: str,
        parent=None
    ):
        super().__init__(parent)

        self.groups = groups
        self.mode = mode

        self.md5_list = list(groups.keys())

    # --------------------------------------------------------------
    # Required Qt model methods
    # --------------------------------------------------------------

    def rowCount(
        self,
        parent=QtCore.QModelIndex()
    ):
        if parent.isValid():
            return 0

        return len(self.md5_list)

    def columnCount(
        self,
        parent=QtCore.QModelIndex()
    ):
        if parent.isValid():
            return 0

        return len(self.HEADERS)

    def headerData(
        self,
        section,
        orientation,
        role=QtCore.Qt.ItemDataRole.DisplayRole
    ):

        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.HEADERS[section]

        return str(section)

    def data(
        self,
        index,
        role=QtCore.Qt.ItemDataRole.DisplayRole
    ):

        if not index.isValid():
            return None

        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        row = index.row()
        column = index.column()

        md5 = self.md5_list[row]

        occurrences = self.groups[md5]

        count = len(occurrences)

        if column == self.COL_GROUP:
            return row

        if column == self.COL_MD5:
            return md5

        if column == self.COL_OCCURRENCES:
            return f"{count:,}"

        if column == self.COL_LOCATIONS:

            # Temporary.
            #
            # Later this can be calculated from the
            # (db_map_index, record_id) references or cached
            # group metadata.
            return "—"

        if column == self.COL_SIZE:
            return "—"

        if column == self.COL_POTENTIAL:
            return "—"

        return None

"""
Repeated / Duplicate Results Dialog
====================================

PURPOSE
-------
Presentation dialog for the results produced by:

    FileMapCliManager.find_repeated_duplicates_in_map()

The calculation/search is performed elsewhere by the Mapping dialog
and WorkerManager. This dialog does NOT perform the search.

The worker returns an index-like structure:

    {
        md5: [
            (db_map_pair_index, record_id),
            (db_map_pair_index, record_id),
            ...
        ],
        ...
    }

where db_map_pair_index refers to the corresponding entry in:

    db_map_pair_list = [
        (database, map/table),
        ...
    ]

The result therefore contains references to files in one or more
database/map pairs, rather than complete file information.

UI CONCEPT
----------
The dialog presents two complementary views:

    1. Results Table
    2. File Explorer Tree

The table shows ONE ROW PER GROUP and provides a compact overview
before loading individual files.

Example:

    Group | MD5        | Occurrences | Locations | Size | Potential Save
      0   | fb08c4...  | 38,723      | 12        | 555  | 20.5 MiB
      1   | fff64a...  | 30,002      |  2        | 555  | 16.5 MiB

Selecting a table row loads/displays that group's files in the
Explorer Tree.

IMPORTANT:
The table should remain lightweight. It should NOT construct all
TreeNodes or resolve every database record merely to display the
group list.

The Explorer Tree uses lazy loading. A group may contain tens of
thousands of occurrences, so individual database records must only
be resolved when required.

REPEATED VS DUPLICATE
---------------------
These are intentionally different concepts and therefore use
different tree structures.

REPEATED:
    Files with the same MD5 anywhere within the selected maps.

    Tree:

        MD5
        ├── file/path
        ├── file/path
        └── file/path

    The full path/location is important because files may exist in
    completely different folders, databases, or maps.

    Example:

        MD5: abc123... [47 occurrences]

        ├── C:\Projects\foo\.gitignore
        ├── C:\Projects\bar\.gitignore
        ├── C:\Projects\baz\.gitignore
        └── D:\Backup\foo\.gitignore

    Repeated does NOT mean redundant. For example, .gitignore files
    occurring in many repositories are expected and should normally
    not be removed automatically.

DUPLICATES:
    Files with the same MD5, in the SAME folder, but with different
    filenames.

    Tree:

        Folder
        ├── fileA
        ├── fileB
        └── fileC

    Example:

        C:\Downloads
        ├── invoice.pdf
        ├── invoice (1).pdf
        └── invoice (2).pdf

    The folder is therefore the natural grouping node for duplicates.

SINGLE TREE
-----------
Only ONE Explorer Tree is used.

The tree structure changes according to the current mode:

    Repeated:
        Group -> MD5 -> files

    Duplicate:
        Group -> Folder -> files

This avoids maintaining two synchronized trees.

SELECTION
---------
Selection represents files that are going to be REMOVED.

    [X] = selected for removal
    [ ] = kept

The selection state is independent from the tree presentation.

Internally, selection can be represented using the original result
references:

    (db_map_pair_index, record_id)

The tree is only a view of that selection state.

DEFAULT SELECTION
-----------------
Default selection is a policy, not part of the duplicate/repeated
calculation.

The calculation determines WHAT is repeated/duplicated.

The UI decides WHICH occurrences are initially selected for removal.

Examples:

    Keep oldest
    Keep newest
    Select all but oldest
    Select none
    Custom/default path rules

Defaults must be conservative for Repeated files because repetition
does not imply redundancy.

STATISTICS
----------
The dialog should show both group-level and selection-level
statistics.

Possible values:

    Groups
    Occurrences
    Selected files
    Selected size
    Potential save

Potential save for a group with N identical files of size S:

    (N - 1) * S

This is theoretical maximum space saving if one occurrence is kept.

The actual selected space is calculated from the current selection.

ARCHITECTURE
------------
Do NOT modify the existing calculation engine for this UI.

Keep the existing separation:

    Mapping Dialog
        |
        v
    WorkerManager
        |
        v
    find_repeated_duplicates_in_map()
        |
        v
    result dictionary
        |
        v
    RepeatedDuplicateResultDialog
        |
        +--> Results Table
        |
        +--> Explorer Tree
                  |
                  v
            Lazy DB Loader

The new lazy loader should be based on the existing DATABASE
lazy-loader implementation, because the result references database
records rather than ordinary filesystem objects.

There are currently three relevant tree/data models in the project:

    1. Standard model
       Reads files/folders directly from the local filesystem.

    2. Default/file-structure model
       Reads from dictionary-style file structure data.

    3. Database model
       Reads file/folder information directly from the FileMap
       database.

The new Repeated/Duplicate lazy loader should be derived/adapted
from the existing DATABASE lazy loader.

The main additional responsibility is resolving:

    (db_map_pair_index, record_id)

from the duplicate/repeated result into the appropriate database
record and presenting it as a TreeNode.

PERFORMANCE
-----------
Do NOT create TreeNodes for all occurrences when the dialog opens.

A result may contain groups such as:

    38,723 occurrences
    30,002 occurrences

The table should remain lightweight.

The tree should initially create only the group/root node and use
lazy loading for its children.

The MD5/result dictionary remains the source/index for the group;
the database lazy loader resolves individual occurrences when needed.

FUTURE
------
Potential future improvements:

    - configurable default-selection rules
    - path/name exclusion rules
    - sorting groups by occurrence count
    - sorting by potential space saving
    - group-level select/deselect
    - partial checkbox state for groups
    - export results
    - Create Selection Map using the existing selection-map system

TAKEOUT:
Calculation:
    "These files are related by MD5."

Selection policy:
    "These are the ones I think you should remove by default."

User:
    "This is what I actually want removed."

"""

from models.class_provider_engine import DefaultProviderEngine, FM
from models.class_action_provider import *

from models.class_style_provider import *
from models.class_lazy_loader import *
from controllers.class_database_manager import DatabaseInfo
from class_file_mapper import MapType

class RepeatedDuplicateSetter:
    """Sets the explorer configuration for the RepeatedDuplicate results dialog
    """
    def __init__(self, 
                 fmap:FileMapCliManager, 
                 db_map_pair_list:list,
                 modding_info:dict,
                 result:dict, # list of dicts md5 -> [(db_map_index, record_id), ...]
                 rep_dup_result_dbmap_pair:tuple[str]=None,
                 lazy_defaults:dict = None,
                 styles_dict:dict = None, # To include other styles later
                 parent =None
                 ):
        
        self.fmap = fmap
        self.modding_info = modding_info
        self.lazy_defaults = lazy_defaults
        self.styles_dict = styles_dict
        self.result_dbmap_pair=rep_dup_result_dbmap_pair or ("","")
        self.groups = result or {} # dict {md5: [(db_map_index, record_id), ...]}
        self.parent = parent
        self.config = None
        self.dlg = None
        self.db_map_pair_list = db_map_pair_list

        self.group_md5_list = list(self.groups.keys())
        # map indexes for each db_map_pair
        self.map_dbmap_pairs={}
        for db_map_index, db_map_pair in enumerate(self.db_map_pair_list):
            self.map_dbmap_pairs[db_map_index]=db_map_pair

        # mode=modding_info.get("mode")
        # if mode == "repeated":        
        #     self._set_repeated_config()
        # else:
        #     self._set_duplicates_config()
        #     # raise AttributeError("Mode not supported!")
        
        self._set_repeated_config()

        if not isinstance(self.config,ExplorerConfig):
            return

        if not isinstance(self.config.explorer_style,TreeStyle):
                self.config.explorer_style = DefaultExplorerStyle() # text, tooltips, icons
        if not isinstance(self.config.tree_style,TreeStyleProvider):
            self.config.tree_style = DefaultTreeStyle() # role formatting by node, treemanager


    def _set_repeated_config(self):
        mode=self.modding_info.get("mode")
        if mode == "repeated":
            vname= f"{TEXT_ICONS['file']} Repeated" 
        else:
            vname=f"{TEXT_ICONS['document']} Duplicates"
        
        virtual_root = TreeNode(vname)
        virtual_root.loaded = True
        virtual_root.i_am = "root"

        if not self.group_md5_list:
            return        
        
        # self.map_dbmap_pairs
        for md5_idx,(md5,rep_list) in enumerate(self.groups.items()):
            # Load MD5 Node
            md5_node = TreeNode(f"{md5_idx} {md5}")
            md5_node.i_am = "md5"
            md5_node.mount = mode
            md5_node.path = md5
            md5_node.num_dirs=0
            md5_node.num_files = len(rep_list)
            md5_node.quantity = len(rep_list)
            md5_node.expand =False            
            md5_node.db = self.result_dbmap_pair[0]
            md5_node.i_exist = True
            md5_node.map = self.result_dbmap_pair[1]
            md5_node.info = rep_list
            md5_node.loaded = False
            virtual_root.add_child(md5_node)
                
        config = ExplorerConfig()
        # Basic
        config.root_node = virtual_root
        # 
        config.show_path_edit = False
        config.show_context_menu = True
        # Mode selection
        config.selection_by_type_mode = SelectionByTypeMode.FILES_ONLY
        config.checkbox_mode = CheckBoxMode.CHECKBOX
        config.selection_mode = SelectionMode.MULTI
        # You must pass lazy_loader, providers and styles in agreement to Mode selection
        lazy_class = RepeatedLazyLoader()
        lazy_class.set_filemap(self.fmap)
        lazy_class.set_db_map_pair_list(self.db_map_pair_list)
        # initial settings
        lazy_defaults=self.lazy_defaults 
        if not isinstance(lazy_defaults,dict):
            lazy_defaults = {}
        lazy_class.set_defaults(lazy_defaults.get("defaults",[]))
        lazy_class.set_hidden(lazy_defaults.get("hidden",[]))
        lazy_class.set_blank(lazy_defaults.get("blank",[]))
        lazy_class.set_locked(lazy_defaults.get("locked",[]))

        config.lazy_loader = lazy_class
        config.provider = DefaultProviderEngine() # functions for behavior
        config.action_provider = RepDupActionProvider() #DefaultFileActionProvider() # menu, shortcuts, global shortcuts
        styles_dict=self.styles_dict
        if not isinstance(styles_dict,dict):
            styles_dict={}
        config.explorer_style = styles_dict.get("explorer_style",DefaultExplorerStyle()) # text, tooltips, icons
        config.tree_style = styles_dict.get("tree_style",DefaultTreeStyle()) # role formatting by node, treemanager
        
        config.extra_columns=[
            TreeColumn(
                key="type",
                title="Type",
                value=lambda node: node.i_am,
            ),
            TreeColumn(
                key="path",
                title="Location",
                value=lambda node: node.itempath, #getattr(node, "path", ""),
            ),
        ]

        self.config = config

    
        
