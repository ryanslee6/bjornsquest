import pygame
import os
import time

class Item:
    def __init__(self, item_id, data, sprite = None, rolled_stats = None):
        self.id = item_id
        self.name = data.get("name", item_id)
        
        #Generic item fields
        self.type = data.get("type", "misc")
        self.description = data.get("description", "")
        self.rarity = data.get("rarity", "common")
        self.stackable = data.get("stackable", True)
        self.subtype = data.get("subtype", None)
        
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

        #enhancement tracking
        self.enhancements = []
        self.used_slots = 0

        #enhancement scroll fields
        self.target_type = data.get("target_type", None) #weapon, armor, accessories
        self.success_chance = data.get("success_chance", 0)
        self.stat_to_enhance = data.get("stat", None)
        self.stat_bonus = data.get("stat_bonus", 0)
        self.is_safe_scroll = data.get("safe", True)

        #rolled stats (actual values for this specific item)
        if rolled_stats:
            self.rolled_armor = rolled_stats.get("armor", None)
            self.rolled_stats = rolled_stats.get("bonus_stats", {})
        else:
            self.rolled_armor = None
            self.rolled_stats = {}
        
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

        #Weapon stats
        if self.type == "Weapon":
            #base damage
            base_damage = f"{self.min_dmg}-{self.max_dmg}"
            lines.append(f"Damage: {base_damage}")

            #attack speed
            lines.append(f"Attack Speed: {self.attack_speed:.1f}s")

            #weapon type
            if hasattr(self, 'weapon_type') and self.weapon_type:
                lines.append(f"Weapon Type: {self.weapon_type}")

            #hands required
            if hasattr(self, 'hands'):
                hands_text = "Two-Handed" if self.hands == 2 else "One-Handed"
                lines.append(hands_text)

        #Armor stats
        if self.type == "Armor":
            #show rolled armor value if it exists
            if hasattr(self, 'rolled_armor') and self.rolled_armor is not None:
                lines.append(f"Armor: {self.rolled_armor}")
            elif hasattr(self, 'armor_min') and self.armor_max > 0:
                lines.append(f"Armor: {self.armor_min}-{self.armor_max}")

            #armor type
            if hasattr(self, 'armor_type') and self.armor_type:
                lines.append(f"Armor Type: {self.armor_type}")


        #show level requirement (will be colored in rendering)
        if hasattr(self, 'required_level') and self.required_level > 1:
            lines.append(f"Level Required: {self.required_level}")

        #show bonus stats if they exist
        if hasattr(self, 'rolled_stats') and self.rolled_stats:
            for stat, value in self.rolled_stats.items():
                stat_display = stat.replace("_", " ").title()
                if value > 0:
                    lines.append(f"ROLLED:+{value} {stat_display}")

        #enhancements
        if hasattr(self, 'enhancements') and self.enhancements:
            for enhancement in self.enhancements:
                stat = enhancement["stat"].replace("_", " ").title()
                value = enhancement["value"]
                lines.append(f"ENHANCED:+{value} {stat}")

        #enhancement slots remaining
        if hasattr(self, 'enhancement_slots') and self.enhancement_slots > 0:
            remaining = self.enhancement_slots - (self.used_slots if hasattr(self, 'used_slots') else 0)
            if remaining > 0:
                lines.append(f"SLOTS:{remaining}/{self.enhancement_slots}")
            else:
                lines.append(f"SLOTS:0/{self.enhancement_slots}")

        if self.description:
            lines.append(self.description)
        return lines

class ConsumableItem(Item):
    def __init__(self, item_id, data):
        super().__init__(item_id, data)
        self.heal_amount = data.get("heal_amount", 0)
        self.mana_amount = data.get("mana_amount", 0)

        self.duration = data.get("duration", 0)
        self.flags = data.get("flags", {})

        self.icon_name = data.get("icon", "")

        #load icon image for consumables
        self.icon_surface = None
        self.scaled_icon = None
        if self.icon_name:
            try:
                path = os.path.join("assets", "images", self.icon_name)
                self.icon_surface = pygame.image.load(path).convert_alpha()
                #pre-scale for floating text
                self.scaled_icon = pygame.transform.scale(self.icon_surface, (20, 20))
            except Exception as e:
                print(f"[WARNING] Failed to load icon '{self.icon_name}' for item '{self.id}': {e}")

    def use(self, player):
        #heal player

        #start = time.perf_counter()

        if self.heal_amount > 0:

            #t1 = time.perf_counter()

            player.stats.hp = min(player.stats.max_hp, player.stats.hp + self.heal_amount)
            
            #print(f"[PERF] HP update: {(time.perf_counter() - t1) * 1000:.2f}ms")
            
            print(f"{player.name} healed for {self.heal_amount} HP!")

            if hasattr(player.game, "player_draw_x"):
                px = player.game.player_draw_x + player.sprite.get_width() // 2
                py = player.game.player_draw_y + player.sprite.get_height() // 2 + 55
            else:    
                px = 200
                py = 240
            
            player.game.combat.spawn_heal_particles(px, py)

            icon_surface = self.scaled_icon
            #if hasattr(self, "icon") and self.icon:
            #    icon_surface = pygame.transform.scale(self.icon, (20, 20))

            #t2 = time.perf_counter()
            player.game.combat.add_floating_text(
                f"+{self.heal_amount} HP",
                0, 0,
                target= "player",
                text_type = "heal",
                icon = icon_surface
            )
            #print(f"[PERF] add_floating_text: {(time.perf_counter() - t2) * 1000:.2f}ms")

        if self.mana_amount > 0:
            player.stats.mp = min(player.stats.max_mp, player.stats.mp + self.mana_amount)
            print(f"{player.name} restored {self.mana_amount} MP!")

            player.game.combat.add_floating_text(
                f"+{self.mana_amount} MP",
                0, 0,
                target = "player",
                text_type = "mana"
            )

        # ------------------------------------------------
        # 3) Apply duration-based effects (buffs/debuffs)
        # ------------------------------------------------
        duration = getattr(self, "duration", 0)
        flags = getattr(self, "flags", {})

        #If this consumable has a duration or flags, treat it as a status effect
        if duration > 0 or flags:
            now = time.time()
            new_exp = now + duration

            # ------------------------------------------
            # A) Check if this effect already exists
            # ------------------------------------------
            for eff in player.active_effects:
                if eff.get("raw_key") == self.id:
                    #Refresh duraiton
                    eff["expires"] = new_exp
                    eff["expires_at"] = new_exp
                    eff["start"] = now

                    print("[EFFECT] Anti-poison resfreshed")

                    #keep poison protection active:
                    if flags.get("poison_protection"):
                        player.is_poison_protected = True

                    return
                

            # ------------------------------------------------
            # B) Otherwise create a NEW effect entry
            # ------------------------------------------------
            effect_entry = {
                "name": self.name,
                "raw_key": self.id,
                "expires": new_exp,
                "expires_at": new_exp,
                "duration": duration,
                "start": now,
                "icon_surface": self.icon_surface,
                "icon": None,
                "description": self.description,
                "flags": flags,
                "color": (80, 200, 80)
            }

            #add to players active effects list
            player.active_effects.append(effect_entry)

            #apply any immediate flags (like poison protection)
            if flags.get("poison_protection"):
                player.is_poison_protected = True
                print("[EFFECT] Anti-poison protection applied")

                #print("[DEBUG EFFECT ENTRY]", effect_entry)

        #total = (time.perf_counter() - start) * 1000
        #print(f"[PERF] TOTAL use() time: {total:.2f}ms")

    def tooltip_text(self):
        base = super().tooltip_text()
        base.insert(2, f"Heals: {self.heal_amount} HP")
        return base
