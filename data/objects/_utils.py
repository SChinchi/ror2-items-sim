import math


def round_value(number, ndigits=6):
    """
    Round function which ignores infinities.

    Parameters
    ----------
    number : float
        The number to round.
    ndigits : int, optional
        The precision to round to.

    Returns
    -------
    float
    """
    if number == -math.inf or number == math.inf:
        return number
    return round(number, ndigits)
