
"""command_input_manager.py

Adapta input bruto (teclas) para Commands (Command Pattern).

Objetivo:
- O resto do jogo (Player/Game) consome ações via `patterns.command`.
- Evita duplicar a lógica de combate: apenas publica o estado de input no Game
  (fire/grenade/aim), e o `Game.handle_combat()` continua a ser a fonte de verdade.
"""

from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

import controls

from managers.input_manager import (
    get_move_axis,
    get_shoot_direction,
    is_fire_pressed,
    is_granade_pressed,
)

from patterns.command import Command, build_player_action_macro

if TYPE_CHECKING:
    import pg_engine as pg
    from game_state import Game


class CommandInputManager:
    """Traduz input (keys) → Commands executáveis por um `CommandInvoker`."""

    def build_commands(self, keys: "pg.KeyState", game: "Game") -> List[Command]:
        player = getattr(game, "player", None)

        move_axis = get_move_axis(keys)

        jump_key = controls.get_key(controls.JUMP)
        down_key = controls.get_key(controls.DOWN)
        jump_pressed = bool(keys[jump_key])
        down_pressed = bool(keys[down_key])

        fire_pressed = bool(is_fire_pressed(keys))
        grenade_pressed = bool(is_granade_pressed(keys))

        facing = getattr(player, "facing", 1) if player is not None else 1
        shoot_dir: Tuple[int, int] = get_shoot_direction(
            keys,
            facing=facing,
            allow_diagonals=True,
        )

        macro = build_player_action_macro(
            game=game,
            player=player,
            move_axis=move_axis,
            jump_pressed=jump_pressed,
            down_pressed=down_pressed,
            fire_pressed=fire_pressed,
            grenade_pressed=grenade_pressed,
            shoot_dir=shoot_dir,
        )

        return [macro]
