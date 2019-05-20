import math

def rounded_to_precision(number: float, precision: int = 0) -> float:
    """
    Given a number, round it to the nearest tick. Very useful for sussing float error
    out of numbers: e.g. rounded_to_precision(401.46, 2) -> 401.46, whereas processing is
    normally with floats would give you 401.46000000000004.
    Use this after adding/subtracting/multiplying numbers.

    >>> rounded_to_precision(401.4600001000001002455, 8)
    401.4600001
    >>> rounded_to_precision(401.4650001, 2)
    401.46
    >>> rounded_to_precision(401.01200000004, 3)
    401.012

    """
    if precision > 0:
        decimal_precision = math.pow(10, precision)
        return math.trunc(number * decimal_precision) / decimal_precision
    else:
        return float(('%d'.format(number)))
