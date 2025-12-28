import time
import random
import json
import os

class MiningSystem:
    def __init__(self):
        #mining stats tracking
        self.total_attempts = 0
        self.successful_mines = 0
        self.failed_mines = 0

        #node states
        self.nodes = {}
        self.active_node = None
        self.mining_timer = 0
        self.mining_action_time = 0

        #auto mining
        self.auto_mining_enabled = False
        self.last_mined_node = None

        #load node data
        self.node_data = self.load_node_data()

        #initialize node states
        self.initialize_nodes()

    #load mining node definitions from JSON
    def load_node_data(self):
        path = os.path.join("data", "mining_nodes.json")

        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        else:
            return {
                "copper_ore": {
                    "name": "Copper Ore",
                    "difficulty": 10,
                    "base_action_time": 3.0,
                    "xp_reward": 17,
                    "required_level": 1,
                    "respawn_time": 5.0,
                    "max_health": 3
                }
            }
        
    #initialize state for all mining nodes
    def initialize_nodes(self):
        for node_id, node_data in self.node_data.items():
            self.nodes[node_id] = {
                "current_health": node_data["max_health"],
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
    
    #calculate actual mining time with speed bonus (hard capped at 90%)
    def calculate_action_time(self, base_time, mining_speed_bonus):
        #clamp max speed to 90%
        capped_bonus = min(0.90, mining_speed_bonus)

        #apply reduction
        actual_time = base_time * (1 - capped_bonus)

        return max(0.1, actual_time) #minimum 0.1s action time
    
    #initiate mining action on a node
    def start_mining(self, player, node_id):
        if not self.can_mine_node(player, node_id):
            return False
        
        if node_id not in self.node_data:
            print(f"[MINING] Unknown node: {node_id}")
            return False
        
        node_info = self.node_data[node_id]
        node_state = self.nodes[node_id]

        #check level requirement
        if player.mining_level < node_info["required_level"]:
            return False
        
        #check of node is depleted
        if node_state["depleted"]:
            return False
        
        #calculate action time with mining speed
        mining_speed = player.mining_speed_bonus
        action_time = self.calculate_action_time(
            node_info["base_action_time"],
            mining_speed
        )

        #set active mining
        self.active_node = node_id
        self.last_mined_node = node_id
        self.mining_timer = 0
        self.mining_action_time = action_time

        return True
    
    #update mining progress and handle completions
    def update(self, dt, player):
        #update respawn timers
        for node_id, state in self.nodes.items():
            if state["depleted"]:
                state["respawn_timer"] -= dt
                if state["respawn_timer"] <= 0:
                    #respawn node
                    node_data = self.node_data[node_id]
                    state["current_health"] = node_data["max_health"]
                    state["depleted"] = False
                    print(f"[MINING] {node_data['name']} respawned")

                    if self.auto_mining_enabled and self.last_mined_node == node_id:
                        print(f"[MINING] Auto-restarting mining")
                        self.start_mining(player, node_id)

        #update active mining
        if self.active_node:
            self.mining_timer += dt

            #check if action completed
            if self.mining_timer >= self.mining_action_time:
                self.complete_mining_action(player)

                #auto mining re-initiate
                if self.auto_mining_enabled and self.active_node and not self.nodes[self.active_node]["depleted"]:
                    self.start_mining(player, self.active_node)
                else:
                    self.active_node = None
                    self.mining_timer = 0

    #process a mining attempt
    def complete_mining_action(self, player):
        if not self.active_node:
            return
        
        node_id = self.active_node
        node_info = self.node_data[node_id]
        node_state = self.nodes[node_id]

        self.total_attempts += 1

        #calculate success chance
        gathering_power = player.gathering_power
        difficulty = node_info["difficulty"]
        success_chance = self.calculate_success_chance(gathering_power, difficulty)

        #roll for success
        roll = random.random()
        success = roll <= success_chance

        if success:
            self.successful_mines += 1

            #grant xp
            xp_gained = node_info["xp_reward"]
            player.gain_mining_xp(xp_gained)

            #add ore to inventory
            ore_item_id = node_id
            player.add_item(ore_item_id, 1)

            #damage node
            node_state["current_health"] -= 1

            #check if node is depleted
            if node_state["current_health"] <= 0:
                node_state["depleted"] = True
                node_state["respawn_timer"] = node_info["respawn_time"]
                print(f"[MINING] {node_info['name']} depleted, respawns in {node_info['respawn_time']}s")

                #stop auto mining if node depleted
                if self.auto_mining_enabled:
                    self.active_node = None
                    self.mining_timer = 0

            print(f"[MINING] Success! +{xp_gained} XP, gained {node_info['name']}")
        else:
            self.failed_mines += 1
            print(f"[MINING] Failed to mine {node_info['name']}")

        #reset for next action if not auto mining or node depleted
        if not self.auto_mining_enabled or node_state["depleted"]:
            self.active_node = None
            self.mining_timer = 0

    #get current mining action progress
    def get_progress_percentage(self):
        if not self.active_node or self.mining_action_time <= 0:
            return 0
        
        return min(1.0, self.mining_timer / self.mining_action_time)
    
    #calculate overall success rate
    def get_success_rate_percentage(self):
        if self.total_attempts == 0:
            return 0
        
        return (self.successful_mines / self.total_attempts) * 100
    
    #get full info about a node including current state
    def get_node_info(self, node_id):
        if node_id not in self.node_data:
            return None
        
        data = self.node_data[node_id].copy()
        state = self.nodes[node_id]
        data["current_state"] = state

        return data
    
    #check if a player can mine this node
    def can_mine_node(self, player, node_id):
        if node_id not in self.node_data:
            return False
        
        node_info = self.node_data[node_id]
        node_state = self.nodes[node_id]

        tool = player.equipment.get("weapon")
        if not tool or not hasattr(tool, "tool_type") or tool.tool_type != "Pickaxe":
            return False

        #level check
        if player.mining_level < node_info["required_level"]:
            return False
        
        #depletion check
        if node_state["depleted"]:
            return False
        
        return True
    
#generate mining xp table
#formula: sum of floor(level + 300 * 2^(level/7)) for each level
def generate_mining_xp_table(max_level = 99):
    xp_table = [0] #level 1 starts at 0 xp

    for level in range(1, max_level):
        points = int(level + 300 * (2 ** (level / 7.0)))
        xp_table.append(xp_table[-1] + int(points / 4))

    return xp_table
    
MINING_XP_TABLE = generate_mining_xp_table(99)

        