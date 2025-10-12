from dndassist.room import RoomMap

# ascii_map = """
# WWWWWWWWWW|
# W  OM   lW|
# W  .  O  W|
# W      G W|
# WWWWWWWWWW|
# """



#room=RoomMap.load("HallEchoes.yaml")
with open("bridge.map", "r") as fin:
    ascii_map = fin.read()
print(ascii_map)
room = RoomMap.from_ascii("Bridge", ascii_map)
room.add_actor("Aelar", pos=(8, 2), symbol="@", facing="SE")
room.add_actor("Liana", pos=(9, 2), symbol="&", facing="SE")

print(room.actors)
print(room.render_ascii())
print(room.render_ascii(mode="traversable"))
print(room.describe_view_los("Liana"))
print()
room.move_actor("Liana", 1, 0)
print(room.render_ascii())
print(room.describe_view_los("Liana"))
#room.pick_up_loot("Player")

#room.save("HallEchoes.yaml")

#room.load("HallEchoes.yaml")


print(room.render_ascii())