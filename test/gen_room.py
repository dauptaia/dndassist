import random

width = 40
height = 40

out = []
for j in range(height):
    row = ""
    for col in range(width):
        rnd = random.random()
        if rnd < 0.33:
            sym = "O"
        elif rnd < 0.6:
            sym = "o"
        # elif rnd < 0.7:
        #     sym = "."
        else: 
            sym = " "
        row+= sym
    out.append(row)

for j in range(height):
    print(f' - "{out[j]}"')