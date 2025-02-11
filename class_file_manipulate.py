########################
# F.garcia
# creation: 03.02.2025
########################
import os
import re
import sys
from datetime import datetime
import shutil
import psutil

ALLOWED_CHARS = 'áéíóúüöäÜÖÄÁÉÍÓÚçÇabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ -'

class FileManipulate:
    def __init__(self):
        self.file = None
     
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
            int: value in bits
        """
        return os.path.getsize(file_path)

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
        print(f"{path} Does not exists")
        return False
    
    @staticmethod
    def validate_path_file(pathfile: str) -> tuple[bool]:
        """
        Validate the input file with path.
        
        Args:
            pathfilepath (str): The input path and file name to be validated.
        
        Returns:
            tuple[bool]: (file_exist, is_file)
        """

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
           
    