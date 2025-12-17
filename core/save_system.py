import json
import os
from datetime import datetime
from pathlib import Path
import time

class SaveSystem:
    #handles saving and loading player progress to/from json files

    #This system saves:
    #- Player stats (level, exp, stat points, attributes)
    #- Inventory (including unique equipment with enhancements)
    #- Equipped items
    #- Gold and other currencies
    #- Unlocks (like auto combat)
    #- Active effects and buffs

    def __init__(self, saves_folder = "saves"):
        #initialize the save system
        self.saves_folder = saves_folder
        self._ensure_saves_folder()

    def _ensure_saves_folder(self):
        #create the save folder if it doesnt exist
        Path(self.saves_folder).mkdir(parents = True, exist_ok = True)

    def save_game(self, player, game_state, save_name = None):
        #save the current game state to a file
        try:
            #generate save filename
            if save_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_name = f"{player.name}.json"

            #ensure .json extension
            if not save_name.endswith('.json'):
                save_name += '.json'

            save_path = os.path.join(self.saves_folder, save_name)

            #build save data
            save_data = {
                'metadata': {
                    'version': '1.0',
                    'save_date': datetime.now().isoformat(),
                    'character_name': player.name,
                    'level': player.level,
                    'playertime': game_state.get('playtime', 0)
                },
                'player': self._serialize_player(player),
                'game_state': self._serialize_game_state(game_state)
            }

            #write to file with nice formatting
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent = 2)

            print(f"[SAVE] Game saved successfully to {save_path}")
            return save_path
        
        except Exception as e:
            print(f"[SAVE ERROR] Failed to save game: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    #convert player object to a dict that can be saved as json
    def _serialize_player(self, player):
        
        base_str = getattr(player.stats, 'base_strength', player.stats.strength)
        base_dex = getattr(player.stats, 'base_dexterity', player.stats.dexterity)
        base_con = getattr(player.stats, 'base_constitution', player.stats.constitution)
        base_int = getattr(player.stats, 'base_intelligence', player.stats.intelligence)

        player_data = {
            'name': player.name,
            'level': player.level,
            'exp': player.exp,
            'gold': player.gold,
            'stat_points': player.stat_points,

            #base stats
            'stats': {
                'base_strength': base_str,
                'base_dexterity': base_dex,
                'base_intelligence': base_int,
                'hp': player.stats.hp,
                'mp': player.stats.mp,
            },

            #unlocks
            'unlocks': {
                'auto_combat': player.auto_combat_unlocked,
            },

            #inventory
            'inventory': self._serialize_inventory(player.inventory),

            #equipment
            'equipment': self._serialize_equipment(player.equipment),

            #active effects
            'active_effects': self._serialize_effects(player.active_effects),
        }

        return player_data
    
    #serialize the inventory, handling both stackable and unique items
    def _serialize_inventory(self, inventory):
        serialized = []

        for entry in inventory:
            if entry.get('stackable', True):
                #stackables
                serialized.append({
                    'type': 'stackable',
                    'id': entry['id'],
                    'qty': entry['qty']
                })
            else:
                #unique items - need full serialization
                item = entry['item']
                serialized.append({
                    'type': 'unique',
                    'item_data': self._serialize_item(item)
                })
        return serialized
    
    def _serialize_item(self, item):
        #serialize a single item (usually equipment) with all its properties

        item_data = {
            'id': item.id,
            'name': item.name,
            'type': item.type,

            #enhancement data
            'enhancements': item.enhancements if hasattr(item, 'enhancements') else [],
            'used_slots': item.used_slots if hasattr(item, 'used_slots') else 0,
            'enhancement_slots': item.enhancement_slots if hasattr(item, 'enhancement_slots') else 0,

            #rolled stats
            'rolled_armor': item.rolled_armor if hasattr(item, 'rolled_armor') else None,
            'rolled_stats': item.rolled_stats if hasattr(item, 'rolled_stats') else {},
        }

        return item_data
    
    def _serialize_equipment(self, equipment):
        #serialize equipped items (weapons, armor, accessories)
        serialized = {}

        for slot, item in equipment.items():
            if item is None:
                serialized[slot] = None
            else:
                serialized[slot] = self._serialize_item(item)

        return serialized
    
    #serialize active effects
    #Note: save reamining duration, not absolute expiration time
    def _serialize_effects(self, effects):
        serialized = []
        current_time = time.time()

        for effect in effects:
            #calculate remaining duration
            expires_at = effect.get('expires_at', effect.get('expires', current_time))
            remaining = max(0, expires_at - current_time)

            #only save effects with time remaining
            if remaining > 0:
                serialized.append({
                    'name': effect['name'],
                    'remaining_duration': remaining,
                    'raw_key': effect.get('raw_key'),
                    'mods': effect.get('mods', {}),
                    'color': effect.get('color', (200, 200, 200)),
                })

        return serialized
    
    def _serialize_game_state(self, game_state):
        return {
            'current_monster': game_state.get('current_monster'),
            'monster_page': game_state.get('monster_page', 0),
            'playtime': game_state.get('playtime', 0),
        }
    
    #load a saved game and apply it to the player object
    def load_game(self, save_path, player, item_manager):
        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)

            print(f"[LOAD] Loading save from {save_path}")

            #load player data
            self._deserialize_player(save_data['player'], player, item_manager)

            #return game stat for the game manger to handle
            return save_data.get('game_stat', {})
        
        except Exception as e:
            print(f"[LOAD ERROR] Failed to load game: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    #load saved player data into the player object
    #this rebuilds the players state including inventory with enhancements
    def _deserialize_player(self, player_data, player, item_manager):

        #basic attributes
        player.name = player_data['name']
        player.level = player_data['level']
        player.exp = player_data['exp']
        player.gold = player_data['gold']
        player.stat_points = player_data['stat_points']

        #stats
        stats_data = player_data['stats']  
        
        base_str = stats_data.get('base_strength', 5)
        base_dex = stats_data.get('base_dexterity', 5)
        base_con = stats_data.get('base_constitution', 5)
        base_int = stats_data.get('base_intelligence', 5)

        # Set base stats
        player.stats.base_strength = base_str
        player.stats.base_dexterity = base_dex
        player.stats.base_constitution = base_con
        player.stats.base_intelligence = base_int
        
        # Update current stat values
        player.stats.strength = base_str
        player.stats.dexterity = base_dex
        player.stats.constitution = base_con
        player.stats.intelligence = base_int

        #recalculate derived stats
        player.stats.recalc_stats()

        #set current hp/mp
        player.stats.hp = stats_data['hp']
        player.stats.mp = stats_data['mp']

        #unlocks
        unlocks = player_data.get('unlocks', {})
        player.auto_combat_unlocked = unlocks.get('auto_combat', False)

        #clear and rebuild inventory
        player.inventory.clear()
        self._deserialize_inventory(player_data['inventory'], player, item_manager)

        #clear and rebuild equipment
        for slot in player.equipment:
            player.equipment[slot] = None
        self._deserialize_equipment(player_data['equipment'], player, item_manager)

        #recalculate stats with equipment
        player.recalculate_stats()

        #active effects
        player.active_effects.clear()
        self._deserialize_effects(player_data.get('active_effects', []), player)

        print(f"[LOAD] Player {player.name} loaded successfully!")
        print(f"[LOAD] Level {player.level}, {player.gold} gold, {len(player.inventory)} inventory items")

    #rebuilds inventory from saved data
    def _deserialize_inventory(self, inventory_data, player, item_manager):
        for entry in inventory_data:
            if entry['type'] == 'stackable':
                player.inventory.append({
                    'id': entry['id'],
                    'qty': entry['qty'],
                    'stackable': True
                })
            else:
                item = self._deserialize_item(entry['item_data'], item_manager)
                player.inventory.append({
                    'item': item,
                    'stackable': False
                })
    
    #recreate an item from saved data, including enhancements
    def _deserialize_item(self, item_data, item_manager):
        from systems.items import Item

        #get base item data from item manager
        base_data = item_manager.item_data.get(item_data['id'])
        if not base_data:
            print(f"[LOAD WARNING] Item {item_data['id']} not found in item data!")
            return None
        
        #create rolled stats dict
        rolled_stats = {
            'armor': item_data.get('rolled_armor'),
            'bonus_stats': item_data.get('rolled_stats', {})
        }

        #create the item with rolled stats
        item = Item(item_data['id'], base_data, rolled_stats = rolled_stats)

        #restore enhancements
        item.enhancements = item_data.get('enhancements', [])
        item.used_slots = item_data.get('used_slots', 0)
        item.enhancement_slots = item_data.get('enhancement_slots', 0)

        #setup visuals
        item_manager._setup_item_visuals(item, base_data)

        return item
    
    #rebuild equipped items
    def _deserialize_equipment(self, equipment_data, player, item_manager):
        for slot, item_data in equipment_data.items():
            if item_data is None:
                player.equipment[slot] = None
            else:
                item = self._deserialize_item(item_data, item_manager)
                player.equipment[slot] = item

    #restore active effects
    def _deserialize_effects(self, effects_data, player):
        current_time = time.time()

        for effect_data in effects_data:
            remaining = effect_data['remaining_duration']

            player.active_effects.append({
                'name': effect_data['name'],
                'raw_key': effect_data.get('raw_key'),
                'expires': current_time + remaining,
                'expires_at': current_time + remaining,
                'duration': remaining,
                'start': current_time,
                'mods': effect_data.get('mods', {}),
                'color': tuple(effect_data.get('color', (200, 200, 200))),
            })

    #get a list of all available save files
    def list_saves(self):
        saves = []

        for filename in os.listdir(self.saves_folder):
            if not filename.endswith('.json'):
                continue

            try:
                filepath = os.path.join(self.saves_folder, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)

                metadata = data.get('metadata', {})
                saves.append({
                    'filename': filename,
                    'path': filepath,
                    'character_name': metadata.get('character_name', 'Unknown'),
                    'level': metadata.get('level', 1),
                    'save_date': metadata.get('save_date', 'Unknown'),
                })
            except Exception as e:
                print(f"[LOAD] Error reading save file {filename}: {e}")

        #sort by save date (newest first)
        saves.sort(key = lambda s: s['save_date'], reverse = True)

        return saves
    
    #delete a save file
    def delete_save(self, save_path):
        try:
            os.remove(save_path)
            print(f"[SAVE] Deleted save file: {save_path}")
            return True
        except Exception as e:
            print(f"[SAVE ERROR] Failed to delete {save_path}: {e}")
            return False
        
    #get the path for the autosave file for this character
    def get_autosave_path(self, player):
        return os.path.join(self.saves_folder, f"{player.name}_autosave.json")
    
    #perform an autosave using a fixed filename for this character
    def autosave(self, player, game_state):
        autosave_path = self.get_autosave_path(player)

        #extract just the filename for save_game
        filename = os.path.basename(autosave_path)

        return self.save_game(player, game_state, save_name = filename)