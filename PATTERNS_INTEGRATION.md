# PATTERNS_INTEGRATION.md
# Integração de Programming Patterns no Metal Slug

## Resumo

Este documento mostra como integrar os 7 patterns implementados no código existente do jogo, **SEM quebrar nada do que já funciona**.

## Patterns Implementados

1. **Singleton** - SoundManager e ScoreManager (instância única)
2. **Command** - Input do jogador (Move, Jump, Shoot)
3. **Observer** - Eventos de jogo (EnemyDead, PickupCollected, etc)
4. **State** - Estados do jogador (Idle, Running, Jumping)
5. **Flyweight** - Cache de sprites e fontes
6. **Prototype** - Factory de inimigos baseada em clonagem
7. **Object Pool** - Reutilização de projectiles

---

## 1. Singleton (SoundManager)

**Situação atual:** SoundManager é instanciado em `Game.__init__`

**Melhoria:**
```python
# sound.py - NO TOPO do ficheiro
from patterns.singleton import SingletonMeta

class SoundManager(metaclass=SingletonMeta):
    def __init__(self):
        # ... resto do código igual
        self.enabled = False
        # ...
```

**Uso:**
```python
# Em qualquer lugar do código:
sound = SoundManager()  # Sempre a MESMA instância
sound.play_sfx("tiro1.mp3")
```

**Compatibilidade:** ✅ 100% - apenas adiciona garantia de instância única

---

## 2. Command (Input do Jogador)

**Situação atual:** Input processado diretamente em `game.py` / `player.py`

**Melhoria - Exemplo integração básica:**
```python
# Em game.py - handle_combat() pode usar Command pattern:

from patterns.command import CommandInvoker, MoveCommand, JumpCommand

class Game:
    def __init__(self):
        # ... código existente
        self.command_invoker = CommandInvoker()
    
    def handle_player_input(self):
        keys = pg.get_keys()
        
        if keys[pg.K_LEFT]:
            cmd = MoveCommand(self.player, -1)
            self.command_invoker.execute(cmd)
        
        if keys[pg.K_RIGHT]:
            cmd = MoveCommand(self.player, 1)
            self.command_invoker.execute(cmd)
        
        if keys[pg.K_UP]:  # salto
            cmd = JumpCommand(self.player)
            self.command_invoker.execute(cmd)
```

**Compatibilidade:** ✅ Incremental - pode adicionar gradualmente

---

## 3. Observer (Eventos de Jogo)

**Situação atual:** Lógica espalhada por todo o código

**Melhoria:**
```python
# Em game.py - no __init__:

from patterns.observer import EventManager, ScoreObserver, SoundObserver

class Game:
    def __init__(self):
        # ... código existente
        self.event_manager = EventManager()
        
        # Subscreve observers
        score_obs = ScoreObserver(self)
        sound_obs = SoundObserver(self.sound)
        
        self.event_manager.subscribe("enemy_dead", score_obs.on_event)
        self.event_manager.subscribe("enemy_dead", sound_obs.on_event)
        self.event_manager.subscribe("pickup_collected", score_obs.on_event)
```

**Uso quando inimigo morre:**
```python
# Em game.py - handle_collisions():
if not enemy.alive:
    self.event_manager.emit("enemy_dead", {
        "enemy": enemy,
        "points": getattr(enemy, "points", 100),
        "x": enemy.rect.centerx,
        "y": enemy.rect.top,
    })
```

**Compatibilidade:** ✅ Complementar - melhora sem quebrar código existente

---

## 4. State (Estados do Jogador)

**Situação atual:** Estados geridos com flags (`is_jumping`, `leg_state`)

**Melhoria:**
```python
# Em entity/player.py - __init__:

from patterns.state import StateManager, PlayerIdleState, PlayerRunningState, PlayerJumpingState

class Player:
    def __init__(self, x, y, character: str = "player1", ...):
        # ... código existente
        
        # Criar state machine
        idle_state = PlayerIdleState()
        running_state = PlayerRunningState()
        jumping_state = PlayerJumpingState()
        
        self.state_manager = StateManager(self, idle_state)
        self.state_manager.register_state(running_state)
        self.state_manager.register_state(jumping_state)
    
    def update_animation(self, dt_ms: int):
        # Adiciona update do state machine
        self.state_manager.update(dt_ms / 1000.0)
        
        # ... resto do código de animação
```

**Compatibilidade:** ✅ Compatível - refatora internamente, API idêntica

---

## 5. Flyweight (Cache de Sprites)

**Situação atual:** `load_enemy()` e `load_player_sprites()` carregam imagens directamente

**Melhoria:**
```python
# Em resource.py:

from patterns.flyweight import get_global_flyweight_factory

factory = get_global_flyweight_factory()

def load_enemy(width, height, filename):
    """Carrega sprite com Flyweight cache."""
    path = find_asset(filename)
    # Tenta do cache primeiro
    sprite = factory.get_sprite(path)
    if sprite:
        return sprite
    # ... fallback se cache falhar
    return pg.scale_image(img, (width, height))
```

**Compatibilidade:** ✅ Transparente - apenas adiciona cache

---

## 6. Prototype (Factory de Inimigos)

**Situação atual:** Factory inline em `Game.start_game()`

**Melhoria:**
```python
# Em game.py - start_game():

from patterns.prototype import PrototypeFactory, EnemyPrototype

class Game:
    def start_game(self):
        # ... código existente
        
        # Registar enemy prototypes
        factory = PrototypeFactory()
        
        factory.register_enemy(
            "soldier",
            EnemyPrototype("Soldier", "Rebel1.png", hp=20, damage=5, points=100)
        )
        factory.register_enemy(
            "shooter",
            EnemyPrototype("Shooter", "Rebel2.png", hp=30, damage=10, points=150)
        )
        
        self.enemy_prototype_factory = factory
        
        # Usar em enemy_manager...
```

**Compatibilidade:** ✅ Opcional - melhora sem quebrar

---

## 7. Object Pool (Projectiles)

**Situação atual:** Projectiles criados/deletados dinamicamente

**Melhoria:**
```python
# Em game.py - start_game():

from patterns.object_pool import ProjectilePool

class Game:
    def start_game(self):
        # ... código existente
        
        # Criar pool de projectiles
        self.projectile_pool = ProjectilePool(Projectile, size=200)
```

**Uso:**
```python
# Em handle_combat() - quando dispara:
for i in range(bullets_to_fire):
    # Em vez de: proj = Projectile(...)
    proj = self.projectile_pool.acquire()
    proj.reset(sx, sy, aim.x, aim.y, max_range=self.bg_width)
    # ... resto do código

# Limpeza em handle_collisions():
self.projectiles = [p for p in self.projectiles if p.alive]
for p in dead_projectiles:
    self.projectile_pool.release(p)
```

**Compatibilidade:** ✅ Incremento - reduz alocações de memória

---

## Roadmap de Integração

### Fase 1 (Hoje) - Patterns Isolados
- ✅ Criar ficheiros em `/src/patterns/`
- ✅ Sem mudanças em code existente
- ✅ Tudo importável mas não usado obrigatoriamente

### Fase 2 (Amanhã) - Integração Opcional
- Adicionar Singleton a SoundManager
- Adicionar EventManager a Game
- Adicionar StateManager a Player

### Fase 3 (Semana) - Otimizações
- Adicionar Flyweight para cache de sprites
- Adicionar Object Pool para projectiles
- Validar performance

### Fase 4 (Futuro) - Refatoração Completa
- Usar Command para input
- Usar Prototype para factories
- Testes unitários

---

## Verificação de Funcionalidade

```bash
# Testar que nada quebrou
python src/main.py

# Testar imports dos patterns
python -c "from patterns import *; print('✅ Patterns importáveis')"
```

---

## Conclusão

Estes 7 patterns fazem sentido real para este projeto:

| Pattern | Razão | Impacto |
|---------|-------|--------|
| Singleton | Uma única instância de som | ✅ Essencial |
| Command | Desacoplar input de lógica | ✅ Importante |
| Observer | Eventos desacoplados | ✅ Importante |
| State | Estados explícitos | ✅ Importante |
| Flyweight | Cache de sprites | ✅ Performance |
| Prototype | Factory flexível | ✅ Qualidade |
| Object Pool | Reutilizar projectiles | ✅ Performance |

**Nenhum deles quebra o código existente** - todos são aditivos e podem ser integrados gradualmente.

**Qualidade do código final:**
- Mais desacoplado
- Mais testável
- Melhor performance
- Mais profissional
