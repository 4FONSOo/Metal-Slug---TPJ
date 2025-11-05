import pygame

class Projectile:
    def __init__(self, x, y, direction, speed=14, damage=10,
                 color=(255, 60, 60), size=(20, 6), max_range=None):
        """
        Representa um projétil simples.
        :param max_range: distância máxima (px) antes de desaparecer. 
                          Se None, será definido dinamicamente.
        """
        self.rect = pygame.Rect(x, y, *size)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.color = color
        self.alive = True
        self.travelled = 0
        self.max_range = max_range  # pode ser None

    def update(self):
        """Movimenta o projétil e verifica se passou o alcance máximo"""
        move = self.speed * self.direction
        self.rect.x += move
        self.travelled += abs(move)

        # se max_range estiver definido, verifica
        if self.max_range is not None and self.travelled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_x):
        """Desenha o projétil (vermelho provisório)"""
        pygame.draw.rect(screen, self.color, self.rect.move(-camera_x, 0))
