
class Stats:
    def __init__(self, hp = 500, mp = 50, strength = 10, dexterity = 5, constitution = 10, intelligence = 5):
        self.hp = hp
        self.max_hp = hp
        self.mp = mp
        self.max_mp = mp
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence

        self.crit_chance = 0.05
        self.dodge_chance = 0.05
        self.attack_speed = 1.0
        self.armor = 0
        self.hp_regen = 0.1
        self.mp_regen = 0.05