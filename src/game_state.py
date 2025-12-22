# game_state.py
"""
Cérebro principal do jogo:
- loop global
- estado (pontuação, tempo, dificuldade)
- gestão de cenas (menu, nível)
- cheats, HUD, etc.

Nota: aqui não se importa pygame directamente, só pg_engine.
"""

import random  # <- para o enemy_factory

import pg_engine as pg
from pg_engine import Vector2

import config
from config import DIFFICULTY_PRESETS, DEFAULT_DIFFICULTY, CHEAT_CODES

from scene import Scene

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
from managers.scene_manager import SceneManager

from entity.boss import Boss
from entity.player import Player
from entity.enemy import (
    Enemy,
    EnemySoldier,
    EnemyShooter,
    EnemyHeavy,
    EnemyFast,
)

from entity.projectile import Projectile
from entity.granade import Granade  # lógica da granada

try:
    from patterns.command import CommandInvoker  # type: ignore
    from managers.command_input_manager import CommandInputManager  # type: ignore
except Exception:
    CommandInvoker = None  # type: ignore
    CommandInputManager = None  # type: ignore

try:
    from patterns.observer import EventManager, ScoreObserver, SoundObserver  # type: ignore
except Exception:
    EventManager = None  # type: ignore
    ScoreObserver = None  # type: ignore
    SoundObserver = None  # type: ignore

# ----------------------------- #
# OPTIONAL SYSTEMS (merged from the "new" version)
#   - ObjectPool para reutilizar projécteis (performance)
#   - PrototypeFactory para dados de tipos de inimigo (sprite/HP/dano/pontos)
# Tudo é opcional: se estes módulos não existirem, há fallback seguro.
# ----------------------------- #

try:
    # Se existir no teu projecto, usa a implementação oficial
    from managers.object_pool import ObjectPool  # type: ignore
except Exception:
    class ObjectPool:
        """Pool simples (LIFO) para reutilizar objectos."""

        def __init__(self, cls, size: int = 100, factory=None, max_size: int | None = None):
            self._cls = cls
            self._factory = factory or cls
            self._pool = []
            self._max_size = int(max_size) if isinstance(max_size, int) else None
            try:
                for _ in range(max(0, int(size))):
                    self._pool.append(self._factory())
            except Exception:
                self._pool = []

        def acquire(self):
            try:
                return self._pool.pop()
            except Exception:
                return self._factory()

        def release(self, obj) -> None:
            if obj is None:
                return
            if self._max_size is not None and len(self._pool) >= self._max_size:
                return
            self._pool.append(obj)

try:
    from patterns.prototype import EnemyPrototype, get_global_prototype_factory  # type: ignore
except Exception:
    class EnemyPrototype:
        def __init__(self, key: str, sprite_path: str, hp: int = 0, damage: int = 0, points: int = 0):
            self.key = str(key)
            self.sprite_path = str(sprite_path)
            self.hp = int(hp)
            self.damage = int(damage)
            self.points = int(points)

        def create(self, x: int, y: int) -> dict:
            return {
                "key": self.key,
                "sprite_path": self.sprite_path,
                "hp": self.hp,
                "damage": self.damage,
                "points": self.points,
                "x": int(x),
                "y": int(y),
            }

    class _EnemyPrototypeFactory:
        def __init__(self):
            self._enemies: dict[str, EnemyPrototype] = {}

        def register_enemy(self, key: str, proto: EnemyPrototype) -> None:
            self._enemies[str(key)] = proto

        def create_enemy(self, key: str, x: int, y: int) -> dict | None:
            proto = self._enemies.get(str(key))
            return proto.create(x, y) if proto else None

    _GLOBAL_PROTO_FACTORY = _EnemyPrototypeFactory()

    def get_global_prototype_factory():
        return _GLOBAL_PROTO_FACTORY

from scenes.menu import Menu as MenuScene  # cena de menu principal
from scenes.level import LevelScene
from scenes.flow import NoMoreLevelsScene

from scenes.Lvl1 import load_level as load_level_1
from scenes.Lvl2 import load_level as load_level_2

LEVEL_LOADERS = [
    load_level_1,  # índice 0 → Lvl1
    load_level_2,  # índice 1 → Lvl2
]

from scenes.game_over import GameOverScene
import score


from sound import SoundManager

from resource import load_pickup_sprites, load_enemy

#from score import ScoreManager

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

        # --------------------------------------------------------------
        # Patterns (opcional, sem quebrar compatibilidade)
        # --------------------------------------------------------------

        # Command Pattern: input → commands (LevelScene já suporta)
        self.command_invoker = None
        self.command_input = None
        if CommandInvoker is not None and CommandInputManager is not None:
            try:
                self.command_invoker = CommandInvoker(history_limit=100)
                self.command_input = CommandInputManager()
            except Exception:
                self.command_invoker = None
                self.command_input = None

        # Estado publicado por Commands para o combate (fallback: teclado)
        self._command_fire_pressed = False
        self._command_grenade_pressed = False
        self._command_shoot_dir = (1, 0)

        # Observer Pattern: bus de eventos
        self.events = None
        if EventManager is not None:
            try:
                self.events = EventManager()
            except Exception:
                self.events = None

        try:
            from score import ScoreManager as _ScoreManager
            print("[SCORE] A usar ScoreManager de score.py")
        except Exception as e:
            print("[WARN] Falha a importar ScoreManager de score.py:", e)
            print("[WARN] A usar ScoreManager de fallback (com ficheiro scores.json).")

            import json
            import os

            SCORE_FILE = "scores.json"
            MAX_HIGH_SCORES = 7

            class _ScoreManager:
                def __init__(
                    self,
                    filename: str = SCORE_FILE,
                    max_scores: int = MAX_HIGH_SCORES,
                ):
                    self.filename = filename
                    self.max_scores = max_scores
                    self.current_score = 0
                    self.high_scores = []
                    self.load_scores()

                # -----------------------------
                # Score da run actual
                # -----------------------------
                def reset_current(self):
                    self.current_score = 0

                def add_points(self, pontos: int):
                    if pontos <= 0:
                        return
                    self.current_score += pontos

                # -----------------------------
                # Highscores (ficheiro)
                # -----------------------------
                def load_scores(self):
                    if not os.path.exists(self.filename):
                        self.high_scores = []
                        return

                    try:
                        with open(self.filename, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        if isinstance(data, list):
                            self.high_scores = []
                            for e in data:
                                try:
                                    name = str(e.get("name", "???")).strip().upper()[:12]
                                    score = int(e.get("score", 0))
                                    self.high_scores.append(
                                        {"name": name, "score": score}
                                    )
                                except Exception:
                                    continue

                            self.high_scores.sort(
                                key=lambda e: e["score"], reverse=True
                            )
                            self.high_scores = self.high_scores[: self.max_scores]
                        else:
                            self.high_scores = []
                    except Exception as e2:
                        print(
                            f"[SCORE] Ficheiro de scores marado, vou limpar. Erro: {e2}"
                        )
                        self.high_scores = []

                def save_scores(self):
                    try:
                        with open(self.filename, "w", encoding="utf-8") as f:
                            json.dump(self.high_scores, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"[SCORE] Não consegui gravar scores: {e}")

                # -----------------------------
                # Lógica de highscore
                # -----------------------------
                def qualifies_for_highscore(self) -> bool:
                    if self.current_score <= 0:
                        return False

                    if len(self.high_scores) < self.max_scores:
                        return True

                    return self.current_score > self.high_scores[-1]["score"]

                def register_current_score(self, name: str):
                    name = (name or "???").strip().upper()[:12]
                    entry = {"name": name, "score": self.current_score}
                    self.high_scores.append(entry)
                    self.high_scores.sort(
                        key=lambda e: e["score"], reverse=True
                    )
                    self.high_scores = self.high_scores[: self.max_scores]
                    self.save_scores()

                def get_high_scores(self):
                    return list(self.high_scores)

        self.score_manager = _ScoreManager()

        # Sprites dos pickups (health, granadas, etc.)
        try:
            self.pickup_sprites = load_pickup_sprites()
        except Exception as e:
            print(f"[WARN] Falha a carregar sprites de pickups: {e}")
            self.pickup_sprites = {}

        # Sistema de scores (pontuação actual + highscores)
        # 
        self.score_manager = score.ScoreManager()

        # Subscrever observers (sem alterar a lógica de jogo)
        if self.events is not None:
            try:
                if ScoreObserver is not None:
                    so = ScoreObserver(self)
                    self.events.subscribe("enemy_dead", so.on_event)
                    self.events.subscribe("pickup_collected", so.on_event)
                if SoundObserver is not None:
                    snd = SoundObserver(self.sound)
                    self.events.subscribe("enemy_dead", snd.on_event)
                    self.events.subscribe("shoot", snd.on_event)
                    self.events.subscribe("grenade_throw", snd.on_event)
                    self.events.subscribe("grenade_explode", snd.on_event)
            except Exception:
                pass

        # Gestor de cenas
        self.scene_manager = SceneManager(self)
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
    # SCENES / SCENE MANAGER
    # ----------------------------- #
    @property
    def current_scene(self) -> Scene | None:
        """Compat: devolve a cena actual a partir do SceneManager."""
        return self.scene_manager.current_scene

    @current_scene.setter
    def current_scene(self, value: Scene | None) -> None:
        """Compat: permite atribuir current_scene, delegando no SceneManager."""
        self.scene_manager.current_scene = value    

    # ----------------------------- #
    # GESTÃO DE CENAS
    # ----------------------------- #
    def change_scene(self, new_scene: Scene):
        """Troca de cena de forma civilizada via SceneManager."""
        self.scene_manager.change_scene(new_scene)

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
    # VERIFICAR SE CONDIÇÃO DE X% É CUMPRIDA
    # ----------------------------- #

    def get_enemy_kill_stats(self):
        """
        Devolve estatísticas dos inimigos deste nível:

          killed: nº de inimigos mortos
          total_max: nº total de spawns possíveis
          kill_ratio: killed / total_max (0.0–1.0)
          active_now: nº de inimigos actualmente vivos
        """
        em = self.enemy_manager
        if em is None:
            return 0, 0, 0.0, 0

        try:
            total_max = int(getattr(em, "max_spawns", 0))
            total_spawned = int(getattr(em, "total_spawned", 0))
            active_now = int(getattr(em, "active_enemies_count", 0))
        except Exception:
            return 0, 0, 0.0, 0

        total_max = max(0, total_max)
        total_spawned = max(0, total_spawned)
        active_now = max(0, active_now)

        # Preferir contador real (se existir); fallback para estimativa via EnemyManager.
        killed = int(getattr(self, "level_enemy_kills", 0) or 0)
        if killed <= 0:
            killed = max(0, min(total_spawned, total_max) - active_now)

        kill_ratio = (killed / float(total_max)) if total_max > 0 else 0.0

        return killed, total_max, kill_ratio, active_now

    def has_enough_kills_for_current_level(self) -> bool:
        """
        Verifica se já cumprimos o requisito mínimo de kills
        para desbloquear o próximo nível.

        Neste momento só aplicamos isto no NÍVEL 1.
        """
        level_id = getattr(self, "current_level_id", 1)

        # Só nível 1 tem este requisito especial
        if level_id != 1:
            return True

        killed, total_max, kill_ratio, active_now = self.get_enemy_kill_stats()
        required_ratio = float(getattr(config, "LEVEL1_REQUIRED_KILL_RATIO", 0.60))

        if total_max <= 0:
            # Se não houver inimigos configurados, por segurança dizemos que não passou
            return False

        return kill_ratio >= required_ratio






    # ----------------------------- #
    # KILL COUNTER (novo)
    # ----------------------------- #
    def register_enemy_kill(self, enemy) -> None:
        """Marca um inimigo como contado e incrementa o contador do nível.

        Isto evita contagens duplicadas quando:
          - o mesmo inimigo é atingido por vários projécteis no mesmo frame
          - há AOE (granada) + projéctil
        """
        if enemy is None:
            return

        # Evitar double-count
        if getattr(enemy, "_kill_counted", False):
            return

        setattr(enemy, "_kill_counted", True)

        try:
            self.level_enemy_kills = int(getattr(self, "level_enemy_kills", 0)) + 1
        except Exception:
            self.level_enemy_kills = 1

    def get_kill_stats(self):
        """Alias compatível com o 'novo': devolve (killed, total_max, ratio, active_now)."""
        return self.get_enemy_kill_stats()
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


    # ----------------------------- #
    # BOSS
    # ----------------------------- #
    def _load_boss_sprite(self):
        """(novo) Carrega sprite do boss com fallback para vários nomes."""
        candidates = [
            getattr(config, "BOSS_SPRITE_NAME", "boss.png"),
            "boss.png",
            "Boss.png",
            "BossHeli.png",
            "boss_heli.png",
            "boss_helicopter.png",
        ]

        w = getattr(config, "BOSS_WIDTH", 160)
        h = getattr(config, "BOSS_HEIGHT", 120)

        for name in candidates:
            try:
                return load_enemy(w, h, name)
            except Exception:
                continue

        # Último fallback: tentar sempre boss.png
        try:
            return load_enemy(w, h, "boss.png")
        except Exception:
            return None

    def _handle_boss_defeated(self) -> None:
        """(novo) Só corre 1x quando o boss morre."""
        if getattr(self, "_boss_defeated_handled", False):
            return
        self._boss_defeated_handled = True

        # Opcional: som / pontos extra
        try:
            self.sound.play_sfx("boss_dead.mp3")
        except Exception:
            pass

        # Tenta LevelCompleteScene se existir; senão avança para o próximo nível
        try:
            from scenes.flow import LevelCompleteScene  # type: ignore
        except Exception:
            LevelCompleteScene = None

        if LevelCompleteScene is not None:
            self.change_scene(LevelCompleteScene(self))
        else:
            # fallback: avança directamente
            self.go_to_next_level()

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

        # Sprite do boss (novo: tenta vários nomes)
        img = self._load_boss_sprite()
        if img is None:
            return

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
        if not boss:
            return

        if not getattr(boss, "alive", False):
            self._handle_boss_defeated()

            self.has_boss = False
            self.boss = None
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
                # No menu: roda o nível inicial. In-game: usa como "skip" para o próximo nível.
                if not isinstance(self.current_scene, MenuScene):
                    try:
                        self.go_to_next_level()
                    except Exception:
                        pass
                    continue

                # Nº máximo de níveis de debug (ajusta aqui se adicionares mais)
                max_levels = getattr(config, "DEBUG_MAX_LEVELS", 2)

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
                    # Já não há mais níveis → cena “CHEATER, no more levels”
                    self.change_scene(NoMoreLevelsScene(self))

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

        # Contadores/flags por nível (novo)
        self.level_enemy_kills = 0
        self._boss_defeated_handled = False

        # Pool opcional de projécteis (novo)
        self.projectile_pool = None

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
        """
        Transição para a cena de Game Over.

        - Sincroniza a pontuação actual com o ScoreManager
        - Delega toda a lógica de pedir nome / mostrar tabela de highscores
          na GameOverScene.
        """
        # Sincronizar a pontuação actual (caso ainda não esteja)
        if self.game_state is not None:
            self.score_manager.current_score = self.game_state.score

        # Parar a música actual
        try:
            self.sound.stop_music()
        except Exception:
            pass

        # Tocar som de game over (se existir)
        try:
            self.sound.play_game_over_sfx()
        except Exception:
            pass

        # Ir para a cena de Game Over (não bloqueante)
        self.change_scene(GameOverScene(self))
        

    def go_to_next_level(self) -> None:
        """
        Transição automática para o nível seguinte (usado no fim do Lvl1).

        Mantém pontuação e estado básico do jogador (HP / granadas).
        Não mostra ecrãs – isso é tratado pelas Scenes (LevelCompleteScene/LoadingScene).
        """
        # Índice actual / próximo (debug_level_index 0→1, etc.)
        max_index = max(0, len(LEVEL_LOADERS) - 1)
        current_idx = max(0, min(self.debug_level_index, max_index))
        next_idx = current_idx + 1

        if next_idx > max_index:
            # Sem mais níveis definidos → cena "no more levels"
            self.change_scene(NoMoreLevelsScene(self))
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

    def start_game(self, level_id: int | None = None, preserve_progress: bool = False):
        """
        Arranca um novo jogo:
          - faz reset de estado
          - carrega o nível
          - cria player e inimigos
          - muda para a cena de jogo (LevelScene)
        """
        # (novo) Opcional: pedir para arrancar directamente num level_id (compatível com o sistema antigo)
        if level_id is not None:
            try:
                level_id = int(level_id)
            except Exception:
                level_id = None

            # Mapeamento simples: Lvl1→index0, Lvl2→index1 (ajusta se adicionares mais níveis)
            if level_id == 2:
                self.debug_level_index = 1
            elif level_id == 1:
                self.debug_level_index = 0

        # (novo) Guardar progresso se quisermos preservar entre níveis (score, upgrades, granadas)
        prev_score = getattr(self.game_state, "score", 0) if getattr(self, "game_state", None) else 0
        prev_sm_score = getattr(self.score_manager, "current_score", 0) if getattr(self, "score_manager", None) else 0
        prev_weapon_stacks = int(getattr(self, "weapon_upgrade_stacks", 0) or 0)
        prev_fire_mult = float(getattr(self, "weapon_fire_rate_multiplier", 1.0) or 1.0)
        prev_dmg_mult = float(getattr(self, "weapon_damage_multiplier", 1.0) or 1.0)
        prev_player_hp = getattr(getattr(self, "player", None), "hp", None)
        prev_player_grenades = getattr(getattr(self, "player", None), "granades", None)
        prev_cm_grenades = getattr(getattr(self, "combat_manager", None), "grenades", None)

        self.reset_all_state()

        # Restaurar progresso (se pedido)
        if preserve_progress:
            try:
                self.weapon_upgrade_stacks = prev_weapon_stacks
                self.weapon_fire_rate_multiplier = prev_fire_mult
                self.weapon_damage_multiplier = prev_dmg_mult
            except Exception:
                pass

            if self.game_state is not None:
                self.game_state.score = prev_score
            if self.score_manager is not None:
                self.score_manager.current_score = prev_sm_score

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

        # (novo) Pool opcional de projécteis do jogador
        self.projectile_pool = None
        try:
            pool_size = int(getattr(config, "PROJECTILE_POOL_SIZE", 250))
            # Criamos instâncias "vazias" com valores dummy e depois fazemos reset no disparo.
            self.projectile_pool = ObjectPool(
                Projectile,
                size=pool_size,
                factory=lambda: Projectile(
                    0,
                    0,
                    1,
                    0,
                    max_range=1,
                    color=getattr(config, "PLAYER_PROJECTILE_COLOR", (255, 255, 0)),
                ),
                max_size=pool_size,
            )
        except Exception:
            self.projectile_pool = None

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

        # (novo) Restaurar estado básico do jogador (HP/granadas) se preserve_progress
        if preserve_progress and self.player:
            if prev_player_hp is not None:
                try:
                    self.player.hp = max(0, min(int(prev_player_hp), int(getattr(self.player, "max_hp", prev_player_hp))))
                except Exception:
                    self.player.hp = prev_player_hp

            if prev_player_grenades is not None:
                try:
                    self.player.granades = max(0, int(prev_player_grenades))
                except Exception:
                    pass

            if self.combat_manager and prev_cm_grenades not in (None, float("inf")):
                try:
                    self.combat_manager.set_grenades(int(prev_cm_grenades))
                except Exception:
                    pass

        # Inimigos – EnemyManager genérico + fábrica de inimigos concretos
        max_spawns, max_active, damage_mult = self._get_enemy_params_for_difficulty()

        # (novo) PrototypeFactory: regista stats/sprites por tipo (se existir no projecto)
        proto_factory = None
        try:
            proto_factory = get_global_prototype_factory()

            # Registos default (ajusta sprites se quiseres)
            proto_factory.register_enemy(
                "soldier",
                EnemyPrototype("soldier", "Rebel1.png", hp=getattr(config, "ENEMY_SOLDIER_HP", 1), damage=1, points=100),
            )
            proto_factory.register_enemy(
                "shooter",
                EnemyPrototype("shooter", "Rebel2.png", hp=getattr(config, "ENEMY_SHOOTER_HP", 1), damage=1, points=120),
            )
            proto_factory.register_enemy(
                "heavy",
                EnemyPrototype("heavy", "Rebel3.png", hp=getattr(config, "ENEMY_HEAVY_HP", 2), damage=2, points=200),
            )
            proto_factory.register_enemy(
                "fast",
                EnemyPrototype("fast", "Rebel4.png", hp=getattr(config, "ENEMY_FAST_HP", 1), damage=1, points=130),
            )
        except Exception:
            proto_factory = None

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
                enemy_key = "heavy"
                cls, sprite = EnemyHeavy, "Rebel3.png"
            elif p < shooter_thr:
                enemy_key = "shooter"
                cls, sprite = EnemyShooter, "Rebel2.png"
            else:
                enemy_key, cls, sprite = random.choice(
                    [
                        ("soldier", EnemySoldier, "Rebel1.png"),
                        ("fast", EnemyFast, "Rebel4.png"),
                    ]
                )

            # (novo) Se houver PrototypeFactory, pode sobrepor o sprite (e outros stats no futuro)
            if proto_factory:
                try:
                    proto = proto_factory.create_enemy(enemy_key, int(spawn_x), 0) or {}
                    sprite = proto.get("sprite_path", sprite)
                except Exception:
                    pass
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

            boss = getattr(self, "boss", None)

            for enemy in self.enemies:
                if not getattr(enemy, "alive", False):
                    continue

                # Boss é imune à nuke
                if boss is not None and enemy is boss:
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

        #alvo.take_damage(config.MELEE_KILL_DAMAGE)

        if not alvo:
            return False

        # Som da faca
        try:
            self.sound.play_melee()
        except Exception:
            pass



        # Dano especial no boss: não queremos que a faça o one-shot. Mas esta merda ainda é insta-kill.... why????
        
        boss = getattr(self, "boss", None)

        if boss is not None and alvo is boss:
                base_hp = getattr(boss, "max_hp", None) or getattr(boss, "hp", 1000) or 1000
                melee_damage = getattr(config, "BOSS_MELEE_DAMAGE", max(1, int(base_hp * 0.01)))  # 1% por facada
        else:
            melee_damage = config.MELEE_KILL_DAMAGE

            alvo.take_damage(melee_damage)

        if not getattr(alvo, "alive", False):
            self.register_enemy_kill(alvo)
            points = getattr(alvo, "points", 100)
            x = alvo.rect.centerx
            y = alvo.rect.top

            if getattr(self, "events", None) is not None:
                try:
                    self.events.emit("enemy_dead", {"enemy": alvo, "points": points, "x": x, "y": y})
                except Exception:
                    self.add_score(points, x, y)
                    try:
                        self.sound.play_enemy_death()
                    except Exception:
                        pass
            else:
                self.add_score(points, x, y)
                try:
                    self.sound.play_enemy_death()
                except Exception:
                    pass

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

        # ------------------------------------------
        # Projécteis do player em inimigos
        # ------------------------------------------
        boss = getattr(self, "boss", None)
        processed_projectiles = set()

        for hit in result.enemy_hits:
            proj = hit.projectile
            enemy = hit.enemy

            # Já tratámos este projéctil num hit anterior
            if proj in processed_projectiles:
                continue

            if not getattr(enemy, "alive", False):
                continue

            damage = getattr(proj, "damage", 0)
            base_damage = getattr(proj, "base_damage", None)

            # No boss, ignorar o multiplicador da arma melhorada
            if boss is not None and enemy is boss and base_damage is not None:
                damage = base_damage

            was_alive = getattr(enemy, "alive", True)
            before_hp = getattr(enemy, "hp", None)

            try:
                enemy.take_damage(damage)
            except Exception:
                processed_projectiles.add(proj)
                continue

            now_alive = getattr(enemy, "alive", True)
            after_hp = getattr(enemy, "hp", None)

            just_died = (was_alive and not now_alive)
            if not just_died and before_hp is not None and after_hp is not None:
                if before_hp > 0 and after_hp <= 0:
                    just_died = True

            if just_died:
                self.register_enemy_kill(enemy)
                points = getattr(enemy, "points", 100)
                x = enemy.rect.centerx
                y = enemy.rect.top
                if getattr(self, "events", None) is not None:
                    try:
                        self.events.emit("enemy_dead", {"enemy": enemy, "points": points, "x": x, "y": y})
                    except Exception:
                        self.add_score(points, x, y)
                        try:
                            self.sound.play_enemy_death()
                        except Exception:
                            pass
                else:
                    self.add_score(points, x, y)
                    try:
                        self.sound.play_enemy_death()
                    except Exception:
                        pass

            # Projéctil morre ao primeiro impacto
            if hasattr(proj, "alive"):
                proj.alive = False
            if hasattr(proj, "trigger_hit"):
                try:
                    proj.trigger_hit()
                except Exception:
                    pass

            processed_projectiles.add(proj)

        # ------------------------------------------
        # Projécteis de inimigos em player
        # ------------------------------------------
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

        # ------------------------------------------
        # Contacto físico player <-> inimigos

        if self.player and not self.god_mode:
            for contact in result.contact_hits:
                enemy = contact.enemy
                if not getattr(enemy, "alive", False):
                    continue

                try:
                    # Player leva dano de contacto
                    self.player.take_damage(enemy.contact_damage_to_player())

                    # Inimigo também pode levar dano ao tocar no player
                    was_alive = getattr(enemy, "alive", False)
                    enemy.take_damage(enemy.contact_self_damage())
                except Exception:
                    continue

                # Se o contacto matou o inimigo, dar pontos + som tal como nos projécteis
                if was_alive and not getattr(enemy, "alive", False):
                    points = getattr(enemy, "points", 100)
                    x = enemy.rect.centerx
                    y = enemy.rect.top
                    if getattr(self, "events", None) is not None:
                        try:
                            self.events.emit("enemy_dead", {"enemy": enemy, "points": points, "x": x, "y": y})
                        except Exception:
                            self.add_score(points, x, y)
                            try:
                                self.sound.play_enemy_death()
                            except Exception:
                                pass
                    else:
                        self.add_score(points, x, y)
                        try:
                            self.sound.play_enemy_death()
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


    def handle_combat(self, dt_seconds: float, keys=None, **_ignored_kwargs) -> None:
        """
        Processa input de combate (tiro, melee, granada) via CombatManager.
        """
        if not self.player or not self.combat_manager:
            return

        # Input (preferir estado publicado via Command Pattern; fallback: teclado)
        keys = keys if keys is not None else pg.get_keys()

        use_command_state = False
        try:
            fire_pressed = bool(getattr(self, "_command_fire_pressed"))
            secondary_pressed = bool(getattr(self, "_command_grenade_pressed"))
            raw_dx, raw_dy = getattr(self, "_command_shoot_dir")
            raw_dx, raw_dy = int(raw_dx), int(raw_dy)
            use_command_state = True
        except Exception:
            use_command_state = False

        if not use_command_state:
            fire_pressed = is_fire_pressed(keys)
            secondary_pressed = is_granade_pressed(keys)
            raw_dx, raw_dy = get_shoot_direction(
                keys,
                facing=self.player.facing,
                allow_diagonals=True,
            )

        fire_just_pressed = fire_pressed and not self.shoot_pressed
        secondary_just_pressed = secondary_pressed and not self.granade_pressed

        # Guardar estado para próximo frame
        self.shoot_pressed = fire_pressed
        self.granade_pressed = secondary_pressed

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

                    # (novo) Tentar reutilizar projéctil do pool (se existir)
                    proj = None
                    if getattr(self, "projectile_pool", None) is not None:
                        try:
                            proj = self.projectile_pool.acquire()
                            if hasattr(proj, "reset"):
                                # reset() deve espelhar os argumentos do construtor
                                proj.reset(
                                    x=sx,
                                    y=sy,
                                    dir_x=aim.x,
                                    dir_y=aim.y,
                                    max_range=self.bg_width,
                                    color=projectile_color,
                                )
                            else:
                                proj = None
                        except Exception:
                            proj = None

                    if proj is None:
                        proj = Projectile(
                            sx,
                            sy,
                            aim.x,
                            aim.y,
                            max_range=self.bg_width,
                            color=projectile_color,
                        )

                    spawn_left = self.POV
                    spawn_right = self.POV + config.WIDTH
                    setattr(proj, "spawn_view_left", spawn_left)
                    setattr(proj, "spawn_view_right", spawn_right)

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

                # Som do tiro via Observer (fallback: directo)
                if getattr(self, "events", None) is not None:
                    try:
                        self.events.emit("shoot", {"upgraded": upgraded_shot})
                    except Exception:
                        try:
                            if upgraded_shot:
                                self.sound.play_sfx("tiro2.mp3")
                            else:
                                self.sound.play_sfx("tiro1.mp3")
                        except Exception:
                            pass
                else:
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

                if getattr(self, "events", None) is not None:
                    try:
                        self.events.emit("grenade_throw", {})
                    except Exception:
                        pass

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

            owner = getattr(g, "owner", "player")

            # 1) Enquanto está a voar
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

                if owner == "player":
                    # -----------------------------
                    # GRANADA DO JOGADOR
                    # -----------------------------
                    # Comportamento antigo: explode se bater em inimigos
                    for enemy in self.enemies:
                        if not getattr(enemy, "alive", False):
                            continue
                        if enemy.rect.colliderect(grenade_rect):
                            g.explode()
                            break
                else:
                    # -----------------------------
                    # GRANADA DO BOSS / INIMIGOS
                    # -----------------------------
                    # NÃO usa colisão com TMX aqui.
                    # Só explode se acertar directamente no player;
                    # o "bater no chão" fica a cargo da física da própria Granade.
                    if self.player and not self.god_mode:
                        if self.player.rect.colliderect(grenade_rect):
                            g.explode()

            # 2) Explosão: aplica dano em área uma única vez
            if g.is_exploding() and not g.damage_applied:
                if getattr(self, "events", None) is not None:
                    try:
                        self.events.emit("grenade_explode", {})
                    except Exception:
                        try:
                            self.sound.play_grenade_explosion()
                        except Exception:
                            pass
                else:
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

        - Se for do jogador → afecta inimigos (inclui boss).
        - Se for do boss/inimigos → afecta o jogador.
        """
        gx, gy = granade.get_center()
        r = granade.explosion_radius
        r2 = r * r

        owner = getattr(granade, "owner", "player")

        if owner == "player":
            # -----------------------------
            # AOE DO JOGADOR → INIMIGOS
            # -----------------------------
            for enemy in self.enemies:
                if not getattr(enemy, "alive", False):
                    continue

                ex, ey = enemy.rect.center
                dx = ex - gx
                dy = ey - gy

                if dx * dx + dy * dy <= r2:
                    enemy.take_damage(granade.damage)
                    if not enemy.alive:
                        self.register_enemy_kill(enemy)
                        points = getattr(enemy, "points", 100)
                        self.add_score(points, enemy.rect.centerx, enemy.rect.top)
                        self.sound.play_enemy_death()
        else:
            # -----------------------------
            # AOE DO BOSS → PLAYER
            # -----------------------------
            if self.player and not self.god_mode:
                px, py = self.player.rect.center
                dx = px - gx
                dy = py - gy

                if dx * dx + dy * dy <= r2:
                    self.player.take_damage(granade.damage)

    #
    #   Limitar os projecteis para fora do ecrâ (é estúpido matar sem ver o que estou a fazer!!!!)
    #

    def cull_offscreen_projectiles(self) -> None:
        """
        Desactiva/remover projécteis do JOGADOR que já saíram da área visível.

        Regra:
          - Se o rect da bala ficar totalmente:
              * à esquerda de POV
              * ou à direita de POV + WIDTH
            → marcamos como morto e removemos da lista.

        Isto é independente de onde a câmara estava quando disparaste:
        só interessa onde está AGORA.
        """
        if not self.projectiles:
            return

        # Janela visível em coordenadas do mundo
        left_limit = self.POV
        right_limit = self.POV + config.WIDTH

        for proj in list(self.projectiles):
            if proj is None:
                continue

            rect = getattr(proj, "rect", None)
            if rect is None:
                continue

            # (novo) Limpar se morto OU totalmente fora da área visível
            offscreen = rect.right < left_limit or rect.left > right_limit
            dead = not getattr(proj, "alive", True)

            if dead or offscreen:
                if hasattr(proj, "alive"):
                    proj.alive = False
                try:
                    self.projectiles.remove(proj)
                except ValueError:
                    pass

                # Se vier de um pool, devolvemos para reutilizar
                if getattr(self, "projectile_pool", None) is not None:
                    try:
                        self.projectile_pool.release(proj)
                    except Exception:
                        pass


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

        # POV efectivo (já com tremor)
        camera_x = self.POV - shake_x

        # Background
        if self.background:
            # lembrar: background é desenhado com -POV
            self.screen.blit(self.background, (-camera_x, 0))

        # Pickups
        if self.pickup_manager:
            for p in self.pickup_manager.get_pickups():
                data = p.get_draw_data()
                if not data:
                    continue

                x = int(data.get("x", 0) - camera_x)
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
                    enemy.draw(self.screen, camera_x)
                    continue
                except Exception:
                    pass

            img = getattr(enemy, "image", None)
            rect = getattr(enemy, "rect", None)
            if img is not None and rect is not None:
                self.screen.blit(img, (rect.x - camera_x, rect.y))
        # Boss (sprite única, se existir e estiver vivo)
        boss = getattr(self, "boss", None)
        if boss and getattr(boss, "alive", False):
            img = getattr(boss, "image", None)
            rect = getattr(boss, "rect", None)
            if img is not None and rect is not None:
                if hasattr(boss, "draw"):
                    try:
                        boss.draw(self.screen, camera_x)
                    except Exception:
                        self.screen.blit(img, (rect.x - camera_x, rect.y))
                else:
                    self.screen.blit(img, (rect.x - camera_x, rect.y))

        # Jogador
        if self.player:
            self.screen.blit(
                self.player.image,
                (self.player.rect.x - camera_x, self.player.rect.y),
            )

        # Projécteis
        for proj in self.projectiles + self.enemy_projectiles:
            if proj:
                proj.draw(self.screen, camera_x)

        # Granadas
        for g in self.granades:
            data = g.get_draw_data()
            if not data:
                continue

            x = int(data["x"] - camera_x)
            y = int(data["y"])
            radius = int(data["radius"])

            color = (255, 80, 80) if data["exploding"] else (255, 0, 0)
            pg.draw_circle(self.screen, color, (x, y), radius)

        # Floating texts
        for text in self.floating_texts:
            text.draw(self.screen, camera_x)


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

        draw_text_with_outline(
            self.screen,
            top_text,
            self.font,
            20,
            10,
            config.HUD_TEXT_COLOR,
        )

        # --------- Contador de kills (apenas nível 1) ---------
        level_id = getattr(self, "current_level_id", 1)
        if level_id == 1 and self.enemy_manager is not None:
            killed, total_max, kill_ratio, active_now = self.get_enemy_kill_stats()

            if total_max > 0:
                required_ratio = float(
                    getattr(config, "LEVEL1_REQUIRED_KILL_RATIO", 0.60)
                )

                # nº mínimo de inimigos que tens MESMO de matar.
                # ex.: total=50, ratio=0.6 → 30
                # ex.: total=7,  ratio=0.6 → ceil(4.2)=5
                required_kills = max(
                    1,
                        int(total_max * required_ratio + 0.9999),
                )

                # Texto no formato "Kills: 10/30"
                kills_text = f"Kills: {killed}/{required_kills}"

                # Cor baseada na progressão:
                #   <50% do alvo  → vermelho
                #   entre 50–99%  → amarelo
                #   >= alvo       → verde
                progress = killed / float(required_kills)

                if killed >= required_kills:
                    color = getattr(
                        config,
                        "HUD_KILL_COLOR_GREEN",
                        (0, 255, 0),
                    )
                elif progress >= 0.5:
                    color = getattr(
                        config,
                        "HUD_KILL_COLOR_YELLOW",
                        (255, 255, 0),
                    )
                else:
                    color = getattr(
                        config,
                        "HUD_KILL_COLOR_RED",
                        (255, 80, 80),
                    )

                # Canto superior direito (ajusta X se quiseres mais à esquerda)
                x = config.WIDTH - 200
                y = 10
                draw_text_with_outline(
                    self.screen,
                    kills_text,
                    self.font,
                    x,
                    y,
                    color,
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

            # Se por algum motivo ainda não houver cena, vai para o Menu
            if not self.scene_manager.current_scene:
                self.change_scene(MenuScene(self))

            # Encaminhar para a cena activa
            self.scene_manager.handle_input(events)
            self.scene_manager.update(dt)
            self.scene_manager.draw(self.screen)

            pg.display_flip()
            self.clock.tick(config.FPS)

if __name__ == "__main__":
    Game().run()
