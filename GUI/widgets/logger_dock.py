# logger_dock.py
from PyQt6.QtWidgets import (
    QDockWidget,
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
)


class LoggerDock(QDockWidget):

    def __init__(self, parent=None):
        super().__init__("Logger", parent)

        self.setObjectName("LoggerDock")

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        self.text = QTextEdit()

        self.text.setReadOnly(True)
        buttons = QWidget()
        button_layout = QHBoxLayout(buttons)

        button_layout.setContentsMargins(0, 0, 0, 0)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)

        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        layout.addWidget(self.text)
        layout.addWidget(buttons)

        self.setWidget(container)


    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def append(self, message):
        self.text.append(str(message))

    def clear(self):
        self.text.clear()

    def info(self, message):
        self.append(f"[INFO] {message}")

    def warning(self, message):
        self.append(f"[WARNING] {message}")

    def error(self, message):
        self.append(f"[ERROR] {message}")
    
    def write_GUI_Log(self, text):
        """Called by ConsolePanelHandler"""
        self.append(text)