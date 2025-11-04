import pygame
from settings import *
import os
from entities.player import Player
from entities.monster import Monster
from systems.combat import CombatManager
from systems.loot_system import LootSystem


class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.float_font = pygame.font.Font(None, 42)
        self.state = "title"
        self.title_image = self.load_image("bq_titlescreen.png")
        self.home_image = self.load_image("bq_campsite.png")
        self.loot_system = LootSystem()

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

        self.player = Player()
        self.current_monster = None
        self.combat = CombatManager(self.player, self.current_monster, self.loot_system)
        self.combat.auto_callback = lambda: self.auto_combat_enabled

        self.auto_combat_unlocked = True
        self.auto_combat_enabled = False

        if self.combat:
            self.combat.auto_combat_enabled = self.auto_combat_enabled

        button_width = 150
        button_height = 50
        bottom_margin = 15
        gap = 25

        buttons = ["Fight", "Gather", "Craft", "Inventory"]
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
                    if rect.collidepoint(event.pos) and text == "Fight":
                        self.state = "creature_select"
                        print("Please select a creature to fight")

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
                                self.current_monster = Monster(name = "Wolf", level = 3)
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
                                if not self.auto_combat_unlocked:
                                    print("Auto-Combat isn't unlocked yet!")
                                    #add popup/tooltip instead of console output
                                    return
                                self.auto_combat_enabled = not self.auto_combat_enabled
                                print(f"Auto-Combat is now {'ON' if self.auto_combat_enabled else 'OFF'}")
                                
                                if self.auto_combat_enabled and not self.combat.player_initiated:
                                    self.combat.player_initiated = True
                                
                                return
                            elif label == "Cast Spell":
                                pass
                            elif label == "Use Item":
                                pass
                            elif label == "Inventory":
                                pass
                            elif label == "Home":
                                self.state = "home"
                                print("[UI] Returning to home screen")

    def update(self):
        if self.state == "combat" and self.combat:            
            if self.combat.update():
                print(self.combat.combat_log[-1])

            if not self.combat.combat_active:
                print("✅ Combat ended! Returning to creature select.")
                self.state = "creature_select"

            if self.combat is not None:
                self.combat.auto_combat_enabled = self.auto_combat_enabled

    def draw(self):
        if self.state == "title":
            self.draw_title()
        elif self.state == "home":
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
            
        if hasattr(self, 'player_sprite_sheet1') and self.player_sprite_sheet1:
            frame_width = 124
            frame_height = 140 + 28

            frame_x = 5.9 * 54 - 21   # adjust these
            frame_y = 7 * 80 - 125 # adjust these

            frame_rect = pygame.Rect(frame_x, frame_y, frame_width * 3, frame_height * 3)
            player_frame = self.player_sprite_sheet1.subsurface(frame_rect).copy()

            target_width = 100
            target_height = 175
            scaled_frame = pygame.transform.scale(player_frame, (target_width, target_height))

            # Check if the frame is empty
            non_transparent_pixels = [
                player_frame.get_at((x, y))
                for x in range(frame_width) for y in range(frame_height)
                if player_frame.get_at((x, y)).a > 0
            ]

            if not non_transparent_pixels:
                print(f"[Debug] Frame at ({frame_x}, {frame_y}) is fully transparent!")

            offset_x = -200
            offset_y = 80
            
            player_pos = (SCREEN_WIDTH // 2 - target_width // 2 + offset_x,
                          SCREEN_HEIGHT // 2 - target_height // 2 + offset_y)
            self.screen.blit(scaled_frame, player_pos)
        else:
            print("[Warning] Player sprite sheet not loaded yet.")
        

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

        #semi-transparent background for unit frame
        frame_width = bar_width + 45
        frame_height = 90
        frame_x = player_x - 35
        frame_y = player_y - 2
        
        unit_frame_surf = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        unit_frame_surf.fill((0, 0, 0, 160))
        self.screen.blit(unit_frame_surf, (frame_x, frame_y))

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


        player_sprite_rect = pygame.Rect(player_x + 100, 240, 200, 180)
        if self.player.sprite:
            sprite = self.player.sprite
            sprite_x = player_sprite_rect.x + (player_sprite_rect.width - sprite.get_width()) // 2
            sprite_y = player_sprite_rect.y + (player_sprite_rect.height - sprite.get_height()) // 2
            self.screen.blit(sprite, (sprite_x, sprite_y))
        
        else:
            pygame.draw.rect(self.screen, (30, 30, 30), player_sprite_rect, border_radius = 8)
            pygame.draw.rect(self.screen, (80, 80, 80), player_sprite_rect, width = 2, border_radius = 8)

        #monster hp/mp

        enemy_x = SCREEN_WIDTH - 250
        enemy_y = 40
        monster = self.combat.current_monster

        monster_text = font.render(f"{monster.name} (Lvl {monster.level})", True, WHITE)
        self.screen.blit(monster_text, (enemy_x, enemy_y))
        monster_hp_ratio = monster.stats.hp / monster.stats.max_hp
        pygame.draw.rect(self.screen, RED, (enemy_x, enemy_y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (enemy_x, enemy_y + 30, int(bar_width * monster_hp_ratio), bar_height))

        monster_mp_ratio = self.current_monster.stats.mp / self.current_monster.stats.max_mp
        pygame.draw.rect(self.screen, BLUE, (enemy_x, enemy_y + 50, bar_width, bar_height))
        pygame.draw.rect(self.screen, CYAN, (enemy_x, enemy_y + 50, int(bar_width * monster_mp_ratio), bar_height))

        enemy_sprite_rect = pygame.Rect(enemy_x - 100, 240, 200, 180)

        if self.current_monster.sprite:
            sprite = self.current_monster.sprite
            
            scaled_sprite = pygame.transform.scale(sprite, (enemy_sprite_rect.width, enemy_sprite_rect.height))
             
            sprite_x = enemy_sprite_rect.x + (enemy_sprite_rect.width - scaled_sprite.get_width()) // 2
            sprite_y = enemy_sprite_rect.y + (enemy_sprite_rect.height - scaled_sprite.get_height()) // 2
            
            self.screen.blit(scaled_sprite, (sprite_x, sprite_y))
        else:
            pygame.draw.rect(self.screen, (30, 30, 30), enemy_sprite_rect, border_radius = 8)
            pygame.draw.rect(self.screen, (80, 80, 80), enemy_sprite_rect, width = 2, border_radius = 8)


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

        for t in self.combat.floating_text_player:
            text_str = t.get("text", "")
            color = t.get("color", (255, 255, 255))
            alpha = t.get("alpha", 255)

            text_surface = self.float_font.render(text_str, True, color)
            text_surface.set_alpha(max(0, alpha))

            player_center_x = 38 + 100
            player_center_y = 240

            draw_x = player_center_x + t.get("offset_x", 0)
            draw_y = player_center_y - 40 + t.get("offset_y", 0)

            self.screen.blit(text_surface, (draw_x, draw_y))

        for t in self.combat.floating_text_enemy:
            text_str = t.get("text", "")
            color = t.get("color", (255, 255, 255))
            alpha = t.get("alpha", 255)

            text_surface = self.float_font.render(text_str, True, color)
            text_surface.set_alpha(max(0, alpha))

            enemy_center_x = SCREEN_WIDTH - 250 + 100
            enemy_center_y = 240

            draw_x = enemy_center_x + t.get("offset_x", 0)
            draw_y = enemy_center_y - 40 + t.get("offset_y", 0)

            self.screen.blit(text_surface, (draw_x, draw_y))

        border_y = SCREEN_HEIGHT - 70
        self.screen.blit(self.ui_border, (0, border_y))


        button_labels = ["Attack", "Auto", "Cast Spell", "Use Item", "Inventory", "Home"]
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

    def get_frame(self, sheet, frame_rect):
        frame = sheet.subsurface(frame_rect)

        return frame