from typing import List
import shutil
import textwrap
from colorama import Fore, Style, init

init(autoreset=True)

DEFAULT_MARGIN=4
DEFAULT_WRAP = 60





def print_color(text: str, width: int = 4, primary: str = "WHITE", secondary: str = "YELLOW"):
    """
    Print text with left padding and color.
    Use __double_underscores__ around words for secondary highlight.
    """
    # --- Prepare colors
    primary_color = getattr(Fore, primary.upper(), Fore.WHITE)
    secondary_color = getattr(Fore, secondary.upper(), Fore.YELLOW)

    # --- insert pads 
    term_width = shutil.get_terminal_size((100, 20)).columns
    pad = (term_width-width) // 2
    parts = text.split("\n")
    parts = [" " * pad+ part for part in parts]
    text = "\n".join(parts)

    # --- Parse markup
    parts = text.split("__")
    colored = ""
    for i, part in enumerate(parts):
        if i % 2 == 1:
            colored += secondary_color + part + primary_color
        else:
            colored += part

    # --- Print with padding
    print(primary_color + colored + Style.RESET_ALL)


def storyprint(
    text: str,
    align: str = "left",
    primary: str = "WHITE",
    secondary: str = "YELLOW",
    wrap_width: int = None
):
    """
    Print story text with alignment, wrapping, and color markup.
    
    Markup: use __word__ for secondary color highlight.
    """
    
    
    # --- Detect terminal width
    term_width = shutil.get_terminal_size((100, 20)).columns
    
    max_line_len = 0
    for line in text.split("\n"):
        max_line_len = max(max_line_len, len(line))

    if wrap_width is None:
        wrap_width = int(term_width*0.6)
    # --- Choose colors dynamically
    primary_color = getattr(Fore, primary.upper(), Fore.WHITE)
    secondary_color = getattr(Fore, secondary.upper(), Fore.YELLOW)

    # --- Apply color markup
    segments = []
    parts = text.split("__")
    for i, part in enumerate(parts):
        if i % 2 == 1:
            segments.append(secondary_color + part )
        else:
            segments.append(primary_color + part)
    colored_text = "".join(segments) + Style.RESET_ALL
    # --- Wrap text lines
    wrapped_lines = []
    for line in colored_text.split("\n"):
        if len(line) > wrap_width:
            wrapped_lines.extend(textwrap.wrap(line, width=wrap_width))
        else:
            wrapped_lines.append(line)

    # --- Determine alignment
       
    for line in wrapped_lines:
        line = primary_color +line
        if align == "right":
            pad = term_width // 2 + int(0.2*term_width) 
        elif align == "center": 
            pad = max((term_width - wrap_width) // 2, 0)
        else:
            pad = + int(0.1*term_width) 
        
        
        print(" " * pad + line)

def print_l(text:str):
    storyprint(
        text,
        align="left",
        primary="GREY",
        secondary="LIGHTGREY_EX",
        wrap_width = None
    )

def print_r(text:str):
    storyprint(
        text,
        align="right",
        primary="GREEN",
        secondary="LIGHTGREEN_EX",
        wrap_width = None
    )

def print_c(text:str):
    storyprint(
        text,
        align="center",
        primary="LIGHTGREY_EX",
        secondary="YELLOW",
        wrap_width = 80
    )


def print_c_red(text:str):
    storyprint(
        text,
        align="center",
        primary="LIGHTRED_EX",
        secondary="RED",
        wrap_width = None
    )


def print_c_orange(text:str):
    storyprint(
        text,
        align="center",
        primary="YELLOW",
        secondary="LIGHTYELLOW_EX",
        wrap_width = None
    )


