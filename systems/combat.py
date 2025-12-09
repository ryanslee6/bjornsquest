import time
import pygame
import random
import math
from entities.monster import Monster
from random import randint
from systems.spell_system import get_default_spellbook


class CombatManager:
    def __init__(self, player, current_monster, loot_system, game):
        self.player = player
        self.current_monster = current_monster
        self.game = game
        self.combat_log = []
        self.loot_log = []
        self.max_log_entries = 50
        self.log_scroll = 0
        self.log_line_height = 20
        self.user_is_scrolling = False
        self.force_scroll_to_bottom = False
        self.floating_text_player = []
        self.floating_text_enemy = []
        self.projectiles = []
        self.active_burns = []
        self.battlecry_waves = []
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
        self.heal_spell_particles = []

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

        self._update_effects(self.player, current_time)
        self._update_effects(self.current_monster, current_time)
        
        if self.ready_time is not None:
                    if pygame.time.get_ticks() < self.ready_time:
                        return
                    self.ready_time = None

        if not self.player_initiated:
            if hasattr(self, "auto_combat_enabled") and self.auto_combat_enabled:
                 self.player_initiated = True
            else:
                 return

        #prevent enemy action if stunned
        if hasattr(self.current_monster, "is_stunned") and self.current_monster.is_stunned:
            if time.time() < self.current_monster.stun_expires_at:
                return
            else:
                self.current_monster.is_stunned = False

        player_eff = self.player.stats.compute_effective_stats(self.player.active_effects)
        if current_time - self.last_player_attack >= player_eff["attack_speed"]:
            if self.player.is_alive() and self.current_monster.is_alive():
                dmg, is_miss, is_crit, is_dodged = self.player.attack(self.current_monster)
                if is_miss:
                    self.add_log(f"{self.player.name} misses {self.current_monster.name}!")
                    self.add_floating_text("Miss!", 0, 0, text_type="combat", target="enemy")
                    self.last_player_attack = current_time
                    something_happened = True
                    return
                elif is_dodged:
                    self.add_log(f"{self.current_monster.name} dodges {self.player.name}'s attack!")
                    self.add_floating_text("Dodged!", 0, 0, text_type = "combat", target = "enemy")
                    self.last_player_attack = current_time
                    something_happened = True
                    return
                elif is_crit:
                    self.add_log(f"{self.player.name} crits {self.current_monster.name} for {dmg} damage!")
                    text_type = "crit"
                else:
                    self.add_log(f"{self.player.name} hits {self.current_monster.name} for {dmg} damage!")
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

        monster_eff = self.current_monster.stats.compute_effective_stats(self.current_monster.active_effects)
        ability = self.current_monster.choose_ability(self.game)
        
        # effects DEBUG
        print("Monster Effective Stats:",
            "DMG", monster_eff["min_damage"], "-", monster_eff["max_damage"])#,
        #    "| AS", monster_eff["attack_speed"],
        #    "| Armor", monster_eff["armor"],
        #    "| Effects:", self.current_monster.active_effects)
        

        if current_time - self.last_monster_attack >= monster_eff["attack_speed"]:
            if self.player.is_alive() and self.current_monster.is_alive():
                dmg, is_miss, is_crit, is_dodged = self.current_monster.attack(self.player)
                
                if ability:
                    self.add_log(f"{self.current_monster.name} uses {ability}!")
                    self.current_monster.cast_ability(ability, self.player, self.game)
                    latest_effect = self.current_monster.active_effects[-1]
                    display_name = latest_effect["name"]
            
                    self.add_floating_text(
                        display_name,
                        0, 0,
                        text_type = "buff",
                        target = "enemy"
                    )
                
                if is_miss:
                    self.add_log(f"{self.current_monster.name} misses {self.player.name}!")
                    self.add_floating_text("Miss!", 0, 0, text_type="combat", target="player")
                    self.last_player_attack = current_time
                    something_happened = True
                    return
                
                elif is_dodged:
                    self.add_log(f"{self.player.name} dodges {self.current_monster.name}'s attack!")
                    self.add_floating_text("Dodged!", 0, 0, text_type = "combat", target = "player")
                    self.last_monster_attack = current_time
                    something_happened = True
                    return
                elif is_crit:
                    self.add_log(f"{self.current_monster.name} crits {self.player.name} for {dmg} damage!")
                    text_type = "crit"
                else:
                    self.add_log(f"{self.current_monster.name} hits {self.player.name} for {dmg} damage!")
                    text_type = "damage"
                self.last_monster_attack = current_time
                something_happened = True

                self.add_floating_text(
                     str(dmg),
                     0, 0,
                     text_type = text_type,
                     target = "player"
                )

            
        if not self.player.is_alive():
            self.add_log(f"{self.player.name} was defeated!")
            self.combat_active = False
            something_happened = True

        now = pygame.time.get_ticks()
        if not hasattr(self, "_last_tick"):
            self._last_tick = now
        #dt = now - self._last_tick
        self.last_tick = now
        #self.update_floating_text(dt)

        return something_happened
    
    def add_floating_text(self, text, x, y, color = None, target = "enemy", text_type = "damage", icon = None):
        presets = {
             "damage": {"color": (255, 220, 50), "outline": (0, 0, 0), "font_size": 70},
             "crit": {"color": (255, 80, 80), "outline": (255, 255, 100), "font_size": 80},
             "heal": {"color": (120, 255, 120), "outline": (0, 100, 0), "font_size": 40},
             "mana": {"color": (100, 150, 255), "outline": (0, 0, 80), "font_size": 40},
             "spell": {"color": (100, 200, 255), "outline": (0, 40, 120), "font_size": 70},
             "spell_crit": {"color": (180, 120, 255), "outline": (255, 255, 180), "font_size": 80},
             "burn": {"color": (255, 100, 0), "outline": (80, 0, 0), "font_size": 40},
             "buff": {"color": (80, 180, 255), "outline": (255, 255, 120), "font_size": 40},
             "debuff": {"color": (220, 60, 120), "outline": (40, 0, 40), "font_size": 40},
             "poison": {"color": (120, 255, 80), "outline": (20, 60, 0), "font_size": 40},
             "combat": {"color": (220, 230, 255), "outline": (40, 40, 80), "font_size": 35}
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
                elif text_type == "mana":
                    x = base_x - 75
                elif text_type == "spell":
                    x = base_x + 120
                elif text_type == "spell_crit":
                    x = base_x + 115
                elif text_type == "burn":
                    x = base_x + 60
                elif text_type == "buff":
                    x = base_x - 10
                elif text_type == "debuff":
                    x = base_x - 10
                elif text_type == "combat":
                    x = base_x - 7
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
                elif text_type == "spell_crit":
                    x = base_x - 115
                elif text_type == "burn":
                    x = base_x - 60
                elif text_type == "combat":
                    x = base_x + 7
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
            "float_speed": 40,
            "time": 0,
            "outline": style["outline"],
            "color": style["color"],
            "font_size": style["font_size"],
            "target": target,
            "type": text_type,
            "icon": icon
        }

        if target == "enemy":
            self.floating_text_enemy.append(entry)
        else:
            self.floating_text_player.append(entry)

    def update_floating_text(self, dt):
        for group in [self.floating_text_enemy, self.floating_text_player]:
            for entry in group[:]:
                # Increase internal timer
                entry["time"] += dt

                # FLOAT UPWARD — use a real speed (pixels per second)
                float_speed = entry.get("float_speed", 40)  # 40 px/sec upward
                entry["y"] += -float_speed * dt

                # TIMING (seconds)
                lifetime = 1.2        # total life
                fade_start = 0.6      # when fading begins

                # FADING
                if entry["time"] > fade_start:
                    fade_progress = (entry["time"] - fade_start) / (lifetime - fade_start)
                    entry["alpha"] = int(255 * (1 - max(0, min(1, fade_progress))))
                else:
                    entry["alpha"] = 255

                # REMOVE WHEN DONE
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
                icon = entry.get("icon", None)
                
                
                font = pygame.font.Font(None, font_size)
                text_surf = font.render(text, True, color)
                text_surf.set_alpha(alpha)

                scaled = pygame.transform.rotozoom(text_surf, 0, scale)
                rect = scaled.get_rect(center = (x, y))

                if icon:
                    icon_h = int(font_size * scale)
                    icon_w = icon_h
                    icon_surf = pygame.transform.smoothscale(icon, (icon_w, icon_h))

                    icon_rect = icon_surf.get_rect(center = (x - icon_w, y))
                    surface.blit(icon_surf, icon_rect)

                    rect.x += icon_w

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


        for spell in self.game.spell_slots.values():
            if spell.name.lower() == spell_name.lower():
                
                if not spell.can_cast(self.player):
                    return False
                success = spell.cast(self.player, self.current_monster, self)
                if success:
                    now = time.time()
                    self.last_player_attack = now
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
            step = p["speed"] * dt
            if dist > 0:
                p["x"] += dx / dist * step
                p["y"] += dy / dist * step

        self.projectiles = [p for p in self.projectiles if not p["done"]]

    def add_burn_effect(self, target, damage, interval, duration):
        if not hasattr(target, "active_effects"):
            target.active_effects = []
        
        target.active_effects.append({
            "name": "Burn",
            "color": (255, 80, 0),
            "expires_at": time.time() + duration,
            "duration": duration,
            "start": time.time(),
            "description": f"Burns for {damage} fire damage every {interval}s.",
            "icon": "burn"
        })
        
        self.active_burns.append({
            "target": target,
            "damage": damage,
            "interval": interval,
            "duration": duration,
            "elapsed": 0,
            "start": time.time(),
            "tick_timer": 0,
        })

    def update_burns(self, dt):
        current_time = time.time()
        

        for burn in self.active_burns[:]:
            target = burn["target"]

            if not target.is_alive():
                print(f"🔥 Burn on {target.name} ended (target defeated).")
                self.active_burns.remove(burn)
                continue
                  
            if current_time >= burn["start"] + burn["duration"]:
                self.active_burns.remove(burn)
                continue

            next_tick_time = burn.get("next_tick_time")

            if next_tick_time is None:
                burn["next_tick_time"] = burn["start"] + burn["interval"]
                continue

            if current_time >= burn["next_tick_time"]:
                burn["next_tick_time"] += burn["interval"]
                
                target.stats.hp = max(0, target.stats.hp - burn["damage"])
                
                log_message = f"{burn['target'].name} takes {burn['damage']} burn damage!"
                
                if hasattr(self, "combat_log"):
                    self.add_log(log_message)

                self.add_floating_text(
                    f"{burn['damage']}",
                    0, 0,
                    text_type = "burn",
                    target = "enemy"
                )
            
            if current_time >= burn["start"] + burn["duration"]:
                self.active_burns.remove(burn)
                continue

    def spawn_heal_effect(self, target, amount):
        #creates a burst of particles for the heal spell
        if target == "player":
            base_x = self.player.game.player_draw_x + 75
            base_y = self.player.game.player_draw_y + 60
        else:
            base_x = self.game.enemy_sprite_rect.centerx
            base_y = self.game.enemy_sprite_rect.centery

        for _ in range(80):
            p = {
                "x": base_x + random.randint(-10, 10),
                "y": base_y + random.randint(-5, 5),
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(-1.5, -0.3),
                "size": random.randint(4, 7),
                "alpha": 255,
                "color": (0, random.randint(200, 255), random.randint(120, 255)),  # green/teal
                "gravity": 0.03,
            }
            self.heal_spell_particles.append(p)

    def update_heal_spell_particles(self, dt):
        for p in list(self.heal_spell_particles):
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += p["gravity"]

            p["alpha"] -= 3
            if p["alpha"] <= 0:
                self.heal_spell_particles.remove(p)
                continue

    def draw_heal_spell_particles(self, surface):
        for p in self.heal_spell_particles:
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], max(0, p["alpha"])))
            surface.blit(s, (p["x"], p["y"]))

    def spawn_battlecry_wave(self):
            # Get player sprite world position
            sprite = self.game.player.sprite
            sprite_x = self.game.player_draw_x + 85 + (200 - sprite.get_width()) // 2
            sprite_y = 300 + (180 - sprite.get_height()) // 2

            base_x = sprite_x + sprite.get_width() // 2 - 115
            base_y = sprite_y + sprite.get_height()

            
            # Spawn multiple waves with horizontal offsets
            for i in range(12):
                self.battlecry_waves.append({
                    "x": base_x + random.randint(-40, 40),     # horizontal spread
                    "y": base_y,
                    "height": 0,
                    "max_height": random.randint(40, 100),
                    "speed": random.uniform(2.5, 3.2),         # vertical animation speed
                    "lifetime": random.uniform(0.35, 0.55),
                    "age": 0,
                    "thickness": random.randint(3, 6),         # easier to see
                    "color": (255, random.randint(80, 120), 80)
                })
    
    def update_battlecry_waves(self, dt):
        for wave in list(self.battlecry_waves):
            wave["age"] += dt
            t = wave["age"] / wave["lifetime"]

            if t >= 1:
                self.battlecry_waves.remove(wave)
                continue

            # Rising then falling animation curve
            if t < 0.5:
                wave["height"] = wave["max_height"] * (t / 0.5)
            else:
                wave["height"] = wave["max_height"] * (1 - (t - 0.5) / 0.5)

            # Slight horizontal drift (makes them visible)
            wave["x"] += random.uniform(-0.7, 0.7)
    
    def draw_battlecry_waves(self, surface):
                for wave in self.battlecry_waves:
                    x = int(wave["x"])
                    base_y = int(wave["y"])
                    h = int(wave["height"])

                    pygame.draw.line(
                        surface,
                        wave["color"],
                        (x, base_y),
                        (x, base_y - h),
                        wave["thickness"]
                    )

    def add_log(self, message):
        self.combat_log.append(message)

        if len(self.combat_log) > 50:
            self.combat_log.pop(0)

        if not self.user_is_scrolling:
            self.force_scroll_to_bottom = True

    def _update_effects(self, entity, current_time):
        if not hasattr(entity, "active_effects"):
            return
        
        entity.active_effects = [
            eff for eff in entity.active_effects
            if eff["expires_at"] > current_time
        ]
