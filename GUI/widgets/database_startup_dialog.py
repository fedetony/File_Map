# database_startup_dialog.py
from PyQt6 import QtGui
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
from class_icons import *
from controllers.class_database_manager import DatabaseManager, DatabaseInfo
from controllers.class_configuration_manager import ConfigurationManager

from class_LogHandler import LM
log=LM.get_logger_with_handler("DBStartup","debug",True,None)

class DatabaseStartupDialog(QDialog):

    def __init__(self, conf:ConfigurationManager, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Open File Map Databases"
        )
        self.icons = Icons() 
        self.setWindowIcon(QtGui.QIcon(self.icons.icon("db settings")))
        self.conf = conf
        self.dbm = DatabaseManager(self.conf)
        
        self.databases = self.dbm.databases
        self.file_list, self.password_list, self.key_list, self.activation_list = self.dbm.get_file_pwd_key_lists()

        self.database_widgets = []
        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select databases to activate:"))

        self.database_list = QListWidget()

        layout.addWidget(self.database_list)

        for db in self.databases:
            if isinstance(db,DatabaseInfo):
                pass
            item = QListWidgetItem()
            if db.autoload:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)    
            widget = QWidget()
            row = QVBoxLayout(widget)
            # Database name
            name = QLabel(str(db.db_file))

            # Password flag
            password_check = QCheckBox("Password protected")

            # Key file
            key_row = QHBoxLayout()
            key_edit = QLineEdit()
            key_edit.setPlaceholderText(db.keyfile_filepath)

            browse = QPushButton("Browse")
            browse.setIcon(self.icons.icon("db key"))

            browse.clicked.connect(lambda checked=db.requires_password, edit=key_edit: self.select_key(edit))
            
            key_row.addWidget(key_edit)            
            key_row.addWidget(browse)
            row.addWidget(name)
            row.addWidget(password_check)
            row.addLayout(key_row)
            item.setSizeHint(widget.sizeHint())

            self.database_list.addItem(item)
            self.database_list.setItemWidget( item, widget)

            self.database_widgets.append(
                {
                    "item": item,
                    "database": str(db.db_file),
                    "password": password_check,
                    "key": key_edit
                }
            )

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        open_btn = QPushButton("Open")
        open_btn.setIcon(self.icons.icon("open file"))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setIcon(self.icons.icon("bin"))

        open_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(open_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)


    # --------------------------------------------------
    # Key selection
    # --------------------------------------------------

    def select_key(self,target_edit):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SHA256 Key File",
            filter="Text files (*.txt);;All files (*)"
        )

        if filename:
            target_edit.setText(filename)


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
                self.file_list.append(entry["database"])
                self.password_list.append(entry["password"].isChecked())
                key = entry["key"].text().strip()
                self.key_list.append(key if key else None)
        return (
            self.file_list,
            self.password_list,
            self.key_list
        )