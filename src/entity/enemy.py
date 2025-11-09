import pygame
import random
from config import HEIGHT
from resource import load_enemy
from entity.projectile import Projectile

ENEMY_GRAVITY = 1
ENEMY_JUMP_INTERVAL = (2000, 5000)
ENEMY_MAX_HP = 100


class Enemy:
    def __init__(self, image, x, y):
        
        self.scale = getattr(self, "scale", 1.0)
        if self.scale != 1.0:
            w = int(image.get_width() * self.scale)
            h = int(image.get_height() * self.scale)
            image = pygame.transform.smoothscale(image, (w, h))
        self.image = image

        # Orientação, parece que resolvi, até ver!!!!!
        self.faces_right = getattr(self, "faces_right", True)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.direction = random.choice([-1, 1])
        self.platforms = []
        self.last_jump = pygame.time.get_ticks()
        self.jump_delay = random.randint(*ENEMY_JUMP_INTERVAL)
        self.hp = ENEMY_MAX_HP
        self.alive = True

        self.min_x = x - 100
        self.max_x = x + 100
        self.speed = getattr(self, "speed", 2.0)
        self.damage = getattr(self, "damage", 10)
        self.points = getattr(self, "points", 100)
        self.shoot_interval = getattr(self, "shoot_interval", (3000, 6000))
        self.last_shot = pygame.time.get_ticks()

    def set_platforms(self, platforms):
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
        return on_ground

    def move(self):
        
        #método para tentar para tremeliques

        margin = 5
        self.rect.x += self.direction * self.speed
        if self.direction > 0 and self.rect.right > self.max_x - margin:
            self.direction = -1
        elif self.direction < 0 and self.rect.left < self.min_x + margin:
            self.direction = 1

    def maybe_jump(self):
        now = pygame.time.get_ticks()
        if now - self.last_jump >= self.jump_delay:
            patrol_dist = self.max_x - self.min_x
            jump_height = -10 - int((patrol_dist / 100) * 2)
            jump_height = max(-18, min(jump_height, -10))
            self.vel_y = jump_height
            self.last_jump = now
            self.jump_delay = random.randint(*ENEMY_JUMP_INTERVAL)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    def update(self):
        if not self.alive:
            return
        self.move()
        self.maybe_jump()
        self.apply_gravity()

    def _needs_flip(self) -> bool:
        if self.faces_right:
            return self.direction < 0
        else:
            return self.direction > 0

    def draw(self, screen, camera_x):
        if not self.alive:
            return
        img = pygame.transform.flip(self.image, self._needs_flip(), False)
        screen.blit(img, (self.rect.x - camera_x, self.rect.y))
        self.draw_health_bar(screen, camera_x)

    def draw_health_bar(self, screen, camera_x):
        bar_width = 40
        bar_height = 6
        x = self.rect.centerx - bar_width // 2 - camera_x
        y = self.rect.top - 10
        fill = int(bar_width * (self.hp / ENEMY_MAX_HP))
        color = (0, 255, 0) if self.hp > 60 else (255, 255, 0) if self.hp > 30 else (255, 0, 0)
        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (x, y, fill, bar_height))

    def maybe_shoot(self, projectiles, bg_width):
        pass

class EnemySoldier(Enemy):
    faces_right = False
    scale = 0.95
    speed = 2.0
    damage = 10
    points = 100
    shoot_interval = (3000, 6000)

    def maybe_shoot(self, projectiles, bg_width):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 30)
            sy = self.rect.centery
            p = Projectile(sx, sy, self.direction, 0, max_range=bg_width, color=(255, 50, 50), damage=4)
            projectiles.append(p)
            self.last_shot = now


class EnemyShooter(Enemy):
    faces_right = False
    scale = 1.0
    speed = 1.8
    damage = 20
    points = 150
    shoot_interval = (2000, 4000)

    def maybe_shoot(self, projectiles, bg_width):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 40)
            sy = self.rect.centery
            p = Projectile(sx, sy, self.direction, 0, max_range=bg_width, color=(255, 50, 50), damage=10)
            projectiles.append(p)
            self.last_shot = now


class EnemyHeavy(Enemy):
    faces_right = False
    scale = 1.15
    speed = 1.2
    damage = 30
    points = 200
    shoot_interval = (3000, 5000)

    def maybe_shoot(self, projectiles, bg_width):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 50)
            sy = self.rect.centery
            p = Projectile(sx, sy, self.direction, 0, max_range=bg_width, color=(255, 50, 50), damage=20)
            projectiles.append(p)
            self.last_shot = now


class EnemyFast(Enemy):
    faces_right = False
    scale = 0.85
    speed = 3.5
    damage = 15
    points = 120
    shoot_interval = (3500, 6500)

    def maybe_shoot(self, projectiles, bg_width):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_interval):
            sx = self.rect.centerx + (self.direction * 30)
            sy = self.rect.centery
            p = Projectile(sx, sy, self.direction, 0, max_range=bg_width, color=(255, 50, 50), damage=2)
            projectiles.append(p)
            self.last_shot = now


class EnemyManager:
    def __init__(self, bg_width, platforms):
        self.bg_width = bg_width
        self.platforms = platforms
        self.enemies = []
        self.total_spawns = 0
        self.max_spawns = 50
        self.max_active = 10
        self.projectiles = []

    def spawn_enemy_random(self):
        if self.total_spawns >= self.max_spawns or len(self.enemies) >= self.max_active:
            return
        p = random.random()
        if p < 0.15:
            cls, sprite = EnemyHeavy, "Rebel3.png"
        elif p < 0.45:
            cls, sprite = EnemyShooter, "Rebel2.png"
        else:
            cls, sprite = random.choice([(EnemySoldier, "Rebel1.png"), (EnemyFast, "Rebel4.png")])
        x = random.randint(100, self.bg_width - 100)
        y = random.randint(50, HEIGHT // 2)
        img = load_enemy(80, 80, sprite)
        e = cls(img, x, y)
        e.set_platforms(self.platforms)
        patrol = random.randint(150, 350)
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

    def draw(self, screen, camera_x):
        for e in self.enemies:
            e.draw(screen, camera_x)

    def get_enemies(self):
        return self.enemies

    def get_projectiles(self):
        active = [p for p in self.projectiles if p and p.alive]
        self.projectiles = [p for p in self.projectiles if p and p.alive]
        return active
