from entities.stats import Stats
from data.exp_table import exp_table
import pygame
import time
from settings import EQUIP_SLOTS, WEAPON_SLOT

class Player:
    def __init__(self, name = "Bjorn", item_manager = None, game = None, is_player = True):
        self.name = name
        self.game = game
        self.stats = Stats()
        self.level = 1
        self.exp = 0
        self.stat_points = 0
        self.inventory = []
        self.active_effects = []
        self.regen_timer = 0
        self.gold = 100
        self.auto_combat_unlocked = False
        self.is_poison_protected = False

        self.enhancement_scroll = None #currently selected scroll for enhancement

        #mining stats
        self.mining_level = 1
        self.mining_xp = 0
        self.gathering_power = 0
        self.mining_speed_bonus = 0.0
        self.auto_mining_unlocked = False

        #woodcutting stats
        self.woodcutting_level = 1
        self.woodcutting_xp = 0
        self.woodcutting_speed_bonus = 0.0
        self.auto_woodcutting_unlocked = False

        self.current_shield = 0
        self.max_shield = 0

        self.item_manager = item_manager

        self.equipment = {
            "head": None,
            "neck": None,
            "back": None,
            "chest": None,
            "legs": None,
            "feet": None,
            "weapon": None,
            "offhand": None,
            "ring1": None,
            "ring2": None
        }

        try:
            self.sprite = pygame.image.load("assets/images/bjorn1.png").convert_alpha()
        except:
            self.sprite = None
            print("⚠️ Player sprite missing — using placeholder.")

        if self.sprite:
            self.sprite = pygame.transform.scale(self.sprite, (180, 160))

        if item_manager is not None:
            self.recalculate_stats()
    
    def level_up(self):
        self.level += 1
        self.stat_points += 5

        self.stats.recalc_stats
        
        self.game.show_levelup_window = True

    def add_item(self, item_id, quantity = 1):

        #handle gold specially
        if item_id.lower() in ("gold", "gold_coins", "gold_coins", "coins"):
            self.gold += quantity
            print(f"[INVENTORY] +{quantity} Gold Coins (Total: {self.gold})")
            return
        
        #get base item to check if stackable
        base_item = self.item_manager.get(item_id)

        if base_item.stackable:
            #stackable items (potions, materials, etc) - use cached template, no rolling
            for entry in self.inventory:
                if "id" in entry and entry["id"] == item_id and entry.get("stackable", True):
                    entry["qty"] += quantity
                    break
            else:
                self.inventory.append({"id": item_id, "qty": quantity, "stackable": True})
            print(f"[INVENTORY] +{quantity} {base_item.name}")
        else:
            #non-stackable items (equipment) - roll stats for each one
            for _ in range(quantity):
                rolled_item = self.item_manager.create_item_with_rolls(item_id)

                if rolled_item:                
                    self.inventory.append({"item": rolled_item, "stackable": False})

                    #show rolled armor in log for now REMOVE LATER
                    if hasattr(rolled_item, 'rolled_armor') and rolled_item.rolled_armor:
                        print(f"[INVENTORY] +{rolled_item.name} ({rolled_item.rolled_armor} Armor)")
                    else:
                        print(f"[INVENTORY] +{rolled_item.name}")
        
        if self.game and hasattr(self.game, 'inventory_window'):
            self.game.inventory_window.mark_dirty()
        
    def use_item(self, item_id, item_manager):

        #first check if its a scroll
        item = item_manager.get(item_id)

        print(f"[DEBUG] use_item called for: {item_id}")
        print(f"[DEBUG] Item object: {item}")
        print(f"[DEBUG] Has subtype? {hasattr(item, 'subtype')}")
        if hasattr(item, 'subtype'):
            print(f"[DEBUG] Subtype value: {item.subtype}")

        #enhancement scrolls enter selection mode instead of immediate use
        if item and hasattr(item, 'subtype') and item.subtype == "enhancement_scroll":
            self.start_enhancement_mode(item)
            return #dont consume yet - wait for player to select target item
        
        print("[DEBUG] Not a scroll, proceeding with regular consumable logic")
        #regular consumable handling
        for entry in self.inventory:

            #ignore any malformed / non-item entries
            if "id" not in entry:
                continue
            
            if entry["id"] == item_id:
                item = item_manager.get(item_id)
                item.use(self)

                if item.stackable:
                    entry["qty"] -= 1
                    if entry["qty"] <= 0:
                        self.inventory.remove(entry)
                else:
                    self.inventory.remove(entry)
                return
        print(f"[ERROR] Tried to use {item_id}, but player doesn't have it!")

    def recalculate_stats(self):
        #reset stats back to base values
        self.stats.reset_to_base()

        #let Stats class compute hp/mp/regen
        self.stats.recalc_stats()

        #add gear bonuses
        self.apply_gear_stats()

        self.update_gathering_stats_from_tool()

    def equip_item(self, item):
        #attmpts to equip an item from inventory

        print(f"[DEBUG] Attempting to equip: {item.name}, type: '{item.type}'")

        #required level check
        req = getattr(item, "required_level", 1)
        if self.level < req:
            print(f"[EQUIP] Cannot equip {item.name}: requires level {req}.")
            return False
        
        #weapon equipping
        if item.type == "Weapon":
            slot = WEAPON_SLOT

            #clear offhand if 2h wep
            if item.hands == 2:
                if self.equipment.get("offhand"):
                    self.unequip_slot("offhand")

            #Equip weapon
            self.unequip_slot(slot)
            self.equipment[slot] = item
            self.remove_from_inventory(item)
            self.recalculate_stats()

            print(f"[EQUIP] Equipped weapon: {item.name}")
            return True

        #tool equipping
        if item.type == "Tool":
            slot = "weapon" #tools use weapon slot

            #check if tool requires mining level
            if hasattr(item, "required_level"):
                if self.mining_level < item.required_level:
                    print(f"[EQUIP] requires mining level {item.required_level}")
                    return False
                
            #equip tool
            self.unequip_slot(slot)
            self.equipment[slot] = item
            self.remove_from_inventory(item)
            self.recalculate_stats()
            print(f"[EQUIP] Equipped tool: {item.name}")
            return True

        #Armor equipping
        if item.type == "Armor":
            armor_type = item.armor_type

            #find matching equipment slot
            if armor_type == "Ring":
                #Choose first empty ring slot
                if self.equipment["ring1"] is None:
                    slot = "ring1"
                elif self.equipment["ring2"] is None:
                    slot = "ring2"
                else:
                    # Both full → replace ring1 for now (or pop-up later)
                    slot = "ring1"
            else:
                slot = EQUIP_SLOTS.get(armor_type)
            
            if not slot:
                print(f"[EQUIP] Unknown armor type {armor_type}")
                return False
            
            # --- Special case: attempting to equip a shield while a 2H weapon is equipped ---
            if slot == "offhand":
                weapon = self.equipment.get("weapon")
                if weapon and weapon.hands == 2:
                    print("[EQUIP] Equipping shield removes 2H weapon")
                    self.unequip_slot("weapon")

            #Equip armor
            self.unequip_slot(slot)
            self.equipment[slot] = item
            self.remove_from_inventory(item)
            self.recalculate_stats()

            print(f"[EQUIP] Equipped armor: {item.name}")
            return True
        
        print(f"[EQUIP] {item.name} cannot be equipped.")
        return False

    def unequip_slot(self, slot_name):
        #unequip whatever is in given slot
        equipped_item = self.equipment.get(slot_name)
        if equipped_item:
            #add the actual Item object back to inventory (preserves rolled stats)
            self.inventory.append({"item": equipped_item, "stackable": False})
            self.equipment[slot_name] = None
            print(f"[UNEQUIP] Removed item from {slot_name}.")
            self.recalculate_stats()

            #mark inventory dirty so it updates
            if hasattr(self, 'game') and hasattr(self.game, 'inventory_window'):
                self.game.inventory_window.mark_dirty()

    def remove_from_inventory(self, item):
        #remove a single insteance of an item from inventory list
        for entry in self.inventory:
            #handle equipment (stored as Item objects)
            if "item" in entry and entry["item"] is item:
                self.inventory.remove(entry)
                return
            #handle stackable items
            elif "id" in entry and entry["id"] == item.id:
                self.inventory.remove(entry)
                return
            
    def consume_stackable_item(self, item_id, amount = 1):
        for entry in self.inventory:
            if entry.get("id") == item_id:
                entry["qty"] -= amount
                if entry["qty"] <= 0:
                    self.inventory.remove(entry)
                return True
        return False
            
    def apply_gear_stats(self):
        #apply armor and weapon stats
        for slot, item in self.equipment.items():
            if not item:
                continue

            #armor
            if item.type == "Armor":
                #use rolled armor if it exists, otherwise fall back to armor_min
                if hasattr(item, 'rolled_armor') and item.rolled_armor is not None:
                    armor_value = item.rolled_armor
                else:
                    armor_value = item.armor_min
                
                self.stats.armor += armor_value

                #apply bonus stats from this armor piece
                if hasattr(item, 'rolled_stats') and item.rolled_stats:
                    for stat, value in item.rolled_stats.items():
                        self._apply_stat_bonus(stat, value)

                #apply enhancements from scrolls
                if hasattr(item, 'enhancements') and item.enhancements:
                    for enhancement in item.enhancements:
                        stat = enhancement["stat"]
                        value = enhancement["value"]
                        self._apply_stat_bonus(stat, value)
            
            #weapon
            if item.type == "Weapon":
                self.stats.min_damage = item.min_dmg
                self.stats.max_damage = item.max_dmg
                self.stats.attack_speed = item.attack_speed

                #apply bonus stats from rolling
                if hasattr(item, 'rolled_stats') and item.rolled_stats:
                    for stat, value in item.rolled_stats.items():
                        self._apply_stat_bonus(stat, value)

                #apply enhancements from scrolls
                if hasattr(item, 'enhancements') and item.enhancements:
                    for enhancement in item.enhancements:
                        stat = enhancement["stat"]
                        value = enhancement["value"]
                        self._apply_stat_bonus(stat, value)

    def _apply_stat_bonus(self, stat, value):
        #helper method to apply a stat bonus from equipment
        if stat == "strength":
            self.stats.strength += value
        elif stat == "dexterity":
            self.stats.dexterity += value
        elif stat == "constitution":
            self.stats.constitution += value
        elif stat == "intelligence":
            self.stats.intelligence += value
        elif stat == "max_hp":
            self.stats.max_hp += value
        elif stat == "max_mp":
            self.stats.max_mp += value
        elif stat == "attack":
            self.stats.min_damage += value
            self.stats.max_damage += value
        elif stat == "armor":
            self.stats.armor += value
        elif stat == "crit_chance":
            self.stats.base_crit_chance += value
        elif stat == "attack_speed":
            self.stats.attack_speed += value
                 

    def print_inventory(self):
        print("\n=== INVENTORY ===")
        if not self.inventory:
            print("Empty")
        else:
            for item, qty in self.inventory.items():
                print(f"{item}: {qty}")
        print("=================\n")

    def is_alive(self):
        return self.stats.hp > 0
    
    def take_damage(self, damage):
        #apply damage to player, checking shield first
        #returns: (actual_hp_damage, shield_damage, shield_broke)

        if damage <= 0:
            return 0, 0, False
        
        shield_broke = False
        shield_damage = 0
        hp_damage = 0

        #if player has shield, it absorbs damage first
        if self.current_shield > 0:
            if damage <= self.current_shield:
                #shield absorbs all damage
                shield_damage = damage
                self.current_shield -= damage
                hp_damage = 0
            else:
                #shield breaks, overflow goes to hp
                shield_damage = self.current_shield
                hp_damage = damage - self.current_shield
                self.current_shield = 0
                shield_broke = True
        else:
            #no shield, damage goes straigh tto hp
            hp_damage = damage

        #apply hp damage
        self.stats.hp = max(0, self.stats.hp - hp_damage)

        return hp_damage, shield_damage, shield_broke
    
    def attack(self, target):
        import random

        #miss check
        is_miss = random.random() > self.stats.hit_chance
        if is_miss:
            return 0, True, False, False

        #dodge check
        is_dodged = random.random() < target.stats.dodge_chance
        if is_dodged:
            return 0, False, False, True

        eff = self.stats.compute_effective_stats(self.active_effects)
        target_eff = target.stats.compute_effective_stats(target.active_effects)

        min_dmg = eff["min_damage"]
        max_dmg = eff["max_damage"]
        armor = target_eff["armor"]

        #base damage roll    
        min_dmg, max_dmg = self.stats.get_damage_range()
        base_damage = random.randint(min_dmg, max_dmg)
        
        #crit chance
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:    
            base_damage *= 2
        
        #armor reduction
        armor = target.stats.armor
        if armor > 0:
            damage_reduction = armor / (armor + 400)
            final_damage = int(base_damage * (1 - damage_reduction))
        else:
            final_damage = int(base_damage)

        final_damage = max(1, int(final_damage))

        #apply damage
        hp_dmg, shield_dmg, shield_broke = target.take_damage(final_damage)
        
        return final_damage, is_miss, is_crit, is_dodged
    
    def gain_exp(self, amount):
        self.exp += amount
        leveled_up = False
        
        while self.level < len(exp_table) and self.exp >= exp_table[self.level]:
            self.level += 1
            leveled_up = True

            self.stat_points += 5
            
            self.stats.hp = self.stats.max_hp
            self.stats.mp = self.stats.max_mp

            print(f"LEVEL UP! 🎉 Reached Level {self.level}")
            print(f"Unspent stat points: {self.stat_points}")
            print(f"HP/MP fully restored: {self.stats.hp}/{self.stats.max_hp} HP, {self.stats.mp}/{self.stats.max_mp} MP")
        
            if hasattr(self.game, "levelup_window"):
                self.game.levelup_window.visible = True

        if not leveled_up:
            print(f"{self.name} gained {amount} exp!")

    @property
    def exp_to_level(self):
        if self.level >= len(exp_table):
            return 0
        return exp_table[self.level]
    
    def exp_progress(self):
        #exp required up to previous level
        prev_required = exp_table[self.level - 1] if self.level > 1 else 0

        next_required = exp_table[self.level]

        exp_into_level = self.exp - prev_required

        exp_needed = next_required - prev_required

        return exp_into_level, exp_needed
    
    def get_total_gold(self):
        return self.gold
    
    def spend_gold(self, amount):
        if self.gold >= amount:
            self.gold -= amount
            print(f"[GOLD] Spent {amount}, new total - {self.gold}")
            return True
        else:
            print(f"[GOLD] Not enough gold! Have {self.gold}, need {amount}")
            return False

    def add_status_effect(self, name, duration, icon = None, color = (200, 200, 200)):
        if not hasattr(self, "active_effects"):
            self.active_effects = []

        self.active_effects.append({
            "name": name,
            "expires": time.time() + duration,
            "icon": icon,
            "color": color
        })

    def remove_expired_effects(self, game = None):
        now = time.time()
        new_list = []

        for effect in self.active_effects:
            if now < effect["expires"]:
                new_list.append(effect)
            else:
                if "revert" in effect:
                    effect["revert"](self)

                if effect.get("flags", {}).get("poison_protection"):
                    self.is_poison_protected = False
                    print("[EFFECT] Anti-poison protection expired.")

        self.active_effects = new_list

    def start_enhancement_mode(self, scroll):
        #enter scroll selection mode - player muyse select an item to enhance
        self.enhancement_scroll = scroll
        print(f"[ENHANCE] Selected scroll: {scroll.name}")
        print(f"[ENHANCE] Target type: {scroll.target_type}, Stat: {scroll.stat_to_enhance} +{scroll.stat_bonus}")
        
    def can_enhance_item(self, item, scroll):
        #check if an item can be enhanced with this scroll
        #must be equipment
        if item.type not in ("Weapon", "Armor", "Accessory"):
            return False, "This item cannot be enhanced."
        
        #must match scroll target type:
        if item.type != scroll.target_type:
            return False, f"This scroll can only be used on {scroll.target_type}s."
        
        #must have enhancement slots
        if item.enhancement_slots == 0:
            return False, "This item cannot be enhanced."
        
        #must have available slots
        if item.used_slots >= item.enhancement_slots:
            return False, "This item has no remaining enhancement slots."
        
        return True, ""
    
    def apply_enhancement(self, scroll, target_item):
        #attempt to enhance an item with a scroll
        import random

        #validate
        can_enhance, error_msg = self.can_enhance_item(target_item, scroll)
        if not can_enhance:
            print(f"[ENHANCE] Cannot enhance: {error_msg}")
            return {"success": False, "message": error_msg, "item_destroyed": False}
        
        #consume the scroll
        self.use_item(scroll.id, self.game.items)

        self.consume_stackable_item(scroll.id, 1)

        self.enhancement_scroll = None

        #roll for success
        roll = random.random()
        success = roll <= scroll.success_chance

        #increment used slots regardless of success
        target_item.used_slots += 1

        if success:
            #apply enhancement
            enhancement = {
                "stat": scroll.stat_to_enhance,
                "value": scroll.stat_bonus
            }
            target_item.enhancements.append(enhancement)

            target_item.rebuild_name_surface(self.game.font_small)

            print(f"[ENHANCE] SUCCESS! +{scroll.stat_bonus} {scroll.stat_to_enhance}")

            #recalculate stats if item is equipped
            if target_item in self.equipment.values():
                self.recalculate_stats()

            return {
                "success": True,
                "message": f"Success! +{scroll.stat_bonus} {scroll.stat_to_enhance.replace('_', ' ').title()}",
                "item_destroyed": False
            }
        else:
            #failed
            print(f"[ENHANCE] FAILED! Slots remaining: {target_item.enhancement_slots - target_item.used_slots}")

            #check for item destruction
            item_destroyed = False
            if not scroll.is_safe_scroll:
                #boom scroll has 50% chance to destroy item on failure
                boom_roll = random.random()
                if boom_roll < 0.5:
                    item_destroyed = True
                    #remove item from inventory
                    self.remove_from_inventory(target_item)
                    print(f"[ENHANCE] BOOM! Item destroyed!")

            slots_left = target_item.enhancement_slots - target_item.used_slots

            if item_destroyed:
                return {
                    "success": False,
                    "message": f"Enhancement failed. {slots_left} slot(s) remaining.",
                    "item_destroyed": True
                }
            else:
                return {
                    "success": False,
                    "message": f"Enhancement failed. {slots_left} slot(s) remaining.",
                    "item_destroyed": False
                }
            
    #gain mining xp and handle level ups
    def gain_mining_xp(self, amount):
        from systems.mining_system import MINING_XP_TABLE

        self.mining_xp += amount
        leveled_up = False

        #check for level ups
        while self.mining_level < 99 and self.mining_xp >= MINING_XP_TABLE[self.mining_level]:
            self.mining_level += 1
            leveled_up = True
            print(f"⛏️ Mining level up! Reached level {self.mining_level}")

        if not leveled_up:
            print(f"⛏️ Gained {amount} mining XP")

    #get progress towards next mining level
    def get_mining_xp_progress(self):
        from systems.mining_system import MINING_XP_TABLE

        if self.mining_level >= 99:
            return 1.0, 0, 0
        
        current_level_xp = MINING_XP_TABLE[self.mining_level - 1] if self.mining_level > 1 else 0
        next_level_xp = MINING_XP_TABLE[self.mining_level]
            
        xp_into_level = self.mining_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp

        progress = xp_into_level / xp_needed if xp_needed > 0 else 1.0

        return progress, xp_into_level, xp_needed
    
    #update gathering power and mining speed from equipped pickaxe
    def update_gathering_stats_from_tool(self):

        #reset to base
        self.gathering_power = 0
        self.mining_speed_bonus = 0.0
        self.woodcutting_speed_bonus = 0.0

        #check weapon slot for tool
        tool = self.equipment.get("weapon")

        if tool and hasattr(tool, "tool_type"):
            gathering = getattr(tool, "gathering_power", 0)
            self.gathering_power += gathering

            if tool.tool_type == "Pickaxe":
                speed = getattr(tool, "mining_speed_bonus", 0.0)
                self.mining_speed_bonus += speed
            elif tool.tool_type == "Hatchet":
                speed = getattr(tool, "woodcutting_speed_bonus", 0.0)
                self.woodcutting_speed_bonus += speed

    #gain woodcutting xp and handle level ups
    def gain_woodcutting_xp(self, amount):
        from systems.woodcutting_system import WOODCUTTING_XP_TABLE

        self.woodcutting_xp += amount
        leveled_up = False

        #check for level ups
        while self.woodcutting_level < 99 and self.woodcutting_xp >= WOODCUTTING_XP_TABLE[self.woodcutting_level]:
            self.woodcutting_level += 1
            leveled_up = True
            print(f"🪓 Woodcutting level up! Reached level {self.woodcutting_level}")

        if not leveled_up:
            print(f"🪓 Gained {amount} woodcutting XP")

    #get progress towards next woodcutting level
    def get_woodcutting_xp_progress(self):
        from systems.woodcutting_system import WOODCUTTING_XP_TABLE

        if self.woodcutting_level >= 99:
            return 1.0, 0, 0
        
        current_level_xp = WOODCUTTING_XP_TABLE[self.woodcutting_level - 1] if self.woodcutting_level > 1 else 0
        next_level_xp = WOODCUTTING_XP_TABLE[self.woodcutting_level]

        xp_into_level = self.woodcutting_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp

        progress = xp_into_level / xp_needed if xp_needed > 0 else 1.0

        return progress, xp_into_level, xp_needed
    






                