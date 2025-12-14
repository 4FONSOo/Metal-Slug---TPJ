# patterns/command.py
"""
Command Pattern - Encapsula ações como objetos.

Usado para:
- Input do jogador (Move, Jump, Shoot, ThrowGrenade)
- Undo/Redo de ações (básico)
- Fila de commands para replay

Vantagens:
- Desacopla input de lógica
- Permite undo/redo
- Facilita testes (commands são testáveis isoladamente)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple


class Command(ABC):
    """Base para todos os commands."""
    
    @abstractmethod
    def execute(self) -> Any:
        """Executa a ação."""
        pass
    
    def undo(self):
        """Desfaz a ação (opcional)."""
        pass
    
    def redo(self):
        """Refaz a ação (opcional)."""
        pass


class MoveCommand(Command):
    """Command para movimento do jogador."""
    
    def __init__(self, player, direction: int):
        self.player = player
        self.direction = int(direction)  # -1 (esquerda), 0, 1 (direita)
        self.old_x = player.rect.x if hasattr(player, "rect") else 0
    
    def execute(self) -> None:
        if not self.player:
            return

        # Usa a API do Player (evita duplicar lógica fora da entidade)
        if hasattr(self.player, "apply_move_axis"):
            self.player.apply_move_axis(self.direction)
        else:
            # fallback mínimo (compatibilidade)
            if self.direction < 0:
                self.player.facing = -1
            elif self.direction > 0:
                self.player.facing = 1
    
    def undo(self) -> None:
        if self.player and hasattr(self.player, "rect"):
            self.player.rect.x = self.old_x


class JumpCommand(Command):
    """Command para salto do jogador."""
    
    def __init__(self, player, *, jump_pressed: bool, down_pressed: bool):
        self.player = player
        self.jump_pressed = bool(jump_pressed)
        self.down_pressed = bool(down_pressed)
        self._was_jumping = False
    
    def execute(self) -> None:
        if not self.player:
            return

        before = bool(getattr(self.player, "is_jumping", False))

        if hasattr(self.player, "apply_jump_input"):
            self.player.apply_jump_input(
                jump_pressed=self.jump_pressed,
                down_pressed=self.down_pressed,
            )
        else:
            # fallback básico
            if self.jump_pressed and not getattr(self.player, "is_jumping", False):
                self.player.is_jumping = True

        after = bool(getattr(self.player, "is_jumping", False))
        self._was_jumping = (not before) and after
    
    def undo(self) -> None:
        if self.player and self._was_jumping:
            self.player.is_jumping = False


class SetFireInputCommand(Command):
    """Publica no Game o estado do botão de tiro para este frame."""

    def __init__(self, game, pressed: bool):
        self.game = game
        self.pressed = bool(pressed)

    def execute(self) -> None:
        if self.game is not None:
            setattr(self.game, "_command_fire_pressed", self.pressed)


class SetGrenadeInputCommand(Command):
    """Publica no Game o estado do botão de granada para este frame."""

    def __init__(self, game, pressed: bool):
        self.game = game
        self.pressed = bool(pressed)

    def execute(self) -> None:
        if self.game is not None:
            setattr(self.game, "_command_grenade_pressed", self.pressed)


class SetAimInputCommand(Command):
    """Publica no Game a direcção discreta de mira/tiro para este frame."""

    def __init__(self, game, shoot_direction: Tuple[int, int]):
        self.game = game
        dx, dy = shoot_direction
        self.shoot_direction = (int(dx), int(dy))

    def execute(self) -> None:
        if self.game is not None:
            setattr(self.game, "_command_shoot_dir", self.shoot_direction)


class CommandInvoker:
    """
    Invoca commands e mantém histórico para undo/redo.
    
    Uso:
        invoker = CommandInvoker()
        cmd = MoveCommand(player, 1)
        invoker.execute(cmd)
        invoker.undo()  # desfaz movimento
    """
    
    def __init__(self, history_limit: int = 100):
        self.history: List[Command] = []
        self.redo_stack: List[Command] = []
        self.history_limit = history_limit
    
    def execute(self, command: Command) -> Any:
        """Executa um command e o guarda no histórico."""
        result = command.execute()
        self.history.append(command)
        self.redo_stack.clear()  # Limpa redo ao executar novo command
        
        # Limita tamanho da história
        if len(self.history) > self.history_limit:
            self.history.pop(0)
        
        return result
    
    def undo(self) -> bool:
        """Desfaz o último command."""
        if not self.history:
            return False
        
        cmd = self.history.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        return True
    
    def redo(self) -> bool:
        """Refaz o último comando desfeito."""
        if not self.redo_stack:
            return False
        
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.history.append(cmd)
        return True
    
    def clear(self) -> None:
        """Limpa histórico e redo stack."""
        self.history.clear()
        self.redo_stack.clear()


class MacroCommand(Command):
    """Command que executa múltiplos commands em sequência."""
    
    def __init__(self, commands: List[Command]):
        self.commands = commands
    
    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()
    
    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()


def build_player_action_macro(
    *,
    game,
    player,
    move_axis: int,
    jump_pressed: bool,
    down_pressed: bool,
    fire_pressed: bool,
    grenade_pressed: bool,
    shoot_dir: Tuple[int, int],
) -> MacroCommand:
    """Helper: gera um MacroCommand com as ações de input deste frame."""
    cmds: List[Command] = []
    if player is not None:
        cmds.append(MoveCommand(player, move_axis))
        cmds.append(JumpCommand(player, jump_pressed=jump_pressed, down_pressed=down_pressed))
    if game is not None:
        cmds.append(SetFireInputCommand(game, fire_pressed))
        cmds.append(SetGrenadeInputCommand(game, grenade_pressed))
        cmds.append(SetAimInputCommand(game, shoot_dir))
    return MacroCommand(cmds)
