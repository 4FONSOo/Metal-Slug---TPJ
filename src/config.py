# config.py

import os
import pygame

# ---------- ⚙️ JANELA E PERFORMANCE ----------
WIDTH = 800
HEIGHT = 600
WINDOW_TITLE = "Metal Slug 2D"
FPS = 60

# ---------- 📁 CAMINHOS ----------
# Caminho base do projeto (onde está este ficheiro)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho dinâmico para Assets
ASSETS_DIR = os.path.join(BASE_DIR, "..", "Assets")
ASSETS_DIR = os.path.abspath(ASSETS_DIR)  # converte para caminho absoluto

if not os.path.isdir(ASSETS_DIR):
    raise FileNotFoundError(f"Pasta de assets não encontrada: {ASSETS_DIR}")

# ---------- 🖼️ RECURSOS ----------
BACKGROUND_FILE = "metal_slug_sub.png"
PLAYER_EXTS = ("png", "jpg", "jpeg")

# ---------- 🧍‍♂️ JOGADOR ----------
# Tamanho ajustado às novas sprites (mais detalhadas)
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 80
PLAYER_SPEED = 5

# Física refinada para saltos mais leves e naturais
PLAYER_JUMP_SPEED = -12
PLAYER_GRAVITY = 0.4

# Vida máxima
PLAYER_MAX_HP = 100

# ---------- 🌄 CENÁRIO ----------
BACKGROUND_WIDTH_MANUAL = 4527
BACKGROUND_HEIGHT_MANUAL = 0
BG_SPEED = 3

# ---------- 🧱 PLATAFORMAS DE TESTE (fallback) ----------
PLATFORMS = [
    pygame.Rect(100, 500, 200, 20),
    pygame.Rect(400, 400, 200, 20),
    pygame.Rect(600, 300, 200, 20),
]
