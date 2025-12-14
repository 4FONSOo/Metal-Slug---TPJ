# patterns/__init__.py
"""
Implementação elegante de Programming Patterns para o jogo Metal Slug.
Apenas patterns que fazem sentido real para este projeto.

Patterns implementados:
- Singleton: SoundManager, ScoreManager
- Command: Sistema de input/ações
- Observer: Sistema de eventos (EnemyDead, PickupCollected, etc)
- State: Estados do jogador (Idle, Running, Jumping)
- Flyweight: Cache de sprites
- Prototype: Factory de inimigos
- Object Pool: Reutilização de projécteis
"""

from .singleton import SingletonMeta
from .command import Command, CommandInvoker
from .observer import EventManager, EventListener
from .state import StateManager, State
from .flyweight import FlyweightFactory
from .prototype import PrototypeFactory
from .object_pool import ObjectPool

__all__ = [
    "SingletonMeta",
    "Command",
    "CommandInvoker",
    "EventManager",
    "EventListener",
    "StateManager",
    "State",
    "FlyweightFactory",
    "PrototypeFactory",
    "ObjectPool",
]
