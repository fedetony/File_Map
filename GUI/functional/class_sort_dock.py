# class_sort_dock.py
#     SortPage (UI only)
#     ↳ emits signals (drag, drop, rename, etc.)

# models/
#     filesystem_model.py (lazy QAbstractItemModel)
#     virtual_model.py (editable QAbstractItemModel)

# controllers/
#     sort_controller.py
#         - connects models to views
#         - handles drag & drop logic
#         - records macro operations
#         - updates virtual model
#         - exposes API to main window

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTreeView, QListWidget, QLabel, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint


class SortPage(QWidget):
    # Signals for controller
    rename_requested = pyqtSignal(object)          # index
    new_folder_requested = pyqtSignal(object)      # parent index
    delete_requested = pyqtSignal(object)          # index
    refresh_requested = pyqtSignal()
    copy_requested = pyqtSignal(object)            # index
    cut_requested = pyqtSignal(object)             # index
    paste_requested = pyqtSignal(object)           # target index
    expand_requested = pyqtSignal(object)          # index
    collapse_requested = pyqtSignal(object)        # index

    apply_macro_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    save_map_requested = pyqtSignal()
    load_map_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("<h2>Sort / File Mapping Tool</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Source TreeView
        self.source_view = QTreeView()
        self.source_view.setHeaderHidden(False)
        self.source_view.setObjectName("sourceTree")
        self.source_view.setDragEnabled(True)
        self.source_view.setAcceptDrops(False)
        self.source_view.setDragDropMode(QTreeView.DragDropMode.DragOnly)

        # Target TreeView
        self.target_view = QTreeView()
        self.target_view.setHeaderHidden(False)
        self.target_view.setObjectName("targetTree")
        self.target_view.setDragEnabled(True)
        self.target_view.setAcceptDrops(True)
        self.target_view.setDropIndicatorShown(True)
        self.target_view.setDragDropMode(QTreeView.DragDropMode.DragDrop)
        self.target_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.target_view.customContextMenuRequested.connect(self.open_context_menu)

        splitter.addWidget(self.source_view)
        splitter.addWidget(self.target_view)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Macro list
        self.macro_list = QListWidget()
        layout.addWidget(self.macro_list)

    def open_context_menu(self, pos: QPoint):
        index = self.target_view.indexAt(pos)
        menu = QMenu(self)

        act_rename = menu.addAction("Rename")
        act_new_folder = menu.addAction("New Folder")
        act_delete = menu.addAction("Delete")
        menu.addSeparator()
        act_expand = menu.addAction("Expand")
        act_collapse = menu.addAction("Collapse")
        act_refresh = menu.addAction("Refresh")
        menu.addSeparator()
        act_copy = menu.addAction("Copy")
        act_cut = menu.addAction("Cut")
        act_paste = menu.addAction("Paste")
        menu.addSeparator()
        act_undo = menu.addAction("Undo")
        act_redo = menu.addAction("Redo")
        act_apply = menu.addAction("Apply Macro")
        act_save = menu.addAction("Save Map")
        act_load = menu.addAction("Load Map")

        action = menu.exec(self.target_view.mapToGlobal(pos))
        if not action:
            return

        if action == act_rename and index.isValid():
            self.rename_requested.emit(index)
        elif action == act_new_folder:
            parent = index if index.isValid() else self.target_view.rootIndex()
            self.new_folder_requested.emit(parent)
        elif action == act_delete and index.isValid():
            self.delete_requested.emit(index)
        elif action == act_expand and index.isValid():
            self.expand_requested.emit(index)
        elif action == act_collapse and index.isValid():
            self.collapse_requested.emit(index)
        elif action == act_refresh:
            self.refresh_requested.emit()
        elif action == act_copy and index.isValid():
            self.copy_requested.emit(index)
        elif action == act_cut and index.isValid():
            self.cut_requested.emit(index)
        elif action == act_paste:
            target = index if index.isValid() else self.target_view.rootIndex()
            self.paste_requested.emit(target)
        elif action == act_undo:
            self.undo_requested.emit()
        elif action == act_redo:
            self.redo_requested.emit()
        elif action == act_apply:
            self.apply_macro_requested.emit()
        elif action == act_save:
            self.save_map_requested.emit()
        elif action == act_load:
            self.load_map_requested.emit()

    def record_operation(self, text: str):
        self.macro_list.addItem(text)



