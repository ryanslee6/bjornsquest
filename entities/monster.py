from entities.stats import Stats
import pygame, json, os
import time
import random

class Monster:
    

    def __init__(self, name):       
        MONSTER_DATA_PATH = os.path.join("data", "monster_list.json")
        ABILITIES_PATH = os.path.join("data", "abilities.json")
        try:
            with open(ABILITIES_PATH, "r") as f:
                ABILITIES_DATA = json.load(f)
        except FileNotFoundError:
            ABILITIES_PATH = {}
            print("[WARN] abilities.json not found – monsters won’t cast abilities.")


        with open(MONSTER_DATA_PATH, "r") as f:
            MONSTER_DATA = json.load(f)

        data = MONSTER_DATA[name]   
        self.name = name
        self.level = data["level"]
        
        self.stats = Stats(
            hp = data["base_hp"],
            mp = data["base_mp"],
            strength = data["strength"],
            dexterity = data["dexterity"],
            constitution = data["constitution"],
            intelligence = data["intelligence"],
            min_damage = data.get("min_damage", 1),
            max_damage = data.get("max_damage", 3),
            dodge_chance = data.get("dodge_chance", 0.0),
            attack_speed = data.get("attack_speed", 1.0),
            hit_chance = data.get("hit_chance", 0.90),
            is_player = False
        )
        
        self.abilities = data.get("abilities", [])
        self.ability_cooldowns = {ability_id: 0.0 for ability_id in self.abilities}

        self.passives = data.get("passives", [])

        self.current_shield = 0
        self.max_shield = 0

        #passive skill debug
        #print(f"[DEBUG] Monster {self.name} passives loaded:", self.passives)

    

        self.exp_reward = data["exp_reward"]
        self.sprite_path = os.path.join("assets", "images", data["sprite"])
        self.sprite = pygame.image.load(self.sprite_path).convert_alpha()
        
        scale = data.get("scale", 1.0)

        if scale != 1.0:
            w = int(self.sprite.get_width() * scale)
            h = int(self.sprite.get_height() * scale)
            self.sprite = pygame.transform.scale(self.sprite, (w, h))
        
        self.alive = True

        self.active_effects = []

        
        
        #try:
        #    self.sprite = pygame.image.load("assets/images/goblin1.png").convert_alpha()
        #except:
        #    self.sprite = None
        #    print("⚠️ Goblin sprite missing — using placeholder box.")

        #if self.sprite:
        #    self.sprite = pygame.transform.scale(self.sprite, (180, 160))


    def is_alive(self):
        return self.stats.hp > 0
    
    def take_damage(self, damage):
        #apply damage to this monster, checking shield first.
        #Returns: (actual_hp_damage, shield_damage, shield_broke)
        if damage <= 0:
            return 0, 0, False
        
        shield_broke = False
        shield_damage = 0
        hp_damage = 0

        #If monster has a shield, it absorbs damage first
        if self.current_shield > 0:

            #print(f"[SHIELD] {self.name} has {self.current_shield} shield, taking {damage} damage")

            if damage <= self.current_shield:
                #shield absorbs all damage
                shield_damage = damage
                self.current_shield -= damage
                hp_damage = 0
                #print(f"[SHIELD] Shield absorbed all damage! Shield remaining: {self.current_shield}")
            else:
                #shield breaks, overflow goes to HP
                shield_damage = self.current_shield
                hp_damage = damage - self.current_shield
                self.current_shield = 0
                shield_broke = True
                #print(f"[SHIELD] Shield broke! {hp_damage} damage to HP")

        else:
            #no shield, damage goes straight to hp
            hp_damage = damage

        self.stats.hp = max(0, self.stats.hp - hp_damage)

        return hp_damage, shield_damage, shield_broke
    
    def attack(self, target, game = None):
        import random

        
        # -----------------------------------------------
        # 1) TRY TO CAST AN ABILITY IF AVAILABLE
        # -----------------------------------------------

        if self.abilities and game:
            ability_name = self.choose_ability(game)

            if ability_name == "enrage":
                ability_name = None
                
            if ability_name:
                self.cast_ability(ability_name, target, game)
                return 0, False, False, False
        
        #miss check
        is_miss = random.random() > self.stats.hit_chance
        if is_miss:
            return 0, True, False, False

        #dodge check
        is_dodged = random.random() < target.stats.dodge_chance
        if is_dodged:
            return 0, False, False, True
        
        if getattr(self, "is_stunned", False):
            return 0, False, False, False
        
        eff = self.stats.compute_effective_stats(self.active_effects)
        target_eff = target.stats.compute_effective_stats(target.active_effects)

        min_dmg = eff["min_damage"]
        max_dmg = eff["max_damage"]
        armor = target_eff["armor"]
        
        #base damage
        min_dmg, max_dmg = self.stats.get_damage_range()
        base_damage = random.randint(min_dmg, max_dmg)

        #crit check
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:    
            base_damage *= 2
        

        #armor reduction
        armor = target.stats.armor
        if armor > 0:
            damage_reduction = armor / (armor + 400)
            final_damage = int(base_damage * (1 - damage_reduction))
        else:
            final_damage = base_damage

        final_damage = max(1, final_damage)
        
        hp_dmg, shield_dmg, shield_broke = target.take_damage(final_damage)

        self.apply_on_hit_passives(final_damage, target, game)

        return final_damage, is_miss, is_crit, is_dodged
    
    def add_status_effect(self, name, duration, icon = None, color = (200, 200, 200)):
        if not hasattr(self, "active_effects"):
            self.active_effects = []

        self.active_effects.append({
            "name": name,
            "expires": time.time() + duration,
            "icon": icon,
            "color": color
        })

    def remove_expired_effects(self, game = None):
        now = time.time()
        new_list = []

        for effect in self.active_effects:
            if now < effect["expires_at"]:
                new_list.append(effect)
            else:

                if effect.get("raw_key") == "bone_shield":
                    #clear the shield when bone shield expires
                    self.current_shield = 0
                    self.max_shield = 0

                    if game and hasattr(game, 'combat'):
                        game.combat.add_log(f"{self.name}'s Bone Shield fades away.")

                if "revert" in effect:
                    effect["revert"](self)

        self.active_effects = new_list

    def choose_ability(self, game):
        #no abilities
        if not self.abilities:
            return None
        
        ability_data = game.ability_data
        now = time.time()

        for ability_name in self.abilities:
            ability = ability_data.get(ability_name)
            if not ability:
                continue

            cd = ability.get("cooldown", 5)
            chance = ability.get("chance", 1.0)
            last_cast = self.ability_cooldowns.get(ability_name, -9999)

            if now - last_cast < cd:
                continue
            
            if random.random() <= chance:
                return ability_name
            
        return None
        
    def cast_ability(self, ability_name, target, game):
            ability = game.ability_data.get(ability_name)
            if not ability:
                print(f"[ERROR] Ability {ability_name} missing from abilities.json")
                return

            print(f"[ABILITY] {self.name} casts {ability_name}!")

            # Cooldown
            self.ability_cooldowns[ability_name] = time.time()

            duration = ability.get("duration", 5)
            effects = ability.get("effects", {})
            


            # target selection
            target_obj = self if ability.get("type") == "self_buff" else target

            # Build unified modifier dict for Stats.compute_effective_stats()
            mods = {}

            # --- TRANSLATION LAYER FOR YOUR JSON FORMAT ---
            for eff in effects:
                stat = eff["stat"]
                val = eff["value"]

                if stat in ["damage_flat", "armor_flat"]:
                    mods[stat] = mods.get(stat, 0) + val

                elif stat in ["damage_pct", "attack_speed_pct", "armor_pct"]:
                    mods[stat] = mods.get(stat, 0) + val

                elif stat == "crit_pct":
                    mods["crit_chance"] = mods.get("crit_chance", 0) + val

                elif stat == "dodge_pct":
                    mods["dodge_chance"] = mods.get("dodge_chance", 0) + val

            now = time.time()
            expires_at = now + duration
            
            tooltip_lines = []

            if "damage_flat" in mods:
                tooltip_lines.append(f"+{mods['damage_flat']} Damage")

            if "attack_speed_pct" in mods:
                pct = mods["attack_speed_pct"] * 100
                tooltip_lines.append(f"{pct:+.0f}% Attack Speed")

            if "armor_flat" in mods:
                tooltip_lines.append(f"{mods['armor_flat']:+} Armor")

            if "armor_pct" in mods:
                tooltip_lines.append(f"+{int(mods['armor_pct'] * 100)}% Armor")

            if "crit_chance" in mods:
                tooltip_lines.append(f"+{int(mods['crit_chance'] * 100)}% Crit Chance")

            if "dodge_chance" in mods:
                tooltip_lines.append(f"+{int(mods['dodge_chance'] * 100)}% Dodge Chance")

            display_name = ability.get("name", ability_name)
            entry = {
                "name": display_name,
                "raw_key": ability_name,
                "mods": mods,
                "expires_at": expires_at,
                "expires": expires_at,
                "duration": duration,
                "source": ability_name,
                "color": (80, 180, 255),
                "log_text": ability.get("log_text", ability_name),
                "tooltip": tooltip_lines
            }


            # ----------------------------------------------------
            # Ability Icon handing
            # ----------------------------------------------------
            icon_name = ability.get("icon")
            if icon_name:
                #strip .png extension to match buff_icons key format
                entry["icon"] = icon_name.replace(".png", "")

            # ----------------------------------------------------
            # SHIELD HANDLING (Bone Shield, etc.)
            # ----------------------------------------------------
            if "shield_amount" in ability:
                shield_value = ability["shield_amount"]
                target_obj.current_shield = shield_value
                target_obj.max_shield = shield_value
                game.combat.add_log(f"{target_obj.name} gains a {shield_value} HP Shield!")

                #add shield floating text
                game.combat.add_floating_text(
                    f"Shield+{shield_value}",
                    0, 0,
                    text_type = "buff",
                    target = "enemy"
                )

            if "stun_duration" in ability and target_obj is game.player:
                stun_dur = ability["stun_duration"]
                target_obj.is_stunned = True
                target_obj.stun_expires_at = now + stun_dur


            #only add UI entry if not a poison ability
            if not ability.get("poison"):
                target_obj.active_effects.append(entry)

            # optional combat log
            game.combat.add_log(entry["log_text"])

            # ----------------------------------------------------
            # POISON HANDLING
            # ----------------------------------------------------
            if ability.get("poison"):          
                    
                dmg = ability.get("tick_damage", 100)
                reduced = ability.get("reduced_tick_damage", 10)
                interval = ability.get("tick_interval", 1.0)
                dur = ability.get("duration", 8)
                    
                if not game.combat.has_active_poison(target_obj):
                    #call combat systems add poison effect
                    game.combat.add_poison_effect(
                        target_obj,
                        damage = dmg,
                        reduced_damage = reduced,
                        interval = interval,
                        duration = dur
                    )

                else:
                    game.combat.refresh_poison(target_obj, dur)

                #floating text
                game.combat.add_floating_text(
                    "Poisoned!",
                    0, 0,
                    text_type = "debuff",
                    target = "player"
                )

    def has_passive(self, name: str) -> bool:
        return any(p.lower() == name.lower() for p in self.passives)
    
    def apply_on_hit_passives(self, damage, target, game):
        if damage <= 0 or game is None:
            return
        
        #life leech
        if self.has_passive("life_leech"):
            ability = game.ability_data.get("life_leech", {})
            pct = ability.get("leech_pct", 0)

            heal_amount = int(damage * pct)

            if heal_amount > 0:
                self.stats.hp = min(self.stats.max_hp, self.stats.hp + heal_amount)

                game.combat.add_log(f"{self.name} drains you for {heal_amount} HP!")

                icon = game.buff_icons.get("life_leech")

                game.combat.add_floating_text(
                    f"+{heal_amount}",
                    0, 0,
                    text_type = "heal",
                    target = "enemy",
                    icon = icon
                )
