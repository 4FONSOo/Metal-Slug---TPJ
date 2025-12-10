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
import random  # <- para o enemy_factory

import pg_engine as pg
import config
import controls

from scene import Scene
from scenes.menu import Menu as MenuSecene, PauseMenu
from cheats import CheatEngine
from managers.input_manager import (
    is_fire_pressed,
    get_shoot_direction,
    is_granade_pressed,
)
from managers.pickup_manager import PickupManager
from managers.projectile_manager import ProjectileManager
from managers.collision_manager import CollisionManager
from managers.combat_manager import (
    CombatManager,
    CombatInput,
    MeleeAttackEvent,
    ShootEvent,
    ThrowGrenadeEvent,
)
from managers.effects_manager import EffectsManager
from managers.enemy_manager import EnemyManager, SpawnZone

from entity.player import Player
from entity.enemy import (
    Enemy,
    EnemySoldier,
    EnemyShooter,
    EnemyHeavy,
    EnemyFast,
)

from entity.boss import Boss

from entity.projectile import Projectile
from entity.granade import Granade  # lógica da granada

from scenes.Lvl1 import load_level as load_level_1
from scenes.Lvl2 import load_level as load_level_2

LEVEL_LOADERS = [
    load_level_1,  # índice 0 → Lvl1
    load_level_2,  # índice 1 → Lvl2
]

from scenes.menu import Menu as MenuScene  # cena de menu principal

from sound import SoundManager
from config import DIFFICULTY_PRESETS, DEFAULT_DIFFICULTY, CHEAT_CODES
from pg_engine import Vector2
from score import ScoreManager, EnterNameScene, HighScoreScene
from resource import load_pickup_sprites, load_enemy


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

        # Sprites dos pickups (health, granadas, etc.)
        try:
            self.pickup_sprites = load_pickup_sprites()
        except Exception as e:
            print(f"[WARN] Falha a carregar sprites de pickups: {e}")
            self.pickup_sprites = {}

        # Sistema de scores (pontuação actual + highscores)
        self.score_manager = ScoreManager()

        # Cena actual (menu, nível, etc.)
        self.current_scene: Scene | None = None
        self.running = True

        # Nível / cenário
        self.level = None
        self.background = None
        self.bg_width = config.WIDTH
        self.platforms: list[pg.Rect] = []
        self.current_level_id: int = 1

        #self.debug_level_index = 0  # cheat TTT

        # Jogador / inimigos / projécteis
        self.player_choice = "player1"
        self.player: Player | None = None
        self.enemy_manager: EnemyManager | None = None
        self.enemies: list[object] = []
        self.projectiles: list[Projectile] = []          # projécteis do jogador
        self.enemy_projectiles: list[Projectile] = []    # projécteis dos inimigos
        self.granades: list[Granade] = []                # granadas do jogador
        self.floating_texts: list[FloatingText] = []

        # Boss de nível (ex: helicóptero)
        self.boss: Boss | None = None
        self.has_boss: bool = False

        # Gestor de projécteis
        self.projectile_manager: ProjectileManager | None = None

        # Gestor de colisões (stateless, pode ser partilhado)
        self.collision_manager = CollisionManager()

        # Gestor de combate (input → eventos de tiro/melee/granada)
        self.combat_manager: CombatManager | None = None

        
        #isto vai sair
        
        self.camera_shake_time = 0.0
        self.camera_shake_intensity = 0.0
        self.camera_shake_offset_x = 0


        # Efeitos (flash, NUKE, slow-motion)
        self.effects = EffectsManager()

        # Pickups / power-ups
        self.pickup_manager: PickupManager | None = None

        # Disparo / mira
        self.shoot_pressed = False        # estado da tecla de tiro no frame anterior
        self.granade_pressed = False      # estado da tecla de granada no frame anterior
        self.aim_dir = Vector2(1, 0)

        # Upgrade de arma (stacks afectam dano / fire-rate)
        self.weapon_upgrade_stacks = 0
        self.weapon_fire_rate_multiplier = 1.0
        self.weapon_damage_multiplier = 1.0

        # POV = deslocamento da “câmara” horizontal
        self.POV = 0

        # Dificuldade
        self.difficulty = DEFAULT_DIFFICULTY
        self.difficulty_preset = DIFFICULTY_PRESETS[self.difficulty]

        # Estado lógico (score / tempo / etc.)
        self.game_state: GameState | None = None

        # Debug Only: Troca entre o Lvl1 e Lvl2 (posso complicar, mas............)
        self.debug_start_level = 1

        # Cheats
        self.cheat_engine = CheatEngine(CHEAT_CODES)
        self.god_mode = False
        self.infinite_time = False
        self.infinite_granades = False
        self.super_jump = False

        self.debug_level_index = 0

        # Começamos no menu principal
        self.change_scene(MenuScene(self))

    # ----------------------------- #
    # GESTÃO DE CENAS
    # ----------------------------- #
    def change_scene(self, new_scene: Scene):
        """Troca de cena de forma civilizada."""
        if self.current_scene is not None:
            self.current_scene.on_exit()
        self.current_scene = new_scene
        self.current_scene.on_enter()

    # ----------------------------- #
    # DIFICULDADE
    # ----------------------------- #
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

        # Se o nível for “caótico”, quadruplicar nº de inimigos
        if getattr(self, "enemy_density", "normal") == "chaotic":
            max_spawns *= 4
            max_active *= 4

        return max_spawns, max_active, damage_multiplier

    # ----------------------------- #
    # FX
    # ----------------------------- #
    def flash(self, color, frames=None):
        """
        Flash de ecrã via EffectsManager (usado pelos cheats e NUKE).
        Mantém compatibilidade com a API antiga baseada em 'frames'.
        """
        if not getattr(self, "effects", None):
            return

        if frames is None:
            # nº de frames padrão (por ex. 10); cai para 10 se não existir na config
            frames = getattr(config, "SCREEN_FLASH_DEFAULT_FRAMES", 10)

        try:
            duration = max(0.0, float(frames)) / float(config.FPS)
        except Exception:
            # fallback seguro
            duration = frames / 60.0

        # Fade linear durante a duração toda
        self.effects.trigger_flash(
            color=color,
            duration=duration,
            fade_time=duration,
        )
    
    
    def trigger_camera_shake(self, duration: float, intensity: float = 6.0) -> None:
        """
        Wrapper para o tremor de câmara no EffectsManager.
        """
        if not getattr(self, "effects", None):
            return

        try:
            self.effects.trigger_camera_shake(duration, intensity)
        except Exception:
            pass

    def _update_camera_shake(self, dt_seconds: float) -> None:
        """Actualiza offsets de tremor de câmara."""
        if self.camera_shake_time <= 0.0:
            self.camera_shake_time = 0.0
            self.camera_shake_offset_x = 0
            return

        self.camera_shake_time -= dt_seconds
        if self.camera_shake_time <= 0.0:
            self.camera_shake_time = 0.0
            self.camera_shake_offset_x = 0
            return

        max_off = int(self.camera_shake_intensity)
        if max_off <= 0:
            self.camera_shake_offset_x = 0
            return

        # Tremor horizontal aleatório
        self.camera_shake_offset_x = random.randint(-max_off, max_off)

    # ----------------------------- #
    # BOSS
    # ----------------------------- #
    def maybe_spawn_boss(self) -> None:
        """Cria o boss quando o player chega a ~85% do nível."""
        if not self.has_boss:
            return
        if self.boss is not None:
            return
        if not self.player or self.bg_width <= 0:
            return

        progress = self.player.rect.centerx / float(self.bg_width)
        if progress < 0.85:
            return

        # Sprite do boss (guardaste boss.png em assets/enemy)
        img = load_enemy(
            getattr(config, "BOSS_WIDTH", 160),
            getattr(config, "BOSS_HEIGHT", 120),
            "boss.png",
        )

        # Spawn um bocado à frente do player mas dentro do nível
        spawn_x = self.player.rect.centerx + config.WIDTH // 3
        spawn_x = max(0, min(self.bg_width - img.get_width(), spawn_x))

        start_y = -img.get_height()
        target_y = int(config.HEIGHT * getattr(config, "BOSS_TARGET_Y_RATIO", 0.15))

        self.boss = Boss(img, spawn_x, start_y, target_y)

    def update_boss(self, dt_seconds: float) -> None:
        """Actualiza boss + garante que entra nas listas de colisão/desenho."""
        if not self.has_boss:
            return

        # Spawna se ainda não existir
        self.maybe_spawn_boss()

        boss = self.boss
        if not boss or not getattr(boss, "alive", False):
            # (Mais tarde podemos tratar aqui do fim de nível ao matar o boss)
            return

        # Movimento / AI / tiros
        boss.update(dt_seconds, self)

        # Garante que é considerado para colisões / melee / granadas
        if boss not in self.enemies:
            self.enemies.append(boss)


  # ----------------------------- #
    # CHEATS
    # ----------------------------- #
    def process_cheats(self, event) -> bool:
        """Processa letras para códigos de cheat. Devolve True se consumiu a tecla."""
        if event.type != pg.KEYDOWN:
            return False

        key_name = pg.key_name(event.key)
        if not key_name or len(key_name) != 1:
            return False

        # Normalizar para 1 letra (A-Z)
        key_name = key_name.upper()
        if not key_name.isalpha():
            return False

        consumed, activations = self.cheat_engine.process_char(key_name)

        for code, active in activations:
            # GOD MODE
            if code == "GOD":
                self.god_mode = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_GOD_ON
                    if active
                    else config.CHEAT_FLASH_COLOR_GOD_OFF
                )

            # TEMPO INFINITO
            elif code == "TIME":
                self.infinite_time = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_TIME_ON
                    if active
                    else config.CHEAT_FLASH_COLOR_TIME_OFF
                )

            # SUPER JUMP
            elif code == "SPJ":
                self.super_jump = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_SPJ_ON
                    if active
                    else config.CHEAT_FLASH_COLOR_SPJ_OFF
                )
                if self.player:
                    self.player.jump_speed = (
                        config.CHEAT_SUPER_JUMP_VALUE
                        if active
                        else config.CHEAT_NORMAL_JUMP_VALUE
                    )

            # GRANADAS INFINITAS
            elif code == "GRN":
                self.infinite_granades = active
                self.flash(
                    config.CHEAT_FLASH_COLOR_GRN_ON
                    if active
                    else config.CHEAT_FLASH_COLOR_GRN_OFF
                )

                # Actualizar CombatManager e garantir pelo menos 1 granada
                if self.combat_manager:
                    self.combat_manager.enable_infinite_grenades(active)
                    try:
                        if active and self.combat_manager.grenades <= 0:
                            self.combat_manager.set_grenades(1)
                    except Exception:
                        pass

                if active and self.player and getattr(self.player, "granades", 0) <= 0:
                    self.player.granades = 1

            # TROCA – muda o nível inicial (só no Menu)
            elif code == "TTT":
                # Só funciona no menu principal
                if not isinstance(self.current_scene, MenuScene):
                    continue

                # Nº máximo de níveis de debug (ajusta aqui se adicionares mais)
                max_levels = getattr(config, "DEBUG_MAX_LEVELS", 2)
                try:
                    max_levels = int(max_levels)
                except Exception:
                    max_levels = 2
                if max_levels < 1:
                    max_levels = 1

                if self.debug_level_index < max_levels - 1:
                    # Avança para o próximo nível de debug
                    self.debug_level_index += 1
                    try:
                        color = getattr(
                            config,
                            "CHEAT_FLASH_COLOR_TROCA",
                            (100, 255, 100),
                        )
                        self.flash(color)
                    except Exception:
                        pass

                    print(
                        f"[CHEAT] Próximo jogo começa no nível "
                        f"{self.debug_level_index + 1}/{max_levels}"
                    )
                else:
                    # Já não há mais níveis → ecrã “CHEATER, no more levels”
                    if hasattr(self, "show_no_more_levels"):
                        self.show_no_more_levels()
                    else:
                        # fallback seguro: reset evitar crash
                        self.debug_level_index = 0
                        print("[CHEAT] No more levels → reset para nível 1")

        return consumed

    def reset_all_state(self):
        """Reset total: cheats, estado lógico, entidades e música."""
        self.cheat_engine.reset_all()
        self.god_mode = False
        self.infinite_time = False
        self.infinite_granades = False
        self.super_jump = False

        # Reset da pontuação actual e estado lógico do jogo
        self.score_manager.reset_current()
        self.game_state = GameState(
            initial_score=self.score_manager.current_score,
            initial_time=self._get_initial_time_for_difficulty(),
        )

        self.player = None

        self.boss = None
        self.has_boss = False

        if self.enemy_manager:
            self.enemy_manager.clear()
        
        self.enemy_manager = None
        self.enemies.clear()

        self.projectiles.clear()
        self.enemy_projectiles.clear()
        self.granades.clear()
        self.floating_texts.clear()

        if self.pickup_manager:
            self.pickup_manager.clear()
        self.pickup_manager = None

        if self.projectile_manager:
            self.projectile_manager.clear()
        self.projectile_manager = None

        # Reset de combate / upgrade
        self.combat_manager = None
        self.weapon_upgrade_stacks = 0
        self.weapon_fire_rate_multiplier = 1.0
        self.weapon_damage_multiplier = 1.0

        self.shoot_pressed = False
        self.granade_pressed = False

        try:
            self.sound.stop_music()
        except Exception:
            pass

    # ----------------------------- #
    # GAME OVER / START
    # ----------------------------- #
    def handle_game_over(self):
        """Mostra GAME OVER, trata de highscores e volta ao menu."""
        # Sincroniza pontuação actual com o ScoreManager (por segurança)
        if self.game_state:
            self.score_manager.current_score = self.game_state.score

        final_score = self.score_manager.current_score

        # Pára a música e mostra texto de GAME OVER
        self.sound.stop_music()
        text = pg.render_text(self.font, "GAME OVER", (255, 50, 50))
        self.screen.blit(
            text,
            (config.WIDTH // 2 - text.get_width() // 2, config.HEIGHT // 2),
        )
        pg.display_flip()
        pg.time_wait(config.GAME_OVER_WAIT_MS)

        # Se o score entrar no top, pedir nome
        if final_score > 0 and self.score_manager.qualifies_for_highscore():
            enter_scene = EnterNameScene(self.screen, self.clock, self.score_manager)
            name = enter_scene.run()
            if name:
                self.score_manager.register_current_score(name)

        # Mostrar tabela de highscores
        high_scene = HighScoreScene(self.screen, self.clock, self.score_manager)
        high_scene.run()

        # Reset do estado e voltar ao menu
        self.reset_all_state()

        #DEBUG DE NÍVEL

        self.change_scene(MenuScene(self))

    def show_no_more_levels(self):
        """
        Ecrã de debug quando o cheat TROCA tenta ir para além do último nível.

        Mostra:
          CHEATER
          no more levels

        ENTER: volta ao menu com o nível 1 seleccionado.
        """
        big_font = pg.create_font(
            getattr(config, "MENU_FONT_NAME", config.HUD_FONT_NAME),
            72,
        )
        small_font = pg.create_font(
            getattr(config, "MENU_OPTIONS_FONT_NAME", config.HUD_FONT_NAME),
            26,
        )

        title_surf = pg.render_text(big_font, "CHEATER", (255, 50, 50))
        msg_surf = pg.render_text(big_font, "no more levels", (255, 255, 255))
        hint_surf = pg.render_text(
            small_font,
            "ENTER: voltar ao nível 1",
            (200, 200, 200),
        )

        # Pequeno flash só para reforçar que foi um cheat
        try:
            self.flash((255, 50, 50))
        except Exception:
            pass

        while True:
            for event in pg.get_events():
                if event.type == pg.QUIT:
                    try:
                        self.sound.stop_music()
                    except Exception:
                        pass
                    pg.quit()
                    sys.exit()
                elif event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    # Reset lógico para o primeiro nível
                    self.debug_level_index = 0
                    print("[CHEAT] Reset para nível 1 após 'no more levels'")
                    return

            self.screen.fill((0, 0, 0))

            self.screen.blit(
                title_surf,
                (
                    config.WIDTH // 2 - title_surf.get_width() // 2,
                    config.HEIGHT // 2 - 150,
                ),
            )
            self.screen.blit(
                msg_surf,
                (
                    config.WIDTH // 2 - msg_surf.get_width() // 2,
                    config.HEIGHT // 2 - 40,
                ),
            )
            self.screen.blit(
                hint_surf,
                (
                    config.WIDTH // 2 - hint_surf.get_width() // 2,
                    config.HEIGHT // 2 + 60,
                ),
            )

            pg.display_flip()
            self.clock.tick(config.FPS)

    def show_level_complete_screen(self) -> None:
        """
        Ecrã de 'COMPLETE' no fim de um nível.
        Toca end.mp3 e espera por ENTER antes de continuar.
        """
        try:
            big_font = pg.create_font(
                getattr(config, "MENU_FONT_NAME", config.HUD_FONT_NAME),
                72,
            )
            small_font = pg.create_font(
                getattr(config, "MENU_OPTIONS_FONT_NAME", config.HUD_FONT_NAME),
                26,
            )
        except Exception:
            big_font = self.font
            small_font = self.font

        title_surf = pg.render_text(big_font, "COMPLETE", (255, 255, 0))
        hint_surf = pg.render_text(
            small_font,
            "ENTER para continuar",
            (220, 220, 220),
        )

        # Música de fim de nível
        try:
            self.sound.stop_music()
        except Exception:
            pass

        # Tentar tocar end.mp3 como música; se falhar, tenta como SFX
        try:
            self.sound.play_music("end.mp3")
        except Exception:
            try:
                self.sound.play_sfx("end.mp3")
            except Exception:
                pass

        # Loop até ENTER / ESC / SPACE
        while True:
            for event in pg.get_events():
                if event.type == pg.QUIT:
                    try:
                        self.sound.stop_music()
                    except Exception:
                        pass
                    pg.quit()
                    sys.exit()
                elif event.type == pg.KEYDOWN:
                    if event.key in (pg.K_RETURN, pg.K_SPACE, pg.K_ESCAPE):
                        return

            self.screen.fill((0, 0, 0))

            self.screen.blit(
                title_surf,
                (
                    config.WIDTH // 2 - title_surf.get_width() // 2,
                    config.HEIGHT // 2 - 100,
                ),
            )
            self.screen.blit(
                hint_surf,
                (
                    config.WIDTH // 2 - hint_surf.get_width() // 2,
                    config.HEIGHT // 2 + 20,
                ),
            )

            pg.display_flip()
            self.clock.tick(config.FPS)

    def show_loading_screen(self, seconds: float = 4.0) -> None:
        """
        Ecrã simples de 'Loading...' com barra de progresso.
        A barra enche ao longo de 'seconds'.
        """
        try:
            font_name = getattr(config, "MENU_FONT_NAME", config.HUD_FONT_NAME)
            font_size = getattr(config, "MENU_TITLE_FONT_SIZE", 48)
            font = pg.create_font(font_name, font_size)
        except Exception:
            font = self.font

        text_surf = pg.render_text(font, "Loading...", (255, 255, 255))

        total_time = max(0.1, float(seconds))
        frames = int(total_time * config.FPS)

        # Barra de loading
        bar_width = int(config.WIDTH * 0.6)
        bar_height = 20
        bar_x = (config.WIDTH - bar_width) // 2
        bar_y = config.HEIGHT // 2 + 40

        for i in range(frames):
            for event in pg.get_events():
                if event.type == pg.QUIT:
                    try:
                        self.sound.stop_music()
                    except Exception:
                        pass
                    pg.quit()
                    sys.exit()

            progress = (i + 1) / float(frames)

            self.screen.fill((0, 0, 0))

            # Texto "Loading..."
            self.screen.blit(
                text_surf,
                (
                    config.WIDTH // 2 - text_surf.get_width() // 2,
                    config.HEIGHT // 2 - text_surf.get_height() // 2 - 30,
                ),
            )

            # Fundo da barra
            pg.draw_rect(
                self.screen,
                (60, 60, 60),
                (bar_x, bar_y, bar_width, bar_height),
            )

            # Parte preenchida
            pg.draw_rect(
                self.screen,
                (200, 200, 50),
                (bar_x, bar_y, int(bar_width * progress), bar_height),
            )

            pg.display_flip()
            self.clock.tick(config.FPS)

    def go_to_next_level(self) -> None:
        """
        Transição automática para o nível seguinte (usado no fim do Lvl1).

        Mantém pontuação e estado básico do jogador (HP / granadas).
        """
        # Índice actual / próximo (debug_level_index 0→1, etc.)
        max_index = max(0, len(LEVEL_LOADERS) - 1)
        current_idx = max(0, min(self.debug_level_index, max_index))
        next_idx = current_idx + 1

        if next_idx > max_index:
            # Sem mais níveis definidos → trata como "no more levels" / fim de jogo
            try:
                self.show_no_more_levels()
            except Exception:
                self.handle_game_over()
            return

        # Guardar estado a manter
        prev_score = 0
        if self.game_state:
            prev_score = self.game_state.score
        prev_sm_score = (
            self.score_manager.current_score if self.score_manager else prev_score
        )

        prev_player_hp = None
        prev_player_grenades = 0
        if self.player:
            prev_player_hp = getattr(self.player, "hp", None)
            prev_player_grenades = getattr(self.player, "granades", 0)

        prev_cm_grenades = None
        if self.combat_manager:
            try:
                prev_cm_grenades = self.combat_manager.grenades
            except Exception:
                prev_cm_grenades = None

        # Avançar para o próximo nível
        self.debug_level_index = next_idx

        # Ecrã de Loading (bloqueante durante ~4s)
        self.show_loading_screen(seconds=4.0)

        # Arranca nível seguinte (faz reset completo internamente)
        self.start_game()

        # Restaurar pontuação
        if self.game_state:
            self.game_state.score = prev_score
        if self.score_manager:
            self.score_manager.current_score = prev_sm_score

        # Restaurar estado básico do jogador
        if self.player:
            if prev_player_hp is not None:
                # Não deixar passar do novo max_hp
                try:
                    self.player.hp = max(
                        0,
                        min(int(prev_player_hp), int(self.player.max_hp)),
                    )
                except Exception:
                    self.player.hp = prev_player_hp

            try:
                self.player.granades = max(0, int(prev_player_grenades))
            except Exception:
                pass

        if self.combat_manager and prev_cm_grenades not in (None, float("inf")):
            try:
                self.combat_manager.set_grenades(int(prev_cm_grenades))
            except Exception:
                pass



    def start_game(self):
        """
        Arranca um novo jogo:
          - faz reset de estado
          - carrega o nível
          - cria player e inimigos
          - muda para a cena de jogo (LevelScene)
        """
        self.reset_all_state()

        # Nível (TMX) – escolhe pelo índice de debug
        max_index = max(0, len(LEVEL_LOADERS) - 1)
        level_index = max(0, min(self.debug_level_index, max_index))
        load_fn = LEVEL_LOADERS[level_index]

        self.level = load_fn()
        self.background = self.level["background"]
        self.bg_width = self.level["bg_width"]
        self.platforms = self.level["platforms"]
        self.current_level_id = int(self.level.get("level_id", 1))
        self.has_boss = bool(self.level.get("has_boss", False))
        self.boss = None
        self.enemy_density = self.level.get("enemy_density", "normal")

        # Gestor de pickups (power-ups)
        ground_y = config.HEIGHT
        self.pickup_manager = PickupManager(
            level_width=self.bg_width,
            ground_y=ground_y,
            platforms=self.platforms,
            auto_spawn=True,
        )

        # Gestor de projécteis
        self.projectile_manager = ProjectileManager()
        self.projectiles = self.projectile_manager.get_player_projectiles()
        self.enemy_projectiles = self.projectile_manager.get_enemy_projectiles()

        # Música do nível:
        #   - Lvl1  → theme.mp3
        #   - Lvl2  → theme2.mp3
        self.sound.stop_music()
        try:
            if level_index == 1 or self.current_level_id == 2:
                music_file = "theme2.mp3"
            else:
                music_file = "theme.mp3"
            self.sound.play_music(music_file)
        except Exception:
            # fallback: tenta sempre a original
            self.sound.play_music("theme.mp3")
        self.sound.play_level_start()
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

        # Sistema de combate do jogador
        base_interval = config.PLAYER_FIRE_INTERVAL_MS / 1000.0
        self.combat_manager = CombatManager(
            base_fire_interval=base_interval,
            upgraded_fire_interval=base_interval,  # ajustado quando apanha upgrade
            melee_priority=True,
            initial_grenades=getattr(self.player, "granades", 0),
        )
        # se o cheat de granadas infinitas já estiver activo
        self.combat_manager.enable_infinite_grenades(self.infinite_granades)

        # Inimigos – EnemyManager genérico + fábrica de inimigos concretos
        max_spawns, max_active, damage_mult = self._get_enemy_params_for_difficulty()

        # Factory que recria a lógica antiga:
        #  - tipos diferentes (soldier/shooter/heavy/fast)
        #  - sprite adequado
        #  - patrol min/max
        #  - plataformas
        
        def enemy_factory(spawn_x: float, _spawn_y: float) -> Enemy:
            p = random.random()

            # Distribuição:
            #  - nível 1: 15% heavy, 30% shooter, 55% pequenos
            #  - nível 2: 5% heavy, 10% shooter, 85% pequenos (mais caos de mooks)
            
            if getattr(self, "current_level_id", 1) == 2:
                heavy_thr = 0.05
                shooter_thr = 0.15
            else:
                heavy_thr = 0.15
                shooter_thr = 0.45

            if p < heavy_thr:
                cls, sprite = EnemyHeavy, "Rebel3.png"
            elif p < shooter_thr:
                cls, sprite = EnemyShooter, "Rebel2.png"
            else:
                cls, sprite = random.choice(
                    [
                        (EnemySoldier, "Rebel1.png"),
                        (EnemyFast, "Rebel4.png"),
                    ]
                )

            # Clamp do X dentro de margens seguras
            margin_x = config.ENEMY_MANAGER_SPAWN_X_MARGIN
            x = int(spawn_x)
            x = max(margin_x, min(self.bg_width - margin_x, x))

            # Y inicial aleatório, tal como antes
            y = random.randint(
                config.ENEMY_MANAGER_SPAWN_Y_MIN,
                config.HEIGHT // 2,
            )

            img = load_enemy(80, 80, sprite)
            enemy = cls(img, x, y, damage_multiplier=damage_mult)

            # Plataformas para gravidade / colisão
            enemy.set_platforms(self.platforms)

            # Zona de patrulha
            patrol = random.randint(
                config.ENEMY_MANAGER_PATROL_MIN,
                config.ENEMY_MANAGER_PATROL_MAX,
            )
            enemy.min_x = max(0, x - patrol)
            enemy.max_x = min(self.bg_width, x + patrol)

            return enemy

        # Zona de spawn única que cobre praticamente o nível todo
        spawn_margin = getattr(config, "ENEMY_MANAGER_SPAWN_X_MARGIN", 100)
        spawn_margin = max(1, int(spawn_margin))

        spawn_zone = SpawnZone(
            x_min=spawn_margin,
            x_max=max(spawn_margin + 1, self.bg_width - spawn_margin),
            y=0.0,  # o Y real é escolhido no factory
        )

        self.enemy_manager = EnemyManager(
            enemy_factory,
            max_spawns=max_spawns,
            max_active=max_active,
            spawn_zones=[spawn_zone],
            auto_spawn=True,
            enemy_projectiles=self.enemy_projectiles,
            bg_width=self.bg_width,
        )

        # Spawn inicial até ao limite de activos
        for _ in range(min(max_active, max_spawns)):
            self.enemy_manager.try_spawn_enemy()

        self.enemies = self.enemy_manager.get_enemies()

        # Listas de textos / granadas / POV
        self.granades = []
        self.floating_texts = []
        self.POV = 0

        # Muda para a cena de jogo
        self.change_scene(LevelScene(self))

    # ----------------------------- #
    # COMBATE / HELPERS
    # ----------------------------- #
    def add_score(self, points: int, x: int | None = None, y: int | None = None):
        """Adiciona pontos à pontuação actual e, opcionalmente, cria texto flutuante."""
        if points <= 0:
            return

        if self.game_state:
            self.game_state.score += points
        if self.score_manager:
            self.score_manager.add_points(points)

        if x is not None and y is not None:
            self.floating_texts.append(FloatingText(f"+{points}", x, y))

    def apply_pickup_effect(self, effect: dict) -> None:
        """
        Aplica um efeito de pickup ao estado actual do jogo.

        Convenções esperadas no dicionário `effect` (tudo opcional; só aplica o que existir):
          - type: string com o tipo lógico ("hp", "grenade", "score", "nuke", "time", ...).
          - hp / heal / hp_delta: int – cura/dano no jogador.
          - granades / grenades / grenades_delta: int – ajusta nº de granadas do jogador.
          - score / points: int – pontos a adicionar.
          - time / time_delta / seconds: int – segundos a adicionar ao tempo restante.
          - nuke: bool – se True, mata todos os inimigos actuais.
        """
        if not effect:
            return

        player = self.player
        gs = self.game_state

        kind = str(effect.get("type", effect.get("kind", ""))).lower()

        # ---------------- HP / cura ----------------
        hp_delta = None
        if "hp" in effect:
            hp_delta = effect["hp"]
        elif "heal" in effect:
            hp_delta = effect["heal"]
        elif "hp_delta" in effect:
            hp_delta = effect["hp_delta"]

        if player and isinstance(hp_delta, (int, float)):
            player.hp = max(0, min(player.max_hp, player.hp + int(hp_delta)))

        # ---------------- Granadas ----------------
        gren_delta = None
        for key in ("granades", "grenades", "grenade_delta", "grenades_delta"):
            if key in effect:
                gren_delta = effect[key]
                break

        if isinstance(gren_delta, int):
            if self.combat_manager:
                self.combat_manager.add_grenades(gren_delta)
                if player and not self.infinite_granades:
                    remaining = self.combat_manager.grenades
                    if remaining != float("inf"):
                        player.granades = max(0, int(remaining))
            elif player:
                current = int(getattr(player, "granades", 0))
                player.granades = max(0, current + gren_delta)

        # ---------------- Pontuação ----------------
        score_delta = effect.get("score", effect.get("points"))
        if isinstance(score_delta, int):
            fx_x = player.rect.centerx if player else None
            fx_y = player.rect.top if player else None
            self.add_score(score_delta, fx_x, fx_y)

        # ---------------- Tempo extra ----------------
        time_delta = None
        for key in ("time", "time_delta", "seconds"):
            if key in effect:
                time_delta = effect[key]
                break

        if gs and isinstance(time_delta, (int, float)):
            gs.time_left = max(0, gs.time_left + int(time_delta))

        # ---------------- UPGRADE DE ARMA ----------------
        if kind == "weapon_up":
            ammo = int(effect.get("ammo", 0) or 0)
            mult = float(effect.get("fire_rate_multiplier", 1.0) or 1.0)
            self.activate_weapon_upgrade(ammo, mult)

        # ---------------- NUKE / bomba total ----------------
        if effect.get("nuke") or kind in ("nuke", "bomb", "kill_all"):
            # Efeito visual + slow-motion opcional via EffectsManager
            if self.effects:
                try:
                    self.effects.trigger_nuke(
                        total_duration=getattr(config, "NUKE_TOTAL_DURATION", 0.8),
                        flash_color=getattr(
                            config,
                            "NUKE_FLASH_COLOR",
                            (255, 255, 255),
                        ),
                        slowmo_factor=getattr(config, "NUKE_SLOWMO_FACTOR", 0.3),
                        slowmo_duration=getattr(
                            config,
                            "NUKE_SLOWMO_DURATION",
                            0.5,
                        ),
                    )
                except Exception:
                    pass

            for enemy in self.enemies:
                if not getattr(enemy, "alive", False):
                    continue
                enemy.take_damage(99999)
                if not enemy.alive:
                    points = getattr(enemy, "points", 100)
                    self.add_score(points, enemy.rect.centerx, enemy.rect.top)

        # ---------------- Som opcional ----------------
        sfx_name = effect.get("sfx") or None
        if sfx_name and hasattr(self.sound, "play_sfx"):
            try:
                self.sound.play_sfx(sfx_name)
            except Exception:
                pass
        elif hasattr(self.sound, "play_sfx"):
            try:
                self.sound.play_sfx("pickup")
            except Exception:
                pass

    def activate_weapon_upgrade(self, ammo: int, fire_rate_multiplier: float) -> None:
        """
        Activa/empilha o upgrade de arma (pickup WEAPON_UP).

        - Até WEAPON_UPGRADE_MAX_STACKS upgrades empilham efeito (mais dano / fire-rate).
        - A partir do 4.º, não aumenta mais o poder, só dá munição extra (2x ammo base).
        """
        ammo = max(0, int(ammo or 0))
        if ammo <= 0:
            return

        max_stacks = getattr(config, "WEAPON_UPGRADE_MAX_STACKS", 3)

        # Gestão de stacks
        if self.weapon_upgrade_stacks < max_stacks:
            self.weapon_upgrade_stacks += 1
            extra_presses = ammo
        else:
            # Já no máximo → só munição extra (2x)
            extra_presses = ammo * 2

        # Recalcular multiplicadores com base no nº de stacks
        stacks = max(1, self.weapon_upgrade_stacks)
        base_fire_mult = float(fire_rate_multiplier or 1.0)
        base_dmg_mult = getattr(config, "WEAPON_UPGRADE_DAMAGE_MULTIPLIER", 1.0)

        # Multiplicador acumulado: base^stacks
        self.weapon_fire_rate_multiplier = base_fire_mult ** stacks
        self.weapon_damage_multiplier = base_dmg_mult ** stacks

        # Configurar CombatManager: intervalo base vs. melhorado + munições
        if self.combat_manager:
            base_interval = config.PLAYER_FIRE_INTERVAL_MS / 1000.0
            self.combat_manager.base_fire_interval = base_interval
            self.combat_manager.upgraded_fire_interval = (
                base_interval * self.weapon_fire_rate_multiplier
            )
            self.combat_manager.apply_weapon_upgrade(extra_presses)

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
            if not enemy or not getattr(enemy, "alive", False):
                continue
            if not melee_rect.colliderect(enemy.rect):
                continue

            if facing == 1 and enemy.rect.centerx < player_rect.centerx:
                continue
            if facing == -1 and enemy.rect.centerx > player_rect.centerx:
                continue

            alvo = enemy
            break

        if not alvo:
            return False

        self.sound.play_melee()

        alvo.take_damage(config.MELEE_KILL_DAMAGE)

        if not alvo.alive:
            points = getattr(alvo, "points", 100)
            self.add_score(points, alvo.rect.centerx, alvo.rect.top)
            self.sound.play_enemy_death()

        return True

    def handle_collisions(self):
        """Trata colisões usando o CollisionManager."""
        if not self.collision_manager:
            return

        result = self.collision_manager.detect_collisions(
            self.player,
            self.enemies,
            self.projectiles,
            self.enemy_projectiles,
        )

        # Projécteis do player em inimigos
        for hit in result.enemy_hits:
            proj = hit.projectile
            enemy = hit.enemy

            if not getattr(enemy, "alive", False):
                continue

            damage = getattr(proj, "damage", 0)
            try:
                enemy.take_damage(damage)
            except Exception:
                pass

            if hasattr(proj, "trigger_hit"):
                try:
                    proj.trigger_hit()
                except Exception:
                    pass

            if not getattr(enemy, "alive", False):
                points = getattr(enemy, "points", 100)
                self.add_score(points, enemy.rect.centerx, enemy.rect.top)
                try:
                    self.sound.play_enemy_death()
                except Exception:
                    pass

        # Projécteis de inimigos em player
        if self.player and not self.god_mode:
            for hit in result.player_hits:
                proj = hit.projectile

                if not getattr(proj, "alive", False):
                    continue

                damage = getattr(proj, "damage", 0)
                self.player.take_damage(damage)

                if hasattr(proj, "trigger_hit"):
                    try:
                        proj.trigger_hit()
                    except Exception:
                        pass

        # Contacto físico player <-> inimigos
        if self.player and not self.god_mode:
            for contact in result.contact_hits:
                enemy = contact.enemy
                if not getattr(enemy, "alive", False):
                    continue

                try:
                    self.player.take_damage(enemy.contact_damage_to_player())
                    enemy.take_damage(enemy.contact_self_damage())
                except Exception:
                    pass

        # Limpar inimigos mortos
        self.enemies = [e for e in self.enemies if getattr(e, "alive", False)]

        # GAME OVER por morte do jogador
        if self.player and not self.player.alive:
            try:
                self.sound.play_game_over_sfx()
            except Exception:
                pass
            self.handle_game_over()

    def handle_combat(self, dt_seconds: float) -> None:
        """
        Processa input de combate (tiro, melee, granada) via CombatManager.
        """
        if not self.player or not self.combat_manager:
            return

        # Estados de teclas
        keys = pg.get_keys()
        fire_pressed = is_fire_pressed(keys)
        secondary_pressed = is_granade_pressed(keys)

        fire_just_pressed = fire_pressed and not self.shoot_pressed
        secondary_just_pressed = secondary_pressed and not self.granade_pressed

        # Guardar estado para próximo frame
        self.shoot_pressed = fire_pressed
        self.granade_pressed = secondary_pressed

        # Direcção discreta de tiro
        raw_dx, raw_dy = get_shoot_direction(
            keys,
            facing=self.player.facing,
            allow_diagonals=True,
        )

        combat_input = CombatInput(
            fire_pressed=fire_pressed,
            fire_just_pressed=fire_just_pressed,
            secondary_pressed=secondary_pressed,
            secondary_just_pressed=secondary_just_pressed,
            shoot_dir=(raw_dx, raw_dy),
        )

        events = self.combat_manager.update(dt_seconds, combat_input)

        # Mira suavizada (mantém o comportamento antigo)
        target_vec = Vector2(raw_dx, raw_dy)
        if target_vec.length_squared() == 0:
            if self.aim_dir.length_squared() == 0:
                target_vec = Vector2(1, 0)
            else:
                target_vec = self.aim_dir
        target_vec = target_vec.normalize()

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

        # Posição base de spawn dos projécteis
        cx = self.player.rect.centerx
        cy = self.player.rect.centery

        if raw_dx == 0 and raw_dy == -1:
            base_sx, base_sy = cx, self.player.rect.top
        elif raw_dx == 0 and raw_dy == 1:
            base_sx, base_sy = cx, cy
        else:
            base_sx = cx + raw_dx * config.PLAYER_PROJECTILE_OFFSET_X
            base_sy = cy - config.PLAYER_PROJECTILE_OFFSET_Y

        did_melee_hit = False

        for ev in events:
            if isinstance(ev, MeleeAttackEvent):
                if self.try_melee_attack():
                    did_melee_hit = True

            elif isinstance(ev, ShootEvent):
                # Se o melee acertou, ignoramos o tiro deste frame
                if did_melee_hit:
                    continue

                upgraded_shot = bool(ev.upgraded_weapon)

                # Pistola: 1 bala. Upgrade: 5 balas em linha, espaçadas.
                bullets_to_fire = 5 if upgraded_shot else 1

                projectile_color = config.PLAYER_PROJECTILE_COLOR
                if upgraded_shot:
                    projectile_color = (0, 0, 0)  # bala preta no upgrade

                for i in range(bullets_to_fire):
                    if upgraded_shot:
                        offset_dist = i * 25
                        sx = base_sx + int(aim.x * offset_dist)
                        sy = base_sy + int(aim.y * offset_dist)
                    else:
                        sx, sy = base_sx, base_sy

                    proj = Projectile(
                        sx,
                        sy,
                        aim.x,
                        aim.y,
                        max_range=self.bg_width,
                        color=projectile_color,
                    )

                    if upgraded_shot:
                        base_damage = getattr(proj, "damage", 1)
                        proj.damage = base_damage * self.weapon_damage_multiplier
                        try:
                            proj.rect.inflate_ip(4, 4)
                        except Exception:
                            pass

                    if self.projectile_manager:
                        self.projectile_manager.add_player_projectile(proj)
                    else:
                        self.projectiles.append(proj)

                # Som do tiro
                try:
                    if upgraded_shot:
                        self.sound.play_sfx("tiro2.mp3")
                    else:
                        self.sound.play_sfx("tiro1.mp3")
                except Exception:
                    pass

            elif isinstance(ev, ThrowGrenadeEvent):
                facing = getattr(self.player, "facing", 1)
                direction = 1 if facing >= 0 else -1

                g = Granade(
                    x=self.player.rect.centerx,
                    y=self.player.rect.centery,
                    direction=direction,
                    owner="player",
                )
                self.granades.append(g)

                # Sincronizar nº de granadas visível com CombatManager
                if (
                    not self.infinite_granades
                    and self.combat_manager
                    and self.player
                ):
                    remaining = self.combat_manager.grenades
                    if remaining != float("inf"):
                        self.player.granades = int(remaining)

    # ----------------------------- #
    # GRANADAS
    # ----------------------------- #
    def update_granades(self, dt_ms: float):
        """
        Actualiza lógica das granadas.
        dt_ms vem do clock (milissegundos).
        """
        dt = dt_ms / 1000.0 if dt_ms else 0.0

        for g in self.granades[:]:
            g.update(dt)

            # 1) Enquanto está a voar, verifica se bateu em algum inimigo
            if g.is_flying():
                gx, gy = g.get_center()
                gx_i, gy_i = int(gx), int(gy)

                radius = g.flight_radius
                grenade_rect = pg.Rect(
                    gx_i - radius,
                    gy_i - radius,
                    radius * 2,
                    radius * 2,
                )

                for enemy in self.enemies:
                    if not getattr(enemy, "alive", False):
                        continue
                    if enemy.rect.colliderect(grenade_rect):
                        g.explode()
                        break

            # 2) Explosão: aplica dano em área uma única vez
            if g.is_exploding() and not g.damage_applied:
                try:
                    self.sound.play_grenade_explosion()
                except Exception:
                    pass

                self.apply_granade_aoe_damage(g)
                g.damage_applied = True

            # 3) Limpa granadas mortas
            if g.is_dead():
                self.granades.remove(g)

    def apply_granade_aoe_damage(self, granade: Granade):
        """
        Aplica dano em área à volta da granada.
        Só afecta inimigos (por agora).
        """
        gx, gy = granade.get_center()
        r = granade.explosion_radius
        r2 = r * r

        for enemy in self.enemies:
            if not getattr(enemy, "alive", False):
                continue

            ex, ey = enemy.rect.center
            dx = ex - gx
            dy = ey - gy

            if dx * dx + dy * dy <= r2:
                enemy.take_damage(granade.damage)
                if not enemy.alive:
                    points = getattr(enemy, "points", 100)
                    self.add_score(points, enemy.rect.centerx, enemy.rect.top)
                    self.sound.play_enemy_death()

    # ----------------------------- #
    # DRAW HELPERS
    # ----------------------------- #
    def draw_scene(self):
        """Desenha cenário, inimigos, jogador, projécteis, granadas e textos flutuantes."""
        self.screen.fill((0, 0, 0))

        # Offset de tremor de câmara (horizontal)
        shake_x = 0
        if self.effects and hasattr(self.effects, "get_camera_shake_offset"):
            try:
                shake_x = int(self.effects.get_camera_shake_offset())
            except Exception:
                shake_x = 0

        if self.background:
            self.screen.blit(self.background, (-self.POV + shake_x, 0))

        # Pickups
        if self.pickup_manager:
            for p in self.pickup_manager.get_pickups():
                data = p.get_draw_data()
                if not data:
                    continue

                x = int(data.get("x", 0) - self.POV + shake_x)
                y = int(data.get("y", 0))
                w = int(data.get("width", 0))
                h = int(data.get("height", 0))
                color = data.get("color", (255, 255, 0))

                sprite = None
                if hasattr(self, "pickup_sprites") and self.pickup_sprites:
                    sprite = self.pickup_sprites.get(getattr(p, "kind", None))

                if sprite is not None:
                    img = sprite
                    img_rect = img.get_rect()
                    draw_x = x + (w - img_rect.width) // 2
                    draw_y = y + (h - img_rect.height) // 2
                    self.screen.blit(img, (draw_x, draw_y))
                else:
                    pg.draw_rect(self.screen, color, (x, y, w, h))

        # Inimigos
        for enemy in self.enemies:
            if not enemy:
                continue
            if hasattr(enemy, "draw"):
                try:
                    # POV “virtual” para tremer tudo
                    enemy.draw(self.screen, self.POV - shake_x)
                    continue
                except Exception:
                    pass
            img = getattr(enemy, "image", None)
            rect = getattr(enemy, "rect", None)
            if img is not None and rect is not None:
                self.screen.blit(img, (rect.x - self.POV + shake_x, rect.y))

        # Jogador
        if self.player:
            self.screen.blit(
                self.player.image,
                (self.player.rect.x - self.POV + shake_x, self.player.rect.y),
            )

        # Projécteis
        for proj in self.projectiles + self.enemy_projectiles:
            if proj:
                # Mesma ideia: POV ajustado
                proj.draw(self.screen, self.POV - shake_x)

        # Granadas
        for g in self.granades:
            data = g.get_draw_data()
            if not data:
                continue

            x = int(data["x"] - self.POV + shake_x)
            y = int(data["y"])
            radius = int(data["radius"])

            color = (255, 80, 80) if data["exploding"] else (255, 0, 0)
            pg.draw_circle(self.screen, color, (x, y), radius)

        for text in self.floating_texts:
            text.draw(self.screen, self.POV - shake_x)


        # Inimigos
        for enemy in self.enemies:
            if not enemy:
                continue
            if hasattr(enemy, "draw"):
                try:
                    enemy.draw(self.screen, self.POV)
                    continue
                except Exception:
                    pass
            img = getattr(enemy, "image", None)
            rect = getattr(enemy, "rect", None)
            if img is not None and rect is not None:
                self.screen.blit(img, (rect.x - self.POV, rect.y))

        # Boss (sprite única, se existir)
        if getattr(self, "boss", None):
            boss = self.boss
            img = getattr(boss, "image", None)
            rect = getattr(boss, "rect", None)
            if img is not None and rect is not None:
                if hasattr(boss, "draw"):
                    try:
                        boss.draw(self.screen, self.POV)
                    except Exception:
                        self.screen.blit(img, (rect.x - self.POV, rect.y))
                else:
                    self.screen.blit(img, (rect.x - self.POV, rect.y))

        # Boss
        if self.boss:
            try:
                self.boss.draw(self.screen, self.POV)
            except Exception:
                self.screen.blit(
                    self.boss.image,
                    (self.boss.rect.x - self.POV, self.boss.rect.y),
                )

        # Jogador
        if self.player:
            self.screen.blit(
                self.player.image,
                (self.player.rect.x - self.POV, self.player.rect.y),
            )

        # Projécteis
        for proj in self.projectiles + self.enemy_projectiles:
            if proj:
                proj.draw(self.screen, self.POV)

        # Granadas
        for g in self.granades:
            data = g.get_draw_data()
            if not data:
                continue

            x = int(data["x"] - self.POV)
            y = int(data["y"])
            radius = int(data["radius"])

            color = (255, 80, 80) if data["exploding"] else (255, 0, 0)
            pg.draw_circle(self.screen, color, (x, y), radius)

        for text in self.floating_texts:
            text.draw(self.screen, self.POV)

    def draw_hud(self):
        """Desenha HUD: pontuação, tempo, dificuldade, barra de HP."""
        if not self.game_state:
            return

        tempo_str = "∞" if self.infinite_time else f"{self.game_state.time_left}s"
        score_value = self.score_manager.current_score if self.score_manager else 0

        # Granadas
        granades_str = ""
        if self.player and hasattr(self.player, "granades"):
            if getattr(self, "infinite_granades", False):
                g_value = "∞"
            else:
                g_value = str(self.player.granades)
            granades_str = f"   G:{g_value}"

        # Balas / upgrade
        ammo_str = ""
        if self.combat_manager:
            if self.combat_manager.has_weapon_upgrade:
                ammo_value = str(int(self.combat_manager.upgrade_ammo))
            else:
                ammo_value = "∞"
            ammo_str = f"   B:{ammo_value}"

        top_text = (
            f"Pontuação: {score_value}   "
            f"Tempo: {tempo_str}   "
            f"Dif: {self.difficulty}"
            f"{granades_str}{ammo_str}"
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

            # Barra de vida do BOSS
        boss = getattr(self, "boss", None)
        if boss and getattr(boss, "alive", False):
            boss_ratio = boss.hp / boss.max_hp if boss.max_hp > 0 else 0

            bar_width = getattr(config, "HUD_BOSS_HP_BAR_WIDTH", 300)
            bar_height = getattr(config, "HUD_BOSS_HP_BAR_HEIGHT", 16)
            x = (config.WIDTH - bar_width) // 2
            y = getattr(config, "HUD_BOSS_HP_BAR_Y", 40)

            bg_color = getattr(config, "HUD_BOSS_HP_BG_COLOR", (40, 0, 0))
            bar_color = getattr(config, "HUD_BOSS_HP_COLOR", (220, 40, 40))

            pg.draw_rect(
                self.screen,
                bg_color,
                (x - 2, y - 2, bar_width + 4, bar_height + 4),
            )
            pg.draw_rect(
                self.screen,
                bar_color,
                (x, y, bar_width * boss_ratio, bar_height),
            )            

    # ----------------------------- #
    # LOOP GLOBAL
    # ----------------------------- #
    def run(self):
        """Loop global de jogo: delega tudo na cena actual."""
        while self.running:
            events = pg.get_events()
            dt = self.clock.get_time()

            if not self.current_scene:
                self.change_scene(MenuScene(self))

            self.current_scene.handle_input(events)
            self.current_scene.update(dt)
            self.current_scene.draw(self.screen)

            pg.display_flip()
            self.clock.tick(config.FPS)


# ----------------------------- #
# CENA DE JOGO (LEVEL)
# ----------------------------- #
class LevelScene(Scene):
    """
    Cena que trata do jogo em si (nível actual).
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
                    game.reset_all_state()
                    game.change_scene(MenuScene(game))
                    return

                if event.key == pause_key and not cheat_consumed:
                    game.change_scene(PauseMenu(game, previous_scene=self))
                    return

            if game.game_state and event.type == game.game_state.timer_event:
                if not game.infinite_time:
                    game.game_state.update_time()

    def update(self, dt: float):
        game = self.game

        # dt "real" (antes de slow-motion)
        dt_seconds_raw = dt / 1000.0 if dt else 0.0

        # Actualizar FX em tempo real
        if game.effects:
            game.effects.update(dt_seconds_raw)
            time_scale = game.effects.get_time_scale()
        else:
            time_scale = 1.0

        # dt afectado por slow-motion (para lógica de jogo)
        dt_seconds = dt_seconds_raw * time_scale
        dt_ms_scaled = dt * time_scale if dt else 0.0

        # Condição de timeout / fim de nível
        timeout = (
            game.game_state
            and game.game_state.time_left <= 0
            and not game.infinite_time
        )

        if timeout:
            player_alive = bool(game.player and game.player.alive)

            if player_alive:
                try:
                    game.sound.play_level_end()
                except Exception:
                    pass
            else:
                try:
                    game.sound.play_game_over_sfx()
                except Exception:
                    pass

            game.handle_game_over()
            return

        # Pausa lógica
        if game.game_state and game.game_state.paused:
            return

        # --- UPDATE JOGADOR ---
        keys = pg.get_keys()
        if game.player:
            game.player.handle_input(keys)
            game.player.update_animation(dt_ms_scaled)
            game.player.apply_gravity()
            game.handle_combat(dt_seconds)

        # --- UPDATE INIMIGOS ---
        if game.enemy_manager:
            game.enemy_manager.update(dt_seconds)
            game.enemies = game.enemy_manager.get_enemies()
            # projécteis de inimigos: a gestão passa a ser feita directamente
            # (ex: dentro de Enemy usando o ProjectileManager)

        # --- UPDATE BOSS ---
        game.update_boss(dt_seconds)

        # --- UPDATE PICKUPS ---
        if game.pickup_manager:
            player_rect = game.player.rect if game.player else None
            pickup_events = game.pickup_manager.update(
                dt_seconds,
                player_rect=player_rect,
            )
            for ev in pickup_events:
                game.apply_pickup_effect(ev.effect)

        # --- UPDATE PROJÉCTEIS ---
        if game.projectile_manager:
            game.projectile_manager.update(dt_seconds)

        # --- UPDATE GRANADAS ---
        game.update_granades(dt_ms_scaled)

        # --- COLISÕES ---
        game.handle_collisions()

        if not isinstance(game.current_scene, LevelScene):
            return
        
        # --- FIM DE NÍVEL (Lvl1 → Lvl2) ---
        # Só fazemos auto-transição quando estamos no 1.º nível
        # (debug_level_index == 0) e já não há inimigos vivos nem spawns.
        if (
            getattr(game, "debug_level_index", 0) == 0
            and game.enemy_manager is not None
        ):
            em = game.enemy_manager
            try:
                total_max = em.max_spawns
                total_spawned = em.total_spawned
                active_now = em.active_enemies_count
            except Exception:
                total_max = 0
                total_spawned = 0
                active_now = 0

            if total_max > 0:
                killed = max(0, total_spawned - active_now)
                kill_ratio = killed / float(total_max)

                enough_kills = kill_ratio >= 0.60
                no_active_enemies = active_now == 0

                if enough_kills and no_active_enemies:
                    # 1) ecrã de COMPLETE (com end.mp3)
                    # 2) loading com barra
                    # 3) arranca próximo nível
                    game.show_level_complete_screen()
                    game.go_to_next_level()
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

        # Cena normal
        game.draw_scene()
        game.draw_hud()

        # Overlay de flash / FX
        if game.effects:
            tint = game.effects.get_screen_tint()
            if tint is not None:
                color, intensity = tint
                if intensity > 0.0:
                    overlay = pg.create_surface(
                        (config.WIDTH, config.HEIGHT),
                        alpha=True,
                    )
                    alpha = int(max(0.0, min(1.0, intensity)) * 255)
                    overlay.fill((color[0], color[1], color[2], alpha))
                    screen.blit(overlay, (0, 0))


if __name__ == "__main__":
    Game().run()
