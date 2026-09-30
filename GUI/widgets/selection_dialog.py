
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading
from dataclasses import fields

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer
from widgets.class_explorer_tree_widget import *
from widgets.class_selection_menu import SelectionMenu
from widgets.class_simple_target_widget import *

from models.class_provider_engine import DefaultProviderEngine, FM
from models.class_action_provider import DefaultFileActionProvider
from models.class_style_provider import *
from models.class_lazy_loader import *
from functional.class_text_exporter import TableTextExporter
from widgets.class_file_dialogs import MsgBoxHelper, QMessageBox
from class_file_mapper import MapType

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
            db_node.i_exist = db.active
            db_node.map = None
            db_node.info = db_filepath
            db_node.loaded = True
            virtual_root.add_child(db_node)
            maps_in_db=self.fmap.get_maps_in_db(db_filepath)
            # Load maps
            for a_map in maps_in_db:
                mount,serial = self.fmap.get_mount_serial_of_map(db_filepath,a_map) 
                map_node = TreeNode(f"{a_map} @ ({mount})")
                map_node.i_am = "map"
                map_full_path = self.fmap.get_full_mount_path_of_map(db_filepath,a_map) 
                map_node.path = mount
                map_node.info = (db_filepath,a_map)
                map_node.loaded = False
                map_node.db = db_filepath
                map_node.i_exist=self.fmap.is_mount_serial_active(mount,serial)
                map_node.map = a_map
                db_node.add_child(map_node)
                self._add_db_map_children(map_node,map_node.path,map_full_path)

        config = ExplorerConfig()
        # Basic
        config.root_node = virtual_root
        # 
        config.show_path_edit = False
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
        multiple_folders=self.modding_info.get("multiple_folders")
        # Single folder level
        p_node=map_node
        if not multiple_folders:
            ch_path=self.fmap.fm.remove_mount_from_path(mount,full_path)
            p_node.loaded=True
            ch_node=TreeNode(ch_path)
            ch_node.i_am ="dir"
            ch_node.db = p_node.db
            ch_node.path = full_path
            ch_node.i_exist = os.path.exists(full_path)
            ch_node.map = p_node.map
            ch_node.loaded=False
            ch_node.locked=True
            p_node.add_child(ch_node)
            return
        
        # Multiple folder levels loading
        path_list=self.fmap.fm.path_to_list(full_path)
        if mount not in ["/","\\",os.sep]:
            # Remove the mount is included on map_node.path
            path_list=path_list[1:]
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
        self._lazy_loading = False

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
        self.fexp_widget.userSelectionChanged.connect(self.on_selection_changed)
        self.fexp_widget.actionEvaluated.connect(self.on_action_evaluated)
        self.fexp_widget.lazyLoading.connect(self.on_lazy_loading)

        ##################################
        # Selected Treeview widget
        ##################################
        self.s_m_tv =QTreeView()
        self.sel_menu=SelectionMenu(self.fmap,self.s_m_tv,self)
        self.sel_menu.target_items_changed.connect(self._new_targets_selected)
        self.sel_menu.set_end_database(self.database)

        ##################################
        # Target widget
        ##################################
        self.target_widget=TargetManagerWidget(self.fmap,target_type="map")
        #self.target_widget=MapTargetManagerWidget(self.fmap)
        self.target_widget.targetChanged.connect(self._on_target_changed)

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
        if self.mode not in ["FESelection"]:
            self.shallow_chkb.setHidden(True)

        self.stop_button.setEnabled(False)

        mode_actions = {
            "FESelection": (self.start_fe_selection, self.stop_fe_selection),
            "DBSelection": (self.start_db_selection, self.stop_db_selection),
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

        processing_layout.addWidget(self.target_widget)
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
    
    def get_sorted_selected_nodes(self):
        selected_nodes_list=self.fexp_widget.selected_nodes()
        sorted_nodes={}
        for node in selected_nodes_list:
            ms=(node.mount,node.serial)
            a_node_list=sorted_nodes.get(ms,[])
            a_node_list.append(node)
            sorted_nodes.update({ms:a_node_list})
        return sorted_nodes


    def _start_mapping(self,mode="create"):
        target_list=self.target_widget.get_valid_target_list()
        if not target_list:
            QtWidgets.QMessageBox.warning(
                self,
                "Missing Targets",
                "Please enter a valid targets to make a map.",
            )
            return
        target_full={}
        sorted_nodes=self.get_sorted_selected_nodes()
        for target in target_list:
            t_ms=(target.source_mount,target.source_serial)
            for ms,node_list in sorted_nodes.items():
                if t_ms == ms:
                    target_full[ms]=(target,node_list)
                    break

        for ms, (a_target,a_node_list) in target_full.items():
            if not isinstance(a_target,MapTargetItem):
                continue
            database = self.target_widget.database_ref.get(a_target.target_database)
            a_map = a_target.target_map_name
            target_db_map_pair=(database,a_map)

            is_ok, msg = self.fmap.map_validation(database,a_map)
            if not is_ok:
                QtWidgets.QMessageBox.warning(self, msg, 
                        "Please enter a valid table name.")
                return

        self._start_ui()

        worker_actions = {
            "FESelection": self.start_fe_selection_worker,
            "DBSelection": self.start_db_selection_worker,
            
        }

        worker_action = worker_actions.get(mode)

        if worker_action:
            worker_action(target_full)
    
    
    def on_lazy_loading(self, is_loading: bool):
        """Change the mouse cursor while lazy loading is active."""
        if is_loading:
            if not self._lazy_loading:
                self._lazy_loading = True
                QtWidgets.QApplication.setOverrideCursor(
                    QtCore.Qt.CursorShape.WaitCursor
                )
        else:
            if self._lazy_loading:
                self._lazy_loading = False
                QtWidgets.QApplication.restoreOverrideCursor()



    def on_action_evaluated(self,action,result):
        """Action from action provider and result of the evaluation"""
        if action:
            # print("Got action evaluated ->",action)
            selected_nodes_list=self.fexp_widget.selected_nodes()
            self.generate_node_structure(selected_nodes_list)


    def on_selection_changed(self,changed_nodes_list:list):
        selected_nodes_list=self.fexp_widget.selected_nodes()
        self.generate_node_structure(selected_nodes_list)
    
    def generate_node_structure(self,nodes_list):
        self.fexp_widget.lazyLoading.emit(True)
        try:
            self.sel_menu.generate_selection_struct(nodes_list)
        finally:
            self.fexp_widget.lazyLoading.emit(False)
        
    def _get_path_list_from_node_list(self,node_list:list[TreeNode]):
        path_list=[]
        parent_node_list=[]
        for node in node_list:
            if node.i_am == "dir" and node.selected_children:
                parent_node_list.append(node)

        # Filter files and dirs inside tree paths    
        new_node_list:list[TreeNode]=[]
        for node in node_list:
            bl=node.get_bloodline()
            add_node=True
            # dont include yourself
            for pnode in bl[:-1]:
                if pnode in parent_node_list:
                    add_node=False
                    break
            if add_node:
                new_node_list.append(node)
                
        for node in new_node_list:
            if node.i_am == "dir":
                path_list.append(os.path.join(node.mount,node.itempath))
            elif node.i_am == "file":
                path_list.append(os.path.join(node.mount,node.itempath,node.name))
        
        return list(set(path_list))

    def start_fe_selection_worker(self, target_full: dict):
        self.mapping_is_running_signal.emit()

        self.progress = QtMapProgress()
        self.progress_layout.addWidget(self.progress)

        self.mapping_running = True
        is_shallow = self.shallow_chkb.isChecked()

        self._stop_fe_mapping = False
        self.fmap.mapping_to_pair = (None, None)

        # ------------------------------------------------------------
        # Build a queue of mapping jobs.
        #
        # IMPORTANT:
        # We do NOT start all workers here.
        # Only the first worker will be started.
        # The next worker is started from on_fe_mapping_finished().
        # ------------------------------------------------------------
        self._fe_mapping_queue = []
        for ms, (a_target, a_node_list) in target_full.items():
            if not isinstance(a_target, MapTargetItem):
                continue
            database = self.target_widget.database_ref.get(
                a_target.target_database)

            a_map = a_target.target_map_name

            target_db_map_pair = (database, a_map)

            path_list_to_map = self._get_path_list_from_node_list(
                a_node_list)

            self._fe_mapping_queue.append({
                "mount_serial_pair": ms,
                "database": database,
                "map": a_map,
                "target_db_map_pair": target_db_map_pair,
                "path_list_to_map": path_list_to_map,
                "shallow_map": is_shallow,
            })
        # Nothing to do
        if not self._fe_mapping_queue:
            self._mapping_finished()
            return
        # Start the first mapping.
        self._start_next_fe_mapping()


    @QtCore.pyqtSlot()
    def _start_next_fe_mapping(self):
        """
        Start exactly ONE FE mapping worker.

        The next worker is started only after this worker emits
        finished/stopped/error.
        """
        # Stop requested
        if self._stop_fe_mapping:
            self._mapping_finished()
            return

        # Queue exhausted
        if not self._fe_mapping_queue:
            self._mapping_finished()
            return
        # ------------------------------------------------------------
        # Get the next job
        # ------------------------------------------------------------
        job = self._fe_mapping_queue.pop(0)

        database = job["database"]
        a_map = job["map"]
        ms = job["mount_serial_pair"]
        path_list_to_map = job["path_list_to_map"]

        # Store information belonging specifically to THIS worker.
        # Do not rely on these values being updated by the next loop
        # iteration because there is no loop starting workers anymore.
        self.target_dbmap_pair = job["target_db_map_pair"]

        # Optional but useful if you want to inspect the current job.
        self._current_fe_mapping_job = job
        # ------------------------------------------------------------
        # Start worker
        # ------------------------------------------------------------
        self.worker = self.worker_manager.start(
            self.fmap.create_selection_map,
            database=database,
            mount_serial_pair_list=[ms],
            table_name_list=[a_map],
            path_list_to_map_list=[path_list_to_map],
            log_print=True,
            progress_bar=self.progress,
            shallow_map=job["shallow_map"],
            press_to_continue=False,
            log_callback=self.log_buffer.write
        )

        self.worker.finished.connect(self.on_fe_mapping_finished)
        self.worker.stopped.connect(self.on_fe_mapping_stopped)
        self.worker.error.connect(self.on_fe_mapping_error)

        # is_shallow=job["shallow_map"]
        # killtemp=threading.Event()
        # killtemp.clear()
        # self.fmap.create_selection_map(
        #     database = database,
        #     mount_serial_pair_list = [ms],
        #     table_name_list=[a_map],
        #     path_list_to_map_list=[path_list_to_map],
        #     log_print=True,
        #     progress_bar=self.progress,
        #     shallow_map=is_shallow,
        #     press_to_continue=False,
        #     log_callback=self.log_buffer.write,
        #     kill_ev=killtemp
        # )


    def start_db_selection_worker(self, target_full):
        self.mapping_is_running_signal.emit()
        self.worker = self.worker_manager.start(
            self._create_selection_maps,
            target_full=target_full,
        )

        self.worker.finished.connect(self.on_db_mapping_finished)
        self.worker.stopped.connect(self.on_db_mapping_stopped)
        self.worker.error.connect(self.on_db_mapping_error)
        # killtemp=threading.Event()
        # killtemp.clear()
        # result=self._create_selection_maps(target_full,killtemp)
        
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
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def _mapping_finished(self):
        self.mapping_running = False
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
        
    def stop_db_selection(self):
        self.stop_mapping()


    # -----------------------------------------------------
    # Worker callbacks
    # -----------------------------------------------------
    
    # general Mapping error handler
    @QtCore.pyqtSlot(object)
    def on_mapping_error(self, error):
        self._append_status(f"[red]Mapping error: {error}[/red]")
        self._flush_mapping_log()
        self._mapping_finished()
    
    # ************* db **************
    @QtCore.pyqtSlot()
    def on_db_mapping_stopped(self):
        self._append_status("[yellow]Mapping worker stopped[/yellow]")
        self._flush_mapping_log()
        try:
            self._commit_db_mapping()
        except Exception as exc:
            self.on_mapping_error(exc)
            return
        self._mapping_finished()
    
    @QtCore.pyqtSlot(object)
    def on_db_mapping_error(self, error):
        self.on_mapping_error(error)

    @QtCore.pyqtSlot(object)
    def on_db_mapping_finished(self, result=None):
        try:
            self._commit_db_mapping(result)
        except Exception as exc:
            self.on_mapping_error(exc)
            return
        self._flush_mapping_log()
        self._mapping_finished()
    
    # ************* fe ************** 

    # FE selection mapping error handler
    @QtCore.pyqtSlot(object)
    def on_fe_mapping_error(self, error):
        # Prevent the next queued FE mapping from starting.
        self._stop_fe_mapping = True
        # Clear the remaining jobs because this FE mapping sequence
        # is being aborted.
        if hasattr(self, "_fe_mapping_queue"):
            self._fe_mapping_queue.clear()
        # Use the common/general error handling.
        self.on_mapping_error(error)

    @QtCore.pyqtSlot(object)
    def on_fe_mapping_finished(self, result=None):
        msg = "[cyan]" + "*" * 33 + "[/cyan]"
        self._append_status(msg)
        self._append_status("[cyan]Finished Selection Mapping: [/cyan]")

        temp_db, temp_map = self.fmap.mapping_to_pair
        target_db, target_map = self.target_dbmap_pair

        self._append_status(f"[cyan]Tranfering from: ({temp_db}, {temp_map})[/cyan]")
        self._append_status(f"[cyan]===========> to: ({target_db}, {target_map})[/cyan]")
        self._append_status(msg)
        # Commit THIS worker before starting the next worker.
        try:
            self._commit_fe_mapping(result)
        except Exception as exc:
            self.on_mapping_error(exc)
            return

        self._flush_mapping_log()
        # Start the next mapping.
        self._start_next_fe_mapping()


    @QtCore.pyqtSlot()
    def on_fe_mapping_stopped(self):
        self._append_status(
            "[yellow]Mapping worker stopped[/yellow]"
        )
        self._flush_mapping_log()
        try:
            self._commit_fe_mapping()
        except Exception as exc:
            self.on_mapping_error(exc)
            return
        self._mapping_finished()

        # Do not start another mapping after an explicit stop.
        self._stop_fe_mapping = True


    # -----------------------------------------------------
    # Commit 
    # -----------------------------------------------------

    def _commit_db_mapping(self,result=None):
        if isinstance(result,dict):
            maps_created=result
            msgbox=MsgBoxHelper()
            if maps_created:
                #Set the correct size of new map in cache
                self.fmap.refresh_map_size_cache()
                # Ask for refresh
                self.refresh_mapping_tree.emit()

                dmsg="Maps Created:"
                for iii,db_map_pair in enumerate(maps_created):
                    dmsg+="\n"+"-"*33
                    dmsg+=f"\n{iii}\tDatabase: {db_map_pair[0]}"
                    dmsg+=f"\n{iii}\t     Map: {db_map_pair[1]}"
                dmsg+="\n"+"-"*33
                msgbox.show("Create Selection Map",
                        f"Successfully created {len(maps_created)} selection maps!",
                        icon=QMessageBox.Icon.Information,
                        buttons=None,
                        default=None,
                        detailed_text=dmsg,
                        informative_text=None,
                        )
        self.refresh_mapping_tree.emit()
    
    def _commit_fe_mapping(self,result=None):
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
    
    # -----------------------------------------------------
    # Load selection tree
    # -----------------------------------------------------
    def _load_selection_tree(self):
        """Use lazy loader to load all nodes info... takes much more time"""
        selected_nodes_list=self.fexp_widget.selected_nodes()
        for node in selected_nodes_list:
            if node.i_am == "dir":
                # Load all branch
                self.fexp_widget.load_node(node,None) 
            if node.selected:
                self.fexp_widget.t_m.select_subtree(node,node.selected)
    
    def _get_selection_ids(self,target_full:dict):
        """Get ids lists of selections"""
        id_results={}
        for ms, (a_target,a_node_list) in target_full.items():
            if not isinstance(a_target,MapTargetItem):
                continue
            # default pair
            db_map_pair = (a_target.source_db, a_target.source_map)
            fm=self.fmap.cma.get_file_map(db_map_pair[0])
            # get ids
            all_ids=[]
            all_ids_dict={}
            for node in a_node_list:
                if not isinstance(node,TreeNode):
                    continue
                if node.i_am == "file":
                    all_ids.append(node.db_id)
                    continue
                if not node.i_am == "dir":
                    continue
                if node.db and node.map:
                    # A node can come from another map use the node's db_map pair
                    if (node.db != db_map_pair[0] or node.map != db_map_pair[1]):
                        if all_ids:
                            all_ids_dict.update({db_map_pair:list(set(all_ids))})
                            all_ids=[]  
                        db_map_pair = (node.db, node.map)
                        fm=self.fmap.cma.get_file_map(db_map_pair[0])
                    if not fm:
                        continue
                    # get ids from database map
                    # remove end separator for itempath
                    itempath = node.itempath
                    if node.itempath and node.itempath[-1] in ["/", "\\", os.sep] and len(node.itempath)>1:
                        itempath = node.itempath[:-1]
                    sep = "'" + os.sep + "'" 
                    if os.sep == '/':
                        rep = "char(92)"
                    else:
                        rep = "'/'" 
                    where_files_dirs = (
                        f"replace(filepath, {rep}, {sep}) LIKE "
                        + fm.db.quotes(itempath + "%")
                    )
                    data_ids=fm.db.get_data_from_table(db_map_pair[1],'id',where_files_dirs)
                    if not data_ids:
                        continue

                    ids=[an_id[0] for an_id in data_ids]
                    all_ids+=ids
            if all_ids:
                all_ids_dict.update({db_map_pair:list(set(all_ids))})    
            if all_ids_dict:    
                id_results.update({ms:all_ids_dict.copy()})

        return id_results

    def _get_data_from_nodes(self, mount_serial_pair, 
                             id_results_dict:dict,
                             fields:list):
        """
        Build the data directly from database id selection.

        The returned rows follow the supplied database field order.
        """
        # remove id from data
        fields_proc=[]
        for fie in fields:
            if fie != "id":
                fields_proc.append('"' + fie + '"') # double quotes is identifier
        what=", ".join(fields_proc) 
        data=[]
        for ms,dbmpair_ids_dict in id_results_dict.items():
            if ms != mount_serial_pair:
                continue
            if isinstance(dbmpair_ids_dict,dict): 
                for db_map_pair,id_list in dbmpair_ids_dict.items():
                    data+=self.fmap.ba.get_data_from_id_list_batched(db_map_pair,
                                                                    id_list,
                                                                    what=what,
                                                                    batch_size=33)
        return data   


    # -----------------------------------------------------
    # Create Mapping functions
    # -----------------------------------------------------

    def _create_selection_maps(self,target_full, kill_ev:threading.Event=None):

        selected_nodes_list=self.fexp_widget.selected_nodes()
        if not selected_nodes_list:
            message="There are no selected items to Create a Map!"
            self._append_status(f"[red]{message}[/red]")
            return
        
        mount_serial_list,mount_serial_dict=self._get_mount_serial_pair(selected_nodes_list)
        if len(mount_serial_list)<1:
            message="Cant Map there is No mount serial"
            self._append_status(f"[red]{message}[/red]")
            return
        
        maps_created=[]
        target_list=self.target_widget.get_valid_target_list()
        id_results_dict=self._get_selection_ids(target_full)
        for mount_serial_pair in mount_serial_list:
            if kill_ev.is_set():
                return None
            mount,serial =mount_serial_pair
            sel_target=None
            for target in target_list:
                if mount == target.source_mount and serial==target.source_serial:
                    sel_target=target
                    break
            if not sel_target:
                message=f"No Target for mount {mount} serial {serial}"
                self._append_status(f"[red]{message}[/red]")
                continue
            if not sel_target.is_db_valid:
                message=f"No valid database for mount {mount} serial {serial}"
                self._append_status(f"[red]{message}[/red]")
                continue
            if not sel_target.is_map_valid:
                message=f"No valid map for mount {mount} serial {serial}"
                self._append_status(f"[red]{message}[/red]")
                continue

            db_to =self.target_widget.database_ref.get(sel_target.target_database)
            map_to = sel_target.target_map_name
            common_path=self._get_common_path(mount_serial_pair,mount_serial_dict)
            fm=self.fmap.cma.get_file_map(db_to)
            if not fm:
                message=f"No target Filemapper: {db_to}"
                self._append_status(f"[red]{message}[/red]")
                message= "check database is active!"
                self._append_status(f"[yellow]{message}[/yellow]")
                continue
            # route database logger
            fm.db.set_log_callback(self._append_status)
            # Destination table fields
            origin_db, origin_map = self._get_origin_from_nodes(mount_serial_pair, mount_serial_dict)
            if not origin_db or not origin_map:
                dbmappair_ids_dict=id_results_dict.get(mount_serial_pair)
                for dbmpair in dbmappair_ids_dict.keys():
                    # set first one as origin
                    (origin_db, origin_map)=dbmpair
                    break
            origin_fm=self.fmap.cma.get_file_map(origin_db)
            if not origin_fm:
                message=f"No Origin Filemapper: {origin_db}"
                self._append_status(f"[red]{message}[/red]")
                message= "check database is active!"
                self._append_status(f"[yellow]{message}[/yellow]")
                continue
            field_list = origin_fm.db.get_column_list_of_table(origin_map)
            if not field_list:
                message = f"No fieldlist for origin map {origin_map}"
                self._append_status(f"[red]{message}[/red]")
                continue
            origin_info=self.fmap.cma.get_map_info_as_dict(origin_db, origin_map)
            mappath=self.fmap.fm.remove_mount_from_path(
                origin_info['mount'], common_path,remove_start_separator=True)
            
            # Get data selected nodes                 
            data = self._get_data_from_nodes(
                mount_serial_pair, id_results_dict, field_list)
            if not data:
                message = "No data found!"
                self._append_status(f"[red]{message}[/red]")
                continue
            if kill_ev.is_set():
                return None
            #Create Selection map 
            fm.db.create_connection()
            was_indexed=fm.add_table_to_mapper_index(map_to, mappath, 
                MapType.SELECTION.value)
            if not was_indexed:
                message = f"{map_to} could not be indexed!"
                self._append_status(f"[red]{message}[/red]")
                continue
            # fix mount and serial
            was_mount_serial_set=fm.set_mount_serial_to_map(
                    map_to, origin_info['mount'],origin_info['serial'])
            if not was_mount_serial_set:
                message = (f"Failed setting mount and serial to {map_to}: "
                f"{origin_info['mount']},{origin_info['serial']}")
                self._append_status(f"[red]{message}[/red]")
                continue
            fm._create_map_in_db(map_to)
            an_id=fm.get_table_id(map_to)
            if an_id:
                was_inserted = fm.db.insert_data_to_table(map_to,data)
                if not was_inserted:
                    message=f"Failed to insert data to {map_to}"
                    self._append_status(f"[red]{message}[/red]")
                    continue
                # if db_to != origin_db:
                #     fm.set_origin_db_map(map_to,origin_db,origin_map)
                # else:
                #     # dont set origin_db if is the same database
                #     fm.set_origin_db_map(map_to,origin_map=origin_map)

                # test = fm.db.get_data_from_table(map_to,'*')
                maps_created.append((db_to,map_to))
                message=f"Successfully Created {map_to}"
                self._append_status(f"[green]{message}[/green]")
            else:
                message=f"Failed to insert data, could not find the table id for {map_to}"
                self._append_status(f"[red]{message}[/red]")
        
        return maps_created
    
   
    def _get_mount_serial_pair(self,selected_nodes_list:list[TreeNode])->list[tuple]:
        mount_serial_pair_list=[]
        mount_serial_pair_node_dict={}
        for node in selected_nodes_list:
            mount_serial_pair = (node.mount, node.serial)
            if mount_serial_pair not in mount_serial_pair_list:
                mount_serial_pair_list.append(mount_serial_pair)
            ms_p_l=mount_serial_pair_node_dict.get(mount_serial_pair,[])
            ms_p_l+=[node]
            mount_serial_pair_node_dict.update({mount_serial_pair:ms_p_l})
        return mount_serial_pair_list, mount_serial_pair_node_dict
    
    def _get_common_path(self,mount_serial_pair, mount_serial_dict:dict)->str:
        node_list=mount_serial_dict.get(mount_serial_pair,[])
        paths_list=[]
        for node in node_list:
            if isinstance(node,TreeNode):
                paths_list.append(node.path)
        if paths_list:
            return self.fmap.fm.get_common_path(paths_list)
        return ""
    
    def _get_origin_from_nodes(self, mount_serial_pair, mount_serial_dict: dict):
        """
        Get the origin map belonging to one (mount, serial) pair form Treenodes.

        Returns (origin_db,origin_map) tuple.
        """
        node_list = mount_serial_dict.get(mount_serial_pair, [])
        
        origin_db = None
        origin_map = None
        for node in node_list:
            if not isinstance(node, TreeNode):
                continue
            if node.i_am == "map":
                try:
                    (_, _, origin_db, origin_map)=self._info_db_maps(node.info)
                    return origin_db, origin_map
                except:
                    pass
            if node.i_am != "file":
                continue
            # get origins
            if origin_db is None or origin_map is None:
                bl = node.get_bloodline()
                for p_node in bl:
                    # map info retains the origin db and map
                    if p_node.i_am == "map":
                        try:
                            (_, _, origin_db, origin_map)=self._info_db_maps(p_node.info)
                            return origin_db, origin_map
                        except:
                            pass 
        return origin_db, origin_map
    
    def _info_db_maps(self,info):
        """The node's info can have one db_map pair or two. 
        If has one info comes from  origin map. If has 2 pairs then 
        is a temporal map, with a origin map as the second tuple. 
        The first tuple in info is used to build the tree, so loads the nodes 
        from positions 0 and 1.
        """
        temp_db=None
        temp_map=None
        origin_db=None
        origin_map=None
        if isinstance(info,tuple):
            if len(info) == 2:
                (origin_db, origin_map)=info
            elif len(info) == 4:
                (temp_db,temp_map,origin_db, origin_map)=info  
        return temp_db, temp_map, origin_db, origin_map 
    
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

    def _new_targets_selected(self, targets: list[MapTargetItem]):
        if self.target_widget.target_type == "map":
            self.target_widget.set_targets_to_ref(targets)

        elif self.target_widget.target_type == "file":
            new_file_list = [
                copy_shared_fields(tar, FileTargetItem())
                for tar in targets
            ]
            self.target_widget.set_targets_to_ref(new_file_list)

    def _on_target_changed(self,targets:list[MapTargetItem]):
        print(targets)


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
