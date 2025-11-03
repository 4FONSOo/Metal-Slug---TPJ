import pygame
import sys

from config import *
from resource import load_player
from entity.player import Player
from scenes.Lvl1 import load_level
from scenes.menu import Menu
from sound import SoundManager


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Som
        self.sound = SoundManager()

        # Estados
        self.running = True
        self.state = "menu"  # menu → playing
        self.player_choice = "player_2"

        # Carrega o menu
        self.menu = Menu(self)
        self.level = None

    # ---------- JOGO ----------
    def start_game(self):
        """CArrega Nível e jogador"""
        self.state = "playing"
        self.level = load_level()
        self.sound.play_music("theme.mp3")   # toca ao iniciar o jogo
        self.background = self.level["background"]
        self.bg_width = self.level["bg_width"]
        self.platforms = self.level["platforms"]

        player_img = load_player(PLAYER_WIDTH, PLAYER_HEIGHT, self.player_choice)
        self.player = Player(player_img, 15, 0)
        self.POV = 0
        self.run_game_loop()

    def run_game_loop(self):
        """Loop jogo"""
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sound.stop_music()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    return

            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            self.player.apply_gravity()

            self.POV = self.player.rect.centerx - WIDTH // 2
            self.POV = max(0, min(self.POV, self.bg_width - WIDTH))

            self.draw_scene()
            pygame.display.flip()
            self.clock.tick(FPS)

    def draw_scene(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (-self.POV, 0))
        for plat in self.platforms:
            pygame.draw.rect(self.screen, (0, 255, 0), plat.move(-self.POV, 0))
        self.screen.blit(self.player.image, (self.player.rect.x - self.POV, self.player.rect.y))

    def run(self):
        """Loop Main"""
        while self.running:
            if self.state == "menu":
                self.menu.run()
            elif self.state == "playing":
                self.run_game_loop()
