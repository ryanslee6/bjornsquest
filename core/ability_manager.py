import json
import os

class AbilityManager:
    def __init__(self):
        self.abilities = {}
        self.load_abilities()

    def load_abilities(self):
        path = os.path.join("data", "abilities.json")
        with open(path, "r") as f:
            data = json.load(f)

        self.abilities = data

    def get(self, ability_id):
        return self.abilities.get(ability_id)