"""
Isometric renderer using Pygame.
Expect: Theme YAML and Room YAML as described previously (Theme.load / Room.load).
Place this file alongside your theme and room YAMLs and run.

Controls:
 - LEFT/RIGHT keys: rotate camera (NE -> NW -> SW -> SE -> NE)
 - ESC or window close: exit
 - Move mouse to see tooltips for tiles / loots / actors
"""

import sys, os
import math
import pygame
import yaml
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional

# -------------------------
# Isometric renderer
# -------------------------

from dndassist.room import RoomMap, Actor, Loot


class IsometricRenderer:
    """
    Render a Room with a Theme in Pygame using isometric projection.
    """

    ORIENTATIONS = ["NE", "NW", "SW", "SE"]  # cycling order for left/right rotate

    def __init__(
        self,
        room: RoomMap,
        tile_w: int = 130,
        tile_h: int = 76,
        screen_size=(1200, 600),
    ):
        self.room = room
        #self.scenario_path = scenario_path
        self.theme = room.theme
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.screen_w, self.screen_h = screen_size
        self.cam_x = 0
        self.cam_y = 0
        self.zoom = 1.0
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption(
            f"Isometric Renderer - {room.name} ({self.theme.name})"
        )
        self.clock = pygame.time.Clock()

        self.orientation_index = 0  # start NE
        self.orientation = self.ORIENTATIONS[self.orientation_index]

        # sprite cache: path -> Surface
        self.sprite_cache: Dict[str, pygame.Surface] = {}

        # map tile bounding boxes for hover detection
        # each tile: dict with keys 'rect' (pygame.Rect), 'coord' (x,y), 'screen' (sx,sy)
        self.tile_hitboxes: List[Dict] = []

        # actor and loot objects
        self.actors: Dict[str, Actor] = self.room.actors
        self.loots: Dict[str, Loot] = self.room.loots

        # preload actors and loots from Room
        # self._init_actors_loots()

        # prepare tile grid and pre-load sprites declared by theme
        self._prepare_tiles_and_sprites()

    # ---------- convenience: color hex -> pygame.Color ----------
    @staticmethod
    def _hex_to_color(h: str):
        try:
            return pygame.Color(h)
        except Exception:
            # fallback to gray
            return pygame.Color("#888888")

    # ---------- load image (cached) ----------
    def _load_sprite(self, path: Optional[str]) -> Optional[pygame.Surface]:
        if not path:
            return None
        if path in self.sprite_cache:
            return self.sprite_cache[path]
        try:
            img = pygame.image.load(path).convert_alpha()
            self.sprite_cache[path] = img
            return img
        except Exception as e:
            print(f"[renderer] Warning: cannot load sprite '{path}': {e}")
            self.sprite_cache[path] = None
            return None

    def _load_sprite_in_cache(self, wkdir:str, path: Optional[str], ) -> Optional[pygame.Surface]:
        if not path:
            return None
        if path in self.sprite_cache:
            return self.sprite_cache[path]
        try:
            img = pygame.image.load(os.path.join(wkdir, path)).convert_alpha()
            self.sprite_cache[path] = img
            return img
        except Exception as e:
            print(f"[renderer] Warning: cannot load sprite '{path}': {e}")
            self.sprite_cache[path] = None
            return None


    # ---------- prepare tiles/actors/loots ----------
    def _prepare_tiles_and_sprites(self):
        # preload all sprites referenced by theme tiles
        for ch, spec in self.theme.tiles.items():
            if spec.sprite:
                self._load_sprite_in_cache(
                    os.path.join(self.room.wkdir, "Tiles"),
                    spec.sprite
                )
                
        # preload actor/loot sprites if present in room object (or theme-specific)
        for a in self.actors.values():
            if a.character.sprite:
                self._load_sprite_in_cache(
                    os.path.join(self.room.wkdir, "Characters"),
                    a.character.sprite
                )
        for l in self.loots.values():
            if l.sprite:
                self._load_sprite_in_cache(
                    os.path.join(self.room.wkdir, "Loots"), 
                    l.sprite
                )
    # def _init_actors_loots(self):
    #     # convert room.npcs and room.loots into Actor / Loot objects
    #     for nid, v in self.room.npcs.items():
    #         # v expected [x,y,facing]
    #         x, y, facing = v
    #         # try to find sprite for NPC symbol in theme (M) else None
    #         sprite = None
    #         if "M" in self.theme.tiles and self.theme.tiles["M"].sprite:
    #             sprite = self.theme.tiles["M"].sprite
    #         self.actors[nid] = Actor(id=nid, name=nid, pos=(x, y), facing=facing, sprite=sprite)

    #     for lid, v in self.room.loots.items():
    #         # v expected [x,y,name]
    #         x, y, name = v
    #         # no guaranteed sprite; look for 'l' in theme
    #         sprite = None
    #         if "l" in self.theme.tiles and self.theme.tiles["l"].sprite:
    #             sprite = self.theme.tiles["l"].sprite
    #         self.loots[lid] = Loot(id=lid, name=name, pos=(x,y), sprite=sprite)

    #     # add player as an actor (symbol '@'), if provided
    #     if self.room.player_pos:
    #         px, py = self.room.player_pos
    #         # attempt to use "Player" sprite from theme or fallback to None
    #         player_sprite = None
    #         if "@" in self.theme.tiles and self.theme.tiles["@"] .sprite:
    #             player_sprite = self.theme.tiles["@"] .sprite
    #         self.actors["Player"] = Actor(id="Player", name="Player", pos=(px,py), facing=self.room.player_facing, sprite=player_sprite)

    # ---------- coordinate transforms ----------
    def _transform_coord_for_orientation(self, x: int, y: int) -> Tuple[int, int]:
        """Return transformed grid coords according to current orientation.
        We reorder/flip (x,y) so that same projection formula works for all views.
        Orientation mapping:
            NE: use (x, y)
            NW: flip X (mirror horizontally)
            SW: swap x,y and flip both -> rotate 180?
            SE: flip Y? (we'll implement symmetrical transforms)
        We'll implement transforms that produce visually correct rotation/mirror for isometric projection below.
        """
        # w = len(self.room.ascii_map[0])
        # h = len(self.room.ascii_map)
        w = self.room.width
        h = self.room.height
        if self.orientation == "NE":
            return x, y
        elif self.orientation == "NW":
            # mirror horizontally (x -> w-1-x)
            return y, (w - 1 - x)
        elif self.orientation == "SW":
            # rotate 180 degrees (x->w-1-x, y->h-1-y)
            return (w - 1 - x), (h - 1 - y)
        elif self.orientation == "SE":
            # mirror vertically (y -> h-1-y)
            return (h - 1 - y), x
        else:
            return x, y

    def project(self, x: int, y: int) -> Tuple[int, int]:
        """Project grid coord (x,y) to screen px,py using standard isometric formula.
        Projection origin will be centered horizontally and slightly offset vertically.
        """
        tx, ty = self._transform_coord_for_orientation(x, y)
        # basic isometric projection
        sx = (tx - ty) * (self.tile_w // 2) * self.zoom
        sy = (tx + ty) * (self.tile_h // 2) * self.zoom
        # offset to center map on screen
        # w = self.room.width
        # h = self.room.height

        # map_px_width = (w + h - 1) * (self.tile_w // 2)

        offset_x = (self.screen_w) / 2 + self.cam_x
        offset_y = 80 + self.cam_y
        return int(sx + offset_x), int(sy + offset_y)

    # ---------- draw utilities ----------
    def _draw_diamond(self, surf, cx, cy, w, h, color):
        # draw a filled isometric diamond centered at (cx, cy)
        points = [
            (cx, cy - h // 2),  # top
            (cx + w // 2, cy),  # right
            (cx, cy + h // 2),  # bottom
            (cx - w // 2, cy),  # left
        ]
        pygame.draw.polygon(surf, color, points)

    def _draw_rect(self, surf, cx, cy, w, h, color):
        # draw a filled isometric square centered at (cx, cy)
        points = [
            (cx, cy + h),  # top
            (cx, cy),  # right
            (cx + w, cy),  # right
            (cx + w, cy + h),  # right
            # left
        ]
        pygame.draw.polygon(surf, color, points)

    # ---------- main render pass ----------
    def _build_hitboxes_and_draw_order(self):
        """Create a list of tile cells with screen coords and bounding rects for hit detection and ordering."""
        self.tile_hitboxes = []
        width = len(self.room.ascii_map[0])
        height = len(self.room.ascii_map)
        for y in range(height):
            for x in range(width):
                sx, sy = self.project(x, y)
                # bounding rectangle roughly covering tile sprite area
                rect = pygame.Rect(
                    sx - self.tile_w // 2,
                    sy - self.tile_h // 2,
                    self.tile_w,
                    self.tile_h,
                )
                self.tile_hitboxes.append(
                    {"coord": (x, y), "screen": (sx, sy), "rect": rect}
                )
        # sort back-to-front by depth key (tx+ty) using transformed coords
        self.tile_hitboxes.sort(
            key=lambda d: (
                self._transform_coord_for_orientation(*d["coord"])[0]
                + self._transform_coord_for_orientation(*d["coord"])[1]
            )
        )

    def render_frame(self):
        # clear background
        bg_color = self._hex_to_color(self.theme.base_color)
        self.screen.fill(bg_color)

        # build hitboxes & draw order
        self._build_hitboxes_and_draw_order()

        w_std = int(self.tile_w * self.zoom)
        h_std = int(self.tile_h * self.zoom)

        # draw tiles in order
        for tileinfo in self.tile_hitboxes:
            x, y = tileinfo["coord"]
            sx, sy = tileinfo["screen"]
            ch = (
                self.room.ascii_map[y][x]
                if y < len(self.room.ascii_map) and x < len(self.room.ascii_map[y])
                else " "
            )
            spec = self.theme.tiles.get(ch)
            if spec and spec.sprite:
                surf = self.sprite_cache[spec.sprite] if spec.sprite else None
            
                if surf:
                    # position sprite bottom-center on isometric tile
                    w_exact, h_exact = surf.get_size()
                    w_exact *= self.zoom
                    h_exact *= self.zoom
                    blit_x = sx - w_std // 2
                    blit_y = sy + (
                        h_std - h_exact
                    )  # + (self.tile_h)  # slight vertical offset
                    if self.zoom != 1.0:
                        surf = pygame.transform.scale_by(surf, self.zoom)

                    self.screen.blit(surf, (blit_x, blit_y))
                    tileinfo["blit_rect"] = pygame.Rect(
                        blit_x - w_std // 2, blit_y - h_std // 2, w_std // 2, h_std // 2
                    )

                    continue
            # fallback: colored diamond
            color = (
                self._hex_to_color(spec.color)
                if spec and spec.color
                else pygame.Color("#666666")
            )
            self._draw_diamond(self.screen, sx, sy, w_std, h_std, color)
            tileinfo["blit_rect"] = tileinfo["rect"]

        # draw loots and actors after tiles
        # prepare a list with screen positions so we can depth-sort them too
        entity_draw_list = []
        for lid, loot in self.loots.items():
            sx, sy = self.project(*loot.pos)
            sprite = self.sprite_cache[loot.sprite] if loot.sprite else None
            entity_draw_list.append(("loot", loot, sx, sy, sprite))
        for aid, actor in self.actors.items():
            sx, sy = self.project(*actor.pos)
            sprite = self.sprite_cache[actor.character.sprite] if actor.character.sprite else None
            entity_draw_list.append(("actor", actor, sx, sy, sprite))

        # sort by sy (vertical) so lower items appear on top
        entity_draw_list.sort(key=lambda e: e[3] + (0 if e[4] is None else 0))

        for etype, obj, sx, sy, sprite in entity_draw_list:
            if sprite:
                w_exact, h_exact = sprite.get_size()
                w_exact *= self.zoom
                h_exact *= self.zoom
                blit_x = sx - w_std // 2
                blit_y = sy + (h_std - h_exact) - h_std
                # if self.zoom != 1.0:
                sprite = pygame.transform.scale_by(sprite, self.zoom)
                self.screen.blit(sprite, (blit_x, blit_y))
                obj._screen_rect = pygame.Rect(
                    blit_x + 0 * w_std // 2,
                    blit_y + 1 * h_std // 2,
                    w_std // 2,
                    h_exact // 2,
                )
            else:
                # draw placeholder circle
                color = (
                    pygame.Color("#FFD700")
                    if etype == "loot"
                    else pygame.Color("#00BFFF")
                )
                pygame.draw.circle(
                    self.screen, color, (sx, sy - self.tile_h // 4), self.tile_h // 6
                )
                obj._screen_rect = pygame.Rect(
                    sx - 6, sy - 6 - self.tile_h // 4, 12, 12
                )

        # draw tooltip if any
        mx, my = pygame.mouse.get_pos()
        hover_info = self._pick_hover(mx, my)
        if hover_info:
            Tooltip.draw(self.screen, hover_info, (mx, my))

        # draw overlay text (orientation & instructions)
        self._draw_overlay()

        pygame.display.flip()

    def _draw_overlay(self):
        font = pygame.font.SysFont(None, 18)
        txt = f"Orientation: {self.orientation}  |  Pan: LEFT/RIGHT/UP/DOWN | Zoom: a/z | Rotate:  w/x |  Tiles: {len(self.room.ascii_map[0])}x{len(self.room.ascii_map)}"
        surf = font.render(txt, True, pygame.Color("white"))
        self.screen.blit(surf, (8, self.screen_h - 24))

    # ---------- hover detection ----------
    def _pick_hover(self, mx, my):
        # check entities first (actors/loots), then tiles
        # actors/loots have _screen_rect set in render_frame
        for aid, actor in self.actors.items():
            r = getattr(actor, "_screen_rect", None)
            if r and r.collidepoint(mx, my):
                # build tooltip content
                spec = self.theme.tiles.get("M") if "M" in self.theme.tiles else None
                short = actor.name
                longdesc = spec.long_description if spec else "A creature."
                return {
                    "title": short,
                    "body": f"{actor.name}\nFacing: {actor.facing}\n{longdesc}\n{actor.pos}",
                }

        for lid, loot in self.loots.items():
            r = getattr(loot, "_screen_rect", None)
            if r and r.collidepoint(mx, my):
                spec = self.theme.tiles.get("l") if "l" in self.theme.tiles else None
                longdesc = spec.long_description if spec else "An item."
                return {
                    "title": loot.name,
                    "body": f"{loot.name}\n{longdesc}\n{loot.pos}",
                }

        # tiles hitboxes
        for t in reversed(self.tile_hitboxes):  # topmost first
            r = t["rect"]
            if r.collidepoint(mx, my):
                x, y = t["coord"]
                ch = self.room.ascii_map[y][x]
                spec = self.theme.tiles.get(ch)
                if spec:
                    return {
                        "title": spec.name,
                        "body": f"{spec.long_description}\n{x}-{y}",
                    }
                else:
                    return {"title": f"Tile '{ch}'", "body": f"Unknown tile\n{x}-{y}"}
        return None

    # ---------- public controls ----------
    def rotate_left(self):
        self.orientation_index = (self.orientation_index + 1) % len(self.ORIENTATIONS)
        self.orientation = self.ORIENTATIONS[self.orientation_index]

    def rotate_right(self):
        self.orientation_index = (self.orientation_index - 1) % len(self.ORIENTATIONS)
        self.orientation = self.ORIENTATIONS[self.orientation_index]

    # ---------- main loop ----------
    def run(self):
        running = True
        zoom_step = 1.1
        while running:
            self.clock.tick(30)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        running = False
                    elif ev.key == pygame.K_w:
                        self.rotate_left()
                    elif ev.key == pygame.K_x:
                        self.rotate_right()
                    elif ev.key == pygame.K_UP:
                        self.cam_y += 50
                    elif ev.key == pygame.K_DOWN:
                        self.cam_y -= 50
                    elif ev.key == pygame.K_LEFT:
                        self.cam_x += 50
                    elif ev.key == pygame.K_RIGHT:
                        self.cam_x -= 50
                    elif ev.key == pygame.K_a:
                        self.zoom *= 1.0 / zoom_step
                        self.zoom = max(
                            1.0 / zoom_step**6, min(self.zoom, zoom_step**6)
                        )
                    elif ev.key == pygame.K_z:
                        self.zoom *= zoom_step
                        self.zoom = max(
                            1.0 / zoom_step**6, min(self.zoom, zoom_step**6)
                        )
                
            self.render_frame()
        pygame.quit()


# -------------------------
# Tooltip helper
# -------------------------


class Tooltip:
    @staticmethod
    def draw(surface: pygame.Surface, info: Dict[str, str], mouse_pos: Tuple[int, int]):
        """Draw a small translucent tooltip box with title/body near mouse_pos."""
        x, y = mouse_pos
        title = info.get("title", "")
        body = info.get("body", "")
        lines = [title] + body.splitlines()
        font = pygame.font.SysFont(None, 18)
        padding = 6
        # compute size
        w = 0
        h = 0
        rendered = []
        for i, line in enumerate(lines):
            s = font.render(line, True, pygame.Color("white"))
            rendered.append(s)
            w = max(w, s.get_width())
            h += s.get_height()
        box_w = w + padding * 2
        box_h = h + padding * 2
        box_x = x + 16
        box_y = y + 16
        # keep on screen
        sw, sh = surface.get_size()
        if box_x + box_w > sw:
            box_x = x - box_w - 16
        if box_y + box_h > sh:
            box_y = y - box_h - 16
        # background
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        pygame.draw.rect(bg, (255, 255, 255, 30), bg.get_rect(), 1)
        surface.blit(bg, (box_x, box_y))
        # draw text
        oy = box_y + padding
        for s in rendered:
            surface.blit(s, (box_x + padding, oy))
            oy += s.get_height()


# -------------------------
# Main (example usage)
# -------------------------


def main(theme_yaml: str, room_yaml: str):
    # load theme + room
    theme = Theme.load(theme_yaml)
    room = Room.load(room_yaml, theme)
    renderer = IsometricRenderer(room)
    renderer.run()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python renderer_isometric.py <theme.yaml> <room.yaml>")
        sys.exit(1)
    theme_yaml = sys.argv[1]
    room_yaml = sys.argv[2]
    main(theme_yaml, room_yaml)
