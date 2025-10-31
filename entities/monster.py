from entities.stats import Stats

class Monster:
    def __init__(self, name = "Goblin", level = 1):
        self.name = name
        self.level = level
        self.stats = Stats(
            hp = 50 + level * 10,
            strength = 5 + level * 2,
            dexterity = 3 + level,
            constitution = 5 + level * 2,
        )
        self.exp_reward = 15
        self.alive = True

    def is_alive(self):
        return self.stats.hp > 0
    
    def attack(self, target):
        import random
        base_damage = self.stats.strength
        if random.random() < self.stats.crit_chance:
            base_damage *= 2
        damage = max(0, base_damage - target.stats.armor)
        target.stats.hp -= damage
        return damage
