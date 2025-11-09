import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple, List, Optional
import textwrap, math, yaml, json
import heapq
import math
import numpy as np
import textwrap
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from dndassist.themes import Theme
from dndassist.character import Character
from dndassist.matrix_utils import get_crown_pos, compute_nap_of_earth, compute_transparency,return_relative_pos
from dndassist.dialog import Dialog

from dndassist.storyprint import story_print, print_3cols

# constants (tweakable)
UNIT_M = 1.5  # 1 tile/unit = 1.5 meters (matches your band example)
MAX_UNITS = 50  # max scanning distance in units
CLOSE_MAX_U = 6  # <=6 units = close (<9m)
MID_MIN_U, MID_MAX_U = 7, 20  # 7..20 units = mid (9m..30m)
FAR_MIN_U = 21  # >20 units = far
RAY_STEP_DEG = 4  # angular resolution for rays across a sector
RAY_STEP_UNIT = 0.5  # step length along each ray (in units)
PLURAL_THRESHOLD = 3  # >3 items -> pluralize (user requested >3 -> plural)


# facing -> base angle in degrees (0 = north/up, increases clockwise)
FACING_ANGLE = {
    "North": 0,
    "NorthEast": 45,
    "East": 90,
    "SouthEast": 135,
    "South": 180,
    "SouthWest": 225,
    "West": 270,
    "NorthWest": 315,
}


def _angle_to_vector(angle_deg: float):
    """Return (dx, dy) vector for grid coordinates where x increases to right, y increases downward.
    We define angle=0 as NORTH (up / -y)."""
    rad = math.radians(angle_deg)
    dx = math.sin(rad)  # x component (right positive)
    dy = -math.cos(rad)  # y component (down positive) => -cos so 0deg -> (0,-1)
    return dx, dy


# -----------------------------------------------------------
#  BASIC TILE
# -----------------------------------------------------------
@dataclass
class Tile:
    symbol: str
    difficulty: int =  1
    blocks_view: bool = False # shall be removed
    elevation: float = 0
    opacity: float =  0.01 #  1% of opacity per m
    obstacle_height: float =  0
    climb_height: float =  0
    description: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


# -----------------------------------------------------------
#  MOVEABLE ELEMENTS
# -----------------------------------------------------------
@dataclass
class Actor:
    name: str
    symbol: str
    pos: Tuple[int, int]
    facing: str = "North"
    height: float = 1.7 # height of the creature, standing
    xp_to_gain: int = 10
    xp_accumulated: int = 0
    sprite: str = None
    last_action: str = None
    last_outcome: str = None
    state: str = "idle" # one of "idle", "manual" (manual input),  "auto" (auto played by a LLM)
    aggro: str = None
    dialog: Dialog = None
    objectives: List[str] = field(
        default_factory=list
    )
    character: Character = None
    """This class is the simplified actor, the actual player in the Game.

    We keep here attributes that are ROOM BOUNDED

    through attribute character, you get the complete DND Character template of the NPC/player
    Several actors can be built on the same character template!
    """

    # def turn(self, direction: str):
    #     self.facing = direction

    # def move(self, dx: int, dy: int):
    #     x, y = self.pos
    #     self.pos = (x + dx, y + dy)

    def __repr__(self):
        out = f"{self.name} ({self.symbol}), pos: {self.pos}"
        return out

    def situation(self):
        """Return the current situation of the actor"""
        if self.character.gender == "male":
            pronoun = "He"
            possessive = "His"
        if self.character.gender == "female":
            pronoun = "She"
            possessive = "Her"
        else:
            pronoun = "It"
            possessive = "Its"
        situation = ""
        if len(self.objectives)==0:
            situation += f"{pronoun} has no current objectives."
        elif len(self.objectives) == 1:
            situation += f"{possessive}'s objective is: {self.objectives[0]}"
        elif len(self.objectives) == 1:
            _objectives_list =" -"+'\n - '.join(self.objectives)
            situation += f"{possessive}'s objectives are\n - : {_objectives_list}"

        if self.last_action is not None:
            situation += (
                f"\n {possessive} last action was  {self.last_action}"
            )
        if self.last_outcome is not None:
            situation += f"\n {possessive} last outcome was  {self.last_outcome}"
        if self.aggro is not None:
            situation += f"\n {pronoun} wants to attack {self.aggro}"
        return situation

    @classmethod
    def from_dict(cls, d, wkdir):
        d["pos"] = tuple(
            d["pos"]
        )  # when read from safe yaml , tuple were stored as list
        #transforma character string into character
        char =  Character.load(wkdir, d["character"])
        char.name = d["name"] #impose actor name in character description
        if "dialog" in d:
            dname = d["dialog"]
            d["dialog"] = Dialog.from_yaml(wkdir,d["dialog"])
            d["dialog"].name=dname
        d["character"] = char 
        return cls(**d)
    
    def to_dict_with_character_data(self):
        data = asdict(self)
        if self.dialog is not None:
            data["dialog"]=self.dialog.name
        return data

    @classmethod
    def from_dict_with_character_data(cls,data):
        data["pos"] = tuple(
            data["pos"]
        )
        data["character"] = Character(**data["character"])
        return cls(**data)

    # def to_dict(self):
    #     return asdict(self)


@dataclass
class Loot:
    name: str
    symbol: str
    sprite: str
    index: int
    pos: Tuple[int, int]
    height: float = 0.5 # height, 0.5m
    

    def __repr__(self):
        out = f"{self.name} ({self.symbol}), pos: {self.pos}"
        return out

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        d["pos"] = tuple(
            d["pos"]
        )  # when read from safe yaml , tuple were stored as list
        return cls(**d)



@dataclass
class RoomGate:
    name: str
    # symbol: str
    # sprite: str
    # index: intheifgh
    pos: Tuple[int, int]
    description: str
    height: float = 3
    
    def __repr__(self):
        out = f"{self.name} ,pos: {self.pos}"
        return out

    def save_to_dict(self):
        return self.to_dict()

    @classmethod
    def load_from_dict(self,dict):
        return self.from_dict(dict)
    # def to_dict(self):
    #     return asdict(self)

    # @classmethod
    # def from_dict(cls, d):
    #     d["pos"] = tuple(
    #         d["pos"]
    #     )  # when read from safe yaml , tuple were stored as list
    #     return cls(**d)


# -----------------------------------------------------------
#  MAP CLASS
# -----------------------------------------------------------
@dataclass
class RoomMap:
    name: str
    wkdir: str
    ascii_map: str
    description: str
    tiles: Dict[Tuple[int, int], Tile]
    theme: Theme
    width: int
    height: int
    elevation: np.ndarray
    opacity: np.ndarray
    unit_m: float = 1.5
    npc_ordered_list: List[str] = None
    actors: Dict[str, Actor] = field(default_factory=dict)
    loots: Dict[str, Loot] = field(default_factory=dict)
    gates: Dict[str, RoomGate] = field(default_factory=dict)
    
    def unit_to_m(self, u: float) -> int:
        """Convert map units to meters (rounded integer)."""
        return int(round(u * self.unit_m))

    def m_to_unit(self, u: float) -> int:
        """Convert map meters to units (rounded integer)."""
        return int(round(u / self.unit_m))

    def add_gate(self, name: str, pos: Tuple[int, int], description: str):
        """Turn a tile into a  gate"""
        self.tiles[pos] = Tile(
            symbol="G",
            description=name + ":" + description,
        )
        self.gates[name]= RoomGate(
            name,
            pos,
            description
        )
        #print(f"Adding gate {name} at {pos}")

    def spread_actors_loots(self):

        for actor in self.actors.values():
            actor.pos = self._free_pos_nearest(actor.pos)
        for loot in self.loots.values():
            loot.pos = self._free_pos_nearest(loot.pos)

    def _free_pos_nearest(self, pos: Tuple[int, int], max_crown=3) -> Tuple[int, int]:
        """Return the free position nearest of pos,
        maximum of 2 crowns"""

        def _is_occupied(test_pos):
            """Check that this position is neither an obstacle or filled with someone"""
            if self.tiles[test_pos].symbol in ["X", "O", "W", "G"]:
                return True
            for actor in self.actors.values():
                if actor.pos == test_pos:
                    return True
            return False

        if not _is_occupied(pos):
            print(pos, " is free")
            return pos

        for rad in range(1, max_crown + 1):
            elligible_pos = get_crown_pos(pos, self.width, self.height, rad)
            for _pos in elligible_pos:
                if not _is_occupied(_pos):
                    return _pos
        raise RuntimeError(f"Could not find a free position around {pos}")

    # to refine
    def add_loot(self, name: str, pos: Tuple[int, int], symbol="l"):
        """add a loot in the room.

        Loots are identified by their unique names, handled outside the room concept.
        - If name already present, the addition is refused
        """
        if name in self.loots:
            print(f"Loot {name} is already in the room")
        else:
            self.loots[name] = Actor(name, symbol, pos)

    def del_loot(self, name: str):
        """remove an actor in the room"""
        if name in self.loots:
            del self.loots[name]
        else:
            print(f"Loot {name} is not in the room")

    # -------------------------------------------
    def pick_up_loot(self, actor_name: str):
        actor = self.actors[actor_name]
        for key, loot in list(self.loots.items()):
            if loot.pos == actor.pos:
                print(f"{actor.name} picked up {loot.name}.")
                del self.loots[key]

    # -------------------------------------------

    def draw_map(self, save_pdf: bool = False, filename: str = "map.pdf"):
        """
        Draws a black & white map with automatic scaling (autozoom) to fit an A4 landscape page.
        Adds name, description, and legend.
        Optionally saves the figure as a PDF.
        """
        # --- A4 landscape size (in inches for matplotlib) ---
        fig_w, fig_h = 11.7, 8.3  # A4 landscape

        # Compute a scaling factor to fit the map in the left ~70% of the width
        legend_fraction = 0.25  # space for legend
        map_fraction = 1.0 - legend_fraction
        map_max_w = fig_w * map_fraction
        map_max_h = fig_h * 0.85  # leave top/bottom margins

        # Tile-based aspect ratio
        if self.width / self.height > map_max_w / map_max_h:
            zoom = map_max_w / self.width
        else:
            zoom = map_max_h / self.height
        # general adusjt
        zoom = zoom * 0.1

        shift_x = 2 * zoom
        shift_y = 3 * zoom

        # --- Create figure ---
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("white")

        # --- Draw Tiles ---
        for (x, y), tile in self.tiles.items():
            if tile.symbol in ("/", "", "X"):  # skip void
                continue

            rect = patches.Rectangle(
                (shift_x + x * zoom, shift_y + (self.height - y - 1) * zoom),
                zoom,
                zoom,
                linewidth=0.5,
                edgecolor="black",
                facecolor="white",
            )
            ax.add_patch(rect)
            sym = tile.symbol
            if sym == " ":
                sym = ":"

            ax.text(
                shift_x + (x + 0.5) * zoom,
                shift_y + (self.height - y - 0.5) * zoom,
                sym,
                ha="center",
                va="center",
                fontsize=8,
                color="black",
                family="monospace",
            )

        # --- Adjust axes limits so map fits nicely ---
        # ax.set_xlim(0, self.width * zoom)
        # ax.set_ylim(0, self.height * zoom)
        # ax.invert_yaxis()

        # --- Legend ---
        unique_tiles = {}
        for tile in self.tiles.values():
            if tile.symbol not in ("/", "", "X") and tile.symbol not in unique_tiles:
                unique_tiles[tile.symbol] = tile.description

        # Legend position in figure coordinates
        legend_ax = fig.add_axes([0.75, 0.1, 0.22, 0.8])
        legend_ax.axis("off")
        legend_ax.text(
            0,
            1,
            "Legend",
            ha="left",
            va="top",
            fontsize=10,
            weight="bold",
            color="black",
        )

        y_pos = 0.9
        for sym, desc in unique_tiles.items():
            if sym == " ":
                sym = ":"
            legend_ax.text(
                0,
                y_pos,
                f"{sym}  -  {desc}",
                ha="left",
                va="center",
                fontsize=8,
                color="black",
                family="monospace",
            )
            y_pos -= 0.05

        # --- Map Name & Description (footer) ---
        fig.text(
            0.5,
            0.12,
            self.name,
            ha="center",
            va="center",
            fontsize=12,
            weight="bold",
            color="black",
        )
        fig.text(
            0.5,
            0.08,
            "\n".join(textwrap.wrap(self.description, 80)),
            ha="center",
            va="center",
            fontsize=9,
            color="black",
        )

        plt.subplots_adjust(left=0.05, right=0.7, top=0.95, bottom=0.1)

        # --- Save or show ---
        if save_pdf:
            fig.savefig(filename, format="pdf", bbox_inches="tight")
            plt.close(fig)
            print(f"Map saved to {filename}")
        else:
            plt.show()

    def render_ascii(
        self, for_save: bool = False, path: List[Tuple[int, int]]=None, actor_name:str=None
    ) -> str:
        
        grid = [
            [
                self.tiles.get((x, y), Tile("/", True, False, "")).symbol
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

        # exit with simple output if for_svae
        if for_save:
            return "\n".join("".join(row) for row in grid)

        # Change ground into visible symbol
        for y in range(self.height):
            for x in range(self.width):
                if grid[y][x] == ".":
                    grid[y][x] = ":"
                elif grid[y][x] == " ":
                    grid[y][x] = "."
        
        

        # add path
        if path is not None:
            for x, y in path:
                grid[y][x] = "__*__"
        


        # add loots
        for loot in self.loots.values():
                x, y = loot.pos
                grid[y][x] = "__" + loot.symbol + "__"
        
        # add actors
        for actor in self.actors.values():
            x, y = actor.pos
            grid[y][x] = "__" + actor.symbol + "__"
        
        # make obstructed tiles invisible
        if actor_name is not None:
            actor = self.actors[actor_name]
            noe = compute_nap_of_earth(self.elevation,actor.pos,h0= actor.height, dx=self.unit_m)
            fog_of_war = compute_transparency(self.opacity,actor.pos, dx=self.unit_m)
            for y in range(self.height):
                for x in range(self.width):
                    if noe[x,y] > 0:
                        grid[y][x] = " "
                    if fog_of_war[x,y] < 0.5:
                        grid[y][x] = " "
        # add coordinates
        tip = ["."]
        top = ["."]
        idx = -1
        tens = 0
        for x in range(self.width):
            idx += 1
            if idx == 10:
                idx = 0
                tens +=1
                top.append(f"__{str(idx)}__")
                tip.append(f"__{str(tens)}__")
            else:    
                top.append(f"__{str(idx)}__")
                tip.append(" ")
            
        grid.insert(0, top)
        grid.insert(0, tip)
        

        idx = -2
        for y in range(self.height + 1):
            if idx <= -1:
                grid[y].insert(0, " ")
                grid[y].append(" .")
            else:
                grid[y].insert(0, f"__{idx: 2d}__")
                grid[y].append(f"__{idx: 2d}__")
            idx += 1
            # if idx == 10:
            #     idx = 0
        return "\n".join(" ".join(row) for row in grid)
        
    def print_map(self, actor_name:str=None, path: List[Tuple[int, int]] = None):
        map = self.render_ascii(path=path, actor_name=actor_name)

        left = ["\n\nActors:"]
        for actor in self.actors.values():
            left.append(f" {actor.name} : __{actor.symbol}__")
        left.append("\n\nLoots:")
        for loot in self.loots.values():
            left.append(f" {loot.name} : __{loot.symbol}__")
        left = "\n".join(left)

        right =[f"\n Map: {self.name}\n"]
        for sym, tile_spec in self.theme.tiles.items():
            #sym = tile_spec.symbol
            if sym == ".":
                sym = ":"
            if sym == " ":
                sym = "."
                
            right.append(f"{sym} : {tile_spec.description}")

        right = "\n".join(right)
    
        center = map 
        print_3cols(left,center, right)

        
    def actor_situation(self, actor_name: str):
        actor = self.actors[actor_name]
        x, y = actor.pos
        map_locate_x = ""
        map_locate_y = ""
        if x > 0.66 * self.width:
            map_locate_x = "East"
        if x > 0.85 * self.width:
            map_locate_x = "far East"
        if x < 0.33 * self.width:
            map_locate_x = "West"
        if x < 0.15 * self.width:
            map_locate_x = "far West"
        if y > 0.66 * self.height:
            map_locate_y = "South"
        if y > 0.85 * self.height:
            map_locate_y = "far South"
        if y < 0.33 * self.height:
            map_locate_y = "North"
        if y < 0.15 * self.height:
            map_locate_y = "far North"

        if map_locate_x == "" and map_locate_y == "":
            locate = "center"
        else:
            locate = ",".join([map_locate_x, map_locate_y]).strip(",")
        situation = f"{actor_name} is currently at the {locate} of the map"
        return situation

    


    def visible_actors_loots_gates(self, pos_0, view_height):
        noe = compute_nap_of_earth(self.elevation,pos_0,h0= view_height, dx=self.unit_m)
        visible_actors=[]
        for actor in self.actors.values():
            # If 75% of actor heigh is hidden by nap of earth, item is nit visible
            if noe[*actor.pos] < actor.height * 0.75:
                visible_actors.append(actor.name)
        
        visible_loots=[]
        for loot in self.loots.values():
            if noe[*loot.pos] < loot.height * 0.75:
                visible_loots.append(loot.name)
        visible_gates=[]
        
        for gate in self.gates.values():
            if noe[*gate.pos] < gate.height * 0.75:
                visible_gates.append(gate.name)
        
        return visible_actors,visible_loots,visible_gates
        
                

    def look_around_report(self, actor_name: str)->str:
        actor = self.actors[actor_name]
        visible_actors,visible_loots,visible_gates=self.visible_actors_loots_gates(actor.pos,actor.height)
        report =[]
        for other_name in visible_actors:
            other = self.actors[other_name]
            dist,dir=return_relative_pos(actor.pos,other.pos, self.unit_m)
            report.append(f"Actor {other_name} is {dist}m {dir}")
        for other_name in visible_loots:
            other = self.loots[other_name]
            dist,dir=return_relative_pos(actor.pos,other.pos, self.unit_m)
            report.append(f"Object {other_name} is {dist}m {dir}")
        for other_name in visible_gates:
            other = self.gates[other_name]
            dist,dir=return_relative_pos(actor.pos,other.pos, self.unit_m)
            report.append(f"Gate {other_name} is {dist}m {dir}")
        return "\n".join(report)



    def visible_actors_n_loots_n_gates(
        self, actor_name: str
    ) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], List[Tuple[str, int]]]:
        """
        True LoS description using multiple rays per sector.
        Returns a list of (visible actors distance in m)
        """
        actor = self.actors[actor_name]
        visible_actors,visible_loots,visible_gates=self.visible_actors_loots_gates(actor.pos,actor.height)
        _visible_actors =[]
        for other_name in visible_actors:
            other = self.actors[other_name]
            dist = math.hypot(
                (actor.pos[0]-other.pos[0])*self.unit_m,
                (actor.pos[1]-other.pos[1])*self.unit_m,
                actor.height-other.height
            )
            _visible_actors.append((other_name,round(dist)))

        _visible_loots =[]
        for other_name in visible_loots:
            other = self.loots[other_name]
            dist = math.hypot(
                (actor.pos[0]-other.pos[0])*self.unit_m,
                (actor.pos[1]-other.pos[1])*self.unit_m,
                actor.height-other.height
            )
            _visible_loots.append((other_name,round(dist)))
        
        _visible_gates =[]
        for other_name in visible_gates:
            other = self.gates[other_name]
            dist = math.hypot(
                (actor.pos[0]-other.pos[0])*self.unit_m,
                (actor.pos[1]-other.pos[1])*self.unit_m,
                actor.height-other.height
            )
            _visible_gates.append((other_name,round(dist)))
        
        return _visible_actors, _visible_loots, _visible_gates

    def _neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        """Return all valid 8-directional neighbors with cost multiplier."""
        deltas = [
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (1, 1, math.sqrt(2)),
        ]
        neighbors = []
        for dx, dy, mult in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny, self.unit_to_m(mult)))
        return neighbors

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic for A*."""
        (x1, y1), (x2, y2) = a, b
        return math.hypot(x2 - x1, y2 - y1)

    # -------------------------------------------
    def move_actor_to_direction(self, actor_name: str, dir: str, distance_m: int):
        """Move an actor toward a direction.

        Return used distance in m"""
        actor = self.actors[actor_name]

        x0, y0 = actor.pos
        if dir == "Center":
            dy = self.height // 2 - y0
            dx = self.width // 2 - x0
        elif dir == "North":
            dy = -self.m_to_unit(distance_m)
            dx = 0
        elif dir == "NorthEast":
            dx = self.m_to_unit(distance_m * 1.414)
            dy = -self.m_to_unit(distance_m * 1.414)
        elif dir == "East":
            dx = self.m_to_unit(distance_m)
            dy = 0
        elif dir == "SouthEast":
            dx = self.m_to_unit(distance_m * 1.414)
            dy = self.m_to_unit(distance_m * 1.414)
        elif dir == "South":
            dy = self.m_to_unit(distance_m)
            dx = 0
        elif dir == "SouthWest":
            dx = -self.m_to_unit(distance_m * 1.414)
            dy = self.m_to_unit(distance_m * 1.414)
        elif dir == "West":
            dx = -self.m_to_unit(distance_m)
            dy = 0
        elif dir == "NorthWest":
            dx = -self.m_to_unit(distance_m * 1.414)
            dy = -self.m_to_unit(distance_m * 1.414)
        else:
            raise RuntimeError(f"Error, direction {dir} is not understood...")
        x0, y0 = actor.pos
        path, used_dist = self.move_to(
            x0, y0, x0 + dx, y0 + dy, max_distance_m=distance_m
        )
        # print(f"Inital pos: {x0},{y0}")
        # print(f"Aiming pos: {x0+dx},{y0+dy}")
        actor.pos = path[-1]
        
        self.print_map(path=path, actor_name=actor_name)
        story_print(f"final pos {actor.pos}", color="green", justify="right")
        

        # new_facing = ""
        # try:
        #     prev_pos = path[-2]
        #     if actor.pos[1] > prev_pos[1]:
        #         new_facing += "South"
        #     if actor.pos[1] < prev_pos[1]:
        #         new_facing += "North"
        #     if actor.pos[0] > prev_pos[0]:
        #         new_facing += "East"
        #     if actor.pos[0] < prev_pos[0]:
        #         new_facing += "West"
        # except IndexError:
        #     pass

        # if new_facing != "":
        #     actor.facing = new_facing

        # xf, yf = actor.pos
        # print(f"final pos: {xf},{yf}")
        return used_dist

    def move_actor_to_target(
        self, actor_name: str, target_name: str, distance_m: int
    ) -> int:
        """Move an actor toward a target , loot or actors.

        Return used distance in m"""
        actor = self.actors[actor_name]
        x0, y0 = actor.pos
        target = None
        if target_name in self.actors:
            target = self.actors[target_name]
            x1, y1 = target.pos
            print(f"going from {x0},{y0} to actor {target_name} at {x1},{y1}")
        elif target_name in self.loots:
            target = self.loots[target_name]
            x1, y1 = target.pos
            print(f"going from {x0},{y0} to loot {target_name} at {x1},{y1}")
        elif target_name in self.gates:
            target = self.gates[target_name]
            x1, y1 = target.pos
            print(f"going from {x0},{y0} to gates {target_name} at {x1},{y1}")
        else:
            print(f"Target {target_name} not found in actors nor loots")
            return None

        path, used_dist = self.move_to(x0, y0, x1, y1, max_distance_m=distance_m)
        actor.pos = path[-1]
        self.print_map(path=path, actor_name=actor_name)
        story_print(f"final pos {actor.pos}", color="green", justify="right")
        return used_dist

    def move_to(
        self, x0: int, y0: int, x: int, y: int, max_distance_m: Optional[float] = None
    ) -> Tuple[List[Tuple[int, int]], int]:
        """
        Find shortest path from (x0, y0) to (x, y) using A* algorithm.
        Accounts for tile difficulty, diagonal movement, and movement limit.

        If `max_distance` is provided, the path stops when movement allowance is exceeded.
        Returns (path, used distance in meters).
        """
        start, goal = (x0, y0), (x, y)

        frontier = [(0, start)]  # priority queue (f_score, position)
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}

        best_reached = start  # last reachable position if max_distance stops us

        occupied_positions = [actor.pos for actor in self.actors.values()]

        while frontier:
            _, current = heapq.heappop(frontier)

            # If max distance exceeded, stop at the farthest reachable tile
            if max_distance_m is not None and g_score[current] > max_distance_m:
                continue

            # If we reached the goal before exceeding distance, stop
            if current == goal:
                best_reached = goal
                break

            for nx, ny, mult in self._neighbors(*current):
                tile = self.tiles[(nx, ny)]
                if tile.difficulty >= 999:  # impassable
                    continue
                if (nx, ny) in occupied_positions:  # position occupied by an actor
                    continue

                tentative_g = g_score[current] + tile.difficulty * mult

                if max_distance_m is not None and tentative_g > max_distance_m:
                    continue  # skip unreachable within move allowance

                if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                    g_score[(nx, ny)] = tentative_g
                    f_score = tentative_g + self._heuristic((nx, ny), goal)
                    heapq.heappush(frontier, (f_score, (nx, ny)))
                    came_from[(nx, ny)] = current
                    if self._heuristic((nx, ny), goal) < self._heuristic(
                        best_reached, goal
                    ):
                        best_reached = (nx, ny)

        # --- Reconstruct path ---
        if best_reached not in came_from:
            return [], 0  # No path found

        path = []
        node = best_reached
        while node:
            path.append(node)
            node = came_from[node]
        path.reverse()

        # remove last path item, because you stop juste before destination.
       
        return path, int(round(g_score[path[-1]]))

    # -------------------------------------------
    # SAVE / LOAD
    # -------------------------------------------

    @classmethod
    def load(cls, wkdir: str, room_name: str):
        """Load a room map and apply a theme to it."""

        room_path = os.path.join(wkdir, "Rooms", room_name)
        with open(room_path, "r", encoding="utf-8") as fin:
            data = yaml.safe_load(fin)

        name = room_name.strip(".yaml")
        theme_path = data["theme"]
        theme_path = os.path.join(wkdir, "Rooms", "Themes", theme_path)
        theme = Theme.load(theme_path)
        actors = {}
        
        npc_ordered_list = []
        for a_name, a_dict in data["actors"].items():
            a_dict["name"] = a_name
            npc_ordered_list.append(a_name)
            a_dict["state"] = "idle"
            actors[a_name] = Actor.from_dict(a_dict, wkdir)
        # loots = {k: Loot.from_dict(v) for k, v in data["loots"].items()}
        tiles, width, height = from_ascii_map(data["ascii_map"], theme.tiles)

        npc_ordered_list =sorted(npc_ordered_list)

        elevation = np.full((width, height),0.)
        for x in range(width):
            for y in range(height):
                elevation[x,y] = tiles[x,y].elevation +tiles[x,y].obstacle_height
        opacity = np.full((width, height),0.)
        for x in range(width):
            for y in range(height):
                opacity[x,y] = tiles[x,y].opacity

        return cls(
            name=name,
            wkdir=wkdir,
            description=data["description"],
            ascii_map=data["ascii_map"],
            width=width,
            height=height,
            tiles=tiles,
            theme=theme,
            elevation=elevation,
            opacity=opacity,
            actors=actors,
            npc_ordered_list=npc_ordered_list
            # loots=loots,
        )

    def save(self, yaml_path: str):
        """Save the room definition (excluding theme)."""
        data = {
            "name": self.name,
            "ascii_map": self.render_ascii(spaced=False),
            "actors": self.npcs,
            "loots": self.loots,
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    

def from_ascii_map(ascii_map: str, tile_specs: dict):
    if isinstance(ascii_map, list):
        ascii_map = "\n".join(ascii_map)
    lines = textwrap.dedent(ascii_map).strip().splitlines()
    height = len(lines)
    width = max(len(line) for line in lines)
    tiles = {}
    for y, line in enumerate(lines):
        for x, char in enumerate(line.ljust(width)):
            tiles[(x, y)] = symbol_to_tile(char, tile_specs)
    return tiles, width, height



def symbol_to_tile(symbol: str, tile_specs: dict) -> Tile:
    tile_spec = tile_specs.get(symbol)

    if tile_spec is None:
        print(f"Warning, symbol {symbol} not found in theme. Interpreted as ground")
        tile_spec = tile_specs.get(" ")

    return Tile(
        symbol=symbol,
        difficulty=tile_spec.move_difficulty,
        description=tile_spec.description,
        opacity=tile_spec.opacity,
        obstacle_height=tile_spec.obstacle_height,
        climb_height=tile_spec.climb_height
    )



# def compute_los(
#     actor_name: str,
#     actors: Dict[str, Actor],
#     loots: Dict[str, Loot],
#     gates: Dict[str, RoomGate],
#     tiles: Dict[Tuple[int, int], Tile],
#     width: int,
#     height: int,
# ) -> Tuple[
#     List[list[List[Tuple[str, str]]]],
#     List[Tuple[str, int]],
#     List[Tuple[str, int]],
#     List[Tuple[str, int]],
# ]:
#     actor = actors[actor_name]
#     px, py = actor.pos

#     f_angle = FACING_ANGLE[actor.facing]

#     # sector angle ranges relative to facing
#     # front: -30..+30 ; left: -90..-30 ; right: +30..+90 (deg)
#     sector_ranges = {"front": (-20, 20), "left": (-60, -20), "right": (20, 60)}

#     # We'll gather nearest distance (in units) for each unique object name under each sector.
#     # data structure: items_by_zone[band][sector] -> dict name -> nearest_distance_units
#     items_by_zone = {
#         "close": {"left": {}, "front": {}, "right": {}},
#         "mid": {"left": {}, "front": {}, "right": {}},
#         "far": {"left": {}, "front": {}, "right": {}},
#     }

#     seen_positions = (
#         set()
#     )  # optional: avoid double counting same tile across rays for tile-only items

#     # Helper to register found object
#     def register(sector, dist_u, label):
#         # determine band
#         u = dist_u
#         if u <= CLOSE_MAX_U:
#             band = "close"
#         elif MID_MIN_U <= u <= MID_MAX_U:
#             band = "mid"
#         elif u >= FAR_MIN_U:
#             band = "far"
#         else:
#             # between close max and mid min (rare if thresholds overlap); treat as mid
#             band = "mid"
#         existing = items_by_zone[band][sector].get(label)
#         if existing is None or dist_u < existing:
#             items_by_zone[band][sector][label] = dist_u

#     # Build list of ray angles to cast (for all three sectors)
#     rays = []
#     for sector_name, (a_min, a_max) in sector_ranges.items():
#         # cast rays from a_min to a_max inclusive with step RAY_STEP_DEG
#         a = a_min
#         while a <= a_max:
#             rays.append((sector_name, (f_angle + a) % 360))
#             a += RAY_STEP_DEG

#     # For actors and loots, build quick lookup by pos
#     pos_to_actors = {
#         a.pos: (k, a) for k, a in actors.items()
#     }  # key includes Player too
#     pos_to_loots = {l.pos: (k, l) for k, l in loots.items()}
#     pos_to_gates = {g.pos: (k, g) for k, g in gates.items()}


#     visible_actors = []
#     visible_loots = []
#     visible_gates = []

#     # Cast each ray
#     for sector_name, ray_angle in rays:
#         dx_unit, dy_unit = _angle_to_vector(ray_angle)  # per-unit vector in map units
#         s = RAY_STEP_UNIT
#         blocked = False
#         visited_tiles = set()
#         while s <= MAX_UNITS and not blocked:
#             tx = px + dx_unit * s
#             ty = py + dy_unit * s
#             ix = int(round(tx))
#             iy = int(round(ty))
#             tile_coord = (ix, iy)

#             # skip if same tile already processed along this ray
#             if tile_coord in visited_tiles:
#                 s += RAY_STEP_UNIT
#                 continue
#             visited_tiles.add(tile_coord)

#             # out of bounds ?
#             if ix < 0 or iy < 0 or ix >= width or iy >= height:
#                 break

#             tile = tiles.get(tile_coord)
#             # check for actors (exclude the observer)
#             if tile_coord in pos_to_actors:
#                 akey, ak = pos_to_actors[tile_coord]
#                 if akey != actor_name:
#                     dist_units = math.hypot((ak.pos[0] - px), (ak.pos[1] - py))
#                     register(sector_name, dist_units, (ak.name.lower(), "actor"))
#                     if (akey, dist_units) not in visible_actors:
#                         visible_actors.append((akey, dist_units))
#             # check for loots
#             if tile_coord in pos_to_loots:
#                 lkey, lo = pos_to_loots[tile_coord]
#                 dist_units = math.hypot((lo.pos[0] - px), (lo.pos[1] - py))
#                 register(sector_name, dist_units, (lo.name.lower(), "loot"))
#                 if (lkey, dist_units) not in visible_loots:
#                     visible_loots.append((lkey, dist_units))
#             # check for gates
#             if tile_coord in pos_to_gates:
#                 gkey, go = pos_to_gates[tile_coord]
#                 dist_units = math.hypot((go.pos[0] - px), (go.pos[1] - py))
#                 desc=  gkey +" : "+ go.description.lower()
#                 register(sector_name, dist_units, (desc, "gate"))
#                 if (desc, dist_units) not in visible_gates:
#                     visible_gates.append((desc, dist_units))

#             # check tile itself (non-floor items)
#             if tile and tile.symbol not in [" "]:
#                 # avoid duplicates if we've already registered this tile by its coordinate earlier rays
#                 if tile_coord not in seen_positions:
#                     # label tile descriptively
#                     label = tile.description.lower()
#                     dist_units = math.hypot((ix - px), (iy - py))
#                     register(sector_name, dist_units, (label, label))
#                     seen_positions.add(tile_coord)

#             # if tile blocks view, terminate this ray
#             if tile and tile.blocks_view:
#                 blocked = True
#                 break

#             s += RAY_STEP_UNIT
#     return items_by_zone, visible_actors, visible_loots, visible_gates


# def assemble_description(
#     items_by_zone: List[list[List[Tuple[str, str]]]], unit_to_m: float
# ) -> List[str]:
#     # Now format the textual report using grouped data
#     report_lines = []
#     for band in ("close", "mid", "far"):
#         band_report = []
#         for sector in ("left", "front", "right"):
#             items_seen = items_by_zone[band][sector]
#             if not items_seen:
#                 continue
#             # if more than PLURAL_THRESHOLD items, pluralize and don't show distances
#             # --- Group items by category ---
#             grouped = {}
#             for (
#                 name,
#                 category,
#             ), dist_u in items_seen.items():  # (name, distance, category)
#                 grouped.setdefault(category, []).append((name, dist_u))

#             # --- Construct sentences per category ---
#             parts = []
#             for category, entries in grouped.items():
#                 entries.sort(key=lambda e: e[1])  # sort by distance ascending
#                 if len(entries) > 3:
#                     parts.append(f"several {category}s")
#                 else:
#                     for name, dist_u in entries:
#                         parts.append(f"{name} ({round(unit_to_m*dist_u)}m)")

#             # Combine into a single readable sentence
#             if parts:
#                 joined = ", ".join(parts)
#                 band_report.append(f" {sector}, There is {joined}")
#         if band_report:
#             report_lines.append(band.capitalize() + ":")
#             report_lines.extend(band_report)

#     if len(report_lines) == 1:
#         # only the facing line, no visible items found
#         report_lines.append("There is empty floor ahead.")
#     return report_lines
