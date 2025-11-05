import time
import pygame
import random
from entities.monster import Monster
from random import randint


class CombatManager:
    def __init__(self, player, current_monster, loot_system):
        self.player = player
        self.current_monster = current_monster
        self.combat_log = []
        self.loot_log = []
        self.floating_text_player = []
        self.floating_text_enemy = []
        self.combat_active = True
        self.monster_defeated = False
        self.respawn_time = None
        self.player_initiated = False
        self.auto_combat_enabled = False
        self.loot_system = loot_system

        self.last_player_attack = time.time()
        self.last_monster_attack = time.time()

        self.player_attack_delay = 1.0
        self.monster_attack_delay = 1.5

        self.post_respawn_delay = 1000 #ms
        self.ready_time = None

        self.heal_particles = []

        #self.combat = CombatManager(self.player, self.current_monster, self.loot_system)
        #self.combat.auto_combat_enabled = self.auto_combat_enabled


    def update(self):
        if not self.combat_active:
            return False

        current_time = time.time()
        something_happened = False
        
        if self.ready_time is not None:
                    if pygame.time.get_ticks() < self.ready_time:
                        return
                    self.ready_time = None

        for t in self.floating_text_player[:]:
             t["offset_y"] -= 0.5
             t["alpha"] -= 3
             if t["alpha"] <= 0:
                  self.floating_text_player.remove(t)

        for t in self.floating_text_enemy[:]:
             t["offset_y"] -= 0.5
             t["alpha"] -= 3
             if t["alpha"] <= 0:
                  self.floating_text_enemy.remove(t)

        if self.monster_defeated:
            if pygame.time.get_ticks() >= self.respawn_time:
                self.current_monster = Monster(self.current_monster.name)
                self.current_monster.stats.hp = self.current_monster.stats.max_hp
                self.current_monster.stats.mp = self.current_monster.stats.max_mp
                
                self.monster_defeated = False
                self.respawn_time = None

                self.ready_time = pygame.time.get_ticks() + self.post_respawn_delay

                if self.auto_combat_enabled:
                     self.player_initiated = True

            return

        if not self.player_initiated:
            if hasattr(self, "auto_combat_enabled") and self.auto_combat_enabled:
                 self.player_initiated = True
            else:
                 return

        if current_time - self.last_player_attack >= self.player_attack_delay:
            if self.player.is_alive() and self.current_monster.is_alive():
                dmg = self.player.attack(self.current_monster)
                self.combat_log.append(f"{self.player.name} hits {self.current_monster.name} for {dmg} damage!")
                self.last_player_attack = current_time
                something_happened = True

                self.add_floating_text(
                     str(dmg),
                     0, 0,
                     (255, 60, 60),
                     target = "enemy"
                )

        if current_time - self.last_monster_attack >= self.monster_attack_delay:
            if self.player.is_alive() and self.current_monster.is_alive():
                dmg = self.current_monster.attack(self.player)
                self.combat_log.append(f"{self.current_monster.name} hits {self.player.name} for {dmg} damage!")
                self.last_monster_attack = current_time
                something_happened = True

                self.add_floating_text(
                     str(dmg),
                     0, 0,
                     (255, 255, 100),
                     target = "player"
                )

        if not self.current_monster.is_alive() and not self.monster_defeated:
            self.monster_defeated = True
            
            self.combat_log.append(f"{self.current_monster.name} was defeated!")
            exp = self.current_monster.exp_reward
            drops = self.loot_system.generate_loot(self.current_monster.name)
            print("You found:", drops)
            for drop in drops:
                self.player.add_item(drop["item"], drop["quantity"])

                self.loot_log.append(f"+{drop['quantity']} {drop['item']}")
                self.loot_log = self.loot_log[-5:]
            self.player.gain_exp(exp)
            self.combat_active = True
            something_happened = True
            self.player_initiated = False
            
            self.respawn_time = pygame.time.get_ticks() + 1000
            
            return
            
        


        if not self.player.is_alive():
            self.combat_log.append(f"{self.player.name} was defeated!")
            self.combat_active = False
            something_happened = True

        return something_happened
    
    def add_floating_text(self, text, x, y, color, target = "enemy"):
        entry = {
            "text": text,
            "x": x,
            "y": y,
            "color": color,
            "alpha": 255,
            "float_speed": 0.4,
            "offset_x": random.randint(-10, 10),
            "offset_y": 0
        }

        if target == "enemy":
            self.floating_text_enemy.append(entry)
        else:
            self.floating_text_player.append(entry)

    def spawn_heal_particles(self, x, y):
         for _ in range(16):
              self.heal_particles.append({
                   "x": x + randint(-10, 10),
                   "y": y + randint(-10, 10),
                   "vx": randint(-1, 1),
                   "vy": -2,
                   "alpha": 255,
                   "size": randint(2, 4),
                   "color": (80, 255, 80),
              })
             


