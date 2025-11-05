import pygame
import config

from config import PLAYER_SPEED, PLAYER_GRAVITY, HEIGHT

PLAYER_MAX_HP = 100

class Player:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.is_jumping = False
        self.jump_held = False
        self.drop_timer = 0
        self.hp = PLAYER_MAX_HP
        self.alive = True
        self.platforms = []
        self.facing = 1
        self.facing_vertical = 0
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.bg_width = 0

    def set_level_limits(self, bg_width):
        self.bg_width = bg_width

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    def draw_health_bar(self, screen, camera_x):
        bar_width = 60
        bar_height = 8
        x = self.rect.centerx - bar_width // 2 - camera_x
        y = self.rect.top - 15
        fill = int(bar_width * (self.hp / self.max_hp))
        color = (0, 255, 0) if self.hp > 60 else (255, 255, 0) if self.hp > 30 else (255, 0, 0)
        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (x, y, fill, bar_height))

    def handle_input(self, keys):
        move_x = 0
        if keys[pygame.K_LEFT]:
            move_x = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            move_x = PLAYER_SPEED
            self.facing = 1

        jump_pressed = keys[pygame.K_UP]
        down_pressed = keys[pygame.K_DOWN]

        if jump_pressed and not self.jump_held and not self.is_jumping:
            if down_pressed:
                self.drop_timer = 10
                self.vel_y = 5
            else:
                self.is_jumping = True
                self.vel_y = getattr(config, "PLAYER_JUMP_SPEED", -15)
            self.jump_held = True
        if not jump_pressed:
            self.jump_held = False

        self.rect.x += move_x
        if self.bg_width:
            self.rect.x = max(0, min(self.rect.x, self.bg_width - self.rect.width))

    def apply_gravity(self):
        self.vel_y += PLAYER_GRAVITY
        self.rect.y += self.vel_y
        ignore_platform = self.drop_timer > 0
        if self.drop_timer > 0:
            self.drop_timer -= 1
        on_ground = self.check_collisions(ignore_platform)
        if on_ground:
            self.is_jumping = False
            self.vel_y = 0

    def check_collisions(self, ignore_platform=False):
        on_ground = False
        for plat in self.platforms:
            if ignore_platform:
                continue
            if self.rect.colliderect(plat) and self.rect.bottom - self.vel_y <= plat.top:
                self.rect.bottom = plat.top
                on_ground = True
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            on_ground = True
        return on_ground
