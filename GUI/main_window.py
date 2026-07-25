import sys

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
from widgets.navigation_tree import NavigationTree
from widgets.status_widget import StatusWidget
from widgets.logger_dock import LoggerDock


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Mapping Tool")
        self.resize(1800, 1000)

        self.setDockOptions(
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.AnimatedDocks
        )

        self.create_pages()
        self.create_central()
        self.create_navigation()
        self.create_logger()
        self.create_statusbar()
        self.create_menubar()

        self.nav.pageSelected.connect(self.change_page)
        self.pages["Home"].openPage.connect(self.change_page)

        self.change_page("Home")

    # --------------------------------------------------
    # Pages
    # --------------------------------------------------

    def create_pages(self):

        self.pages = {

            "Home": HomePage(),

            "Databases": DatabasePage(),

            "Mapping": MappingPage(),

            "Map Explorer": MapExplorerPage(),

            "Sort": SortPage(),

            "Devices": DevicesPage(),

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

        self.nav = NavigationTree()

        self.navDock = QDockWidget("Navigation")

        self.navDock.setObjectName("Navigation")

        self.navDock.setWidget(self.nav)

        self.navDock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
        )

        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            self.navDock,
        )

        self.navDock.setMinimumWidth(220)
        self.navDock.setMaximumWidth(320)

    # --------------------------------------------------
    # Logger Dock
    # --------------------------------------------------

    def create_logger(self):

        self.loggerDock = LoggerDock()

        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea,
            self.loggerDock,
        )

        self.loggerDock.hide()

    # --------------------------------------------------
    # Status Bar
    # --------------------------------------------------

    def create_statusbar(self):

        self.statusWidget = StatusWidget()

        status = QStatusBar()

        status.addPermanentWidget(
            self.statusWidget,
            1,
        )

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

        actAbout.triggered.connect(
            lambda: self.change_page("About")
        )

        actHome.triggered.connect(
            lambda: self.change_page("Home")
        )

        menuFile.addAction(actHome)

        menuFile.addSeparator()

        menuFile.addAction(actExit)

        menuView.addAction(
            self.navDock.toggleViewAction()
        )

        menuView.addAction(
            self.loggerDock.toggleViewAction()
        )

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


    # --------------------------------------------------
    # Window State
    # --------------------------------------------------

    def closeEvent(self, event):

        event.accept()


# --------------------------------------------------
# Run
# --------------------------------------------------

def main():

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()