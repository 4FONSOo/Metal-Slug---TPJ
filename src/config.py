# config.py

import os
import pygame

# Tela

WIDTH = 800
HEIGHT = 600
WINDOW_TITLE = "Metal Slug 2D"
FPS = 60

# Projecto

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Assets

ASSETS_DIR = os.path.join(BASE_DIR, "..", "Assets")
ASSETS_DIR = os.path.abspath(ASSETS_DIR)  # converte para caminho absoluto

if not os.path.isdir(ASSETS_DIR):
    raise FileNotFoundError(f"Pasta de assets não encontrada: {ASSETS_DIR}")


# Aqui começa a sério

BACKGROUND_FILE = "metal_slug_sub.png"
PLAYER_EXTS = ("png", "jpg", "jpeg")

# Jogardor

PLAYER_WIDTH = 60
PLAYER_HEIGHT = 80
PLAYER_SPEED = 5
PLAYER_JUMP_SPEED = -12
PLAYER_GRAVITY = 0.4
PLAYER_MAX_HP = 1000

# Background

BACKGROUND_WIDTH_MANUAL = 4527
BACKGROUND_HEIGHT_MANUAL = 0
BG_SPEED = 3

# Plataformas manuais (apenas para testes!!!)
PLATFORMS = [
    pygame.Rect(100, 500, 200, 20),
    pygame.Rect(400, 400, 200, 20),
    pygame.Rect(600, 300, 200, 20),
]


# -----------------------------
# GAME STATE DEFAULTS
# -----------------------------
INITIAL_SCORE = 0
INITIAL_CREDITS = 5
INITIAL_TIME_LEFT = 60          # segundos por nível
INITIAL_LEVEL_NAME = "Nível 1"

# Timer do HUD / relógio
TIMER_EVENT_INDEX = 1           # vai ser usado como pygame.USEREVENT + TIMER_EVENT_INDEX
TIMER_INTERVAL_MS = 1000        # 1000 ms = 1 segundo

# -----------------------------
# INPUT KEYS
# -----------------------------
KEY_MENU = pygame.K_ESCAPE   # sair para menu / back
KEY_PAUSE = pygame.K_p       # pausar o jogo

KEY_FIRE = pygame.K_SPACE    # disparar / melee

KEY_UP = pygame.K_UP         
KEY_DOWN = pygame.K_DOWN     
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_JUMP = pygame.K_LALT