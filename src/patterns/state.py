# patterns/state.py
"""
State Pattern - Máquina de estados para o jogador e inimigos.

Usado para:
- Player: Idle → Running → Jumping → Falling
- Enemy: Patrolling → ChargingAttack → Attacking → Retreating
- Game: Menu → Playing → Paused → GameOver

Vantagens:
- Torna transições de estado explícitas
- Fácil de testar e debugar
- Evita if/else aninhados complexos
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class State(ABC):
    """Base para qualquer estado."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def enter(self, context: Any) -> None:
        """Chamado quando se entra neste estado."""
        pass
    
    @abstractmethod
    def update(self, context: Any, dt: float) -> Optional[str]:
        """
        Chamado cada frame. 
        Retorna o nome do estado para o qual transitar (ou None).
        """
        pass
    
    @abstractmethod
    def exit(self, context: Any) -> None:
        """Chamado quando se sai deste estado."""
        pass


class PlayerIdleState(State):
    """Jogador parado/idle."""
    
    def __init__(self):
        super().__init__("idle")
        self.idle_duration = 0.0
    
    def enter(self, player: Any) -> None:
        player.leg_state = "idle"
        self.idle_duration = 0.0
    
    def update(self, player: Any, dt: float) -> Optional[str]:
        if getattr(player, "is_jumping", False):
            return "jumping"
        if getattr(player, "moving", False):
            return "running"
        return None
    
    def exit(self, player: Any) -> None:
        pass


class PlayerRunningState(State):
    """Jogador em movimento."""
    
    def __init__(self):
        super().__init__("running")
    
    def enter(self, player: Any) -> None:
        player.leg_state = "run"
    
    def update(self, player: Any, dt: float) -> Optional[str]:
        if getattr(player, "is_jumping", False):
            return "jumping"
        if not getattr(player, "moving", False):
            return "idle"
        return None
    
    def exit(self, player: Any) -> None:
        pass


class PlayerJumpingState(State):
    """Jogador no ar."""
    
    def __init__(self):
        super().__init__("jumping")
    
    def enter(self, player: Any) -> None:
        pass  # animação já foi iniciada no handle_input
    
    def update(self, player: Any, dt: float) -> Optional[str]:
        # Sai do estado quando aterrar (sem saltar + velocidade vertical 0)
        if not getattr(player, "is_jumping", False) and getattr(player, "vel_y", 0) == 0:
            return "running" if getattr(player, "moving", False) else "idle"
        return None
    
    def exit(self, player: Any) -> None:
        pass


class StateManager:
    """
    Gestor de máquina de estados.
    
    Uso:
        manager = StateManager(player)
        manager.change_state("running")
        manager.update(dt)
    """
    
    def __init__(self, context: Any, initial_state: State):
        self.context = context
        self.states: Dict[str, State] = {}
        self.current_state = initial_state
        self.previous_state: Optional[State] = None
        
        self.register_state(initial_state)
        self.current_state.enter(context)
    
    def register_state(self, state: State) -> None:
        """Regista um estado pelo seu nome."""
        self.states[state.name] = state
    
    def change_state(self, state_name: str) -> bool:
        """Muda para um novo estado."""
        if state_name not in self.states:
            return False
        
        if self.current_state.name == state_name:
            return False  # já está neste estado
        
        self.current_state.exit(self.context)
        self.previous_state = self.current_state
        self.current_state = self.states[state_name]
        self.current_state.enter(self.context)
        return True
    
    def update(self, dt: float) -> None:
        """Atualiza o estado e trata transições."""
        next_state = self.current_state.update(self.context, dt)
        if next_state:
            self.change_state(next_state)
    
    def get_current_state(self) -> str:
        """Retorna o nome do estado atual."""
        return self.current_state.name
    
    def get_previous_state(self) -> Optional[str]:
        """Retorna o nome do estado anterior."""
        return self.previous_state.name if self.previous_state else None
