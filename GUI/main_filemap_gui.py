import os,sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
import yaml

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QHBoxLayout, QVBoxLayout, QLabel, QStatusBar,
    QMenuBar, QMenu, QTreeView, QSplitter, QTextEdit,
    QProgressBar, QDockWidget, QLineEdit
)
from PyQt6.QtGui import QAction,QFileSystemModel
from PyQt6.QtCore import Qt

from controllers.class_sort_controller import SortController
from models.class_virtual_model import VirtualModel

# Docks UI
from class_database_manager_dock import DatabaseManagerDock
from class_sort_dock import SortPage
from class_sort_dock import SortPage
from controllers.class_sort_controller import SortController

from class_file_manipulate import *
FM = FileManipulate()
ap= FM.get_app_path()
print(ap)
config_path=os.path.join(ap,"config")
from pathlib import Path

def load_config(path: str):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

general_config_file=os.path.join(config_path,"filemap_configuration.yml")
general_config = load_config(general_config_file)
log_path = general_config["paths"]["log_dir"]

log_file="__session__.log"

    
# -----------------------------
# Generic Placeholder Page
# -----------------------------
class PlaceholderPage(QWidget):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(f"<h2>{title}</h2>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

# -----------------------------
# Main Window
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Mapping Tool")
        self.resize(1800, 1000)

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # -----------------------------
        # Left Navigation Tree
        # -----------------------------
        self.nav = QTreeWidget()
        self.nav.setHeaderHidden(True)
        self.build_navigation_tree()
        self.nav.itemClicked.connect(self.on_nav_clicked)

        # -----------------------------
        # Right Workspace (Stacked Pages)
        # -----------------------------
        self.pages = QStackedWidget()

        # Create pages
        self.page_about = PlaceholderPage("About")
        self.page_devices = PlaceholderPage("Show Devices")
        self.page_rescan = PlaceholderPage("Rescan Devices")

        self.page_db = PlaceholderPage("Handle Databases")
        self.page_mapping = PlaceholderPage("Mapping")
        self.page_backup = PlaceholderPage("Backup")
        self.page_selection = PlaceholderPage("Selection")

        self.page_sort = SortPage()

        # Map names to pages
        self.pages_map = {
            "About": self.page_about,
            "Show Devices": self.page_devices,
            "Rescan Devices": self.page_rescan,
            "Handle Databases": self.page_db,
            "Mapping": self.page_mapping,
            "Backup": self.page_backup,
            "Selection": self.page_selection,
            "Sort": self.page_sort,
        }

        for page in self.pages_map.values():
            self.pages.addWidget(page)

        # Add navigation + pages
        main_layout.addWidget(self.nav, 1)
        main_layout.addWidget(self.pages, 4)

        # -----------------------------
        # Menu Bar
        # -----------------------------
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        menu_file = QMenu("File", self)
        menubar.addMenu(menu_file)

        action_about = QAction("About", self)
        action_exit = QAction("Exit", self)

        menu_file.addAction(action_about)
        menu_file.addSeparator()
        menu_file.addAction(action_exit)

        action_about.triggered.connect(lambda: self.show_page("About"))
        action_exit.triggered.connect(self.close)

        # -----------------------------
        # Status Box (DB, Map, Progress, Logger)
        # -----------------------------
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)

        self.db_label = QLineEdit("Active DB: None")
        self.db_label.setReadOnly(True)

        self.map_label = QLineEdit("Active Map: None")
        self.map_label.setReadOnly(True)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.logger = QTextEdit()
        self.logger.setReadOnly(True)
        self.logger.setMaximumHeight(80)

        status_layout.addWidget(self.db_label)
        status_layout.addWidget(self.map_label)
        status_layout.addWidget(self.progress)
        status_layout.addWidget(self.logger)

        status_bar = QStatusBar()
        status_bar.addPermanentWidget(status_widget, 1)
        self.setStatusBar(status_bar)

        # -----------------------------
        # Dockables 
        # -----------------------------
        # Sort Page
        self.sort_page = SortPage()
        self.sort_dock = QDockWidget("Sort Tool", self)
        self.sort_dock.setWidget(self.sort_page)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sort_dock)
        self.sort_dock.hide()

        # Handle database Page
        self.db_dock = QDockWidget("Database Manager", self)
        self.db_dock.setWidget(DatabaseManagerDock(config=general_config))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.db_dock)
        self.db_dock.hide()

        # Models
        self.source_model = QFileSystemModel()
        self.source_model.setRootPath("/")

        self.target_model = VirtualModel()

        # Controller
        self.sort_controller = SortController(
            self.sort_page,
            self.db_label,      # QLineEdit for active DB
            self.map_label,     # QLineEdit for active Map
            self.logger         # QTextEdit logger
        )

    # -----------------------------
    # Navigation Tree
    # -----------------------------
    def build_navigation_tree(self):
        root = QTreeWidgetItem(["File Map"])

        about = QTreeWidgetItem(["About"])
        show_devices = QTreeWidgetItem(["Show Devices"])
        rescan_devices = QTreeWidgetItem(["Rescan Devices"])

        db = QTreeWidgetItem(["Handle Databases"])
        db.addChildren([
            QTreeWidgetItem(["Create New Database File"]),
            QTreeWidgetItem(["Append Database File"]),
            QTreeWidgetItem(["Remove Database File"]),
            QTreeWidgetItem(["Activate Database File"]),
            QTreeWidgetItem(["Deactivate Database File"]),
        ])

        mapping = QTreeWidgetItem(["Mapping"])
        mapping.addChildren([
            QTreeWidgetItem(["Create New Map"]),
            QTreeWidgetItem(["Delete Map"]),
            QTreeWidgetItem(["Clone Map"]),
            QTreeWidgetItem(["Rename Map"]),
            QTreeWidgetItem(["Update Map"]),
            QTreeWidgetItem(["Shallow Compare Maps"]),
            QTreeWidgetItem(["Deep Compare Maps"]),
            QTreeWidgetItem(["Deepen Shallow Map"]),
            QTreeWidgetItem(["Continue Mapping"]),
            QTreeWidgetItem(["Process Map"]),
        ])

        backup = QTreeWidgetItem(["Backup"])
        backup.addChildren([
            QTreeWidgetItem(["Backup of Map base"]),
            QTreeWidgetItem(["Backup of Selection Map"]),
            QTreeWidgetItem(["Backup compare"]),
        ])

        selection = QTreeWidgetItem(["Selection"])
        selection.addChildren([
            QTreeWidgetItem(["Browse Tree"]),
            QTreeWidgetItem(["Browse Directories"]),
            QTreeWidgetItem(["Search Map"]),
            QTreeWidgetItem(["Edit Selection from Origin"]),
            QTreeWidgetItem(["Selection Map Action"]),
        ])

        sort = QTreeWidgetItem(["Sort"])
        sort.addChildren([
            QTreeWidgetItem(["Select active Files/Directories"]),
            QTreeWidgetItem(["Select Mapped Files/Directories"]),
            QTreeWidgetItem(["Deselect Files/Directories"]),
            QTreeWidgetItem(["Selection to Map"]),
            QTreeWidgetItem(["Save Selection to File"]),
            QTreeWidgetItem(["Load Selection from File"]),
            QTreeWidgetItem(["Process Selection"]),
        ])

        root.addChildren([
            about,
            show_devices,
            rescan_devices,
            db,
            mapping,
            backup,
            selection,
            sort,
        ])

        self.nav.addTopLevelItem(root)
        self.nav.expandAll()

    # -----------------------------
    # Navigation Click Handler
    # -----------------------------
    def on_nav_clicked(self, item, column):
        name = item.text(0)
        self.show_page(name)

    def show_page(self, name):
        # Show stacked page
        if name in self.pages_map:
            self.pages.setCurrentWidget(self.pages_map[name])

        # Show dock only for Sort
        if name == "Sort":
            self.sort_dock.show()
        else:
            self.sort_dock.hide()
        # Show dock only for Handle databases
        if name == "Handle Databases":
            self.db_dock.show()
        else:
            self.db_dock.hide()



# -----------------------------
# Run App
# -----------------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
