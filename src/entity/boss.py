# entity/boss.py
"""
Boss helicóptero do nível.

- Ignora gravidade (movimento manual).
- Entra de cima quando o player já está quase no fim.
- Paira e mexe-se cima/baixo.
- Faz dashes laterais ocasionais.
- Dispara projécteis com dano multiplicado.
- Lança rajadas de granadas (3) que ignoram o TMX (via owner="boss").
"""

from __future__ import annotations

import random
import math
import config

from pg_engine import Vector2
from entity.projectile import Projectile
from entity.granade import Granade


class Boss:
    def __init__(self, image, x: int, start_y: int, target_y: int):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = int(x)
        self.rect.y = int(start_y)

        # -----------------------------
        # Entrada / movimento vertical
        # -----------------------------
        self.entering = True
        self.target_y = int(target_y)
        self.hover_center_y = int(target_y)
        self.hover_amplitude = getattr(config, "BOSS_HOVER_AMPLITUDE", 60)
        self.hover_speed = getattr(config, "BOSS_HOVER_SPEED", 1.2)
        self._hover_phase = 0.0

        # Velocidade de descida quando começa a entrar
        self.entry_speed = float(getattr(config, "BOSS_ENTRY_SPEED", 180.0))

        # Delay antes de descer (segundos)
        self.entry_delay = float(getattr(config, "BOSS_ENTRY_DELAY", 3.0))
        self.entry_timer = self.entry_delay
        self.music_started = False

        # -----------------------------
        # Movimento lateral (dashes)
        # -----------------------------
        self.lateral_speed = float(getattr(config, "BOSS_LATERAL_SPEED", 420.0))
        self.lateral_distance = float(getattr(config, "BOSS_LATERAL_DISTANCE", 260.0))
        self.lateral_cooldown_min = float(
            getattr(config, "BOSS_LATERAL_COOLDOWN_MIN", 1.5)
        )
        self.lateral_cooldown_max = float(
            getattr(config, "BOSS_LATERAL_COOLDOWN_MAX", 3.0)
        )
        self._lateral_cooldown_timer = random.uniform(
            self.lateral_cooldown_min,
            self.lateral_cooldown_max,
        )
        self._lateral_active = False        # se está num dash neste momento
        self._lateral_direction = 0         # -1 esquerda, +1 direita
        self._lateral_travelled = 0.0       # distância percorrida no dash actual

        # -----------------------------
        # HP / pontuação
        # -----------------------------
        self.max_hp = getattr(config, "BOSS_MAX_HP", 5000)
        self.hp = self.max_hp
        self.alive = True
        self.points = getattr(config, "BOSS_POINTS", 15000)

        # -----------------------------
        # Ataques (tiros)
        # -----------------------------
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

    def _update_lateral_movement(self, dt_seconds: float, game=None) -> None:
        """
        Pequenos 'dashes' horizontais ocasionais.
        """
        if game is None or self.entering:
            return

        level_width = getattr(game, "bg_width", config.WIDTH)
        margin = getattr(config, "BOSS_LATERAL_MARGIN", 40)

        # 1) Se já estamos em dash, continuar esse movimento
        if self._lateral_active:
            step = self.lateral_speed * dt_seconds * self._lateral_direction
            self.rect.x += int(step)
            self._lateral_travelled += abs(step)

            # Limites do nível
            if self.rect.left < margin:
                self.rect.left = margin
                self._lateral_active = False
            elif self.rect.right > level_width - margin:
                self.rect.right = level_width - margin
                self._lateral_active = False

            # Distância máxima atingida?
            if self._lateral_travelled >= self.lateral_distance:
                self._lateral_active = False

            # Se o dash terminou, preparar próximo cooldown
            if not self._lateral_active:
                self._lateral_travelled = 0.0
                self._lateral_cooldown_timer = random.uniform(
                    self.lateral_cooldown_min,
                    self.lateral_cooldown_max,
                )
            return

        # 2) Não estamos em dash → contar cooldown até ao próximo
        self._lateral_cooldown_timer -= dt_seconds
        if self._lateral_cooldown_timer > 0.0:
            return

        # 3) Arrancar um novo dash
        player = getattr(game, "player", None)
        direction = 0
        if player:
            if player.rect.centerx < self.rect.centerx:
                direction = -1
            elif player.rect.centerx > self.rect.centerx:
                direction = 1

        # Se por alguma razão estiver alinhado, escolhe aleatório
        if direction == 0:
            direction = random.choice([-1, 1])

        self._lateral_direction = direction
        self._lateral_active = True
        self._lateral_travelled = 0.0

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

        # -----------------------------
        # 1) Entrada do boss (delay + descida)
        # -----------------------------
        if self.entering:
            # 1.a) Delay inicial: treme e arranca já a música do boss
            if self.entry_timer > 0.0:
                self.entry_timer -= dt_seconds

                # Arrancar música do boss no primeiro frame de tremor
                if not self.music_started:
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
                                "bosstheme.mp3",
                            )
                            snd.play_music(music_file)
                        except Exception:
                            pass
                    self.music_started = True

                # Tremor de ecrã durante o delay
                duration = getattr(config, "BOSS_ENTRY_SHAKE_DURATION", 0.15)
                intensity = getattr(config, "BOSS_ENTRY_SHAKE_INTENSITY", 6.0)
                game.trigger_camera_shake(duration, intensity)

                return

            # 1.b) Depois do delay → descer até ao target_y
            self.rect.y += int(self.entry_speed * dt_seconds)
            if self.rect.y >= self.target_y:
                self.rect.y = self.target_y
                self.entering = False

            # Enquanto está na fase de entrada (delay + descida) não faz ataques
            return

        # -----------------------------
        # 2) Hover cima/baixo + dashes laterais
        # -----------------------------
        self._hover_phase += self.hover_speed * dt_seconds
        offset = math.sin(self._hover_phase) * self.hover_amplitude
        self.rect.y = int(self.hover_center_y + offset)

        # Movimento lateral ocasional
        self._update_lateral_movement(dt_seconds, game)

        # -----------------------------
        # 3) Ataques (tiros / granadas)
        # -----------------------------
        self._time_since_last_shot += dt_seconds
        if self._time_since_last_shot >= self._next_shot_interval:
            self._time_since_last_shot = 0.0
            self._next_shot_interval = self._random_shot_interval()
            self._do_random_attack(game)

    def _do_random_attack(self, game) -> None:
        """
        Escolhe um dos “ataques” disponíveis.
        """
        if not game or not game.player:
            return

        patterns = [
            self._shoot_straight,
            self._shoot_spread,
            self._shoot_down,
            self._throw_grenades,   # padrão: 3 granadas
        ]
        attack = random.choice(patterns)
        attack(game)

    # --------------------------- #
    # Padrões de disparo (balas)
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
    # Padrão de granadas
    # --------------------------- #

    def _throw_grenades(self, game):
        """
        Lança várias granadas para baixo, com offsets na horizontal.

        - Número de granadas: aleatório entre 2 e 7 (por omissão).
        - Direcção: mistura de esquerda/direita, garantindo pelo menos 1
          para cada lado se houver 2 ou mais.
        - As granadas têm owner="boss", logo:
            * ignoram TMX (pela tua lógica em Game.update_granades)
            * explodem por impacto (chão / player), não por temporizador.
        """
        if not game or not hasattr(game, "granades"):
            return

        # Número ALEATÓRIO de granadas por ataque (configurável se quiseres depois)
        min_count = getattr(config, "BOSS_GRENADE_MIN_COUNT", 2)
        max_count = getattr(config, "BOSS_GRENADE_MAX_COUNT", 7)

        try:
            min_count = int(min_count)
            max_count = int(max_count)
        except Exception:
            min_count, max_count = 2, 7

        if max_count < min_count:
            max_count = min_count

        count = max(1, random.randint(min_count, max_count))

        spacing = getattr(config, "BOSS_GRENADE_SPACING", 40)

        base_x = self.rect.centerx
        y = self.rect.bottom

        # Garante pelo menos uma granada para cada lado se houver 2 ou mais
        if count >= 2:
            directions = [-1, 1]  # uma esquerda, uma direita garantidas
            while len(directions) < count:
                directions.append(random.choice([-1, 1]))
        else:
            directions = [random.choice([-1, 1])]

        for i in range(count):
            # Espalha as granadas em leque à volta do centro do boss
            offset = (i - (count - 1) / 2) * spacing
            direction = directions[i]

            g = Granade(
                x=base_x + offset,
                y=y,
                direction=direction,
                owner="boss",
            )

            # Opcional: dano das granadas do boss pode ser aumentado
            try:
                dmg_mult = float(
                    getattr(config, "BOSS_GRENADE_DAMAGE_MULTIPLIER", 1.0)
                )
                g.damage = int(g.damage * dmg_mult)
            except Exception:
                pass

            game.granades.append(g)

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
