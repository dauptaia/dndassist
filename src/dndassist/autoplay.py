import subprocess
from typing import Tuple,List
from random import choice

LLM_MODEL = "llama3:latest"


context = """
--- liora's turn ---
Liora Dawnblade is a neutral Elf Ranger character  of level 3 (xp 850)
He belongs to the faction player, with the alignment Chaotic Good
Prefers ranged combat.
Currently:
His hit points are  10
His objectives are stand watch
His last action was  idle
liora is facing SE.
Close:
left, There is a tall tree (3m)
front, There is a ravine (2m)
right, There is a ravine (3m)
Mid:
left, There is a tall tree (11m), a ravine (9m)
front, There is a ravine (10m), selra (10m), a wall (16m)
right, There is a wall (15m), a ravine (9m)

    Remaining moves: 35m
"""
actions_dialog = [
"0 - round finished",
"1 - look around",
"2 - move in direction",
"3 - move to selra at 10m ",
"4 - attack selra with Longbow ; damage max 8 HP",
]

def auto_play_random(context:str, possible_actions:List[str])-> Tuple[str,str]:
    """Failsafe random actions"""
    selected_action = choice(possible_actions)
    comment = "I don't know what I am doing"
    return selected_action, comment

def auto_play_ollama(context:str, possible_actions:List[str])-> Tuple[str,str]:
    """Ollama-based action selection"""
    prompt = "You are controlling a NPC in dungeons and dragons. Here is the context of your turn:"
    prompt += context
    prompt += "Here are the possible actions strings:"
    prompt += "\n".join(possible_actions)+"\n"
    prompt += """Given the context, 
    select the most appropriate action.
    Then, start you answer with the action string.
    Add a “|” character to your answer 
    Finish you answer by single, short, role-play sentence.
"""
    prompt += "Answer examples:"
    prompt += '4 - attack selra with Longbow ; damage max 8 HP | Liora says "You won’t see it coming..."'
    prompt += '2 - move in direction | Liora moves swiftly and silently through the bushes.'
    prompt += '1 - look around | The Elf eyes cautiously scan the terrain.'
    
    cmd = ["ollama", "run", LLM_MODEL,]
    try:
        result = subprocess.run(cmd, input = prompt, capture_output=True, text=True, timeout=30).stdout.strip()
    except subprocess.TimeoutExpired:
        print("⚠️ [LLM timeout]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    except Exception as e:
        print(f"⚠️ [LLM autoplay error: {e}]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    if "-" not in result:
        print("⚠️ LLM autoplay answer ill-formerd \n{result} \n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    
    index = int(result.split("-")[0].strip())
    if "|" not in result:
        comment = ""
    else:
        comment = result.split("|")[-1].strip()
    return possible_actions[index], comment

print(auto_play_random(context, actions_dialog))
print(auto_play_random(context, actions_dialog))
print(auto_play_random(context, actions_dialog))
print(auto_play_ollama(context, actions_dialog))
print(auto_play_ollama(context, actions_dialog))
print(auto_play_ollama(context, actions_dialog))