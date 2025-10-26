from dndassist.room import RoomMap
from dndassist.isometric_renderer import IsometricRenderer


SCENARIO = "./SCENARIO_A"
room = RoomMap.load(SCENARIO, "forest_glade.yaml")

renderer = IsometricRenderer(room)
renderer.run()
#room.draw_map()
#print(room.render_ascii())