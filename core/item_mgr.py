import json
from systems.items import Item, ConsumableItem

class ItemManager:
    def __init__(self, items_file = "data/items.json"):
        with open(items_file, "r") as f:
            self.item_data = json.load(f)

    def get(self, item_id):
        data = self.item_data[item_id]

        if data["type"] == "consumable":
            return ConsumableItem(item_id, data)
        
        return Item(item_id, data)