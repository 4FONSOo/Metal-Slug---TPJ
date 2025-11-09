import pygame
import config

from config import (
    PLAYER_SPEED,
    PLAYER_JUMP_SPEED,
    PLAYER_GRAVITY,
    PLAYER_MAX_HP,
    HEIGHT
)

class Player:
    def __init__(self, x, y, character="marco"):
        
        # Proteção contra tipo erro de ficheiro
        
        if not isinstance(character, str):
            raise TypeError(f"[Player] Waiting for string em 'character', recebeu {character} ({type(character)})")
        
        # Sprites
        
        self.sprites = self.load_sprites(character)
        self.image = pygame.Surface((config.PLAYER_WIDTH, config.PLAYER_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))

        # Animação 
        
        self.leg_state = "idle"  # idle ou run
        self.leg_frame = 0
        self.animation_timer = 0
        self.animation_speed = 100  # ms entre frames

        # Movimento
        
        self.vel_y = 0
        self.is_jumping = False
        self.jump_held = False
        self.drop_timer = 0
        self.moving = False

        # Direção
        
        self.facing = 1 
        self.bg_width = 0

        # HP
        
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.alive = True

        # Plataformas (Não atives neste momento, só para testes)
        
        self.platforms = []
        
        self.update_sprite()

    # Sprites

    def load_sprites(self, character):
        
        from resource import load_player_sprites
        return load_player_sprites(config.PLAYER_WIDTH, config.PLAYER_HEIGHT, character)

    def update_sprite(self):

        self.image.fill((0, 0, 0, 0))

        if self.leg_state == "idle":
            legs_sprite = self.sprites["idle_legs"][self.leg_frame]
        else:
            legs_sprite = self.sprites["run_legs"][self.leg_frame]

        torso_sprite = self.sprites["torso"]

        if self.facing == -1:
            torso_sprite = pygame.transform.flip(torso_sprite, True, False)
            legs_sprite = pygame.transform.flip(legs_sprite, True, False)

        # Combinação

        legs_y = self.image.get_height() - self.sprites["legs_height"]
        overlap = 15
        torso_y = legs_y - self.sprites["torso_height"] + overlap
        self.image.blit(legs_sprite, (0, legs_y))
        self.image.blit(torso_sprite, (0, torso_y))

    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if self.leg_state == "idle":
                self.leg_frame = (self.leg_frame + 1) % len(self.sprites["idle_legs"])
            else:
                self.leg_frame = (self.leg_frame + 1) % len(self.sprites["run_legs"])
            self.update_sprite()

    # Teclas

    def handle_input(self, keys):
        move_x = 0
        self.moving = False

        if keys[pygame.K_LEFT]:
            move_x = -PLAYER_SPEED
            self.facing = -1
            self.moving = True
        if keys[pygame.K_RIGHT]:
            move_x = PLAYER_SPEED
            self.facing = 1
            self.moving = True

        self.leg_state = "run" if self.moving else "idle"

        jump_pressed = keys[pygame.K_UP]
        down_pressed = keys[pygame.K_DOWN]

        if jump_pressed and not self.jump_held and not self.is_jumping:
            if down_pressed:
                self.drop_timer = 10
                self.vel_y = 5
            else:
                self.is_jumping = True
                self.vel_y = PLAYER_JUMP_SPEED
            self.jump_held = True

        if not jump_pressed:
            self.jump_held = False

        # Bloquear a saída da tela

        self.rect.x += move_x
        if self.bg_width:
            self.rect.x = max(0, min(self.rect.x, self.bg_width - self.rect.width))

    # Colisões

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

            if self.rect.colliderect(plat):
                
                if self.vel_y > 0 and self.rect.bottom > plat.top and self.rect.top < plat.top:
                    self.rect.bottom = plat.top
                    on_ground = True
                    self.vel_y = 0
                
                elif self.vel_y < 0 and self.rect.top < plat.bottom and self.rect.bottom > plat.bottom:
                    self.rect.top = plat.bottom
                    self.vel_y = 0
                
                elif self.rect.right > plat.left and self.rect.left < plat.left:
                    self.rect.right = plat.left
                elif self.rect.left < plat.right and self.rect.right > plat.right:
                    self.rect.left = plat.right

        
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            on_ground = True
            self.vel_y = 0

        return on_ground

    # HP

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

    def set_level_limits(self, bg_width):
        self.bg_width = bg_width
