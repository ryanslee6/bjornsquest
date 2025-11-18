from entities.stats import Stats
from data.exp_table import exp_table
import pygame
import time
from settings import EQUIP_SLOTS, WEAPON_SLOT

class Player:
    def __init__(self, name = "Bjorn", item_manager = None, is_player = True):
        self.name = name
        self.stats = Stats()
        self.level = 1
        self.exp = 0
        self.stat_points = 0
        self.inventory = []
        self.active_effects = []
        self.regen_timer = 0
        self.gold = 100
        self.auto_combat_unlocked = False

        self.item_manager = item_manager

        self.equipment = {
            "head": None,
            "necke": None,
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
    
    def level_up(self):
        self.level += 1
        self.stat_points += 5

        self.stats.recalc_stats
        
        self.game.show_levelup_window = True

    def add_item(self, item_id, quantity = 1):
        #if item_id in self.inventory:
        #    self.inventory[item_id] += quantity
        #else:
        #    self.inventory[item_id] = quantity

        #print(f"[INVENTORY] +{quantity} {item_id} (Total: {self.inventory[item_id]})")
        item = self.item_manager.get(item_id)

        if item_id.lower() in ("gold", "gold_coins", "gold_coins", "coins"):
            self.gold += quantity
            print(f"[INVENTORY] +{quantity} Gold Coins (Total: {self.gold})")
            return

        if item.stackable:
            for entry in self.inventory:
                if entry["id"] == item_id and entry.get("stackable", True):
                    entry["qty"] += quantity
                    break
            else:
                self.inventory.append({"id": item_id, "qty": quantity, "stackable": True})
        else:
            for _ in range(quantity):
                self.inventory.append({"id": item_id, "stackable": False})
        print(f"[INVENTORY] +{quantity} {item.name}")
        

    def use_item(self, item_id, item_manager):
        #item = item_manager.get(item_id)

        #item.use(self)

        #if item.stackable:
        #    self.inventory[item_id] -= 1
        #    if self.inventory[item_id] <= 0:
        #        del self.inventory[item_id]
        for entry in self.inventory:
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

        #add gear bonuses
        self.apply_gear_stats()

        #let Stats class compute hp/mp/regen
        self.stats.recalc_stats()

    def equip_item(self, item):
        #attmpts to equip an item from inventory

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
            self.inventory.append({"id": equipped_item.id})
            self.equipment[slot_name] = None
            print(f"[UNEQUIP] Removed item from {slot_name}.")
            self.recalculate_stats()

    def remove_from_inventory(self, item):
        #remove a single insteance of an item from inventory list
        for entry in self.inventory:
            if entry["id"] == item.id:
                self.inventory.remove(entry)
                return
            
    def apply_gear_stats(self):
        #apply armor and weapon stats
        for slot, item in self.equipment.items():
            if not item:
                continue

            #armor
            if item.type == "Armor":
                armor_value = item.armor_min
                self.stats.armor += armor_value
            
            #weapon
            if item.type == "Weapon":
                self.stats.min_damage = item.min_dmg
                self.stats.max_damage = item.max_dmg
                self.stats.attack_speed = item.attack_speed
                 

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
    
    def attack(self, target):
        import random

        is_miss = random.random() > self.stats.hit_chance
        if is_miss:
            return 0, True, False, False

        is_dodged = random.random() < target.stats.dodge_chance
        if is_dodged:
            return 0, False, False, True
        
        min_dmg, max_dmg = self.stats.get_damage_range()
        base_damage = random.randint(min_dmg, max_dmg)
        
        #crit chance
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:    
            base_damage *= 2
        
        damage = max(0, base_damage - target.stats.armor)
        
        target.stats.hp = max(0, target.stats.hp - damage)
        
        return damage, is_miss, is_crit, is_dodged
    
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
        #returns players total gold based on gold coins in inventory
        total = self.gold
        if isinstance(self.inventory, dict):
            total += self.inventory.get("gold_coins", 0)
        else:
            for entry in self.inventory:
                if entry["id"] == "gold_coins":
                    total += entry.get("qty", 1)
        return total
    
    def spend_gold(self, amount):
        remaining = amount

        for entry in self.inventory:
            if entry["id"] == "gold_coins":
                if entry["qty"] >= remaining:
                    entry["qty"] -= remaining
                    remaining = 0
                else:
                    remaining -= entry["qty"]
                    entry["qty"] = 0
                break
        
        if remaining > 0:
            self.gold = max(0, self.gold - remaining)

    def add_status_effect(self, name, duration, icon = None, color = (200, 200, 200)):
        if not hasattr(self, "active_effects"):
            self.active_effects = []

        self.active_effects.append({
            "name": name,
            "expires": time.time() + duration,
            "icon": icon,
            "color": color
        })

    def remove_expired_effects(self):
        now = time.time()
        new_list = []

        for effect in self.active_effects:
            if now < effect["expires"]:
                new_list.append(effect)
            else:
                if "revert" in effect:
                    effect["revert"](self)

        self.active_effects = new_list