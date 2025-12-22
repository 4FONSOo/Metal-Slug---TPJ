# patterns/object_pool.py
"""
Object Pool Pattern - Reutilização de objetos para evitar alocação/desalocação contínua.

Usado para:
- Projectiles: Reutilizar instâncias em vez de criar/apagar a cada tiro
- Granadas: Pool de granadas para reutilizar

Vantagens:
- Reduz garbage collection (menos alocações)
- Melhor performance (objetos reutilizáveis)
- Previsível (sem picos de GC)
"""

from typing import List, Optional, Generic, TypeVar


T = TypeVar('T')


class ObjectPool(Generic[T]):
    """
    Pool genérico de objetos reutilizáveis.
    
    Uso:
        pool = ObjectPool(Projectile, size=100)
        proj = pool.acquire()
        proj.reset(x=100, y=100, vx=1, vy=0)
        # ... usar projectile
        pool.release(proj)
    """
    
    def __init__(self, object_class: type, size: int = 50, factory=None):
        self.object_class = object_class
        self.size = size
        self.factory = factory
        self._available: List[T] = []
        self._in_use: List[T] = []
        
        # Pre-aloca objetos
        for _ in range(size):
            obj = self._create_object()
            self._available.append(obj)
    
    def _create_object(self) -> T:
        """Cria uma nova instância do objeto."""
        if self.factory:
            return self.factory()
        else:
            return self.object_class()
    
    def acquire(self) -> T:
        """Adquire um objeto do pool."""
        if self._available:
            obj = self._available.pop()
        else:
            # Se não há disponível, cria um novo
            obj = self._create_object()
        
        self._in_use.append(obj)
        return obj
    
    def release(self, obj: T) -> None:
        """Devolve um objeto ao pool."""
        if obj in self._in_use:
            self._in_use.remove(obj)
        
        # Opcionalmente, reseta o objeto se ele tiver método reset
        if hasattr(obj, 'reset'):
            try:
                obj.reset()
            except Exception:
                pass
        
        if len(self._available) < self.size:
            self._available.append(obj)
        # Senão, descarta (GC vai lidar)
    
    def release_all(self) -> None:
        """Devolve todos os objetos em uso ao pool."""
        for obj in self._in_use[:]:
            self.release(obj)
    
    def clear(self) -> None:
        """Limpa todo o pool."""
        self._available.clear()
        self._in_use.clear()
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do pool."""
        return {
            "available": len(self._available),
            "in_use": len(self._in_use),
            "total_capacity": self.size,
        }
    
    def resize(self, new_size: int) -> None:
        """Redimensiona o pool."""
        if new_size > self.size:
            # Adiciona novos objetos
            for _ in range(new_size - self.size):
                self._available.append(self._create_object())
        elif new_size < self.size:
            # Remove objetos disponíveis
            to_remove = self.size - new_size
            while to_remove > 0 and self._available:
                self._available.pop()
                to_remove -= 1
        
        self.size = new_size


class ProjectilePool(ObjectPool):
    """Pool especializado para projectiles."""
    
    def __init__(self, projectile_class: type, size: int = 200):
        super().__init__(projectile_class, size)
        self._active: List[T] = []  # Projectiles em uso e "vivos"
    
    def update(self, dt: float) -> List[T]:
        """
        Atualiza todos os projectiles ativos e retorna os que morreram.
        
        Uso:
            dead_projectiles = pool.update(dt)
            for proj in dead_projectiles:
                pool.release(proj)
        """
        dead = []
        
        for proj in self._active[:]:
            if hasattr(proj, 'update'):
                proj.update(dt)
            
            # Verifica se projectile morreu
            if not getattr(proj, 'alive', True):
                dead.append(proj)
                self._active.remove(proj)
        
        return dead
    
    def add_active(self, proj: T) -> None:
        """Marca um projectile como ativo."""
        if proj not in self._active:
            self._active.append(proj)
    
    def get_active(self) -> List[T]:
        """Retorna lista de projectiles ativos."""
        return self._active.copy()
