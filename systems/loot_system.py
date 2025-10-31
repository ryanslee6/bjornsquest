import random
import json
from pathlib import Path

class LootSystem:
    def __init__(self, data_file = "data/loot_tables.json"):
        self.loot_tables = self.load_loot_tables(data_file)

    def load_loot_tables(self, file_path):
        path = Path(file_path)
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
            
        else:
            print(f"[Warning] Loot table not found at {file_path}. Using defaults.")
            return {
                "goblin": [
                    {"item": "Gold Coins", "chance": 1.0, "min": 1, "max": 5},
                    {"item": "Health Potion", "chance": 0.1, "min": 1, "max": 1},
                    {"item": "Goblin Chain Mail", "chance": 0.01, "min": 1, "max": 1}
                ],
                "Skeleton": [
                    {"item": "Gold Coins", "chance": 1.0, "min": 5, "max": 10},
                    {"item": "Mana Potion", "chance": 0.1, "min": 1, "max": 1},
                    {"item": "Bone Mace", "chance": 0.01, "min": 1, "max": 1}        
                ]
            }

    def generate_loot(self, source_name):
        if source_name not in self.loot_tables:
            print(f"[LootSystem] No loot table found for '{source_name}'.")
            return []
        
        loot_table = self.loot_tables[source_name]
        drops = []

        for entry in loot_table:
            if random.random() <= entry["chance"]:
                quantity = random.randint(entry["min"], entry["max"])
                drops.append({"item": entry["item"], "quantity": quantity})

        return drops