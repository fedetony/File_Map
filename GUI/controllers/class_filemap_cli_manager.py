# FileMap Cli Manager
import io
import logging
from contextlib import redirect_stdout

from controllers.class_configuration_manager import ConfigurationManager
from controllers.class_database_manager import DatabaseManager

from class_file_manipulate import FileManipulate
from class_autocomplete_input import *
from class_backup_actions import *
from widgets.ask_confirmation_dialog import *
from controllers.class_database_manager import *

from class_LogHandler import LM
log=LM.get_logger_with_handler("FileMapCli","debug",False,None)

class FileMapCliManager:
    """
    Coordinates configuration, DatabaseManager and FileMap CLI operations.

    Acts as the application's service layer between the GUI and the lower-level
    managers. Performs database activation, registration, configuration updates,
    and keeps the DatabaseManager synchronized with FileMap's state.
    """
    def __init__(self, 
                conf_manager:ConfigurationManager,
                dbm:DatabaseManager
                ):
        """
        Initialize managers and synchronize the initial active database state.
        """ 
        with redirect_stdout(LoggerWriter(log)):    
            # Get Filemap's inputs
            self.cfg = conf_manager
            self.dbm = dbm
            (self.file_list, self.password_list, 
            self.key_list, activate_list ) = self.dbm.get_file_pwd_key_lists()
            self.user_dialogs=ConfirmationDialog()
            self.ba= BackupActions(self.file_list,
                                self.password_list,
                                self.key_list,
                                self.user_dialogs.ask_confirmation
                                )
            self.cma = self.ba.cma
            self.fm=FileManipulate()
            for name, activate in zip(self.file_list,activate_list):
                if activate:
                    self.cma.activate_databases(name)
            self.set_active_databases_in_dbm()

    def save_db_in_config(self, db_id_list, user=True):
        """
        Save the selected databases to the configuration.

        Existing entries are updated; new entries are added.
        """
        for db in self._get_db_list_from_id_list(db_id_list):
            is_ok_db, is_ok_k, *_ = self.dbm.verify_db_paths(db)
            if is_ok_db and is_ok_k:
                self.cfg.save_database(db.config_dict, user)
        
    
    def _get_db_list_from_id_list(self,db_id_list)->list[DatabaseInfo]:
        """
        Convert a list of database IDs into DatabaseInfo objects.
        """
        the_dbs=[]
        for db_id in db_id_list:
            if isinstance(db_id,str):
                id_pos=int(db_id)
            elif isinstance(db_id,int):
                id_pos=db_id
            if id_pos >=0 and id_pos < len(self.dbm.databases):
                db=self.dbm.databases[id_pos]
                the_dbs.append(db)
        return the_dbs

    def set_db_name(self,db_id, new_name):
        """
        Rename a database in the DatabaseManager.
        """
        the_dbs=self._get_db_list_from_id_list([db_id])
        for db in the_dbs:
            db.name = new_name

    def set_autoload(self,autoload_list, set_auto:bool):
        """
        Enable or disable autoload for the selected databases.
        """
        the_dbs=self._get_db_list_from_id_list(autoload_list)
        for db in the_dbs:
            db.autoload = set_auto

    def activate_databases(self,db_id_list):
        """
        Activate the selected databases in FileMap and update their active state.
        """
        activation_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            is_ok_db, is_ok_k, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            if is_ok_db and is_ok_k:
                activation_list.append(db_filepath)
            else:
                if not is_ok_db:
                    log.error(f"The DB file could not be opened: {db.name} {db.db_file}")
                if not is_ok_k:
                    log.error(f"The Key file could not be opened: {db.name} {db.key_file}")
        for dbfname in activation_list:
            self.cma.activate_databases(dbfname)
        self.set_active_databases_in_dbm()
    
    def deactivate_databases(self,db_id_list):
        """
        Deactivate the selected databases in FileMap and update their active state.
        """
        deactivation_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            deactivation_list.append(db_filepath)
        for dbfname in deactivation_list:
            self.cma.deactivate_databases(dbfname)
        self.set_active_databases_in_dbm()
    
    def get_authentication_list(self,db_id_list:list[str])->list[tuple]:
        """
        Return authentication information for the selected databases.

        Returns:
            list[tuple]:
                (DatabaseInfo, db_path, requires_password, has_key, key_path)
        """
        authentication_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            authentication_list.append((db, db_filepath, db.requires_password, db.has_key, k_filepath))
        return authentication_list

    def remove_database(self,db_id_list):
        """
        Remove the selected databases from FileMap and the DatabaseManager.
        """
        removal_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            removal_list.append(db_filepath)
        # Remove in filemap    
        for dbfname in removal_list:
            self.cma.remove_database_file(dbfname)
        # Remove in dbm
        for db in the_dbs:
            self.dbm.remove_database(db)
        self.set_active_databases_in_dbm()
    
    def add_database(self,file_path,a_pwd=None,keyfile=None,activate=False):
        """
        Create a DatabaseInfo entry and register it with FileMap.
        """
        # Add to database manager
        file_we=FM.extract_filename(file_path,with_extension=True)
        file_woe=FM.extract_filename(file_path,with_extension=False)
        path_we=FM.extract_path(file_path,True)
        k_file = None
        k_path = None
        if keyfile:
            k_file = FM.extract_filename(keyfile)
            k_path = FM.extract_path(keyfile)
        db=DatabaseInfo(
            name = file_woe,
            db_path = path_we,
            db_file = file_we,
            requires_password = (a_pwd == True),
            key_path = k_path,
            key_file = k_file,
            user_database = True,
        )
        self.dbm.databases.append(db)
        self.dbm.save()
        # Add to filemap
        self.cma.file_list.append(file_path)
        self.cma.password_list.append(a_pwd)
        self.cma.key_list.append(keyfile)
        
        if activate:
            self.cma.activate_databases(file_path)

        self.set_active_databases_in_dbm()

    def get_autoload_db_id_list(self,db_id_list):
        """
        Split database IDs into autoload and non-autoload groups.
        """
        auto_db_list=[]
        notauto_db_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db_id, db in zip(db_id_list,the_dbs):
            if db.autoload:        
                auto_db_list.append(db_id)         
            else:
                notauto_db_list.append(db_id) 
        return auto_db_list, notauto_db_list

    def get_active_unactive_db_id_list(self,db_id_list):
        """
        Split database IDs into active and inactive groups.
        """
        active_db_list=[]
        unactive_db_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db_id, db in zip(db_id_list,the_dbs):
            if db.active:        
                active_db_list.append(db_id)         
            else:
                unactive_db_list.append(db_id) 
        return active_db_list, unactive_db_list
    
    def set_active_databases_in_dbm(self):
        """
        Synchronize DatabaseInfo.active with FileMap's active database list.
        """
        for db in self.dbm.databases:
            if isinstance(db,DatabaseInfo):
                _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
                if self.cma.is_database_active(db_filepath):
                    db.active=True
                else:
                    db.active=False



class LoggerWriter(io.TextIOBase):
    def __init__(self, logger:logging.Logger, level=logging.INFO):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, text):
        self.buffer += text

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line:
                self.logger.log(self.level, line)

        return len(text)

    def flush(self):
        if self.buffer:
            self.logger.log(self.level, self.buffer)
            self.buffer = ""
    
    def isatty(self): #Accept colors from rich
        return True
    
