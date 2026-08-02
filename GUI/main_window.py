import sys

from PyQt6 import QtGui ,QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QDockWidget,
    QStackedWidget,
    QStatusBar,
    QMenu,
    QMenuBar,
    QLabel,
    QVBoxLayout,
    QTreeView,
)
# gui/
#     main_window.py
#     pages/
#         home_page.py
#         database_page.py
#         mapping_page.py
#         map_explorer_page.py
#         sort_page.py
#         devices_page.py
#         settings_page.py
#         about_page.py

#     widgets/
#         navigation_tree.py
#         status_widget.py
#         logger_dock.py

# -------- Pages --------

from pages.home_page import HomePage
from pages.database_page import DatabasePage
from pages.mapping_page import MappingPage
from pages.map_explorer_page import MapExplorerPage
from pages.sort_page import SortPage
from pages.devices_page import DevicesPage
from pages.settings_page import SettingsPage
from pages.about_page import AboutPage

# -------- Widgets --------
#from widgets.navigation_tree import NavigationTree
from GUI.widgets.class_navigation_menu import NavigationMenu
from widgets.status_widget import StatusWidget
from widgets.logger_dock import LoggerDock

from controllers.class_configuration_manager import ConfigurationManager
from controllers.class_database_manager import DatabaseManager
from controllers.class_filemap_cli_manager import FileMapCliManager
# icons
from functional.class_icons import Icons
# looger
from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("MainWindow","debug",True,None)
log.info("Main Window Logger started")

class MainWindow(QMainWindow):

    def __init__(
    self,
    conf_manager:ConfigurationManager,
    dbm:DatabaseManager,
    ):
        super().__init__()
        # Get Filemap's inputs
        self.conf_manager = conf_manager
        self.dbm = dbm
        # Object to Filemap Cli 
        self.fmap = FileMapCliManager(conf_manager=self.conf_manager,
                                      dbm=self.dbm)

        self.icons = Icons() 

        self.setWindowTitle("File Mapping Tool")
        self.setWindowIcon(self.icons.icon("main"))

        self.resize(1800, 1000)

        self.setDockOptions(
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.AnimatedDocks
        )

        self.create_logger()
        self.create_pages()
        self.create_central()
        self.create_navigation()
        self.create_statusbar()
        self.create_menubar()

        self.nav_menu.pageSelected.connect(self.change_page)
        self.pages["Home"].openPage.connect(self.change_page)

        self.change_page("Home")

    # --------------------------------------------------
    # Pages
    # --------------------------------------------------

    def create_pages(self):

        self.pages = {
            "Home": HomePage(),
            "Devices": DevicesPage(self.fmap),
            "Databases": DatabasePage(self.fmap),
            "Mapping": MappingPage(),
            "Map Explorer": MapExplorerPage(),
            "Sort": SortPage(),
            "Settings": SettingsPage(),
            "About": AboutPage(),
        }

    # --------------------------------------------------
    # Central Widget
    # --------------------------------------------------

    def create_central(self):
        self.stack = QStackedWidget()
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.setCentralWidget(self.stack)

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    def create_navigation(self):
        # self.nav = NavigationTree()
        self.nav_tv_obj = QTreeView()
        self.nav_menu = NavigationMenu(self.nav_tv_obj,None)
        self.navDock = QDockWidget("Navigation")
        self.navDock.setObjectName("Navigation")
        self.navDock.setWidget(self.nav_tv_obj)
        self.navDock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.navDock)

        self.navDock.setMinimumWidth(220)
        self.navDock.setMaximumWidth(320)

    # --------------------------------------------------
    # Logger Dock
    # --------------------------------------------------

    def create_logger(self):
        self.loggerDock = LoggerDock(LM.log_queue)
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea,
            self.loggerDock,
        )
        LM.attach_gui_handler(self.loggerDock, emit_record=True)
        # log.info("GUI Logger attached...")
        # self.loggerDock.hide()

    # --------------------------------------------------
    # Status Bar
    # --------------------------------------------------

    def create_statusbar(self):
        self.statusWidget = StatusWidget()
        status = QStatusBar()
        status.addPermanentWidget(self.statusWidget,1)
        self.setStatusBar(status)

    # --------------------------------------------------
    # Menu
    # --------------------------------------------------

    def create_menubar(self):
        menubar = self.menuBar()
        menuFile = menubar.addMenu("File")
        menuView = menubar.addMenu("View")
        menuHelp = menubar.addMenu("Help")
        actExit = QAction("Exit", self)
        actAbout = QAction("About", self)
        actHome = QAction("Home", self)

        actExit.triggered.connect(self.close)
        actAbout.triggered.connect(lambda: self.change_page("About"))
        actHome.triggered.connect(lambda: self.change_page("Home"))

        menuFile.addAction(actHome)
        menuFile.addSeparator()
        menuFile.addAction(actExit)
        menuView.addAction(self.navDock.toggleViewAction())
        menuView.addAction(self.loggerDock.toggleViewAction())

        menuHelp.addAction(actAbout)

    # --------------------------------------------------
    # Page Switching
    # --------------------------------------------------

    def change_page(self, name):
        page = self.pages.get(name)
        if not page:
            return
        old = self.stack.currentWidget()
        if old and hasattr(old, "deactivate"):
            old.deactivate()
        self.stack.setCurrentWidget(page)
        if hasattr(page, "activate"):
            page.activate()
        self.setWindowTitle(
            f"File Mapping Tool - {name}"
        )


    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def current_page(self):
        return self.stack.currentWidget()


    def log_message(self, text):
        if self.loggerDock:
            self.loggerDock.append(text)
    
    # def write_GUI_Log(self, text):
    #     """Called by ConsolePanelHandler in class_LogHandler"""
    #     self.log_message(text)

    # --------------------------------------------------
    # Window State
    # --------------------------------------------------

    def closeEvent(self, event):

        event.accept()



if __name__ == "__main__":
    pass