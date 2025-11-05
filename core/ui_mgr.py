import pygame
from settings import *

class InventoryWindow:
    def __init__(self, game):
        self.game = game
        self.width = 350
        self.height = 400
        self.bg_color = (40, 40, 40)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font(None, 22)

        self.item_rects = {}

    def draw(self, screen):
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2

        pygame.draw.rect(screen, self.bg_color, (x, y, self.width, self.height))
        pygame.draw.rect(screen, self.border_color, (x, y, self.width, self.height), 2)

        title = self.font.render("Inventory", True, self.text_color)
        screen.blit(title, (x + 10, y + 10))

        self.item_rects = {}
        y_offset = 40

        for item_id, qty in self.game.player.inventory.items():
            item = self.game.items.get(item_id)

            rect = pygame.Rect(x + 10, y + y_offset, self.width - 20, 28)
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 1)

            text = self.font.render(f"{item.name} x{qty}", True, self.text_color)
            screen.blit(text, (rect.x + 5, rect.y + 5))

            self.item_rects[item_id] = rect
            y_offset += 32

            mouse_pos = pygame.mouse.get_pos()
            for item_id, rect in self.item_rects.items():
                if rect.collidepoint(mouse_pos):
                    item = self.game.items.get(item_id)
                    if hasattr(item, "tooltip_text"):
                        self.draw_tooltip(screen, item.tooltip_text(), mouse_pos)
                    break

        # Close text
        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        screen.blit(close_text, (x + 10, y + self.height - 25))

    def draw_tooltip(self, screen, lines, mouse_pos):
        padding = 6
        line_height = 18
        width = 0

        for line in lines:
            text_surface = self.font.render(line, True, (255, 255, 255))
            width = max(width, text_surface.get_width())

        height = line_height * len(lines)

        x, y = mouse_pos
        x += 16
        y += 16

        pygame.draw.rect(screen, (20, 20, 20), (x, y, width + padding * 2, height + padding * 2))
        pygame.draw.rect(screen, (180, 180, 180), (x, y, width + padding * 2, height + padding * 2), 1)

        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (x + padding, y + padding + i * line_height))

    def click(self, pos, button):
        #right click uses item if consumable
        if button == 3:
            for item_id, rect in self.item_rects.items():
                if rect.collidepoint(pos):
                    item = self.game.items.get(item_id)
                    if item.type == "consumable":
                        self.game.player.use_item(item_id, self.game.items)
                        print(f"[ITEM] Used {item.name}")
                        return True
        return False


    def click_outside(self, pos):
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2
        rect = pygame.Rect(x, y, self.width, self.height)
        return not rect.collidepoint(pos)