
from typing import List, Tuple
import random
from dndassist.autoplay import user_select_option
"""
interactions:
      smalltalk:
      - what strangers like ya'r doin' here. No business with ya!
      paths:
      - cost : money | 10 cp
        name: item for the quest
        reward: equipment | bottle of beer
      - cost : money | 1 sp
        name: echange silver pieces for copper pieces 
        reward: money | 10 cp
      - cost : equipment | dagger
        name: info on quest2 
        reward: information | this quest is blue
      - cost : impress me 
        name: map of the region
        reward: equipment | map"""


class Interaction:
    def __init__(self,smalltalk: List[str], paths: list = None):

        self.smalltalk_list = smalltalk
        self.paths=paths
    
    def to_dict(self)-> dict:
        out = {
            "smalltalk":self.smalltalk_list,
            "paths":self.paths
        }
        return out


    def smalltalk(self):
        return random.choice(self.smalltalk_list)

    def try_talking(self)-> Tuple[str, str, str]:
        if self.paths is None:
            return self.smalltalk(), None, None
        
        list_options = ["forget it"]
        for path in self.paths:
            if path['cost'] is not None:
                list_options.append(f"{path['name']}, cost {path['cost']}")
        option,_ = user_select_option(
            self.smalltalk(),
            context="",
            options=list_options
        )

        if option == "forget it":
            return None,None,None
        idx = list_options.index(option) - 1
        return self.paths[idx]["name"], self.paths[idx]["cost"], self.paths[idx]["reward"]
    
        
            