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
log=LM.get_logger_with_handler("DBManager","debug",True,None)

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
        self.databases.clear()
        self.load_default_databases()
        self.load_user_databases()
    
    def load_default_databases(self):
        defaults = self.cfg.bundled_databases# self.config.get("default_databases", [])
        for db in defaults:
            self.databases.append(
                DatabaseInfo(
                    name=db["name"],
                    db_path=db.get("db_path"),
                    db_file=db["db_file"],
                    requires_password=db.get(
                        "requires_password", False),
                    key_path=db.get("key_path"),
                    key_file=db.get("key_file"),
                    autoload=db.get("autoload", True),
                    active=db.get("autoload", False),
                    user_database=False
                )
            )
    
    def load_user_databases(self):

        filename = (
            Path(self.cfg.config_directory)
            / self.cfg.user_database_file 
        ) #self.config["paths"]["config_dir"]) #self.config["paths"]["user_databases"]
        if not filename.exists():
            return
        with open(filename, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for db in data.get("databases", []):
            self.databases.append(
                DatabaseInfo(
                    name=db["name"],
                    db_path=db.get("db_path"),
                    db_file=db["db_file"],
                    requires_password=db.get(
                        "requires_password", False),
                    key_path=db.get("key_path"),
                    key_file=db.get("key_file"),
                    autoload=db.get("autoload", True),
                    active=db.get("autoload", False),
                    user_database=True
                )
            )

    def save(self):
        filename = self.cfg.user_database_file
        filename.parent.mkdir(parents=True, exist_ok=True)
        output = {"databases": []}
        for db in self.databases:
            if not db.user_database:
                continue
            output["databases"].append({
                "name": db.name,
                "db_path": db.db_path,
                "db_file": db.db_file,
                "requires_password": db.requires_password,
                "key_path": db.key_path,
                "key_file": db.key_file,
                "autoload": db.autoload
            })

        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(output,f,sort_keys=False)
    
    def append_database(self, filename):
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

        self.databases.append(db)
        self.save()

    def remove_database(self, db:DatabaseInfo):
        if db in self.databases:
            self.databases.remove(db)
            self.save()
    
    def activate(self, db:DatabaseInfo):
        db.active = True
    
    def deactivate(self, db:DatabaseInfo):
        db.active = False

    def create_database(self, filename):
        Path(filename).touch(exist_ok=True)
        self.append_database(filename)
    
    @property
    def active_databases(self):
        return [db for db in self.databases if db.active]
    
    def activate_database(self, db_file):
        try:
            self.open_database(db_file)
        except DatabasePasswordRequired:
            dialog = DatabaseAuthDialog(
                db_file,
                need_password=True,
                need_key=False
            )
            if dialog.exec():
                password, key = dialog.values()
                self.open_database(
                    db_file,
                    password,
                    key
                )

        except DatabaseKeyRequired:
            dialog = DatabaseAuthDialog(
                db_file,
                need_password=False,
                need_key=True
            )
            if dialog.exec():
                password, key = dialog.values()
                self.open_database(
                    db_file,
                    password,
                    key
                )

    def open_database(self,*args):
        print(args)
    
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