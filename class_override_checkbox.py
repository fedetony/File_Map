from readchar import key

from inquirer import errors
from inquirer.render.console._other import GLOBAL_OTHER_CHOICE
from inquirer.render.console.base import MAX_OPTIONS_DISPLAYED_AT_ONCE
from inquirer.render.console.base import BaseConsoleRender
from inquirer.render.console.base import half_options


from inquirer.render.console._list import List
from inquirer import errors
from class_autocomplete_input import AutocompletePathFile

add_ansi=AutocompletePathFile.add_ansi 

CONTRACT_KEYWORD = '***Contract***'
EXPAND_KEYWORD = '***Expand***'

def process_input_list(self, pressed):
        question = self.question
        # self.current=question.default_pos
        if pressed == key.UP:
            if question.carousel and self.current == 0:
                self.current = len(question.choices) - 1
            else:
                self.current = max(0, self.current - 1)
            question.default_pos=self.current
            return
        if pressed == key.DOWN:
            if question.carousel and self.current == len(question.choices) - 1:
                self.current = 0
            else:
                self.current = min(len(self.question.choices) - 1, self.current + 1)
            question.default_pos=self.current
            return
        elif pressed == key.LEFT:
            question.default_pos=self.current
            value = self.question.choices[self.current]
            tag=getattr(value, "tag", value)
            if '─<' in tag:
                result = CONTRACT_KEYWORD + getattr(value, "value", value)
                raise errors.EndOfInput(result)
        elif pressed == key.RIGHT:
            question.default_pos=self.current
            value = self.question.choices[self.current]
            tag=getattr(value, "tag", value)
            if '─>' in tag:
                result=EXPAND_KEYWORD+getattr(value, "value", value)
                raise errors.EndOfInput(result)
        if pressed == key.ENTER:
            question.default_pos=self.current
            value = self.question.choices[self.current]
            if value == GLOBAL_OTHER_CHOICE:
                value = self.other_input()
                if not value:
                    # Clear the print inquirer.text made, since the user didn't enter anything
                    print(self.terminal.move_up + self.terminal.clear_eol, end="")
                    return
            raise errors.EndOfInput(getattr(value, "value", value))
        elif pressed == key.ESC:
            result = ''    
            raise errors.EndOfInput(result)
        if pressed == key.CTRL_C:
            raise KeyboardInterrupt()

List.process_input=process_input_list

MENU_PROCESS_SELECTOR={
    '__mode__': None, # mode for steps
    'R':'***Remove***', # Remove
    'M':'***Move***', # Move
    'F':'***NewFolder***', # New Folder
    'N':'***Rename***', # Rename
    'C':'***Copy***', # Copy
    'X':'***Cut***', # Cut
    'V':'***Paste***', # Paste
    'E':'***Reveal***', # Reveal in Explorer
}

class Checkbox(BaseConsoleRender):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_locked_in_default = False
        self.locked = self.question.locked or []
        self.selection = [k for (k, v) in enumerate(self.question.choices) if v in self.default_choices()]
        try:
            self.current = self.question.default_pos
        except (AttributeError,ValueError,TypeError):    
            self.current = 0
        #set process mode
        self.m_s=MENU_PROCESS_SELECTOR.copy()
        try:
            self.m_s['__mode__'] = self.question.process_mode
        except (AttributeError,ValueError,TypeError):    
            self.m_s['__mode__'] = None
        try:
            self.process_list = self.question.process_list
        except (AttributeError,ValueError,TypeError):    
            self.process_list = [] # list of (index_from,a_process,index_to)
        
    def get_hint(self):
        try:
            hint = self.question.hints[self.question.choices[self.current]]
            return hint or ""
        except KeyError:
            return ""

    def default_choices(self):
        default = self.question.default or []
        if self.include_locked_in_default:
            return default + self.locked
        return default

    @property
    def is_long(self):
        choices = self.question.choices or []
        return len(choices) >= MAX_OPTIONS_DISPLAYED_AT_ONCE

    def get_options(self):
        choices = self.question.choices or []
        if self.is_long:
            cmin = 0
            cmax = MAX_OPTIONS_DISPLAYED_AT_ONCE

            if half_options < self.current < len(choices) - half_options:
                cmin += self.current - half_options
                cmax += self.current - half_options
            elif self.current >= len(choices) - half_options:
                cmin += len(choices) - MAX_OPTIONS_DISPLAYED_AT_ONCE
                cmax += len(choices)

            cchoices = choices[cmin:cmax]
        else:
            cchoices = choices

        ending_milestone = max(len(choices) - half_options, half_options + 1)
        is_in_beginning = self.current <= half_options
        is_in_middle = half_options < self.current < ending_milestone
        is_in_end = self.current >= ending_milestone
        for index, choice in enumerate(cchoices):
            if (
                (is_in_middle and self.current - half_options + index in self.selection)
                or (is_in_beginning and index in self.selection)
                or (is_in_end and index + max(len(choices) - MAX_OPTIONS_DISPLAYED_AT_ONCE, 0) in self.selection)
            ):  # noqa
                symbol = self.theme.Checkbox.selected_icon
                color = self.theme.Checkbox.selected_color
            else:
                symbol = self.theme.Checkbox.unselected_icon
                color = self.theme.Checkbox.unselected_color

            selector = " "
            end_index = ending_milestone + index - half_options - 1
            if (
                (is_in_middle and index == half_options)
                or (is_in_beginning and index == self.current)
                or (is_in_end and end_index == self.current)
            ):
                selector = self.theme.Checkbox.selection_icon
                color = self.theme.Checkbox.selection_color

            if choice in self.locked:
                color = self.theme.Checkbox.locked_option_color

            if choice == GLOBAL_OTHER_CHOICE:
                symbol = "+"

            for proc in self.process_list:
                (index_from,a_process,index_to) = proc
                if index in [index_from]:
                    symbol = a_process + '›' + symbol
                elif index in [index_to]:
                    symbol = a_process + '‹' + symbol
                    
            yield choice, selector + " " + symbol, color

    def process_input(self, pressed):
        question = self.question     
        # initial_selection=question.default
        is_current_choice_locked = question.choices[self.current] in self.locked
        if pressed == key.UP:
            if question.carousel and self.current == 0:
                self.current = len(question.choices) - 1
            else:
                self.current = max(0, self.current - 1)
            return
        elif pressed == key.DOWN:
            if question.carousel and self.current == len(question.choices) - 1:
                self.current = 0
            else:
                self.current = min(len(self.question.choices) - 1, self.current + 1)
            return
        elif pressed == key.SPACE or pressed == key.CTRL_I:
            if not is_current_choice_locked:
                if self.question.choices[self.current] == GLOBAL_OTHER_CHOICE:
                    self.other_input()
                elif self.current in self.selection:
                    self.selection.remove(self.current)
                else:
                    self.selection.append(self.current)
        elif pressed == key.LEFT:
            # if self.current in self.selection:
                # self.selection.remove(self.current)
            # if not is_current_choice_locked:
                value = self.question.choices[self.current]
                tag=getattr(value, "tag", value)
                if '─<' in tag:
                    result = []
                    for x in self.selection:
                        value = self.question.choices[x]
                        result.append(getattr(value, "value", value))
                    value = self.question.choices[self.current]
                    result.append(CONTRACT_KEYWORD+str(getattr(value, "value", value)))
                    raise errors.EndOfInput(result)
        elif pressed == key.RIGHT:
            # if self.current not in self.selection:
                # self.selection.append(self.current)
            # if not is_current_choice_locked:
                value = self.question.choices[self.current]
                tag=getattr(value, "tag", value)
                if '─>' in tag:
                    result = []
                    for x in self.selection:
                        value = self.question.choices[x]
                        result.append(getattr(value, "value", value))
                    value = self.question.choices[self.current]
                    result.append(EXPAND_KEYWORD+str(getattr(value, "value", value)))
                    raise errors.EndOfInput(result)
        elif pressed == key.CTRL_A:
            self.selection = [i for i in range(len(self.question.choices))]
        elif pressed == key.CTRL_R:
            self.selection = []
        elif pressed == key.CTRL_T:
            before=self.selection
            self.selection = []
            for i in range(len(self.question.choices)):
                if i not in before and not self.question.choices[i] in self.locked:
                    self.selection.append(i)
                if i in before and self.question.choices[i] in self.locked:
                    self.selection.append(i)    
        elif pressed == key.ESC:
            result = []    
            raise errors.EndOfInput(result)    
        elif pressed == key.ENTER:
            result = []
            for x in self.selection:
                value = self.question.choices[x]
                result.append(getattr(value, "value", value))
            # if initial_selection:
            #     for ini_sel in initial_selection:
            #         if ini_sel not in self.selection:    
            #             result.append(ini_sel)
            raise errors.EndOfInput(result)
        elif pressed == key.CTRL_C:
            raise KeyboardInterrupt()
        elif pressed.upper() in list(self.m_s.keys()) and self.m_s['__mode__']=='all':
            self.process_list.append((self.current,pressed.upper(),None))
        elif pressed == key.DELETE:
            rem_p=[]
            for proc in self.process_list:
                if self.current not in proc[0]:
                    rem_p.append[proc]
            self.process_list=rem_p         

    def other_input(self):
        other = super().other_input()

        # Clear the print that inquirer.text made
        print(self.terminal.move_up + self.terminal.clear_eol, end="")

        if not other:
            return

        index = self.question.add_choice(other)
        if index not in self.selection:
            self.selection.append(index)
