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

    user_database: bool = False

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

