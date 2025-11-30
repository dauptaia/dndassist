# 

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
from importlib_resources import files

SPELLS_PATH = files("dndassist").joinpath(
    "spells.json"
) 
with open(SPELLS_PATH, "r", encoding="utf-8") as f:
    SPELL_DICT = json.load(f)

def item_is_offensive_spell(item_spell):
    ispell = False
    for spell in SPELL_DICT:
        if spell.lower() == item_spell.lower():
            ispell = True
            break
    if ispell is False:
        return False
    
    if SPELL_DICT[spell]["damage_dice"] is None:
        return False
    return True


@dataclass
class Spell:
    name: str
    desc: str
    damage_dice: str
    saving_throw: str
    range: int
    radius: int
    duration: int
    isverbal: bool
    issomatic: bool
    ismaterial: bool
    material: str
    

    @classmethod
    def _load_all_spells(cls) -> Dict[str, Dict[str, Any]]:
        """Load all weapon specs into a dict indexed by name (case-insensitive)."""
        out = {}
        for key, value in SPELL_DICT.items():
            value["name"] = key
            if "material" not in value:
                value["material"] = None
            out[key.lower()] = value
           
        return out

    @classmethod
    def from_name(cls, name: str) -> "Spell":
        """Create a Spell instance by name (case-insensitive lookup)."""
        all_spells = cls._load_all_spells()
        key = name.lower()
        if key not in all_spells:
            raise ValueError(f"Spell '{name}' not found in {SPELLS_PATH}")
        return cls(**all_spells[key])
