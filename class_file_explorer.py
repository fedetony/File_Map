########################
# F.garcia
# creation: 17.02.2025
########################
import os
import sys
import glob as gb

import inquirer.render
import inquirer.render.console

from inquirer.render import ConsoleRender

from rich import print
import json

import inquirer
from inquirer import errors

# from inquirer.render.console._checkbox import Checkbox
from inquirer.render.console._confirm import Confirm
from inquirer.render.console._editor import Editor
# from inquirer.render.console._list import List
from inquirer.render.console._password import Password
from inquirer.render.console._path import Path
from inquirer.render.console._text import Text

from class_file_manipulate import FileManipulate
from class_autocomplete_input import *
from class_tree_viewer import TreeViewer,TreeNode

# Overrides
import inquirer.questions as questions
from inquirer.render.console import ConsoleRender
from class_override_checkbox import Checkbox ,List ,CONTRACT_KEYWORD, EXPAND_KEYWORD, MENU_PROCESS_SELECTOR
def checkbox_shortcut(message, default_pos=0,process_mode=None,process_list=None,render=None, **kwargs):
    render = render or ConsoleRender()
    question =  questions.Checkbox(
                                    name=kwargs.get('name',""), 
                                    message=message, 
                                    choices=kwargs.get('choices',None),
                                    hints=kwargs.get('hints',None),
                                    locked=kwargs.get('locked',None),
                                    default=kwargs.get('default',None),
                                    ignore=kwargs.get('ignore',False),
                                    validate=kwargs.get('validate',True),
                                    carousel=kwargs.get('carousel',False),
                                    other=kwargs.get('other',False),
                                    autocomplete=kwargs.get('autocomplete',None),
                                    )
    
    # question=CheckboxSelect(default_pos,question)
    setattr(question,"answers",{})
    setattr(question,"default_pos",default_pos)
    setattr(question,"current",default_pos)
    if process_list:
        setattr(question,"process_list",process_list)
    else:
        setattr(question,"process_list",[])
    setattr(question,"process_mode",process_mode)
    if process_mode:
        to_print=[]
        for a_key,value in MENU_PROCESS_SELECTOR.items():
            if len(a_key)==1:
                to_print.append(f"{a_key}={value.replace('*','')}")
        print(', '.join(to_print))
    print("ESC: Cancel, ENTER:Selection, ARROWS:Navigate, TAB/SPACE:Select, CTRL+T:Toggle, CTRL+A:Select ALL, CTRL+R:Unselect ALL")
    # setattr(question,'_current_index',_current_index)
    rrr=render.render(question)
    setattr(question,"current",default_pos)
    return rrr

def render_factory_mod(self, question_type):
        matrix = {
            "text": Text,
            "editor": Editor,
            "password": Password,
            "confirm": Confirm,
            "list": List,
            "checkbox": Checkbox,
            "path": Path,
        }

        if question_type not in matrix:
            raise errors.UnknownQuestionTypeError()
        return matrix.get(question_type)

ConsoleRender.render_factory=render_factory_mod
inquirer.checkbox=checkbox_shortcut

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
        if node.expand or node.expand is None:
            prefix=prefix.replace(prefix[-3:],'─< ')
        else:
            prefix=prefix.replace(prefix[-3:],'─> ')
    return prefix

def my_style_dir_expand(node:TreeNode,level):
    """Style with expansion"""
    prefix=my_style(node,level)
    if node.i_am=='dir': 
        if node.expand or node.expand is None:
            prefix=prefix.replace(prefix[-3:],'─< ')
        else:
            prefix=prefix.replace(prefix[-3:],'─> ')
        has_subdirs=False
        for child in node.children:
            if child.i_am=='dir':
                has_subdirs=True
                break
        if not has_subdirs:
            prefix=prefix.replace(prefix[-3:],'─¤ ')  # ‡ • † × · ¤
        # Mark the Nodes with selected children
        if node.selected_children:
            prefix=A_C.add_ansi(prefix,'yellow')
    return prefix

def my_style_file_expand(node:TreeNode,level):
    """Style with expansion"""
    prefix=my_style(node,level)
    if node.i_am=='dir': 
        if node.expand or node.expand is None:
            prefix=prefix.replace(prefix[-3:],'─< ')
        else:
            prefix=prefix.replace(prefix[-3:],'─> ')
        if len(node.children)==0:
            prefix=prefix.replace(prefix[-3:],'─¤ ')  # ‡ • † × · ¤
        # Mark the Nodes with selected children
        if node.selected_children:
            prefix=A_C.add_ansi(prefix,'yellow')
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

def my_style_dir_expand_size(node:TreeNode,level):
    """Style with expansion"""
    prefix=my_style_dir_expand(node,level)
    size_str=str(F_M.get_size_str_formatted(node.size,11,False))
    prefix=f'{size_str}\t'+ prefix
    return prefix

def my_style_file_expand_size(node:TreeNode,level):
    """Style with expansion"""
    prefix=my_style_file_expand(node,level)
    size_str=str(F_M.get_size_str_formatted(node.size,11,False))
    prefix=f'{size_str}\t'+ prefix
    return prefix
######################################################################################

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
            # was_saved=F_M.save_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'__temp__fs.json',self.file_structure)
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
        # self.t_v.clear_selected_children(self.t_v.main_node)
        self.t_v.set_selected_children(self.t_v.main_node) 
        return tree_list
    
    def reset_t_v(self):
        """Resets treeviewer"""
        #self.t_v.call_style=self.t_v.original_call_style
        self.t_v=None
    
    def browse_tree_list(self,a_filter,style=my_style,prompt="Browse")->int:
        """Show treestring in inquire format

        Args:
            a_filter (str): filter for tree viewer

        Returns:
            int: node id in the tree
        """
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
                    message=prompt,
                    choices=ch,
                    carousel=False,
                    default=f"{default_pos}"
                    )]

        answers = inquirer.prompt(questions)
        #print(answers)
        ans=str(answers['path'])
        is_expand=None
        if CONTRACT_KEYWORD in ans:
            ans=ans.replace(CONTRACT_KEYWORD,'')
            is_expand=False
        elif EXPAND_KEYWORD in ans:
            ans=ans.replace(EXPAND_KEYWORD,'')
            is_expand=True
        node=self.t_v.filtered_nodes[int(ans)]
        if is_expand is not None:
            setattr(node,'expand',is_expand)
        return node.id ,is_expand
    
    def browse_files(self,style=my_style_expand,allow_dir_selection=True,prompt="Browse")->TreeNode:
        """Browser for files with expandable folders

        Returns:
            TreeNode: Selected file node
        """
        self.reset_t_v() # to change to new style
        is_expand = True
        while is_expand is not None: #selected_node.i_am=='dir':
            os.system('cls' if os.name == 'nt' else 'clear')
            nodeid,is_expand=self.browse_tree_list('expand',style,prompt)
            selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
            self.t_v.clear_default()
            selected_node.default=True
            if selected_node.i_am=='dir' and not allow_dir_selection:
                is_expand = True
            if selected_node.id==0:
                is_expand = True
           
        return selected_node
    
    def browse_folders(self,style=my_style_dir_expand,prompt="Browse")->TreeNode:
        """Browses through folders (Does not show files)

        Returns:
            TreeNode: Selected folder node
        """
        self.reset_t_v() # to change to new style
        is_expand = True
        while is_expand is not None: #selected_node.i_am=='dir':
            os.system('cls' if os.name == 'nt' else 'clear')
            nodeid,is_expand=self.browse_tree_list('expand_dir',style,prompt)
            selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
            self.t_v.clear_default()
            selected_node.default=True
            # Do not return the main node
            if selected_node.id==0:
                is_expand = True
        return selected_node
    
    def browse_tree_checkbox(self,a_filter,style=my_style,selected_list:list=None,locked_list:list=None,prompt:str="Select",expand_contract_id=None, allow_dir_selection=True)->list:
        """Show tree string in inquire checkbox format

        Args:
            a_filter (str): filter for tree viewer

        Returns:
            list: node id in the tree
        """
        suggestions = self.get_tree_view_list(a_filter,style)
        
        default_pos=0
        default_selected_list=[]
        # hidden_node_list=[]
        if not selected_list:
            selected_list=[]
        for jjj,node in enumerate(self.t_v.filtered_nodes):
            if node.id == expand_contract_id:
                default_pos=jjj
            if node.id in selected_list or node.selected:
                default_selected_list.append(f"{jjj}")
            # elif node.id not in selected_list and node.selected:
            #     hidden_node_list.append(node.id)
            if not allow_dir_selection and node.i_am == 'dir':    
                if not isinstance(locked_list,list):
                    locked_list=[]
                locked_list.append(f"{jjj}")
                # setattr(node,'selected',False)
            
        ch=[(f"{suggestions[iii]}",f"{iii}") for iii in range(len(suggestions))]
        answers={}
        answers["path"] =inquirer.checkbox(
                    message=prompt,
                    default_pos=default_pos,
                    name="path",
                    choices=ch,
                    carousel=False,
                    locked=locked_list,
                    default=default_selected_list,
                    )
        # print(answers)
        # getch()
        nodeid_list=[]
        has_expansion=False
        for ans in answers['path']:
            ans=str(ans)
            is_expand=None
            is_process=False
            for a_key, value_keyword in MENU_PROCESS_SELECTOR.items():
                if value_keyword:
                    if value_keyword in ans:
                        ans=ans.replace(value_keyword,'')
                        node=self.t_v.filtered_nodes[int(ans)]
                        self.do_process(node,a_key)
                        setattr(node,'default',True)
                        has_expansion=True
                        expand_contract_id=node.id
                        is_process=True
            if CONTRACT_KEYWORD in ans:
                ans=ans.replace(CONTRACT_KEYWORD,'')
                is_expand=False
            elif EXPAND_KEYWORD in ans:
                ans=ans.replace(EXPAND_KEYWORD,'')
                is_expand=True
            node=self.t_v.filtered_nodes[int(ans)]
            if not is_process:
                if is_expand is not None:
                    setattr(node,'expand',is_expand)
                    self.t_v.clear_default()
                    setattr(node,'default',True)
                    has_expansion=True
                    expand_contract_id=node.id
                    # self.t_v.clear_selected_children(node)
                    self.t_v.set_selected_children(node)
                elif is_expand is None:
                    # Set selected to true
                    setattr(node,'selected',True)
                    nodeid_list.append(node.id)
                    expand_contract_id=None
        # set the not selected to False 
        for node in self.t_v.filtered_nodes:
            if node.id not in nodeid_list:
                setattr(node,'selected',False)
        nodeid_list=[]
        self.t_v.set_selected_children(self.t_v.main_node)
        for node in self.t_v.all_nodes:
            if node.selected:
                nodeid_list.append(node.id)
        return nodeid_list ,has_expansion, expand_contract_id   
    
    def do_process(self,node:TreeNode,process_key:str):
        print(node.id,f' pressed {process_key}')

    def select_multiple_folders(self,style=my_style_dir_expand,locked_list:list=None,prompt:str="Select")->list[TreeNode]:
        """Browses through folders (Does not show files)

        Returns:
            TreeNode: Selected folder node
        """
        self.reset_t_v() # to change to new style
        has_expansion = True
        selection_list=None
        nodeid_list=None
        expand_contract_id=None
        # locked_list=[0]
        while has_expansion: #selected_node.i_am=='dir':
            os.system('cls' if os.name == 'nt' else 'clear')
            nodeid_list ,has_expansion, expand_contract_id=self.browse_tree_checkbox('expand_dir',style,nodeid_list,locked_list,prompt, expand_contract_id,allow_dir_selection=True)
            selection_list=[]
            for nodeid in nodeid_list:
                selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
                if selected_node.selected:
                    selection_list.append(selected_node)
            
                
        return selection_list
    
    def select_multiple_files(self,style=my_style_file_expand,locked_list:list=None,prompt:str="Select",allow_dir_selection=True)->list[TreeNode]:
        """Browses through files (Does not show files)

        Returns:
            TreeNode: Selected folder node
        """
        self.reset_t_v() # to change to new style
        has_expansion = True
        selection_list=None
        nodeid_list=None
        expand_contract_id=None
        # start treeview
        _=self.get_tree_view_list('expand_dir',style)
        while has_expansion: #selected_node.i_am=='dir':
            os.system('cls' if os.name == 'nt' else 'clear')
            nodeid_list ,has_expansion, expand_contract_id=self.browse_tree_checkbox('expand',style,nodeid_list,locked_list,prompt, expand_contract_id,allow_dir_selection)
            selection_list=[]
            for nodeid in nodeid_list:
                selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
                if allow_dir_selection and selected_node.selected:
                    selection_list.append(selected_node)
                elif not allow_dir_selection and selected_node.selected and selected_node.i_am=='file':
                    selection_list.append(selected_node)
        return selection_list
    
    def process_list_tree_checkbox(self,a_filter,style=my_style,selected_list:list=None,process_list:list=None,locked_list:list=None,prompt:str="Select",expand_contract_id=None)->list:
        """Show and allow process selection tree string in inquire checkbox format

        Args:
            a_filter (str): filter for tree viewer

        Returns:
            list: node id in the tree
        """
        suggestions = self.get_tree_view_list(a_filter,style)
        
        default_pos=0
        default_selected_list=[]
        if not selected_list:
            selected_list=[]
        for jjj,node in enumerate(self.t_v.filtered_nodes):
            if node.id == expand_contract_id:
                default_pos=jjj
            if node.id in selected_list or node.selected:
                default_selected_list.append(f"{jjj}")
            

        ch=[(f"{suggestions[iii]}",f"{iii}") for iii in range(len(suggestions))]
        answers={}
        answers["path"] = inquirer.checkbox(
                    message=prompt,
                    default_pos=default_pos,
                    process_mode='all',
                    process_list=process_list,
                    name="path",
                    choices=ch,
                    carousel=False,
                    locked=locked_list,
                    default=default_selected_list,
                    )
        # print(answers)
        # getch()
        nodeid_list=[]
        has_expansion=False
        for ans in answers['path']:
            ans=str(ans)
            is_expand=None
            if CONTRACT_KEYWORD in ans:
                ans=ans.replace(CONTRACT_KEYWORD,'')
                is_expand=False
            elif EXPAND_KEYWORD in ans:
                ans=ans.replace(EXPAND_KEYWORD,'')
                is_expand=True
            node=self.t_v.filtered_nodes[int(ans)]
            if is_expand is not None:
                setattr(node,'expand',is_expand)
                self.t_v.clear_default()
                setattr(node,'default',True)
                has_expansion=True
                expand_contract_id=node.id
                # self.t_v.clear_selected_children(node)
                self.t_v.set_selected_children(node)
            elif is_expand is None:
                # Set selected to true
                setattr(node,'selected',True)
                nodeid_list.append(node.id)
                expand_contract_id=None
        # set the not selected to False 
        for node in self.t_v.filtered_nodes:
            if node.id not in nodeid_list:
                setattr(node,'selected',False)
        nodeid_list=[]
        self.t_v.set_selected_children(self.t_v.main_node)
        for node in self.t_v.all_nodes:
            if node.selected:
                nodeid_list.append(node.id)
        return nodeid_list ,has_expansion, expand_contract_id
    
    def browse_files_with_process(self,style=my_style_expand,allow_dir_selection=True,locked_list:list=None,prompt="Browse")->TreeNode:
        """Browser for files with expandable folders

        Returns:
            TreeNode: Selected file node
        """
        self.reset_t_v() # to change to new style
        has_expansion = True
        selection_list=None
        nodeid_list=None
        expand_contract_id=None
        process_list=None
        # locked_list=[0]
        while has_expansion: #selected_node.i_am=='dir':
            os.system('cls' if os.name == 'nt' else 'clear')
            nodeid_list ,has_expansion, expand_contract_id=self.process_list_tree_checkbox(
                a_filter='expand',
                style=style,
                selected_list=nodeid_list,
                process_list=process_list,
                locked_list=locked_list,
                prompt=prompt, 
                expand_contract_id=expand_contract_id,
                )
            selection_list=[]
            for nodeid in nodeid_list:
                selected_node=self.t_v.get_nodes_by_attribute('id',nodeid)[0]
                if selected_node.selected:
                    selection_list.append(selected_node)
        return selection_list
        

# Example usage
if __name__ == "__main__":
    # F_E=FileExplorer('d:\\Downloads\\amenofis',['D:\\Downloads',APP_PATH],None)
    # F_E=FileExplorer(None,['d:\\','d:\\Temp\\','D:\\Downloads',APP_PATH],None)
    # fs=F_M.load_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'__temp__fs_small.json')
    fs=F_M.load_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'d__temp__fs.json')
    F_E=FileExplorer(None,['d:\\','d:\\Temp\\','D:\\Downloads',APP_PATH],fs)
    print(F_E.is_file_structure)
    # print(F_E.file_structure)
    # tree=F_E.get_tree_view_string('dir')
    # print(tree)

    # Test Files and Folders list
    #----------------------------
    # selected_node=F_E.browse_folders()
    selected_node=F_E.browse_files()

    print('Finally selected:',selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)

    # Test Files and Folders checkbox
    #----------------------------
    # selected_node_list=F_E.select_multiple_folders()
    selected_node_list=F_E.select_multiple_files()

    for selected_node in selected_node_list:
        print('Finally selected:',selected_node.id,selected_node.name,F_M.get_size_str_formatted(selected_node.size),selected_node.expand)

