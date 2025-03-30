"""
File Mapping functions for a single database
########################
# F.garcia
# creation: 05.02.2025
########################
"""

import os
import sys
import time
from datetime import datetime
import hashlib
import threading
import difflib
import keyboard

from rich import print  # pylint: disable=redefined-builtin
from rich.progress import Progress

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate
from class_device_monitor import DeviceMonitor
from class_database_result import DBResult
from class_data_manage import DataManage
from class_autocomplete_input import AutocompletePathFile, getch, SQL_SG, raw_key_pressed, APP_PATH

# from class_file_explorer import raw_key_pressed
from thread_queue_calculation_stream import QueueCalcStream

A_C = AutocompletePathFile(None, APP_PATH, False, False, False)
MD5_CALC = "***Calculate***"
MD5_SHALLOW = "***Shallow***"
DATA_ADVANCE = 50  # gather 50 records before writting to db
SINGLE_MULTIPLE_SEARCH = 15  # use single search or generalized search limit
MAP_TYPES_LIST=["Device Map","Selection Map","Backup Map"]

class FileMapper:
    """Class for Mapping functions in a specific database"""

    def __init__(self, db_filepath, key_filepath, password):
        self.password = password
        self.db_path_file = db_filepath
        self.db_file = FileManipulate.extract_filename(db_filepath, True)
        self.db_path = FileManipulate.extract_path(db_filepath, True)
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
        self.key_filepath = ""
        if key_filepath:
            self.key_filepath = key_filepath
        self.key = None
        self.is_db_encrypted = False
        self.db_has_password = False
        self.db, self.is_db_encrypted, self.db_has_password = self.start_db(
            self.db_path_file, self.key_filepath, self.password
        )
        self.db_list = [self.db]
        # connect
        self.db.create_connection()
        self.active_devices = []
        self.look_for_active_devices()
        self.mapper_reference_table = "__File_Mapper_Reference__"

    def look_for_active_devices(self):
        """Looks for devices mounted sets the device, serial list to active_devices"""
        md = DeviceMonitor(log_print=True)
        for _, serial in md.devices:
            if not serial:
                md.check_none_devices()
        self.active_devices = md.devices
        print(f"Found devices: {self.active_devices}")

    @staticmethod
    def start_db(db_path_file, key_filepath, password=None):
        """Starts a database. If not existing, database is created. Returns connected database object.

        Args:
            db_path_file (str): database file with path
            key_filepath (str): if encrypted, encryption key file with path else None
            password (str, optional): if db is password proteced. Defaults to None.

        Returns:
            SQLiteDatabase: database
            bool: is_encrypted
            bool: has_password
        """
        key = None
        has_password = False
        is_encrypted = False
        has_password = False
        db = None
        #
        is_path = os.path.exists(db_path_file)
        if is_path:  # if db exists
            if os.path.exists(key_filepath):
                with open(key_filepath, "rb") as f:
                    key = f.read()
                db = SQLiteDatabase(db_path_file, True, key, password)
                is_encrypted = True
            else:
                is_encrypted = False
                db = SQLiteDatabase(db_path_file, False, None, password)
        elif not is_path:  # if db not exists
            if key_filepath:
                # Create new encrypted database
                is_encrypted = True
                db = SQLiteDatabase(db_path_file, True, None, password)
                key_generated = db.encrypt_db()
                if key_generated:
                    db.save_key_to_file(key_filepath)
                    db.decrypt_db()
            else:
                is_encrypted = False
                db = SQLiteDatabase(db_path_file, False, None, password)
        if password:
            has_password = True
        print("Started:", db, is_encrypted, has_password)
        return db, is_encrypted, has_password

    @staticmethod
    def calculate_time_elapsed(start_datetime, end_datetime):
        """Calculate the time elapsed between two timestamps"""
        time_elapsed = (end_datetime - start_datetime).total_seconds()
        return time_elapsed

    @staticmethod
    def calculate_md5(file_path, leave_to_thread=False, shallow_map=False):
        """
        Calculate the MD5 hash of a file.

        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.
            leave_to_thread (bool, optional): Sets Calculate keyword if not shallow. Defaults to False.
            shallow_map (bool, optional): Sets Shallow keyword. Defaults to False.

        Returns:
            str: The MD5 sum as a hexadecimal string.
        """
        if shallow_map:
            return MD5_SHALLOW
        if leave_to_thread and not shallow_map:
            # time.sleep(0.01) # cant write to db so fast
            return MD5_CALC
        try:
            with open(file_path, "rb") as f:
                md5 = hashlib.md5()
                while chunk := f.read(4096):
                    md5.update(chunk)
                return md5.hexdigest()

        except FileNotFoundError:
            print(f"File {file_path} not found.")
            sys.exit(1)
        return None

    @staticmethod
    def calculate_sha1(file_path):
        """
        Calculate the SHA128 hash of a file.

        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.

        Returns:
            str: The SHA128 hash as a string.
        """
        try:
            with open(file_path, "rb") as f:
                sha1 = hashlib.sha1()
                while chunk := f.read(4096):
                    sha1.update(chunk)
                return sha1.hexdigest()

        except FileNotFoundError:
            print(f"File {file_path} not found.")
            sys.exit(1)
        return None

    @staticmethod
    def calculate_sha256(file_path):
        """
        Calculate the SHA256 hash of a file.

        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.

        Returns:
            str: The SHA256 hash as a string.
        """
        try:
            with open(file_path, "rb") as f:
                sha256 = hashlib.sha256()
                while chunk := f.read(4096):
                    sha256.update(chunk)
                return sha256.hexdigest()

        except FileNotFoundError:
            print(f"File {file_path} not found.")
            sys.exit(1)
        return None

    @staticmethod
    def remove_mount_from_path(mount: str, path: str) -> str:
        """Removes the mounting point
        Args:
            mount (str): mounting point
            path (str): path

        Returns:
            str: Path without mount not starting with '/' because join removes the mount.
        """
        if mount.endswith("\\"):
            mount = mount.replace("\\", "")
            path = path[(len(mount) + 1) :]
            if path.startswith("\\"):
                path = path[1:]
            return path
        if mount.endswith("/") and len(mount) > 1:
            return path[len(mount) :]
        if not mount.endswith("/") and len(mount) > 1:
            if path.startswith("/"):
                return path[(len(mount) + 1) :]
            return path[len(mount) :]
        if mount == "/":
            if path.startswith("/"):
                path = path[1:]
            return path
        return path[len(mount) :]

    def find_mount_serial_of_path(self, path: str):
        """Returns the mount point and serial for a path on an active device.

        Args:
            path (str): path to look for

        Returns:
            tuple: (mount, serial)
        """
        # find mounting point
        mount = ""
        serial = ""
        lenmd = -1
        if isinstance(self.active_devices, list):
            for md in self.active_devices:
                if os.name == "nt":
                    if path.startswith(md[0]):
                        mount = md[0]
                        serial = md[1]
                        break
                    if path.startswith(md[0].lower()):
                        mount = md[0].lower()
                        serial = md[1]
                        break
                    if path.startswith(md[0].upper()):
                        mount = md[0].upper()
                        serial = md[1]
                        break
                elif os.name != "nt":
                    if path.startswith(md[0]) and len(md[0]) > lenmd:
                        lenmd = len(md[0])
                        mount = md[0]
                        serial = md[1]
        return mount, serial

    def add_table_to_mapper_index(self, table_name:str, path_to_map:str, table_type:str=None):  # pylint: disable=too-many-locals
        """Adds the information of the table to mapper index table

        Args:
            table_name (str): table in database
            path_to_map (str): path in device
            table_type (str): type of table being indexed. Defaults to None ("Device Map").
        Returns:
            bool: Was indexed
        """
        db = self.db
        # if not db.table_exists(self.mapper_reference_table):
        db.create_table(
            self.mapper_reference_table,
            [
                ("dt_map_created", "DATETIME DEFAULT CURRENT_TIMESTAMP", True),
                ("dt_map_modified", "DATETIME", True),
                ("mappath", "TEXT", True),
                ("tablename", "TEXT", True),
                ("mount", "TEXT", True),
                ("serial", "TEXT", True),
                ("mapname", "TEXT", True),
                ("maptype", "TEXT", True),
            ],
        )
        db_result = DBResult(db.describe_table_in_db(self.mapper_reference_table))
        db_result.set_values(db.get_data_from_table(self.mapper_reference_table, "*", f"tablename={db.quotes(table_name)}"))
        table_indexed = False
        if len(db_result.dbr) > 0:
            # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
            for dbr in db_result.dbr:
                if dbr.tablename == table_name:
                    table_indexed = True
                    an_id = dbr.id
                    break
        if not table_indexed:
            print(f"Table {table_name} is Not in reference indexed")
        mapname = ""
        if not table_type:
            maptype = MAP_TYPES_LIST[0] #"Device Map"
        else:
            maptype = table_type
        dt_map_created = datetime.now()
        dt_map_modified = datetime.now()
        # find mounting point
        mount, serial = self.find_mount_serial_of_path(path_to_map)
        mappath = self.remove_mount_from_path(mount, path_to_map)
        was_indexed = None
        if table_indexed:
            # Update mount point and date modified
            print(f"Editing table {table_name}")
            db.edit_value_in_table(self.mapper_reference_table, an_id, "dt_map_modified", dt_map_modified)
            was_indexed = db.edit_value_in_table(self.mapper_reference_table, an_id, "mount", mount)
        else:
            print(f"Indexing table {table_name}")
            data = [(dt_map_created, dt_map_modified, mappath, table_name, mount, serial, mapname, maptype)]
            was_indexed = db.insert_data_to_table(self.mapper_reference_table, data)
        if not was_indexed:
            print(f"[red] Table {table_name} was not correctly indexed!!")
        return was_indexed
        # # check
        # if db.get_number_or_rows_in_table(self.mapper_reference_table):
        #     raise ValueError("No data was added to index")

    def map_to_file_structure(
        self, a_map, where=None, fields_to_tab: list[str] = None, sort_by: list = None, ascending: bool = True
    ) -> dict:
        """Generates a file structure from map information

        Args:
            database (str): database
            a_map (str): table in database
            where (_type_, optional): sql filter for the database search. Defaults to None.
            fields_to_tab (list[str], optional): Additional information to 'filename' and 'size' from map
            into file tuple. Defaults to None.
            sort_by (list, optional): Dataframe sorting. Defaults to None.
            ascending (bool, optional): AScending descending order for sorting. Defaults to True.

        Returns:
            dict: filestruct of map
        """
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6
        # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        field_list = self.db.get_column_list_of_table(a_map)
        # Map info
        # id=0 'dt_map_created'=1 'dt_map_modified'=2 'mappath'=3 'tablename'=4 'mount'=5 'serial'=6
        # 'mapname'=7 'maptype'=8
        map_info = self.db.get_data_from_table(self.mapper_reference_table, "*", f"tablename='{a_map}'")
        if len(map_info) == 0:
            return {}

        data = self.db.get_data_from_table(a_map, "*", where)
        try:
            d_m1 = DataManage(data, field_list)
        except ValueError:
            # No data
            return {}
        default = ["filename", "size"]
        fields2tab = []
        if isinstance(fields_to_tab, list):
            for field in fields_to_tab:
                if field not in default and field in field_list:
                    fields2tab.append(field)
        # df = d_m1.get_selected_df(fields_to_tab=fields2tab, sort_by=sort_by, ascending=ascending)
        df = d_m1.get_selected_df(fields_to_tab=field_list, sort_by=sort_by, ascending=ascending)
        map_list = []
        fi_ma = FileManipulate()
        for iii, (filepath, filename, size) in enumerate(zip(df["filepath"], df["filename"], df["size"])):
            # print(f"{filepath} - {filename}, Size: {size}")
            file_tuple = (filename, size)
            # Add more info to the tuple
            for field in fields2tab:
                file_tuple = file_tuple + (df[field][iii],)
            if iii == 0:
                dict1 = fi_ma.path_to_file_structure_dict(filepath, file_tuple)
                map_list = [dict1]
            elif iii == 1:
                dict2 = fi_ma.path_to_file_structure_dict(filepath, file_tuple)
                map_list = fi_ma.merge_file_structure_dicts(dict1, dict2)
            else:
                dict3 = fi_ma.path_to_file_structure_dict(filepath, file_tuple)
                map_list = fi_ma.merge_file_structure_lists(map_list, [dict3])
        # mappath = map_info[0][3]
        # file_struct = {mappath: map_list}
        # return file_struct
        return {map_info[0][3]: map_list}

    # def file_structure_to_map(self, table_name):
    #     # this may not have sense since lacks information
    #     pass

    def remap_map_in_thread_to_db(self, table_name, progress_bar=None, wait_for_key_press=False):
        """Starts a thread that looks inside the table for '***Calculate***' md5.
            Calculates the correspondant md5 and updates the value in the database.

        Args:
            table_name (str): table
            progress_bar (object, optional):Object to use for progressbar in GUI. Defaults to None.

        Returns:
            str: message to print
        """
        db_info = {
            "name": self.db_path_file,
            "key": self.key_filepath,
            "pwd": self.password,
            "encrypt": self.is_db_encrypted,
        }
        mount, mount_active, mappath_exists = self.check_if_map_device_active(self.db, table_name, False)
        if mount_active and mappath_exists:
            kill_ev = threading.Event()
            kill_ev.clear()
            cycle_time = 0.1
            start_datetime = datetime.now()
            qstream = QueueCalcStream(db_info, table_name, mount, cycle_time, kill_ev, progress_bar)
            qstream.start()
            try:
                was_user_exit = False
                while qstream.is_alive():
                    if os.name == "nt":
                        if keyboard.is_pressed("F12"):
                            was_user_exit = True
                            kill_ev.set()
                    time.sleep(0.5)
            except KeyboardInterrupt:
                was_user_exit = True
                kill_ev.set()
            took = self.calculate_time_elapsed(start_datetime, datetime.now())
            if was_user_exit:
                print(f"Thread exit from user after {self.time_seconds_to_hhmmss(took)}")
            else:
                print(f"Thread Mapping finished after {self.time_seconds_to_hhmmss(took)}")
            if wait_for_key_press:
                print("+" * 33)
                print("Press any key to continue")
                print("+" * 33)
                getch()
            return ""
        return "Mount not available!"

    def is_device_map(self,table_name:str)->bool:
        """If is a device or selection map

        Args:
            table_name (str): Map to check

        Returns:
            bool: True if is a device Map, False if selection. None if no map.
        """
        an_id=self.get_table_id(table_name)
        map_type=self.db.get_data_from_table(self.mapper_reference_table,"maptype",f"id={an_id}")
        if len(map_type)>0:
            if map_type[0][0] == MAP_TYPES_LIST[0]:
                return True
            return False
        return None

    def map_a_selection(self,selection_name:str, origin_map:str, map_data:list, map_type:str=None):
        """Makes a selection map

        Args:
            selection_name (str): map name
            origin_map (str): map of the same db where the selection is taken from
            map_data (list): _description_
        """

        if self.db.table_exists(origin_map) and map_data:
            an_id=self.get_table_id(origin_map)
            map_info=self.db.get_data_from_table(self.mapper_reference_table,"*",f"id={an_id}")
            # mount= 5 mappath = 3
            mount_path_to_map=os.path.join(map_info[0][5],map_info[0][3])
            if not map_type:
                map_type=MAP_TYPES_LIST[1]
            self.add_table_to_mapper_index(selection_name, mount_path_to_map, map_type)
            self._create_map_in_db(selection_name)
            an_id=self.get_table_id(selection_name)
            if an_id:
                self.db.insert_data_to_table(selection_name,map_data)
            self.set_mapname(selection_name,origin_map)

    def _create_map_in_db(self,table_name):
        """Creates map structure with table_name"""
        self.db.create_table(
                table_name,
                [
                    ("dt_data_created", "DATETIME DEFAULT CURRENT_TIMESTAMP", True),
                    ("dt_data_modified", "DATETIME", True),
                    ("filepath", "TEXT", True),
                    ("filename", "TEXT", True),
                    ("md5", "TEXT", True),
                    ("size", "REAL", True),
                    ("dt_file_created", "DATETIME", False),
                    ("dt_file_accessed", "DATETIME", False),
                    ("dt_file_modified", "DATETIME", False),
                ],
            )

    def map_a_path_to_db(
        self,
        table_name,
        path_to_map,  # pylint: disable=too-many-locals
        log_print=True,
        progress_bar=None,
        shallow_map=False,
        press_to_continue=True,
    ):
        """Maps a path in a device into a table in the database.

        Args:
            db (SQLiteDatabase): database
            table_name (_type_): table to map the path
            path_to_map (_type_): path to map on the device
            log_print (bool, optional): print logs. Defaults to True.
            shallow_map (bool, optional): Make shallow map (Does not calculate md5,does not run thread).
            Defaults to False.
        """
        db = self.db
        try:
            self.add_table_to_mapper_index(table_name, path_to_map)
            self._create_map_in_db(table_name)
            data = []
            iii = 0
            files_processed = 0
            mount, _ = self.find_mount_serial_of_path(path_to_map)
            start_datetime = datetime.now()
            num_files, num_folders = self.count_files_in_path(path_to_map)
            with Progress() as progress:
                exit_key = "ctrl+c"
                if os.name == "nt":
                    exit_key = "F12"
                task1 = progress.add_task(f"[blue]Initial Mapping [red]({exit_key} to Exit)", total=num_files)
                delta = datetime.now() - start_datetime
                print(f"Counted: {num_files} files and {num_folders} folders in {delta.total_seconds()} sec")
                for dirpath, _, filenames in os.walk(path_to_map):
                    # Get the data for each file
                    for file in filenames:
                        line_data_tup = self.get_mapping_info_data_from_file(
                            mount, dirpath, file, log_print, f"{files_processed}. ", shallow_map
                        )
                        data.append(line_data_tup)
                        iii = iii + 1
                        if os.name == "nt":
                            if keyboard.is_pressed("F12"):
                                return "[red] User Interrupt"
                        if iii >= DATA_ADVANCE:
                            if log_print:
                                delta = datetime.now() - start_datetime
                                print("+" * 10 + f" Time elapsed: {str(delta).split('.',  maxsplit=1)[0]}" + "+" * 10)
                            was_inserted = db.insert_data_to_table(table_name, data)
                            if not was_inserted:
                                time.sleep(0.333)
                                if not db.insert_data_to_table(table_name, data):
                                    raise ValueError(f"Could not insert data in {table_name}")
                            progress.update(task1, advance=DATA_ADVANCE)
                            data = []
                            iii = 0
                        files_processed = files_processed + 1
                db.insert_data_to_table(table_name, data)
                progress.update(task1, completed=num_files)
            time.sleep(0.333)
            # db.print_all_rows(table_name)
            if not shallow_map:
                self.remap_map_in_thread_to_db(table_name, progress_bar, False)
            if log_print:
                # time_elapsed = (datetime.now() - start_datetime).total_seconds()
                delta = datetime.now() - start_datetime
                print("+" * 33)
                n_r = db.get_number_or_rows_in_table(table_name)
                print(f'[green]Successfully Mapped {n_r} files in {str(delta).split(".", maxsplit=1)[0]}')
                if press_to_continue:
                    print("+" * 33, "\nPress any Key to continue\n", "+" * 33)
                    getch()
                return f'[green]Successfully Mapped {n_r} files in {str(delta).split(".", maxsplit=1)[0]}'
        except KeyboardInterrupt:
            print("[magenta]User cancel")
            print("@" * 100, "\nPress any Key to continue\n", "@" * 100)
            return "[red] User Interrupt"
        except Exception as eee:  # pylint: disable=broad-exception-caught
            print(f"[red]Error Mapping: {eee}")
            print(type(eee), line_data_tup)
            if press_to_continue:
                print("@" * 100, "\nPress any Key to continue\n", "@" * 100)
                getch()
        return f"[red]Error Mapping: {eee}"

    @staticmethod
    def count_files_in_path(path):
        """Calculate the number of files and folders in a path.

        Args:
            path (str): path to look in

        Returns:
            tuple[int]: num_files,num_folders
        """
        num_files = 0
        num_folders = 0
        if os.path.exists(path):
            num_folders = num_folders + 1  # root
            for _, dirs, filenames in os.walk(path):
                # Get the data for each file
                num_files = num_files + len(filenames)
                num_folders = num_folders + len(dirs)
        return num_files, num_folders

    @staticmethod
    def time_seconds_to_hhmmss(time_seconds: float) -> str:
        """Returns time in HH:MM:SS format"""
        hours, remainder = divmod(time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:.0f}:{minutes:.0f}:{seconds:.0f}"

    @staticmethod
    def estimate_mapping_time_sec(
        size_sample, time_sample_sec, size_to_calculate, units_sample="bytes", units_calc="bytes"
    ) -> float:
        """Estimates the time for a different size , by using a sample time proportion.

        Args:
            size_sample (int): sample size
            time_sample_sec (float): time to process (seconds?)
            size_to_calculate (int): size to calculate
            units_sample (str, optional): units of sample size. Defaults to 'bytes'.
            units_calc (str, optional): units of calc size. Defaults to 'bytes'.

        Returns:
            float: time in sample time unit
        """
        us = units_sample.lower()
        uc = units_calc.lower()
        if us not in ["bytes", "by", "kb", "mb", "tb", "gb"]:
            us = "bytes"
        if uc not in ["bytes", "by", "kb", "mb", "tb", "gb"]:
            uc = "bytes"
        if size_sample <= 0:
            return 0
        if us == uc:
            return int(size_to_calculate) / int(size_sample) * time_sample_sec
        return SQL_SG.to_bytes(uc, size_to_calculate) / SQL_SG.to_bytes(us, size_sample) * time_sample_sec

    def get_mapping_info_data_from_file(
        self, mount: str, dirpath: str, file: str, log_print: bool = False, count_print="", shallow_map=False
    ) -> tuple:
        """gets tuple with map table info from inputs

        Args:
            mount (str): the mount
            dirpath (str): the path (no mount)
            file (str): the file
            log_print (bool, optional): If you want to print. Defaults to False.
            count_print (int | str, optional): If you want to print the count. Defaults to ''.
            shallow_map (bool, optional): Make shallow map (Does not calculate md5). Defaults to False.
        Returns:
            tuple: (dt_data_created,dt_data_modified,dirpath_nm,file,the_md5,the_size,dt_file_c,dt_file_a,dt_file_m)
        """
        dt_data_created, dt_data_modified, dirpath_nm, the_md5, dt_file_c, dt_file_a, dt_file_m = [None] * 7
        the_size = -1
        f_m = FileManipulate()
        try:
            dirpath_nm = self.remove_mount_from_path(mount, dirpath)
            dt_data_created = datetime.now()
            # when joining, calculating or sizing fails hava a datetime (required in db)
            dt_data_modified = dt_data_created
            # join
            joined_file = os.path.join(dirpath, file)
            # size
            the_size = f_m.get_file_size(joined_file)
            # md5 calculate
            if the_size > 349175808 and log_print and not shallow_map:  # 333*1024*1024=349175808
                str_size = f_m.get_size_str_formatted(the_size)
                t_est = self.time_seconds_to_hhmmss(
                    self.estimate_mapping_time_sec(904.29, 16.08, the_size, "MB", "bytes")
                )
                print(f"Calculating md5 for {file}...{str_size} Estimating: {t_est}")
            if the_size > 50 * 1024 * 1024:  # leave to calculate with the thread
                the_md5 = self.calculate_md5(joined_file, True, shallow_map)
            else:
                the_md5 = self.calculate_md5(joined_file, False, shallow_map)
            dt_data_modified = datetime.now()
            # get file dates
            dt_file_a = f_m.get_accessed_date(joined_file)
            dt_file_c = f_m.get_created_date(joined_file)
            dt_file_m = f_m.get_modified_date(joined_file)
            if log_print:
                str_size = f_m.get_size_str_formatted(the_size, 11)
                # use () not [] because rich looks for commands inside []
                str_just = f_m.get_string_justified(f"{count_print}({str_size})", False, 11 + 3 + 4)
                time_elapsed = (dt_data_modified - dt_data_created).total_seconds()
                print(f"{str_just} ({the_md5}) \t{dirpath+os.sep+file} ... ({time_elapsed:.3f}s)")
        except (FileExistsError, PermissionError, FileNotFoundError, NotADirectoryError, TypeError, OSError) as eee:
            print(f"{mount}{dirpath}{file} Error: {eee}")
            if not the_md5:
                the_md5 = "::UNKNOWN::"
            if not the_size:
                the_size = -1
            if not dt_file_c:
                dt_file_c = dt_data_created
            if not dt_file_a:
                dt_file_a = dt_data_created
            if not dt_file_m:
                dt_file_m = dt_data_created
            # print("@"*100,"\nPress any Key to continue\n","@"*100)
            # getch()
            return (
                dt_data_created,
                dt_data_modified,
                dirpath_nm,
                file,
                the_md5,
                the_size,
                dt_file_c,
                dt_file_a,
                dt_file_m,
            )

        return (dt_data_created, dt_data_modified, dirpath_nm, file, the_md5, the_size, dt_file_c, dt_file_a, dt_file_m)

    def get_repeated_files(self, db: SQLiteDatabase, table_name) -> dict[list]:
        """Gets repeated files in map

        Args:
            db (SQLiteDatabase): database
            table_name (_type_): table

        Returns:
            dict[list]: repeated file ids
                        md5sum:[id of files repeated]
        """
        return self.get_repeated_file_multiple_db_tables([db], [table_name], ["id", "md5"], 1)

    @staticmethod
    def get_repeated_file_multiple_db_tables(
        db_list: list[SQLiteDatabase], table_name_list: list, column_list: list = None, order_by=1
    ) -> dict[list]:
        """Gets repeated files in multiple maps. Maps can be is same or different db.

        Args:
            db_list (list[SQLiteDatabase]): database list (same length as table_name_list)
            table_name_list (list): list of tables (all tables must contain the columns in colunm_list)
            column_list (list): columns in tables, default None -> ['id','md5']
            order_by (int): 0 indexed column to be used. Default 1 -> 'md5'

        Returns:
            dict[list]: {(ordered column name):(list of other columns repeated)..}
            repeated file ids
            default:  md5sum:[id of files repeated]
        """
        if not column_list:
            column_list = ["id", "md5"]
        repeated = {}
        try:
            data_list = []
            cols = str(column_list).replace("[", "").replace("'", "").replace("]", "")
            for index, (db, table_name) in enumerate(zip(db_list, table_name_list)):
                data = db.get_data_sql_command(
                    f"SELECT {cols} FROM {db.quotes(table_name)} ORDER BY {column_list[order_by]}"
                )
                for ddd in data:
                    data_list.append((index,) + ddd)  # add [db,table] index to tuple

            iii = 0
            last_anmd5 = None
            last_an_id = None
            last_db = None
            for dbtable, an_id, anmd5 in data_list:
                if last_anmd5 == anmd5:
                    if anmd5 in repeated:
                        rep_list = repeated[anmd5]
                        if isinstance(rep_list, list):
                            rep_list.append((dbtable, an_id))
                            repeated.update({anmd5: rep_list})
                    else:
                        repeated.update({anmd5: [(last_db, last_an_id), (dbtable, an_id)]})
                last_anmd5 = anmd5
                last_an_id = an_id
                last_db = dbtable
                iii = iii + 1
        except Exception as e:
            print(f"Error: {e}")
            # db.close_connection()
        return repeated

    def validate_new_map_name(self, new_table_name: str):
        """Check if New table name is Correct"""
        tables = self.db.tables_in_db()
        if new_table_name in tables:
            return False
        return True

    def rename_map(self, table_name: str, new_table_name: str) -> bool:
        """Renames a map

        Args:
            table_name (str): actual name
            new_table_name (str): new name

        Returns:
            bool: True if it was renamed
        """
        if table_name == new_table_name or table_name == "" or new_table_name == "":
            return False
        tables = self.db.tables_in_db()
        if table_name in tables and self.validate_new_map_name(new_table_name):
            db_result = DBResult(self.db.describe_table_in_db(self.mapper_reference_table))
            db_result.set_values(
                self.db.get_data_from_table(self.mapper_reference_table, "*", f"tablename='{table_name}'")
            )
            if len(db_result.dbr) > 0:
                # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
                an_id = getattr(db_result.dbr[0], "id")
            else:
                return False

            # Rename table
            self.db.send_sql_command(f"ALTER TABLE '{table_name}' RENAME TO '{new_table_name}'")
            time.sleep(0.1)
            if self.db.table_exists(new_table_name):
                print(f"Editing table {table_name}")
                self.db.edit_value_in_table(self.mapper_reference_table, an_id, "dt_map_modified", datetime.now())
                self.db.edit_value_in_table(self.mapper_reference_table, an_id, "tablename", new_table_name)
            old_ref = self.db.get_data_from_table(self.mapper_reference_table, "*", f"tablename='{table_name}'")
            new_ref = self.db.get_data_from_table(self.mapper_reference_table, "*", f"tablename='{new_table_name}'")
            if len(old_ref) == 0 and len(new_ref) == 1:
                print(f"Reference correctly changed to {new_table_name}")
            return self.db.table_exists(new_table_name)
        return False

    @staticmethod
    def repeated_list_show(
        repeated_dict: dict,
        key,
        db_list: list[SQLiteDatabase],
        table_name_list: list,
        db_cols: list = ["id", "filepath", "filename", "md5"],
    ):
        """Gets additional information on repeated_dict items.

        Args:
            repeated_dict (dict): repeated dictionary
            key (str): key to show
            db_list (list[SQLiteDatabase]): database list (same length as table_name_list)
            table_name_list (list): list of tables (all tables must contain the columns in db_cols)
            db_cols (list, optional): colums to show. Defaults to ['id','filepath','filename','md5'].
            if None will add all columns.

        Returns:
            list: additional info list
        """
        if not db_cols:
            # add all columns
            db_cols = db_list[0].get_column_list_of_table(table_name_list[0])

        rep_tup = repeated_dict[key]
        from_txt = str(db_cols).replace("[", "").replace("'", "").replace("]", "")
        info = []
        for a_db, an_id in rep_tup:
            db = db_list[a_db]
            if isinstance(db, SQLiteDatabase):
                table_name = table_name_list[a_db]
                where = f"id={an_id}"
                data = db.get_data_from_table(table_name, from_txt, where)
                if len(data) > 0:
                    info.append(data[0])
        return info

    def get_table_id(self, table_name:str):
        """Gets in reference table the id of a map

        Args:
            table_name (str): table name

        Returns:
            int: table id
        """
        if self.db.table_exists(self.mapper_reference_table):
            id_list = self.db.get_data_from_table(self.mapper_reference_table, "id", f"tablename={self.db.quotes(table_name)}")
            if len(id_list) > 0: # list[tuple]
                return id_list[0][0]
        return None
    
    def set_mapname(self, table_name, name):
        """Renames name field in Reference

        Args:
            table_name (str): table
            name (str): new name
        """
        an_id=self.get_table_id(table_name)
        if an_id:
            self.db.edit_value_in_table(self.mapper_reference_table, an_id, "mapname", name)

    def get_referenced_attribute(self, attr):
        """Returns the column of mapper_reference_table as list for the attribute

        Args:
            attr (str): 'id','dt_map_created','dt_map_modified','mappath','tablename','mount',
            'serial','mapname','maptype'
        Returns:
            list: column in db with attribute
        """
        tablename_list = []
        if self.db.table_exists(self.mapper_reference_table):
            db_result = DBResult(self.db.describe_table_in_db(self.mapper_reference_table))
            db_result.set_values(self.db.get_data_from_table(self.mapper_reference_table, "*"))
            # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
            for dbr in db_result.dbr:
                # print(getattr(dbr,attr))
                tablename_list.append(getattr(dbr, attr))
        return tablename_list

    def delete_map(self, table_name,log_print=True):
        """Removes a map from index and its referenced table from db.

        Args:
            table_name (str): table
            log_print (bool): print information. Default True
        """
        try:
            if self.db.table_exists(self.mapper_reference_table):
                db_result = DBResult(self.db.describe_table_in_db(self.mapper_reference_table))
                db_result.set_values(
                    self.db.get_data_from_table(self.mapper_reference_table, "*", f"tablename='{table_name}'")
                )
                if len(db_result.dbr) > 0:
                    # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
                    an_id = getattr(db_result.dbr[0], "id")
                    # print(f"Here id {an_id}")
                    self.db.delete_data_from_table(self.mapper_reference_table, f"id={an_id}")
                    if log_print:
                        print(f"{table_name} reference was deleted!!")
                else:
                    print(f"{table_name} Not found in reference!")
            if self.db.table_exists(table_name):
                self.db.delete_data_from_table(table_name, None)  # remove all data
                self.db.delete_table_from_db(table_name,log_print)
                if log_print:
                    print(f"{table_name} was deleted!!")

        except Exception as eee:
            print(f"{table_name} was not deleted: {eee}")

    def serial_close_match(self, serial, devices):
        """Gets a close match of the serial

        Args:
            serial (str): serial
            devices (list): active devices

        Returns:
            _type_: _description_
        """
        serial_list = []
        for dev in devices:
            if dev[1]:
                serial_list.append(dev[1])
        close = difflib.get_close_matches(serial, serial_list, n=3, cutoff=0.9)
        if len(close) > 0:
            return close[0]
        return None

    def check_if_map_device_active(self, db: SQLiteDatabase, table_name: str, rescan_devices: bool = True):
        """Checks if mounted device is active, and if map path exists. Returns the mounting point if device is active.

        Args:
            db (SQLiteDatabase): database of table
            table_name (str): map table to look for
            rescan_devices (bool, optional): scan the connected devices again. Defaults to True.

        Returns:
            tuple: (mount, mount_active, mappath_exists)
                mount: device mount point or None if serial is not found
                mount_active: True if serial matches or mappath exists in a device active,
                mappath_exists: None if no serial matches. True if Serials match and path exists in mount,
                False if serials match but path not in mount.
        """
        if rescan_devices:
            self.look_for_active_devices()
        mount = None
        mount_active = False
        mappath_exists = None
        if db.table_exists(table_name):
            try:
                db_result = DBResult(db.describe_table_in_db(self.mapper_reference_table))
                db_result.set_values(
                    db.get_data_from_table(self.mapper_reference_table, "*", f"tablename='{table_name}'")
                )
                if len(db_result.dbr) > 0:
                    # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
                    an_id = getattr(db_result.dbr[0], "id")
                    mappath = getattr(db_result.dbr[0], "mappath")
                    mp_mount = getattr(db_result.dbr[0], "mount")
                    serial = getattr(db_result.dbr[0], "serial")
                else:
                    print(f"No data found in reference table for {table_name}")
                    return mount, mount_active, mappath_exists

                device_present = False
                for a_mount, a_serial in self.active_devices:
                    if self.serial_close_match(serial, self.active_devices) == a_serial:
                        device_present = True
                    if mp_mount.lower() == a_mount.lower() and device_present:
                        mount = a_mount
                        mount_active = True
                        break
                if not mount:
                    for md in self.active_devices:
                        if md[1] == self.serial_close_match(serial, self.active_devices):
                            mount = md[0]
                            mount_active = True
                            break
                # Check if path exists
                if mount:
                    if os.name == "nt":
                        mappath_exists = os.path.exists(os.path.join(mount, mappath))
                    else:
                        f_m = FileManipulate()
                        if mappath.startswith(os.sep):
                            mappath = mappath[1:]
                        mount_path = os.path.join(f_m.fix_separator_in_path(mount), mappath)
                        mappath_exists = os.path.exists(mount_path)
                else:
                    for md in self.active_devices:
                        if os.path.exists(os.path.join(md[0], mappath)):
                            mount = md[0]
                            print(f"path exists on device {md[1]} not found in {serial}")
                            mount_active = True
                            break
                # update mounting point
                if mappath_exists and mp_mount != mount and mount:
                    dt_map_modified = datetime.now()
                    db.edit_value_in_table(self.mapper_reference_table, an_id, "dt_map_modified", dt_map_modified)
                    db.edit_value_in_table(self.mapper_reference_table, an_id, "mount", mount)
            except IndexError:
                pass

        return mount, mount_active, mappath_exists

    # def get_dbresult_list(self,db_list: list[SQLiteDatabase],table_name_list: list) -> list[DBResult]:
    #     """Returns a list with the dbresult objects for each database,table pair.

    #     Args:
    #         db_list (list[SQLiteDatabase]): database list
    #         table_name_list (list): table list

    #     Returns:
    #         list[DBResult]: Dbresult of each db, table pair
    #     """
    #     dbresult_list=[]
    #     if len(db_list)!=len(table_name_list):
    #         print("Error: database,table Pairs have deffernt lengths!")
    #         return  dbresult_list
    #     for a_db,table_name in zip(db_list,table_name_list):
    #         db_result=DBResult(a_db.describe_table_in_db(table_name))
    #         db_result.set_values(a_db.get_data_from_table(table_name,'*',None))
    #         dbresult_list.append(db_result)
    #     return  dbresult_list

    @staticmethod
    def repeated_in_same_db(repeated_dict, key) -> bool:
        """Finds if items are repeated in the same database

        Args:
            repeated_dict (dict): repeated item dictionary
            key (str): None to look all dictionary. or key of specific item

        Returns:
            _type_: _description_
        """
        same_db = None
        for a_key, value in repeated_dict.items():
            if a_key == key or not key:
                same_db = True
                last_index = 0
                for iii, (index, _) in enumerate(value):
                    if iii == 0:
                        last_index = index
                    elif iii > 0 and index != last_index:
                        return False
        return same_db

    def repeated_list_info(self, repeated_dict: dict, key, dbresult_list: list):
        """Gets all information on repeated_dict items and node.

        Args:
            repeated_dict (dict): Repeated
            key (str, None): Specific key to get result. if None returs all keys.
            dbresult_list (list): list of dbresult objects

        Returns:
            dict: result_dict type dictionary with:
            {key:[(index of repeated item,
            db,table pair index,
            id in db of repeated item,
            index of dbr_key in dbresult List,
            Node object in dbresult.dbr[dbr_key]
            )]}

        """
        node_dict = {}
        for a_key, value in repeated_dict.items():
            if a_key == key or not key:
                # print("Here -----> ",a_key,value)
                node_list = []
                for iii, (index, an_id) in enumerate(value):
                    dbresult = dbresult_list[index]
                    dbr_key = dbresult.find_dbr_key_with_att("id", an_id, True)  # list of keys
                    # print("Now --->",iii,index,an_id,dbr_key)
                    if len(dbr_key) > 0:
                        node_list.append((iii, index, an_id, dbr_key[0], dbresult.dbr[dbr_key[0]]))
                if len(node_list) > 0:
                    node_dict.update({a_key: node_list})
        return node_dict

    def find_duplicates(self, tablename):
        """Returns a list of tuple with the dictionaries of file information of each repeated file.
        Duplicates are the files in the same folder,with different file names but with the same md5 sum.
        Excludes Repeated (different folder).

        Args:
            tablename (str): table in database

        Returns:
            list: list of tuples, each dictionary in the tuple contains the duplicate files
            [({Dupfileinfo1},{Dupfileinfo2}..{DupfileinfoN}), ...({DupfileinfoX1},{DupfileinfoX2}..{DupfileinfoXN})]
        """
        repeated_dict = self.get_repeated_files(self.db, tablename)
        item_list = ["filepath", "filename"]  # ,'id', 'md5', 'size' ]
        match_list = [
            True,
            False,
        ]  # , False, True, True] same md5 implicit in repeated : if same md5-> same size, id is always different
        # return self.find_matching_data(repeated_dict,tablename,item_list,match_list)
        return self.find_matching_dbresult(repeated_dict, tablename, item_list, match_list)

    def find_repeated(self, tablename):
        """Returns a list of tuple with the dictionaries of file information of each repeated file.
        Repeated are files with the same md5 sum, in different folders within the map.
        Excludes Duplicates (same folder).

         Args:
             tablename (str): table in database

         Returns:
             list: list of tuples, each dictionary in the tuple contains the repeat files
             [({Repfileinfo1},{Repfileinfo2}..{RepfileinfoN}), ...({RepfileinfoX1},{RepfileinfoX2}..{RepfileinfoXN})]
        """
        repeated_dict = self.get_repeated_files(self.db, tablename)

        item_list = ["filename", "filepath"]  # ,'id', 'md5', 'size']
        match_list = [False, False]  # , False, True, True]
        # return self.find_matching_data(repeated_dict,tablename,item_list,match_list)
        return self.find_matching_dbresult(repeated_dict, tablename, item_list, match_list)

    def find_matching_dbresult(self, repeated_dict: dict, table_name: str, item_list: list, match_list: list):
        """Finds matching item and match items in a database

        Args:
            repeated_dict (dict): repeated dictionary
            dbresult_list (list): list of databases
            item_list (list[str]): list of items to compare
            match_list (list[bool]): comparison criteria match

        Returns:
            list: list of tuples, each dictionary in the tuple contains the matching files
            [({Matfileinfo1},{Matfileinfo2}..{MatfileinfoN}), ...({MatfileinfoX1},{MatfileinfoX2}..{MatfileinfoXN})]
        """
        a_key = None
        db_result = DBResult(self.db.describe_table_in_db(table_name))
        repeat_list = []
        try:
            with Progress() as progress:
                exit_key = "ctrl+c"
                if os.name == "nt":
                    exit_key = "F12"
                total_count = len(repeated_dict)
                task1 = progress.add_task(f"[blue]Calculating Match [red]({exit_key} to Exit)", total=total_count)
                for count_processed, (a_key, db_id_tup_list) in enumerate(repeated_dict.items()):
                    msg1 = f"{count_processed+1}/{total_count} found {len(repeat_list)}"
                    msg2 = f" looking at {a_key}={repeated_dict[a_key]}"
                    print(f"{msg1}{msg2}")
                    data_same_md5 = []
                    if len(db_id_tup_list) <= SINGLE_MULTIPLE_SEARCH:
                        for db_id_tup in db_id_tup_list:
                            data_same_md5 = data_same_md5 + self.db.get_data_from_table(
                                table_name, "*", f"id={db_id_tup[1]}"
                            )
                    else:
                        data_same_md5 = self.db.get_data_from_table(
                            table_name, "*", f"md5={self.db.quotes(a_key)}"
                        )  # makes a search in all db -> slow if few, fast if many
                    db_result.clear_values()
                    if raw_key_pressed("\xe0\x86"):  # F12
                        raise KeyboardInterrupt("User Cancel")
                    if len(data_same_md5) > 0:
                        db_result.set_values(data_same_md5)
                        for iii, _ in enumerate(data_same_md5):
                            comp_dict = {}
                            if iii == 0:
                                node_1 = db_result.dbr[iii]  # Node object
                                repeat_node = None
                            else:
                                node_2 = db_result.dbr[iii]  # Node object
                                comp_dict = db_result.compare_nodes(node_1, node_2, "==")

                                repeat_file = True
                                for aaa, bbb in zip(item_list, match_list):
                                    if bbb != comp_dict[aaa]:
                                        repeat_file = False
                                        break
                                if repeat_file:
                                    if not repeat_node:
                                        repeat_node = (node_1.to_dict(), node_2.to_dict())
                                    else:
                                        repeat_node = repeat_node + (node_2.to_dict(),)
                            if repeat_node:
                                repeat_list.append(repeat_node)
                    progress.update(task1, completed=count_processed + 1)
                progress.update(task1, completed=total_count)
        except KeyboardInterrupt:
            print("[magenta]User cancel")
            print("@" * 100, "\nPress any Key to continue\n", "@" * 100)
            getch()
        return repeat_list

    @staticmethod
    def compare_data_tuple(comp_dict: dict, data1: tuple, data2: tuple) -> bool:
        for index, result in comp_dict.items():
            comp = data1[index] == data2[index]
            if comp != result:
                return False
        return True

    def find_matching_data(self, repeated_dict: dict, table_name: str, item_list: list, match_list: list):
        """Finds matching item and match items in a database

        Args:
            repeated_dict (dict): repeated dictionary
            dbresult_list (list): list of databases
            item_list (list[str]): list of items to compare
            match_list (list[bool]): comparison criteria match

        Returns:
            list: list of tuples, each dictionary in the tuple contains the matching files
            [({Matfileinfo1},{Matfileinfo2}..{MatfileinfoN}), ...({MatfileinfoX1},{MatfileinfoX2}..{MatfileinfoXN})]
        """
        a_key = None
        comp_dict = {}
        field_list = self.db.get_column_list_of_table(table_name)
        for item, match in zip(item_list, match_list):
            for iii, fff in enumerate(field_list):
                if fff == item:
                    comp_dict.update({iii: match})

        repeat_list = []
        with Progress() as progress:
            exit_key = "F12"
            if os.name == "nt":
                exit_key = "F12"
            total_count = len(repeated_dict)
            task1 = progress.add_task(f"[blue]Calculating Match [red]({exit_key} to Exit)", total=total_count)
            for count_processed, (a_key, db_id_tup_list) in enumerate(repeated_dict.items()):
                msg1 = f"{count_processed+1}/{total_count} found "
                msg2 = f"{len(repeat_list)} looking at {a_key}={repeated_dict[a_key]}"
                print(f"{msg1}{msg2}")
                data_same_md5 = []
                if len(db_id_tup_list) < 10:
                    for db_id_tup in db_id_tup_list:
                        data_same_md5 = data_same_md5 + self.db.get_data_from_table(
                            table_name, "*", f"id={db_id_tup[1]}"
                        )
                else:
                    data_same_md5 = self.db.get_data_from_table(
                        table_name, "*", f"md5={self.db.quotes(a_key)}"
                    )  # makes a search in all db -> slow if few, fast if many
                if raw_key_pressed("\xe0\x86"):  # F12
                    return repeat_list
                if len(data_same_md5) > 0:
                    repeat_node = self.combinatorial_compare(field_list, comp_dict, data_same_md5)
                    if repeat_node:
                        repeat_list.append(repeat_node)
                progress.update(task1, completed=count_processed + 1)
            progress.update(task1, completed=total_count)
        return repeat_list

    def combinatorial_compare(self, field_list: list, comp_dict: dict, d_list: list[tuple]) -> tuple[dict]:
        """Compares all combinations in list.

        Args:
            field_list (list): fields of the data in data_list tuples
            comp_dict (dict): dictionary of comparisons
            d_list (list[tuple]): list of database data tuples

        Returns:
            tuple[dict]: if a combination matches the comp_dict criteria, the data is added as dictionary in a tuple
        """
        repeat_node = None
        # if len(d_list)>=2:
        #     # d_list=data_list.copy()
        lendlist = len(d_list)
        total = lendlist
        iii = 0
        while lendlist > 1:
            data1 = d_list.pop(0)
            if total > 100:
                A_C.print_cycle(iii, total)
            for data2 in d_list:
                if self.compare_data_tuple(comp_dict, data1, data2):
                    if not repeat_node:
                        repeat_node = (
                            self.data_to_field_dict(field_list, data1),
                            self.data_to_field_dict(field_list, data2),
                        )
                    else:
                        repeat_node = repeat_node + (self.data_to_field_dict(field_list, data2),)
            lendlist = len(d_list)
            iii = iii + 1
        return repeat_node

    @staticmethod
    def data_to_field_dict(field_list: list, data: tuple) -> dict:
        """Returns a dictionary with fields and data Data in tuple

        Args:
            field_list (list): fields of data
            data (tuple): data in tuple

        Returns:
            dict: {field:data}
        """
        result = {}
        if len(field_list) == len(data):
            for field, ddd in zip(field_list, data):
                result.update({field: ddd})
        return result

    def __del__(self):
        """On deletion close correctly"""
        try:
            self.close()
        finally:
            pass

    def close(self):
        """Close db connection"""
        if hasattr(self, "is_db_encrypted"):
            if self.is_db_encrypted:
                self.db.encrypt_db()
        if hasattr(self, "db"):
            self.db.close_connection()
