import pandas as pd

class DataManage():
    def __init__(self,data:list,fields:list):
        self.data=data
        self.fields=fields
        self.df = None
        self._arrange_data_fields()
            
    def _arrange_data_fields(self):
        """Arrange data in Dataframe"""
        if len(self.data)==0:
            raise ValueError("No data provided!")
        if isinstance(self.data,list):
            if isinstance(self.data[0],dict):
                fields=list(self.data[0].keys())
                for ddd in self.data:
                    if list(ddd.keys())!=fields:
                        raise ValueError(f"Data fields must have same number of keys({list(ddd.keys())}) != ({fields})")
                if not self.fields:
                    self.fields=[]
                if len(self.fields)!=len(fields):
                    self.fields =fields
                    self.df = pd.DataFrame(self.data)
                else:
                    self.df = pd.DataFrame(self.data)
                    new_fields={}
                    try:
                        for old_field,new_field in zip(fields,self.fields):
                            new_fields.update({old_field:new_field})
                        self.df.rename(columns=new_fields, inplace=True)
                    except:
                        self.fields =fields
            if isinstance(self.data[0],tuple):
                if not self.fields:
                    raise ValueError(f"No fields provided!")
                if len(self.fields)!=len(self.data[0]):
                    raise ValueError(f"Number of Fields({len(self.fields)}) do not match with data size({len(self.data[0])})")
                self.df = pd.DataFrame(self.data, columns=self.fields)
    
    @staticmethod
    def get_df_sorted(df:pd.DataFrame,sort_by,fields_to_tab,ascending=True):
        """Sorts the dataframe

        Args:
            df (pd.DataFrame): dataframe to sort
            sort_by (any): if int: sorts fields_to_tab[sort_by]
                           if str: sorts sort_by
                           if list: adds sort field in list order.
            fields_to_tab (_type_): when sort_by is int or list(int) to get column name
            ascending (bool, optional): Sort direction. Defaults to True.

        Returns:
            pd.DataFrame: a sorted dataframe
        """
        selected_fields=df.columns.tolist()
        if isinstance(sort_by,int):
            if sort_by>=0 and sort_by<len(fields_to_tab):
                if fields_to_tab[sort_by] in selected_fields:
                    return df.sort_values(by=fields_to_tab[sort_by],ascending=ascending) 
        if isinstance(sort_by,str):
            if sort_by in selected_fields:
                return df.sort_values(by=sort_by,ascending=ascending)        
        if isinstance(sort_by,list):
            if len(sort_by)==0:
                return df
            sort_by_list=[]
            for iii,sss in enumerate(sort_by):
                if isinstance(sort_by[iii],int):
                    if sss>=0 and sss<len(fields_to_tab):
                        if fields_to_tab[sss] in selected_fields:
                            sort_by_list.append(fields_to_tab[sss])           
                if isinstance(sort_by[iii],str):
                    if sss in selected_fields:
                        sort_by_list.append(sss)
            return df.sort_values(by=sort_by_list,ascending=ascending)
        return df                
                
    def get_selected_df(self,fields_to_tab=None,sort_by=None,ascending=True):
        """Returns the dataframe with selected fields and sorting

        Args:
            fields_to_tab (list(str), optional): selected columns to use in df, None uses all. Defaults to None.
            sort_by (int, str or list, optional): Sorting if the df is to be sorted. Defaults to None.
            ascending (bool, optional): if sorting, then ascendant. Defaults to True.

        Returns:
            Dataframe: dataframe with the selected data and sorting.
        """
        if not fields_to_tab:
            fields_to_tab=self.fields
        if isinstance(fields_to_tab,list):
            selected_fields=[]
            for field in fields_to_tab:
                if field in self.fields:
                    selected_fields.append(field)
            if len(selected_fields)>0:
                # Select only the specified columns
                df_selected = self.df[selected_fields]
                if sort_by:
                    sorted_df=self.get_df_sorted(df_selected,sort_by,fields_to_tab,ascending)
                    return sorted_df
                return df_selected
        return pd.DataFrame()

    def get_tabulated_fields(self,fields_to_tab=None,sort_by=None,ascending=True,*args,**kwargs):#indexed=False,header=True):
        """Returns Tabulated string

        Args:
            fields_to_tab (list(str), optional): selected columns to use in df, None uses all. Defaults to None.
            sort_by (int, str or list, optional): Sorting if the df is to be sorted. Defaults to None.
            ascending (bool, optional): if sorting, then ascendant. Defaults to True.
            indexed (bool, optional): table indexed
            header=True
        Returns:
            str: Tabulated data
        """
        df_selected=self.get_selected_df(fields_to_tab,sort_by,ascending)
        if not df_selected.empty:    
            #return df_selected.to_string(index=indexed,header=header)
            return df_selected.to_string(*args,**kwargs)
        return ''

if __name__ == '__main__':
    data1 = [(1, "Pedro", 12, "M"),
         (2, "Karla", 13, "F"),
         (3, "Lucia", 17, "F"),
         (4, "Collin", 21, "M")]
    fields = ["id", "name", "age", "gender"]
    # Print the table using pandas
    dt1=DataManage(data1,fields)
    print("+"*33)
    print(dt1.get_tabulated_fields(["name","age","gender"],["gender","name"]))
    print("+"*33)
    data2 = [
    {"id": "1", "name": "Pedro", "age": 12, "gender": "M"},
    {"id": "2", "name": "Karl", "age": 13, "gender": "F"},
    {"id": "3", "name": "Lucia", "age": 17, "gender": "F"},
    {"id": "4", "name": "Collin", "age": 21, "gender": "M"}
    ]
    fields = ["Id", "Name", "Age", "Gender"]
    dt2=DataManage(data2,fields)   
    print("-"*33)     
    print(dt2.get_tabulated_fields(index=True,justify='left'))
    print("-"*33)

    print(dt2.df.to_dict())

    
