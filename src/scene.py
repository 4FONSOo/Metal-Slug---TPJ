# scene.py
"""
Base para todas as cenas do jogo (menu, nível, créditos, etc.).

Isto por si só não faz nada – é a "interface".
O Game fala só com Scene, não quer saber se é menu, nível, ou ecrã de game over.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pg_engine as pg  # só para tipos (Surface), nada de pygame directo

if TYPE_CHECKING:
    from game_state import Game


class Scene(ABC):
    """
    Classe base para cenas.

    Cada cena deve implementar:
      - handle_input(events)
      - update(dt)
      - draw(screen)
    E opcionalmente:
      - on_enter / on_exit
    """

    def __init__(self, game: "Game"):
        # Referência ao "motor" principal (Game)
        self.game = game

    @abstractmethod
    def handle_input(self, events: list):
        """Tratar dos eventos de input desta cena."""
        raise NotImplementedError

    @abstractmethod
    def update(self, dt: float):
        """Actualizar lógica da cena. dt em milissegundos."""
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen: pg.Surface):
        """Desenhar a cena no ecrã."""
        raise NotImplementedError

    def on_enter(self):
        """Chamado quando a cena passa a ser a cena activa."""
        pass

    def on_exit(self):
        """Chamado antes de sair desta cena."""
        pass
