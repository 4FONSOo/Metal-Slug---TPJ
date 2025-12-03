# effects_manager.py
"""
Gestor de efeitos visuais / temporais (FX).

Objectivo:
  - Centralizar efeitos como:
      * flash de ecrã (cheats, NUKE, dano forte)
      * NUKE (flash + slow motion)
      * futuramente: camera shake, etc.
  - Não depende de pygame/pg_engine.
  - Fornece apenas:
      * update(dt)
      * query do estado (cor de flash, factor de slow-mo, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


Color = Tuple[int, int, int]


@dataclass
class ScreenFlashState:
    color: Color = (255, 255, 255)
    intensity: float = 0.0       # 0..1
    time_left: float = 0.0       # segundos
    fade_time: float = 0.0       # segundos de fade após o pico


@dataclass
class NukeState:
    active: bool = False
    time_left: float = 0.0       # duração total do efeito NUKE
    slowmo_factor: float = 1.0   # factor de slow motion (ex: 0.3)
    slowmo_time_left: float = 0.0
    flash_color: Color = (255, 255, 255)


class EffectsManager:
    """
    Gestor de FX globais.

    O Game/Scene pode usar:
      - trigger_flash(...)
      - trigger_nuke(...)
      - update(dt_seconds)
      - get_screen_tint()
      - get_time_scale()
    """

    def __init__(self) -> None:
        self._flash = ScreenFlashState()
        self._nuke = NukeState()

    # ------------------------------------------------------------------ #
    # Triggers
    # ------------------------------------------------------------------ #

    def trigger_flash(
        self,
        color: Color,
        duration: float,
        fade_time: float = 0.0,
    ) -> None:
        """Flash simples de ecrã (cheats, hits fortes, etc.)."""
        self._flash.color = color
        self._flash.intensity = 1.0
        self._flash.time_left = duration
        self._flash.fade_time = fade_time

    def trigger_nuke(
        self,
        *,
        total_duration: float,
        flash_color: Color,
        slowmo_factor: float,
        slowmo_duration: float,
    ) -> None:
        """
        Activa efeito tipo NUKE:
          - Flash forte
          - Slow-motion durante alguns segundos
        """
        self._nuke.active = True
        self._nuke.time_left = total_duration
        self._nuke.slowmo_factor = slowmo_factor
        self._nuke.slowmo_time_left = slowmo_duration
        self._nuke.flash_color = flash_color

        # Sincronizar com o flash
        self.trigger_flash(color=flash_color, duration=total_duration, fade_time=total_duration)

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float) -> None:
        """Actualiza timers de FX (flash, NUKE, slow-motion, etc.)."""
        # Flash
        if self._flash.time_left > 0.0:
            self._flash.time_left -= dt_seconds
            if self._flash.time_left <= 0.0:
                self._flash.time_left = 0.0
                self._flash.intensity = 0.0
            elif self._flash.fade_time > 0.0:
                # intensidade decresce linearmente no fade
                t = max(0.0, self._flash.time_left / self._flash.fade_time)
                self._flash.intensity = min(1.0, t)
            else:
                self._flash.intensity = 1.0
        else:
            self._flash.intensity = 0.0

        # NUKE
        if self._nuke.active:
            self._nuke.time_left -= dt_seconds
            if self._nuke.time_left <= 0.0:
                self._nuke.active = False
                self._nuke.time_left = 0.0

            if self._nuke.slowmo_time_left > 0.0:
                self._nuke.slowmo_time_left -= dt_seconds
                if self._nuke.slowmo_time_left <= 0.0:
                    self._nuke.slowmo_time_left = 0.0

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #

    def get_screen_tint(self) -> Optional[Tuple[Color, float]]:
        """
        Devolve (cor, intensidade) do flash actual, ou None se não houver flash.

        Intensidade: 0..1
        """
        if self._flash.intensity <= 0.0:
            return None
        return self._flash.color, self._flash.intensity

    def get_time_scale(self) -> float:
        """
        Devolve o factor de escala do tempo:

          - 1.0  → normal
          - <1.0 → slow motion
        """
        if self._nuke.active and self._nuke.slowmo_time_left > 0.0:
            return max(0.1, self._nuke.slowmo_factor)
        return 1.0

    def is_nuke_active(self) -> bool:
        return self._nuke.active
