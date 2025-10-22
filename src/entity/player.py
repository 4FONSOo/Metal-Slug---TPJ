# src/entity/player.py
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
import resources

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.original_image = resources.get_sprite('player_idle')
        self.image = pygame.transform.scale(self.original_image, (48, 64))
        self.rect = self.image.get_rect(midbottom=(x, y))

        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 5
        self.gravity = 0.8
        self.on_ground = False
        
        self.is_moving_right = False
        self.is_moving_left = False

    def handle_input(self, events):
        keys = pygame.key.get_pressed()
        self.is_moving_right = keys[pygame.K_RIGHT]
        self.is_moving_left = keys[pygame.K_LEFT]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.on_ground:
                    self.velocity.y = -15 
                    self.on_ground = False

    def apply_gravity(self):
        self.velocity.y += self.gravity
        if self.velocity.y > 10:
            self.velocity.y = 10

    def update(self, dt):
        if self.is_moving_right:
            self.velocity.x = self.speed
        elif self.is_moving_left:
            self.velocity.x = -self.speed
        else:
            self.velocity.x = 0
            
        self.apply_gravity()

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        
        if self.rect.bottom >= SCREEN_HEIGHT - 64: 
            self.rect.bottom = SCREEN_HEIGHT - 64
            self.velocity.y = 0
            self.on_ground = True
        else:
            self.on_ground = False
