# scene_manager.py
"""
SceneManager

Responsável por:
  - Guardar a cena actual
  - Tratar da troca de cenas (on_exit / on_enter)
  - Encaminhar handle_input / update / draw para a cena activa
"""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING

import pg_engine as pg

from scene import Scene

if TYPE_CHECKING:
    from game_state import Game


class SceneManager:
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.current_scene: Optional[Scene] = None

    # ------------------------------ #
    # Gestão da cena actual
    # ------------------------------ #
    def change_scene(self, new_scene: Scene) -> None:
        """
        Troca imediata da cena actual, chamando on_exit/on_enter.
        """
        if self.current_scene is not None:
            try:
                self.current_scene.on_exit()
            except Exception:
                pass

        self.current_scene = new_scene

        try:
            self.current_scene.on_enter()
        except Exception:
            pass

    # ------------------------------ #
    # Encaminhamento para a cena activa
    # ------------------------------ #
    def handle_input(self, events: List[pg.Event]) -> None:
        if self.current_scene is not None:
            self.current_scene.handle_input(events)

    def update(self, dt: float) -> None:
        if self.current_scene is not None:
            self.current_scene.update(dt)

    def draw(self, screen: pg.Surface) -> None:
        if self.current_scene is not None:
            self.current_scene.draw(screen)
