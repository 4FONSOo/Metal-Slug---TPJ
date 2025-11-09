# scene.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame

# Previne circular import (Game precisa de Scene, Scene precisa de Game)
if TYPE_CHECKING:
    from game_state import Game

# Padrão: Template Method (define a estrutura) e State (interface do estado)
class Scene(ABC):

    def __init__(self, game_context: 'Game'):
        # Referência ao Game Manager para transição de cenas
        self.game_context = game_context 

    @abstractmethod
    def handle_input(self, events: list[pygame.event.Event]):
        pass

    @abstractmethod
    def update(self, dt: float):
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        pass
    
    def on_enter(self):
        pass
        
    def on_exit(self):
        pass