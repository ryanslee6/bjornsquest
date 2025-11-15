from entities.stats import Stats
from data.exp_table import exp_table
import pygame
import time

class Player:
    def __init__(self, name = "Bjorn", item_manager = None, is_player = True):
        self.name = name
        self.stats = Stats()
        self.level = 1
        self.exp = 0
        #self.exp_to_level = 15
        self.inventory = []
        self.active_effects = []
        self.regen_timer = 0
        self.gold = 0
        self.auto_combat_unlocked = False

        self.item_manager = item_manager

        try:
            self.sprite = pygame.image.load("assets/images/bjorn1.png").convert_alpha()
        except:
            self.sprite = None
            print("⚠️ Player sprite missing — using placeholder.")

        if self.sprite:
            self.sprite = pygame.transform.scale(self.sprite, (180, 160))

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
        base_damage = self.stats.strength
        
        #crit chance
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:    
            base_damage *= 2
        
        damage = max(0, base_damage - target.stats.armor)
        
        target.stats.hp = max(0, target.stats.hp - damage)
        
        return damage, is_crit
    
    def gain_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.level < len(exp_table) and self.exp >= exp_table[self.level]:
            self.level += 1
            leveled_up = True

            self.stats.strength += 1
            self.stats.dexterity += 1
            self.stats.constitution += 1
            self.stats.intelligence += 1
            
            self.stats.hp = self.stats.max_hp
            self.stats.mp = self.stats.max_mp

            print(f"Leveled up! New level: {self.level}")
            print(f"Stats increased! STR:{self.stats.strength} DEX:{self.stats.dexterity} CON:{self.stats.constitution} INT:{self.stats.intelligence}")
            print(f"HP/MP fully restored: {self.stats.hp}/{self.stats.max_hp} HP, {self.stats.mp}/{self.stats.max_mp} MP")
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