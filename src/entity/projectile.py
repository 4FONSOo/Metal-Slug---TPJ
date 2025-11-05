# src/entity/projectile.py
import pygame

PROJECTILE_SPEED = 12


class Projectile:
    def __init__(self, x, y, dir_x, dir_y, max_range=2000, color=None, damage=10):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.start_x = x
        self.start_y = y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed = PROJECTILE_SPEED
        self.alive = True
        self.max_range = max_range
        self.damage = damage
        self.color = color or (255, 0, 0)

        # efeito de impacto
        self.hit_flash = 0
        self.flash_color = (255, 255, 200)

    def update(self):
        if not self.alive:
            # animação curta do flash de impacto
            if self.hit_flash > 0:
                self.hit_flash -= 1
            return

        self.rect.x += self.dir_x * self.speed
        self.rect.y += self.dir_y * self.speed

        distance = abs(self.rect.x - self.start_x) + abs(self.rect.y - self.start_y)
        if distance > self.max_range:
            self.alive = False
            self.hit_flash = 0

    def draw(self, screen, camera_x):
        # se o projétil já morreu, pode mostrar o flash
        if not self.alive:
            if self.hit_flash > 0:
                radius = 6 + (2 - self.hit_flash) * 2
                pygame.draw.circle(
                    screen,
                    self.flash_color,
                    (self.rect.centerx - camera_x, self.rect.centery),
                    radius,
                )
                self.hit_flash -= 1
            return

        # desenha projétil ativo
        if self.color == (100, 200, 255):
            # 🔵 jogador — bolinha
            pygame.draw.circle(
                screen, self.color, (self.rect.centerx - camera_x, self.rect.centery), 5
            )
        else:
            # 🔴 inimigo — quadrado
            pygame.draw.rect(
                screen,
                self.color,
                (self.rect.x - camera_x, self.rect.y, self.rect.width, self.rect.height),
            )

    def trigger_hit(self):
        """Ativa o flash de impacto (chamado quando há colisão)."""
        self.alive = False
        self.hit_flash = 2
