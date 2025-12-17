import pygame
from settings import *
from datetime import datetime

class SaveSelectWindow:
    #ui window for selecting a save file to load
    def __init__(self, game, save_system):
        self.game = game
        self.save_system = save_system
        self.visible = False

        #window dimensions
        self.width = 600
        self.height = 500
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2

        #colors
        self.bg_color = (30, 30, 40)
        self.border_color = (150, 150, 150)
        self.highlight_color = (60, 60, 80)
        self.selected_color = (80, 120, 180)

        #fonts
        self.title_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        #save list
        self.saves = []
        self.selected_index = None
        self.scroll_offset = 0
        self.max_scroll = 0

        #buttons
        self.load_button = None
        self.delete_button = None
        self.cancel_button = None

        #scrolling
        self.item_height = 80
        self.visible_items = 4

        #confirmation dialog for delte
        self.delete_confimation_visible = False
        self.confirm_yes_button = None
        self.confirm_no_button = None

    #open the window and refresh the save list
    def open(self):
        self.visible = True
        self.refresh_saves()
        self.selected_index = None
        self.scroll_offset = 0
        self.delete_confimation_visible = False

    #close the window
    def close(self):
        self.visible = False
        self.delete_confimation_visible = False

    #reload the list of available saves
    def refresh_saves(self):
        self.saves = self.save_system.list_saves()

        #calculate scrolling limits
        total_height = len(self.saves) * self.item_height
        visible_height = self.visible_items * self.item_height
        self.max_scroll = max(0, total_height - visible_height)

        #clamp scroll offset
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)

    #handle pygame events (mouse clicks, scrolling)
    def handle_event(self, event):
        if not self.visible:
            return False
        
        #handle delete confirmation dialog
        if self.delete_confimation_visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.confirm_yes_button and self.confirm_yes_button.collidepoint(event.pos):
                    #delete the selected save
                    if self.selected_index is not None:
                        save = self.saves[self.selected_index]
                        if self.save_system.delete_save(save['path']):
                            self.refresh_saves()
                            self.selected_index = None
                    self.delete_confimation_visible = False
                    return True
                
                if self.confirm_no_button and self.confirm_no_button.collidepoint(event.pos):
                    #cancel delete
                    self.delete_confimation_visible = False
                    return True
                
            return True
        
        #mouse wheel scrolling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: #scroll up
                self.scroll_offset = max(0, self.scroll_offset - self.item_height)
                return True
            elif event.button == 5: #scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.item_height)
                return True
            
        #mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            #check save list clicks
            list_y_start = self.y + 60
            list_height = self.visible_items * self.item_height

            for i, save in enumerate(self.saves):
                item_y = list_y_start + (i * self.item_height) - self.scroll_offset

                #skip if outside visible area
                if item_y < list_y_start or item_y + self.item_height > list_y_start + list_height:
                    continue

                item_rect = pygame.Rect(self.x + 10, item_y, self.width - 20, self.item_height - 5)

                if item_rect.collidepoint(event.pos):
                    self.selected_index = i
                    return True
                
            #check button clicks
            if self.load_button and self.load_button.collidepoint(event.pos):
                if self.selected_index is not None:
                    self.load_selected_save()
                return True
            
            if self.delete_button and self.delete_button.collidepoint(event.pos):
                if self.selected_index is not None:
                    #show confirmation dialog
                    self.delete_confimation_visible = True
                return True

            if self.cancel_button and self.cancel_button.collidepoint(event.pos):
                self.close()
                return True

            #if click was outside element, close the window
            window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if not window_rect.collidepoint(event.pos):
                self.close()
                return True
        
        return False
    
    #load the currently selected save file
    def load_selected_save(self):
        if self.selected_index is None or self.selected_index >= len(self.saves):
            return
        
        save = self.saves[self.selected_index]
        print(f"[SAVE SELECT] Loading: {save['filename']}")

        #load the save
        game_state = self.save_system.load_game(
            save['path'],
            self.game.player,
            self.game.items
        )

        if game_state is not None:
            #apply game state
            if 'monster_page' in game_state:
                self.game.current_monster_page = game_state['monster_page']

            #start the game
            self.game.state = "home"
            self.close()

            #mark inventory as dirty to refresh the ui
            if hasattr(self.game, 'inventory_window'):
                self.game.inventory_window.mark_dirty()

            print(f"[SAVE SELECT] Load successful!")
        else:
            print(f"[SAVE SELECT] Load failed!")

    #draw the save selection window
    def draw(self, surface):
        if not self.visible:
            return
        
        #draw background
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, self.bg_color, (0, 0, self.width, self.height))
        pygame.draw.rect(panel, self.border_color, (0, 0, self.width, self.height), 2)
        surface.blit(panel, (self.x, self.y))

        #draw title
        title = self.title_font.render("Load Game", True, (255, 255, 255))
        surface.blit(title, (self.x + self.width // 2 - title.get_width() // 2, self.y + 15))

        #draw the save list
        self.draw_save_list(surface)

        #draw buttons
        self.draw_buttons(surface)

        #draw delete confirmation if visible
        if self.delete_confimation_visible:
            self.draw_delete_confirmation(surface)

    
    #draw scrollable list of save files
    def draw_save_list(self, surface):
        list_y_start = self.y + 60
        list_height = self.visible_items * self.item_height
        list_rect = pygame.Rect(self.x + 10, list_y_start, self.width - 20, list_height)

        #background for list area
        pygame.draw.rect(surface, (20, 20, 30), list_rect)
        pygame.draw.rect(surface, (100, 100, 100), list_rect, 1)

        #set clipping region
        surface.set_clip(list_rect)

        #draw each save
        if not self.saves:
            #no saves found message
            no_saves_text = self.font.render("No save files found", True, (150, 150, 150))
            surface.blit(
                no_saves_text,
                (self.x + self.width // 2 - no_saves_text.get_width() // 2, list_y_start + 40)
            )
        else:
            for i, save in enumerate(self.saves):
                item_y = list_y_start + (i * self.item_height) - self.scroll_offset

                #skip if outside visible area
                if item_y + self.item_height < list_y_start or item_y > list_y_start + list_height:
                    continue

                self.draw_save_item(surface, save, item_y, i == self.selected_index)

        #clear clipping region
        surface.set_clip(None)

        #draw scrollbar if needed
        if self.max_scroll > 0:
            self.draw_scrollbar(surface, list_rect)

    #draw a single save file item
    def draw_save_item(self, surface, save, y, is_selected):
        item_rect = pygame.Rect(self.x + 15, y, self.width - 30, self.item_height - 5)

        #background
        if is_selected:
            pygame.draw.rect(surface, self.selected_color, item_rect)
        else:
            pygame.draw.rect(surface, self.highlight_color, item_rect)

        pygame.draw.rect(surface, (120, 120, 120), item_rect, 1)

        #character name and level
        char_text = f"{save['character_name']} - Level {save['level']}"
        char_surf = self.font.render(char_text, True, (255, 255, 255))
        surface.blit(char_surf, (item_rect.x + 10, item_rect.y + 10))

        #save date
        try:
            save_date = datetime.fromisoformat(save['save_date'])
            date_text = save_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_text = save['save_date']

        date_surf = self.small_font.render(date_text, True, (180, 180, 180))
        surface.blit(date_surf, (item_rect.x + 10, item_rect.y + 35))

        #filename
        filename_surf = self.small_font.render(save['filename'], True, (150, 150, 150))
        surface.blit(filename_surf, (item_rect.x + 10, item_rect.y + 55))

    #draw a scrollbar for the save list
    def draw_scrollbar(self, surface, list_rect):
        scrollbar_x = list_rect.right - 8
        scrollbar_y = list_rect.top
        scrollbar_height = list_rect.height

        #track
        track_rect = pygame.Rect(scrollbar_x, scrollbar_y, 6, scrollbar_height)
        pygame.draw.rect(surface, (50, 50, 50), track_rect)

        #thumb
        thumb_height = max(20, int((self.visible_items * self.item_height) / (len(self.saves) * self.item_height) * scrollbar_height))
        scroll_ratio = self.scroll_offset / self.max_scroll if self.max_scroll > 0 else 0
        thumb_y = scrollbar_y + int(scroll_ratio * (scrollbar_height - thumb_height))

        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, 6, thumb_height)
        pygame.draw.rect(surface, (150, 150, 150), thumb_rect)

    #draw the action buttons
    def draw_buttons(self, surface):
        button_y = self.y + self.height - 60
        button_height = 40
        button_spacing = 10

        #calculate button positions
        button_width = (self.width - 40 - button_spacing * 2) // 3

        #load button
        self.load_button = pygame.Rect(
            self.x + 20,
            button_y,
            button_width,
            button_height
        )

        #delete button
        self.delete_button = pygame.Rect(
            self.x + 20 + button_width + button_spacing,
            button_y,
            button_width,
            button_height
        )

        #cancel button
        self.cancel_button = pygame.Rect(
            self.x + 20 + (button_width + button_spacing) * 2,
            button_y,
            button_width,
            button_height
        )

        #draw load button
        load_color = (50, 150, 50) if self.selected_index is not None else (60, 60, 60)
        pygame.draw.rect(surface, load_color, self.load_button)
        pygame.draw.rect(surface, (100, 200, 100) if self.selected_index is not None else (100, 100, 100), self.load_button, 2)
        load_text = self.font.render("Load", True, (255, 255, 255))
        surface.blit(
            load_text,
            (self.load_button.centerx - load_text.get_width() // 2,
             self.load_button.centery - load_text.get_height() // 2)
        )

        #draw delete button
        delete_color = (150, 50, 50) if self.selected_index is not None else (60, 60, 60)
        pygame.draw.rect(surface, delete_color, self.delete_button)
        pygame.draw.rect(surface, (200, 100, 100) if self.selected_index is not None else (100, 100, 100), self.delete_button, 2)
        delete_text = self.font.render("Delete", True, (255, 255, 255))
        surface.blit(
            delete_text,
            (self.delete_button.centerx - delete_text.get_width() // 2,
             self.delete_button.centery - delete_text.get_height() // 2)
        )

        #draw cancel button
        pygame.draw.rect(surface, (80, 80, 80), self.cancel_button)
        pygame.draw.rect(surface, (150, 150, 150), self.cancel_button, 2)
        cancel_text = self.font.render("Cancel", True, (255, 255, 255))
        surface.blit(
            cancel_text,
            (self.cancel_button.centerx - cancel_text.get_width() // 2,
             self.cancel_button.centery - cancel_text.get_height() // 2)
        )

    #draw the delete confirmation dialog
    def draw_delete_confirmation(self, surface):
        #semi transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        #confirmation dialog
        dialog_width = 400
        dialog_height = 200
        dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
        dialog_y = SCREEN_HEIGHT // 2 - dialog_height // 2

        #background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, (40, 40, 50), dialog_rect)
        pygame.draw.rect(surface, (200, 200, 200), dialog_rect, 2)

        #warning text
        warning_text = self.font.render("Delete this save?", True, (255, 200, 200))
        surface.blit(
            warning_text,
            (dialog_x + dialog_width // 2 - warning_text.get_width() // 2, dialog_y + 30)
        )

        #character info
        if self.selected_index is not None:
            save = self.saves[self.selected_index]
            char_text = self.small_font.render(
                f"{save['character_name']} - Level {save['level']}",
                True,
                (255, 255, 255)
            )
            surface.blit(
                char_text,
                (dialog_x + dialog_width // 2 - char_text.get_width() // 2, dialog_y + 70)
            )
        
        #buttons
        button_width = 120
        button_height = 40
        button_y = dialog_y + dialog_height - 60

        #yes button
        self.confirm_yes_button = pygame.Rect(
            dialog_x + 60,
            button_y,
            button_width,
            button_height
        )
        pygame.draw.rect(surface, (150, 50, 50), self.confirm_yes_button)
        pygame.draw.rect(surface, (200, 100, 100), self.confirm_yes_button, 2)
        yes_text = self.font.render("Yes", True, (255, 255, 255))
        surface.blit(
            yes_text,
            (self.confirm_yes_button.centerx - yes_text.get_width() // 2,
            self.confirm_yes_button.centery - yes_text.get_height() // 2)
        )

        #no button
        self.confirm_no_button = pygame.Rect(
            dialog_x + dialog_width - 180,
            button_y,
            button_width,
            button_height
        )
        pygame.draw.rect(surface, (50, 150, 50), self.confirm_no_button)
        pygame.draw.rect(surface, (100, 200, 100), self.confirm_no_button, 2)
        no_text = self.font.render("No", True, (255, 255, 255))
        surface.blit(
            no_text,
            (self.confirm_no_button.centerx - no_text.get_width() // 2,
             self.confirm_no_button.centery - no_text.get_height() // 2)
        )