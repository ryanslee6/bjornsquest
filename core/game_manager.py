import pygame
from settings import *
import os
from entities.player import Player
from entities.monster import Monster
from systems.combat import CombatManager
from systems.loot_system import LootSystem
from core.ui_mgr import *
from core.item_mgr import ItemManager
from core.ui_mgr import SpellbookWindow
from core.ui_mgr import CharacterWindow
from core.ui_mgr import LevelUpWindow
from core.ability_manager import AbilityManager
import time
import math
from pygame import gfxdraw
import json
from systems.bounty_system import BountyBoard, BountyTier
from systems.bounty_ui import BountyBoardUI
from core.save_system import SaveSystem
from core.save_select_window import SaveSelectWindow


class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.float_font = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 24)
        self.state = "title"
        self.title_image = self.load_image("bq_titlescreen.png")
        self.home_image = self.load_image("bq_campsite.png")
        
        #load monster select backgrounds (with fallback system)
        self.monster_select_backgrounds = {}
        #try to load page-specific backgrounds, fall back to default
        for i in range(10): #supports (10 for now) pages
            bg_name = f"mon_bg{i + 1}.png"
            bg = self.load_image(bg_name)
            if bg:
                self.monster_select_backgrounds[i] = bg

        #if no page-specific background exists, use default for all pages
        if not self.monster_select_backgrounds:
            default_bg = self.load_image("mon_bg1.png")
            if default_bg:
                #use efault for pages 0-9
                for i in range(10):
                    self.monster_select_backgrounds[i] = default_bg

        self.loot_system = LootSystem()
        self.items = ItemManager()
        self.inventory_window = InventoryWindow(self)
        self.levelup_window = LevelUpWindow(self)
        self.enhancement_confirmation = EnhancementConfirmationWindow(self)
        self.enhancement_result_window = None
        self.show_inventory = False
        self.show_spell_bar = False
        self.spell_buttons = {}
        self.buff_icons = {}
        self.vendor_window = VendorWindow(self)
        self.character_window = CharacterWindow(self)
        self.combat_log_offset = 0
        self.combat_log_at_bottom = True
        self.fps_font = pygame.font.Font(None, 30)
        self.ability_manager = AbilityManager()
        ABILITIES_PATH = os.path.join("data", "abilities.json")
        with open(ABILITIES_PATH, "r") as f:
            self.ability_data = json.load(f)

        self.load_ability_icons()
        
    def load_ability_icons(self):
        #load all ability icons defined in abilities.json
        abilities_path = os.path.join("data", "abilities.json")

        try:
            with open(abilities_path, "r") as f:
                abilities = json.load(f)

            for ability_id, ability_data in abilities.items():
                icon_filename = ability_data.get("icon")
                if icon_filename:
                    icon_path = os.path.join("assets", "images", icon_filename)
                    if os.path.exists(icon_path):
                        img = pygame.image.load(icon_path). convert_alpha()
                        img = pygame.transform.scale(img, (26, 26))
                        self.buff_icons[ability_id] = img
                    else:
                        print(f"[WARNING] Icon missing for {ability_id}: {icon_path}")
        except FileNotFoundError:
            print("[WARNING] abilities.json not found - no abilitiy icons loaded")
        
        def load_icon(name, filename):
            path = os.path.join("assets", "images", filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (26, 26))
                self.buff_icons[name.lower()] = img
            else:
                print(f"[WARNING] Buff icon missing: {path}")
        
        load_icon("burn", "burn_debuff1.png")
        load_icon("poison", "poison_debuff1.png")      

        self.combat_bg = pygame.image.load("assets/images/combat_bg1.png").convert_alpha()
        self.combat_bg = pygame.transform.scale(self.combat_bg, (SCREEN_WIDTH, SCREEN_HEIGHT - 52))
        
        self.ui_border = pygame.image.load("assets/images/combat_border.png").convert_alpha()
        self.ui_border = pygame.transform.scale(self.ui_border, (SCREEN_WIDTH, 30))

        sprite_path = os.path.join("assets", "images", "bjorn_char_1.png")
        
        
        if os.path.exists(sprite_path):
            self.player_sprite_sheet1 = pygame.image.load(sprite_path).convert_alpha()
        else:
            print(f"[Warning] Missing sprite sheet: {sprite_path}")
            self.player_sprite_sheet1 = pygame.Surface((64, 64))
            self.player_sprite_sheet1.fill((255, 0, 255))


        self.current_monster = None
        self.monster_defeated = False
        self.respawn_time = 0

        self.player = Player(item_manager = self.items)
        self.player.game = self
        self.combat = CombatManager(self.player, self.current_monster, self.loot_system, self)
        self.combat.auto_callback = lambda: self.auto_combat_enabled

        #bounty system
        self.bounty_board = BountyBoard()
        self.bounty_ui = BountyBoardUI(
            self.bounty_board,
            x = 50,
            y = 120,
            width = 700,
            height = 480
        )

        #save system
        self.save_system = SaveSystem()
        self.save_select_window = SaveSelectWindow(self, self.save_system)

        #autosave
        self.autosave_timer = 0
        self.autosave_interval = 300.0 #5 minutes in seconds
    
        self.spellbook_window = SpellbookWindow(
            self.player,
            self.combat.spellbook,
            self.assign_spell_to_slot
        )
        self.spell_slots = {}
        
        

        self.auto_combat_enabled = False

        if self.combat:
            self.combat.auto_combat_enabled = self.auto_combat_enabled

        button_width = 100
        button_height = 40
        bottom_margin = 15
        gap = 8
        row_gap = 8

        buttons = ["Fight", "Gather", "Craft", "Bounties", "Inventory", "Shop", "Save"]
        
        #calculate max buttons per row based on screen width
        side_margin = 20
        available_width = SCREEN_WIDTH - (side_margin * 2)
        max_buttons_per_row = (available_width + gap) // (button_width + gap)

        #split buttons intow rows (1 or 2 rows)
        num_buttons = len(buttons)
        if num_buttons <= max_buttons_per_row:
            #all buttons fit in one row
            buttons_per_row = [num_buttons]
        else:
            #needs 2 rows - balance evenly
            buttons_row1 = (num_buttons + 1) // 2
            buttons_row2 = num_buttons - buttons_row1
            buttons_per_row = [buttons_row1, buttons_row2]

        #create button rects
        self.buttons = {}
        button_index = 0
        
        for row_num, buttons_in_row in enumerate(buttons_per_row):
            #calculate this rows width and center it
            row_width = buttons_in_row * button_width + (buttons_in_row - 1) * gap
            start_x = (SCREEN_WIDTH - row_width) // 2

            #calculate y position
            rows_below = len(buttons_per_row) - row_num - 1
            y_pos = SCREEN_HEIGHT - bottom_margin - button_height - (rows_below * (button_height + row_gap))

            #create buttons for this row
            for col in range(buttons_in_row):
                button_text = buttons[button_index]
                x = start_x + col * (button_width + gap)
                self.buttons[button_text] = pygame.Rect(x, y_pos, button_width, button_height)
                button_index += 1

        self.current_action = None

        self.monster_pages = [
            {
                "monsters": ["Goblin", "Bat", "Skeleton", "Wolf"],
                "boss": "Svartvefnir"
            },
            {
                "monsters": ["Zombie"]
            }
        ]
        self.current_monster_page = 0

        self.start_button = pygame.Rect(100, 650, 200, 50)
        self.load_button = pygame.Rect(500, 650, 200, 50)

    def load_image(self, filename):
        path = os.path.join("assets", "images", filename)
        if os.path.exists(path):
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            return image
        else:
            print(f"[Warning] Missing image: {path}")
            surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            surface.fill(BLACK)
            return surface

    def handle_event(self, event):
        #save select window (highest priority)
        if self.save_select_window.visible:
            if self.save_select_window.handle_event(event):
                return

        # --- GLOBAL MODAL WINDOWS / OVERLAYS FIRST ---
        
        # Inventory window captures all mouse input when open
        if self.show_inventory and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if self._handle_inventory_events(event):
                return
            
        if self.bounty_ui.is_visible and event.type == pygame.MOUSEBUTTONDOWN:
            if self._handle_bounty_events(event):
                return
            
        #keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                self.character_window.toggle()

        #character window click handling
        if self.character_window.visible and event.type == pygame.MOUSEBUTTONDOWN:
            if self._handle_character_window_events(event):
                return
            
        #Level up window click handling
        if self.levelup_window.visible and event.type == pygame.MOUSEBUTTONDOWN:
            if self._handle_levelup_events(event):
                return
            
        #State specific handling

        if self.state == "vendor":
            if self._handle_vendor_events(event):
                return
            
        elif self.state == "combat":
            if self._handle_combat_events(event):
                return
            
        elif self.state == "title":
            if self._handle_title_events(event):
                return
        
        elif self.state == "home":
            if self._handle_home_events(event):
                return
            
        elif self.state == "creature_select":
            if self._handle_creature_select_events(event):
                return
            
        #spellbook window (global overlay)

        if self.spellbook_window.visible and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.spellbook_window.handle_click(event.pos):
                    return

    def _handle_bounty_events(self, event):
        #handle clicks on the bounty board ui
        if event.button != 1:
            return False
        
        #click outside to close
        if not self.bounty_ui.rect.collidepoint(event.pos):
            self.bounty_ui.is_visible = False
            print("[UI] Closed bounty board")
            return True
        
        #handle ui button clicks
        action = self.bounty_ui.handle_click(event.pos)

        if action:
            if action["action"] == "claim":
                #claim completed bounty
                reward = self.bounty_board.claim_bounty(action["bounty_id"])

                if reward:
                    self.player.gain_exp(reward.experience)
                    self.player.gold += reward.gold

                    #add bounty points to player
                    if not hasattr(self.player, 'bounty_points'):
                        self.player.bounty_points = 0
                    self.player.bounty_points += reward.bounty_points

                    print(f"[BOUNTY] Claimed: {reward}")
                    if hasattr(self, 'combat'):
                        self.combat.add_log(f"Bounty claimed! +{reward.experience} XP, +{reward.gold} Gold")
        
                return True
            
            elif action["action"] == "add":
                #add new bounty
                bounty = self.bounty_board.add_bounty(action["tier"])
                print(f"[BOUNTY] Added {action['tier'].name} bounty: {bounty}")
                return True
        
        return True

    def _handle_inventory_events(self, event):
        #enhancement confirmation takes priority
        if self.enhancement_confirmation.visible and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: #left click
                if self.enhancement_confirmation.click(event.pos):
                    return True

        #mouse wheel scrolling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: #scroll up
                self.inventory_window.scroll_offset = max(0, self.inventory_window.scroll_offset - self.inventory_window.scroll_speed)
                return True
            
            if event.button == 5: #scroll down
                self.inventory_window.scroll_offset = min(self.inventory_window.max_scroll, self.inventory_window.scroll_offset + self.inventory_window.scroll_speed)
                return True
            
            #left click down - start drag or handle click
            if event.button == 1:
                #check if click is outside (close inventory)
                if self.inventory_window.click_outside(event.pos):
                    self.show_inventory = False
                    return True
                
                #click inside - start drag
                self.inventory_window.click(event.pos, event.button)
                return True

            #right click uses item
            if event.button == 3:
                self.inventory_window.click(event.pos, event.button)
                return True
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: #left click released
                if self.inventory_window.dragging_item:
                    self.inventory_window.release_drag(event.pos)
                    return True
        
        return True

    def _handle_character_window_events(self, event):
        if event.button == 1:
            if self.character_window.handle_click(event.pos):
                return True
        return False
    
    def _handle_levelup_events(self, event):
        if event.button == 1:

            #check if click is inside window
            window_rect = pygame.Rect(self.levelup_window.x, self.levelup_window.y, self.levelup_window.width, self.levelup_window.height)

            if window_rect.collidepoint(event.pos):
                #click inside window - let the window handle it
                self.levelup_window.handle_click(event.pos)
            else:
                #click outside window - close it
                self.levelup_window.close()

            return True
        return False
    
    def _handle_vendor_events(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False
        
        #mouse wheel scrolling
        if event.button == 4: #wheel up
            self.vendor_window.scroll_offset = max(0, self.vendor_window.scroll_offset - self.vendor_window.scroll_speed)
            return True
        
        if event.button == 5: #wheel down
            self.vendor_window.scroll_offset = min(self.vendor_window.max_scroll, self.vendor_window.scroll_offset + self.vendor_window.scroll_speed)
            return True
        
        #left clicks
        if event.button == 1:
            if self.vendor_window.handle_click(event.pos):
                return True
            
            if self.vendor_window and self.vendor_window.is_click_outside(event.pos):
                print("[UI] Exiting vnedor screen")
                self.state = "home"
                return True
            
        return False
    
    def _handle_combat_events(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False
        
        #combat log mouse wheel scrolling
        if event.button in (4, 5):
            self._handle_combat_log_scroll(event.button)
            return True
        
        #left click in combat ui
        if event.button == 1:
            if self._handle_combat_click(event.pos):
                return True
            
        return False
    
    def _handle_combat_log_scroll(self, button):
        if button == 4: #scroll up
            self.combat.log_scroll = max(self.combat.log_scroll - 1, 0)
            self.combat.user_is_scrolling = (self.combat.log_scroll < self.combat.max_scroll)

        elif button == 5: #scroll down
            total_lines = len(self.combat.wrapped_cache)
            max_visible = self.combat.max_visible_lines
            self.combat.max_scroll = max(0, total_lines - max_visible)

            self.combat.log_scroll = min(self.combat.log_scroll + 1, self.combat.max_scroll)

            if self.combat.log_scroll >= self.combat.max_scroll:
                self.combat.user_is_scrolling = False
            else:
                self.combat.user_is_scrolling = True

    def _handle_combat_click(self, pos):
        #check for level up button
        if hasattr(self, 'levelup_button_rect') and self.levelup_button_rect.collidepoint(pos):
            if hasattr(self, 'levelup_window'):
                self.levelup_window.open()
            return True
        
        
        #main combat buttons ("Attack", "Auto", "Spells", "Use Item", "Inventory", "Home")
        for label, rect in self.combat_buttons.items():
            if rect.collidepoint(pos):
                if label == "Attack":
                    self.combat.player_initiated = True
                    return True
                
                elif label == "Auto":
                    if not self.player.auto_combat_unlocked:
                        print("Auto Combat isn't unlocked yet!")
                        return True
                    
                    self.auto_combat_enabled = not self.auto_combat_enabled
                    print(f"Auto Combat is now {'ON' if self.auto_combat_enabled else 'OFF'}")

                    if self.auto_combat_enabled and not self.combat.player_initiated:
                        self.combat.player_initiated = True

                    return True
            
                elif label == "Spells":
                    self.show_spell_bar = not self.show_spell_bar
                    return True
                
                elif label == "Use Item":
                    #nothing yet
                    return True
                
                elif label == "Inventory":
                    self.show_inventory = not self.show_inventory
                    return True
                
                elif label == "Home":
                    self.state = "home"
                    print("[UI] Returning to home screen")
                    return True
        
        #Spellbar clicks
        if getattr(self, "show_spell_bar", False):
            for label, rect in self.spell_buttons.items():
                if rect.collidepoint(pos):

                    if label == "Spellbook":
                        self.spellbook_window.toggle()
                        return True
                    
                    if label.startswith("Slot"):
                        slot_index = int(label.split(" ")[1])
                        self.selected_spell_slot = slot_index

                        if self.spellbook_window.visible:
                            self.spellbook_window.selected_slot = slot_index
                            print(f"[UI] Selected slot {slot_index} for assignment")
                        else:
                            spell = self.spell_slots.get(slot_index)
                            if spell:
                                self.combat.cast_spell(spell.name)

                        return True
        return False
    
    def _handle_title_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_button.collidepoint(event.pos):
                print("New Game Clicked")
                self.state = "home"
                return True
            
            if self.load_button.collidepoint(event.pos):
                print("Load Game Clicked")
                #open save selection window
                self.save_select_window.open()
                return True
        return False
    
    def _handle_home_events(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        
        for text, rect in self.buttons.items():
            if rect.collidepoint(event.pos):

                if text == "Fight":
                    self.state = "creature_select"
                    return True
                
                elif text == "Bounties":
                    self.bounty_ui.toggle_visibility()
                    print("[UI] Toggling Bounty Board")
                    return True
                
                elif text == "Inventory":
                    self.show_inventory = not self.show_inventory
                    if self.show_inventory:
                        self.inventory_window.mark_dirty()
                    print("[UI] Toggling Inventory Window")
                    return True
                
                elif text == "Shop":
                    self.state = "vendor"
                    print("[UI] Entering vendor screen")
                    return True

                elif text == "Save":
                    game_state = {
                        'monster_page': self.current_monster_page,
                        'current_monster': self.current_monster.name if self.current_monster else None,
                    }

                    save_path = self.save_system.save_game(self.player, game_state)

                    if save_path:
                        print("[UI] ✅ Game saved successfully!")
                    else:
                        print("[UI] ❌ Save failed!")
                    
                    return True

        return False
    
    def _handle_creature_select_events(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        
        #previous page button
        if hasattr(self, "prev_page_button") and self.prev_page_button:
            if self.prev_page_button.collidepoint(event.pos):
                if self.current_monster_page > 0:
                    self.current_monster_page -= 1
                    print(f"[UI] Switched to monster page {self.current_monster_page}")
                return True
        
        #next page button
        if hasattr(self, "next_page_button") and self.next_page_button:
            if self.next_page_button.collidepoint(event.pos):
                if self.current_monster_page < len(self.monster_pages) - 1:
                    self.current_monster_page += 1
                    print(f"[UI] Switched to monster page {self.current_monster_page}")
                return True

        #return to camp button
        if hasattr(self, "return_button") and self.return_button.collidepoint(event.pos):
            self.state = "home"
            return True
        
        #monster selection buttons
        for name, rect in self.creature_buttons.items():
            if rect.collidepoint(event.pos):
                print(f"{name} selected!")
               
                self.current_monster = Monster(name)
                self.combat = CombatManager(self.player, self.current_monster, self.loot_system, self)
                self.state = "combat"

                return True
        return False

    def show_enhancement_confirmation(self, scroll, item):
        #show the enhancement confirmation dialog
        self.enhancement_confirmation.show(scroll, item)

    def show_enhancement_result(self, result):
        #show results of enhancement attempts
        print(f"[ENHANCE RESULT] {result['message']}")
        if result.get('item_destroyed'):
            print('[ENHANCE RESULT] Item was Destroyed!')

    def update(self, dt):
        #self.combat.update_burns(dt) #moved down to bottom with rest of updates
        if self.state == "combat":
            self.combat.update(dt)
            self.player.stats.hp_regen_multiplier = 0.1
            self.player.stats.mp_regen_multiplier = 0.1
        else:
            self.player.stats.hp_regen_multiplier = 1.0
            self.player.stats.mp_regen_multiplier = 1.0

        hp_heal = self.player.stats.regen_tick()
        if hp_heal > 0:
                #floating heal text on regen
                self.combat.add_floating_text(
                    f"+{hp_heal}",
                    0, 0,
                    text_type = "heal",
                    target = "player"
                )
        mp_restore = self.player.stats.regen_mp_tick()
        if mp_restore > 0:
            self.combat.add_floating_text(
                f"+{mp_restore} MP",
                0, 0,
                text_type = "mana",
                target = "player"
            )
                 
        
        if self.state == "combat" and self.combat:            
            if self.combat.update(dt):
                print(self.combat.combat_log[-1])

            if not self.combat.combat_active:
                print("✅ Combat ended! Returning to creature select.")
                self.state = "creature_select"

            if self.combat is not None:
                self.combat.auto_combat_enabled = self.auto_combat_enabled


        if hasattr(self, "combat"):
            self.combat.update_floating_text(dt)

        self.combat.update_projectiles(dt)
        self.combat.update_burns(dt)
        self.combat.update_poisons(dt)
        self.combat.update_heal_spell_particles(dt)
        #print("[DEBUG] calling update_battlecry_waves, waves:", len(self.combat.battlecry_waves))
        self.combat.update_battlecry_waves(dt)

        self.player.remove_expired_effects()
        if self.current_monster:
            #print("[DEBUG ACTIVE EFFECTS MONSTER] =", self.current_monster.active_effects)
            self.current_monster.remove_expired_effects()
            

        
        # ==========================================
        # 1) Handle Monster Death
        # ==========================================
        if self.current_monster and not self.current_monster.is_alive() and not self.monster_defeated:
            self.monster_defeated = True

            self.combat.add_log(f"{self.current_monster.name} was defeated!")

            exp = self.current_monster.exp_reward
            drops = self.loot_system.generate_loot(self.current_monster.name)
            print("You found:", drops)

            for drop in drops:
                item_name = drop["item"]
                qty = drop["quantity"]

                if item_name.lower() == "gold coins":
                    self.player.gold += qty
                    self.loot_log.append(f"+{qty} Gold Coins")
                else:
                    self.player.add_item(item_name, qty)
                    self.combat.loot_log.append(f"+{qty} {item_name}")

            self.combat.loot_log = self.combat.loot_log[-5:]
            self.player.gain_exp(exp)

            completed_bounties = self.bounty_board.on_monster_killed(self.current_monster.name)
            if completed_bounties:
                for bounty in completed_bounties:
                    self.combat.add_log(f"✓ Bounty completed: {bounty.monster_name}!")
                    print(f"[BOUNTY] Completed: {bounty}")

            # clear old debuffs
            self.current_monster.active_effects = []

            #clear enrage visual effects
            self.combat.enrage_flash_alpha = 0
            if hasattr(self.current_monster, 'is_enraged'):
                self.current_monster.is_enraged = False

            # clear lingering burn timers
            self.combat.active_burns = [
                b for b in self.combat.active_burns
                if b["target"].is_alive()
            ]

            self.respawn_time = pygame.time.get_ticks() + 1000
            return  # IMPORTANT


        # ==========================================
        # 2) Handle Monster Respawn
        # ==========================================
        #print("[RESPAWN CHECK] monster_defeated =", self.monster_defeated,
        #    " now=", pygame.time.get_ticks(), 
        #    " respawn_at=", self.respawn_time)
        if self.monster_defeated and pygame.time.get_ticks() > self.respawn_time:
            old_name = self.current_monster.name
            new_monster = Monster(old_name)
            new_monster.active_effects = []

            #clear any lingering enrage effects from previous monster
            self.combat.enrage_flash_alpha = 0

            self.current_monster = new_monster
            self.combat.current_monster = new_monster

            self.player_initiated = False
            self.combat.player_initiated = False
            self.combat_active = True
            self.combat.combat_active = True
            self.combat.last_player_attack = pygame.time.get_ticks()

            self.monster_defeated = False

        # ============ AUTOSAVE SYSTEM ============
        #only autosave during actual gameplay
        if self.state in ["home" , "combat", "creature_select"]:
            self.autosave_timer += dt

            if self.autosave_timer >= self.autosave_interval:
                self.autosave_timer = 0

                game_state = {
                    'monster_page': self.current_monster_page,
                    'current_monster': self.current_monster.name if self.current_monster else None,
                }

                autosave_path = self.save_system.autosave(self.player, game_state)

                if autosave_path:
                    print("[AUTOSAVE] ✅ Game autosaved")

    def draw(self):
        if self.state == "title":
            self.draw_title()
        
        elif self.state == "home":
            self.draw_home()
        
        elif self.state == "vendor":
            self.draw_home()
            self.vendor_window.draw(self.screen)
        
        elif self.state == "creature_select":
            self.draw_creature_select()
        
        elif self.state == "combat":
            self.draw_combat_screen()

        if self.character_window.visible:
            self.character_window.draw(self.screen)

        if self.levelup_window.visible:
            self.levelup_window.draw(self.screen)

        fps = int(self.clock.get_fps())
        fps_color = (0, 255, 0) if fps >= 55 else (255, 215, 0) if fps >= 45 else (255, 0, 0)

        fps_text = self.fps_font.render(f"FPS: {fps}", True, fps_color)
        self.screen.blit(fps_text, (10, 60))

        #save select window
        if self.save_select_window.visible:
            self.save_select_window.draw(self.screen)

    def draw_title(self):
        self.screen.blit(self.title_image, (0, 0))
        pygame.draw.rect(self.screen, PURPLE, self.start_button)
        label = self.font.render("New Game", True, WHITE)
        self.screen.blit(label, (
            self.start_button.x + self.start_button.width // 2 - label.get_width() // 2,
            self.start_button.y + self.start_button.height // 2 - label.get_height() // 2))
        
        pygame.draw.rect(self.screen, PURPLE, self.load_button)
        label = self.font.render("Load Game", True, WHITE)
        self.screen.blit(label, (
            self.load_button.x + self.load_button.width // 2 - label.get_width() // 2,
            self.load_button.y + self.load_button.height // 2 - label.get_height() // 2))

    def draw_home(self):
        self.screen.blit(self.home_image, (0, 0))
        title = self.font.render("Bjorns Quest", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        for text, rect in self.buttons.items():
            pygame.draw.rect(self.screen, PURPLE if self.current_action == text else LIGHT_GRAY, rect)
            label = self.font_small.render(text, True, WHITE)
            self.screen.blit(label, (rect.x + rect.width // 2 - label.get_width() // 2,
                                     rect.y + rect.height // 2 - label.get_height() // 2))
            
        if self.show_inventory or self.state == "vendor":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))

        if self.state == "vendor" and hasattr(self, "vendor_window"):
            self.vendor_window.draw(self.screen)

        if self.show_inventory:
            self.inventory_window.draw(self.screen)

        #draw enhancement confirmation
        if self.enhancement_confirmation.visible:
            self.enhancement_confirmation.draw(self.screen)

        if self.bounty_ui.is_visible:
            self.bounty_ui.draw(self.screen)


    def draw_creature_select(self):
        #draw background (page-specific or fallback)
        bg = self.monster_select_backgrounds.get(self.current_monster_page)
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill(BLACK) #ultimate fallback
        
        title = self.font.render("Select a Monster", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        page = self.monster_pages[self.current_monster_page]
        monsters = page["monsters"]
        boss_name = page.get("boss")

        total_pages = len(self.monster_pages)
        current_page = self.current_monster_page

        btn_w = 180
        btn_h = 55
        spacing = 20

        start_x = SCREEN_WIDTH // 2 - (btn_w * 2 + spacing) // 2
        start_y = 150

        self.creature_buttons = {}
        
        for i, name in enumerate(monsters):
            col = i % 2
            row = i // 2

            x = start_x + col * (btn_w + spacing)
            y = start_y + row * (btn_h + spacing)

            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.creature_buttons[name] = rect

            pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
            pygame.draw.rect(self.screen, WHITE, rect, 2)

            label = self.font.render(name, True, WHITE)
            self.screen.blit(label, (rect.x + (btn_w - label.get_width()) // 2,
                                     rect.y + (btn_h - label.get_height()) // 2))
            
        if boss_name:
            boss_y = start_y + 2 * (btn_h + spacing) + 10
            boss_rect = pygame.Rect(start_x, boss_y, btn_w * 2 + spacing, btn_h)
            self.creature_buttons[boss_name] = boss_rect

            pygame.draw.rect(self.screen, (120, 40, 40), boss_rect)
            pygame.draw.rect(self.screen, (200, 80, 80), boss_rect, 2)

            boss_label = self.font.render(boss_name, True, WHITE)
            self.screen.blit(boss_label, (boss_rect.x + boss_rect.width // 2 - boss_label.get_width() // 2,
                                             boss_rect.y + boss_rect.height // 2 - boss_label.get_height() // 2))
            
            bottom_y = boss_y + btn_h
        else:
            bottom_y = start_y + (2* (btn_h + spacing))

        self.next_page_button = None
        self.prev_page_button = None

        btn_w_nav = 150
        btn_h_nav = 60

        center_y = SCREEN_HEIGHT // 2 - btn_h_nav // 2

        #previous page button (if > 0)
        if current_page > 0:
            prev_rect = pygame.Rect(30, center_y, btn_w_nav, btn_h_nav)
            self.prev_page_button = prev_rect

            pygame.draw.rect(self.screen, (50, 80, 150), prev_rect)
            pygame.draw.rect(self.screen, (100, 140, 200), prev_rect, 2)

            prev_label = self.font_small.render("← Previous", True, WHITE)
            self.screen.blit(prev_label, (prev_rect.x + (prev_rect.width - prev_label.get_width()) // 2,
                                          prev_rect.y + (prev_rect.height - prev_label.get_height()) // 2))
            
        #next page button (only if < last page)
        if current_page < total_pages - 1:
            next_rect = pygame.Rect(SCREEN_WIDTH - btn_w_nav - 30, center_y, btn_w_nav, btn_h_nav)
            self.next_page_button = next_rect

            pygame.draw.rect(self.screen, (50, 80, 150), next_rect)
            pygame.draw.rect(self.screen, (100, 140, 200), next_rect , 2)

            next_label = self.font_small.render("Next Page →", True, WHITE)
            self.screen.blit(next_label, (next_rect. x + (next_rect.width - next_label.get_width()) // 2,
                                          next_rect.y + (next_rect.height - next_label.get_height()) // 2))
            
        self.return_button = pygame.Rect(SCREEN_WIDTH // 2 - 100,
                                             bottom_y + btn_h + 40,
                                             200, 50)
        pygame.draw.rect(self.screen, (100, 100, 100), self.return_button)
        ret = self.font.render("Return to Camp", True, WHITE)
        self.screen.blit(ret, (self.return_button.x + self.return_button.width // 2 - ret.get_width() // 2,
                                   self.return_button.y + self.return_button.height // 2 - ret.get_height() // 2))

    def draw_combat_screen(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.combat_bg, (0, 0))
        
        font = self.font
        small_font = pygame.font.Font(None, 24)
        tiny_font = pygame.font.Font(None, 18)
        label_font = tiny_font
        label_color = WHITE
        self.hovered_effect = None

        player_x = 38
        player_y = 10

        bar_width = 160
        bar_height = 15

        #spell projectiles
        for p in self.combat.projectiles:
            image = p["image"]
            rect = image.get_rect(center = (int(p["x"]), int(p["y"])))
            self.screen.blit(image, rect)

        #semi-transparent background for unit frame
        frame_width = bar_width + 45
        frame_height = 90
        frame_x = player_x - 35
        frame_y = player_y - 2
        
        unit_frame_surf = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        unit_frame_surf.fill((0, 0, 0, 160))
        self.screen.blit(unit_frame_surf, (frame_x, frame_y))

        self.player_frame_x = frame_x
        self.player_frame_y = frame_y
        self.player_frame_height = frame_height

        #player name
        player_text = font.render(f"{self.player.name} (Lv {self.player.level})", True, WHITE)
        self.screen.blit(player_text, (player_x, player_y))
        
        
        #player hp
        player_hp_ratio = self.player.stats.hp / self.player.stats.max_hp
        pygame.draw.rect(self.screen, RED, (player_x, player_y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (player_x, player_y + 30, int(bar_width * player_hp_ratio), bar_height))
        hp_text = tiny_font.render(f"{self.player.stats.hp}/{self.player.stats.max_hp}", True, WHITE)
        hp_text_x = player_x + bar_width // 2 - hp_text.get_width() // 2
        hp_text_y = player_y + 30 + bar_height // 2 - hp_text.get_height() // 2 + 2
        self.screen.blit(hp_text, (hp_text_x, hp_text_y))
        hp_label = label_font.render("HP", True, label_color)
        self.screen.blit(hp_label, (player_x - hp_label.get_width() - 8, player_y + 30))


        #player mp
        player_mp_ratio = self.player.stats.mp / self.player.stats.max_mp
        pygame.draw.rect(self.screen, BLUE, (player_x, player_y + 50, bar_width, bar_height))
        pygame.draw.rect(self.screen, CYAN, (player_x, player_y + 50, int(bar_width * player_mp_ratio), bar_height))
        mp_text = tiny_font.render(f"{self.player.stats.mp}/{self.player.stats.max_mp}", True, WHITE)
        mp_text_x = player_x + bar_width // 2 - mp_text.get_width() // 2
        mp_text_y = player_y + 50 + bar_height // 2 - mp_text.get_height() // 2 + 2
        self.screen.blit(mp_text, (mp_text_x, mp_text_y))
        mp_label = label_font.render("MP", True, label_color)
        self.screen.blit(mp_label, (player_x - mp_label.get_width() - 8, player_y + 50))


        #exp bar
        exp_into_level, exp_needed = self.player.exp_progress()
        exp_ratio = exp_into_level / exp_needed
        exp_percent = int(exp_ratio * 100)
        exp_bar_y = player_y + 70

        pygame.draw.rect(self.screen, (50, 50, 50), (player_x, exp_bar_y, bar_width, bar_height), border_radius = 6)
        pygame.draw.rect(self.screen, (255, 215, 0), (player_x, exp_bar_y, int(bar_width * exp_ratio), bar_height), border_radius = 6)
        exp_text = tiny_font.render(f"{exp_percent}%", True, WHITE)
        self.screen.blit(exp_text, (player_x + bar_width // 2 - exp_text.get_width() // 2,
                                    exp_bar_y + bar_height // 2 - exp_text.get_height() // 2 + 2))

        exp_label = label_font.render("EXP", True, label_color)
        self.screen.blit(exp_label, (player_x - exp_label.get_width() - 8, exp_bar_y))

        #draw level up button if poitns avaialable
        self.draw_levelup_button()

        #player sprite
        player_sprite_rect = pygame.Rect(player_x + 85, 300, 200, 180)
        if self.player.sprite:
            sprite = self.player.sprite
            sprite_x = player_sprite_rect.x + (player_sprite_rect.width - sprite.get_width()) // 2
            sprite_y = player_sprite_rect.y + (player_sprite_rect.height - sprite.get_height()) // 2
                   
            offset_x = 0
            now = pygame.time.get_ticks()
            if self.combat.player_attack_anim:
                elapsed = now - self.combat.player_attack_anim_start
                total = self.combat.player_attack_anim_duration

                if elapsed < total:
                    phase = elapsed / total
                    #first 30% = wind up (move left)
                    #next 40% = swing forward (move right)
                    #last 30% = recoil to center
                    if phase < 0.3:
                        offset_x = -20 * (phase / 0.3)  #wind up left
                    elif phase < 0.7:
                        offset_x = -20 + 60 * ((phase - 0.3) / 0.4)  #swing forward right
                    else:
                        offset_x = 40 - 40 * ((phase - 0.7) / 0.3)  #recoil to center
                else:
                    #animation finished
                    self.combat.player_attack_anim = None

            self.screen.blit(sprite, (sprite_x + offset_x, sprite_y))

            self.player_draw_x = sprite_x + offset_x
            self.player_draw_y = sprite_y

        else:
            pygame.draw.rect(self.screen, (30, 30, 30), player_sprite_rect, border_radius = 8)
            pygame.draw.rect(self.screen, (80, 80, 80), player_sprite_rect, width = 2, border_radius = 8)

        enemy_bar_width = 200
        enemy_bar_height = 20
        enemy_x = SCREEN_WIDTH - enemy_bar_width
        enemy_y = 17

        frame_width = enemy_bar_width + 5
        frame_height = 90
        frame_x = enemy_x - 10
        frame_y = enemy_y - 10

        enemy_frame_surf = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        enemy_frame_surf.fill((0, 0, 0, 160))
        self.screen.blit(enemy_frame_surf, (frame_x, frame_y))     

        self.enemy_frame_x = frame_x
        self.enemy_frame_y = frame_y
        self.enemy_frame_height = frame_height

        #monster hp/mp

        enemy_x = SCREEN_WIDTH - 180
        enemy_y = 20
        monster = self.combat.current_monster

        monster_text = font.render(f"{monster.name} (Lvl {monster.level})", True, WHITE)
        self.screen.blit(monster_text, (enemy_x, enemy_y))
        
        #monster hp bar
        monster_hp_ratio = monster.stats.hp / monster.stats.max_hp
        pygame.draw.rect(self.screen, RED, (enemy_x, enemy_y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (enemy_x, enemy_y + 30, int(bar_width * monster_hp_ratio), bar_height))
        
        #shield bar
        if monster.current_shield > 0:
            shield_color = LIGHT_BLUE

            #calculate how much bar space is already used by hp
            hp_bar_width = int(bar_width * monster_hp_ratio)

            #calculate how much space is available for shield display
            available_space = bar_width - hp_bar_width
            
            #calculate what the shield bar width should be if uncapped
            shield_ratio = monster.current_shield / monster.stats.max_hp
            uncapped_shield_width = int(bar_width * shield_ratio)

            #cap it to available space
            shield_width = min(uncapped_shield_width, available_space)

            #draw shield bar starting from the right edge of the hp bar
            shield_x = enemy_x + hp_bar_width
            pygame.draw.rect(self.screen, shield_color, (shield_x, enemy_y + 30, shield_width, bar_height))
        
        #monster hp text
        if monster.current_shield > 0:
            hp_text = f"{int(monster.stats.hp)}+{int(monster.current_shield)}/{int(monster.stats.max_hp)}"
        else:
            hp_text = f"{int(monster.stats.hp)}/{int(monster.stats.max_hp)}"
        hp_text_surf = tiny_font.render(hp_text, True, WHITE)

        text_x = enemy_x + (bar_width // 2) - (hp_text_surf.get_width() // 2)
        text_y = enemy_y + 32 + (bar_height // 2) - (hp_text_surf.get_height() // 2)
        self.screen.blit(hp_text_surf, (text_x, text_y))



        monster_mp_ratio = self.current_monster.stats.mp / self.current_monster.stats.max_mp
        pygame.draw.rect(self.screen, BLUE, (enemy_x, enemy_y + 50, bar_width, bar_height))
        pygame.draw.rect(self.screen, CYAN, (enemy_x, enemy_y + 50, int(bar_width * monster_mp_ratio), bar_height))



        enemy_sprite_rect = pygame.Rect(enemy_x - 85, 305, 200, 180)
        self.enemy_sprite_rect = enemy_sprite_rect
        if self.current_monster.sprite:
            sprite = self.current_monster.sprite
            
            rect = sprite.get_rect(center = enemy_sprite_rect.center)

            self.screen.blit(sprite, rect)
            
            #scaled_sprite = pygame.transform.scale(sprite, (enemy_sprite_rect.width, enemy_sprite_rect.height))
             
            #sprite_x = enemy_sprite_rect.x + (enemy_sprite_rect.width - scaled_sprite.get_width()) // 2
            #sprite_y = enemy_sprite_rect.y + (enemy_sprite_rect.height - scaled_sprite.get_height()) // 2
            
            #self.screen.blit(scaled_sprite, (sprite_x, sprite_y))

            #flash effect on hit
            now = pygame.time.get_ticks()
            flashing = False
            if (self.combat.enemy_hit_flash_timer > 0 and now - self.combat.enemy_hit_flash_timer < self.combat.enemy_hit_flash_duration):
                #flash every  50 ms
                if ((now - self.combat.enemy_hit_flash_timer) // 50) % 2 == 0:               
                    flash_surf = sprite.copy()
                    flash_surf.fill((255, 255, 255), special_flags = pygame.BLEND_RGB_ADD)
                    self.screen.blit(flash_surf, rect)
            else:
                    self.combat.enemy_hit_flash_timer = 0 

            # ---------------------------------------------------------
            # Apply enraged red flash overlay
            # ---------------------------------------------------------   
            alpha = getattr(self.combat, "enrage_flash_alpha", 0)

            if alpha > 0:
                flash_surf = sprite.copy()
                
                #apply red tint to sprites pixels
                flash_surf.fill((255, 0, 0, 0), special_flags = pygame.BLEND_RGBA_ADD)

                #apply alpha by multiplying the sprite
                flash_surf.set_alpha(alpha)

                self.screen.blit(flash_surf, rect)     

        else:
            pygame.draw.rect(self.screen, (30, 30, 30), enemy_sprite_rect, border_radius = 8)
            pygame.draw.rect(self.screen, (80, 80, 80), enemy_sprite_rect, width = 2, border_radius = 8)


        self.draw_player_buffs()
        self.draw_enemy_buffs()

        #combat/loot log settings
        log_width = (SCREEN_WIDTH - 100) // 2
        log_height = 170
        log_y = SCREEN_HEIGHT - 250
        left_x = 50
        right_x = left_x + log_width + 10

        #loot log box
        loot_log_box = pygame.Rect(right_x, log_y, log_width, log_height)
        pygame.draw.rect(self.screen, (20, 20, 20), loot_log_box, border_radius = 8)
        pygame.draw.rect(self.screen, (80, 80, 80), loot_log_box, width = 2, border_radius = 8)
        
        #combat log box
        combat_log_box = pygame.Rect(left_x, log_y, log_width, log_height)
        pygame.draw.rect(self.screen, (20, 20, 20), combat_log_box, border_radius = 8)
        pygame.draw.rect(self.screen, (80, 80, 80), combat_log_box, width = 2, border_radius = 8)

        self.draw_combat_log(self.screen, combat_log_box)
             
        #combat log text                             
        #for i, line in enumerate(self.combat.combat_log[-5:]):
        #    text = small_font.render(line, True, WHITE)
        #    self.screen.blit(text, (combat_log_box.x + 10, combat_log_box.y + 10 + i * 24))


        #loot log text
        for i, line in enumerate(self.combat.loot_log[-5:]):
            text = small_font.render(line, True, WHITE)
            self.screen.blit(text, (loot_log_box.x + 10, loot_log_box.y + 10 + i * 24))

        #for t in self.combat.floating_text_player:
        #    text_str = t.get("text", "")
        #    color = t.get("color", (255, 255, 255))
        #    alpha = t.get("alpha", 255)

        #    text_surface = self.float_font.render(text_str, True, color)
        #    text_surface.set_alpha(max(0, alpha))

        #    player_center_x = 38 + 100
        #    player_center_y = 240

        #    draw_x = player_center_x + t.get("offset_x", 0)
        #    draw_y = player_center_y - 40 + t.get("offset_y", 0)

        #    self.screen.blit(text_surface, (draw_x, draw_y))

        #heal particle effects
        for p in list(self.combat.heal_particles):
            #move
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            #fade
            p["alpha"] -= 5
            if p["alpha"] <= 0:
                self.combat.heal_particles.remove(p)
                continue
            
            #draw
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], max(0, p["alpha"])))
            self.screen.blit(s, (p["x"], p["y"]))

        self.combat.draw_floating_text(self.screen)
        self.combat.draw_heal_spell_particles(self.screen)
        self.combat.draw_battlecry_waves(self.screen)

        #for p in self.combat.heal_spell_particles:
        #    s = pygame.Surface((p["size"]), pygame.SRCALPHA)
        #    s.fill((*p["color"], max(0, p["alpha"])))
        #    self.screen.blit(s, (p["x"], p["y"]))

        border_y = SCREEN_HEIGHT - 70
        self.screen.blit(self.ui_border, (0, border_y))


        button_labels = ["Attack", "Auto", "Spells", "Use Item", "Inventory", "Home"]
        self.combat_buttons = {}
        button_width, button_height = 130, 40
        spacing = 8
        total_width = len(button_labels) * (button_width + spacing) - spacing
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        y_pos = SCREEN_HEIGHT - 46

        for i, label in enumerate(button_labels):
            rect = pygame.Rect(start_x + i * (button_width + spacing), y_pos, button_width, button_height)
            self.combat_buttons[label] = rect
            pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
            
            #auto button text toggle
            display_label = label
            if label == "Auto":
                display_label = "Auto: On" if self.auto_combat_enabled else "Auto: Off"
            
            text = font.render(display_label, True, WHITE)
            self.screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2,
                                    rect.y + rect.height // 2 - text.get_height() // 2))


        #inventory
        if self.show_inventory:
            self.inventory_window.draw(self.screen)

        #draw enhancement confirmation on top of everything
        #print(f"[DEBUG] Checking enhancement dialog: visible={self.enhancement_confirmation.visible}, scroll={self.enhancement_confirmation.scroll}, target={self.enhancement_confirmation.target_item}")
        if self.enhancement_confirmation.visible:
            #print("[DEBUG] About to draw enhancement confirmation!")
            self.enhancement_confirmation.draw(self.screen)

        hovered_spell = None
        hover_mouse_pos = None

        #spell bar
        if self.show_spell_bar:
            spell_button_labels = ["Spellbook", "Slot 1", "Slot 2", "Slot 3"]
            spell_buttons = {}
            spell_button_width = 110
            spell_button_height = 36
            spell_spacing = 4
            
            spells_rect = self.combat_buttons.get("Spells")
            if spells_rect:
                spell_x = spells_rect.x - 100
                spell_y = spells_rect.y - (spell_button_height + 6)
            else:
                spell_x = SCREEN_WIDTH // 2 - ((len(spell_button_labels) * (spell_button_width + spell_spacing)) // 2)
                spell_y = SCREEN_HEIGHT - 90

            mouse_pos = pygame.mouse.get_pos()
            #hovered_spell = None
            #hover_mouse_pos = None

            #slot_index = None
            #is_selected = False

            for i, label in enumerate(spell_button_labels):
                rect = pygame.Rect(spell_x + i * (spell_button_width + spell_spacing), spell_y, spell_button_width, spell_button_height)
                spell_buttons[label] = rect

                spellbook_open = False
                if hasattr(self, "ui_mgr") and hasattr(self.ui_mgr, "spellbook_window"):
                    spellbook_open = self.ui_mgr.spellbook_window.visible
                elif hasattr(self, "spellbook_window"):
                    spellbook_open = self.spellbook_window.visible

                slot_index = None
                if label.startswith("Slot"):
                    slot_index = int(label.split(" ")[1])

                is_selected = (
                    spellbook_open
                    #and not getattr(self, "in_combat", False)
                    and hasattr(self, "selected_spell_slot")
                    and slot_index is not None
                    and self.selected_spell_slot == slot_index
                )

                base_color = (60, 60, 60)
                highlight_color = (120, 120, 120) if is_selected else base_color

                pygame.draw.rect(self.screen, highlight_color, rect, border_radius = 6)
                pygame.draw.rect(self.screen, (180, 180, 180), rect, 2, border_radius = 6)              

                if slot_index is not None:
                    
                    
                    spell = self.spell_slots.get(slot_index)
                    #print(f"[DEBUG] Got spell for slot {slot_index}: {spell}")
                    
                    if spell:
                        #print(f"[INSTANCE CHECK] {spell.name} id={id(spell)} cooldown_remaining={spell.get_cooldown_remaining()}")
                        remaining = spell.get_cooldown_remaining()
                        if remaining > 0:
                            
                            pct = remaining / spell.cooldown
                            overlay_height = int(rect.height * pct)
                            #print(f"[DRAW] Overlay for {spell.name} — {remaining:.2f}s left, pct={pct:.2f}")

                            overlay_surface = pygame.Surface((rect.width, overlay_height), pygame.SRCALPHA)
                            overlay_surface.fill((0, 0, 0, 140))
                            self.screen.blit(overlay_surface, (rect.x, rect.y + (rect.height - overlay_height)))

                            #cd_text = self.font_small.render(f"{remaining:.1f}", True, (255, 255, 255))
                            #cd_rect = cd_text.get_rect(center = rect.center)
                            #self.screen.blit(cd_text, cd_rect)

                if slot_index is not None:
                    assigned_spell = self.spell_slots.get(slot_index)
                    display_text = assigned_spell.name if assigned_spell else label
                else:
                    display_text = label

                spell_text = self.font_small.render(display_text, True, (255, 255, 255))
                self.screen.blit(spell_text, spell_text.get_rect(center = rect.center))


                if rect.collidepoint(mouse_pos) and slot_index is not None:
                    #slot_index = int(label.split(" ")[1])
                    spell = self.spell_slots.get(slot_index)
                    if spell:
                        hovered_spell = spell
                        hover_mouse_pos = mouse_pos 
                   
                
            self.spell_buttons = spell_buttons

            #if hovered_spell:
            #    print(f"[DEBUG] Hovering over {hovered_spell.name}")
            #    self.ui_mgr.draw_spell_tooltip(self.screen, hovered_spell, hover_mouse_pos)

        if self.spellbook_window.visible:
            self.spellbook_window.draw(self.screen)

        if hovered_spell and hasattr(self, "ui_mgr"):
            self.ui_mgr.draw_spell_tooltip(self.screen, hovered_spell, hover_mouse_pos)
            pygame.display.flip()

        if hasattr(self, "hovered_effect") and self.hovered_effect:
            self.draw_effect_tooltip(self.hovered_effect, pygame.mouse.get_pos())

    def draw_levelup_button(self):
        #draw a button to open level-up window when points are available
        p = self.player

        #calculate total availabe points (unspent + not yet confirmed)
        total_points = p.stat_points

        #only show button if player has points to spend
        if total_points <= 0:
            return
        
        #button position
        button_width = 100
        button_height = 40
        button_x = 50
        button_y = 140

        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        #draw button background
        pygame.draw.rect(self.screen, (180, 140, 20), button_rect, border_radius = 5)
        pygame.draw.rect(self.screen, (255, 215, 0), button_rect, width = 3, border_radius = 5)

        #draw text
        font = pygame.font.Font(None, 22)
        text = font.render(f"Level Up!", True, (255, 255, 255))
        text_rect = text.get_rect(center = (button_rect.centerx, button_rect.centery - 5))
        self.screen.blit(text, text_rect)

        #show points count below
        points_font = pygame.font.Font(None, 18)
        points_text = points_font.render(f"({total_points} points)", True, (255, 215, 0))
        points_rect = points_text.get_rect(center = (button_rect.centerx, button_rect.centery + 8))
        self.screen.blit(points_text, points_rect)

        #store rect for click detection
        self.levelup_button_rect = button_rect

    def draw_effects(self, effects, start_x, start_y):
        box_size = 26
        padding = 4
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, effect in enumerate(effects):
            x = start_x + i * (box_size + padding)
            rect = pygame.Rect(x, start_y, box_size, box_size)

            
            # ----------------------------------------------------
            # 1) DIRECT ICON SURFACE SUPPORT (for consumables)
            # ----------------------------------------------------
            if effect.get("icon_surface"):
                surf = pygame.transform.scale(effect["icon_surface"], (box_size, box_size))
                self.screen.blit(surf, rect.topleft)

                #still draw the border
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

                #draw cooldown overlay if needed
                self.draw_radial_cooldown(self.screen, rect, effect)

                if rect.collidepoint(mouse_x, mouse_y):
                    self.hovered_effect = effect

                continue

            # ----------------------------------------------------
            # 2) ICON-KEY LOOKUP (standard system for spells/buffs)
            # ----------------------------------------------------

            raw_key = effect.get("icon", "")
            icon_key = raw_key.lower() if isinstance(raw_key, str) else ""
            icon = self.buff_icons.get(icon_key)

            bg_color = (40, 40, 40)
            pygame.draw.rect(self.screen, bg_color, rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

            if icon:
                self.screen.blit(icon, rect.topleft)
                pygame.draw.rect(self.screen, (255, 0, 0), rect, 1)
            else:
                #placeholder box
                pygame.draw.rect(self.screen, effect["color"], rect)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

                #optional text (first letter of buff for now)    
                letter = effect["name"][0]
                text = self.font_small.render(letter, True, (0, 0, 0))
                self.screen.blit(text, text.get_rect(center = rect.center))

            self.draw_radial_cooldown(self.screen, rect, effect)

            if rect.collidepoint(mouse_x, mouse_y):
                self.hovered_effect = effect

    def assign_spell_to_slot(self, slot_index, spell):
        #prevent duplicates
        for slot, assigned in self.spell_slots.items():
            if assigned.name == spell.name:
                print(f"[INFO] {spell.name} is already assigned to Slot {slot}.")
                return  
        
        print(f"✅ Assigned {spell.name} to Slot {slot_index} (id={id(spell)})")    
        self.spell_slots[slot_index] = spell
        self.selected_spell_slot = None

        if hasattr(self, "ui_mgr") and hasattr(self.ui_mgr, "spellbook_window"):
            self.ui_mgr.spellbook_window.visible = False
        elif hasattr(self, "spellbook_window"):
            self.spellbook_window.visible = False
    

    def draw_player_buffs(self):
            effects = getattr(self.player, "active_effects", [])
            if not effects:
                return
            
            frame_x = self.player_frame_x
            frame_y = self.player_frame_y
            frame_height = self.player_frame_height

            start_x = frame_x + 10
            start_y = frame_y + frame_height + 8

            self.draw_effects(effects, start_x, start_y)

            if self.hovered_effect:
                self.draw_effect_tooltip(self.hovered_effect, pygame.mouse.get_pos())
            #box_size = 26
            #padding = 4

            #hovered_buff = None
            #hover_mouse_pos = None
            #mouse_pos = pygame.mouse.get_pos()

            #for i, effect in enumerate(effects):
            #    x = start_x + i * (box_size + padding)
            #    rect = pygame.Rect(x, start_y, box_size, box_size)

            #    pygame.draw.rect(self.screen, effect["color"], rect)
            #    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

            #    letter = effect["name"][0]
            #    text = self.font_small.render(letter, True, (0, 0, 0))
            #    self.screen.blit(text, text.get_rect(center = rect.center))

            #    self.draw_radial_cooldown(self.screen, rect, effect)

            #    if rect.collidepoint(mouse_pos):
            #        hovered_buff = effect
            #        hover_mouse_pos = mouse_pos

            #if hovered_buff:
            #    self.draw_effect_tooltip(hovered_buff, hover_mouse_pos)            

    def draw_enemy_buffs(self):
            if not self.current_monster:
                return

            effects = getattr(self.current_monster, "active_effects", [])
            if not effects:
                return

            frame_x = self.enemy_frame_x
            frame_y = self.enemy_frame_y
            frame_height = self.enemy_frame_height

            start_x = frame_x + 10
            start_y = frame_y + frame_height + 8

            self.draw_effects(effects, start_x, start_y)

            if self.hovered_effect:
                self.draw_effect_tooltip(self.hovered_effect, pygame.mouse.get_pos())
            #box_size = 26
            #padding = 4

            #hovered_buff = None
            #hover_mouse_pos = None
            #mouse_pos = pygame.mouse.get_pos()

            #for i, effect in enumerate(effects):
            #    x = start_x + i * (box_size + padding)
            #    rect = pygame.Rect(x, start_y, box_size, box_size)

            #    pygame.draw.rect(self.screen, effect["color"], rect)
            #    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

            #    letter = effect["name"][0]
            #    text = self.font_small.render(letter, True, (0, 0, 0))
            #    self.screen.blit(text, text.get_rect(center = rect.center))

            #    self.draw_radial_cooldown(self.screen, rect, effect)

            #    if rect.collidepoint(mouse_pos):
            #        hovered_buff = effect
            #        hover_mouse_pos = mouse_pos
            #if hovered_buff:
            #    self.draw_effect_tooltip(hovered_buff, hover_mouse_pos)  

    def draw_radial_cooldown(self, surface, rect, effect):
        now = time.time()
        remaining = effect["expires"] - now
        duration = effect["duration"]

        if remaining <= 0:
            return

        pct = remaining / duration
        angle = pct * 360  # degrees

        # Create a transparent overlay surface for the cooldown mask
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        cx = rect.width // 2
        cy = rect.height // 2
        r = rect.width // 2

        # Draw a filled radial "pie" mask
        steps = 90  # more steps = smoother circle
        for i in range(int(angle)):
            rad = math.radians(i)
            x = cx + r * math.cos(rad)
            y = cy - r * math.sin(rad)
            pygame.draw.line(overlay, (0, 0, 0, 150), (cx, cy), (x, y))

        surface.blit(overlay, rect.topleft)


    def get_frame(self, sheet, frame_rect):
        frame = sheet.subsurface(frame_rect)

        return frame
    
    def draw_effect_tooltip(self, effect, mouse_pos):
        name = effect["name"]
        desc = effect.get("description", "")
        mods = effect.get("mods", {})

        now = time.time()
        remaining = max(0, effect["expires"] - now)

        lines = [name]

        for stat, val in mods.items():
            
            if stat == "damage_flat":
                sign = "+" if val > 0 else ""
                lines.append(f"{sign}{val} Damage")

            elif stat == "damage_pct":
                pct = int(val * 100)
                sign = "+" if pct > 0 else ""
                lines.append(f"{sign}{pct}% Damage")

            elif stat == "attack_speed_pct":
                pct = int(abs(val) * 100)

                # val > 0 → delay increases → you attack slower
                if val > 0:
                    lines.append(f"-{pct}% Attack Speed (Slowed)")
                else:
                    # val < 0 → delay decreases → you attack faster
                    lines.append(f"+{pct}% Attack Speed (Haste)")

            elif stat == "armor_flat":
                sign = "+" if val > 0 else ""
                lines.append(f"{sign}{val} Armor")

            elif stat == "armor_pct":
                pct = int(val * 100)
                sign = "+" if pct > 0 else ""
                lines.append(f"{sign}{pct}% Armor")
                
            elif stat == "crit_chance":
                pct = int(val * 100)
                sign = "+" if pct > 0 else ""
                lines.append(f"{sign}{pct}% Crit Chance")

            elif stat == "dodge_chance":
                pct = int(val * 100)
                sign = "+" if pct > 0 else ""
                lines.append(f"{sign}{pct}% Dodge Chance")
        
        lines.append(f"Time left: {remaining:.1f}s")

        font = self.font_small
        padding = 8

        width = max(font.size(line)[0] for line in lines) + padding * 2
        height = len(lines) * 18 + padding * 2

        x, y = mouse_pos
        tooltip_x = x + 15
        tooltip_y = y + 15

        if tooltip_x + width > SCREEN_WIDTH:
            tooltip_x = SCREEN_WIDTH - width - 5

        if tooltip_y + height > SCREEN_HEIGHT:
            tooltip_y = SCREEN_HEIGHT - height - 5
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, width, height)

        pygame.draw.rect(self.screen, (20, 20, 20, 200), tooltip_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), tooltip_rect, 2)

        for i, line in enumerate(lines):
            color = (255, 255, 255)
            if "+" in line:
                color = (120, 255, 120)
            elif "-" in line:
                color = (255, 120, 120)
            
            text_surf = font.render(line, True, color)
            self.screen.blit(text_surf, (tooltip_rect.x + padding, tooltip_rect.y + padding + i * 18))


    def wrap_text(self, text, font, max_width):
        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            test = current + word + " "
            if font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word + " "
        if current:
            lines.append(current)
        return lines
    
    def draw_combat_log(self, surface, combat_log_box):
        font = pygame.font.Font(None, 20)

        x = combat_log_box.x + 10
        y = combat_log_box.y + 10
        w = combat_log_box.width - 20
        h = combat_log_box.height - 20

        #clip region so text never draws outside box
        surface.set_clip(combat_log_box)

        #wrap all log entires to visible lines
        wrapped = []
        for line in self.combat.combat_log:
            wrapped.extend(self.wrap_text(line, font, w))

        total_lines = len(wrapped)

        #calculate how many lines fit in the box
        max_visible_lines = h // self.combat.log_line_height

        #clamp scroll to never scroll beyond real lines
        max_scroll = max(0, total_lines - max_visible_lines)

        if not self.combat.user_is_scrolling:
            self.combat.log_scroll = max_scroll

        if self.combat.force_scroll_to_bottom:
            self.combat.log_scroll = max_scroll
            self.combat.force_scroll_to_bottom = False

        self.combat.log_scroll = max(0, min(self.combat.log_scroll, max_scroll))

        #determine lines that appear
        start = self.combat.log_scroll
        end = start + max_visible_lines

        visible_lines = wrapped[start:end]

        draw_y = y
        
        for line in visible_lines:
            rendered = font.render(line, True, (255, 255, 255))
            surface.blit(rendered, (x, draw_y))
            draw_y += self.combat.log_line_height

        surface.set_clip(None)

        #scroll bar
        if total_lines > max_visible_lines:
            bar_h = int((max_visible_lines / total_lines) * h)
            scroll_percent = self.combat.log_scroll / max_scroll
            bar_y = int(scroll_percent * (h - bar_h))

            scrollbar_rect = pygame.Rect(
                combat_log_box.right - 6,
                combat_log_box.y + 3 + bar_y,
                4,
                bar_h
            )

            pygame.draw.rect(surface, (180, 180, 180), scrollbar_rect)

        self.combat.wrapped_cache = wrapped
        self.combat.max_visible_lines = max_visible_lines
        self.combat.max_scroll = max_scroll