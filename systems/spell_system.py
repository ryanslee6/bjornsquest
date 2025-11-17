import pygame
import random
import time

class Spell:
    def __init__(self, name, mana_cost, power, element = "neutral", target = "enemy", cooldown = 0):
        self.name = name
        self.mana_cost = mana_cost
        self.power = power
        self.element = element
        self.target = target
        self.cooldown = cooldown
        self.last_cast_time = 0.0

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
        super().__init__("Fireball", mana_cost = 50, power = 25, element = "fire", target = "enemey", cooldown = 5.0)

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
            cooldown = 8.0
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

def get_default_spellbook():
    return [Fireball(), Heal(), BattleCry(), LightningBolt()]