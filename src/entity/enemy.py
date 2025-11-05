import pygame
import random
from config import HEIGHT
from entity.projectile import Projectile

# 🔹 Constantes globais
ENEMY_SPEED = 2
ENEMY_JUMP_SPEED = -12
ENEMY_GRAVITY = 1
ENEMY_JUMP_INTERVAL = (2000, 5000)
ENEMY_MAX_HP = 100


# ---------- 🔹 Classe base ----------
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
        self.score_value = 0
        self.projectiles = []

        # 🔹 Movimento / Patrulha
        self.min_x = None
        self.max_x = None

        # 🔹 Disparo
        self.shoot_timer = pygame.time.get_ticks()
        self.shoot_delay = random.randint(2000, 4000)

    # ---------- Movimento vertical ----------
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

    # ---------- Movimento horizontal ----------
    def move(self):
        self.rect.x += self.direction * ENEMY_SPEED

        if self.min_x is not None and self.rect.left <= self.min_x:
            self.direction = 1
        elif self.max_x is not None and self.rect.right >= self.max_x:
            self.direction = -1

    # ---------- Saltos aleatórios ----------
    def maybe_jump(self):
        now = pygame.time.get_ticks()
        if now - self.last_jump >= self.jump_delay:
            self.vel_y = ENEMY_JUMP_SPEED
            self.last_jump = now
            self.jump_delay = random.randint(*ENEMY_JUMP_INTERVAL)

    # ---------- Dano ----------
    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    # ---------- Disparo padrão ----------
    def maybe_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = now
            self.shoot_delay = random.randint(2000, 4000)
            proj = Projectile(
                self.rect.centerx + (self.direction * 30),
                self.rect.centery,
                self.direction,
                max_range=2000,
            )
            self.projectiles.append(proj)

    # ---------- Atualização ----------
    def update(self):
        if not self.alive:
            return

        self.move()
        self.maybe_jump()
        self.apply_gravity()
        self.maybe_shoot()

        # Atualizar projéteis
        for proj in self.projectiles:
            proj.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

    # ---------- Desenho ----------
    def draw(self, screen, camera_x):
        if not self.alive:
            return

        # 🔹 Corrigido: sprites originais voltadas para a ESQUERDA
        # Viramos apenas quando o inimigo vai para a DIREITA
        img = self.image
        if self.direction > 0:
            img = pygame.transform.flip(self.image, True, False)

        screen.blit(img, (self.rect.x - camera_x, self.rect.y))
        self.draw_health_bar(screen, camera_x)

        # Desenhar projéteis
        for proj in self.projectiles:
            proj.draw(screen, camera_x)

    # ---------- Barra de HP ----------
    def draw_health_bar(self, screen, camera_x):
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

        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (x, y, fill, bar_height))

    def set_platforms(self, platforms):
        self.platforms = platforms


# ---------- 🔹 Subclasses específicas ----------
class EnemySoldier(Enemy):
    def __init__(self, image, x, y):
        super().__init__(image, x, y)
        self.score_value = 100


class EnemyShooter(Enemy):
    def __init__(self, image, x, y):
        super().__init__(image, x, y)
        self.score_value = 150
        self.shoot_delay = random.randint(1000, 3000)

    def maybe_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = now
            self.shoot_delay = random.randint(2000, 4000)
            proj = Projectile(
                self.rect.centerx + (self.direction * 30),
                self.rect.centery - 10,
                self.direction,
                max_range=2000,
            )
            self.projectiles.append(proj)


class EnemyFast(Enemy):
    def __init__(self, image, x, y):
        super().__init__(image, x, y)
        self.score_value = 200
        self.speed_boost = 1.5

    def move(self):
        self.rect.x += self.direction * ENEMY_SPEED * self.speed_boost
        if self.min_x is not None and self.rect.left <= self.min_x:
            self.direction = 1
        elif self.max_x is not None and self.rect.right >= self.max_x:
            self.direction = -1


class EnemyHeavy(Enemy):
    def __init__(self, image, x, y):
        super().__init__(image, x, y)
        self.score_value = 300
        self.hp = ENEMY_MAX_HP * 1.5
        self.shoot_delay = random.randint(3000, 6000)

    def maybe_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = now
            self.shoot_delay = random.randint(3000, 6000)
            proj = Projectile(
                self.rect.centerx + (self.direction * 40),
                self.rect.centery,
                self.direction,
                max_range=2000,
            )
            self.projectiles.append(proj)
