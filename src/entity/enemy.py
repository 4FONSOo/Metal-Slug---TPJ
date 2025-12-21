# entity/enemy.py

import random
import pg_engine as pg

from config import (
    HEIGHT,
    ENEMY_GRAVITY,
    ENEMY_JUMP_INTERVAL_DEFAULT,
    ENEMY_MAX_HP,
    ENEMY_CONTACT_PLAYER_FACTOR,
    ENEMY_CONTACT_SELF_DAMAGE,
    ENEMY_MANAGER_MAX_SPAWNS_DEFAULT,
    ENEMY_MANAGER_MAX_ACTIVE_DEFAULT,
    ENEMY_MANAGER_PATROL_MIN,
    ENEMY_MANAGER_PATROL_MAX,
    ENEMY_MANAGER_SPAWN_X_MARGIN,
    ENEMY_MANAGER_SPAWN_Y_MIN,
    ENEMY_PROJECTILE_COLOR,
    ENEMY_PROJECTILE_SPEED,
)
from resource import load_enemy
from entity.projectile import Projectile


class Enemy:
    def __init__(self, image, x: int, y: int, damage_multiplier: float = 1.0):
        self.scale = getattr(self, "scale", 1.0)
        if self.scale != 1.0:
            w = int(image.get_width() * self.scale)
            h = int(image.get_height() * self.scale)
            image = pg.scale_image(image, (w, h))
        self.image = image

        self.faces_right = getattr(self, "faces_right", True)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.direction = random.choice([-1, 1])
        self.platforms: list[pg.Rect] = []
        self.on_ground = False

        self.jump_interval = getattr(self, "jump_interval", ENEMY_JUMP_INTERVAL_DEFAULT)
        self.jump_force_min = getattr(self, "jump_force_min", -18)
        self.jump_force_max = getattr(self, "jump_force_max", -10)

        self.last_jump = pg.time_get_ticks()
        self.jump_delay = random.randint(*self.jump_interval)

        self.max_hp = ENEMY_MAX_HP
        self.hp = self.max_hp
        self.alive = True

        self.min_x = x - 100
        self.max_x = x + 100
        self.speed = getattr(self, "speed", 2.0)

        self.base_damage = getattr(self, "damage", 10)
        self.damage = self.base_damage * damage_multiplier

        self.points = getattr(self, "points", 100)

        self.shoot_interval = getattr(self, "shoot_interval", (3000, 6000))
        self.last_shot = pg.time_get_ticks()

    def contact_damage_to_player(self) -> float:
        return self.damage * ENEMY_CONTACT_PLAYER_FACTOR

    def contact_self_damage(self) -> float:
        return ENEMY_CONTACT_SELF_DAMAGE

    def set_platforms(self, platforms: list[pg.Rect]):
        self.platforms = platforms

    def apply_gravity(self):
        self.vel_y += ENEMY_GRAVITY
        self.rect.y += self.vel_y

        on_ground = False

        for plat in self.platforms:
            if self.rect.colliderect(plat) and self.rect.bottom - self.vel_y <= plat.top:
                self.rect.bottom = plat.top
                self.vel_y = 0
                on_ground = True

        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.vel_y = 0
            on_ground = True

        self.on_ground = on_ground
        return on_ground

    def move(self):
        margin = 5
        self.rect.x += self.direction * self.speed

        if self.direction > 0 and self.rect.right > self.max_x - margin:
            self.direction = -1
        elif self.direction < 0 and self.rect.left < self.min_x + margin:
            self.direction = 1

    def maybe_jump(self):
        if not self.on_ground:
            return

        now = pg.time_get_ticks()
        if now - self.last_jump >= self.jump_delay:
            patrol_dist = self.max_x - self.min_x
            jump_height = self.jump_force_max - int((patrol_dist / 100) * 2)
            jump_height = max(self.jump_force_min, min(jump_height, self.jump_force_max))

            self.vel_y = jump_height
            self.last_jump = now
            self.jump_delay = random.randint(*self.jump_interval)

    def take_damage(self, amount: float):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    def update(self):
        if not self.alive:
            return
        self.move()
        self.apply_gravity()
        self.maybe_jump()

    def _needs_flip(self) -> bool:
        if self.faces_right:
            return self.direction < 0
        else:
            return self.direction > 0

    def draw(self, screen, camera_x: int):
        if not self.alive:
            return

        img = pg.flip_image(self.image, self._needs_flip(), False)
        screen.blit(img, (self.rect.x - camera_x, self.rect.y))
        self.draw_health_bar(screen, camera_x)

    def draw_health_bar(self, screen, camera_x: int):
        bar_width = 40
        bar_height = 6
        x = self.rect.centerx - bar_width // 2 - camera_x
        y = self.rect.top - 10
        fill = int(bar_width * (self.hp / ENEMY_MAX_HP))

        if self.hp > 60:
            color = (0, 255, 0)
        elif self.hp > 30:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)

        pg.draw_rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
        pg.draw_rect(screen, color, (x, y, fill, bar_height))

    def maybe_shoot(self, projectiles: list, bg_width: int):
        pass


class EnemySoldier(Enemy):
    faces_right = False
    scale = 0.95
    speed = 2.0
    damage = 10
    points = 100
    shoot_interval = (3000, 6000)

    jump_interval = (600, 1200)
    jump_force_min = -16
    jump_force_max = -10

    def maybe_shoot(self, projectiles: list, bg_width: int):
        now = pg.time_get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 30)
            sy = self.rect.centery

            p = Projectile(
                sx,
                sy,
                self.direction,
                0,
                speed=ENEMY_PROJECTILE_SPEED,
                max_range=bg_width,
                color=ENEMY_PROJECTILE_COLOR,
                damage=4,
            )
            projectiles.append(p)
            self.last_shot = now


class EnemyShooter(Enemy):
    faces_right = False
    scale = 1.0
    speed = 1.8
    damage = 20
    points = 150
    shoot_interval = (2000, 4000)

    jump_interval = (1400, 2400)
    jump_force_min = -14
    jump_force_max = -9

    def maybe_shoot(self, projectiles: list, bg_width: int):
        now = pg.time_get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 40)
            sy = self.rect.centery

            p = Projectile(
                sx,
                sy,
                self.direction,
                0,
                speed=ENEMY_PROJECTILE_SPEED,
                max_range=bg_width,
                color=ENEMY_PROJECTILE_COLOR,
                damage=10,
            )
            projectiles.append(p)
            self.last_shot = now


class EnemyHeavy(Enemy):
    faces_right = False
    scale = 1.15
    speed = 1.2
    damage = 30
    points = 200
    shoot_interval = (3000, 5000)

    jump_interval = (1800, 3000)
    jump_force_min = -13
    jump_force_max = -8

    def maybe_shoot(self, projectiles: list, bg_width: int):
        now = pg.time_get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 50)
            sy = self.rect.centery

            p = Projectile(
                sx,
                sy,
                self.direction,
                0,
                speed=ENEMY_PROJECTILE_SPEED,
                max_range=bg_width,
                color=ENEMY_PROJECTILE_COLOR,
                damage=20,
            )
            projectiles.append(p)
            self.last_shot = now


class EnemyFast(Enemy):
    faces_right = False
    scale = 0.85
    speed = 7.5
    damage = 15
    points = 120
    shoot_interval = (1500, 3500)

    jump_interval = (400, 900)
    jump_force_min = -20
    jump_force_max = -12

    def maybe_shoot(self, projectiles: list, bg_width: int):
        now = pg.time_get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 30)
            sy = self.rect.centery

            p = Projectile(
                sx,
                sy,
                self.direction,
                0,
                speed=ENEMY_PROJECTILE_SPEED,
                max_range=bg_width,
                color=ENEMY_PROJECTILE_COLOR,
                damage=2,
            )
            projectiles.append(p)
            self.last_shot = now


class EnemyManager:
    def __init__(self, bg_width: int, platforms: list[pg.Rect],
                 max_spawns: int | None = None, max_active: int | None = None,
                 damage_multiplier: float = 1.0):
        self.bg_width = bg_width
        self.platforms = platforms
        self.enemies: list[Enemy] = []

        self.total_spawns = 0
        self.max_spawns = max_spawns or ENEMY_MANAGER_MAX_SPAWNS_DEFAULT
        self.max_active = max_active or ENEMY_MANAGER_MAX_ACTIVE_DEFAULT

        self.damage_multiplier = damage_multiplier

        self.projectiles: list[Projectile] = []

    def spawn_enemy_random(self):
        if self.total_spawns >= self.max_spawns or len(self.enemies) >= self.max_active:
            return

        p = random.random()
        if p < 0.15:
            cls, sprite = EnemyHeavy, "Rebel3.png"
        elif p < 0.45:
            cls, sprite = EnemyShooter, "Rebel2.png"
        else:
            cls, sprite = random.choice(
                [
                    (EnemySoldier, "Rebel1.png"),
                    (EnemyFast, "Rebel4.png"),
                ]
            )

        x = random.randint(ENEMY_MANAGER_SPAWN_X_MARGIN, self.bg_width - ENEMY_MANAGER_SPAWN_X_MARGIN)
        y = random.randint(ENEMY_MANAGER_SPAWN_Y_MIN, HEIGHT // 2)

        img = load_enemy(80, 80, sprite)
        e = cls(img, x, y, damage_multiplier=self.damage_multiplier)
        e.set_platforms(self.platforms)

        patrol = random.randint(ENEMY_MANAGER_PATROL_MIN, ENEMY_MANAGER_PATROL_MAX)
        e.min_x = max(0, x - patrol)
        e.max_x = min(self.bg_width, x + patrol)

        self.enemies.append(e)
        self.total_spawns += 1

    def update(self):
        for e in self.enemies:
            e.update()
            e.maybe_shoot(self.projectiles, self.bg_width)

        self.enemies = [e for e in self.enemies if e.alive]

        while len(self.enemies) < self.max_active and self.total_spawns < self.max_spawns:
            self.spawn_enemy_random()

    def draw(self, screen, camera_x: int):
        for e in self.enemies:
            e.draw(screen, camera_x)

    def get_enemies(self) -> list[Enemy]:
        return self.enemies

    def get_projectiles(self) -> list[Projectile]:
        active = [p for p in self.projectiles if p and p.alive]
        self.projectiles = active
        return active
