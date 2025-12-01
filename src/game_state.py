# game_state.py
"""
Cérebro principal do jogo:
- loop global
- estado (pontuação, tempo, dificuldade)
- gestão de cenas (menu, nível)
- cheats, HUD, etc.

Nota: aqui não se importa pygame directamente, só pg_engine.
"""

import sys

import pg_engine as pg
import config
import controls

from scene import Scene
from cheats import CheatEngine
from input_manager import is_fire_pressed, get_shoot_direction

from entity.player import Player
from entity.enemy import EnemyManager
from entity.projectile import Projectile
from scenes.Lvl1 import load_level
from sound import SoundManager
from config import DIFFICULTY_PRESETS, DEFAULT_DIFFICULTY, CHEAT_CODES
from pg_engine import Vector2

# Import no fim do ficheiro para evitar circular? Não, aqui é seguro:
from scenes.menu import Menu as MenuScene  # cena de menu principal


def draw_text_with_outline(surface, text, font, x, y, color, outline_color=(0, 0, 0)):
    """Texto com contorno maroto, para o HUD não desaparecer no fundo."""
    text_surface = pg.render_text(font, text, color)
    outline_surface = pg.render_text(font, text, outline_color)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                surface.blit(outline_surface, (x + dx, y + dy))
    surface.blit(text_surface, (x, y))


class FloatingText:
    """Texto flutuante tipo '+100', a subir e a desvanecer."""

    def __init__(self, text, x, y, color=None):
        self.text = text
        self.x = x
        self.y = y
        self.color = color or config.FLOATING_TEXT_COLOR_DEFAULT
        self.alpha = 255
        self.lifetime = config.FLOATING_TEXT_LIFETIME_FRAMES
        self.font = pg.create_font(
            config.FLOATING_TEXT_FONT_NAME,
            config.FLOATING_TEXT_FONT_SIZE,
        )

    def update(self):
        """Sobe, perde opacidade e vai à vida quando a lifetime chega ao fim."""
        self.y -= config.FLOATING_TEXT_RISE_SPEED
        self.alpha -= config.FLOATING_TEXT_ALPHA_STEP
        self.lifetime -= 1
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, surface, camera_x):
        text_surf = pg.render_text(self.font, self.text, self.color)
        text_surf.set_alpha(self.alpha)
        surface.blit(text_surf, (self.x - camera_x, self.y))


class GameState:
    """
    Estado lógico “abstrato” do jogo:
      - pontuação
      - créditos (ainda por usar)
      - tempo
      - nome do nível
      - pausa
    """

    def __init__(
        self,
        initial_score=config.INITIAL_SCORE,
        initial_credits=config.INITIAL_CREDITS,
        initial_time=config.INITIAL_TIME_LEFT,
        level_name=config.INITIAL_LEVEL_NAME,
    ):
        self.score = initial_score
        self.credits = initial_credits      # ainda não usado, mas já cá fica
        self.time_left = initial_time
        self.level_name = level_name        # idem, para futuros níveis
        self.paused = False

        # Evento de timer (1x por segundo)
        self.timer_event = config.TIMER_EVENT_ID
        pg.time_set_timer(self.timer_event, config.TIMER_INTERVAL_MS)

    def update_time(self):
        """Desconta 1 segundo se não estiver em pausa."""
        if not self.paused and self.time_left > 0:
            self.time_left -= 1

    def toggle_pause(self):
        self.paused = not self.paused


class Game:
    """Motor principal: gere janela, som, dificuldades, cenas, etc."""

    def __init__(self):
        pg.init()
        self.screen = pg.create_window(config.WIDTH, config.HEIGHT, config.WINDOW_TITLE)
        self.clock = pg.create_clock()
        self.font = pg.create_font(config.HUD_FONT_NAME, config.HUD_FONT_SIZE)
        self.sound = SoundManager()

        # Cena actual (menu, nível, etc.)
        self.current_scene: Scene | None = None
        self.running = True

        # Nível / cenário
        self.level = None
        self.background = None
        self.bg_width = config.WIDTH
        self.platforms: list[pg.Rect] = []

        # Jogador / inimigos / projécteis
        self.player_choice = "player1"
        self.player: Player | None = None
        self.enemy_manager: EnemyManager | None = None
        self.enemies: list[object] = []
        self.projectiles: list[Projectile] = []          # projécteis do jogador
        self.enemy_projectiles: list[Projectile] = []    # projécteis dos inimigos
        self.floating_texts: list[FloatingText] = []

        # Disparo / mira
        self.shoot_pressed = False
        self.last_shot_time = 0
        self.aim_dir = Vector2(1, 0)

        # POV = deslocamento da “câmara” horizontal
        self.POV = 0

        # Dificuldade
        self.difficulty = DEFAULT_DIFFICULTY
        self.difficulty_preset = DIFFICULTY_PRESETS[self.difficulty]

        # Estado lógico (score / tempo / etc.)
        self.game_state: GameState | None = None

        # Cheats
        self.cheat_engine = CheatEngine(CHEAT_CODES)
        self.god_mode = False
        self.infinite_time = False
        self.super_jump = False

        # FX de flash de ecrã
        self.flash_color = None
        self.flash_frames = 0

        # Começamos no menu principal
        self.change_scene(MenuScene(self))

    # -----------------------------
    # GESTÃO DE CENAS
    # -----------------------------
    def change_scene(self, new_scene: Scene):
        """Troca de cena de forma civilizada."""
        if self.current_scene is not None:
            self.current_scene.on_exit()
        self.current_scene = new_scene
        self.current_scene.on_enter()

    # -----------------------------
    # DIFICULDADE
    # -----------------------------
    def update_difficulty_preset(self):
        """Actualiza o preset de dificuldade actual a partir da config."""
        self.difficulty_preset = DIFFICULTY_PRESETS.get(
            self.difficulty,
            DIFFICULTY_PRESETS[DEFAULT_DIFFICULTY],
        )

    def _get_initial_time_for_difficulty(self) -> int:
        preset = self.difficulty_preset
        mult = preset.get("TIME_MULTIPLIER", 1.0)
        return int(config.INITIAL_TIME_LEFT * mult)

    def _get_player_max_hp_for_difficulty(self) -> int:
        preset = self.difficulty_preset
        mult = preset.get("PLAYER_HP_MULTIPLIER", 1.0)
        return int(config.PLAYER_MAX_HP * mult)

    def _get_enemy_params_for_difficulty(self):
        preset = self.difficulty_preset
        max_spawns = preset.get(
            "ENEMY_MAX_SPAWNS",
            config.ENEMY_MANAGER_MAX_SPAWNS_DEFAULT,
        )
        max_active = preset.get(
            "ENEMY_MAX_ACTIVE",
            config.ENEMY_MANAGER_MAX_ACTIVE_DEFAULT,
        )
        damage_multiplier = preset.get("ENEMY_DAMAGE_MULTIPLIER", 1.0)
        return max_spawns, max_active, damage_multiplier

    # -----------------------------
    # FX
    # -----------------------------
    def flash(self, color, frames=None):
        """Flash no ecrã com uma cor, durante N frames (por defeito poucos)."""
        self.flash_color = color
        self.flash_frames = frames if frames is not None else config.SCREEN_FLASH_DEFAULT_FRAMES

    # -----------------------------
    # CHEATS
    # -----------------------------
    def process_cheats(self, event) -> bool:
        """
        Processa um evento à procura de sequências de cheats.

        Devolve:
          - True se o evento foi consumido pelo sistema de cheats
        """
        if event.type != pg.KEYDOWN:
            return False

        key_name = pg.key_name(event.key)
        if not key_name or len(key_name) != 1:
            return False

        consumed, activations = self.cheat_engine.process_char(key_name)
        for code, active in activations:
            if code == "GOD":
                self.god_mode = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_GOD_ON if active else config.CHEAT_FLASH_COLOR_GOD_OFF
                )
            elif code == "TIME":
                self.infinite_time = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_TIME_ON if active else config.CHEAT_FLASH_COLOR_TIME_OFF
                )
            elif code == "SPJ":
                self.super_jump = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_SPJ_ON if active else config.CHEAT_FLASH_COLOR_SPJ_OFF
                )
                if self.player:
                    self.player.jump_speed = (
                        config.CHEAT_SUPER_JUMP_VALUE
                        if active
                        else config.CHEAT_NORMAL_JUMP_VALUE
                    )
        return consumed

    def reset_all_state(self):
        """Reset total: cheats, estado lógico, entidades e música."""
        self.cheat_engine.reset_all()
        self.god_mode = False
        self.infinite_time = False
        self.super_jump = False

        self.game_state = GameState(initial_time=self._get_initial_time_for_difficulty())

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

    # -----------------------------
    # GAME OVER / START
    # -----------------------------
    def handle_game_over(self):
        """Ecrã de GAME OVER básico e retorno ao menu."""
        self.sound.stop_music()
        text = pg.render_text(self.font, "GAME OVER", (255, 50, 50))
        self.screen.blit(
            text,
            (config.WIDTH // 2 - text.get_width() // 2, config.HEIGHT // 2),
        )
        pg.display_flip()
        pg.time_wait(config.GAME_OVER_WAIT_MS)
        self.reset_all_state()
        # Volta ao menu
        self.change_scene(MenuScene(self))

    def start_game(self):
        """
        Arranca um novo jogo:
          - faz reset de estado
          - carrega o nível
          - cria player e inimigos
          - muda para a cena de jogo (LevelScene)
        """
        self.reset_all_state()

        # Nível (TMX)
        self.level = load_level()
        self.background = self.level["background"]
        self.bg_width = self.level["bg_width"]
        self.platforms = self.level["platforms"]

        self.sound.stop_music()
        self.sound.play_music("theme.mp3")

        # Jogador
        max_hp = self._get_player_max_hp_for_difficulty()
        jump_speed = (
            config.CHEAT_SUPER_JUMP_VALUE
            if self.super_jump
            else config.CHEAT_NORMAL_JUMP_VALUE
        )

        self.player = Player(
            x=15,
            y=0,
            character=self.player_choice,
            max_hp=max_hp,
            jump_speed=jump_speed,
        )
        self.player.platforms = self.platforms
        self.player.set_level_limits(self.bg_width)
        if not hasattr(self.player, "facing"):
            self.player.facing = 1

        # Inimigos
        max_spawns, max_active, damage_mult = self._get_enemy_params_for_difficulty()
        self.enemy_manager = EnemyManager(
            self.bg_width,
            self.platforms,
            max_spawns=max_spawns,
            max_active=max_active,
            damage_multiplier=damage_mult,
        )
        self.enemies = self.enemy_manager.get_enemies()

        # Listas de projécteis / textos
        self.projectiles = []
        self.enemy_projectiles = []
        self.floating_texts = []
        self.shoot_pressed = False
        self.POV = 0

        # Muda para a cena de jogo
        self.change_scene(LevelScene(self))

    # -----------------------------
    # COMBATE / HELPERS USADOS PELO LEVELSCENE
    # -----------------------------
    def try_melee_attack(self) -> bool:
        """Tenta ataque melee (faca). Se matar alguém, dá pontos e texto flutuante."""
        if not self.player or not self.enemies:
            return False

        player_rect = self.player.rect
        facing = getattr(self.player, "facing", 1)

        melee_rect = player_rect.inflate(config.MELEE_WIDTH, config.MELEE_HEIGHT)

        if facing == 1:
            melee_rect.x += config.MELEE_WIDTH // 2
        else:
            melee_rect.x -= config.MELEE_WIDTH // 2

        alvo = None
        for enemy in self.enemies:
            if not enemy or not enemy.alive:
                continue
            if not melee_rect.colliderect(enemy.rect):
                continue

            # Só acerta quem estiver à frente (nada de facadas pelas costas)
            if facing == 1 and enemy.rect.centerx < player_rect.centerx:
                continue
            if facing == -1 and enemy.rect.centerx > player_rect.centerx:
                continue

            alvo = enemy
            break

        if not alvo:
            return False

        # Faca é “one-shot kill”
        alvo.take_damage(config.MELEE_KILL_DAMAGE)

        if not alvo.alive and self.game_state:
            points = getattr(alvo, "points", 100)
            self.game_state.score += points
            self.floating_texts.append(
                FloatingText(f"+{points}", alvo.rect.centerx, alvo.rect.top)
            )

        return True

    def handle_collisions(self):
        """Trata de todas as colisões: projécteis, player, inimigos, contacto físico."""
        # Projécteis do jogador em inimigos
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            for proj in self.projectiles:
                if proj and proj.alive and enemy.rect.colliderect(proj.rect):
                    enemy.take_damage(proj.damage)
                    proj.trigger_hit()
                    if not enemy.alive and self.game_state:
                        self.game_state.score += getattr(enemy, "points", 100)
                        self.floating_texts.append(
                            FloatingText(
                                f"+{enemy.points}",
                                enemy.rect.centerx,
                                enemy.rect.top,
                            )
                        )

        # Projécteis de inimigos em jogador
        if self.player and not self.god_mode:
            for proj in self.enemy_projectiles:
                if proj and proj.alive and self.player.rect.colliderect(proj.rect):
                    self.player.take_damage(proj.damage)
                    proj.trigger_hit()

        # Contacto físico jogador <-> inimigo
        if self.player and not self.god_mode:
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if self.player.rect.colliderect(enemy.rect):
                    self.player.take_damage(enemy.contact_damage_to_player())
                    enemy.take_damage(enemy.contact_self_damage())

        # Limpar mortos / impactos
        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [
            p for p in self.projectiles if p and (p.alive or p.hit_flash > 0)
        ]
        self.enemy_projectiles = [
            p for p in self.enemy_projectiles if p and (p.alive or p.hit_flash > 0)
        ]

        if self.player and not self.player.alive:
            self.handle_game_over()

    def handle_player_shoot(self):
        """
        Lida com disparo do jogador:
          - cadência de tiro
          - melee primeiro, tiro depois
          - mira “suavizada” com lerp (Vector2)
        """
        if not self.player:
            return

        keys = pg.get_keys()

        # Se não está a carregar no disparo, limpamos estado e saímos
        if not is_fire_pressed(keys):
            self.shoot_pressed = False
            return

        now = pg.time_get_ticks()

        # Cadência de tiro (auto-fire)
        if self.shoot_pressed and (now - self.last_shot_time) < config.PLAYER_FIRE_INTERVAL_MS:
            return

        # 1) Primeiro tenta melee (faca)
        if self.try_melee_attack():
            self.shoot_pressed = True
            self.last_shot_time = now
            return

        # 2) Direção "desejada" com base nas teclas (discreta)
        raw_dx, raw_dy = get_shoot_direction(
            keys,
            facing=self.player.facing,
            allow_diagonals=True,
        )

        target_vec = Vector2(raw_dx, raw_dy)
        if target_vec.length_squared() == 0:
            if self.aim_dir.length_squared() == 0:
                target_vec = Vector2(1, 0)
            else:
                target_vec = self.aim_dir
        target_vec = target_vec.normalize()

        # Suavizar a mira em direção ao target
        if self.aim_dir.length_squared() == 0:
            self.aim_dir = target_vec
        else:
            self.aim_dir = self.aim_dir.lerp(
                target_vec,
                config.PLAYER_AIM_LERP_FACTOR,
            )
            if self.aim_dir.length_squared() == 0:
                self.aim_dir = target_vec

        aim = self.aim_dir.normalize()

        # 3) Calcular posição de spawn (usa direcção discreta para offsets)
        cx = self.player.rect.centerx
        cy = self.player.rect.centery

        if raw_dx == 0 and raw_dy == -1:
            # tiro puro para cima
            sx, sy = cx, self.player.rect.top
        elif raw_dx == 0 and raw_dy == 1:
            # tiro puro para baixo
            sx, sy = cx, cy
        else:
            # horizontal ou diagonal
            sx = cx + raw_dx * config.PLAYER_PROJECTILE_OFFSET_X
            sy = cy - config.PLAYER_PROJECTILE_OFFSET_Y

        # 4) Criar projéctil com direção de mira suavizada (aim.x, aim.y)
        self.projectiles.append(
            Projectile(
                sx,
                sy,
                aim.x,
                aim.y,
                max_range=self.bg_width,
                color=config.PLAYER_PROJECTILE_COLOR,
            )
        )

        self.shoot_pressed = True
        self.last_shot_time = now

    # -----------------------------
    # DRAW HELPERS
    # -----------------------------
    def draw_scene(self):
        """Desenha cenário, inimigos, jogador, projécteis e textos flutuantes."""
        self.screen.fill((0, 0, 0))
        if self.background:
            self.screen.blit(self.background, (-self.POV, 0))

        if self.enemy_manager:
            self.enemy_manager.draw(self.screen, self.POV)

        if self.player:
            self.screen.blit(
                self.player.image,
                (self.player.rect.x - self.POV, self.player.rect.y),
            )

        for proj in self.projectiles + self.enemy_projectiles:
            if proj:
                proj.draw(self.screen, self.POV)

        for text in self.floating_texts:
            text.draw(self.screen, self.POV)

    def draw_hud(self):
        """Desenha HUD: pontuação, tempo, dificuldade, barra de HP."""
        if not self.game_state:
            return

        tempo_str = "∞" if self.infinite_time else f"{self.game_state.time_left}s"
        top_text = (
            f"Pontuação: {self.game_state.score}   "
            f"Tempo: {tempo_str}   "
            f"Dif: {self.difficulty}"
        )
        draw_text_with_outline(
            self.screen,
            top_text,
            self.font,
            20,
            10,
            config.HUD_TEXT_COLOR,
        )

        if self.player:
            hp_ratio = (
                self.player.hp / self.player.max_hp
                if self.player.max_hp > 0
                else 0
            )
            bar_width = config.HUD_PLAYER_HP_BAR_WIDTH
            bar_height = config.HUD_PLAYER_HP_BAR_HEIGHT
            x, y = config.HUD_PLAYER_HP_BAR_POS

            if hp_ratio > config.HUD_PLAYER_HP_GREEN_THRESHOLD:
                color = config.HUD_PLAYER_HP_COLOR_GREEN
            elif hp_ratio > config.HUD_PLAYER_HP_YELLOW_THRESHOLD:
                color = config.HUD_PLAYER_HP_COLOR_YELLOW
            else:
                color = config.HUD_PLAYER_HP_COLOR_RED

            pg.draw_rect(
                self.screen,
                config.HUD_PLAYER_HP_BG_COLOR,
                (x - 2, y - 2, bar_width + 4, bar_height + 4),
            )
            pg.draw_rect(
                self.screen,
                color,
                (x, y, bar_width * hp_ratio, bar_height),
            )

    # -----------------------------
    # LOOP GLOBAL
    # -----------------------------
    def run(self):
        """Loop global de jogo: delega tudo na cena actual."""
        while self.running:
            events = pg.get_events()
            dt = self.clock.get_time()

            if not self.current_scene:
                # Se por algum motivo ficarmos sem cena activa, volta ao menu
                self.change_scene(MenuScene(self))

            self.current_scene.handle_input(events)
            self.current_scene.update(dt)
            self.current_scene.draw(self.screen)

            pg.display_flip()
            self.clock.tick(config.FPS)


# -----------------------------
# CENA DE JOGO (LEVEL)
# -----------------------------
class LevelScene(Scene):
    """
    Cena que trata do jogo em si (nível actual).

    A lógica pesada que antes estava em Game.run_game_loop
    vive agora aqui: input, update, draw por frame.
    """

    def handle_input(self, events: list):
        game = self.game
        menu_key = controls.get_key(controls.MENU)
        pause_key = controls.get_key(controls.PAUSE)

        for event in events:
            if event.type == pg.QUIT:
                game.sound.stop_music()
                pg.quit()
                sys.exit()

            cheat_consumed = game.process_cheats(event)

            if event.type == pg.KEYDOWN:
                if event.key == menu_key:
                    # Rage quit para o menu: mata jogo actual
                    game.reset_all_state()
                    game.change_scene(MenuScene(game))
                    return

                if (
                    event.key == pause_key
                    and not cheat_consumed
                    and game.game_state
                ):
                    game.game_state.toggle_pause()

            # Timer do relógio
            if game.game_state and event.type == game.game_state.timer_event:
                if not game.infinite_time:
                    game.game_state.update_time()

    def update(self, dt: float):
        game = self.game

        # Timeout de nível
        if (
            game.game_state
            and game.game_state.time_left <= 0
            and not game.infinite_time
        ):
            game.handle_game_over()
            return

        # Flash de cheat / FX: enquanto dura, não há lógica de jogo
        if game.flash_frames > 0:
            game.flash_frames -= 1
            return

        # Pausa: não actualizamos física nem nada
        if game.game_state and game.game_state.paused:
            return

        # --- UPDATE JOGADOR ---
        keys = pg.get_keys()
        if game.player:
            game.player.handle_input(keys)
            game.player.update_animation(dt)
            game.player.apply_gravity()
            game.handle_player_shoot()

        # --- UPDATE INIMIGOS ---
        if game.enemy_manager:
            game.enemy_manager.update()
            game.enemies = game.enemy_manager.get_enemies()
            new_enemy_projectiles = game.enemy_manager.get_projectiles()
            game.enemy_projectiles.extend(new_enemy_projectiles)

        # --- UPDATE PROJÉCTEIS ---
        for proj in game.projectiles + game.enemy_projectiles:
            if proj:
                proj.update()

        # --- COLISÕES ---
        game.handle_collisions()

        # Se o Game Over trocou de cena, não continuamos
        if not isinstance(game.current_scene, LevelScene):
            return

        # --- FLOATING TEXTS ---
        for text in game.floating_texts:
            text.update()
        game.floating_texts = [t for t in game.floating_texts if t.lifetime > 0]

        # --- CÂMARA / POV ---
        if game.player:
            game.POV = game.player.rect.centerx - config.WIDTH // 2
            game.POV = max(0, min(game.POV, game.bg_width - config.WIDTH))

    def draw(self, screen: pg.Surface):
        game = self.game

        # Flash de cheat tem prioridade visual
        if game.flash_frames > 0 and game.flash_color is not None:
            screen.fill(game.flash_color)
            return

        # Cena normal
        game.draw_scene()
        game.draw_hud()


if __name__ == "__main__":
    Game().run()
