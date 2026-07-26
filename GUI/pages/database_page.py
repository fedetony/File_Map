# database_page.py
from PyQt6.QtCore import Qt
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSplitter,
    QTextEdit,
    QFileDialog,
    QMenu,

)
from class_icons import Icons
from controllers.class_database_manager import *
from controllers.class_filemap_cli_manager import FileMapCliManager

# Old:
# class DatabaseManagerDock(QDockWidget):
# becomes:
# class DatabasePage(QWidget):
# Then:
# setWidget(...) disappears
# show()/hide() disappears
# the controller stays
# The logic can move almost unchanged.

class DatabasePage(QWidget):

    def __init__(self, filemapcli:FileMapCliManager,parent=None ):
        super().__init__(parent)
        self.fmap=filemapcli
        self.dbm = self.fmap.dbm
        self.icons=Icons()
        self.create_ui()
        self.connect_ui()
        # self.load_demo()
        self.refresh_table()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def connect_ui(self):
        self.btn_new.clicked.connect(self.create_database)
        self.btn_append.clicked.connect(self.append_database)
        self.btn_remove.clicked.connect(self.remove_selected)

    def create_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header= QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(self.icons.icon("databases").pixmap(32, 32))
        title = QLabel("Database Manager")
        title.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            """
        )
        title.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        header.addWidget(icon)
        header.addWidget(title)
        layout.addLayout(header)


        # Toolbar
        toolbar = QHBoxLayout()

        self.btn_new = QPushButton("New Database")
        self.btn_new.setIcon(self.icons.icon("db key"))
        self.btn_append = QPushButton("Add")
        self.btn_append.setIcon(self.icons.icon("db add"))
        self.btn_remove = QPushButton("Remove")
        self.btn_remove.setIcon(self.icons.icon("db remove"))

        self.btn_activate = QPushButton("Activate")
        self.btn_activate.setIcon(self.icons.icon("db activate"))
        self.btn_deactivate = QPushButton("Deactivate")
        self.btn_deactivate.setIcon(self.icons.icon("db deactivate"))

        #self.refresh_btn = QPushButton("Refresh")

        toolbar.addWidget(self.btn_new)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_append)
        toolbar.addWidget(self.btn_remove)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_activate)
        toolbar.addWidget(self.btn_deactivate)
        #toolbar.addWidget(self.refresh_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Main area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Database list
        db_group = QGroupBox("Databases")

        db_layout = QVBoxLayout(db_group)
        self.database_table = QTableWidget()

        self.database_table.setColumnCount(4)
        self.database_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Location",
                "Maps",
                "Active"
            ]
        )

        db_layout.addWidget(self.database_table)

        # Details
        details_group = QGroupBox("Database Information")
        details_layout = QVBoxLayout(details_group)

        self.details = QTextEdit()
        self.details.setReadOnly(True)

        self.details.setText("Select a database...")

        details_layout.addWidget(self.details)

        splitter.addWidget(db_group)

        splitter.addWidget(details_group)
        splitter.setStretchFactor(0,2)
        splitter.setStretchFactor(1,1)

        layout.addWidget(splitter)

        # Demo data
        #self.load_demo()

    # --------------------------------------------------
    # Demo / placeholder
    # --------------------------------------------------

    def load_demo(self):
        databases = [
            (
                "Music",
                "D:/MusicMap",
                "12",
                "Yes"
            ),
            (
                "Backup",
                "E:/BackupMap",
                "5",
                "No"
            ),
        ]
        self.database_table.setRowCount(len(databases))
        for row, data in enumerate(databases):
            for col, value in enumerate(data):
                self.database_table.setItem(
                    row,
                    col,
                    QTableWidgetItem(value)
                )
        self.refresh_table()

    # ==========================================================
    # TABLE
    # ==========================================================

    def refresh_table(self):
        self.database_table.setRowCount(0)

        for db in self.dbm.databases:
            self.add_database(db)

        self.database_table.resizeColumnsToContents()

    def add_database(self, db:DatabaseInfo):
        row = self.database_table.rowCount()
        self.database_table.insertRow(row)

        # Store database object on first column
        item = QTableWidgetItem(db.name)
        item.setData(Qt.ItemDataRole.UserRole, db)

        self.database_table.setItem(row, 0, item)
        self.database_table.setItem(row, 1, QTableWidgetItem(db.db_file))
        self.database_table.setItem(
            row, 2,
            QTableWidgetItem("Yes" if db.requires_password else "No")
        )
        self.database_table.setItem(
            row, 3,
            QTableWidgetItem("Yes" if db.key_file else "No")
        )
        self.database_table.setItem(
            row, 4,
            QTableWidgetItem("Yes" if db.active else "No")
        )

    # ==========================================================
    # Helpers
    # ==========================================================

    def selected_databases(self):
        databases = []
        rows = {
            index.row()
            for index in self.database_table.selectionModel().selectedRows()
        }

        for row in rows:
            item = self.database_table.item(row, 0)
            databases.append(
                item.data(Qt.ItemDataRole.UserRole)
            )

        return databases

    # ==========================================================
    # Context menu
    # ==========================================================

    def open_context_menu(self, pos):
        menu = QMenu(self)

        act_activate = menu.addAction("Activate")
        act_deactivate = menu.addAction("Deactivate")
        menu.addSeparator()
        act_remove = menu.addAction("Remove")

        action = menu.exec(self.database_table.viewport().mapToGlobal(pos))

        if action == act_activate:

            for db in self.selected_databases():
                self.dbm.activate(db)

        elif action == act_deactivate:

            for db in self.selected_databases():
                self.dbm.deactivate(db)

        elif action == act_remove:

            self.remove_selected()

        self.refresh_table()

    # ==========================================================
    # Buttons
    # ==========================================================

    def create_database(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Create database",
            "",
            "Database (*.db)"
        )

        if not filename:
            return

        self.dbm.create_database(filename)
        self.refresh_table()

    def append_database(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Append database",
            "",
            "Database (*.db)"
        )
        if not filename:
            return

        self.dbm.append_database(filename)
        self.refresh_table()

    def remove_selected(self):
        for db in self.selected_databases():
            self.dbm.remove_database(db)
        self.refresh_table()