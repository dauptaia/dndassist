from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import yaml
import os
from math import floor
from textwrap import indent
from colorama import Fore, Style, init
import random

from dndassist.autoroll import rolldice
from dndassist.equipment import weapon_catg, Weapon, equipment_weight
from dndassist.storyprint import print_r,print_c_red


@dataclass
class Character:
    # --- Identity ---
    name: str
    race: str
    char_class: str
    gender: str  = "neutral"
    level: int = 1
    xp: int = 0
    gold: int = 0
    description: str = "no particular trait"
    alignment: Optional[str] = None
    notes: Optional[str] = None
    sprite: Optional[str] = None
    

    # ---game Engine----
    faction: str = "neutral"  # to simplfy firends and foes
    available_actions: List[str] = field(
        default_factory=list
    )  # lambda: ["attack", "move", "dash", "rest"])

    max_cargo: int = 30  # max weight to carry in Kgs
    max_hp: int = 10
    max_speed: int = 30  # max distance in one round (6 seconds) , in meters
    proficiency_bonus: int = 2
    wkdir:str = None

    # --- Attributes ---
    attributes: Dict[str, int] = field(
        default_factory=lambda: {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
        }
    )

    # --Current state ---
    current_state: Dict[str, any] = field(
        default_factory=lambda: {
            "current_hp": 10,
       #     "objectives": ["stand watch"],
            "conditions": [],
        #    "action": "idle",
        #    "outcome": "",
        #    "aggro": None,
        }
    )

    # --- Equipment / Magic ---
    equipment: List[str] = field(default_factory=list)
    spells: List[str] = field(default_factory=list)
    equipped: Dict[str, Optional[str]] = field(
        default_factory=lambda: {"armor": None, "main_hand": None, "off_hand": None}
    )
    weapon_mastery: Dict[str, str] = field(
        default_factory=lambda: {"simple": "proficient", "martial": "none"}
    )

    # ---------- YAML I/O ----------
    
    @classmethod
    def load(cls, wkdir:str, path: str) -> "Character":
        """Load a character from a YAML file."""
        full_path = os.path.join(wkdir,"Characters",path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"No such character file: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            data["wkdir"]=wkdir
        return cls(**data)

    @classmethod
    def load_from_dict(cls, data:dict) -> "Character":
        """Load a character from a dict descriptio,"""
        return cls(**data)
    
    # def is_npc(self):
    #     npc_bool = True
    #     if "player" in self.faction:
    #         npc_bool = False
    #     if "gamemaster" in self.faction:
    #         npc_bool =False
    #     return npc_bool
    
    def attr_mod(self, attr) -> int:
        """Return attribute modifier"""
        return floor((self.attributes[attr] - 10) / 2)

    def available_ranges(self) -> List[Tuple[str, int, str]]:
        """return all weapon ranges available, from the longest to the shortest
        as a list of weapon_name, range, and damage_dice"""
        found_ranges = []
        for item in self.equipment:
            if weapon_catg(item) is not None:
                weapon = Weapon.from_name(item)
                range_ = weapon.range_normal
                damage_ = weapon.damage_dice
                if weapon.range_long is not None:
                    range_ = weapon.range_long
                found_ranges.append((item, range_, damage_))

        sorted_ranges = sorted(found_ranges, key=lambda x: x[1], reverse=True)
        return sorted_ranges

    def equipped_armor(self) -> str:
        return self.equipped["armor"]

    def equipped_shield(self) -> str:
        return None

    def defense_bonus(self) -> int:
        return 0

    def attack_bonus(self, weapon_name) -> int:
        cat = weapon_catg(weapon_name)
        if cat is None:
            return 0
        if self.weapon_mastery[cat] == "proficient":
            return self.proficiency_bonus
        return 0

    def get_damage(self, damage: int) -> bool:
        """Apply damage to character

        Return a boolean about death : True if dead"""

        print_r(
            f"Character __{self.name}__, at {self.current_state['current_hp']} HP, takes {damage} HP."
        )
        self.current_state["current_hp"] -= damage

        # Insta-kill
        if self.current_state["current_hp"] <= self.max_hp:
            self.current_state["conditions"].append("dead")
            print_c_red(f"Character __{self.name}__ is dead...")
            return True

        # For NPC
        if self.faction != "player":
            if self.current_state["current_hp"] > 0:
                return False
            else:
                print_c_red(f"Character __{self.name}__ is dead...")
                self.current_state["conditions"].append("dead")
                return True
        # For players
        # .  - HP positive ? exit...
        if self.current_state["current_hp"] > 0:
            return False
        else:
            self.current_state["current_hp"] = 0
            print_c_red(f"Character __{self.name}__ is in the hands of fate...")
            success = 0
            fails = 0
            while 1:
                fate = rolldice("1d20")
                if fate == 20:
                    success = 3
                elif fate >= 10:
                    success += 1
                else:
                    fails += 1

                print_r(f"    failuress {fails} , successes {success}")
                if success == 3:
                    self.current_state["current_hp"] = 1
                    self.current_state["conditions"].append("injured")
                    print_r(f"Character __{self.name}__ is injured but awake")
                    return False
                if fails == 3:
                    self.current_state["conditions"].append("dead")
                    print_c_red(f"Character __{self.name}__ is dead...")
                    return True

    def drop_loot(self):
        """Drop one of the properties of the character, randomly"""
        loot = random.choice(self.equipment)
        return loot

    def _count_cargo(self):
        weight = 0
        for item in self.equipment:
            weight+= equipment_weight(item)
        return weight

    def add_item(self, item:str)->bool:
        """Add an item in Character inventory, return false if too heavy"""
        weight = self._count_cargo()+equipment_weight(item)

        if weight > self.max_cargo:
            return False
        
        self.equipment.append(item)

        if weight > 0.8*self.max_cargo:
            if "heavy equipement" not in self.current_state["conditions"]:
                self.current_state["conditions"].append("heavy equipement")
        return True

    def max_distance(self):
        """return the maximum distance """
        max_dist = self.max_speed
        if "heavy equipement"  in self.current_state["conditions"]:
            max_dist = int(max_dist*0.6)
        return max_dist

    def situation(self):
        """Retur the current situation of the character"""
        pronoun = "He"
        possessive = "His"
        if self.gender == "female":
            pronoun = "She"
            possessive = "Her"
        
        if self.gender == "unknown":
            pronoun = "It"
            possessive = "Its" 

        situation  = f"__{self.name}__ is a {self.gender} {self.race} {self.char_class} character  of level {self.level}"
        situation  += "\n" +f"{pronoun} belongs to the faction {self.faction}, with the alignment {self.alignment}"
        situation  += "\n" +self.notes
        situation += "\nCurrently:"
        situation  +=f"\n {possessive} hit points :  {self.current_state['current_hp']}/{self.max_hp}"
        if self.current_state["conditions"]:
            situation  +=f"\n {possessive} conditions: {','.join(self.current_state['conditions'])}"
        if self.equipment:
            situation  +=f"\n {possessive} equipment: {','.join(self.equipment)}"
        return situation
            
    # ---------- Pretty terminal display ----------
    def __repr__(self):
        """Nicely formatted display of the character in terminal."""
        print(f"{Fore.CYAN}{'='*40}")
        print(
            f"{Fore.YELLOW}{self.name} {Fore.WHITE}(Level {self.level} {self.race} {self.char_class})"
        )
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
