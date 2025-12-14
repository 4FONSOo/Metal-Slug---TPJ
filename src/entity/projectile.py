# entity/projectile.py
"""
Projéctil genérico.
"""

import pg_engine as pg
import config


class Projectile:
    def __init__(
        self,
        x=0,
        y=0,
        dir_x=1,
        dir_y=0,
        speed=None,
        max_range=None,
        color=None,
        damage: int = 10,
    ):
        # Permite pooling: cria uma instância e reusa via reset().
        self.rect = pg.Rect(0, 0, 10, 10)
        self.flash_color = (255, 255, 200)
        self.reset(
            x=x,
            y=y,
            dir_x=dir_x,
            dir_y=dir_y,
            speed=speed,
            max_range=max_range,
            color=color,
            damage=damage,
        )

    def reset(
        self,
        *,
        x=0,
        y=0,
        dir_x=1,
        dir_y=0,
        speed=None,
        max_range=None,
        color=None,
        damage: int = 10,
    ) -> None:
        self.x = float(x)
        self.y = float(y)

        self.start_x = self.x
        self.start_y = self.y

        length_sq = dir_x * dir_x + dir_y * dir_y
        if length_sq == 0:
            self.dir_x = 1.0
            self.dir_y = 0.0
        else:
            length = length_sq ** 0.5
            self.dir_x = dir_x / length
            self.dir_y = dir_y / length

        self.speed = speed if speed is not None else config.PLAYER_PROJECTILE_SPEED
        self.max_range = max_range if max_range is not None else config.PLAYER_PROJECTILE_MAX_RANGE

        self.alive = True
        self.damage = int(damage)
        self.color = color or config.PLAYER_PROJECTILE_COLOR
        self.hit_flash = 0

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def update(self):
        if self.alive:
            self.x += self.dir_x * self.speed
            self.y += self.dir_y * self.speed

            self.rect.centerx = int(self.x)
            self.rect.centery = int(self.y)

            distance = abs(self.x - self.start_x) + abs(self.y - self.start_y)
            if distance > self.max_range:
                self.alive = False
                self.hit_flash = 0
        else:
            if self.hit_flash > 0:
                self.hit_flash -= 1

    def draw(self, screen, camera_x):
        if not self.alive:
            if self.hit_flash > 0:
                radius = 6 + (2 - self.hit_flash) * 2
                pg.draw_circle(
                    screen,
                    self.flash_color,
                    (self.rect.centerx - camera_x, self.rect.centery),
                    radius,
                )
            return

        if self.color == config.PLAYER_PROJECTILE_COLOR:
            pg.draw_circle(
                screen,
                self.color,
                (self.rect.centerx - camera_x, self.rect.centery),
                5,
            )
        else:
            pg.draw_rect(
                screen,
                self.color,
                pg.Rect(
                    self.rect.x - camera_x,
                    self.rect.y,
                    self.rect.width,
                    self.rect.height,
                ),
            )

    def trigger_hit(self):
        self.alive = False
        self.hit_flash = 2
