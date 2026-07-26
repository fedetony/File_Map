# FileMap Cli Manager

from controllers.class_configuration_manager import ConfigurationManager
from controllers.class_database_manager import DatabaseManager

from class_file_manipulate import FileManipulate
from class_autocomplete_input import *
from class_backup_actions import *
from widgets.ask_confirmation_dialog import *

from class_LogHandler import LM
log=LM.get_logger_with_handler("DBManager","debug",True,None)

class FileMapCliManager:

    def __init__(self, 
                file_list:list,
                password_list:list,
                key_list:list,
                conf_manager:ConfigurationManager,
                dbm:DatabaseManager
                ):
        
        # Get Filemap's inputs
        self.file_list = file_list
        self.password_list = password_list
        self.key_list = key_list
        self.cfg = conf_manager
        self.dbm = dbm
        self.user_dialogs=ConfirmationDialog()
        self.ba= BackupActions(self.file_list,
                               self.password_list,
                               self.key_list,
                               self.user_dialogs.ask_confirmation
                               )
        self.cma = self.ba.cma
        self.fm=FileManipulate()

    
