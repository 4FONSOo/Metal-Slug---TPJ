"""
Config geral do jogo.
Se isto estiver todo lixado, o resto vem por arrasto.
"""

import os
import pg_engine as pg

# -----------------------------
# TELA / JANELA
# -----------------------------
WIDTH = 800
HEIGHT = 600
WINDOW_TITLE = "Metal Slug 2D"
FPS = 60

# -----------------------------
# PATHS / PROJETO
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta base de assets (imagens, sons, etc.)
ASSETS_DIR = os.path.join(BASE_DIR, "..", "Assets")
ASSETS_DIR = os.path.abspath(ASSETS_DIR)

if not os.path.isdir(ASSETS_DIR):
    raise FileNotFoundError(f"Pasta de assets não encontrada: {ASSETS_DIR}")

# -----------------------------
# JOGADOR – GEOMETRIA E FÍSICA
# -----------------------------
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 80

PLAYER_SPEED = 5
PLAYER_JUMP_SPEED = -12          # valor base do salto
PLAYER_GRAVITY = 0.4

PLAYER_MAX_HP = 1000

# -----------------------------
# GAME STATE DEFAULTS
# -----------------------------
INITIAL_SCORE = 0
INITIAL_CREDITS = 5
INITIAL_TIME_LEFT = 10 #60           # segundos por nível
INITIAL_LEVEL_NAME = "Nível 1"

# Timer do HUD / relógio (1 segundo)
TIMER_EVENT_INDEX = 1            # usado como base para pg.USEREVENT
TIMER_INTERVAL_MS = 1000
TIMER_EVENT_ID = pg.USEREVENT + TIMER_EVENT_INDEX

# -----------------------------
# INPUT KEYS (CONTROLOS DEFAULT)
# -----------------------------
KEY_MENU = pg.K_ESCAPE   # sair para menu / back
KEY_PAUSE = pg.K_P       # pausar o jogo

KEY_FIRE = pg.K_SPACE    # disparar / melee

KEY_UP = pg.K_UP
KEY_DOWN = pg.K_DOWN
KEY_LEFT = pg.K_LEFT
KEY_RIGHT = pg.K_RIGHT
KEY_JUMP = pg.K_LALT     # reservado para salto separado se quiseres

# -----------------------------
# HUD / INTERFACE
# -----------------------------
HUD_FONT_NAME = "Arial"
HUD_FONT_SIZE = 24

HUD_TEXT_COLOR = (255, 255, 255)

HUD_PLAYER_HP_BAR_WIDTH = 200
HUD_PLAYER_HP_BAR_HEIGHT = 20
HUD_PLAYER_HP_BAR_POS = (20, 40)          # (x, y)
HUD_PLAYER_HP_BG_COLOR = (80, 80, 80)

HUD_PLAYER_HP_GREEN_THRESHOLD = 0.6
HUD_PLAYER_HP_YELLOW_THRESHOLD = 0.3

HUD_PLAYER_HP_COLOR_GREEN = (0, 255, 0)
HUD_PLAYER_HP_COLOR_YELLOW = (255, 255, 0)
HUD_PLAYER_HP_COLOR_RED = (255, 0, 0)

# -----------------------------
# FLOATING TEXT (PONTUAÇÃO, ETC.)
# -----------------------------
FLOATING_TEXT_FONT_NAME = "Arial"
FLOATING_TEXT_FONT_SIZE = 22

FLOATING_TEXT_COLOR_DEFAULT = (255, 255, 0)
FLOATING_TEXT_LIFETIME_FRAMES = 60
FLOATING_TEXT_RISE_SPEED = 1
FLOATING_TEXT_ALPHA_STEP = 4

# -----------------------------
# FX / FEEDBACK VISUAL
# -----------------------------
SCREEN_FLASH_DEFAULT_FRAMES = 5

CHEAT_FLASH_COLOR_GOD_ON = (255, 255, 0)
CHEAT_FLASH_COLOR_GOD_OFF = (255, 0, 0)

CHEAT_FLASH_COLOR_TIME_ON = (0, 200, 255)
CHEAT_FLASH_COLOR_TIME_OFF = (255, 120, 120)

CHEAT_FLASH_COLOR_SPJ_ON = (0, 255, 255)
CHEAT_FLASH_COLOR_SPJ_OFF = (255, 100, 100)

GAME_OVER_WAIT_MS = 2000

# -----------------------------
# COMBATE / MELEE / PROJÉTEIS
# -----------------------------
MELEE_WIDTH = 60
MELEE_HEIGHT = 20
MELEE_KILL_DAMAGE = 9999           # faca à Metal Slug

PLAYER_PROJECTILE_COLOR = (100, 200, 255)
PLAYER_PROJECTILE_SPEED = 12
PLAYER_PROJECTILE_OFFSET_X = 40
PLAYER_PROJECTILE_OFFSET_Y = 5
PLAYER_PROJECTILE_MAX_RANGE = 2000
PLAYER_FIRE_INTERVAL_MS = 120
PLAYER_AIM_LERP_FACTOR = 0.35

ENEMY_PROJECTILE_COLOR = (255, 50, 50)
ENEMY_PROJECTILE_SPEED = 12

ENEMY_CONTACT_PLAYER_FACTOR = 0.1
ENEMY_CONTACT_SELF_DAMAGE = 0.5

# -----------------------------
# INIMIGOS – PARÂMETROS GERAIS
# -----------------------------
ENEMY_GRAVITY = 1
ENEMY_JUMP_INTERVAL_DEFAULT = (500, 1000)
ENEMY_MAX_HP = 100

ENEMY_MANAGER_MAX_SPAWNS_DEFAULT = 50
ENEMY_MANAGER_MAX_ACTIVE_DEFAULT = 10
ENEMY_MANAGER_PATROL_MIN = 150
ENEMY_MANAGER_PATROL_MAX = 350
ENEMY_MANAGER_SPAWN_X_MARGIN = 100
ENEMY_MANAGER_SPAWN_Y_MIN = 50

# -----------------------------
# MENU / OPÇÕES
# -----------------------------
MENU_TITLE = "Metal Slug 2D"

MENU_FONT_NAME = "arial"
MENU_FONT_SIZE = 36

MENU_OPTIONS_FONT_NAME = "arial"
MENU_OPTIONS_FONT_SIZE = 30

MENU_VOLUME_HOLD_REPEAT_FRAMES = 3
MENU_VOLUME_STEP = 1

# -----------------------------
# CHEATS
# -----------------------------
CHEAT_CODES = ["GOD", "TIME", "SPJ"]

CHEAT_SUPER_JUMP_VALUE = -35
CHEAT_NORMAL_JUMP_VALUE = -12

# -----------------------------
# DIFICULDADE (PRESETS)
# -----------------------------
DIFFICULTY_PRESETS = {
    "Fácil": {
        "TIME_MULTIPLIER": 1.5,
        "PLAYER_HP_MULTIPLIER": 1.5,
        "ENEMY_DAMAGE_MULTIPLIER": 0.5,
        "ENEMY_MAX_ACTIVE": 5,
        "ENEMY_MAX_SPAWNS": 30,
    },
    "Normal": {
        "TIME_MULTIPLIER": 1.0,
        "PLAYER_HP_MULTIPLIER": 1.0,
        "ENEMY_DAMAGE_MULTIPLIER": 1.0,
        "ENEMY_MAX_ACTIVE": 10,
        "ENEMY_MAX_SPAWNS": 50,
    },
    "Difícil": {
        "TIME_MULTIPLIER": 0.8,
        "PLAYER_HP_MULTIPLIER": 0.8,
        "ENEMY_DAMAGE_MULTIPLIER": 1.5,
        "ENEMY_MAX_ACTIVE": 15,
        "ENEMY_MAX_SPAWNS": 80,
    },
}

DEFAULT_DIFFICULTY = "Normal"
