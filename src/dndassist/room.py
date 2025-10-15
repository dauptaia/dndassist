from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple, List, Optional
import textwrap, math, yaml, json

import math
import numpy
from collections import defaultdict

from dndassist.themes.themes import Theme

# constants (tweakable)
UNIT_M = 1.5                        # 1 tile/unit = 1.5 meters (matches your band example)
MAX_UNITS = 50                      # max scanning distance in units
CLOSE_MAX_U = 6                     # <=6 units = close (<9m)
MID_MIN_U, MID_MAX_U = 7, 20        # 7..20 units = mid (9m..30m)
FAR_MIN_U = 21                      # >20 units = far
RAY_STEP_DEG = 4                    # angular resolution for rays across a sector
RAY_STEP_UNIT = 0.5                 # step length along each ray (in units)
PLURAL_THRESHOLD = 3                # >3 items -> pluralize (user requested >3 -> plural)


# facing -> base angle in degrees (0 = north/up, increases clockwise)
FACING_ANGLE = {
    "N": 0, "NE": 45, "E": 90, "SE": 135,
    "S": 180, "SW": 225, "W": 270, "NW": 315
}

def _angle_to_vector(angle_deg: float):
    """Return (dx, dy) vector for grid coordinates where x increases to right, y increases downward.
       We define angle=0 as NORTH (up / -y)."""
    rad = math.radians(angle_deg)
    dx = math.sin(rad)      # x component (right positive)
    dy = -math.cos(rad)     # y component (down positive) => -cos so 0deg -> (0,-1)
    return dx, dy

def _unit_to_m(u: float) -> int:
    """Convert map units to meters (rounded integer)."""
    return int(round(u * UNIT_M))

# -----------------------------------------------------------
#  BASIC TILE
# -----------------------------------------------------------
@dataclass
class Tile:
    symbol: str
    traversable: bool
    blocks_view: bool
    description: str
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


# -----------------------------------------------------------
#  MOVEABLE ELEMENTS
# -----------------------------------------------------------
@dataclass
class Actor:
    name: str
    symbol: str
    pos: Tuple[int, int]
    facing: str = "N"
    sprite: str= None
    
    def turn(self, direction: str):
        self.facing = direction.upper()

    def move(self, dx: int, dy: int):
        x, y = self.pos
        self.pos = (x + dx, y + dy)

    def to_dict(self): 
        return asdict(self)
    @classmethod
    def from_dict(cls, d): 
        d["pos"] = tuple(d["pos"]) #when read from safe yaml , tuple were stored as list
        return cls(**d)


@dataclass
class Loot:
    name: str
    symbol: str
    sprite: str
    index:int
    pos: Tuple[int, int]
    
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): 
        d["pos"] = tuple(d["pos"] ) #when read from safe yaml , tuple were stored as list
        return cls(**d)


# -----------------------------------------------------------
#  MAP CLASS
# -----------------------------------------------------------
@dataclass
class RoomMap:
    name: str
    ascii_map: str
    tiles: Dict[Tuple[int, int], Tile]
    theme: Theme
    width: int
    height: int
    elevation: Optional[Dict[Tuple[int, int], int]] = None
    actors: Dict[str, Actor] = field(default_factory=dict)
    loots: Dict[str, Loot] = field(default_factory=dict)

   
    # -------------------------------------------
    # def add_player(self, index:int, name: str, pos: Tuple[int, int], facing: str = "N"):
    #     self.actors["Player"+str(index)] = Actor(name, "@", index, pos, facing=facing)

    # to refine
    def add_actor(self, name: str, pos: Tuple[int, int], symbol="M", facing: str = "N"):
        """add an actor in the room. 
        
        Actors are identified by their unique names, handled outside the room concept.
        - If name already present, the addition is refused
        - If position is occupied by object or actor, the addition is refused
        """
        if name in self.actors:
            print(f"Actor {name} is already in the room")
        else:
            self.actors[name] = Actor(name, symbol, pos, facing=facing)

    def del_actor(self, name: str):
        """remove an actor in the room"""
        if name in self.actors:
            del self.actors[name]
        else:
            print(f"Actor {name} is not in the room")


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

    def move_actor_towards(self, actor_name: str, max_range:int, any_name: str):
        """Move an actor in the room toward an other actor
        
        Motion will be limited by the maximum range, 
        the terrain difficulty
        and the ostacles

        Motion will stop against walls or void
        """

        #find the correct final position
        #self.actors[actor_name].pos = new_position
        pass

    # -------------------------------------------
    def move_actor(self, actor_name: str, dx: int, dy: int):
        actor = self.actors[actor_name]
        dir=""
        if dx>0:
            dir+="S"
        if dx<0:
            dir+="N"
        if dy>0:
            dir+="E"
        if dy<0:
            dir+="W"
        dist=_unit_to_m(math.hypot(dx,dy))
        
        
        nx, ny = actor.pos[0] + dx, actor.pos[1] + dy
        tile = self.tiles.get((nx, ny))
        if tile is None:
            print(f"Tile {(nx, ny)} not existing")
            return

        if not tile.traversable:
            print(f"Tile {(nx, ny)} {tile.description} not traversable")
            return

        print(f"{actor_name} is moving {dist:.2f}m to {dir}" )
        actor.pos = (nx, ny)
            
    # -------------------------------------------
    def pick_up_loot(self, actor_name: str):
        actor = self.actors[actor_name]
        for key, loot in list(self.loots.items()):
            if loot.pos == actor.pos:
                print(f"{actor.name} picked up {loot.name}.")
                del self.loots[key]

    # -------------------------------------------
    def render_ascii(self, mode="symbol") -> str:

        if mode == "symbol":
            grid = [[self.tiles.get((x, y), Tile("/", True, False, "")).symbol
                    for x in range(self.width)] for y in range(self.height)]
        elif mode == "traversable":
            grid = [[ str(self.tiles.get((x, y), Tile("/", True, False, "")).traversable)[0]
                    for x in range(self.width)] for y in range(self.height)]
        else:
            raise ValueError(f"render_acii {mode} not implemented...")
        
        print(f"Size {self.width}x{self.height}")
        for loot in self.loots.values():
            x, y = loot.pos
            grid[y][x] = loot.symbol
        for actor in self.actors.values():
            x, y = actor.pos
            grid[y][x] = actor.symbol
        return "\n".join("".join(row) for row in grid)

    # -------------------------------------------
    def describe_view_los(self, actor_name: str) -> str:
        """
        True LoS description using multiple rays per sector.
        Groups visible items into (close, mid, far) x (left, front, right).
        Returns a multi-line text describing what's visible.
        """

        return compute_los_description(
            actor_name, 
            self.actors, 
            self.loots, 
            self.tiles,
            self.width, 
            self.height)
        
    # -------------------------------------------
    # SAVE / LOAD
    # -------------------------------------------

    @classmethod
    def load(cls, yaml_path: str, theme: Theme):
        """Load a room map and apply a theme to it."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        name = data.get("name", "Unnamed Room")
        actors = {k: Actor.from_dict(v) for k, v in data["actors"].items()}
        loots = {k: Loot.from_dict(v) for k, v in data["loots"].items()}
        print(theme)
        tile_specs = theme.tiles
        tiles, width, height = from_ascii_map(data["ascii_map"],tile_specs)

        return cls(
            name=name,
            ascii_map=data["ascii_map"],
            width=width,
            height=height,
            tiles=tiles,
            theme=theme,
            actors=actors,
            loots=loots,
        )


    # def save(self, path: str):
    #     data = {
    #         "name": self.name,
    #         "ascii_map": self.render_ascii(),
    #         "actors": {k: a.to_dict() for k, a in self.actors.items()},
    #         "loots": {k: l.to_dict() for k, l in self.loots.items()},
    #     }
    #     with open(path, "w") as f: yaml.safe_dump(data, f)

    def save(self, yaml_path: str):
        """Save the room definition (excluding theme)."""
        data = {
            "name": self.name,
            "ascii_map": self.render_ascii(),
            "actors": self.npcs,
            "loots": self.loots,
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    # def get_tile_spec(self, x: int, y: int):
    #     """Return the TileSpec from the theme for the map position."""
    #     if y < 0 or y >= len(self.ascii_map):
    #         return None
    #     line = self.ascii_map[y]
    #     if x < 0 or x >= len(line):
    #         return None
    #     char = line[x]
    #     return self.theme.tiles.get(char)
    


def from_ascii_map(ascii_map: str, tile_specs:dict):

    if isinstance(ascii_map,list):
        ascii_map="\n".join(ascii_map)
    lines =  textwrap.dedent(ascii_map).strip().splitlines()
    height = len(lines)
    width = max(len(line) for line in lines)
    tiles = {}
    for y, line in enumerate(lines):
        for x, char in enumerate(line.ljust(width)):
            tiles[(x, y)] = symbol_to_tile(char,tile_specs)
    return tiles, width, height

def symbol_to_tile(symbol: str, tile_specs:dict) -> Tile:

    tile_spec = tile_specs.get(symbol)

    if tile_spec is None:
        print(f"Warning, symbol {symbol} not found in theme. Interpreted as ground")
        tile_spec = tile_specs.get(" ")
    
    
    return Tile(
        symbol=symbol,
        traversable=tile_spec.traversable,
        blocks_view=tile_spec.blocks_view,
        description=tile_spec.short_description,
    )


    
def compute_los_description(
        actor_name:str, 
        actors:Dict[str, Actor], 
        loots:Dict[str, Loot], 
        tiles:Dict[Tuple[int, int], Tile],
        width:int, 
        height:int
    ):

    if actor_name not in actors:
        return f"No actor named {actor_name}."

    actor = actors[actor_name]
    px, py = actor.pos
    facing = actor.facing.upper()
    if facing not in FACING_ANGLE:
        return f"Unknown facing '{actor.facing}'."

    report_lines = [f"{actor.name} is facing {facing}."]
    f_angle = FACING_ANGLE[facing]

    # sector angle ranges relative to facing
    # front: -30..+30 ; left: -90..-30 ; right: +30..+90 (deg)
    sector_ranges = {
        "front": (-20, 20),
        "left":  (-60, -20),
        "right": (20, 60)
    }

    # We'll gather nearest distance (in units) for each unique object name under each sector.
    # data structure: items_by_zone[band][sector] -> dict name -> nearest_distance_units
    items_by_zone = {
        "close": {"left": {}, "front": {}, "right": {}},
        "mid":   {"left": {}, "front": {}, "right": {}},
        "far":   {"left": {}, "front": {}, "right": {}},
    }

    seen_positions = set()  # optional: avoid double counting same tile across rays for tile-only items

    # Helper to register found object
    def register(sector, dist_u, label):
        # determine band
        u = dist_u
        if u <= CLOSE_MAX_U:
            band = "close"
        elif MID_MIN_U <= u <= MID_MAX_U:
            band = "mid"
        elif u >= FAR_MIN_U:
            band = "far"
        else:
            # between close max and mid min (rare if thresholds overlap); treat as mid
            band = "mid"
        existing = items_by_zone[band][sector].get(label)
        if existing is None or dist_u < existing:
            items_by_zone[band][sector][label] = dist_u

    # Build list of ray angles to cast (for all three sectors)
    rays = []
    for sector_name, (a_min, a_max) in sector_ranges.items():
        # cast rays from a_min to a_max inclusive with step RAY_STEP_DEG
        a = a_min
        while a <= a_max:
            rays.append((sector_name, (f_angle + a) % 360))
            a += RAY_STEP_DEG

    # For actors and loots, build quick lookup by pos
    pos_to_actors = {a.pos: (k, a) for k, a in actors.items()}  # key includes Player too
    pos_to_loots = {l.pos: (k, l) for k, l in loots.items()}

    # Cast each ray
    for sector_name, ray_angle in rays:
        dx_unit, dy_unit = _angle_to_vector(ray_angle)  # per-unit vector in map units
        s = RAY_STEP_UNIT
        blocked = False
        visited_tiles = set()
        while s <= MAX_UNITS and not blocked:
            tx = px + dx_unit * s
            ty = py + dy_unit * s
            ix = int(round(tx))
            iy = int(round(ty))
            tile_coord = (ix, iy)

            # skip if same tile already processed along this ray
            if tile_coord in visited_tiles:
                s += RAY_STEP_UNIT
                continue
            visited_tiles.add(tile_coord)

            # out of bounds ?
            if ix < 0 or iy < 0 or ix >= width or iy >= height:
                break

            tile = tiles.get(tile_coord)
            # check for actors (exclude the observer)
            if tile_coord in pos_to_actors:
                akey, ak = pos_to_actors[tile_coord]
                if akey != actor_name:
                    dist_units = math.hypot((ak.pos[0] - px), (ak.pos[1] - py))
                    register(sector_name, dist_units, (ak.name.lower(), "actor"))
            # check for loots
            if tile_coord in pos_to_loots:
                lkey, lo = pos_to_loots[tile_coord]
                dist_units = math.hypot((lo.pos[0] - px), (lo.pos[1] - py))
                register(sector_name, dist_units, (lo.name.lower(), "loot"))

            # check tile itself (non-floor items)
            if tile and tile.symbol not in [" ", "."]:
                # avoid duplicates if we've already registered this tile by its coordinate earlier rays
                if tile_coord not in seen_positions:
                    # label tile descriptively
                    label = tile.description.lower()
                    dist_units = math.hypot((ix - px), (iy - py))
                    register(sector_name, dist_units, (label, label))
                    seen_positions.add(tile_coord)

            # if tile blocks view, terminate this ray
            if tile and tile.blocks_view:
                blocked = True
                break

            s += RAY_STEP_UNIT

    # Now format the textual report using grouped data
    for band in ("close", "mid", "far"):
        band_report=[]
        for sector in ("front","left", "right"):
            items_seen = items_by_zone[band][sector]
            if not items_seen:
                continue
            # if more than PLURAL_THRESHOLD items, pluralize and don't show distances
                # --- Group items by category ---
            grouped = {}
            for (name, category), dist_u in items_seen.items():  # (name, distance, category)
                grouped.setdefault(category, []).append((name, dist_u))
            
            # --- Construct sentences per category ---
            parts = []
            for category, entries in grouped.items():
                entries.sort(key=lambda e: e[1])  # sort by distance ascending
                if len(entries) > 3:
                    parts.append(f"several {category}s")
                else:
                    for name, dist_u in entries:
                        parts.append(f"{name} ({_unit_to_m(dist_u)}m)")
            
            # Combine into a single readable sentence
            if parts:
                joined = ", ".join(parts)
                band_report.append(f" {sector}, you see {joined}")
        if band_report:
            report_lines.append(band.capitalize()+":")
            report_lines.extend(band_report)
            
    
    if len(report_lines) == 1:
        # only the facing line, no visible items found
        report_lines.append("You see only empty floor ahead.")
    return "\n".join(report_lines)