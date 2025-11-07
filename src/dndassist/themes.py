from dataclasses import dataclass
from typing import Optional


@dataclass
class TileSpec:
    name: str
    description: str
    opacity:float = 0.01 # 1% of opacity applied per m
    move_difficulty: int = 1
    lighting: float = 1.0  # relative brightness (0–1)
    color: Optional[str] = None  # hex or color name
    sprite: Optional[str] = None
    obstacle_height: float = 0
    climb_height: float = 0
    

from dataclasses import dataclass, field
from typing import Dict
import yaml


@dataclass
class Theme:
    name: str
    base_color: str = "#FFFFFF"
    tiles: Dict[str, TileSpec] = field(default_factory=dict)

    @classmethod
    def load(cls, yaml_path: str) -> "Theme":
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        tiles = {}
        for k, tdata in data["tiles"].items():
            if "opacity" not in  tdata:
                tdata["opacity"] = data["default_opacity"]
            if "lighting" not in  tdata:
                tdata["lighting"] = data["default_lighting"]
            if "color" not in  tdata:
                tdata["color"] = data["base_color"]
            tiles[k]=TileSpec(**tdata)
            
        return cls(
            name=data["name"],
            base_color=data.get("base_color", "#FFFFFF"),
            tiles=tiles,
        )

    def save(self, yaml_path: str):
        data = {
            "name": self.name,
            "base_color": self.base_color,
            "tiles": {k: vars(v) for k, v in self.tiles.items()},
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
