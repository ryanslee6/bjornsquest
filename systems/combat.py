import time
import pygame
import random
import math
from entities.monster import Monster
from random import randint
from systems.spell_system import get_default_spellbook


class CombatManager:
    def __init__(self, player, current_monster, loot_system):
        self.player = player
        self.current_monster = current_monster
        self.combat_log = []
        self.loot_log = []
        self.floating_text_player = []
        self.floating_text_enemy = []
        self.projectiles = []
        self.active_burns = []
        self.combat_active = True
        self.monster_defeated = False
        self.respawn_time = None
        self.player_initiated = False
        self.auto_combat_enabled = False
        self.loot_system = loot_system
        self.spellbook = get_default_spellbook()

        self.last_player_attack = time.time()
        self.last_monster_attack = time.time()

        self.player_attack_delay = 2.0
        self.monster_attack_delay = 2.0

        self.post_respawn_delay = 1000 #ms
        self.ready_time = None

        self.heal_particles = []

        self.player_attack_anim = None
        self.player_attack_anim_start = 0
        self.player_attack_anim_duration = 500  #total ms for full swing
        
        self.enemy_hit_flash_timer = 0
        self.enemy_hit_flash_duration = 200  #ms
        self.enemy_hit_flash_delay = int(self.player_attack_anim_duration * 0.6)

        


    def update(self, dt):
        if not self.combat_active:
            return False

        current_time = time.time()
        something_happened = False
        
        if self.ready_time is not None:
                    if pygame.time.get_ticks() < self.ready_time:
                        return
                    self.ready_time = None

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
                dmg, is_crit = self.player.attack(self.current_monster)
                if is_crit:
                    self.combat_log.append(f"{self.player.name} crits {self.current_monster.name} for {dmg} damage!")
                    text_type = "crit"
                else:
                    self.combat_log.append(f"{self.player.name} hits {self.current_monster.name} for {dmg} damage!")
                    text_type = "damage"
                self.last_player_attack = current_time
                something_happened = True

                self.add_floating_text(
                     str(dmg),
                     0, 0,
                     text_type = text_type,
                     target = "enemy"
                )

                self.player_attack_anim = "windup"
                self.player_attack_anim_start = pygame.time.get_ticks()

                self.enemy_hit_flash_timer = pygame.time.get_ticks() + self.enemy_hit_flash_delay

        if current_time - self.last_monster_attack >= self.monster_attack_delay:
            if self.player.is_alive() and self.current_monster.is_alive():
                dmg, is_crit = self.current_monster.attack(self.player)
                if is_crit:
                    self.combat_log.append(f"{self.current_monster.name} crits {self.player.name} for {dmg} damage!")
                    text_type = "crit"
                else:
                    self.combat_log.append(f"{self.current_monster.name} hits {self.player.name} for {dmg} damage!")
                    text_type = "damage"
                self.last_monster_attack = current_time
                something_happened = True

                self.add_floating_text(
                     str(dmg),
                     0, 0,
                     text_type = text_type,
                     target = "player"
                )

        if not self.current_monster.is_alive() and not self.monster_defeated:
            self.monster_defeated = True
            
            self.combat_log.append(f"{self.current_monster.name} was defeated!")
            exp = self.current_monster.exp_reward
            drops = self.loot_system.generate_loot(self.current_monster.name)
            print("You found:", drops)
            
            for drop in drops:
                item_name = drop["item"]
                qty = drop["quantity"]

                if item_name.lower() == "gold coins":
                    self.player.gold += qty
                    print(f"[LOOT] +{qty} Gold Coins (Total: {self.player.gold})")
                    self.loot_log.append(f"+{qty} Gold Coins")
                    continue
                else:                    
                    self.player.add_item(item_name, qty)
                    self.loot_log.append(f"+{qty} {item_name}")      
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

        now = pygame.time.get_ticks()
        if not hasattr(self, "_last_tick"):
            self._last_tick = now
        dt = now - self._last_tick
        self.last_tick = now
        #self.update_floating_text(dt)

        return something_happened
    
    def add_floating_text(self, text, x, y, color = None, target = "enemy", text_type = "damage"):
        presets = {
             "damage": {"color": (255, 220, 50), "outline": (0, 0, 0), "font_size": 70},
             "crit": {"color": (255, 80, 80), "outline": (255, 255, 100), "font_size": 80},
             "heal": {"color": (120, 255, 120), "outline": (0, 100, 0), "font_size": 40},
             "mana": {"color": (100, 150, 255), "outline": (0, 0, 80), "font_size": 40},
             "spell": {"color": (100, 200, 255), "outline": (0, 40, 120), "font_size": 70},
             "burn": {"color": (255, 100, 0), "outline": (80, 0, 0), "font_size": 40}
        }
        style = presets.get(text_type, presets["damage"])
        if color:
             style["color"] = color

        if x == 0 and y == 0:
            surf = pygame.display.get_surface()
            sw = surf.get_width() if surf else 800
            sh = surf.get_height() if surf else 700

            if target == "player":
                base_x = 180
                base_y = sh - 420
                if text_type == "heal":
                    x = base_x - 80
                elif text_type == "spell":
                    x = base_x + 120
                elif text_type == "burn":
                    x = base_x + 60
                else:
                    x = base_x + 80
                
                y = base_y
            
            elif target == "enemy":
                base_x = sw - 200 
                base_y = sh - 420
                if text_type == "heal":
                    x = base_x + 80
                elif text_type == "spell":
                    x = base_x - 120
                elif text_type == "burn":
                    x = base_x - 60
                else:
                    x = base_x - 80
                
                y = base_y
        
        

        entry = {
            "text": text,
            "x": x + random.randint(-6, 6),
            "y": y,
            "base_y": y,
            "alpha": 255,
            "scale": 1.0,
            "float_speed": 0.4,
            "time": 0,
            "outline": style["outline"],
            "color": style["color"],
            "font_size": style["font_size"],
            "target": target,
            "type": text_type,
        }

        if target == "enemy":
            self.floating_text_enemy.append(entry)
        else:
            self.floating_text_player.append(entry)

    def update_floating_text(self, dt):
        for group in [self.floating_text_enemy, self.floating_text_player]:
            for entry in group[:]:
                if "time" not in entry:
                    entry["time"] = 0
                    entry["vy"] = -0.02
                    entry["base_y"] = entry.get("y", 0)
                    entry["alpha"] = 255
                if "vy" not in entry:
                    entry["vy"] = -0.02
                
                entry["time"] += dt

                entry["y"] += entry["vy"] * dt

                

                lifetime = 3000
                fade_start = 1500
                
                if entry["time"] > fade_start:
                    fade_progress = (entry["time"] - fade_start) / (lifetime - fade_start)
                    entry["alpha"] = int(255 * max(0, 1 - fade_progress))
                else:
                    entry["alpha"] = 255

                if entry["time"] >= lifetime or entry["alpha"] <= 0:
                    group.remove(entry)

    def draw_floating_text(self, surface):
        for group in [self.floating_text_enemy, self.floating_text_player]:
            for entry in group:
                #fallback defaults
                font_size = entry.get("font_size", 28)
                color = entry.get("color", (255, 255, 255))
                outline = entry.get("outline", (0, 0, 0))
                alpha = entry.get("alpha", 255)
                scale = entry.get("scale", 1.0)
                x = entry.get("x", 0)
                y = entry.get("y", 0)
                text = entry.get("text", "")
                
                
                font = pygame.font.Font(None, font_size)
                text_surf = font.render(text, True, color)
                text_surf.set_alpha(alpha)

                scaled = pygame.transform.rotozoom(text_surf, 0, scale)
                rect = scaled.get_rect(center = (x, y))

                for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    outline_surf = font.render(text, True, outline)
                    outline_surf.set_alpha(alpha)
                    outline_scaled = pygame.transform.rotozoom(outline_surf, 0, scale)
                    surface.blit(outline_scaled, (rect.x + ox, rect.y + oy))

                surface.blit(scaled, rect)

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
             

    def cast_spell(self, spell_name):
        #start combat if not in progress
        if not self.combat_active or not self.player_initiated:
            self.player_initiated = True
            self.combat_active = True
            print("⚔️ Combat initiated by spell cast!")


        for spell in self.spellbook:
            if spell.name.lower() == spell_name.lower():
                if not spell.can_cast(self.player):
                    return False
                success = spell.cast(self.player, self.current_monster, self)
                if success:
                    now = time.time()
                    self.laster_player_attack = now
                return success
        print(f"[ERROR] Spell '{spell_name}' not found in spellbook!")
        return False


    def spawn_projectile(self, image, start_x, start_y, target_x, target_y, speed = 400, damage = None, text_type = "damage"):
        projectile = {
            "image": image,
            "x": start_x,
            "y": start_y,
            "target_x": target_x,
            "target_y": target_y,
            "speed": speed,
            "damage": damage,
            "text_type": text_type,
            "done": False
        }
        self.projectiles.append(projectile)

    def update_projectiles(self, dt):
        for p in self.projectiles[:]:
            dx = p["target_x"] - p["x"]
            dy = p["target_y"] - p["y"]
            dist = (dx**2 + dy**2) ** 0.5
            if dist < 20:
                p["done"] = True
                continue
            step = p["speed"] * (dt / 1000)
            if dist > 0:
                p["x"] += dx / dist * step
                p["y"] += dy / dist * step

        self.projectiles = [p for p in self.projectiles if not p["done"]]

    def add_burn_effect(self, target, damage, interval, duration):
        self.active_burns.append({
            "target": target,
            "damage": damage,
            "interval": interval,
            "duration": duration,
            "elapsed": 0,
            "tick_timer": 0,
        })

    def update_burns(self, dt):
        for burn in self.active_burns[:]:
            target = burn["target"]

            if not target.is_alive():
                print(f"🔥 Burn on {target.name} ended (target defeated).")
                self.active_burns.remove(burn)
                continue
            
            
            burn["elapsed"] += dt / 1000
            burn["tick_timer"] += dt / 1000

            if burn["tick_timer"] >= burn["interval"]:
                burn["tick_timer"] = 0
                burn["target"].stats.hp = max(0, burn["target"].stats.hp - burn["damage"])
                
                log_message = f"{burn['target'].name} takes {burn['damage']} burn damage!"
                print(log_message)
                if hasattr(self, "combat_log"):
                    self.combat_log.append(log_message)

                self.add_floating_text(
                    f"{burn['damage']}",
                    0, 0,
                    text_type = "burn",
                    target = "enemy"
                )
            if burn["elapsed"] >= burn["duration"]:
                self.active_burns.remove(burn)