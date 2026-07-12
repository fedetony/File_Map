from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt
from class_file_manipulate import FileManipulate
FM=FileManipulate()

class DatabaseManagerDock(QWidget):
    def __init__(self, config):
        super().__init__()

        self.config = config  # contains your DB folders
        self.db_files = []    # list of database file paths

        layout = QVBoxLayout(self)

        # -----------------------------
        # Table of database files
        # -----------------------------
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Database File", "Active"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        layout.addWidget(self.table)

        # -----------------------------
        # Buttons
        # -----------------------------
        btn_layout = QHBoxLayout()

        self.btn_create = QPushButton("Create New")
        self.btn_append = QPushButton("Append")
        self.btn_remove = QPushButton("Remove Selected")

        self.btn_create.clicked.connect(self.create_db)
        self.btn_append.clicked.connect(self.append_db)
        self.btn_remove.clicked.connect(self.remove_selected)

        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_append)
        btn_layout.addWidget(self.btn_remove)

        layout.addLayout(btn_layout)

        # Load initial DB list
        self.load_databases()

    # -----------------------------
    # Load DB files from config folders
    # -----------------------------
    def load_databases(self):
        self.table.setRowCount(0)
        self.db_files.clear()

        for folder in self.config["db_folders"]:
            # TODO: scan folder for *.db files
            pass

        # Example placeholder:
        example_files = [
            ("/path/to/db1.db", False),
            ("/path/to/db2.db", True),
        ]

        for path, active in example_files:
            self.add_db_row(path, active)

    def add_db_row(self, path, active):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(path))
        self.table.setItem(row, 1, QTableWidgetItem("Yes" if active else "No"))

    # -----------------------------
    # Context menu (activate/deactivate)
    # -----------------------------
    def open_context_menu(self, pos):
        menu = QMenu(self)

        activate = menu.addAction("Activate")
        deactivate = menu.addAction("Deactivate")

        action = menu.exec(self.table.mapToGlobal(pos))

        if action == activate:
            self.set_active(True)
        elif action == deactivate:
            self.set_active(False)

    def set_active(self, state):
        for item in self.table.selectedItems():
            row = item.row()
            self.table.setItem(row, 1, QTableWidgetItem("Yes" if state else "No"))

        # TODO: update backend active DB

    # -----------------------------
    # Create new DB
    # -----------------------------
    def create_db(self):
        path, _ = QFileDialog.getSaveFileName(self, "Create Database", "", "Database (*.db)")
        if not path:
            return

        # TODO: create empty DB file
        self.add_db_row(path, False)

    # -----------------------------
    # Append DB
    # -----------------------------
    def append_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Append Database", "", "Database (*.db)")
        if not path:
            return

        # TODO: append DB logic
        self.add_db_row(path, False)

    # -----------------------------
    # Remove selected DBs
    # -----------------------------
    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedItems()}, reverse=True)
        for row in rows:
            # TODO: remove from backend
            self.table.removeRow(row)
