import pygame
import sys

from config import *
from resource import load_player
from entity.player import Player
from entity.enemy import EnemyManager
from entity.projectile import Projectile
from scenes.Lvl1 import load_level
from scenes.menu import Menu
from sound import SoundManager

print("[DEBUG] main carregado de:", __file__)

def draw_text_with_outline(surface, text, font, x, y, color, outline_color=(0, 0, 0)):
    text_surface = font.render(text, True, color)
    outline_surface = font.render(text, True, outline_color)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                surface.blit(outline_surface, (x + dx, y + dy))
    surface.blit(text_surface, (x, y))


class FloatingText:
    def __init__(self, text, x, y, color=(255, 255, 0)):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.alpha = 255
        self.lifetime = 60
        self.font = pygame.font.SysFont("Arial", 22)

    def update(self):
        self.y -= 1
        self.alpha -= 4
        self.lifetime -= 1
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, surface, camera_x):
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(self.alpha)
        surface.blit(text_surf, (self.x - camera_x, self.y))


class GameState:
    def __init__(self):
        self.score = 0
        self.credits = 5
        self.time_left = 15
        self.level_name = "Nível 1"
        self.paused = False
        self.timer_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.timer_event, 1000)

    def update_time(self):
        if not self.paused and self.time_left > 0:
            self.time_left -= 1

    def toggle_pause(self):
        self.paused = not self.paused

    def reset(self):
        self.__init__()


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.sound = SoundManager()

        self.running = True
        self.state = "menu"
        self.menu = Menu(self)
        self.game_state = GameState()

        self.level = None
        self.background = None
        self.bg_width = WIDTH
        self.platforms = []

        self.player_choice = "player_2"
        self.player = None
        self.enemy_manager = None
        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.floating_texts = []
        self.shoot_pressed = False
        self.POV = 0

        self.cheats = {
            "GOD": {"progress": 0, "active": False},
            "TIME": {"progress": 0, "active": False},
            "SPJ": {"progress": 0, "active": False},
        }
        self.god_mode = False
        self.infinite_time = False
        self.super_jump = False
        self.flash_color = None
        self.flash_frames = 0

    def flash(self, color, frames=5):
        self.flash_color = color
        self.flash_frames = frames

    # Cheats

    def process_cheat_key(self, event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        key_char = pygame.key.name(event.key).upper()
        consumed = False
        for code, data in self.cheats.items():
            expected = code[data["progress"]] if data["progress"] < len(code) else None
            if key_char == expected:
                data["progress"] += 1
                consumed = True
                if data["progress"] == len(code):
                    data["active"] = not data["active"]
                    data["progress"] = 0
                    if code == "GOD":
                        self.god_mode = data["active"]
                        self.flash((255, 255, 0) if self.god_mode else (255, 0, 0))
                    elif code == "TIME":
                        self.infinite_time = data["active"]
                        self.flash((0, 200, 255) if self.infinite_time else (255, 120, 120))
                    elif code == "SPJ":
                        import config
                        self.super_jump = data["active"]
                        config.PLAYER_JUMP_SPEED = -35 if self.super_jump else -15
                        self.flash((0, 255, 255) if self.super_jump else (255, 100, 100))
            else:
                data["progress"] = 1 if key_char == code[0] else 0
        return consumed

    def reset_all_state(self):
        import config
        self.game_state.reset()
        for c in self.cheats.values():
            c["progress"] = 0
            c["active"] = False
        self.god_mode = False
        self.infinite_time = False
        self.super_jump = False
        config.PLAYER_JUMP_SPEED = -15
        self.player = None
        self.enemy_manager = None
        self.enemies.clear()
        self.projectiles.clear()
        self.enemy_projectiles.clear()
        self.floating_texts.clear()
        try:
            self.sound.stop_music()
        except Exception:
            pass

    def handle_game_over(self):
        self.sound.stop_music()
        text = self.font.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        self.reset_all_state()
        self.state = "menu"

    def start_game(self):

        self.state = "playing"
        self.level = load_level()
        self.sound.stop_music()
        self.sound.play_music("theme.mp3")

        self.background = self.level["background"]
        self.bg_width = self.level["bg_width"]
        self.platforms = self.level["platforms"]

        self.player = Player(x=15, y=0, character=self.player_choice)
        print(f"[DEBUG MAIN] Player criado: {self.player} (rect={self.player.rect})")

        
        self.player.platforms = self.platforms
        self.player.set_level_limits(self.bg_width)
        
        
        if not hasattr(self.player, "facing"):
            self.player.facing = 1

        self.enemy_manager = EnemyManager(self.bg_width, self.platforms)
        self.enemies = self.enemy_manager.get_enemies()

        self.projectiles = []
        self.enemy_projectiles = []
        self.floating_texts = []
        self.shoot_pressed = False
        self.POV = 0

        self.run_game_loop()

    def handle_collisions(self):
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            for proj in self.projectiles:
                if proj and proj.alive and enemy.rect.colliderect(proj.rect):
                    enemy.take_damage(proj.damage)
                    proj.trigger_hit()
                    if not enemy.alive:
                        self.game_state.score += getattr(enemy, "points", 100)
                        self.floating_texts.append(
                            FloatingText(f"+{enemy.points}", enemy.rect.centerx, enemy.rect.top)
                        )

        if self.player and not self.god_mode:
            for proj in self.enemy_projectiles:
                if proj and proj.alive and self.player.rect.colliderect(proj.rect):
                    self.player.take_damage(proj.damage)
                    proj.trigger_hit()

        if self.player and not self.god_mode:
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if self.player.rect.colliderect(enemy.rect):
                    self.player.take_damage(enemy.damage * 0.5)
                    enemy.take_damage(0.5)

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p and (p.alive or p.hit_flash > 0)]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p and (p.alive or p.hit_flash > 0)]

        if self.player and not self.player.alive:
            self.handle_game_over()
            return  # está limpo? limpa frame

    def handle_player_shoot(self):
        if not self.player:
            return
        
        keys = pygame.key.get_pressed()
        if not keys[pygame.K_SPACE]:
            self.shoot_pressed = False
        if keys[pygame.K_SPACE] and not self.shoot_pressed:
            shoot_up = keys[pygame.K_UP]
            shoot_down = keys[pygame.K_DOWN]
            dir_x, dir_y = self.player.facing, 0

            if shoot_up and not shoot_down:
                dir_x, dir_y = 0, -1
                sx, sy = self.player.rect.centerx, self.player.rect.top
            elif shoot_down and not shoot_up:
                if self.player.vel_y != 0:
                    dir_x, dir_y = 0, 1
                    sx, sy = self.player.rect.centerx, self.player.rect.centery
                else:
                    sx, sy = self.player.rect.centerx + (dir_x * 40), self.player.rect.bottom - 20
            else:
                sx, sy = self.player.rect.centerx + (dir_x * 40), self.player.rect.centery - 5

            self.projectiles.append(
                Projectile(sx, sy, dir_x, dir_y, max_range=self.bg_width, color=(100, 200, 255))
            )
            self.shoot_pressed = True

    def run_game_loop(self):
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sound.stop_music()
                    pygame.quit()
                    sys.exit()
                cheat_consumed = self.process_cheat_key(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.reset_all_state()
                        self.state = "menu"
                        return
                    if event.key == pygame.K_p and not cheat_consumed:
                        self.game_state.toggle_pause()
                elif event.type == self.game_state.timer_event:
                    if not self.infinite_time:
                        self.game_state.update_time()

            if self.game_state.time_left <= 0 and not self.infinite_time:
                self.handle_game_over()
                return

            if self.flash_frames > 0:
                self.screen.fill(self.flash_color or (255, 255, 255))
                pygame.display.flip()
                self.flash_frames -= 1
                self.clock.tick(FPS)
                continue

            if self.game_state.paused:
                self.draw_scene()
                pause_text = self.font.render("PAUSADO", True, (255, 255, 255))
                self.screen.blit(pause_text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            keys = pygame.key.get_pressed()
            if self.player:
                self.player.handle_input(keys)
                # atualiza facing sem mexer na sprite base
                if keys[pygame.K_LEFT]:
                    self.player.facing = -1
                elif keys[pygame.K_RIGHT]:
                    self.player.facing = 1

                dt = self.clock.get_time()
                self.player.update_animation(dt)

                self.player.apply_gravity()
                self.handle_player_shoot()

            if self.enemy_manager:
                self.enemy_manager.update()
                self.enemies = self.enemy_manager.get_enemies()
                new_enemy_projectiles = self.enemy_manager.get_projectiles()
                self.enemy_projectiles.extend(new_enemy_projectiles)

            for proj in self.projectiles + self.enemy_projectiles:
                if proj:
                    proj.update()

            self.handle_collisions()
            if self.state != "playing":
                return

            for text in self.floating_texts:
                text.update()
            self.floating_texts = [t for t in self.floating_texts if t.lifetime > 0]

            if self.player:
                self.POV = self.player.rect.centerx - WIDTH // 2
                self.POV = max(0, min(self.POV, self.bg_width - WIDTH))

            self.draw_scene()
            self.draw_hud()
            pygame.display.flip()
            self.clock.tick(FPS)

    def draw_scene(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (-self.POV, 0))

        if self.enemy_manager:
            self.enemy_manager.draw(self.screen, self.POV)

        if self.player:
            # Atenção á direção da imagem, neste caso não me apeteceu fazer photoshop (se usar na direção oposto, isto torna-se obsoleto) e está a dar asneira!!!!
            img = pygame.transform.flip(self.player.image, self.player.facing < 0, False)
            self.screen.blit(img, (self.player.rect.x - self.POV, self.player.rect.y))

        for proj in self.projectiles + self.enemy_projectiles:
            if proj:
                proj.draw(self.screen, self.POV)

        for text in self.floating_texts:
            text.draw(self.screen, self.POV)

    def draw_hud(self):
        tempo_str = "∞" if self.infinite_time else f"{self.game_state.time_left}s"
        top_text = f"Pontuação: {self.game_state.score}   Tempo: {tempo_str}"
        draw_text_with_outline(self.screen, top_text, self.font, 20, 10, (255, 255, 255))
        if self.player:
            hp_ratio = self.player.hp / self.player.max_hp
            bar_width, bar_height = 200, 20
            x, y = 20, 40
            color = (0, 255, 0) if hp_ratio > 0.6 else (255, 255, 0) if hp_ratio > 0.3 else (255, 0, 0)
            pygame.draw.rect(self.screen, (80, 80, 80), (x - 2, y - 2, bar_width + 4, bar_height + 4))
            pygame.draw.rect(self.screen, color, (x, y, bar_width * hp_ratio, bar_height))

    def run(self):
        while self.running:
            if self.state == "menu":
                self.menu.run()
            elif self.state == "playing":
                self.run_game_loop()


if __name__ == "__main__":
    
    print("[DEBUG MAIN] Welcome to my Metal Slug 2D...")

    Game().run()
