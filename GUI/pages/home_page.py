# home_page.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)
from controllers.class_filemap_cli_manager import FileMapCliManager
from functional.class_icons import Icons
from models.class_style_provider import TEXT_ICONS

class HomePage(QWidget):

    openPage = pyqtSignal(str)

    def __init__(self, fmap:FileMapCliManager, parent=None):
        super().__init__(parent)
        self.fmap=fmap
        self.icons=Icons()
        self.create_ui()
        self.refresh_all_cards()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header= QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(self.icons.icon("main").pixmap(32, 32))
        title = QLabel("Welcome to FileMap: File Mapping Tool")
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
        header.addStretch()
        layout.addLayout(header)

        subtitle = QLabel("Manage databases, maps, devices, file searches... and much more")

        layout.addWidget(title)
        layout.addWidget(subtitle)


        layout.addSpacing(20)


        # -----------------------------
        # Quick actions
        # -----------------------------

        actions = QHBoxLayout()

        self.database_btn = QPushButton("Databases")
        self.database_btn.setIcon(self.icons.icon("databases"))

        self.mapping_btn = QPushButton("Mapping")
        self.mapping_btn.setIcon(self.icons.icon("mapping"))

        self.sort_btn = QPushButton("Sort Files")
        self.sort_btn.setIcon(self.icons.icon("sort"))

        self.devices_btn = QPushButton("Devices")
        self.devices_btn.setIcon(self.icons.icon("devices"))

        actions.addWidget(self.devices_btn)
        actions.addWidget(self.database_btn)
        actions.addWidget(self.mapping_btn)
        actions.addWidget(self.sort_btn)

        layout.addLayout(actions)

        self.database_btn.clicked.connect(lambda: self.openPage.emit("Databases"))
        self.mapping_btn.clicked.connect(lambda: self.openPage.emit("Mapping"))
        self.sort_btn.clicked.connect(lambda: self.openPage.emit("Sort"))
        self.devices_btn.clicked.connect(lambda: self.openPage.emit("Devices"))

        layout.addSpacing(25)
        # -----------------------------
        # Information cards
        # -----------------------------
        info = QHBoxLayout()

        self.db_card = self.create_card("Databases", "No active database")
        self.map_card = self.create_card("Maps", "No map selected")
        self.device_card = self.create_card("Devices", "No devices scanned")

        info.addWidget(self.device_card)
        info.addWidget(self.db_card)
        info.addWidget(self.map_card)

        layout.addLayout(info)
        layout.addStretch()

        footer = QLabel("Ready")
        self.status_label = footer

        layout.addWidget(footer)


    # --------------------------------------------------
    # Cards
    # --------------------------------------------------

    def create_card(self, title, text):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        frame.setMinimumHeight(120)

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QVBoxLayout(frame)

        header = QLabel(title)
        header.setStyleSheet("""
            font-family: Consolas;
            font-weight: bold;
            font-size: 16px;
        """)

        value = QLabel()
        value.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        value.setWordWrap(False)
        value.setTextFormat(QtCore.Qt.TextFormat.RichText)
        value.setStyleSheet("""
            font-family: Consolas;
            font-size: 13px;
        """)
        value.setText(text)

        layout.addWidget(header)
        layout.addWidget(value)

        frame.value_label = value

        return frame

    # --------------------------------------------------
    # Page lifecycle
    # --------------------------------------------------
    def activate(self):
        self.status_label.setText("Ready")


    def deactivate(self):
        pass

    # --------------------------------------------------
    # Cards
    # --------------------------------------------------
    # def refresh_database_card(self):
    #     """Refresh the database summary shown on the Home page."""

    #     db_info_list = self.fmap.get_active_databases_in_dbm()
    #     db_id_list = list(range(len(db_info_list)))

    #     active_db_list, inactive_db_list = (
    #         self.fmap.get_active_unactive_db_id_list(db_id_list)
    #     )

    #     total = len(db_info_list)
    #     active = len(active_db_list)
    #     inactive = len(inactive_db_list)

    #     db_card_txt = (
    #         f"<b style='font-size:22px;'>{total}</b> "
    #         f"<span style='color:#777;'>Loaded Databases</span><br>"
    #         f"<span style='color:#2e8b57;'><b>{active}</b> Active</span>"
    #         f"&nbsp;&nbsp;&nbsp;"
    #         f"<span style='color:#888;'><b>{inactive}</b> Inactive</span>"
    #     )

    #     db_label = self.db_card.value_label

    #     if isinstance(db_label, QLabel):
    #         db_label.setText(db_card_txt)
    def refresh_database_card(self):
        """Refresh the database summary shown on the Home page."""

        db_info_list = self.fmap.get_active_databases_in_dbm()
        db_id_list = list(range(len(db_info_list)))

        active_db_list, inactive_db_list = (
            self.fmap.get_active_unactive_db_id_list(db_id_list)
        )

        total = len(db_info_list)
        active = len(active_db_list)
        inactive = len(inactive_db_list)

        db_card_text = (
            f"<span style='font-size:22px; font-weight:bold;'>"
            f"{TEXT_ICONS['database']} {total}"
            f"</span> "
            f"<span style='color:#777;'>Loaded Databases</span><br>"
            f"&nbsp;&nbsp;└── "
            f"<span style='color:#00cc66; font-weight:bold;'>"
            f"{TEXT_ICONS['online']} {active} Active"
            f"</span><br>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;└── "
            f"<span style='color:#888;'>"
            f"{TEXT_ICONS['offline']} {inactive} Inactive"
            f"</span>"
        )

        db_label = self.db_card.value_label

        if isinstance(db_label, QLabel):
            db_label.setText(db_card_text)



    def refresh_map_card(self):
        """Refresh the map summary shown on the Home page."""

        db_info_list = self.fmap.get_active_databases_in_dbm()

        lines = []

        for iii, db in enumerate(db_info_list):
            database = str(db.database_filepath)
            map_list = self.fmap.get_maps_in_db(database)

            total_files = 0

            for map_name in map_list:
                size_tup = self.fmap.get_map_size(database, map_name)

                if size_tup and size_tup[0]:
                    total_files += size_tup[0]

            lines.append(
                f"<div style='margin-bottom:8px;'>"
                f"<span style='font-weight:bold;'>"
                f"{TEXT_ICONS['database']} DB {iii}"
                f"</span><br>"
                f"&nbsp;&nbsp;└── "
                f"{TEXT_ICONS['map']} "
                f"<b>{len(map_list)}</b> maps"
                f"<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;└── "
                f"{TEXT_ICONS['file']} "
                f"<b>{total_files:,}</b> files total"
                f"</div>"
            )

        map_card_text = "".join(lines)

        if not map_card_text:
            map_card_text = (
                "<span style='color:#777;'>No databases loaded</span>"
            )

        map_label = self.map_card.value_label

        if isinstance(map_label, QLabel):
            map_label.setText(map_card_text)


    # def refresh_device_card(self):
    #     devices = self.fmap.device_monitor.devices

    #     count = len(devices)

    #     lines = [
    #         f"<b style='font-size:20px;'>{count}</b> "
    #         f"<span style='color:#777;'>Active Devices Found</span>"
    #     ]

    #     if devices:
    #         lines.append("<br>")

    #     for iii, (mount, serial) in enumerate(devices):
    #         lines.append(
    #             f"<span style='color:#2e8b57;'>{TEXT_ICONS['device']}</span> "
    #             f"<b>{mount}</b>"
    #         )

    #         # If you eventually want the serial visible:
    #         # lines.append(
    #         #     f"&nbsp;&nbsp;&nbsp;&nbsp;"
    #         #     f"<span style='color:#777;'>"
    #         #     f"{serial}</span>"
    #         # )

    #     dev_card_text = "<br>".join(lines)

    #     dev_label = self.device_card.value_label

    #     if isinstance(dev_label, QLabel):
    #         dev_label.setText(dev_card_text)

    def refresh_device_card(self):
        devices = self.fmap.device_monitor.devices

        count = len(devices)

        status_icons = [
            TEXT_ICONS["online"],
            TEXT_ICONS["info"],
            TEXT_ICONS["busy"],
            TEXT_ICONS["warning"],
            TEXT_ICONS["unknown"],
        ]

        lines = [
            f"<span style='font-size:22px; font-weight:bold;'>"
            f"{TEXT_ICONS['device']} {count}"
            f"</span> "
            f"<span style='color:#777;'>Active Devices</span>"
        ]

        if devices:
            lines.append("<br>")

        for iii, (mount, serial) in enumerate(devices):
            is_last = iii == len(devices) - 1
            branch = "└──" if is_last else "├──"

            status_icon = status_icons[iii % len(status_icons)]

            lines.append(
                f"&nbsp;&nbsp;{branch} "
                f"{status_icon} "
                f"<b>{mount}</b>"
            )

        dev_card_text = "<br>".join(lines)
        dev_label = self.device_card.value_label
        if isinstance(dev_label, QLabel):
            dev_label.setText(dev_card_text)




    def refresh_all_cards(self):
        self.refresh_database_card()
        self.refresh_map_card()
        self.refresh_device_card()

