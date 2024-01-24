from enum import Enum

class StrEnum(str, Enum):
    pass


class Modifier(Enum):
    normal = -1
    bright = 0
    pale = 1
    fading = 2


class Type(Enum):
    normal = 0
    unstable = 1
    sinister = 2
    tainted = 3
    hungry = 4
    pure = 5
