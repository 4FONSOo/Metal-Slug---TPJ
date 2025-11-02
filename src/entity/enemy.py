# Entity/enemy.py
# Inimigo simples: patrulha e salta periodicamente

import pygame
import random
from config import HEIGHT

ENEMY_SPEED = 2
ENEMY_JUMP_SPEED = -12
ENEMY_GRAVITY = 1
ENEMY_JUMP_INTERVAL = (2000, 5000)  # intervalo em milissegundos
ENEMY_MAX_HP = 100


class Enemy:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.direction = random.choice([-1, 1])
        self.platforms = []
        self.last_jump = pygame.time.get_ticks()
        self.jump_delay = random.randint(*ENEMY_JUMP_INTERVAL)
        self.hp = ENEMY_MAX_HP
        self.alive = True

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
        # movimento horizontal
        self.rect.x += self.direction * ENEMY_SPEED

        # inverter direção ao bater numa parede
        for plat in self.platforms:
            if self.rect.colliderect(plat):
                if self.direction > 0:
                    self.rect.right = plat.left
                else:
                    self.rect.left = plat.right
                self.direction *= -1
                break

    def maybe_jump(self):
        """Salta de vez em quando"""
        now = pygame.time.get_ticks()
        if now - self.last_jump >= self.jump_delay:
            self.vel_y = ENEMY_JUMP_SPEED
            self.last_jump = now
            self.jump_delay = random.randint(*ENEMY_JUMP_INTERVAL)

    def take_damage(self, amount):
        """Reduz HP"""
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    def update(self):
        if not self.alive:
            return

        self.move()
        self.maybe_jump()
        self.apply_gravity()

    def draw(self, screen, camera_x):
        if not self.alive:
            return

        # vira sprite conforme direção
        img = self.image
        if self.direction < 0:
            img = pygame.transform.flip(self.image, True, False)
        screen.blit(img, (self.rect.x - camera_x, self.rect.y))

        # desenha barra de HP
        self.draw_health_bar(screen, camera_x)

    def draw_health_bar(self, screen, camera_x):
        bar_width = 40
        bar_height = 6
        x = self.rect.centerx - bar_width // 2 - camera_x
        y = self.rect.top - 10
        fill = int(bar_width * (self.hp / ENEMY_MAX_HP))

        # cor de acordo com HP
        if self.hp > 60:
            color = (0, 255, 0)
        elif self.hp > 30:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)

        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (x, y, fill, bar_height))
