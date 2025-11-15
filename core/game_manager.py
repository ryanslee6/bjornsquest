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
import time
import math
from pygame import gfxdraw


class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.float_font = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 24)
        self.state = "title"
        self.title_image = self.load_image("bq_titlescreen.png")
        self.home_image = self.load_image("bq_campsite.png")
        self.loot_system = LootSystem()
        self.items = ItemManager()
        self.inventory_window = InventoryWindow(self)
        self.show_inventory = False
        self.show_spell_bar = False
        self.spell_buttons = {}
        self.vendor_window = VendorWindow(self)
        
        
        
        
        

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
        self.combat = CombatManager(self.player, self.current_monster, self.loot_system)
        self.combat.auto_callback = lambda: self.auto_combat_enabled

    

        self.spellbook_window = SpellbookWindow(
            self.player,
            self.combat.spellbook,
            self.assign_spell_to_slot
        )
        self.spell_slots = {}
        
        

        self.auto_combat_enabled = False

        if self.combat:
            self.combat.auto_combat_enabled = self.auto_combat_enabled

        button_width = 150
        button_height = 50
        bottom_margin = 15
        gap = 25

        buttons = ["Fight", "Gather", "Craft", "Inventory", "Shop"]
        num_buttons = len(buttons)
        total_width = num_buttons * button_width + (num_buttons - 1) * gap
        start_x = (SCREEN_WIDTH - total_width) // 2
        y_pos = SCREEN_HEIGHT - bottom_margin - button_height

        self.buttons = {}
        for i, text in enumerate(buttons):
            x = start_x + i * (button_width + gap)
            self.buttons[text] = pygame.Rect(x, y_pos, button_width, button_height)

        self.current_action = None

        self.creature_select_options = ["Goblin", "Skeleton", "Wolf"]

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
        #if event.type == pygame.MOUSEBUTTONDOWN:
        #    print("[CLICK EVENT]", event.pos, event.button)
        
        if self.show_inventory and event.type == pygame.MOUSEBUTTONDOWN:
               # Right-click uses item
            if event.button == 3 and self.inventory_window.click(event.pos, event.button):
                return

             # Left-click outside closes inventory
            if event.button == 1 and self.inventory_window.click_outside(event.pos):
                self.show_inventory = False
                return

            # ✅ Left-click inside inventory does nothing (prevents closing)
            return 

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "title":
                if self.start_button.collidepoint(event.pos):
                    print("New Game Clicked")
                    self.state = "home"
                elif self.load_button.collidepoint(event.pos):
                    print("Load Game Clicked")
                    #implement load logic here
                    self.state = "home"
            
            elif self.state == "home":
                for text, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        
                        if text == "Fight":
                            self.state = "creature_select"
                            print("Please select a creature to fight")
                            return
                    
                        elif text == "Inventory":
                            self.show_inventory = not self.show_inventory
                            print("[UI] Toggling Inventory Window")
                            return
                        
                        elif text == "Shop":
                            self.state = "vendor"
                            print("[UI] Entering vendor screen")
                            return

            

            elif self.state == "creature_select":
                if hasattr(self, "return_button") and self.return_button.collidepoint(event.pos):
                    print("[UI] Returning to Camp.")
                    self.state = "home"
                    return
                
                for name, rect in self.creature_buttons.items():
                    if rect.collidepoint(event.pos):
                        print(f"{name} selected!")

                        if self.state == "creature_select":
                            if name == "Goblin":
                                self.current_monster = Monster("Goblin")
                            elif name == "Skeleton":
                                self.current_monster = Monster("Skeleton")
                            elif name == "Wolf":
                                self.current_monster = Monster("Wolf")
                            else:
                                self.current_monster = Monster(name = name, level = 1)

                            self.combat = CombatManager(self.player, self.current_monster, self.loot_system)
                            self.state= "combat"

                            print("✅ Combat Started!")
                        else:
                            print("⚠️ Combat already active, ignoring click.")

                        break
            
            elif self.state == "combat":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for label, rect in self.combat_buttons.items():
                        if rect.collidepoint(event.pos):
                            if label == "Attack":
                                self.combat.player_initiated = True
                                print("Combat started!")
                                return
                            elif label == "Auto":
                                if not self.player.auto_combat_unlocked:
                                    print("Auto-Combat isn't unlocked yet!")
                                    #add popup/tooltip instead of console output
                                    return
                                self.auto_combat_enabled = not self.auto_combat_enabled
                                print(f"Auto-Combat is now {'ON' if self.auto_combat_enabled else 'OFF'}")
                                
                                if self.auto_combat_enabled and not self.combat.player_initiated:
                                    self.combat.player_initiated = True
                                
                                return
                            elif label == "Spells":
                                print("🪄 Opening/Closing spell menu...")
                                self.show_spell_bar = not self.show_spell_bar
                            elif label == "Use Item":
                                pass
                            elif label == "Inventory":
                                self.show_inventory = not self.show_inventory
                                return
                            elif label == "Home":
                                self.state = "home"
                                print("[UI] Returning to home screen")


                    if getattr(self, "show_spell_bar", False):
                        for label, rect in self.spell_buttons.items():
                            if rect.collidepoint(event.pos):
                                print(f"Clicked {label}")
                                
                                if label == "Spellbook":
                                    self.spellbook_window.toggle()
                                    return
                                
                                if label.startswith("Slot"):
                                    slot_index = int(label.split(" ")[1])
                                    self.selected_spell_slot = slot_index
                                                                                                   
                                    if self.spellbook_window.visible:
                                        self.spellbook_window.selected_slot = slot_index
                                        print(f"[UI] Selected slot {slot_index} for assignment")
                                    else:
                                        spell = self.spell_slots.get(slot_index)
                                        if spell:
                                            print(f"[CAST DEBUG] Casting {spell.name} id={id(spell)} from slot {slot_index}")
                                            self.combat.cast_spell(spell.name)

                                return


            elif self.state == "vendor":
                #implement vendor screen clicks
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.vendor_window.handle_click(event.pos):
                        return
                    
                    if self.vendor_window and self.vendor_window.is_click_outside(event.pos):
                        print("[UI] Exiting vendor screen")
                        self.state = "home"
                        return


            if self.spellbook_window.visible:
                if self.spellbook_window.handle_click(event.pos):
                    return

    def update(self, dt):
        #hp regen buffer system
        regen = self.player.stats.get_hp_regen()

        if self.state == "combat":
            self.combat.update(dt)
            regen *= 0.05

        #only regen if not full hp
        if self.player.stats.hp < self.player.stats.max_hp:
            #accumulate fractional regen over time
            self.player.stats._hp_regen_buffer += regen

            #when buffer reaches 1 or more, convert to integer healing
            if self.player.stats._hp_regen_buffer >= 1:
                heal_amount = int(self.player.stats._hp_regen_buffer)
                self.player.stats._hp_regen_buffer -= heal_amount

                #apply healing
                self.player.stats.hp = min(
                    self.player.stats.max_hp,
                    self.player.stats.hp + heal_amount
                )

                #floating heal text on regen
                self.combat.add_floating_text(
                    f"+{heal_amount}",
                    0, 0,
                    text_type = "heal",
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
        self.combat.update_heal_spell_particles(dt)

        self.player.remove_expired_effects()
        if self.current_monster:
            self.current_monster.remove_expired_effects()

        
        # ==========================================
        # 1) Handle Monster Death
        # ==========================================
        if self.current_monster and not self.current_monster.is_alive() and not self.monster_defeated:
            self.monster_defeated = True

            self.combat.combat_log.append(f"{self.current_monster.name} was defeated!")

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

            # clear old debuffs
            self.current_monster.active_effects = []

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

            self.current_monster = new_monster
            self.combat.current_monster = new_monster

            self.player_initiated = False
            self.combat.player_initiated = False
            self.combat_active = True
            self.combat.combat_active = True
            self.combat.last_player_attack = pygame.time.get_ticks()

            self.monster_defeated = False


    def draw(self):
        if self.state == "title":
            self.draw_title()
        elif self.state in ("home", "vendor"):
            self.draw_home()
        elif self.state == "creature_select":
            self.draw_creature_select()
        elif self.state == "combat":
            self.draw_combat_screen()

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
            label = self.font.render(text, True, WHITE)
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
        
        
        
        
        #if hasattr(self, 'player_sprite_sheet1') and self.player_sprite_sheet1:
        #    frame_width = 124
        #    frame_height = 140 + 28
        #
        #    frame_x = 5.9 * 54 - 21   # adjust these
        #    frame_y = 7 * 80 - 125 # adjust these

        #    frame_rect = pygame.Rect(frame_x, frame_y, frame_width * 3, frame_height * 3)
        #    player_frame = self.player_sprite_sheet1.subsurface(frame_rect).copy()

        #    target_width = 100
        #    target_height = 175
        #    scaled_frame = pygame.transform.scale(player_frame, (target_width, target_height))

            # Check if the frame is empty
        #    non_transparent_pixels = [
        #        player_frame.get_at((x, y))
        #        for x in range(frame_width) for y in range(frame_height)
        #        if player_frame.get_at((x, y)).a > 0
        #    ]

        #    if not non_transparent_pixels:
        #        print(f"[Debug] Frame at ({frame_x}, {frame_y}) is fully transparent!")

        #    offset_x = -200
        #    offset_y = 80
            
        #    player_pos = (SCREEN_WIDTH // 2 - target_width // 2 + offset_x,
        #                  SCREEN_HEIGHT // 2 - target_height // 2 + offset_y)
        #    self.screen.blit(scaled_frame, player_pos)
        #else:
        #    print("[Warning] Player sprite sheet not loaded yet.")
        

    def draw_creature_select(self):
        self.screen.fill(BLACK)
        title = self.font.render("Select a Monster", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        self.creature_buttons = {}
        y_start = 150
        for i, name in enumerate(self.creature_select_options):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 75, y_start + i * 70, 150, 50)
            self.creature_buttons[name] = rect
            pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
            label = self.font.render(name, True, WHITE)
            self.screen.blit(label, (rect.x + rect.width // 2 - label.get_width() // 2,
                                     rect.y + rect.height // 2 - label.get_height() // 2))

        self.return_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, y_start + len(self.creature_select_options) * 70 + 40, 200, 50)
        pygame.draw.rect(self.screen, (100, 100, 100), self.return_button)
        label = self.font.render("Return to Camp", True, WHITE)
        self.screen.blit(label, (self.return_button.x + self.return_button.width // 2 - label.get_width() // 2,
                                 self.return_button.y + self.return_button.height // 2 - label.get_height() // 2))

    def draw_combat_screen(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.combat_bg, (0, 0))
        
        font = self.font
        small_font = pygame.font.Font(None, 24)
        tiny_font = pygame.font.Font(None, 18)
        label_font = tiny_font
        label_color = WHITE

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
        monster_hp_ratio = monster.stats.hp / monster.stats.max_hp
        pygame.draw.rect(self.screen, RED, (enemy_x, enemy_y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (enemy_x, enemy_y + 30, int(bar_width * monster_hp_ratio), bar_height))
        hp_text = f"{int(self.current_monster.stats.hp)}/{int(self.current_monster.stats.max_hp)}"
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
            
            scaled_sprite = pygame.transform.scale(sprite, (enemy_sprite_rect.width, enemy_sprite_rect.height))
             
            sprite_x = enemy_sprite_rect.x + (enemy_sprite_rect.width - scaled_sprite.get_width()) // 2
            sprite_y = enemy_sprite_rect.y + (enemy_sprite_rect.height - scaled_sprite.get_height()) // 2
            
            self.screen.blit(scaled_sprite, (sprite_x, sprite_y))

            #flash effect on hit
            now = pygame.time.get_ticks()
            flashing = False
            if (self.combat.enemy_hit_flash_timer > 0 and now - self.combat.enemy_hit_flash_timer < self.combat.enemy_hit_flash_duration):
                #flash every  50 ms
                if ((now - self.combat.enemy_hit_flash_timer) // 50) % 2 == 0:               
                    flash_surf = scaled_sprite.copy()
                    flash_surf.fill((255, 255, 255), special_flags = pygame.BLEND_RGB_ADD)
                    self.screen.blit(flash_surf, (sprite_x, sprite_y))
            else:
                    self.combat.enemy_hit_flash_timer = 0    
                    

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
             
        #combat log text                             
        for i, line in enumerate(self.combat.combat_log[-5:]):
            text = small_font.render(line, True, WHITE)
            self.screen.blit(text, (combat_log_box.x + 10, combat_log_box.y + 10 + i * 24))


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

    def draw_effects(self, effects, start_x, start_y):
        box_size = 26
        padding = 4

        for i, effect in enumerate(effects):
            x = start_x + i * (box_size + padding)
            rect = pygame.Rect(x, start_y, box_size, box_size)

            #placeholder box
            pygame.draw.rect(self.screen, effect["color"], rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

            #optional text (first letter of buff for now)    
            letter = effect["name"][0]
            text = self.font_small.render(letter, True, (0, 0, 0))
            self.screen.blit(text, text.get_rect(center = rect.center))

            self.draw_radial_cooldown(self.screen, rect, effect)

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

    def draw_enemy_buffs(self):
            effects = getattr(self.current_monster, "active_effects", [])
            #print("[ENEMY BUFF DEBUG] effects =", effects)
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