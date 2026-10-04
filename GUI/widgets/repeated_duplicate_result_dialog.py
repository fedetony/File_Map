# repeated_duplicate_dialog.py
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from PyQt6 import QtCore, QtGui, QtWidgets

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer

from widgets.class_explorer_tree_widget import *


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

    def __init__(
        self,
        fmap: FileMapCliManager,
        db_map_pair_list: list,
        result: dict,
        mode: str,
        worker_manager: WorkerManager = None,
        parent=None,
    ):
        super().__init__(parent)

        self.fmap = fmap
        self.db_map_pair_list = db_map_pair_list
        self.result = result or {}
        self.mode = mode
        self.worker_manager = worker_manager

        self.icons = Icons()
        self.text_renderer = TextRenderer()

        # ----------------------------------------------------------
        # Internal state
        # ----------------------------------------------------------

        # md5 -> [(db_map_index, record_id), ...]
        self.groups = self.result

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

        self.setWindowTitle(
            "Repeated Files" if self.mode == "Repeated"
            else "Duplicate Files"
        )

        self.resize(1500, 950)

        self.build_ui()
        self.populate_table()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ==========================================================
        # Header
        # ==========================================================

        header_layout = QtWidgets.QHBoxLayout()

        self.title_label = QtWidgets.QLabel()

        if self.mode == "Repeated":
            self.title_label.setText(
                "<b>Repeated Files</b> — "
                "same MD5 in different locations"
            )
        else:
            self.title_label.setText(
                "<b>Duplicate Files</b> — "
                "same MD5 in the same folder"
            )

        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)

        main_layout.addLayout(header_layout)

        # ==========================================================
        # Toolbar
        # ==========================================================

        toolbar_group = QtWidgets.QGroupBox("Selection")

        toolbar_layout = QtWidgets.QHBoxLayout(toolbar_group)

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

        self.btn_invert = QtWidgets.QPushButton(
            "Invert Selection"
        )

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

        tree_group = QtWidgets.QGroupBox(
            "Files"
        )

        tree_layout = QtWidgets.QVBoxLayout(tree_group)

        self.results_tree = QtWidgets.QTreeWidget()
        self.results_tree.setColumnCount(5)
        self.results_tree.setHeaderLabels([
            "Action",
            "File",
            "Size",
            "Modified",
            "Location",
        ])

        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setUniformRowHeights(False)
        self.results_tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )

        tree_layout.addWidget(self.results_tree)

        results_splitter.addWidget(table_group)
        results_splitter.addWidget(tree_group)

        results_splitter.setSizes([350, 500])

        main_layout.addWidget(results_splitter, 1)

        # ==========================================================
        # Summary
        # ==========================================================

        summary_group = QtWidgets.QGroupBox(
            "Selection Summary"
        )

        summary_layout = QtWidgets.QHBoxLayout(summary_group)

        self.lbl_groups = QtWidgets.QLabel(
            "Groups: 0"
        )

        self.lbl_occurrences = QtWidgets.QLabel(
            "Occurrences: 0"
        )

        self.lbl_selected = QtWidgets.QLabel(
            "Selected: 0"
        )

        self.lbl_space = QtWidgets.QLabel(
            "Selected Space: 0 B"
        )

        self.lbl_potential = QtWidgets.QLabel(
            "Potential Save: 0 B"
        )

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

        self.btn_create_selection_map = QtWidgets.QPushButton(
            "Create Selection Map"
        )

        self.btn_export = QtWidgets.QPushButton(
            "Export"
        )

        self.btn_close = QtWidgets.QPushButton(
            "Close"
        )

        button_layout.addWidget(
            self.btn_create_selection_map
        )

        button_layout.addWidget(
            self.btn_export
        )

        button_layout.addStretch(1)

        button_layout.addWidget(
            self.btn_close
        )

        main_layout.addLayout(button_layout)

        # ==========================================================
        # Signals
        # ==========================================================

        self.results_table.clicked.connect(
            self._on_group_clicked
        )

        self.results_table.doubleClicked.connect(
            self._on_group_double_clicked
        )

        self.btn_select_all.clicked.connect(
            self._select_all
        )

        self.btn_select_none.clicked.connect(
            self._select_none
        )

        self.btn_invert.clicked.connect(
            self._invert_selection
        )

        self.btn_keep_newest.clicked.connect(
            self._keep_newest
        )

        self.btn_keep_oldest.clicked.connect(
            self._keep_oldest
        )

        self.btn_close.clicked.connect(
            self.reject
        )

    # ==============================================================
    # Table
    # ==============================================================

    def populate_table(self):

        model = RepeatedDuplicateTableModel(
            self.groups,
            self.mode,
            self
        )

        self.results_table.setModel(model)

        self.results_table.setColumnWidth(
            RepeatedDuplicateTableModel.COL_GROUP,
            70
        )

        self.results_table.setColumnWidth(
            RepeatedDuplicateTableModel.COL_MD5,
            260
        )

        self.results_table.setColumnWidth(
            RepeatedDuplicateTableModel.COL_OCCURRENCES,
            110
        )

        self.results_table.setColumnWidth(
            RepeatedDuplicateTableModel.COL_LOCATIONS,
            100
        )

        self.results_table.setColumnWidth(
            RepeatedDuplicateTableModel.COL_SIZE,
            100
        )

        self.results_table.setColumnWidth(
            RepeatedDuplicateTableModel.COL_POTENTIAL,
            140
        )

        self.lbl_groups.setText(
            f"Groups: {len(self.groups):,}"
        )

        total_occurrences = sum(
            len(items)
            for items in self.groups.values()
        )

        self.lbl_occurrences.setText(
            f"Occurrences: {total_occurrences:,}"
        )

    # ==============================================================
    # Table -> Tree
    # ==============================================================

    def _on_group_clicked(self, index: QtCore.QModelIndex):

        if not index.isValid():
            return

        row = index.row()

        self.current_group_index = row

        md5 = self.group_md5_list[row]

        self.load_group_tree(md5)

    def _on_group_double_clicked(
        self,
        index: QtCore.QModelIndex
    ):

        self._on_group_clicked(index)

        self.results_tree.expandAll()

    # ==============================================================
    # Tree
    # ==============================================================

    def load_group_tree(self, md5: str):

        """
        Temporary implementation.

        Replace this with your ExplorerTreeWidget +
        new lazy loader.

        For now we only create the group root.
        """

        self.results_tree.clear()

        occurrences = self.groups.get(md5, [])

        if self.mode == "Repeated":

            root_text = (
                f"MD5: {md5} "
                f"({len(occurrences):,} occurrences)"
            )

        else:

            root_text = (
                f"MD5: {md5} "
                f"({len(occurrences):,} occurrences)"
            )

        root = QtWidgets.QTreeWidgetItem([
            "",
            root_text,
            "",
            "",
            "",
        ])

        root.setData(
            0,
            QtCore.Qt.ItemDataRole.UserRole,
            md5
        )

        self.results_tree.addTopLevelItem(root)

        # ----------------------------------------------------------
        # DO NOT load all occurrences here.
        #
        # Your new lazy loader will later attach them.
        # ----------------------------------------------------------

        # Temporary placeholder so the node can be expanded.
        if occurrences:

            placeholder = QtWidgets.QTreeWidgetItem([
                "",
                f"Load {len(occurrences):,} files...",
                "",
                "",
                "",
            ])

            root.addChild(placeholder)

        root.setExpanded(True)

    # ==============================================================
    # Selection
    # ==============================================================

    def _select_all(self):

        for md5, occurrences in self.groups.items():

            for occurrence in occurrences:

                self.selected_occurrences.add(
                    occurrence
                )

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
            all_occurrences
        )

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


# ==================================================================
# Table model
# ==================================================================

class RepeatedDuplicateTableModel(
    QtCore.QAbstractTableModel
):
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
