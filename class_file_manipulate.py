########################
# F.garcia
# creation: 03.02.2025
########################
import os
import re
import sys
import glob as gb
from datetime import datetime
import shutil
import psutil
import json
from rich.progress import Progress

ALLOWED_CHARS = 'áéíóúüöäÜÖÄÁÉÍÓÚçÇabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ -'

class FileManipulate:
    def __init__(self):
        self.file = None

    @staticmethod
    def path_to_file_structure_dict(path:str,file_tup):
        """Converts a path string in filepath of a map into a file structure dictionary

        Args:
            path (str): _description_
            file_tup (any): file contents
            
        Returns:
            dict: Example: path='/path1/path2/path3'
                        file_tup='file.txt'
            returns             
            {'path1': [{'path2': [{'path3': ['file.txt']}]}]}
        """
        path_split=os.path.split(path)
        while len(path_split)==2 and path_split[1]!='':
            f_s={path_split[1]:[file_tup]}
            file_tup=f_s
            path_split=os.path.split(path_split[0])
        return file_tup

    def merge_file_structure_lists(self,list1:list,list2:list)->list:
        """Merges two file structure lists. will not check for repeated items, will just add them.
        If dictionaries in contents, will merge the dictionaries. 
        Args:
            list1 (list): list
            list2 (list): second list

        Returns:
            list: merged list
        """
        num_dicts1=0
        merged_list=[]
        dict_list=[]
        for item1 in list1:
            if isinstance(item1, dict):
                num_dicts1=num_dicts1+1
                dict_list.append(item1)
            else:
                merged_list.append(item1)
        num_dicts2=0
        for item2 in list2:
            if isinstance(item2, dict):
                num_dicts2=num_dicts2+1
                dict_list.append(item2)
            else:
                merged_list.append(item2)
        if len(dict_list)==0:
            return merged_list
        elif len(dict_list)==1:
            return dict_list+merged_list
        else:
            while len(dict_list)>0:
                dict1=dict_list.pop(0)
                has_merged=False
                for iii,dict2 in enumerate(dict_list):
                    m_d=self.merge_file_structure_dicts(dict1,dict2) # returs a list
                    if len(m_d)==1:
                        has_merged=True
                        break
                if has_merged:
                    dict_list.pop(iii)
                    merged_list=m_d+merged_list
                else:
                    merged_list=[dict1]+merged_list #self.merge_file_structure_lists(m_d,merged_list)
        return merged_list

    def merge_file_structure_dicts(self,dict1:dict, dict2:dict)->list:
        """Merges two dictionaries when keys are shared.

        Args:
            dict1 (dict): file structure dictionary
            dict2 (dict): second file structure dictionary

        Returns:
            list: list containing one merged dictionary or 2 different dictionaries.
        """
        merged_dict = {}
        a_set=set(list(dict1.keys()) + list(dict2.keys()))
        if len(a_set)==2:
            return [dict1,dict2]
        if len(a_set)==1:
            merged_list=[]
            for key in a_set:
                merged_list=merged_list+self.merge_file_structure_lists(dict1[key],dict2[key])
                merged_dict.update({key:merged_list})
            return [merged_dict]   
        return []

    def split_filepath_and_mountpoint(self,path):
        """Separates the mountpoint from the path. Works only if device is mounted.

        Args:
            path (str): path to be separated

        Returns:
            list(str): list of paths. [mount,path]
        """
        dev_mount=self.get_mounted_disks()
        dm_path_list=['',path]
        for dm in dev_mount:
            if dm[0] in path:
                dm_path_list=path.split(dm[0])
                dm_path_list[0]=dm[0]
            elif dm[1] in path and dm[0]!=dm[1]:
                dm_path_list=path.split(dm[1])
                dm_path_list[0]=dm[1]
        return dm_path_list    
    
    def copy_file(self,file_path, new_file_path):
        """copy a file using shutil.copy2 to preserve metadata

        Args:
            file_path (str): path and file origin
            new_file_path (str): path and file destination

        Returns:
            bool: True if moved
        """
        try:
            if os.path.exists(file_path):
                new_folder_path=self.extract_path(new_file_path,True)
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)    
                shutil.copy2(file_path, new_file_path) # Use copy2 to preserve metadata
                return True
        except Exception as eee:
            print(f"Could not copy file! {file_path} to {new_file_path}\nCopy Error: {eee}")
            return False

    def move_file(self,file_path, new_file_path):
        """Move file or rename.

        Args:
            file_path (str): path and file origin
            new_file_path (str): path and file destination

        Returns:
            bool: True if moved
        """
        if self.copy_file(file_path, new_file_path):
            # Remove the original file if it was copied
            return self.delete_file(file_path)
        return False
    
    def delete_file(self,file_path):
        """Delete file.

        Args:
            file_path (_type_): path and file origin

        Returns:
            bool: True if removed
        """
        try:
            os.remove(file_path)  
            return True
        except Exception as eee:
            print(f"Could not remove {file_path}\nDelete Error: {eee}")
        return False
    
    def copy_folder(self,src_path: str, dst_path: str) -> bool:
        """
        Recursively copies the contents of src_path to dst_path.
        Args:
            src_path (str): The source directory path.
            dst_path (str): The destination directory path.
        Returns:
            bool: True if all files and folders were copied
        """
            
        # Check if the source and destination paths exist
        if not os.path.exists(src_path):
            print(f"Source path '{src_path}' does not exist.")
            return False

        # Create parent directories in dst_path if they don't exist
        for dir_name, dirs, _ in os.walk(dst_path):
            dir_path = os.path.join(dir_name)
            while not os.path.exists(os.path.dirname(dir_path)):
                try:
                    os.makedirs(dir_path)
                except OSError as eee:
                    print(f"Error creating directory {dir_path}: {eee}")
                    return False
                
        all_copied=True
        for item in os.listdir(src_path):
            try:
                src_item = os.path.join(src_path, item)
                dst_item = os.path.join(dst_path, item)
                # If the current item is a file
                if os.path.isfile(src_item):
                    copy_result=self.copy_file(src_item, dst_item)  
                    if not copy_result:
                        print(f"{src_item} Not copied !!!")
                # If the current item is a directory
                elif os.path.isdir(src_item):
                    copy_result=self.copy_folder(src_item, dst_item)
                    if not copy_result:
                        print(f"Not copied items in folder {src_item}!!!")
                all_copied &= copy_result
            except Exception as eee:
                print(f"Error Coping folder {src_path}: {eee}")
                all_copied = False
        return all_copied
    
    def move_folder(self,src_path: str, dst_path: str,remove_empty=True) -> bool:
        """
        Recursively moves the contents of src_path to dst_path.

        Args:
            src_path (str): The source directory path.
            dst_path (str): The destination directory path.
        Returns:
            bool: True if all files and folders were copied
        """
        
        # Check if the source and destination paths exist
        if not os.path.exists(src_path):
            print(f"Source path '{src_path}' does not exist.")
            return False

        # Create parent directories in dst_path if they don't exist
        for dir_name, dirs, _ in os.walk(dst_path):
            dir_path = os.path.join(dir_name)
            while not os.path.exists(os.path.dirname(dir_path)):
                try:
                    os.makedirs(dir_path)
                except OSError as eee:
                    print(f"Error creating directory {dir_path}: {eee}")
                    return False
                
        all_moved=True
        for item in os.listdir(src_path):
            try:
                src_item = os.path.join(src_path, item)
                dst_item = os.path.join(dst_path, item)
                # If the current item is a file
                if os.path.isfile(src_item):
                    moved_result=self.move_file(src_item, dst_item)  
                    if not moved_result:
                        print(f"{src_item} Not copied !!!")  
                # If the current item is a directory
                elif os.path.isdir(src_item):
                    moved_result=self.move_folder(src_item, dst_item)
                    if not moved_result:
                        print(f"Not moved items in folder {src_item}!!!")
                    else:
                        self.remove_empty_folders(src_item)
                all_moved &= moved_result
            except Exception as eee:
                print(f"Error Moving folder {src_path}: {eee}")
                all_moved= False
        if all_moved and remove_empty:
            os.rmdir(src_path)  # Remove the empty folder        
        return all_moved
    
    def delete_folder_recursive(self,directory):
        """
        Recursively deletes all files and subdirectories in the given directory.
        
        Args:
            directory (str): The path of the directory to be deleted.
            
        Returns:
            bool: True if all items were successfully deleted, False otherwise.
        """

        try:
            # Iterate over each item in the directory
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                # If it's a file, delete it
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    
                # If it's a folder, recursively call this function on it
                elif os.path.isdir(item_path):
                    if not self.delete_folder_recursive(item_path):  # Recursively check the subdirectory
                        return False
                    
            # After deleting all items in the directory and its subdirectories,
            # remove the empty directory itself.
            try:
                os.rmdir(directory)
            except OSError:  # If the directory is not empty, this will fail
                pass
            
            return True
        
        except FileNotFoundError:
            print(f"Directory '{directory}' does not exist.")
            return False

    def delete_files_folders(self,file_folder_list):
        """
        Recursively deletes all files and subdirectories in the given directory or any file given in the list.
        
        Args:
            file_folder_list (list): List of paths or files to be deleted.
            
        Returns:
            bool: True if all items were successfully deleted, False otherwise.
        """
        # Iterate over each item in the directory
        for iii,item_path in enumerate(file_folder_list):
            try:
                deleted_all=True
                if os.path.exists(item_path):
                    # If it's a file, delete it
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    # If it's a folder, recursively call this function on it
                    elif os.path.isdir(item_path):
                        result_del = self.delete_folder_recursive(item_path)  # Recursively check the subdirectory
                        if not result_del:
                            print(f"Not all files deleted on folder '{file_folder_list[iii]}'.")
                        deleted_all &= result_del
                else:
                    print(f"Item '{file_folder_list[iii]}' does nor exist.") 
            except Exception as eee:
                print(f"Issue deleting item '{file_folder_list[iii]}': {eee}.")       
        return deleted_all 

    def clean_filename(self, filename, allowed_chars=ALLOWED_CHARS):
        """Remove all undesired characters from a file name while preserving the file extension.

        Args:
            filename (str): The file name to be cleaned.
            allowed_chars (str): A string of allowed characters. Defaults to 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ -'.

        Returns:
            str: The cleaned file name.
        """
        base =self.extract_filename(filename,False)
        baseext=self.extract_filename(filename,True)
        extension = baseext.replace(base,'')
        base = base.strip("¿?")
        cleaned_base = re.sub('[^' + allowed_chars + ']', '', base)
        return cleaned_base + extension
    
    @staticmethod
    def fix_path_separators(pathfile):
        # to fix the separators
        try:
            splitted_path=os.path.split(pathfile)
            end_path=''
            for iii,sss in enumerate(splitted_path):
                if iii==0:
                    end_path=sss
                else:
                    end_path=end_path+os.sep+sss
        except:
            return pathfile
        return end_path

    @staticmethod
    def get_file_list(directory,extension:str=None):
        """
        Returns a list of file names with .txt extension from the given directory.

        Args:
            directory (str): The path to the directory you want to search for txt files.

        Returns:
            list: A list of file names with extension.
        """

        # Check if the provided directory exists
        if not os.path.exists(directory):
            return None

        # Initialize an empty list to store the files
        list_files = []

        # Iterate over each item in the directory
        for filename in os.listdir(directory):
            # Check if the file has a .txt extension and is actually a file (not a dir)
            if extension and extension != "":
                if filename.endswith(extension) and os.path.isfile(os.path.join(directory, filename)):
                    # Add the full path of the file to the list
                    list_files.append(filename)
            else:
                if os.path.isfile(os.path.join(directory, filename)):
                    list_files.append(filename)

        return list_files


    @staticmethod
    def get_mounted_disks() ->list:
        """returns a list of mounted devices  and mountpoints. HDD partitions,CDs DVDs,USBs.

        Returns:
            list[tuple]: Lists of (device,mountpoint) for each device
        """
        disk_dm_list=[]
        for disk in psutil.disk_partitions(all=True):
            # print(f"Device: {disk.device}, Mount Point: {disk.mountpoint}")
            disk_dm_list.append((disk.device,disk.mountpoint))
        return disk_dm_list
    
    @staticmethod
    def get_modified_date(file_path):
        """Gets modified date in register

        Args:
            file_path (str): path to file

        Returns:
            datetime: time stamp 
        """
        return datetime.fromtimestamp(os.path.getmtime(file_path))

    @staticmethod
    def get_accessed_date(file_path):
        """Gets accessed date in register

        Args:
            file_path (str): path to file

        Returns:
            datetime: time stamp 
        """
        return datetime.fromtimestamp(os.path.getatime(file_path))

    @staticmethod
    def get_created_date(file_path):
        """Gets created date in register

        Args:
            file_path (str): path to file

        Returns:
            datetime: time stamp 
        """
        return datetime.fromtimestamp(os.path.getatime(file_path))

    @staticmethod
    def get_file_size(file_path):
        """Gets file size in bits.
            value/(1024*1024) -> Mb

        Args:
            file_path (str): path and filename

        Returns:
            int: value in bits, -1 if error
        """
        size=os.path.getsize(file_path)
        if size:
            return size
        return -1
    
    @staticmethod
    def get_string_justified(a_str,is_left,size):
        """Returns a string of size adding spaces to the left or right. If str size is bigger, returns the string"""
        l_str=len(a_str)
        if l_str>=size:
            return a_str
        elif is_left and l_str<size:
            return a_str+''.join(' ' for _ in range(size-l_str+1))	
        elif not is_left and l_str<size:
            return ''.join(' ' for _ in range(size-l_str+1))+a_str

    def save_dict_to_json(self,filename,info_dict):
        """Saves a json file returns if file was saved

        Args:
            a_filename (str, optional): file name with path.
        """
        #filename = os.path.join(path, fn)
        try:
            # python dictionary with key value pairs
            # create json object from dictionary
            js = json.dumps(info_dict, default=vars)
            # open file for writing, "w"

            with open(filename, "w", encoding="utf-8") as fff:
                # write json object to file
                fff.write(js)
                # close file
                fff.close()
            return True
        except (PermissionError, FileExistsError, FileNotFoundError) as e:
                    print("Json File :%s was not saved", filename)
                    print(e)
        return False
    
    def load_dict_to_json(self, a_filename: str ):
        """Opens a json file and returns a dictionary

        Args:
            a_filename (str, optional): file name with path.
        """
        if a_filename is not None:
            try:
                if not os.path.exists(a_filename):
                    raise FileNotFoundError
                with open(a_filename, encoding="utf-8") as fff:
                    data = fff.read()
                # reconstructing the data as a dictionary
                fff.close()
                js_data = json.loads(data)
                return js_data
            except (PermissionError, FileExistsError, FileNotFoundError) as e:
                print("Json File: %s can not be opened", a_filename)
                print(e)
        return None
    
    def repair_list_tuple_in_file_structure(self,file_structure:dict)->dict:
        """ When file struct is imported from json files, load changes tuples into lists, this 
        routine turns back to tuples the lists. 

        Args:
            file_structure (dict): file structure to repair list to tuple
        Returns:
            dict: Corrected file structure
        """
        fs=file_structure #.copy()
        for key,value in fs.items():
            if isinstance(value,list):
                for pos,item in enumerate(value):
                    if isinstance(item,list):
                       file_structure[key][pos]=tuple(item) 
                    elif isinstance(item,tuple):
                        pass
                    elif isinstance(item,dict):
                        file_structure[key][pos]=self.repair_list_tuple_in_file_structure(item)
        return file_structure

    def get_size_str_formatted(self,file_size,o_size=11,is_left_justified=False):
        """
        Returns the size of a file in bytes, MB, GB, TB, etc.
        
        Parameters:
            file_path (str): The path to the file
        
        Returns:
            str: A string representing the file size with units (By, KB, MB, GB, TB)
        """
        if not file_size:
            return self.get_string_justified(str(None),is_left_justified,o_size)
        # import math
        if not isinstance(file_size, (int, float)):
            raise ValueError("Invalid input")
        if file_size < 0:
            return f'{file_size} ER'
        # Define a list of unit names and their corresponding sizes in bytes
        units = ["By", "kB", "MB", "GB", "TB"]
        sizes = [1, 1024, 1048576, 1073741824, 1099511627776]
        for iii in range(len(units) - 1, -1, -1):
            if file_size >= sizes[iii]:
                # Calculate the size with this unit
                size_with_unit = f"{file_size / sizes[iii]:.2f} {units[iii]}"
                return self.get_string_justified(size_with_unit,is_left_justified,o_size)
        # If no suitable unit is found, display the original value
        return self.get_string_justified(f"{file_size:.2f} By",is_left_justified,o_size)

    @staticmethod
    def extract_filename(filename: str, with_extension: bool = True) -> str:
        """Extracts filename of a path+filename string

        Args:
            filename (str): path+filename
            with_extension (bool, optional): return filename including the extension. Defaults to True.

        Returns:
            str: string with filename
        """
        fn = os.path.basename(filename)  # returns just the name
        fnnoext, fext = os.path.splitext(fn)
        fnnoext = fnnoext.replace(fext, "")
        fn = fnnoext + fext
        if with_extension:
            return fn
        return fnnoext
    
    @staticmethod
    def extract_path(filename: str, with_separator: bool = True) -> str:
        """Extracts path of a path+filename string

        Args:
            filename (str): path+filename
            with_separator (bool, optional): return path including the separator. Defaults to True.

        Returns:
            str: string with path
        """
        fn = os.path.basename(filename)  # returns just the name
        fpath = os.path.abspath(filename)
        if with_separator:
            fpath = fpath.replace(fn, "")
        else:
            fpath = fpath.replace(os.sep + fn, "")
        return fpath
    
    def get_file_structure_from_active_path(self,src_path:str,item_name:str=None,file_structure:dict=None,full_path:bool=True,fcn_call=None,show_progress=False):
        """Gets a dictionary with a structure 
        {'item_name': [{'dir1': ['file1', ..., 'fileN']}, 
                    {'dir2': [{'dir3': ['file4']},'file1']}, 
                    ...
                    'file5', 'file6',... 'fileN']}
        Directories are dictionaries with content in a list. 
        A file is added as string, or tuple with properties

        Args:
            src_path (str): source path
            item_name (str, optional): Leave None to use src_path. Defaults to None.
            file_structure (dict, optional): Leave None or pass a dictionary to add the paths. Defaults to None.
            full_path (bool, optional): True directory names include full path. Defaults to True.
            fcn_call (function, optional): Calls function fcn_call(full_filePath). Defaults to None.

        Returns:
            _type_: _description_
        """
        # Check if the source and destination paths exist
        if not os.path.exists(src_path):
            return file_structure
        first_loop=False
        if not file_structure and not item_name:
            first_loop=True
            file_structure={}
        elif not file_structure and item_name:
            file_structure={}    
        # Search inner structure    
        path_list=[]
        
        num_items=0
        for item in os.listdir(src_path):
            num_items=num_items+1
        val=0
        task1 = None
        # if show_progress:
        #     progress=Progress()
        # else:
        #     progress=None
        for item in os.listdir(src_path):
            # if val==0 and first_loop and show_progress:
            #     print('entered-->',src_path)

            #     task1 = progress.add_task(f"[green]{src_path}", total=num_items) 
            try:    
                # if show_progress:
                #     # progress bar update
                #     if not progress.finished :
                #         print('updating-->',val)
                #         progress.update(task1, advance=1)
                #         val=val+1
                src_item = os.path.join(src_path, item)
                # If the current item is a file
                if os.path.isfile(src_item):
                    if fcn_call:
                        path_list.append(fcn_call(src_item))
                    else:
                        path_list.append(item)
            except PermissionError as error:
                print('File:',error)
                # path_list.append({})     
            try:  
                # If the current item is a directory
                if os.path.isdir(src_item):
                    print(src_item)
                    if full_path:
                        mod_item=item
                    else:    
                        extract=self.extract_parent_path(item,True) 
                        mod_item=item.replace(extract,"")
                    inner_structure=self.get_file_structure_from_active_path(src_item,mod_item,{},full_path,fcn_call, show_progress=False)    
                    path_list.append(inner_structure)
            except PermissionError as error:
                print('Directory:',error)
                  
        # # end progressbar if not finished all
        # if val<num_items and show_progress:
        #     while not progress.finished:
        #         print('updating not finished-->',val)
        #         progress.update(task1, advance=1)
        if first_loop:
            file_structure.update({src_path:path_list})
        elif item_name and not first_loop:
            file_structure.update({item_name:path_list})         
        return file_structure

    @staticmethod
    def extract_parent_path(filename: str, with_separator: bool = True) -> str:
        """Extracts parent path of a path+filename string

        Args:
            filename (str): path+filename
            with_separator (bool, optional): return path including the separator. Defaults to True.

        Returns:
            str: string with path
        """
        if filename.endswith((os.sep,'\\','/')):
             filename=filename[:len(filename)-1]
        fn = os.path.basename(filename)  # returns just the name
        fpath = os.path.abspath(filename)
        if with_separator:
            fpath = fpath.replace(fn, "")
        else:
            fpath = fpath.replace(os.sep + fn, "")
        return fpath    
    
    @staticmethod
    def remove_empty_folders(folder_path):
        """removes empty folders in a given path

        Args:
            folder_path (str): path
        """
        for root, dirs, files in os.walk(folder_path):
            if not files and not dirs:  # Check if directory is empty
                dir_path = os.path.join(root)
                print(f"Removing empty folder: {dir_path}")
                os.rmdir(dir_path)  # Remove the empty folder

    @staticmethod
    def get_app_path() -> str:
        """Gets Appliction path

        Returns:
            str: Application path
        """
        # determine if application is a script file or frozen exe
        application_path = ""
        if getattr(sys, "frozen", False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        return application_path

    @staticmethod
    def rename_folder(src_path: str, new_name: str) -> bool:
        """
        Renames a folder from src_path to new_name.
        
        Args:
            src_path (str): The source path of the folder to be renamed.
            new_name (str): The new name for the folder.
            
        Returns:
            bool: True if the rename operation is successful, False otherwise
        """
        # Check if the source directory exists
        if not os.path.exists(src_path):
            print(f"Source directory '{src_path}' does not exist.")
            return False
        # Construct the new path with the new name
        dst_path = os.path.join(os.path.dirname(src_path), new_name)
        try:
            # Rename the folder using os.rename()
            os.rename(src_path, dst_path)
            print(f"Folder '{src_path}' renamed to '{dst_path}'")
            return True
        except Exception as eee:
            print(f"Error renaming folder {src_path}: {eee}")
            return False
    
    @staticmethod
    def validate_path(path: str) -> bool:
        """
        Validate the input path.
        
        Args:
            path (str): The input path to be validated.
        
        Returns:
            bool: True if the path is valid, False otherwise.
        """

        # Check for empty string
        if not path.strip():
            return False

        # Check length of path
        if len(path) > 256:  # windows & ubuntu limit, adjust as n
            print(f"Path '{path}' exceeds maximum allowed length (256 characters).")
            return False
        if os.path.exists(path):
            print(f"{path} exists")
            if os.path.isdir(path):
                print(f"{path} is a valid directory!")
                return True
            print(f"{path} is not a directory!")
        else:
            print(f"{path} Does not exists")
        return False
    
    def get_possible_path_list(self,path,joker='*')->list[str]:
        """Use glob to find files or directories with patterns

        Args:
            path (str): path as pattern

        Returns:
            list: list of patterns found
        """
        try:
            file_exist,is_file = self.validate_path_file(path)
            if file_exist and not is_file:
                return gb.glob(os.path.join(path, joker))   
            elif file_exist and is_file: 
                return gb.glob(self.extract_path(path,True) + joker)
            return [path]
        except Exception as eee:
            print(f"Error Glob: {eee}")
            return []

    @staticmethod
    def validate_path_file(pathfile: str) -> tuple[bool]:
        """
        Validate the input file with path.
        
        Args:
            pathfilepath (str): The input path and file name to be validated.
        
        Returns:
            tuple[bool]: (file_exist, is_file)
        """
        if not pathfile:
            return False,False
        # Check for empty string
        if not pathfile.strip():
            return False,False

        # Check length of path
        if len(pathfile) > 256:  # windows & ubuntu limit, adjust as n
            print(f"Path '{pathfile}' exceeds maximum allowed length (256 characters).")
            return False,False
        
        file_exist = False
        is_file = False
        if os.path.exists(pathfile):
            #print(f"{pathfile} exists")
            if os.path.isdir(pathfile):
                file_exist = True
                is_file = False
            if os.path.isdir(pathfile):
                file_exist = True
                is_file = True
        return file_exist, is_file 
           
    