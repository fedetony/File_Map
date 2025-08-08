import pandas as pd

class DataFrameCompare:
    def __init__(self,df_a:pd.DataFrame,df_b:pd.DataFrame):
        self.df_a=df_a
        self.df_b=df_b


    @staticmethod
    def validate_input_columns(df_a: pd.DataFrame, df_b: pd.DataFrame, column_name: str):
        """Validate columns are present in dataframes"""
        required_columns = ['id', column_name]
        
        for col in required_columns:
            if col not in df_a.columns:
                raise ValueError(f"df_a is missing required column: '{col}'")
            if col not in df_b.columns:
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
            pd.DataFrame: more than 1 item in df
        """
        if source == 'A':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_a'] == 1)]
        if source == 'B':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_b'] == 1)]
        return md5_comparison.loc[(md5_comparison['num_ids_a'] == 1) & (md5_comparison['num_ids_a'] == 1)] 
    
    
    @staticmethod
    def get_df_of_deleted_created(source:str,md5_comparison: pd.DataFrame)->pd.DataFrame:
        """Returnd the df of the md5 items that have 0 items in their lists

        Args:
            source (str): 'A','B' or 'A&B'
            md5_comparison (pd.DataFrame): comparison df

        Returns:
            pd.DataFrame: with 0 items
        """
        if source == 'A':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_a'] == 0)]
        if source == 'B':
            return md5_comparison.loc[(md5_comparison['source'] == source) & (md5_comparison['num_ids_b'] == 0)]
        return md5_comparison.loc[(md5_comparison['num_ids_a'] == 0) | (md5_comparison['num_ids_a'] == 0)]

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

        return {
            'total_unique_md5': total_unique_md5,
            'count_a_and_b': len(a_and_b),
            'percent_a_and_b': len(a_and_b) / total_unique_md5 * 100,
            'count_only_a': len(only_a),
            'percent_only_a': len(only_a) / total_unique_md5 * 100,
            'count_only_b': len(only_b),
            'percent_only_b': len(only_b) / total_unique_md5 * 100,
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

    




