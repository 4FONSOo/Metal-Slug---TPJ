# resources.py

import os
import pygame

from config import * #ASSETS_DIR, BACKGROUND_FILE, HEIGHT, BACKGROUND_WIDTH_MANUAL, BACKGROUND_HEIGHT_MANUAL

def find_asset(filename):
    """Procura recursivamente dentro de ASSETS_DIR e devolve o caminho completo."""
    for root, _, files in os.walk(ASSETS_DIR):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"Asset '{filename}' não encontrado em {ASSETS_DIR}")

def load_background():
    bg_path = find_asset(BACKGROUND_FILE)
    background = pygame.image.load(bg_path).convert_alpha()
    bg_width = BACKGROUND_WIDTH_MANUAL or background.get_width()
    bg_height = BACKGROUND_HEIGHT_MANUAL or HEIGHT
    background = pygame.transform.scale(background, (bg_width, bg_height))
    return background, bg_width, bg_height

def load_player(width, height, base_name="player_2"):
    """Carrega sprite do jogador conforme o nome (procura automaticamente em subpastas)."""
    filename = f"{base_name}.png"
    path = find_asset(filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (width, height))

