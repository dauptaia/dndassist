from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import yaml
import os
from math import floor
from textwrap import indent
from colorama import Fore, Style, init


from dndassist.equipment import weapon_catg, Weapon
@dataclass
class Character:
    # --- Identity ---
    name: str
    race: str
    char_class: str
    level: int = 1
    xp: int = 0
    gold: int = 0
    description: str = "no particular trait"
    alignment: Optional[str] = None 
    notes: Optional[str] = None

    # ---game Engine----
    faction: str = "neutral" # to simplfy firends and foes
    available_actions: List[str]=field(default_factory=list)#lambda: ["attack", "move", "dash", "rest"])
    

    max_cargo: int = 30 # max weight to carry in Kgs
    max_hp: int = 10
    max_speed: int = 30 # max distance in one round (6 seconds) , in meters
    proficiency_bonus: int = 2
    
    # --- Attributes ---
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
    })


    # --Current state ---
    current_state: Dict[str, int] = field(default_factory=lambda: {
        "current_hp": 10,
        "objectives": ["stand watch"],
        "conditions": [],
        "action": "idle",
        "aggro": None
    })

   
    # --- Equipment / Magic ---
    equipment: List[str] = field(default_factory=list)
    spells: List[str] = field(default_factory=list)
    equipped: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "armor": None,
        "main_hand": None,
        "off_hand": None
    })
    weapon_mastery: Dict[str, str] = field(default_factory=lambda: {
        "simple": "proficient",
        "martial": "none"
    })

    

    # ---------- YAML I/O ----------
    def save(self, path: str):
        """Save the character to a YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(asdict(self), f, sort_keys=False, allow_unicode=True)

    @classmethod
    def load(cls, path: str) -> "Character":
        """Load a character from a YAML file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"No such character file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def push_objective(self, new_obj: str):
        self.current_state["objectives"].insert(0, new_obj)

    def attr_mod(self, attr)-> int:
        """Return attribute modifier"""
        return floor((self.attributes[attr]-10)/2)

    def available_ranges(self)->List[Tuple[str, int, str]]:
        """ return all weapon ranges available, from the longest to the shortest
        as a list of weapon_name, range, and damage_dice"""
        found_ranges=[]
        for item in self.equipment:
            if weapon_catg(item) is not None:
                weapon=Weapon.from_name(item)
                range_ = weapon.range_normal
                damage_ = weapon.damage_dice
                if weapon.range_long is not None:
                    range_=weapon.range_long
                found_ranges.append((item,range_,damage_) )
        
        sorted_ranges = sorted(found_ranges,key=lambda x:x[1], reverse=True)
        return sorted_ranges


    def equipped_armor(self)-> str:
        return self.equipped["armor"]

    def equipped_shield(self)-> str:
        return None

    def defense_bonus(self)-> int:
        return 0

    def attack_bonus(self,weapon_name)-> int:
        cat = weapon_catg(weapon_name)
        if cat is None:
            return 0
        if self.weapon_mastery[cat] == "proficient":
            return self.proficiency_bonus
        return 0

     # ---------- Pretty terminal display ----------
    def __repr__(self):
        """Nicely formatted display of the character in terminal."""
        print(f"{Fore.CYAN}{'='*40}")
        print(f"{Fore.YELLOW}{self.name} {Fore.WHITE}(Level {self.level} {self.race} {self.char_class})")
        if self.alignment:
            print(f"{Fore.LIGHTBLACK_EX}Alignment: {self.alignment}")
        print(f"{Fore.CYAN}{'-'*40}")

        # Attributes
        print(f"{Fore.GREEN}Attributes:")
        for k, v in self.attributes.items():
            print(f"  {Fore.WHITE}{k.capitalize():<13}: {Fore.LIGHTBLUE_EX}{v}")

        # Equipment
        if self.equipment:
            print(f"\n{Fore.GREEN}Equipment:")
            for item in self.equipment:
                print(f"  {Fore.WHITE}- {item}")

        # Spells
        if self.spells:
            print(f"\n{Fore.GREEN}Spells:")
            for spell in self.spells:
                print(f"  {Fore.WHITE}- {spell}")

        # Notes
        if self.notes:
            print(f"\n{Fore.GREEN}Notes:")
            print(indent(self.notes, "  "))

        print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")


# liora = Character.load("liora.yml")
# print(liora.name, liora.level)
# print(liora)

