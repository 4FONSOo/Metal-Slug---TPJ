# resource.py

import os
import pygame

from config import *

def load_background():
    bg_path = os.path.join(ASSETS_DIR, BACKGROUND_FILE)
    background = pygame.image.load(bg_path).convert_alpha()
    bg_width = BACKGROUND_WIDTH_MANUAL or background.get_width()
    bg_height = BACKGROUND_HEIGHT_MANUAL or HEIGHT
    background = pygame.transform.scale(background, (bg_width, bg_height))
    return background, bg_width, bg_height


def load_player(width, height, base_name="player_2"):
    path = os.path.join(ASSETS_DIR, f"{base_name}.png")
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (width, height))
