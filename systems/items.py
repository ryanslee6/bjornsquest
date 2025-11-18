import pygame
import os

class Item:
    def __init__(self, item_id, data, sprite = None):
        self.id = item_id
        self.name = data.get("name", item_id)
        
        #Generic item fields
        self.type = data.get("type", "misc")
        self.description = data.get("description", "")
        self.rarity = data.get("rarity", "common")
        self.stackable = data.get("stackable", True)
        
        #--Equipment Fields--
        #Armor
        self.armor_type = data.get("armor_type", None)
        self.armor_min = data.get("armor_min", 0)
        self.armor_max = data.get("armor_max", 0)

        #Weapon
        self.weapon_type = data.get("weapon_type", None)
        self.min_dmg = data.get("min_dmg", 0)
        self.max_dmg = data.get("max_dmg", 0)
        self.hands = data.get("hands", 1)
        self.attack_speed = data.get("attack_speed", 1.8)

        #other equipment fields
        self.required_level = data.get("required_level", 1)
        self.enhancement_slots = data.get("enhancement_slots", 0)
        
        #Sprite / Icon handling        
        self.sprite = sprite
        if sprite:
            path = os.path.join("assets", "images", sprite)
            self.icon = pygame.image.load(path).convert._alpha()
        else:
            self.icon = None

    def use(self, player):
        #override in child classes
        print(f"{self.name} has no effect.")

    def tooltip_text(self):
        lines = [
            f"{self.name}",
            f"Type: {self.type.title()}",
        ]
        if self.description:
            lines.append(self.description)
        return lines

class ConsumableItem(Item):
    def __init__(self, item_id, data):
        super().__init__(item_id, data)
        self.heal_amount = data.get("heal_amount", 0)
        self.mana_amount = data.get("mana_amount", 0)

    def use(self, player):
        #heal player

        if self.heal_amount > 0:
            player.stats.hp = min(player.stats.max_hp, player.stats.hp + self.heal_amount)
            print(f"{player.name} healed for {self.heal_amount} HP!")

            if hasattr(player.game, "player_draw_x"):
                px = player.game.player_draw_x + player.sprite.get_width() // 2
                py = player.game.player_draw_y + player.sprite.get_height() // 2 + 55
            else:    
                px = 200
                py = 240
            
            player.game.combat.spawn_heal_particles(px, py)

            icon_surface = None
            if hasattr(self, "icon") and self.icon:
                icon_surface = pygame.transform.scale(self.icon, (20, 20))

            player.game.combat.add_floating_text(
                f"+{self.heal_amount} HP",
                0, 0,
                target= "player",
                text_type = "heal",
                icon = icon_surface
            )
        if self.mana_amount > 0:
            player.stats.mp = min(player.stats.max_mp, player.stats.mp + self.mana_amount)
            print(f"{player.name} restored {self.mana_amount} MP!")

            player.game.combat.add_floating_text(
                f"+{self.mana_amount} MP",
                0, 0,
                target = "player",
                text_type = "mana"
            )

    def tooltip_text(self):
        base = super().tooltip_text()
        base.insert(2, f"Heals: {self.heal_amount} HP")
        return base
