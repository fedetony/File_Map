# database_page.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSplitter,
    QTextEdit,
    QFileDialog,
    QMenu,

)
from functional.class_icons import Icons
from controllers.class_database_manager import *
from controllers.class_filemap_cli_manager import FileMapCliManager
from widgets.ask_db_authentication_dialog import DatabaseAuthTypeDialog
from widgets.ask_confirmation_dialog import ConfirmationDialog
from functional.class_table_widget_functions import TableWidgetFunctions
from functional.class_ST import SignalTracker

class DatabasePage(QWidget):

    databasesActivationChange = pyqtSignal(bool)

    def __init__(self, filemapcli:FileMapCliManager,parent=None ):
        super().__init__(parent)
        self.fmap=filemapcli
        self.dbm = self.fmap.dbm
        self.icons=Icons()
        self.define_struct_restrictions()
        self.create_ui()
        self.connect_ui()
        # self.load_demo()
        self.fmap.set_active_databases_in_dbm()
        self.refresh_table()

    def define_struct_restrictions(self):
        self.db_struct = {
        "-1": { "Name": "Dummy", 
        "DB Filepath": "",
        "DB Filename": "",
        "DB active": "False",
        "DB autoload": "False",
        "Requires Password": "False",
        "Has Encryption Key": "False",
        "Config": "None"
        }}
        self.db_struct_mask = {
            "__any__": {
                "Name": {"__m__1": "is_unique", "__mv__1": ""},
                "DB Filepath": {"__m__1": "is_value_type", "__mv__1": str(str)},
                "DB Filename": {"__m__1": "is_value_type", "__mv__1": str(str),
                                "__m__2": "is_format", "__mv__2": r"^[a-zA-Z0-9._-]+(\.[a-zA-Z0-9._-]+)?$"},
                "DB active": {"__m__1": "is_value_type", "__mv__1": str(bool),
                              "__m__2": "is_not_change", "__mv__2": ""},
                "DB autoload": {"__m__1": "is_value_type", "__mv__1": str(bool)},
                "Requires Password": {"__m__1": "is_value_type", "__mv__1": str(bool),
                                      "__m__2": "is_not_change", "__mv__2": ""},
                "Has Encryption Key": {"__m__1": "is_value_type", "__mv__1": str(bool),
                                       "__m__2": "is_not_change", "__mv__2": ""},
                "Config": {"__m__1": "is_value_type", "__mv__1": str(str),
                        "__m__2": "limited_selection", "__mv__2": ["","None","User","Default"],
                        "__m__3": "is_not_change", "__mv__3": ""},                        
                # "Resolution": {"__m__1": "is_not_change", "__mv__1": ""}, # dont mask if it has widget
            },
        }

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def connect_ui(self):
        self.btn_new.clicked.connect(self.create_database)
        self.btn_append.clicked.connect(self.append_database)
        self.btn_remove_all.clicked.connect(self.remove_all)
        self.btn_activate_all.clicked.connect(self.activate_all)
        self.btn_deactivate_all.clicked.connect(self.deactivate_all)

        # right click menu
        self.database_table.customContextMenuRequested.connect(self._table_item_right_clicked)

    def create_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header= QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(self.icons.icon("databases").pixmap(32, 32))
        title = QLabel("Database Manager")
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
        layout.addLayout(header)


        # Toolbar
        toolbar = QHBoxLayout()

        self.btn_new = QPushButton("New Database")
        self.btn_new.setIcon(self.icons.icon("db key"))
        self.btn_append = QPushButton("Add")
        self.btn_append.setIcon(self.icons.icon("db add"))
        self.btn_remove_all = QPushButton("Remove All")
        self.btn_remove_all.setIcon(self.icons.icon("bin"))

        self.btn_activate_all = QPushButton("Activate All")
        self.btn_activate_all.setIcon(self.icons.icon("yes"))
        self.btn_deactivate_all = QPushButton("Deactivate All")
        self.btn_deactivate_all.setIcon(self.icons.icon("db deactivate"))

        #self.refresh_btn = QPushButton("Refresh")

        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_append)

        toolbar.addWidget(self.btn_remove_all)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_activate_all)
        toolbar.addWidget(self.btn_deactivate_all)
        #toolbar.addWidget(self.refresh_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Main area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Database list
        db_group = QGroupBox("Databases")

        db_layout = QVBoxLayout(db_group)
        self.database_table = QTableWidget()
        # -----------TableWidgetFunctions
        self.twf = TableWidgetFunctions(
            self.database_table,self.db_struct,self.db_struct_mask, None, []
        )
        self.twf.signal_data_change[list, str, str, str].connect(self._table_widget_data_changed)
        self.twf.signal_item_button_right_clicked[list, QtCore.QPoint].connect(self._table_item_right_clicked)
        #self.twf.signal_item_combobox_currentindexchanged[int, str, list].connect(self._table_item_comboboxindexchanged)
        # self.model=self.twf.modelobj

        db_layout.addWidget(self.database_table)

        # Details
        details_group = QGroupBox("Database Information")
        details_layout = QVBoxLayout(details_group)

        self.details = QTextEdit()
        self.details.setReadOnly(True)

        self.details.setText("Select a database...")

        details_layout.addWidget(self.details)

        splitter.addWidget(db_group)

        splitter.addWidget(details_group)
        splitter.setStretchFactor(0,2)
        splitter.setStretchFactor(1,1)

        layout.addWidget(splitter)


    # ==========================================================
    # TABLE
    # ==========================================================

    def refresh_table(self):
        """Clears the rows and adds the db_struct"""
        self.database_table.setRowCount(0)
        self.db_struct = {}
        for db in self.dbm.databases:
            self.add_item_to_db_struct(db)

        id_list=self._get_all_id_list()
        active_db_list, unactive_db_list= self.fmap.get_active_unactive_db_id_list(id_list)
        self._add_remove_icons_to_items(active_db_list,True,"DB active",self.icons.icon("yes")) 
        self._add_remove_icons_to_items(unactive_db_list,False,"DB active",None)
        # add icons to active
        autoload, not_autoload = self.fmap.get_autoload_db_id_list(id_list)
        self._add_remove_icons_to_items(autoload,True,"DB autoload",self.icons.icon("bluegreen up dw arrows")) 
        self._add_remove_icons_to_items(not_autoload,False,"DB autoload",None)
        # key
        haskey ,nohaskey =self.fmap.get_cond_db_id_list(id_list,"has_key")
        self._add_remove_icons_to_items(haskey,True,"Has Encryption Key",self.icons.icon("shield")) 
        self._add_remove_icons_to_items(nohaskey,False,"Has Encryption Key",None)
        # password
        haspwd ,nohaspwd =self.fmap.get_cond_db_id_list(id_list,"requires_password")
        self._add_remove_icons_to_items(haspwd,True,"Requires Password",self.icons.icon("key")) 
        self._add_remove_icons_to_items(nohaspwd,False,"Requires Password",None)
        # Config
        user_list, default_list, none_list = self.fmap.get_user_default_config(id_list)
        self._add_remove_icons_to_items(user_list,True,"Config",self.icons.icon("heart")) 
        self._add_remove_icons_to_items(default_list,True,"Config",self.icons.icon("star")) 
        self._add_remove_icons_to_items(none_list,False,"Config",None)

        self._main_refresh_tablewidget()
        self.database_table.resizeColumnsToContents()

    # ==========================================================
    # Helpers
    # ==========================================================

    def selected_databases(self):
        databases = []
        rows = {
            index.row()
            for index in self.database_table.selectionModel().selectedRows()
        }

        for row in rows:
            item = self.database_table.item(row, 0)
            databases.append(
                item.data(Qt.ItemDataRole.UserRole)
            )

        return databases

    # ==========================================================
    # Context menu
    # ==========================================================
    def _table_item_right_clicked(self, track: list, apos: QtCore.QPoint):
        """Display the context menu for the selected database(s).
        right click
            ├── database actions
            ├── autoload actions
            ├── authentication
            ├── activation
            ├── configuration
            └── removal
        """

        if not track:
            return

        id_key_list, track_list = self._get_id_key_list_from_selection(track)

        log.debug(
            "Rightclick Selected-> id_key_list: %s, track_list %s, track %s",
            id_key_list,
            track_list,
            track,
        )

        self.item_menu = QtWidgets.QMenu()

        one_item = len(track_list) == 1
        many_items = len(track_list) > 1

        self._add_database_menu(track)
        self._add_autoload_menu(track, id_key_list)
        self._add_authentication_menu(track)
        self._add_activation_menu(id_key_list)
        self._add_configuration_menu(track, id_key_list)
        self._add_remove_menu(track, id_key_list, one_item, many_items)

        self.item_menu.move(apos)
        self.item_menu.show()
    
    def _add_database_menu(self, track):
        if len(track) < 2:
            return

        if track[1] not in ("Name", "DB Filepath", "DB Filename"):
            return

        act = self._add_action_to_menu("Create New Database", True, self.icons.icon("db key"))
        act.triggered.connect(self._create_new_database)

        act = self._add_action_to_menu("Add Database", True, self.icons.icon("db add"))
        act.triggered.connect(self._add_database)

        self.item_menu.addSeparator()
    
    def _add_autoload_menu(self, track, id_key_list):
        if len(track) < 2 or track[1] != "DB autoload":
            return

        autoload, not_autoload = self.fmap.get_autoload_db_id_list(id_key_list)

        if autoload:
            act = self._add_action_to_menu(
                f"AutoLoad OFF {autoload}",True, self.icons.icon("folder not ok"))
            act.triggered.connect(
                lambda: self._set_autoload(autoload, False))

        if not_autoload:
            act = self._add_action_to_menu(
                f"AutoLoad ON {not_autoload}",True, self.icons.icon("folder ok"))
            act.triggered.connect(
                lambda: self._set_autoload(not_autoload, True))

        self.item_menu.addSeparator()
    
    def _add_authentication_menu(self, track):
        if len(track) < 2:
            return

        if track[1] not in ("Requires Password", "Has Encryption Key"):
            return
        
        act = self._add_action_to_menu(
            f"Authenticate [{track[0]}]", True, self.icons.icon("shield"))
        act.triggered.connect(lambda: self._authenticate_db(track[0]))

        self.item_menu.addSeparator()
    
    def _add_activation_menu(self, id_key_list):
        active, inactive = self.fmap.get_active_unactive_db_id_list(id_key_list)

        if inactive:
            act = self._add_action_to_menu(
                f"Activate {inactive}", True, self.icons.icon("db activate"))
            act.triggered.connect(lambda: self._activate_databases(inactive))

        if active:
            act = self._add_action_to_menu(
                f"Deactivate {active}", True, self.icons.icon("db deactivate"))
            act.triggered.connect(lambda: self._deactivate_databases(active))

        self.item_menu.addSeparator()
    
    def _add_configuration_menu(self, track, ids):
        if len(track) < 2 or track[1] != "Config":
            return

        user_list, default_list, none_list = self.fmap.get_user_default_config(ids)

        # Databases not yet saved
        if none_list:
            act = self._add_action_to_menu(f"Save {none_list} to User Configuration",
                                        True, self.icons.icon("add file"))
            act.triggered.connect(lambda: self._save_db_in_config(none_list, user=True))

            act = self._add_action_to_menu(f"Save {none_list} to Default Configuration",
                                        True, self.icons.icon("add file"))
            act.triggered.connect(lambda: self._save_db_in_config(none_list, user=False))

        # Already in user configuration
        if user_list:
            act = self._add_action_to_menu(f"Update User Configuration {user_list}", 
                                           True, self.icons.icon("update file"))
            act.triggered.connect(lambda: self._save_db_in_config(user_list, user=True))

            act = self._add_action_to_menu(f"Remove from User Configuration {user_list}",
                True, self.icons.icon("trash"))
            act.triggered.connect(lambda: self._remove_db_from_config(user_list, user=True))

        # Already in default configuration
        if default_list:
            act = self._add_action_to_menu(f"Update Default Configuration {default_list}",
                True, self.icons.icon("update file"))
            act.triggered.connect(lambda: self._save_db_in_config(default_list, user=False))

            act = self._add_action_to_menu(f"Remove from Default Configuration {default_list}", 
                True, self.icons.icon("trash"))
            act.triggered.connect(lambda: self._remove_db_from_config(default_list, user=False))

        self.item_menu.addSeparator()
    
    def _add_remove_menu(self, track, id_key_list, one_item, many_items):
        if not (one_item or many_items):
            return

        if many_items:
            text = f"Remove {id_key_list}"
        else:
            db_name = self.twf.get_tracked_value_in_struct(
                [track[0], "Name"], self.db_struct)
            text = f"Remove [{track[0]}] - {db_name}"

        act = self._add_action_to_menu( text, True, self.icons.icon("bin"))
        act.triggered.connect(lambda: self._remove_databases(id_key_list))

        self.item_menu.addSeparator()

    # ==========================================================
    # Buttons
    # ==========================================================

    def create_database(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Create database",
            "",
            "Database (*.db)"
        )

        if not filename:
            return

        self.dbm.create_database(filename)
        self.refresh_table()

    def append_database(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Append database",
            "",
            "Database (*.db)"
        )
        if not filename:
            return
        
        name=FM.extract_filename(filename,False)
        password, keyfile=self.ask_db_authentication(name)
        self.fmap.add_database(filename,password, keyfile)
        self.refresh_table()
    

    def ask_confirmation(self, message, default:bool=False):
        conf_dialog = ConfirmationDialog()
        confirmed = default

        if conf_dialog.exec():
            confirmed = conf_dialog.ask_confirmation(message=message,default=default)

        return confirmed
    
    def ask_db_authentication(self,database_name):
        auth_type = DatabaseAuthTypeDialog(database_name)
        password = None
        keyfile = None
        if auth_type.exec():
            need_password, need_key = auth_type.values()

            auth_dialog = DatabaseAuthDialog(
                database_name,
                need_password=need_password,
                need_key=need_key,
            )

            if auth_dialog.exec():
                password, keyfile = auth_dialog.values()

        return password, keyfile

    def remove_selected(self):
        for db in self.selected_databases():
            self.dbm.remove_database(db)
        self.refresh_table()

    def _get_all_id_list(self)->list[str]:
        """Returns all ids in dbm

        Returns:
            list[str]: list of ids
        """
        return [str(dbid) for dbid in range(len(self.dbm.databases))]

    def activate_all(self):
        """Activates all unactive databases 
        """
        id_list=self._get_all_id_list()
        _ , unactive_db_list= self.fmap.get_active_unactive_db_id_list(id_list)
        self._activate_databases(unactive_db_list)
    
    def deactivate_all(self):
        """Deactivates all active databases 
        """
        id_list=self._get_all_id_list()
        active_db_list, _ = self.fmap.get_active_unactive_db_id_list(id_list)
        self._deactivate_databases(active_db_list)

    def remove_all(self):
        """Removes all databases in Table
        """
        numdb=len(self.dbm.databases)
        confirm=False
        if numdb>0:
            confirm=self.ask_confirmation((f"Are you sure to remove {numdb} "
                                  f"database{'s' if numdb>1 else ''} from list?"),False)
        if confirm:    
            for db in self.dbm.databases:
                self.dbm.remove_database(db)
        self.refresh_table()
        
    def _create_new_database(self):
        self.create_database()
        # self.refresh_table() # in create
    
    def _add_database(self):
        self.append_database()
        # self.refresh_table() # in append
    
    def _remove_databases(self,db_id_list):        
        self.fmap.remove_database(db_id_list)        
        self.refresh_table()
    
    def _authenticate_db(self,db_id):
        auth_list=self.fmap.get_authentication_list([db_id])
        for (db , db_filepath, requires_password, has_key, db_key_filepath) in auth_list:
            if isinstance(db,DatabaseInfo):
                password, keyfile=self.ask_db_authentication(db.name)
            auth_changed=False
            auth_changed = auth_changed or (not has_key and keyfile) 
            auth_changed = auth_changed or (db_key_filepath != keyfile)
            auth_changed = auth_changed or requires_password != bool(password)
            if auth_changed:
                self.fmap.remove_database([db_id])
                self.fmap.add_database(db_filepath, password, keyfile)
        self.refresh_table()
    
    def _set_name(self,db_id,new_name:str):
        self.fmap.set_db_name(db_id, new_name)
        self.refresh_table()

    def _set_autoload(self, autoload_list, set_auto:bool):
        self.fmap.set_autoload(autoload_list, set_auto)
        self.refresh_table()

    def _activate_databases(self,active_db_list):
        self.fmap.activate_databases(active_db_list)
        self.databasesActivationChange.emit(True)
        self.refresh_table()
    
    def _deactivate_databases(self,unactive_db_list):
        self.fmap.deactivate_databases(unactive_db_list)
        self.databasesActivationChange.emit(False)
        self.refresh_table()

    def _save_db_in_config(self, a_list, user):    
        self.fmap.save_db_in_config(a_list, user)
        self.refresh_table()

    def _remove_db_from_config(self, a_list, user):    
        self.fmap.remove_db_from_config(a_list, user)
        self.refresh_table()

    def _add_action_to_menu(self, text: str, is_enabled: bool, an_icon: QtGui.QIcon = None):
        """Adds an action to the menu interactively
        Args:
            text (str):text of menu
            an_icon (QtGui.QIcon, optional): Icon. Defaults to None.

        Returns:
            QAction: menu action
        """
        menu_itemxx = self.item_menu.addAction(text)
        if an_icon:
            menu_itemxx.setIcon(an_icon)
        menu_itemxx.setEnabled(is_enabled)
        return menu_itemxx

    def _get_id_key_list_from_selection(self,atrack) -> tuple[list, list]:
        """Gets a list of keys of the items selected

        Returns:
            tuple[list,list]: list of selected items, list of track lists
        """
        selindex = self.database_table.selectedIndexes()
        id_key_list = []
        track_list = []
        if len(atrack)>0:
            id_key_list.append(atrack[0])
            track_list.append(atrack)

        for selection in selindex:
            itm = self.twf.tablewidgetobj.itemFromIndex(selection)
            id_key = self.twf.get_key_value_from_item(itm)
            track = self.twf.get_track_of_item_in_table(itm)
            
            if id_key not in id_key_list:
                id_key_list.append(id_key)
                track_list.append(track)
        return id_key_list, track_list
    
    def _table_widget_data_changed(self, track: list[str], val: any, valtype: str, subtype: str):
        """Sets the changed information in table widget by user into the Structure

        Args:
            track (list[str]): _description_
            val (any): _description_
            valtype (str): _description_
            subtype (str): _description_
        """
        # print("before: %s",self.url_struct)
        processed_val = self.twf.check_restrictions.set_type_to_value(val, valtype, subtype)
        self.twf.set_tracked_value_to_dict(track, processed_val, self.db_struct, subtype, False)
        if track[1] == "DB autoload":
            self.fmap.set_autoload([track[0]],processed_val)
            
        if track[1] == "Name":
            self.fmap.set_db_name(track[0],processed_val)
        

    def _get_db_id(self,db:DatabaseInfo) -> str:
        db_id=None
        for iii, reg_db in enumerate(self.dbm.databases):
            if reg_db == db :
                db_id = iii
        if db_id is None:
            db_id=len(self.dbm.databases)
            log.info(f"{db_id} New database {db.name} Registered in user databases")
            self.dbm.databases.append(db)
            self.dbm.save()
        return str(db_id)

    def add_item_to_db_struct(self, db:DatabaseInfo):
        """Adds item to list"""
        self.twf.tablewidgetobj.clearSelection()
        db_id = self._get_db_id(db)
        self.db_struct.update(
                {
                db_id: {
                        "Name": db.name, 
                        "DB Filepath": db.db_path,
                        "DB Filename": db.db_file,
                        "DB active": str(db.active),
                        "DB autoload": str(db.autoload),
                        "Requires Password": str(db.requires_password),
                        "Has Encryption Key": str(db.has_key),
                        "Config": db.config_name,
                    },
                }
        )
        
    def _main_refresh_tablewidget(self):
        """Refresh the tablewidget"""
        # refresh
        self.twf.data_struct = self.db_struct
        # self.twf.set_show_dict()
        self.twf.refresh_tablewidget(self.db_struct, self.twf.modelobj, self.twf.tablewidgetobj)

    def _add_remove_icons_to_items(self, 
                                   id_key_list: list,         
                                   add_to: bool, 
                                   column_field: str, 
                                   the_icon: QtGui.QIcon = None
    ):
        """Adds icons to items

        Args:
            id_key_list (list): items to add icon
            add_to (bool) : True adds icons,False remove them
            column_field (str): Column name of the item
            the_icon (QtGui.QIcon, optional): Icon to set, None to remove. Defaults to None.
        """
        it_icon_dict = {}
        it_icon_dict = self.twf.icon_dict.copy()
        
        track_list = it_icon_dict["track_list"]
        icon_list = it_icon_dict["icon_list"]
        if add_to and the_icon is not None:
            # add icon to twf
            for id_key in id_key_list:
                track = [id_key, column_field]
                track_list.append(track)
                icon_list.append(the_icon)
            it_icon_dict.update({"track_list": track_list})
            it_icon_dict.update({"icon_list": icon_list})
        elif not add_to:
            pos_to_del_list = []
            for id_key in id_key_list:
                del_track = [id_key, column_field]
                for pos, track in enumerate(track_list):
                    if self._is_same_list(del_track, track):
                        pos_to_del_list.append(pos)
            new_track_list = []
            new_icon_list = []
            for pos, (a_track, an_icon) in enumerate(zip(track_list, icon_list)):
                if pos not in pos_to_del_list:
                    new_track_list.append(a_track)
                    new_icon_list.append(an_icon)
            it_icon_dict = {}
            it_icon_dict.update({"track_list": new_track_list})
            it_icon_dict.update({"icon_list": new_icon_list})
    
        self.twf.set_items_icons(it_icon_dict)
        self._main_refresh_tablewidget()
    
    def _is_same_list(self, list1: list, list2: list) -> bool:
        """Compares two lists

        Args:
            list1 (list): list1
            list2 (list): list2

        Returns:
            bool: True if the same,False if different
        """
        if len(list1) != len(list2):
            return False
        for iii, jjj in zip(list1, list2):
            if iii != jjj:
                return False
        return True
    

if __name__ == "__main__":
    pass