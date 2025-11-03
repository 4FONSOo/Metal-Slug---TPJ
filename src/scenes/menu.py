import pygame
import sys

from config import WIDTH, HEIGHT, FPS

class Menu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.font = pygame.font.SysFont("arial", 36)
        self.selected = 0
        self.options = ["Marco Rossi", "Tarma Roving", "Sair"]

    def draw(self):
        self.screen.fill((20, 20, 40))
        title = self.font.render("Metal Slug 2D", True, (255, 255, 0))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (150, 150, 150)
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 250 + i * 60))

        pygame.display.flip()

    def run(self):
        while self.game.state == "menu":
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.sound.stop_music()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        self.handle_selection()

            self.clock.tick(FPS)

    def handle_selection(self):
        if self.selected == 0:
            self.game.player_choice = "Marco Rossi"
            self.game.start_game()
        elif self.selected == 1:
            self.game.player_choice = "Tarma Roving"
            self.game.start_game()
        elif self.selected == 2:
            self.game.sound.stop_music()
            pygame.quit()
            sys.exit()
