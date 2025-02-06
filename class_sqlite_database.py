import os
import sqlite3
from cryptography.fernet import Fernet

class SQLiteDatabase:
    def __init__(self, db_path,encrypt=False,key=None,password=None):
        self.conn = None
        self.db_path = db_path
        self.encrypt=encrypt
        self.key=key
        self.password=password
        self.db_is_encrypted=False
        if encrypt and key:
            self.db_is_encrypted=True
        self.create_connection()
        
    def encrypt_db(self):
        """Encrypt AES-256 the database.

        Returns:
            bool: if a new key was generated. 
        """
        self.encrypt=True
        new_key=False
        # Generate a new encryption key and wrap it in a Fernet object
        if self.encrypt and not self.key:
            self.key = Fernet.generate_key()
            new_key=True
        if self.encrypt:
            fernet = Fernet(self.key)

            # Encrypt the database file using AES-256 encryption
            with open(self.db_path, 'rb') as f:
                encrypted_data = fernet.encrypt(f.read())
            with open(self.db_path, 'wb') as f:
                f.write(encrypted_data)
        return new_key
    
    def set_key(self,key):
        """Sets encryption key

        Args:
            key (Any): set internal key variable
        """
        self.key = key

    def decrypt_db(self):
        """Decrypt the database file using AES-256 encryption."""
        if self.key:
            fernet = Fernet(self.key)
            # Decrypt the database file using AES-256 encryption
            with open(self.db_path, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = fernet.decrypt(encrypted_data)
            with open(self.db_path, 'wb') as f:
                f.write(decrypted_data)

    def save_key_to_file(self,key_path):
        """Save the key in a file
        Args:
            key_path (str): path and filename of Key
        """
        with open(key_path, 'wb') as f:
            f.write(self.key)
    
    def load_key_from_file(self,key_path):
        """Load key from file

        Args:
            key_path (str): path and filename of Key
        """
        with open(key_path, 'rb') as f:
            self.key = f.read()
    
    def create_connection(self):
        """Create a new connection to the database"""
        if self.db_is_encrypted:
            self.decrypt_db()
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Connected to {self.db_path}")
        except sqlite3.Error as eee:
            print(eee)

    def create_table(self,table_name:str,Columns:list[tuple],temporary: bool=False):
        """Creates table if it does not exist

        Args:
            table_name (str): Table name
            Columns (list[tuple]): For each column except id tuple contains 
            (Column name, Data type, Not null constraint)
        """
        if len(Columns)==0:
            print("No items to make table")
            return
        
        if len(Columns[0])!=3:
            print("Wrong size of tuple: (Column name, Data type, Not null constraint)")
            return

        # Create the table
        try:
            c = self.conn.cursor()
            temp=""
            if temporary:
                temp="TEMPORARY "
            sql = "CREATE "+temp+"TABLE "
            sql=sql+table_name+" (id INTEGER PRIMARY KEY AUTOINCREMENT"
            for a_tup in Columns:
                (column_name, data_type, not_null_constraint)= a_tup
                if column_name != 'id':
                    sql = sql + ", " + column_name 
                    if data_type not in ["INTEGER", "REAL", "TEXT", "BLOB", "DATE", "TIME", "DATETIME", "BOOLEAN"]:
                        data_type="TEXT" 
                    sql = sql + ' ' + data_type + ' ' 
                    if not_null_constraint:
                        sql = sql + 'NOT NULL'

            sql=sql+");"
            c.execute(sql)
            self.commit()
        except sqlite3.OperationalError:
            pass
        except sqlite3.Error as eee:
            print(f'Error Creating table: {eee}')

    def send_sql_command(self,sql,table_to_lock=None):
        """Send any sql command, if a specific table needs to be locked then specify the table_name.

        Args:
            sql (str): SQL text
            table_to_lock (str, optional): locks the table for during operation. Defaults to None.
        """
        try:
            c = self.conn.cursor()
            c.execute(sql)
            self.commit()
        except sqlite3.OperationalError:
            pass
        except sqlite3.Error as eee:
            print(f'Error Executing sql:\n{sql}\nError: {eee}')
        finally:
            # Release all resources
            c.close()  


    def commit(self):
        """Commit any pending changes"""
        if self.conn is not None:
            self.conn.commit()

    def close_connection(self):
        """Close the current connection """
        if self.encrypt:
             if self.encrypt_db(): 
                # if there is no prior encryption key will store it before it exits
                # without the key db is useless
                fn = os.path.basename(self.db_path)  # returns just the name
                fpath = os.path.abspath(self.db_path)
                fnnoext, _ = os.path.splitext(fn)
                fpath = fpath.replace(fn, "")
                self.save_key_to_file(fpath+fnnoext+"_key.txt")
        if self.conn is not None:
            self.conn.close()

    def delete_table_from_db(self, table_name):
        """Delete a table from the database"""
        try:
            c = self.conn.cursor()
            c.execute("DROP TABLE IF EXISTS " + table_name)
            print(f"Table {table_name} deleted")
            self.commit()
        except sqlite3.Error as eee:
            print(eee)

    def rename_column_in_table(self, table_name, column_name, new_column_name):
        """Rename a column in the database"""
        try:
            c = self.conn.cursor()
            c.execute("ALTER TABLE IF EXISTS " + table_name + " RENAME COLUMN " + column_name + " TO " + new_column_name)
            print(f"Column {column_name} renamed to {new_column_name}")
            self.commit()
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()  

    def remove_column_from_table(self, table_name, column_name):
        """Remove a column from the database"""
        try:
            c = self.conn.cursor()
            c.execute("ALTER TABLE IF EXISTS " + table_name + " DROP COLUMN " + column_name)
            print(f"Column {column_name} removed")
            self.commit()
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()  
    
    def tables_in_db(self):
        """Get the list of tables in the database

        Returns:
            list: table names
        """
        c = self.conn.cursor()
        
        tables=c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return tables
    
    def print_all_rows(self,table):
        """Prints all rows in table

        Args:
            table (str): table
        """
        # Execute a SELECT statement and fetch all rows from the files table
        rows = self.get_data_from_table(table)
        # Print the values of each row
        for row in rows:
            print(row)
    
    def get_data_from_table(self,table:str,column_filter:str="*",where:str= None)->list:
        """returns the data in the rows

        Args:
            table (str):table to look at
            column_filter (str, optional): filter. Defaults to "*".
            where (str, optional): add condition statement. Defaults to None.

        Returns:
            list: data in table
        """
        data=[]
        sql = "SELECT "
        sql = sql + column_filter + " FROM "+ table
        if where:
            sql = sql + " WHERE "+ where
        try:
            c = self.conn.cursor()
            c.execute(sql)
            data= c.fetchall()
        except sqlite3.Error as eee:
            print(eee)
            # Release all resources
            # if c:
            #     c.close()  
        return data
    
    def delete_data_from_table(self,table:str,where:str= None)->list:
        """Delete data in the rows

        Args:
            table (str): table to delete the rows
            where (str, optional): add condition statement. Defaults to None.
        """
        sql = "DELETE "
        sql = sql + " FROM "+ table
        if where:
            sql = sql + " WHERE "+ where
        try:
            c = self.conn.cursor()
            c.execute(sql)
            self.commit()
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()  
        
    
    def edit_value_in_table(self, table_name:str, id:int, column_name:str, new_value):
        """Edits a value in a table.

        Args:
            table_name (str): table
            id (int): id to edit
            column_name (str): column item
            new_value (_type_): value
        """
        try:
            c = self.conn.cursor()
            # Update the specified column with the given value for all rows that match the condition
            c.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?", (new_value, id))
            #print("Row updated successfully")
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()  
    
    def table_exists(self, table: str) -> bool:
        """Table exists

        Args:
            table (str): Table name to look in db

        Returns:
            bool: True if the table exists, False otherwise.
        """
        try:
            c = self.conn.cursor()
            c.execute(f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{table}'")
            return len(c.fetchall()) > 0
        except (sqlite3.OperationalError, ValueError) as eee:
            print("No table:", eee)
            return False

    def describe_table_in_db(self, table:str)->list:
        """returns the column structure of the table

        Args:
            table (str): table name

        Returns:
            list[tuple]: For each column in the table tuple contains 
                (Index,
                Column name,
                Data type,
                Not null constraint,
                Default value,
                Primary key flag)
        """
        if not self.table_exists(table):
            return []
        # Get the column names and types of the table
        description=[]
        try:
            c = self.conn.cursor()
            c.execute(f"PRAGMA table_info({table})")
            description = c.fetchall()
            # print(table,": ",description)
        except sqlite3.OperationalError as eee:
            print("No description:", eee)
        # Print a string with the table name, column names, and data types
        # result = f"{table}: \n"
        # for row in description:
        #     result += f"- {row[0]} ({row[1]})\n"
        # print(result)
        return description

    def add_data_to_table_id(self,table:str,id:int,sample_data:tuple):
        """Add data to a table

        Args:
            table (str): Table name
            id (int): the id
            sample_data (tuple): must match with Columns name
        """
        description=self.describe_table_in_db(table)
        if len(description)==0:
            print("No data in table")
            return 
        column_name_list=[]
        data_type_list=[]
        for desc in description:
            column_name_list.append(desc[1])
            data_type_list.append(desc[2])
        
        sqltxt=str(column_name_list)
        sqltxt=sqltxt.replace("'","")
        sqltxt=sqltxt.replace(",",", ")
        sqltxt=sqltxt.replace("[","(")
        sqltxt=sqltxt.replace("]",")")
        val=sqltxt
        for ccc in column_name_list:
            val=val.replace(ccc,"?")
        sqltxt= sqltxt + " VALUES " + val
        try:
            c = self.conn.cursor()
            # Update the specified column with the given value for all rows that match the condition
            if len(sample_data)==len(column_name_list)-1:

                c.execute(f"INSERT INTO {table} {sqltxt}", (id,)+sample_data)
            else:
                print(f"id or data size is not correct {column_name_list} != {sample_data}")
                return 
            self.commit()
            #print("Row updated successfully")
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()    

    def insert_data_to_table(self,table:str,sample_data:list[tuple]):
        """Add data to a table

        Args:
            
            table (str): Table name
            sample_data (list[tuple]): must match with Columns name
        """
        description=self.describe_table_in_db(table)
        if len(description)==0:
            print("No data in table")
            return 
        column_name_list=[]
        data_type_list=[]
        for desc in description:
            if desc[1] != 'id':
                column_name_list.append(desc[1])
                data_type_list.append(desc[2])
        
        sqltxt=str(column_name_list)
        sqltxt=sqltxt.replace("'","")
        sqltxt=sqltxt.replace(",",", ")
        sqltxt=sqltxt.replace("[","(")
        sqltxt=sqltxt.replace("]",")")
        val=sqltxt
        for ccc in column_name_list:
            val=val.replace(ccc,"?")
        sqltxt= sqltxt + " VALUES " + val
        try:
            c = self.conn.cursor()
            # Update the specified column with the given value for all rows that match the condition
            for row in sample_data:
                if len(row)==len(column_name_list):
                    c.execute(f"INSERT INTO {table} {sqltxt}", row)
                else:
                    print(f"Data Size is not correct {column_name_list} != {row}")
                    return 
            self.commit()
            #print("Row updated successfully")
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()  
    
    def get_next_available_id(self,table:str)->int:
        """Gets the next id that is available in a table

        Args:
            table (str): table

        Returns:
            int: next available id
        """
        id_list=self.get_data_from_table(table,'id')
        for iii,idtup in enumerate(id_list):
            if iii+1 < idtup[0]:
                return iii+1
        return iii+2    
    
    def get_number_or_rows_in_table(self,table:str)->int:
        """Get number of rows"""
        if self.table_exists(table):
            return self.get_data_from_table(table,'COUNT(*)',None)[0][0]
        return None
    
    def reenumerate_id_sequence(self,table:str):
        """Reorganized ids in sequential order in the table

        Args:
            table (str): the table
        """
        id_list=self.get_data_from_table(table,'id')
        try:
            for iii,idtup in enumerate(id_list):
                index=iii+1
                if index != idtup[0]:
                    self.edit_value_in_table(table,idtup[0],'id',index)
            self.commit()
        except Exception as eee:
            print(eee)

    def add_column_to_table(self,table:str,column:str,column_type:str):
        """Add columns to table

        Args:
            table (str): Table name
            column (str): Column name
            column_type (str):
                INTEGER: Stores whole numbers (positive or negative).
                REAL: Stores floating-point numbers with a decimal point.
                TEXT: Stores variable-length strings of text.
                BLOB: Stores binary data, such as images or documents.
                DATE: Stores dates and times in the format "YYYY-MM-DD".
                TIME: Stores time values in the format "HH:MM:SS".
                DATETIME: Stores a combination of date and time values in the format "YYYY-MM-DD HH:MM:SS".
                BOOLEAN: Stores true or false values.
        """
        # Connect to the database
        try:
            c = self.conn.cursor()
            # Add age and lastname columns to the users table
            if column_type not in ["INTEGER", "REAL", "TEXT", "BLOB", "DATE", "TIME", "DATETIME", "BOOLEAN"]:
                column_type="TEXT"
            c.execute(f"ALTER TABLE IF EXISTS {table} ADD COLUMN {column} {column_type}")
        except sqlite3.Error as eee:
            print(eee)
        finally:
            # Release all resources
            c.close()  

# Example usage
if __name__ == "__main__":
    key = None
    if os.path.exists('mydatabase_key.txt'):
        with open('mydatabase_key.txt', 'rb') as f:
            key = f.read()
    db = SQLiteDatabase('mydatabase.db',True,key)
    
    try:
        db.delete_table_from_db('files')
        db.create_table("files",[('filename','TEXT',True) , ('size', 'REAL', True)])
        # db.insert_data_to_table("files",[('insert1.test',777) , ('insert2.test',333)])
        data=[]
        for iii in range(60):
            data.append((f'fn{iii}.test',iii*3.3))
        db.insert_data_to_table("files",data)
        db.print_all_rows("files")
        print(db.get_data_from_table("files","id"," size < 10000"))
        print(db.get_data_from_table("files","*"," id = 33 OR id = 22"))
        print(db.get_data_from_table("files","*"," id = 33 OR id = 22 OR id =11"))

        db.insert_data_to_table("files",[('insert1.test','555')])
        db.delete_data_from_table("files",where="id = 51")
        print("Next available:",db.get_next_available_id('files'))
        db.add_data_to_table_id('files',db.get_next_available_id('files'),('insertaddat51.test',51))
        db.print_all_rows("files")
        print("Next available:",db.get_next_available_id('files'))
        print(db.get_number_or_rows_in_table("files"))
        print("delete")
        db.delete_data_from_table("files",where="id = 50 OR id =52 OR id = 55")
        print(db.get_number_or_rows_in_table("files"))
        db.reenumerate_id_sequence("files")
        db.print_all_rows("files")
        print(db.get_number_or_rows_in_table("files"))
        # db.rename_column_in_table('table2', 'old_column', 'new_column')
        # db.remove_column_from_table('table3', 'column4')
    finally:
        db.close_connection()