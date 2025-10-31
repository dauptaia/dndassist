from typing import Tuple
from random import randint
from dndassist.storyprint import print_r, print_l

def scan_dice(dice: str) -> Tuple[int, int, int]:
    """return the scan of a dice

    1D20+4 => 1, 20, 4"""
    dice_ = dice
    mod = 0
    if "+" in dice:
        mod = int(dice.split("+")[-1])
        dice_ = dice.split("+")[0]
    nb = int(dice_.split("d")[0])
    faces = int(dice_.split("d")[1])
    return nb, faces, mod


def max_dice(dice: str) -> int:
    nb, faces, mod = scan_dice(dice)
    return nb * faces + mod


def _ask_advantage()-> int:
    done = False
    while not done:
        result = int(input(f"Enter abritrary advantage : +1 or -1"))
        if result in [-1,1,0]:
            done = True
    return result

def _ask_dice(dice:str, min_:int, max_:int, mod:int)-> int:
    done = False
    while not done:
        result = int(input(f"Enter dice __{dice}__ result:")) + mod
        if result >= min_ and result <= max_:
            done = True
    return result


def rolldice(dice: str, autoroll=False, advantage: int = 0) -> Tuple[int, float]:
    nb, faces, mod = scan_dice(dice)
    min_ = nb
    max_ = nb * faces
    if not autoroll:
        advantage = _ask_advantage()
    if autoroll:
        result = randint(min_, max_)
        if advantage <= -1:
            for i in range(-advantage):
                result = min(randint(min_, max_), result)
        if advantage >= 1:
            for i in range(advantage):
                result = max(randint(min_, max_), result)
    else:
        result = _ask_dice(dice, min_, max_, mod)
        if advantage <= 1:
            for i in range(-advantage):
                result = min(_ask_dice(dice, min_, max_, mod), result)
        if advantage >= 1:
            for i in range(advantage):
                result = max(_ask_dice(dice, min_, max_, mod), result)

    normed = (result - min_) / (max_ - min_)
    result += mod
    if autoroll:
        print_r(f".  Result of {dice}: __{result}__")
    else:
        print_l(f".  Result of {dice}: __{result}__")
    
    return result, normed
