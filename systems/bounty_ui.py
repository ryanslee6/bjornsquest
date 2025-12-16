import pygame
from systems.bounty_system import BountyBoard, BountyTier, Bounty
from typing import Optional

class BountyBoardUI:
    #handles displaying bounty board and user interactions
    def __init__(self, bounty_board: BountyBoard, x: int, y: int, width: int, height: int):
        #initialize the bounty board ui
        self.bounty_board = bounty_board
        self.rect = pygame.Rect(x, y, width, height)

        #ui state
        self.is_visible = False
        self.scroll_offset = 0
        self.selected_bounty_id: Optional[int] = None

        #visual settings
        self.bg_color = (40, 40, 50)
        self.border_color = (100, 100, 120)
        self.text_color = (220, 220, 220)
        self.header_color = (200, 150, 50)

        #tier colors for visual distinction
        self.tier_colors = {
            BountyTier.EASY: (100, 200, 100), #green
            BountyTier.MEDIUM: (200, 200, 100), #yellow
            BountyTier.HARD: (200, 100, 100) #red
        }

        #fonts
        self.title_font = None
        self.text_font = None
        self.small_font = None

        #button areas (calculated when drawing)
        self.claim_buttons = {} #maps bounty_id to rect
        self.add_bounty_buttons = {} #maps tier to rect

    def initialize_fonts(self, title_size: int = 32, text_size: int = 20, small_size: int = 16):
        self.title_font = pygame.font.Font(None, title_size)
        self.text_font = pygame.font.Font(None, text_size)
        self.small_font = pygame.font.Font(None, small_size)

    def toggle_visibility(self):
        #show/hide the board
        self.is_visible = not self.is_visible

    def draw(self, surface: pygame.Surface):
        #draw the board UI
        if not self.is_visible:
            return
        
        #make sure fonts are initialized
        if self.title_font is None:
            self.initialize_fonts()

        #reset button tracking
        self.claim_buttons.clear()
        self.add_bounty_buttons.clear()

        #draw background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 3)

        #draw title
        title_text = self.title_font.render("Bounty Board", True, self.header_color)
        title_rect = title_text.get_rect(centerx = self.rect.centerx, top = self.rect.top + 10)
        surface.blit(title_text, title_rect)

        #current y position for drawing elements
        current_y = self.rect.top + 60

        #draw 'add bounty' buttons
        button_width = 100
        button_height = 30
        button_spacing = 10
        total_button_width = (button_width * 3) + (button_spacing * 2)
        start_x = self.rect.centerx - (total_button_width // 2)

        for i, tier in enumerate([BountyTier.EASY, BountyTier.MEDIUM, BountyTier.HARD]):
            button_x = start_x + (button_width + button_spacing) * i
            button_rect = pygame.Rect(button_x, current_y, button_width, button_height)

            #store button location for click detection
            self.add_bounty_buttons[tier] = button_rect

            #draw button
            color = self.tier_colors[tier]
            pygame.draw.rect(surface, color, button_rect)
            pygame.draw.rect(surface, self.border_color, button_rect, 2)

            #draw button text
            text = self.small_font.render(f"Add {tier.name}", True, (0, 0, 0))
            text_rect = text.get_rect(center = button_rect.center)
            surface.blit(text, text_rect)

        current_y += button_height + 20

        #draw a seperator line
        pygame.draw.line(
            surface,
            self.border_color,
            (self.rect.left + 10, current_y),
            (self.rect.right - 10, current_y),
            2
        )

        current_y += 20

        #draw bounties
        bounties = self.bounty_board.get_active_bounties()

        if not bounties:
            #no bounties message
            no_bounty_text = self.text_font.render(
                "No active bounties.",
                True,
                self.text_color
            )
            text_rect = no_bounty_text.get_rect(
                centerx = self.rect.centerx,
                top = current_y
            )
            surface.blit(no_bounty_text, text_rect)
        else:
            #draw each bounty
            for bounty in bounties:
                #check if still within visible area
                if current_y > self.rect.bottom - 50:
                    break  #dont draw bounties that would be cut off

                current_y = self._draw_bounty(surface, bounty, current_y)
                current_y += 10 #spacing between bounties

    def _draw_bounty(self, surface: pygame.Surface, bounty: Bounty, y_pos: int) -> int:
        #draw a single bounty entry
        padding = 10
        bounty_height = 80

        #bounty container
        bounty_rect = pygame.Rect(
            self.rect.left + padding,
            y_pos,
            self.rect.width - (padding * 2),
            bounty_height
        )

        #background color based on completion
        bg_color = (60, 80, 60) if bounty.is_completed else (50, 50, 60)
        pygame.draw.rect(surface, bg_color, bounty_rect)

        #colored left border based on tier
        tier_color = self.tier_colors[bounty.tier]
        pygame.draw.rect(
            surface,
            tier_color,
            pygame.Rect(bounty_rect.left, bounty_rect.top, 5, bounty_height)
        )

        #border
        pygame.draw.rect(surface, self.border_color, bounty_rect, 2)

        #draw bounty info
        text_x = bounty_rect.left + 15
        text_y = bounty_rect.top + 10

        #title
        title = f"[{bounty.tier.name}] Kill {bounty.target_count} {bounty.monster_name}"
        title_text = self.text_font.render(title, True, self.text_color)
        surface.blit(title_text, (text_x, text_y))

        #progress
        text_y += 25
        progress_text = self.small_font.render(
            f"Progress: {bounty.get_progress_text()}",
            True,
            self.text_color
        )
        surface.blit(progress_text, (text_x, text_y))

        #progress bar
        bar_width = 150
        bar_height = 10
        bar_x = text_x + 100
        bar_y = text_y + 5

        #background bar
        bar_bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, (100, 100, 100), bar_bg_rect)

        #progress bar fill
        fill_width = int(bar_width * bounty.get_progress_percentage())
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        fill_color = (100, 200, 100) if bounty.is_completed else tier_color
        pygame.draw.rect(surface, fill_color, fill_rect)

        #border around b ar
        pygame.draw.rect(surface, self.border_color, bar_bg_rect, 1)

        #rewards
        text_y += 20
        reward_text = self.small_font.render(
            f"Reward: {bounty.reward}",
            True,
            self.header_color
        )
        surface.blit(reward_text, (text_x, text_y))

        #claim button (if completed)
        if bounty.is_completed:
            button_width = 80
            button_height = 25
            button_x = bounty_rect.right - button_width - 10
            button_y = bounty_rect.centery - (button_height // 2)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

            #store button locations
            self.claim_buttons[bounty.id] = button_rect

            #draw button
            pygame.draw.rect(surface, (100, 200, 100), button_rect)
            pygame.draw.rect(surface, self.border_color, button_rect, 2)

            #button text
            claim_text = self.small_font.render("Claim", True, (0, 0, 0))
            claim_rect = claim_text.get_rect(center = button_rect.center)
            surface.blit(claim_text, claim_rect)

        return y_pos + bounty_height
    
    def handle_click(self, pos: tuple) -> Optional[dict]:
        #handle mouse clicks on the ui
        if not self.is_visible:
            return None
        
        #check if click is within bounty board
        if not self.rect.collidepoint(pos):
            return None
        
        #check claim buttons
        for bounty_id, button_rect in self.claim_buttons.items():
            if button_rect.collidepoint(pos):
                return {"action": "claim", "bounty_id": bounty_id}
            
        #check add bounty button
        for tier, button_rect in self.add_bounty_buttons.items():
            if button_rect.collidepoint(pos):
                return {"action": "add", "tier": tier}
            
        return None




