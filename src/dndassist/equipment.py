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

EQUIPMENT_PATH = files("dndassist").joinpath(
    "equipment.json"
)  # os.path.join("data", "weapons.json")
EQUIPMENT_CATG_PATH = files("dndassist").joinpath(
    "equipment_categories.json"
)  # os.path.join("data", "weapons.json")

with open(EQUIPMENT_PATH, "r", encoding="utf-8") as f:
    EQUIPMENT_DICT = json.load(f)

with open(EQUIPMENT_CATG_PATH, "r", encoding="utf-8") as f:
    EQUIPMENT_CATG_DICT = json.load(f)



def print_r(text):
    story_print(text, color="green", justify="right")


def equipment_weight(equip_name):
    weight = 0
    for cat in ["Weapon", "Armor", "Shield"]:
        for equip in EQUIPMENT_DICT[cat]:
            if equip["name"] == equip_name:
                weight = equip["weight"]
        if equip_name in EQUIPMENT_DICT[cat]:
            weight = EQUIPMENT_DICT[cat][equip_name]
    if weight == 0:
        print_r(f"{equip_name} not present in equipment ddb.")
    return weight

def equipment_cost(equip_name):
    weight = 0
    for cat in ["Weapon", "Armor", "Shield"]:
        for equip in EQUIPMENT_DICT[cat]:
            if equip["name"] == equip_name:
                weight = equip["cost"]
        if equip_name in EQUIPMENT_DICT[cat]:
            weight = EQUIPMENT_DICT[cat][equip_name]
    if weight == 0:
        print_r(f"{equip_name} not present in equipment ddb.")
    return weight


def weapon_catg(weapon_name):
    for cat in EQUIPMENT_CATG_DICT:
        if "Simple" not in cat and "Martial" not in cat:
            continue
        if weapon_name in EQUIPMENT_CATG_DICT[cat]:
            if "Simple" in cat:
                return "simple"
            else:
                return "martial"
    return None


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
    def _load_all_weapons(cls) -> Dict[str, Dict[str, Any]]:
        """Load all weapon specs into a dict indexed by name (case-insensitive)."""
        return {entry["name"].lower(): entry for entry in EQUIPMENT_DICT["Weapon"]}

    @classmethod
    def from_name(cls, name: str) -> "Weapon":
        """Create a Weapon instance by name (case-insensitive lookup)."""

        if not name:
            # Bare hands fallback
            return cls(
                name="Unarmed strike",
                weapon_category="Simple",
                weapon_range="Melee",
                damage_dice="1d1",
                damage_bonus=1,
                damage_type="Bludgeoning",
                range_normal=5,
                range_long=None,
                properties=[],
                cost=0,
                weight=0,
            )

        all_weapons = cls._load_all_weapons()
        key = name.lower()
        if key not in all_weapons:
            raise ValueError(f"Weapon '{name}' not found in {EQUIPMENT_PATH}")
        return cls(**all_weapons[key])

    # ------------------ GAME LOGIC ------------------

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


    # Path to your weapon definitions (adjust to your project structure)

    @classmethod
    def _load_all_armors(cls) -> Dict[str, Dict[str, Any]]:
        """Load all armor specs into a dict indexed by name (case-insensitive)."""
        return {entry["name"].lower(): entry for entry in EQUIPMENT_DICT["Armor"]}

    @classmethod
    def from_name(cls, name: str) -> "Armor":
        """Create a Armor instance by name (case-insensitive lookup)."""

        all_weapons = cls._load_all_armors()
        key = name.lower()
        if key not in all_weapons:
            raise ValueError(f"Armor '{name}' not found in {EQUIPMENT_PATH}")
        return cls(**all_weapons[key])


@dataclass
class Shield:
    name: str
    base: int
    cost: str
    weight: int


    # Path to your weapon definitions (adjust to your project structure)

    @classmethod
    def _load_all_shields(cls) -> Dict[str, Dict[str, Any]]:
        """Load all shield specs into a dict indexed by name (case-insensitive)."""
        return {entry["name"].lower(): entry for entry in EQUIPMENT_DICT["Shield"]}

    @classmethod
    def from_name(cls, name: str) -> "Shield":
        """Create a Shield instance by name (case-insensitive lookup)."""

        all_weapons = cls._load_all_shields()
        key = name.lower()
        if key not in all_weapons:
            raise ValueError(f"Shield '{name}' not found in {EQUIPMENT_PATH}")
        return cls(**all_weapons[key])
