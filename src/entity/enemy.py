# entity/enemy.py
# Sistema modular de inimigos com comportamentos e disparos distintos

import pygame
import random
from config import HEIGHT
from entity.projectile import Projectile


# ------------------- 🔹 Classe Base -------------------
class EnemyBase:
    def __init__(self, image, x, y, hp=100, speed=2, color=(255, 180, 0), shoot_delay=(1500, 3000)):
        # 🔹 Sprite
        self.original_image = pygame.transform.flip(image, True, False)  # corrige se sprite estiver virada
        self.image = self.original_image
        self.rect = self.image.get_rect(topleft=(x, y))

        # 🔹 Física e movimento
        self.vel_y = 0
        self.direction = random.choice([-1, 1])
        self.speed = speed
        self.platforms = []
        self.min_x, self.max_x = 0, 800

        # 🔹 Atributos de combate
        self.hp = hp
        self.max_hp = hp
        self.alive = True
        self.color = color

        # 🔹 Disparo
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = shoot_delay
        self.projectiles = []

        # 🔹 Saltos
        self.last_jump = pygame.time.get_ticks()
        self.jump_delay = random.randint(2000, 5000)

    # ------------------- Movimento -------------------
    def set_platforms(self, platforms):
        self.platforms = platforms

    def move(self):
        self.rect.x += self.direction * self.speed

        # Limites de patrulha
        if self.rect.left <= self.min_x:
            self.rect.left = self.min_x
            self.direction = 1
        elif self.rect.right >= self.max_x:
            self.rect.right = self.max_x
            self.direction = -1

        # Atualiza flip conforme direção
        self.image = pygame.transform.flip(self.original_image, self.direction == -1, False)

    def apply_gravity(self):
        self.vel_y += 1
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

    # ------------------- Ações -------------------
    def maybe_jump(self):
        now = pygame.time.get_ticks()
        if now - self.last_jump >= self.jump_delay:
            self.vel_y = -12
            self.last_jump = now
            self.jump_delay = random.randint(2000, 5000)

    def shoot(self):
        """Disparo genérico"""
        now = pygame.time.get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_delay):
            proj = Projectile(
                self.rect.centerx + (self.direction * 40),
                self.rect.centery,
                self.direction,
                color=self.color
            )
            self.projectiles.append(proj)
            self.last_shot = now

    # ------------------- Ciclo de vida -------------------
    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        if self.hp == 0:
            self.alive = False

    def update(self):
        if not self.alive:
            return
        self.move()
        self.apply_gravity()
        self.maybe_jump()
        self.shoot()
        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

    # ------------------- Render -------------------
    def draw(self, screen, camera_x):
        if not self.alive:
            return
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y))
        self.draw_health_bar(screen, camera_x)
        for p in self.projectiles:
            p.draw(screen, camera_x)

    def draw_health_bar(self, screen, camera_x):
        bar_width = 40
        bar_height = 6
        x = self.rect.centerx - bar_width // 2 - camera_x
        y = self.rect.top - 10
        fill = int(bar_width * (self.hp / self.max_hp))

        if self.hp > self.max_hp * 0.6:
            color = (0, 255, 0)
        elif self.hp > self.max_hp * 0.3:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)

        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (x, y, fill, bar_height))


# ------------------- 🔹 Tipos de Inimigos -------------------

class EnemySoldier(EnemyBase):
    """Inimigo padrão - o atual rebel1"""
    def __init__(self, image, x, y):
        super().__init__(image, x, y, hp=100, speed=2, color=(255, 180, 0))


class EnemyShooter(EnemyBase):
    """Atira com mais frequência e menos HP"""
    def __init__(self, image, x, y):
        super().__init__(image, x, y, hp=80, speed=1, color=(0, 200, 255), shoot_delay=(700, 1200))


class EnemyHeavy(EnemyBase):
    """Projéteis lentos e grandes"""
    def __init__(self, image, x, y):
        super().__init__(image, x, y, hp=200, speed=1, color=(255, 50, 50), shoot_delay=(2500, 4000))

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= random.randint(*self.shoot_delay):
            proj = Projectile(
                self.rect.centerx + (self.direction * 50),
                self.rect.centery,
                self.direction,
                speed=6,
                size=(25, 10),
                damage=20,
                color=self.color
            )
            self.projectiles.append(proj)
            self.last_shot = now


class EnemyFast(EnemyBase):
    """Rápido e fraco"""
    def __init__(self, image, x, y):
        super().__init__(image, x, y, hp=60, speed=4, color=(255, 255, 0), shoot_delay=(3000, 5000))


Enemy = EnemySoldier
