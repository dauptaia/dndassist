from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import yaml
import os
from math import floor
from textwrap import indent
from colorama import Fore, Style, init


from dndassist.equipment import weapon_catg
@dataclass
class Character:
    # --- Identity ---
    name: str
    race: str
    char_class: str
    level: int = 1
    alignment: Optional[str] = None

    # --- Attributes ---
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
    })

    # --- Combat Stats ---
    max_hp: int = 10
    current_hp: int = 10
    temp_hp: int = 0
    armor_class: int = 10
    speed: int = 30
    proficiency_bonus: int = 2
    initiative: Optional[int] = None
    hit_dice: str = "1d10"
    conditions: List[str] = field(default_factory=list)

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

    # --- Progression / Notes ---
    xp: int = 0
    notes: Optional[str] = None

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

    def attr_mod(self, attr)-> int:
        """Return attribute modifier"""
        return floor((self.attributes[attr]-10)/2)

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

