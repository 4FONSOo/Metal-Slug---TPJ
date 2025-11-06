import pygame
import sys
from config import WIDTH, HEIGHT, FPS


# ---------- MENU PRINCIPAL ----------
class Menu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.font = pygame.font.SysFont("arial", 36)
        self.selected = 0
        # voltou a incluir os personagens
        self.options = ["Marco Rossi", "Tarma Roving", "Opções", "Sair"]

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
            self.game.player_choice = "player1"
            self.game.start_game()
        elif self.selected == 1:
            self.game.player_choice = "player2"
            self.game.start_game()
        elif self.selected == 2:
            MenuOptions(self.game).run()
        elif self.selected == 3:
            self.game.sound.stop_music()
            pygame.quit()
            sys.exit()


# ---------- SUBMENU DE OPÇÕES ----------
class MenuOptions:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.font = pygame.font.SysFont("arial", 30)
        self.small_font = pygame.font.SysFont("arial", 26)
        self.selected = 0
        self.volume = int(pygame.mixer.music.get_volume() * 100)
        self.muted = False
        self.hold_timer = 0  # para volume suave
        self.hovering_mute = False  # deteta se o rato está em cima
        self.options = ["Dificuldade", "Controlos", "Volume Música", "Voltar"]

    def draw(self):
        self.screen.fill((10, 10, 25))
        title = self.font.render("Opções", True, (255, 215, 0))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        mouse_pos = pygame.mouse.get_pos()

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (120, 120, 120)
            surf = self.font.render(text, True, color)
            y = 220 + i * 60
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))

            # --- Volume ---
            if text == "Volume Música":
                vol_text = "MUTE" if self.muted else f"{self.volume}%"
                vol_icon = "🔇" if self.muted else "🔊"
                vol_color = (255, 80, 80) if self.muted else (0, 200, 255)

                vol_surf = self.small_font.render(f"{vol_icon} {vol_text}", True, vol_color)
                self.vol_rect = vol_surf.get_rect()
                self.vol_rect.topleft = (WIDTH // 2 + 180, y)

                # hover visual
                self.hovering_mute = self.vol_rect.collidepoint(mouse_pos)
                if self.hovering_mute:
                    highlight = pygame.Surface((self.vol_rect.width + 10, self.vol_rect.height + 4))
                    highlight.fill((30, 60, 100))
                    self.screen.blit(highlight, (self.vol_rect.x - 5, self.vol_rect.y - 2))

                self.screen.blit(vol_surf, self.vol_rect)

        pygame.display.flip()

    def adjust_volume(self, change):
        if self.muted:
            return
        self.volume = max(0, min(100, self.volume + change))
        pygame.mixer.music.set_volume(self.volume / 100)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.music.set_volume(0)
        else:
            pygame.mixer.music.set_volume(self.volume / 100)

    def handle_input(self, keys):
        """Volume suave (mantendo tecla premida)"""
        if self.selected == 2:
            change = 0
            if keys[pygame.K_LEFT]:
                change = -1
            elif keys[pygame.K_RIGHT]:
                change = +1
            if change != 0:
                self.hold_timer += 1
                if self.hold_timer % 3 == 0:
                    self.adjust_volume(change)
            else:
                self.hold_timer = 0

    def run(self):
        running = True
        while running:
            keys = pygame.key.get_pressed()
            self.handle_input(keys)
            self.draw()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        if self.selected == 3:  # Voltar
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_m and self.selected == 2:
                        self.toggle_mute()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # clique do rato sobre "MUTE"
                    if hasattr(self, "vol_rect") and self.vol_rect.collidepoint(event.pos):
                        self.toggle_mute()

            self.clock.tick(FPS)
