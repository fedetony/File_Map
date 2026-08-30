import re
import html
import logging
from PyQt6 import QtCore, QtGui, QtWidgets

from functional.class_text_renderer import TextRenderer
from functional.class_icons import Icons
from controllers.class_filemap_cli_manager import FileMapCliManager
from class_sql_search_query import SQLSearchGenerator, ALLOWED_DICT,ALLOWED_OPERATORS_DICT
ALLOWED_OPERATORS=list(ALLOWED_OPERATORS_DICT.keys())
ALLOWED_OPERATIONS=list(ALLOWED_DICT.keys())
from models.class_provider_engine import AC,AutocompletePathFile
from widgets.class_explorer_tree_widget import OptionPopup

from dataclasses import dataclass, field
from typing import Any

SQL_SG = SQLSearchGenerator()
logging.getLogger("class_sql_search_query").propagate = False


QUERY_COLORS = {
    "operation": "bright_green",
    "operator": "green",
    "keyword": "magenta",
    "field": "yellow",
    "string": "bright_yellow",
    "number": "cyan",
    "boolean": "bright_magenta",
    "punctuation": "bold",
}

SQL_KEYWORDS = {
    "AND",
    "OR",
    "NOT",
    "IN",
    "IS",
    "NULL",
    "LIKE",
    "BETWEEN",
    "ASC",
    "DESC",
}

@dataclass
class AutocompleteResult:
    text: str
    options: list[str]


class SearchQueryWidget(QtWidgets.QWidget):
    """
    Reusable GUI widget for entering and validating advanced search queries.

    The widget is the GUI counterpart of the terminal application's
    A_C.get_sql_input() method. It does not perform the actual database
    search. Instead, it uses the application's SQL search generator to
    translate the user's text into an SQL WHERE clause.

    The widget provides:

        - Query input
        - Live SQL validation
        - Validation message
        - SQL preview
        - Search button
        - Clear button
        - Query history
        - Save Query
        - Load Query
        - Help / available operations
        - HTML rendering through TextRenderer

    The actual search is performed by the parent dialog/controller after
    receiving the searchRequested signal.

    Signals:
        searchRequested(str, str):
            Emitted when the user presses Search and the query is valid.
            Arguments:
                query_text: Original user-entered query.
                sql: Generated SQL WHERE clause.

        queryChanged(str):
            Emitted whenever the query text changes.

        validationChanged(bool, str, str):
            Emitted whenever validation is performed.
            Arguments:
                is_valid: Whether the query is valid.
                message: Validation message.
                sql: Generated SQL WHERE clause.

        queryCleared():
            Emitted when the query is cleared.
    """
    searchRequested = QtCore.pyqtSignal(str, str)
    queryChanged = QtCore.pyqtSignal(str)
    validationChanged = QtCore.pyqtSignal(bool, str, str)
    queryCleared = QtCore.pyqtSignal()

    def __init__(self, fmap: FileMapCliManager, parent=None):
        super().__init__(parent)
        self.fmap = fmap
        self.renderer = TextRenderer()
        self.icons = Icons()

        # Current validation state
        self._current_sql = ""
        self._sql_where = ""
        self._is_valid = False
        self._current_sql = ""
        self._error_msg = ""
        self._error_msg_log = ""
        self._query_history=[]
        # reroute check logger
        self._attach_class_sql_search_query()
        # Prevent recursive updates while loading/saving history
        self._updating = False

        self.build_ui()
        self._connect_signals()

        # Validate initial empty query
        self.validate_query()
    
    def _attach_class_sql_search_query(self):
        self.sql_log_handler = QtLogHandler()
        self.sql_log_handler.setLevel(logging.ERROR)
        self.sql_log_handler.setFormatter(logging.Formatter("%(message)s"))
        self.sql_log = logging.getLogger("class_sql_search_query")
        self.sql_log.addHandler(self.sql_log_handler)
        self.sql_log_handler.recordLogged.connect(self._on_sql_log_message)
    
    def _on_sql_log_message(self, record):
        self._error_msg_log = self.format_record(record)  
        self._update_validation_display()
        
    def format_record(self, record):
        """
        Convert a LogRecord into Rich-formatted text for display.

        The log level is color coded while the rest of the
        message keeps its original text.
        """
        colors = {
            "DEBUG": "magenta",
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bright_red",
        }
        msg = record.getMessage()
        if not msg:
            return ""
        words = msg.split(" ")
        formatted = []
        for word in words:
            if word.upper() in colors:
                color = colors[word.upper()]
                word = f"[{color}]{word}[/]"

            formatted.append(word)
        return " ".join(formatted)

        

    def build_ui(self):
        """
        Build the compact search query widget.

        Layout:
            [valid icon] [ where sql query.. ] [valid message..] [valid] [?]
            [icon] [ query............................. ] [search] [history]

        Detailed validation, SQL preview, history management and
        search options are intentionally kept out of the main layout
        to keep this widget suitable for embedding in crowded dialogs.
        """
        query_font = QtGui.QFont("Consolas")
        query_font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        query_font.setPointSize(10)

        # ----------------------
        # Search icon
        # ----------------------
        self.search_icon = QtWidgets.QToolButton()
        self.search_icon.setIcon(self.icons.icon("search"))
        self.search_icon.setAutoRaise(True)
        self.search_icon.setEnabled(False)
        self.search_icon.setFixedWidth(32)
        self.search_icon.setToolTip("Search")
        # ----------------------
        # Query
        # ----------------------
        self.query_edit = QtWidgets.QLineEdit()
        self.query_edit.setPlaceholderText("Search...")
        self.query_edit.setClearButtonEnabled(True)
        self.query_edit.setMinimumHeight(26)
        # ----------------------
        # Validation indicator
        # ----------------------
        self.valid_icon = QtWidgets.QToolButton()
        self.valid_icon.setAutoRaise(True)
        self.valid_icon.setEnabled(True)
        self.valid_icon.setFixedWidth(32)

        self.valid_label = QtWidgets.QLabel()
        self.valid_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.valid_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.valid_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.valid_label.setCursor(QtCore.Qt.CursorShape.IBeamCursor)
        self.valid_label.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.valid_label.setToolTip("Query validation")
        # ----------------------
        # History
        # ----------------------
        self.history_button = QtWidgets.QToolButton()
        self.history_button.setText("")
        self.history_button.setIcon(self.icons.icon("history2"))
        self.history_button.setFixedWidth(32)
        self.history_button.setAutoRaise(True)
        self.history_button.setToolTip("Search history")
        # ----------------------
        # Search
        # ----------------------
        self.search_button = QtWidgets.QPushButton("🔍 Go Search")
        #self.search_button.setText("🔍 Go")
        self.search_button.setIcon(self.icons.icon("search db"))
        self.search_button.setToolTip("Let's go! Search...")
        # ----------------------
        # Help
        # ----------------------
        self.help_button = QtWidgets.QToolButton()
        self.help_button.setText("?")
        self.help_button.setIcon(self.icons.icon("help b"))
        self.help_button.setFixedWidth(32)
        self.help_button.setAutoRaise(True)
        self.help_button.setToolTip("Search operations and operators")

        # ----------------------
        # SQL
        # ----------------------

        self.sql_where_label = QtWidgets.QLabel()
        self.sql_where_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.sql_where_label.setWordWrap(False)
        self.sql_where_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.sql_where_label.setCursor(QtCore.Qt.CursorShape.IBeamCursor)

        self.sql_where_label.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.sql_what_label = QtWidgets.QLabel("WHAT:")
        self.sql_what_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.sql_what_label.adjustSize()
        # self.sql_what_label.setWordWrap(True)
        
        # Set Fonts
        self.query_edit.setFont(query_font)
        self.sql_where_label.setFont(query_font)
        self.valid_label.setFont(query_font)

        # ----------------------
        # Main layout
        # ----------------------
        main_layout = QtWidgets.QVBoxLayout(self)
        
        validation_layout = QtWidgets.QHBoxLayout()
        validation_layout.setContentsMargins(4, 1, 4, 1)
        validation_layout.setSpacing(4)

        validation_layout.addWidget(self.valid_icon)
        validation_layout.addWidget(self.sql_where_label, 1)
        validation_layout.addWidget(self.valid_label, 2)
        validation_layout.addWidget(self.help_button)

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.setContentsMargins(4, 3, 4, 3)
        input_layout.setSpacing(3)       

        input_layout.addWidget(self.search_icon)
        input_layout.addWidget(self.query_edit, 1)
        input_layout.addSpacing(3)
        input_layout.addWidget(self.search_button)
        input_layout.addWidget(self.history_button)

        main_layout.addLayout(validation_layout)
        main_layout.addLayout(input_layout)
        # ----------------------
        # Option popup
        # ----------------------
        self.option_popup = OptionPopup(target_edit=self.query_edit, parent=self)
        # ----------------------
        # history popup
        # ----------------------
        self.history_popup = OptionPopup(target_edit=self.query_edit, parent=self)

        # ----------------------
        # Compact frame styling
        # ----------------------

        self.setObjectName("SearchQueryWidget")

        self.setStyleSheet("""
            QWidget#SearchQueryWidget {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background: palette(base);
            }

            QWidget#SearchQueryWidget QLineEdit {
                border: none;
                background: transparent;
                padding: 2px 4px;
            }

            QWidget#SearchQueryWidget QToolButton {
                border: none;
                background: transparent;
                padding: 2px;
            }

            QWidget#SearchQueryWidget QToolButton:hover {
                background: palette(midlight);
                border-radius: 3px;
            }

            QWidget#SearchQueryWidget QToolButton:pressed {
                background: palette(mid);
            }
        """)

        # Initial state
        self._set_validation_state_icon_tooltip(None)

    # ==============================================================
    # Properties
    # ==============================================================

    @property
    def sql_sg(self)-> SQLSearchGenerator:
        return self.fmap.sql_sg
    
    @property
    def ac(self)->AutocompletePathFile:
        return AC
    
    # ==============================================================
    # Autocomplete 
    # ==============================================================
    #Event Filter
    def eventFilter(self, obj, event):
        if obj is self.query_edit:
            if event.type() == QtCore.QEvent.Type.KeyPress:
                key = event.key()
                if key == QtCore.Qt.Key.Key_Tab:
                    self._autocomplete()
                    return True

                if key == QtCore.Qt.Key.Key_F1:
                    self._show_help()
                    return True
                
                if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                    self.validate_query()
                    self._do_search()
                    return True
                
                if key == QtCore.Qt.Key.Key_Down:
                    self._show_options()
                    return True

        return super().eventFilter(obj, event)

    def _autocomplete(self):
        text = self.query_edit.text()
        pos = self.query_edit.cursorPosition()
        before = text[:pos]
        after = text[pos:]

        # Reset previous options
        self.ac.options = ""

        auto = self.ac.autocomplete_from_list(
            before,
            ALLOWED_OPERATIONS,
        )

        if auto:
            new_text = before + auto + after

            self.query_edit.setText(new_text)

            # Put cursor immediately after autocomplete
            self.query_edit.setCursorPosition(
                len(before + auto)
            )

        self._show_options()
    
    def _show_history(self):
        """Show the saved query history in the history popup."""
        if not self._query_history:
            self.history_popup.hide()
            self.query_edit.setFocus()
            return
        self.history_popup.clear()
        for query in self._query_history:
            self.history_popup.addItem(query)
        # Keep the popup reasonably sized.
        self.history_popup.setMinimumWidth(
            max(self.history_button.width(), self.query_edit.width())
        )
        self.history_popup.setMaximumWidth(900)
        self.history_popup.adjustSize()
        # Place directly below the history button.
        pos = self.history_button.mapToGlobal(
            QtCore.QPoint(
                self.history_button.width() - self.history_popup.width(),
                self.history_button.height(),
            )
        )
        self.history_popup.move(pos)
        self.history_popup.show()
        self.history_popup.raise_()
        if self.history_popup.count() > 0:
            self.history_popup.setCurrentRow(0)
        self.history_popup.setFocus()



    def _show_options(self):
        options = self.ac.autocomplete_options
        if not options:
            self.option_popup.hide()
            return
        self.option_popup.clear()
        for option in options:
            self.option_popup.addItem(str(option))
        self.option_popup.adjustSize()
        pos = self.query_edit.mapToGlobal(
            QtCore.QPoint(
                0,
                self.query_edit.height(),
            )
        )
        self.option_popup.move(pos)
        self.option_popup.show()
        self.option_popup.setFocus()

    def _option_selected(self, option: str):
        options = self.ac.autocomplete_options
        complements = self.ac.complement_options_list
        complement=""
        for opt,comp in zip(options,complements):
            if opt == option:
                complement=comp
                break
        
        self.option_popup.hide()

        text = self.query_edit.text()
        pos = self.query_edit.cursorPosition()

        before = text[:pos]
        after = text[pos:]

        token_start = pos #self._find_current_token_start(before)

        new_text = (
            before[:token_start]
            + complement
            + before[pos:]
            + after
        )

        self.query_edit.setText(new_text)
        new_pos = token_start + len(complement)
        self.query_edit.setCursorPosition(new_pos)
        self.query_edit.setFocus()

        self.validate_query()


    # ==============================================================
    # Signals
    # ==============================================================

    def _connect_signals(self):

        self.query_edit.installEventFilter(self)
        self.query_edit.textChanged.connect(self._query_text_changed)

        self.search_button.clicked.connect(self._do_search)
        # pressed fires when the mouse button goes down; 
        # clicked fires after the button press/release interaction

        self.option_popup.optionSelected.connect(self._option_selected)
        self.sql_where_label.customContextMenuRequested.connect(
            self._sql_context_menu_where)
        self.valid_label.customContextMenuRequested.connect(
            self._sql_context_menu_valid)
        self.query_edit.textChanged.connect(self.validate_query)

        self.help_button.clicked.connect(self._show_help)
        self.history_button.clicked.connect(self._show_history)
        self.history_popup.optionSelected.connect(self._history_selected)

        # self.clear_button.clicked.connect(self._clear)
        
        # self.save_query_button.clicked.connect(self._save_query)
        # self.load_query_button.clicked.connect(self._load_query)


    # ==============================================================
    # Validation
    # ==============================================================

    def validate_query(self):
        """
        Validate the current query and update the GUI.

        Returns:
            tuple[str, str, bool]:
                (SQL WHERE clause, message, is_valid)
        """

        text = self.query_edit.text()

        try:
            sql, msg, is_valid = (
                SQL_SG.get_sql_from_text_input(text))
        except Exception as exc:
            sql = ""
            msg = str(exc)
            is_valid = False

        self._sql_where = sql or ""
        self._error_msg = msg or ""
        if self._error_msg_log:
            self._error_msg = self._error_msg_log + self._error_msg
            self._error_msg_log = ""
        self._is_valid = bool(is_valid)

        self._update_validation_display()

        self.validationChanged.emit(
            self._is_valid,
            self._sql_where,
            self._error_msg,
        )

        return self._sql_where, self._error_msg, self._is_valid 

    def _update_validation_display(self):
        """
        Update validation, message and SQL preview widgets.
        """
        self._set_validation_state_icon_tooltip(self.is_valid,self._error_msg,self._sql_where)
        the_err=str(self._error_msg)
        if self._error_msg:
            the_err=self.rich_query_markup(self._error_msg)
        self.valid_label.setText(self.renderer.to_html(the_err))
        self.valid_label.adjustSize()

        if self._sql_where:
            sql_where=self.rich_query_markup(self._sql_where)
            self.sql_where_label.setText(
                self.renderer.to_html(sql_where)
            )
        else:
            color='#888888'
            self.sql_where_label.setText(
                f'<span style="color:{color};">'
                'No query available...'
                '</span>'
            )

        # if self._current_sql:
        #     self.sql_preview.setHtml(
        #         self.renderer.to_html(self._current_sql)
        #     )
        # else:
        #     self.sql_preview.setHtml(
        #         '<span style="color:#888888;">'
        #         'SQL WHERE:'
        #         '</span>'
        #     )

    # ==============================================================
    # Query changes
    # ==============================================================

    def _query_text_changed(self, text: str):
        if self._updating:
            return

        self.validate_query()
        self.queryChanged.emit(text)

    # ==============================================================
    # Search
    # ==============================================================

    def _do_search(self):
        """
        Validate and emit a search request.

        The widget does not execute the search itself.
        """
        print("######## _do_search", id(self))
        sql, msg, is_valid = self.validate_query()

        if not is_valid:
            # Make the invalid state visually obvious
            self.query_edit.setFocus()
            return

        query = self.query_edit.text().strip()

        if not query or not sql:
            self.query_edit.setFocus()
            return

        self._add_history(query)
        self.searchRequested.emit(query, sql)

    # ==============================================================
    # Clear
    # ==============================================================

    def clear_search(self):
        self._clear()

    def _clear(self):
        self._updating = True
        try:
            self.query_edit.clear()
        finally:
            self._updating = False

        self.validate_query()

        self.queryCleared.emit()
        self.query_edit.setFocus()

    # ==============================================================
    # History
    # ==============================================================
    def _add_history(self, query: str, max_history: int = 50):
        query = query.strip()
        if not query:
            return
        # Remove existing occurrence so the newest use moves to the top.
        try:
            self._query_history.remove(query)
        except ValueError:
            pass
        # Newest first.
        self._query_history.insert(0, query)
        # Keep at most max_history entries.
        del self._query_history[max_history:]

    def _history_selected(self, history_query: str):
        """Load a query from history into the query editor."""
        self.history_popup.hide()
        if not history_query:
            return
        self.query_edit.setText(history_query)
        self.query_edit.setCursorPosition(len(history_query))
        self.query_edit.setFocus()

    # ==============================================================
    # Save / Load
    # ==============================================================
    def _save_query(self):
        query = self.query_edit.text().strip()

        if not query:
            QtWidgets.QMessageBox.information(
                self,
                "Save Query",
                "There is no query to save.",
            )
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Query",
            "",
            "Search Query (*.query);;Text Files (*.txt);;All Files (*)",
        )

        if not filename:
            return

        try:
            with open(
                filename,
                "w",
                encoding="utf-8",
            ) as f:
                f.write(query)

        except OSError as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Query",
                f"Could not save query:\n{exc}",
            )

    def _load_query(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Query",
            "",
            "Search Query (*.query);;Text Files (*.txt);;All Files (*)",
        )

        if not filename:
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                query = f.read().strip()

        except OSError as exc:
            QtWidgets.QMessageBox.critical(
                self, "Load Query", f"Could not load query:\n{exc}")
            return

        self._updating = True

        try:
            self.query_edit.setText(query)
        finally:
            self._updating = False

        self.validate_query()
        self._add_history(query)
        self.query_edit.setFocus()

    # ==============================================================
    # Help
    # ==============================================================

    def _show_help(self):
        """
        Show detailed information about the search syntax.

        The help is generated from ALLOWED_DICT and
        ALLOWED_OPERATORS_DICT so it stays synchronized with
        the actual SQL search engine configuration.
        """
        lines = []
        # ---------------
        # Title
        # ---------------
        lines.append("[bold blue]Search Help[/]")
        lines.append(
            "Build queries using an operation, an operator and a value."
        )
        lines.append("")
        # ---------------
        # Operations
        # ---------------
        lines.append("[bold green]Available Operations[/]")
        lines.append("[dim]" + "─" * 55 + "[/]")
        operation_descriptions = {
            "id": "Unique database identifier.",
            "dt_data_created": "Date/time when the database record was created.",
            "dt_data_modified": "Date/time when the database record was modified.",
            "filepath": "Text in a path of a file",
            "filename": "Name or part of the name of a the file.",
            "md5": "MD5 checksum of the file.",
            "size": "File size. Supports numeric comparisons and units.",
            "dt_file_created": "File creation date/time.",
            "dt_file_accessed": "File access date/time.",
            "dt_file_modified": "File modification date/time.",
        }
        for operation, config in ALLOWED_DICT.items():
            description = operation_descriptions.get(
                operation,
                "Search using this field."
            )
            operators = ", ".join(f"[yellow]{op}[/]" for op in config["operators"])
            lines.append(f"[bold cyan]{operation}[/] — {description}")
            lines.append(f"    Operators: {operators}")

            lines.append("")
        # ---------------
        # Operators
        # ---------------
        lines.append("[bold green]Available Operators[/]")
        lines.append("[dim]" + "─" * 55 + "[/]")

        for operator, description in ALLOWED_OPERATORS_DICT.items():
            lines.append(
                f"[bold yellow]{operator}[/]  "
                f"{description}"
            )
        lines.append("")
        # ---------------
        # Examples
        # ---------------
        lines.append("[bold green]Examples[/]")
        lines.append("[dim]" + "─" * 55 + "[/]")
        examples = [
            '[cyan]filename[/] [yellow]=[/] *.jpg',
            '[cyan]filename[/] [yellow]~=[/] report',
            '[cyan]filepath[/] [yellow]=[/] %Documents%',
            '[cyan]size[/] [yellow]>[/] 1000000',
            '[cyan]size[/] [yellow]=>[/] 1000000',
            '[cyan]filename[/] [yellow]=[/] *.jpg [yellow]&&[/] [cyan]size[/] [yellow]>[/] 100000',
            '[cyan]filepath[/] [yellow]=[/] %Documents% [yellow]&&[/] [cyan]filename[/] [yellow]~= [/ ]report',
        ]

        for example in examples:
            lines.append(f"    {example}")
        # ---------------
        # Render Rich -> HTML
        # ---------------
        help_txt = "<br>".join(self.renderer.to_html(line) for line in lines)
        help_txt = f"""
            <div style="font-family: Consolas, monospace; font-size: 10pt;">
                {help_txt}
            </div>
            """
        # ---------------
        # Dialog
        # ---------------
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Search Options")
        dialog.resize(850, 700)

        layout = QtWidgets.QVBoxLayout(dialog)

        browser = QtWidgets.QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(help_txt)

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(dialog.accept)

        layout.addWidget(browser)
        layout.addWidget(close_button)

        dialog.exec()


    # ==============================================================
    # Public API
    # ==============================================================

    @property
    def query(self) -> str:
        """Return the current user-entered query."""
        return self.query_edit.text().strip()

    @property
    def sql(self) -> str:
        """Return the most recently generated SQL WHERE clause."""
        return self._current_sql

    @property
    def message(self) -> str:
        """Return the most recent validation message."""
        return self._sql_where

    @property
    def is_valid(self) -> bool:
        """Return whether the current query is valid."""
        return self._is_valid

    def set_query(self, query: str):
        """Set the query text and validate it."""
        self._updating = True

        try:
            self.query_edit.setText(query or "")
        finally:
            self._updating = False

        self.validate_query()

    def get_sql_input(self) -> tuple:
        """
        Return the current query in the same format as the terminal
        A_C.get_sql_input() method.

        Returns:
            tuple[str, str, bool]:
                (SQL WHERE clause, message, is_valid)
        """
        return self.validate_query()
    
    def _set_validation_state_icon_tooltip(self, state, message="", sql=""):
        """
        Update the compact validation indicator.

        state:
            None  -> unknown / empty
            True  -> valid
            False -> invalid
        """
        if state is True and (sql or message):
            self.valid_icon.setIcon(self.icons.icon("valid query"))
            tooltip = "Query is valid"
            if message:
                tooltip += f"\n\n{message}"
            if sql:
                tooltip += f"\n\nSQL WHERE:\n{sql}"
            self.search_icon.setEnabled(True)
            self.search_button.setEnabled(True)

        elif state is False:
            self.valid_icon.setIcon(self.icons.icon("not valid query"))
            tooltip = "Query is invalid"
            if message:
                tooltip += f"\n\n{message}"
            if sql:
                tooltip += f"\n\nSQL WHERE:\n{sql}"
            self.search_icon.setEnabled(False)
            self.search_button.setEnabled(False)
        
        else:
            self.valid_icon.setIcon(self.icons.icon("gift"))
            tooltip="Enter a search query"
            self.search_icon.setEnabled(False)
            self.search_button.setEnabled(False)

        self.valid_icon.setToolTip(tooltip)
        self.valid_label.setToolTip(tooltip)

    def _sql_context_menu_where(self, pos):
        self._sql_context_menu(self.sql_where_label, pos)
    
    def _sql_context_menu_valid(self, pos):
        self._sql_context_menu(self.valid_label, pos)

    def _sql_context_menu(self,obj, pos):
        """Context menu for the SQL/query preview."""

        menu = QtWidgets.QMenu(self)

        copy_action = menu.addAction("Copy Query")
        copy_action.setIcon(self.icons.icon("copy"))
        clear_action = menu.addAction("Clear Query")
        clear_action.setIcon(self.icons.icon("clear"))
        menu.addSeparator()
        clear_history_action = menu.addAction("Clear History")
        clear_history_action.setIcon(self.icons.icon("trash"))
        # --------------------------------------------------------------
        # Future actions
        # --------------------------------------------------------------
        #
        # menu.addSeparator()
        # save_action = menu.addAction("Save Query")
        # copy_html_action = menu.addAction("Copy Formatted")
        # select_action = menu.addAction("Select All")
        #
        action = menu.exec(obj.mapToGlobal(pos))

        if action == copy_action:
            self._copy_sql_html()

        elif action == clear_action:
            self._clear()

        elif action == clear_history_action:
            self._clear_history()


    def _copy_sql(self):
        """Copy the current SQL WHERE clause to the clipboard."""
        if not self._current_sql:
            return
        QtWidgets.QApplication.clipboard().setText(self._current_sql)


    def _clear_history(self):
        """Clear the search query history."""

        self._query_history.clear()

        # If you display history in a popup, keep it synchronized.
        if hasattr(self, "history_popup"):
            self.history_popup.clear()
            self.history_popup.hide()

        # If you also maintain a history combo somewhere,
        # clear it here as well.
        #
        # if hasattr(self, "history_combo"):
        #     self.history_combo.clear()
    
    def _copy_sql_html(self):
        mime = QtCore.QMimeData()
        mime.setHtml(self.sql_where_label.text())
        mime.setText(self._current_sql)

        QtWidgets.QApplication.clipboard().setMimeData(mime)
    
    def _select_sql(self):
        pass

    def _save_current_query(self):
        pass
    

    @staticmethod
    def rich_query_markup(query: str, 
                          operations: list[str] =ALLOWED_OPERATIONS, 
                          operators: list[str]=ALLOWED_OPERATORS):
        """
        Apply Rich markup colors to a search query.

        Args:
            query: Query text.
            operations: Allowed search operations.
            operators: Allowed operators.

        Returns:
            Query formatted with Rich color markup.
        """
        if not query:
            return ""

        # ----------------------------------------------------------
        # Build lookup sets
        # ----------------------------------------------------------
        operation_set = {str(x).casefold() for x in operations}
        operator_set = {str(x).casefold() for x in operators}
        keyword_set = {x.casefold() for x in SQL_KEYWORDS}

        # ----------------------------------------------------------
        # Tokenizer
        # ----------------------------------------------------------
        token_pattern = re.compile(
            r"""
            '(?:''|[^'])*'             # SQL string
            |"(?:[^"]|"")*"            # quoted string
            |\b\d+(?:\.\d+)?\b        # number
            |>=|<=|!=|<>|=|>|<         # operators
            |\(|\)|,                   # punctuation
            |\b[A-Za-z_][A-Za-z0-9_]*\b
            """,
            re.VERBOSE,
        )

        result = []
        pos = 0

        for match in token_pattern.finditer(query):
            # ------------------------------------------------------
            # Text between tokens
            # ------------------------------------------------------
            result.append(query[pos:match.start()])
            token = match.group(0)
            folded = token.casefold()

            # ------------------------------------------------------
            # String
            # ------------------------------------------------------
            if ((token.startswith("'") and token.endswith("'"))
                or (token.startswith('"') and token.endswith('"'))):
                result.append(
                    f"[{QUERY_COLORS['string']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # Number
            # ------------------------------------------------------
            elif re.fullmatch(r"\d+(?:\.\d+)?", token):
                result.append(
                    f"[{QUERY_COLORS['number']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # Operator
            # ------------------------------------------------------
            elif folded in operator_set:
                result.append(
                    f"[{QUERY_COLORS['operator']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # Search operation
            # ------------------------------------------------------
            elif folded in operation_set:
                result.append(
                    f"[{QUERY_COLORS['operation']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # SQL keyword
            # ------------------------------------------------------

            elif folded in keyword_set:
                result.append(
                    f"[{QUERY_COLORS['keyword']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # Boolean
            # ------------------------------------------------------

            elif folded in {"true", "false"}:
                result.append(
                    f"[{QUERY_COLORS['boolean']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # Punctuation
            # ------------------------------------------------------
            elif token in {"(", ")", ","}:
                result.append(
                    f"[{QUERY_COLORS['punctuation']}]"
                    f"{token}"
                    f"[/]"
                )

            # ------------------------------------------------------
            # Everything else
            # ------------------------------------------------------
            else:
                result.append(token)

            pos = match.end()
        result.append(query[pos:])

        return "".join(result)


class QtLogHandler(QtCore.QObject, logging.Handler):
    """
    Logging handler that forwards LogRecords to Qt via a signal.
    """

    recordLogged = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            self.recordLogged.emit(record)
        except Exception:
            self.handleError(record)




