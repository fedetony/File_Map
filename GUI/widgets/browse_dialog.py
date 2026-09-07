# compare_dialog.py
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets.class_qt_map_progress import QtMapProgress

from collections import deque
import threading
from datetime import datetime

from controllers.class_filemap_cli_manager import FileMapCliManager
from controllers.mapping_worker_thread import WorkerManager
from functional.class_icons import Icons
from functional.class_text_renderer import TextRenderer
from functional.class_text_exporter import ExporterHandler, TableTextExporter
from widgets.class_explorer_tree_widget import *
from widgets.search_query_widget import *
from widgets.ask_new_name_dialog import NewMapDialog

from models.class_provider_engine import DefaultProviderEngine, FM
from models.class_action_provider import *

from models.class_style_provider import *
from models.class_lazy_loader import *
from widgets.class_export_widget import *
from controllers.class_database_manager import DatabaseInfo
from class_file_mapper import MapType

from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("BrowseDialog","debug",True,None)

from copy import deepcopy
from dataclasses import dataclass


NODE_HIDDEN_PROPERTIES = {
    "parent",
    "children",
}


class BrowseDialogSetter:
    """Sets the configuration for the browse dialog
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
        # if mode == "Files":        
        #     self._set_db_mode_config()
        self._set_db_browse_mode_config()
            
            # raise AttributeError("Mode not supported!")
        if not isinstance(self.config,ExplorerConfig):
            return
        
        if not isinstance(self.config.explorer_style,TreeStyle):
                self.config.explorer_style = DefaultExplorerStyle() # text, tooltips, icons
        if not isinstance(self.config.tree_style,TreeStyleProvider):
            self.config.tree_style = DefaultTreeStyle() # role formatting by node, treemanager

        self.dlg = BrowseDialog(fmap=self.fmap,
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

    def _set_db_browse_mode_config(self):
        virtual_root = TreeNode("Map Browser")
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
        config.show_path_edit = True
        config.show_context_menu = True
        # Mode selection
        mode=self.modding_info.get("mode")
        
        if mode == "files":
            config.selection_by_type_mode = SelectionByTypeMode.FILES_ONLY
        elif mode == "dirs":
            config.selection_by_type_mode = SelectionByTypeMode.DIRS_ONLY
        else:
            config.selection_by_type_mode = SelectionByTypeMode.ANY

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
        config.action_provider = BrowseFileActionProvider() # menu, shortcuts, global shortcuts
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

class BrowseDialog(QtWidgets.QDialog):

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
        self.mode = self.modding_info.get("mode")
        self.worker_manager = worker_manager
        self.explorer_config = explorer_config
        self.icons=Icons()
        self.text_renderer = TextRenderer()
    
        self._explorer_root_node=None
        self.debug_counter=0
        self._lazy_loading = False
        # self.statistic_dict={}
        
        self.db_idx_map_registry=[]

        self.setWindowTitle("Browse")
        self.resize(1600, 950)

        self.build_ui()
        # Hide files
        if self.mode == "dirs":
            self.show_hide_files(self.hide_files_cb.checkState())
        elif self.mode == "files":
            self.hide_files_cb.setChecked(False)
            self.show_hide_files(self.hide_files_cb.checkState())

    def build_ui(self):


        # ==============================================================
        # View filters
        # ==============================================================

        filter_group = QtWidgets.QGroupBox("🛠️ Tools and Filters")

        filter_layout = QtWidgets.QHBoxLayout(filter_group)

        self.clear_selected_icon = QtWidgets.QToolButton()
        self.clear_selected_icon.setIcon(self.icons.icon('unselect'))
        self.clear_selected_icon.setAutoRaise(True)
        self.clear_selected_icon.setEnabled(True)
        self.clear_selected_icon.setFixedWidth(32)
        self.clear_selected_icon.setToolTip("Clear Selection")
        self.clear_selected_icon.clicked.connect(self.clear_files_folders_selection)


        self.hide_files_cb = QtWidgets.QCheckBox("Hide Files")
        self.hide_files_cb.setChecked(True)
        self.hide_files_cb.checkStateChanged.connect(self.show_hide_files)

        # self.show_folders_cb = QtWidgets.QCheckBox("Folders")
        # self.show_folders_cb.setChecked(True)

        # self.show_size_cb = QtWidgets.QCheckBox("Show Size")
        # self.show_size_cb.setChecked(True)

        # self.show_dates_cb = QtWidgets.QCheckBox("Show Dates")
        # self.show_dates_cb.setChecked(False)

        # self.show_md5_cb = QtWidgets.QCheckBox("Show MD5")
        # self.show_md5_cb.setChecked(False)

        filter_layout.addWidget(self.clear_selected_icon)

        if self.mode == "dirs":
            filter_layout.addWidget(self.hide_files_cb)
        
        # filter_layout.addWidget(self.show_folders_cb)
        # filter_layout.addWidget(self.show_size_cb)
        # filter_layout.addWidget(self.show_dates_cb)
        # filter_layout.addWidget(self.show_md5_cb)

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
        self.br_tree = ExplorerTreeWidget(self.explorer_config)
        self.br_tree.action_provider.set_mode(self.mode)
        self.br_tree.userSelectionChanged.connect(self.on_selection_changed)
        self.br_tree.nodeExpanded.connect(lambda: 
                self._on_node_expanded(True))
        self.br_tree.nodeCollapsed.connect(lambda: 
                self._on_node_expanded(False))
        # self.br_tree.actionEvaluated.connect(self.on_action_evaluated)
        self.br_tree.exportRequested.connect(self.on_export_requested)
        self.br_tree.exportFormatChanged.connect(self.on_export_format_changed)
        self.br_tree.lazyLoading.connect(self.on_lazy_loading)
        #self.br_tree.nodeDoubleClicked.connect(self._show_node_properties)
        self.br_tree.nodeClicked.connect(self._show_node_properties)
        self.br_tree.currentSelectionChanged.connect(self._on_current_selection_changed)
        # Exporter widget
        self._set_export_default_configuration()

        self.properties_tree = QtWidgets.QTreeWidget()
        self.properties_tree.setHeaderLabels(
            ["Property", "Value"]
        )

        results_splitter.addWidget(self.br_tree)
        results_splitter.addWidget(self.properties_tree)

        results_splitter.setSizes([1600, 0])

        # ==============================================================
        # Statistics
        # ==============================================================

        stats_group = QtWidgets.QGroupBox("Statistics")

        stats_layout = QtWidgets.QHBoxLayout(stats_group)

        self.files_label = QtWidgets.QLabel("Node Files: 0")
        self.folders_label = QtWidgets.QLabel("Node Folders: 0")
        self.quantity_label = QtWidgets.QLabel("Node Quantity: 0")
        self.size_label = QtWidgets.QLabel("Size: 0 MB")
        self.selected_label = QtWidgets.QLabel("Selected: 0")

        stats_layout.addWidget(self.quantity_label)
        stats_layout.addSpacing(20)

        stats_layout.addWidget(self.files_label)
        stats_layout.addSpacing(20)

        stats_layout.addWidget(self.folders_label)
        stats_layout.addSpacing(20)

        stats_layout.addWidget(self.size_label)
        stats_layout.addSpacing(20)

        stats_layout.addWidget(self.selected_label)

        stats_layout.addStretch(1)

        # ==============================================================
        # Action buttons
        # ==============================================================

        button_layout = QtWidgets.QHBoxLayout()

        # self.selection_map_button = QtWidgets.QPushButton("Create Selection Map")
        # self.selection_map_button.setIcon(self.icons.icon("selection map"))
        # self.selection_map_button.clicked.connect(self._create_selection_map)

        self.export_button = QtWidgets.QPushButton("Export")
        self.export_button.setIcon(self.icons.icon("export"))
        self.is_export_showing = False
        self.export_button.clicked.connect(self._toggle_export_show)

        # self.delete_button = QtWidgets.QPushButton("Delete")

        # self.copy_button = QtWidgets.QPushButton("Copy Results")

        self.close_button = QtWidgets.QPushButton("Close")

        # button_layout.addWidget(self.selection_map_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.close_button)

        # ==============================================================
        # Main layout
        # ==============================================================

        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Query widget gets the most natural amount of space
        main_layout.addWidget(filter_group)

        # Results should consume all remaining vertical space
        main_layout.addWidget(results_splitter,1)
        main_layout.addWidget(stats_group)
        main_layout.addLayout(button_layout)

        # ==============================================================
        # Final sizing
        # ==============================================================

        self.br_tree.tree.setAlternatingRowColors(True)
        self.br_tree.tree.setUniformRowHeights(False)

        self.properties_tree.setAlternatingRowColors(True)

        self.close_button.clicked.connect(self.reject)

    def log_callback(self,*args):
        self.log_print(*args, logger=log, level="info", sep=" ", end="")
    
    @staticmethod
    def log_print(*args, logger=None, level="info", sep=" ", end="\n"):
        text = sep.join(str(arg) for arg in args) + end
        log_func = getattr(logger, level) if logger else getattr(logging, level)
        log_func("%s", text)

    
    
    def _set_export_default_configuration(self):
        ex_cfg=self.fmap.cfg.export
        selection=ex_cfg.get("default_selection","file_tree") # options: "expanded", "selected", "file_tree","directory_tree"
        format=ex_cfg.get("default_format", "filestruct_json") #options: "filestruct_json", "list_txt", "list_csv", "text_tree"
        selected_fields=ex_cfg.get("default_selected_fields") # null -> all selected [] -> none selected
        ex_wid=self.br_tree.export_widget
        ex_wid.setSelection(selection)
        ex_wid.setFormat(format)
        field_list=ex_wid.getFields()
        field_id_list=[]
        if isinstance(selected_fields,list):
            for an_id,a_field in field_list:
                if a_field in selected_fields:
                    field_id_list.append(an_id)
            ex_wid.setSelectedFields(field_id_list)
    

    def _get_db_info_obj(self,db_filepath:str)->DatabaseInfo:
        db_info_list = self.fmap.get_active_databases_in_dbm()
        for db in db_info_list:
            if not db.active:
                continue
            if str(db.database_filepath) == db_filepath:
                return db    
        return None

    def _add_db_map_children(self,map_node:TreeNode,full_path):    
        multiple_folders=self.modding_info.get("multiple_folders")
        # Single folder level
        p_node=map_node
        #print(f"6 adding children={map_node}")
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
            #print(f"7 child added={ch_node} to {p_node}")
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
                self._set_statistics_node(self.br_tree.current_node())


    def _toggle_export_show(self):
        if self.is_export_showing:
            self.export_button.setIcon(self.icons.icon("export"))
            self.is_export_showing = False
        else:
            self.export_button.setIcon(self.icons.icon("notexport"))
            self.is_export_showing = True
        self._configure_export_widget()
        self.br_tree.show_export_widget(self.is_export_showing)
    
    
    def _format_property_value(self, value):
        if isinstance(value, bool):
            return "[bold]✓ Yes[/]" if value else "✕ No"

        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(x) for x in value)

        if isinstance(value, dict):
            return ", ".join(
                f"{key}: {val}"
                for key, val in value.items()
            )

        return str(value)
    
    def _show_node_properties(self, node: TreeNode):
        self.properties_tree.clear()
        add_info_at_end=False
        for name, value in vars(node).items():
            if name in NODE_HIDDEN_PROPERTIES:
                continue
            if value is None:
                continue

            if name == "size":
                value = self.fmap.fm.get_size_str_formatted(value)
            if name == "i_am":
                value = TEXT_ICONS.get(value, "") + " " + value

            # Set to strings
            value = self._format_property_value(value)

            # add colors and formats
            if name in ("quantity","num_dirs", "num_files","size"):
                value = "[cyan]" + value +"[/]"
            if name in ("mount","serial") and node.i_exist:
                value = "[bright_green]" + value +"[/]"
            if name in ("mount","serial") and not node.i_exist:
                value = "[red]" + value +"[/]"
            if name in ("map","db") and node.i_exist:
                value = "[magenta]" + value +"[/]"
            if name in ("path","name") and node.i_exist:
                value = "[bright_yellow]" + value +"[/]"

            if name == "info" and node.i_am == "file":
                add_info_at_end=True        
            else:
                self._add_property(name, value)
                
        if add_info_at_end:   
            info_dict=self._parse_node_info(node)
            self._add_property("Database Properties", "[bright_red]"+"-"*33+"[/]")
            for prop,val in info_dict.items(): 
                val = self._format_db_file_property_value(prop,val,node)
                if prop == "id":
                    prop = "id_in_db"
                self._add_property(prop, val)
        self.properties_tree.resizeColumnToContents(0)
        # set the statistics
        self._set_statistics_node(node)

    def _add_property(self, name, value):
        item = QtWidgets.QTreeWidgetItem(self.properties_tree, [name])
        label = QtWidgets.QLabel()
        label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        label.setText(self.text_renderer.to_html(value))
        label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.properties_tree.setItemWidget(item, 1, label)

    def _get_fields_on_db(self, node:TreeNode)->list[str]:
        if not node:
            return []
        if node.db and node.map:
            fm=self.fmap.cma.get_file_map(node.db)
            if fm:
                return fm.db.get_column_list_of_table(node.map)
        return []
        

    def _parse_node_info(self, node: TreeNode) -> dict:
        if not node:
            return {}

        if node.i_am != "file":
            return {}

        if not node.info:
            return {}

        fields = self._get_fields_on_db(node)

        if not fields:
            return {}

        return dict(zip(fields, node.info))
    
    def _format_db_file_property_value(self, name:str, value, node:TreeNode):
        if value is None:
            return None

        # ISO datetime fields
        if name.startswith("dt_"):
            try:
                value = datetime.fromisoformat(value).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )[:-3]
            except (TypeError, ValueError):
                # Keep the original value if it isn't a valid ISO date
                pass

        elif name == "size":
            value = self.fmap.fm.get_size_str_formatted(value)
        else:
            value = self._format_property_value(value)

        # Styling
        if name in ("id", "size"):
            value = f"[cyan]{value}[/]"

        elif name == "md5":
            value = f"[red]{value}[/]"

        elif name in ("filepath", "filename") and node.i_exist:
            value = f"[bright_yellow]{value}[/]"

        elif name.startswith("dt_"):
            value = f"[bright_blue]{value}[/]"

        return value
    
    def _set_statistics_node(self, node: TreeNode):
        if not node:
            return
        # db_total_matches=self.statistic_dict.get(f"Total_{node.db}",0)
        # map_total_matches=self.statistic_dict.get((node.db,node.map),0)
        # sel_node_list=self.br_tree.selected_nodes()
        all_selected=len(self.br_tree.selected_ids())

        self.files_label.setText(f"Node Files: {node.num_files or 0}")
        self.folders_label.setText(f"Node Folders: {node.num_dirs or 0}")
        self.quantity_label.setText(f"Node Quantity: {node.quantity or 0}")
        if node.size:
            value = self.fmap.fm.get_size_str_formatted(node.size)
        else:
            value = 0
        self.size_label.setText(f"Size: {value}")
        self.selected_label.setText(f"Selected: {all_selected}")

    def on_selection_changed(self,nodes_list):
        if isinstance(nodes_list,list) and len(nodes_list)>0:
            node=nodes_list[0]
            if isinstance(node,TreeNode):
                self._set_statistics_node(node)
    
    def get_export_formats_selections(self):
        if self.mode == "dirs" and self.hide_files:
            ex_formats = [
                # These require files
                # ExportFormat("Filestruct → JSON", "filestruct_json", ".json"),
                # ExportFormat("List → TXT", "list_txt", ".txt"),
                # ExportFormat("List → CSV", "list_csv", ".csv"),
                ExportFormat("Text Tree", "text_tree", ".txt"),
            ]
            ex_selections = [
                ExportSelection("Expanded", "expanded"),
                ExportSelection("Selected", "selected"),
                #ExportSelection("File Tree", "file_tree"),
                ExportSelection("Directory Tree", "directory_tree"),
                ]
        else:
            ex_formats=DC_DEFAULT_FORMATS
            ex_selections=DC_DEFAULT_SELECTIONS
        return ex_formats,ex_selections

    def on_export_requested(self,export_dict: dict):
        self.log_callback("Got export Request " + 
            "\n".join([f"{kkk}: {vvv} " for kkk,vvv in export_dict.items()]))
        t_m=self.br_tree.model.t_m
        
        ex_formats,ex_selections =self.get_export_formats_selections()        
        ex_handler=ExporterHandler(fmap=self.fmap,
                        export_request_dict=export_dict,
                        root_node=t_m.root,
                        style=DefaultExportStyle(), 
                        available_fields=None,
                        available_formats=ex_formats,
                        available_selections=ex_selections,
                        log_callback=self.log_callback,
                        )
        was_exported, msg = ex_handler.do_export()
        msgbox=MsgBoxHelper()
        filepath_target=export_dict.get("target")
        if was_exported:
            msgbox.show("Export",
                    f"File {filepath_target} was Successfully Exported!",
                    icon=QMessageBox.Icon.Information,
                    buttons=None,
                    default=None,
                    detailed_text=msg,
                    informative_text=None,
                    )
        else:
            msgbox.show("Export",
                    f"File {filepath_target} was Not Exported!",
                    icon=QMessageBox.Icon.Critical,
                    buttons=None,
                    default=None,
                    detailed_text=msg,
                    informative_text=None,
                    )
    
    def on_export_format_changed(self,format_tup):
        label,format = format_tup
        ex_wid=self.br_tree.export_widget
        if format not in ("filestruct_json", "list_txt", "list_csv", "text_tree"):
            return
        if format == "filestruct_json":
            req_fields=['filename','filepath','id','size']
        elif format == "list_txt":
            req_fields=['id']
        elif format == "list_csv":
            req_fields=['id']
        elif format == "text_tree":
            req_fields=['filename','filepath']
        ex_wid.SetRequiredFields(req_fields)
    
    def _configure_export_widget(self):
        ex_wid = self.br_tree.export_widget
        ex_formats,ex_selections =self.get_export_formats_selections()   
        selections=[]
        for sel_obj in ex_selections:
            if isinstance(sel_obj,ExportSelection):
                selections.append((sel_obj.label,sel_obj.value))
        ex_wid.setSelections(selections)
        if selections:
            ex_wid.setSelection(selections[0][1])
        formats=[]
        for for_obj in ex_formats:
            if isinstance(for_obj,ExportFormat):
                formats.append((for_obj.label,for_obj.value))
        ex_wid.setFormats(formats)
        if formats:
            ex_wid.setFormat(formats[0][1])

    def clear_files_folders_selection(self):
        """Unselect all nodes"""
        tm=self.br_tree.t_m
        selected_nodes=self.br_tree.selected_nodes()
        for node in selected_nodes:
            tm.set_selected(node,False)
        self.br_tree.refresh()
    
    def show_hide_files(self, checkstate):
        self.hide_files = (checkstate == Qt.CheckState.Checked)
        tm=self.br_tree.t_m
        ap=self.br_tree.action_provider
        if isinstance(ap,BrowseFileActionProvider):
            ap.hide_all_files(tm,self.hide_files)
        self.set_nodes_hidden_in_treeview(tm.root)
        self._configure_export_widget()
        
    def set_nodes_hidden_in_treeview(self,node:TreeNode):
        index = self.br_tree.model.get_index_from_node(node)
        if index.isValid():
            self.br_tree.tree.setRowHidden(
                index.row(), index.parent(), node.hidden)
        for ch_node in node.children:
            self.set_nodes_hidden_in_treeview(ch_node)
    
    def _on_node_expanded(self,is_expand:bool):
        self.show_hide_files(self.hide_files_cb.checkState())
    
    def _on_current_selection_changed(self,current_selection_list:list):
        if current_selection_list and isinstance(current_selection_list,list): 
            self._set_statistics_node(current_selection_list[0])

        
    
    

            




        
            

        
        










