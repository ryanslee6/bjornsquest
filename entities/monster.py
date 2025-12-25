from entities.stats import Stats
import pygame, json, os
import time
import random

_MONSTER_DATA_CACHE = None
_MONSTER_DATA_PATH = os.path.join("data", "monster_list.json")

def _load_monster_data():
    global _MONSTER_DATA_CACHE

    if _MONSTER_DATA_CACHE is not None:
        return _MONSTER_DATA_CACHE
    
    print(f"[MONSTER] Loading monster data from {_MONSTER_DATA_PATH}...")

    try:
        with open(_MONSTER_DATA_PATH, "r") as f:
            _MONSTER_DATA_CACHE = json.load(f)

        print(f"[MONSTER] ✅ Loaded {len(_MONSTER_DATA_CACHE)} monster types")
        return _MONSTER_DATA_CACHE
    
    except FileNotFoundError:
        print(f"[MONSTER] ❌ ERROR: {_MONSTER_DATA_PATH} not found!")
        _MONSTER_DATA_CACHE = {}
        return _MONSTER_DATA_CACHE
    
    except json.JSONDecodeError as e:
        print(f"[MONSTER] ❌ ERROR: Invalid JSON in {_MONSTER_DATA_PATH}: {e}")
        _MONSTER_DATA_CACHE = {}
        return _MONSTER_DATA_CACHE
        

class Monster:
    def __init__(self, name, level = 1):       
        self.name = name
        self.level = level
        self.active_effects = []
        self.current_shield = 0
        self.is_poison_protected = False

        #load data from cache
        monster_data = _load_monster_data()

        #get this monsters template
        template = monster_data.get(name)

        if not template:
            print(f"[MONSTER] ⚠️ WARNING: No data found for '{name}', using defaults")
            self._init_default_stats()
            return
        
        #initialize from template
        self._init_from_template(template, level)

    #fallback stats if monster not found in JSON
    def _init_default_stats(self):
        if Stats is None:
            print("[MONSTER] Error: Cannot create stats - Stats class not imported!")
            return
        
        self.stats = Stats(
            hp = 50,
            mp = 20,
            strength = 5,
            dexterity = 5,
            constitution = 5,
            intelligence = 5,
            min_damage = 3,
            max_damage = 8,
            dodge_chance = 0.05,
            attack_speed = 2.0,
            is_player = False
        )

        self.stats.armor = 2

        self.exp_reward = 10
        self.abilities = []
        self.sprite = None
        self.ability_cooldowns = {}
        self.passives = []

    #initialize monster from json template data
    def _init_from_template(self, template, level):
        if Stats is None:
            print("[MONSTER] Error: Cannot create stats - Stats class not imported!")
            self._init_default_stats()
            return

        #scale stats by level
        hp = template.get("base_hp", 50)
        mp = template.get("base_mp", 20)

        strength = template.get("strength", 5)
        dexterity = template.get("dexterity", 5)
        constitution = template.get("constitution", 5)
        intelligence = template.get("intelligence", 5)

        min_dmg = template.get("min_damage", 3)
        max_dmg = template.get("max_damage", 8)
        armor = template.get("armor", 2)

        dodge_chance = template.get("dodge_chance", 0.05)
        attack_speed = template.get("attack_speed", 2.0)

        #create Stats object using existing class
        self.stats = Stats(
            hp = hp,
            mp = mp,
            strength = strength,
            dexterity = dexterity,
            constitution = constitution,
            intelligence = intelligence,
            min_damage = min_dmg,
            max_damage = max_dmg,
            dodge_chance = dodge_chance,
            attack_speed = attack_speed,
            is_player = False
        )

        #armor
        self.stats.armor = armor

        #experience reward
        self.exp_reward = template.get("exp_reward", 10) + (level - 1) * 5

        #abilities
        self.abilities = template.get("abilities", [])
        self.ability_cooldowns = {ability: 0 for ability in self.abilities}
        self.passives = template.get("passives", [])

        #load sprite
        sprite_file = template.get("sprite")
        self.sprite = self._load_sprite(sprite_file) if sprite_file else None

    #load monster sprite image
    def _load_sprite(self, sprite_file):
        sprite_path = os.path.join("assets", "images", sprite_file)

        if os.path.exists(sprite_path):
            try:
                sprite = pygame.image.load(sprite_path).convert_alpha()

                max_width = 200
                max_height = 180

                #get current size
                width, height = sprite.get_size()

                #calculate scaling to fit within max bounds while preserving aspect ratio
                scale_x = max_width / width if width > max_width else 1
                scale_y = max_height / height if height > max_height else 1
                scale = min(scale_x, scale_y)

                #apply scaling if needed
                if scale < 1:
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    sprite = pygame.transform.scale(sprite, (new_width, new_height))
                                 
                print(f"[MONSTER] Loaded sprite: {sprite_file}({sprite.get_width()}x{sprite.get_height()})")
                return sprite
            except Exception as e:
                print(f"[MONSTER] ⚠️ Error loading sprite {sprite_file}: {e}")
                return None
        else:
            print(f"[MONSTER] ⚠️ Sprite not found: {sprite_path}")
            return None

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
        #compute effective stats with active effects
        eff = self.stats.compute_effective_stats(self.active_effects)

        #check for miss (5% base)
        if random.random() < 0.05:
            return 0, True, False, False
        
        #check if target dodges
        target_eff = target.stats.compute_effective_stats(
            getattr(target, "active_effects", [])
        )
        if random.random() < target_eff.get("dodge_chance", 0):
            return 0, False, False, True
        
        #calculate base damage
        base_damage = random.randint(
            int(eff["min_damage"]),
            int(eff["max_damage"])
        )

        #check for critical hit
        is_crit = random.random() < eff["crit_chance"]
        if is_crit:
            base_damage = int(base_damage * 2)

        #apply armor reduction
        armor = target_eff.get("armor", 0)
        damage_multiplier = 100 / (100 + armor)
        final_damage = int(base_damage * damage_multiplier)
        final_damage = max(1, final_damage) #minimum 1 damage

        #apply damage to target
        target.stats.hp = max(0, target.stats.hp - final_damage)

        final_damage = int(final_damage)

        if game is not None:
            self.apply_on_hit_passives(final_damage, target, game)

        return final_damage, False, is_crit, False
    
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

    #choose which ability to cast (if any)
    def choose_ability(self, game):
        #no abilities
        if not self.abilities:
            return None
        
        current_time = time.time()

        #filter abilities that are off cooldown
        available = [
            ability for ability in self.abilities
            if current_time >= self.ability_cooldowns.get(ability, 0)
        ]

        if not available:
            return None
        
        #30% chance to use an ability
        if random.random() < 0.3:
            return random.choice(available)
        
        return None
        
    def cast_ability(self, ability_name, target, game):
            ability = game.ability_data.get(ability_name)
            if not ability:
                print(f"[ERROR] Ability {ability_name} missing from abilities.json")
                return

            print(f"[ABILITY] {self.name} casts {ability_name}!")

            # Cooldown
            cooldown_duration = ability.get("cooldown", 5.0)
            self.ability_cooldowns[ability_name] = time.time() + cooldown_duration

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
