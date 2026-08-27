# class_explorer_tree_widget.py
import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QLineEdit,
    QLabel,
    QMenu,
    QListWidget,
)
from PyQt6.QtWidgets import QAbstractItemView

from PyQt6.QtCore import Qt, pyqtSignal
from models.class_explorer_config import ExplorerConfig
from models.class_enums_definitions import SelectionByTypeMode, SelectionMode, CheckBoxMode
from models.class_explorer_tree_model import ExplorerTreeModel, TreeNode
from models.class_action_provider import DefaultFileActionProvider
from models.class_lazy_loader import LazyLoaderProvider
from PyQt6.QtGui import QShortcut, QKeySequence


from controllers.class_tree_node_manager import (TreeManager)

class ExplorerTreeWidget(QWidget):

    nodeClicked = pyqtSignal(TreeNode)
    nodeDoubleClicked = pyqtSignal(TreeNode)
    nodeRightClicked = pyqtSignal(TreeNode)
    userSelectionChanged = pyqtSignal(list)
    currentSelectionChanged = pyqtSignal(list)
    actionEvaluated = pyqtSignal(object,object)
    nodeExpanded = pyqtSignal(TreeNode)
    nodeCollapsed = pyqtSignal(TreeNode)
    lazyLoading = pyqtSignal(bool)

    def __init__(self, config: ExplorerConfig, parent=None):
        super().__init__(parent)

        self.config = config
        self.provider = config.provider
        self.action_provider = config.action_provider
        self._current_nodes = []
        self.user_typing=False
        self._build_manager()
        self._build_model()
        self._build_ui()
        self._connect()
        self._setup_shortcuts()
        # Expand / Collapse nodes
        self._walk_tree_expansion(self.t_m.root)
    
    def _build_manager(self):
        if self.config.root_node is None:
            raise ValueError("ExplorerConfig.root_node required")
        self.t_m = TreeManager(self.config.root_node)
    
    def _build_model(self):
        self.model = ExplorerTreeModel(self.config)
        self.model.t_m = self.t_m
        self.model.set_new_explorer_style(self.config.explorer_style)
        self.model.set_new_tree_style(self.config.tree_style)
        self.model.userSelectionChanged.connect(self.userSelectionChanged.emit)
        self.model.lazyLoading.connect(self.lazyLoading.emit)
        if self.config.lazy_loading:
            lazy = self.config.lazy_loader
            if isinstance(self.config.lazy_loader,LazyLoaderProvider):
                lazy.set_selectionbytypemode(self.config.selection_by_type_mode)
                lazy.set_selectionmode(self.config.selection_mode)
                lazy.set_checkboxmode(self.config.checkbox_mode)
                lazy.set_tree_manager(self.t_m)
                setattr(self.model,"lazy_loader",lazy.lazy_loader)
            else:
                setattr(self.model,"lazy_loader",self.config.lazy_loader)
    
    def _build_ui(self):
        self.layout = QVBoxLayout(self)

        # path edit
        if self.config.show_path_edit:
            self.path_edit = QLineEdit()
            self.layout.addWidget(self.path_edit)
        else:
            self.path_edit = None
        # text label    
        if self.config.show_label:
            self.text_label = QLabel()
            self.layout.addWidget(self.text_label)
            self.text_label.setText(self.config.root_node.name)
        else:
            self.text_label = None
        # tree
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        if self.config.selection_mode == SelectionMode.SINGLE:
            self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        else:
            self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            

        self.layout.addWidget(self.tree)

        self.option_popup = OptionPopup(self)
        self.option_popup.setSpacing(0)
        self.option_popup.setStyleSheet("""
                                        QListWidget {
                                            padding: 0px;
                                            margin: 0px;
                                        }
                                        QListWidget::item {
                                            padding: 1px;
                                        }
                                        """)
        self.option_popup.hide()

    def _connect(self):
        self.tree.clicked.connect(self._on_tree_clicked)
        self.tree.doubleClicked.connect(self._on_tree_double_clicked)
        
        self.tree.expanded.connect(self._on_tree_expanded)
        self.tree.collapsed.connect(self._on_tree_collapsed)

        if (self.path_edit and self.provider):
            self.path_edit.textChanged.connect(self._path_changed)
            self.path_edit.textEdited.connect(self._update_tv_from_path)
            self.option_popup.itemClicked.connect(self._option_selected)
            self.option_popup.optionSelected.connect(self._option_text_selected)

        if self.action_provider:
            self.tree.customContextMenuRequested.connect(self._show_context_menu)

        if self.tree.selectionModel():
            self.tree.selectionModel().selectionChanged.connect(self._selection_changed)
    
    def _fetch(self, index):
        if self.model.canFetchMore(index):
            self.model.fetchMore(index)
    
    def _path_changed(self, txt):
        if hasattr(self.provider,"get_possible_path_list"):   
            opts = (self.provider.get_possible_path_list(txt))
            self.show_options(opts) # opts[:10])
        if hasattr(self.provider,"get_label_text"):
            label_fcn= getattr(self.provider,"get_label_text","") 
            label_txt = label_fcn()
            if self.text_label and label_txt:
                self.text_label.setText(label_txt)

    # --------------------------------------------------
    # Access helpers
    # --------------------------------------------------

    def current_node(self):
        idx = self.tree.currentIndex()
        if not idx.isValid():
            return None
        return self.model.get_node_from_index(idx)
    
    def selected_nodes(self):
        return self.t_m.get_selected_nodes()
    
    def selected_ids(self):
        return self.t_m.get_selected_ids()
    
    def refresh(self):
        self.model.layoutChanged.emit()

    # --------------------------------------------------
    # lazy load
    # --------------------------------------------------

    def _on_tree_expanded(self, index):
        node = self.model.get_node_from_index(index)
        if not node:
            return
        node.expand = True
        for child in node.children:
            self._walk_tree_expansion(child)
        self.nodeExpanded.emit(node)
        self._fetch(index)
    
    def _on_tree_collapsed(self, index):
        node = self.model.get_node_from_index(index)
        if not node:
            return
        node.expand = False
        self.nodeCollapsed.emit(node)
    
    def _walk_tree_expansion(self, node: TreeNode):
        index = self.model.get_index_from_node(node)
        if not index.isValid():
            return
        # Collapse or expand if explicitly stated
        is_expanded=self.tree.isExpanded(index)
        if node.expand == True and not is_expanded:
            self.tree.expand(index)
        elif node.expand == False and is_expanded:
            self.tree.collapse(index)

        for child in node.children:
            self._walk_tree_expansion(child)


    
    # --------------------------------------------------
    # Current nodes
    # --------------------------------------------------

    def _on_tree_clicked(self, index):
        node = self.model.get_node_from_index(index)
        self.user_typing = False
        if node:
            self.nodeClicked.emit(node)
    
    def _on_tree_double_clicked(self, index):
        node = self.model.get_node_from_index(index)
        self.user_typing = False
        if node:
            self.nodeDoubleClicked.emit(node)
    
    def current_nodes(self)->list[TreeNode]:
        return self._current_nodes
    
    def current_node(self)->TreeNode:
        if self._current_nodes:
            return self._current_nodes[0]
        return None
    
    def _selection_changed(self, selected, deselected):
        self._current_nodes = []
        for idx in self.tree.selectionModel().selectedRows():
            node = self.model.get_node_from_index(idx)
            if node:
                self._current_nodes.append(node)
        self.currentSelectionChanged.emit(self._current_nodes)
        if not self.user_typing or self.tree.hasFocus():
            self._update_text_edit_from_tv()
        #print("New selection ->",self._current_nodes)

    def toggle_current_nodes(self):
        # print("toggle_current_nodes",len(self._current_nodes))
        if self.config.selection_mode == SelectionMode.SINGLE:
            self.toggle_current_item()
        else:
            for node in self._current_nodes:
                # print(node.name)
                self.t_m.toggle_selection(node)
            self.userSelectionChanged.emit([self._current_nodes])
        self.refresh()
    
    def toggle_current_item(self):
        idx = self.tree.currentIndex()
        if not idx.isValid():
            return
        if self.config.checkbox_mode == CheckBoxMode.NO_CHECKBOX:
            return
        node = self.model.get_node_from_index(idx)
        if not node.selectable:
            return
        current = self.model.data(idx, Qt.ItemDataRole.CheckStateRole)
        if current == Qt.CheckState.Checked:
            state = Qt.CheckState.Unchecked
        else:
            state = Qt.CheckState.Checked
        self.userSelectionChanged.emit([node])
        self.model.setData(idx, state, Qt.ItemDataRole.CheckStateRole)
    
    def _update_text_edit_from_tv(self):
        node=self.current_node()
        path=self.t_m.get_full_path(node,sep=os.sep)
        if self.path_edit:
            self.path_edit.blockSignals(True)
            self.path_edit.setText(path)
            self.path_edit.blockSignals(False)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def expand_node(self, node: TreeNode):
        index = self.model.index_from_node(node)
        if index.isValid():
            self.tree.expand(index)

    def collapse_node(self, node: TreeNode):
        index = self.model.index_from_node(node)
        if index.isValid():
            self.tree.collapse(index)
    
    def set_lazy_attribute(self,attribute,value):
        """Set lazy loader atrributes to change behavior: 
            defaults (list)
            locked (list)
            hidden (list)
            blank (list)
            tree_manager (TreeManager)

            selectionbytypemode (SelectionByTypeMode)
            selectionmode (SelectionMode)
            checkboxmode (CheckBoxMode)

            lazy_loader(self,node:TreeNode) (Callable)
        """
        lazy = self.config.lazy_loader
        if not isinstance(lazy, LazyLoaderProvider):
            return
        if hasattr(lazy, attribute):
            setattr(lazy,attribute,value)

    # --------------------------------------------------
    # Generic context menu
    # --------------------------------------------------
    def _show_context_menu(self, pos):
        if not self.config.show_context_menu:
            return
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return

        node = self.model.get_node_from_index(index)
        self.nodeRightClicked.emit(node)
        menu = QMenu(self)

        actions = (self.action_provider.get_actions(node,self.t_m))

        for a in actions:
            if not a.text:
                continue
            visible = (a.visible(node) if callable(a.visible) else a.visible)
            if not visible:
                continue
            if a.separator_before:
                menu.addSeparator()
            qt_action = menu.addAction(a.text)
            enabled = (a.enabled(node) if callable(a.enabled) else a.enabled)
            if a.shortcut and enabled:
                qt_action.setShortcut(QKeySequence(a.shortcut))
            if a.icon:
                qt_action.setIcon(a.icon)
            if a.tip:
                qt_action.setToolTip(a.tip)
                qt_action.setStatusTip(a.tip)
            qt_action.setEnabled(enabled)
            qt_action.setCheckable(a.checkable)
            if a.checkable:
                checked = (a.checked(node) if callable(a.checked) else a.checked)
                qt_action.setChecked(checked)
            

            qt_action.triggered.connect(
                lambda checked=False, a=a: self._execute_action(a))


        menu.exec(self.tree.viewport().mapToGlobal(pos))
        self.refresh()
    
    def _execute_action(self, action):
        result = self.action_provider.execute_action(
            self.current_node(),
            action
        )
        self.actionEvaluated.emit(action,result)
        return result

    # --------------------------------------------------
    # Generic shortcuts
    # --------------------------------------------------

    def _setup_shortcuts(self):
        self.shortcuts = []
        if not self.action_provider:
            return

        for action in self.action_provider.get_global_actions(self):
            if not action.shortcut:
                continue
            shortcut = QShortcut(
                QKeySequence(action.shortcut),
                self
            )

            shortcut.activated.connect(
                lambda a=action:
                self.action_provider.execute_action(
                    self.current_node(),
                    a
                )
            )
            self.shortcuts.append(shortcut)
            print("registered", action.shortcut)

    # --------------------------------------------------
    # Autocomplete
    # --------------------------------------------------
    def autocomplete(self):
        if not self.provider or not self.path_edit:
            return
        txt = self.path_edit.text()
        txt = self.provider.autocomplete_path(txt)
        self.path_edit.setText(txt)
    
    def _update_tv_from_path(self, text):
        if not self.provider:
            return
        self.user_typing = True
        valid_path, mount, path_nm = self.provider.get_valid_path_from_text(text)
        if not valid_path:
            return
        parts = self.provider.path_to_list(valid_path)
        if len(parts) == 0:
            return
        #self.lazyLoading.emit(True)
        try:
            print("Parts, mount, path nm", parts, mount, path_nm)
            current = self.t_m.root
            for child in current.children:
                nname = self.provider.normalize_path(child.name)
                if nname == mount or nname.lower() == mount.lower():
                    current = child
                    break

            for part in parts:
                # Ensure loaded
                if not current.loaded and self.model.lazy_loader:
                    self.model.lazy_loader(current)
                found = self.t_m.find_child_name(current, part)

                # Stop at last valid node
                if found is None:
                    break

                # Expand tree
                idx = self.model.get_index_from_node(found)

                if idx.isValid():
                    self.tree.expand(idx)

                current = found

            # Highlight current location
            idx = self.model.get_index_from_node(current)
            if idx.isValid():
                self.tree.setCurrentIndex(idx)
                self.tree.scrollTo(idx)
        finally:
            # self.lazyLoading.emit(False)
            pass
    
    def set_current_node(self, node: TreeNode):
        idx = self.model.get_index_from_node(node)
        if not idx.isValid():
            return
        self.tree.setCurrentIndex(idx)
        self.tree.scrollTo(idx)
    
    def expand_to_node(self, node: TreeNode):
        for parent in node.get_bloodline()[1:-1]:
            idx = self.model.get_index_from_node(parent)
            if idx.isValid():
                self.tree.expand(idx)
        self.set_current_node(node)

    # --------------------------------------------------
    # Pop up list
    # --------------------------------------------------
    def _option_selected(self, item):
        if not self.path_edit:
            return
        txt = item.text()
        self.path_edit.setText(txt)
        self.option_popup.hide()
        self._update_tv_from_path(txt)

    def show_options(self, options):
        if not self.path_edit:
            return
        self.option_popup.clear()
        self.option_popup.addItems(options)
        if len(options) == 0:
            self.option_popup.hide()
            return
        # place below path edit
        pos = self.path_edit.geometry()
        self.option_popup.setGeometry(
            pos.x(),
            pos.bottom() + 2,
            pos.width(),
            min(200, 22 * len(options) + 4)
        )
        rows = min(len(options), 8)
        self.option_popup.setFixedHeight(rows * self.option_popup.sizeHintForRow(0) + 4)
        self.option_popup.setCurrentRow(0)
        self.option_popup.show()
        self.option_popup.raise_()
    
    def _option_text_selected(self, txt):
        if not self.path_edit:
            return
        self.path_edit.setText(txt)
        self.option_popup.hide()
        self.path_edit.setFocus()
    
    def keyPressEvent(self, event):
        if (self.path_edit
            and self.path_edit.hasFocus()
            and self.option_popup.isVisible()
        ):

            if event.key() == Qt.Key.Key_Down:
                self.option_popup.setFocus()
                self.option_popup.setCurrentRow(0)

                event.accept()
                return

        super().keyPressEvent(event)



        
# class OptionPopup(QListWidget):
#     optionSelected = pyqtSignal(str)
#     def keyPressEvent(self, event):

#         if event.key() in (
#             Qt.Key.Key_Return,
#             Qt.Key.Key_Enter
#         ):
#             item = self.currentItem()
#             if item:
#                 self.optionSelected.emit(
#                     item.text()
#                 )
#             return
        
#         if event.key() == Qt.Key.Key_Escape:
#             self.hide()
#             if hasattr(self.parent(),"path_edit"):
#                 self.parent().path_edit.setFocus()
#             event.accept()
#             return

#         super().keyPressEvent(event)

class OptionPopup(QListWidget):

    optionSelected = pyqtSignal(str)

    def __init__(self, target_edit=None, parent=None):
        super().__init__(parent)

        self.target_edit = target_edit

        self.setWindowFlags(
            Qt.WindowType.Popup
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def set_target(self, target_edit):
        self.target_edit = target_edit

    def keyPressEvent(self, event):

        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Tab,
            Qt.Key.Key_Space,
            ):
            item = self.currentItem()

            if item:
                self.optionSelected.emit(item.text())

            event.accept()
            return

        if event.key() in (
            Qt.Key.Key_Escape,
            Qt.Key.Key_Delete, 
            ):
            self.hide()

            if self.target_edit:
                self.target_edit.setFocus()

            event.accept()
            return

        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())

        if item:
            self.setCurrentItem(item)
            self.optionSelected.emit(item.text())

        super().mousePressEvent(event)
