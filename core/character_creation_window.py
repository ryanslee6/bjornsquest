import pygame
from settings import *
from core.font_manager import FontManager

class CharacterCreationWindow:
    def __init__(self, game):
        self.game = game
        self.visible = False

        #window dimensions
        self.width = 400
        self.height = 250
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2

        #colors
        self.bg_color = (40, 40, 50)
        self.border_color = (150, 150, 150)
        self.input_bg_color = (60, 60, 70)
        self.input_active_color = (80, 80, 100)

        #fonts
        self.font_mgr = FontManager()
        self.title_font = self.font_mgr.get(36)
        self.font = self.font_mgr.get(28)
        self.small_font = self.font_mgr.get(22)

        #input field
        self.input_text = ""
        self.input_active = True
        self.max_length = 20
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_speed = 0.5 #seconds

        #buttons
        self.create_button = None
        self.cancel_button = None

    #opens the character creation window
    def open(self):
        self.visible = True
        self.input_text = ""
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0

    #closes the character creation window
    def close(self):
        self.visible = False

    #handle pygame events for the character creation window
    def handle_event(self, event):
        if not self.visible:
            return False
        
        #handle text input
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    #enter key - create character if name is valid
                    if self.input_text.strip():
                        self.create_character()
                        return True
                    
                elif event.key == pygame.K_BACKSPACE:
                    #remove last character
                    self.input_text = self.input_text[:-1]

                elif event.key == pygame.K_ESCAPE:
                    #cancel
                    self.close()
                    return True
                
                else:
                    #add character if its valid and within length limit
                    if len(self.input_text) < self.max_length:
                        #only allow alphanumeric characters and spces
                        if event.unicode.isprintable():
                            self.input_text += event.unicode

        #handle mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            #check create button
            if self.create_button and self.create_button.collidepoint(event.pos):
                if self.input_text.strip():
                    self.create_character()
                    return True
                
            #check cancel button
            if self.cancel_button and self.cancel_button.collidepoint(event.pos):
                self.close()
                return True
            
            #check if clicked outside window
            window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if not window_rect.collidepoint(event.pos):
                self.close()
                return True
            
        return False
    
    #create a new character with the entered name
    def create_character(self):
        name = self.input_text.strip()

        if not name:
            print("[CHARACTER CREATION] Name cannot be empty!")
            return
        
        #set players name
        self.game.player.name = name

        print(f"[CHARACTER CREATION] Created character: {name}")

        #close the window and start the game
        self.close()
        self.game.state = "home"

    #update the cursor blink animation
    def update(self, dt):
        if not self.visible:
            return
        
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_blink_speed:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

    #draw character creation window
    def draw(self, surface):
        if not self.visible:
            return
        
        #draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        #draw background
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, panel)
        pygame.draw.rect(surface, self.border_color, panel, 2)

        #draw title
        title = self.title_font.render("Create Character", True, (255, 255, 255))
        surface.blit(title, (self.x + self.width // 2 - title.get_width() // 2, self.y + 20))

        #draw instructions
        instruction = self.small_font.render("Enter your character's name:", True, (200, 200, 200))
        surface.blit(instruction, (self.x + 20, self.y + 70))

        #draw input field
        input_rect = pygame.Rect(self.x + 20, self.y + 100, self.width - 40, 40)
        input_color = self.input_active_color if self.input_active else self.input_bg_color
        pygame.draw.rect(surface, input_color, input_rect)
        pygame.draw.rect(surface, self.border_color, input_rect, 2)

        #draw input text
        display_text = self.input_text
        text_surface = self.font.render(display_text, True, (255, 255, 255))
        text_x = input_rect.x + 10
        text_y = input_rect.y + (input_rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

        #draw cursor
        if self.input_active and self.cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y = input_rect.y + 8
            cursor_height = input_rect.height - 16
            pygame.draw.line(surface, (255, 255, 255),
                             (cursor_x, cursor_y),
                             (cursor_x, cursor_y + cursor_height), 2)
            
        #draw character limit info
        limit_text = self.small_font.render(
            f"{len(self.input_text)}/{self.max_length} characters",
            True,
            (150, 150, 150)
        )
        surface.blit(limit_text, (self.x + 20, self.y + 145))

        #draw buttons
        button_y = self.y + self.height - 60
        button_width = 140
        button_height = 40
        button_spacing = 20

        #create button
        total_button_width = button_width * 2 + button_spacing
        button_x = self.x + (self.width - total_button_width) // 2

        self.create_button = pygame.Rect(button_x, button_y, button_width, button_height)

        #enable/disable based on whether name is valid
        can_create = len(self.input_text.strip()) > 0
        create_color = (50, 150, 50) if can_create else (60, 60, 60)
        border_color = (100, 255, 100) if can_create else (100, 100, 100)

        pygame.draw.rect(surface, create_color, self.create_button)
        pygame.draw.rect(surface, border_color, self.create_button, 2)

        create_text = self.font.render("Create", True, (255, 255, 255))
        surface.blit(
            create_text,
            (self.create_button.centerx - create_text.get_width() // 2,
             self.create_button.centery - create_text.get_height() // 2)
        )

        #cancel button
        self.cancel_button = pygame.Rect(
            button_x + button_width + button_spacing,
            button_y,
            button_width,
            button_height
        )
        pygame.draw.rect(surface, (150, 50, 50), self.cancel_button)
        pygame.draw.rect(surface, (255, 100, 100), self.cancel_button, 2)

        cancel_text = self.font.render("Cancel", True, (255, 255, 255))
        surface.blit(
            cancel_text,
            (self.cancel_button.centerx - cancel_text.get_width() // 2,
             self.cancel_button.centery - cancel_text.get_height() // 2)
        )