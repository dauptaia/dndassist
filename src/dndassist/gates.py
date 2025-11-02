from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import yaml
import os
from datetime import datetime

from dndassist.room import Actor

class Gates:
    """Handle all the gates available"""
    def __init__(self):
        self.gates_dict: Dict[str, Gate]=None

    def load(self, wkdir, path):
        full_path = os.path.join(wkdir,path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"No such Gates file: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        self.gates_dict={}
        for gate, gate_data in data.items():
            self.gates_dict[gate] = Gate.from_dict(gate_data)
            
    def travelers_sorted_list(self):
        if self._active_gate() is None:
            return []
        list_actors =  self.gates_dict[self._active_gate()].travelers
        list_names = [actor.name for actor in list_actors]
        return sorted(list_names)

    def travelers_actors(self):
        if self._active_gate() is None:
            return []
        list_actors =  self.gates_dict[self._active_gate()].travelers
        return list_actors
    
    def new_traveler(self, traveler_actor:Actor, gate:str):
        self.gates_dict[gate].new_traveler(traveler_actor)
       
    def _active_gate(self):
        for gname,gdata in self.gates_dict.items():
            if gdata.travelers:
                return gname
        return None
        
    def resolve_gates(self,room:str=None, in_time:datetime=None)-> Tuple[List[str], str, datetime]:
        gname = self._active_gate()
        if gname is None:
            raise RuntimeError()
        return self.gates_dict[gname].purge_gate(room=room,in_time=in_time)
        

    def __repr__(self):
        out =[]
        for g in self.gates_dict.values():
            out.append(g.__repr__())
        return "\n".join(out)

    def save(self, wkdir, path):
        full_path = os.path.join(wkdir,path)
        data=[]
        for gate in self.self.gates_dict.values():
            data.append(asdict(gate))
        
        with open(full_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)
    
    def gates_by_room(self,room:str)-> List[Tuple[str, Tuple[int,int], str, str]]:
        list_gates= []
        for gname, gdata in self.gates_dict.items():
            if gdata.room0 == room:
                list_gates.append(
                    (gname, gdata.pos0, gdata.description, gdata.player_objective_from_0)
                )
            if gdata.room1 == room:
                list_gates.append(
                    (gname, gdata.pos1, gdata.description, gdata.player_objective_from_1)
                )
        return list_gates

@dataclass
class Gate:
    """A Gate allow actors to move from one map to the other
    
    Only players can move around
    Gates can add an objective to a player
    """
    
    # --- Identity ---
    name: str # Short lower case name
    room0: str # use None for the initial gate
    pos0: Tuple[int,int] # position in room 0
    player_objective_from_0: str
    room1: str # use None for the final gate
    pos1: Tuple[int,int] # position in room 1
    player_objective_from_1: str
    travelers: List[Actor]
    duration: int = 1 # One hour to take this path
    oneway: bool = False # True if path work only one way
    description: str = "A narrow path between trough dense vegetation"

    @classmethod
    def from_dict(cls, dict_:dict):

        cls_ = cls(**dict_)
        cls_.pos0 = tuple(cls_.pos0)
        cls_.pos1 = tuple(cls_.pos1)
        return cls_
        
    def new_traveler(self, traveler_actor:Actor):
        self.travelers.append(traveler_actor)
   
    def purge_gate(self,room:str=None, in_time:datetime= None)-> Tuple[List[str], str, datetime]:
        """Resolve this gate, returning travelers, destination room, and time of exit"""
        if room == self.room0:
            destination_room=self.room1
            destination_pos=self.pos1
            objective=self.player_objective_from_1
        elif room == self.room1:
            destination_room=self.room0
            destination_pos=self.pos0
            objective=self.player_objective_from_0
        else:
            raise RuntimeError(f"Room {room} is neither room1 or room2 of Gate {self.name}")
        
        if in_time is None:
            out_time = datetime.now()
        else:
            out_time=in_time
        
        travelers_out = []
        travelers_names = []
        for actor in self.travelers:
            actor.pos = destination_pos
            actor.objectives.append(objective)
            travelers_out.append(actor)
            travelers_names.append(actor.name)
        msg = "At "+ str(out_time)+", " +", ".join(travelers_names) + " arrived in "+destination_room
        print(msg)
        self.travelers = []
        return travelers_out, destination_room, out_time


