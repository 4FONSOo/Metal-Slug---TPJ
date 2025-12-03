# projectile_manager.py
"""
Gestor de projécteis (balas, granadas, etc.)

Objectivo:
  - Centralizar a gestão de projécteis do jogador e dos inimigos.
  - Não depende de pygame/pg_engine.
  - Só trata de:
      * armazenar projécteis
      * actualizá-los
      * limpar os mortos
  - A lógica de colisão fica noutro lado (CollisionManager).

Integração típica (futuro):
  - O Game ou a Scene cria o ProjectileManager.
  - Sempre que dispara, regista o projéctil aqui.
  - A cada frame chama update(dt_seconds).
  - Usa os getters para percorrer listas de projécteis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List


class ProjectileLike(Protocol):
    """Interface mínima que um projéctil deve cumprir para ser gerido aqui."""

    alive: bool

    def update(self, dt: float) -> None:
        ...


@dataclass
class ProjectileGroup:
    """Agrupa projécteis por “dono” (player, inimigo, etc.)."""

    player: List[ProjectileLike]
    enemies: List[ProjectileLike]
    others: List[ProjectileLike]  # granadas, lasers especiais, etc.


class ProjectileManager:
    """
    Gestor de projécteis.

    Mantém três grupos lógicos:
      - projécteis do jogador
      - projécteis de inimigos
      - outros (granadas, especiais, etc.)

    Não sabe nada de colisões nem de desenho.
    """

    def __init__(self) -> None:
        self._player_projectiles: List[ProjectileLike] = []
        self._enemy_projectiles: List[ProjectileLike] = []
        self._other_projectiles: List[ProjectileLike] = []

    # ------------------------------------------------------------------ #
    # Registo de projécteis
    # ------------------------------------------------------------------ #

    def add_player_projectile(self, projectile: ProjectileLike) -> None:
        self._player_projectiles.append(projectile)

    def add_enemy_projectile(self, projectile: ProjectileLike) -> None:
        self._enemy_projectiles.append(projectile)

    def add_other_projectile(self, projectile: ProjectileLike) -> None:
        """
        Para projécteis que não sejam balas normais:
          - granadas
          - mísseis
          - lasers especiais
        """
        self._other_projectiles.append(projectile)

    # ------------------------------------------------------------------ #
    # Update / limpeza
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float) -> None:
        """Actualiza todos os projécteis e remove os que já morreram."""
        for proj in self._player_projectiles:
            proj.update(dt_seconds)

        for proj in self._enemy_projectiles:
            proj.update(dt_seconds)

        for proj in self._other_projectiles:
            proj.update(dt_seconds)

        self._player_projectiles = [p for p in self._player_projectiles if p.alive]
        self._enemy_projectiles = [p for p in self._enemy_projectiles if p.alive]
        self._other_projectiles = [p for p in self._other_projectiles if p.alive]

    # ------------------------------------------------------------------ #
    # Acesso às listas
    # ------------------------------------------------------------------ #

    def get_player_projectiles(self) -> List[ProjectileLike]:
        return self._player_projectiles

    def get_enemy_projectiles(self) -> List[ProjectileLike]:
        return self._enemy_projectiles

    def get_other_projectiles(self) -> List[ProjectileLike]:
        return self._other_projectiles

    def get_all_projectiles(self) -> ProjectileGroup:
        """Devolve todas as listas agrupadas num só objecto."""
        return ProjectileGroup(
            player=self._player_projectiles,
            enemies=self._enemy_projectiles,
            others=self._other_projectiles,
        )

    # ------------------------------------------------------------------ #
    # Utilitários
    # ------------------------------------------------------------------ #

    def clear(self) -> None:
        """Apaga todos os projécteis (ex: ao recomeçar o nível)."""
        self._player_projectiles.clear()
        self._enemy_projectiles.clear()
        self._other_projectiles.clear()
