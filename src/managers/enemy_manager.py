# enemy_manager.py

from dataclasses import dataclass
from typing import Protocol, List, Callable, Optional, Tuple
import random

import config


class EnemyLike(Protocol):

    alive: bool

    def update(self) -> None:
        ...

    @property
    def rect(self):
        ...

    def maybe_shoot(self, projectiles: list, bg_width: int) -> None:
        ...


# Função que cria um inimigo em (x, y)
EnemyFactory = Callable[[float, float], EnemyLike]


@dataclass
class SpawnZone:

    x_min: float
    x_max: float
    y: float


class EnemyManager:

    def __init__(
        self,
        enemy_factory: EnemyFactory,
        *,
        max_spawns: Optional[int] = None,
        max_active: Optional[int] = None,
        spawn_zones: Optional[List[SpawnZone]] = None,
        auto_spawn: bool = True,
        spawn_interval_min: float = 1.0,
        spawn_interval_max: float = 3.0,
        enemy_projectiles: Optional[List] = None,
        bg_width: Optional[int] = None,
    ) -> None:
        if max_spawns is None:
            max_spawns = config.ENEMY_MANAGER_MAX_SPAWNS_DEFAULT
        if max_active is None:
            max_active = config.ENEMY_MANAGER_MAX_ACTIVE_DEFAULT

        self._enemy_factory = enemy_factory
        self._max_spawns_total = int(max_spawns)
        self._max_active = int(max_active)

        self._spawned_total = 0
        self._enemies: List[EnemyLike] = []

        self._spawn_zones: List[SpawnZone] = list(spawn_zones) if spawn_zones else []

        self.auto_spawn = bool(auto_spawn)
        self.spawn_interval_min = float(spawn_interval_min)
        self.spawn_interval_max = float(spawn_interval_max)
        self._spawn_timer = 0.0
        self._next_spawn_time = self._random_spawn_interval()

        self._enemy_projectiles: Optional[List] = enemy_projectiles
        self._bg_width: int = int(bg_width) if bg_width is not None else 0

    # ------------------------------------------------------------------ #
    # Helpers de construção
    # ------------------------------------------------------------------ #

    @classmethod
    def from_level_bounds(
        cls,
        enemy_factory: EnemyFactory,
        *,
        level_width: int,
        ground_y: float,
        margin: Optional[int] = None,
        max_spawns: Optional[int] = None,
        max_active: Optional[int] = None,
        auto_spawn: bool = True,
        spawn_interval_min: float = 1.0,
        spawn_interval_max: float = 3.0,
        enemy_projectiles: Optional[List] = None,
    ) -> "EnemyManager":

        if margin is None:
            margin = config.ENEMY_MANAGER_SPAWN_X_MARGIN

        margin = max(1, int(margin))
        level_width = max(2 * margin + 1, int(level_width))

        zones = [
            SpawnZone(x_min=0, x_max=margin, y=ground_y),
            SpawnZone(x_min=level_width - margin, x_max=level_width, y=ground_y),
        ]

        return cls(
            enemy_factory,
            max_spawns=max_spawns,
            max_active=max_active,
            spawn_zones=zones,
            auto_spawn=auto_spawn,
            spawn_interval_min=spawn_interval_min,
            spawn_interval_max=spawn_interval_max,
            enemy_projectiles=enemy_projectiles,
            bg_width=level_width,
        )

    # ------------------------------------------------------------------ #
    # Configuração
    # ------------------------------------------------------------------ #

    def set_spawn_zones(self, zones: List[SpawnZone]) -> None:
        self._spawn_zones = list(zones)

    def add_spawn_zone(self, zone: SpawnZone) -> None:
        self._spawn_zones.append(zone)

    # ------------------------------------------------------------------ #
    # Spawning
    # ------------------------------------------------------------------ #

    def _can_spawn_more(self) -> bool:
        if self._spawned_total >= self._max_spawns_total:
            return False
        if len(self._enemies) >= self._max_active:
            return False
        return True

    def _random_spawn_interval(self) -> float:
        if self.spawn_interval_max <= self.spawn_interval_min:
            return max(0.1, self.spawn_interval_min)
        return random.uniform(self.spawn_interval_min, self.spawn_interval_max)

    def _random_spawn_position(self) -> Optional[Tuple[float, float]]:
        if not self._spawn_zones:
            return None

        zone = random.choice(self._spawn_zones)
        x = random.uniform(zone.x_min, zone.x_max)
        y = zone.y
        return x, y

    def try_spawn_enemy(self) -> Optional[EnemyLike]:
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
    # Update
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float | None = None) -> None:

        enemy_projectiles = self._enemy_projectiles
        bg_width = self._bg_width

        # 1) Actualizar inimigos + disparos
        for enemy in self._enemies:
            enemy.update()
            if enemy_projectiles is not None and hasattr(enemy, "maybe_shoot"):
                try:
                    enemy.maybe_shoot(enemy_projectiles, bg_width)
                except Exception:
                    # Não deixamos um inimigo marado rebentar o manager.
                    pass

        # 2) Limpar mortos
        self._enemies = [e for e in self._enemies if getattr(e, "alive", False)]

        # 3) Auto-spawn temporizado (à medida que vão morrendo)
        if not (self.auto_spawn and dt_seconds is not None and dt_seconds > 0.0):
            return

        if not self._can_spawn_more():
            return

        self._spawn_timer += float(dt_seconds)
        if self._spawn_timer >= self._next_spawn_time:
            if self._can_spawn_more():
                self.try_spawn_enemy()
            self._spawn_timer = 0.0
            self._next_spawn_time = self._random_spawn_interval()

    # ------------------------------------------------------------------ #
    # Acesso
    # ------------------------------------------------------------------ #

    def get_enemies(self) -> List[EnemyLike]:
        
        return self._enemies

    def clear(self) -> None:
        
        self._enemies.clear()
        self._spawned_total = 0
        self._spawn_timer = 0.0
        self._next_spawn_time = self._random_spawn_interval()

    # ------------------------------------------------------------------ #
    # Info
    # ------------------------------------------------------------------ #

    @property
    def total_spawned(self) -> int:
        
        return self._spawned_total

    @property
    def max_spawns(self) -> int:
        return self._max_spawns_total

    @property
    def max_active(self) -> int:
        return self._max_active

    @property
    def active_enemies_count(self) -> int:
        
        return len(self._enemies)

    @property
    def spawns_remaining(self) -> int:
        
        return max(0, self._max_spawns_total - self._spawned_total)
