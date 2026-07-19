import os,sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
import yaml

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QHBoxLayout, QVBoxLayout, QLabel, QStatusBar,
    QMenuBar, QMenu, QTreeView, QSplitter, QTextEdit,
    QProgressBar, QDockWidget, QLineEdit, QSizePolicy
)
from PyQt6.QtGui import QAction,QFileSystemModel
from PyQt6.QtCore import Qt

#Configure logger before importing classes (so they become child loggers)
import class_LogHandler
log_file = None # do stream handler
LM = class_LogHandler.init_logger_manager(log_file)
log = LM.get_logger(__name__)
log.info("Application starting...")

from controllers.class_sort_controller import SortController
from models.class_virtual_model import VirtualModel

# Docks UI
from class_database_manager_dock import DatabaseManagerDock
from class_sort_dock import SortPage
from class_sort_dock import SortPage
from controllers.class_sort_controller import SortController
from class_navigation_tree import *

from class_file_manipulate import *
FM = FileManipulate()
ap= FM.get_app_path()
config_path=os.path.join(ap,"config")

general_config_file=os.path.join(config_path,"filemap_configuration.yml")

from controllers.class_configuration_manager import *
from controllers.class_database_manager import *
conf_manager=ConfigurationManager(general_config_file)
    
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

        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks |
            QMainWindow.DockOption.AllowTabbedDocks
        )
        # Central layout
        # self.central = QLabel("Select an item from Navigation")
        # self.central.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.setCentralWidget(self.central)
        self.central = QWidget()
        self.central.setMinimumSize(0, 0)
        self.central.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored
        )

        self.setCentralWidget(self.central)

        # -----------------------------
        # Left Navigation Tree
        # -----------------------------
        # Navigation Dock
        self.nav_dock = QDockWidget("Navigation", self)
        
        self.nav_obj=QtWidgets.QTreeView(self)
        self.nav_struct=NAV_STRUCT_EXAMPLE
        self.nav = NavigationMenu(self.nav_obj,self.nav_struct,self)
        # self.nav = QTreeWidget()
        # self.nav.setHeaderHidden(True)
        # self.build_navigation_tree()
        # self.nav.itemClicked.connect(self.on_nav_clicked)
        self.nav_dock.setWidget(self.nav_obj)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.nav_dock)
        self.nav_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.nav_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
    
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

        menu_view = QMenu("View", self)
        menubar.addMenu(menu_view)

        # action_nav = QAction("Navigation", self)
        # action_nav.setCheckable(True)
        # action_nav.setChecked(True)
        menu_view.addAction(self.nav_dock.toggleViewAction())
 
        # menu_view.addAction(action_nav)
        # action_nav.triggered.connect(self.nav_dock.setVisible)
        
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
        self.create_docks()

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

    def create_docks(self):
        # Database
        dbm = DatabaseManager(conf_manager)
        self.db_dock = QDockWidget("Database Manager",self)
        self.db_dock.setWidget(DatabaseManagerDock(database_manager=dbm))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.db_dock)
        self.db_dock.hide()

        # Sort
        self.sort_dock = QDockWidget("Sort Tool",self)
        self.sort_page = SortPage()
        self.sort_dock.setWidget(self.sort_page)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.sort_dock)
        self.sort_dock.hide()

    # -----------------------------
    # Navigation Tree
    # -----------------------------
    def build_navigation_tree(self):
        root = QTreeWidgetItem(["File Map"])

        about = QTreeWidgetItem(["About"])
        devices = QTreeWidgetItem(["Devices"])
        databases = QTreeWidgetItem(["Databases"])
        mapping = QTreeWidgetItem(["Mapping"])
        backup = QTreeWidgetItem(["Backup"])
        sort = QTreeWidgetItem(["Sort"])
        # sort.addChildren([
        #     QTreeWidgetItem(["Select active Files/Directories"]),
        # ])
        settings = QTreeWidgetItem(["Settings"])
        ##########################
        # ├── About
        # ├── Devices
        # ├── Databases
        # ├── Mapping
        # ├── Selection
        # ├── Backup
        # └── Settings
        root.addChildren([
            about,
            devices,
            databases,
            mapping,
            backup,
            sort,
            settings,
        ])

        self.nav.addTopLevelItem(root)
        self.nav.expandAll()

    # -----------------------------
    # Navigation Click Handler
    # -----------------------------
    def on_nav_clicked(self, item, column):
        name = item.text(0)
        if name == "Databases":
            self.show_database_dock()
        elif name == "Sort":
            self.show_sort_dock()
        elif name == "Devices":
            self.show_devices_dock()
        elif name == "Mapping":
            self.show_mapping_dock()
        elif name == "About":
            self.show_about()

    def show_devices_dock(self):
        pass
    
    def show_mapping_dock(self):
        pass

    def show_about(self):
        pass

    def show_database_dock(self):
        # self.hide_all_docks()
        self.db_dock.show()
        self.db_dock.raise_()
    
    def show_sort_dock(self):
        # self.hide_all_docks()
        self.sort_dock.show()
        self.sort_dock.raise_()
    
    def hide_all_docks(self):
        for dock in self.findChildren(QDockWidget):
            dock.hide()


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
