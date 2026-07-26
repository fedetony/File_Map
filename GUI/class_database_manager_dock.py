from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog,
    QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt
from controllers.class_database_manager import *

class DatabaseManagerDock(QWidget):
    """
    Database manager widget.

    This widget never manipulates YAML directly.
    All work is delegated to the backend (database_manager).
    """

    def __init__(self, database_manager:DatabaseManager):
        super().__init__()

        self.dbm = database_manager

        layout = QVBoxLayout(self)

        # ---------------------------------
        # Database table
        # ---------------------------------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Name",
            "Database",
            "Password",
            "Key",
            "Active"
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        self.table.customContextMenuRequested.connect(
            self.open_context_menu
        )

        layout.addWidget(self.table)

        # ---------------------------------
        # Buttons
        # ---------------------------------
        buttons = QHBoxLayout()

        self.btn_create = QPushButton("Create")
        self.btn_append = QPushButton("Append")
        self.btn_remove = QPushButton("Remove")

        buttons.addWidget(self.btn_create)
        buttons.addWidget(self.btn_append)
        buttons.addWidget(self.btn_remove)

        layout.addLayout(buttons)

        self.btn_create.clicked.connect(self.create_database)
        self.btn_append.clicked.connect(self.append_database)
        self.btn_remove.clicked.connect(self.remove_selected)

        self.refresh_table()

    # ==========================================================
    # TABLE
    # ==========================================================

    def refresh_table(self):
        self.table.setRowCount(0)

        for db in self.dbm.databases:
            self.add_database(db)

        self.table.resizeColumnsToContents()

    def add_database(self, db):

        row = self.table.rowCount()
        self.table.insertRow(row)

        # Store database object on first column
        item = QTableWidgetItem(db.name)
        item.setData(Qt.ItemDataRole.UserRole, db)

        self.table.setItem(row, 0, item)
        self.table.setItem(row, 1, QTableWidgetItem(db.db_file))
        self.table.setItem(
            row, 2,
            QTableWidgetItem("Yes" if db.requires_password else "No")
        )
        self.table.setItem(
            row, 3,
            QTableWidgetItem("Yes" if db.key_file else "No")
        )
        self.table.setItem(
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
            for index in self.table.selectionModel().selectedRows()
        }

        for row in rows:
            item = self.table.item(row, 0)
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

        action = menu.exec(self.table.viewport().mapToGlobal(pos))

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