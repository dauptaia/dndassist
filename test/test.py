from dndassist.attack import attack


from dndassist.character import Character

lana1 = Character.load("liora.yml")
lana2 = Character.load("liora.yml")

combat = True
attacker = lana1
defender = lana2
i=0
while combat:
    i=i+1
    print(f"====turn{i}")
    print(lana1.current_hp,"<>", lana2.current_hp )

    dmg = attack(attacker,"Dagger", defender,autoroll=False)
    defender.current_hp -= min(dmg,defender.current_hp)

    attacker, defender = defender, attacker
    
    if lana1.current_hp == 0:
        print("2 wins")
        combat=False
    if lana2.current_hp == 0:
        print("1 wins")
        combat=False