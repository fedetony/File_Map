from PyQt6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractItemModel,
    pyqtSignal
)

from PyQt6.QtGui import QColor
from models.class_enums_definitions import *
from models.class_explorer_tree_model import *
from controllers.class_tree_node_manager import *
from models.class_style_provider import *
from models.class_explorer_config import *
import os


class ExplorerTreeModel(QAbstractItemModel):
    userSelectionChanged = pyqtSignal(list)
    lazyLoading = pyqtSignal(bool)
    
    def __init__(self, config:ExplorerConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.root_node = self.config.root_node
        self.provider_engine = self.config.provider
        self.style_provider = self.config.tree_style
        self.style = self.config.explorer_style
        self.selection_mode = self.config.selection_mode
        self.selection_by_type_mode=self.config.selection_by_type_mode
        self.checkbox_mode=self.config.checkbox_mode
        self.t_m = TreeManager(self.root_node)
        self.current_nodes = []

    # -------------------------------------------------
    # Basic TreeModel
    # -------------------------------------------------

    def rowCount(self, parent=QModelIndex()):

        if not parent.isValid():
            node = self.root_node
        else:
            node = self.get_node_from_index(parent)

        return node.child_count()

    def columnCount(self, parent=QModelIndex()):
        return 1

    def index(self, row, column, parent=QModelIndex()):

        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = self.get_node_from_index(parent)

        child_node = parent_node.child(row)

        if child_node:
            return self.createIndex(
                row,
                column,
                child_node
            )

        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        try:
            node = self.get_node_from_index(index)
            parent_node = node.parent
        except AttributeError:
            return QModelIndex()

        if (parent_node is None or parent_node == self.root_node):
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    # -------------------------------------------------
    # Data Roles
    # -------------------------------------------------
    def data(self, index, role):
        if not index.isValid():
            return None
        node = self.get_node_from_index(index)
        if node.hidden is None: 
            return None
        # text provider
        if role == Qt.ItemDataRole.DisplayRole:
            return self.style.text(node)

        if role == Qt.ItemDataRole.ToolTipRole:
            return self.style.tooltip(node)

        if role == Qt.ItemDataRole.DecorationRole:
            return self.style.icon(node)

        # checkbox
        if role == Qt.ItemDataRole.CheckStateRole:
            if not node.selectable:
                return None
            return (
                Qt.CheckState.Checked
                if node.selected
                else Qt.CheckState.Unchecked
            )
        
        # visual styling provider
        if role in (
            Qt.ItemDataRole.ForegroundRole,
            Qt.ItemDataRole.BackgroundRole,
            Qt.ItemDataRole.FontRole,
        ):
            return self.style_provider.get_style(
                node,
                role
            )
        return None
    
    # -------------------------------------------------
    # Config and Styles
    # -------------------------------------------------
    def set_new_config(self,config:ExplorerConfig):
        self.config=config
        self.root_node = self.config.root_node
        self.provider_engine = self.config.provider
        self.style_provider = self.config.tree_style
        self.style = self.config.explorer_style
        self.selection_mode = self.config.selection_mode
        self.selection_by_type_mode = self.config.selection_by_type_mode
        self.checkbox_mode = self.config.checkbox_mode

    def set_new_explorer_style(self,style:TreeStyle):
        if isinstance(style,TreeStyle):
            self.style=style
    
    def set_new_tree_style(self,style:TreeStyleProvider):
        if isinstance(style,TreeStyleProvider): 
            self.style_provider = style
    
    # -------------------------------------------------
    # Item Flags
    # -------------------------------------------------

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        node = self.get_node_from_index(index)
        if not isinstance(node,TreeNode):
            return Qt.ItemFlag.NoItemFlags
        selectable=self.get_node_selectability(node)
        node.selectable= selectable
        if node.hidden:
            return Qt.ItemFlag.NoItemFlags
        if node.locked:
            return Qt.ItemFlag.ItemIsEnabled
        # print("flags ",node,"->",node.selectable)
        if selectable:
            flags= (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
        else:
            flags = (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )

        return flags

    # -------------------------------------------------
    # Checkbox Editing
    # -------------------------------------------------

    def get_node_selectability(self, node: TreeNode) -> bool:
        if not node:
            return False
        
        if self.checkbox_mode == CheckBoxMode.NO_CHECKBOX:
            return False

        if self.selection_by_type_mode == SelectionByTypeMode.FILES_ONLY:
            return node.i_am == "file"

        elif self.selection_by_type_mode == SelectionByTypeMode.DIRS_ONLY:
            return node.i_am in ("dir", "folder")

        elif self.selection_by_type_mode == SelectionByTypeMode.FILES_DIRS_ONLY:
            return node.i_am in ("dir", "folder", "file")

        elif self.selection_by_type_mode == SelectionByTypeMode.DATABASE:
            return node.i_am == "database"

        elif self.selection_by_type_mode == SelectionByTypeMode.MAP:
            return node.i_am == "map"

        elif self.selection_by_type_mode == SelectionByTypeMode.ROOT:
            return node.i_am == "root"

        return True

    def setData( self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        node = self.get_node_from_index(index)
        selectable = self.get_node_selectability(node)
        node.selectable = selectable
        if not selectable:
            return False
        else:
            if role != Qt.ItemDataRole.CheckStateRole:
                return False
            is_selected = (value == Qt.CheckState.Checked or value == Qt.CheckState.Checked.value)
            if is_selected:
                if self.selection_mode == SelectionMode.SINGLE:
                    # uncheck everything
                    for nnn in self.t_m.get_nodes_by_attribute("selected", True):
                        nnn.selected = False
                    self.t_m.set_selected(node,is_selected)    
                else:
                    self.t_m.set_selected(node,is_selected)
            else:    
                self.t_m.set_selected(node,is_selected)
            self.userSelectionChanged.emit([node])
            # update bloodline
            self._rebuild_selection_state()
            self.layoutChanged.emit()
        return True

    # -------------------------------------------------
    # Selection propagation
    # -------------------------------------------------

    def _rebuild_selection_state(self):
        self.t_m.clear_selected_children(self.t_m.root)
        self.t_m.update_selected_children(self.t_m.root)

    # -------------------------------------------------
    # Lazy loading support
    # -------------------------------------------------

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            return True
        node = self.get_node_from_index(parent)
        if node.i_am != "file":
            return True

        return False

    def canFetchMore(self, parent):
        if not parent.isValid():
            return False
        node = self.get_node_from_index(parent)
        if node.i_am == "file":
            return False
        return not node.loaded
    
    def fetchMore(self, parent):
        if not parent.isValid():
            return
        node = self.get_node_from_index(parent)
        if not isinstance(node, TreeNode):
            return
        if hasattr(self, "lazy_loader"):
            self.lazyLoading.emit(True)
            try:
                self.lazy_loader(node)
            finally:
                self.lazyLoading.emit(False)
        else:
            node.loaded = True
        self.t_m.register_subtree(node)
        self.layoutChanged.emit()

    def load_directory(self, node):
        path = node.path
        if hasattr(self.provider_engine, "list_items_in_path"):
            fcn = self.provider_engine.list_items_in_path
        else:
            fcn=os.listdir
        for item in fcn(path):
            child = TreeNode(item)
            child.path = os.path.join(path, item)
            _ , is_file = self.provider_engine.validate_path_file(path)
            if not is_file:
                child.i_am = "dir"
            else:
                child.i_am = "file"
            self.t_m.add_child(node,child)

    def get_selected_ids(self):
        return self.t_m.get_selected_ids()
    
    def get_selected_nodes(self):
        return self.t_m.get_selected_nodes()
    
    def get_node_from_index(self,index:QModelIndex)->TreeNode:
        node = index.internalPointer()
        return node
    
    def get_index_from_node(self, node: TreeNode, column: int = 0) -> QModelIndex:
        if node is None:
            return QModelIndex()
        if node.parent is None:
            return QModelIndex()
        return self.createIndex(
            node.row(),
            column,
            node
        )
    
    def index_from_node(self, node: TreeNode):
        if node is None:
            return QModelIndex()
        parent = node.parent
        if parent is None:
            return QModelIndex()
        return self.createIndex(parent.children.index(node), 0, node)
    
    def toggle_current(self):
        self.get_node_from_index()
        node_list=self.curr()
        for node in node_list:
            self.t_m.toggle_selection(node)
    
        