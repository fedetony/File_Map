# ask_new_name_dialog.py
from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Callable, Any

import html

from functional.class_icons import Icons
from controllers.class_filemap_cli_manager import FileMapCliManager

class AskNewNameDialog(QtWidgets.QDialog):

    def __init__(
        self,
        text_description,
        parent=None,
        title="New Name",
        default_name=None,
        validation_callback: Callable = None,
    ):
        super().__init__(parent)
        if not validation_callback:
            self.validate_callback=self._no_validation_callback
        else:    
            self.validate_callback=validation_callback
        
        self.default_name=default_name

        self.setWindowTitle(title)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        top_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_MessageBoxQuestion
        )
        icon_label.setPixmap(icon.pixmap(48, 48))
        top_layout.addWidget(icon_label)

        text_label = QtWidgets.QLabel(text_description)

        text_label.setWordWrap(True)
        top_layout.addWidget(text_label, 1)

        layout.addLayout(top_layout)

        self.line_edit = QtWidgets.QLineEdit()
        if not self.default_name:
            self.line_edit.setPlaceholderText(
                "Type Here..."
            )
        else:
            self.line_edit.setText(self.default_name)
        self.line_edit.setMinimumWidth(300)
        self.line_edit.setMinimumHeight(28)
        layout.addWidget(self.line_edit)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.ok_button = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        
        self.ok_button.setEnabled(False)
        self.line_edit.textChanged.connect(self._update_ok_button)


        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self._update_ok_button(self.line_edit.text().strip())

    def _update_ok_button(self, text):
        if text:
            self.ok_button.setEnabled(self.validate_callback(text.strip()))

    def _no_validation_callback(self,txt)->bool:
        return True
    
    def confirmed(self):
        return self.validate_callback(self.line_edit.text().strip())
    

class NewMapDialog(QtWidgets.QDialog):

    def __init__(
        self,
        fmap: FileMapCliManager, default_map_name=None, title="New Selection Map", icon_name="selection map" ,parent=None):
        super().__init__(parent)

        self.fmap = fmap
        self.icons = Icons()
        self.processed_name = ""
        self.default_map_name=default_map_name
        self.title=title

        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowIcon(self.icons.icon(icon_name))
        layout = QtWidgets.QFormLayout(self)

        # Database
        self.database_combo = QtWidgets.QComboBox()

        db_list = self.fmap.get_active_databases_in_dbm()
        databases = [
            (
                str(db.database_filepath),
                str(db.name),
                str(db.db_file),
                bool(db.active),
            ) for db in db_list]
        
        for db_full, db_name, db_file, is_active in databases:
            if is_active:
                self.database_combo.addItem(f"{db_name} — {db_file}", db_full)

        # # Select source database initially
        # index = self.database_combo.findData(db_from)
        index = 0 
        if index >= 0:
            self.database_combo.setCurrentIndex(index)

        # Name
        
        self.name_edit = QtWidgets.QLineEdit()
        if not self.default_map_name:
            self.name_edit.setPlaceholderText("Type Here...")
        else:
            self.name_edit.setText(self.default_map_name)

        self.name_edit.selectAll()
        self.name_edit.setToolTip(
            "You can use % (date/time), # (date), ? (time), "
            "& (directory), or ! (full path).")

        # Result preview
        self.result_label = QtWidgets.QLabel()
        self.result_label.setStyleSheet("color: #666666;")

        layout.addRow(
            self._icon_label("db", "Database:"),
            self.database_combo)

        layout.addRow(
            self._icon_label("mapping", "Map name:"), self.name_edit)

        layout.addRow(
            self._icon_label("keep map", "Result:"), self.result_label)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

        # Live preview
        self.name_edit.textChanged.connect(self._update_preview)
        self.database_combo.currentIndexChanged.connect(self._update_preview)
        self._update_preview()

    def _icon_label(self, icon_name, text):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(5)

        icon = QtWidgets.QLabel()
        icon.setPixmap(self.icons.icon(icon_name).pixmap(18, 18))

        label = QtWidgets.QLabel(text)

        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addStretch()

        return widget
    
    def _update_preview(self):
        name = self.name_edit.text().strip()
        db_path = self.database_combo.currentData()

        if not name or not db_path:
            self.processed_name = ""
            self.result_label.clear()
            return

        self.processed_name = (
            self.fmap.cma.format_new_table_name(name, db_path))

        self.result_label.setText(
            f"<b>{html.escape(self.processed_name)}</b>"
        )

    def _accept(self):
        if not self.processed_name:
            QtWidgets.QMessageBox.warning(
                self,
                self.title,
                "Please enter a map name.",
            )
            return
        self.accept()

    def get_values(self):
        return (
            self.database_combo.currentData(),
            self.processed_name,
        )