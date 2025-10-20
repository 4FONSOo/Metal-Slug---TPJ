import pygame
from resources import ResourceManager

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.images = ResourceManager.load_image('assets/player_spritesheet.png')
        # implementar animação: dividir a sprite sheet
        self.rect = self.images.get_rect(topleft=pos)
        self.vel = pygame.Vector2(0,0)
        self.speed = 200
        self.on_ground = False
        self.shoot_cooldown = 0.2
        self._time_since_shot = 0

    def handle_input(self, keys):
        self.vel.x = 0
        if keys[pygame.K_LEFT]:
            self.vel.x = -self.speed
        if keys[pygame.K_RIGHT]:
            self.vel.x = self.speed
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = -300

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.handle_input(keys)
        self._time_since_shot += dt
        # gravidade
        self.vel.y += 800 * dt
        self.rect.x += int(self.vel.x * dt)
        self.rect.y += int(self.vel.y * dt)

    def try_shoot(self):
        if self._time_since_shot >= self.shoot_cooldown:
            self._time_since_shot = 0
            # retornar um Projectile instanciado pela Factory
            return True
        return False