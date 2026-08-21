# class_provier_engine.py:
import os
from class_autocomplete_input import AutocompletePathFile
from class_file_manipulate import FileManipulate

FM = FileManipulate()
AC = AutocompletePathFile('', FM.get_app_path(),absolute_path=True, verbose=False , inquire=False)
   
class ProviderEngine:
    """Class uses Filemanipulate to verify a path exists, 
    if loader is not active path you can replace this to verify your path"""
    def verify_path(self,pathfile)->tuple[bool]:
        """Validate the input file with path.

        Args
        pathfilepath : str
        The input path and file name to be validated.

        Returns
        tuple[bool]
        (file_exist, is_file)"""
        return False, False
    
    def get_possible_path_list(self,path)->list[str]:
        """Use glob to find similar paths with patterns

        Args:
            path (str): path as pattern

        Returns:
            list: list of patterns found
        """
        return []
    
    def get_label_text(self)->str:
        """ Set the text of label over Treeview on path change event
        Returns:
            str: Text to display 
        """
        return ""
    
    def autocomplete_path(self, a_path_file)->str:
        """Autocompletes the paths. If only one possibility, will autocomplete. If many possibilities, will find

        Args:
            a_path_file (str): path to autocomplete

        Returns:
            str: autocompleted path
        """
        return ""
    
    def list_items_in_path(self,path)->list[str]:
        """returns directories and files in path"""
        return []
    
    def path_to_list(self, path)->list:
        """Converts a path string in a list"""
        return FM.path_to_list(path)
    
    def get_valid_path_from_text(self, txt):
        """Returns a valid path from the user text"""
        return "", "", ""
    
    def normalize_path(self,path:str)->str:
        return os.path.normpath(path)
    
    def set_default_path(self,path):
        (file_exist, is_file)=FM.validate_path_file(path)
        if file_exist and not is_file:
            AC.base_path=path
    
    def get_app_path(self):
        return FM.get_app_path()

class DefaultProviderEngine(ProviderEngine):
    """Class uses Filemanipulate to verify a path exists, 
    if loader is not active path you can replace this to verify your path"""
    def verify_path(self,pathfile):
        """Validate the input file with path.

        Args
        pathfilepath : str
        The input path and file name to be validated.

        Returns
        tuple[bool]
        (file_exist, is_file)"""
        return FM.validate_path_file(pathfile)
    
    def get_possible_path_list(self,path):
        """Use glob to find similar paths with patterns

        Args:
            path (str): path as pattern

        Returns:
            list: list of patterns found
        """
        options_list=AC._get_possible_path_list(path)
        mod_opt_lits=[]
        for opt in options_list:
            mod_opt_lits.append(os.path.abspath(opt))
        return mod_opt_lits
        
    
    def autocomplete_path(self, a_path_file):
        """Autocompletes the paths. If only one possibility, will autocomplete. If many possibilities, will find

        Args:
            a_path_file (str): path to autocomplete

        Returns:
            str: autocompleted path
        """
        return AC.autocomplete_path(a_path_file)
         
    
    def list_items_in_path(self,path):
        """returns directories and files in path"""
        try:
            return os.listdir(path)
        except:
            pass
        return []
    
    def path_to_list(self, path):
        """Converts a path string in a list (does not include mountpoint)
            Args
            path : str
            path to make list

            Returns
            list[str]
            path as list separated
        """
        return FM.path_to_list(path)
        
    def get_valid_path_from_text(self, txt):
        """Returns a valid path from the user text

        Args:
            txt (str): user string

        Returns:
            str: last valid path within string
        """
        try:
            txt=os.path.normpath(txt)
            [mount,path_nm]=FM.split_filepath_and_mountpoint(txt)
            file_exist, is_file=FM.validate_path_file(txt)
            if file_exist:
                return txt, mount, path_nm 
            file=FM.extract_filename(txt,True)
            path=FM.extract_path(txt,True)
            file_exist, is_file=FM.validate_path_file(path)
            if file_exist:
                return path, mount, path_nm 
            ppath=FM.extract_parent_path(txt,True)
            
            file_exist, is_file=FM.validate_path_file(ppath)
            if file_exist:
                return ppath, mount, path_nm 
        except:
            pass
        return "", mount, path_nm
    
    
    
    
    

