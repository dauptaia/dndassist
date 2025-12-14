
from typing import Tuple, List

from dndassist.autoplay import user_select_option
from dndassist.autoroll import max_dice, rolldice


def check_new_level(past_xp:int, new_xp:int, hit_dice:str, const_mod:int)-> Tuple[int,int,int,List[str]]:
    """find the bonuses to apply for a new level, by comparing past and new XP

    Return:
        - the curent level and proficiency
        - if level up the increase in Hit Points and ability increase 
    """
    past_lvl,_ = get_lvl_proficiency(past_xp)
    new_lvl, new_proficiency = get_lvl_proficiency(new_xp)
    print("??",past_lvl,new_lvl)
    if past_lvl == new_lvl:
        return new_lvl, new_proficiency, 0, []
    
    avg = max_dice(hit_dice)+1
    opt, _ = user_select_option(
        f"Use average hit dice ({avg})? or roll {hit_dice}?",
        f"",
        ["roll dice", "use average"]
    )
    if opt == "use average":
        hp_up = avg+const_mod
    else:
        roll,_ =rolldice(hit_dice)
        hp_up = max(1, roll+const_mod)
    
    # ASI phase
    ability_upgrades = ability_score_increase(new_lvl)
    if "constitution" in ability_upgrades:
        hp_up += new_lvl
    return new_lvl, new_proficiency, hp_up, ability_upgrades


def get_lvl_proficiency(xp:int)-> Tuple[int, int]:
    """return level and proficiency from xp_points"""
    if xp < 300:
        return 1, 2
    if xp < 900:
        return 2, 2
    if xp < 2700:
        return 3, 2
    if xp < 6500:
        return 4, 2
    if xp < 14000:
        return 5, 3
    if xp < 23000:
        return 6, 3
    if xp < 34000:
        return 7, 3
    if xp < 48000:
        return 8, 3
    if xp < 64000:
        return 9, 4
    if xp < 85000:
        return 10, 4
    if xp < 85000:
        return 11, 4
    if xp < 120000:
        return 12, 4
    if xp < 140000:
        return 13, 5
    if xp < 165000:
        return 14, 5
    if xp < 195000:
        return 15, 5
    if xp < 225000:
        return 16, 5
    if xp < 265000:
        return 17, 6
    if xp < 305000:
        return 18, 6
    if xp < 355000:
        return 19, 6
    return 20, 6

def ability_score_increase(lvl:int) -> List[str]:
    """Ask what abilities to increase if level is an ASI"""
    if lvl not in [4,8,12,16,20]:
        return []
    
    abilities = ["strength","dexterity","constitution","intelligence","wisdom","charisma"]
    
    ab1, _ = user_select_option(
        "What ability you want to increase first?",
        f"This is you ability increase for level {lvl}",
        abilities
    )
    ab2, _ = user_select_option(
        "What ability you want to increase last?",
        f"This is you ability increase for level {lvl}",
        abilities
    )
    return [ab1,ab2]

# print( check_new_level(2600, 2800, '1d10',2))