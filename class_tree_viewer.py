#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
########################
# F.garcia
# creation: 15.02.2025
########################

class TreeNode:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.i_am=''
        self.expand=True
        self.level=None
        self.parent = None 
        self.id=None
        self.info=None
        self.size=None
    
    def to_dict(self)->dict:
        """Convert node to dictionary. Only attributes not starting with '__'

        Returns:
            dict: Node as dictionary
        """
        me_dict={}
        for key in dir(self):
            if not key.startswith('__') and not key in ["to_dict"]:
                att=getattr(self,key)
                if  key not in ['parent','children']:
                    me_dict.update({key:att}) 
                else:
                    if key == 'parent':
                        if isinstance(att,TreeNode):
                            me_dict.update({key:getattr(att,'id')})
                        else:
                            me_dict.update({key:None})
                    elif key == 'children':
                        att_list=[]
                        for child in att:
                            if isinstance(child,TreeNode):
                                att_list.append(getattr(child,'id')) 
                            else:
                                att_list.append(None)
                        me_dict.update({key:att_list})
        return me_dict

class TreeViewer:
    def __init__(self, file_struct,indexes_dict:dict=None,str_style=0):
        self.file_struct = file_struct
        self.all_nodes=[]
        self.filtered_nodes=[]
        self.count=0
        self.filename_index=0
        self.size_index=None
        if indexes_dict:
            if 'name' in indexes_dict.keys():
                self.filename_index=indexes_dict['name']
            if 'size' in indexes_dict.keys():
                self.size_index=indexes_dict['size']    
        self.main_node=None
        self.str_style=str_style
        self._define_struct()
    
    @staticmethod
    def _is_dir(fs)->bool:
        """Check if is a File structure directory

        Args:
            fs (any): Checks for directory of filestructure

        Returns:
            bool: True if a directory.
        """
        if isinstance(fs,dict):
            for a_key,value in fs.items():
                if not isinstance(value,list):
                    return False
            return True
        return False
    
    @staticmethod
    def _is_file(fs)->bool:
        """Check if is a File structure file

        Args:
            fs (any): Checks for directory of filestructure

        Returns:
            bool: True if a directory.
        """
        if isinstance(fs,tuple):
            for value in fs:
                if isinstance(value,(dict,list)) :
                    return False
            return True
        if not isinstance(fs,(dict,list)) :
            return True
        return False
    
    def get_file_name_in_tuple(self,file_tup:tuple)->str:
        """Returns string when Filestructure has tuple with information
            uses filename_index to get position of filename in tuple
        Args:
            file_tup (tuple): tuple with file information

        Returns:
            str: file name in tuple
        """
        if len(file_tup)==0:
            self.count=self.count+1
            return 'file_'+str(self.count)
        return str(file_tup[self.filename_index])
    
    def get_file_size_in_tuple(self,file_tup:tuple)->str:
        """Returns string when Filestructure has tuple with information
            uses size_index to get position of filename in tuple
        Args:
            file_tup (tuple): tuple with file information

        Returns:
            int: file size in tuple
        """

        if len(file_tup)==0 or not self.size_index:
            return None
        return file_tup[self.size_index]

    def _get_nodes(self,fs)->TreeNode:
        """Recursive Node formation from file structure

        Args:=
            fs (dict): File structure

        Returns:
            TreeNode: Main node 
        """
        if self._is_dir(fs):
            for a_key,file_list in fs.items():
                node = TreeNode(a_key)
                node.i_am='dir'
                self.all_nodes.append(node)
                node.children=self._get_nodes(file_list)
                return node
        
        elif isinstance(fs,list):
            node_list=[]
            for a_file in fs:
                if self._is_dir(a_file):
                    node = self._get_nodes(a_file)
                    node_list.append(node)
                elif self._is_file(a_file):
                    if isinstance(a_file,tuple):
                        a_f=self.get_file_name_in_tuple(a_file)
                        a_size=self.get_file_size_in_tuple(a_file)
                    else:
                        a_f=str(a_file)
                    node = TreeNode(a_f)
                    node.i_am='file'
                    node.info=a_file # add all info to the node
                    if a_size:
                        node.size=a_size
                    node_list.append(node)
                    self.all_nodes.append(node)
            return node_list
        raise ValueError(f'{type(fs)} is not a valid type for file structure!')
        return None

    def _define_struct(self):
        """Set information for file struct
        """
        self.main_node=self._get_nodes(self.file_struct)
        self._set_treenode_levels(self.main_node)
        self._set_treenode_sizes(self.main_node)
    
    def get_nodes_by_attribute(self,attribute:str,value)->list[TreeNode]:
        """Returns a list of nodes which have node.attribute=value

        Args:
            attribute (str): node attibute
            value (any): value to find

        Returns:
            list: list of TreeNode
        """
        the_node=[]
        for node in self.all_nodes:
            if hasattr(node,attribute):
                if getattr(node,attribute)==value:
                    the_node.append(node)
        return the_node
    
    def call_style(self,node:TreeNode,level):
        """Function to be overwritten"""
        self._call_style(node,level)

    def _call_style(self, node:TreeNode,level):
        """Inner style"""
        if self.str_style==0:
            if level==0:
                prefix = '  ' * (level - 1) 
            else:    
                prefix = '  ' * (level - 1) + '└── '
        elif self.str_style==1:
            if level==0:
                prefix = '  ' * (level - 1) 
            else:    
                prefix = '  ' * (level - 1) + '└── '
            prefix = str(node.level) +' > '+ prefix
        elif self.str_style==2:
            if level==0:
                prefix = '  ' * (level - 1) 
            else:    
                prefix = '  ' * (level - 1) + f'{node.i_am}({node.level}): '
        else:
            prefix=''
        return prefix

    def expand_all_treenodes(self,expand=True):
        """Expands or contract all nodes.

        Args:
            expand (bool, optional): Expand if True otherwise contract. Defaults to True.
        """
        for node in self.all_nodes:
            node.expand=expand

    def treenode_to_string(self, node:TreeNode, str_out='', level=0, a_filter=None)->str:
        """Generates a string with a Tree structure.

        Args:
            node (TreeNode): TreeNode object to print
            str_out (str, optional): String prefix. Defaults to ''.
            level (int, optional): level depth. Defaults to 0.
            a_filter (_type_, optional): Filter only folders with 'dir','expand' checks for expand flag in node. Defaults to None.

        Returns:
            str: File tree string 
        """
        if not str_out:
            str_out=''
        if node is None:
            return str_out
        if not node.name:
            return str_out
        if level==0 and not node.parent: 
            self.filtered_nodes=[]
        # set the style
        prefix = self.call_style(node,level)  

        if a_filter not in ['dir','expand']:
            str_out=str_out+prefix + str(node.name) +'\n'
            self.filtered_nodes.append(node)
            for child in node.children:
                str_out=self.treenode_to_string(child, str_out, level + 1,a_filter)
                
        elif a_filter == 'dir':
            if node.i_am=='dir':    
                str_out=str_out+prefix + str(node.name) +'\n'
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=self.treenode_to_string(child, str_out, level + 1,a_filter)
                    
        elif a_filter == 'expand':
            if node.i_am=='dir' and node.expand:    
                str_out=str_out+prefix + str(node.name) +'\n'#' <─\n'
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=str(self.treenode_to_string(child, str_out, level + 1,a_filter))
            elif node.i_am=='dir' and not node.expand:    
                str_out=str_out+prefix + str(node.name) +'\n'#' ─>\n'
                self.filtered_nodes.append(node)
            elif node.i_am=='file':
                str_out=str_out+prefix + str(node.name) +'\n'
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=self.treenode_to_string(child, str_out, level + 1,a_filter)
                    
        return str_out
    
    def _set_treenode_levels(self, node:TreeNode, level=0):
        """Sets the level and parent in each node

        Args:
            node (TreeNode): main node
            level (int, optional): initial level value. Defaults to 0.
        """
        if node:
            node.level=level
            if not node.id:
                node.id=self.count
                self.count=self.count+1
            for child in node.children:
                child.parent=node
                self._set_treenode_levels(child, level + 1)
    
    def _set_treenode_sizes(self, node:TreeNode, level=0):
        """Sets the level and parent in each node

        Args:
            node (TreeNode): main node
            level (int, optional): initial level value. Defaults to 0.
        """
        if node and self.size_index:
            if node.i_am=='dir':
                size=0    
                for child in node.children:
                    size=size+self._set_treenode_sizes(child, level + 1)
                node.size=size #sets size of directory as sum of directories and files inside
                return size
            if node.i_am=='file':
                if node.size:
                    return node.size 
        return 0
            
            
# Example usage
if __name__ == "__main__":
    from class_file_manipulate import FileManipulate
    F_M=FileManipulate()
    def get_file_info(src_item):
        return (F_M.extract_filename(src_item),F_M.get_file_size(src_item))
        return ('f',F_M.get_file_size(src_item))
    fs=F_M.get_file_structure_from_active_path('D:\\temp','test',{},full_path=False,fcn_call=get_file_info)
    T_V=TreeViewer(fs,indexes_dict={'name':0,'size':1})
    print(T_V.count)
    print(T_V._is_dir(fs))
    print(T_V.main_node.to_dict())
    T_V.call_style=T_V._call_style #need to set an style before calling
    tree=T_V.treenode_to_string(T_V.main_node,a_filter='dir')
    print(tree)
    print('*'*50)
    T_V.str_style=2
    def my_style(node:TreeNode,level):
        if level==0:
            prefix = '8>' * (level - 1) 
        else:    
            prefix = '8'+'==' * (level - 1) + '==> '
        prefix=str(node.id)+":"+prefix
        return prefix
    
    T_V.call_style=my_style
    tree=T_V.treenode_to_string(T_V.main_node,a_filter=None)
    print(tree)

    T_V.str_style=1
    T_V.call_style=T_V._call_style #need to set an style before calling
    tree=T_V.treenode_to_string(T_V.main_node,a_filter='dir')
    print(tree)