# effects_manager.py

from dataclasses import dataclass
from typing import Optional, Tuple
import random


Color = Tuple[int, int, int]


@dataclass
class ScreenFlashState:
    color: Color = (255, 255, 255)
    intensity: float = 0.0       
    time_left: float = 0.0       
    fade_time: float = 0.0       


@dataclass
class NukeState:
    active: bool = False
    time_left: float = 0.0       
    slowmo_factor: float = 1.0   
    slowmo_time_left: float = 0.0
    flash_color: Color = (255, 255, 255)


@dataclass
class ShakeState:
    time_left: float = 0.0       
    intensity: float = 0.0       
    offset_x: float = 0.0        


class EffectsManager:

    def __init__(self) -> None:
        self._flash = ScreenFlashState()
        self._nuke = NukeState()
        self._shake = ShakeState()

    # ------------------------------------------------------------------ #
    # Triggers
    # ------------------------------------------------------------------ #

    def trigger_flash(
        self,
        color: Color,
        duration: float,
        fade_time: float = 0.0,
    ) -> None:
        
        try:
            duration = float(duration)
            fade_time = float(fade_time)
        except Exception:
            return

        if duration <= 0.0:
            return

        self._flash.color = color
        self._flash.intensity = 1.0
        self._flash.time_left = duration
        self._flash.fade_time = max(0.0, fade_time)

    def trigger_nuke(
        self,
        *,
        total_duration: float,
        flash_color: Color,
        slowmo_factor: float,
        slowmo_duration: float,
    ) -> None:
        
        try:
            total_duration = float(total_duration)
            slowmo_factor = float(slowmo_factor)
            slowmo_duration = float(slowmo_duration)
        except Exception:
            return

        if total_duration <= 0.0:
            return

        self._nuke.active = True
        self._nuke.time_left = total_duration
        self._nuke.slowmo_factor = slowmo_factor
        self._nuke.slowmo_time_left = max(0.0, slowmo_duration)
        self._nuke.flash_color = flash_color

        # Sincronizar com o flash
        self.trigger_flash(
            color=flash_color,
            duration=total_duration,
            fade_time=total_duration,
        )

    def trigger_camera_shake(self, duration: float, intensity: float = 6.0) -> None:

        try:
            duration = float(duration)
            intensity = float(intensity)
        except Exception:
            return

        if duration <= 0.0 or intensity <= 0.0:
            return

        self._shake.time_left = max(self._shake.time_left, duration)
        self._shake.intensity = max(self._shake.intensity, intensity)

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float) -> None:
        
        try:
            dt = float(dt_seconds)
        except Exception:
            dt = 0.0

        if dt <= 0.0:
            # Clean after nuke
            if self._flash.time_left <= 0.0:
                self._flash.intensity = 0.0
            if self._shake.time_left <= 0.0:
                self._shake.offset_x = 0.0
            return

        # Flash
        if self._flash.time_left > 0.0:
            self._flash.time_left -= dt
            if self._flash.time_left <= 0.0:
                self._flash.time_left = 0.0
                self._flash.intensity = 0.0
            elif self._flash.fade_time > 0.0:
                
                t = max(0.0, self._flash.time_left / self._flash.fade_time)
                self._flash.intensity = min(1.0, t)
            else:
                self._flash.intensity = 1.0
        else:
            self._flash.intensity = 0.0

        # NUKE
        if self._nuke.active:
            self._nuke.time_left -= dt
            if self._nuke.time_left <= 0.0:
                self._nuke.active = False
                self._nuke.time_left = 0.0

            if self._nuke.slowmo_time_left > 0.0:
                self._nuke.slowmo_time_left -= dt
                if self._nuke.slowmo_time_left <= 0.0:
                    self._nuke.slowmo_time_left = 0.0

        # Camera shake
        if self._shake.time_left > 0.0 and self._shake.intensity > 0.0:
            self._shake.time_left -= dt
            if self._shake.time_left <= 0.0:
                self._shake.time_left = 0.0
                self._shake.intensity = 0.0
                self._shake.offset_x = 0.0
            else:
                max_off = int(self._shake.intensity)
                if max_off > 0:
                    self._shake.offset_x = random.randint(-max_off, max_off)
                else:
                    self._shake.offset_x = 0.0
        else:
            self._shake.offset_x = 0.0

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #

    def get_screen_tint(self) -> Optional[Tuple[Color, float]]:

        if self._flash.intensity <= 0.0:
            return None
        return self._flash.color, self._flash.intensity

    def get_time_scale(self) -> float:
        if self._nuke.active and self._nuke.slowmo_time_left > 0.0:
            return max(0.1, self._nuke.slowmo_factor)
        return 1.0

    def is_nuke_active(self) -> bool:
        return self._nuke.active

    def get_camera_shake_offset(self) -> float:

        return float(self._shake.offset_x)
