########################
# F.garcia
# creation: 05.02.2025
########################
import os
from datetime import datetime
import hashlib

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate
from class_device_monitor import DeviceMonitor
from class_database_result import DBResult


class FileMapper:
    def __init__(self,db_filepath,key_filepath,password):
        self.password=password
        self.db_path_file=db_filepath
        self.db_file=FileManipulate.extract_filename(db_filepath,True)
        self.db_path=FileManipulate.extract_path(db_filepath,True)
        self.key_filepath=''
        if key_filepath:
            self.key_filepath=key_filepath
        self.key = None
        self.db =self.start_db(self.db_path_file,self.key_filepath,self.password)
        self.db_list=[self.db]
        self.is_db_encrypted=False
        if os.path.exists(self.key_filepath):
            self.is_db_encrypted=True
        if not os.path.exists(self.db_path):
            os.mkdir(self.db_path)
        self.active_devices = []
        self.look_for_active_devices()
        self.mapper_reference_table="__File_Mapper_Reference__"

    def look_for_active_devices(self):
        """Looks for devices mounted sets the device, serial list to active_devices
        """
        md=DeviceMonitor(log_print=True)
        for _,serial in md.devices:
            if not serial:
                md.check_none_devices()
        self.active_devices = md.devices
        print(f"Found devices: {self.active_devices}")
        
    @staticmethod
    def start_db(db_path_file,key_filepath,password = None):
        """Starts a database. If not existing, database is created. Returns connected database object.

        Args:
            db_path_file (str): database file with path
            key_filepath (str): if encrypted, encryption key file with path else None 
            password (str, optional): if db is password proteced. Defaults to None.

        Returns:
            SQLiteDatabase: database
        """
        key = None
        # 
        if os.path.exists(db_path_file): #if db exists
            if os.path.exists(key_filepath):
                with open(key_filepath, 'rb') as f:
                    key = f.read()
                db = SQLiteDatabase(db_path_file,True,key,password)
            else:
                db = SQLiteDatabase(db_path_file,False,None,password)
        else: #if db not exists
            if key_filepath:
                # Create new encrypted database
                db = SQLiteDatabase(db_path_file,True,None,password)
                key_generated=db.encrypt_db()
                if key_generated:
                    db.save_key_to_file(key_filepath)
                    db.decrypt_db()
            else:
                db = SQLiteDatabase(db_path_file,False,None,password)
        db.create_connection()
        return db

    def calculate_time_elapsed(start_datetime,end_datetime):
        """Calculate the time elapsed between two timestamps"""
        time_elapsed = (end_datetime - start_datetime).total_seconds()
        return time_elapsed

    @staticmethod
    def calculate_md5(file_path):
        """
        Calculate the MD5 hash of a file.
        
        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.
            
        Returns:
            str: The MD5 sum as a hexadecimal string.
        """
        try:
            with open(file_path, 'rb') as f:
                md5 = hashlib.md5()
                while chunk := f.read(4096):
                    md5.update(chunk)
                return md5.hexdigest()

        except FileNotFoundError:
            print(f"File {file_path} not found.")
            exit(1)

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
            with open(file_path, 'rb') as f:
                sha1 = hashlib.sha1()
                while chunk := f.read(4096):
                    sha1.update(chunk)  
                return sha1.hexdigest()

        except FileNotFoundError:
            print(f"File {file_path} not found.")
            exit(1)

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
            with open(file_path, 'rb') as f:
                sha256 = hashlib.sha256()
                while chunk := f.read(4096):
                    sha256.update(chunk)   
                return sha256.hexdigest()

        except FileNotFoundError:
            print(f"File {file_path} not found.")
            exit(1)

    @staticmethod
    def remove_mount_from_path(mount:str,path:str) -> str:
        """Removes the mounting point
        Args:
            mount (str): mounting point
            path (str): path

        Returns:
            _type_: _description_
        """
        if mount.endswith("\\"):
            mount=mount.replace("\\",'')
            return path.replace(mount,'')
        if mount.endswith("/"):
            return '/'+path.replace(mount,'')    
        return path.replace(mount,'')

    def find_mount_serial_of_path(self,path):
        """Returns the mount point and serial for a path on an active device.

        Args:
            path (str): path to look for

        Returns:
            tuple: (mount, serial)
        """
        # find mounting point
        mount=''
        serial=''
        if isinstance(self.active_devices,list):
            for md in self.active_devices:
                if md[0] in path:
                    mount=md[0]
                    serial=md[1]
            return mount, serial

    def add_table_to_mapper_index(self,table_name,path_to_map):
        """Adds the information of the table to mapper index table

        Args:
            db (SQLiteDatabase): database
            table_name (str): table in database
            path_to_map (str): path in device
        """
        db=self.db
        #if not db.table_exists(self.mapper_reference_table):
        db.create_table(self.mapper_reference_table,[('dt_map_created', 'DATETIME DEFAULT CURRENT_TIMESTAMP', True),
                                        ('dt_map_modified', 'DATETIME', True),
                                        ('mappath','TEXT',True),
                                        ('tablename','TEXT',True), 
                                        ('mount','TEXT',True), 
                                        ('serial', 'TEXT', True), 
                                        ('mapname', 'TEXT', True), 
                                        ('maptype', 'TEXT', True),
                                        ])
        db_result=DBResult(db.describe_table_in_db(self.mapper_reference_table))
        db_result.set_values(db.get_data_from_table(self.mapper_reference_table,'*',f"tablename='{table_name}'"))
        table_indexed=False
        if len(db_result.dbr)>0:
            # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
            for dbr in db_result.dbr:
                if dbr.tablename == table_name:
                    table_indexed=True
                    an_id=dbr.id
                    break
        if not table_indexed:
            print(f"Table {table_name} is Not in reference indexed")
        mapname=""
        maptype="Device Map"
        dt_map_created=datetime.now()
        dt_map_modified=datetime.now()
        # find mounting point
        mount, serial =self.find_mount_serial_of_path(path_to_map)
        mappath=self.remove_mount_from_path(mount,path_to_map)
        if table_indexed:
            # Update mount point and date modified
            print(f"Editing table {table_name}")
            db.edit_value_in_table(self.mapper_reference_table,an_id,'dt_map_modified',dt_map_modified)
            db.edit_value_in_table(self.mapper_reference_table,an_id,'mount',mount)
        else:
            print(f"Indexing table {table_name}")
            data=[(dt_map_created,dt_map_modified,mappath,table_name,mount,serial,mapname,maptype)]
            db.insert_data_to_table(self.mapper_reference_table,data)
        # # check
        # if db.get_number_or_rows_in_table(self.mapper_reference_table):
        #     raise ValueError("No data was added to index")    
            
    def map_a_path_to_db(self,table_name,path_to_map,log_print=True):
        """Maps a path in a device into a table in the database.

        Args:
            db (SQLiteDatabase): database
            table_name (_type_): table to map the path
            path_to_map (_type_): path to map on the device
            log_print (bool, optional): print logs. Defaults to True.
        """
        db=self.db
        try:
            self.add_table_to_mapper_index(table_name,path_to_map)
            db.create_table(table_name,[('dt_data_created', 'DATETIME DEFAULT CURRENT_TIMESTAMP', True),
                                        ('dt_data_modified', 'DATETIME', True),
                                        ('filepath','TEXT',True), 
                                        ('filename','TEXT',True), 
                                        ('md5', 'TEXT', True), 
                                        ('size', 'REAL', True), 
                                        ('dt_file_created','DATETIME',False),
                                        ('dt_file_accessed','DATETIME',False),
                                        ('dt_file_modified','DATETIME',False),
                                        ])
            data=[]
            iii=0
            files_processed=0
            mount, _ =self.find_mount_serial_of_path(path_to_map)
            for dirpath, dirnames, filenames in os.walk(path_to_map):
                dirpath_nm=self.remove_mount_from_path(mount,dirpath)
                if files_processed==0:
                    last_dirpath=dirpath_nm
                
                for file in filenames:
                    dt_data_created=datetime.now()
                    joined_file=os.path.join(dirpath,file)
                    the_md5=self.calculate_md5(joined_file)
                    the_size=FileManipulate.get_file_size(joined_file)
                    dt_data_modified=datetime.now()
                    dt_file_a=FileManipulate.get_accessed_date(joined_file)
                    dt_file_c=FileManipulate.get_created_date(joined_file)
                    dt_file_m=FileManipulate.get_modified_date(joined_file)
                    if log_print:
                        print(f"{files_processed} {dirpath}{os.sep}{file} [{the_md5}]\t{the_size / (1024 * 1024):.2f} MB")
                    data.append((dt_data_created,dt_data_modified,dirpath_nm,file,the_md5,the_size,dt_file_c,dt_file_a,dt_file_m))
                    iii=iii+1
                    if iii>10:
                        if log_print:
                            print("+"*10)
                        db.insert_data_to_table(table_name,data)
                        data=[]
                        iii=0
                    files_processed=files_processed+1
            db.insert_data_to_table(table_name,data)
            #db.print_all_rows(table_name)
            if log_print:
                print(db.get_number_or_rows_in_table(table_name))
        except Exception as eee:
            print(f"Error: {eee}")
            db.close_connection()

    def get_repeated_files(self,db: SQLiteDatabase,table_name) -> dict[list]:
        """Gets repeated files in map

        Args:
            db (SQLiteDatabase): database
            table_name (_type_): table

        Returns:
            dict[list]: repeated file ids
                        md5sum:[id of files repeated]
        """
        return self.get_repeated_file_multiple_db_tables([db],[table_name],["id", "md5"],1)
       

    @staticmethod
    def get_repeated_file_multiple_db_tables(db_list: list[SQLiteDatabase],table_name_list: list,column_list:list=['id','md5'],Orderby=1) -> dict[list]:
        """Gets repeated files in multiple maps. Maps can be is same or different db.

        Args:
            db_list (list[SQLiteDatabase]): database list (same length as table_name_list)
            table_name_list (list): list of tables (all tables must contain the columns in colunm_list)
            column_list (list): columns in tables, default ['id','md5']
            Orderby (int): 0 indexed column to be used. Default 1 -> 'md5'

        Returns:
            dict[list]: {(ordered column name):(list of other columns repeated)..} 
            repeated file ids
            default:  md5sum:[id of files repeated]
        """
        repeated={}
        try:
            data_list=[]
            cols=str(column_list).replace("[","").replace("'","").replace("]","")
            for index,(db,table_name) in enumerate(zip(db_list,table_name_list)):
                data=db.get_data_from_table(f"{table_name} ORDER BY {column_list[Orderby]}", f"{cols}")
                for ddd in data:
                    data_list.append((index,)+ddd) # add [db,table] index to tuple

            iii=0
            last_anmd5=None
            last_an_id=None
            last_db=None
            for dbtable,an_id,anmd5 in data_list:
                if last_anmd5 == anmd5:
                    if anmd5 in repeated:
                        rep_list=repeated[anmd5]
                        if isinstance(rep_list,list):
                            rep_list.append((dbtable,an_id))
                            repeated.update({anmd5:rep_list})
                    else:
                        repeated.update({anmd5:[(last_db,last_an_id),(dbtable,an_id)]})
                last_anmd5=anmd5
                last_an_id=an_id
                last_db=dbtable
                iii=iii+1
        except Exception as e:
            print(f"Error: {e}")
            db.close_connection()
        return repeated

    @staticmethod
    def repeated_list_show(repeated_dict:dict,key,db_list: list[SQLiteDatabase],table_name_list: list,db_cols:list=['id','filepath','filename','md5']):
        """Gets additional information on repeated_dict items.

        Args:
            repeated_dict (dict): repeated dictionary
            key (str): key to show
            db_list (list[SQLiteDatabase]): database list (same length as table_name_list)
            table_name_list (list): list of tables (all tables must contain the columns in db_cols)
            db_cols (list, optional): colums to show. Defaults to ['id','filepath','filename','md5']. if None will add all columns.

        Returns:
            list: additional info list
        """
        if not db_cols:
            # add all columns 
            db_cols=[]
            description=db_list[0].describe_table_in_db(table_name_list[0])
            for ddd in description:
                db_cols.append(ddd[1])

        rep_tup=repeated_dict[key]
        from_txt= str(db_cols).replace("[","").replace("'","").replace("]","")
        info=[]
        for a_db,an_id in rep_tup:
            db=db_list[a_db]
            if isinstance(db,SQLiteDatabase):
                table_name=table_name_list[a_db]
                where= f"id={an_id}"
                data=db.get_data_from_table(table_name,from_txt,where)
                if len(data)>0:
                    info.append(data[0])
        return info
    
    def delete_map(self,table_name):
        """Removes a map from index and its referenced table from db.

        Args:
            db (SQLiteDatabase): database
            table_name (str): table
        """
        try:
            if self.db.table_exists(self.mapper_reference_table):
                db_result=DBResult(self.db.describe_table_in_db(self.mapper_reference_table))
                db_result.set_values(self.db.get_data_from_table(self.mapper_reference_table,'*',f"tablename='{table_name}'"))
                if len(db_result.dbr)>0:
                    # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
                    an_id=getattr(db_result.dbr[0],'id')
                    print(f"Here id {an_id}")
                    self.db.delete_data_from_table(self.mapper_reference_table,f'id={an_id}')
                    print(f"{table_name} reference was deleted!!")
                else:
                    print(f"{table_name} Not found in reference!")
            if self.db.table_exists(table_name):
                self.db.delete_data_from_table(table_name,None) #remove all data
                self.db.delete_table_from_db(table_name)
                print(f"{table_name} was deleted!!")
                
        except Exception as eee:
            print(f"{table_name} was not deleted: {eee}")

    def check_if_map_device_active(self,db:SQLiteDatabase,table_name:str,rescan_devices:bool=True):
        """Checks if mounted device is active, and if map path exists. Returns the mounting point if device is active. 

        Args:
            db (SQLiteDatabase): database of table
            table_name (str): map table to look for
            rescan_devices (bool, optional): scan the connected devices again. Defaults to True.

        Returns:
            tuple: (mount, mount_active, mappath_exists)
                mount: device mount point or None if serial is not found
                mount_active: True if serial matches or mappath exists in a device active, 
                mappath_exists: None if no serial matches. True if Serials match and path exists in mount, False if serials match but path not in mount. 
        """
        if rescan_devices:
            self.look_for_active_devices()
        mount=None
        mount_active=False
        mappath_exists=None
        if db.table_exists(table_name):
            try:
                db_result=DBResult(db.describe_table_in_db(self.mapper_reference_table))
                db_result.set_values(db.get_data_from_table(self.mapper_reference_table,'*',f"tablename='{table_name}'"))
                if len(db_result.dbr)>0:
                    # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
                    an_id=getattr(db_result.dbr[0],'id')
                    mappath=getattr(db_result.dbr[0],'mappath')
                    mp_mount=getattr(db_result.dbr[0],'mount')
                    serial=getattr(db_result.dbr[0],'serial')
                else:
                    print(f"No data found in reference table for {table_name}")
                    return mount, mount_active, mappath_exists    
                
                for md in self.active_devices:
                    if md[1] in serial:
                        mount=md[0]
                        mount_active=True 
                # Check if path exists
                if mount:
                    mappath_exists=os.path.exists(os.path.join(mount,mappath))
                else:
                    for md in self.active_devices:
                        if os.path.exists(os.path.join(md[0],mappath)):
                            mount=md[0]
                            print(f"path exists on device {md[1]} not found in {serial}")
                            mount_active=True
                            break
                # update mounting point
                if mappath_exists and mp_mount!=mount and mount:
                    dt_map_modified=datetime.now()
                    db.edit_value_in_table(self.mapper_reference_table,an_id,'dt_map_modified',dt_map_modified)
                    db.edit_value_in_table(self.mapper_reference_table,an_id,'mount',mount)
            except IndexError:
                pass

        return mount, mount_active, mappath_exists
    
    def close(self):
        """Close db connection"""
        self.db.close_connection()
