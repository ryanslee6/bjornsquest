import pygame
from settings import *
from settings import RARITY_COLORS


#mining window ui
class MiningWindow:
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
        self.title_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        #UI elements
        self.node_buttons = {}
        self.close_button = None

        #stats panel toggle
        self.show_stats = True

    #toggle window visibility
    def toggle(self):
        self.visible = not self.visible

    #draw the mining window
    def draw(self, surface):
        if not self.visible:
            return
        
        #draw background
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, panel)
        pygame.draw.rect(surface, self.border_color, panel, 2)

        #title
        title = self.title_font.render("Mining", True, (200, 150, 50))
        surface.blit(title, (self.x + 20, self.y + 15))

        #player mining info
        player = self.game.player
        level_text = self.font.render(f"Level: {player.mining_level}", True, self.text_color)
        surface.blit(level_text, (self.x + self.width - 150, self.y + 20))

        #xp progress bar
        progress, xp_into, xp_needed = player.get_mining_xp_progress()
        self.draw_xp_bar(surface, self.x + 20, self.y + 60, 300, 20, progress, xp_into, xp_needed)

        #gathering stats
        stats_y = self.y + 90
        power_text = self.small_font.render(f"Gathering Power: {player.gathering_power}", True, (120, 200, 120))
        surface.blit(power_text, (self.x + 20, stats_y))

        speed_text = self.small_font.render(f"Mining Speed: +{int(player.mining_speed_bonus * 100)}%", True, (120, 200, 200))
        surface.blit(speed_text, (self.x + 220, stats_y))

        #equipped tool
        tool = player.equipment.get("weapon")
        if tool and hasattr(tool, "tool_type"):
            tool_text = self.small_font.render(f"Tool: {tool.name}", True, (200, 200, 100))
            surface.blit(tool_text, (self.x + 420, stats_y))

        #mining nodes section
        nodes_y = self.y + 130
        self.draw_mining_nodes(surface, nodes_y)

        #active mining progress
        if self.game.mining_system.active_node:
            self.draw_mining_progress(surface)

        #statistics panel
        if self.show_stats:
            self.draw_statistics_panel(surface)

        #close instruction
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

    #draw avilable mining nodes
    def draw_mining_nodes(self, surface, start_y):
        self.node_buttons.clear()

        player = self.game.player
        mining_system = self.game.mining_system

        #title
        nodes_title = self.font.render("Available Nodes:", True, (200, 200, 200))
        surface.blit(nodes_title, (self.x + 20, start_y))

        #layout
        button_width = 200
        button_height = 60
        spacing = 10
        columns = 3

        current_y = start_y + 35
        col = 0

        for node_id, node_data in mining_system.node_data.items():
            node_state = mining_system.nodes[node_id]

            #calculate position
            button_x = self.x + 20 + (col * (button_width + spacing))
            button_rect = pygame.Rect(button_x, current_y, button_width, button_height)

            #check if player can mine this
            can_mine = mining_system.can_mine_node(player, node_id)
            is_depleted = node_state["depleted"]
            meets_level = player.mining_level >= node_data["required_level"]
        
            #determine button color
            if is_depleted:
                bg_color = (60, 40, 40) #dark red (depleted)
            elif not meets_level:
                bg_color = (40, 40, 40) #dark gray (locked)
            elif can_mine:
                bg_color = (50, 80, 50) #green (available)
            else:
                bg_color = (60, 60, 60) #grat (unavailable)

            #draw button
            pygame.draw.rect(surface, bg_color, button_rect)
            pygame.draw.rect(surface, (120, 120, 120), button_rect, 2)

            #node name
            name_text = self.small_font.render(node_data["name"], True, self.text_color)
            surface.blit(name_text, (button_x + 10, current_y + 10))

            #required level
            level_color = (100, 255, 100) if meets_level else (255, 100, 100)
            level_text = self.small_font.render(f"Lvl {node_data['required_level']}", True, level_color)
            surface.blit(level_text, (button_x + 10, current_y + 30))

            #success chance
            if meets_level:
                success_chance = mining_system.calculate_success_chance(
                    player.gathering_power,
                    node_data["difficulty"]
                )
                chance_pct = int(success_chance * 100)
                chance_text = self.small_font.render(f"{chance_pct}%", True, (200, 200, 100))
                surface.blit(chance_text, (button_x + 100, current_y + 30))

            #respawn timer if depleted
            if is_depleted:
                time_left = int(node_state["respawn_timer"])
                timer_text = self.small_font.render(f"{time_left}s", True, (255, 150, 150))
                surface.blit(timer_text, (button_x + 150, current_y + 30))

            #store button for click detection
            if can_mine:
                self.node_buttons[node_id] = button_rect

            #move to next position
            col += 1
            if col >= columns:
                col = 0
                current_y += button_height + spacing

    #draw current mining action progress bar
    def draw_mining_progress(self, surface):
        mining_system = self.game.mining_system

        if not mining_system.active_node:
            return
        
        node_data = mining_system.node_data[mining_system.active_node]
        progress = mining_system.get_progress_percentage()

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
        progress_text = self.font.render(f"Mining {node_data['name']}...", True, (255, 255, 255))
        text_rect = progress_text.get_rect(center = (bar_x + bar_width // 2, bar_y + bar_height // 2))
        surface.blit(progress_text, text_rect)

    #draw mining statistics
    def draw_statistics_panel(self, surface):
        mining_system = self.game.mining_system

        #panel dimensions
        panel_width = 300
        panel_height = 140
        panel_x = self.x + (self.width - panel_width) // 2
        panel_y = self.y + self.height - 50

        #background
        pygame.draw.rect(surface, (30, 30, 40), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (100, 100, 100), (panel_x, panel_y, panel_width, panel_height), 2)

        #title
        title = self.font.render("Statistics", True, (200, 150, 50))
        surface.blit(title, (panel_x + 10, panel_y + 10))

        #stats
        stats_y = panel_y + 40
        line_height = 22

        stats = [
            f"Total Attempts: {mining_system.total_attempts}",
            f"Successful: {mining_system.successful_mines}",
            f"Failed: {mining_system.failed_mines}",
            f"Success Rate: {mining_system.get_success_rate_percentage():.1f}%"
        ]

        for i, stat in enumerate(stats):
            text = self.small_font.render(stat, True, (200, 200, 200))
            surface.blit(text, (panel_x + 10, stats_y + i * line_height))

    #handle mouse clicks on mining nodes
    def handle_click(self, pos):
        if not self.visible:
            return False
        
        #check if click is ouside the window - return to gathering select
        window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if not window_rect.collidepoint(pos):
            self.visible = False
            self.game.state = "gathering_select"
            return True
        
        #check node buttons
        for node_id, button_rect in self.node_buttons.items():
            if button_rect.collidepoint(pos):
                #start mining the node
                success = self.game.mining_system.start_mining(self.game.player, node_id)
                if success:
                    print(f"[MINING] Started mining {self.game.mining_system.node_data[node_id]['name']}")
                return True
        
        return False

