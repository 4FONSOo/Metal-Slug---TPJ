# controls.py
"""
Sistema de controlos reconfiguráveis em runtime.
"""

import pg_engine as pg
import config

MOVE_LEFT = "MOVE_LEFT"
MOVE_RIGHT = "MOVE_RIGHT"
UP = "UP"
DOWN = "DOWN"
JUMP = "JUMP"
FIRE = "FIRE"
GRANADE = "GRANADE"
MENU = "MENU"
PAUSE = "PAUSE"

DEFAULT_BINDINGS = {
    MOVE_LEFT: config.KEY_LEFT,
    MOVE_RIGHT: config.KEY_RIGHT,
    UP: config.KEY_UP,
    DOWN: config.KEY_DOWN,
    JUMP: config.KEY_JUMP,
    FIRE: config.KEY_FIRE,
    GRANADE: config.KEY_SEC_FIRE,
    MENU: config.KEY_MENU,
    PAUSE: config.KEY_PAUSE,
}

_current_bindings = dict(DEFAULT_BINDINGS)


def get_key(action: str) -> int:
    return _current_bindings.get(action, 0)


def set_key(action: str, key_code: int) -> None:
    if action in DEFAULT_BINDINGS:
        _current_bindings[action] = key_code


def get_key_name(action: str) -> str:
    code = get_key(action)
    try:
        name = pg.key_name(code)
    except Exception:
        return "?"
    return name.upper()


def reset_defaults() -> None:
    global _current_bindings
    _current_bindings = dict(DEFAULT_BINDINGS)


def all_bindings() -> dict:
    return dict(_current_bindings)
