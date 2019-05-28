from enum import Enum

class Side(Enum):
    BID = 1
    ASK = 2

class OType(Enum):
    ADD = 1
    CANCEL = 2
    MODIFY = 3

    