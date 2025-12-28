import pygame
import os
import time
from settings import *

class Item:
    def __init__(self, item_id, data, sprite = None, rolled_stats = None):
        self.id = item_id
        self.name = data.get("name", item_id)
        self.name_font = None

        
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
        #self.enhancement_level = 0

        #enhancement scroll fields
        self.target_type = data.get("target_type", None) #weapon, armor, accessories
        self.success_chance = data.get("success_chance", 0)
        self.stat_to_enhance = data.get("stat", None)
        self.stat_bonus = data.get("stat_bonus", 0)
        self.is_safe_scroll = data.get("safe", True)

        #tools
        self.tool_type = data.get("tool_type", None)
        self.gathering_power = data.get("gathering_power", 0)
        self.mining_speed_bonus = data.get("mining_speed_bonus", 0.0)
        self.woodcutting_speed_bonus = data.get("woodcutting_speed_bonus", 0.0)

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
            self.icon = pygame.image.load(path).convert_alpha()
        else:
            self.icon = None

        self.name_surface = None

    def get_enhancement_bonus(self, stat_key):
        if not self.enhancements:
            return 0
        return sum(e["value"] for e in self.enhancements if e["stat"] == stat_key)

    def get_display_name(self):
        level = len(self.enhancements) if hasattr(self, "enhancements") else 0
        if level > 0:
            return f"{self.name} +{level}"
        return self.name
    
    def rebuild_name_surface(self, font):
        display_name = self.get_display_name()
        rarity_color = RARITY_COLORS.get(self.rarity, (255, 255, 255))
        self.name_surface = font.render(display_name, True, rarity_color)

    def use(self, player):
        #override in child classes
        print(f"{self.name} has no effect.")

    def get_total_stat(self, stat):
        base = 0

        #base stats
        if stat == "min_dmg":
            base = self.min_dmg
        elif stat == "max_dmg":
            base = self.max_dmg
        elif stat == "armor":
            base = self.rolled_armor if self.rolled_armor is not None else 0
        elif hasattr(self, stat):
            base = getattr(self, stat, 0)

        #rolled bonsues 
        base += self.rolled_stats.get(stat, 0)

        #enhancement bonuses
        base += self.get_enhancement_bonus(stat)

        #attack enhances both min and max damage
        if stat in ("min_dmg", "max_dmg"):
            base += self.get_enhancement_bonus("attack")


        return base       

    def tooltip_text(self):
        lines = [
            f"{self.get_display_name()}"
        ]

        #Weapon stats
        if self.type == "Weapon":
            #hands required + weapon type
            if hasattr(self, 'hands'):
                hands_text = "Two-Handed" if self.hands == 2 else "One-Handed"
                weapon_type = self.weapon_type.title() if self.weapon_type else "Weapon"
                lines.append(f"{hands_text} {weapon_type}")
            
            #weapon damage
            min_dmg = self.get_total_stat("min_dmg")
            max_dmg = self.get_total_stat("max_dmg")

            attack_bonus = self.get_enhancement_bonus("attack")

            if attack_bonus > 0:
                lines.append({
                    "text": f"Damage: {min_dmg}-{max_dmg} (+{attack_bonus})",
                    "color": "enhanced"
                })
            else:
                lines.append({
                    "text": f"Damage: {min_dmg}-{max_dmg}",
                    "color": "normal"
                })

            #attack speed
            lines.append(f"Attack Speed: {self.attack_speed:.1f}s")

        #Armor stats
        if self.type == "Armor":
            
            #armor type
            if hasattr(self, 'armor_type') and self.armor_type:
                lines.append(f"{self.armor_type}")

            #armor value
            base_armor = self.rolled_armor if self.rolled_armor is not None else 0
            bonus_armor = self.get_enhancement_bonus("armor")
            total_armor = base_armor + bonus_armor

            if bonus_armor > 0:
                lines.append({
                    "text": f"Armor: {total_armor} (+{bonus_armor})",
                    "color": "enhanced"
                })
            else:
                lines.append({
                    "text": f"Armor: {total_armor}",
                    "color": "normal"
                })           

        #show level requirement (will be colored in rendering)
        if hasattr(self, 'required_level') and self.required_level >= 1:
            lines.append(f"Level Required: {self.required_level}")

        # --------------------------------------------------
        # ROLLED + ENHANCED STATS (unified display)
        # --------------------------------------------------
        all_stats = set()

        #rolled stats
        if hasattr(self, "rolled_stats"):
            all_stats.update(self.rolled_stats.keys())

        #enhancement-only stats
        if hasattr(self, "enhancements") and self.enhancements:
            all_stats.update(e["stat"] for e in self.enhancements)

        for stat in sorted(all_stats):
            #attack is applied to damage, never show as stat line
            if stat in ("attack", "armor"):
                continue

            base = self.rolled_stats.get(stat, 0) if hasattr(self, "rolled_stats") else 0
            bonus = self.get_enhancement_bonus(stat)
            total = base + bonus

            if total <= 0:
                continue

            stat_name = stat.replace("_", " ").title()

            if bonus > 0:
                lines.append({
                    "text": f"{stat_name}: {total} (+{bonus})",
                    "color": "enhanced"
                })
            else:
                lines.append(f"{stat_name}: {total}")     

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
