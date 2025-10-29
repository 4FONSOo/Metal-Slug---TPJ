# config.py

import pygame

WIDTH = 800
HEIGHT = 600
WINDOW_TITLE = "Metal Slug 2D"
FPS = 60

ASSETS_DIR = r"C:\Users\userdr\Desktop\Metal_2710\Assets"
BACKGROUND_FILE = "metal_slug_sub.png"
PLAYER_EXTS = ("png", "jpg", "jpeg")

PLAYER_WIDTH = 125
PLAYER_HEIGHT = 125
PLAYER_SPEED = 5
PLAYER_JUMP_SPEED = -15
PLAYER_GRAVITY = 1

BACKGROUND_WIDTH_MANUAL = 4527
BACKGROUND_HEIGHT_MANUAL = 0
BG_SPEED = 3

PLATFORMS = [
    pygame.Rect(100, 500, 200, 20),
    pygame.Rect(400, 400, 200, 20),
    pygame.Rect(600, 300, 200, 20),
]
