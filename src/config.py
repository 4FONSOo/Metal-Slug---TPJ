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
PLAYER_MAX_HP = 100

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
