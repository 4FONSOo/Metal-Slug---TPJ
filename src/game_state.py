import pygame
import sys

from config import *
from resource import load_player
from entity.player import Player
from scenes.Lvl1 import load_level
from scenes.menu import Menu
from sound import SoundManager


# ---------- 🔹 Estado global do jogo ----------
class GameState:
    def __init__(self):
        # --- PONTUAÇÃO ---
        self.score = 0

        # --- CRÉDITOS ---
        self.credits = 5

        # --- TEMPO ---
        self.time_left = 15
        self.timer_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.timer_event, 1000)

        # --- ESTADO DE JOGO ---
        self.paused = False
        self.level_name = "Nível 1"

        # --- FLAG de controlo ---
        self.time_up_handled = False

    def update_time(self):
        """Diminui o tempo se o jogo não estiver pausado"""
        if not self.paused and self.time_left > 0:
            self.time_left -= 1

    def toggle_pause(self):
        """Alterna entre pausa e jogo ativo"""
        self.paused = not self.paused

    def add_score(self, amount):
        """Aumenta a pontuação"""
        self.score += amount

    def add_credits(self, amount):
        """Aumenta os créditos"""
        self.credits += amount

    def reset(self):
        """Reinicia o estado do jogo"""
        self.score = 0
        self.credits = 0
        self.time_left = 50
        self.paused = False
        self.level_name = "Nível 1"
        self.time_up_handled = False


# ---------- 🔹 Classe principal do jogo ----------
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
        self.state = "menu"
        self.player_choice = "player_2"

        # Carrega o menu
        self.menu = Menu(self)
        self.level = None

        # 🔹 Estado global
        self.game_state = GameState()

        # 🔹 Fonte para HUD
        self.font = pygame.font.SysFont("Arial", 24)

        # 🔹 Contador para mostrar mensagem de tempo esgotado
        self.time_up_display_frames = 0



    # ---------- JOGO ----------
    def start_game(self):
        """Carrega nível e jogador"""
        self.state = "playing"
        self.level = load_level()
        self.sound.play_music("theme.mp3")
        self.background = self.level["background"]
        self.bg_width = self.level["bg_width"]
        self.platforms = self.level["platforms"]

        player_img = load_player(PLAYER_WIDTH, PLAYER_HEIGHT, self.player_choice)
        self.player = Player(player_img, 15, 0)

        # 🔹 Define HP inicial do jogador
        self.player.max_hp = getattr(self.player, "max_hp", 100)
        self.player.hp = getattr(self.player, "hp", self.player.max_hp)

        self.POV = 0
        self.run_game_loop()

    def handle_time_up(self):
        """Executado quando o tempo chega a 0"""
        self.game_state.time_up_handled = True

        # 🔹 Pára a música
        try:
            self.sound.stop_music()
        except Exception:
            pass

        # 🔹 Toca som de aviso (se existir)
        try:
            self.sound.play_sfx("time_up.wav")
        except Exception:
            pass

        # 🔹 Penalização opcional
        penalty = 1
        self.game_state.credits = max(0, self.game_state.credits - penalty)

        # 🔹 Ativa pausa visual e contador para exibir mensagem
        self.game_state.paused = True
        self.time_up_display_frames = 3 * FPS  # mostra 3 segundos

    def run_game_loop(self):
        """Loop principal do jogo"""
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sound.stop_music()
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    return

                # 🔹 Pausa
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.game_state.toggle_pause()

                # 🔹 Atualização do tempo
                elif event.type == self.game_state.timer_event:
                    self.game_state.update_time()

            # 🔹 Quando o tempo chega a 0
            if self.game_state.time_left == 0 and not self.game_state.time_up_handled:
                self.handle_time_up()

            # 🔹 Se o tempo esgotou, mostra mensagem e conta 3s
            if self.time_up_display_frames > 0:
                self.draw_scene()
                self.draw_hud()
                msg = "TEMPO ESGOTADO!"
                text_surf = self.font.render(msg, True, (255, 50, 50))
                self.screen.blit(
                    text_surf,
                    (WIDTH // 2 - text_surf.get_width() // 2, HEIGHT // 2 - text_surf.get_height() // 2),
                )
                pygame.display.flip()
                self.clock.tick(FPS)
                self.time_up_display_frames -= 1

                # 🔹 Após 3s volta ao menu
                if self.time_up_display_frames <= 0:
                    self.game_state.reset()
                    self.state = "menu"
                    return
                continue

            # 🔹 Se estiver pausado manualmente
            if self.game_state.paused:
                self.draw_scene()
                self.draw_hud()
                pause_text = self.font.render("PAUSADO", True, (255, 255, 255))
                self.screen.blit(pause_text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            # Controlo do jogador
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            self.player.apply_gravity()

            # 🔹 Teste temporário: diminuir HP com tecla H
            if keys[pygame.K_h]:
                self.player.hp = max(0, self.player.hp - 1)

            # Movimento da câmara
            self.POV = self.player.rect.centerx - WIDTH // 2
            self.POV = max(0, min(self.POV, self.bg_width - WIDTH))

            # Desenho
            self.draw_scene()
            self.draw_hud()
            pygame.display.flip()
            self.clock.tick(FPS)

    def draw_scene(self):
        """Desenha cenário e entidades"""
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (-self.POV, 0))
        for plat in self.platforms:
            pygame.draw.rect(self.screen, (0, 255, 0), plat.move(-self.POV, 0))
        self.screen.blit(self.player.image, (self.player.rect.x - self.POV, self.player.rect.y))

    # ---------- 🔹 HUD com contorno e barra de vida ----------
    def draw_hud(self):
        """Mostra pontuação, tempo, nível, créditos e vida"""

        # Função auxiliar para contorno
        def draw_text_with_outline(surface, text, font, x, y, color, outline_color=(0, 0, 0)):
            text_surface = font.render(text, True, color)
            outline_surface = font.render(text, True, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        surface.blit(outline_surface, (x + dx, y + dy))
            surface.blit(text_surface, (x, y))

        # Topo: pontuação e tempo
        top_text = f"Pontuação: {self.game_state.score}   Tempo: {self.game_state.time_left}s"
        draw_text_with_outline(self.screen, top_text, self.font, 20, 10, (255, 255, 255))

        # Barra de vida
        hp_ratio = self.player.hp / self.player.max_hp
        bar_width, bar_height = 200, 20
        x, y = 20, 40
        if hp_ratio > 0.6:
            bar_color = (0, 255, 0)
        elif hp_ratio > 0.3:
            bar_color = (255, 255, 0)
        else:
            bar_color = (255, 0, 0)
        pygame.draw.rect(self.screen, (80, 80, 80), (x - 2, y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(self.screen, bar_color, (x, y, bar_width * hp_ratio, bar_height))

        # Fundo centro: nome do nível
        draw_text_with_outline(
            self.screen,
            self.game_state.level_name,
            self.font,
            WIDTH // 2 - self.font.size(self.game_state.level_name)[0] // 2,
            HEIGHT - 40,
            (255, 255, 255),
        )

        # Fundo direita: créditos
        credits_text = f"Créditos: {self.game_state.credits}"
        draw_text_with_outline(
            self.screen,
            credits_text,
            self.font,
            WIDTH - self.font.size(credits_text)[0] - 20,
            HEIGHT - 40,
            (255, 255, 255),
        )

    def run(self):
        """Loop Main"""
        while self.running:
            if self.state == "menu":
                self.menu.run()
            elif self.state == "playing":
                self.run_game_loop()
