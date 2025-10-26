import subprocess
import shutil
from typing import Tuple,List
from random import choice
from dndassist.storyprint import print_r, print_c, print_l, print_c_orange
LLM_MODEL = "llama3:latest"



def user_select_option(title: str, context:str , options: List[str], npc:bool=False) -> str:
    """Dialog with the user to select an option"""

    
    
    term_width = shutil.get_terminal_size((100, 20)).columns
    print_l(title)
    for i, option in enumerate(options):
        print_l(f" {i} - {option}")

    if npc is True:
        return auto_play_ollama(context, options)
    elif npc is None:
        return auto_play_random(context, options)
    
    select_option = True
    while select_option:
        act = input(" "*int(0.2*term_width) +"?")
        try:
            act = int(act)
        except ValueError:
            print_l(". enter a valid option nb.")
            continue
        if act > len(options) - 1:
            print_l(". enter a valid option nb.")
            continue
        if act < 0:
            print_l(". enter a valid option nb.")
            continue
        action = options[act]
        select_option = False

    return action,""


def user_select_quantity(title: str, context:str, min_: int, max_: int, bins:int = 6, npc:bool=False) -> int:
    """Dialog with the user to select a quantity"""
    step = (max_ - min_)/bins
    options = [str(min_)]
    for i in range(bins):
        options.append(str(int(round(min_ + (i+1)*step))))
    res, comment = user_select_option(title, context, options, npc=npc)

    return int(res),comment


def auto_play_random(context:str, possible_actions:List[str])-> Tuple[str,str]:
    """Failsafe random actions"""
    selected_action = choice(possible_actions)
    comment = "I don't know what I am doing"
    return selected_action, comment

def auto_play_ollama(context:str, possible_actions:List[str])-> Tuple[str,str]:
    """Ollama-based action selection"""

    indexed_actions = []
    for i, option in enumerate(possible_actions):
        indexed_actions.append(f" {i} - {option}")
    
    prompt = "You are controlling a NPC in dungeons and dragons. Here is the context of your turn:"
    prompt += context
    prompt += "\nHere are the possible actions:"
    prompt += "\n".join(indexed_actions)+"\n"
    prompt += """Given the context, 
    Your answer will start by the index of the selected action.
    Add a “>” character before this index.
    Add a “|” character after this index.
    Finish your answer by single, short, role-play sentence.
"""
    prompt += "Answer examples:"
    prompt += '> 6 | Liora says "You won’t see it coming..."'
    prompt += '> 4 | Liora moves swiftly and silently through the bushes.'
    prompt += '> 1 | The Elf eyes cautiously scan the terrain.'
   
    
    
    cmd = ["ollama", "run", LLM_MODEL,]
    print_c_orange(".  LLM running...")
    #print_c(prompt)
    try:
        result = subprocess.run(cmd, input = prompt, capture_output=True, text=True, timeout=30).stdout.strip()
    except subprocess.TimeoutExpired:
        print("⚠️ [LLM timeout]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    except Exception as e:
        print(f"⚠️ [LLM autoplay error: {e}]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    print_c_orange(result)
    
    if ">" in result:
        result = result.split(">")[-1]
    if "|" in result:
        index = result.split("|")[0]
        comment = result.split("|")[-1]  
    else:
        print(f"⚠️ [LLM autoplay error in result: {result}]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    option = possible_actions[int(index)]

    return option.strip(), comment.strip()
