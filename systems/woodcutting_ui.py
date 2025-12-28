import pygame
from settings import *
from settings import RARITY_COLORS
from core.font_manager import FontManager

class WoocuttingWindow:
    def __init__(self, game):
        self.game = game
        self.visible = False

        #window dimensions
        self.width = 700
        self.height = 550
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2

        #colors
        self.bg_color = (35, 35, 45)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)

        #fonts
        self.font_mgr = FontManager()
        self.title_font = self.font_mgr.get(36)
        self.font = self.font_mgr.get(24)
        self.small_font = self.font_mgr.get(20)

        #ui elements
        self.tree_buttons = {}
        self.close_button = None

        #stats panel toggle
        self.show_stats = True

    #toggle window visibility
    def toggle(self):
        self.visible = not self.visible

    #draw the woodcutting window
    def draw(self, surface):
        if not self.visible:
            return
        
        #draw background
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, panel)
        pygame.draw.rect(surface, self.border_color, panel, 2)

        #title
        title = self.title_font.render("Woodcutting", True, (200, 150, 50))
        surface.blit(title, (self.x + 20, self.y + 15))

        #player woodcutting info
        player = self.game.player
        level_text = self.font.render(f"Level: {player.woodcutting_level}", True, self.text_color)
        surface.blit(level_text, (self.x + self.width - 150, self.y + 20))

        #xp progress bar
        progress, xp_into, xp_needed = player.get_woodcutting_xp_progress()
        self.draw_xp_bar(surface, self.x + 20, self.y + 60, 300, 20, progress, xp_into, xp_needed)

        #gathering stats
        stats_y = self.y + 90
        power_text = self.small_font.render(f"Gathering Power: {player.gathering_power}", True, (120, 120, 120))
        surface.blit(power_text, (self.x + 20, stats_y))

        speed_text = self.small_font.render(f"Chopping Speed: +{int(player.woodcutting_speed_bonus * 100)}%", True, (120, 200, 200))
        surface.blit(speed_text, (self.x + 220, stats_y))

        #equipped tool
        tool = player.equipment.get("weapon")
        if tool and hasattr(tool, "tool_type"):
            tool_text = self.small_font.render(f"Tool: {tool.name}", True, (200, 200, 100))
            surface.blit(tool_text, (self.x + 420, stats_y))

        #trees section
        trees_y = self.y + 130
        self.draw_trees(surface, trees_y)

        #woodcutting xp bar
        self.draw_woodcutting_xp_bar(surface)

        #active chopping progress
        if self.game.woodcutting_system.active_tree:
            self.draw_chopping_progress(surface)

        #statistics panel
        if self.show_stats:
            self.draw_statistics_panel(surface)

        #close instructions
        close_text = self.small_font.render("Click outside to close", True, (150, 150, 150))
        surface.blit(close_text, (self.x + 20, self.y + self.height - 30))

    #draw xp progress bar
    def draw_xp_bar(self, surface, x, y, width, height, progress, xp_into, xp_needed):
        #background
        pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))

        #fill
        fill_width = int(width * progress)
        if fill_width > 0:
            pygame.draw.rect(surface, (100, 200, 100), (x, y, fill_width, height))

        #border
        pygame.draw.rect(surface, (100, 100, 100), (x, y, width, height), 1)

        #text
        if xp_needed > 0:
            text = self.small_font.render(f"{xp_into}/{xp_needed} XP", True, (255, 255, 255))
        else:
            text = self.small_font.render("Max Level", True, (255, 215, 0))

        text_rect = text.get_rect(center = (x + width // 2, y + height // 2))
        surface.blit(text, text_rect)

    #draw available trees
    def draw_trees(self, surface, start_y):
        self.tree_buttons.clear()

        player = self.game.player
        woodcutting_system = self.game.woodcutting_system

        #title
        trees_title = self.font.render("Available Trees:", True, (200, 200, 200))
        surface.blit(trees_title, (self.x + 20, start_y))

        #layout
        button_width = 200
        button_height = 60
        spacing = 10
        columns = 3

        current_y = start_y + 35
        col = 0

        for tree_id, tree_data in woodcutting_system.tree_data.items():
            tree_state = woodcutting_system.trees[tree_id]

            #calculate position
            button_x = self.x + 20 + (col * (button_width + spacing))
            button_rect = pygame.Rect(button_x, current_y, button_width, button_height)

            #check if player can chop this
            can_chop = woodcutting_system.can_chop_tree(player, tree_id)
            is_depleted = tree_state["depleted"]
            meets_level = player.woodcutting_level >= tree_data["required_level"]

            #determine button color
            if is_depleted:
                bg_color = (60, 40, 40) #dark red
            elif not meets_level:
                bg_color = (40, 40, 40) #dark gray
            elif can_chop:
                bg_color = (50, 80, 50) #green
            else:
                bg_color = (60, 60, 60) #gray

            #draw button
            pygame.draw.rect(surface, bg_color, button_rect)
            pygame.draw.rect(surface, (120, 120, 120), button_rect, 2)

            #tree name
            name_text = self.small_font.render(tree_data["name"], True, self.text_color)
            surface.blit(name_text, (button_x + 10, current_y + 10))

            #required level
            level_color = (100, 255, 100) if meets_level else (255, 100, 100)
            level_text = self.small_font.render(f"Lvl {tree_data['required_level']}", True, level_color)
            surface.blit(level_text, (button_x + 10, current_y + 30))

            #success chance
            if meets_level:
                success_chance = woodcutting_system.calculate_success_chance(
                    player.gathering_power,
                    tree_data["difficulty"]
                )
                chance_pct = int(success_chance * 100)
                chance_text = self.small_font.render(f"{chance_pct}%", True, (200, 200, 100))
                surface.blit(chance_text, (button_x + 100, current_y + 30))

            #respawn timer if depleted
            if is_depleted:
                time_left = int(tree_state["respawn_timer"])
                timer_text = self.small_font.render(f"{time_left}s", True, (255, 150, 150))
                surface.blit(timer_text, (button_x + 150, current_y + 30))

            #store button for click detection
            if can_chop:
                self.tree_buttons[tree_id] = button_rect

            #move to next position
            col += 1
            if col >= columns:
                col = 0
                current_y += button_height + spacing

    #draw current chopping action progress bar
    def draw_chopping_progress(self, surface):
        woodcutting_system = self.game.woodcutting_system

        if not woodcutting_system.active_tree:
            return
        
        tree_data = woodcutting_system.tree_data[woodcutting_system.active_tree]
        progress = woodcutting_system.get_progress_percentage()

        #progress bar position
        bar_width = 400
        bar_height = 30
        bar_x = self.x + (self.width - bar_width) // 2
        bar_y = self.y + self.height - 120

        #background
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))

        #fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(surface, (100, 150, 200), (bar_x, bar_y, fill_width, bar_height))

        #border
        pygame.draw.rect(surface, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height), 2)

        #text
        progress_text = self.font.render(f"Chopping {tree_data['name']}...", True, (255, 255, 255))
        text_rect = progress_text.get_rect(center = (bar_x + bar_width // 2, bar_y + bar_height // 2))
        surface.blit(progress_text, text_rect)

    #draw woodcutting statistics
    def draw_statistics_panel(self, surface, override_x = None, override_y = None):
        woodcutting_system = self.game.woodcutting_system

        panel_width = 300
        panel_height = 200
        
        if override_x is not None and override_y is not None:
            panel_x = override_x
            panel_y = override_y
        else:
            panel_x = SCREEN_WIDTH - 320
            panel_y = 20

        #background
        pygame.draw.rect(surface, (30, 30, 40), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (100, 100, 100), (panel_x, panel_y, panel_width, panel_height), 2)

        #stats
        stats_y = panel_y + 10
        line_height = 22
        player = self.game.player

        stats = [
            f"Level: {player.woodcutting_level}",
            f"Gathering Power: {player.gathering_power}",
            f"Chopping Speed: +{int(player.woodcutting_speed_bonus * 100)}%",
            "",
            f"Total Attempts: {woodcutting_system.total_attempts}",
            f"Successful: {woodcutting_system.successful_chops}",
            f"Failed: {woodcutting_system.failed_chops}",
            f"Success Rate: {woodcutting_system.get_success_rate_percentage():.1f}%"
        ]

        for i, stat in enumerate(stats):
            if stat:
                text = self.small_font.render(stat, True, (200, 200, 200))
                surface.blit(text, (panel_x + 10, stats_y + i * line_height))

    #draw woodcutting xp bar
    def draw_woodcutting_xp_bar(self, surface):
        player = self.game.player

        #get xp progress
        progress, xp_into, xp_needed = player.get_woodcutting_xp_progress()

        #position the bar below the progress bar
        bar_width = 400
        bar_height = 25
        bar_x = SCREEN_WIDTH // 2 - bar_height // 2
        bar_y = SCREEN_HEIGHT - 80

        #background
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))

        #fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(surface, (120, 120, 120), (bar_x, bar_y, fill_width, bar_height))

        #border
        pygame.draw.rect(surface, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height), 2)

        #text show level and percentage
        if xp_needed > 0:
            percent = int(progress * 100)
            text = self.font.render(f"Level {player.woodcutting_level} - {percent}%", True, (255, 255, 255))
        else:
            text = self.font.render(f"Level {player.woodcutting_level} - Max", True, (255, 215, 0))

        text_rect = text.get_rect(center = (bar_x + bar_width // 2, bar_y + bar_height // 2))
        surface.blit(text, text_rect)

    #handle mouse clicks on trees
    def handle_click(self, pos):
        if not self.visible:
            return False
        
        #check if click is outside the window - return to gathering select
        window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if not window_rect.collidepoint(pos):
            self.visible = False
            self.game.state = "gathering_select"
            return True
        
        #check for buttons
        for tree_id, button_rect in self.tree_buttons.items():
            if button_rect.collidepoint(pos):
                #start chopping the tree
                success = self.game.woodcutting_system.start_chopping(self.game.player, tree_id)
                if success:
                    print(f"[WOODCUTTING] Started chopping {self.game.woodcutting_system.tree_data[tree_id]['name']}")
                return True
            
        return False






