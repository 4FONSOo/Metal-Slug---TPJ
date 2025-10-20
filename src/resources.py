import pygame
from pathlib import Path

class ResourceManager:
    _images = {}
    _sounds = {}

    @classmethod
    def load_image(cls, path, colorkey=None):
        path = Path(path)
        key = str(path)
        if key in cls._images:
            return cls._images[key]
        img = pygame.image.load(str(path)).convert_alpha()
        if colorkey is not None:
            img.set_colorkey(colorkey)
        cls._images[key] = img
        return img

    @classmethod
    def get_image(cls, path):
        return cls._images.get(str(path))

    @classmethod
    def load_sound(cls, path):
        path = Path(path)
        key = str(path)
        if key in cls._sounds:
            return cls._sounds[key]
        snd = pygame.mixer.Sound(str(path))
        cls._sounds[key] = snd
        return snd