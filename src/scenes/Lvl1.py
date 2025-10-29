# Scenes/lvl_1.py

from resource import load_background
from config import PLATFORMS

def load_level():
    background, bg_width, bg_height = load_background()
    return {
        "background": background,
        "bg_width": bg_width,
        "bg_height": bg_height,
        "platforms": PLATFORMS
    }

