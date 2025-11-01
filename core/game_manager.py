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
        self.state = "title"
        self.title_image = self.load_image("bq_titlescreen.png")
        self.home_image = self.load_image("bq_campsite.png")
        self.loot_system = LootSystem()

        sprite_path = os.path.join("assets", "images", "bjorn_char_1.png")
        print("DEBUG: Loading sprite sheet from:", sprite_path)
        
        if os.path.exists(sprite_path):
            print(f"DEBUG: Loading sprite sheet from: {sprite_path}")
            self.player_sprite_sheet1 = pygame.image.load(sprite_path).convert_alpha()
            print(f"✅ Sprite sheet loaded. Size: {self.player_sprite_sheet1.get_size()}")

            grid_debug = self.player_sprite_sheet1.copy()
            for y in range(0, grid_debug.get_height(), 64):
                pygame.draw.line(grid_debug, (255, 0, 0), (0, y), (grid_debug.get_width(), y), 1)
            for x in range(0, grid_debug.get_width(), 64):
                pygame.draw.line(grid_debug, (0, 255, 0), (x, 0), (x, grid_debug.get_height()), 1)
            pygame.image.save(grid_debug, "debug_grid.png")
            print("✅ Saved debug_grid.png — open it to see the sprite layout.")
            # --- End of debug block ---

        else:
            print(f"[Warning] Missing sprite sheet: {sprite_path}")
            self.player_sprite_sheet1 = pygame.Surface((64, 64))
            self.player_sprite_sheet1.fill((255, 0, 255))

        self.player = Player()
        self.current_monster = Monster(level = 1)
        self.combat = CombatManager(self.player, self.current_monster, self.loot_system)

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
                                self.current_monster = Monster(name = "Goblin", level = 1)
                            elif name == "Skeleton":
                                self.current_monster = Monster(name = "Skeleton", level = 2)
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
                            if label == "Cast Spell":
                                pass
                            elif label == "Use Item":
                                pass
                            elif label == "Inventory":
                                pass
                            elif label == "Return to Camp":
                                self.state = "home"
                                print("[UI] Returning to home screen")

    def update(self):
        if self.state == "combat" and self.combat:            
            if self.combat.update():
                print(self.combat.combat_log[-1])

            if not self.combat.combat_active:
                print("✅ Combat ended! Returning to creature select.")
                self.state = "creature_select"

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
        font = self.font
        small_font = pygame.font.Font(None, 24)

        player_x = 50
        player_y = 40

        bar_width = 160
        bar_height = 15


        #player hp/mp
        player_text = font.render(f"{self.player.name} (Lv {self.player.level})", True, WHITE)
        self.screen.blit(player_text, (player_x, player_y))
        player_hp_ratio = self.player.stats.hp / self.player.stats.max_hp
        pygame.draw.rect(self.screen, RED, (player_x, player_y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (player_x, player_y + 30, int(bar_width * player_hp_ratio), bar_height))

        player_mp_ratio = self.player.stats.mp / self.player.stats.max_mp
        pygame.draw.rect(self.screen, BLUE, (player_x, player_y + 50, bar_width, bar_height))
        pygame.draw.rect(self.screen, CYAN, (player_x, player_y + 50, int(bar_width * player_mp_ratio), bar_height))

        player_sprite_rect = pygame.Rect(player_x, 120, 200, 180)
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


        monster_text = font.render(f"{self.current_monster.name} (Lvl {self.current_monster.level})", True, WHITE)
        self.screen.blit(monster_text, (enemy_x, enemy_y))
        monster_hp_ratio = self.current_monster.stats.hp / self.current_monster.stats.max_hp
        pygame.draw.rect(self.screen, RED, (enemy_x, enemy_y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (enemy_x, enemy_y + 30, int(bar_width * monster_hp_ratio), bar_height))

        monster_mp_ratio = self.current_monster.stats.mp / self.current_monster.stats.max_mp
        pygame.draw.rect(self.screen, BLUE, (enemy_x, enemy_y + 50, bar_width, bar_height))
        pygame.draw.rect(self.screen, CYAN, (enemy_x, enemy_y + 50, int(bar_width * monster_mp_ratio), bar_height))

        enemy_sprite_rect = pygame.Rect(enemy_x, 120, 200, 180)
        if self.current_monster.sprite:
            sprite = self.current_monster.sprite
            sprite_x = enemy_sprite_rect.x + (enemy_sprite_rect.width - sprite.get_width()) // 2
            sprite_y = enemy_sprite_rect.y + (enemy_sprite_rect.height - sprite.get_height()) // 2
            self.screen.blit(sprite, (sprite_x, sprite_y))
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

        button_labels = ["Attack", "Cast Spell", "Use Item", "Inventory", "Home"]
        self.combat_buttons = {}
        button_width, button_height = 150, 40
        spacing = 20
        total_width = len(button_labels) * (button_width + spacing) - spacing
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        y_pos = SCREEN_HEIGHT - 50

        for i, label in enumerate(button_labels):
            rect = pygame.Rect(start_x + i * (button_width + spacing), y_pos, button_width, button_height)
            self.combat_buttons[label] = rect
            pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
            text = font.render(label, True, WHITE)
            self.screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2,
                                    rect.y + rect.height // 2 - text.get_height() // 2))

    def get_frame(self, sheet, frame_rect):
        frame = sheet.subsurface(frame_rect)

        return frame