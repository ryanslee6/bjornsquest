import json
import pygame
from systems.items import Item, ConsumableItem
from settings import RARITY_COLORS

class ItemManager:
    def __init__(self, items_file = "data/items.json"):
        with open(items_file, "r") as f:
            self.item_data = json.load(f)

        self.tooltip_font = pygame.font.Font(None, 20)

    def get(self, item_id):
        data = self.item_data[item_id]

        if data["type"] == "consumable":
            item = ConsumableItem(item_id, data)
        else:
            item = Item(item_id, data)

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

        lines = item.tooltip_text()
        item.tooltip_surfaces = [
            self.tooltip_font.render(line, True, (255, 255, 255))
            for line in lines
        ]

        item.tooltip_width = max(s.get_width() for s in item.tooltip_surfaces)
        item.tooltip_height = sum(s.get_height() for s in item.tooltip_surfaces)

        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))

        item.name_surface = self.tooltip_font.render(item.name, True, rarity_color)
        item.name_height = item.name_surface.get_height()
        item.qty_surfaces = {}

        return item