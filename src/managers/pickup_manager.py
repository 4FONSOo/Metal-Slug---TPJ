# managers/pickup_manager.py
"""
Gestor de pickups (power-ups) do nível.

Ideia geral:
  - Não depende de pygame nem de pg_engine (só lógica).
  - Mantém e actualiza a lista de pickups activos.
  - Trata do spawn automático aleatório (a cair de paraquedas).
  - Detecta quando o jogador apanha um pickup.
  - Devolve uma lista de "efeitos" para o Game/Scene aplicar
    (não mexe directamente no Player, inimigos, som, etc.).

Fluxo típico de uso (no LevelScene / Game):

  manager = PickupManager(
      level_width=self.bg_width,
      ground_y=altura_do_chao_global_ou_none,
      platforms=self.platforms,
  )

  # a cada frame (dt em segundos!):
  events = manager.update(dt_seconds, player_rect=game.player.rect)

  for ev in events:
      # ev.effect é o dict vindo de pickup.get_effect()
      game.apply_pickup_effect(ev.effect)

  # para desenhar:
  for p in manager.get_pickups():
      data = p.get_draw_data()
      # usar data["x"], data["y"], data["width"], data["height"], data["color"]
      # e desenhar com pg.draw_rect(...) no Game.draw_scene()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Iterable, Dict, Any, Tuple
import random

import config
from entity.pickups import Pickup, PickupKind, spawn_random_pickup


# -----------------------------
# CONSTANTES vindas do config
# -----------------------------

MAX_ACTIVE_PICKUPS = config.PICKUP_MAX_ACTIVE

AUTO_SPAWN_INTERVAL_MIN = config.PICKUP_AUTO_SPAWN_INTERVAL_MIN
AUTO_SPAWN_INTERVAL_MAX = config.PICKUP_AUTO_SPAWN_INTERVAL_MAX


@dataclass
class PickupEffectEvent:
    """
    Evento lógico gerado quando o jogador apanha um pickup.

    O campo 'effect' é exactamente o dicionário devolvido por pickup.get_effect().
    """

    effect: Dict[str, Any]
    kind: str


class PickupManager:
    """
    Gestor de pickups para um nível.

    Responsabilidades:
      - Guardar a lista de pickups vivos.
      - Spawn automático aleatório (opcional).
      - Update (queda tipo paraquedas, lifetime).
      - Detectar colisão com o jogador.
      - Devolver efeitos para o jogo aplicar.

    Não desenha nada, não mexe no Player, nem em som:
      -> isso é tudo responsabilidade do Game / Scenes.
    """

    def __init__(
        self,
        level_width: int,
        ground_y: Optional[float] = None,
        *,
        platforms: Optional[Iterable[object]] = None,
        auto_spawn: bool = True,
        max_active: int = MAX_ACTIVE_PICKUPS,
        spawn_interval_min: float = AUTO_SPAWN_INTERVAL_MIN,
        spawn_interval_max: float = AUTO_SPAWN_INTERVAL_MAX,
        include_kinds: Optional[Iterable[PickupKind]] = None,
        exclude_kinds: Optional[Iterable[PickupKind]] = None,
    ) -> None:
        """
        level_width: largura total do nível (para X aleatório dos pickups).
        ground_y: y global de chão (fallback) se não houver plataforma nesse X.
        platforms: lista de plataformas (pg.Rect ou tuples) para pousar em cima.
        auto_spawn: se True, o manager vai criar pickups sozinho ao longo do tempo.
        max_active: limite de pickups simultâneos.
        spawn_interval_min/max: intervalo aleatório entre spawns, em segundos.
        include_kinds / exclude_kinds: filtros opcionais de tipos de pickup.
        """
        self.level_width = int(level_width)
        self.ground_y = ground_y
        self._platforms = list(platforms) if platforms is not None else None

        self.auto_spawn = bool(auto_spawn)
        self.max_active = int(max_active)
        self.spawn_interval_min = float(spawn_interval_min)
        self.spawn_interval_max = float(spawn_interval_max)

        self._include_kinds = list(include_kinds) if include_kinds is not None else None
        self._exclude_kinds = list(exclude_kinds) if exclude_kinds is not None else None

        self._pickups: List[Pickup] = []
        self._spawn_timer = 0.0
        self._next_spawn_time = self._random_spawn_interval()

    # ------------------------------------------------------------------ #
    # Helpers internos
    # ------------------------------------------------------------------ #

    def _random_spawn_interval(self) -> float:
        """Escolhe um intervalo aleatório entre dois spawns automáticos."""
        if self.spawn_interval_max <= self.spawn_interval_min:
            return max(0.5, self.spawn_interval_min)
        return random.uniform(self.spawn_interval_min, self.spawn_interval_max)

    @staticmethod
    def _rect_to_tuple(rect_like) -> Tuple[int, int, int, int]:
        """
        Converte algo tipo pg.Rect ou (x, y, w, h) num tuple de ints.

        Isto evita depender directamente de pygame/pg_engine.
        """
        if rect_like is None:
            return 0, 0, 0, 0

        # Se tiver atributos típicos de Rect
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

        # Assume (x, y, w, h)
        x, y, w, h = rect_like
        return int(x), int(y), int(w), int(h)

    @staticmethod
    def _rects_overlap(
        a: Tuple[int, int, int, int],
        b: Tuple[int, int, int, int],
    ) -> bool:
        """Teste simples de overlap entre dois rects (ax, ay, aw, ah) e (bx, by, bw, bh)."""
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
    # API pública
    # ------------------------------------------------------------------ #

    def get_pickups(self) -> List[Pickup]:
        """Devolve a lista de pickups actualmente activos (para desenhar, debug, etc.)."""
        return self._pickups

    def clear(self) -> None:
        """Remove todos os pickups (por exemplo, ao recomeçar o nível)."""
        self._pickups.clear()

    def force_spawn(
        self,
        kind: PickupKind,
        x: float,
        y: float,
        *,
        lifetime: float,
    ) -> Pickup:
        """
        Força o spawn de um pickup específico na posição indicada.

        Útil para scripts de nível, recompensas garantidas, etc.
        """
        p = Pickup(
            kind=kind,
            x=x,
            y=y,
            lifetime=lifetime,
            falling=True,
            ground_y=self.ground_y,
        )
        self._pickups.append(p)
        return p

    def spawn_random(self) -> Optional[Pickup]:
        """
        Cria um pickup aleatório a cair de paraquedas, se ainda não atingimos o limite de activos.

        Devolve o pickup criado ou None se não foi possível (limite atingido).
        """
        if len(self._pickups) >= self.max_active:
            return None

        p = spawn_random_pickup(
            level_width=self.level_width,
            ground_y=self.ground_y,
            include=self._include_kinds,
            exclude=self._exclude_kinds,
            platforms=self._platforms,
        )
        self._pickups.append(p)
        return p

    def update(
        self,
        dt_seconds: float,
        player_rect=None,
    ) -> List[PickupEffectEvent]:
        """
        Actualiza o estado do manager.

        dt_seconds: delta time em segundos (importante! não passes milissegundos aqui).
        player_rect: rect do jogador (pg.Rect ou (x, y, w, h)) para teste de colisão.

        Devolve:
          lista de PickupEffectEvent – um por pickup apanhado neste frame.
        """
        effects: List[PickupEffectEvent] = []

        # 1) Spawn automático
        if self.auto_spawn and self.max_active > 0:
            self._spawn_timer += dt_seconds
            if self._spawn_timer >= self._next_spawn_time:
                self._spawn_timer = 0.0
                self._next_spawn_time = self._random_spawn_interval()
                self.spawn_random()

        # 2) Update de todos os pickups
        for p in self._pickups:
            p.update(dt_seconds)

        # 3) Colisão com o player
        if player_rect is not None:
            player_tup = self._rect_to_tuple(player_rect)

            for p in self._pickups:
                if not p.alive:
                    continue

                pickup_tup = p.get_rect_tuple()
                if self._rects_overlap(player_tup, pickup_tup):
                    # Apanhou o pickup
                    effect_dict = p.get_effect()
                    effects.append(
                        PickupEffectEvent(
                            effect=effect_dict,
                            kind=effect_dict.get("type", "unknown"),
                        )
                    )
                    p.mark_collected()

        # 4) Limpar pickups mortos / expirados
        self._pickups = [p for p in self._pickups if p.alive]

        return effects
