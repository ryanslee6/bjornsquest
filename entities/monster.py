from entities.stats import Stats
import pygame, json, os

class Monster:
    

    def __init__(self, name):       
        MONSTER_DATA_PATH = os.path.join("data", "monster_list.json")
    
        with open(MONSTER_DATA_PATH, "r") as f:
            MONSTER_DATA = json.load(f)

        data = MONSTER_DATA[name]   
        self.name = name
        self.level = data["level"]
        
        self.stats = Stats(
            hp = data["base_hp"],
            mp = data["base_mp"],
            strength = data["strength"],
            dexterity = data["dexterity"],
            constitution = data["constitution"],
            intelligence = data["intelligence"],
            is_player = False
        )
        self.exp_reward = data["exp_reward"]
        self.sprite_path = os.path.join("assets", "images", data["sprite"])
        self.sprite = pygame.image.load(self.sprite_path).convert_alpha()
        
        
        self.alive = True

        
        
        #try:
        #    self.sprite = pygame.image.load("assets/images/goblin1.png").convert_alpha()
        #except:
        #    self.sprite = None
        #    print("⚠️ Goblin sprite missing — using placeholder box.")

        #if self.sprite:
        #    self.sprite = pygame.transform.scale(self.sprite, (180, 160))


    def is_alive(self):
        return self.stats.hp > 0
    
    def attack(self, target):
        import random
        base_damage = self.stats.strength
        
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:    
            base_damage *= 2
        damage = max(0, base_damage - target.stats.armor)
        target.stats.hp = max(0, target.stats.hp - damage)
        return damage, is_crit
