# database manager
from pathlib import Path
import yaml
import os

from controllers.class_database_info import DatabaseInfo
from controllers.class_configuration_manager import ConfigurationManager
from widgets.database_auth_dialog import DatabaseAuthDialog
from class_file_manipulate import FileManipulate
FM = FileManipulate()

from class_LogHandler import LM
log=LM.get_logger_with_handler("DBManager","debug",False,None)

class DatabaseManager:
    """
    This class only interact with the configuration in Yml File
    Keeps the information syncronizes between the configuration 
    and user selection.
    """
    def __init__(self, config_manager:ConfigurationManager):
        self.cfg = config_manager
        self.databases = []
        self.load()
    
    
    def load(self):
        """
        Load all configured databases into the manager.

        Clears the current list and loads both bundled and
        user database definitions.
        """
        self.databases.clear()
        self.load_default_databases()
        self.load_user_databases()
    
    def load_default_databases(self):
        """
        Load bundled database definitions from configuration.
        """
        for db in self.cfg.bundled_databases:
            self.databases.append(
                self._database_from_config(db, False)
            )

    def load_user_databases(self):
        """
        Load user database definitions from configuration.
        """
        for db in self.cfg.user_databases:
            self.databases.append(
                self._database_from_config(db, True)
            )
    
    
    def _database_from_config(self, db_dict, user_database):
        """
        Create a DatabaseInfo object from a configuration dictionary.

        Resolves available paths and marks the database source
        as user or bundled configuration.
        """
        db = DatabaseInfo(
            name=db_dict["name"],
            db_path=db_dict.get("db_path"),
            db_file=db_dict["db_file"],
            requires_password=db_dict.get("requires_password", False),
            key_path=db_dict.get("key_path"),
            key_file=db_dict.get("key_file"),
            autoload=db_dict.get("autoload", True),
            active=db_dict.get("autoload", False),
            user_database=user_database,
        )

        is_ok = self._resolve_database_paths(db)
        if not is_ok:
            log.warning(f"Filepaths could not be verified for:{db_dict}")

        return db
    
    def _resolve_database_paths(self, db: DatabaseInfo):
        """
        Resolve and update database paths using the filesystem.

        Returns:
            bool: True if database and key paths are valid.
        """
        is_ok_db, is_ok_k, db_filepath, k_filepath = self.verify_db_paths(db)

        if is_ok_db and db_filepath:
            db.db_path = FM.extract_path(db_filepath)

        if is_ok_k and k_filepath:
            db.key_path = FM.extract_path(k_filepath)

        return is_ok_db and is_ok_k

    def save(self):
        """
        Save all user databases to the user configuration.

        Bundled/default databases are not modified.
        """
        self.cfg.user["databases"] = [
            {
                "name": db.name,
                "db_path": db.db_path,
                "db_file": db.db_file,
                "requires_password": db.requires_password,
                "key_path": db.key_path,
                "key_file": db.key_file,
                "autoload": db.autoload,
            }
            for db in self.databases
            if db.user_database
        ]
        self.cfg.save_user()
    
    def append_database(self, filename):
        """
        Create and register a new user database from a file.
        """
        p = Path(filename)
        db = DatabaseInfo(
            name=p.stem,
            db_path=str(p.parent),
            db_file=p.name,
            requires_password=False,
            key_path=None,
            key_file=None,
            user_database=True
        )
        auth_dialog=DatabaseAuthDialog(db.name,db.requires_password,db.has_key)
        auth_dialog.values()
        self.databases.append(db)
        self.save()

    def remove_database(self, db: DatabaseInfo):
        """
        Remove a database from the manager and save the change.
        """
        if db in self.databases:
            self.databases.remove(db)
            self.save()
    
    def activate(self, db: DatabaseInfo):
        """
        Mark a database as active.
        """
        db.active = True
    
    def deactivate(self, db: DatabaseInfo):
        """
        Mark a database as inactive.
        """
        db.active = False

    def create_database(self, filename):
        """
        Create a new database file and register it.
        """
        Path(filename).touch(exist_ok=True)
        self.append_database(filename)
    
    @property
    def active_databases(self):
        """
        Return the list of currently active databases.
        """
        return [db for db in self.databases if db.active]
    
    # def activate_database(self, db_file):
    #     """
    #     Open a database, requesting authentication if required.
    #     """
    #     try:
    #         self.open_database(db_file)
    #     except DatabasePasswordRequired:
    #         dialog = DatabaseAuthDialog(
    #             db_file,
    #             need_password=True,
    #             need_key=False
    #         )
    #         if dialog.exec():
    #             password, key = dialog.values()
    #             self.open_database(
    #                 db_file,
    #                 password,
    #                 key
    #             )

    #     except DatabaseKeyRequired:
    #         dialog = DatabaseAuthDialog(
    #             db_file,
    #             need_password=False,
    #             need_key=True
    #         )
    #         if dialog.exec():
    #             password, key = dialog.values()
    #             self.open_database(
    #                 db_file,
    #                 password,
    #                 key
    #             )

    # def open_database(self,*args):
    #     print(args)
    
    def verify_db_paths(self,db:DatabaseInfo):
        """Verify if paths are ok and exist in db Info item.

        Args:
            db (DatabaseInfo): Item of database

        Returns:
            tuple: (is_ok_db, is_ok_k, db_filepath, k_filepath)
        """
        db_filepath, k_filepath = None, None
        if not db.db_path:
            db_path=os.path.join(FM.get_app_path(),self.cfg.paths["database_dir"])
        else:
            db_path=db.db_path
        db_filepath=os.path.join(db_path,db.db_file)
        file_exist, is_file=FM.validate_path_file(db_filepath)
        if db.key_file:
            if not db.key_path:
                k_path=os.path.join(FM.get_app_path(),self.cfg.paths["database_dir"])
            else:
                k_path=db.key_path
            k_filepath=os.path.join(k_path,db.key_file)
            kfile_exist, kis_file=FM.validate_path_file(k_filepath)
            if kfile_exist and kis_file:
                is_ok_k=True
            else:
                is_ok_k=False
        else:
            is_ok_k=True
            
        is_ok_db=False
        if file_exist and is_file:
            is_ok_db=True
        return is_ok_db,is_ok_k, db_filepath, k_filepath
        
    def get_file_pwd_key_lists(self)->tuple[list]:
        """Gets the valid content of databases in the lists

        Returns:
            _type_: (file_list, password_list, key_list , activation_list)
        """
        file_list = []
        password_list = []
        key_list = []
        activation_list = []
        for db in self.databases:
            if isinstance(db,DatabaseInfo):
                is_ok_db,is_ok_k, db_filepath, k_filepath = self.verify_db_paths(db)
                if is_ok_db and is_ok_k:
                    file_list.append(db_filepath)
                    password_list.append(db.requires_password)
                    key_list.append(k_filepath)
                    activation_list.append(db.autoload)
                else:
                    if not is_ok_db:
                        log.error(f"Could not load {db_filepath}, check the configuration, file does not exist!")
                    if not is_ok_k:
                        log.error(f"Could not load {k_filepath}, check the configuration, file does not exist!")

        
        return file_list, password_list, key_list , activation_list             



class DatabasePasswordRequired(Exception):
    pass


class DatabaseKeyRequired(Exception):
    pass

if __name__ == "__main__":
    pass