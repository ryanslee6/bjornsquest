
class Stats:
    def __init__(self, hp = 400, mp = 500, strength = 10, dexterity = 5, constitution = 10, intelligence = 5, is_player = False):
        #self.hp = hp
        #self.max_hp = hp
        #self.mp = mp
        #self.max_mp = mp
        
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence

        if is_player:
            self.base_hp = 400
            self.base_mp = 500
        else:
            self.base_hp = hp
            self.base_mp = mp
        
        
        self.hp_per_con = 5
        self.base_hp_regen = 0.02
        self.hp_regen_per_con = 0.01
        self._hp_regen_buffer = 0.0

        self.base_mp = 500
        self.mp_per_int = 5
        self.base_mp_regen = 0.05
        self.mp_regen_per_int = 0.01

        self.recalc_stats()

        self.crit_chance = 0.05
        self.dodge_chance = 0.05
        self.attack_speed = 1.0
        self.armor = 0
        
    def recalc_stats(self):
        self.max_hp = self.base_hp + (self.constitution * self.hp_per_con)
        if not hasattr(self, "hp"):
            self.hp = self.max_hp
        else:
            self.hp = min(self.hp, self.max_hp)

        self.max_mp = self.base_mp + (self.intelligence * self.mp_per_int)
        if not hasattr(self, "mp"):
            self.mp = self.max_mp
        else:
            self.mp = min(self.mp, self.max_mp)

        self.hp_regen = self.base_hp_regen + (self.constitution * self.hp_regen_per_con)
        self.mp_regen = 0.05 + (self.intelligence * 0.01)

    def get_hp_regen(self):
        return self.base_hp_regen + (self.constitution * self.hp_regen_per_con)
    
    def get_mp_regen(self):
        return 0.05 + (self.intelligence * 0.01)
    
    def regen_tick(self):
        regen = self.get_hp_regen

        self._hp_regen_buffer += regen

        if self._hp_regen_buffer >= 1:
            heal_amount = int(self._hp_regen_buffer)
            self._hp_regen_buffer -= heal_amount

            self.hp = min(self.max_hp, self.hp + heal_amount)

            return heal_amount
        
        return 0