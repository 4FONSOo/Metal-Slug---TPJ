# src/resources.py
import pygame
import os
from config import PATH_ASSETS # Importa o caminho base para os assets

# Padrão Sugerido: Module/Singleton (para garantir que os recursos só são carregados uma vez)

# Dicionário global para armazenar todas as imagens carregadas
SPRITES = {}

def load_image(file_name, colorkey=None):
    """
    Carrega uma imagem do diretório de assets.
    """
    path = os.path.normpath(os.path.join(PATH_ASSETS, file_name))
    print(f"[DEBUG] Tentando carregar: {path}")  # Mostra o caminho exato no terminal
    
    try:
        image = pygame.image.load(path).convert_alpha()  # convert_alpha para transparência
    except FileNotFoundError:
        print(f"[ERRO] Ficheiro não encontrado: {path}")
        raise
    except pygame.error as message:
        print(f"[ERRO Pygame] Não foi possível carregar a imagem: {path}")
        raise message
    
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))  # Define o pixel superior esquerdo como cor-chave
        image.set_colorkey(colorkey, pygame.RLEACCEL)
        
    return image

def load_resources():
    """
    Função principal para carregar todos os recursos do jogo.
    TODO: Mudar 'placeholder.png' para os seus ficheiros reais.
    """
    global SPRITES
    
    SPRITES['player_idle'] = load_image(os.path.join('player', 'player1', 'player_idle.png'))
    
    SPRITES['level1_bg'] = load_image(os.path.join('background', 'level1_bg.png'))
    
    # Exemplo: Adicionar mais frames de animação do jogador aqui:
    # SPRITES['player_run_1'] = load_image(os.path.join('player', 'player_run_1.png'))
    # SPRITES['player_run_2'] = load_image(os.path.join('player', 'player_run_2.png'))
    
    print("Recursos carregados com sucesso!")

def get_sprite(name):
    """
    Acede a um sprite carregado pelo seu nome.
    """
    return SPRITES.get(name)