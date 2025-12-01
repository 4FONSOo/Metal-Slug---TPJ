
# input_manager.py
"""
Gestão de input de jogador (teclado).

- Movimento horizontal
- Direção de tiro (inclui diagonais)
"""

from typing import Tuple
import controls


def get_move_axis(keys) -> int:
    dx = 0
    left_key = controls.get_key(controls.MOVE_LEFT)
    right_key = controls.get_key(controls.MOVE_RIGHT)

    if keys[left_key]:
        dx -= 1
    if keys[right_key]:
        dx += 1
    return dx


def is_fire_pressed(keys) -> bool:
    fire_key = controls.get_key(controls.FIRE)
    return keys[fire_key]


def get_shoot_direction(
    keys,
    facing: int,
    allow_diagonals: bool = True,
) -> Tuple[int, int]:
    """
    Calcula a direção do tiro com base nas teclas de direção + orientação do jogador.

    Convenções:
      - Eixo X: -1 = esquerda, 0 = centro, +1 = direita
      - Eixo Y: -1 = cima,    0 = centro, +1 = baixo

    Regras:
      - Se carregar para cima + esquerda/direita → diagonal para cima.
      - Se carregar para baixo + esquerda/direita → diagonal para baixo.
      - Se só cima → tiro vertical para cima.
      - Se só baixo → tiro vertical para baixo.
      - Caso contrário → tiro horizontal na direção de 'facing'.
    """
    up_key = controls.get_key(controls.UP)
    down_key = controls.get_key(controls.DOWN)
    left_key = controls.get_key(controls.MOVE_LEFT)
    right_key = controls.get_key(controls.MOVE_RIGHT)

    up = keys[up_key]
    down = keys[down_key]
    left = keys[left_key]
    right = keys[right_key]

    # Base: para onde o jogador está virado
    dir_x, dir_y = facing, 0

    if allow_diagonals:
        # DIAGONAIS PARA CIMA
        if up and not down:
            if left:
                return -1, -1   # cima-esquerda
            if right:
                return 1, -1    # cima-direita

        # DIAGONAIS PARA BAIXO
        if down and not up:
            if left:
                return -1, 1    # baixo-esquerda
            if right:
                return 1, 1     # baixo-direita

    # VERTICAL SIMPLES
    if up and not down:
        return 0, -1

    if down and not up:
        return 0, 1

    # HORIZONTAL (default – segue o facing)
    return dir_x, dir_y
