import random
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class BountyTier(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3

@dataclass
class BountyReward:
    experience: int
    gold: int
    bounty_points: int

    def __str__(self):
        return f"{self.experience} XP, {self.gold} Gold, and {self.bounty_points} Bounty Points"
    
@dataclass
class Bounty:       
    #Represents a single bounty quest.
    
    #Attributes explained:
    #- id: Unique identifier for each bounty (useful for saving/loading)
    #- tier: Which difficulty tier (EASY, MEDIUM, HARD)
    #- monster_name: The type of monster to kill
    #- target_count: How many monsters need to be killed
    #- current_count: How many have been killed so far
    #- reward: The BountyReward object containing all reward info
    #- is_completed: Whether the bounty is done
    
    id: int
    tier: BountyTier
    monster_name: str
    target_count: int
    current_count: int
    reward: BountyReward
    is_completed: bool = False

    def add_kill(self, count: int = 1) -> bool:
        #add kills to the bounty and check if completed
        if self.is_completed:
            return False
        
        self.current_count += count

        #check if weve reached or exceeded the target
        if self.current_count >= self.target_count:
            self.current_count = self.target_count #cap at target
            self.is_completed = True
            return True
        
        return False
     
    def get_progress_percentage(self) -> float:
        #get completion progress as a percentage
        return self.current_count / self.target_count
    
    def get_progress_text(self) -> str:
        #get human readable progress text
        return f"{self.current_count}/{self.target_count}"
    
    def __str__(self):
        #string representation for displaying the bounty
        status = "COMPLETE" if self.is_completed else self.get_progress_text()
        return f"[{self.tier.name}] Kill {self.target_count} {self.monster_name} - {status}"
    
class BountyBoard:
    def __init__(self):
        #monster pools
        self.monster_pools: Dict[BountyTier, List[str]] = {
            BountyTier.EASY: [
                "Goblin"
            ],
            BountyTier.MEDIUM: [
                "Skeleton"
            ],
            BountyTier.HARD: [
                "Wolf"
            ]
        }
        #kill count ranges for each tier (min, max)
        self.kill_count_ranges: Dict[BountyTier, tuple] = {
            BountyTier.EASY: (5, 15),
            BountyTier.MEDIUM: (10, 25),
            BountyTier.HARD: (15, 40)
        }

        #rewards for each tier (currently multiplied by kill count, look into changing later)
        self.base_rewards: Dict[BountyTier, Dict[str, int]] = {
            BountyTier.EASY: {
                "experience": 10,
                "gold": 5,
                "bounty_points": 1
            },
            BountyTier.MEDIUM: {
                "experience": 25,
                "gold": 15,
                "bounty_points": 2
            },
            BountyTier.HARD: {
                "experience": 50,
                "gold": 35,
                "bounty_points": 3
            }
        }

        #track active bounties
        self.active_bounties: List[Bounty] = []

        #counter for generating unique IDs
        self._next_bounty_id = 0

    def generate_bounty(self, tier: BountyTier) -> Bounty:
        #generate a new random bounty for the specified tier
        monster = random.choice(self.monster_pools[tier])

        #generate random kill count within tiers range
        min_kills, max_kills = self.kill_count_ranges[tier]
        kill_count = random.randint(min_kills, max_kills)

        #calculate rewards based on tier and kill count
        base_reward = self.base_rewards[tier]
        reward = BountyReward(
            experience = base_reward["experience"] * kill_count,
            gold = base_reward["gold"] * kill_count,
            bounty_points = base_reward["bounty_points"]
        )

        #create the bounty
        bounty = Bounty(
            id = self._next_bounty_id,
            tier = tier,
            monster_name = monster,
            target_count = kill_count,
            current_count = 0,
            reward = reward
        )

        #increment ID for next bounty
        self._next_bounty_id += 1

        return bounty
    
    def add_bounty(self, tier: BountyTier) -> Bounty:
        #generate and add a new bounty to the active list
        bounty = self.generate_bounty(tier)
        self.active_bounties.append(bounty)
        return bounty
    
    def remove_bounty(self, bounty_id: int) -> bool:
        #remove a bounty from the active list

        for i, bounty in enumerate(self.active_bounties):
            if bounty.id == bounty_id:
                self.active_bounties.pop(i)
                return True
        return False
    
    def on_monster_killed(self, monster_name: str) -> List[Bounty]:
        #called when a monster is killed. updates all relevant bounties
        completed_bounties = []

        #check active bounties
        for bounty in self.active_bounties:
            #only update if monster matches and bounty isnt already completed
            if bounty.monster_name == monster_name and not bounty.is_completed:
                was_completed = bounty.add_kill(1)
                if was_completed:
                    completed_bounties.append(bounty)

        return completed_bounties
    
    def get_active_bounties(self) -> List[Bounty]:
        #get active bounties
        return self.active_bounties
    
    def get_incomplete_bounties(self) -> List[Bounty]:
        #get only bounties not yet completed
        return [b for b in self.active_bounties if not b.is_completed]
    
    def get_completed_bounties(self) -> List[Bounty]:
        #get only completed bounties
        return [b for b in self.active_bounties if b.is_completed]
    
    def claim_bounty(self, bounty_id: int) -> Optional[BountyReward]:
        #claim a completed bounty and remove it from the list

        for i, bounty in enumerate(self.active_bounties):
            if bounty.id == bounty_id:
                if bounty.is_completed:
                    reward = bounty.reward
                    self.active_bounties.pop(i)
                    return reward
                else:
                    return None
        return None


    
