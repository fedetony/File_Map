"""
File Mapping from dataframes to File structure
########################
# F.garcia
# creation: 05.02.2025
########################
"""
import pandas as pd
import os

class FileStructurer():
    """Class to form a file structure from a dataframe, must contain "id", "filepath", "filename", "size" in dataframe columns. 
    """
    def __init__(self,df:pd.DataFrame,additional_columns:list=None):
        """Converts df to filestructure

        Args:
            df (pd.DataFrame): dataframe
            additional_columns (list[str], optional): additional columns to be included in tuples (filename,size,additional). Defaults to None and forms (filename,size).

        Raises:
            AssertionError: when missing "id", "filepath", "filename" or "size" in dataframe
        """
        if not self.check_df_cols_is_ok(df):
            raise AssertionError('Missing columns "id", "filepath", "filename", "size" in dataframe')
        self.df=self._fix_paths_in_df(df)
        self.additional_columns=additional_columns
    
    @staticmethod
    def check_df_cols_is_ok(df:pd.DataFrame)->bool:
        """Check "id", "filepath", "filename", "size" are in dataframe

        Returns:
            bool: True if they are, False if not
        """
        df_cols=list(df.columns)
        req_cols=["id", "filepath", "filename", "size"]
        for col in req_cols:
            if col not in df_cols:
                return False
        return True
    
    def get_max_depth(self,df:pd.DataFrame)->int:
        """Calculates maximum depth of df

        Args:
            df (pd.DataFrame): dataframe with filepath

        Returns:
            int: max depth of paths
        """
        try:
            the_max=df['path_depth'].max()
        except KeyError:
            df=self.add_depth_to_df(df)
            the_max=df['path_depth'].max()
        return int(the_max)
    
    def get_min_depth(self,df:pd.DataFrame)->int:
        """Calculates minimum depth of df

        Args:
            df (pd.DataFrame): dataframe with filepath

        Returns:
            int: min depth of paths
        """
        try:
            the_min=df['path_depth'].min()
        except KeyError:
            df=self.add_depth_to_df(df)
            the_min=df['path_depth'].min()
        return int(the_min)
    
    def create_file_tuple_df(self,df:pd.DataFrame)->pd.DataFrame:
        """Add 'file_tuple' column to dataframe with (filename,size) tuples when there is no 'file_tuple' column.

        Args:
            df (pd.DataFrame): _description_

        Raises:
            KeyError: _description_

        Returns:
            pd.DataFrame: dataframe with 'file_tuple'
        """
        df_cols=list(df.columns)
        if 'file_tuple' in df_cols:
            return df
        if isinstance(self.additional_columns,list):
            req_cols=["filename", "size"]+self.additional_columns
        else:    
            req_cols=["filename", "size"]
        for col in req_cols:
            if col not in df_cols:
                raise KeyError(f'missing {col} required column in dataframe!')
        # Create a new column with (filename, size) tuples
        def get_tuple_formed(column_list,row):
            return tuple([row[col] for col in column_list])
        df['file_tuple'] = df.apply(lambda row: get_tuple_formed(req_cols,row), axis=1)
        return df

    def compress_nth_file_structure(self,df:pd.DataFrame)->pd.DataFrame:
        """Compresses the nth last path folder in the dataframe into a filestructure.

        Args:
            df (pd.DataFrame): dataframe with minimum "id", "filepath", "filename", "size" in columns

        Returns:
            pd.DataFrame: dataframe with compressed nth path 
        """
        # Create a new column with (filename, size) tuples
        df=self.create_file_tuple_df(df)
        # Add depths
        df=self.add_depth_to_df(df)
        # Step 1: Identify max depth
        max_depth = self.get_max_depth(df)
        # Step 2–3: For rows at max depth, extract path_n and truncate filepath
        df=self.add_splitted_path_n_df(df,max_depth)
        # Group and aggregate file_tuple into a list
        df=self.group_and_aggregate_df(df)
        # Get grouped dataframe
        grouped=self.get_grouped_df(df)
        # refresh the depths
        grouped=self.add_depth_to_df(grouped)
        df = self.add_depth_to_df(df)
        return self.merge_grouped_df(df,grouped)


    @staticmethod
    def add_depth_to_df(df:pd.DataFrame)->pd.DataFrame:
        """ adds computed depth of paths

        Args:
            df (pd.DataFrame): dataframe
        Returns:
            pd.DataFrame: dataframe with 'path_depth'
        """
        def compute_depth(path):
            if not path or path.strip() == "":
                return 0
            return len(path.strip("/").split("/"))

        df['path_depth'] = df['filepath'].apply(compute_depth)
        return df
    
    @staticmethod
    def _fix_paths_in_df(df:pd.DataFrame)->pd.DataFrame:
        """Converts path strings to a standard form for making fast splitting
            All paths are separatted with single "/", and start with "/".

        Args:
            df (pd.DataFrame): df with standard filepath format
        """
        def set_standard_path(path):
            if not path or path.strip() == "":
                return ''
            path=str(path).replace('\\\\',"/").replace("//","/")
            if not str(path).startswith(('\\',"/",os.sep)):
                path="/"+path
            return path.replace('\\',"/").replace(os.sep,"/")

        df['filepath'] = df['filepath'].apply(set_standard_path)
        return df


    @staticmethod
    def add_splitted_path_n_df(df:pd.DataFrame,max_depth)->pd.DataFrame:
        """Separates the path in the the start of path and last path folder 

        Args:
            df (pd.DataFrame): dataframe
            max_depth (str): depth to separate path

        Returns:
            pd.DataFrame: with filepath parent_path, and path_n separation at depth n
        """
        # Step 2–3: For rows at max depth, extract path_n and truncate filepath
        def split_path(path, current_depth, max_depth):
            if current_depth != max_depth:
                return path, None  # Leave untouched

            parts = path.strip("/").split("/")
            path_n = parts[-1] if len(parts) > 0 else None
            parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else ""
            return parent_path, path_n

        # Apply the transformation
        df[['filepath', 'path_n']] = df.apply(
            lambda row: pd.Series(split_path(row['filepath'], row['path_depth'], max_depth)),
            axis=1
        )
        return df

    @staticmethod
    def group_and_aggregate_df(df: pd.DataFrame)->pd.DataFrame:
        """Compress the shared filepath and path_n into lists. Add to the list the different types of data, if list extend it. 

        Args:
            df (pd.DataFrame): dataframe

        Returns:
            pd.DataFrame: Compressed filepath and path_n
        """
        # from collections.abc import Iterable

        def smart_aggregate(series):
            result = []
            for item in series:
                if isinstance(item, tuple):
                    result.append(item)
                elif isinstance(item, dict):
                    #result.insert(0,item) # put dictionaries first
                    result.append(item)
                elif isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result

        compressed_df = (
            df.groupby(['filepath', 'path_n'], dropna=False)
            .agg({'file_tuple': smart_aggregate})
            .reset_index()
        )
        return compressed_df


    @staticmethod
    def get_grouped_df(df:pd.DataFrame)->pd.DataFrame:
        """Forms dictionary with filepath and path_n compressed. sets the dictionary in file_tuple column 

        Args:
            df (pd.DataFrame): dataframe

        Returns:
            pd.DataFrame: Compressed df with file_tuple dictionary
        """
        # Filter out non-NaN 'path_n' rows
        filtered = df[df['path_n'].notna()]
        # Drop 'path_n' and 'file_tuple' duplicates for safety
        filtered = filtered[['filepath', 'path_n', 'file_tuple']].copy()
        # Build nested dictionary by explicitly excluding grouping columns
        grouped = (
            filtered.groupby('filepath')
                    .apply(lambda g: pd.Series({'file_tuple': dict(zip(g['path_n'], g['file_tuple']))}))#,include_groups=False)
                    .reset_index()
        )
        def convert_list(f_t):
            if isinstance(f_t,dict):
                f_list=[]
                for key,value in f_t.items():
                    f_list.append({key:value})
                return f_list
            else:
                return f_t

        grouped['file_tuple']=grouped['file_tuple'].apply(lambda row: convert_list(row))
        
        return grouped
        

    @staticmethod
    def merge_grouped_df(df:pd.DataFrame,grouped:pd.DataFrame)->pd.DataFrame:
        """Merge the df and grouped dataframes keeping order

        Args:
            df (pd.DataFrame): dataframe
            grouped (pd.DataFrame): dataframe

        Returns:
            pd.DataFrame: merged df
        """
        # Keep only rows where path_n is NaN
        direct_files_df = df[df['path_n'].isna()].copy()
        direct_files_df.drop(columns='path_n', inplace=True)
        # Merge with grouped dict-style folders
        final_df = pd.concat([grouped, direct_files_df], ignore_index=True) #sets dictionaries first
        #return final_df

        # Reorder columns if needed
        preferred_order = ['filepath'] #['filepath', 'file_tuple']
        remaining_cols = [col for col in final_df.columns if col not in preferred_order]
        return final_df[preferred_order + remaining_cols]
    
    def fully_compress(self)->pd.DataFrame:
        """Compress the dataframe Iteratevily until max compression depth.

        Returns:
            pd.DataFrame: max compressed dataframe
        """
        df = self.add_depth_to_df(self.df)
        max_depth=self.get_max_depth(df)
        min_depth=self.get_min_depth(df)
        iii=1
        while max_depth > min_depth:
            print(f'{iii} Compressing {max_depth} to {min_depth}, {df["path_depth"].size} elements left')
            df = self.compress_nth_file_structure(df)
            max_depth=self.get_max_depth(df)            
            iii+=1
        # Last Compression
        print(f'{iii} Compressing {max_depth} to {min_depth}, {df["path_depth"].size} elements left')
        df = self.compress_nth_file_structure(df)
        return df
    
    def get_file_structure(self)->list:
        """Returns the file structure of the compressed dataframe

        Returns:
            list: File structure list
        """
        df=self.fully_compress()
        if df['file_tuple'].size==0:
            return []
        if df['file_tuple'].size==1:
            if df['filepath'][0]=='':
                return df['file_tuple'][0]
            return [{df['filepath'][0]:df['file_tuple'][0]}]
        #add the path_n
        df=self.add_splitted_path_n_df(df,1)
        #form a 1 item list of dictionaries with all levels
        df=self.get_grouped_df(df)
        return  df['file_tuple'][0] 
    
    def get_file_structure_dict(self,name:str)->dict:
        """Returns the file structure of the compressed dataframe
        under a dictionary {name:[file structure list]}

        Returns:
            dict: {name:[file structure list]}
        """
        fs_list=self.get_file_structure()
        return {name:fs_list}



    
