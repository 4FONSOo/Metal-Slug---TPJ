import os
# Ecrã
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
TITLE = "Metal Slug Mini Game (TPJ)"
FPS = 60

# Cores 
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminhos
PATH_ASSETS = os.path.join(BASE_DIR, '..', 'assets')