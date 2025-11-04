from entities.stats import Stats
from data.exp_table import exp_table
import pygame

class Player:
    def __init__(self, name = "Bjorn"):
        self.name = name
        self.stats = Stats()
        self.level = 1
        self.exp = 0
        #self.exp_to_level = 15
        self.inventory = {}

        try:
            self.sprite = pygame.image.load("assets/images/bjorn1_cut.png").convert_alpha()
        except:
            self.sprite = None
            print("⚠️ Player sprite missing — using placeholder.")

        if self.sprite:
            self.sprite = pygame.transform.scale(self.sprite, (180, 160))

    def add_item(self, item_name, quantity = 1):
        if item_name in self.inventory:
            self.inventory[item_name] += quantity
        else:
            self.inventory[item_name] = quantity

        print(f"[INVENTORY] +{quantity} {item_name} (Total: {self.inventory[item_name]})")

    def print_inventory(self):
        print("\n=== INVENTORY ===")
        if not self.inventory:
            print("Empty")
        else:
            for item, qty in self.inventory.items():
                print(f"{item}: {qty}")
        print("=================\n")

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

    @property
    def exp_to_level(self):
        if self.level >= len(exp_table):
            return 0
        return exp_table[self.level]
    
    def exp_progress(self):
        #exp required up to previous level
        prev_required = exp_table[self.level - 1] if self.level > 1 else 0

        next_required = exp_table[self.level]

        exp_into_level = self.exp - prev_required

        exp_needed = next_required - prev_required

        return exp_into_level, exp_needed