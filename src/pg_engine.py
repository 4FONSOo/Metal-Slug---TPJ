"""
Camada de abstracção por cima do pygame.

Objetivo:
  - Esconder completamente o módulo `pygame` do resto do código.
  - Fornecer helpers e aliases suficientes para o jogo actual.

Qualquer coisa que precise de pygame directamente deve ser adicionada aqui.
"""

import pygame
from pygame.math import Vector2 as _Vector2

# Re-export de tipos mais usados
Surface = pygame.Surface
Rect = pygame.Rect
Vector2 = _Vector2

# -----------------------------
# Inicialização / shutdown
# -----------------------------
def init():
    """Inicializa pygame (mas não o mixer)."""
    pygame.init()


def quit():
    """Fecha o pygame todo."""
    pygame.quit()


# -----------------------------
# Janela / ecrã
# -----------------------------
def create_window(width: int, height: int, title: str) -> Surface:
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    return screen


def set_window_title(title: str) -> None:
    pygame.display.set_caption(title)


def display_flip() -> None:
    pygame.display.flip()


# -----------------------------
# Clock / tempo
# -----------------------------
def create_clock():
    return pygame.time.Clock()


def time_get_ticks() -> int:
    """Devolve pygame.time.get_ticks()."""
    return pygame.time.get_ticks()


def time_set_timer(event_id: int, interval_ms: int) -> None:
    """Wrapper para pygame.time.set_timer."""
    pygame.time.set_timer(event_id, interval_ms)


def time_wait(ms: int) -> None:
    pygame.time.wait(ms)


# -----------------------------
# Eventos / input
# -----------------------------
def get_events():
    return pygame.event.get()


def get_keys():
    return pygame.key.get_pressed()


def key_name(key_code: int) -> str:
    return pygame.key.name(key_code)


def mouse_get_pos():
    return pygame.mouse.get_pos()


# Constantes

QUIT = pygame.QUIT
KEYDOWN = pygame.KEYDOWN
KEYUP = pygame.KEYUP
USEREVENT = pygame.USEREVENT
MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN

# TEclas pré-definidas

K_ESCAPE = pygame.K_ESCAPE
K_RETURN = pygame.K_RETURN
K_SPACE = pygame.K_SPACE
K_UP = pygame.K_UP
K_DOWN = pygame.K_DOWN
K_LEFT = pygame.K_LEFT
K_RIGHT = pygame.K_RIGHT
K_P = pygame.K_p
K_M = pygame.K_m
K_LALT = pygame.K_LALT
K_LCTRL = pygame.K_LCTRL



# -----------------------------
# Desenho / superfícies
# -----------------------------
def create_surface(size, alpha: bool = False) -> Surface:
    flags = pygame.SRCALPHA if alpha else 0
    return pygame.Surface(size, flags)


def blit(surface: Surface, source: Surface, dest):
    surface.blit(source, dest)


def draw_rect(surface: Surface, color, rect, width: int = 0):
    pygame.draw.rect(surface, color, rect, width)


def draw_circle(surface: Surface, color, center, radius: int, width: int = 0):
    pygame.draw.circle(surface, color, center, radius, width)


def flip_image(image: Surface, flip_x: bool = False, flip_y: bool = False) -> Surface:
    return pygame.transform.flip(image, flip_x, flip_y)


def scale_image(image: Surface, size) -> Surface:
    return pygame.transform.smoothscale(image, size)


def _raw_load_image(path: str) -> Surface:
    """Carregamento directo (sem cache) — usado pelo Flyweight para evitar recursão."""
    return pygame.image.load(path).convert_alpha()


def load_image(path: str) -> Surface:
    """Carrega imagem; usa Flyweight cache quando disponível."""
    try:
        from patterns.flyweight import get_global_flyweight_factory

        img = get_global_flyweight_factory().get_sprite(path)
        if img is not None:
            return img
    except Exception:
        pass

    return _raw_load_image(path)


# -----------------------------
# Fontes / texto
# -----------------------------
def _raw_create_font(name: str, size: int):
    """Criação directa (sem cache) — usado pelo Flyweight para evitar recursão."""
    return pygame.font.SysFont(name, int(size))


def create_font(name: str, size: int):
    """Cria fonte; usa Flyweight cache quando disponível."""
    try:
        from patterns.flyweight import get_global_flyweight_factory

        font = get_global_flyweight_factory().get_font(name, int(size))
        if font is not None:
            return font
    except Exception:
        pass

    return _raw_create_font(name, int(size))


def render_text(font, text: str, color, antialias: bool = True):
    return font.render(text, antialias, color)


# -----------------------------
# Som / música
# -----------------------------
def mixer_init():
    pygame.mixer.init()


def mixer_get_init():
    return pygame.mixer.get_init()


def music_load_and_play(path: str, loop: int = -1):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play(loop)


def music_stop():
    pygame.mixer.music.stop()


def music_set_volume(volume_float: float):
    pygame.mixer.music.set_volume(volume_float)


def music_get_volume() -> float:
    return pygame.mixer.music.get_volume()
