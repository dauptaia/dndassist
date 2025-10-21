"""Module to solve an attack"""

from dndassist.autoroll import rolldice
from dndassist.character import Character

from dndassist.equipment import Armor, Weapon, Shield
from dndassist.storyprint import print_r,print_c_orange

def attack(
    attacker: Character,
    weapon_name,
    defender: Character,
    autoroll=False,
    advantage: int = 0,
):
    print_r(f"Defender {defender.name}, {defender.current_state['current_hp']} HP")
    dex_bonus = 0
    armor_name = defender.equipped_armor()
    if armor_name is None:
        armor_score = 0
        print_r(f".      No Armor")
    else:
        armor = Armor.from_name(armor_name)
        armor_score = armor.base
        print_r(f".      Armor  +{armor_score}")
        if armor.dex_bonus:
            max_dex = 100
            if armor.max_bonus is not None:
                max_dex = armor.max_bonus
            dex_bonus = min(defender.attr_mod("dexterity"), max_dex)
            print_r(f"   Dex. Bonus +{dex_bonus}")

    shield_name = defender.equipped_shield()
    if shield_name is None:
        shield_score = 0
        print_r(f".      No Shield")
    else:
        shield = Shield.from_name(shield_name)
        shield_score = shield.bonus
        print_r(f"      Shield +{shield_score}")

    defense_score = (
        armor_score
        + shield_score
        + dex_bonus
        + defender.defense_bonus()  # Dons, sorts, etc.
    )
    print_r(f"    Total Defense : {defense_score}")

    print_r(f"{attacker.name} attacks with {weapon_name} HP")

    weapon = Weapon.from_name(weapon_name)

    attr_modifier = 0
    attr_used = None
    for _attr in weapon.attributes():
        _amod = attacker.attr_mod(_attr)
        if _amod > attr_modifier:
            attr_modifier = _amod
            attr_used = _attr
    if attr_used is not None:
        print_r(f"    Using {attr_used} : {attr_modifier}")

    attack_bonus = attacker.attack_bonus(weapon_name)
    if attack_bonus > 0:
        print_r(f"    character bonus : {attack_bonus}")

    if weapon.damage_bonus > 0:
        print_r(f"    weapons bonus : {weapon.damage_bonus}")

    roll, dice_normed = rolldice("1d20", autoroll=autoroll, advantage=advantage)

    attack_score = roll + attr_modifier + attack_bonus + weapon.damage_bonus

    damage = 0
    attack_result = attack_score - defense_score
    if dice_normed == 1.0 and advantage > 0:  # Critique aet pas de desavantage
        print_r(f"Reussite critique !")
        attack_result = 1
    if dice_normed == 0.0:  # Fumble
        attack_result = -1

    if attack_result >= 0:
        print_c_orange(f"Attack successful")
        roll_dmg, _ = rolldice(
            weapon.damage_dice, autoroll=autoroll, advantage=advantage
        )
        if dice_normed == 1.0 and advantage > 0:  # Critique et pas de desavantage
            roll_dmg *= 2

        damage = roll_dmg + attr_modifier + weapon.damage_bonus

        print_r(f"Damage : {damage} HP")
        defender.current_state["current_hp"] -= damage

    else:
        # Attaque rate
        print_c_orange("Attack failed")

    return damage
