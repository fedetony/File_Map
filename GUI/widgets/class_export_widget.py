import os

from PyQt6 import QtCore, QtGui, QtWidgets

from functional.class_icons import Icons

from dataclasses import dataclass

@dataclass(frozen=True)
class ExportFormat:
    label: str
    value: str
    extension: str

    @property
    def file_filter(self):
        return f"Files (*{self.extension})"


DC_DEFAULT_FORMATS = [
    ExportFormat("Filestruct → JSON", "filestruct_json", ".json"),
    ExportFormat("List → TXT", "list_txt", ".txt"),
    ExportFormat("List → CSV", "list_csv", ".csv"),
    ExportFormat("Text Tree", "text_tree", ".txt"),
]
# fmt = self.exportWidget.getFormatDefinition()
# filters = f"{fmt.file_filter};;All Files (*)"

@dataclass(frozen=True)
class ExportField:
    id: int
    label: str

DC_DEFAULT_FIELDS = [
    ExportField(0, "id"),
    ExportField(1, "dt_data_created"),
    ExportField(2, "dt_data_modified"),
    ExportField(3, "filepath"),
    ExportField(4, "filename"),
    ExportField(5, "md5"),
    ExportField(6, "size"),
    ExportField(7, "dt_file_created"),
    ExportField(8, "dt_file_accessed"),
    ExportField(9, "dt_file_modified"),
]

@dataclass(frozen=True)
class ExportSelection:
    label: str
    value: str

DC_DEFAULT_SELECTIONS = [
    ExportSelection("Expanded", "expanded"),
    ExportSelection("Selected", "selected"),
    ExportSelection("File Tree", "file_tree"),
    ExportSelection("Directory Tree", "directory_tree"),
]

class ExportWidget(QtWidgets.QWidget):

    exportRequested = QtCore.pyqtSignal(dict)

    DEFAULT_FIELDS = [
        (0, "id"),
        (1, "dt_data_created"),
        (2, "dt_data_modified"),
        (3, "filepath"),
        (4, "filename"),
        (5, "md5"),
        (6, "size"),
        (7, "dt_file_created"),
        (8, "dt_file_accessed"),
        (9, "dt_file_modified"),
    ]

    DEFAULT_SELECTIONS = [
        ("Expanded", "expanded"),
        ("Selected", "selected"),
        ("File Tree", "file_tree"),
        ("Directory Tree", "directory_tree"),
    ]

    DEFAULT_FORMATS = [
        ("Filestruct → JSON", "filestruct_json"),
        ("List → TXT", "list_txt"),
        ("List → CSV", "list_csv"),
        ("Text Tree", "text_tree"),
    ]

    def __init__(
        self,
        parent=None,
        fields=None,
        selections=None,
        formats=None,
        default_selection="expanded",
        default_format="filestruct_json",
        default_fields=None,
    ):
        super().__init__(parent)

        self.icons=Icons()
        self.fields = list(
            fields if fields is not None else self.DEFAULT_FIELDS
        )
        self.selections = list(
            selections if selections is not None else self.DEFAULT_SELECTIONS
        )
        self.formats = list(
            formats if formats is not None else self.DEFAULT_FORMATS
        )

        # ------------------------------------------------------------
        # Selection
        # ------------------------------------------------------------

        self.selectionCombo = QtWidgets.QComboBox()
        self._populateCombo(self.selectionCombo, self.selections)

        self.setSelection(default_selection)

        # ------------------------------------------------------------
        # Format
        # ------------------------------------------------------------

        self.formatCombo = QtWidgets.QComboBox()
        self._populateCombo(self.formatCombo, self.formats)

        self.setFormat(default_format)

        # ------------------------------------------------------------
        # Fields
        # ------------------------------------------------------------

        self.fieldChecks = {}

        self.fieldsWidget = QtWidgets.QWidget()
        self.fieldsLayout = QtWidgets.QGridLayout(self.fieldsWidget)
        self.fieldsLayout.setContentsMargins(0, 0, 0, 0)
        self.fieldsLayout.setHorizontalSpacing(8)
        self.fieldsLayout.setVerticalSpacing(2)

        fieldsBox = QtWidgets.QGroupBox("Fields")
        fieldsBox.setLayout(self.fieldsLayout)

        self.setFields(
            self.fields,
            selected_fields=default_fields,
        )

        # ------------------------------------------------------------
        # Target
        # ------------------------------------------------------------

        self.targetEdit = QtWidgets.QLineEdit()
        self.targetEdit.setPlaceholderText("Export file...")

        self.browseButton = QtWidgets.QPushButton("Browse...")
        self.browseButton.setIcon(self.icons.icon("folder download"))
        self.browseButton.clicked.connect(self.browseTarget)

        self.exportButton = QtWidgets.QPushButton("Export")
        self.exportButton.setIcon(self.icons.icon("green arrow dn"))
        self.exportButton.clicked.connect(self.requestExport)

        # icons
        self.export_icon = QtWidgets.QToolButton()
        self.export_icon.setIcon(self.icons.icon("green arrow dn"))
        self.export_icon.setAutoRaise(True)
        self.export_icon.setEnabled(True)
        self.export_icon.setFixedWidth(32)

        self.save_icon = QtWidgets.QToolButton()
        self.save_icon.setIcon(self.icons.icon("save as"))
        self.save_icon.setAutoRaise(True)
        self.save_icon.setEnabled(True)
        self.save_icon.setFixedWidth(32)
        # ------------------------------------------------------------
        # Top row
        # ------------------------------------------------------------

        topLayout = QtWidgets.QHBoxLayout()
        topLayout.setContentsMargins(0, 0, 0, 0)

        topLayout.addWidget(self.export_icon)
        topLayout.addWidget(QtWidgets.QLabel("Export:"))
        topLayout.addWidget(self.selectionCombo)

        topLayout.addSpacing(8)

        topLayout.addWidget(QtWidgets.QLabel("Format:"))
        topLayout.addWidget(self.formatCombo)

        topLayout.addStretch()

        # ------------------------------------------------------------
        # Target row
        # ------------------------------------------------------------

        targetLayout = QtWidgets.QHBoxLayout()
        targetLayout.setContentsMargins(0, 0, 0, 0)

        targetLayout.addWidget(self.save_icon)
        targetLayout.addWidget(QtWidgets.QLabel("Save:"))
        targetLayout.addWidget(self.targetEdit)
        targetLayout.addWidget(self.browseButton)
        targetLayout.addWidget(self.exportButton)

        # ------------------------------------------------------------
        # Main layout
        # ------------------------------------------------------------

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        layout.addLayout(topLayout)
        layout.addWidget(fieldsBox)
        layout.addLayout(targetLayout)

    # ============================================================
    # Helper
    # ============================================================

    @staticmethod
    def _populateCombo(combo, items):
        combo.clear()

        for label, value in items:
            combo.addItem(label, value)


    # ------------------------------------------------------------------
    # Target
    # ------------------------------------------------------------------

    def browseTarget(self):
        """Open a Save As dialog for the current export format."""

        format_value = self.getFormat()

        # Find the definition for the current format
        format_def = next(
            (
                fmt
                for fmt in self.formats
                if fmt[1] == format_value
            ),
            None,
        )

        if format_def is not None and len(format_def) >= 3:
            extension = format_def[2]
        else:
            extension = "*.*"

        # Use the existing target as the initial filename
        current_target = self.getTarget()

        # If there is no target yet, provide a sensible default
        if not current_target:
            current_target = "export"

        # Make the filter readable, e.g.:
        # "JSON Files (*.json);;All Files (*)"
        if extension == "*.json":
            filter_text = "JSON Files (*.json);;All Files (*)"
        elif extension == "*.csv":
            filter_text = "CSV Files (*.csv);;All Files (*)"
        elif extension == "*.txt":
            filter_text = "Text Files (*.txt);;All Files (*)"
        else:
            filter_text = f"Files ({extension});;All Files (*)"

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Export",
            current_target,
            filter_text,
        )

        if not filename:
            return

        # Add the extension when the user did not provide one.
        if extension != "*.*":
            suffix = extension.removeprefix("*")

            if not filename.lower().endswith(suffix.lower()):
                filename += suffix

        self.setTarget(filename)

    def getTarget(self):
        """Return the current export target path."""
        return self.targetEdit.text()


    def setTarget(self, target):
        """Set the export target path."""
        self.targetEdit.setText(target)


    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def requestExport(self):
        """Emit the current export configuration."""
        info = self.getConfiguration()
        self.exportRequested.emit(info)
    
    def getConfiguration(self):
        """Return the current widget configuration."""
        return {
            "selection": self.getSelection(),
            "format": self.getFormat(),
            "fields": self.getSelectedFields(),
            "target": self.getTarget(),
        }

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def getSelections(self):
        """Return the available selection definitions."""
        return list(self.selections)


    def setSelections(self, selections, current=None):
        """
        Replace the available selection definitions.

        Args:
            selections: List of (label, value) tuples.
            current: Optional value to select after updating.
        """

        self.selections = list(selections)

        self.selectionCombo.clear()

        for label, value in self.selections:
            self.selectionCombo.addItem(label, value)

        if current is not None:
            self.setSelection(current)


    def getSelection(self):
        """Return the currently selected selection value."""
        return self.selectionCombo.currentData()


    def setSelection(self, value):
        """
        Set the current selection by value.

        Returns:
            True if the value exists, otherwise False.
        """

        index = self.selectionCombo.findData(value)

        if index >= 0:
            self.selectionCombo.setCurrentIndex(index)
            return True

        return False


    # ------------------------------------------------------------------
    # Format
    # ------------------------------------------------------------------

    def getFormats(self):
        """Return the available format definitions."""
        return list(self.formats)


    def setFormats(self, formats, current=None):
        """
        Replace the available format definitions.

        Args:
            formats: List of (label, value) tuples.
            current: Optional value to select after updating.
        """

        self.formats = list(formats)

        self.formatCombo.clear()

        for label, value in self.formats:
            self.formatCombo.addItem(label, value)

        if current is not None:
            self.setFormat(current)


    def getFormat(self):
        """Return the currently selected format value."""
        return self.formatCombo.currentData()


    def setFormat(self, value):
        """
        Set the current format by value.

        Returns:
            True if the value exists, otherwise False.
        """

        index = self.formatCombo.findData(value)

        if index >= 0:
            self.formatCombo.setCurrentIndex(index)
            return True

        return False


    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    def getFields(self):
        """Return the available field definitions."""
        return list(self.fields)


    def setFields(self, fields, selected_fields=None):
        """
        Replace the available field definitions.

        Args:
            fields: List of (field_id, field_name) tuples.
            selected_fields:
                Field IDs that should be checked.
                If None, all fields are checked.
        """

        self.fields = list(fields)

        # Remove existing field widgets
        while self.fieldsLayout.count():
            item = self.fieldsLayout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.fieldChecks.clear()

        if selected_fields is None:
            selected_fields = {
                field_id
                for field_id, _ in self.fields
            }
        else:
            selected_fields = set(selected_fields)

        for i, (field_id, field_name) in enumerate(self.fields):

            checkbox = QtWidgets.QCheckBox(field_name)
            checkbox.setChecked(field_id in selected_fields)

            self.fieldChecks[field_id] = checkbox

            row = i // 5
            col = i % 5

            self.fieldsLayout.addWidget(
                checkbox,
                row,
                col,
            )


    def getSelectedFields(self):
        """Return the IDs of the currently selected fields."""

        return [
            field_id
            for field_id, checkbox in self.fieldChecks.items()
            if checkbox.isChecked()
        ]


    def setSelectedFields(self, field_ids):
        """Set the selected fields by field ID."""

        field_ids = set(field_ids)

        for field_id, checkbox in self.fieldChecks.items():
            checkbox.setChecked(
                field_id in field_ids
            )
   

# Example — default configuration
# exportWidget = ExportWidget()
# exportWidget.exportRequested.connect(self.doExport)

# Example — custom fields
# fields = [
#     (100, "Name"),
#     (101, "Path"),
#     (102, "Size"),
#     (103, "Checksum"),
# ]

# exportWidget = ExportWidget(
#     fields=fields,
# )

# Example — custom selections and formats

# selections = [
#     ("Everything", "all"),
#     ("Current Selection", "selected"),
#     ("Visible", "visible"),
# ]

# formats = [
#     ("JSON", "json"),
#     ("CSV", "csv"),
#     ("Plain Text", "text"),
# ]

# exportWidget = ExportWidget(
#     selections=selections,
#     formats=formats,
#     default_selection="selected",
#     default_format="csv",
# )

# Example — custom initial field selection

# exportWidget = ExportWidget(
#     default_selection="file_tree",
#     default_format="list_csv",
#     default_fields=[0, 3, 4, 6],
# )

# The resulting signal would be:

# {
#     "selection": "file_tree",
#     "format": "list_csv",
#     "fields": [0, 3, 4, 6],
#     "target": "/tmp/export.csv",
# }

# I also deliberately keep the display label separate from the internal value:
# ("List → CSV", "list_csv")
# so you can freely change the UI text later without breaking the export code.