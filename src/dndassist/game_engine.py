import os
import yaml
from typing import List, Dict, Optional, Tuple
import random
import time
from dndassist.gates import Gates
from dndassist.room import RoomMap, Actor, Loot
from dndassist.autoroll import rolldice, max_dice
from dndassist.attack import attack, offensive_spell
from dndassist.storyprint import (
    story_title,
    story_print,
    print_color,
    print_3cols
)
from dndassist.level_up import check_new_level
from dndassist.autoplay import (
    user_select_option,user_ask_coordinates
)
from dndassist.isometric_renderer import (
    IsometricRenderer
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
    def __init__(self, wkdir: str, reload_from_save:int=None):
        print_color(banner, color="yellow")
        time.sleep(0.1)
        self.wkdir=wkdir
        self.adventure_log = []

        self.adventure_log.append(banner)

        self.gates: Gates = Gates()
        self.players_sorted_list: List[str] = None
        self.room: RoomMap = None
        if reload_from_save is None:
            self.round_counter: int = 0
            self.startup()
        else:
            self.load_game(reload_from_save)
        self.main_loop()

    def startup(self):
        # load gates
        self.gates.load(self.wkdir, "gates.yaml")
        # load players 
        with open(os.path.join(self.wkdir, "players.yaml"), "r") as fin:
            players_data = yaml.safe_load(fin)

        self.players_sorted_list = sorted([ actor_name for actor_name in players_data["players"].keys()])

        list_players_actors = [ ]
        for pdict in players_data["players"].values():
            pdict["state"] = "manual"
            list_players_actors.append(Actor.from_dict(pdict, self.wkdir))
        # startup room
        zero_date = datetime(1000, 10, 5, 12, 00)
        self.change_room(players_data["room"],list_players_actors,zero_date)
    
    def save_game(self):
        save = {
            "round_counter" : self.round_counter,
            "now" : self.now,
            "room" : self.room.name,
            "players_sorted_list" : self.players_sorted_list,
            "actors": {},
    #        "loots": {}
        }

        for actor_name, actor in self.room.actors.items():
            save["actors"][actor_name] = actor.to_dict_with_character_data()
        # for loot_name, loot in self.room.loots.items():
        #     save["loots"][loot_name] = loot.to_dict()
        
        savefile = os.path.join(self.wkdir,"Saves",f"Save_dnd_turn_{ self.round_counter}.yaml")
        story_print(f"Saving game at __{savefile}__",color="green", justify="right")
        
        with open(savefile,"w") as fout:
            yaml.safe_dump(save, fout)
    
    def load_game(self, round_counter:int):
        
        savefile = os.path.join(self.wkdir,"Saves",f"Save_dnd_turn_{round_counter}.yaml")
        story_print(f"Loading game __{savefile}__", color="green", justify="right")
        try:
            with open(savefile,"r") as fin:
                save = yaml.safe_load(fin)
        except FileNotFoundError:
            story_print(f"File __{savefile}__ not found try again!", color="red", justify="left")
            return
        self.gates.load(self.wkdir, "gates.yaml") #just in case
        self.round_counter = save["round_counter"]
        self.now = save["now"]
        self.players_sorted_list = save["players_sorted_list"]
        
        self.room = RoomMap.load(self.wkdir, save["room"] + ".yaml")
        list_gates = self.gates.gates_by_room(save["room"] )
        for g_name, g_pos, g_desc, d_obj_play in list_gates:
            self.room.add_gate(g_name, g_pos, g_desc)

        for actor_name, actor_dict in save["actors"].items():
            self.room.actors[actor_name]=Actor.from_dict_with_character_data(actor_dict)
        # for loot_name, loot_dict in save["loots"].items():
        #     self.room.loots[loot_name]=Loot.from_dict(loot_dict)
        
    def change_room(self,destination_room:str, travelers:List[Actor], out_time:datetime):
        
        self.room = RoomMap.load(self.wkdir, destination_room + ".yaml")
        list_gates = self.gates.gates_by_room(destination_room)
        for g_name, g_pos, g_desc, d_obj_play in list_gates:
            self.room.add_gate(g_name, g_pos, g_desc)

        for actor in travelers:
            story_print(f"Add Actor {actor.name} to {destination_room}",color="green", justify="right")
            self.room.actors[actor.name]=actor
        
        self.room.spread_actors_loots()

        #list_names=" -"+"\n -".join(self.room.actors.keys())
        #print_(list_names)
        self.now=out_time
        
    def main_loop(self):
        running = True
        while running:
            running = self.run_one_round()
        
        story_print("End of main loop", color="red")

    def run_one_round(self):
        """Run one round (each actor acts once in initiative order)."""
        self.round_counter += 1

        turn_mark = f"ROUND {self.round_counter} START"
        turn_mark += f"\n   Room {self.room.name}, time {self.now.time()}"

        story_title(turn_mark, level=1)

        self.adventure_log.append(turn_mark)

        # 1️⃣ Filter out inactive actors
        active_actors = []
        for  actor in self.room.actors.values():
            skip = False
            for skip_state in ["dead", "resting"]:
                if skip_state in actor.character.current_state["conditions"]:
                    skip = True
            if  actor.state == "idle":
                story_print(f"[{actor.name}] is idle, skipping this turn",color="green", justify="right")
                skip = True
            if skip:
                continue

            active_actors.append(actor)
        # 2️⃣ Compute initiative for all active actors
        initiative_order = self.compute_initiative(active_actors)
        

        # 3️⃣ Execute each actor's turn in initiative order
        for actor in initiative_order:
            time.sleep(0.1)
            # skip is actor is dead or unconcious
            skip = False
            for skip_state in ["dead"]:
                if skip_state in actor.character.current_state["conditions"]:
                    skip = True
            if skip:
                continue

            self.now += timedelta(0, 6)
            self.room.print_map(actor_name=actor.name)
            # ----- build context ---

            self.adventure_log.append("\n\n" + f"--- __{actor.name}__'s turn {actor.pos}---")
            remaining_moves = actor.character.max_distance()
            remaining_actions = 100
            while remaining_moves >= self.room.unit_m and remaining_actions > 0:
                time.sleep(0.1)
                story_print(f"""
    --- __{actor.name}__'s turn ---
    pos: {actor.pos}, view height: {actor.height+actor.climbed} m
    Remaining moves: __{remaining_moves}__m
""", color="grey",justify="left")
                actions_avail = self.build_all_actions_available_to_actor(actor)
                #story_print("Actions available:\n"+"\n".join(actions_avail), color="grey",justify="left")
                npc_bool = actor.state == "auto"
                action, comment = user_select_option(
                    "What action will you do?",
                    actor.character.situation()
                    + "\n"  # what is not in the room
                    + self.room.look_around_report(actor.name)
                    + "\n"
                    + actor.situation(),  # what is in view
                    actions_avail,
                    npc=npc_bool,
                )
                actor.last_action = action
                story_print("__" + action + "__", color="grey")
                story_print(comment, color="grey")
            
                self.adventure_log.append(action)
                self.adventure_log.append(comment)

                outcome = ""
                if action.startswith("round finished"):
                    remaining_moves = 0
                    remaining_actions = 0
                elif action.startswith("show view"):
                    self.room.ask_tactical_view(actor_name=actor.name)
                elif action.startswith("show status"):
                    str1 , str2, str3 = actor.status_str()
                    print_3cols(str1 , str2, str3 )
                elif action.startswith("stand watch"):
                    remaining_actions -= 100
                elif action.startswith("climb"):
                    remaining_moves -= self.climb_adjacent_tile(actor, action)
                    if remaining_moves > 0:
                        self.room.print_map(actor_name=actor.name)

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
                        story_print(f"Action {action} not understood", color="red", justify="left")
                        remaining_actions -= 100
                        remaining_moves = 0

                    if used_dist == 0:
                        remaining_moves -= self.room.unit_m
                    else:
                        remaining_moves -= used_dist

                elif action.startswith("attack"):
                    remaining_actions -= 100
                    outcome = self.action_attack(actor, action)

                elif action.startswith("hex"):
                    remaining_actions -= 100
                    outcome = self.action_hex(actor, action)

                elif action.startswith("pick up"):
                    remaining_actions -= 100
                    outcome = self.action_pick_up_loot(actor, action)

                elif action.startswith("talk to"):
                    remaining_actions -= 100
                    npc_actor = self.room.actors[action.split()[2]]
                    name, cost_str, reward_str, xp = npc_actor.talk_to()
                    if cost_str is None:
                        outcome = f"[{npc_actor.name}] {name})"
                    else:
                        if actor.give_something(cost_str):
                            npc_actor.get_equipment(cost_str)
                            kind, reward = actor.get_something(reward_str)
                            self.room.xp_accumulated += xp
                            outcome = f"[{actor.name}] gave {cost_str} to [{npc_actor.name}]"
                            outcome += f"\n[{npc_actor.name}] gave {kind} {reward} to [{actor.name}]"
                            outcome += f"\nParty gained {xp}"
                        else:
                            outcome = f"[{actor.name}] cannot give {cost_str} to [{npc_actor.name}]"
                            

                elif action.startswith("quit map"):
                    remaining_actions -= 100
                    gate_name = action.split()[2]
                    gate_desc = action.split(":")[-1].strip()   
                    self.gates.new_traveler(actor,gate_name)
                    del self.room.actors[actor.name]
                    outcome = f"actor {actor.name} enters {gate_desc}."
                
                else:
                    raise RuntimeError(f"Action {action} not understood")    

                actor.last_outcome = outcome
                self.adventure_log.append(outcome + "\n")
                story_print("__" + outcome + "__", color="grey")
                with open(LOGFILE, "w") as fout:
                    fout.write("\n".join(self.adventure_log))

        story_print(f"\n=== ROUND __{self.round_counter}__ END ===")


        self.save_game()


        continue_game = self.end_of_round_dialog()
       
        if continue_game is False:
            story_print("Thank you for playing dnd assist...", color="green")
            return False
                
        # end of round, if a gate is full, players are changing rooms
        if self.gates.travelers_sorted_list() == self.players_sorted_list:        
            # Must compute and distribute XP points when leaving the room
            self.distribute_xp_points()
            travelers, destination_room, out_time = self.gates.resolve_gates(self.room.name, self.now)
            self.change_room(destination_room,travelers,out_time)

        return True

    def climb_adjacent_tile(self, actor: Actor, action:str)->int:
        """What happen when climbing up, equal or down
        actor can lose HP if critical fails
        return the distance consumed by the motion
        """
        pos_to_climb = ""
        for  char  in action.split(":")[0] :
            if char.isdigit() or char == ",":
                pos_to_climb+=char
        x,y = pos_to_climb.split(',')
        dest_pos = (int(x),int(y))
        dest_tile = self.room.tiles[dest_pos]
        actor_tile = self.room.tiles[actor.pos]
        climb_gap = int((dest_tile.elevation+dest_tile.climb_height) - (actor_tile.elevation +actor.climbed))

        if climb_gap > 6:
            story_print(f"Cannot climb up {climb_gap}m.", color="green", justify="right")
            return 0
        elif climb_gap < -6:
            story_print(f"Cannot climb down {climb_gap}m.", color="green", justify="right")
            return 0
        elif climb_gap > 0:
            difficulty = int(climb_gap * 5) # 1m 5 Very Easy, 3m 15 Average, 6m 30 very hard
            story_print(f" Climb up {climb_gap}m \n Difficulty {difficulty} \n", color="white", justify="left")
            roll, success,dex_mod = actor.rolldice("1d20", "dexterity")
            if success == 1.0: #perfect climb
                story_print(f"Climb perfect!", color="green", justify="right")
                actor.climbed = dest_tile.climb_height
                actor.pos = dest_pos
                return int(climb_gap)
            elif success == 0.0: #failed climb
                story_print(f"Climb failed!", color="green", justify="right")
                roll, _ , _ = actor.rolldice("1d4")
                actor.character.current_state.current_hp -= roll
                return int(climb_gap*3)
            else:
                if roll + dex_mod >= difficulty:
                    story_print(f"Climb successful", color="green", justify="right")
                    actor.climbed = dest_tile.climb_height
                    actor.pos = dest_pos
                    return int(climb_gap*3) 
                else:
                    story_print(f"Climb failed", color="green", justify="right")
                    return int(climb_gap*3) 
        elif climb_gap == 0:
            difficulty = 5
            roll, success,dex_mod = actor.rolldice("1d20", "dexterity")
            if roll + dex_mod >= difficulty:
                story_print(f"Climb successful", color="green", justify="right")
                actor.climbed = dest_tile.climb_height
                actor.pos = dest_pos
                return self.room.unit_m
            else:
                story_print(f"Climb  failed", color="green", justify="right") 
                return self.room.unit_m

        elif climb_gap < 0:
            difficulty = int(abs(climb_gap) * 5) # 1m 5 Very Easy, 3m 15 Average, 6m 30 very hard
            story_print(f" Climb down {climb_gap}m \n Difficulty {difficulty} \n", color="white", justify="left")
            roll, success,dex_mod = actor.rolldice("1d20", "dexterity")
            if success == 1.0: #perfect climb
                story_print(f"Climb down perfect!", color="green", justify="right")
                actor.climbed = dest_tile.climb_height
                actor.pos = dest_pos
                return int(climb_gap)
            elif success == 0.0: #failed climb
                story_print(f"Climb down CRITICAL FAIL!", color="green", justify="right")
                roll, _ = actor.rolldice("1d4")
                actor.character.current_state.current_hp -= roll
                actor.climbed = dest_tile.climb_height
                actor.pos = dest_pos
                return int(climb_gap*3)
            else :
                if roll + dex_mod >= difficulty:
                    story_print(f"Climb down successful", color="green", justify="right")
                    actor.climbed = dest_tile.climb_height
                    actor.pos = dest_pos
                    return int(climb_gap*3)
                else:
                    story_print(f"Climb down failed", color="green", justify="right")
                    return int(climb_gap*3)
                

        
    def distribute_xp_points(self):
        """Distribute XP to players"""
        
        xp_share = self.room.xp_accumulated // len(self.players_sorted_list)
        self.room.xp_accumulated = 0
        for actor in self.gates.travelers_actors():
            story_print(f"__[{actor.name}]__ has gained __{xp_share}__ XP points!" )
            actor.character.xp += xp_share
            
            # Levelling up...
            lvl, prof, hp_increase, abilities_increase = check_new_level(
                actor.character.xp, 
                actor.character.xp+xp_share, 
                actor.character.hit_dices_max[0], 
                actor.character.attr_mod("constitution"))
            if lvl > actor.character.level:
                story_print(f"__[{actor.name}]__ level up ! {actor.character.level}->{lvl}" )
                actor.character.level = lvl
            if prof > actor.character.proficiency_bonus:
                story_print(f"__[{actor.name}]__ proficiency_bonus increased ! {actor.character.proficiency_bonus}->{prof}" )
                actor.character.proficiency_bonus = prof
            if hp_increase:
                story_print(f"__[{actor.name}]__ hit points increased ! +{hp_increase}" )
                actor.character.max_hp += hp_increase
            for ability in abilities_increase:
                story_print(f"__[{actor.name}]__ ability {ability} increased ! +1" )
                actor.character.attributes[ability]+=1            

            

        
    def end_of_round_dialog(self):
        """Game master dialog to fine-tune actions btw rounds"""
        end_of_turn_options= [
            "Continue",
            "Show full Map",
            "Reload last turn",
            "Change actor(s) status : idle < > manual < > auto",
            "Move actor(s) to coordinates",
            "Send player(s) to gate",
            "Short rest",
            "Long rest",
            "Exit game",
        ]
        continue_game = None
        gamemaster_dialog_running = True
        while gamemaster_dialog_running:
            option,_ = user_select_option(
            "Turn has ended, what do you want to do?",
            "Main dialog for the game master",
            end_of_turn_options)

            if option == "Continue":
                gamemaster_dialog_running = False
                continue_game = True
            elif option == "Show full Map":
                self.room.print_map()
            elif option ==  "Exit game":
                continue_game = False
                gamemaster_dialog_running =False
            elif option ==  "Reload last turn":
                self.load_game(self.round_counter-1)
                
            elif option == "Change actor(s) status : idle < > manual < > auto":
                targets_options = ["all_actors", "all_players", "all_npcs"]
                for actor_name in self.room.actors:
                    if actor_name in self.players_sorted_list:
                        targets_options.append(f"{actor_name} : player")
                    else:
                        targets_options.append(f"{actor_name} : npc")

                target,_ = user_select_option(
                    "What actors must change status?",
                    "no context provided",
                    targets_options)

                if target == "all_actors":
                    target_list = self.players_sorted_list+self.room.npc_ordered_list
                elif target == "all_players":
                    target_list = self.players_sorted_list
                elif target == "all_npcs":
                    target_list = self.room.npc_ordered_list
                else:
                    target_list = [target]
                new_state,_ = user_select_option(
                    "What is the new status? ",
                    "no context provided",
                    ["idle", "manual", "auto"])
                for actor_name in target_list:
                    self.room.actors[actor_name].state = new_state
                    story_print(f"[{actor_name}] state is now __{new_state}__", color="green", justify="right")
                pass
            elif option == "Move actor(s) to coordinates":
                targets_options = ["all_actors", "all_players", "all_npcs"]
                for actor_name in self.room.actors:
                    if actor_name in self.players_sorted_list:
                        targets_options.append(f"{actor_name} : player")
                    else:
                        targets_options.append(f"{actor_name} : npc")

                target,_ = user_select_option(
                    "What actors must change coordinates?",
                    "no context provided",
                    targets_options)

                if target == "all_actors":
                    target_list = self.players_sorted_list+self.room.npc_ordered_list
                elif target == "all_players":
                    target_list = self.players_sorted_list
                elif target == "all_npcs":
                    target_list = self.room.npc_ordered_list
                else:
                    tname = target.split(":")[0].strip()
                    target_list = [tname]
                new_pos = user_ask_coordinates(
                    "Coordinates of the position? ",
                    self.room.width,
                    self.room.height)
                
                for actor_name in target_list:
                    new_pos = self.room._free_pos_nearest(new_pos)
                    self.room.actors[actor_name].pos = new_pos
                    story_print(f"[{actor_name}] new coords is now __{new_pos}__", color="green", justify="right")

            elif option == "Send player(s) to gate" :
                gate_list = [f"{gate.name}: {gate.description}" for gate in self.room.gates.values()]
                target,_ = user_select_option(
                    "What gate?",
                    "no context provided",
                    gate_list)
                target_gate = target.split(':')[0]
                for actor_name,actor in self.room.actors.items():
                    if actor_name in self.players_sorted_list:
                        self.gates.new_traveler(actor,target_gate)
            elif option == "Short rest" :
                self.now += timedelta(0, 3600)
                for actor_name,actor in self.room.actors.items():
                    if actor_name in self.players_sorted_list:

                        hit_mask = self.room.actors[actor_name].character.hit_dices_mask
                        hit_dices =  self.room.actors[actor_name].character.hit_dices

                        if sum(hit_mask) == 0:
                            story_print(f"[{actor_name}] have no hit_dices left]")
                        else:

                            remain_hit_dices = ["no recovery"] + [v for i,v in enumerate(hit_dices) if hit_mask[i]] 
                            hit_dice, _ = user_select_option(
                                f"What hit dice [{actor_name}] will use? ",
                                f"[{actor_name}] is having a short rest",
                                remain_hit_dices
                            )
                            if hit_dice == "no recovery":
                                continue
                            idx = remain_hit_dices.index(hit_dice)-1
                            self.room.actors[actor_name].character.hit_dices_mask[idx] = False
                            roll, success, mod = self.room.actors[actor_name].rolldice(hit_dice, attr="constitution")
                            story_print(f"[{actor_name}] get {roll}+{mod} (const) HP")
                            chp = self.room.actors[actor_name].character.current_state["current_hp"] 
                            mhp = self.room.actors[actor_name].character.max_hp
                            self.room.actors[actor_name].character.current_state["current_hp"] = min(mhp, chp+roll+mod)
            elif option == "Long rest" :
                self.now += timedelta(0, 8*3600)
                for actor_name,actor in self.room.actors.items():
                    if actor_name in self.players_sorted_list:
                        if self.room.actors[actor_name].character.current_state["current_hp"] < 1:
                            continue
                        self.room.actors[actor_name].character.current_state["current_hp"] = self.room.actors[actor_name].character.max_hp
                        hd_m =  self.room.actors[actor_name].character.hit_dices_mask
                        gain = max(1, (len(hd_m)-sum(hd_m))//2)
                        for i,val in enumerate(hd_m):
                            if val is False:
                                self.room.actors[actor_name].character.hit_dices_mask[i] = True
                                gain -=1
                            if gain == 0:
                                break
            else:
                raise RuntimeError(f"End of turn action {option} not understood...")
        if continue_game is None:
            raise RuntimeError("GameMaster dialog ended unexpectedly...")
        return continue_game
                

        
    def build_all_actions_available_to_actor(self, actor:Actor)-> List[str]:
        """ Create a list of possible actions for an Actor"""

        actions_avail = ["round finished"]
        
        climb_up_dir, climb_up_pos, climb_down_dir , climb_down_pos= self.room.tiles_to_climb(actor.pos)
        if climb_up_dir:
            for dir,pos in zip(climb_up_dir,climb_up_pos):
                actions_avail.append(f"climbUp {dir} {pos} : {self.room.tiles[pos].description}")
        
        if actor.climbed > 0:
            for dir,pos in zip(climb_down_dir,climb_down_pos):
                actions_avail.append(f"climbDown {dir} {pos} : ground")
        
        if actor.climbed == 0:
            actions_avail.append( "move in direction")

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
                    if actor.climbed == 0:
                        actions_avail.append(f"move to {other} at {dist}m ")
                else:
                    actions_avail.append(f"talk to {other}")

        for other, dist in all_visible_loots:
            if dist > proximity_dist:
                if actor.climbed == 0: 
                    actions_avail.append(f"move to {other} at {dist}m ")
            else:
                actions_avail.append(f"pick up {other}")

        for other, dist in all_visible_gates:
            if dist > proximity_dist:
                if actor.climbed == 0: 
                    actions_avail.append(f"move to {other} at {dist}m ")
            else:
                actions_avail.append(f"quit map {other}")

                # Attack solutions
        actions_avail.extend(
                    self.build_attack_solutions(actor, all_visible_actors)
                )
        
        actions_avail.append("show view")
        actions_avail.append("show status")
        
        return actions_avail

    def action_pick_up_loot(self, actor:Actor, action:str)->str:
        """Action handler to pick up loot (remove form room, give to Actor's Character)"""
        loot_key = action.split("ick up")[-1].strip()
        item_name = self.room.loots[loot_key].name
        success = actor.character.add_item(item_name)
        if success:
            del self.room.loots[loot_key]
            outcome = f"\n{actor.name} has picked up {loot_key} {item_name}"
        else:
            outcome = f"\n{actor.name} cannot pick up {loot_key} {item_name}, too heavy to carry."
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
            outcome += f" and is dead"
            self.room.add_loot(defender.character.drop_loot(), defender.pos)
            self.room.xp_accumulated += defender.xp_to_gain
        return outcome

    def action_hex(self, actor, action)->str:
        """Action handler for Actor attacker hexing Actor defender """
        
        defender_name = action.split(" ")[1]
        weapon_name = action.split(";")[0].split("with")[-1].strip()
        defender = self.room.actors[defender_name]
        dmg = offensive_spell(actor.character, weapon_name, defender.character)
        is_dead = defender.character.get_damage(dmg)
        outcome = f"\n{defender_name} took {dmg} hp damage"
        if is_dead:
            outcome += f" and is dead"
            self.room.add_loot(defender.character.drop_loot(), defender.pos)
            self.room.xp_accumulated += defender.xp_to_gain
        return outcome

    def action_move_to_target(self, actor:Actor, remaining_moves:float, action:str)->Tuple[str,int]:
        """Action handler for Actor moving to a target (Actor, Loot or Gate)"""
        tgt = action.split(" ")[2]
        print(f"Trying to go to {tgt}")
        used_dist = self.room.move_actor_to_target(actor.name, tgt, remaining_moves)
        outcome = f"\n{actor.name} moved toward {tgt} over {used_dist}m"
        return outcome, used_dist

    def action_move_to_direction(self, actor:Actor, remaining_moves:float)->Tuple[str,int]:
        

        npc_bool = actor.state == "auto"
        
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
            spell, dmg = actor_hex_solutions(actor, dist)
            if spell is not None:
                actions_avail.append(
                    f"hex {other} with {spell} ; damage max {dmg} HP"
                )
        return actions_avail

    # ---------- INITIATIVE ----------
    def compute_initiative(self, active_actors: List[Actor]) -> List[Actor]:
        """Compute initiative order based on dice rolls and dexterity modifiers."""
        initiatives = []
        for a in active_actors:
            story_print(f"Initiative roll for [{a.name}]",color="green", justify="right")
            d20, _ = rolldice("1d20", autoroll=True)
            init_value = a.character.attr_mod("dexterity") + d20
            initiatives.append((init_value, random.random(), a))
        # print(f"{a.name} initiative: {init_value}")
        # Sort by initiative descending (then random tie-breaker)
        initiatives.sort(key=lambda x: (-x[0], x[1]))

        ordered = [a for (_, _, a) in initiatives]
        story_print("Order for this turn:",color="green", justify="right")
        for i, a in enumerate(ordered):
            story_print(f".  {i}, __[{a.name}]__",color="green", justify="right")
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
    for weapon, range, damage_dice in actor.character.available_ranges():
        if range >= dist:
            if max_dice(damage_dice) > max_dmg:
                weap, max_dmg = weapon, max_dice(damage_dice)

    return weap, max_dmg

def actor_hex_solutions(actor: Actor, dist: int) -> Tuple[str, str]:
    """return strongest available hex  in range"""
    max_dmg = 0
    hex = None
    for spell, range, damage_dice in actor.character.available_hex_ranges():
        if range >= dist:
            if max_dice(damage_dice) > max_dmg:
                hex, max_dmg = spell, max_dice(damage_dice)

    return hex, max_dmg