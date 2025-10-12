"""Module to solve an attack"""

from dndassist.autoroll import rolldice
from dndassist.character import Character

from dndassist.equipment import (
    Armor, Weapon, Shield
)

def attack(attacker:Character, weapon_name, defender:Character, autoroll=False, advantage:int=0):

    
    
    armor_name = defender.equipped_armor()
    if armor_name is None:
        armor_score=0
    else:
        armor = Armor.from_name(armor_name)
        armor_score = armor.base 
        print(f".      Armor  +{armor_score}")
        
    shield_name = defender.equipped_shield()
    if shield_name is None:
        shield_score=0
    else:
        shield = Shield.from_name(shield_name)
        shield_score = shield.bonus 
        print(f"      Shield +{shield_score}")

    if armor.dex_bonus:
            
        max_dex = 100
        if armor.max_bonus is not None:
            max_dex = armor.max_bonus
        dex_bonus = min(defender.attr_mod("dexterity"),max_dex)

        print(f"   Dex. Bonus +{dex_bonus}")

   

    defense_score = (armor_score + shield_score + dex_bonus
       + defender.defense_bonus()  # Dons, sorts, etc.
    )
    print(f"    Defense : {defense_score}")
    
    roll, dice_normed =   rolldice("1d20", autoroll=autoroll, advantage=advantage)      
    
    weapon=Weapon.from_name(weapon_name)

    attr_modifier = 0
    for attr in weapon.attributes():
        attr_modifier = max(attr_modifier,attacker.attr_mod(attr) )
    
    attack_score = (roll
        + attr_modifier
        + attacker.attack_bonus(weapon_name)
        + weapon.damage_bonus
    )

    damage = 0
    attack_result = attack_score-defense_score
    if dice_normed == 1.0 and advantage > 0: #Critique aet pas de desavantage
        print(f"Reussite critique !")
        attack_result = 1
    if dice_normed == 0.0: # Fumble
        attack_result = -1

    if attack_result>=0: 
        print(f"L’attaque touche !")
        roll_dmg, _ =   rolldice(weapon.damage_dice, autoroll=autoroll, advantage=advantage)   
        if dice_normed == 1.0 and advantage > 0: #Critique et pas de desavantage
            roll_dmg *=2
        
        damage = (roll_dmg
            + attr_modifier
            + weapon.damage_bonus
        )

        print(f"Dégâts : {damage}")
    else:
        # Attaque rate
        print("L’attaque rate.")
    
    return damage
