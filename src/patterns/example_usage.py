# patterns/example_usage.py
"""
Exemplos práticos de como usar os patterns no jogo.
Pode ser executado para demonstração ou como guia de integração.
"""

# ============================================================================
# EXEMPLO 1: Singleton - SoundManager
# ============================================================================
def example_singleton():
    """Singleton garante uma única instância de SoundManager."""
    from patterns.singleton import SingletonMeta
    
    class SoundManager(metaclass=SingletonMeta):
        def __init__(self):
            self.volume = 1.0
            print(f"[SoundManager] Inicializado: volume={self.volume}")
    
    # Ambas as instâncias são exatamente a mesma
    s1 = SoundManager()
    s2 = SoundManager()
    
    assert s1 is s2, "Singleton falhou!"
    print("✅ Singleton funciona: s1 is s2")


# ============================================================================
# EXEMPLO 2: Command - Input do jogador
# ============================================================================
def example_command():
    """Command encapsula ações e permite undo/redo."""
    from patterns.command import MoveCommand, JumpCommand, CommandInvoker
    
    class MockPlayer:
        def __init__(self):
            self.facing = 1
            self.rect = type('obj', (object,), {'x': 100})()
            self.is_jumping = False
    
    player = MockPlayer()
    invoker = CommandInvoker()
    
    # Executar commands
    invoker.execute(MoveCommand(player, -1))
    print(f"✅ Movimento: facing={player.facing} (esperado -1)")
    
    invoker.execute(JumpCommand(player))
    print(f"✅ Salto: is_jumping={player.is_jumping} (esperado True)")
    
    # Desfazer
    invoker.undo()
    print(f"✅ Undo: is_jumping={player.is_jumping} (esperado False)")


# ============================================================================
# EXEMPLO 3: Observer - Eventos de jogo
# ============================================================================
def example_observer():
    """Observer permite subscri-se a eventos sem acoplamento."""
    from patterns.observer import EventManager
    
    manager = EventManager()
    
    # Listeners (simples funções ou métodos)
    events_received = []
    
    def listener1(data):
        events_received.append(("listener1", data))
    
    def listener2(data):
        events_received.append(("listener2", data))
    
    # Subscrever
    manager.subscribe("enemy_dead", listener1)
    manager.subscribe("enemy_dead", listener2)
    
    # Emitir evento
    manager.emit("enemy_dead", {"points": 100, "x": 50, "y": 60})
    
    assert len(events_received) == 2, "Listeners não foram chamados!"
    print(f"✅ Observer: {len(events_received)} listeners receberam evento")


# ============================================================================
# EXEMPLO 4: State - Estados do jogador
# ============================================================================
def example_state():
    """State torna transições de estado explícitas."""
    from patterns.state import State, StateManager
    
    class IdleState(State):
        def __init__(self):
            super().__init__("idle")
        
        def enter(self, context):
            context.status = "idle"
            print(f"  → Entrando em {self.name}")
        
        def update(self, context, dt):
            # Simular mudança de estado
            if context.action == "move":
                return "running"
            return None
        
        def exit(self, context):
            print(f"  ← Saindo de {self.name}")
    
    class RunningState(State):
        def __init__(self):
            super().__init__("running")
        
        def enter(self, context):
            context.status = "running"
            print(f"  → Entrando em {self.name}")
        
        def update(self, context, dt):
            if context.action == "stop":
                return "idle"
            return None
        
        def exit(self, context):
            print(f"  ← Saindo de {self.name}")
    
    class Context:
        def __init__(self):
            self.status = None
            self.action = None
    
    context = Context()
    manager = StateManager(context, IdleState())
    manager.register_state(RunningState())
    
    # Atualizar com transição
    context.action = "move"
    manager.update(0.016)
    print(f"✅ State: {manager.get_current_state()} (esperado 'running')")


# ============================================================================
# EXEMPLO 5: Flyweight - Cache de sprites
# ============================================================================
def example_flyweight():
    """Flyweight reutiliza objetos immutáveis em cache."""
    from patterns.flyweight import FlyweightFactory
    
    factory = FlyweightFactory()
    
    # Simulamos sprite load
    class MockSprite:
        def __init__(self, path):
            self.path = path
    
    # Redefine o carregamento
    import pg_engine as pg
    original = pg.image_load
    call_count = [0]
    
    def mock_load(path):
        call_count[0] += 1
        return MockSprite(path)
    
    pg.image_load = mock_load
    
    # Primeira chamada: carrega (miss)
    sprite1 = factory.get_sprite("enemy.png")
    
    # Segunda chamada: do cache (hit)
    sprite2 = factory.get_sprite("enemy.png")
    
    # Terceira: nova imagem (miss)
    sprite3 = factory.get_sprite("other.png")
    
    stats = factory.get_stats()
    print(f"✅ Flyweight: {stats['hits']} hits, {stats['misses']} misses")
    print(f"  → Cache size: {factory.get_cache_size()} itens")
    
    pg.image_load = original  # restore


# ============================================================================
# EXEMPLO 6: Prototype - Factory de inimigos
# ============================================================================
def example_prototype():
    """Prototype clona objetos em vez de criar do zero."""
    from patterns.prototype import EnemyPrototype, PrototypeFactory
    
    factory = PrototypeFactory()
    
    # Registar prototypes
    factory.register_enemy(
        "soldier",
        EnemyPrototype("Soldier", "soldier.png", hp=20, damage=5, points=100)
    )
    
    # Criar instâncias (clones)
    instance1 = factory.create_enemy("soldier", 100, 50)
    instance2 = factory.create_enemy("soldier", 200, 50)
    
    assert instance1["x"] == 100, "Prototype falhou!"
    assert instance1 is not instance2, "Não deveriam ser a mesma instância!"
    print(f"✅ Prototype: 2 instâncias criadas corretamente")
    print(f"  → Tipo 1: {instance1['name']} @ ({instance1['x']}, {instance1['y']})")
    print(f"  → Tipo 2: {instance2['name']} @ ({instance2['x']}, {instance2['y']})")


# ============================================================================
# EXEMPLO 7: Object Pool - Reutilização de projectiles
# ============================================================================
def example_object_pool():
    """Object Pool reutiliza objetos em vez de alocar/desalocar."""
    from patterns.object_pool import ObjectPool
    
    class MockProjectile:
        def __init__(self):
            self.x = 0
            self.y = 0
            self.alive = True
        
        def reset(self):
            self.x = 0
            self.y = 0
            self.alive = True
    
    # Criar pool
    pool = ObjectPool(MockProjectile, size=10)
    
    # Adquirir objetos
    proj1 = pool.acquire()
    proj2 = pool.acquire()
    
    proj1.x = 100
    proj2.x = 200
    
    stats_before = pool.get_stats()
    print(f"✅ Object Pool antes: {stats_before['in_use']} em uso")
    
    # Devolver ao pool
    pool.release(proj1)
    pool.release(proj2)
    
    stats_after = pool.get_stats()
    print(f"✅ Object Pool depois: {stats_after['available']} disponíveis")
    
    # Reutilizar
    proj3 = pool.acquire()
    assert proj3 is proj1, "Não reutilizou o objeto!"
    print(f"✅ Objeto reutilizado corretamente")


# ============================================================================
# MAIN - Executar todos os exemplos
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("DEMONSTRAÇÃO DE PROGRAMMING PATTERNS")
    print("=" * 70)
    
    try:
        print("\n[1/7] Singleton - SoundManager")
        example_singleton()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    try:
        print("\n[2/7] Command - Input do jogador")
        example_command()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    try:
        print("\n[3/7] Observer - Eventos de jogo")
        example_observer()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    try:
        print("\n[4/7] State - Estados do jogador")
        example_state()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    try:
        print("\n[5/7] Flyweight - Cache de sprites")
        example_flyweight()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    try:
        print("\n[6/7] Prototype - Factory de inimigos")
        example_prototype()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    try:
        print("\n[7/7] Object Pool - Reutilização de projectiles")
        example_object_pool()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 70)
    print("✅ DEMONSTRAÇÃO COMPLETA")
    print("=" * 70)
