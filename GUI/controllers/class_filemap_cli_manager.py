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

from class_LogHandler import LM
log=LM.get_logger_with_handler("FileMapCli","debug",False,None)

class FileMapCliManager:

    def __init__(self, 
                conf_manager:ConfigurationManager,
                dbm:DatabaseManager
                ):
        
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
    
