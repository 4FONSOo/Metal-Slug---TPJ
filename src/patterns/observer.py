# patterns/observer.py
"""
Observer Pattern - Sistema de eventos desacoplado.

Usado para:
- EnemyDead: quando um inimigo morre (score, som)
- PickupCollected: quando apanhas um pickup
- PlayerDamaged: quando o jogador leva dano
- WeaponUpgraded: quando apanhas upgrade de arma

Vantagens:
- Desacopla sistemas (combate não precisa saber sobre score)
- Fácil adicionar novos listeners (achievements, etc)
- Testável em isolamento
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any


class EventListener(ABC):
    """Base para qualquer listener de eventos."""
    
    @abstractmethod
    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Chamado quando um evento é disparado."""
        pass


class EventManager:
    """
    Gestor centralizado de eventos.
    
    Uso:
        manager = EventManager()
        manager.subscribe("enemy_dead", score_listener)
        manager.emit("enemy_dead", {"enemy": enemy_obj, "points": 100})
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, listener: Callable) -> None:
        """Subscreve a um tipo de evento."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
    
    def unsubscribe(self, event_type: str, listener: Callable) -> None:
        """Desinscreve de um tipo de evento."""
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(listener)
            except ValueError:
                pass
    
    def emit(self, event_type: str, data: Dict[str, Any] | None = None) -> None:
        """Emite um evento para todos os listeners subscritos."""
        if data is None:
            data = {}
        
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(data)
                except Exception as e:
                    print(f"[EventManager] Erro ao processar {event_type}: {e}")
    
    def clear(self, event_type: str | None = None) -> None:
        """Limpa listeners de um tipo ou de todos."""
        if event_type is None:
            self._listeners.clear()
        elif event_type in self._listeners:
            self._listeners[event_type].clear()


class ScoreObserver(EventListener):
    """Observer que atualiza a pontuação quando eventos ocorrem."""
    
    def __init__(self, game):
        self.game = game
    
    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type == "enemy_dead":
            points = data.get("points", 0)
            x = data.get("x")
            y = data.get("y")
            self.game.add_score(points, x, y)
        
        elif event_type == "pickup_collected":
            effect = data.get("effect", {})
            self.game.apply_pickup_effect(effect)


class SoundObserver(EventListener):
    """Observer que toca sons em resposta a eventos."""
    
    def __init__(self, sound_manager):
        self.sound = sound_manager
    
    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type == "enemy_dead":
            try:
                self.sound.play_enemy_death()
            except Exception:
                pass
        
        elif event_type == "shoot":
            upgraded = data.get("upgraded", False)
            try:
                if upgraded:
                    self.sound.play_sfx("tiro2.mp3")
                else:
                    self.sound.play_sfx("tiro1.mp3")
            except Exception:
                pass
        
        elif event_type == "melee_hit":
            try:
                self.sound.play_melee()
            except Exception:
                pass
        
        elif event_type == "grenade_throw":
            try:
                self.sound.play_sfx("granada.mp3")
            except Exception:
                pass
        
        elif event_type == "grenade_explode":
            try:
                self.sound.play_grenade_explosion()
            except Exception:
                pass
