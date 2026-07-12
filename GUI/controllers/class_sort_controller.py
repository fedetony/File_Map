import json
from PyQt6.QtCore import QItemSelectionModel
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QFileSystemModel

from models.class_virtual_model import VirtualModel
from models.class_macro_engine import MacroEngine


class SortController:
    def __init__(self, sort_page, status_db_label, status_map_label, logger_widget):
        self.page = sort_page
        self.status_db_label = status_db_label
        self.status_map_label = status_map_label
        self.logger = logger_widget

        # Models
        self.source_model = QFileSystemModel()
        self.source_model.setRootPath("/")  # TODO: set to active map root or device root
        self.page.source_view.setModel(self.source_model)

        self.virtual_model = VirtualModel()
        self.page.target_view.setModel(self.virtual_model)

        # Macro engine
        self.macro = MacroEngine()

        # Clipboard for copy/cut/paste
        self.clipboard_index = None
        self.clipboard_mode = None  # "copy" or "cut"

        # Connect signals
        self.page.rename_requested.connect(self.on_rename)
        self.page.new_folder_requested.connect(self.on_new_folder)
        self.page.delete_requested.connect(self.on_delete)
        self.page.refresh_requested.connect(self.on_refresh)
        self.page.copy_requested.connect(self.on_copy)
        self.page.cut_requested.connect(self.on_cut)
        self.page.paste_requested.connect(self.on_paste)
        self.page.expand_requested.connect(self.on_expand)
        self.page.collapse_requested.connect(self.on_collapse)

        self.page.undo_requested.connect(self.on_undo)
        self.page.redo_requested.connect(self.on_redo)
        self.page.apply_macro_requested.connect(self.on_apply_macro)
        self.page.save_map_requested.connect(self.on_save_map)
        self.page.load_map_requested.connect(self.on_load_map)

        # Drag & drop: override dropEvent on target view
        self.page.target_view.dropEvent = self.handle_drop_event

    # --- logging helper ---

    def log(self, msg: str):
        self.logger.append(msg)

    # --- context menu actions ---

    def on_rename(self, index):
        self.page.target_view.edit(index)

    def on_new_folder(self, parent_index):
        name = "New Folder"
        self.virtual_model.insert_folder(parent_index, name)
        path = self.virtual_model.filePath(parent_index) + "/" + name
        self.macro.add_op("mkdir", path=path)
        self.page.record_operation(f"mkdir {path}")
        self.log(f"[MACRO] mkdir {path}")

    def on_delete(self, index):
        path = self.virtual_model.filePath(index)
        self.virtual_model.remove_node(index)
        self.macro.add_op("delete", path=path)
        self.page.record_operation(f"delete {path}")
        self.log(f"[MACRO] delete {path}")

    def on_refresh(self):
        # TODO: reload from backend map if needed
        self.log("[INFO] Refresh requested")

    def on_copy(self, index):
        self.clipboard_index = index
        self.clipboard_mode = "copy"
        self.log(f"[INFO] Copy {self.virtual_model.filePath(index)}")

    def on_cut(self, index):
        self.clipboard_index = index
        self.clipboard_mode = "cut"
        self.log(f"[INFO] Cut {self.virtual_model.filePath(index)}")

    def on_paste(self, target_index):
        if not self.clipboard_index or not self.clipboard_mode:
            return
        src_path = self.virtual_model.filePath(self.clipboard_index)
        dst_path = self.virtual_model.filePath(target_index) + "/" + src_path.split("/")[-1]
        op_type = "copy" if self.clipboard_mode == "copy" else "move"
        self.macro.add_op(op_type, src=src_path, dst=dst_path)
        self.page.record_operation(f"{op_type} {src_path} → {dst_path}")
        self.log(f"[MACRO] {op_type} {src_path} → {dst_path}")
        # TODO: update virtual model structure accordingly

    def on_expand(self, index):
        self.page.target_view.expand(index)

    def on_collapse(self, index):
        self.page.target_view.collapse(index)

    # --- drag & drop from source to target ---

    def handle_drop_event(self, event):
        source_index = self.page.source_view.currentIndex()
        target_index = self.page.target_view.indexAt(event.position().toPoint())
        if not source_index.isValid() or not target_index.isValid():
            return
        src_path = self.source_model.filePath(source_index)
        dst_path = self.virtual_model.filePath(target_index) + "/" + src_path.split("/")[-1]
        self.macro.add_op("move", src=src_path, dst=dst_path)
        self.page.record_operation(f"move {src_path} → {dst_path}")
        self.log(f"[MACRO] move {src_path} → {dst_path}")
        # TODO: insert into virtual model
        self.virtual_model.insert_folder(target_index, src_path.split("/")[-1])
        event.acceptProposedAction()

    # --- undo/redo (virtual only) ---

    def on_undo(self):
        op = self.macro.undo_last()
        if not op:
            return
        self.log(f"[UNDO] {op.op_type} {op.args}")
        # TODO: reverse op in virtual_model

    def on_redo(self):
        op = self.macro.redo_last()
        if not op:
            return
        self.log(f"[REDO] {op.op_type} {op.args}")
        # TODO: re-apply op in virtual_model

    # --- apply macro to filesystem (your engine) ---

    def on_apply_macro(self):
        self.log("[APPLY] Macro requested")
        # TODO: call your existing engine here with self.macro.ops
        # e.g. self.backend.apply_macro(self.macro.ops)

    # --- save/load map (JSON) ---

    def on_save_map(self):
        path, _ = QFileDialog.getSaveFileName(None, "Save Map", "", "JSON (*.json)")
        if not path:
            return
        data = self.virtual_model.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.log(f"[SAVE] Map saved to {path}")

    def on_load_map(self):
        path, _ = QFileDialog.getOpenFileName(None, "Load Map", "", "JSON (*.json)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.virtual_model.beginResetModel()
        self.virtual_model.from_dict(data)
        self.virtual_model.endResetModel()
        self.log(f"[LOAD] Map loaded from {path}")
