import pygame
from config import *
from scene import Scene
from scenes.menu_scene import MenuScene
import sys
import resources

class Game:
    """
    Mantém o estado/cena atual.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        resources.load_resources()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        
        # O estado atual do jogo, que é uma Scene
        self.current_scene: Scene = None
        
        # Inicializa com a cena do Menu
        self.set_scene(MenuScene(self)) 

    def set_scene(self, new_scene: Scene):
        """Muda o estado/cena atual."""
        if self.current_scene:
            self.current_scene.on_exit()
            
        self.current_scene = new_scene
        self.current_scene.on_enter()

    def run(self):
        """
        O Game Loop principal.
        Padrão: Template Method (A estrutura do loop é fixa)
        """
        while self.running:
            # 1. Input/Eventos
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            
            if self.current_scene:
                self.current_scene.handle_input(events)

            # 2. Update/Lógica
            dt = self.clock.tick(FPS) / 1000.0 # Tempo decorrido (em segundos)
            if self.current_scene:
                self.current_scene.update(dt)

            # 3. Draw/Desenho
            self.screen.fill(BLACK) # Limpa o ecrã
            if self.current_scene:
                self.current_scene.draw(self.screen)
            
            pygame.display.flip()

        pygame.quit()
        sys.exit()