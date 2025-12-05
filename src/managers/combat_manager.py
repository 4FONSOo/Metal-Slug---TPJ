# combat_manager.py
"""
Gestor de combate do jogador (lógica).

Objectivo:
  - Tirar do Game a lógica de:
      * cooldown de tiro
      * decisão entre melee / tiro
      * granadas (contagem, cooldown)
      * upgrades de arma (fire-rate, munições especiais)
  - NÃO cria projécteis nem granadas. Em vez disso, devolve
    “intenção de acção” em forma de eventos (MeleeAttackEvent,
    ShootEvent, ThrowGrenadeEvent, etc.).

Integração típica (futuro):
  - A Scene prepara um CombatInput com:
      * fire_pressed
      * fire_just_pressed
      * secondary_pressed (granada)
      * secondary_just_pressed
      * shoot_dir (dx, dy)
  - Chama combat_manager.update(dt, input).
  - Recebe uma lista de CombatEvent.
  - Para cada evento:
      * cria projéctil / granada / animação de melee
      * chama som, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


# ------------------------------------------------------------------ #
# Input e Eventos
# ------------------------------------------------------------------ #

@dataclass
class CombatInput:
    """Estado de input relevante para o combate do jogador num frame."""

    fire_pressed: bool
    fire_just_pressed: bool
    secondary_pressed: bool       # ex: granada
    secondary_just_pressed: bool
    shoot_dir: Tuple[int, int]    # direcção discreta (dx, dy), ex: (1,0), (0,-1), (1,-1)


@dataclass
class CombatEvent:
    """Base para todos os eventos de combate."""
    type: str


@dataclass
class MeleeAttackEvent(CombatEvent):
    """Ataque melee (faca)."""

    def __init__(self):
        super().__init__(type="melee")


@dataclass
class ShootEvent(CombatEvent):
    """
    Pedido de disparo de projéctil.

    direction: direcção normalizada (dx, dy) em floats.
    upgraded_weapon: se o disparo usa arma melhorada.
    """

    direction: Tuple[float, float]
    upgraded_weapon: bool

    def __init__(self, direction: Tuple[float, float], upgraded_weapon: bool):
        super().__init__(type="shoot")
        self.direction = direction
        self.upgraded_weapon = upgraded_weapon


@dataclass
class ThrowGrenadeEvent(CombatEvent):
    """Pedido para lançar granada (sem posição, só intenção)."""

    def __init__(self):
        super().__init__(type="grenade")


# ------------------------------------------------------------------ #
# CombatManager
# ------------------------------------------------------------------ #

class CombatManager:
    """
    Gestor de combate do jogador.

    Não conhece o Player nem o mundo. Só gere:
      - cooldown de tiro
      - munições de arma melhorada
      - número de granadas
      - cheats de granadas infinitas
      - ordem: melee primeiro, depois tiro

    Unidades:
      - dt_seconds em segundos
      - base_fire_interval / upgraded_fire_interval em segundos
    """

    def __init__(
        self,
        *,
        base_fire_interval: float,
        upgraded_fire_interval: float,
        melee_priority: bool = True,
        initial_grenades: int = 0,
    ) -> None:
        self.base_fire_interval = float(base_fire_interval)
        self.upgraded_fire_interval = float(upgraded_fire_interval)
        self.melee_priority = melee_priority

        # Tiro
        self._time_since_last_shot = 0.0
        self._has_weapon_upgrade = False
        self._upgrade_ammo = 0  # munições restantes da arma melhorada

        # Granadas
        self._grenades = max(0, int(initial_grenades))
        self._infinite_grenades = False

    # ------------------------------------------------------------------ #
    # Config / estado público
    # ------------------------------------------------------------------ #

    def set_grenades(self, amount: int) -> None:
        self._grenades = max(0, int(amount))

    def add_grenades(self, delta: int) -> None:
        self._grenades = max(0, self._grenades + int(delta))

    def enable_infinite_grenades(self, enable: bool) -> None:
        self._infinite_grenades = bool(enable)

    def apply_weapon_upgrade(self, ammo: int) -> None:
        """
        Activa arma melhorada com determinada quantidade de munições.

        - Se já houver upgrade activo, acumula munições.
        - Enquanto houver ammo > 0, usa fire-rate mais rápido
          (upgraded_fire_interval).
        """
        extra = max(0, int(ammo))
        if extra <= 0:
            return

        self._has_weapon_upgrade = True
        self._upgrade_ammo += extra

    @property
    def has_weapon_upgrade(self) -> bool:
        return self._has_weapon_upgrade and self._upgrade_ammo > 0

    @property
    def upgrade_ammo(self) -> int:
        return self._upgrade_ammo

    @property
    def grenades(self) -> int | float:
        """Devolve nº de granadas (ou infinito se cheat activo)."""
        if self._infinite_grenades:
            return float("inf")
        return self._grenades

    # ------------------------------------------------------------------ #
    # Loop principal
    # ------------------------------------------------------------------ #

    def update(self, dt_seconds: float, input_state: CombatInput) -> List[CombatEvent]:
        """
        Processa um frame de combate e devolve eventos a executar.

        Não cria projécteis nem aplica dano – apenas diz o que deve acontecer.
        """
        events: List[CombatEvent] = []
        self._time_since_last_shot += float(dt_seconds or 0.0)

        # -------------------------------------------------------------- #
        # 1) Ataque melee (se tiver prioridade e botão acabou de ser premido)
        #    Replicando a lógica actual: se o melee acertar, normalmente o
        #    Game não dispara bala nesse frame.
        # -------------------------------------------------------------- #
        if self.melee_priority and input_state.fire_just_pressed:
            events.append(MeleeAttackEvent())
            # A decisão de “se acertou ou não” é feita no Game.
            # Aqui não forçamos return, porque o Game pode decidir ignorar
            # o evento ou continuar a disparar na mesma se quiser.

        # -------------------------------------------------------------- #
        # 2) Tiro
        #
        # Padrão que tens actualmente:
        #   - arma base (pistola): só dispara em fire_just_pressed
        #   - arma melhorada: permite disparo contínuo (fire_pressed)
        # Tudo isto respeitando o cooldown (_time_since_last_shot).
        # -------------------------------------------------------------- #
        wants_fire = False

        if self.has_weapon_upgrade:
            # upgrade activo → pode manter premido para auto-fire
            wants_fire = input_state.fire_pressed
        else:
            # pistola base → só quando a tecla é carregada neste frame
            wants_fire = input_state.fire_just_pressed

        if wants_fire and self._can_shoot():
            direction = self._direction_from_input(input_state.shoot_dir)
            upgraded = self.has_weapon_upgrade

            events.append(ShootEvent(direction=direction, upgraded_weapon=upgraded))
            self._consume_shot(upgraded)

        # -------------------------------------------------------------- #
        # 3) Granada
        #
        # Lógica actual: só no momento em que a tecla é “just pressed”.
        # O número de granadas / cheat INF é gerido aqui.
        # -------------------------------------------------------------- #
        if input_state.secondary_just_pressed:
            if self._can_throw_grenade():
                events.append(ThrowGrenadeEvent())
                self._consume_grenade()

        return events

    # ------------------------------------------------------------------ #
    # Lógica interna
    # ------------------------------------------------------------------ #

    def _current_fire_interval(self) -> float:
        if self.has_weapon_upgrade:
            return self.upgraded_fire_interval
        return self.base_fire_interval

    def _can_shoot(self) -> bool:
        interval = self._current_fire_interval()
        # proteger contra intervalos inválidos
        interval = max(0.0, float(interval))
        if interval == 0.0:
            return True
        return self._time_since_last_shot >= interval

    def _consume_shot(self, upgraded_used: bool) -> None:
        self._time_since_last_shot = 0.0
        if upgraded_used and self._upgrade_ammo > 0:
            self._upgrade_ammo -= 1
            if self._upgrade_ammo <= 0:
                self._upgrade_ammo = 0
                self._has_weapon_upgrade = False

    def _can_throw_grenade(self) -> bool:
        if self._infinite_grenades:
            return True
        return self._grenades > 0

    def _consume_grenade(self) -> None:
        if self._infinite_grenades:
            return
        if self._grenades > 0:
            self._grenades -= 1

    @staticmethod
    def _direction_from_input(shoot_dir: Tuple[int, int]) -> Tuple[float, float]:
        """Converte (dx, dy) discreto em direcção normalizada (ou fallback para a direita)."""
        dx, dy = shoot_dir
        dx = int(dx)
        dy = int(dy)

        if dx == 0 and dy == 0:
            # fallback: direita
            return 1.0, 0.0

        length_sq = dx * dx + dy * dy
        if length_sq <= 0:
            return 1.0, 0.0

        length = length_sq ** 0.5
        return dx / length, dy / length
