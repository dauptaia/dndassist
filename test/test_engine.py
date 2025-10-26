

from dndassist.room import RoomMap
from dndassist.character import Character
from dndassist.game_engine import GameEngine

scenario = "SCENARIO_A"

#Load first characters
liora = Character.load(scenario,"liora.yaml")
garruk = Character.load(scenario,"garruk.yaml")
selra = Character.load(scenario,"selra.yaml")
#Load first room
room = RoomMap.load(scenario,"forest_glade.yaml")

#Place characters
room.add_actor("liora", (2,3),symbol="@", facing="SE", character=liora)
room.add_actor("garruk", (8,3),symbol="&", facing="N", character=garruk)
room.add_actor("selra", (6,8),symbol="ç", facing="NW", character=selra)

#Start game
game = GameEngine(room=room)