

from dndassist.room import RoomMap
from dndassist.themes.themes import Theme
from dndassist.character import Character
from dndassist.game_engine import GameEngine
from dndassist.isometric_renderer import IsometricRenderer
liora = Character.load("liora.yaml")
liora.save("liora_save.yaml")
garruk = Character.load("garruk.yaml")
garruk.save("garruk_save.yaml")
selra = Character.load("selra.yaml")
selra.save("selra_save.yaml")

forest_theme = Theme.load("./forest_theme.yaml")
room = RoomMap.load("forest_glade.yaml", forest_theme)
room.add_actor("liora", (2,3),symbol="@", facing="SE", character=liora)
room.add_actor("garruk", (8,3),symbol="&", facing="N", character=garruk)
room.add_actor("selra", (6,8),symbol="ç", facing="NW", character=selra)

#renderer = IsometricRenderer(room)
#renderer.run()
game = GameEngine(room=room)