import pygame
import sys
import random

from config import *
from resource import load_player, load_enemy
from entity.player import Player
from entity.enemy import EnemySoldier, EnemyShooter, EnemyHeavy, EnemyFast
from entity.projectile import Projectile
from scenes.Lvl1 import load_level
from scenes.menu import Menu
from sound import SoundManager


# ---------- 🔹 Estado global do jogo ----------
class GameState:
    def __init__(self):
        self.score = 0
        self.credits = 5
        self.time_left = 15
        self.timer_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.timer_event, 1000)
        self.paused = False
        self.level_name = "Nível 1"
        self.time_up_handled = False

    def update_time(self):
        if not self.paused and self.time_left > 0:
            self.time_left -= 1

    def toggle_pause(self):
        self.paused = not self.paused

    def reset(self):
        self.__init__()


# ---------- 🔹 Classe principal do jogo ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.sound = SoundManager()

        self.running = True
        self.state = "menu"
        self.player_choice = "player_2"
        self.menu = Menu(self)
        self.level = None
        self.game_state = GameState()
        self.font = pygame.font.SysFont("Arial", 24)
        self.time_up_display_frames = 0

        self.enemies = []
        self.projectiles = []
        self.shoot_pressed = False


    # ---------- Início do jogo ----------
    def start_game(self):
        self.state = "playing"
        self.level = load_level()

        self.sound.stop_music()
        self.sound.play_music("theme.mp3")

        self.background = self.level["background"]
        self.bg_width = self.level["bg_width"]
        self.platforms = self.level["platforms"]

        player_img = load_player(PLAYER_WIDTH, PLAYER_HEIGHT, self.player_choice)
        self.player = Player(player_img, 15, 0)

        # ---------- Criação de inimigos com sprites únicas ----------
        enemy1 = EnemySoldier(load_enemy(80, 80, "Rebel1.png"), 400, 100)
        enemy1.set_platforms(self.platforms)
        enemy1.min_x, enemy1.max_x = (100, 600)

        enemy2 = EnemyShooter(load_enemy(80, 80, "Rebel2.png"), 800, 100)
        enemy2.set_platforms(self.platforms)
        enemy2.min_x, enemy2.max_x = (700, 1100)

        enemy3 = EnemyHeavy(load_enemy(100, 100, "Rebel3.png"), 1200, 100)
        enemy3.set_platforms(self.platforms)
        enemy3.min_x, enemy3.max_x = (1100, 1500)

        enemy4 = EnemyFast(load_enemy(70, 70, "Rebel4.png"), 1600, 100)
        enemy4.set_platforms(self.platforms)
        enemy4.min_x, enemy4.max_x = (1500, 1900)

        self.enemies = [enemy1, enemy2, enemy3, enemy4]

        self.projectiles = []
        self.POV = 0

        self.run_game_loop()


    # ---------- Colisões ----------
    def handle_collisions(self):
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            if self.player and self.player.rect.colliderect(enemy.rect):
                self.player.take_damage(1)
                enemy.take_damage(0.5)

            for proj in self.projectiles:
                if proj.alive and enemy.rect.colliderect(proj.rect):
                    enemy.take_damage(proj.damage)
                    proj.alive = False

            for e_proj in enemy.projectiles:
                if self.player and e_proj.alive and self.player.rect.colliderect(e_proj.rect):
                    self.player.take_damage(e_proj.damage)
                    e_proj.alive = False

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]


    # ---------- Disparo do jogador ----------
    def handle_player_shoot(self):
        if not self.player:
            return

        keys = pygame.key.get_pressed()

        if not keys[pygame.K_SPACE]:
            self.shoot_pressed = False

        if keys[pygame.K_SPACE] and not self.shoot_pressed:
            direction = self.player.facing
            proj = Projectile(
                self.player.rect.centerx + (direction * 40),
                self.player.rect.centery,
                direction,
                max_range=self.bg_width
            )
            self.projectiles.append(proj)
            self.shoot_pressed = True


    # ---------- Morte do jogador ----------
    def check_player_death(self):
        if self.player and self.player.hp <= 0:
            msg = self.font.render("Jogador morto!", True, (255, 0, 0))
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1500)
            self.sound.stop_music()
            self.game_state.reset()
            self.state = "menu"


    # ---------- GAME OVER ----------
    def handle_time_up(self):
        self.sound.stop_music()
        self.player = None
        msg = self.font.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(3000)
        self.game_state.reset()
        self.state = "menu"


    # ---------- Loop principal ----------
    def run_game_loop(self):
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sound.stop_music()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.sound.stop_music()
                    self.state = "menu"
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.game_state.toggle_pause()
                elif event.type == self.game_state.timer_event:
                    self.game_state.update_time()
                    if self.game_state.time_left == 0:
                        self.handle_time_up()
                        return

            if self.game_state.paused:
                self.draw_scene()
                self.draw_hud()
                pause_text = self.font.render("PAUSADO", True, (255, 255, 255))
                self.screen.blit(pause_text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            keys = pygame.key.get_pressed()
            if self.player:
                self.player.handle_input(keys)
                self.player.apply_gravity()
                self.handle_player_shoot()

            for enemy in self.enemies:
                enemy.update()

            for proj in self.projectiles:
                proj.update()

            self.handle_collisions()
            self.check_player_death()

            if self.player:
                self.POV = self.player.rect.centerx - WIDTH // 2
                self.POV = max(0, min(self.POV, self.bg_width - WIDTH))

            self.draw_scene()
            self.draw_hud()
            pygame.display.flip()
            self.clock.tick(FPS)


    # ---------- Renderização ----------
    def draw_scene(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (-self.POV, 0))

        for plat in self.platforms:
            pygame.draw.rect(self.screen, (0, 255, 0), plat.move(-self.POV, 0))

        if self.player:
            self.screen.blit(self.player.image, (self.player.rect.x - self.POV, self.player.rect.y))

        for enemy in self.enemies:
            enemy.draw(self.screen, self.POV)

        for proj in self.projectiles:
            proj.draw(self.screen, self.POV)


    def draw_hud(self):
        def draw_text_with_outline(surface, text, font, x, y, color, outline_color=(0, 0, 0)):
            text_surface = font.render(text, True, color)
            outline_surface = font.render(text, True, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        surface.blit(outline_surface, (x + dx, y + dy))
            surface.blit(text_surface, (x, y))

        top_text = f"Pontuação: {self.game_state.score}   Tempo: {self.game_state.time_left}s"
        draw_text_with_outline(self.screen, top_text, self.font, 20, 10, (255, 255, 255))

        if self.player:
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

        credits_text = f"Créditos: {self.game_state.credits}"
        draw_text_with_outline(
            self.screen,
            credits_text,
            self.font,
            WIDTH - self.font.size(credits_text)[0] - 20,
            HEIGHT - 40,
            (255, 255, 255),
        )


    # ---------- Loop Main ----------
    def run(self):
        while self.running:
            if self.state == "menu":
                self.menu.run()
            elif self.state == "playing":
                self.run_game_loop()
