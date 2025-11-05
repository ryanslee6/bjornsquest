import pygame
from settings import *

class InventoryWindow:
    def __init__(self, game):
        self.game = game
        self.width = 350
        self.height = 280
        self.bg_color = (40, 40, 40)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font(None, 22)

        self.item_rects = []

    def draw(self, screen):
        from settings import RARITY_COLORS
        offset_x = 150
        x = SCREEN_WIDTH // 2 - self.width // 2 + offset_x
        y = SCREEN_HEIGHT // 2 - self.height // 2

        #pygame.draw.rect(screen, self.bg_color, (x, y, self.width, self.height))
        #pygame.draw.rect(screen, self.border_color, (x, y, self.width, self.height), 2)
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        bg_with_alpha = (*self.bg_color, 180)

        pygame.draw.rect(panel, bg_with_alpha, (0, 0, self.width, self.height))
        pygame.draw.rect(panel, self.border_color, (0, 0, self.width, self.height), 2)

        screen.blit(panel, (x, y))

        title = self.font.render("Inventory", True, self.text_color)
        screen.blit(title, (x + 10, y + 10))

        self.item_rects = []
        y_offset = 40

        

        #for item_id, qty in self.game.player.inventory.items():
        #    item = self.game.items.get(item_id)
        for entry in self.game.player.inventory:
            item = self.game.items.get(entry["id"])
            rect = pygame.Rect(x + 10, y + y_offset, self.width - 20, 28)
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 1)


            if item.stackable:
                display_name = f"{item.name} x {entry['qty']}"
            else:
                display_name = item.name

            rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
            
            text = self.font.render(display_name, True, rarity_color)
            screen.blit(text, (rect.x + 5, rect.y + 5))
            
            self.item_rects.append((rect, entry))
            y_offset += 32
            
            
            #text = self.font.render(f"{item.name} x{qty}", True, self.text_color)
            #screen.blit(text, (rect.x + 5, rect.y + 5))                        
            #text = self.font.render(f"{item.name} x {qty}", True, rarity_color)
            #screen.blit(text, (rect.x + 5, rect.y + 5))
            #if item.stackable:
            #    display_name = f"{item.name} x {qty}"
            #else:
            #    display_name = item.name
            #text = self.font.render(display_name, True, rarity_color)
            #screen.blit(text, (rect.x + 5, rect.y + 5))


            

        mouse_pos = pygame.mouse.get_pos()
        for rect, entry in self.item_rects:
            if rect.collidepoint(mouse_pos):
                item = self.game.items.get(entry["id"])
                self.draw_tooltip(screen, item.tooltip_text(), mouse_pos )
                #if hasattr(item, "tooltip_text"):
                #    self.draw_tooltip(screen, item.tooltip_text(), mouse_pos)
                break

        # Close text
        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        screen.blit(close_text, (x + 10, y + self.height - 25))

    def draw_tooltip(self, screen, lines, mouse_pos):
        from settings import RARITY_COLORS

        padding = 6
        line_height = 18
        
        width = max(self.font.render(line, True, (255, 255, 255)).get_width() for line in lines)
        height = line_height * len(lines)

        for line in lines:
            text_surface = self.font.render(line, True, (255, 255, 255))
            width = max(width, text_surface.get_width())

        x, y = mouse_pos
        x += 16
        y += 16

        pygame.draw.rect(screen, (20, 20, 20), (x, y, width + padding * 2, height + padding * 2))
        pygame.draw.rect(screen, (180, 180, 180), (x, y, width + padding * 2, height + padding * 2), 1)

        rarity_color = (255, 255, 255) #fallback
        item_name = lines[0]
        #item = None

        #mouse_item_id = next((iid for iid, r in self.item_rects.items() if r.collidepoint(mouse_pos)), None)
        #if mouse_item_id:
        #    item = self.game.items.get(mouse_item_id)

        
        for rect, entry in self.item_rects:
            if rect.collidepoint(mouse_pos):
                item = self.game.items.get(entry["id"])
                rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
                break

        name_surface = self.font.render(item_name, True, rarity_color)
        screen.blit(name_surface, (x + padding, y + padding))        
        
        for i, line in enumerate(lines[1:], start = 1):
            text_surface = self.font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (x + padding, y + padding + i * line_height))

    def click(self, pos, button):
        #right click uses item if consumable
        if button == 3:
            for rect, entry in self.item_rects:
                if rect.collidepoint(pos):
                    item_id = entry["id"]
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