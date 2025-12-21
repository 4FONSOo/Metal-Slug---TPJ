# entity/pickups.py

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Tuple, Optional, Iterable
import random

import config

PICKUP_WIDTH = 64
PICKUP_HEIGHT = 64
PICKUP_FALL_SPEED = 120.0       
PICKUP_SPAWN_MARGIN_X = 32      
PICKUP_SPAWN_Y_OFFSET = 40      

PICKUP_COLOR_DEFAULT = (255, 255, 0)
PICKUP_COLOR_HP_UP = (0, 220, 0)
PICKUP_COLOR_HP_DOWN = (220, 0, 0)
PICKUP_COLOR_GRENADES = (0, 180, 255)
PICKUP_COLOR_WEAPON_UP = (255, 165, 0)
PICKUP_COLOR_TIME = (0, 200, 255)
PICKUP_COLOR_NUKE = (255, 255, 255)


class PickupKind(Enum):
    HP_UP = "hp_up"
    HP_DOWN = "hp_down"
    GRENADES = "grenades"
    WEAPON_UP = "weapon_up"
    NUKE = "nuke"
    TIME = "time"


def _get_color_for_kind(kind: PickupKind) -> Tuple[int, int, int]:
    if kind == PickupKind.HP_UP:
        return PICKUP_COLOR_HP_UP
    if kind == PickupKind.HP_DOWN:
        return PICKUP_COLOR_HP_DOWN
    if kind == PickupKind.GRENADES:
        return PICKUP_COLOR_GRENADES
    if kind == PickupKind.WEAPON_UP:
        return PICKUP_COLOR_WEAPON_UP
    if kind == PickupKind.TIME:
        return PICKUP_COLOR_TIME
    if kind == PickupKind.NUKE:
        return PICKUP_COLOR_NUKE
    return PICKUP_COLOR_DEFAULT


@dataclass
class Pickup:
    kind: PickupKind
    x: float
    y: float
    lifetime: float
    falling: bool = True
    ground_y: Optional[float] = None

    vy: float = PICKUP_FALL_SPEED
    width: float = PICKUP_WIDTH
    height: float = PICKUP_HEIGHT
    alive: bool = True
    collected: bool = False

    # -----------------------------
    # LÓGICA
    # -----------------------------

    def update(self, dt: float) -> None:
        """
        Actualiza posição e lifetime.

        dt em segundos (não milissegundos).
        """
        if not self.alive:
            return

        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.alive = False
            return

        if self.falling:
            if self.ground_y is not None:
                new_y = self.y + self.vy * dt
                if new_y + self.height >= self.ground_y:
                    self.y = self.ground_y - self.height
                    self.falling = False
                else:
                    self.y = new_y
            else:
                new_y = self.y + self.vy * dt
                screen_bottom = config.HEIGHT
                if new_y + self.height >= screen_bottom:
                    self.y = screen_bottom - self.height
                    self.falling = False
                else:
                    self.y = new_y

    # -----------------------------
    # COLISÃO
    # -----------------------------

    def get_rect_tuple(self) -> Tuple[int, int, int, int]:
        return int(self.x), int(self.y), int(self.width), int(self.height)

    def get_draw_data(self) -> Dict[str, Any]:
        if not self.alive:
            return {}

        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": _get_color_for_kind(self.kind),
            "kind": self.kind.value,
        }

    # -----------------------------
    # VFX
    # -----------------------------

    def get_effect(self) -> Dict[str, Any]:
        if self.kind == PickupKind.HP_UP:
            return {
                "type": "hp_up",
                "hp": config.HP_UP_AMOUNT,
                "sfx": "PickUp2.mp3",
            }

        if self.kind == PickupKind.HP_DOWN:
            return {
                "type": "hp_down",
                "hp": -config.HP_DOWN_AMOUNT,
                "sfx": "PickUp2.mp3",
            }

        if self.kind == PickupKind.GRENADES:
            return {
                "type": "grenades",
                "grenades_delta": config.GRENADE_RELOAD_AMOUNT,
                "sfx": "PickUp2.mp3",
            }

        if self.kind == PickupKind.WEAPON_UP:
            return {
                "type": "weapon_up",
                "ammo": config.WEAPON_UPGRADE_AMMO,
                "fire_rate_multiplier": config.WEAPON_UPGRADE_FIRE_RATE_MULTIPLIER,
                "sfx": "PickUp1.mp3",
            }

        if self.kind == PickupKind.NUKE:
            return {
                "type": "nuke",
                "nuke": True,
                "sfx": "PickUp2.mp3",
            }
        
        if self.kind == PickupKind.TIME:
            return {
                "type": "time",
                "time": config.TIME_PICKUP_SECONDS,
                "sfx": "PickUp2.mp3",
            }

        return {
            "type": "unknown",
        }

    def mark_collected(self) -> None:
        self.collected = True
        self.alive = False


# -----------------------------
# Helpers
# -----------------------------

def _rect_to_tuple(rect_like) -> Tuple[int, int, int, int]:
    if rect_like is None:
        return 0, 0, 0, 0

    for attr in ("x", "y", "width", "height"):
        if not hasattr(rect_like, attr):
            break
    else:
        return (
            int(rect_like.x),
            int(rect_like.y),
            int(rect_like.width),
            int(rect_like.height),
        )

    x, y, w, h = rect_like
    return int(x), int(y), int(w), int(h)


def _compute_ground_y_for_x(
    x: float,
    platforms: Iterable[object],
    fallback_ground_y: Optional[float] = None,
) -> Optional[float]:
    best_y: Optional[int] = None
    xi = int(x)

    for plat in platforms:
        px, py, pw, ph = _rect_to_tuple(plat)
        if xi < px or xi > px + pw:
            continue

        # primeira plataforma que a caixa encontra ao cair:
        # a de menor y (mais perto do topo do ecrã)
        if best_y is None or py < best_y:
            best_y = py

    if best_y is not None:
        return float(best_y)

    return fallback_ground_y


def _base_random_kind() -> PickupKind:

    probs = [
        (config.PICKUP_PROB_HP_UP, PickupKind.HP_UP),
        (config.PICKUP_PROB_HP_DOWN, PickupKind.HP_DOWN),
        (config.PICKUP_PROB_GRENADES, PickupKind.GRENADES),
        (config.PICKUP_PROB_WEAPON_UP, PickupKind.WEAPON_UP),
        (config.PICKUP_PROB_NUKE, PickupKind.NUKE),
        (config.PICKUP_PROB_TIME, PickupKind.TIME),
    ]

    total = sum(p for p, _ in probs)
    if total <= 0:
        # fallback: distribuição uniforme
        return random.choice([k for _, k in probs])

    r = random.uniform(0, total)
    acc = 0.0
    for prob, kind in probs:
        acc += prob
        if r <= acc:
            return kind

    return probs[-1][1]


def _choose_random_kind(
    include: Optional[Iterable[PickupKind]] = None,
    exclude: Optional[Iterable[PickupKind]] = None,
) -> PickupKind:

    include_set = set(include) if include is not None else None
    exclude_set = set(exclude) if exclude is not None else None

    def allowed(k: PickupKind) -> bool:
        if include_set is not None and k not in include_set:
            return False
        if exclude_set is not None and k in exclude_set:
            return False
        return True

    kind = _base_random_kind()
    if allowed(kind):
        return kind

    candidates = [k for k in PickupKind if allowed(k)]
    if candidates:
        return random.choice(candidates)

    return kind


# -----------------------------
# Spawns
# -----------------------------

def spawn_random_pickup(
    level_width: int,
    *,
    ground_y: Optional[float] = None,
    include: Optional[Iterable[PickupKind]] = None,
    exclude: Optional[Iterable[PickupKind]] = None,
    platforms: Optional[Iterable[object]] = None,
) -> Pickup:
    kind = _choose_random_kind(include=include, exclude=exclude)

    margin = PICKUP_SPAWN_MARGIN_X
    lw = max(2 * margin + 1, int(level_width))
    x = random.randint(margin, lw - margin)

    if platforms is not None:
        gy = _compute_ground_y_for_x(x, platforms, fallback_ground_y=ground_y)
    else:
        gy = ground_y

    y = -PICKUP_SPAWN_Y_OFFSET

    return Pickup(
        kind=kind,
        x=float(x),
        y=float(y),
        lifetime=config.PICKUP_LIFETIME_SECONDS,
        falling=True,
        ground_y=gy,
    )
