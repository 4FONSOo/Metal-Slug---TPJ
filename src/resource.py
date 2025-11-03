# resources.py

import os
import pygame
import pytmx

from config import * #ASSETS_DIR, BACKGROUND_FILE, HEIGHT, BACKGROUND_WIDTH_MANUAL, BACKGROUND_HEIGHT_MANUAL
# BACKGROUND_HEIGHT_MANUAL, LEVEL_FILE

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

def load_sound_path(filename):
     """ Loading de música """
     sounds_dir = os.path.join(ASSETS_DIR, "sounds")
     path = os.path.join(sounds_dir, filename)

     if not os.path.isfile(path):
         raise FileNotFoundError(f"[resource] Som não encontrado: {path}")

     return os.path.abspath(path)
"""
def load_tmx() -> pytmx.TiledMap:
    Carrega o mapa TMX do Tiled com alpha.
    level_path = find_asset(LEVEL_FILE)
    return pytmx.load_pygame(level_path, pixelalpha=True)"""

