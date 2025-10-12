from dataclasses import dataclass
from typing import Optional

@dataclass
class TileSpec:
    name: str
    short_description: str
    long_description: str
    traversable: bool
    blocks_view: bool
    move_difficulty: int = 1
    enter_condition: Optional[str] = None
    leave_condition: Optional[str] = None
    lighting: float = 1.0                  # relative brightness (0–1)
    color: Optional[str] = None            # hex or color name
    sprite: Optional[str] = None

from dataclasses import dataclass, field
from typing import Dict
import yaml

@dataclass
class Theme:
    name: str
    environment: str = "outdoor"           # "indoor" or "outdoor"
    default_lighting: float = 1.0
    base_color: str = "#FFFFFF"
    tiles: Dict[str, TileSpec] = field(default_factory=dict)

    @classmethod
    def load(cls, yaml_path: str) -> "Theme":
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        tiles = {k: TileSpec(**v) for k, v in data.get("tiles", {}).items()}
        return cls(
            name=data.get("name", "Unnamed Theme"),
            environment=data.get("environment", "outdoor"),
            default_lighting=data.get("default_lighting", 1.0),
            base_color=data.get("base_color", "#FFFFFF"),
            tiles=tiles,
        )

    def save(self, yaml_path: str):
        data = {
            "name": self.name,
            "environment": self.environment,
            "default_lighting": self.default_lighting,
            "base_color": self.base_color,
            "tiles": {k: vars(v) for k, v in self.tiles.items()},
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
