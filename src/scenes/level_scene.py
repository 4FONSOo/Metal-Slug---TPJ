# src/scenes/level_scene.py
import pygame
from scene import Scene
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK
from entity.player import Player
from typing import TYPE_CHECKING
import resources

if TYPE_CHECKING:
    from game_state import Game

class LevelScene(Scene):
    def __init__(self, game_context: 'Game'):
        super().__init__(game_context)
        
        # Grupos de Sprites
        self.all_sprites = pygame.sprite.Group()
        
        # O jogador
        self.player = Player(100, SCREEN_HEIGHT - 64) 
        self.all_sprites.add(self.player)

        # Câmera / Deslocamento do Mundo (World Offset)
        # Este valor representa o quanto o mundo se moveu para a esquerda (positivo)
        self.camera_offset_x = 0 
        
        # Mundo (simulação de um nível maior que o ecrã)
        self.world_width = 3000 
        
        # Arte Placeholder para o Fundo (Duas imagens lado a lado)
        self.bg_color = (100, 100, 255) # Céu azul
        self.ground_height = 64
        self.ground_color = (50, 200, 50) # Chão verde

    def handle_input(self, events: list[pygame.event.Event]):
        self.player.handle_input(events)

    def update(self, dt: float):
        # 1. Atualiza o jogador
        self.player.update(dt)
        
        # 2. Atualiza a Câmera (O "Scrolling" do Metal Slug)
        
        # Define um "Dead Zone" (Zona Morta) no centro do ecrã.
        # Se o jogador sair desta zona, a câmera move-se.
        dead_zone_left = SCREEN_WIDTH // 3
        dead_zone_right = SCREEN_WIDTH * 2 // 3
        
        # Câmera segue o jogador (Horizontal Scroll)
        player_screen_x = self.player.rect.x - self.camera_offset_x
        
        # Se o jogador se mover para a direita e sair da zona morta
        if player_screen_x > dead_zone_right:
            # Move o offset para a direita (o mundo move-se para a esquerda)
            self.camera_offset_x += player_screen_x - dead_zone_right
            
        # Se o jogador se mover para a esquerda e sair da zona morta
        elif player_screen_x < dead_zone_left:
            # Move o offset para a esquerda (o mundo move-se para a direita)
            self.camera_offset_x += player_screen_x - dead_zone_left

        # Limitar o offset da câmera ao início do mundo (não pode ir para trás do 0)
        self.camera_offset_x = max(0, self.camera_offset_x)
        
        # Limitar o offset da câmera ao fim do mundo
        max_offset = self.world_width - SCREEN_WIDTH
        self.camera_offset_x = min(self.camera_offset_x, max_offset)
        
        # Garante que o jogador não ultrapasse o limite do mundo
        if self.player.rect.right > self.world_width:
             self.player.rect.right = self.world_width
             
        if self.player.rect.left < 0:
            self.player.rect.left = 0
            
    def draw_background(self, screen: pygame.Surface):
        """Desenha o background e o chão, aplicando o offset da câmera."""
        # Preenche o fundo (Céu)
        screen.blit(resources.SPRITES['level1_bg'], (0, 0))
        
        # Desenha o chão
        # A área do chão deve ser estendida pelo tamanho do mundo
        ground_rect = pygame.Rect(
            0 - self.camera_offset_x, # Aplica o offset X
            SCREEN_HEIGHT - self.ground_height, 
            self.world_width, # Desenha com o tamanho total do mundo
            self.ground_height
        )
        pygame.draw.rect(screen, self.ground_color, ground_rect)
        
        # Simulação de repetição de background (para arte real)
        # Se estivesse a usar uma imagem real, repetia o desenho da imagem 
        # offset_bg = (self.camera_offset_x * 0.5) % 800 # Exemplo de parallax
        # screen.blit(self.bg_image, (-offset_bg, 0))

    def draw(self, screen: pygame.Surface):
        # 1. Desenha o Background
        self.draw_background(screen)

        # 2. Desenha o Jogador e Outras Entidades
        for sprite in self.all_sprites:
            # Calcula a posição de desenho na tela aplicando o offset da câmera
            draw_pos = sprite.rect.topleft - pygame.math.Vector2(self.camera_offset_x, 0)
            screen.blit(sprite.image, draw_pos)