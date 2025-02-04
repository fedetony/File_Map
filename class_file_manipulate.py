########################
# F.garcia
# creation: 03.02.2025
########################
import os
import sys
from datetime import datetime
import shutil
import psutil


class FileManipulate:
    def __init__(self):
        self.file = None
    
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

