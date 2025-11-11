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
        print(log_message)
        if hasattr(combat, "combat_log"):
            combat.combat_log.append(log_message)

        burn_duration = 5.0
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
    

def get_default_spellbook():
    return [Fireball()]