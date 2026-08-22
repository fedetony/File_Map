
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer
from widgets.class_explorer_tree_widget import *

from models.class_provider_engine import DefaultProviderEngine, FM
from models.class_action_provider import DefaultFileActionProvider
from models.class_style_provider import *
from models.class_lazy_loader import *

class SelectionDialogSetter:
    """Sets the configuration for the selection dialog
    """
    def __init__(self, 
                 fmap:FileMapCliManager, 
                 worker_manager: WorkerManager,
                 modding_info:dict,
                 lazy_defaults:dict = None,
                 styles_dict:dict = None, # To include other styles later
                 parent =None
                 ):
        # modding_info={"database": "Test DB",
        #             "mode":"FESelection",
        #             "path_to_map":"",
        #             "map_name":"",
        #             }
        self.fmap = fmap
        self.worker_manager = worker_manager
        self.modding_info = modding_info
        self.lazy_defaults = lazy_defaults
        self.styles_dict = styles_dict
        self.parent = parent
        self.config = None
        self.dlg = None

        mode=modding_info.get("mode")
        if mode == "FESelection":
            self._set_fe_mode_config()
        elif  mode == "DBSelection":   
            self._set_db_mode_config()

            
            
            # raise AttributeError("Mode not supported!")
        if not isinstance(self.config,ExplorerConfig):
            return
        
        if not isinstance(self.config.explorer_style,TreeStyle):
                self.config.explorer_style = DefaultExplorerStyle() # text, tooltips, icons
        if not isinstance(self.config.tree_style,TreeStyleProvider):
            self.config.tree_style = DefaultTreeStyle() # role formatting by node, treemanager

        self.dlg = SelectionDialog(fmap=self.fmap,
                                   worker_manager=self.worker_manager,
                                   modding_info=self.modding_info,
                                   explorer_config=self.config,
                                   parent=self.parent
                                   )
        
    def _set_db_mode_config(self):
        virtual_root = TreeNode("Database Explorer")
        virtual_root.loaded = True
        virtual_root.i_am = "root"
        db_list = self.fmap.get_active_databases_in_dbm()

        for idx, db in enumerate(db_list):
            if not db.active:
                continue
            # Load databases
            db_node = TreeNode(f"{idx} {db.name}")
            db_node.i_am = "database"
            db_filepath=str(db.database_filepath)
            db_node.path = "" # do not add to path
            db_node.db = db_filepath
            db_node.i_exist=True
            db_node.map = None
            db_node.info = db_filepath
            db_node.loaded = True
            virtual_root.add_child(db_node)
            maps_in_db=self.fmap.get_maps_in_db(db_filepath)
            # Load maps
            for a_map in maps_in_db:
                map_node = TreeNode(a_map)
                map_node.i_am = "map"
                map_full_path = self.fmap.get_full_mount_path_of_map(db_filepath,a_map) 
                map_node.path = self.fmap.get_mount_of_map(db_filepath,a_map) 
                map_node.info = (db_filepath,a_map)
                map_node.loaded = False
                map_node.db = db_filepath
                map_node.i_exist=True
                db_node.map = a_map
                db_node.add_child(map_node)
                self._add_db_map_children(map_node,map_node.path,map_full_path)
                

        config = ExplorerConfig()
        # Basic
        config.root_node = virtual_root
        # 
        config.show_path_edit = True
        config.show_context_menu = True
        # Mode selection
        config.selection_by_type_mode = SelectionByTypeMode.FILES_DIRS_ONLY
        config.checkbox_mode = CheckBoxMode.CHECKBOX
        config.selection_mode = SelectionMode.MULTI
        # You must pass lazy_loader, providers and styles in agreement to Mode selection
        lazy_class = DatabaseLazyLoader()
        lazy_class.set_filemap(self.fmap)
        # initial settings
        lazy_defaults=self.lazy_defaults 
        if not isinstance(lazy_defaults,dict):
            lazy_defaults = {}
        lazy_class.set_defaults(lazy_defaults.get("defaults",[]))
        lazy_class.set_hidden(lazy_defaults.get("hidden",[]))
        lazy_class.set_blank(lazy_defaults.get("blank",[]))
        lazy_class.set_locked(lazy_defaults.get("locked",[]))

        config.lazy_loader = lazy_class
        config.provider = DefaultProviderEngine() # functions for behavior
        config.action_provider = DefaultFileActionProvider() # menu, shortcuts, global shortcuts
        styles_dict=self.styles_dict
        if not isinstance(styles_dict,dict):
            styles_dict={}
        config.explorer_style = styles_dict.get("explorer_style",DefaultExplorerStyle()) # text, tooltips, icons
        config.tree_style = styles_dict.get("tree_style",DefaultTreeStyle()) # role formatting by node, treemanager
        self.config = config

    def _add_db_map_children(self,map_node:TreeNode,mount,full_path):    
        path_list=self.fmap.fm.path_to_list(full_path)
        if mount not in ["/","\\",os.sep]:
            # Remove the mount is included on map_node.path
            path_list=path_list[1:]
        p_node=map_node
        for iii,a_dir in enumerate(path_list):
            p_node.loaded=True
            ch_node=TreeNode(a_dir)
            ch_node.i_am ="dir"
            ch_node.db = p_node.db
            ch_node.path = os.path.join(p_node.path,a_dir)
            ch_node.i_exist = os.path.exists(ch_node.path)
            ch_node.map = p_node.map
            ch_node.loaded=False
            ch_node.locked=True
            # Dont expand the last path else it loads the first files and folders for all maps
            if iii<len(path_list)-1:
                ch_node.expand=True
            p_node.add_child(ch_node)
            # Next iteration
            p_node = ch_node

            


    def _set_fe_mode_config(self):

        virtual_root = TreeNode("File Explorer")
        virtual_root.loaded = True
        virtual_root.i_am = "root"
        mounted_list = self.fmap.device_monitor.devices
        
        for mountpoint, serial in mounted_list:
            nmount=os.path.normpath(mountpoint)
            drive = TreeNode(nmount)
            drive.i_am = "dir"
            drive.path = nmount
            drive.loaded = False
            virtual_root.add_child(drive)

        config = ExplorerConfig()
        # Basic
        config.root_node = virtual_root
        # 
        config.show_path_edit = True
        config.show_context_menu = True
        # Mode selection
        config.selection_by_type_mode = SelectionByTypeMode.FILES_DIRS_ONLY
        config.checkbox_mode = CheckBoxMode.CHECKBOX
        config.selection_mode = SelectionMode.MULTI
        # You must pass lazy_loader, providers and styles in agreement to Mode selection
        lazy_class = ActiveFELazyLoader()
        # initial settings
        lazy_defaults=self.lazy_defaults 
        if not isinstance(lazy_defaults,dict):
            lazy_defaults = {}
        lazy_class.set_defaults(lazy_defaults.get("defaults",[]))
        lazy_class.set_hidden(lazy_defaults.get("hidden",[]))
        lazy_class.set_blank(lazy_defaults.get("blank",[]))
        lazy_class.set_locked(lazy_defaults.get("locked",[]))

        config.lazy_loader = lazy_class
        config.provider = DefaultProviderEngine() # functions for behavior
        config.action_provider = DefaultFileActionProvider() # menu, shortcuts, global shortcuts
        styles_dict=self.styles_dict
        if not isinstance(styles_dict,dict):
            styles_dict={}
        config.explorer_style = styles_dict.get("explorer_style",DefaultExplorerStyle()) # text, tooltips, icons
        config.tree_style = styles_dict.get("tree_style",DefaultTreeStyle()) # role formatting by node, treemanager
        self.config = config

    
    def get_dialog(self):
        return self.dlg
        


class SelectionDialog(QtWidgets.QDialog):

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
        explorer_config: ExplorerConfig,
        parent=None,
    ):
        super().__init__(parent)
        self.explorer_config=explorer_config
        self.fmap = fmap
        self.modding_info=modding_info
        self.worker_manager = worker_manager
        self.database = str(self.modding_info.get("database",""))
        self.mode = self.modding_info.get("mode","FESelection")
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
            "FESelection": "File Explorer Selection Mapping",
            "DBSelection": "Database Selection Mapping",
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
            "FESelection": "Ready to start Mapping selection...",
            "DBSelection": "Ready for selected Mapping...",
        }
        message = messages.get(
            self.mode, "*** mapping *** >> Mode missing")
        
        self._append_status("[cyan]" + "+" * 33 + "[/cyan]")
        self._append_status(f"[cyan]{message}[/cyan]")
        self._append_status("[cyan]" + "+" * 33 + "[/cyan]")
        
        self.resize(1500, 950)
            

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    def _create_ui(self):

        the_db = self.fmap.fm.extract_filename(self.database)
        
        # Header

        header= QtWidgets.QHBoxLayout()
        icon = QtWidgets.QLabel()
        
        mode_ui = {
            "FESelection": ("selection map",f"Selection from Active Files to Database: {the_db}"),
            "DBSelection": ("db activate", f"Selection from Map to Database: {the_db}"),
        }

        icon_name, title_text = mode_ui.get(self.mode,
            ("selection map",f"Selection Mapping: {the_db}"))

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
        ##################################
        # Explorer widget
        ##################################
        self.fexp_widget = ExplorerTreeWidget(self.explorer_config)

        ##################################
        # Selected Treeview widget
        ##################################
        self.s_m_tv =QTreeView()

        ##################################
        # Processing widget
        ##################################
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
            "FESelection": "FE Selection",
            "DBSelection": "DB Selection",
            
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
            "FESelection": (self.start_fe_selection, self.stop_fe_selection),
            "FESelection": (self.start_db_selection, self.stop_db_selection),
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

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(header)

        # -------------------------------------------------
        # Top area
        # -------------------------------------------------

        top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        top_splitter.addWidget(self.fexp_widget)
        top_splitter.addWidget(self.s_m_tv)

        # Explorer / Mapping ratio
        top_splitter.setSizes([350, 1150])

        # -------------------------------------------------
        # Processing area
        # -------------------------------------------------

        processing_widget = QtWidgets.QWidget()
        processing_layout = QtWidgets.QVBoxLayout(processing_widget)

        processing_layout.addWidget(table_label)
        processing_layout.addWidget(self.table_name_edit)

        processing_layout.addWidget(path_label)
        processing_layout.addLayout(path_layout)

        processing_layout.addWidget(self.progress_container)

        # Let log consume most available space
        processing_layout.addWidget(self.output, 1)

        processing_layout.addLayout(button_layout)

        # -------------------------------------------------
        # Main vertical splitter
        # -------------------------------------------------

        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(processing_widget)

        # Top 60%, Bottom 40%
        main_splitter.setSizes([600, 350])

        main_layout.addWidget(main_splitter, 1)

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
            #momcomment is_ok, msg = self.fmap.map_validation(self.database, table_name)
            is_ok =True #momcomment 
            msg="" #momcomment 
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
        
        """ #momcomment 
        file_exist, is_file = (
            self.fmap.fm.validate_path_file(path_to_map))

        if file_exist and is_file:
            path_to_map = (self.fmap.fm.extract_path(path_to_map))

            file_exist, is_file = (
                self.fmap.fm.validate_path_file(path_to_map))
        #momcomment """
        file_exist=True #momcomment 
        if not file_exist:
            QtWidgets.QMessageBox.warning(self,
                "Invalid Path",
                "The selected folder does not exist.")
            return

        self._start_ui()
        self.target_dbmap_pair = (self.database, table_name)

        worker_actions = {
            "FESelection": self.start_fe_selection_worker,
            "DBSelection": self.start_db_selection_worker,
            
        }

        worker_action = worker_actions.get(mode)

        if worker_action:
            worker_action(table_name, path_to_map)

    def start_fe_selection_worker(self, table_name, path_to_map):
        pass

    def start_db_selection_worker(self, table_name, path_to_map):
        pass

    def start_create_worker(self, table_name, path_to_map):
        return #momcomment 
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
    # Deepening
    # -----------------------------------------------------
    def start_deepening(self):
        self._start_mapping(self.mode)

    def start_deepening_worker(self, table_name, path_to_map):
        return #momcomment 
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
    def start_fe_selection(self):
        self._start_mapping(self.mode)

    # -----------------------------------------------------
    # Continue Mapping
    # -----------------------------------------------------
    def start_db_selection(self):
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
    
    def stop_fe_selection(self):
        self.stop_mapping()

    def stop_deepening(self):
        self.stop_mapping()
        
    def stop_db_selection(self):
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
        return #momcomment 
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
        return #momcomment   
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

