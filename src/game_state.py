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


# ---------- 🔹 Texto flutuante (efeito visual de pontuação aprimorado) ----------
class FloatingText:
    def __init__(self, text, x, y, color_start=(255, 230, 0), color_end=(255, 255, 255), lifetime=60):
        self.text = text
        self.x = x
        self.y = y
        self.color_start = color_start
        self.color_end = color_end
        self.alpha = 255
        self.timer = lifetime
        self.font = pygame.font.SysFont("Arial", 22, bold=True)

    def interpolate_color(self):
        """Transição suave entre cor inicial e final."""
        t = 1 - (self.timer / 60)  # 0 → 1
        r = int(self.color_start[0] + (self.color_end[0] - self.color_start[0]) * t)
        g = int(self.color_start[1] + (self.color_end[1] - self.color_start[1]) * t)
        b = int(self.color_start[2] + (self.color_end[2] - self.color_start[2]) * t)
        return (r, g, b)

    def update(self):
        """Faz o texto subir e desaparecer gradualmente."""
        self.y -= 0.7  # sobe um pouco mais rápido
        self.alpha = max(0, self.alpha - 4)
        self.timer -= 1

    def draw(self, screen, camera_x):
        if self.timer <= 0:
            return
        color = self.interpolate_color()
        surf = self.font.render(self.text, True, color)
        surf.set_alpha(self.alpha)
        screen.blit(surf, (self.x - camera_x, self.y))


# ---------- 🔹 Estado global do jogo ----------
class GameState:
    def __init__(self):
        self.score = 0
        self.credits = 5
        self.time_left = 60
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
        self.floating_texts = []  # 🔹 lista para textos de pontuação
        self.shoot_pressed = False

        # Cheats
        self.god_mode = False
        self.infinite_time = False
        self.cheats = {
            "GOD": {"progress": 0, "active": False, "timer": 0},
            "TIME": {"progress": 0, "active": False, "timer": 0},
        }


    # ---------- 🔹 Efeito de flash ----------
    def screen_flash(self, color=(255,255,255), duration=5):
        flash = pygame.Surface((WIDTH, HEIGHT))
        flash.fill(color)
        flash.set_alpha(100)
        for _ in range(duration):
            self.screen.blit(flash, (0, 0))
            pygame.display.flip()
            self.clock.tick(FPS)


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

        # ---------- Criação de inimigos ----------
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


    # ---------- Cheats ----------
    def handle_cheat_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key_char = pygame.key.name(event.key).upper()

        for code, data in self.cheats.items():
            expected_char = code[data["progress"]] if data["progress"] < len(code) else None
            if key_char == expected_char:
                data["progress"] += 1
                if data["progress"] == len(code):
                    data["active"] = not data["active"]
                    data["timer"] = 120
                    data["progress"] = 0
                    if code == "GOD":
                        self.god_mode = data["active"]
                        color = (255,255,0) if self.god_mode else (255,0,0)
                        self.screen_flash(color)
                    elif code == "TIME":
                        self.infinite_time = data["active"]
            else:
                data["progress"] = 1 if key_char == code[0] else 0


    # ---------- Colisões ----------
    def handle_collisions(self):
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            # Projéteis do jogador -> inimigos
            for proj in self.projectiles:
                if proj.alive and enemy.rect.colliderect(proj.rect):
                    enemy.take_damage(proj.damage)
                    proj.alive = False
                    # 🔹 Se morrer, soma pontos + cria texto
                    if not enemy.alive:
                        pts = getattr(enemy, "score_value", 0)
                        self.game_state.score += pts
                        self.floating_texts.append(
                            FloatingText(f"+{pts}", enemy.rect.centerx, enemy.rect.y)
                        )

            # Dano no jogador (só se não estiver em GOD)
            if self.player and not self.god_mode:
                if self.player.rect.colliderect(enemy.rect):
                    self.player.take_damage(1)
                    enemy.take_damage(0.5)
                for e_proj in enemy.projectiles:
                    if e_proj.alive and self.player.rect.colliderect(e_proj.rect):
                        self.player.take_damage(e_proj.damage)
                        e_proj.alive = False

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]


    # ---------- Disparo ----------
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


    # ---------- Morte / tempo ----------
    def check_player_death(self):
        if self.player and self.player.hp <= 0:
            msg = self.font.render("Jogador morto!", True, (255, 0, 0))
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1500)
            self.sound.stop_music()
            self.game_state.reset()
            self.state = "menu"

    def handle_time_up(self):
        if self.infinite_time:
            return
        self.sound.stop_music()
        self.player = None
        msg = self.font.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(3000)
        self.game_state.reset()
        self.state = "menu"


    # ---------- Loop ----------
    def run_game_loop(self):
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sound.stop_music()
                    pygame.quit()
                    sys.exit()
                self.handle_cheat_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.sound.stop_music()
                    self.state = "menu"
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.game_state.toggle_pause()
                elif event.type == self.game_state.timer_event:
                    if not self.infinite_time:
                        self.game_state.update_time()
                    if self.game_state.time_left == 0:
                        self.handle_time_up()
                        return

            # Pausa
            if self.game_state.paused:
                self.draw_scene()
                self.draw_hud()
                pause_text = self.font.render("PAUSADO", True, (255,255,255))
                self.screen.blit(pause_text, (WIDTH//2-60, HEIGHT//2-20))
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            # Atualizações
            keys = pygame.key.get_pressed()
            if self.player:
                self.player.handle_input(keys)
                self.player.apply_gravity()
                self.handle_player_shoot()

            for enemy in self.enemies:
                enemy.update()
            for proj in self.projectiles:
                proj.update()
            for text in self.floating_texts:
                text.update()

            self.floating_texts = [t for t in self.floating_texts if t.timer > 0]
            self.handle_collisions()
            self.check_player_death()

            if self.player:
                self.POV = self.player.rect.centerx - WIDTH // 2
                self.POV = max(0, min(self.POV, self.bg_width - WIDTH))

            self.draw_scene()
            self.draw_hud()
            pygame.display.flip()
            self.clock.tick(FPS)


    # ---------- Desenho ----------
    def draw_scene(self):
        self.screen.fill((0,0,0))
        self.screen.blit(self.background, (-self.POV, 0))

        for plat in self.platforms:
            pygame.draw.rect(self.screen, (0,255,0), plat.move(-self.POV,0))

        if self.player:
            self.screen.blit(self.player.image, (self.player.rect.x - self.POV, self.player.rect.y))

        for enemy in self.enemies:
            enemy.draw(self.screen, self.POV)
        for proj in self.projectiles:
            proj.draw(self.screen, self.POV)
        for text in self.floating_texts:
            text.draw(self.screen, self.POV)


    # ---------- HUD ----------
    def draw_hud(self):
        def draw_text_with_outline(surface, text, font, x, y, color, outline_color=(0, 0, 0)):
            text_surface = font.render(text, True, color)
            outline_surface = font.render(text, True, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        surface.blit(outline_surface, (x + dx, y + dy))
            surface.blit(text_surface, (x, y))

        tempo_str = "∞" if self.infinite_time else f"{self.game_state.time_left}s"
        top_text = f"Pontuação: {self.game_state.score}   Tempo: {tempo_str}"
        draw_text_with_outline(self.screen, top_text, self.font, 20, 10, (255, 255, 255))

        if self.player:
            hp_ratio = self.player.hp / self.player.max_hp
            bar_width, bar_height = 200, 20
            x, y = 20, 40
            bar_color = (0,255,0) if hp_ratio>0.6 else (255,255,0) if hp_ratio>0.3 else (255,0,0)
            pygame.draw.rect(self.screen, (80,80,80), (x-2,y-2,bar_width+4,bar_height+4))
            pygame.draw.rect(self.screen, bar_color, (x,y,bar_width*hp_ratio,bar_height))

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
