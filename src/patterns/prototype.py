# patterns/prototype.py
"""
Prototype Pattern - Clonagem de objetos como alternativa a factories complexas.

Usado para:
- EnemyPrototype: Clona um inimigo "template" em vez de criar do zero
- ConfigurationPrototype: Clona configs de dificuldade

Vantagens:
- Mais flexível que factory
- Fácil criar variantes (clone + modificação)
- Melhor performance (não precisa reinterpretar dados)
"""

from copy import deepcopy
from typing import Dict, Any, Optional


class Prototype:
    """Base para objetos que podem ser clonados."""
    
    def clone(self) -> 'Prototype':
        """Retorna uma cópia profunda deste objeto."""
        return deepcopy(self)
    
    def clone_and_update(self, **kwargs) -> 'Prototype':
        """Clona e depois atualiza atributos específicos."""
        obj = self.clone()
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        return obj


class EnemyPrototype:
    """Template de inimigo que pode ser clonado."""
    
    def __init__(self, name: str, sprite_path: str, hp: int, damage: int, points: int):
        self.name = name
        self.sprite_path = sprite_path
        self.hp = hp
        self.damage = damage
        self.points = points
        self.speed = 1.0
        self.patrol_range = 100
    
    def clone(self) -> 'EnemyPrototype':
        """Clona este prototype."""
        return deepcopy(self)
    
    def create_instance(self, x: float, y: float) -> Dict[str, Any]:
        """Cria uma instância concreta baseada neste prototype."""
        return {
            "name": self.name,
            "sprite_path": self.sprite_path,
            "x": x,
            "y": y,
            "hp": self.hp,
            "damage": self.damage,
            "points": self.points,
            "speed": self.speed,
            "patrol_range": self.patrol_range,
        }


class PrototypeRegistry:
    """Registo centralizado de prototypes."""
    
    def __init__(self):
        self._prototypes: Dict[str, Prototype] = {}
    
    def register(self, key: str, prototype: Prototype) -> None:
        """Regista um prototype."""
        self._prototypes[key] = prototype
    
    def create(self, key: str) -> Optional[Prototype]:
        """Cria um clone de um prototype registado."""
        if key in self._prototypes:
            return self._prototypes[key].clone()
        return None
    
    def create_and_modify(self, key: str, **kwargs) -> Optional[Prototype]:
        """Cria um clone e modifica seus atributos."""
        if key in self._prototypes:
            return self._prototypes[key].clone_and_update(**kwargs)
        return None
    
    def list_keys(self) -> list[str]:
        """Lista todos os prototypes registados."""
        return list(self._prototypes.keys())


class PrototypeFactory:
    """
    Factory que usa prototypes para criar objetos complexos.
    
    Uso:
        factory = PrototypeFactory()
        factory.register_enemy("soldier", EnemyPrototype("Soldier", "soldier.png", 10, 5, 50))
        
        instance = factory.create_enemy("soldier", 100, 200)
    """
    
    def __init__(self):
        self.enemy_registry = PrototypeRegistry()
        self.config_registry = PrototypeRegistry()
    
    def register_enemy(self, key: str, prototype: EnemyPrototype) -> None:
        """Regista um prototype de inimigo."""
        self.enemy_registry.register(key, prototype)
    
    def create_enemy(self, key: str, x: float, y: float) -> Optional[Dict[str, Any]]:
        """Cria uma instância de inimigo baseada no prototype."""
        if key in self.enemy_registry._prototypes:
            proto = self.enemy_registry._prototypes[key]
            return proto.create_instance(x, y)
        return None
    
    def list_enemy_types(self) -> list[str]:
        """Lista todos os tipos de inimigo disponíveis."""
        return self.enemy_registry.list_keys()


# Factory global singleton
_global_factory: Optional[PrototypeFactory] = None


def get_global_prototype_factory() -> PrototypeFactory:
    """Retorna a factory global de prototypes."""
    global _global_factory
    if _global_factory is None:
        _global_factory = PrototypeFactory()
    return _global_factory
