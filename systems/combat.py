import time

class CombatManager:
    def __init__(self, player, monster, loot_system):
        self.player = player
        self.monster = monster
        self.combat_log = []
        self.loot_log = []
        self.combat_active = True
        self.loot_system = loot_system

        self.last_player_attack = time.time()
        self.last_monster_attack = time.time()

        self.player_attack_delay = 1.0
        self.monster_attack_delay = 1.5


    def update(self):
        if not self.combat_active:
            return False

        current_time = time.time()
        something_happened = False
        
        if current_time - self.last_player_attack >= self.player_attack_delay:
            if self.player.is_alive() and self.monster.is_alive():
                dmg = self.player.attack(self.monster)
                self.combat_log.append(f"{self.player.name} hits {self.monster.name} for {dmg} damage!")
                self.last_player_attack = current_time
                something_happened = True

        if current_time - self.last_monster_attack >= self.monster_attack_delay:
            if self.player.is_alive() and self.monster.is_alive():
                dmg = self.monster.attack(self.player)
                self.combat_log.append(f"{self.monster.name} hits {self.player.name} for {dmg} damage!")
                self.last_monster_attack = current_time
                something_happened = True

        if not self.monster.is_alive():
            self.combat_log.append(f"{self.monster.name} was defeated!")
            exp = self.monster.exp_reward
            drops = self.loot_system.generate_loot(self.monster.name)
            print("You found:", drops)
            for drop in drops:
                self.player.add_item(drop["item"], drop["quantity"])

                self.loot_log.append(f"+{drop['quantity']} {drop['item']}")
                self.loot_log = self.loot_log[-5:]
            self.player.gain_exp(exp)
            self.combat_active = False
            something_happened = True
            

        if not self.player.is_alive():
            self.combat_log.append(f"{self.player.name} was defeated!")
            self.combat_active = False
            something_happened = True

        return something_happened
