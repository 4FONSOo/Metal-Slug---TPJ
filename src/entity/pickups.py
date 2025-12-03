# pickups.py
"""
Sistema de pickups (power-ups / power-downs).

Arquitectura:
  - Nada de pygame aqui dentro.
  - Só lógica: posição, tipo, lifetime, movimento (paraquedas) e descrição do efeito.
  - O Game/LevelScene trata de:
      * spawn aleatório (usa helpers deste ficheiro)
      * colidir player <-> pickup
      * aplicar o efeito ao player / inimigos / HUD
      * desenhar (quadrados agora, sprites depois)
      * tocar sons (ex: NUKE PIIIIII)

Tipos de pickups:
  1) WEAPON_UPGRADE  – upgrade temporário de arma (50 munições, fire-rate mais rápido)
  2) GRENADE_RELOAD  – carrega granadas
  3) HP_UP           – cura HP
  4) HP_DOWN         – dano ao jogador (trollzinho)
  5) NUKE            – rebenta com tudo, flash no ecrã, slow-mo, som "PIIIII"

Cada pickup tem:
  - (x, y): posição no mundo (canto superior esquerdo)
  - largura/altura (para colisão e desenho)
  - tempo de vida (em segundos)
  - tipo (kind)
  - dados do efeito (via get_effect())
  - movimento estilo “paraquedas”: queda lenta, opcionalmente com balanço lateral.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple
import random
import math


# -----------------------------
# CONSTANTES (podes mover para config.py se quiseres)
# -----------------------------

# Dimensão default do pickup (quadrado)
PICKUP_WIDTH = 24
PICKUP_HEIGHT = 24

# Quanto tempo fica no mundo até desaparecer (segundos)
PICKUP_LIFETIME_SECONDS = 10.0

# Movimento "paraquedas"
PICKUP_PARACHUTE_FALL_SPEED = 80.0          # pixels/seg – queda lenta
PICKUP_PARACHUTE_SWAY_AMPLITUDE = 10.0      # quanto balança para os lados
PICKUP_PARACHUTE_SWAY_SPEED = 2.0           # velocidade do balanço

# Efeitos base (ajusta à vontade)
WEAPON_UPGRADE_AMMO = 50
WEAPON_UPGRADE_FIRE_RATE_MULTIPLIER = 0.5   # 0.5 = duas vezes mais rápido

GRENADE_RELOAD_AMOUNT = 3

HP_UP_AMOUNT = 200
HP_DOWN_AMOUNT = 200

# NUKE – estes valores são apenas "contrato" para o Game usar
NUKE_FLASH_DURATION = 0.6        # segundos de flash forte
NUKE_FLASH_FADE_DURATION = 1.0   # segundos a voltar ao normal
NUKE_SLOWMO_DURATION = 0.8       # duração de "slow motion" depois
NUKE_SCREEN_FLASH_COLOR = (255, 255, 255)  # branco nuclear
NUKE_SOUND_ID = "sfx_nuke_beep"  # placeholder para som "PIIIII" no sistema de áudio


class PickupKind(str, Enum):
    """Tipos de pickup suportados."""

    WEAPON_UPGRADE = "weapon_upgrade"
    GRENADE_RELOAD = "grenade_reload"
    HP_UP = "hp_up"
    HP_DOWN = "hp_down"
    NUKE = "nuke"


class Pickup:
    """
    Instância de um pickup no mundo.

    Não sabe nada de Player, Game, pygame, etc.
    Só:
      - onde está
      - que tipo é
      - quanto tempo dura
      - se ainda está a cair estilo paraquedas
      - que efeito descreve
    """

    def __init__(
        self,
        kind: PickupKind,
        x: float,
        y: float,
        lifetime: float = PICKUP_LIFETIME_SECONDS,
        width: int = PICKUP_WIDTH,
        height: int = PICKUP_HEIGHT,
        *,
        falling: bool = True,
        fall_speed: float = PICKUP_PARACHUTE_FALL_SPEED,
        ground_y: Optional[float] = None,
    ):
        if not isinstance(kind, PickupKind):
            raise TypeError(f"[Pickup] kind inválido: {kind!r}")

        self.kind = kind

        # posição base
        self.x = float(x)
        self.y = float(y)
        self.width = int(width)
        self.height = int(height)

        # tempo de vida em segundos
        self.time_left = float(lifetime)
        self.alive = True

        # movimento estilo paraquedas
        self.falling = bool(falling)
        self.fall_speed = float(fall_speed)
        self.ground_y: Optional[float] = ground_y

        # para balanço lateral (paraquedas a abanar)
        self._float_phase = 0.0
        self._base_x = float(x)

    # ------------------------------------------------------------------ #
    # Configuração de chão / limite vertical
    # ------------------------------------------------------------------ #

    def set_ground_y(self, ground_y: float) -> None:
        """
        Define a linha de "chão" onde o pickup pára de cair.

        Exemplo de uso no Game:
          p = Pickup(...)
          p.set_ground_y(ground_y_do_nível_ou_da_plataforma)
        """
        self.ground_y = float(ground_y)

    # ------------------------------------------------------------------ #
    # Atualização
    # ------------------------------------------------------------------ #

    def update(self, dt: float) -> None:
        """
        Atualiza o estado do pickup.

        dt: delta time em segundos (ex: 0.016 / 60 FPS)

        - Desconta lifetime.
        - Se estiver a cair, move para baixo e abana para os lados.
        - Quando atinge o ground_y (se definido), pára de cair.
        """
        if not self.alive:
            return

        # Lifetime
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.alive = False
            return

        # Animação de "flutuação" para o paraquedas
        self._float_phase += dt

        if self.falling:
            # queda lenta
            self.y += self.fall_speed * dt

            # balanço lateral tipo paraquedas
            sway = PICKUP_PARACHUTE_SWAY_AMPLITUDE * math.sin(
                self._float_phase * PICKUP_PARACHUTE_SWAY_SPEED
            )
            self.x = self._base_x + sway

            # parar quando atinge o chão, se definido
            if self.ground_y is not None:
                bottom = self.y + self.height
                if bottom >= self.ground_y:
                    # pousa suavemente no chão
                    self.y = self.ground_y - self.height
                    self.falling = False
                    # actualiza base_x para o ponto onde ficou
                    self._base_x = self.x

    def is_expired(self) -> bool:
        """True se já passou o tempo de vida (desapareceu)."""
        return not self.alive

    def is_falling(self) -> bool:
        """True se ainda estiver a cair estilo paraquedas."""
        return self.falling and self.alive

    # ------------------------------------------------------------------ #
    # Colisão / geometria
    # ------------------------------------------------------------------ #

    def get_rect_tuple(self) -> Tuple[int, int, int, int]:
        """
        Devolve (x, y, w, h) em ints, para o Game criar pg.Rect se quiser.
        """
        return int(self.x), int(self.y), self.width, self.height

    # ------------------------------------------------------------------ #
    # Efeito lógico
    # ------------------------------------------------------------------ #

    def get_effect(self) -> Dict[str, Any]:
        """
        Descreve o efeito do pickup em forma de dicionário.

        O Game pode usar isto para aplicar:
          - WEAPON_UPGRADE: mexer no fire_rate e munições, por tempo limitado
          - GRENADE_RELOAD: somar granadas ao player
          - HP_UP / HP_DOWN: ajustar HP
          - NUKE: matar todos os inimigos, flash no ecrã, slow-mo, som, etc.

        NÃO aplica nada por si – apenas diz "o que devia acontecer".
        """
        if self.kind == PickupKind.WEAPON_UPGRADE:
            return {
                "type": self.kind.value,
                "ammo": WEAPON_UPGRADE_AMMO,
                "fire_rate_multiplier": WEAPON_UPGRADE_FIRE_RATE_MULTIPLIER,
                # Se quiseres, mais tarde podes adicionar:
                # "duration": 5.0,  # segundos de duração do upgrade
            }

        if self.kind == PickupKind.GRENADE_RELOAD:
            return {
                "type": self.kind.value,
                "grenades_delta": GRENADE_RELOAD_AMOUNT,
            }

        if self.kind == PickupKind.HP_UP:
            return {
                "type": self.kind.value,
                "hp_delta": +HP_UP_AMOUNT,
            }

        if self.kind == PickupKind.HP_DOWN:
            return {
                "type": self.kind.value,
                "hp_delta": -HP_DOWN_AMOUNT,
            }

        if self.kind == PickupKind.NUKE:
            return {
                "type": self.kind.value,
                "kill_all_enemies": True,
                "screen_flash": True,
                "flash_color": NUKE_SCREEN_FLASH_COLOR,
                "flash_duration": NUKE_FLASH_DURATION,
                "flash_fade_duration": NUKE_FLASH_FADE_DURATION,
                "slow_motion": True,
                "slow_motion_duration": NUKE_SLOWMO_DURATION,
                # Hook para som tipo "PIIIII"
                "sound_id": NUKE_SOUND_ID,
            }

        # fallback paranoico
        return {"type": "unknown"}

    # ------------------------------------------------------------------ #
    # Dados para desenho (placeholder)
    # ------------------------------------------------------------------ #

    def get_draw_data(self) -> Dict[str, Any]:
        """
        Dados mínimos para o Game desenhar o pickup.

        O Game pode fazer:
          - olhar para "kind" e escolher cor/sprite
          - usar (x, y, width, height) para rect ou colocar a sprite

        Neste momento:
          - apenas sugere cores diferentes por tipo
          - não toca em pygame nem pg_engine
        """
        # Cores sugeridas (podes alterar à vontade no Game)
        if self.kind == PickupKind.WEAPON_UPGRADE:
            color = (0, 200, 255)      # azul ciano
        elif self.kind == PickupKind.GRENADE_RELOAD:
            color = (0, 255, 0)        # verde
        elif self.kind == PickupKind.HP_UP:
            color = (0, 255, 100)      # verde clarinho
        elif self.kind == PickupKind.HP_DOWN:
            color = (255, 80, 80)      # vermelho forte
        elif self.kind == PickupKind.NUKE:
            color = (255, 255, 0)      # amarelo nuclear
        else:
            color = (255, 255, 255)    # branco, fallback

        # Aqui, se quisermos sprites no futuro:
        # sprite_id = "pickup_weapon" / "pickup_grenade" / "pickup_hp_up" / ...
        # e o Game faria algo como: image = resource.load_sprite(sprite_id)
        sprite_id = None  # placeholder; por enquanto desenhas só rects

        return {
            "kind": self.kind.value,
            "x": int(self.x),
            "y": int(self.y),
            "width": self.width,
            "height": self.height,
            "color": color,
            "sprite_id": sprite_id,
            "time_left": self.time_left,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def mark_collected(self) -> None:
        """
        Marca explicitamente como apanhado.

        O fluxo típico no Game será:
          - se player.rect colide com pickup -> ler efeito -> aplicar -> mark_collected()
        """
        self.alive = False
        self.time_left = 0.0


# ---------------------------------------------------------------------- #
# HELPERS PARA SPAWN ALEATÓRIO
# ---------------------------------------------------------------------- #

def random_pickup_kind(
    include: Optional[Iterable[PickupKind]] = None,
    exclude: Optional[Iterable[PickupKind]] = None,
) -> PickupKind:
    """
    Escolhe um tipo de pickup aleatoriamente.

    include: se fornecido, só escolhe dentro deste conjunto.
    exclude: tipos a evitar.

    Exemplo:
      random_pickup_kind(exclude=[PickupKind.HP_DOWN])
    """
    if include is not None:
        pool = list(include)
    else:
        pool = list(PickupKind)

    if exclude:
        excluded = set(exclude)
        pool = [k for k in pool if k not in excluded]

    if not pool:
        # fallback: pelo menos um tipo
        pool = [PickupKind.WEAPON_UPGRADE]

    return random.choice(pool)


def spawn_random_pickup(
    level_width: int,
    ground_y: Optional[float] = None,
    *,
    spawn_y: float = -40.0,
    lifetime: float = PICKUP_LIFETIME_SECONDS,
    include: Optional[Iterable[PickupKind]] = None,
    exclude: Optional[Iterable[PickupKind]] = None,
) -> Pickup:
    """
    Cria um pickup aleatório, a cair de paraquedas no nível.

    - level_width: largura total do nível (para escolher o X aleatório).
    - ground_y: linha vertical onde o pickup deve pousar (ex: altura do chão).
    - spawn_y: altura inicial (default: -40, ligeiramente acima do topo do ecrã).
    - lifetime: tempo de vida em segundos.

    Exemplo de uso no Game:
      p = spawn_random_pickup(self.bg_width, ground_y=self.ground_y)
      self.pickups.append(p)
    """
    kind = random_pickup_kind(include=include, exclude=exclude)
    x = random.randint(0, max(0, level_width - PICKUP_WIDTH))

    pickup = Pickup(
        kind=kind,
        x=x,
        y=spawn_y,
        lifetime=lifetime,
        falling=True,
        fall_speed=PICKUP_PARACHUTE_FALL_SPEED,
        ground_y=ground_y,
    )
    return pickup
