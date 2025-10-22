# src/scenes/menu_scene.py
import pygame
from scene import Scene
from config import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT
from typing import TYPE_CHECKING
from scenes.level_scene import LevelScene

if TYPE_CHECKING:
    from game_state import Game

# Importe a sua cena de jogo real aqui
# from scenes.level_one_scene import LevelOneScene 

class MenuScene(Scene):
    def __init__(self, game_context: 'Game'):
        super().__init__(game_context)
        self.font = pygame.font.Font(None, 74)
        self.smaller_font = pygame.font.Font(None, 36)
        
    def on_enter(self):
        print("Entrando no Menu.")
        # Se tivéssemos um Resource Manager, carregávamos aqui as imagens do Menu.
        
    def handle_input(self, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # **MUDAR AQUI** para ir para o LevelScene
                    self.game_context.set_scene(LevelScene(self.game_context)) # <---

    def update(self, dt: float):
        # Lógica de animação do menu, se houver
        pass

    def draw(self, screen: pygame.Surface):
        # Desenha o título
        title_surf = self.font.render("CLONE - METAL SLUG (TPJ)", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        screen.blit(title_surf, title_rect)

        # Desenha a instrução
        prompt_surf = self.smaller_font.render("Pressione ENTER para Começar", True, WHITE)
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
        screen.blit(prompt_surf, prompt_rect)