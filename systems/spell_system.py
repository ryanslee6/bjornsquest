import pygame
import random
import time
import os

class Spell:
    def __init__(self, name, mana_cost, power, element = "neutral", target = "enemy", cooldown = 0, icon_filename = None):
        self.name = name
        self.mana_cost = mana_cost
        self.power = power
        self.element = element
        self.target = target
        self.cooldown = cooldown
        self.last_cast_time = 0.0

        #icon support
        self.icon_filename = icon_filename
        self.icon = None

        if icon_filename:
            self.load_icon()

    #load spell icon from assets/images
    def load_icon(self):
        if not self.icon_filename:
            return
        
        try:
            if not self.icon_filename.endswith('.png'):
                icon_path = os.path.join("assets", "images", f"{self.icon_filename}.png")
            else:
                icon_path = os.path.join("assets", "images", self.icon_filename)
            
            if os.path.exists(icon_path):
                self.icon = pygame.image.load(icon_path).convert_alpha()
                print(f"[SPELL] Loaded icon for {self.name}: {icon_path}")
            else:
                print(f"[SPELL] Icon not found for {self.name}: {icon_path}")
        except Exception as e:
            print(f"[SPELL] Error loading icon for {self.name}: {e}")

    def can_cast(self, caster):
        now = time.time()
        if now - self.last_cast_time < self.cooldown:
            remaining = round(self.cooldown - (now - self.last_cast_time), 1)
            print(f"{self.name} is on cooldown ({remaining}s left).")
            return False
        return caster.stats.mp >= self.mana_cost
    
    def cast(self, caster, target, combat):
        #override in subclasses
        raise NotImplementedError
    
    def get_cooldown_remaining(self):
        elapsed = time.time() - self.last_cast_time
        remaining = max(0, self.cooldown - elapsed)
        #print(f"[COOLDOWN DEBUG] {self.name}: cooldown={self.cooldown}, elapsed={elapsed}, remaining={remaining}")
        return remaining
    
    def is_on_cooldown(self):
        return self.get_cooldown_remaining() > 0


class Fireball(Spell):
    def __init__(self):
        super().__init__("Fireball", mana_cost = 50, power = 25, element = "fire", target = "enemey", cooldown = 5.0, icon_filename = "fireball_icon")

    def cast(self, caster, target, combat):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False
        
        caster.stats.mp -= self.mana_cost

        dmg = int(self.power + caster.stats.intelligence * 1.5)
        dmg = max(1, dmg - target.stats.armor)
        target.stats.hp = max(0, target.stats.hp - dmg)

        log_message = f"{caster.name} casts {self.name} for {dmg} damage!"
        
        if hasattr(combat, "combat_log"):
            combat.add_log(log_message)

        burn_duration = 5.1
        burn_interval = 1.0
        burn_damage = 10

        combat.add_burn_effect(target, burn_damage, burn_interval, burn_duration)


        combat.add_floating_text(
            f"{dmg}",
            0, 0,
            text_type = "spell",
            target = "enemy"
        )
        
        if not hasattr(combat, "fireball1.png"):
            raw = pygame.image.load("assets/images/fireball1.png").convert_alpha()
            combat.fireball_image = pygame.transform.scale(raw, (75, 75))

        x_offset_start = 100
        y_offset_start = 100
        x_offset_target = 60
        y_offset_target = 30

        start_x = caster.game.player_draw_x + x_offset_start
        start_y = caster.game.player_draw_y + y_offset_start

        if hasattr(caster.game, "enemy_sprite_rect"):
            rect = caster.game.enemy_sprite_rect
            target_x = rect.centerx
            target_y = rect.centery
        else:
            target_x = 650
            target_y = 300

        #target_x = 650 + x_offset_target
        #target_y = 300 + y_offset_target

        #start_x = caster.game.player_draw_x + 80
        #start_y = caster.game.player_draw_y + 50
        #target_x = 650
        #target_y = 300

        combat.spawn_projectile(
            combat.fireball_image,
            start_x, start_y,
            target_x, target_y,
            speed = 700,
            damage = self.power,
            text_type = "damage"
        ) 
        
        combat.enemy_hit_flash_timer = pygame.time.get_ticks() + int(combat.player_attack_anim_duration * 0.4)

        self.last_cast_time = time.time()

        return True
    
    

class Heal(Spell):
    def __init__(self):
        super().__init__(
            name = "Heal",
            mana_cost = 45,
            cooldown = 5.0,
            power = 25
            #description = "Restores a small amount of health."
        )

    def cast(self, caster, target = None, combat = None):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False

        caster.stats.mp -= self.mana_cost
        heal_amount = 10
        caster.stats.hp = min(caster.stats.hp + heal_amount, caster.stats.max_hp)
        
        log_message = f"{caster.name} casts {self.name} and heals for {heal_amount} HP!"
        
        if hasattr(combat, "combat_log"):
            combat.add_log(log_message)
        
        combat.add_floating_text(
            f"{heal_amount}",
            0, 0,
            text_type = "heal",
            target = "player"
        )
        
        #if hasattr(combat, "spawn_heal_spell_particles"):
        #    combat.spawn_heal_spell_particles(
        #        caster.game.player_draw_x + 40,
        #        caster.game.player_draw_y - 20
        #    )

        combat.spawn_heal_effect("player", heal_amount)

        self.last_cast_time = time.time()
        return True

class BattleCry(Spell):
    def __init__(self):
        super().__init__(
            "Battle Cry",
            mana_cost = 40,
            power = 0,
            element = "physical",
            target = "self",
            cooldown = 20.0
        )

        self.buff_duration = 10.0
        self.str_buff = 5
    def cast(self, caster, target, combat):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False

        caster.stats.mp -= self.mana_cost

        combat.spawn_battlecry_wave()

        caster.stats.strength = int(caster.stats.strength + self.str_buff)
        if not hasattr(caster, "active_buffs"):
            caster.active_effects = []
        caster.active_effects.append({
            "name": self.name,
            "color": (100, 150, 255),
            "description": f"Increase strength by {self.str_buff} for {self.buff_duration}s.",
            "duration": self.buff_duration,
            "start": time.time(),
            "expires": time.time() + self.buff_duration,
            "revert": lambda c: setattr(c.stats, "strength", int(c.stats.strength - self.str_buff))
        })

        log_message = f"{caster.name} uses {self.name}! Strength increased by {self.str_buff} for {int(self.buff_duration)}s."
        
        if hasattr(combat, "combat_log"):
            combat.add_log(log_message)

        combat.add_floating_text(
            "Battle Cry!",
            0, 0,
            text_type = "buff",
            target = "player"
        )

        self.last_cast_time = time.time()
        return True

class LightningBolt(Spell):
    def __init__(self):
        super().__init__(
            name = "Lightning Bolt",
            mana_cost = 50,
            power = 30,
            element = "earth",
            target = "enemy",
            cooldown = 8.0,
            icon_filename = "lightningbolt_icon"
        )

        self.stun_duration = 3.0

    def cast(self, caster, target, combat):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False
        
        caster.stats.mp -= self.mana_cost

        dmg = int(self.power + caster.stats.intelligence)
        dmg = max(1, dmg - target.stats.armor)
        target.stats.hp = max(0, target.stats.hp - dmg)

        log_message = f"{caster.name} casts {self.name} for {dmg} damage and stuns the enemy!"
        
        if hasattr(combat, "combat_log"):
            combat.add_log(log_message)

        combat.add_floating_text(
            f"{dmg}",
            0, 0,
            text_type = "spell",
            target = "enemy"
        )

        if not hasattr(target, "active_effects"):
            target.active_effects = []

        target.active_effects.append({
            "name": "Stun",
            "color": (200, 200, 50),
            "start": time.time(),
            "duration": self.stun_duration,
            "expires": time.time() + self.stun_duration,
            "type": "stun",
            "description": f"Stun the enemy for {self.stun_duration:.1f}s."
        })

        if not hasattr(target, "is_stunned"):
            target.is_stunned = False

        target.is_stunned = True
        target.stun_expires_at = time.time() + self.stun_duration

        self.last_cast_time = time.time()

        return True
    
#creates an absorption shield on the player that blocks incoming damage
class Barrier(Spell):
    def __init__(self):
        super().__init__(
            name = "Barrier",
            mana_cost = 60,
            power = 50, #shield amount
            element = "arcane",
            target = "self",
            cooldown = 15.0
        )
        self.shield_duration = 10.0

    def cast(self, caster, target, combat):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False
        
        #consume mana
        caster.stats.mp -= self.mana_cost

        #calculate shield amount (scales with intelligence)
        shield_amount = int(self.power + caster.stats.intelligence * 2)

        #apply shield to player
        caster.current_shield = shield_amount
        caster.max_shield = shield_amount

        #add visual effect to active_effects for UI display
        if not hasattr(caster, "active_effects"):
            caster.active_effects = []

        caster.active_effects.append({
            "name": self.name,
            "raw_key": "barrier",
            "color": (100, 150, 255),
            "description": f"Absorbs {shield_amount} damage.",
            "duration": self.shield_duration,
            "start": time.time(),
            "expires": time.time() + self.shield_duration,
            "expires_at": time.time() + self.shield_duration,
            "mods": {},
            "revert": lambda c: setattr(c, "current_shield", 0)
        })

        #combat log
        log_message = f"{caster.name} casts {self.name}! Gained a {shield_amount} HP shield for {int(self.shield_duration)}s."
        if hasattr(combat, "combat_log"):
            combat.add_log(log_message)

        #floating text
        combat.add_floating_text(
            f"Shield +{shield_amount}",
            0, 0,
            text_type = "buff",
            target = "player"
        )

        self.last_cast_time = time.time()
        return True
    
#poisons the enemy, dealing damage over time
class PoisonStrike(Spell):
    def __init__(self):
        super().__init__(
            name = "Poison Strike",
            mana_cost = 40,
            power = 15, #initial hit damage
            element = "nature",
            target = "enemy",
            cooldown = 8.0
        )
        self.poison_duration = 10.0
        self.poison_tick_damage = 8
        self.poison_tick_interval = 1.0

    def cast(self, caster, target, combat):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False
        
        #consume mana
        caster.stats.mp -= self.mana_cost

        #initial hit damage
        initial_dmg = int(self.power + caster.stats.intelligence * 0.5)
        initial_dmg = max(1, initial_dmg - target.stats.armor)
        target.stats.hp = max(0, target.stats.hp - initial_dmg)

        #apply poison dot effect using combat systems poison logic
        reduced_damage = int(self.poison_tick_damage * 0.3)

        combat.add_poison_effect(
            target,
            damage = self.poison_tick_damage,
            reduced_damage = reduced_damage,
            interval = self.poison_tick_interval,
            duration = self.poison_duration
        )

        #combat log
        log_message = f"{caster.name} casts {self.name} for {initial_dmg} damage and poisons the enemy!"
        if hasattr(combat, "combat_log"):
            combat.add_log(log_message)

        #floating text for initial damage
        combat.add_floating_text(
            f"{initial_dmg}",
            0, 0,
            text_type = "spell",
            target = "enemy"
        )

        #add projectile effect (fireball image for now, replace later)
        if hasattr(combat, "fireball_image"):
            x_offset_start = 100
            y_offset_start = 100

            start_x = caster.game.player_draw_x + x_offset_start
            start_y = caster.game.player_draw_y + y_offset_start

            if hasattr(caster.game, "enemy_sprite_rect"):
                rect = caster.game.enemy_sprite_rect
                target_x = rect.centerx
                target_y = rect.centery
            else:
                target_x = 650
                target_y = 300

            combat.spawn_projectile(
                combat.fireball_image,
                start_x, start_y,
                target_x, target_y,
                speed = 600,
                damage = self.power,
                text_type = "spell"
            )

            combat.enemy_hit_flash_timer = pygame.time.get_ticks() + int(combat.player_attack_anim_duration * 0.4)

        self.last_cast_time = time.time()
        return True
    
#Deals ice damage and slows the enemies attack speed
class Frostbolt(Spell):
    def __init__(self):
        super().__init__(
            name = "Frostbolt",
            mana_cost = 55,
            power = 35,
            element = "ice",
            target = "enemy",
            cooldown = 6.0,
            icon_filename = "frostbolt_icon"
        )
        self.slow_duration = 6.0
        self.slow_amount = 0.30 #30% attack speed reduction (increases delay)

    def cast(self, caster, target, combat):
        if not self.can_cast(caster):
            print(f"{caster.name} tried to cast {self.name}, but didn't have enough MP!")
            return False
        
        #consume mana
        caster.stats.mp -= self.mana_cost

        #calculate damage
        dmg = int(self.power + caster.stats.intelligence * 1.2)
        dmg = max(1, dmg - target.stats.armor)
        target.stats.hp = max(0, target.stats.hp - dmg)

        #apply slow debuff to enemy
        if not hasattr(target, "active_effects"):
            target.active_effects = []

            #build slow effect using the mods system
            target.active_effects.append({
                "name": "Frostbolt Slow",
                "raw_key": "frostbolt_slow",
                "color": (100, 200, 255),
                "description": f"-{int(self.slow_amount * 100)}% Attack Speed",
                "duration": self.slow_duration,
                "start": time.time(),
                "expires": time.time() + self.slow_duration,
                "expires_at": time.time() + self.slow_duration,
                "tooltip": [f"-{int(self.slow_amount * 100)}% Attack Speed"],
                "mods": {
                    "attack_speed_pct": self.slow_amount
                }
            })

            #combat log
            log_message = f"{caster.name} casts {self.name} for {dmg} damage and slows the enemy!"
            if hasattr(combat, "combat_log"):
                combat.add_log(log_message)

            #floating text for damage
            combat.add_floating_text(
                f"{dmg}",
                0, 0,
                text_type = "spell",
                target = "enemy"
            )

            #floating text for slow effect
            combat.add_floating_text(
                "Slowed!",
                0, 0,
                text_type = "debuff",
                target = "enemy"
            )

            #projectile effect (use fireball for now, replace later)
            if hasattr(combat, "fireball_image"):
                x_offset_start = 100
                y_offset_start = 100

                start_x = caster.game.player_draw_x + x_offset_start
                start_y = caster.game.player_draw_y + y_offset_start

                if hasattr(caster.game, "enemy_sprite_rect"):
                    rect = caster.game.enemy_sprite_rect
                    target_x = rect.centerx
                    target_y = rect.centery
                else:
                    target_x = 650
                    target_y = 300

                combat.spawn_projectile(
                    combat.fireball_image,
                    start_x, start_y,
                    target_x, target_y,
                    speed = 750,
                    damage = self.power,
                    text_type = "spell"
                )

                combat.enemy_hit_flash_timer = pygame.time.get_ticks() + int(combat.player_attack_anim_duration * 0.4)

            self.last_cast_time = time.time()
            return True

def get_default_spellbook():
    return [Fireball(), 
            Frostbolt(), 
            LightningBolt(), 
            PoisonStrike(), 
            Heal(), 
            BattleCry(), 
            Barrier()]