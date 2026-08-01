# navigation_tree.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem


class NavigationTree(QTreeWidget):

    pageSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)

        self.build_tree()

        self.itemClicked.connect(
            self.item_clicked
        )

    # --------------------------------------------------
    # Build navigation
    # --------------------------------------------------

    def build_tree(self):

        root = QTreeWidgetItem(
            ["File Map"]
        )

        root.setExpanded(True)

        pages = [
            "Home",
            "Devices",
            "Databases",
            "Mapping",
            "Map Explorer",
            "Sort",
            "Settings",
            "About",
        ]

        for name in pages:
            item = QTreeWidgetItem(
                [name]
            )
            root.addChild(item)

        self.addTopLevelItem(root)


    # --------------------------------------------------
    # Click handler
    # --------------------------------------------------

    def item_clicked(self, item, column):
        name = item.text(0)
        if name == "File Map":
            return
        self.pageSelected.emit(name)