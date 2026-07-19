# class_db_explorer.py

from PyQt6 import QtCore, QtGui, QtWidgets

from class_db_tree_viewer import DBTreeView, DBTreeNode
from class_backup_actions import BackupActions


class DBExplorer(QtCore.QObject):
    """
    High-level interface for browsing one or more database maps.

    This class wraps DBTreeView and provides helper functions for
    selection, expansion and context-menu actions.

    The goal is to provide an API similar to the terminal
    FileExplorer while letting Qt handle the user interaction.
    """

    nodeActivated = QtCore.pyqtSignal(DBTreeNode)
    actionTriggered = QtCore.pyqtSignal(DBTreeNode, str)

    def __init__(
        self,
        db_map_pairs: list[tuple],
        ba: BackupActions,
        do_action=None,
        parent=None
    ):
        super().__init__(parent)

        self.ba = ba

        self.tree = DBTreeView(
            db_map_pairs=db_map_pairs,
            ba=ba,
            parent=parent
        )

        if do_action:
            self.do_action = do_action
        else:
            self.do_action = self._do_action

        self.tree.doubleClicked.connect(self._double_clicked)

        self.tree.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tree.customContextMenuRequested.connect(
            self._show_context_menu
        )

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def widget(self):
        """
        Returns the underlying Qt widget.

        Returns:
            DBTreeView
        """
        return self.tree

    def model(self):
        """
        Returns the underlying tree model.

        Returns:
            DBTreeModel
        """
        return self.tree.tree_model

    # ---------------------------------------------------------
    # Selection
    # ---------------------------------------------------------

    def selected_indexes(self):
        """
        Returns:
            list[QModelIndex]
        """
        return self.tree.selectionModel().selectedRows()

    def selected_nodes(self)->list[DBTreeNode]:
        """
        Returns all selected nodes.

        Returns:
            list[DBTreeNode]
        """
        nodes = []

        for index in self.selected_indexes():
            node = index.internalPointer()
            if node:
                nodes.append(node)

        return nodes

    def selected_files(self):
        """
        Returns:
            list[DBTreeNode]
        """
        return [
            n
            for n in self.selected_nodes()
            if n.node_type == "file"
        ]

    def selected_folders(self):
        """
        Returns:
            list[DBTreeNode]
        """
        return [
            n
            for n in self.selected_nodes()
            if n.node_type in ("folder", "dir")
        ]
    
    def maps_in_selection(self):
        """
        Returns the unique map nodes containing the current selection.

        Returns:
            list[DBTreeNode]: Selected map nodes without duplicates.
        """
        sel_maps=[]

        for node in self.selected_nodes():
            for parent in node.get_node_bloodline():
                if parent.node_type == "map":
                    if parent not in sel_maps:
                        sel_maps.append(parent)
                    break

        return sel_maps
    
    def selected_maps(self):
        """
        Returns the selected map nodes within the current selection.

        Returns:
            list[DBTreeNode]: Selected map nodes without duplicates.
        """
        maps = []
        for node in self.selected_nodes():
            current = node
            while current is not None:
                if current.node_type == "map":
                    if current not in maps:
                        maps.append(current)
                    break
                current = current.parent
        return maps

    def current_node(self):
        """
        Returns the current node.

        Returns:
            DBTreeNode | None
        """
        index = self.tree.currentIndex()

        if not index.isValid():
            return None

        return index.internalPointer()

    # ---------------------------------------------------------
    # Expansion
    # ---------------------------------------------------------

    def expand_node(self, node):
        """
        Expands a node.

        Args:
            node (DBTreeNode)
        """
        index = self.index_from_node(node)

        if index.isValid():
            self.tree.expand(index)

    def collapse_node(self, node):
        """
        Collapses a node.

        Args:
            node (DBTreeNode)
        """
        index = self.index_from_node(node)

        if index.isValid():
            self.tree.collapse(index)

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self):
        """
        Refreshes the tree.
        """
        self.model().layoutChanged.emit()

    # ---------------------------------------------------------
    # Node lookup
    # ---------------------------------------------------------

    def node_from_node_id(self, node_id):
        """
        Returns a node from its node_id.

        Args:
            node_id (int)

        Returns:
            DBTreeNode | None
        """
        return self.model().node_from_node_id(node_id)

    def index_from_node(self, node):
        """
        Returns the QModelIndex of a node.

        Args:
            node (DBTreeNode)

        Returns:
            QModelIndex
        """

        if node.parent is None:
            return QtCore.QModelIndex()

        row = node.parent.children.index(node)

        return self.model().createIndex(
            row,
            0,
            node
        )

    # ---------------------------------------------------------
    # Signals
    # ---------------------------------------------------------

    def _double_clicked(self, index):

        node = index.internalPointer()

        if node:
            self.nodeActivated.emit(node)

    # ---------------------------------------------------------
    # Context Menu
    # ---------------------------------------------------------

    def _show_context_menu(self, pos):

        index = self.tree.indexAt(pos)

        if not index.isValid():
            return

        node = index.internalPointer()

        menu = QtWidgets.QMenu(self.tree)

        actions = [
            ("Open", "open"),
            ("Rename", "rename"),
            ("Delete", "delete"),
            ("Copy path", "copy_path"),
            ("Properties", "properties"),
        ]

        for text, keyword in actions:

            action = menu.addAction(text)

            action.triggered.connect(
                lambda checked=False,
                n=node,
                k=keyword:
                self._trigger_action(n, k)
            )

        menu.exec(
            self.tree.viewport().mapToGlobal(pos)
        )

    def _trigger_action(self, node, keyword):

        self.actionTriggered.emit(node, keyword)

        self.do_action(node, keyword)

    # ---------------------------------------------------------
    # Default callback
    # ---------------------------------------------------------

    def _do_action(self, node, keyword):
        """
        Default action callback.

        Override this method or provide a custom callback
        in the constructor.

        Args:
            node (DBTreeNode)
            keyword (str)
        """

        print("-----------------------------------")
        print(f"Action : {keyword}")
        print(f"Node   : {node.name}")
        print(f"Type   : {node.node_type}")
        print(f"NodeID : {node.node_id}")
        print(f"MapKey : {node.db_map_key}")
        print(f"Row ID : {node.id_in_map}")
        print(f"Trace  : {node.get_node_id_bloodline()}")
        print("-----------------------------------")