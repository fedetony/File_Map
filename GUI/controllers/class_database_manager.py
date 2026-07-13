# database manager
from pathlib import Path
import yaml

from controllers.class_database_info import DatabaseInfo
from controllers.class_configuration_manager import ConfigurationManager

class DatabaseManager:

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

    def remove_database(self, db):
        if db in self.databases:
            self.databases.remove(db)
            self.save()
    
    def activate(self, db):
        db.active = True
    
    def deactivate(self, db):
        db.active = False

    def create_database(self, filename):
        Path(filename).touch(exist_ok=True)
        self.append_database(filename)
    
    @property
    def active_databases(self):
        return [db for db in self.databases if db.active]

    