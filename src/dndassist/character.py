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
from dndassist.spellcasting import item_is_offensive_spell, Spell
from dndassist.storyprint import story_print


def print_r(text):
    story_print(text, color="green", justify="right")

@dataclass
class Character:
    # --- Identity ---
    name: str
    race: str
    char_class: str
    hit_dices:  List[str] = field(default_factory=list) # As many Hitdices as level
    hit_dices_mask:  List[bool] = field(default_factory=list) # all true when starting
    gender: str  = "neutral"
    level: int = 1
    xp: int = 0
    description: str = "no particular trait"
    alignment: Optional[str] = None
    notes: Optional[str] = None
    sprite: Optional[str] = None
    

    # ---game Engine----
    faction: str = "neutral"  # to simplfy firends and foes
    max_cargo: int = 30  # max weight to carry in Kgs
    max_hp: int = 10
    max_speed: int = 30  # max distance in one round (6 seconds) , in meters
    proficiency_bonus: int = 2

    wkdir:str = None

    # --- Attributes ---
    money: Dict[str, int] = field(
        default_factory=lambda: {
            "cp": 0,
            "sp": 0,
            "pp": 0,
            "gp": 0,
        }
    )


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
            "conditions": [],
        }
    )

    # --- Equipment / Magic ---
    equipment: List[str] = field(default_factory=list)
    proficiencies: List[str] = field(default_factory=list)
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
        """Load a character from a dict description"""
        return cls(**data)
    
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

    def available_hex_ranges(self) -> List[Tuple[str, int, str]]:
        """return all hexes ranges available, from the longest to the shortest
        as a list of weapon_name, range, and damage_dice"""
        found_ranges = []
        for item in self.spells:
            if item_is_offensive_spell(item) :
                spell = Spell.from_name(item)
                range_ = spell.range
                damage_ = spell.damage_dice
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
        if -self.current_state["current_hp"] > self.max_hp:
            self.current_state["conditions"].append("dead")
            story_print(f"Character __{self.name}__ is dead...", color="red")
            return True

        # For NPC
        if self.faction != "player":
            if self.current_state["current_hp"] > 0:
                return False
            else:
                story_print(f"Character __{self.name}__ is dead...", color="red")
                self.current_state["conditions"].append("dead")
                return True
        # For players
        # .  - HP positive ? exit...
        if self.current_state["current_hp"] > 0:
            return False
        else:
            self.current_state["current_hp"] = 0
            story_print(f"Character __{self.name}__ is in the hands of fate...", color="red")
            success = 0
            fails = 0
            while 1:
                fate,_ = rolldice("1d20")
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
                    story_print(f"Character __{self.name}__ is dead...", color="red")
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
    

    def status_str(self)-> Tuple[str,str]:
        """return status string for current data on character"""

        situation  = f"__{self.gender} {self.race} {self.char_class}, level {self.level}__"
        situation  += f"\n faction {self.faction}, alignment {self.alignment}"
        situation  += "\n" +self.description
        situation  += "\n" +self.notes
        situation  += "\n" +f"Max speed {self.max_speed} m"
        
        situation  +=f"\n\n hit points  :  {self.current_state['current_hp']}HP/{self.max_hp}HP"
        situation  +=f"\n\n payload     :  {self._count_cargo()}Kg/{self.max_cargo}Kg"
        situation  +=f"\n\n conditions  :  {','.join(self.current_state['conditions'])}"
        situation  +=f"\n\n __Money__ :"
        _list_str =[]
        for k,v in self.money.items():
            if int(v) > 0:
                _list_str.append(f"{v} {k}") 
        situation += ", ".join(_list_str)

        situation  +=f"\n\n __Hit Dices__ :"
        for hd,hd_m in zip(self.hit_dices,self.hit_dices_mask):
            sym = " "
            if hd_m:
                sym = "*"
            situation  +=f"\n {hd} {sym}"
         
        add_info = ""

        situation  +=f"\n\n __Attributes__ :"
        for k,v in self.attributes.items():
            situation  +=f"\n {k} : {v} ({self.attr_mod(k)})"
         
        add_info = ""
        
        
        add_info  +=f"\n__Weapon Mastery__ :"
        for k,v in self.weapon_mastery.items():
            add_info  +=f"\n {k} : {v}"

        
        if self.proficiencies:
            add_info  += f"\n __Proficiencies__ (bonus {self.proficiency_bonus}):"
            for pr in self.proficiencies:
                add_info+="\n  - "+pr

        if self.equipment:
            add_info  += "\n__Equipment__"
            for eq in self.equipment:
                add_info+="\n  - "+eq
        if self.spells:
            add_info  += "\n__Spells__"
            for sp in self.spells:
                add_info+="\n  - "+sp
          

    
        return situation, add_info
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
