# collision_manager.py
"""
Gestor de colisões (lógica).

Objectivo:
  - Centralizar a detecção de colisões entre:
      * player
      * inimigos
      * projécteis do player
      * projécteis dos inimigos
      * (opcional) granadas / explosões
  - NÃO depende de pygame/pg_engine.
  - Não aplica danos directamente. Só devolve “eventos de colisão”.
    O Game/Scene é que decide o que fazer (HP--, score++, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Tuple, Any, Optional


# ------------------------------------------------------------------ #
# Protocols / interfaces mínimas
# ------------------------------------------------------------------ #

class RectLike(Protocol):
    x: int
    y: int
    width: int
    height: int


class HasRect(Protocol):
    @property
    def rect(self) -> RectLike:
        ...


class DamageSource(Protocol):
    """Projéctil, explosão, etc. com potencial de causar dano."""

    damage: float
    alive: bool

    @property
    def rect(self) -> RectLike:
        ...


class EnemyLike(HasRect, Protocol):
    alive: bool


class PlayerLike(HasRect, Protocol):
    alive: bool


# ------------------------------------------------------------------ #
# Eventos de colisão
# ------------------------------------------------------------------ #

@dataclass
class ProjectileHitEnemy:
    projectile: DamageSource
    enemy: EnemyLike


@dataclass
class ProjectileHitPlayer:
    projectile: DamageSource
    player: PlayerLike


@dataclass
class EnemyTouchesPlayer:
    enemy: EnemyLike
    player: PlayerLike


@dataclass
class CollisionResult:
    """
    Resultado de uma passagem de detecção de colisões.

    O Game/Scene pode iterar por estas listas e aplicar o que entender.
    """

    player_hits: List[ProjectileHitPlayer]
    enemy_hits: List[ProjectileHitEnemy]
    contact_hits: List[EnemyTouchesPlayer]


# ------------------------------------------------------------------ #
# Helpers de rect
# ------------------------------------------------------------------ #

def _rect_to_tuple(rect: Any) -> Tuple[int, int, int, int]:
    """
    Converte pg.Rect-like ou (x, y, w, h) em (x, y, w, h).
    """
    if rect is None:
        return 0, 0, 0, 0

    # Tem atributos típicos de Rect?
    if all(hasattr(rect, a) for a in ("x", "y", "width", "height")):
        return int(rect.x), int(rect.y), int(rect.width), int(rect.height)

    # Assume tuplo ou lista
    x, y, w, h = rect
    return int(x), int(y), int(w), int(h)


def _rects_overlap(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return False

    if ax + aw <= bx:
        return False
    if bx + bw <= ax:
        return False
    if ay + ah <= by:
        return False
    if by + bh <= ay:
        return False
    return True


# ------------------------------------------------------------------ #
# CollisionManager
# ------------------------------------------------------------------ #

class CollisionManager:
    """
    Motor de detecção de colisões.

    Não mantém estado entre frames. Apenas fornece métodos puros
    para analisar o estado actual das entidades.
    """

    def detect_collisions(
        self,
        player: Optional[PlayerLike],
        enemies: List[EnemyLike],
        player_projectiles: List[DamageSource],
        enemy_projectiles: List[DamageSource],
    ) -> CollisionResult:
        """
        Analisa colisões e devolve um CollisionResult com listas de eventos.

        Não altera HP, não mata ninguém – isso é responsabilidade do código
        que consome o resultado.
        """
        player_hits: List[ProjectileHitPlayer] = []
        enemy_hits: List[ProjectileHitEnemy] = []
        contact_hits: List[EnemyTouchesPlayer] = []

        player_rect_tup: Optional[Tuple[int, int, int, int]] = None
        if player is not None and player.alive:
            player_rect_tup = _rect_to_tuple(player.rect)

        # Projécteis do player vs inimigos
        for proj in player_projectiles:
            if not proj.alive:
                continue
            proj_rect = _rect_to_tuple(proj.rect)

            for enemy in enemies:
                if not enemy.alive:
                    continue
                enemy_rect = _rect_to_tuple(enemy.rect)
                if _rects_overlap(proj_rect, enemy_rect):
                    enemy_hits.append(ProjectileHitEnemy(projectile=proj, enemy=enemy))

        # Projécteis de inimigos vs player
        if player_rect_tup is not None:
            for proj in enemy_projectiles:
                if not proj.alive:
                    continue
                proj_rect = _rect_to_tuple(proj.rect)
                if _rects_overlap(proj_rect, player_rect_tup):
                    player_hits.append(ProjectileHitPlayer(projectile=proj, player=player))

        # Contacto físico player <-> inimigos
        if player_rect_tup is not None:
            for enemy in enemies:
                if not enemy.alive:
                    continue
                enemy_rect = _rect_to_tuple(enemy.rect)
                if _rects_overlap(player_rect_tup, enemy_rect):
                    contact_hits.append(EnemyTouchesPlayer(enemy=enemy, player=player))

        return CollisionResult(
            player_hits=player_hits,
            enemy_hits=enemy_hits,
            contact_hits=contact_hits,
        )
