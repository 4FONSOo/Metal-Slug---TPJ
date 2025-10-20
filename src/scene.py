# scene.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame

# Previne circular import (Game precisa de Scene, Scene precisa de Game)
if TYPE_CHECKING:
    from game_state import Game

# Padrão: Template Method (define a estrutura) e State (interface do estado)
class Scene(ABC):
    """
    Classe base abstrata para todas as Cenas do jogo (Menus, Níveis, etc.).
    """
    def __init__(self, game_context: 'Game'):
        # Referência ao Game Manager para transição de cenas
        self.game_context = game_context 

    @abstractmethod
    def handle_input(self, events: list[pygame.event.Event]):
        """Processa a entrada do utilizador (teclas, rato)."""
        pass

    @abstractmethod
    def update(self, dt: float):
        """Atualiza a lógica da cena (dt é o tempo delta)."""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """Desenha a cena no ecrã."""
        pass
    
    def on_enter(self):
        """Chamado quando a cena é ativada. Útil para carregar recursos específicos."""
        pass
        
    def on_exit(self):
        """Chamado quando a cena está a ser desativada. Útil para limpar recursos."""
        pass