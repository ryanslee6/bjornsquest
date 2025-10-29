import pygame
from settings import *
import os

class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.state = "title"
        self.title_image = self.load_image("bq_titlescreen.png")

        self.buttons = {
            "Fight": pygame.Rect(150, 500, 150, 50),
            "Gather": pygame.Rect(325, 500, 150, 50),
            "Craft": pygame.Rect(500, 500, 150, 50),
        }
        self.current_action = None

        self.start_button = pygame.Rect(SCREEN_WIDTH // 2 - 75, 450, 150, 50)

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
                    print(f"Clicked at {event.pos}")
                    self.state = "home"
            elif self.state == "home":
                for action, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        self.current_action = action
                        print(f"Action set to: {action}")

    

    def update(self):
        pass

    def draw(self):
        if self.state == "title":
            self.draw_title()
        elif self.state == "home":
            self.draw_home()

    def draw_title(self):
        self.screen.blit(self.title_image, (0, 0))
        pygame.draw.rect(self.screen, PURPLE, self.start_button)
        label = self.font.render("New Game", True, WHITE)
        self.screen.blit(label, (
            self.start_button.x + self.start_button.width // 2 - label.get_width() // 2,
            self.start_button.y + self.start_button.height // 2 - label.get_height() // 2,
        ))

    def draw_home(self):
        self.screen.fill(GRAY)
        title = self.font.render("Bjorns Quest", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        for text, rect in self.buttons.items():
            pygame.draw.rect(self.screen, PURPLE if self.current_action == text else LIGHT_GRAY, rect)
            label = self.font.render(text, True, WHITE)
            self.screen.blit(label, (rect.x + rect.width // 2 - label.get_width() // 2,
                                     rect.y + rect.height // 2 - label.get_height() // 2))