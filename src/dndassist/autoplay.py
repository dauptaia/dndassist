import subprocess
import shutil
from typing import Tuple,List
from random import choice
from dndassist.storyprint import print_r, print_c, print_l, print_c_blue

LLM_MODEL = "llama3:latest"
# LLM_TEMPERATURE=0.0
# SYSTEM_PROMPT = "You are a player of a simplified dungeons and dragons game. Given a NPC context, you select the next action of this NPC."
# from langchain_ollama import OllamaLLM
# MY_LLM = OllamaLLM(model=LLM_MODEL, temperature=LLM_TEMPERATURE, system=SYSTEM_PROMPT)

def user_select_option(title: str, context:str , options: List[str], npc:bool=False) ->Tuple[str, str]:
    """Dialog with the user to select an option"""

    
    
    term_width = shutil.get_terminal_size((100, 20)).columns
    print_l(title)
    for i, option in enumerate(options):
        print_l(f" {i+1} - {option}")

    if npc is True:
        return auto_play_ollama(context, title, options)
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
        if act > len(options):
            print_l(". enter a valid option nb.")
            continue
        if act < 1:
            print_l(". enter a valid option nb.")
            continue
        action = options[act-1]
        select_option = False

    return action,"Manual input"


def user_select_quantity(title: str, context:str, min_: int, max_: int, bins:int = 5, npc:bool=False) -> int:
    """Dialog with the user to select a quantity"""
    step = (max_ - min_)/bins
    options = [str(min_)]
    for i in range(bins):
        options.append(str(int(round(min_ + (i+1)*step))))
    res, comment = user_select_option(title, context, options, npc=npc)

    return int(round(float(res))),comment


def auto_play_random(context:str, possible_actions:List[str])-> Tuple[str,str]:
    """Failsafe random actions"""
    selected_action = choice(possible_actions)
    comment = "I don't know what I am doing"
    return selected_action, comment

def auto_play_ollama(context:str, title:str, possible_actions:List[str], verbose:bool=True)-> Tuple[str,str]:
    """Ollama-based action selection"""

    indexed_actions = []
    for i, option in enumerate(possible_actions):
        indexed_actions.append(f" {i+1} - {option}")
    
    prompt = "You are controlling a NPC in dungeons and dragons. Here is the context of your turn:\n\n"
    prompt += context
    prompt += "\n\nYou must satisfy the objectives of this NPC."
    prompt += f"\n\nThe current decision to take is {title}"
    prompt += "\nFor your answer, YOU MUST SELECT ONE OF THE FOLLOWING INDEXED SENTENCES:\n"
    prompt += "\n".join(indexed_actions)
    prompt += f"""\n
    Add a “>” character before the index.
    Add a “<” character after the index.
    Add a “|” character after the sentence.
    Finish your answer by a very short explanation of the decision.
    Exemple for an attack:
      > 6 < attack beowulf | fafnir and beowulf belongs to opposed non-neutral factions.'
    Exemple for moving:
      > 3 < move North | Fafnir moves north as fast a possible, to satisfy his objective.'
"""
   
    print_c_blue(".  LLM running...")
    #print_c_blue(context)
    if verbose:
        print_c(prompt)
    
    cmd = ["ollama", "run", LLM_MODEL]
    try:
        result = subprocess.run(cmd, input = prompt, capture_output=True, text=True, timeout=30).stdout.strip()
    except subprocess.TimeoutExpired:
        print("⚠️ [LLM timeout]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    except Exception as e:
        print(f"⚠️ [LLM autoplay error: {e}]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    
    print_c_blue("__"+result+"__")
    
    if ">" in result:
        result = result.split(">")[-1]
    if "<" in result:
        index = result.split("<")[0]
    if "|" in result:
        comment = result.split("|")[-1]  
    else:
        print(f"⚠️ [LLM autoplay error in result: {result}]\n Switching to random autoplay...")
        return auto_play_random(context, possible_actions)
    idx= int(index)
    option = possible_actions[idx-1]

    return option.strip(), comment.strip()
