# patterns/flyweight.py
"""
Flyweight Pattern - Cache compartilhada de objetos.

Usado para:
- Cache de sprites (mesma imagem em múltiplos inimigos)
- Fontes (mesma fonte em múltiplos texts)
- Dados de configuração (EnemyType, etc)

Vantagens:
- Reduz uso de memória (não duplica sprites)
- Mais rápido (não carrega mesma imagem N vezes)
- Melhor performance em geral
"""

from typing import Dict, Any, Tuple


class Flyweight:
    """Base para um objeto flyweight (imutável em memória)."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Acede a um atributo do flyweight."""
        return self.data.get(key, default)


class FlyweightFactory:
    """
    Factory que mantém cache de flyweights.
    
    Uso:
        factory = FlyweightFactory()
        sprite1 = factory.get_sprite("enemy.png")
        sprite2 = factory.get_sprite("enemy.png")
        assert sprite1 is sprite2  # mesma instância em memória
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._stats = {"hits": 0, "misses": 0}
    
    def get_sprite(self, filepath: str) -> Any:
        """
        Retorna sprite (imagem) do cache.
        Carrega se não existir.
        """
        if filepath in self._cache:
            self._stats["hits"] += 1
            return self._cache[filepath]
        
        # Carrega imagem (função interna)
        try:
            import pg_engine as pg
            loader = getattr(pg, "_raw_load_image", None) or pg.load_image
            img = loader(filepath)
            self._cache[filepath] = img
            self._stats["misses"] += 1
            return img
        except Exception as e:
            print(f"[FlyweightFactory] Erro ao carregar {filepath}: {e}")
            return None

    def get_scaled_sprite(self, filepath: str, size: Tuple[int, int]) -> Any:
        """Retorna sprite escalada (com cache por filepath+size)."""
        w, h = int(size[0]), int(size[1])
        key = f"{filepath}|{w}x{h}"

        if key in self._cache:
            self._stats["hits"] += 1
            return self._cache[key]

        base = self.get_sprite(filepath)
        if base is None:
            return None

        try:
            import pg_engine as pg
            scaled = pg.scale_image(base, (w, h))
            self._cache[key] = scaled
            self._stats["misses"] += 1
            return scaled
        except Exception as e:
            print(f"[FlyweightFactory] Erro ao escalar {filepath} ({w}x{h}): {e}")
            return base
    
    def get_font(self, font_name: str, size: int) -> Any:
        """Retorna fonte do cache."""
        key = f"{font_name}_{size}"
        
        if key in self._cache:
            self._stats["hits"] += 1
            return self._cache[key]
        
        try:
            import pg_engine as pg
            creator = getattr(pg, "_raw_create_font", None) or pg.create_font
            font = creator(font_name, int(size))
            self._cache[key] = font
            self._stats["misses"] += 1
            return font
        except Exception as e:
            print(f"[FlyweightFactory] Erro ao criar fonte {font_name}:{size}: {e}")
            return None
    
    def get_config(self, config_key: str, config_dict: Dict[str, Any]) -> Flyweight:
        """Retorna um flyweight de configuração."""
        if config_key in self._cache:
            self._stats["hits"] += 1
            return self._cache[config_key]
        
        if config_key not in config_dict:
            return None
        
        fw = Flyweight(config_dict[config_key])
        self._cache[config_key] = fw
        self._stats["misses"] += 1
        return fw
    
    def clear(self) -> None:
        """Limpa cache."""
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0}
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de cache hit/miss."""
        return self._stats.copy()
    
    def get_cache_size(self) -> int:
        """Retorna número de itens em cache."""
        return len(self._cache)


# Factory global singleton
_global_factory: FlyweightFactory | None = None


def get_global_flyweight_factory() -> FlyweightFactory:
    """Retorna a factory global de flyweights."""
    global _global_factory
    if _global_factory is None:
        _global_factory = FlyweightFactory()
    return _global_factory
