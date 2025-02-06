########################
# F.garcia
# creation: 06.02.2025
########################
class Node:
    def __init__(self, index):
        self.index = index

class DBResult:
    def __init__(self, description: list[tuple]):
        self.description = description
        self.dbr = []

    def _get_obj(self):
        """Creates a Node object with the attributes of the table description

        Returns:
            Node: object with the table attributes
        """
        # [(0, 'id', 'INTEGER', 0, None, 1), (1, 'dt_map_created', 'TEXT', 1, None, 0), (2, 'dt_map_modified', 'DATETIME', 1, None, 0), (3, 'mappath', 'TEXT', 1, None, 0), (4, 'tablename', 'TEXT', 1, None, 0), (5, 'mount', 'TEXT', 1, None, 0), (6, 'serial', 'TEXT', 1, None, 0), (7, 'mapname', 'TEXT', 1, None, 0)]
        obj=Node(1)
        delattr(obj,'index')
        for item in self.description:
            setattr(obj,item[1],None)    
        return obj
    
    def set_values(self,db_value_list):
        """Sets the query data in the database result list dbr.
            to call a data value:
            db_result = DBResult(table_description)
            db_result.set_values(table_data)
            value=db_result.dbr[0].column_in_table
        """
        # [(1, '2025-02-05 14:05:38.006341', '2025-02-05 14:05:38.006341', '\Users\Tony\Downloads', 'table_test_2', 'C:\', '0025_3858_01AD_3222.', '')]
        for data in db_value_list:
            if len(self.description)!=len(data):
                raise AssertionError("Data size and description size do not match!")
            obj=self._get_obj()
            for index,value in enumerate(data):
                attr=self.description[index][1]
                setattr(obj,attr,value)
            self.dbr.append(obj)
    
# Example usage
if __name__ == "__main__":
    # from db.describe_table_in_db(self.mapper_reference_table)
    test_struct=[(0, 'id', 'INTEGER', 0, None, 1), (1, 'dt_map_created', 'TEXT', 1, None, 0), (2, 'dt_map_modified', 'DATETIME', 1, None, 0), (3, 'mappath', 'TEXT', 1, None, 0), (4, 'tablename', 'TEXT', 1, None, 0), (5, 'mount', 'TEXT', 1, None, 0), (6, 'serial', 'TEXT', 1, None, 0), (7, 'mapname', 'TEXT', 1, None, 0)]
    db_result = DBResult(test_struct)
    print(dir(db_result))

    # from db.get_data_from_table(self.mapper_reference_table,'*',f"tablename='{table_name}'")
    test_data= [(1, '2025-02-05 14:05:38.006341', '2025-02-05 14:05:38.006341', '\\Users\\Tony\\Downloads', 'table_test_1', 'C:\\', '0025_3858_01AD_3222.', ''),
                (2, '2025-02-05 14:05:38.006341', '2025-02-05 14:05:38.006100', '\\Users\\Tony\\Downloads', 'table_test_2', 'C:\\', '0025_3858_01AD_3222.', '')]
    db_result.set_values(test_data)
    print(db_result.dbr[0].tablename)  # prints table_test_1
    print(db_result.dbr[1].dt_map_modified)  # prints the value '2025-02-05 14:05:38.006100'