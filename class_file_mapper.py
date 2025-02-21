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
from class_data_manage import DataManage 
from class_autocomplete_input import getch
from rich import print
from rich.progress import Progress

class FileMapper:
    def __init__(self,db_filepath,key_filepath,password):
        self.password=password
        self.db_path_file=db_filepath
        self.db_file=FileManipulate.extract_filename(db_filepath,True)
        self.db_path=FileManipulate.extract_path(db_filepath,True)
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
        self.key_filepath=''
        if key_filepath:
            self.key_filepath=key_filepath
        self.key = None
        self.is_db_encrypted=False
        self.db_has_password=False
        self.db, self.is_db_encrypted, self.db_has_password = self.start_db(self.db_path_file,self.key_filepath,self.password)
        self.db_list=[self.db]
        # connect
        self.db.create_connection()
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
            bool: is_encrypted
            bool: has_password 
        """
        key = None
        has_password=False
        is_encrypted=False
        has_password=False
        db=None
        # 
        if os.path.exists(db_path_file): #if db exists
            if os.path.exists(key_filepath):
                with open(key_filepath, 'rb') as f:
                    key = f.read()
                db = SQLiteDatabase(db_path_file,True,key,password)
                is_encrypted=True
            else:
                is_encrypted=False
                db = SQLiteDatabase(db_path_file,False,None,password)
        else: #if db not exists
            if key_filepath:
                # Create new encrypted database
                is_encrypted=True
                db = SQLiteDatabase(db_path_file,True,None,password)
                key_generated=db.encrypt_db()
                if key_generated:
                    db.save_key_to_file(key_filepath)
                    db.decrypt_db()
            else:
                is_encrypted=False
                db = SQLiteDatabase(db_path_file,False,None,password)
        if password:
            has_password=True
        print("Started:",db,is_encrypted,has_password)
        return db,is_encrypted,has_password

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

    def find_mount_serial_of_path(self,path:str):
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
                if path.startswith(md[0]):
                    mount=md[0]
                    serial=md[1]
                    break
                if path.startswith(md[0].lower()):
                    mount=md[0].lower()
                    serial=md[1]
                    break
                if path.startswith(md[0].upper()):
                    mount=md[0].upper()
                    serial=md[1]
                    break
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
    
    def map_to_file_structure(self,a_map,where=None,fields_to_tab:list[str]=None,sort_by:list=None,ascending:bool=True)->dict:
        """Generates a file structure from map information

        Args:
            database (str): database
            a_map (str): table in database
            where (_type_, optional): sql filter for the database search. Defaults to None.
            fields_to_tab (list[str], optional): Additional information to 'filename' and 'size' from map into file tuple. Defaults to None.
            sort_by (list, optional): Dataframe sorting. Defaults to None.
            ascending (bool, optional): AScending descending order for sorting. Defaults to True.

        Returns:
            dict: filestruct of map
        """
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        field_list=self.db.get_column_list_of_table(a_map)
        # Map info
        # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
        map_info=self.db.get_data_from_table(self.mapper_reference_table,'*',f"tablename='{a_map}'")
        if len(map_info)==0:
            return {}
        mappath=map_info[0][3]
        data=self.db.get_data_from_table(a_map,'*',where)  
        try:
            d_m1=DataManage(data,field_list)
        except ValueError:
            # No data
            return {}
        default=['filename','size']
        fields2tab=[]
        if isinstance(fields_to_tab,list):   
            for field in fields_to_tab:
                if field not in default and field in field_list:
                    fields2tab.append(field) 
        df=d_m1.get_selected_df(fields_to_tab=fields2tab,sort_by=sort_by,ascending=ascending)
        df=d_m1.get_selected_df(fields_to_tab=field_list,sort_by=sort_by,ascending=ascending)
        map_list=[]
        fi_ma=FileManipulate()
        for iii,(filepath, filename, size) in enumerate(zip(df['filepath'], df['filename'], df['size'])):
            #print(f"{filepath} - {filename}, Size: {size}")
            file_tuple=(filename,size)
            #Add more info to the tuple
            for field in fields2tab:
                file_tuple=file_tuple+(df[field][iii],)
            if iii==0:
                dict1=fi_ma.path_to_file_structure_dict(filepath,file_tuple)
                map_list=[dict1]
            elif iii==1:
                dict2=fi_ma.path_to_file_structure_dict(filepath,file_tuple)
                map_list=fi_ma.merge_file_structure_dicts(dict1,dict2) 
            else:
                dict3=fi_ma.path_to_file_structure_dict(filepath,file_tuple)
                map_list=fi_ma.merge_file_structure_lists(map_list,[dict3])    
        file_struct={mappath:map_list}
        return file_struct


    def file_structure_to_map(self,table_name):
        # this may not have sense since lacks information
        pass    

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
            start_datetime=datetime.now()
            for dirpath, _, filenames in os.walk(path_to_map):
                # Get the data for each file
                for file in filenames:
                    line_data_tup=self.get_mapping_info_data_from_file(mount,dirpath,file,log_print,f'{files_processed}. ')
                    data.append(line_data_tup)
                    iii=iii+1
                    if iii>=10:
                        if log_print:
                            delta = (datetime.now() - start_datetime)
                            print("+"*10+f" Time elapsed: {str(delta).split(".")[0]}"+"+"*10)
                        db.insert_data_to_table(table_name,data)
                        data=[]
                        iii=0
                    files_processed=files_processed+1
            db.insert_data_to_table(table_name,data)
            #db.print_all_rows(table_name)
            
            if log_print:
                # time_elapsed = (datetime.now() - start_datetime).total_seconds()
                delta = (datetime.now() - start_datetime)
                print("+"*33)        
                print(f'[green]Successfully Mapped {db.get_number_or_rows_in_table(table_name)} files in {str(delta).split(".")[0]}')
                print("+"*33,"\nPress any Key to continue\n","+"*33)
                getch()
        except Exception as eee:
            print(f"[red]Error Mapping: {eee}")
            print(type(eee),line_data_tup)
            print("@"*100,"\nPress any Key to continue\n","@"*100)        
            getch()
            # db.close_connection()

    @staticmethod
    def time_seconds_to_hhmmss(time_seconds:float)->str:
        """Returns time in HH:MM:SS format
        """
        hours, remainder = divmod(time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:.0f}:{minutes:.0f}:{seconds:.0f}'

    @staticmethod
    def estimate_mapping_time_sec(size_sample,time_sample_sec, size_to_calculate,units_sample='bytes',units_calc='bytes')->float:
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
        us=units_sample.lower()
        uc=units_calc.lower()
        if us not in ['bytes','by','kb','mb','tb','gb']:
           us='bytes'
        if uc not in ['bytes','by','kb','mb','tb','gb']:
            uc='bytes' 
        if size_sample<=0:
            return 0
        if us==uc:
            return  int(size_to_calculate)/int(size_sample)*time_sample_sec
        def to_bytes(us,size_sample):
            if us in ['bytes','by']:
                bytes_sample=int(size_sample)
            elif us == 'kb':
                bytes_sample=int(size_sample)*1024
            elif us == 'mb':
                bytes_sample=int(size_sample)*1024**2
            elif us == 'gb':
                bytes_sample=int(size_sample)*1024**3
            elif us == 'tb':
                bytes_sample=int(size_sample)*1024**4
            return bytes_sample    
        return to_bytes(uc,size_to_calculate)/to_bytes(us,size_sample)*time_sample_sec
         
    def get_mapping_info_data_from_file(self,mount:str,dirpath:str,file:str,log_print:bool=False,count_print='')->tuple:
        """gets tuple with map table info from inputs 

        Args:
            mount (str): the mount
            dirpath (str): the path (no mount)
            file (str): the file
            log_print (bool, optional): If you want to print. Defaults to False.
            count_print (int | str, optional): If you want to print the count. Defaults to ''.

        Returns:
            tuple: (dt_data_created,dt_data_modified,dirpath_nm,file,the_md5,the_size,dt_file_c,dt_file_a,dt_file_m)
        """
        dt_data_created,dt_data_modified,dirpath_nm,the_md5,dt_file_c,dt_file_a,dt_file_m=[None]*7
        the_size=-1
        f_m=FileManipulate()
        try:
            dirpath_nm=self.remove_mount_from_path(mount,dirpath)
            dt_data_created=datetime.now()
            # when joining, calculating or sizing fails hava a datetime (required in db)
            dt_data_modified=dt_data_created
            # join
            joined_file=os.path.join(dirpath,file)
            #size
            the_size=f_m.get_file_size(joined_file)
            # md5 calculate
            if the_size > 349175808 and log_print: #333*1024*1024=349175808
                str_size=f_m.get_size_str_formatted(the_size)
                print(f"Calculating md5 for {file}...{str_size}")
            the_md5=self.calculate_md5(joined_file)
            dt_data_modified=datetime.now()
            # get file dates
            dt_file_a=f_m.get_accessed_date(joined_file)
            dt_file_c=f_m.get_created_date(joined_file)
            dt_file_m=f_m.get_modified_date(joined_file)
            if log_print:
                str_size=f_m.get_size_str_formatted(the_size,11)
                # use () not [] because rich looks for commands inside []
                str_just=f_m.get_string_justified(f"{count_print}({str_size})",False,11+3+4)
                time_elapsed = (dt_data_modified - dt_data_created).total_seconds()
                print(f"{str_just} ({the_md5}) \t{dirpath+os.sep+file} ... ({time_elapsed:.3f}s)")
        except (FileExistsError,PermissionError,FileNotFoundError,NotADirectoryError,TypeError) as eee:
            print(f"{mount}{dirpath}{file} Error: {eee}")
            if not the_md5:
                the_md5='::UNKNOWN::'
            if not the_size:
                the_size=-1
            if not dt_file_c:
                dt_file_c=dt_data_created
            if not dt_file_a:
                dt_file_a=dt_data_created
            if not dt_file_m:
                dt_file_m=dt_data_created
            # print("@"*100,"\nPress any Key to continue\n","@"*100)        
            # getch()
            return (dt_data_created,dt_data_modified,dirpath_nm,file,the_md5,the_size,dt_file_c,dt_file_a,dt_file_m)
        
        return (dt_data_created,dt_data_modified,dirpath_nm,file,the_md5,the_size,dt_file_c,dt_file_a,dt_file_m)

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
            # db.close_connection()
        return repeated
    
    def validate_new_map_name(self,new_table_name:str):
        """Check if New table name is Correct"""
        tables=self.db.tables_in_db()
        if new_table_name in tables:
            return False
        return True
    
    def rename_map(self,table_name:str,new_table_name:str)->bool:
        if table_name==new_table_name or table_name=='' or new_table_name=='':
            return False
        tables=self.db.tables_in_db()
        if table_name in tables and self.validate_new_map_name(new_table_name):
            db_result=DBResult(self.db.describe_table_in_db(self.mapper_reference_table))
            db_result.set_values(self.db.get_data_from_table(self.mapper_reference_table,'*',f"tablename='{table_name}'"))
            if len(db_result.dbr)>0:
                # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
                an_id=getattr(db_result.dbr[0],'id')
            else:
                return False
            print(f"Editing table {table_name}")
            self.db.edit_value_in_table(self.mapper_reference_table,an_id,'dt_map_modified',datetime.now())
            self.db.edit_value_in_table(self.mapper_reference_table,an_id,'tablename',new_table_name)
            # Rename table
            self.db.send_sql_command(f'ALTER TABLE {table_name} RENAME TO {new_table_name}')


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
            db_cols=db_list[0].get_column_list_of_table(table_name_list[0])
            
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
    
    def set_mapname(self,table_name,name):
        """Renames name field in Reference

        Args:
            table_name (str): table 
            name (str): new name
        """
        if self.db.table_exists(self.mapper_reference_table):
            id_list=self.db.get_data_from_table(self.mapper_reference_table,'id',f"tablename='{table_name}'")
            if len(id_list)>0:
                self.db.edit_value_in_table(self.mapper_reference_table,id_list[0],'mapname',name)

    def get_referenced_attribute(self,attr):
        """Returns the column of mapper_reference_table as list for the attribute
            
        Args:
            attr (str): 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
        Returns:
            list: column in db with attribute    
        """
        tablename_list=[]
        if self.db.table_exists(self.mapper_reference_table):
            db_result=DBResult(self.db.describe_table_in_db(self.mapper_reference_table))
            db_result.set_values(self.db.get_data_from_table(self.mapper_reference_table,'*'))
            # 'id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'
            for dbr in db_result.dbr:
                #print(getattr(dbr,attr))
                tablename_list.append(getattr(dbr,attr))
        return tablename_list

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
    
    def get_dbresult_list(self,db_list: list[SQLiteDatabase],table_name_list: list) -> list[DBResult]:
        """Returns a list with the dbresult objects for each database,table pair.

        Args:
            db_list (list[SQLiteDatabase]): database list
            table_name_list (list): table list

        Returns:
            list[DBResult]: Dbresult of each db, table pair
        """
        dbresult_list=[]
        if len(db_list)!=len(table_name_list):
            print("Error: database,table Pairs have deffernt lengths!")
            return  dbresult_list
        for a_db,table_name in zip(db_list,table_name_list):
            db_result=DBResult(a_db.describe_table_in_db(table_name))
            db_result.set_values(a_db.get_data_from_table(table_name,'*',None))
            dbresult_list.append(db_result)
        return  dbresult_list
    
    @staticmethod
    def repeated_in_same_db(repeated_dict,key)->bool:
        """Finds if items are repeated in the same database

        Args:
            repeated_dict (dict): repeated item dictionary
            key (str): None to look all dictionary. or key of specific item

        Returns:
            _type_: _description_
        """
        same_db=None
        for a_key,value in repeated_dict.items():
            if a_key==key or not key:
                same_db=True
                last_index=0
                for iii,(index,_) in enumerate(value):
                    if iii==0:
                        last_index=index
                    else:
                        if index!=last_index:
                             return False
        return same_db
    
    def repeated_list_info(self,repeated_dict:dict,key, dbresult_list: list):
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
        node_dict={}
        for a_key,value in repeated_dict.items():   
            if a_key==key or not key:
                # print("Here -----> ",a_key,value)
                node_list=[]
                for iii,(index,an_id) in enumerate(value):
                    dbresult=dbresult_list[index]
                    dbr_key=dbresult.find_dbr_key_with_att('id',an_id,True) #list of keys
                    # print("Now --->",iii,index,an_id,dbr_key)
                    if len(dbr_key)>0:
                        node_list.append((iii,index,an_id,dbr_key[0],dbresult.dbr[dbr_key[0]]))
                        #print(iii,an_id,dbr_key,dbresult.dbr[dbr_key[0]].filename,dbresult.dbr[dbr_key[0]].size,dbresult.dbr[dbr_key[0]].md5)
                if len(node_list)>0:
                    node_dict.update({a_key:node_list})
        return node_dict    

    def find_duplicates(self,tablename):
        """Returs a list of tuple with the dictionaries of file information of each repeated file.
        Duplicates are the files in the same folder,with different file names but with the same md5 sum.

        Args:
            tablename (str): table in database

        Returns:
            list: list of tuples, each dictionary in the tuple contains the duplicate files
            [({Dupfileinfo1},{Dupfileinfo2}..{DupfileinfoN}), ...({DupfileinfoX1},{DupfileinfoX2}..{DupfileinfoXN})]
        """
        repeated_dict=self.get_repeated_files(self.db,tablename)
        dbresult_list=self.get_dbresult_list([self.db],[tablename])
        a_key=None #key_list[3]
        repeated_info_dict=self.repeated_list_info(repeated_dict,a_key,dbresult_list)
        #print(repeated_info_dict)
        # repeated_in_same_db=self.repeated_in_same_db(repeated_dict,a_key)
        # print("Elements in same database,table pair: {}".format(repeated_in_same_db))
        duplicate_list=[]
        for a_key,_ in repeated_info_dict.items():
            for iii,rid_list in enumerate(repeated_info_dict[a_key]):
                comp_dict={}
                if iii == 0:
                    node_1=rid_list[4] #Node object
                    duplicate_node=None
                else:
                    node_2=rid_list[4] #Node object
                    comp_dict=dbresult_list[0].compare_nodes(node_1,node_2,'==')
                    item_list=[ 'id', 'md5', 'size', 'filename', 'filepath']
                    match=    [False, True, True, False, True]
                    duplicate_file=True
                    #print("."*33)
                    for aaa,bbb in zip(item_list,match):
                        #print(f"{aaa}: {getattr(node_1,aaa)} ==? {getattr(node_2,aaa)} -> {comp_dict[aaa]} <- should be {bbb}")
                        if bbb != comp_dict[aaa]:
                            duplicate_file=False
                            break
                    if duplicate_file:
                        if iii==1:
                            duplicate_node=(node_1.to_dict(),node_2.to_dict())
                        else:
                            duplicate_node=duplicate_node+(node_2.to_dict(),)
                if duplicate_node:    
                    duplicate_list.append(duplicate_node)
                        # print("@"*5+'---->Duplicate')   
        return duplicate_list

    def __del__(self):
        """On deletion close correctly"""
        try:
            self.close()
        finally:
            pass

    def close(self):
        """Close db connection"""
        if hasattr(self, 'is_db_encrypted'):
            if self.is_db_encrypted:
                self.db.encrypt_db()
        if hasattr(self, 'db'):
            self.db.close_connection()
    

