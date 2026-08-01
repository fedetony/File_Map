import os,sys
from PyQt6.QtCore import Qt
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
import yaml

#Configure logger before importing classes (so they become child loggers)
import class_LogHandler
log_file = None # do stream handler
LM = class_LogHandler.init_logger_manager(log_file,emit_record = True)
log = LM.get_logger(__name__)
log.info("Application starting...")

from class_file_manipulate import *
FM = FileManipulate()
ap= FM.get_app_path()
config_path=os.path.join(ap,"config")

general_config_file=os.path.join(config_path,"filemap_configuration.yml")

from controllers.class_configuration_manager import *
from controllers.class_database_manager import *
conf_manager=ConfigurationManager(general_config_file)
    
# Filemap main action classes
from class_mapping_actions import *
from class_backup_actions import *

# -----------------------------
# Main Window
# -----------------------------
from main_window import *
from widgets.database_startup_dialog import *

# -----------------------------
# Run App
# -----------------------------
def main():

    app = QApplication(sys.argv)
    conf_manager = ConfigurationManager(general_config_file)
    
    dialog = DatabaseStartupDialog(conf_manager)

    if dialog.exec():
        win = MainWindow(dialog.conf,dialog.dbm)
        win.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
