# compare_dialog.py
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer
from widgets.class_explorer_tree_widget import *
from widgets.search_query_widget import *

from models.class_provider_engine import DefaultProviderEngine, FM
from models.class_action_provider import DefaultFileActionProvider
from models.class_style_provider import *
from models.class_lazy_loader import *
from controllers.class_database_manager import DatabaseInfo

from copy import deepcopy
from dataclasses import dataclass

@dataclass
class SearchResult:
    idx: int
    user_query: str
    sql_where: str
    temp_map: str
    temp_db: str
    temp_db_map_pair: tuple[str,str]
    origin_db: str
    origin_map: str
    origin_db_map_pair: tuple[str,str]
    idx_dict: dict
    matches: int = 0
    title: str = ""



class SearchDialogSetter:
    """Sets the configuration for the search dialog
    """
    def __init__(self, 
                 fmap:FileMapCliManager, 
                 db_map_pair_list:list,
                 worker_manager: WorkerManager,
                 modding_info:dict,
                 lazy_defaults:dict = None,
                 styles_dict:dict = None, # To include other styles later
                 parent =None
                 ):
        
        self.fmap = fmap
        self.worker_manager = worker_manager
        self.modding_info = modding_info
        self.lazy_defaults = lazy_defaults
        self.styles_dict = styles_dict
        self.parent = parent
        self.config = None
        self.dlg = None
        self.db_map_pair_list =db_map_pair_list

        # mode=modding_info.get("mode")
        # if mode == "Search":        
        #     self._set_db_mode_config()
        self._set_db_mode_config()
            
            # raise AttributeError("Mode not supported!")
        if not isinstance(self.config,ExplorerConfig):
            return
        
        if not isinstance(self.config.explorer_style,TreeStyle):
                self.config.explorer_style = DefaultExplorerStyle() # text, tooltips, icons
        if not isinstance(self.config.tree_style,TreeStyleProvider):
            self.config.tree_style = DefaultTreeStyle() # role formatting by node, treemanager

        self.dlg = SearchDialog(fmap=self.fmap,
                                db_map_pairs=self.db_map_pair_list,
                                worker_manager=self.worker_manager,
                                modding_info=self.modding_info,
                                explorer_config=self.config,
                                parent=self.parent,
                                )
        
    def _get_selected_dbs(self)->list[DatabaseInfo]:
        db_info_list = self.fmap.get_active_databases_in_dbm()
        db_list = []
        selected_db_info_list=[]
        for (a_db,_) in self.db_map_pair_list:
            if a_db not in db_list:
                db_list.append(a_db)
        for db in db_info_list:
            if not db.active:
                continue
            if str(db.database_filepath) not in db_list:
                continue
            selected_db_info_list.append(db)
        return selected_db_info_list
    
    def _get_selected_maps_from_db_pair(self,db:DatabaseInfo):
        selected_maps=[]
        for (a_db,a_map) in self.db_map_pair_list:
            maps_in_db=self.fmap.get_maps_in_db(a_db)
            if (a_db == str(db.database_filepath) 
                and a_map in maps_in_db):
                selected_maps.append(a_map)
        return selected_maps

    def _set_db_mode_config(self):
        virtual_root = TreeNode("Search Results")
        virtual_root.loaded = True
        virtual_root.i_am = "root"
        
        db_info_list = self._get_selected_dbs()

        for idx, db in enumerate(db_info_list):
            maps_list = self._get_selected_maps_from_db_pair(db)
            if not maps_list:
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
            # Load maps
            for a_map in maps_list:
                mount,serial = self.fmap.get_mount_serial_of_map(db_filepath,a_map) 
                map_node = TreeNode(f"{a_map} @ ({mount})")
                map_node.i_am = "map"
                # map_full_path = self.fmap.get_full_mount_path_of_map(db_filepath,a_map) 
                map_node.path = mount
                map_node.info = (db_filepath,a_map)
                map_node.loaded = False
                map_node.db = db_filepath
                map_node.i_exist=self.fmap.is_mount_serial_active(mount,serial)
                map_node.map = a_map
                db_node.add_child(map_node)
                # Children are added with results
                #self._add_db_map_children(map_node,map_node.path,map_full_path)
                
        config = ExplorerConfig()
        # Basic
        config.root_node = virtual_root
        # 
        config.show_path_edit = False
        config.show_context_menu = True
        # Mode selection
        config.selection_by_type_mode = SelectionByTypeMode.FILES_ONLY
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

    def get_dialog(self):
        return self.dlg
        
##########################################################################
##########################################################################

class SearchDialog(QtWidgets.QDialog):

    refresh_mapping_tree = QtCore.pyqtSignal()
    mapping_is_running_signal = QtCore.pyqtSignal()
    mapping_is_not_running_signal = QtCore.pyqtSignal()
    dialog_exit = QtCore.pyqtSignal(str)

    def __init__(self, 
                 fmap: FileMapCliManager ,
                 db_map_pairs: list,
                 explorer_config:ExplorerConfig,
                 worker_manager:WorkerManager,
                 modding_info=None, 
                 parent=None):
        super().__init__(parent)
        self.fmap = fmap
        self.db_map_pairs = db_map_pairs
        self.modding_info = modding_info
        self.worker_manager = worker_manager
        self.explorer_config = explorer_config
        self.icons=Icons()

        self.s_result = None # list[SearchResult]        
        self._has_been_searched=False
        self._explorer_root_node=None
        self.debug_counter=0
        self._lazy_loading = False
        
        self.db_idx_map_registry=[]

        self.setWindowTitle("Search")
        self.resize(1600, 950)

        self.build_ui()

    def build_ui(self):

        # ==============================================================
        # Query widget
        # ==============================================================

        self.search_widget = SearchQueryWidget(self.fmap,parent=self)
        self.search_widget.searchRequested.connect(self._on_search_requested)

        # ==============================================================
        # View filters
        # ==============================================================

        filter_group = QtWidgets.QGroupBox("View Filters")

        filter_layout = QtWidgets.QHBoxLayout(filter_group)

        self.show_files_cb = QtWidgets.QCheckBox("Files")
        self.show_files_cb.setChecked(True)

        self.show_folders_cb = QtWidgets.QCheckBox("Folders")
        self.show_folders_cb.setChecked(True)

        self.show_size_cb = QtWidgets.QCheckBox("Show Size")
        self.show_size_cb.setChecked(True)

        self.show_dates_cb = QtWidgets.QCheckBox("Show Dates")
        self.show_dates_cb.setChecked(False)

        self.show_md5_cb = QtWidgets.QCheckBox("Show MD5")
        self.show_md5_cb.setChecked(False)

        filter_layout.addWidget(self.show_files_cb)
        filter_layout.addWidget(self.show_folders_cb)
        filter_layout.addWidget(self.show_size_cb)
        filter_layout.addWidget(self.show_dates_cb)
        filter_layout.addWidget(self.show_md5_cb)

        # Keep filters on the left rather than stretching them
        filter_layout.addStretch(1)

        # ==============================================================
        # Results area
        # ==============================================================

        results_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal
        )

        ##################################
        # Explorer widget
        ##################################
        self.results_tree = ExplorerTreeWidget(self.explorer_config)
        # self.results_tree.userSelectionChanged.connect(self.on_selection_changed)
        # self.results_tree.actionEvaluated.connect(self.on_action_evaluated)
        self.results_tree.lazyLoading.connect(self.on_lazy_loading)

        self.properties_tree = QtWidgets.QTreeWidget()
        self.properties_tree.setHeaderLabels(
            ["Property", "Value"]
        )

        results_splitter.addWidget(self.results_tree)
        results_splitter.addWidget(self.properties_tree)

        results_splitter.setSizes([1200, 400])

        # ==============================================================
        # Statistics
        # ==============================================================

        stats_group = QtWidgets.QGroupBox("Statistics")

        stats_layout = QtWidgets.QHBoxLayout(stats_group)

        self.files_label = QtWidgets.QLabel("Files: 0")
        self.folders_label = QtWidgets.QLabel("Folders: 0")
        self.size_label = QtWidgets.QLabel("Size: 0 MB")
        self.selected_label = QtWidgets.QLabel("Selected: 0")

        stats_layout.addWidget(self.files_label)
        stats_layout.addSpacing(30)

        stats_layout.addWidget(self.folders_label)
        stats_layout.addSpacing(30)

        stats_layout.addWidget(self.size_label)
        stats_layout.addSpacing(30)

        stats_layout.addWidget(self.selected_label)

        stats_layout.addStretch(1)

        # ==============================================================
        # Action buttons
        # ==============================================================

        button_layout = QtWidgets.QHBoxLayout()

        self.selection_map_button = QtWidgets.QPushButton("Create Selection Map")

        self.export_button = QtWidgets.QPushButton("Export Tree")

        self.delete_button = QtWidgets.QPushButton("Delete")

        self.copy_button = QtWidgets.QPushButton("Copy Results")

        self.close_button = QtWidgets.QPushButton("Close")

        button_layout.addWidget(self.selection_map_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.close_button)

        # ==============================================================
        # Main layout
        # ==============================================================

        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Query widget gets the most natural amount of space
        main_layout.addWidget(self.search_widget)
        main_layout.addWidget(filter_group)

        # Results should consume all remaining vertical space
        main_layout.addWidget(results_splitter,1)
        main_layout.addWidget(stats_group)
        main_layout.addLayout(button_layout)

        # ==============================================================
        # Final sizing
        # ==============================================================

        self.results_tree.tree.setAlternatingRowColors(True)
        self.results_tree.tree.setUniformRowHeights(False)

        self.properties_tree.setAlternatingRowColors(True)

        self.close_button.clicked.connect(self.reject)
    
    def _on_search_requested(self,user_query_txt, sql_where):
        #set this to a worker
        self.search_for_(user_query_txt, sql_where)

    
    def search_for_(self, user_query_txt, sql_where):

        (temp_db, idx_map)=self.fmap.do_a_search(self.db_map_pairs,
                              sql_where,
                              log_callback=print, # set log_callback
                              )
        self.s_result=[]
        for idx,idx_dict in idx_map.items():
            s_result=self._get_search_result_obj(idx, temp_db, idx_dict , user_query_txt, sql_where)
            self.s_result.append(s_result)

        self.db_idx_map_registry.append((temp_db, idx_map , user_query_txt, sql_where))
        # do this with Qtimer oneshot
        self._load_search_results_to_tree()
    
    def _get_search_result_obj(self,idx, temp_db, idx_dict , user_query_txt, sql_where)->SearchResult:
        print(f"{idx} Search '{user_query_txt}' found {idx_dict['matches']} matches!")
        return SearchResult(idx = idx,
                            user_query = user_query_txt,
                            sql_where = sql_where,
                            idx_dict=idx_dict,
                            temp_map = idx_dict["name"],
                            temp_db = temp_db,
                            temp_db_map_pair = (temp_db, idx_dict["name"]),
                            origin_db = idx_dict["db_map_pair"][0],
                            origin_map = idx_dict["db_map_pair"][1],
                            origin_db_map_pair = idx_dict["db_map_pair"],
                            matches = idx_dict["matches"],
                            )
    


    def _get_db_info_obj(self,db_filepath:str)->DatabaseInfo:
        db_info_list = self.fmap.get_active_databases_in_dbm()
        for db in db_info_list:
            if not db.active:
                continue
            if str(db.database_filepath) == db_filepath:
                return db    
        return None
    
    def _clear_search(self):
        if not self._has_been_searched:
            return
        # get tree manager 
        model=self.results_tree.model
        t_m=self.results_tree.model.t_m
        root_node = t_m.root
        
        self._has_been_searched = False
        # remove all children
        try:
            model.beginResetModel()
            for ch_node in root_node.children[:]:
                t_m.remove_node(ch_node)
            
            for e_node in self._explorer_root_node.children:
                e_copy=deepcopy(e_node)
                print("E_NODE AFTER DEEP:", type(e_copy), e_copy)
                t_m.add_child(root_node,e_copy)   
        finally:
            model.endResetModel() 
        self._explorer_root_node = None

    def _load_search_results_to_tree(self):
        if not self.s_result:
            return
        # get tree manager 
        model=self.results_tree.model
        t_m=self.results_tree.model.t_m
        root_node = t_m.root
        print("ROOT:", type(root_node), root_node)
        if not self._has_been_searched:
            self._explorer_root_node = deepcopy(root_node)
            print("ROOT AFTER DEEP:", type(root_node), root_node)
            self._has_been_searched = True

        # remove all children
        model.beginResetModel()
        try:
            for ch_node in root_node.children[:]:
                t_m.remove_node(ch_node)
            
            for s_r in self.s_result:
                if not isinstance(s_r,SearchResult):
                    continue
                self._load_a_search_result_to_tree(root_node=root_node, s_r=s_r)
        finally:
            model.endResetModel()

    def _load_a_search_result_to_tree(self,root_node:TreeNode,s_r:SearchResult):
        print("1 _load_a_search_result_to_tree entered")
        a_db=s_r.temp_db
        is_on_db = False
        if len(root_node.children)>0:
            for chdb_node in root_node.children:
                if chdb_node.i_am == "database" and chdb_node.db == a_db:
                    is_on_db=True
                    db_node=chdb_node
                    break
        print(f"2 is_on_db={is_on_db}")
        if not is_on_db:
            # Load database
            db=self._get_db_info_obj(s_r.origin_db)
            db_node = TreeNode(f"Search Result {s_r.idx} {db.name}")
            db_node.i_am = "database"
            real_db_filepath=str(db.database_filepath)
            db_node.path = "" # do not add to path
            db_node.db = real_db_filepath
            db_node.i_exist = db.active
            db_node.map = None
            db_node.info = s_r.temp_db
            db_node.loaded = True
            db_node.expand = True
            print(f"3 dbnode formed={db_node}")
            root_node.add_child(db_node)
        print(f"4 db_node={db_node}")
        # Load map                    
        mount,serial = self.fmap.get_mount_serial_of_map(s_r.temp_db,s_r.temp_map) 
        map_node = TreeNode(f"{s_r.temp_map} @ ({mount})")
        map_node.i_am = "map"
        map_node.path = mount
        map_node.info = s_r.temp_db_map_pair
        map_node.loaded = False
        map_node.db = s_r.temp_db
        map_node.i_exist=self.fmap.is_mount_serial_active(mount,serial)
        map_node.mount = mount
        map_node.serial = serial
        map_node.map = s_r.temp_map
        map_node.expand = True
        print(f"5 map_node formed={map_node}")
        db_node.add_child(map_node)
        # Children are added with results
        map_full_path = self.fmap.get_full_mount_path_of_map(s_r.temp_db,s_r.temp_map) 
        self._add_db_map_children(map_node,map_full_path)
        # Set by the lazyloader
        #  # database mapping
        # map_node.db_id = None
        # # file mapping
        # map_node.itempath = None
        # map_node.quantity = 0
        # map_node.num_files = None
        # map_node.num_dirs = None

    def _add_db_map_children(self,map_node:TreeNode,full_path):    
        multiple_folders=self.modding_info.get("multiple_folders")
        # Single folder level
        p_node=map_node
        print(f"6 adding children={map_node}")
        if not multiple_folders:
            ch_path=self.fmap.fm.remove_mount_from_path(p_node.mount,full_path,remove_start_separator=True)
            p_node.loaded=True
            ch_node=TreeNode(ch_path)
            ch_node.i_am ="dir"
            ch_node.db = p_node.db
            ch_node.map = p_node.map
            ch_node.mount = p_node.mount
            ch_node.serial = p_node.serial
            ch_node.itempath = self._normalize_itempath(ch_path)
            ch_node.path = full_path
            ch_node.i_exist = os.path.exists(full_path)
            ch_node.loaded=False
            ch_node.locked=True
            p_node.add_child(ch_node)
            print(f"7 child added={ch_node} to {p_node}")
            return
        
        # Multiple folder levels loading
        path_list=self.fmap.fm.path_to_list(full_path)
        if p_node.mount not in ["/","\\",os.sep]:
            # Remove the mount is included on map_node.path
            path_list=path_list[1:]
        for iii,a_dir in enumerate(path_list):
            p_node.loaded=True
            ch_node=TreeNode(a_dir)
            ch_node.i_am ="dir"
            ch_node.db = p_node.db
            ch_node.map = p_node.map
            ch_node.mount = p_node.mount
            ch_node.serial = p_node.serial
            ch_node.path = os.path.join(p_node.path,a_dir)
            ch_path=self.fmap.fm.remove_mount_from_path(p_node.mount,full_path,remove_start_separator=True)
            ch_node.itempath = self._normalize_itempath(ch_path)
            ch_node.i_exist = os.path.exists(ch_node.path)

            ch_node.loaded=False
            ch_node.locked=True
            # Dont expand the last path else it loads the first files and folders for all maps
            if iii<len(path_list)-1:
                ch_node.expand=True
            p_node.add_child(ch_node)
            # Next iteration
            p_node = ch_node
    
    def _normalize_itempath(self,path):
        if not path:
            return path
        if len(path)==1 and path in ["/", "\\", os.sep]:
            return path
        if path[0] in ["/", "\\", os.sep]:
            #remove / in beguining
            path=path[1:]
        if path[-1] not in ["/", "\\", os.sep]:
            return path + os.sep #add / in the end
        else:
            return path
    
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

    # # ==============================================================
    # # UI
    # # ==============================================================
    # def build_ui(self):

    #     # ==============================================================
    #     # Compact search frame
    #     # ==============================================================

    #     self.search_frame = QtWidgets.QFrame()
    #     self.search_frame.setObjectName("SearchFrame")
    #     self.search_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
    #     self.search_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

    #     search_layout = QtWidgets.QHBoxLayout(self.search_frame)

    #     search_layout.setContentsMargins(6, 3, 6, 3)
    #     search_layout.setSpacing(4)

    #     # --------------------------------------------------------------
    #     # Search icon
    #     # --------------------------------------------------------------

    #     self.search_icon = QtWidgets.QLabel()

    #     # Replace with your own icon later:
    #     # self.search_icon.setPixmap(...)
    #     self.search_icon.setText("🔎")
    #     self.search_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    #     self.search_icon.setFixedWidth(22)
    #     search_layout.addWidget(self.search_icon)

    #     # --------------------------------------------------------------
    #     # Query edit
    #     # --------------------------------------------------------------

    #     self.query_edit = QtWidgets.QLineEdit()
    #     self.query_edit.setPlaceholderText("Search...")

    #     self.query_edit.setClearButtonEnabled(True)
    #     self.query_edit.setMinimumWidth(150)

    #     search_layout.addWidget(self.query_edit,1)

    #     # --------------------------------------------------------------
    #     # Validation indicator
    #     # --------------------------------------------------------------

    #     self.valid_icon = QtWidgets.QLabel()
    #     self.valid_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    #     self.valid_icon.setFixedWidth(22)
    #     self.valid_icon.setToolTip("Query validation")
    #     search_layout.addWidget(self.valid_icon)

    #     # --------------------------------------------------------------
    #     # History button
    #     # --------------------------------------------------------------

    #     self.history_button = QtWidgets.QToolButton()
    #     self.history_button.setText("⌄")
    #     self.history_button.setToolTip("Search history")

    #     self.history_button.setAutoRaise(True)
    #     self.history_button.setFixedWidth(26)

    #     search_layout.addWidget(self.history_button)

    #     # --------------------------------------------------------------
    #     # Search button
    #     # --------------------------------------------------------------

    #     self.search_button = QtWidgets.QToolButton()
    #     self.search_button.setText("🔍")
    #     self.search_button.setToolTip("Search")
    #     self.search_button.setAutoRaise(True)
    #     self.search_button.setFixedWidth(30)

    #     search_layout.addWidget(self.search_button)

    #     # --------------------------------------------------------------
    #     # Options button
    #     # --------------------------------------------------------------

    #     self.options_button = QtWidgets.QToolButton()
    #     self.options_button.setText("⋮")
    #     self.options_button.setToolTip("Search options")

    #     self.options_button.setAutoRaise(True)
    #     self.options_button.setFixedWidth(26)

    #     search_layout.addWidget(self.options_button)

    #     # ==============================================================
    #     # Main dialog layout
    #     # ==============================================================

    #     main_layout = QtWidgets.QVBoxLayout(self)
    #     main_layout.setContentsMargins(8, 8, 8, 8)
    #     main_layout.setSpacing(6)
    #     main_layout.addWidget(self.search_frame)

    #     # ==============================================================
    #     # View filters
    #     # ==============================================================

    #     filter_group = QtWidgets.QGroupBox("View Filters")
    #     filter_layout = QtWidgets.QHBoxLayout(filter_group)
    #     filter_layout.setContentsMargins(8, 4, 8, 4)
    #     filter_layout.setSpacing(12)

    #     self.show_files_cb = QtWidgets.QCheckBox("Files")
    #     self.show_files_cb.setChecked(True)

    #     self.show_folders_cb = QtWidgets.QCheckBox("Folders")
    #     self.show_folders_cb.setChecked(True)

    #     self.show_size_cb = QtWidgets.QCheckBox("Size")
    #     self.show_size_cb.setChecked(True)

    #     self.show_dates_cb = QtWidgets.QCheckBox("Dates")
    #     self.show_md5_cb = QtWidgets.QCheckBox("MD5")

    #     filter_layout.addWidget(self.show_files_cb)
    #     filter_layout.addWidget(self.show_folders_cb)
    #     filter_layout.addWidget(self.show_size_cb)
    #     filter_layout.addWidget(self.show_dates_cb)
    #     filter_layout.addWidget(self.show_md5_cb)
    #     filter_layout.addStretch(1)
    #     main_layout.addWidget(filter_group)

    #     # ==============================================================
    #     # Results
    #     # ==============================================================

    #     results_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
    #     self.results_tree = QtWidgets.QTreeView()

    #     self.properties_tree = QtWidgets.QTreeWidget()
    #     self.properties_tree.setHeaderLabels(["Property", "Value"])

    #     results_splitter.addWidget(self.results_tree)
    #     results_splitter.addWidget(self.properties_tree)
    #     results_splitter.setSizes([1200, 400])

    #     main_layout.addWidget(results_splitter,1)

    #     # ==============================================================
    #     # Statistics
    #     # ==============================================================
    #     stats_group = QtWidgets.QGroupBox("Statistics")
    #     stats_layout = QtWidgets.QHBoxLayout(stats_group)
    #     stats_layout.setContentsMargins(8, 3, 8, 3)

    #     self.files_label = QtWidgets.QLabel("Files: 0")
    #     self.folders_label = QtWidgets.QLabel("Folders: 0")
    #     self.size_label = QtWidgets.QLabel("Size: 0 MB")

    #     self.selected_label = QtWidgets.QLabel("Selected: 0")

    #     stats_layout.addWidget(self.files_label)

    #     stats_layout.addSpacing(20)
    #     stats_layout.addWidget(self.folders_label)
    #     stats_layout.addSpacing(20)
    #     stats_layout.addWidget(self.size_label)
    #     stats_layout.addSpacing(20)
    #     stats_layout.addWidget(self.selected_label)
    #     stats_layout.addStretch(1)
    #     main_layout.addWidget(stats_group)

    #     # ==============================================================
    #     # Actions
    #     # ==============================================================

    #     button_layout = QtWidgets.QHBoxLayout()

    #     self.selection_map_button = QtWidgets.QPushButton("Create Selection Map")
    #     self.export_button = QtWidgets.QPushButton("Export Tree")

    #     self.delete_button = QtWidgets.QPushButton("Delete")
    #     self.copy_button = QtWidgets.QPushButton("Copy Results")
    #     self.close_button = QtWidgets.QPushButton("Close")

    #     button_layout.addWidget(self.selection_map_button)
    #     button_layout.addWidget(self.export_button)
    #     button_layout.addWidget(self.delete_button)
    #     button_layout.addWidget(self.copy_button)

    #     button_layout.addStretch(1)
    #     button_layout.addWidget(self.close_button)
    #     main_layout.addLayout(button_layout)

    #     # ==============================================================
    #     # Compact styling
    #     # ==============================================================

    #     self.search_frame.setStyleSheet("""
    #         QFrame#SearchFrame {
    #             border: 1px solid palette(mid);
    #             border-radius: 4px;
    #             background: palette(base);
    #         }

    #         QFrame#SearchFrame QLineEdit {
    #             border: none;
    #             background: transparent;
    #             padding: 3px 2px;
    #         }

    #         QFrame#SearchFrame QToolButton {
    #             border: none;
    #             padding: 2px;
    #             margin: 0px;
    #         }

    #         QFrame#SearchFrame QToolButton:hover {
    #             background: palette(midlight);
    #             border-radius: 3px;
    #         }
    #     """)

    #     # ==============================================================
    #     # Initial validation state
    #     # ==============================================================
    #     self._set_validation_state(None)