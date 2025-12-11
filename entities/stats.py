
class Stats:
    def __init__(self, hp = 500, mp = 75, strength = 5, dexterity = 5, constitution = 5, intelligence = 5, is_player = False, dodge_chance = 0.0, attack_speed = 1.8, hit_chance = None, min_damage = None, max_damage = None):

        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence

        if is_player:
            self.base_hp = 500
            self.base_mp = 75
            self.base_hit_chance = hit_chance if hit_chance is not None else 0.85
        else:
            self.base_hp = hp
            self.base_mp = mp
            self.base_hit_chance = hit_chance if hit_chance is not None else 0.85
        
        #HP Scaling
        self.hp_per_con = 5
        self.base_hp_regen = 0.02
        self.hp_regen_per_con = 0.01
        self._hp_regen_buffer = 0.0
        self.hp_regen_multiplier = 1.0

        #MP Scaling
        self.base_mp = 75
        self.mp_per_int = 5
        self.base_mp_regen = 0.05
        self.mp_regen_per_int = 0.01
        self._mp_regen_buffer = 0.0
        self.mp_regen_multiplier = 1.0

        self.armor = 0

        self.base_min_damage = 10
        self.base_max_damage = 30
        self.damage_per_str = 0.25

        self.base_crit_chance = 0.05
        self.crit_per_dex = 0.0001

        self.base_dodge_chance = 0.05
        self.dodge_per_dex = 0.0001

        self.base_attack_speed = attack_speed
        self.attack_speed = attack_speed
        self.hit_chance = self.base_hit_chance
        #self.min_damage = min_damage if min_damage is not None else strength
        #self.max_damage = max_damage if max_damage is not None else strength + 2

        self.recalc_stats()

        #ensure min/max damage exists (fallback to base values)
        if min_damage is None:
            self.min_damage = self.base_min_damage
        else:
            self.min_damage = min_damage

        if max_damage is None:
            self.max_damage = self.base_max_damage
        else:
            self.max_damage = max_damage

    @property
    def crit_chance(self):
        return self.base_crit_chance + (self.dexterity * self.crit_per_dex)
    
    @property
    def dodge_chance(self):
        return self.base_dodge_chance + (self.dexterity * self.dodge_per_dex)
        
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
        if self.hp >= self.max_hp:
            self._hp_regen_buffer = 0
            return 0

        regen = self.get_hp_regen()

        regen *= getattr(self, "hp_regen_multiplier", 1.0)

        self._hp_regen_buffer += regen

        if self._hp_regen_buffer >= 1:
            heal_amount = int(self._hp_regen_buffer)
            self._hp_regen_buffer -= heal_amount

            self.hp = min(self.max_hp, self.hp + heal_amount)

            return heal_amount
        
        return 0
    
    def regen_mp_tick(self):
        if self.mp >= self.max_mp:
            self._mp_regen_buffer = 0
            return 0
        
        regen = self.get_mp_regen()

        regen *= getattr(self, "mp_regen_multiplier", 1.0)

        self._mp_regen_buffer += regen

        if self._mp_regen_buffer >= 1:
            restore_amount = int(self._mp_regen_buffer)
            self._mp_regen_buffer -= restore_amount

            self.mp = min(self.max_mp, self.mp + restore_amount)

            return restore_amount
        
        return 0
    
    def get_damage_range(self):
        #If weapon has set custom min/max damage, use those
        if hasattr(self, "min_damage") and hasattr(self, "max_damage"):
            min_dmg = int(self.min_damage + self.strength * self.damage_per_str)
            max_dmg = int(self.max_damage + self.strength * self.damage_per_str)
        else:
            #fallback: base unarmed damage
            min_dmg = int(self.base_min_damage + self.strength * self.damage_per_str)
            max_dmg = int(self.base_max_damage + self.strength * self.damage_per_str)
        
        if max_dmg < min_dmg:
            max_dmg = min_dmg
        
        return min_dmg, max_dmg
    
    def reset_to_base(self):
        #reset all combat relevant stats to base values before gear is applied

        #armor
        self.armor = 0

        #damage range (weapon bonuses will overwrite these)
        self.min_damage = self.base_min_damage
        self.max_damage = self.base_max_damage

        #regen modifiers (base regen is handled in recalc_stats)
        self.hp_regen_multiplier = 1.0
        self.mp_regen_multiplier = 1.0

        #hit chance
        self.hit_chance = self.base_hit_chance
        self.attack_speed = self.base_attack_speed

    def compute_effective_stats(self, effects):
        eff = {
            "min_damage": self.min_damage,
            "max_damage": self.max_damage,
            "armor": self.armor,
            "attack_speed": self.attack_speed,
            "crit_chance": self.crit_chance,
            "hit_chance": self.hit_chance,
            "dodge_chance": self.dodge_chance,
        }

        for eff_data in effects:
            mods = eff_data.get("mods", {})
            for stat, val in mods.items():
                
                if stat == "damage_flat":
                    eff["min_damage"] += val
                    eff["max_damage"] += val

                elif stat == "attack_speed_pct":
                    eff["attack_speed"] *= (1 + val)

                elif stat == "armor_flat":
                    eff["armor"] += val

                elif stat == "armor_pct":
                    eff["armor"] *= (1 + val)

                elif stat == "damage_pct":
                    eff["min_damage"] *= (1 + val)
                    eff["max_damage"] *= (1 + val)

                elif stat == "crit_chance":
                    eff["crit_chance"] *= (1 + val)

                elif stat == "dodge_chance":
                    eff["dodge_chance"] *= (1 + val)

        return eff