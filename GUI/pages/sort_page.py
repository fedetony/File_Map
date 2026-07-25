# sort_page.py

from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QGroupBox,
)


class SortPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)


        title = QLabel(
            "Sort / Assemble Maps"
        )
        
        title.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        title.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            """
        )

        layout.addWidget(title)


        # Toolbar

        toolbar = QHBoxLayout()


        self.load_source = QPushButton(
            "Load Source"
        )

        self.load_target = QPushButton(
            "Load Destination"
        )

        self.execute_button = QPushButton(
            "Apply Changes"
        )


        toolbar.addWidget(
            self.load_source
        )

        toolbar.addWidget(
            self.load_target
        )

        toolbar.addWidget(
            self.execute_button
        )

        toolbar.addStretch()


        layout.addLayout(
            toolbar
        )


        # Main split

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )


        self.source_panel = self.create_panel(
            "Source Map"
        )

        self.target_panel = self.create_panel(
            "Destination Map"
        )


        splitter.addWidget(
            self.source_panel
        )

        splitter.addWidget(
            self.target_panel
        )


        splitter.setStretchFactor(
            0,
            1
        )

        splitter.setStretchFactor(
            1,
            1
        )


        layout.addWidget(
            splitter
        )


    # --------------------------------------------------
    # Explorer panel
    # --------------------------------------------------

    def create_panel(self, title):

        group = QGroupBox(
            title
        )

        layout = QVBoxLayout(
            group
        )


        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )


        tree = QTreeWidget()

        tree.setHeaderHidden(
            True
        )


        root = QTreeWidgetItem(
            [
                "Root"
            ]
        )

        root.addChild(
            QTreeWidgetItem(
                ["Folder A"]
            )
        )

        root.addChild(
            QTreeWidgetItem(
                ["Folder B"]
            )
        )

        tree.addTopLevelItem(
            root
        )

        root.setExpanded(
            True
        )


        table = QTableWidget()

        table.setColumnCount(
            3
        )

        table.setHorizontalHeaderLabels(
            [
                "Name",
                "Size",
                "Status"
            ]
        )


        demo = [
            (
                "file1.txt",
                "10 KB",
                "Ready"
            ),
            (
                "file2.jpg",
                "2 MB",
                "Ready"
            ),
        ]


        table.setRowCount(
            len(demo)
        )


        for row, data in enumerate(demo):

            for col, value in enumerate(data):

                table.setItem(
                    row,
                    col,
                    QTableWidgetItem(value)
                )


        splitter.addWidget(
            tree
        )

        splitter.addWidget(
            table
        )


        splitter.setStretchFactor(
            0,
            1
        )

        splitter.setStretchFactor(
            1,
            2
        )


        layout.addWidget(
            splitter
        )


        return group


    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def activate(self):

        pass


    def deactivate(self):

        pass