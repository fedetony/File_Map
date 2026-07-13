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

        self.load()

    # -------------------------------------------------
    # IO
    # -------------------------------------------------

    def load(self):
        with open(self.config_file, "r", encoding="utf-8") as f:
            self.general = yaml.safe_load(f) or {}

    def save(self):

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.general,
                f,
                sort_keys=False
            )

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
    def behavior(self):
        return self.general["behavior"]

    @property
    def bundled_databases(self):
        return self.general.get("default_databases", [])

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