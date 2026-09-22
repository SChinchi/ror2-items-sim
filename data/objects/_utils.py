import math
import random


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

def check_roll(chance, inventory):
    """
    Chance roll with taking the player's luck into account.

    Parameters
    ----------
    chance : float
        Chance to succeed. Anything less is a fail. 100 is used for a guaranteed
        roll.
    inventory : Inventory
        The player's inventory.

    Returns
    -------
    bool
        Whether the roll was successful.

    Notes
    -----
    An implementation or `RoR2.Util.CheckRoll`.
    """
    if chance <= 0:
        return False
    luck = inventory.luck
    integer_luck = math.ceil(abs(luck))
    roll = random.randint(0, 100)
    for _ in range(integer_luck):
        new_roll = random.randint(0, 100)
        roll = min(roll, new_roll) if luck > 0 else max(roll, new_roll)
    return roll <= chance
