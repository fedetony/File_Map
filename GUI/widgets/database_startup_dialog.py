# database_startup_dialog.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QLabel,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QGroupBox,
)


class DatabaseStartupDialog(QDialog):

    def __init__(self, databases, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Open File Map Databases"
        )

        self.databases = databases

        self.file_list = []
        self.password_list = []
        self.key_list = []

        self.database_widgets = []

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)


        layout.addWidget(
            QLabel(
                "Select databases to activate:"
            )
        )


        self.database_list = QListWidget()

        layout.addWidget(
            self.database_list
        )


        for db in self.databases:

            item = QListWidgetItem()

            item.setCheckState(
                Qt.CheckState.Checked
            )

            widget = QWidget()

            row = QVBoxLayout(widget)


            # Database name

            name = QLabel(
                str(db)
            )


            # Password flag

            password_check = QCheckBox(
                "Password protected"
            )


            # Key file

            key_row = QHBoxLayout()


            key_edit = QLineEdit()

            key_edit.setPlaceholderText(
                "Optional key file"
            )


            browse = QPushButton(
                "Browse"
            )


            browse.clicked.connect(
                lambda checked=False,
                edit=key_edit:
                self.select_key(edit)
            )


            key_row.addWidget(
                key_edit
            )

            key_row.addWidget(
                browse
            )


            row.addWidget(
                name
            )

            row.addWidget(
                password_check
            )

            row.addLayout(
                key_row
            )


            item.setSizeHint(
                widget.sizeHint()
            )


            self.database_list.addItem(
                item
            )

            self.database_list.setItemWidget(
                item,
                widget
            )


            self.database_widgets.append(
                {
                    "item": item,
                    "database": str(db),
                    "password": password_check,
                    "key": key_edit
                }
            )


        # Buttons

        buttons = QHBoxLayout()

        buttons.addStretch()


        open_btn = QPushButton(
            "Open"
        )

        cancel_btn = QPushButton(
            "Cancel"
        )


        open_btn.clicked.connect(
            self.accept
        )

        cancel_btn.clicked.connect(
            self.reject
        )


        buttons.addWidget(
            open_btn
        )

        buttons.addWidget(
            cancel_btn
        )


        layout.addLayout(
            buttons
        )


    # --------------------------------------------------
    # Key selection
    # --------------------------------------------------

    def select_key(
        self,
        target_edit
    ):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SHA256 Key File",
            filter="Text files (*.txt);;All files (*)"
        )

        if filename:

            target_edit.setText(
                filename
            )


    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    def get_databases(self):

        self.file_list.clear()
        self.password_list.clear()
        self.key_list.clear()


        for entry in self.database_widgets:

            item = entry["item"]

            if item.checkState() == Qt.CheckState.Checked:

                self.file_list.append(
                    entry["database"]
                )


                self.password_list.append(
                    entry["password"].isChecked()
                )


                key = entry["key"].text().strip()


                self.key_list.append(
                    key if key else None
                )


        return (
            self.file_list,
            self.password_list,
            self.key_list
        )