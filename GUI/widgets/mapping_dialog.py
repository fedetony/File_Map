
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer


class MappingDialog(QtWidgets.QDialog):

    MAX_LOG_LINES = 1000
    LOG_FLUSH_INTERVAL = 100
    LOG_BATCH_SIZE = 200

    refresh_mapping_tree = QtCore.pyqtSignal()
    mapping_is_running_signal = QtCore.pyqtSignal()
    mapping_is_not_running_signal = QtCore.pyqtSignal()
    dialog_exit = QtCore.pyqtSignal(str)

    def __init__(
        self,
        fmap: FileMapCliManager,
        worker_manager: WorkerManager,
        modding_info: dict,
        parent=None,
    ):
        super().__init__(parent)

        self.fmap = fmap
        self.modding_info=modding_info
        self.worker_manager = worker_manager
        self.database = str(self.modding_info.get("database",""))
        self.mode = self.modding_info.get("mode","create")
        self.predifined_path_to_map = self.modding_info.get("path_to_map")
        self.predifined_map_name = self.modding_info.get("map_name")
        if not self.database:
            raise ValueError("Dialog requires a Database")

        self.icons = Icons()
        self.text_renderer = TextRenderer()
        self.log_buffer = MappingLogBuffer()

        self.worker = None
        self.progress = None
        self.mapping_running = False
        self.target_dbmap_pair = (None, None)

        titles = {
            "create": "New Mapping",
            "deepening": "Shallow to Deep",
            "repeated": "Find Repeated Files",
            "duplicates": "Find Duplicate Files",
            "update": "Update",
            "continue": "Continue Mapping",
        }

        self.setWindowTitle(titles.get(self.mode, "*** Mapping ***"))
        
        self.setMinimumSize(800, 600)
        self.setWindowFlags( QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowMaximizeButtonHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
        )

        self._create_ui()

        self.log_timer = QtCore.QTimer(self)
        self.log_timer.timeout.connect(self._flush_mapping_log)
        self.log_timer.start(self.LOG_FLUSH_INTERVAL)
        messages = {
            "create": "Ready to start Mapping...",
            "deepening": "Ready for converting shallow to deep...",
            "repeated": ("Ready to find Repeated Files:\n "
                            "Repeated are the files in different folders, "
                            "with the same md5 sum."),
            "duplicates": ("Ready to find Duplicate Files:\n "
                            "Duplicates are the files in the same folder, "
                            "with different file names but with the same md5 sum."),
            "update": "Ready for updating map...",
            "continue": "Ready to continue incomplete mapping...",
        }
        message = messages.get(
            self.mode, "*** mapping *** >> Mode missing")
        
        self._append_status("[cyan]" + "+" * 33 + "[/cyan]")
        self._append_status(f"[cyan]{message}[/cyan]")
        self._append_status("[cyan]" + "+" * 33 + "[/cyan]")
            

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    def _create_ui(self):

        the_db = self.fmap.fm.extract_filename(self.database)

        # Header
        header= QtWidgets.QHBoxLayout()
        icon = QtWidgets.QLabel()
        mode_ui = {
            "create": ("mapping",f"New Mapping for Database: {the_db}"),
            "deepening": ("shallow", f"Deepening @ Database: {the_db}"),
            "repeated": ("find repeated", f"Repeated @ Database: {the_db}"),
            "duplicates": ("find duplicates", f"Duplicates @ Database: {the_db}"),
            "update": ("update map", f"Updating @ Database: {the_db}"),
            "continue": ("continue mapping", f"Continue Mapping @ Database: {the_db}"),
        }

        icon_name, title_text = mode_ui.get(self.mode,
            ("mapping",f"New Mapping for Database: {the_db}"))

        icon.setPixmap(self.icons.icon(icon_name).pixmap(32, 32))
        title = QtWidgets.QLabel(title_text)

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

        table_label = QtWidgets.QLabel("Table name:")

        self.table_name_edit = QtWidgets.QLineEdit()
        if not self.predifined_map_name:
            self.table_name_edit.setPlaceholderText("Enter table name")
            self.table_name_edit.setToolTip(
                "Special characters will be replaced: "
                "% (Date_Time), # (Date), ? (Time), "
                "& (Dir), ! (Full_Path)"
            )
        else:
            self.table_name_edit.setText(self.predifined_map_name)
            self.table_name_edit.setEnabled(False)

        path_label = QtWidgets.QLabel("Path:")

        self.path_edit = QtWidgets.QLineEdit()
        if not self.predifined_path_to_map:
            self.path_edit.setPlaceholderText("Select folder to map")
        else:
            self.path_edit.setText(self.predifined_path_to_map)
            self.path_edit.setEnabled(False)

        self.browse_button = QtWidgets.QPushButton("Browse...")
        self.browse_button.setIcon(self.icons.icon("search folder"))
        if not self.predifined_path_to_map:
            self.browse_button.clicked.connect(self.browse_folder)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.path_edit,1)
        path_layout.addWidget(self.browse_button)

        # -------------------------------------------------
        # Progress
        # -------------------------------------------------

        self.progress_container = QtWidgets.QWidget()
        self.progress_layout = QtWidgets.QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)

        # -------------------------------------------------
        # Output
        # -------------------------------------------------

        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)
        self.output.setUndoRedoEnabled(False)

        # This is important.
        # Qt will discard old blocks automatically.
        self.output.document().setMaximumBlockCount(self.MAX_LOG_LINES)

        self.output.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)

        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #111111;
                color: #dddddd;
                font-family: Consolas, "Courier New", monospace;
                font-size: 10pt;
            }
        """)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------
        what = {
            "create": "Mapping",
            "deepening": "Deepening",
            "repeated": "Finding Reps",
            "duplicates": "Finding Dups",
            "update": "Updating",
            "continue": "Re-Mapping",
        }.get(self.mode, "")

        self.start_button = QtWidgets.QPushButton(f"Start {what}")
        self.start_button.setIcon(self.icons.icon("play"))

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setIcon(self.icons.icon("stop"))

        self.shallow_chkb = QtWidgets.QCheckBox("Shallow Map")
        self.shallow_chkb.setIcon(self.icons.icon("shallow"))
        if self.mode not in ["create", "continue"]:
            self.shallow_chkb.setHidden(True)

        self.stop_button.setEnabled(False)

        mode_actions = {
            "create": (self.start_mapping, self.stop_mapping),
            "deepening": (self.start_deepening, self.stop_deepening),
            "repeated": (self.start_repeated, self.stop_repeated),
            "duplicates": (self.start_duplicates, self.stop_duplicates),
            "update": (self.start_updating, self.stop_updating),
            "continue": (self.start_continueing, self.stop_continueing),
        }

        actions = mode_actions.get(self.mode)

        if actions:
            start_action, stop_action = actions
            self.start_button.clicked.connect(start_action)
            self.stop_button.clicked.connect(stop_action)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.shallow_chkb)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

        layout = QtWidgets.QVBoxLayout(self)

        layout.addLayout(header)

        layout.addWidget(table_label)
        layout.addWidget(self.table_name_edit)

        layout.addWidget(path_label)
        layout.addLayout(path_layout)

        layout.addWidget(self.progress_container)
        layout.addWidget(self.output,1)
        layout.addLayout(button_layout)

    # -----------------------------------------------------
    # Folder selection
    # -----------------------------------------------------

    @QtCore.pyqtSlot()
    def browse_folder(self):

        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Map",
            self.path_edit.text() or "",
        )

        if path:
            self.path_edit.setText(path)

    # -----------------------------------------------------
    # Mapping
    # -----------------------------------------------------
    def start_mapping(self):
        self._start_mapping(self.mode)

    def _start_mapping(self,mode="create"):
        self._text_format()
        table_name = (self.table_name_edit.text().strip())

        if not table_name:
            QtWidgets.QMessageBox.warning(
                self,
                "Missing Table Name",
                "Please enter a table name.",
            )
            return
        if mode == "create":
            # validate new names only
            is_ok, msg = self.fmap.map_validation(self.database, table_name)
        else:
            is_ok = True
            msg=""

        if not is_ok:
            QtWidgets.QMessageBox.warning(self, msg, 
                    "Please enter a valid table name.")
            return

        path_to_map = (self.path_edit.text().strip())

        if not path_to_map:
            QtWidgets.QMessageBox.warning(self,
                "Missing Path", "Please select a folder to map.",)
            return

        file_exist, is_file = (
            self.fmap.fm.validate_path_file(path_to_map))

        if file_exist and is_file:
            path_to_map = (self.fmap.fm.extract_path(path_to_map))

            file_exist, is_file = (
                self.fmap.fm.validate_path_file(path_to_map))

        if not file_exist:
            QtWidgets.QMessageBox.warning(self,
                "Invalid Path",
                "The selected folder does not exist.")
            return

        self._start_ui()
        self.target_dbmap_pair = (self.database, table_name)

        worker_actions = {
            "create": self.start_create_worker,
            "deepening": self.start_deepening_worker,
            "repeated": self.start_repeated_worker,
            "duplicates": self.start_duplicates_worker,
            # "update": self.start_update_worker,
            # "continue": self.start_continue_worker,
        }

        worker_action = worker_actions.get(mode)

        if worker_action:
            worker_action(table_name, path_to_map)

    def start_create_worker(self, table_name, path_to_map):
        self.mapping_is_running_signal.emit()

        self.progress = QtMapProgress()
        self.progress_layout.addWidget(self.progress)

        self.mapping_running = True
        is_shallow = self.shallow_chkb.isChecked()

        # self.log_timer = QtCore.QTimer(self)
        # self.log_timer.timeout.connect(self._flush_mapping_log)
        # self.log_timer.start(100)

        self.worker = self.worker_manager.start(
            self.fmap.create_new_map,
            self.database,
            table_name,
            path_to_map,
            log_print=True,
            progress_bar=self.progress,
            shallow_map=is_shallow,
            press_to_continue=False,
            log_callback=self.log_buffer.write
        )

        self.worker.finished.connect(self.on_mapping_finished)
        self.worker.stopped.connect(self.on_mapping_stopped)
        self.worker.error.connect(self.on_mapping_error)

    # -----------------------------------------------------
    # Repeated and Duplicates
    # -----------------------------------------------------
    def start_repeated(self):
        self._start_mapping(self.mode)
    
    def start_duplicates(self):
        self._start_mapping(self.mode)
    
    def start_repeated_worker(self, table_name, path_to_map):
        return
        self.mapping_is_running_signal.emit()

        self.progress = QtMapProgress()
        self.progress_layout.addWidget(self.progress)

        self.mapping_running = True

        self.worker = self.worker_manager.start(
            self.fmap.deepen_shallow_map,
            self.database,
            table_name,
            path_to_map,
            progress_bar=self.progress,
            press_to_continue=False,
            log_callback=self.log_buffer.write
        ) # kill_ev added by worker_manager

        self.worker.finished.connect(self.on_deepening_finished)
        self.worker.stopped.connect(self.on_deepening_stopped)
        self.worker.error.connect(self.on_deepening_error)
    
    def start_duplicates_worker(self, table_name, path_to_map):
        return
        self.mapping_is_running_signal.emit()

        self.progress = QtMapProgress()
        self.progress_layout.addWidget(self.progress)

        self.mapping_running = True

        self.worker = self.worker_manager.start(
            self.fmap.deepen_shallow_map,
            self.database,
            table_name,
            path_to_map,
            progress_bar=self.progress,
            press_to_continue=False,
            log_callback=self.log_buffer.write
        ) # kill_ev added by worker_manager

        self.worker.finished.connect(self.on_deepening_finished)
        self.worker.stopped.connect(self.on_deepening_stopped)
        self.worker.error.connect(self.on_deepening_error)
    # -----------------------------------------------------
    # Deepening
    # -----------------------------------------------------
    def start_deepening(self):
        self._start_mapping(self.mode)

    def start_deepening_worker(self, table_name, path_to_map):
        self.mapping_is_running_signal.emit()

        self.progress = QtMapProgress()
        self.progress_layout.addWidget(self.progress)

        self.mapping_running = True

        self.worker = self.worker_manager.start(
            self.fmap.deepen_shallow_map,
            self.database,
            table_name,
            path_to_map,
            progress_bar=self.progress,
            press_to_continue=False,
            log_callback=self.log_buffer.write
        ) # kill_ev added by worker_manager

        self.worker.finished.connect(self.on_deepening_finished)
        self.worker.stopped.connect(self.on_deepening_stopped)
        self.worker.error.connect(self.on_deepening_error)


    # -----------------------------------------------------
    # Updating
    # -----------------------------------------------------
    def start_updating(self):
        self._start_mapping(self.mode)

    # -----------------------------------------------------
    # Continue Mapping
    # -----------------------------------------------------
    def start_continueing(self):
        self._start_mapping(self.mode)

    # -----------------------------------------------------
    # Mapping log
    # -----------------------------------------------------

    def _flush_mapping_log(self):
        messages = self.log_buffer.drain(self.LOG_BATCH_SIZE)
        if not messages:
            return
        scrollbar = self.output.verticalScrollBar()
        at_bottom = (scrollbar.value() >= scrollbar.maximum() - 5)

        cursor = self.output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)

        for message in messages:
            html = self.text_renderer.to_html(message.rstrip("\n"))
            cursor.insertHtml(html)
            cursor.insertBlock()

        self.output.setTextCursor(cursor)

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        
    def _append_status(self, *args, sep=" ", end="\n"):
        message = sep.join(str(arg) for arg in args)

        if not message:
            return
        message = message.rstrip(end)
        self.log_buffer.write(message)

    # -----------------------------------------------------
    # UI state
    # -----------------------------------------------------

    def _start_ui(self):
        self.table_name_edit.setEnabled(False)
        self.path_edit.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def _mapping_finished(self):
        self.mapping_running = False
        if not self.predifined_map_name:
            self.table_name_edit.setEnabled(True)
        if not self.predifined_path_to_map:
            self.path_edit.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stop")
        self.mapping_is_not_running_signal.emit()

    # -----------------------------------------------------
    # Stop
    # -----------------------------------------------------

    def stop_mapping(self):
        if self.worker is None:
            return
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stopping...")
        self.worker.stop()
    
    def stop_updating(self):
        self.stop_mapping()

    def stop_deepening(self):
        self.stop_mapping()
        
    def stop_continueing(self):
        self.stop_mapping()

    def stop_repeated(self):
        self.stop_mapping()
    
    def stop_duplicates(self):
        self.stop_mapping()

    # -----------------------------------------------------
    # Worker callbacks
    # -----------------------------------------------------
    @QtCore.pyqtSlot()
    def on_mapping_stopped(self):
        self._append_status("[yellow]Mapping worker stopped[/yellow]")
        self._flush_mapping_log()
        try:
            self._commit_mapping()
        except Exception as exc:
            self.on_mapping_error(exc)
            return
        self._mapping_finished()

    @QtCore.pyqtSlot(object)
    def on_mapping_error(self, error):
        self._append_status(f"[red]Mapping error: {error}[/red]")
        self._flush_mapping_log()
        self._mapping_finished()

    @QtCore.pyqtSlot(object)
    def on_mapping_finished(self, result=None):
        try:
            self._commit_mapping()
        except Exception as exc:
            self.on_mapping_error(exc)
            return
        self._flush_mapping_log()
        self._mapping_finished()
    
    @QtCore.pyqtSlot()
    def on_deepening_stopped(self):
        self._append_status("[yellow]Mapping worker stopped[/yellow]")
        self._commit_deepening()
        self._mapping_finished()

    @QtCore.pyqtSlot(object)
    def on_deepening_error(self, error):
        self._append_status(f"[red]Mapping error: {error}[/red]")
        self._flush_mapping_log()
        self._mapping_finished()

    @QtCore.pyqtSlot(object)
    def on_deepening_finished(self, result=None):
        msg="[yellow]Deepening: [/yellow]"
        replaced=False
        if isinstance(result,tuple) and len(result)==3:
            msg += "\n"+self.mark_txt(f"is_ok: {result[0]}",result[0])
            msg += "\n"+self.mark_txt(f"is_finished: {result[1]}",result[1])
            msg += "\n"+self.mark_txt(f"replaced: {result[2]}",result[2])
            finished = result[1]
            replaced = result[2]
        self._append_status(msg)
        #if replaced:
        self._commit_deepening()
        self._flush_mapping_log()
        self._mapping_finished()

    # -----------------------------------------------------
    # Commit temporary database
    # -----------------------------------------------------

    def _commit_mapping(self):
        temp_db, temp_map = (self.fmap.mapping_to_pair)
        target_db, target_map = (self.target_dbmap_pair)

        if not all((temp_db, temp_map, target_db, target_map)):
            raise RuntimeError(
                "Mapping completed but mapping pair "
                "information is missing.")

        was_copied=self.fmap.copy_table_from_to_database(
            temp_db, temp_map, target_db, target_map)
        self._append_status(f"Map was copied: {was_copied} \n from {temp_db} \n to {target_db}")
        if was_copied:
            self._append_status("[yellow]Deleting Temporal database")
            # for privacy dont keep temporal maps
            self.fmap.delete_temporal_database()    
        self.fmap.set_active_databases_in_dbm()
        self.refresh_mapping_tree.emit()
    
    def _commit_deepening(self):        
        temp_db, temp_map = (self.fmap.mapping_to_pair)
        target_db, target_map = (self.target_dbmap_pair)
        was_replaced=self.fmap.replace_map_from_temporal_db(self.target_dbmap_pair,
                log_callback=self.log_buffer.write)

        if not all((temp_db, temp_map, target_db, target_map)):
            raise RuntimeError(
                "Deepening completed but mapping pair "
                "information is missing.")

        msg = self.mark_color("Map was deepened and replaced: ","yellow")
        msg += f"{self.mark_txt(str(was_replaced),was_replaced)} \n" 
        msg += f"from {temp_db} \n to {target_db}"
        self._append_status(msg)

        if was_replaced:
            self._append_status("[yellow]Deleting Temporal database")
            # for privacy dont keep temporal maps
            self.fmap.delete_temporal_database()    
        self.fmap.set_active_databases_in_dbm()
        self.refresh_mapping_tree.emit()

    # -----------------------------------------------------
    # Table formatting
    # -----------------------------------------------------

    def _text_format(self):
        table_name = (self.table_name_edit.text())

        path_to_map = (self.path_edit.text())

        if not path_to_map or not table_name:
            return

        new_table_name = (
            self.fmap.cma.format_new_table_name(
                table_name,
                path_to_map,
            )
        )
        self.table_name_edit.blockSignals(True)
        self.table_name_edit.setText(new_table_name)
        self.table_name_edit.blockSignals(False)

    # -----------------------------------------------------
    # Close
    # -----------------------------------------------------

    def closeEvent(self, event):

        if self.mapping_running:
            QtWidgets.QMessageBox.information(
                self,
                "Mapping in progress",
                "Stop the mapping before closing "
                "this window.",
            )
            event.ignore()
            return
        self.dialog_exit.emit(self.database)
        if self.log_timer.isActive():
            self.log_timer.stop()
            
        event.accept()
    @staticmethod
    def mark_txt(txt:str,val:bool):
        if val:
            return f"[green]{txt}[/green]"
        return f"[red]{txt}[/red]"
    
    @staticmethod
    def mark_color(txt:str,color:str):
        return f"[{color}]{txt}[/{color}]"


class MappingLogBuffer:
    def __init__(self):

        self._queue = deque()
        self._lock = threading.Lock()

    def write(self,*args, sep=" "):
        message = sep.join(str(arg) for arg in args)
        if not message:
            return
        with self._lock:
            self._queue.append(message)

    def drain(self, maximum=100):
        with self._lock:
            count = min(maximum, len(self._queue))
            return [self._queue.popleft() for _ in range(count)]

