# class_enums_definitions.py

from enum import Enum, auto

class SelectionMode(Enum):
    SINGLE = auto()
    MULTI = auto()

class CheckBoxMode(Enum):
    CHECKBOX = auto()
    NO_CHECKBOX = auto()

class SelectionByTypeMode(Enum):
    ANY = auto()
    FILES_ONLY = auto()
    DIRS_ONLY = auto()
    FILES_DIRS_ONLY = auto()
    DATABASE = auto()
    MAP = auto()
    ROOT = auto()