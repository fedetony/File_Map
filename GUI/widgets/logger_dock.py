from PyQt6.QtWidgets import (
    QDockWidget,
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from collections import deque
from datetime import datetime
from class_text_renderer import TextRenderer


class LoggerDock(QDockWidget):
    """
    Dockable GUI console for displaying application log records.

    Receives logging.LogRecord objects through a queue populated by the
    LoggerManager QueueHandler. The dock is responsible only for displaying
    and managing the GUI representation of logs.

    Features:
        - Terminal-style log viewer.
        - Color formatting based on log level.
        - Keeps a limited history using an internal deque buffer.
        - Allows exporting displayed log history to a text file.
        - Processes records asynchronously using a QTimer to keep the GUI
          responsive while background threads generate logs.

    Notes:
        Log filtering should be implemented here at the display layer,
        not in LoggerManager. The logging system should continue receiving
        all records, while this widget decides which records are visible.

        Future filters can include:
            - Enable/disable log levels (DEBUG, INFO, WARNING, ERROR, etc.).
            - Filter by logger name (DatabaseManager, MainWindow, etc.).
            - Search/filter text.
            - Toggle thread name or timestamp visibility.

    Args:
        log_queue (queue.Queue):
            Queue containing logging.LogRecord objects emitted by the
            LoggerManager QueueHandler.

        parent (QWidget, optional):
            Parent widget owning this dock.
    """

    MAX_LINES = 10000

    def __init__(self, log_queue, parent=None):
        super().__init__("Logger", parent)

        self.log_queue = log_queue

        self.create_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_queue)
        self.timer.start(100)   # 10 times/sec
        self.records = deque(maxlen=self.MAX_LINES)
        self.t_r = TextRenderer()


    def create_ui(self):

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2,2,2,2)

        self.text = QTextEdit()
        self.text.setReadOnly(True)

        # terminal look
        self.text.setStyleSheet("""
            QTextEdit {
                background-color: #111111;
                color: #dddddd;
                font-family: Consolas, Courier New, monospace;
                font-size: 11pt;
            }
        """)
        self.text.setFont(QFont("Consolas", 10))
        self.text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        buttons = QWidget()
        button_layout = QHBoxLayout(buttons)
        button_layout.setContentsMargins(0,0,0,0)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)

        self.save_button = QPushButton("Save Log")
        self.save_button.clicked.connect(self.save_log)


        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()


        layout.addWidget(self.text)
        layout.addWidget(buttons)

        self.setWidget(container)

    def process_queue(self):
        """
        Reads pending log records from the queue and displays them.
        """
        while not self.log_queue.empty():
            record = self.log_queue.get()
            self.append_record(record)
    
    def format_record(self, record):
        """
        Converts a LogRecord into formatted HTML for display.

        The log level is color coded while the rest of the
        message keeps the terminal style formatting.
        """
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        colors = {
            "DEBUG": "#888888",
            "INFO": "#55dd55",
            "WARNING": "#ffff55",
            "ERROR": "#ff5555",
            "CRITICAL": "#ff2222",
        }

        level_color = colors.get(
            record.levelname,
            "#dddddd"
        )

        level = (
            f'<span style="color:{level_color};">'
            f'[{record.levelname}]'
            f'</span>'
        )

        message= self.t_r.to_html(record.message)

        return (
            f'<span style="color:#888888;">'
            f'{timestamp} {record.name}'
            f'</span> '
            f'{level} '
            f'{message}'
        )

    def append_record(self, record):
        """
        Stores a log record and appends its formatted output to the view.
        """
        self.records.append(record)
        self.text.append(self.format_record(record))
        self.limit_lines()
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())

    def limit_lines(self):
        """
        Removes oldest displayed lines when the log exceeds the limit.
        """
        doc = self.text.document()
        while doc.blockCount() > self.MAX_LINES:
            cursor = self.text.textCursor()
            cursor.movePosition(
                cursor.MoveOperation.Start
            )
            cursor.select(
                cursor.SelectionType.BlockUnderCursor
            )
            cursor.removeSelectedText()
            cursor.deleteChar()

    def save_log(self):
        filename,_ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            "filemap_log.txt",
            "Text files (*.txt)"
        )

        if filename:
            with open(filename,"w",encoding="utf-8") as f:
                for record in self.records:
                    f.write(
                        f"{record.levelname} "
                        f"({record.name}) "
                        f"{record.message}\n"
                    )

    def clear(self):
        """
        Clears the visible log output.
        """
        self.text.clear()
        self.records.clear()
    
    def write_GUI_Log(self, text):
        """Called by ConsolePanelHandler in class_LogHandler"""
        print(f"Got-> {text}")
        #self.log_message(text)