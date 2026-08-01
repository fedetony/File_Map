# database manager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseInfo:

    name: str

    db_path: str | None
    db_file: str

    requires_password: bool

    key_path: str | None
    key_file: str | None

    autoload: bool = True
    active: bool = False

    user_database: bool | None = None

    @property
    def database_filepath(self) -> Path:

        if self.db_path:
            return Path(self.db_path) / self.db_file

        return Path(self.db_file)

    @property
    def keyfile_filepath(self):

        if self.key_file is None:
            return None

        if self.key_path:
            return Path(self.key_path) / self.key_file

        return Path(self.key_file)
    
    @property
    def has_key(self):
        if self.key_file:
            return True
        return False
    
    @property
    def config_dict(self):
        list_cfg=["name", "db_path", "db_file", "requires_password", "key_path", "key_file", "autoload"]
        cfg_dict={}
        for cfgitem in list_cfg:
            cfg_dict[cfgitem]=getattr(self,cfgitem)
        return cfg_dict  

    @property
    def config_name(self) -> str:
        if self.user_database is True:
            return "User"
        if self.user_database is False:
            return "Default"
        return "None" 

