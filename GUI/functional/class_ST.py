from PyQt6.QtCore import QObject, pyqtSignal
import logging


class SignalTracker(QObject):
    """
    Central signal dispatcher for FileMap.

    Worker threads and background tasks emit these signals instead of
    interacting with the GUI directly.

    Signals
    -------
    log_update(bool)
        Indicates that new log messages are available.

    log_to_main(logging.LogRecord)
        Forwards a LogRecord to the main logger.

    devices_changed(list)
        Active devices have changed.
        Payload: [(mount_path, serial), ...]

    databases_changed()
        Database list or activation state changed.

    maps_changed()
        Maps have changed and dependent views should refresh.
    """

    log_update = pyqtSignal(bool)
    log_to_main = pyqtSignal(object)

    devices_changed = pyqtSignal(list)
    databases_changed = pyqtSignal()
    maps_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log_to_main_record(self, record: logging.LogRecord):
        """Forward a LogRecord to the main logger."""
        self.log_to_main.emit(record)

    def log_update_tick(self):
        """Notify listeners that log output is available."""
        self.log_update.emit(True)

    # --------------------------------------------------
    # Database
    # --------------------------------------------------

    def databases_updated(self):
        """Notify that the database list changed."""
        self.databases_changed.emit()

    # --------------------------------------------------
    # Devices
    # --------------------------------------------------

    def devices_updated(self, devices: list):
        """Notify that the detected devices changed."""
        self.devices_changed.emit(devices)

    # --------------------------------------------------
    # Maps
    # --------------------------------------------------

    def maps_updated(self):
        """Notify that maps changed."""
        self.maps_changed.emit()