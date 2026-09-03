from pathlib import Path
import yaml


class ConfigurationManager:
    """
    Owns the application's configuration.

    Responsible for:
        - loading/saving general_config.yml
        - exposing convenient properties
        - never interacting with the GUI
    """

    def __init__(self, config_file):

        self.config_file = Path(config_file)

        self.general = {}
        self.user ={}

        self.load()
        self.load_user()
        
    # -------------------------------------------------
    # IO
    # -------------------------------------------------

    def load(self):
        with open(self.config_file, "r", encoding="utf-8") as f:
            self.general = yaml.safe_load(f) or {}

    def save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.general, f, sort_keys=False)
    
    def load_user(self):
        if self.user_database_file.exists():
            with open(self.user_database_file, "r", encoding="utf-8") as f:
                self.user = yaml.safe_load(f) or {}
        else:
            self.user = {"databases": []}
    
    def save_user(self):
        with open(self.user_database_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.user, f, sort_keys=False)
    
    def save_database(self, database, user=True):
        store = self.user if user else self.general
        key = "databases" if user else "default_databases"
        save = self.save_user if user else self.save

        databases = store.setdefault(key, [])

        for i, db in enumerate(databases):
            if (
                db["db_file"] == database["db_file"] and
                db["db_path"] == database["db_path"]
            ):
                databases[i] = database
                save()
                return

        databases.append(database)
        save()

    def remove_database(self, database, user=True):
        """
        Remove a database from the selected configuration.

        Args:
            database (dict): Database configuration dictionary.
            user (bool): True for the user configuration,
                        False for the bundled configuration.
        """
        if user:
            databases = self.user.setdefault("databases", [])
        else:
            databases = self.general.setdefault("default_databases", [])

        databases[:] = [
            db for db in databases
            if not (
                db.get("db_file") == database.get("db_file")
                and db.get("db_path") == database.get("db_path")
            )
        ]

        if user:
            self.save_user()
        else:
            self.save()

    # -------------------------------------------------
    # Properties
    # -------------------------------------------------

    @property
    def paths(self):
        return self.general["paths"]

    @property
    def ui(self):
        return self.general["ui"]
    
    @property
    def export(self):
        return self.general["export"]

    @property
    def behavior(self):
        return self.general["behavior"]

    @property
    def bundled_databases(self):
        return self.general.get("default_databases", [])

    @property
    def user_databases(self):
        return self.user.setdefault("databases", [])

    @property
    def config_directory(self):
        return Path(self.paths["config_dir"])

    @property
    def database_directory(self):
        return Path(self.paths["database_dir"])

    @property
    def user_database_file(self):

        return (
            self.config_directory /
            self.paths["user_databases"]
        )

    @property
    def log_directory(self):

        return Path(self.paths["log_dir"])

    @property
    def logfile(self):

        return self.log_directory / self.paths["log_file"]

    # -------------------------------------------------
    # Default databases
    # -------------------------------------------------

    def add_default_database(self, database):
        self._add_to_list(
            self.general,
            "default_databases",
            database,
            self.save,
        )

    def remove_default_database(self, database):
        self._remove_from_list(
            self.general,
            "default_databases",
            database,
            self.save,
        )

    def update_default_database(self, old, new):
        return self._replace_in_list(
            self.general,
            "default_databases",
            old,
            new,
            self.save,
        )

    # -------------------------------------------------
    # User databases
    # -------------------------------------------------

    def add_user_database(self, database):
        self._add_to_list(
            self.user,
            "databases",
            database,
            self.save_user,
        )

    def remove_user_database(self, database):
        self._remove_from_list(
            self.user,
            "databases",
            database,
            self.save_user,
        )

    def update_user_database(self, old, new):
        return self._replace_in_list(
            self.user,
            "databases",
            old,
            new,
            self.save_user,
        )

    # -------------------------------------------------
    # Generic helpers
    # -------------------------------------------------

    def _add_to_list(self, store, key, value, save_func):
        items = store.setdefault(key, [])

        if value not in items:
            items.append(value)
            save_func()


    def _remove_from_list(self, store, key, value, save_func):
        items = store.setdefault(key, [])

        if value in items:
            items.remove(value)
            save_func()


    def _replace_in_list(self, store, key, old, new, save_func):
        items = store.setdefault(key, [])

        try:
            index = items.index(old)
        except ValueError:
            return False

        items[index] = new
        save_func()
        return True

