# patterns/singleton.py
"""
Singleton Pattern - Garante instância única de uma classe, uma só vez.

Usado para:
- SoundManager (uma única instância de mixer)
- ScoreManager (um único estado de pontuações)
"""

from typing import Dict, Type, Any


class SingletonMeta(type):
    """
    Metaclass que implementa Singleton de forma thread-safe.
    
    Uso:
        class SoundManager(metaclass=SingletonMeta):
            def __init__(self):
                self.volume = 1.0
        
        s1 = SoundManager()
        s2 = SoundManager()
        assert s1 is s2  # mesma instância
    """
    
    _instances: Dict[Type, Any] = {}
    
    def __call__(cls, *args, **kwargs):
        """Retorna instância existente ou cria uma nova (apenas 1)."""
        if cls not in cls._instances:
            instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    
    @classmethod
    def clear(mcs):
        """Reset para testes."""
        mcs._instances.clear()
