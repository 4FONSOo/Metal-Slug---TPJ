# enemy_manager.py
"""
Gestor de inimigos.

NOTA IMPORTANTE:
  - Este ficheiro não está integrado em lado nenhum por enquanto.
  - A ideia é separar melhor a responsabilidade de “gerir muitos inimigos”
    da definição de um Enemy individual (normalmente em entity/enemy.py).

Responsabilidades:
  - Manter lista de inimigos activos.
  - Controlar spawns até um máximo.
  - Actualizar inimigos.
  - Fornecer acesso fácil à lista de inimigos.

Não faz:
  - Desenho (isso é trabalho do Game/Scene).
  - Colisões (isso é trabalho do CollisionManager).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Callable, Optional, Tuple
import random


class EnemyLike(Protocol):
    """Interface mínima esperada para um inimigo."""

    alive: bool

    def update(self, dt: float) -> None:
        ...

    @property
    def rect(self):
        """Qualquer coisa tipo Rect (pg.Rect, etc.)."""
        ...


EnemyFactory = Callable[[float, float], EnemyLike]


@dataclass
class SpawnZone:
    """Zona lógica onde podem ser criados inimigos."""

    x_min: float
    x_max: float
    y: float


class EnemyManager:
    """
    Gestor de inimigos genérico.

    Exige uma função `enemy_factory(x, y)` para criar novos inimigos. Assim,
    o código de spawn fica desacoplado da classe Enemy concreta.
    """

    def __init__(
        self,
        enemy_factory: EnemyFactory,
        *,
        max_spawns: int = 50,
        max_active: int = 10,
        spawn_zones: Optional[List[SpawnZone]] = None,
    ) -> None:
        self._enemy_factory = enemy_factory
        self._max_spawns_total = max_spawns
        self._max_active = max_active

        self._spawned_total = 0
        self._enemies: List[EnemyLike] = []

        # Se não houver zonas, podem ser definidas mais tarde
        self._spawn_zones = spawn_zones or []

    # ------------------------------------------------------------------ #
    # Configuração
    # ------------------------------------------------------------------ #

    def set_spawn_zones(self, zones: List[SpawnZone]) -> None:
        self._spawn_zones = zones

    # ------------------------------------------------------------------ #
    # Spawning
    # ------------------------------------------------------------------ #

    def _can_spawn_more(self) -> bool:
        if self._spawned_total >= self._max_spawns_total:
            return False
        if len(self._enemies) >= self._max_active:
            return False
        return True

    def _random_spawn_position(self) -> Optional[Tuple[float, float]]:
        if not self._spawn_zones:
            return None

        zone = random.choice(self._spawn_zones)
        x = random.uniform(zone.x_min, zone.x_max)
        y = zone.y
        return x, y

    def try_spawn_enemy(self) -> Optional[EnemyLike]:
        """
        Tenta criar um inimigo novo se as regras de limite permitirem.

        Devolve o Enemy criado ou None se não foi possível.
        """
        if not self._can_spawn_more():
            return None

        pos = self._random_spawn_position()
        if pos is None:
            return None

        x, y = pos
        enemy = self._enemy_factory(x, y)
        self._enemies.append(enemy)
        self._spawned_total += 1
        return enemy

    # ------------------------------------------------------------------ #
    # Update / limpeza
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float) -> None:
        """Actualiza todos os inimigos e remove os que já morreram."""
        for enemy in self._enemies:
            enemy.update(dt_seconds)

        self._enemies = [e for e in self._enemies if e.alive]

    # ------------------------------------------------------------------ #
    # Acesso
    # ------------------------------------------------------------------ #

    def get_enemies(self) -> List[EnemyLike]:
        return self._enemies

    def clear(self) -> None:
        """Remove todos os inimigos e faz reset à contagem de spawns."""
        self._enemies.clear()
        self._spawned_total = 0

    # ------------------------------------------------------------------ #
    # Info
    # ------------------------------------------------------------------ #

    @property
    def total_spawned(self) -> int:
        """Quantos inimigos já foram criados desde o início."""
        return self._spawned_total

    @property
    def max_spawns(self) -> int:
        return self._max_spawns_total

    @property
    def max_active(self) -> int:
        return self._max_active
