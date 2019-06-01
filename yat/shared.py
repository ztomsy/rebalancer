from enum import Enum


class Side(Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class OType(Enum):
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'


class TIFType(Enum):
    GTC = 'GTC'
    IOC = 'IOC'
