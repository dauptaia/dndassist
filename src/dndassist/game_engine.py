from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random

from dndassist.character import Character

from dndassist.room import RoomMap, Actor
from dndassist.autoroll import rolldice, max_dice
from dndassist.attack import attack
from dndassist.storyprint import print_l,print_c,print_r,print_color,user_select_option,user_select_quantity

from datetime import datetime, timedelta


banner = u"""
                            ==(W{==========-      /===-                        
                              ||  (.--.)         /===-_---~~~~~~~~~------____  
                              | \_,|**|,__      |===-~___                _,-' `
                 -==\\        `\ ' `--'   ),    `//~\\   ~~~~`---.___.-~~      
             ______-==|        /`\_. .__/\ \    | |  \\           _-~`         
       __--~~~  ,-/-==\\      (   | .  |~~~~|   | |   `\        ,'             
    _-~       /'    |  \\     )__/==0==-\<>/   / /      \      /               
  .'        /       |   \\      /~\___/~~\/  /' /        \   /'                
 /  ____  /         |    \`\.__/-~~   \  |_/'  /          \/'                  
/-'~    ~~~~~---__  |     ~-/~         ( )   /'        _--~`                   
                  \_|      /        _) | ;  ),   __--~~                        
                    '~~--_/      _-~/- |/ \   '-~ \                            
                   {\__--_/}    / \\_>-|)<__\      \                           
                   /'   (_/  _-~  | |__>--<__|      |                          
                  |   _/) )-~     | |__>--<__|      |                          
                  / /~ ,_/       / /__>---<__/      |                          
                 o-o _//        /-~_>---<__-~      /                           
                 (^(~          /~_>---<__-      _-~                            
                ,/|           /__>--<__/     _-~                               
             ,//('(          |__>--<__|     /  -Alex Wargacki  .----_          
            ( ( '))          |__>--<__|    |                 /' _---_~\        
         `-)) )) (           |__>--<__|    |               /'  /     ~\`\      
        ,/,'//( (             \__>--<__\    \            /'  //        ||      
      ,( ( ((, ))              ~-__>--<_~-_  ~--____---~' _/'/        /'       
    `~/  )` ) ,/|                 ~-_~>--<_/-__       __-~ _/                  
  ._-~//( )/ )) `                    ~~-'_/_/ /~~~~~~~__--~                    
   ;'( ')/ ,)(                              ~~~~~~~~~~                         
  ' ') '( (/                                                                   
    '   '  `

DND-assist, a dungeon's and dragon GameMaster helper. 
By Antoine Dauptain, dedicated to Noé, Gaspard, Hugo.

"""

class GameEngine:
    room: RoomMap
    turn_counter: int = 0
    round_counter: int = 1

    def __init__(self, room: RoomMap):
        print_color(banner, width=80, primary="YELLOW")
        self.room: RoomMap = room
        self.room.print_map()
        
        self.round_counter: int = 0
        self.now: datetime = datetime(1000, 1, 1) + timedelta(0, 3600 * 12)
        self.run_round()

    # ---------- MAIN LOOP ----------
    def run_round(self):
        """Run one round (each actor acts once in initiative order)."""
        self.round_counter += 1
        print_c(f"\n=== ROUND {self.round_counter} START ===")
        print_c(f"\n   Room {self.room.name}, time {self.now.time()}")


        # 1️⃣ Filter out inactive actors
        active_actors = []
        for actor_key, actor in self.room.actors.items():
            for skip_state in ["dead", "resting"]:
                if skip_state in actor.character.current_state["conditions"]:
                    continue

            active_actors.append(actor)
        # 2️⃣ Compute initiative for all active actors
        initiative_order = self.compute_initiative(active_actors)

        killed_actors = []
        # 3️⃣ Execute each actor's turn in initiative order
        for actor in initiative_order:
            for skip_state in ["dead", "resting"]:
                if skip_state in actor.character.current_state["conditions"]:
                    continue

            self.now += timedelta(0, 6)

            # ----- build context ---
            actor_context =f"--- __{actor.name}__'s turn ---"            
            actor_context += "\n" + actor.character.describe_situation()
            actor_context += "\n" + self.room.describe_view_los(actor.name)
            print_c(actor_context)
            
            remaining_moves = actor.character.max_speed
            remaining_actions = 100
            while remaining_moves > 0 and remaining_actions > 0:
                print_c(f"\n    Remaining moves: {remaining_moves}m")
                actions_avail = ["round finished", "look around", "move in direction"]

                (
                    all_visible_actors_,
                    all_visible_loots,
                ) = self.room.visible_actors_n_loots(actor.name)

                for other, dist in all_visible_actors_:
                    if dist > 3:
                        actions_avail.append(f"move to {other} at {dist}m ")
                    if dist <= 3:
                        actions_avail.append(f"talk to {other}")

                for other, dist in all_visible_loots:
                    if dist > 3:
                        actions_avail.append(f"move to {other} at {dist}m ")
                    if dist <= 3:
                        actions_avail.append(f"pick up {other}")

                # Attack solutions
                actions_avail.extend(self.build_attack_solutions(actor, all_visible_actors_))

                action = user_select_option("Select an action:", actions_avail)

                if action.startswith("round finished"):
                    remaining_moves = 0
                    remaining_actions = 0
                elif action.startswith("move"):
                    if action.startswith("move to"):
                        tgt = action.split(" ")[2]
                        used_dist = self.room.move_actor_to_target(
                            actor.name, tgt, remaining_moves
                        )
                        remaining_moves -= used_dist

                    elif action.startswith("move in direction"):
                        dir = user_select_option(
                            "Which direction:",
                            ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                        )
                        select_dist = user_select_quantity(
                            "Which distance:", 0, remaining_moves
                        )
                        used_dist = self.room.move_actor_to_direction(
                            actor.name, dir, select_dist
                        )
                        remaining_moves -= used_dist
                elif action.startswith("attack"):
                    remaining_actions -= 100
                    defender_name = action.split(" ")[1]
                    weapon_name = action.split(";")[0].split("with")[-1].strip()
                    defender = self.room.actors[defender_name]
                    dmg = attack(actor.character, weapon_name, defender.character)
                    is_dead = defender.character.get_damage(dmg)
                    if is_dead:
                        self.room.add_loot(defender.character.drop_loot(), defender.pos)
                        killed_actors.append(defender_name)

        # for dead_name in killed_actors:
        #     self.room.del_actor(dead_name)

        # 4️⃣ End of round
        print_c(f"\n=== ROUND {self.round_counter} END ===")

        cont = input("Continue? (y/n):")
        if cont == "y":
            self.run_round()

    def build_attack_solutions(self, actor, all_visible_actors_):
        actions_avail=[]
        faction = actor.character.faction
        visible_foes = []
        for other, dist in all_visible_actors_:
            if self.room.actors[other].character.faction not in [
                        "neutral",
                        faction,
                    ]:
                visible_foes.append((other, dist))

        for other, dist in visible_foes:
            weapon, dmg = actor_attack_solutions(actor, dist)
            if weapon is not None:
                actions_avail.append(
                            f"attack {other} with {weapon} ; damage max {dmg} HP"
                        )
        return actions_avail

    # ---------- INITIATIVE ----------
    def compute_initiative(self, active_actors: List[Actor]) -> List[Actor]:
        """Compute initiative order based on dice rolls and dexterity modifiers."""
        initiatives = []
        for a in active_actors:
            print_r(f"Initiative roll for __{a.name}__")
            d20, _ = rolldice("1d20", autoroll=True)
            init_value = a.character.attr_mod("dexterity") + d20
            initiatives.append((init_value, random.random(), a))
        # print(f"{a.name} initiative: {init_value}")
        # Sort by initiative descending (then random tie-breaker)
        initiatives.sort(key=lambda x: (-x[0], x[1]))

        ordered = [a for (_, _, a) in initiatives]
        print_r("Order for this turn:")
        for i, a in enumerate(ordered):
            print_r(f".  {i}, __{a.name}__")
        return ordered


def list_of_foes(actor: Actor, other_actors_: List[Actor]) -> List[Actor]:
    """return the foes of this actor"""
    out = []
    for other in other_actors_:
        if other.character.faction not in ["neutral", actor.character.faction]:
            out.append(other)
    return out


def actor_attack_solutions(actor: Actor, dist: int) -> Tuple[str, str]:
    """return strongest available weapon  in range"""
    max_dmg = 0
    weap = None
    for weapon, range, damage in actor.character.available_ranges():
        if range >= dist:
            if max_dice(damage) > max_dmg:
                weap, max_dmg = weapon, max_dice(damage)

    return weap, max_dmg

