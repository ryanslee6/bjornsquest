import time
import random
import json
import os

class WoodcuttingSystem:
    def __init__(self):
        #woodcutting stats tracking
        self.total_attempts = 0
        self.successful_chops = 0
        self.failed_chops = 0

        #tree states
        self.trees = {}
        self.active_tree = None
        self.chopping_timer = 0
        self.chopping_action_time = 0
        self.selected_tree_id = None

        #auto woodcutting
        self.auto_woodcutting_enabled = False
        self.last_chopped_tree = None

        #load tree data
        self.tree_data = self.load_tree_data()

        #initialize tree states
        self.initialize_trees()

    #load woodcutting tree definitions from JSON
    def load_tree_data(self):
        path = os.path.join("data", "woodcutting_nodes.json")

        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        else:
            return {
                "normal_tree": {
                    "name": "Normal Tree",
                    "difficulty": 10,
                    "base_action_time": 3.0,
                    "xp_reward": 17,
                    "required_level": 1,
                    "respawn_time": 5.0,
                    "max_health": 3
                }
            }
        
    #initialize state for all trees
    def initialize_trees(self):
        for tree_id, tree_data in self.tree_data.items():
            self.trees[tree_id] = {
                "current_health": tree_data["max_health"],
                "depleted": False,
                "respawn_timer": 0
            }

    #calculate success chance
    def calculate_success_chance(self, gathering_power, difficulty):
        if gathering_power <= 0:
            return 0.05
        
        success_chance = gathering_power / (gathering_power + difficulty)

        #clamp to min/max
        return max(0.05, min(0.95, success_chance))
    
    #calculate actual chopping time with speed bonus (hard capped 90%)
    def calculate_action_time(self, base_time, woodcutting_speed_bonus):
        #clamp max speed to 90%
        capped_bonus = min(0.90, woodcutting_speed_bonus)

        #apply reduction
        actual_time = base_time * (1 - capped_bonus)

        return max(0.1, actual_time)
    
    #initiate chopping action on a tree
    def start_chopping(self, player, tree_id):
        if not self.can_chop_tree(player, tree_id):
            return False
        
        if tree_id not in self.tree_data:
            print(f"[WOODCUTTING] Unknown tree: {tree_id}")
            return False
        
        tree_info = self.tree_data[tree_id]
        tree_state = self.trees[tree_id]

        #check level requirement
        if player.woodcutting_level < tree_info["required_level"]:
            return False
        
        #check if tree is depleted
        if tree_state["depleted"]:
            return False
        
        #calculate action time with woodcutting speed
        woodcutting_speed = player.woodcutting_speed_bonus
        action_time = self.calculate_action_time(
            tree_info["base_action_time"],
            woodcutting_speed
        )

        #set active chopping
        self.active_tree = tree_id
        self.last_chopped_tree = tree_id
        self.chopping_timer = 0
        self.chopping_action_time = action_time

        return True
    
    #update woodcutting progress and handle completions
    def update(self, dt, player):
        #update respawn timers
        for tree_id, state in self.trees.items():
            if state["depleted"]:
                state["respawn_timer"] -= dt
                if state["respawn_timer"] <= 0:
                    #respawn tree
                    tree_data = self.tree_data[tree_id]
                    state["current_health"] = tree_data["max_health"]
                    state["depleted"] = False
                    print(f"[WOODCUTTING] {tree_data['name']} respawned")

                    if self.auto_woodcutting_enabled and self.last_chopped_tree == tree_id:
                        print(f"[WOODCUTTING] Auto-restarting chopping")
                        self.start_chopping(player, tree_id)

        #update active chopping
        if self.active_tree:
            self.chopping_timer += dt

            #check if action is completed
            if self.chopping_timer >= self.chopping_action_time:
                self.complete_chopping_action(player)

                #auto woodcutting re-initiate
                if self.auto_woodcutting_enabled and self.active_tree and not self.trees[self.active_tree]["depleted"]:
                    self.start_chopping(player, self.active_tree)
                else:
                    self.active_tree = None
                    self.chopping_timer = 0

    #process a chopping attempt
    def complete_chopping_action(self, player):
        if not self.active_tree:
            return
        
        tree_id = self.active_tree
        tree_info = self.tree_data[tree_id]
        tree_state = self.trees[tree_id]

        self.total_attempts += 1

        #calculate success chance
        gathering_power = player.gathering_power
        difficulty = tree_info["difficulty"]
        success_chance = self.calculate_success_chance(gathering_power, difficulty)

        #roll for success
        roll = random.random()
        success = roll <= success_chance

        if success:
            self.successful_chops += 1

            #grant xp
            xp_gained = tree_info["xp_reward"]
            player.gain_woodcutting_xp(xp_gained)

            #add logs to inventory
            log_item_id = tree_id.replace("_tree", "_logs")
            player.add_item(log_item_id, 1)

            #damage tree
            tree_state["current_health"] -= 1

            #check if tree is depleted
            if tree_state["current_health"] <= 0:
                tree_state["depleted"] = True
                tree_state["respawn_timer"] = tree_info["respawn_time"]
                print(f"[WOODCUTTING] {tree_info['name']} depleted, respawns in {tree_info['respawn_time']}s")

                #stop auto woodcutting if tree depleted
                if self.auto_woodcutting_enabled:
                    self.active_tree = None
                    self.chopping_timer = 0

            print(f"[WOODCUTTING] Success! +{xp_gained} XP, gained {tree_info['name'].replace('Tree', 'Logs')}")

        else:
            self.failed_chops += 1
            print(f"[WOODCUTTING] Failed to chop {tree_info['name']}")

        #reset for next action if not auto chopping or tree depleted
        if not self.auto_woodcutting_enabled or tree_state["depleted"]:
            self.active_tree = None
            self.chopping_timer = 0

    #get current chopping action progress
    def get_progress_percentage(self):
        if not self.active_tree or self.chopping_action_time <= 0:
            return 0
        
        return min(1.0, self.chopping_timer / self.chopping_action_time)

    #calculate overall success rate
    def get_success_rate_percentage(self):
        if self.total_attempts == 0:
            return 0
        
        return (self.successful_chops / self.total_attempts) * 100
    
    #get full info about a tree,m including current state
    def get_tree_info(self, tree_id):
        if tree_id not in self.tree_data:
            return None
        
        data = self.tree_data[tree_id].copy()
        state = self.trees[tree_id]
        data["current_state"] = state

        return data
    
    #check if a player can chop this tree
    def can_chop_tree(self, player, tree_id):
        if tree_id not in self.tree_data:
            return False
        
        tree_info = self.tree_data[tree_id]
        tree_state = self.trees[tree_id]

        tool = player.equipment.get("weapon")
        if not tool or not hasattr(tool, "tool_type") or tool.tool_type != "Hatchet":
            return False

        #level check
        if player.woodcutting_level < tree_info["required_level"]:
            return False
        
        #depletion check
        if tree_state["depleted"]:
            return False
        
        return True
    
from systems.mining_system import MINING_XP_TABLE
WOODCUTTING_XP_TABLE = MINING_XP_TABLE


