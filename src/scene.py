# scene.py
"""
Base para todas as cenas do jogo (menu, nível, créditos, etc.).

Isto por si só não faz nada – é a "interface".
O Game fala só com Scene, não quer saber se é menu, nível, ou ecrã de game over.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

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

    E pode opcionalmente sobrepor:
      - on_enter / on_exit
        (inicialização / limpeza específica da cena)
    """

    def __init__(self, game: "Game") -> None:
        # Referência ao "motor" principal (Game)
        self.game = game

    # ------------------------------ #
    # Ciclo principal da cena
    # ------------------------------ #
    @abstractmethod
    def handle_input(self, events: List[pg.Event]) -> None:
        """Tratar dos eventos de input desta cena."""
        raise NotImplementedError

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Actualizar lógica da cena.

        dt vem em milissegundos (valor do clock do Game).
        """
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen: pg.Surface) -> None:
        """Desenhar a cena no ecrã."""
        raise NotImplementedError

    # ------------------------------ #
    # Hooks de ciclo de vida
    # ------------------------------ #
    def on_enter(self) -> None:
        """
        Chamado quando a cena passa a ser a cena activa.

        Útil para:
          - carregar recursos específicos
          - arrancar música
          - reset de timers locais
        """
        pass

    def on_exit(self) -> None:
        """
        Chamado antes de sair desta cena.

        Útil para:
          - parar música
          - libertar recursos temporários
          - guardar estado
        """
        pass
