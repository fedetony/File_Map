########################
# F.garcia
# creation: 17.02.2025
########################

import inquirer
import os
import sys
import glob as gb
from class_file_manipulate import FileManipulate
from class_autocomplete_input import *
from class_tree_viewer import TreeViewer,TreeNode
from rich import print
import json

F_M=FileManipulate() 
APP_PATH=f_m.get_app_path()
A_C=AutocompletePathFile(None,APP_PATH,False,False,False)

def my_style(node:TreeNode,level)->str:
    """Normal style"""
    if level==0:
        prefix = '|' * (level - 1) 
    else:   
        if node.i_am=='file': 
            prefix = '|'+'  ' * (level - 1) + '├── '
        else:
            prefix = '|'+'  ' * (level - 1) + '└── '
    return prefix

def my_style_expand(node:TreeNode,level):
    """Style with expansion"""
    prefix=my_style(node,level)
    if node.i_am=='dir': 
        if node.expand:
            prefix=prefix.replace(prefix[-2:],'< ')
        else:
            prefix=prefix.replace(prefix[-2:],'> ')
    return prefix

def my_style_size(node:TreeNode,level):
    """Style with sizes"""
    prefix=my_style(node,level)
    size_str=str(F_M.get_size_str_formatted(node.size,11,False))
    prefix=f'{size_str}\t'+ prefix
    return prefix

def my_style_expand_size(node:TreeNode,level):
    """Style with sizes"""
    prefix=my_style_expand(node,level)
    size_str=str(F_M.get_size_str_formatted(node.size,11,False))
    prefix=f'{size_str}\t'+ prefix
    return prefix
    

class FileExplorer:
    """File explorer"""
    def __init__(self,base_path:str=None,path_options:list=None,file_structure=None):
        self.base_path=base_path
        self.file_structure=file_structure
        self.path_options=path_options
        self.is_base_valid=False
        self.is_base_active=False
        self.is_file_structure=False
        self.t_v=None
        if self.check_path_options():
            self.is_file_structure=self.set_tree_structure()

    def check_path_options(self):
        """Checks for a valid base path

        Returns:
            bool: passed validation
        """
        # if there is a path use it
        if self.base_path:
            if self.set_base_path(self.base_path):
                return True
        # if path not valid and there is a file structure use it
        if self.file_structure:
            self.is_base_active=False
            self.is_base_valid=False
            return True
        
        if isinstance(self.path_options,list):
            if len(self.path_options)==0:
                self.path_options.append(APP_PATH)
            if  not self.file_structure and not self.is_base_valid:
                if len(self.path_options)==1:
                    return self.set_base_path(self.path_options[0])
                elif len(self.path_options)>1:
                    ch=[(f"{iii}. {self.path_options[iii-1]}",f"{iii}") for iii in range(1,len(self.path_options)+1)]
                    ch=ch+[("--> Enter a Path",':')]
                    questions = [inquirer.List(
                                "path",
                                message="Select a base path?",
                                choices=ch,
                                carousel=False,
                                )]
                    answers = inquirer.prompt(questions)
                    if answers['path'] == ':':
                        A_C.prompt='Type your entry: (Tab to autofill)'
                        user_path=A_C.get_input()
                        A_C.prompt=None
                        if not F_M.validate_path(user_path):
                            return self.check_path_options()
                        return self.set_base_path(user_path)
                        
                    else:
                        return self.set_base_path(self.path_options[int(answers['path'])-1])
        return False
    
    def set_base_path(self,a_path):
        """Sets a base path

        Args:
            a_path (str): path to set
         Returns:
            bool: path set    
        """
        if a_path:
            if os.path.exists(a_path):
                self.is_base_valid=True
                self.is_base_active=True
                self.base_path=a_path
                return True
            else:
                self.is_base_valid=f_m.validate_path(self.base_path)
                self.is_base_active=False
                if self.is_base_valid:
                    self.base_path=a_path
                    return True
        self.base_path=None
        return False

    @staticmethod
    def get_file_info(src_item):
        """Sets the file information Overrides Treeviewer function 
        Args:
            src_item (str): file path of file

        Returns:
            tuple: (name, size..., other info)
        """
        return (F_M.extract_filename(src_item),F_M.get_file_size(src_item))
        
    def set_tree_structure(self)->bool:
        """Sets file structure

        Returns:
            bool: file structure was set
        """
        if self.is_base_active and self.is_base_valid and not self.file_structure:
            self.is_base_valid
            self.file_structure=F_M.get_file_structure_from_active_path(self.base_path,None,{},full_path=False,fcn_call=self.get_file_info,show_progress=True)
            was_saved=F_M.save_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'__temp__fs.json',self.file_structure)
            # print('@'*50+'\n'+"Finished ->",was_saved,len(self.file_structure),'\n',A_C.cut_string_to_size(str(self.file_structure),333))
            # print('#'*33+'\nHit any key to continue:\n TAB to quit here\n'+'#'*33)
            # char=getch()
            # if char in ['\t',b'\t']:
            #     raise NameError("User Exit :)")
            return True
        elif self.file_structure and not self.is_base_valid:
            #when loaded from json tuples are lists
            print('[yellow]Repairing File structure:')
            self.file_structure=F_M.repair_list_tuple_in_file_structure(self.file_structure)
            print('[green]Success...File structure repaired!')
            return True
        return False

    def get_tree_view_string(self,a_filter=None,style=None):
        """Gets a tree viewer string with the file structure

        Args:
            a_filter (str, optional): Treeviewr filter. Defaults to None.
            style (str,function or None optional): if None uses my_style function. 
                            '' uses Treeviewer predifined style.
                            function uses a style function you set (use my style template).
                            Defaults to None.

        Returns:
            str: Treeviewer string
        """
        if not self.t_v:
            self.t_v=TreeViewer(self.file_structure,indexes_dict={'name':0,'size':1})
            if style=='':
                pass
            elif not style:
                self.t_v.call_style=self.my_style
            else:
                self.t_v.call_style=style
        return self.t_v.treenode_to_string(self.t_v.main_node,a_filter=a_filter)
    
    def get_tree_view_list(self,a_filter=None,style=None):
        """Gets a tree viewer string with the file structure

        Args:
            a_filter (str, optional): Treeviewr filter. Defaults to None.
            style (str,function or None optional): if None uses my_style function. 
                            '' uses Treeviewer predifined style.
                            function uses a style function you set (use my style template).
                            Defaults to None.

        Returns:
            str: Treeviewer string
        """
        tree_list=[]
        if not self.t_v:
            self.t_v=TreeViewer(self.file_structure,indexes_dict={'name':0,'size':1})
            if style=='':
                pass
            elif not style:
                self.t_v.call_style=self.my_style
            else:
                self.t_v.call_style=style
        tree_list=self.t_v.treenode_to_string_list(self.t_v.main_node,a_filter=a_filter)       
        return tree_list
    
    def reset_t_v(self):
        """Resets treeviewer"""
        #self.t_v.call_style=self.t_v.original_call_style
        self.t_v=None
    
    def browse_tree(self,a_filter,style=my_style)->int:
        """Show treestring in inquire format

        Args:
            a_filter (str): filter for tree viewer

        Returns:
            int: node id in the tree
        """
        # tree=self.get_tree_view_string(a_filter,style)
        # suggestions = tree.split('\n')
        # # remove last enter
        # if len(suggestions)>0:
        #     suggestions.pop(len(suggestions)-1)
        default_id=None
        suggestions = self.get_tree_view_list(a_filter,style)
        for node in self.t_v.all_nodes:
            if node.default:
                default_id=node.id
                break
        default_pos=0
        for jjj,node in enumerate(self.t_v.filtered_nodes):
            if node.id==default_id:
                default_pos=jjj
                break
        
        ch=[(f"{suggestions[iii]}",f"{iii}") for iii in range(len(suggestions))]
        questions = [inquirer.List(
                    "path",
                    message="Browse",
                    choices=ch,
                    carousel=False,
                    default=f"{default_pos}"
                    )]

        answers = inquirer.prompt(questions)
        #print(answers)
        node=self.t_v.filtered_nodes[int(answers['path'])]
        return node.id
    
    def browse_files(self,style=my_style_expand)->TreeNode:
        """Browser for files with expandable folders

        Returns:
            TreeNode: Selected file node
        """
        self.reset_t_v() # to change to new style
        os.system('cls' if os.name == 'nt' else 'clear')
        nodeid=self.browse_tree('expand',style)
        selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
        #print(selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)
        while selected_node.i_am=='dir':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.t_v.clear_default()
            selected_node.default=True
            if selected_node.expand==True:
                setattr(selected_node,'expand',False)
            else:
                setattr(selected_node,'expand',True)
            nodeid=self.browse_tree('expand',style)
            selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
            #print(selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)
        return selected_node
    
    def browse_folders(self,style=my_style)->TreeNode:
        """Browses through folders (Does not show files)

        Returns:
            TreeNode: Selected folder node
        """
        self.reset_t_v()
        os.system('cls' if os.name == 'nt' else 'clear')
        nodeid=self.browse_tree('dir',style)
        selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
        #print(selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)
        return selected_node
        

# Example usage
if __name__ == "__main__":
    # F_E=FileExplorer('d:\\Downloads\\amenofis',['D:\\Downloads',APP_PATH],None)
    # F_E=FileExplorer(None,['d:\\','d:\\Temp\\','D:\\Downloads',APP_PATH],None)
    fs=F_M.load_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'d__temp__fs.json')
    # fs=F_M.load_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'__temp__fs.json')
    F_E=FileExplorer(None,['d:\\','d:\\Temp\\','D:\\Downloads',APP_PATH],fs)
    print(F_E.is_file_structure)
    # print(F_E.file_structure)
    # tree=F_E.get_tree_view_string('dir')
    # print(tree)
    # selected_node=F_E.browse_folders()
    # print('Finally selected:',selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)
    selected_node=F_E.browse_files()
    print('Finally selected:',selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)

    # selected_node=F_E.browse_folders()
    # print('Finally selected:',selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)
    
    # selected_node=F_E.browse_folders(my_style_size)
    # print('Finally selected:',selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)
    # print(selected_node.to_dict())
    

    # # Test tab autocomplete
    # def autocomplete_fn(_text, state):
    #     # Every time the user presses TAB, we'll switch to the next suggestion
    #     # The `state` variable contains the index of the current suggestion
    #     # We can wrap it around to the first suggestion if we reach the end
    #     return suggestions[state % len(suggestions)]


    # questions = [
    #     inquirer.Text(
    #         "name",
    #         message="Press TAB to cycle through suggestions",
    #         autocomplete=autocomplete_fn,
    #     ),
    # ]

    # answers = inquirer.prompt(questions)

    # print(answers)


# input_path = A_C.get_input
# my_path = input_path()
# print("User input:", my_path)
# def test_handle():
#     last_char=' '
#     while True:
#         print("Map keys: press enter to exit")
#         char = getch()
#         os.system('cls' if os.name == 'nt' else 'clear')
#         key_handle=A_C.handle_key(last_char,char)
#         print('Char: ',chr(ord(char)),' last->ord:',ord(last_char),' ord:',ord(char), 'keyhandle=',key_handle)
#         print(key_handle," Special :",A_C.is_special_character(last_char,char))
#         if char in [b'\r', b'\n', '\r', '\n'] or key_handle=='enter': #enter
#             return
#         last_char=char
# test_handle()