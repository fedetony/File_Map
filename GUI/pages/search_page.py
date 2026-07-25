# search_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem,
    QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal


class SearchPage(QWidget):
    """
    Search interface.

    The page does not know about databases or CMA.
    It only collects requests and displays results.
    """

    search_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.results = []

        self.build_ui()


    def build_ui(self):

        main = QVBoxLayout(self)


        # -------------------------
        # Search box
        # -------------------------

        search_box = QGroupBox("Search")
        search_layout = QHBoxLayout(search_box)

        self.search_text = QLineEdit()
        self.search_text.setPlaceholderText(
            "Search filename, folder, metadata..."
        )

        self.search_button = QPushButton("🔍 Search")

        self.search_button.clicked.connect(
            self.emit_search
        )

        self.search_text.returnPressed.connect(
            self.emit_search
        )


        search_layout.addWidget(self.search_text)
        search_layout.addWidget(self.search_button)


        main.addWidget(search_box)



        # -------------------------
        # Filters
        # -------------------------

        filter_box = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_box)


        self.search_type = QComboBox()
        self.search_type.addItems([
            "Filename",
            "Path",
            "Everything",
            "SQL"
        ])


        self.include_deleted = QCheckBox(
            "Include deleted files"
        )

        self.case_sensitive = QCheckBox(
            "Case sensitive"
        )


        filter_layout.addWidget(
            QLabel("Search:")
        )

        filter_layout.addWidget(
            self.search_type
        )

        filter_layout.addWidget(
            self.include_deleted
        )

        filter_layout.addWidget(
            self.case_sensitive
        )


        main.addWidget(filter_box)



        # -------------------------
        # Database selection
        # -------------------------

        db_box = QGroupBox(
            "Databases / Maps"
        )

        db_layout = QHBoxLayout(db_box)


        self.database_selector = QComboBox()
        self.database_selector.addItem(
            "All databases"
        )

        self.map_selector = QComboBox()
        self.map_selector.addItem(
            "All maps"
        )


        db_layout.addWidget(
            QLabel("Database:")
        )

        db_layout.addWidget(
            self.database_selector
        )

        db_layout.addWidget(
            QLabel("Map:")
        )

        db_layout.addWidget(
            self.map_selector
        )


        main.addWidget(db_box)



        # -------------------------
        # Results
        # -------------------------

        splitter = QSplitter(
            Qt.Orientation.Vertical
        )


        self.table = QTableWidget()
        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels([
            "Name",
            "Path",
            "Size",
            "Modified",
            "Hash",
            "Map"
        ])

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.doubleClicked.connect(
            self.result_double_clicked
        )


        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(120)


        splitter.addWidget(
            self.table
        )

        splitter.addWidget(
            self.info
        )


        main.addWidget(
            splitter
        )


    # -------------------------------------------------
    # Communication with controller
    # -------------------------------------------------

    def emit_search(self):

        request = {
            "text":
                self.search_text.text(),

            "type":
                self.search_type.currentText(),

            "database":
                self.database_selector.currentText(),

            "map":
                self.map_selector.currentText(),

            "include_deleted":
                self.include_deleted.isChecked(),

            "case_sensitive":
                self.case_sensitive.isChecked()
        }

        self.search_requested.emit(
            request
        )


    # -------------------------------------------------
    # Results from backend
    # -------------------------------------------------

    def set_results(self, results:list):

        """
        Expected:

        [
          {
            name:"",
            path:"",
            size:"",
            modified:"",
            hash:"",
            map:""
          }
        ]
        """

        self.results = results

        self.table.setRowCount(
            len(results)
        )


        for row,data in enumerate(results):

            values = [
                data.get("name",""),
                data.get("path",""),
                data.get("size",""),
                data.get("modified",""),
                data.get("hash",""),
                data.get("map","")
            ]

            for col,value in enumerate(values):

                self.table.setItem(
                    row,
                    col,
                    QTableWidgetItem(
                        str(value)
                    )
                )


    def result_double_clicked(self,index):

        row=index.row()

        if row < len(self.results):

            result=self.results[row]

            self.info.setText(
                str(result)
            )


    # -------------------------------------------------
    # External population
    # -------------------------------------------------

    def set_databases(self, databases):

        self.database_selector.clear()

        self.database_selector.addItem(
            "All databases"
        )

        for db in databases:
            self.database_selector.addItem(
                db
            )


    def set_maps(self, maps):

        self.map_selector.clear()

        self.map_selector.addItem(
            "All maps"
        )

        for m in maps:
            self.map_selector.addItem(
                m
            )