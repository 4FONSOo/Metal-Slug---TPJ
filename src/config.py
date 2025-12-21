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

PLAYER_START_GRANADES = 3        # granadas


# -----------------------------
# GAME STATE DEFAULTS
# -----------------------------
INITIAL_SCORE = 0
INITIAL_CREDITS = 5
INITIAL_TIME_LEFT = 60           # segundos por nível
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
KEY_SEC_FIRE = pg.K_LCTRL

KEY_UP = pg.K_UP
KEY_DOWN = pg.K_DOWN
KEY_LEFT = pg.K_LEFT
KEY_RIGHT = pg.K_RIGHT
KEY_JUMP = pg.K_LALT     

# -----------------------------
# HUD / INTERFACE
# -----------------------------
HUD_FONT_NAME = "Arial"
HUD_FONT_SIZE = 24

HUD_TEXT_COLOR = (255, 255, 255)

HUD_PLAYER_HP_BAR_WIDTH = 200
HUD_PLAYER_HP_BAR_HEIGHT = 20
HUD_PLAYER_HP_BAR_POS = (20, 40)
HUD_PLAYER_HP_BG_COLOR = (80, 80, 80)

HUD_PLAYER_HP_GREEN_THRESHOLD = 0.6
HUD_PLAYER_HP_YELLOW_THRESHOLD = 0.3

HUD_PLAYER_HP_COLOR_GREEN = (0, 255, 0)
HUD_PLAYER_HP_COLOR_YELLOW = (255, 255, 0)
HUD_PLAYER_HP_COLOR_RED = (255, 0, 0)

HUD_KILL_COLOR_RED = (255, 80, 80)
HUD_KILL_COLOR_YELLOW = (255, 255, 0)
HUD_KILL_COLOR_GREEN = (0, 255, 0)

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

CHEAT_FLASH_COLOR_GRN_ON = (255,0,0)
CHEAT_FLASH_COLOR_GRN_OFF = (125,125,125)

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

LEVEL1_REQUIRED_KILL_RATIO = 0.60 #percentagem 100% -> 1

# -----------------------------
# BOSS / LUTA FINAL
# -----------------------------

# Sprite / posição base
BOSS_WIDTH = 160              # largura do sprite do boss
BOSS_HEIGHT = 120             # altura do sprite do boss
BOSS_TARGET_Y_RATIO = 0.15    # % da altura do ecrã onde ele fica a pairar (0.15 = 15%)

# Vida / pontuação
BOSS_MAX_HP = 10000           # vida máxima do boss
BOSS_POINTS = 15000           # pontos ganhos ao matar o boss

# Movimento vertical (hover) e entrada
BOSS_HOVER_AMPLITUDE = 60     # quantos pixels sobe/desce a “abanar”
BOSS_HOVER_AMPLITUDE = 150    # distância do chão  
BOSS_HOVER_SPEED = 1.2        # velocidade do abanão
BOSS_ENTRY_SPEED = 180.0      # velocidade a que desce quando entra

# Delay / FX da entrada
BOSS_ENTRY_DELAY = 5.0        
BOSS_ENTRY_SHAKE_DURATION = 0.15
BOSS_ENTRY_SHAKE_INTENSITY = 6.0

# Ataques (tiros)
BOSS_DAMAGE_MULTIPLIER = 1.5      # multiplicador de dano dos projécteis do boss
BOSS_SHOT_INTERVAL_MIN = 0.3      # intervalo mínimo entre ataques (segundos)
BOSS_SHOT_INTERVAL_MAX = 0.8      # intervalo máximo entre ataques (segundos)
BOSS_GRENADE_MIN_COUNT = 5
BOSS_GRENADE_MAX_COUNT = 14
BOSS_GRENADE_SPACING = 60
BOSS_GRENADE_DAMAGE_MULTIPLIER = 2.0

# Música do boss
BOSS_MUSIC_FILE = "bosstheme.mp3"

# Contacto físico
ENEMY_CONTACT_DAMAGE_TO_PLAYER = 10   # dano base por contacto
BOSS_CONTACT_SELF_DAMAGE = 0          # quanto dano o boss leva ao tocar no player

# Movimento lateral (dash)
BOSS_LATERAL_SPEED = 420.0          # quanto maior, mais violento o dash
BOSS_LATERAL_DISTANCE = 260.0       # píxeis percorridos por dash
BOSS_LATERAL_COOLDOWN_MIN = 1.5     # segundos
BOSS_LATERAL_COOLDOWN_MAX = 3.0     # segundos
BOSS_LATERAL_MARGIN = 40            # margem aos lados do nível

# GRANADAS DO BOSS
BOSS_GRENADE_COUNT = 2              # nº de granadas por lado em cada ataque
BOSS_GRENADE_SPACING = 40           # espaçamento horizontal entre granadas

BOSS_MELEE_DAMAGE = 1               # evitar one-shot kill no boss

# HUD da barra de vida do boss
HUD_BOSS_HP_BAR_WIDTH = 300
HUD_BOSS_HP_BAR_HEIGHT = 16
HUD_BOSS_HP_BAR_Y = 40
HUD_BOSS_HP_BG_COLOR = (40, 0, 0)
HUD_BOSS_HP_COLOR = (220, 40, 40)

# FX do NUKE
NUKE_TOTAL_DURATION = 0.8
NUKE_FLASH_COLOR = (255, 255, 255)
NUKE_SLOWMO_FACTOR = 0.3
NUKE_SLOWMO_DURATION = 0.5

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
# PICKUPS / POWER-UPS
# -----------------------------

# Frequência de spawn automático (segundos)
PICKUP_AUTO_SPAWN_INTERVAL_MIN = 0.5
PICKUP_AUTO_SPAWN_INTERVAL_MAX = 1

# Número máximo de pickups activos em simultâneo
PICKUP_MAX_ACTIVE = 7

# Tempo de vida de cada pickup (em segundos)
PICKUP_LIFETIME_SECONDS = 15.0

# Probabilidades (%). Devem somar 100.

PICKUP_PROB_HP_UP = 50
PICKUP_PROB_HP_DOWN = 40
PICKUP_PROB_GRENADES = 30
PICKUP_PROB_WEAPON_UP = 10
PICKUP_PROB_TIME = 30
PICKUP_PROB_NUKE = 5

# Efeitos numéricos dos pickups

# Upgrade de arma
WEAPON_UPGRADE_AMMO = 100
WEAPON_UPGRADE_FIRE_RATE_MULTIPLIER = 0.5   # 0.5 = duas vezes mais rápido
WEAPON_UPGRADE_DAMAGE_MULTIPLIER = 2.0
WEAPON_UPGRADE_MAX_STACKS = 3

# Granadas
GRENADE_RELOAD_AMOUNT = 3

# Vida
HP_UP_AMOUNT = 500
HP_DOWN_AMOUNT = 200

TIME_PICKUP_SECONDS = 15

# -----------------------------
# CHEATS
# -----------------------------
CHEAT_CODES = ["GOD", "TIME", "SPJ", "GRN", "TTT"]

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
