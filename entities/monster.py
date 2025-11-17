from entities.stats import Stats
import pygame, json, os
import time

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
            min_damage = data.get("min_damage", 1),
            max_damage = data.get("max_damage", 3),
            dodge_chance = data.get("dodge_chance", 0.0),
            attack_speed = data.get("attack_speed", 1.0),
            hit_chance = data.get("hit_chance", 0.90),
            is_player = False
        )
        
        self.exp_reward = data["exp_reward"]
        self.sprite_path = os.path.join("assets", "images", data["sprite"])
        self.sprite = pygame.image.load(self.sprite_path).convert_alpha()
        
        
        self.alive = True

        self.active_effects = []

        
        
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
        #print("[DEBUG MONSTER ATTACK] hit_chance=", self.stats.hit_chance)

        is_miss = random.random() > self.stats.hit_chance
        if is_miss:
            return 0, True, False, False

        is_dodged = random.random() < target.stats.dodge_chance
        if is_dodged:
            return 0, False, False, True
        
        min_dmg, max_dmg = self.stats.get_damage_range()
        base_damage = random.randint(min_dmg, max_dmg)

        if getattr(self, "is_stunned", False):
            return 0, False, False, False

        
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:    
            base_damage *= 2
        
        damage = max(0, base_damage - target.stats.armor)
        
        target.stats.hp = max(0, target.stats.hp - damage)
        
        return damage, is_miss, is_crit, is_dodged
    
    def add_status_effect(self, name, duration, icon = None, color = (200, 200, 200)):
        if not hasattr(self, "active_effects"):
            self.active_effects = []

        self.active_effects.append({
            "name": name,
            "expires": time.time() + duration,
            "icon": icon,
            "color": color
        })

    def remove_expired_effects(self):
        now = time.time()
        new_list = []

        for effect in self.active_effects:
            if now < effect["expires"]:
                new_list.append(effect)
            else:
                if "revert" in effect:
                    effect["revert"](self)

        self.active_effects = new_list
        
