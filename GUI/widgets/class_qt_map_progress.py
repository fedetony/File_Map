# class_qt_map_progress.py

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QProgressBar,
    QHBoxLayout,
    QWidget,
)

from class_map_progress import MapProgress
from functional.class_text_renderer import TextRenderer


class QtMapProgress(QWidget, MapProgress):
    """
    Thread-safe PyQt6 implementation of MapProgress.

    The MapProgress methods can be called from a worker thread.
    All actual QWidget manipulation is performed in the GUI thread
    through Qt queued signals.
    """

    # Payloads from worker -> GUI
    start_requested = QtCore.pyqtSignal(int, str)
    update_requested = QtCore.pyqtSignal(object)
    stop_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None, text_renderer=None):
        super().__init__(parent)

        self.total = 0
        self.current = 0
        self.last_per = -1

        self.text_renderer = text_renderer or TextRenderer()

        self.description_label = QLabel()
        self.description_label.setTextFormat(
            Qt.TextFormat.RichText
        )
        self.description_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.description_label, 0)
        layout.addWidget(self.progress_bar, 1)

        self.setLayout(layout)

        # These slots execute in the GUI thread.
        self.start_requested.connect(self._start_gui)
        self.update_requested.connect(self._update_gui)
        self.stop_requested.connect(self._stop_gui)

        self.hide()

    # --------------------------------------------------
    # MapProgress interface
    # --------------------------------------------------

    def start(self, total, description):
        """
        Safe to call from any thread.
        """

        self.start_requested.emit(max(0, int(total)), str(description))

    def update(self, current=None, advance=None, description=None):
        """
        Safe to call from any thread.
        """
        self.update_requested.emit({
            "current": current,
            "advance": advance,
            "description": description})

    def SetStatus(self, value):
        self.update_percent(value)

    def update_percent(self, value, total=100):
        """
        Safe to call from any thread.
        """
        value = max(0, min(int(value), total))
        self.update_requested.emit({"percent": value, "percent_total": total})

    def stop(self):
        """
        Safe to call from any thread.
        """
        self.stop_requested.emit()

    # --------------------------------------------------
    # GUI-thread slots
    # --------------------------------------------------

    @QtCore.pyqtSlot(int, str)
    def _start_gui(self, total, description):

        self.total = total
        self.current = 0
        self.last_per = -1

        self.progress_bar.setRange(
            0,
            self.total,
        )

        self.progress_bar.setValue(0)

        self._set_description(description)

        self.show()

    @QtCore.pyqtSlot(object)
    def _update_gui(self, data):

        if self.total <= 0:
            return

        # Percentage update
        if "percent" in data:

            value = data["percent"]
            total = data["percent_total"]
            if self.last_per == value:
                return

            current = int(self.total * value / total)

            self.current = max(0, min(current, self.total))
            self.progress_bar.setValue(self.current)
            self.last_per = value
            return

        # Normal update
        current = data.get("current")
        advance = data.get("advance")
        description = data.get("description")

        if current is not None:
            self.current = int(current)

        if advance is not None:
            self.current += int(advance)

        self.current = max(0, min(self.current, self.total))

        if description is not None:
            self._set_description(description)

        self.progress_bar.setValue(self.current)

    @QtCore.pyqtSlot()
    def _stop_gui(self):

        self.hide()

        self.total = 0
        self.current = 0
        self.last_per = -1

    # --------------------------------------------------
    # Rendering
    # --------------------------------------------------

    def _set_description(self, value):
        html_text = self.text_renderer.to_html(value)
        self.description_label.setText(html_text)