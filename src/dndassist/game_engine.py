import os
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random

from dndassist.character import Character

from dndassist.gates import Gates
from dndassist.room import RoomMap, Actor
from dndassist.autoroll import rolldice, max_dice
from dndassist.attack import attack
from dndassist.storyprint import print_l, print_c, print_r, print_color, print_c_red
from dndassist.autoplay import (
    auto_play_ollama,
    user_select_option,
    user_select_quantity,
)
from datetime import datetime, timedelta

LOGFILE = "./adventure_log.txt"

banner = """
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
    def __init__(self, wkdir: str):
        print_color(banner, width=80, primary="YELLOW")
        self.wkdir=wkdir
        self.adventure_log = []

        self.adventure_log.append(banner)

        self.gates: Gates = Gates()
        self.players_sorted_list: List[str] = None
        self.room: RoomMap = None

        self.round_counter: int = 0
        self.startup()
        self.run_one_round()

    def startup(self):
        # load gates
        self.gates.load(self.wkdir, "gates.yaml")

        # load players 
        with open(os.path.join(self.wkdir, "players.yaml"), "r") as fin:
            players_data = yaml.safe_load(fin)

        self.players_sorted_list = sorted([ actor_name for actor_name in players_data["players"].keys()])
        list_players_actors = [ Actor.from_dict(pdict, self.wkdir) for pdict in players_data["players"].values()]
        # startup room
        self.change_room(players_data["room"],list_players_actors,datetime.now() )
        
    def change_room(self,destination_room:str, travelers:List[Actor], out_time:datetime):
        
        self.room = RoomMap.load(self.wkdir, destination_room + ".yaml")
        list_gates = self.gates.gates_by_room(destination_room)
        for g_name, g_pos, g_desc, d_obj_play in list_gates:
            self.room.add_gate(g_name, g_pos, g_desc)

        for actor in travelers:
            print_r(f"Add Actor {actor.name} to {destination_room}")
            self.room.actors[actor.name]=actor
        
        self.room.spread_actors_loots()

        list_names=" -"+"\n -".join(self.room.actors.keys())
        print_r(list_names)
        self.now=out_time
        
        
    def run_one_round(self):
        """Run one round (each actor acts once in initiative order)."""
        self.round_counter += 1

        turn_mark = f"\n=== ROUND {self.round_counter} START ==="
        turn_mark += f"\n   Room {self.room.name}, time {self.now.time()}"

        print_c(turn_mark)

        self.adventure_log.append(turn_mark)

        # 1️⃣ Filter out inactive actors
        active_actors = []
        for  actor in self.room.actors.values():
            skip = False
            for skip_state in ["dead", "resting"]:
                if skip_state in actor.character.current_state["conditions"]:
                    skip = True
            if not actor.objectives:
                print_r(f"{actor.name} has no objectives, skipping this turn")
                skip = True
            if skip:
                continue

            active_actors.append(actor)
        # 2️⃣ Compute initiative for all active actors
        initiative_order = self.compute_initiative(active_actors)

        # 3️⃣ Execute each actor's turn in initiative order
        for actor in initiative_order:
            # skip is actor is dead or unconcious
            skip = False
            for skip_state in ["dead"]:
                if skip_state in actor.character.current_state["conditions"]:
                    skip = True
            if skip:
                continue

            self.now += timedelta(0, 6)
            self.room.print_map()
            # ----- build context ---

            actor_context = f"--- __{actor.name}__'s turn ---"
            self.adventure_log.append("\n\n" + actor_context)
            remaining_moves = actor.character.max_distance()
            remaining_actions = 100
            while remaining_moves >= self.room.unit_m and remaining_actions > 0:
                print_c(actor_context)
                print_c(f"\n    Remaining moves: {remaining_moves}m")
                actions_avail = self.build_all_actions_available_to_actor(actor)
                print_l("Actions available:")
                print_l("\n".join(actions_avail))
            


                npc_bool = ("player" not in actor.character.faction)
                
                action, comment = user_select_option(
                    "What action will you do?",
                    actor.character.situation()
                    + "\n"  # what is not in the room
                    + self.room.describe_view_los(actor.name)
                    + "\n"
                    + actor.situation(),  # what is in view
                    actions_avail,
                    npc=npc_bool,
                )
                actor.last_action = action
                print_l("__" + action + "__")
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
                    self.room.look_around(actor.name)
                    remaining_actions -= 100
                elif action.startswith("move"):
                    if action.startswith("move to"):
                        outcome, used_dist = self.action_move_to_target(
                            actor, remaining_moves, action
                        )

                    elif action.startswith("move in direction"):
                        outcome, used_dist = self.action_move_to_direction(
                            actor, remaining_moves
                        )
                    else:
                        print_c_red(f"Action {action} not understood")
                        remaining_actions -= 100
                        remaining_moves = 0

                    if used_dist == 0:
                        remaining_moves -= self.room.unit_m
                    else:
                        remaining_moves -= used_dist

                elif action.startswith("attack"):
                    remaining_actions -= 100
                    outcome = self.action_attack(actor, action)

                elif action.startswith("pick up"):
                    remaining_actions -= 100
                    outcome = self.action_pick_up_loot(actor, action)

                elif action.startswith("talk to"):
                    remaining_actions -= 100
                    npc_actor = self.room.actors[action.split()[2]]
                    if npc_actor.dialog is None:
                        outcome = f"{npc_actor.name} has nothing to say to you.."
                    else:
                        outcome = npc_actor.dialog.run(actor)

                elif action.startswith("quit map"):
                    remaining_actions -= 100
                    gate_name = action.split()[2]
                    gate_desc = action.split(":")[-1].strip()   
                    self.gates.new_traveler(actor,gate_name)
                    
                    del self.room.actors[actor.name]
                    list_names=" -"+"\n -".join(self.room.actors.keys())
                    print_r(list_names)
        
                    outcome = f"actor {actor.name} enters {gate_desc}."
                
                else:
                    raise RuntimeError(f"Action {action} not understood")    

                actor.last_outcome = outcome
                self.adventure_log.append(outcome + "\n")
                print_l("__" + outcome + "__")
                with open(LOGFILE, "w") as fout:
                    fout.write("\n".join(self.adventure_log))

        print_c(f"\n=== ROUND {self.round_counter} END ===")

        print_l(str(self.gates.travelers_sorted_list()))
        print_l(str(self.players_sorted_list))
        
        if self.gates.travelers_sorted_list() == self.players_sorted_list:
            travelers, destination_room, out_time = self.gates.resolve_gates(self.room.name, self.now)
            self.change_room(destination_room,travelers,out_time)
        # This is where mor General controls               
        cont = input("Continue? (y/n):")
        if cont == "y":
            self.run_one_round()

    def build_all_actions_available_to_actor(self, actor:Actor)-> List[str]:
        """ Create a list of possible actions for an Actor"""

        actions_avail = ["round finished", "move in direction","look around"]
                
        (
                    all_visible_actors,
                    all_visible_loots,
                    all_visible_gates,
                ) = self.room.visible_actors_n_loots_n_gates(actor.name)

        proximity_dist = 2*self.room.unit_m
        for other, dist in all_visible_actors:
            if (
                        "dead"
                        in self.room.actors[other].character.current_state["conditions"]
                    ):
                pass
            else:
                if dist > proximity_dist:
                    actions_avail.append(f"move to {other} at {dist}m ")
                else:
                    actions_avail.append(f"talk to {other}")

        for other, dist in all_visible_loots:
            if dist > proximity_dist:
                actions_avail.append(f"move to {other} at {dist}m ")
            else:
                actions_avail.append(f"pick up {other}")

        for other, dist in all_visible_gates:
            if dist > proximity_dist:
                actions_avail.append(f"move to {other} at {dist}m ")
            else:
                actions_avail.append(f"quit map {other}")

                # Attack solutions
        actions_avail.extend(
                    self.build_attack_solutions(actor, all_visible_actors)
                )
        
        return actions_avail

    def action_pick_up_loot(self, actor:Actor, action:str)->str:
        """Action handler to pick up loot (remove form room, give to Actor's Character)"""
        loot = action.split("ick up")[-1].strip()
        equipment_name = self.room.loots[loot].name
        success = actor.character.add_item(equipment_name)
        if success:
            del self.room.loots[loot]
            outcome += f"\n{actor.name} has picked up {loot} {equipment_name}"
        else:
            outcome += f"\n{actor.name} cannot pick up {loot} {equipment_name}, too heavy to carry."
        return outcome

    def action_attack(self, actor, action)->str:
        """Action handler for Actor attacker hitting Actor defender """
        
        defender_name = action.split(" ")[1]
        weapon_name = action.split(";")[0].split("with")[-1].strip()
        defender = self.room.actors[defender_name]
        dmg = attack(actor.character, weapon_name, defender.character)
        is_dead = defender.character.get_damage(dmg)
        outcome = f"\n{defender_name} took {dmg} hp damage"
        if is_dead:
            outcome += f"and is dead"
            self.room.add_loot(defender.character.drop_loot(), defender.pos)
        return outcome

    def action_move_to_target(self, actor:Actor, remaining_moves:float, action:str)->Tuple[str,int]:
        """Action handler for Actor moving to a target (Actor, Loot or Gate)"""
        tgt = action.split(" ")[2]
        print(f"Trying to go to {tgt}")
        used_dist = self.room.move_actor_to_target(actor.name, tgt, remaining_moves)
        outcome = f"\n{actor.name} moved toward {tgt} over {used_dist}m"
        return outcome, used_dist

    def action_move_to_direction(self, actor:Actor, remaining_moves:float)->Tuple[str,int]:
        
        npc_bool = ("player" not in actor.character.faction)
               
        
        dir, _ = user_select_option(
            "In what direction ar you moving?",
            actor.character.situation()
            + "\n"
            + self.room.actor_situation(actor.name)
            + "\n"
            + actor.situation()
            + f"{actor.name} decided to move...",
            [
                "to the South of the map",
                "to the SouthWest of the map",
                "to the West of the map",
                "to the NorthWest of the map",
                "to the North of the map",
                "to the NorthEast of the map",
                "to the East of the map",
                "to the SouthEast of the map",
                "to the Center of the map",
            ],
            npc=npc_bool,
        )
        if npc_bool:  # non playable characters do not wonder about distance
            select_dist = "As far as possible"
        else:
            select_dist, _ = user_select_option(
                f"How far are you moving to the {dir}?",
                actor.character.situation()
                + "\n"
                + self.room.actor_situation(actor.name)
                + "\n"
                + actor.situation()
                + f"{actor.name} decided to move...",
                [
                    "As far as possible",
                    "Half of my range",
                    "Quarter of my range",
                    "Smallest movement possible",
                ],
                npc=npc_bool,
            )

        if select_dist == "As far as possible":
            actual_dist = remaining_moves
        elif select_dist == "Half of my range":
            actual_dist = remaining_moves // 2
        elif select_dist == "Quarter of my range":
            actual_dist = remaining_moves // 4
        elif select_dist == "Smallest movement possible":
            actual_dist = self.room.unit_m
        else:
            raise RuntimeError()
        heading = dir.split()[2]
        used_dist = self.room.move_actor_to_direction(actor.name, heading, actual_dist)
        outcome = f"\n{actor.name} moved {heading} over {used_dist}m"
        if used_dist == 0:
            outcome = f"\nMOVEMENT TO {heading} IMPOSSIBLE DUE TO AN OBSTACLE!"
            used_dist = self.room.unit_m
        return outcome, used_dist

    def build_attack_solutions(self, actor, all_visible_actors_):
        actions_avail = []
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
