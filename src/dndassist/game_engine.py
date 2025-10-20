from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random

from dndassist.character import Character

from dndassist.room import RoomMap,Actor
from dndassist.autoroll import rolldice, max_dice

from datetime import datetime,timedelta
class GameEngine:
    room: RoomMap
    turn_counter: int = 0
    round_counter: int = 1
    

    def __init__(self, room:RoomMap):
        self.room: RoomMap = room
        self.round_counter:int = 0
        self.now: datetime = datetime(1000, 1, 1)+ timedelta(0,3600*12)
        self.run_round()
    
    # ---------- MAIN LOOP ----------
    def run_round(self):
        """Run one round (each actor acts once in initiative order)."""
        self.round_counter +=1
        print(f"\n=== ROUND {self.round_counter} START ===")
        print(f"\n   Room {self.room.name}, time {self.now.time()}")
        # 1️⃣ Filter out inactive actors
        active_actors = []
        for key,actor in self.room.actors.items():
            
            conditions =  actor.character.current_state["conditions"]
            if "unconscious" in conditions:
                continue
            if "stunned" in conditions:
                continue
            if "sleeping" in conditions:
                continue
            if  actor.character.current_state["current_hp"] <= 0:
                continue
            active_actors.append(actor)

        # 2️⃣ Compute initiative for all active actors
        initiative_order = self.compute_initiative(active_actors)

        # 3️⃣ Execute each actor's turn in initiative order
        for actor in initiative_order:
            self.now += timedelta(0,6)
            print(f"\n--- {actor.name}'s turn ---")

            remaining_moves =  actor.character.max_speed

            while remaining_moves >0 : 
                print(f"\n    Remaining moves: {remaining_moves}m")
                actions_avail = [ "look around", "move to a direction"]
                
                all_visible_actors_, all_visible_loots = self.room.visible_actors_n_loots(actor.name)

                
                for (other, dist) in all_visible_actors_:
                    if dist > 3:
                        actions_avail.append(f"move to person {other} at {dist}m ")
                    if dist <=3:
                        actions_avail.append(f"talk to {other}")

                for (other, dist) in all_visible_loots:
                    if dist > 3:
                        actions_avail.append(f"move to object {other} at {dist}m ")
                    if dist <=3:
                        actions_avail.append(f"pick up {other}")


                # Attack solutions
                faction = actor.character.faction
                visible_foes = []
                for (other, dist) in all_visible_actors_:
                    if self.room.actors[other].character.faction not in ["neutral", faction]:
                        visible_foes.append((other, dist) )
                
                for (other, dist) in visible_foes:
                    weapon,dmg = actor_attack_solutions(actor, dist)
                    actions_avail.append(f"attack {other} with {weapon} ({dmg})")
                
                print("Actions available:")
                for i, action in enumerate(actions_avail):
                    print(f" {i} - {action}")
                

                select_action = True
                while select_action:
                    act  = input("What action do you take?")
                    try:
                        act = int(act)
                    except ValueError:
                        print(". enter a valid action number")
                        continue
                    if act > len(actions_avail)-1:
                        print(". enter a valid action number")
                        continue
                    if act < 0:
                        print(". enter a valid action number")
                        continue
                    action = actions_avail[act]
                    select_action = False

                print(f"you selected: {action}")

                if action.startswith("move to"):
                    tgt = action.split(" ")[2]
                    if action.startswith("move to person"):
                        pos = self.room.actors[tgt].pos
                    elif action.startswith("move to object"):
                        pos = self.room.actors[tgt].pos
                    elif action.startswith("move to a direction"):
                        dir = input("which direction? (N,S,E, NW etc..)")
                                            
                        



            # Refresh temporary states
            #actor.start_turn()

            # 3.1 Determine possible actions
            # 3.2 Select action (AI or player input)
            #action = self.select_action(actor, actions)

            # 3.3 Execute the chosen action
            #self.execute_action(actor, action)

            # 3.4 End turn housekeeping
            #actor.end_turn()

        # 4️⃣ End of round
        print(f"\n=== ROUND {self.round_counter} END ===")

        cont = input("Continue? (y/n):")
        if cont=="y":
            self.run_round()

    # ---------- INITIATIVE ----------
    def compute_initiative(self, active_actors: List[Actor]) -> List[Actor]:
        """Compute initiative order based on dice rolls and dexterity modifiers."""
        initiatives = []
        for a in active_actors:
            d20,_ = rolldice("1d20",autoroll=True)
            init_value = a.character.attr_mod("dexterity") + d20
            initiatives.append((init_value, random.random(), a))
           # print(f"{a.name} initiative: {init_value}")
        # Sort by initiative descending (then random tie-breaker)
        initiatives.sort(key=lambda x: (-x[0], x[1]))

        ordered=  [a for (_, _, a) in initiatives]
        print("Order for this turn:")
        for i,a in enumerate(ordered):
            print(f"{i}, {a}")
        return ordered

def list_of_foes(actor: Actor, other_actors_:List[Actor])-> List[Actor]:
    """ return the foes of this actor"""
    out = []
    for other in other_actors_:
        if other.character.faction not in ["neutral", actor.character.faction]:
            out.append(other)
    return out

def actor_attack_solutions(actor: Actor, dist:int)-> Tuple[str, str]:
    """return strongest available weapon  in range"""
    max_dmg = 0
    weap = None
    print(actor.character.available_ranges(),"d", dist)
        
    for weapon, range, damage in actor.character.available_ranges():

        if range>= dist:
            if max_dice(damage) > max_dmg:
                weap, max_dmg = weapon,max_dice(damage)

    return weap, max_dmg

    # ---------- ACTION SELECTION ----------
    # def select_action(self, actor: "Character", actions: List[str]) -> str:
    #     """Decide which action to take. NPCs choose automatically, players are prompted."""
    #     if actor.is_npc:
    #         # Simple AI: choose first valid or random action
    #         return random.choice(actions)
    #     else:
    #         # For players, you can replace this with interactive input later
    #         print(f"\n{actor.name}, available actions: {', '.join(actions)}")
    #         choice = input("Choose your action: ").strip().lower()
    #         if choice in actions:
    #             return choice
    #         return "rest"

    # ---------- ACTION EXECUTION ----------
    # def execute_action(self, actor: "Character", action: str):
    #     """Stub for executing an action."""
    #     # In full system, you would dispatch to Action subclasses (AttackAction, MoveAction, etc.)
    #     if action == "attack":
    #         visible = self.room.visible_actors(actor)
    #         if visible:
    #             target = random.choice(visible)
    #             print(f"{actor.name} attacks {target.name}!")
    #         else:
    #             print(f"{actor.name} wants to attack, but sees no target.")
    #     elif action == "move":
    #         print(f"{actor.name} moves tactically.")
    #     elif action == "dash":
    #         print(f"{actor.name} dashes forward.")
    #     elif action == "rest":
    #         print(f"{actor.name} takes a moment to rest.")
    #     else:
    #         print(f"{actor.name} does nothing.")

    # ---------- GAME STATE ----------
    # def add_actor(self, actor: "Character"):
    #     self.actors.append(actor)

    # def remove_actor(self, actor: "Character"):
    #     self.actors = [a for a in self.actors if a != actor]

    # def print_log(self):
    #     print("\n".join(self.log))
