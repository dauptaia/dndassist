from dndassist.room import RoomMap
from dndassist.character import Character
from dndassist.isometric_renderer import IsometricRenderer


scenario = "./CRIMSON_MOON"


#Load first room
room = RoomMap.load(scenario,"forest_bridge.yaml")

#Place characters
liora = Character.load(scenario,"liora.yaml")
garruk = Character.load(scenario,"garruk.yaml")
selra = Character.load(scenario,"selra.yaml")
room.add_actor("liora", (2,3),symbol="@", facing="SE", character=liora)
room.add_actor("garruk", (8,3),symbol="&", facing="N", character=garruk)
room.add_actor("selra", (6,8),symbol="ç", facing="NW", character=selra)

renderer = IsometricRenderer(room)
renderer.run()
room.draw_map()
print(room.render_ascii())