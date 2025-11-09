from typing import List,Tuple
import shutil
import textwrap
from colorama import Fore, Style, init

init(autoreset=True)

DEFAULT_MARGIN=4
DEFAULT_WRAP = 60


# def print_color(text: str, width: int = 4, primary: str = "WHITE", secondary: str = "YELLOW"):
#     """
#     Print text with left padding and color.
#     Use __double_underscores__ around words for secondary highlight.
#     """
#     # --- Prepare colors
#     primary_color = getattr(Fore, primary.upper(), Fore.WHITE)
#     secondary_color = getattr(Fore, secondary.upper(), Fore.YELLOW)

#     # --- insert pads 
#     term_width = shutil.get_terminal_size((100, 20)).columns
#     pad = (term_width-width) // 2
#     parts = text.split("\n")
#     parts = [" " * pad+ part for part in parts]
#     text = "\n".join(parts)

#     # --- Parse markup
#     parts = text.split("__")
#     colored = ""
#     for i, part in enumerate(parts):
#         if i % 2 == 1:
#             colored += secondary_color + part + primary_color
#         else:
#             colored += part

#     # --- Print with padding
#     print(primary_color + colored + Style.RESET_ALL)


# def storyprint(
#     text: str,
#     align: str = "left",
#     primary: str = "WHITE",
#     secondary: str = "YELLOW",
#     wrap_width: int = None
# ):
#     """
#     Print story text with alignment, wrapping, and color markup.
    
#     Markup: use __word__ for secondary color highlight.
#     """
    
    
#     # --- Detect terminal width
#     term_width = shutil.get_terminal_size((100, 20)).columns
    
#     max_line_len = 0
#     for line in text.split("\n"):
#         max_line_len = max(max_line_len, len(line))

#     if wrap_width is None:
#         wrap_width = int(term_width*0.6)
#     # --- Choose colors dynamically
#     primary_color = getattr(Fore, primary.upper(), Fore.WHITE)
#     secondary_color = getattr(Fore, secondary.upper(), Fore.YELLOW)

#     # --- Apply color markup
#     segments = []
#     parts = text.split("__")
#     for i, part in enumerate(parts):
#         if i % 2 == 1:
#             segments.append(secondary_color + part )
#         else:
#             segments.append(primary_color + part)
#     colored_text = "".join(segments) + Style.RESET_ALL
#     # --- Wrap text lines
#     wrapped_lines = []
#     for line in colored_text.split("\n"):
#         if len(line) > wrap_width:
#             wrapped_lines.extend(textwrap.wrap(line, width=wrap_width))
#         else:
#             wrapped_lines.append(line)

#     # --- Determine alignment
       
#     for line in wrapped_lines:
#         line = primary_color +line
#         if align == "right":
#             pad = term_width // 2 + int(0.1*term_width) 
#         elif align == "center": 
#             pad = max((term_width - wrap_width) // 2, 0)
#         else:
#             pad = + int(0.1*term_width) 
        
        
#         print(" " * pad + line)

# def print_l(text:str):
#     storyprint(
#         text,
#         align="left",
#         primary="GREY",
#         secondary="LIGHTGREY_EX",
#         wrap_width = None
#     )

# def print_r(text:str):
#     storyprint(
#         text,
#         align="right",
#         primary="GREEN",
#         secondary="LIGHTGREEN_EX",
#         wrap_width = None
#     )

# def print_c(text:str):
#     storyprint(
#         text,
#         align="center",
#         primary="LIGHTGREY_EX",
#         secondary="YELLOW",
#         wrap_width = 80
#     )


# def print_c_red(text:str):
#     storyprint(
#         text,
#         align="center",
#         primary="LIGHTRED_EX",
#         secondary="RED",
#         wrap_width = None
#     )


# def print_c_blue(text:str):
#     storyprint(
#         text,
#         align="center",
#         primary="BLUE",
#         secondary="LIGHTBLUE_EX",
#         wrap_width = None
#     )



def story_title(text:str, level=1):

    term_width = shutil.get_terminal_size((100, 20)).columns
    if "\n" in text:
        stest = text.split("\n")
        stest[0] = "__"+stest[0]+"__"
        text = "\n".join(stest)
    else:
        text = "__"+text+"__"
    
    if level ==0:
        banner_w = term_width//2
    
        ruler_char="="
    if level ==1:
        banner_w = term_width//4
    
        ruler_char="-"
        
    text = ruler_char*banner_w+"\n\n"+text+"\n\n"+ruler_char*banner_w
    text = story_print(text)

    
        
def print_color(text: str, color: str="dummy"):
    """Print some text to the terminal
    
    - Colors available are: white, red, blue, green
   
    """
    term_width = shutil.get_terminal_size((100, 20)).columns
    primary_color = getattr(Fore, color.upper(), Fore.WHITE)

    parts = text.split("\n")
    parts = [" " * (term_width//4) + part for part in parts]
    text = "\n".join(parts)
    text = primary_color + text +  Style.RESET_ALL
    print(text)


def story_print(text: str, color="dummy", justify="center"):
    """Print some text to the terminal
    
    - Colors available are: white, red, blue, green
    - If parts are dundered (__part__), a secondary color will be used to highlight 
   
    """
    # colorization comes 
    text, mask = split_text_mask(text)
    term_width = shutil.get_terminal_size((100, 20)).columns
    
    if justify == "center":
        width_c =  int(term_width*0.6)
        text = trim_text(text, width_c)
        mask = trim_text(mask, width_c)
        text = ctr_txt(text, size=term_width)
        mask= ctr_txt(mask, size=term_width)
    elif justify == "left":
        width_s =  int(term_width*0.5)
        text = trim_text(text, width_s)
        mask = trim_text(mask, width_s)
        text = pad_txt(text, size=term_width, margin=term_width//10)
        mask= pad_txt(mask, size=term_width, margin=term_width//10)
    elif justify == "right":
        width_s =  int(term_width*0.3)
        text = trim_text(text, width_s)
        mask = trim_text(mask, width_s)
        text = pad_txt(text, size=term_width, margin=term_width//10 * 7)
        mask= pad_txt(mask, size=term_width, margin=term_width//10 * 7)
    else :
        raise RuntimeError(f"Error {justify} not understood")
    text = colorize_text(text, mask, color=color)
    print(text)


def split_text_mask(text:str)->Tuple[str,str]:
    
    clean_txt=""
    mask=""
    mode = 1
    mode_markup = {
        1 : "-",
        -1 : "X"
    }
    last_char = "@"
    for char in text:
        if char == "_":
            if last_char =="_":
                mode *=-1
        elif char in [" ", "\n"]:
            clean_txt+=char
            mask += char
        else:
            clean_txt+=char
            mask += mode_markup[mode]
        last_char = char
        
    return clean_txt,mask


def trim_text(text:str, wrap_width=int)-> str:
    wrapped_lines = []
    for line in text.split("\n"):
        if len(line) > wrap_width:
            wrapped_lines.extend(textwrap.wrap(line, width=wrap_width))
        else:
            wrapped_lines.append(line)
    return "\n".join(wrapped_lines)

def colorize_text(text:str, mask:str, color="dummy")-> str:
    """Apply coloring to a text, independendly of breaklines"""
    primary_color = getattr(Fore, color.upper(), Fore.WHITE)
    secondary_color = getattr(Fore, "LIGHT"+color.upper()+"_EX", Fore.YELLOW)

    last_mchar="-"
    out =primary_color
    for char, mchar in zip(text, mask):
        if mchar =="X" and last_mchar == "-":
            out+= secondary_color
            last_mchar = "X"
        if mchar =="-" and last_mchar =="X":
            out+= primary_color
            last_mchar = "-"
        out += char   

    out+=Style.RESET_ALL
    return out


def print_3cols(col1: str, col2: str, col3: str, sep: str ="|"):

    col1, mcol1 = split_text_mask(col1)
    col2, mcol2 = split_text_mask(col2)
    col3, mcol3 = split_text_mask(col3)
    cols = merge_3cols(col1,col2, col3, sep=sep)
    cols_m = merge_3cols(mcol1,mcol2, mcol3, sep=" ")
    print(colorize_text(cols,cols_m))


def merge_3cols(col1: str, col2: str, col3: str, sep: str ="|")->str:
    """
    Merge 3 texts (breaklines as '\n')  into a single 3-column text 
    adjusted to the terminal
    """
    col1_l = col1.split("\n")
    col2_l = col2.split("\n")
    col3_l = col3.split("\n")
    max_ctr_w = max(*[len(line) for line in col2_l])
    height = max(len(col1_l),len(col2_l), len(col3_l))
    col1_l.extend(["" for _ in range(height- len(col1_l))])
    col2_l.extend(["" for _ in range(height- len(col2_l))])
    col3_l.extend(["" for _ in range(height- len(col3_l))])
    term_width = shutil.get_terminal_size((100, 20)).columns
    center_w = max_ctr_w+6
    sidew = (term_width-center_w)//2-1
    rows = [""]

    for i in range(height):
        rows.append(
            pad_str(col1_l[i],sidew, right_justified=True) 
            + sep + ctr_str(col2_l[i],center_w) 
            + sep + pad_str(col3_l[i],sidew) 
        )
    return "\n".join(rows)


def pad_txt(text:str, size:int, margin:int=2, right_justified:bool=False)->str:
    out=[]
    for line in text.split("\n"):
        out.append(pad_str(line, size=size, margin=margin, right_justified=right_justified))
    return "\n".join(out)

def pad_str(str_:str, size:int, margin:int=2, right_justified:bool=False)->str:
    """Pad string to the left or the right for a single line"""

    if "\n" in str_:
        raise RuntimeError("Use pad_txt for multiline str")
    if len(str_) > size:
        return str_[:size]
    if len(str_) > size-margin:
        return str_[:size-margin]
    curlen = len(str_.strip())
    spacesleft = size-margin-curlen

    if right_justified:
        return " "*spacesleft + str_.strip() + " "*margin
    else:
        return " "*margin + str_.strip() + " "*spacesleft

def ctr_txt(text:str, size:int)->str:
    out=[]
    for line in text.split("\n"):
        out.append(ctr_str(line, size=size))
    return "\n".join(out)

def ctr_str(str_:str, size:int)->str:
    """Pad string to the center"""
    if "\n" in str_:
        raise RuntimeError("Use ctr_txt for multiline str")
    str_ = str_.strip() 
    margins = (size- len(str_))//2
    return  " "*margins + str_ + " "*margins

story_print("lorem \nipsum __sic__ hamet", color="green", justify="right")
        
#story_title("big news\n did you know", level=1)

# map = """OOOaaaBBBCCC
# OOOaaaBBBCCC
# OOOaaaBBBCCC
# OOOaaa__H__BBCCC
# OOOaaaBBBCCC
# OOOaaaBBBCCC"""

# legend_left= """  O - 
#   o - 
#   X - void
#   . - ground
# : - special ground"""

# legend_right= """

# V = __Vihna__
# L = Rhohna

# """
# print_3cols(legend_left, map, legend_right)
# legend_left, left_m = split_text_mask(legend_left)
# legend_right, right_m = split_text_mask(legend_right)
# map, map_m = split_text_mask(map)
# cols = merge_3cols(legend_left,map, legend_right)
# cols_m = merge_3cols(left_m,map_m, right_m)
# print(colorize_text(cols,cols_m))