from entities.stats import Stats
from data.exp_table import exp_table

class Player:
    def __init__(self, name = "Bjorn"):
        self.name = name
        self.stats = Stats()
        self.level = 1
        self.exp = 0

    def is_alive(self):
        return self.stats.hp > 0
    
    def attack(self, target):
        import random
        base_damage = self.stats.strength
        if random.random() < self.stats.crit_chance:
            base_damage *= 2
        damage = max(0, base_damage - target.stats.armor)
        target.stats.hp -= damage
        return damage
    
    def gain_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.level < len(exp_table) and self.exp >= exp_table[self.level]:
            self.level += 1
            leveled_up = True

            self.stats.strength += 1
            self.stats.dexterity += 1
            self.stats.constitution += 1
            self.stats.intelligence += 1
            
            self.stats.hp = self.stats.max_hp
            self.stats.mp = self.stats.max_mp

            print(f"Leveled up! New level: {self.level}")
            print(f"Stats increased! STR:{self.stats.strength} DEX:{self.stats.dexterity} CON:{self.stats.constitution} INT:{self.stats.intelligence}")
            print(f"HP/MP fully restored: {self.stats.hp}/{self.stats.max_hp} HP, {self.stats.mp}/{self.stats.max_mp} MP")
        if not leveled_up:
            print(f"{self.name} gained {amount} exp!")