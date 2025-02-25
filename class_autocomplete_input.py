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
        self.char_sequence=[]
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

    @staticmethod
    def list_compare(list1:list,list2:list)->bool:
        """Compares two lists returns True if they are the same

        Args:
            list1 (list): list 1
            list2 (list): list 2

        Returns:
            bool: True if order and size are the same.
        """
        if not isinstance(list1,list) or not isinstance(list2,list):
             return False
        if len(list1)!=len(list2):
            return False
        for l1,l2 in zip(list1,list2):
            if l1!=l2:
                return False
        return True
    
    def _get_key_comparison(self,char_sequence,opt1:list,opt2:list=None,result:str=None):
        """Compares options to char_sequence: if are the same then returns (result,reseted char sequence)
            if opt2 the same then returns (result,reseted char sequence)
            else (None , same char_sequence)
        Args:
            char_sequence (_type_): char sequence
            opt1 (list): option to compare
            opt2 (list, optional): Second option. Defaults to None.
            result (str, optional): Value. Defaults to ''.

        Returns:
            tuple: (result,char_sequence)
        """
        if self.list_compare(char_sequence,opt1):
            return result,[]
        if self.list_compare(char_sequence,opt2):
            return result,[]
        return (None, char_sequence)
    
    def _handle_key_linux(self,key):
        """Maps a key to a string for any character looking into sequences.
            After getch, a sequence is emmitted for special characters.
            Some characters map with a sequence.
        Args:
            key (bytes): ASCII value

        Returns:
            str: key pressed string, None
        """
        # Linux
        if len(self.char_sequence)>=6:
            self.char_sequence=[]
        self.char_sequence.append(ord(key))
        if isinstance(key,bytes):
            enc_key=key
        if isinstance(key,str):
            enc_key=key.encode('utf-8')
            if enc_key == b'':
                    self.char_sequence=[]
                    return None
        if len(self.char_sequence)==6:
            if self.list_compare(self.char_sequence,[27,91,49,59,53,65]):
                    self.char_sequence=[]
                    return 'cntr+'+'arrow'+'up' # 27-> 91 -> 49 -> 59 -> 53 -> 65
            elif self.list_compare(self.char_sequence,[27,91,49,59,53,66]):
                    self.char_sequence=[]
                    return 'cntr+'+'arrow'+'down' # 27-> 91 -> 49 -> 59 -> 53 -> 66
            elif self.list_compare(self.char_sequence,[27,91,49,59,53,67]):
                    self.char_sequence=[]
                    return 'cntr+'+'arrow'+'right' # 27-> 91 -> 49 -> 59 -> 53 -> 67
            elif self.list_compare(self.char_sequence,[27,91,49,59,53,68]):
                    self.char_sequence=[]
                    return 'cntr+'+'arrow'+'left' # 27-> 91 -> 49 -> 59 -> 53 -> 68
            else:
                    out=self.char_sequence[5]
                    self.char_sequence=[]
                    return chr(out) # 27-> 91 -> 49 -> 59 -> 53 -> X
        elif len(self.char_sequence)==5:
            if self.list_compare(self.char_sequence,[27,91,49,53,126]): 
                    self.char_sequence=[]
                    return 'F5' # 27-> 91 ->49 ->53 ->126
            elif self.list_compare(self.char_sequence,[27,91,49,55,126]): 
                    self.char_sequence=[]
                    return 'F6' # 27-> 91 ->49 ->55 ->126
            elif self.list_compare(self.char_sequence,[27,91,49,56,126]): 
                    self.char_sequence=[]
                    return 'F7' # 27-> 91 ->49 ->56 ->126
            elif self.list_compare(self.char_sequence,[27,91,49,57,126]): 
                    self.char_sequence=[]
                    return 'F8' # 27-> 91 ->49 ->57 ->126
                
            elif self.list_compare(self.char_sequence,[27,91,50,48,126]): 
                    self.char_sequence=[]
                    return 'F9' # 27-> 91 ->50 ->48 ->126
            elif self.list_compare(self.char_sequence,[27,91,50,49,126]): 
                    self.char_sequence=[]
                    return 'F10' # 27-> 91 ->50 ->49 ->126 # os uses this key
            elif self.list_compare(self.char_sequence,[27,91,50,51,126]): 
                    self.char_sequence=[]
                    return 'F11' # os uses this key ?????? Assumed
            elif self.list_compare(self.char_sequence,[27,91,50,52,126]): 
                    self.char_sequence=[]
                    return 'F12' # 27-> 91 ->50 ->52 ->126
            # elif self.char_sequence[4] not in [53]:
            #         out=self.char_sequence[4]
            #         self.char_sequence=[]
            #         return chr(out)
        
        elif len(self.char_sequence)==4:
            if self.list_compare(self.char_sequence,[27,91,53,126]):
                    self.char_sequence=[]
                    return 'page'+'up' # 27-> 91 -> 53 -> 126
            elif self.list_compare(self.char_sequence,[27,91,54,126]):
                    self.char_sequence=[]
                    return 'page'+'down' # 27-> 91 -> 54 -> 126
            elif self.list_compare(self.char_sequence,[27,91,51,126]):
                    self.char_sequence=[]
                    return 'delete' # 27-> 91 -> 51 -> 126  
            elif self.list_compare(self.char_sequence,[27,91,50,126]):
                    self.char_sequence=[]
                    return 'insert' # 27-> 91 -> 50 -> 126
            # elif self.char_sequence[2] not in [49,50,51] and self.char_sequence[3] not in [48,49,50,51,52,53,55,56,57]:
            #         out=self.char_sequence[3]
            #         self.char_sequence=[]
            #         return chr(out)
        
        elif len(self.char_sequence)==3:
            if self.list_compare(self.char_sequence,[27,79,80]): 
                    self.char_sequence=[]
                    return 'F1' # 27-> 79 -> 80
            elif self.list_compare(self.char_sequence,[27,79,81]): 
                    self.char_sequence=[]
                    return 'F2' # 27-> 79 -> 81
            elif self.list_compare(self.char_sequence,[27,79,82]): 
                    self.char_sequence=[]
                    return 'F3' # 27-> 79 -> 82
            elif self.list_compare(self.char_sequence,[27,79,83]): 
                    self.char_sequence=[]
                    return 'F4' # 27-> 79 -> 83
            elif self.list_compare(self.char_sequence,[27,91,65]): 
                    self.char_sequence=[]
                    return 'arrow'+'up' # 27-> 91 -> 65
            elif self.list_compare(self.char_sequence,[27,91,66]): 
                    self.char_sequence=[]
                    return 'arrow'+'down' # 27-> 91 -> 66
            elif self.list_compare(self.char_sequence,[27,91,67]): 
                    self.char_sequence=[]
                    return 'arrow'+'right' # 27-> 91 -> 67
            elif self.list_compare(self.char_sequence,[27,91,68]): 
                    self.char_sequence=[]
                    return 'arrow'+'left' # 27-> 91 -> 68
            elif self.list_compare(self.char_sequence,[27,91,70]):
                    self.char_sequence=[]
                    return 'end' # 27-> 91 -> 70
            elif self.list_compare(self.char_sequence,[27,91,72]):
                    self.char_sequence=[]
                    return 'home' # 27-> 91 -> 72
            # elif self.char_sequence[1] == 91 and self.char_sequence[2] not in [49,50,51,52,53,54]:
            #         self.char_sequence=[]
            #         return chr(self.char_sequence[2])
        
        elif len(self.char_sequence)==2:
            if self.char_sequence[0] == 27 and self.char_sequence[1] not in [79,91]: # esc
                self.char_sequence=[]
                return 'esc'
            # elif self.char_sequence[1] not in [79,91]:
            #     out=self.char_sequence[1]
            #     self.char_sequence=[]
            #     return chr(out)
            
        elif self.list_compare(self.char_sequence,[13]):
                self.char_sequence=[]
                return 'enter'
        elif self.list_compare(self.char_sequence,[127]):
                self.char_sequence=[]
                return 'backspace'
        elif self.list_compare(self.char_sequence,[9]):
                self.char_sequence=[]
                return 'tab'
        elif len(self.char_sequence)==1:
            if self.char_sequence[0] in range(1,27):
                return 'cntr+'+chr(96+self.char_sequence.pop(0))
            elif self.char_sequence[0] in range(32,127): # printable characters
                return chr(self.char_sequence.pop(0))
            elif self.char_sequence[0] not in [27]:
                return chr(self.char_sequence.pop(0))
        
        else:
            try:
                return chr(ord(key))
            except:
                return ''

    def _handle_key_windows(self,key):
        """Maps a key to a string for any character looking into sequences.
            After getch, a sequence is emmitted for special characters.
            Some characters map with a sequence.
        Args:
            key (bytes): ASCII value

        Returns:
            str: key pressed string, None
        """
        if len(self.char_sequence)>2:
            self.char_sequence=[]
        self.char_sequence.append(ord(key))
        if isinstance(key,str):
            enc_key=key.encode('utf-8')
        if isinstance(key,bytes):
            enc_key=key
        
        if len(self.char_sequence)==2:
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,59],[224,59],result='F1') # 0 -> 59
            if comp_result: return comp_result 
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,60],[224,60],result='F2') # 0 -> 60
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,61],[224,61],result='F3') # 0 -> 61
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,62],[224,62],result='F4') # 0 -> 62
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,63],[224,63],result='F5') # 0 -> 63
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,64],[224,64],result='F6') # 0 -> 64
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,65],[224,65],result='F7') # 0 -> 65
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,66],[224,66],result='F8') # 0 -> 66
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,67],[224,67],result='F9') # 0 -> 67
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,68],[224,68],result='F10') # 0 -> 68
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[224,133],[0,133],result='F11') # 224 -> 133
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[224,134],[0,134],result='F12') # 224 -> 134
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,72],[224,72],result='arrow'+'up') # 0 -> 72
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,80],[224,80],result='arrow'+'down') # 0 -> 80
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,77],[224,77],result='arrow'+'right') # 0 -> 77
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,75],[224,75],result='arrow'+'left') # 0 -> 75
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[224,141],[0,141],result='cntr+'+'arrow'+'up') # 224 -> 141
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[224,145],[0,145],result='cntr+'+'arrow'+'down') # 224 -> 145
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[224,116],[0,116],result='cntr+'+'arrow'+'right') # 224 -> 116
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[224,115],[0,115],result='cntr+'+'arrow'+'left') # 224 -> 115
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,73],[224,73],result='page'+'up') # 0 -> 73
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,81],[224,81],result='page'+'down') # 0 -> 81
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,83],[224,83],result='delete') # 0 -> 83
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,79],[224,79],result='end') # 0 -> 79
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,71],[224,71],result='home') # 0 -> 71
            if comp_result: return comp_result
            comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[0,82],[224,82],result='insert') # 0 -> 82
            if comp_result: return comp_result
            
            if not comp_result and self.char_sequence[1] not in [224,0]:
                out=self.char_sequence[1]
                self.char_sequence=[]
                return chr(out)
        comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[13], result='enter') # 13  
        if comp_result: return comp_result 
        comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[8],result='backspace') # 8 
        if comp_result: return comp_result
        comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[27],result='esc') # 27
        if comp_result: return comp_result
        comp_result, self.char_sequence = self._get_key_comparison(self.char_sequence,[9],result='tab') # 9
        if comp_result: return comp_result
        elif len(self.char_sequence)==1:
            if self.char_sequence[0] in range(1,27):
                return 'cntr+'+chr(96+self.char_sequence.pop(0))
            elif self.char_sequence[0] in range(32,127): # printable characters
                return chr(self.char_sequence.pop(0))
            elif self.char_sequence[0] not in [0,224]:
                return chr(self.char_sequence.pop(0))
        else:
            try:
                char=chr(ord(key))
                return char.decode()
                # return chr(ord(key))
            except:
                return key
         

    def handle_key(self,key)->str:
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
        # Windows
        if os.name == 'nt':
            return self._handle_key_windows(key)            
        else:
            return self._handle_key_linux(key)
    
    def wait_key_press(self):
        """Returns the key that was pressed and if its special character

        Returns:
            tuple[str,bool]: Key handle, True if special character.
        """
        key_handle=None
        while not key_handle:       
            char = getch()
            key_handle=self.handle_key(char)
        special_character = False
        if len(key_handle)>1: # words with more than 1 character is special character
            special_character = True
        return key_handle, special_character 

    def get_input(self):
        """Get user input.

        Returns:
            str: User input
        """
        pos=0
        lenght=0
        lenoptions=0
        while True:
            key_handle,is_special_character=self.wait_key_press()
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
            # Print prompt
            if self.verbose:
                print(self.prompt)
            if  key_handle=='enter': 
                if not self.verbose:
                    sys.stdout.write("\r")
                    sys.stdout.flush()
                return self.line_autocompleted
            if  key_handle=='tab': 
                inlen=len(self.line_user_input)
                self.line_user_input=self.autocomplete_path(self.line_user_input)
                if not self.verbose:
                    sys.stdout.write("\b"*inlen+self.line_user_input)
                    sys.stdout.flush()
                    lenoptions=len(self.options)
                    if lenoptions>0:
                        sys.stdout.write(self.options)
                        sys.stdout.flush()
                else:
                    print(self.options)  
                key_handle = None 
            elif  key_handle=='esc': 
                return None
            elif key_handle=='cntr+c':
                pass
            elif  key_handle=='cntr+v': 
                # paste clipboard
                pass
            elif key_handle=='backspace': 
                lenght=len(self.line_user_input)
                self.line_user_input=self.line_user_input[:lenght-1]
                lenght=len(self.line_user_input)
                if not self.verbose:
                    sys.stdout.write("\b ")
                    sys.stdout.flush()
                    sys.stdout.write("\b")
            else: 
                pos=pos+1
                if key_handle and not is_special_character:
                    self.line_user_input=self.line_user_input+key_handle
                    if not self.verbose:
                        sys.stdout.write(key_handle)
                        sys.stdout.flush()
            if self.verbose:        
                print(self.line_user_input)        
            self.line_autocompleted=self.line_user_input    
            
            
if __name__ == "__main__":
    AC=AutocompletePathFile('return string (ENTER), Autofill path/file (TAB), Cancel (ESC) Paste (CTRL+V)\nPlease type path: ',APP_PATH,False,verbose=True)
    input_path = AC.get_input
    my_path = input_path()
    print("User input:", my_path)
    def test_handle(): 
        """To see internally the keyboard mapping sequences"""
        while True:
            print("Map keys: press enter to exit")
            char = getch()
            if isinstance(char,str): # linux
                print(type(char),"Here->",char,'str->',str(char),'ord->',ord(char),'encode->',char.encode('utf-8'))
            if isinstance(char,bytes): # windows
                print(type(char),"Here->",char,'str->',str(char),'ord->',ord(char),'encode->',char)
            # os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Sequence before:{AC.char_sequence}")
            key_handle=AC.handle_key(char)
            print(f"Sequence After:{AC.char_sequence}")
            print('Char: ',chr(ord(char)),' ord:',ord(char), 'keyhandle=',key_handle)
            if char in [b'\r', b'\n', '\r', '\n'] or key_handle=='enter': 
                return
    def test_handle2():
        """Teste wait key press"""
        while True:
            print("Map keys: press enter to exit")
            key_handle,is_special_character=AC.wait_key_press()
            print('keyhandle=',key_handle, 'is_special_character:',is_special_character)
            if key_handle=='enter': #enter
                return
    test_handle2()
