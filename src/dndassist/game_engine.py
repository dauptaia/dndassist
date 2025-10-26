from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random

from dndassist.character import Character

from dndassist.room import RoomMap, Actor
from dndassist.autoroll import rolldice, max_dice
from dndassist.attack import attack
from dndassist.storyprint import print_l,print_c,print_r,print_color,print_c_red
from dndassist.autoplay import auto_play_ollama,user_select_option,user_select_quantity
from datetime import datetime, timedelta

LOGFILE = "./adventure_log.txt"

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

        self.adventure_log=[]
        
        self.adventure_log.append(banner)
        
        self.room: RoomMap = room
        self.room.print_map()
        
        self.round_counter: int = 0
        self.now: datetime = datetime(1000, 1, 1) + timedelta(0, 3600 * 12)
        self.run_round()


    # ---------- MAIN LOOP ----------
    def run_round(self):
        """Run one round (each actor acts once in initiative order)."""
        self.round_counter += 1

        turn_mark = f"\n=== ROUND {self.round_counter} START ==="
        turn_mark += f"\n   Room {self.room.name}, time {self.now.time()}"
        
        print_c(turn_mark)
        
        self.adventure_log.append(turn_mark)
                

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
            skip = False
            for skip_state in ["dead", "resting"]:
                if skip_state in actor.character.current_state["conditions"]:
                    skip=True

            if skip:
                continue

            self.now += timedelta(0, 6)

            # ----- build context ---
            actor_context = f"--- __{actor.name}__'s turn ---"            
            self.adventure_log.append("\n\n"+actor_context)
            actor_context += "\n" + actor.character.describe_situation()
            actor_context += "\n" + self.room.describe_view_los(actor.name)
            print_c(actor_context)
            remaining_moves = actor.character.max_distance()
            remaining_actions = 100
            lookaround_done = False
            while remaining_moves > 0 and remaining_actions > 0:
                print_c(f"\n    Remaining moves: {remaining_moves}m")
                actions_avail = ["round finished", "move in direction"]
                if not lookaround_done:
                    actions_avail.append("look around")
                (
                    all_visible_actors_,
                    all_visible_loots,
                ) = self.room.visible_actors_n_loots(actor.name)

                for other, dist in all_visible_actors_:
                    if "dead" in self.room.actors[other].character.current_state["conditions"]:
                        pass
                    else:
                        if dist > 3:
                            actions_avail.append(f"move to {other} at {dist}m ")
                        if dist <= 3:
                            actions_avail.append(f"talk to {other}")

                for other, dist in all_visible_loots:
                    if other in killed_actors:
                        continue
                    if dist > 3:
                        actions_avail.append(f"move to {other} at {dist}m ")
                    if dist <= 3:
                        actions_avail.append(f"pick up {other}")

                # Attack solutions
                actions_avail.extend(self.build_attack_solutions(actor, all_visible_actors_))
                npc = True
                if "player" in actor.character.faction:
                    npc = False

                action,comment = user_select_option("Select an action:", actor_context, actions_avail, npc=npc)
                
                print_l("Actions available:")
                print_l("\n".join(actions_avail))
                actor.character.current_state["action"]= action
                print_l("__"+action+"__")
                print_l(comment)
                
                self.adventure_log.append(action)
                self.adventure_log.append(comment)
                
                outcome = ""
                if action.startswith("round finished"):
                    remaining_moves = 0
                    remaining_actions = 0
                if action.startswith("stand watch"):
                    remaining_actions -= 100
                        

                elif action.startswith("look around"):
                    facing_ = actor.facing
                    actor.facing = "N"
                    print_c(self.room.describe_view_los(actor.name))
                    actor.facing = "E"
                    print_c(self.room.describe_view_los(actor.name))
                    actor.facing = "S"
                    print_c(self.room.describe_view_los(actor.name))
                    actor.facing = "W"
                    print_c(self.room.describe_view_los(actor.name))
                    actor.facing = facing_
                    lookaround_done = True
                    self.room.print_map()
                elif action.startswith("move"):
                    if action.startswith("move to"):
                        tgt = action.split(" ")[2]
                        used_dist = self.room.move_actor_to_target(
                            actor.name, tgt, remaining_moves
                        )
                        outcome +=f"\n{actor.name} moved toward {tgt} over {used_dist}m"
                        remaining_moves -= used_dist
                        

                    elif action.startswith("move in direction"):
                        dir, _ = user_select_option(
                            "Which direction:",
                            actor_context, 
                            ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                            npc=npc
                        )
                        select_dist, _ = user_select_quantity(
                            "Which distance:", 
                            actor_context, 
                            0, remaining_moves, 
                            npc=npc
                        )
                        used_dist = self.room.move_actor_to_direction(
                            actor.name, dir, select_dist
                        )
                        outcome +=f"\n{actor.name} moved {dir} over {used_dist}m"
                        remaining_moves -= used_dist
                    else:
                        print_c_red(f"Action {action} not understood")
                        remaining_actions -= 100
                        remaining_moves =0
                
                elif action.startswith("attack"):
                    remaining_actions -= 100
                    defender_name = action.split(" ")[1]
                    weapon_name = action.split(";")[0].split("with")[-1].strip()
                    defender = self.room.actors[defender_name]
                    dmg = attack(actor.character, weapon_name, defender.character)
                    is_dead = defender.character.get_damage(dmg)
                    outcome +=f"\n{defender_name} took {dmg} hp damage."
                    if is_dead:
                        outcome+=f"\n{defender_name} is dead."
                        self.room.add_loot(defender.character.drop_loot(), defender.pos)
                        killed_actors.append(defender_name)
                
                elif action.startswith("pick up"):
                    remaining_actions -= 100
                    loot = action.split("ick up")[-1].strip()
                    equipment_name = self.room.loots[loot].name
                    success = actor.character.add_item(equipment_name)
                    if success:
                        del self.room.loots[loot]
                        outcome += f"\n{actor.name} has picked up {loot} {equipment_name}"
                    else:
                        outcome +=f"\n{actor.name} cannot picked {loot} {equipment_name}, too heavy"                    

                elif action.startswith("talk to"):
                    remaining_actions -= 100
                    outcome+="\nblabla"

                actor.character.current_state["outcome"]=outcome
                self.adventure_log.append(outcome+"\n")
                print_l("__"+outcome+"__") 
                with open(LOGFILE,"w") as fout:
                    fout.write("\n".join(self.adventure_log))
        
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

