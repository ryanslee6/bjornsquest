from entities.stats import Stats
import pygame

class Monster:
    def __init__(self, name = "Goblin", level = 1):
        self.name = name
        self.level = level
        self.stats = Stats(
            hp = 50 + level * 10,
            mp = 20 + level * 5,
            strength = 5 + level * 2,
            dexterity = 3 + level,
            constitution = 5 + level * 2,
        )
        self.exp_reward = 15
        self.alive = True

        try:
            self.sprite = pygame.image.load("assets/images/goblin1.png").convert_alpha()
        except:
            self.sprite = None
            print("⚠️ Goblin sprite missing — using placeholder box.")

        if self.sprite:
            self.sprite = pygame.transform.scale(self.sprite, (180, 160))


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
