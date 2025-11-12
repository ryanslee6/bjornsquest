import pygame
from settings import *

spell_slots = {}

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

        gold_text = self.font.render(f"Gold: {self.game.player.gold}", True, (255, 215, 0))
        screen.blit(gold_text, (x + self.width - gold_text.get_width() - 20, y + 10))

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
    
class VendorWindow:
    def __init__(self, game):
        self.game = game
        self.width = 400
        self.height = 360
        self.bg_color = (35, 35, 45)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font(None, 24)
        self.item_rects = []

        self.items_for_sale = [
            {"id": "health_potion_small", "price": 10},
            {"id": "mana_potion_small", "price": 12},
            #{"id": "vial_of_water", "price": 5},
            {"id": "Auto Attack", "price": 5}
        ]

    def draw(self, screen):
        from settings import RARITY_COLORS
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2

        pygame.draw.rect(screen, self.bg_color, (x, y, self.width, self.height))
        pygame.draw.rect(screen, self.border_color, (x, y, self.width, self.height), 2)

        title = self.font.render("Vendor", True, self.text_color)


        total_gold = self.game.player.get_total_gold()
        gold_text = self.font.render(f"Gold: {total_gold}", True, (255, 220, 100))
        screen.blit(gold_text, (x + self.width - 140, y+ 10))

        y_offset = 50
        self.item_rects.clear()
        for entry in self.items_for_sale:
            item = self.game.items.get(entry["id"])
            
            
            rect = pygame.Rect(x + 10, y + y_offset, self.width - 20, 30)
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1)

            if item and hasattr(item, "rarity"):
                rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
                name_text = item.name
            else:
                rarity_color = (255, 255, 255)
                name_text = entry["id"]

            item_text = self.font.render(f"{name_text} - {entry['price']}g", True, rarity_color)
            screen.blit(item_text, (rect.x + 8, rect.y + 5))

            self.item_rects.append((rect, entry))
            y_offset += 36

        # Close text
        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        screen.blit(close_text, (x + 10, y + self.height - 25))

    def handle_click(self, pos):
        for rect, entry in self.item_rects:
            if rect.collidepoint(pos):                
                price = entry["price"]
                item_id = entry["id"]
                
                if self.game.player.get_total_gold() < price:
                    print("[VENDOR] Not enough gold!")
                    return True
                
                self.game.player.spend_gold(price)

                if item_id.lower() == "auto attack":
                    if not self.game.player.auto_combat_unlocked:
                        self.game.player.auto_combat_unlocked = True
                        print("[VENDOR] Auto Combat unlocked!")
                    else:
                        print("[VENDOR] Auto Combat already unlocked.")
                    return True
                
                self.game.player.add_item(item_id, 1)
                print(f"[VENDOR] Purchased {item_id} for {price} gold.")
                return True
        return False
    
    def is_click_outside(self, pos):
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2
        rect = pygame.Rect(x, y, self.width, self.height)
        return not rect.collidepoint(pos)
    
class SpellbookWindow:
    def __init__(self, player, spellbook, on_assign_callback):
        self.player = player
        self.spellbook = spellbook
        self.on_assign_callback = on_assign_callback
        self.visible = False

        self.width = 360
        self.height = 300
        self.x = 220
        self.y = 150
        self.bg_color = (20, 20, 20)
        self.border_color = (100, 100, 100)

        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 30)

        self.selected_slot = None
    

    def toggle(self, slot_index = None):
        was_visible = self.visible
        self.visible = not self.visible
        #self.selected_slot = slot_index if self.visible else None
        
        if self.visible and slot_index is not None:
            self.selected_slot = slot_index
        else:
            self.selected_slot = None
        
        print(f"📖 Spellbook {'opened' if self.visible else 'closed'} (slot={slot_index})")
        
        if not self.visible and hasattr(self.player.game, "selected_spell_slot"):
            self.player.game.selected_spell_slot = None

    def draw(self, surface):
        if not self.visible:
            return
        
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, panel)
        pygame.draw.rect(surface, self.border_color, panel, 2)

        title = self.title_font.render("Spellbook", True, (255, 255, 255))
        surface.blit(title, (self.x + 10, self.y + 10))

        start_y = self.y + 50

        for i, spell in enumerate(self.spellbook):
            text = f"{spell.name}"
            color = (200, 200, 255)
            surf = self.font.render(text, True, color)
            rect = surf.get_rect(topleft = (self.x + 20, start_y + i * 32))
            surface.blit(surf, rect)

            pygame.draw.rect(surface, (60, 60, 60), rect.inflate(8, 4), 1)
            spell.click_rect = rect.inflate(8, 4)

        mouse_pos = pygame.mouse.get_pos()
        for spell in self.spellbook:
            if hasattr(spell, "click_rect") and spell.click_rect.collidepoint(mouse_pos):
                self.draw_spell_tooltip(surface, spell, mouse_pos)
                break

    def handle_click(self, pos):
        if not self.visible:
            return False
        
        for i, spell in enumerate(self.spellbook):
            if hasattr(spell, "click_rect") and spell.click_rect.collidepoint(pos):
                if self.selected_slot is None:
                    print(f"[INFO] Clicked {spell.name}, but no slot is selected.")
                    return True   
                
                print(f"🪄 Selected {spell.name} for Slot {self.selected_slot}")
                if self.on_assign_callback:
                    self.on_assign_callback(self.selected_slot, spell)
                             
                self.toggle(None)
                return True
        return False
    
    def draw_spell_tooltip(self, surface, spell, mouse_pos):
        #print(f"[UI DEBUG] Tooltip surface id={id(surface)}")
        equipped_slot = None
        #find which slot spell is assigned to (if any)
        if hasattr(self.player.game, "spell_slots"):
            for slot, s in self.player.game.spell_slots.items():
                if s.name == spell.name:
                    equipped_slot = slot
                    break
        lines = [
            f"{spell.name}",
            f"MP Cost: {spell.mana_cost}",
            f"Cooldown: {spell.cooldown // 1000}s",
            f"Damage: {getattr(spell, 'power', '?')}",
        ]
        if equipped_slot:
            lines.append(f"Equipped to Slot {equipped_slot}")
        else:
            lines.append("Not equipped")

        font = pygame.font.Font(None, 22)
        padding = 8
        width = max(font.size(line)[0] for line in lines) + padding * 2
        height = len(lines) * 22 + padding * 2
        x, y = mouse_pos
        
        screen_w, screen_h = surface.get_size()
        x = min(x, screen_w - width - 15)
        y = min(y, screen_h - height - 15)
        rect = pygame.Rect(x + 15, y+ 15, width, height)

        pygame.draw.rect(surface, (30, 30, 30), rect)
        pygame.draw.rect(surface, (150, 150, 150), rect, 2)

        for i, line in enumerate(lines):
            surf = font.render(line, True, (255, 255, 255))
            surface.blit(surf, (rect.x + padding, rect.y + padding + i * 22))