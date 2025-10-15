

from dndassist.room import RoomMap
from dndassist.themes.themes import Theme
from dndassist.character import Character
from dndassist.game_engine import GameEngine

liora = Character.load("liora.yml")
garruk = Character.load("garruk.yaml")
selra = Character.load("selra.yaml")

forest_theme = Theme.load("./forest_theme.yaml")
room = RoomMap.load("forest_glade.yaml", forest_theme)
room.add_actor("liora", (2,3),symbol="@", facing="NS", character=liora)
room.add_actor("garruk", (2,4),symbol="&", facing="NS", character=garruk)
room.add_actor("selra", (2,5),symbol="ç", facing="NS", character=selra)
room.render_ascii(spaced=True)

game = GameEngine(room=room)