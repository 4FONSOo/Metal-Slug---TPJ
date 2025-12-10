# entity/boss.py
"""
Boss helicóptero do nível.

- Ignora gravidade (movimento manual).
- Entra de cima quando o player já está quase no fim.
- Paira e mexe-se cima/baixo.
- Dispara projécteis como o jogador, com dano multiplicado.
"""

from __future__ import annotations

import random
import math

import config
from pg_engine import Vector2
from entity.projectile import Projectile


class Boss:
    def __init__(self, image, x: int, start_y: int, target_y: int):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = int(x)
        self.rect.y = int(start_y)

        # Entrada / movimento base
        self.entering = True
        self.target_y = int(target_y)
        self.hover_center_y = int(target_y)
        self.hover_amplitude = getattr(config, "BOSS_HOVER_AMPLITUDE", 60)
        self.hover_speed = getattr(config, "BOSS_HOVER_SPEED", 1.2)
        self._hover_phase = 0.0

        # Velocidade de descida quando começa a entrar
        self.entry_speed = float(getattr(config, "BOSS_ENTRY_SPEED", 180.0))

        # Delay antes de descer (segundos)
        self.entry_delay = 3.0
        self.entry_timer = self.entry_delay

        # HP
        self.max_hp = getattr(config, "BOSS_MAX_HP", 300)
        self.hp = self.max_hp
        self.alive = True
        self.points = getattr(config, "BOSS_POINTS", 5000)

        # Ataque
        self.damage_multiplier = getattr(config, "BOSS_DAMAGE_MULTIPLIER", 1.5)
        self._time_since_last_shot = 0.0
        self._shot_interval_min = getattr(config, "BOSS_SHOT_INTERVAL_MIN", 0.8)
        self._shot_interval_max = getattr(config, "BOSS_SHOT_INTERVAL_MAX", 1.8)
        self._next_shot_interval = self._random_shot_interval()

    # --------------------------- #
    # Helpers internos
    # --------------------------- #
    def _random_shot_interval(self) -> float:
        return random.uniform(self._shot_interval_min, self._shot_interval_max)

    # --------------------------- #
    # API usada pelo Game
    # --------------------------- #
    def update(self, dt_seconds: float = 0.0, game=None) -> None:
        """
        Movimento + AI básica.

        Nota:
          - EnemyManager chama enemy.update() sem argumentos → aqui game será None.
            Nesse caso NÃO fazemos nada (o update “real” é chamado via Game.update_boss).
        """
        if not self.alive:
            return

        # Chamado a partir do EnemyManager (sem 'game') → ignora
        if game is None:
            return

        # 1) Entrada do boss: delay + shake + descida
        if self.entering:
            # 1.a) Delay inicial: só treme o ecrã
            if self.entry_timer > 0.0:
                self.entry_timer -= dt_seconds

                if hasattr(game, "trigger_camera_shake"):
                    # shake curto renovado todos os frames
                    game.trigger_camera_shake(0.15, 6.0)

                return

            # 1.b) Depois do delay → descer até ao target_y
            self.rect.y += int(self.entry_speed * dt_seconds)
            if self.rect.y >= self.target_y:
                self.rect.y = self.target_y
                self.entering = False

                # Troca de música para tema do boss (se quiseres aqui)
                snd = getattr(game, "sound", None)
                if snd and hasattr(snd, "play_music"):
                    try:
                        snd.stop_music()
                    except Exception:
                        pass
                    try:
                        music_file = getattr(
                            config,
                            "BOSS_MUSIC_FILE",
                            "boss_theme.mp3",
                        )
                        snd.play_music(music_file)
                    except Exception:
                        pass

            return  # enquanto está em fase de entrada, não ataca

        # 2) Hover cima/baixo quando já está "em jogo"
        self._hover_phase += self.hover_speed * dt_seconds
        offset = math.sin(self._hover_phase) * self.hover_amplitude
        self.rect.y = int(self.hover_center_y + offset)

        # 3) Ataques
        self._time_since_last_shot += dt_seconds
        if self._time_since_last_shot >= self._next_shot_interval:
            self._time_since_last_shot = 0.0
            self._next_shot_interval = self._random_shot_interval()
            self._do_random_attack(game)

    def _do_random_attack(self, game) -> None:
        """
        Escolhe um dos “ataques” disponíveis.
        Para já só tiros (tipo o player), aleatórios.
        """
        if not game or not game.player:
            return

        patterns = [self._shoot_straight, self._shoot_spread, self._shoot_down]
        attack = random.choice(patterns)
        attack(game)

    # --------------------------- #
    # Padrões de disparo
    # --------------------------- #
    def _base_shot(self, game, direction: Vector2):
        direction = Vector2(direction.x, direction.y)
        if direction.length_squared() == 0:
            return

        direction = direction.normalize()

        sx = self.rect.centerx
        sy = self.rect.centery

        proj = Projectile(
            sx,
            sy,
            direction.x,
            direction.y,
            max_range=game.bg_width,
            color=getattr(config, "ENEMY_PROJECTILE_COLOR", (255, 80, 80)),
        )

        base_damage = getattr(proj, "damage", 1)
        proj.damage = base_damage * self.damage_multiplier  # dano x1.5

        if game.projectile_manager:
            game.projectile_manager.add_enemy_projectile(proj)
        else:
            game.enemy_projectiles.append(proj)

    def _shoot_towards_player(self, game):
        player = game.player
        if not player:
            return

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        self._base_shot(game, Vector2(dx, dy))

    def _shoot_straight(self, game):
        # tiro directo em direcção ao player
        self._shoot_towards_player(game)

    def _shoot_spread(self, game):
        # 3 tiros em “cone”
        player = game.player
        if not player:
            return

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        base = Vector2(dx, dy)
        if base.length_squared() == 0:
            base = Vector2(1, 0)
        base = base.normalize()

        left = Vector2(base.x, base.y - 0.3)
        right = Vector2(base.x, base.y + 0.3)

        self._base_shot(game, base)
        self._base_shot(game, left)
        self._base_shot(game, right)

    def _shoot_down(self, game):
        # “spray” para baixo (zona do chão)
        self._base_shot(game, Vector2(0, 1))

    # --------------------------- #
    # Interface para colisões
    # --------------------------- #
    def take_damage(self, amount: float) -> None:
        if not self.alive:
            return

        self.hp -= float(amount)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def contact_damage_to_player(self) -> float:
        """Dano por contacto físico com o player."""
        base = getattr(config, "ENEMY_CONTACT_DAMAGE_TO_PLAYER", 10)
        return base * self.damage_multiplier

    def contact_self_damage(self) -> float:
        """Quanto dano o boss leva quando toca no player."""
        return getattr(config, "BOSS_CONTACT_SELF_DAMAGE", 0)

    def draw(self, surface, camera_x: int) -> None:
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))
