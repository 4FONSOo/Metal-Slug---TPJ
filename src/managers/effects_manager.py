# managers/effects_manager.py
"""
Gestor de efeitos visuais / temporais (FX).

Objectivo:
  - Centralizar efeitos como:
      * flash de ecrã (cheats, NUKE, dano forte)
      * NUKE (flash + slow motion)
      * camera shake
  - Não depende de pygame/pg_engine.
  - Fornece apenas:
      * update(dt_seconds)
      * triggers (flash, nuke, shake)
      * queries do estado (cor de flash, factor de slow-mo, offset de shake, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import random  # para offsets aleatórios do tremor


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


@dataclass
class CameraShakeState:
    time_left: float = 0.0       # segundos restantes de shake
    intensity: float = 0.0       # máximo de píxeis de desvio horizontal
    offset_x: float = 0.0        # deslocamento actual (x)


class EffectsManager:
    """
    Gestor de FX globais.

    O Game/Scene pode usar:
      - trigger_flash(...)
      - trigger_nuke(...)
      - trigger_camera_shake(...)
      - update(dt_seconds)
      - get_screen_tint()
      - get_time_scale()
      - get_camera_shake_offset()
    """

    def __init__(self) -> None:
        self._flash = ScreenFlashState()
        self._nuke = NukeState()
        self._shake = CameraShakeState()  # <- ISTO É O QUE ESTAVA A FALTAR

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
        self._flash.time_left = max(0.0, float(duration))
        self._flash.fade_time = max(0.0, float(fade_time))

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
        self._nuke.time_left = max(0.0, float(total_duration))
        self._nuke.slowmo_factor = float(slowmo_factor)
        self._nuke.slowmo_time_left = max(0.0, float(slowmo_duration))
        self._nuke.flash_color = flash_color

        # Sincronizar com o flash
        self.trigger_flash(
            color=flash_color,
            duration=self._nuke.time_left,
            fade_time=self._nuke.time_left,
        )

    def trigger_camera_shake(self, duration: float, intensity: float = 6.0) -> None:
        """
        Activa/renova um efeito de tremor de câmara.

        duration  → segundos
        intensity → nº máximo de píxeis de deslocamento horizontal
        """
        try:
            duration_f = float(duration)
            intensity_f = float(intensity)
        except Exception:
            return

        if duration_f <= 0.0 or intensity_f <= 0.0:
            return

        # Se já houver shake activo, fica com o mais longo/forte
        self._shake.time_left = max(self._shake.time_left, duration_f)
        self._shake.intensity = max(self._shake.intensity, intensity_f)

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float) -> None:
        """Actualiza timers de FX (flash, NUKE, slow-motion, shake, etc.)."""
        try:
            dt = float(dt_seconds)
        except Exception:
            dt = 0.0

        if dt <= 0.0:
            # Mesmo com dt=0, convém garantir estados coerentes
            if self._flash.time_left <= 0.0:
                self._flash.intensity = 0.0
            if self._shake.time_left <= 0.0:
                self._shake.offset_x = 0.0
            return

        # --- Flash ---
        if self._flash.time_left > 0.0:
            self._flash.time_left -= dt
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

        # --- NUKE / slow-motion ---
        if self._nuke.active:
            self._nuke.time_left -= dt
            if self._nuke.time_left <= 0.0:
                self._nuke.active = False
                self._nuke.time_left = 0.0

            if self._nuke.slowmo_time_left > 0.0:
                self._nuke.slowmo_time_left -= dt
                if self._nuke.slowmo_time_left <= 0.0:
                    self._nuke.slowmo_time_left = 0.0

        # --- Camera shake ---
        if self._shake.time_left > 0.0 and self._shake.intensity > 0.0:
            self._shake.time_left -= dt
            if self._shake.time_left <= 0.0:
                self._shake.time_left = 0.0
                self._shake.offset_x = 0.0
            else:
                max_off = int(self._shake.intensity)
                if max_off > 0:
                    self._shake.offset_x = random.randint(-max_off, max_off)
                else:
                    self._shake.offset_x = 0.0
        else:
            self._shake.time_left = 0.0
            self._shake.offset_x = 0.0

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

    def get_camera_shake_offset(self) -> float:
        """
        Deslocamento horizontal actual do tremor de câmara (pode ser 0.0).
        """
        return self._shake.offset_x
