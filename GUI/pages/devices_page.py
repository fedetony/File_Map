# devices_page.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QGroupBox,
    QTextEdit,
    QTreeView,
)

from functional.class_icons import Icons
from controllers.class_filemap_cli_manager import FileMapCliManager
from widgets.ask_confirmation_dialog import ConfirmationDialog
from widgets.class_device_menu import DeviceMenu
# from class_table_widget_functions import TableWidgetFunctions

class DevicesPage(QWidget):

    def __init__(self, fmap:FileMapCliManager, parent=None):
        super().__init__(parent)
        
        self.icons =Icons()
        self.fmap = fmap
        self.dev_m = fmap.device_monitor

        self._refresh_timeout_ms = 5000
        self._refresh_elapsed = 0

        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.setInterval(200)      # check every 200 ms
        self.refresh_timer.timeout.connect(self._check_refresh)

        self.create_ui()
        self.connect_objects()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(self)
        
        # Header
        header= QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(self.icons.icon("devices").pixmap(32, 32))
        title = QLabel("Devices")
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


        toolbar = QHBoxLayout()
        self.rescan_btn = QPushButton("Rescan Devices")
        self.rescan_btn.setIcon(self.icons.icon("refresh"))
        toolbar.addWidget(self.rescan_btn)

        toolbar.addStretch()

        self.view_details_ckb= QCheckBox("View Details")
        self.view_details_ckb.setIcon(self.icons.icon("details"))
        self.view_details_ckb.setChecked(False)
        toolbar.addWidget(self.view_details_ckb)

        layout.addLayout(toolbar)

        splitter = QSplitter()

        # Device list
        devices_group = QGroupBox("Detected Devices")

        devices_layout = QVBoxLayout(devices_group)

        self.device_tv_obj = QTreeView()
        self.dev_menu = DeviceMenu(self.fmap,self.device_tv_obj)
        
        #self.dev_menu.__signal__.connect(self.change_page)

        # Details
        devices_layout.addWidget(self.device_tv_obj)
        details_group = QGroupBox("Device Information")
        details_layout = QVBoxLayout(details_group)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setText("Select a device...")

        details_layout.addWidget(self.details)
        splitter.addWidget(devices_group)
        splitter.addWidget(details_group)


        splitter.setStretchFactor(0,3)
        splitter.setStretchFactor(1,1)
        layout.addWidget(splitter)

    def connect_objects(self):
        self.view_details_ckb.stateChanged.connect(self.change_view)
        self.rescan_btn.clicked.connect(self.rescan_devices)

    # --------------------------------------------------
    # functions
    # --------------------------------------------------

    def change_view(self,value):
        is_checked=self.view_details_ckb.isChecked()
        if is_checked:
            self.dev_menu.generate_new_info_struct()
        else:
            self.dev_menu.generate_new_mount_serial_struct()
    
    def rescan_devices(self):
        self.rescan_btn.setEnabled(False)
        self.rescan_btn.setText("Scanning...")

        self.dev_menu.info_cache.clear()

        self._refresh_elapsed = 0
        self.fmap.device_monitor.refresh()

        self.refresh_timer.start()

    def _check_refresh(self):
        self._refresh_elapsed += self.refresh_timer.interval()
        devices = self.fmap.device_monitor.devices

        if devices:
            self.refresh_timer.stop()

            self.rescan_btn.setEnabled(True)
            self.rescan_btn.setText("Rescan Devices")

            if self.view_details_ckb.isChecked():
                self.dev_menu.generate_new_info_struct()
            else:
                self.dev_menu.generate_new_mount_serial_struct()
            return

        if self._refresh_elapsed >= self._refresh_timeout_ms:
            self.refresh_timer.stop()

            self.rescan_btn.setEnabled(True)
            self.rescan_btn.setText("Rescan Devices")

            QtWidgets.QMessageBox.warning(
                self,
                "Timeout",
                "Device scan did not complete."
            )
    
    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def activate(self):
        pass


    def deactivate(self):
        pass