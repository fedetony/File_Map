import pandas as pd
from collections import defaultdict
from difflib import SequenceMatcher


class DataFrameCompare:
    def __init__(self,df_a:pd.DataFrame,df_b:pd.DataFrame,column_name: str='md5'):
        self.df_a_all=df_a
        self.df_b_all=df_b
        self.column_name=column_name
        fields=['id',column_name]
        try:
            self.validate_input_columns(df_a,df_b,column_name)
            self.df_a=self.get_df_with_fields(df_a,fields)
            self.df_b=self.get_df_with_fields(df_b,fields)
        except ValueError as eee:
            print(f"Not selecting fields from dataframes: {eee}")
            self.df_a=df_a
            self.df_b=df_b      


    @staticmethod
    def validate_input_columns(df_a: pd.DataFrame, df_b: pd.DataFrame, column_name: str):
        """Validate columns are present in dataframes"""
        required_columns = ['id', column_name]
        
        for col in required_columns:
            if col not in list(df_a.columns):
                raise ValueError(f"df_a is missing required column: '{col}'")
            if col not in list(df_b.columns):
                raise ValueError(f"df_b is missing required column: '{col}'")


    @staticmethod
    def sort_by(df:pd.DataFrame,column_name)->pd.DataFrame:
        """Sort the dataframe by the column_name 

        Args:
            df (pd.DataFrame): dataframe to sort
            column_name (_type_): column to sort

        Returns:
            pd.DataFrame: sorted dataframe
        """
        # Sort df_a by 'md5'
        return df.sort_values(by=column_name).reset_index(drop=True)

    def compare_a_b(self,column_name='md5')->pd.DataFrame:
        """Makes full comparison of df_a and b. Must contain an 'id' and column_name columns.

        Args:
            column_name (str, optional): dataframe column to compare. Defaults to 'md5'.

        Returns:
            pd.DataFrame: Datafame with unique column_name "ids_on_a","ids_on_b":list of ids,Source: "A","B" or "A&B", 
                            'num_ids_a','num_ids_b': Number of ids in each
        """
        # Sort df_a by 'md5'
        self.validate_input_columns(self.df_a,self.df_b,column_name)
        df_a_sorted = self.sort_by(self.df_a,column_name)
        df_b_sorted = self.sort_by(self.df_b,column_name)
        id_a="ids_on_a"
        id_b="ids_on_b"
        md5_summary_a=self.make_summary_ids(df_a_sorted,id_a,column_name)
        md5_summary_b=self.make_summary_ids(df_b_sorted,id_b,column_name)
        md5_comparison=self.compare_a_b_column_df(md5_summary_a,id_a,md5_summary_b,id_b,'num_ids_a','num_ids_b',column_name)
        return md5_comparison

    @staticmethod
    def get_df_of_a_source(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Gets the df of filtered 'A','B' or 'A&B'.

        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame: filtered df
        """
        return md5_comparison.loc[md5_comparison['source'] == source]
    
    @staticmethod
    def get_df_of_repeated(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Returnd the df of the md5 items that have more than 1 item in their lists

        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame: more than 1 item in df
        """
        if source == 'A':
            return md5_comparison.loc[((md5_comparison['source']=='A&B') | (md5_comparison['source']=='A')) & (md5_comparison['num_ids_a'] > 1)] 
        if source == 'B':
            return md5_comparison.loc[((md5_comparison['source']=='A&B') | (md5_comparison['source']=='B')) & (md5_comparison['num_ids_b'] > 1)] 
        
        return md5_comparison.loc[(md5_comparison['num_ids_a'] > 1) | (md5_comparison['num_ids_b'] > 1)]

    @staticmethod
    def get_df_of_unique(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Returnd the df of the md5 items that have only 1 item in their lists

        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame:  1 item in df
        """
        if source == 'A':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_a'] == 1)]
        if source == 'B':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_b'] == 1)]
        return md5_comparison.loc[(md5_comparison['num_ids_a'] == 1) & (md5_comparison['num_ids_b'] == 1)] 
    
    @staticmethod
    def get_df_of_converge_diverge(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Returnd the df of the md5 items that have:
           A: A more than B at least 1 B item (Converge)
           B: B more than A at least 1 A item (Diverge)
           A&B: Converge or Diverge

        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame: more than 1 item in df
        """
        if source == 'A':
            return md5_comparison.loc[(md5_comparison['num_ids_a'] > md5_comparison['num_ids_b']) & (md5_comparison['num_ids_a'] >= 1) & (md5_comparison['num_ids_b'] >= 1)]
        if source == 'B':
            return md5_comparison.loc[(md5_comparison['num_ids_a'] < md5_comparison['num_ids_b']) & (md5_comparison['num_ids_a'] >= 1) & (md5_comparison['num_ids_b'] >= 1)]
        return md5_comparison.loc[((md5_comparison['num_ids_a'] > md5_comparison['num_ids_b']) | (md5_comparison['num_ids_a'] < md5_comparison['num_ids_b'])) & 
                                  (md5_comparison['num_ids_a'] >= 1) & (md5_comparison['num_ids_b'] >= 1)]
    
    @staticmethod
    def get_df_of_equilibrium(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Returnd the df of the md5 items that have:
           more than 1 item and have same A anb b amount of items 
            (use unique source=a'A&B' for 1 to 1 item)
        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame: more than 1 item in df
        """
        if source in ['A','B','A&B']:
            return md5_comparison.loc[(md5_comparison['num_ids_a'] > 1) & (md5_comparison['num_ids_a'] == md5_comparison['num_ids_b'])]
        
        return md5_comparison.loc[(md5_comparison['source'] == source)]
    
    
    @staticmethod
    def get_df_of_deleted_created(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Return the df of the md5 items that have items on source ie. 0 items in the other source. 

        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame: with 0 items
        """
        if source == 'A':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_b'] == 0)]
        if source == 'B':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_a'] == 0)]
        return md5_comparison.loc[(md5_comparison['num_ids_a'] == 0) | (md5_comparison['num_ids_b'] == 0)]

    def generate_comparison_stats(self,md5_comparison: pd.DataFrame) -> dict:
        """Make statistics of the comparison

        Args:
            md5_comparison (pd.DataFrame): dataframe with comparison results

        Returns:
            dict: some statistics
        """
        total_unique_md5 = len(md5_comparison)
        a_and_b = self.get_df_of_a_source('A&B',md5_comparison)
        only_a = self.get_df_of_a_source('A',md5_comparison)
        only_b = self.get_df_of_a_source('B',md5_comparison)
        one_to_one =self.get_df_of_unique('A&B',md5_comparison)
        many_to_many=self.get_df_of_equilibrium('A&B',md5_comparison)
        converged = self.get_df_of_converge_diverge('A',md5_comparison)
        diverged = self.get_df_of_converge_diverge('B',md5_comparison)
        repeated_a = self.get_df_of_repeated('A',md5_comparison)
        repeated_b = self.get_df_of_repeated('B',md5_comparison)

        return {
            'Total Unique': total_unique_md5,
            '# In A&B': len(a_and_b),
            'In A&B %': round(len(a_and_b) / total_unique_md5 * 100,2),
            '# Only in A': len(only_a),
            'Only in A %': round(len(only_a) / total_unique_md5 * 100,2),
            '# Only in B': len(only_b),
            'Only in B %': round(len(only_b) / total_unique_md5 * 100,2),
            '# One to One A=B': len(one_to_one),
            '# Many to Many An=Bn': len(many_to_many),
            'Mapped %': round((len(one_to_one)+len(many_to_many)) / total_unique_md5 * 100,2),
            '# Converging An>Bn': len(converged),
            '# Diverging An<Bn': len(diverged),
            '# Repeated A': len(repeated_a),
            '# Repeated B': len(repeated_b),
        }
    
    @staticmethod
    def merge_id_columns(df_sorted:pd.DataFrame,merged_name='ids_list',ids_a_name:str='ids_on_a',ids_b_name:str='ids_on_b'):
        """Merge id_on_a with ids_on_b into a single list"""
        def mergecols(col1,col2):
            if isinstance(col1,list) and isinstance(col2,list):
                return col1+col2
            elif isinstance(col1,list) and not isinstance(col2,list):
                return col1
            elif not isinstance(col1,list) and isinstance(col2,list):
                return col2    
            return None

        df_sorted[merged_name]=df_sorted.apply(mergecols(df_sorted[ids_a_name],df_sorted[ids_b_name]),axis=1)
        return  df_sorted

    @staticmethod
    def make_summary_ids(df_sorted:pd.DataFrame,ids_column_name:str='ids_list',column_name='md5'):
        """Group df_sorted by 'md5' and collect the 'id's into a list.

        Args:
            df_sorted (pd.DataFrame): sorted by md5 df
            ids_column_name (str,optional): column name . Default 'ids_list'

        Returns:
            pd.DataFrame: unique md5 sorted with 'ids_list'
        """
        # Group df_a_sorted by 'md5' and collect the 'id's into a list
        md5_summary = df_sorted.groupby(column_name)['id'].apply(list).reset_index()
        # Rename the 'id' column to 'ids_on_A'
        md5_summary.rename(columns={'id': ids_column_name}, inplace=True)
        return md5_summary
    
    @staticmethod
    def compare_a_b_column_df(md5_summary_a:pd.DataFrame,id_list_a_name:str,md5_summary_b:pd.DataFrame,id_list_b_name:str,count_a_name:str='num_ids_a',count_b_name:str='num_ids_b',column_name='md5')->pd.DataFrame:
        """Compare 2 dataframes

        Args:
            md5_summary_a (pd.DataFrame): Sorted unique dataframe a
            id_list_a_name (str): Name for id list column of a
            md5_summary_b (pd.DataFrame): Sorted unique dataframe b
            id_list_b_name (str): Name for id list column of b
            count_a_name (str, optional): Column name to set count of a. Defaults to 'num_ids_a'.
            count_b_name (str, optional): Column name to set count of b. Defaults to 'num_ids_b'.
            column_name (str, optional): Column name being compared. Defaults to 'md5'.

        Returns:
            pd.DataFrame: Comparison dataframe with unique column_name id_list_a_name,id_list_b_name:list of ids, source: "A","B" or "A&B", 
                            count_a_name,count_b_name: Number of ids in each
        """
        # Merge both summaries on 'md5'
        md5_comparison = pd.merge(
            md5_summary_a,
            md5_summary_b,
            on=column_name,
            how='outer'  # ensures we include md5s unique to either A or B
        )

        # Define the status for each md5 row
        def label_md5_source(row):
            a_val=row[id_list_a_name]
            b_val=row[id_list_b_name]
            if isinstance(a_val,list) and isinstance(b_val,list): 
            #if pd.notna(row[id_list_a_name]) and pd.notna(row[id_list_b_name]):
                return 'A&B'
            elif isinstance(a_val,list) and not isinstance(b_val,list):
            #elif pd.notna(row[id_list_a_name]):
                return 'A'
            elif not isinstance(a_val,list) and isinstance(b_val,list):
            #elif pd.notna(row[id_list_b_name]):
                return 'B'
            else:
                return 'Unknown'

        # Apply the labeling function
        md5_comparison['source'] = md5_comparison.apply(label_md5_source, axis=1)
        # Count number of IDs in each list
        md5_comparison[count_a_name] = md5_comparison[id_list_a_name].apply(lambda x: len(x) if isinstance(x, list) else 0)
        md5_comparison[count_b_name] = md5_comparison[id_list_b_name].apply(lambda x: len(x) if isinstance(x, list) else 0)
        return md5_comparison
    
    
    def get_df_ab_all_from_df_comp(self,df_comp:pd.DataFrame,column_name='md5',ids_a_name:str='ids_on_a',ids_b_name:str='ids_on_b')->tuple:
        """Get matching df fro a and b with all columns of the comparison df

        Args:
            df_comp (pd.DataFrame): Comparison df
            column_name (str, optional): columnname. Defaults to 'md5'.
            ids_a_name (str, optional): id list a column name. Defaults to 'ids_on_a'.
            ids_b_name (str, optional): id list b column name. Defaults to 'ids_on_b'.

        Returns:
            tuple(pd.DataFrame,pd.DataFrame): selected_df_a,selected_df_b
        """
        selected_df_a = self.get_df_x_all_from_df_comp(df_comp,'a',column_name,ids_a_name)
        selected_df_b = self.get_df_x_all_from_df_comp(df_comp,'b',column_name,ids_b_name)
        return selected_df_a,selected_df_b
    
    def get_df_x_all_from_df_comp(self,df_comp:pd.DataFrame,x:str='a',column_name='md5',ids_x_name:str='ids_on_a')->pd.DataFrame:
        """Get matching df with all columns of the comparison df

        Args:
            df_comp (pd.DataFrame): Comparison df
            x (str,optional): a or b
            column_name (str, optional): columnname. Defaults to 'md5'.
            ids_a_name (str, optional): id list a column name. Defaults to 'ids_on_a'.
            ids_b_name (str, optional): id list b column name. Defaults to 'ids_on_b'.

        Returns:
            pd.DataFrame: selected df
        """
        id_list=[]
        for id_l in df_comp[ids_x_name].tolist():
            if isinstance(id_l,list):
                id_list.extend(id_l)
            else:
                id_list.append(id_l)
        if x=='a':
            selected_df_x = self.df_a_all.loc[(self.df_a_all['id'].isin(id_list))]
        elif x=='b':
            selected_df_x = self.df_b_all.loc[(self.df_b_all['id'].isin(id_list))]   
        else:
            selected_df_x=pd.DataFrame()
        # selected_df_x = self.df_a_all.loc[(self.df_a_all['id'].isin(df_comp[ids_x_name])) & (self.df_a_all[column_name] == df_comp[column_name])]
        return selected_df_x


    @staticmethod
    def selected_df_from_comparison_df(df_all:pd.DataFrame,df_comp:pd.DataFrame,source='A&B',from_ids='ids_on_b',column_name='md5')->pd.DataFrame:
        """Gets a df with the original df_all fields/columns matching with the comparison of the selected column_name (normally md5),source and id list column

        Args:
            df_all (pd.DataFrame): dataframe with all columns 'id','filename','filepath','md5' ...
            df_comp (pd.DataFrame): A B Comparison dataframe
            source (str, optional): source A,B or A&B. Defaults to 'A&B'.
            from_ids (str, optional): id list column 'ids_on_a' or 'ids_on_b'. Defaults to 'ids_on_b'.

        Returns:
            pd.DataFrame: _description_
        """
        selected_df_a = df_all.loc[(df_all['id'].isin(df_comp[df_comp['source'] == source][from_ids])) & (df_a[column_name] == df_comp[df_comp['source'] == source][column_name])]
        return selected_df_a
    
    @staticmethod
    def get_df_with_fields(df_any:pd.DataFrame,fields:list=None)->pd.DataFrame:
        """Gets a df with the desired fields/columns 

        Args:
            df_any (pd.DataFrame): dataframe with all columns 'id','filename','filepath','md5' ...
            fields (list, optional): desired fields list . Defaults to None -> ['md5', 'id'].

        Returns:
            pd.DataFrame: df with only the fields
        """
        if not fields:
            fields=['md5', 'id']
        for field in fields:
            if field not in df_any.columns:
                return df_any
        if isinstance(fields,list):    
            selected_df = df_any.dropna().loc[:, fields]
            return selected_df
        return df_any

    def _check_for_fields(self):
        """Checks the dfs contain all columns relevant for detail comparison

        Returns:
            bool: True if ok, false something missing
        """
        required_cols=[self.column_name,'id','filename','filepath','size','dt_file_modified']
        missinga=[]
        missingb=[]
        for col in required_cols:
            if col not in self.df_a_all.columns:
                missinga.append(col)
            if col not in self.df_b_all.columns:
                missingb.append(col)
        if len(missinga)==0 and len(missingb)==0:
            return True
        else:
            print(f"Missing columns in df A: {missinga}")
            print(f"Missing columns in df B: {missingb}")
            return False
        
    def detail_comparison(self,md5_comparison: pd.DataFrame)->dict:
        """Give Detail information on file mapping over a comparison

        Args:
            md5_comparison (pd.DataFrame): _description_

        Returns:
            dict(pd.DataFrame): dictionary with a single Dataframe per category under the following categories 
            'unmodified', 'data changed', 'file renamed', 'file moved', 'added file', 'removed file', 'file moved and renamed'
        """
        detailed_comp_dict={'unmodified':None, 'data changed':None, 'file renamed':None, 'file moved':None, 'added file':None,'removed file':None,'file moved and renamed':None}
        if not self._check_for_fields():
            return detailed_comp_dict
        md5=self.column_name
        comp_only_a = self.get_df_of_a_source('A',md5_comparison)
        comp_only_b = self.get_df_of_a_source('B',md5_comparison)
        # These are single files with unique md5 (includes at least 'id','filename','filepath','size','dt_file_modified','md5')
        df_all_only_a=self.get_df_x_all_from_df_comp(comp_only_a,'a',md5,'ids_on_a')
        df_all_only_b=self.get_df_x_all_from_df_comp(comp_only_b,'b',md5,'ids_on_b')
        # if they have the same filename  -> 'data changed'
        data_changed_a=df_all_only_a.loc[(df_all_only_a['filename'].isin(df_all_only_b['filename']))] 
        data_changed_b=df_all_only_b.loc[(df_all_only_b['filename'].isin(df_all_only_a['filename']))] 
        added_file=df_all_only_b.loc[~df_all_only_b['filename'].isin(df_all_only_a['filename'])]
        added_file = added_file.add_suffix('_b')
        removed_file=df_all_only_a.loc[~df_all_only_a['filename'].isin(df_all_only_b['filename'])] 
        removed_file = removed_file.add_suffix('_a')
        data_changed_a['__filename_m']=data_changed_a['filename']
        data_changed_b['__filename_m']=data_changed_b['filename']
        merged_data_changed = pd.merge(data_changed_a,data_changed_b,on='__filename_m',suffixes=('_a', '_b'))
        merged_data_changed.drop('__filename_m', axis=1, inplace=True)
        d_c_d7={}
        d_c_d7.update({'data changed':merged_data_changed})
        d_c_d7.update({'added file':added_file})
        d_c_d7.update({'removed file':removed_file})

        # These are files in a and b with same unique md5 only once
        comp_one_to_one =self.get_df_of_unique('A&B',md5_comparison)
        df_all_one_to_one_a=self.get_df_x_all_from_df_comp(comp_one_to_one,'a',md5,'ids_on_a')
        df_all_one_to_one_b=self.get_df_x_all_from_df_comp(comp_one_to_one,'b',md5,'ids_on_b')
        comparator = MD5FileComparator(df_all_one_to_one_a, df_all_one_to_one_b, md5,'filename', 'filepath', 'dt_file_modified')
        comparator.compare() #in self.compare
        summary_df = comparator.get_summary_df()
        d_c_d0=self._merge_summary(df_all_one_to_one_a, df_all_one_to_one_b,summary_df)
        
        # These are files in a and b with many of same unique md5 in same amounts in a and b
        comp_many_to_many=self.get_df_of_equilibrium('A&B',md5_comparison)
        df_all_m_to_m_a=self.get_df_x_all_from_df_comp(comp_many_to_many,'a',md5,'ids_on_a')
        df_all_m_to_m_b=self.get_df_x_all_from_df_comp(comp_many_to_many,'b',md5,'ids_on_b')        
        comparator = MD5FileComparator(df_all_m_to_m_a, df_all_m_to_m_b, md5,'filename', 'filepath', 'dt_file_modified')
        comparator.compare() #in self.compare
        summary_df = comparator.get_summary_df()
        d_c_d1=self._merge_summary(df_all_m_to_m_a, df_all_m_to_m_b,summary_df)

        # These are files in a and b with many of same unique md5 in amounts in a > b
        comp_converged = self.get_df_of_converge_diverge('A',md5_comparison)
        df_all_conv_a=self.get_df_x_all_from_df_comp(comp_converged,'a',md5,'ids_on_a')
        df_all_conv_b=self.get_df_x_all_from_df_comp(comp_converged,'b',md5,'ids_on_b')        
        comparator = MD5FileComparator(df_all_conv_a, df_all_conv_b, md5,'filename', 'filepath', 'dt_file_modified')
        comparator.compare()
        summary_df = comparator.get_summary_df()
        d_c_d2=self._merge_summary(df_all_conv_a, df_all_conv_b,summary_df)

        # These are files in a and b with many of same unique md5 in amounts in a < b
        comp_diverged = self.get_df_of_converge_diverge('B',md5_comparison)
        df_all_div_a=self.get_df_x_all_from_df_comp(comp_diverged,'a',md5,'ids_on_a')
        df_all_div_b=self.get_df_x_all_from_df_comp(comp_diverged,'b',md5,'ids_on_b')        
        comparator = MD5FileComparator(df_all_div_a, df_all_div_b, md5,'filename', 'filepath', 'dt_file_modified')
        comparator.compare()
        summary_df = comparator.get_summary_df()
        d_c_d3=self._merge_summary(df_all_div_a, df_all_div_b,summary_df)

        # List of partial dictionaries to merge
        partial_dicts = [d_c_d0, d_c_d1, d_c_d2, d_c_d3, d_c_d7]

        # Merge each category across all partial dictionaries
        # Categories: 'unmodified', 'data changed', 'file renamed', 'file moved', 'added file', 'removed file', 'file moved and renamed'
        for category in detailed_comp_dict.keys():
            dfs_to_concat = [d[category] for d in partial_dicts if d[category] is not None and not d[category].empty]
            
            if dfs_to_concat:
                detailed_comp_dict[category] = pd.concat(dfs_to_concat, ignore_index=True)
            else:
                for d in partial_dicts:
                    if d[category] is not None:
                        detailed_comp_dict[category] = pd.DataFrame(columns=d[category].columns)
                        break
                else:
                    detailed_comp_dict[category] = pd.DataFrame()  # Fallback if all are None

        return detailed_comp_dict
    
    def _merge_summary(self,df_a:pd.DataFrame,df_b:pd.DataFrame,summary_df:pd.DataFrame):
        """Generates a detailed comparison dictionary with the information.

        Args:
            df_a (pd.DataFrame): dataframe with all columns a
            df_b (pd.DataFrame): dataframe with all columns b
            summary_df (pd.DataFrame): summary_comparison
            md5 (str, optional): column being compared. Defaults to 'md5'.

        Returns:
            _type_: Generated detailed_comp_dict={'unmodified':None, 
                                            'data changed':None, 
                                            'file renamed':None, 
                                            'file moved':None, 
                                            'added file':None,
                                            'removed file':None,
                                            'file moved and renamed':None}
           
        """
        detailed_comp_dict={'unmodified':None, 'data changed':None, 'file renamed':None, 'file moved':None, 'added file':None,'removed file':None,'file moved and renamed':None}
        for category in detailed_comp_dict.keys():
            df_cat = summary_df[summary_df['change_type'] == category].copy()

            if not df_cat.empty:
                if category in ['added file','removed file']:
                    if category == 'added file':
                        sel_df_b = df_b.set_index('id').loc[df_cat['id_b']].reset_index()
                        merged_df = sel_df_b.add_suffix('_b')
                    if category == 'removed file':
                        sel_df_a = df_a.set_index('id').loc[df_cat['id_a']].reset_index()
                        merged_df = sel_df_a.add_suffix('_a')
                else:
                    # Keep only relevant columns and ensure consistent suffixes
                    sel_df_a = df_a.set_index('id').loc[df_cat['id_a']].reset_index()
                    sel_df_b = df_b.set_index('id').loc[df_cat['id_b']].reset_index()
                    # Add suffixes manually
                    sel_df_a = sel_df_a.add_suffix('_a')
                    sel_df_b = sel_df_b.add_suffix('_b')
                    # Concatenate side-by-side
                    merged_df = pd.concat([sel_df_a.reset_index(drop=True), sel_df_b.reset_index(drop=True)], axis=1)
                detailed_comp_dict[category] = merged_df                
            else:
                detailed_comp_dict[category] = pd.DataFrame()  # Empty DataFrame for consistency
        return detailed_comp_dict


class MD5FileComparator:
    def __init__(self, df_a:pd.DataFrame, df_b:pd.DataFrame, md5_col:str='md5', filename_col:str='filename', filepath_col:str='filepath',dt_file_modified_col:str='dt_file_modified'):
        self.df_a = df_a.copy()
        self.df_b = df_b.copy()
        self.md5_col = md5_col
        self.filename_col = filename_col
        self.filepath_col = filepath_col
        self.dt_file_modified_col = dt_file_modified_col
        self.categories = defaultdict(list)

    def similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def compare(self):
        shared_md5s = set(self.df_a[self.md5_col]) & set(self.df_b[self.md5_col])

        for md5_val in shared_md5s:
            group_a = self.df_a[self.df_a[self.md5_col] == md5_val].copy()
            group_b = self.df_b[self.df_b[self.md5_col] == md5_val].copy()

            matched_b_indices = set()

            for idx_a, row_a in group_a.iterrows():
                best_match = None
                best_score = 0
                best_idx_b = None

                for idx_b, row_b in group_b.iterrows():
                    if idx_b in matched_b_indices:
                        continue

                    score = 0
                    if row_a[self.filename_col] == row_b[self.filename_col]:
                        score += 1
                    else:
                        score += self.similarity(row_a[self.filename_col], row_b[self.filename_col])

                    if row_a[self.filepath_col] == row_b[self.filepath_col]:
                        score += 1
                    else:
                        score += self.similarity(row_a[self.filepath_col], row_b[self.filepath_col])

                    if score > best_score:
                        best_score = score
                        best_match = row_b
                        best_idx_b = idx_b

                if best_match is not None:
                    matched_b_indices.add(best_idx_b)

                    fname_a = row_a[self.filename_col]
                    fname_b = best_match[self.filename_col]
                    fpath_a = row_a[self.filepath_col]
                    fpath_b = best_match[self.filepath_col]
                    dt_a = row_a[self.dt_file_modified_col]
                    dt_b = best_match[self.dt_file_modified_col]

                    if fname_a == fname_b and fpath_a == fpath_b:
                        self.categories['unmodified'].append((row_a, best_match))
                    elif fname_a == fname_b and dt_a == dt_b:
                        self.categories['file moved'].append((row_a, best_match))
                    elif fpath_a == fpath_b and dt_a == dt_b:
                        self.categories['file renamed'].append((row_a, best_match))
                    elif dt_a == dt_b:
                        self.categories['file moved and renamed'].append((row_a, best_match))
                    else:
                        self.categories['removed file'].append(row_a)
                        self.categories['added file'].append(best_match)
                else:
                    self.categories['removed file'].append(row_a)

            unmatched_b = group_b.loc[~group_b.index.isin(matched_b_indices)]
            for _, row_b in unmatched_b.iterrows():
                self.categories['added file'].append(row_b)

        return self.categories

    def get_summary_df(self):
        summary = []
        for category, items in self.categories.items():
            for item in items:
                if isinstance(item, tuple):
                    row_a, row_b = item
                    summary.append({
                        'md5': row_a[self.md5_col],
                        'id_a': row_a.get('id', None),
                        'filename_a': row_a.get(self.filename_col, None),
                        'filepath_a': row_a.get(self.filepath_col, None),
                        'id_b': row_b.get('id', None),
                        'filename_b': row_b.get(self.filename_col, None),
                        'filepath_b': row_b.get(self.filepath_col, None),
                        'change_type': category
                    })
                else:
                    # Unmatched file (added or removed)
                    if category == 'added file':
                        summary.append({
                            'md5': item[self.md5_col],
                            'id_a': None,
                            'filename_a': None,
                            'filepath_a': None,
                            'id_b': item.get('id', None),
                            'filename_b': item.get(self.filename_col, None),
                            'filepath_b': item.get(self.filepath_col, None),
                            'change_type': category
                        })
                    else:  # removed file
                        summary.append({
                            'md5': item[self.md5_col],
                            'id_a': item.get('id', None),
                            'filename_a': item.get(self.filename_col, None),
                            'filepath_a': item.get(self.filepath_col, None),
                            'id_b': None,
                            'filename_b': None,
                            'filepath_b': None,
                            'change_type': category
                        })
        return pd.DataFrame(summary)

if __name__=="__main__":
    import hashlib
    import random
    import string
    from rich import print

    def generate_md5(input_str):
        return hashlib.md5(input_str.encode()).hexdigest()

    def random_string(length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    # Create sample df_a
    df_a = pd.DataFrame({
        'id': range(1, 21),
        'md5': [generate_md5(random_string()) for _ in range(20)]
    })

    # Create sample df_b with some overlapping and differing md5s
    df_b = pd.DataFrame({
        'id': range(1, 21),
        'md5': [
            df_a.loc[i, 'md5'] if i % 3 == 0 else generate_md5(random_string())
            for i in range(20)
        ]
    })

    MD5C=DataFrameCompare(df_a,df_b)
    df_compare=MD5C.compare_a_b('md5')
    print(df_compare)
    print(MD5C.generate_comparison_stats(df_compare))

    



