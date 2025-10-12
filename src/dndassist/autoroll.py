
from typing import Tuple
from random import randint


def rolldice(dice:str, autoroll=False, advantage:int=0)-> Tuple[ int, float] :

    mod = 0
    modstr=""
    dice_ = dice
    if "+" in dice:
        modstr = " without modifier"
        mod=int(dice.split("+")[-1])
        dice_ = dice.split("+")[0]
    
    
    nb= int(dice_.split("d")[0])
    faces= int(dice_.split("d")[1])
    
    min_ = nb 
    max_ = nb*faces

    if autoroll:
        result = randint(min_, max_)
        if advantage <= 1:
            for i in range(-advantage):
                print(i)
                result = min(randint(min_, max_), result)
        if advantage >= 1:
            for i in range(advantage):
                print(i)
                result = max(randint(min_, max_), result)
    else:
        done=False
        while not done: 
            result = int(input(f"Enter dice {dice} result {modstr}:"))+mod
            if result>= min_ and result<= max_:
                done=True    

    normed = (result-min_)/(max_-min_)

    result += mod

    print(f"Result of {dice}: {result} ({int(normed*100)}%)")
    return result, normed
  