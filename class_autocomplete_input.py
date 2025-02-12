# -*- coding: utf-8 -*-

import os
import glob as gb
import pyperclip 
from class_file_manipulate import FileManipulate
from rich import print
f_m=FileManipulate() 
APP_PATH=f_m.get_app_path()

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

# Backspace (delete previous character): \x08 or b'\x08'
# Tab (move to next tab stop): \t or b'\t'
# Enter (submit form, end line): \n or b'\n'
# Escape (exit command mode): \x1b[27m or b'\x1b[27m'
# Page up: \x03 or b'\x03'
# Page down: \x04 or b'\x04'
# Up arrow (move cursor up one line): \x05 or b'\x05'
# Down arrow (move cursor down one line): \x06 or b'\x06'
# Left arrow (move cursor left one character): \x07 or b'\x07'
# Right arrow (move cursor right one character): \x08 or b'\x08'
# Home key (move to beginning of line): \x09 or b'\x09'
# End key (move to end of line): \x10 or b'\x10'
# Control+C (interrupt program, send EOF signal): \x03 or b'\x03'
# Control+D (send EOF signal without interrupting program): \x04 or b'\x04'
# Control+L (clear screen): \x1b[2J or b'\x1b[2J'
# Control+Z (suspend program, send SIGSTOP signal): \x1b[33m or b'\x1b[33m'

class AutocompletePathFile:
    def __init__(self, prompt,base_path=APP_PATH,absolute_path=True,verbose=True):
        self.prompt = prompt
        self.line_user_input=''
        self.line_autocompleted=""
        self.autocomplete_options=[]
        self.base_path=base_path
        self.absolute_path=absolute_path
        self.verbose=verbose
        print(self.prompt)
        
    def _get_possible_path_list(self, path)->list[str]:
        """Use glob to find similar paths with patterns

        Args:
            path (str): path as pattern

        Returns:
            list: list of patterns found
        """
        try:
            if os.path.isdir(path):
                    return gb.glob(os.path.join(path, '*'))    
            list_ans= gb.glob(path + '*')
            # from application path
            if len(list_ans)==0:
                path_app=os.path.join(self.base_path,path)
                if os.path.isdir(path_app):
                    return gb.glob(os.path.join(path_app, '*'))
                list_ans=gb.glob(path_app + '*')
                if len(list_ans)>0:
                    return list_ans
                return [path]
            return list_ans
        except Exception as eee:
            print(f"Error: {eee}")
            return []
    
    @staticmethod
    def get_commontxt_optionlist(a_string_list:list):
        """Takes a list of string, like paths, and returns the repeated text in the beguining of each string. 

        Args:
            a_string_list (list): List of strings

        Returns:
            tuple(str,list): Repeated text in string start.
                    List with non repeated end of strings
        """
        fill_add=''
        ini_str=''
        comp_list=a_string_list.copy()
        all_same=True
        if isinstance(comp_list,list) and len(comp_list)>0:
            if len(comp_list[0])>0:
                ini_str=comp_list[0][0]
        
        while all_same and ini_str != '':
            new_comp=[]
            for ccc in comp_list:
                if len(ccc)>0:
                    if ccc[0] == ini_str:
                        new_comp.append(ccc[1:]) 
                    else:
                        all_same=False
                        break
                else:
                    break
            if all_same:
                fill_add=fill_add+ini_str
                if isinstance(new_comp,list) and len(new_comp)>0:
                    if len(new_comp[0])>0:
                        ini_str=new_comp[0][0]
                    else:
                        break
                    comp_list=new_comp.copy()
                else:
                    break    
            # print(f"options: {comp_list}")
        return fill_add,comp_list


    def autocomplete_path(self,a_path_file):
        """Autocompletes the paths. If only one possibility, will autocomplete. If many possibilities, will find

        Args:
            a_path_file (str): path to autocomplete

        Returns:
            _type_: autocompleted path
        """
        list_auto=self._get_possible_path_list(a_path_file)
        #print(f"List----->>>>{list_auto}")
        #print(f"base Path----->>>>{self.base_path} -> {a_path_file}")
        if len(list_auto)==1:
            end_path=list_auto[0]
            if not self.absolute_path and os.path.exists(os.path.join(self.base_path,end_path)):
                end_path=os.path.join(self.base_path,end_path)
            path_exists=os.path.exists(end_path)
            if self.verbose:    
                print(f"File/Path exists: {path_exists}")
            if path_exists:
                # to fix the separators
                end_path=f_m.fix_path_separators(end_path)   
            return end_path
        elif len(list_auto)>1:
            comp_list=[]
            fill_add2,_=self.get_commontxt_optionlist(list_auto)
            for path in list_auto:
                comp_list.append(path.replace(fill_add2,''))
            fill_add,comp_list=self.get_commontxt_optionlist(comp_list)
            # print(a_path_file,'-->>',fill_add,"=?????=",fill_add2)  
            if fill_add == '':
                end_path=fill_add2
            else:
                end_path=a_path_file+fill_add
            if self.verbose:
                print(f"Options: {end_path}+{comp_list}")
            return end_path
        return a_path_file

    def get_input(self):
        last_char=None
        pos=0
        lenght=0
        while True:
            char = getch()
            os.system('cls' if os.name == 'nt' else 'clear')
            if self.verbose:
                print(self.prompt)
            if char in [b'\r', b'\n']: #enter
                return self.line_autocompleted
            if char == b'\t': #tab
                self.line_user_input=self.autocomplete_path(self.line_user_input)
                char = None 
            elif char == b'\x1b': # esc
                return None
            elif char == b'\x03': # cntr + c
                pass
            elif char == b'\x18': # cntr + v
                # paste clipboard
                pyperclip.paste()
                pass
            elif char == b'\x1a': # cntr + z
                pass
            elif char == b'\x1a': # cntr + z
                pass    
            elif last_char == b'\x00':
                if char == b'I': # page up
                    print("PageUP")
                    pass
                elif char == b'Q': # page Down
                    print("PageDown")
                    pass
                elif char == b'H': #arrow up
                    pass
                elif char == b'P': #arrow down
                    pass
                elif char == b'M': #arrow right
                    pass
                elif char == b'K': #arrow left
                    pass
                elif char == b'S': #Delete
                    pass
                elif char == b's': #cntr + arrow left
                    pass
                elif char == b't': #cntr + arrow right
                    pass
                elif char == b'G': #Home
                    pass
                elif char == b'O': #End
                    pass
                elif char == b'>': #F2
                    pass
                else:
                    pass
            elif char == b'\x08': #Back Space
                lenght=len(self.line_user_input)
                self.line_user_input=self.line_user_input[:lenght-1]
                lenght=len(self.line_user_input)
            else: 
                pos=pos+1
                if char and char not in [b'\x00',b'\x01',b'\x02',b'\x03',b'\x08',b'\x05',b'\x06',b'\x07',b'\x08']:
                    try:
                        self.line_user_input=self.line_user_input+'{}'.format(char.decode())
                    except:
                        pass

            print(self.line_user_input)        
            self.line_autocompleted=self.line_user_input    
            last_char=char
            
            
if __name__ == "__main__":
    input_path = AutocompletePathFile('return string (ENTER), Autofill path/file (TAB), Cancel (ESC) Paste (CTRL+V)\nPlease type path: ',APP_PATH,False,True).get_input
    my_path = input_path()
    print("entered", my_path)