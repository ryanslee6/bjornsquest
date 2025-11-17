import json
import pygame
from systems.items import Item, ConsumableItem

class ItemManager:
    def __init__(self, items_file = "data/items.json"):
        with open(items_file, "r") as f:
            self.item_data = json.load(f)

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
            except Exception as e:
                 print(f"[WARNING] Failed to load icon '{icon_name}' for item '{item_id}' — {e}")
                 item.icon = None
        else:
            item.icon = None

        
        return item