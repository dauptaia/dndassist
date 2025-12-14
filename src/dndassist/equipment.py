# import json

# with open("equipment.json", "r") as fin:
#     EQUIPMENT_DATA = json.load(fin)
# with open("equipment_categories.json", "r") as fin:
#     EQUIPMENT_CATEGORIES = json.load(fin)


from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
import os
from importlib_resources import files
from dndassist.storyprint import story_print


EQUIP_CATG = ["Weapon","Shield","Armor","Item"]

with open( files("dndassist").joinpath("equipment.json"), "r", encoding="utf-8") as f:
    EQUIPMENT_DICT = json.load(f)
with open( files("dndassist").joinpath("equipment_custom.json"), "r", encoding="utf-8") as f:
    data_ = json.load(f)
    for catg in EQUIP_CATG:
        try:
            EQUIPMENT_DICT[catg].update(data_[catg])
        except KeyError:
            pass

WEAPONS = EQUIPMENT_DICT["Weapon"]
SHIELDS = EQUIPMENT_DICT["Shield"]
ARMORS = EQUIPMENT_DICT["Armor"]
ITEMS = EQUIPMENT_DICT["Item"]


def _print_r(text):
    story_print(text, color="green", justify="right")

def equipment_weight(equip_name):
    equip_name = equip_name.lower()
    
    qoi = None
    for cat in EQUIP_CATG:
        if equip_name in EQUIPMENT_DICT[cat]:
            qoi = EQUIPMENT_DICT[cat][equip_name]["weight"]
            break
    if qoi is None:
        _print_r(f"{equip_name} not present in equipment ddb.")
    return qoi

def equipment_cost(equip_name):
    equip_name = equip_name.lower()
    
    qoi = None
    for cat in EQUIP_CATG:
        if equip_name in EQUIPMENT_DICT[cat]:
            qoi = EQUIPMENT_DICT[cat][equip_name]["weight"]
            break
    if qoi is None:
        _print_r(f"{equip_name} not present in equipment ddb.")
    return qoi

def weapon_catg(weapon_name):   
    weapon_name = weapon_name.lower()
    if  weapon_name not in WEAPONS:
        return None
    return WEAPONS[weapon_name]["weapon_category"]
    

@dataclass
class Weapon:
    name: str
    weapon_category: str
    weapon_range: str
    damage_dice: str
    damage_bonus: int
    damage_type: str
    range_normal: int
    range_long: Optional[int]
    properties: List[str]
    cost: str
    weight: int

    # Path to your weapon definitions (adjust to your project structure)

    @classmethod
    def from_name(cls, name: str) -> "Weapon":
        """Create a Weapon instance by name (case-insensitive lookup)."""
        name = name.lower()
        if name not in WEAPONS:
            raise ValueError(f"Weapon '{name}' not found ")
        return cls(name, **WEAPONS[name])
    
    def attributes(self) -> List[str]:
        """Return which ability (e.g. Strength, Dexterity) is used to attack with this weapon."""
        props = [p.lower() for p in self.properties or []]
        w_range = self.weapon_range.lower()

        if "finesse" in props and w_range == "melee":
            return ["dexterity", "strength"]
        elif "thrown" in props:
            if "finesse" in props:
                return ["dexterity", "strength"]
            return ["strength"]
        elif w_range == "ranged":
            return ["dexterity"]
        else:
            return ["strength"]


@dataclass
class Armor:
    name: str
    category: str
    base: int
    dex_bonus: bool
    max_bonus: bool
    cost: str
    weight: int

    @classmethod
    def from_name(cls, name: str) -> "Armor":
        """Create a Armor instance by name (case-insensitive lookup)."""
        name = name.lower()
        if name not in ARMORS:
            raise ValueError(f"Armor '{name}' not found ")
        return cls(name, **ARMORS[name])
@dataclass
class Shield:
    name: str
    base: int
    cost: str
    weight: int
    """Used for shield or other stuff for the moment, """

    @classmethod
    def from_name(cls, name: str) -> "Shield":
        """Create a Shield instance by name (case-insensitive lookup)."""
        name = name.lower()
        if name not in SHIELDS:
            raise ValueError(f"Shield '{name}' not found ")
        return cls(name, **SHIELDS[name])

@dataclass
class Item:
    name: str
    cost: str
    weight: int
    """Used for Items or other stuff for the moment, """
    @classmethod
    def from_name(cls, name: str) -> "Item":
        name = name.lower()
        """Create a Item instance by name (case-sensitive lookup)."""
        if name not in ITEMS:
            raise ValueError(f"Item '{name}' not found ")
        return cls(name, **ITEMS[name])