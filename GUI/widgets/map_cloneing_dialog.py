

from PyQt6 import QtCore, QtGui, QtWidgets

import html

from functional.class_icons import Icons
from controllers.class_filemap_cli_manager import FileMapCliManager

class CloneMapDialog(QtWidgets.QDialog):

    def __init__(
        self,
        fmap: FileMapCliManager, databases, db_from, map_name, parent=None):
        super().__init__(parent)

        self.fmap = fmap
        self.icons = Icons()
        self.db_from = db_from
        self.processed_name = ""

        self.setWindowTitle("Clone Map")
        self.setModal(True)
        self.setWindowIcon(self.icons.icon("clone"))

        layout = QtWidgets.QFormLayout(self)

        # Database
        self.database_combo = QtWidgets.QComboBox()

        for db_full, db_name, db_file in databases:
            self.database_combo.addItem(
                f"{db_name} — {db_file}",
                db_full,
            )

        # Select source database initially
        index = self.database_combo.findData(db_from)
        if index >= 0:
            self.database_combo.setCurrentIndex(index)

        # Name
        self.name_edit = QtWidgets.QLineEdit(map_name)
        self.name_edit.selectAll()

        self.name_edit.setToolTip(
            "You can use % (date/time), # (date), ? (time), "
            "& (directory), or ! (full path)."
        )

        # Result preview
        self.result_label = QtWidgets.QLabel()
        self.result_label.setStyleSheet(
            "color: #666666;"
        )

        layout.addRow(
            self._icon_label("db", "Database:"),
            self.database_combo,
        )

        layout.addRow(
            self._icon_label("mapping", "Map name:"),
            self.name_edit,
        )

        layout.addRow(
            self._icon_label("keep map", "Result:"),
            self.result_label,
        )

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

        # Live preview
        self.name_edit.textChanged.connect(
            self._update_preview
        )
        self.database_combo.currentIndexChanged.connect(
            self._update_preview
        )

        self._update_preview()

    def _icon_label(self, icon_name, text):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(5)

        icon = QtWidgets.QLabel()
        icon.setPixmap(
            self.icons.icon(icon_name).pixmap(18, 18)
        )

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
            self.fmap.cma.format_new_table_name(
                name,
                db_path,
            )
        )

        self.result_label.setText(
            f"<b>{html.escape(self.processed_name)}</b>"
        )

    def _accept(self):
        if not self.processed_name:
            QtWidgets.QMessageBox.warning(
                self,
                "Clone Map",
                "Please enter a map name.",
            )
            return

        self.accept()

    def get_values(self):
        return (
            self.database_combo.currentData(),
            self.processed_name,
        )