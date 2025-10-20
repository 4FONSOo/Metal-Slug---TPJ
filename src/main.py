import pygame
from config import *
from game_state import GameStateManager

def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    gsm = GameStateManager(screen)
    gsm.change_state('menu')

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            gsm.handle_event(event)

        gsm.update(dt)
        gsm.render()
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    run()