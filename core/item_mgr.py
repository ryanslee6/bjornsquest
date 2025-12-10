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

        # --------------------------------------------------------
        # ICON LOADING
        # --------------------------------------------------------

        icon_name = data.get("icon")
        if icon_name:
            try:
                path = f"assets/images/{icon_name}"
                item.icon = pygame.image.load(path).convert_alpha()
                item.icon_small = pygame.transform.scale(item.icon, (24, 24))

            except Exception as e:
                print(f"[WARNING] Failed to load icon '{icon_name}' for item '{item_id}' — {e}")
                item.icon = None
                item.icon_small = None
        else:
            item.icon = None
            item.icon_small = None 

        # --------------------------------------------------------
        # TOOLTIP TEXT SURFACES
        # --------------------------------------------------------

        lines = item.tooltip_text()
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

        
        # --------------------------------------------------------
        # NAME SURFACE (rarity-colored)
        # --------------------------------------------------------
        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
        item.name_surface = self.tooltip_font.render(item.name, True, rarity_color)
        item.name_height = item.name_surface.get_height()

        item.qty_surfaces = {}
        self.item_cache[item_id] = item

        return item   