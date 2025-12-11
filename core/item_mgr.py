import json
import os
import pygame
from systems.items import Item, ConsumableItem
from settings import RARITY_COLORS

class ItemManager:
    def __init__(self, data_folder = "data"):
        self.item_data = {}
        self.item_cache = {}
        self.tooltip_font = pygame.font.Font(None, 20)

        self.load_all_item_files(data_folder)
    
    # -------------------------------------------------------------------------
    # Load ALL .json item files    (items.json, weapons.json, armor.json, etc)
    # -------------------------------------------------------------------------

    def load_all_item_files(self, data_folder):
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                full_path = os.path.join(data_folder, filename)

                try:
                    with open(full_path, "r") as f:
                        data = json.load(f)

                    for item_id, item_def in data.items():
                        self.item_data[item_id] = item_def

                except Exception as e:
                    print(f"[ITEM MANAGER] Failed to load {filename}: {e}")

        print(f"[ITEM MANAGER] Successfully loaded {len(self.item_data)} items from data/*.json")

    def _setup_item_visuals(self, item, item_data):
        #helper method to setup icons, tooltips, and surfaces for any item
        
        #icon loading
        icon_name = item_data.get("icon")
        if icon_name:
            try:
                path = f"assets/images/{icon_name}"
                item.icon = pygame.image.load(path).convert_alpha()
                item.icon_small = pygame.transform.scale(item.icon, (24, 24))
            except Exception as e:
                item.icon = None
                item.icon_small = None
        else:
            item.icon = None
            item.icon_small = None

        #tooltip surfaces
        lines = [line for line in item.tooltip_text() if not line.startswith("Level Required:")]
        item.tooltip_surfaces = [
            self.tooltip_font.render(line, True, (255, 255, 255))
            for line in lines
        ]

        if item.tooltip_surfaces:
            item.tooltip_width = max(s.get_width() for s in item.tooltip_surfaces)
            item.tooltip_height = sum(s.get_height() for s in item.tooltip_surfaces)
        else:
            item.tooltip_width = 0
            item.tooltip_height = 0

        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
        item.name_surface = self.tooltip_font.render(item.name, True, rarity_color)
        item.name_height = item.name_surface.get_height()
        item.qty_surfaces = {}

    # ------------------------------------------------------------
    # Build an Item object from item_data
    # ------------------------------------------------------------

    def get(self, item_id):
        #check cache first
        if item_id in self.item_cache:
            return self.item_cache[item_id]

        #Not cached - create it
        data = self.item_data[item_id]

        if data.get("type") == "consumable":
            item = ConsumableItem(item_id, data)
        else:
            item = Item(item_id, data)

        #setup all visuals using helper
        self._setup_item_visuals(item, data)

        #cache and return
        self.item_cache[item_id] = item
        return item
    
    def _roll_bonus_stats(self, item_data):
        #roll bonus stats for an item based on its rarty and possible_bonus_stats
        #returns a dict like {"strength": 2, "max_hp": 12}
        import random

        #check if item can have bonus stats
        possible_stats = item_data.get("possible_bonus_stats", {})
        if not possible_stats:
            return {}
        
        #determine how many stats to roll based on rarity
        rarity = item_data.get("rarity", "common").lower()
        stat_count_by_rarity = {
            "common": 0,
            "uncommon": 1,
            "rare": 2,
            "epic": 3,
            "legendary": 4
        }

        num_stats = stat_count_by_rarity.get(rarity, 0)
        if num_stats == 0:
            return {}
        
        #pick random stats from possible_stats
        available_stats = list(possible_stats.keys())
        num_to_roll = min(num_stats, len(available_stats))

        chosen_stats = random.sample(available_stats, num_to_roll)

        #roll values for each chosen stat
        rolled = {}
        for stat in chosen_stats:
            min_val, max_val = possible_stats[stat]
            rolled[stat] = random.randint(min_val, max_val)

        return rolled

    def create_item_with_rolls(self, item_id):
        #create a new item instance with randomly rolled stats
        #returns an item object with rolled_stats applied
        import random

        #get base item data
        if item_id not in self.item_data:
            print(f"[ITEM MANAGER] Item '{item_id}' not found!")
            return None
        
        item_data = self.item_data[item_id]

        #roll stats for this specific item
        rolled_stats = {}

        #roll armor if it's armor with a range
        armor_min = item_data.get("armor_min", 0)
        armor_max = item_data.get("armor_max", 0)

        if armor_max > 0:
            rolled_armor = random.randint(armor_min, armor_max)
            rolled_stats["armor"] = rolled_armor
            print(f"[LOOT]{item_data.get('name', item_id)} rolled {rolled_armor} armor ({armor_min}-{armor_max})")

        #roll bonus stats like +str, +hp, etc for gear based on rarity
        bonus_stats = self._roll_bonus_stats(item_data)
        rolled_stats["bonus_stats"] = bonus_stats

        if bonus_stats:
            bonus_desc = ", ".join([f"+{v} {k}" for k, v in bonus_stats.items()])
            print(f"[LOOT] Bonus stats: {bonus_desc}")

        #if its consumable (no rolling needed), just return cached template
        if item_data.get("type") == "consumable":
            return self.get(item_id)
        
        #for equpment, create a new item instance with rolled stats (not from the cache)
        new_item = Item(item_id, item_data, rolled_stats = rolled_stats)

        #setup all visuals using helper method
        self._setup_item_visuals(new_item, item_data)

        return new_item

