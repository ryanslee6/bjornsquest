import pygame
from core.game_manager import GameManager
from settings import *
import random


def main():
    
    
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    clock = pygame.time.Clock()
    

    game = GameManager(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
            game.handle_event(event)

        dt = clock.tick(60)
        
        game.update(dt)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)



    pygame.quit()

if __name__ == "__main__":
    main()
