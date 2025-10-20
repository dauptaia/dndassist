from dndassist.room import RoomMap
from dndassist.themes.themes import Theme
from dndassist.isometric_renderer import IsometricRenderer
# ascii_map = """
# WWWWWWWWWW|
# W  OM   lW|
# W  .  O  W|
# W      G W|
# WWWWWWWWWW|
# """

forest_theme = Theme.load("./forest_theme.yaml")
#room=RoomMap.load("HallEchoes.yaml")
#with open("bridge.map", "r") as fin:
#    ascii_map = fin.read()
#print(ascii_map)
room = RoomMap.load("forest_glade.yaml", forest_theme)
#room.add_actor("Aelar", pos=(2, 2), symbol="@", facing="SE")
#room.add_actor("Liana2", pos=(3, 2), symbol="&", facing="SE")


renderer = IsometricRenderer(room)
renderer.run()

print(room.actors)
print(room.render_ascii(spaced=True))
#print(room.render_ascii(mode="traversable"))
print(room.describe_view_los("Grunt"))
# print()
# room.move_actor("Liana", 1, 0)
# print(room.render_ascii())
# print(room.describe_view_los("Liana"))
#room.pick_up_loot("Player")

#room.save("HallEchoes.yaml")

#room.load("HallEchoes.yaml")


print(room.render_ascii())