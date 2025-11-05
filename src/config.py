# config.py

import os
import pygame


WIDTH = 800
HEIGHT = 600
WINDOW_TITLE = "Metal Slug 2D"
FPS = 60

# Caminho base do projeto (onde está este ficheiro)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho dinâmico para Assets
ASSETS_DIR = os.path.join(BASE_DIR, "..", "Assets")
ASSETS_DIR = os.path.abspath(ASSETS_DIR)  # converte para caminho absoluto

if not os.path.isdir(ASSETS_DIR):
    raise FileNotFoundError(f"Pasta de assets não encontrada: {ASSETS_DIR}")

BACKGROUND_FILE = "metal_slug_sub.png"
# LEVEL_FILE = "level1.tmx"
PLAYER_EXTS = ("png", "jpg", "jpeg")

PLAYER_WIDTH = 125
PLAYER_HEIGHT = 125
PLAYER_SPEED = 5
PLAYER_JUMP_SPEED = -35
PLAYER_GRAVITY = 1

BACKGROUND_WIDTH_MANUAL = 4527
BACKGROUND_HEIGHT_MANUAL = 0
BG_SPEED = 3

PLATFORMS = [
    pygame.Rect(100, 500, 200, 20),
    pygame.Rect(400, 400, 200, 20),
    pygame.Rect(600, 300, 200, 20),
]
