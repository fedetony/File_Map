# -*- coding: utf-8 -*-
import inquirer

import os
import sys
import glob as gb
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

class AutocompletePathFile:
    def __init__(self, prompt,base_path=APP_PATH,absolute_path=True,verbose=True,inquire=False):
        self.prompt = prompt
        self.line_user_input=''
        self.line_autocompleted=""
        self.autocomplete_options=[]
        self.base_path=base_path
        self.absolute_path=absolute_path
        self.verbose=verbose
        self.options=''
        self.inquire=inquire
        self.limit_for_inquire=-11 # limit the list length.. else is not nice
        self.limit_for_not_verbose=20
        if self.prompt:
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

    def do_inquire(self,a_path_file,list_auto,limit_count=4):
        """Use PyInquire to get the path

        Args:
            a_path_file (str): file for path
            list_auto (list): list of options to autofill

        Returns:
            str: Autofilled until exit.
        """
        comp_list=[]
        while True:
            fill_add2,_=self.get_commontxt_optionlist(list_auto)
            for path in list_auto:
                comp_list.append(path.replace(fill_add2,''))
            fill_add,comp_list=self.get_commontxt_optionlist(comp_list)
            # print(a_path_file,'-->>',fill_add,"=?????=",fill_add2)  
            if fill_add == '':
                end_path=fill_add2
            else:
                end_path=a_path_file+fill_add
            choices=[]
            ini_letters=self.get_initial_letters(comp_list)
            opt_txt=[]
            opt_count=[]
            for ini_l in ini_letters:
                the_name=''
                count=0
                for ccc in comp_list:
                    if ccc[:1] == ini_l:
                        if the_name =='':
                            the_name=ccc
                        else:   
                            if count <limit_count: 
                                the_name=the_name+', '+ccc
                            elif count == limit_count:
                                the_name=the_name+', ...' 
                        count=count+1    
                opt_count.append(count)
                opt_txt.append(the_name)
            choices.append(("-> Exit",':'))
            for (ini_l,ntxt,count) in zip(ini_letters,opt_txt,opt_count):
                choices.append((f"{ini_l}({count}): {ntxt}",f"{ini_l}"))

            questions = [
                        inquirer.List(
                            "letter",
                            message=f"Options for {end_path}",
                            choices=choices,
                            carousel=False,
                        )]
            # os.system('cls' if os.name == 'nt' else 'clear')
            answers = inquirer.prompt(questions)
            if answers['letter']==':':
                return end_path
            for (ini_l,ntxt,count) in zip(ini_letters,opt_txt,opt_count):
                if answers['letter']==ini_l and count != 1:
                    end_path=end_path+answers['letter']
                    return end_path
                    print("Here---->",a_path_file,end_path)
                    list_auto=self._get_possible_path_list(end_path)
                    break
                elif answers['letter']==ini_l and count == 1:
                    end_path=end_path+ntxt
                    return end_path
            
            
            
    
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
        self.options=''
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
            if self.inquire and len(list_auto)<self.limit_for_inquire or self.inquire and self.limit_for_inquire<0:
                return self.do_inquire(a_path_file,list_auto)
            comp_list=[]
            fill_add2,_=self.get_commontxt_optionlist(list_auto)
            for path in list_auto:
                comp_list.append(path.replace(fill_add2,''))
            fill_add,comp_list=self.get_commontxt_optionlist(comp_list)
            # print(a_path_file,'-->>',fill_add,"=?????=",fill_add2)  
            if fill_add == '':
                if len(fill_add2)<len(a_path_file):
                    end_path=a_path_file
                else:
                    end_path=fill_add2
            else:
                end_path=a_path_file+fill_add
            if self.verbose:
                self.options=f"[{len(comp_list)}] Options: {end_path}+{comp_list}"
                self.options=self.cut_string_to_size(self.options,333)
                
            else:
                if len(comp_list)<self.limit_for_not_verbose:
                    self.options=f"[{len(comp_list)}options]+{comp_list}"#-->{fill_add}<-{fill_add2} got {a_path_file}"
                else:
                    self.options=f"[{len(comp_list)} options starting with {self.get_initial_letters(comp_list)}]"#-->{fill_add}<-{fill_add2} got {a_path_file}"
                self.options=self.cut_string_to_size(self.options,333)
            return end_path
        return a_path_file
    
    @staticmethod
    def get_initial_letters(comp_list):
        ini_letters=[]    
        for ccc in comp_list:
            if ccc[:1] not in ini_letters:
                ini_letters.append(ccc[:1])
        return ini_letters

    @staticmethod
    def cut_string_to_size(txt:str,size:int)->str:
        if len(txt)>size:
            aaa=int(size/2)-3
            bbb=int(size/2)-1
            sss=txt[:aaa]+' ... '+txt[-bbb:]
            return sss
        return txt

    def handle_key(self,last_key,key)->str:
        """Maps a key to a string for special characters ater getch
            Some characters map with a sequence.
        Args:
            last_key (char): last value
            key (char): ASCII value

        Returns:
            str: key pressed string
        """
        if not key:
            return '' 
        if not last_key:
            last_key=' '
        if os.name == 'nt':
            if ord(key) == 13: # enter
                return 'enter'    
            elif ord(last_key) == 0 and ord(key) == 59: # F1
                return 'F1'
            elif ord(last_key) == 0 and ord(key) == 60: # F2
                return 'F2'
            elif ord(last_key) == 0 and ord(key) == 61: # F3
                return 'F3'
            elif ord(last_key) == 0 and ord(key) == 62: 
                return 'F4'
            elif ord(last_key) == 0 and ord(key) == 63: 
                return 'F5'
            elif ord(last_key) == 0 and ord(key) == 64: 
                return 'F6'
            elif ord(last_key) == 0 and ord(key) == 65: 
                return 'F7'
            elif ord(last_key) == 0 and ord(key) == 66: 
                return 'F8'
            elif ord(last_key) == 0 and ord(key) == 67: 
                return 'F9'
            elif ord(last_key) == 0 and ord(key) == 68: 
                return 'F10'
            elif ord(last_key) == 224 and ord(key) == 133: 
                return 'F11'
            elif ord(last_key) == 224 and ord(key) == 134: 
                return 'F12'
            
            elif ord(last_key) == 224 and ord(key) == 72: 
                return 'arrow'+'up'
            elif ord(last_key) == 224 and ord(key) == 80: 
                return 'arrow'+'down'
            elif ord(last_key) == 224 and ord(key) == 77: 
                return 'arrow'+'right'
            elif ord(last_key) == 224 and ord(key) == 75: 
                return 'arrow'+'left'
            elif ord(last_key) == 224 and ord(key) == 141:
                return 'cntr+'+'arrow'+'up'
            elif ord(last_key) == 224 and ord(key) == 145:
                return 'cntr+'+'arrow'+'down'
            elif ord(last_key) == 224 and ord(key) == 116:
                return 'cntr+'+'arrow'+'right'
            elif ord(last_key) == 224 and ord(key) == 115:
                return 'cntr+'+'arrow'+'left'
            elif ord(last_key) == 224 and ord(key) == 73:
                return 'page'+'up'
            elif ord(last_key) == 224 and ord(key) == 81:
                return 'page'+'down'
            elif ord(last_key) == 224 and ord(key) == 83:
                return 'delete'
            elif ord(last_key) == 224 and ord(key) == 79:
                return 'end'
            elif ord(last_key) == 224 and ord(key) == 71:
                return 'home'
            # elif ord(last_key) == 224 and ord(key) == 126:
            #     return 'insert'
            elif ord(key) == 8:
                return 'backspace'
            elif ord(key) == 27: # esc
                return 'esc'
            elif ord(key) == 9: # tab
                return 'tab'
            elif ord(key) in range(1,27):
                return 'cntr+'+chr(96+ord(key))
            elif ord(key) in range(32,127): # printable characters
                return key.decode()
            else:
                try:
                    char=chr(ord(key))
                    return char.decode()
                    # return chr(ord(key))
                except:
                    return key
                    
        else:
            if ord(key) == 13: # enter
                return 'enter'
            
            elif ord(last_key) == 79 and ord(key) == 80: # F1
                return 'F1'
            elif ord(last_key) == 79 and ord(key) == 81: # F2
                return 'F2'
            elif ord(last_key) == 79 and ord(key) == 82: # F3
                return 'F3'
            elif ord(last_key) == 79 and ord(key) == 83: 
                return 'F4'
            # elif ord(last_key) == 53 and ord(key) == 126: 
            #     return 'F5'
            elif ord(last_key) == 55 and ord(key) == 126: 
                return 'F6'
            elif ord(last_key) == 56 and ord(key) == 126: 
                return 'F7'
            elif ord(last_key) == 57 and ord(key) == 126: 
                return 'F8'
            elif ord(last_key) == 48 and ord(key) == 126: 
                return 'F9'
            elif ord(last_key) == 91 and ord(key) == 65: 
                return 'arrow'+'up'
            elif ord(last_key) == 91 and ord(key) == 66: 
                return 'arrow'+'down'
            elif ord(last_key) == 91 and ord(key) == 67: 
                return 'arrow'+'right'
            elif ord(last_key) == 91 and ord(key) == 68: 
                return 'arrow'+'left'
            elif ord(last_key) == 53 and ord(key) == 65:
                return 'cntr+'+'arrow'+'up'
            elif ord(last_key) == 53 and ord(key) == 66:
                return 'cntr+'+'arrow'+'down'
            elif ord(last_key) == 53 and ord(key) == 67:
                return 'cntr+'+'arrow'+'right'
            elif ord(last_key) == 53 and ord(key) == 68:
                return 'cntr+'+'arrow'+'left'
            elif ord(last_key) == 53 and ord(key) == 126:
                return 'page'+'up'
            elif ord(last_key) == 54 and ord(key) == 126:
                return 'page'+'down'
            elif ord(last_key) == 51 and ord(key) == 126:
                return 'delete'
            elif ord(last_key) == 91 and ord(key) == 70:
                return 'end'
            elif ord(last_key) == 91 and ord(key) == 72:
                return 'home'
            # elif ord(last_key) == 50 and ord(key) == 126:
            #     return 'insert'
            elif ord(key) == 127:
                return 'backspace'
            elif ord(key) == 27: # esc
                return 'esc'
            elif ord(key) == 9: # tab
                return 'tab'
            elif ord(key) in range(1,27):
                return 'cntr+'+chr(96+ord(key))
            elif ord(key) in range(32,127): # printable characters
                return key
            else:
                try:
                    return chr(ord(key))
                except:
                    return ''

    def is_special_character(self,last_key,key)->bool:
        """Check if is a pecial character

        Args:
            last_key (char): last value
            key (char): ASCII value

        Returns:
            bool: _description_
        """
        if os.name=='nt' and ord(key) in [0,224,13,8,27,9]+list(range(1,27)):
            return True
        # if not os.name=='nt' and ord(last_key) not in [79,54,55,56,57,48,91] and ord(key) in [79,54,55,56,57,48,91]+list(range(1,27)):
        #     return True
        key_handle=self.handle_key(last_key,key)
        if key_handle:
            if len(key_handle)>1: # words with more than 1 character
                return True
        return False

        

    def get_input(self):
        """Get user input.

        Returns:
            str: User input
        """
        last_char=' '
        pos=0
        lenght=0
        lenoptions=0
        while True:
            char = getch()
            if self.verbose:
                os.system('cls' if os.name == 'nt' else 'clear')
            else:
                if lenoptions>0:
                    for _ in range(1,lenoptions):
                        sys.stdout.write("\b ")
                        sys.stdout.flush()
                        sys.stdout.write("\b")
                    sys.stdout.write("\r")
                    sys.stdout.flush()
                    sys.stdout.write(self.line_user_input)
                    sys.stdout.flush()
                    lenoptions=0
            #print('Char: ',chr(ord(char)),' ord:',ord(char), ' last->ord:',ord(last_char),self.handle_key(last_char,char))
            key_handle=self.handle_key(last_char,char)
            if self.verbose:
                print(self.prompt)
            if  key_handle=='enter': #enter char in [b'\r', b'\n', '\r', '\n'] or
                if not self.verbose:
                    sys.stdout.write("\r")
                    sys.stdout.flush()
                return self.line_autocompleted
            if  key_handle=='tab': #tab char in [ b'\t','\t'] or
                inlen=len(self.line_user_input)
                self.line_user_input=self.autocomplete_path(self.line_user_input)
                if not self.verbose:
                    sys.stdout.write("\b"*inlen+self.line_user_input)
                    sys.stdout.flush()
                    lenoptions=len(self.options)
                    if lenoptions>0:
                        sys.stdout.write(self.options)
                        sys.stdout.flush()
                last_char=' '    
                char = None 
            elif  key_handle=='esc': # esc char in [ b'\x1b','\x1b'] or
                print(key_handle)
                last_char=' '
                return None
            elif key_handle=='cntr+c': # cntr + c char in [ b'\x03','\x03'] or 
                print(key_handle)
                pass
            elif  key_handle=='cntr+v': # cntr + v char in [ b'\x18','\x18'] or
                # paste clipboard
                pass
            elif key_handle=='backspace': #Back Space char in [ b'\x08','\x08'] or 
                lenght=len(self.line_user_input)
                self.line_user_input=self.line_user_input[:lenght-1]
                lenght=len(self.line_user_input)
                if not self.verbose:
                    sys.stdout.write("\b ")
                    sys.stdout.flush()
                    sys.stdout.write("\b")
                last_char=' '
            else: 
                pos=pos+1
                if char and not self.is_special_character(last_char,char):
                    try:
                        self.line_user_input=self.line_user_input+'{}'.format(char.decode())
                        if not self.verbose:
                            sys.stdout.write('{}'.format(char.decode()))
                    except:
                        self.line_user_input=self.line_user_input+'{}'.format(char)
                        if not self.verbose:
                            sys.stdout.write('{}'.format(char))
                        pass
                    if not self.verbose:
                        sys.stdout.flush()
            if self.verbose:        
                print(self.line_user_input)        
            self.line_autocompleted=self.line_user_input    
            last_char=char
            
            
if __name__ == "__main__":
    AC=AutocompletePathFile('return string (ENTER), Autofill path/file (TAB), Cancel (ESC) Paste (CTRL+V)\nPlease type path: ',APP_PATH,False,verbose=False)
    input_path = AC.get_input
    my_path = input_path()
    print("User input:", my_path)
    def test_handle():
        last_char=' '
        while True:
            print("Map keys: press enter to exit")
            char = getch()
            os.system('cls' if os.name == 'nt' else 'clear')
            key_handle=AC.handle_key(last_char,char)
            print('Char: ',chr(ord(char)),' last->ord:',ord(last_char),' ord:',ord(char), 'keyhandle=',key_handle)
            print(key_handle," Special :",AC.is_special_character(last_char,char))
            if char in [b'\r', b'\n', '\r', '\n'] or key_handle=='enter': #enter
                return
            last_char=char
    test_handle()