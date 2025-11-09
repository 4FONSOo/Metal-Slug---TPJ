import os
import pygame
from config import *  # ASSETS_DIR, BACKGROUND_FILE, HEIGHT, BACKGROUND_WIDTH_MANUAL, BACKGROUND_HEIGHT_MANUAL


# Pasta Assets

def find_asset(filename):
    """Procura recursivamente dentro de ASSETS_DIR e devolve o caminho completo."""
    for root, _, files in os.walk(ASSETS_DIR):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"Asset '{filename}' não encontrado em {ASSETS_DIR}")


# Background

def load_background():
    bg_path = find_asset(BACKGROUND_FILE)
    background = pygame.image.load(bg_path).convert_alpha()
    bg_width = BACKGROUND_WIDTH_MANUAL or background.get_width()
    bg_height = BACKGROUND_HEIGHT_MANUAL or HEIGHT
    background = pygame.transform.scale(background, (bg_width, bg_height))
    return background, bg_width, bg_height


# Jogador (Versão original -> TESTES ONLY)

def load_player(width, height, base_name="player_2"):
    filename = f"{base_name}.png"
    path = find_asset(filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (width, height))


# JOGADOR (Versão animada Afonso -> Final )

def load_player_sprites(width, height, character="player1"):

    import os

    base_path = os.path.join(ASSETS_DIR, "player", character)
    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"[Erro] Pasta da personagem não encontrada: {base_path}")

    folder_to_stem = {
        "player1": "marco",
        "player2": "tarma",
    }
    stems_to_try = []
    if character in folder_to_stem:
        stems_to_try.append(folder_to_stem[character])
        stems_to_try.append(character)

    torso = None
    used_stem = None
    for stem in stems_to_try:
        torso_name = f"tronco_{stem}.png"
        torso_path = os.path.join(base_path, torso_name)
        if os.path.isfile(torso_path):
            used_stem = stem
            torso = pygame.image.load(torso_path).convert_alpha()
            torso = pygame.transform.smoothscale(torso, (width, height // 2))
            break

    if torso is None:
        exp = " ou ".join([f"'tronco_{s}.png'" for s in stems_to_try])
        #raise FileNotFoundError(f"[Erro] Onde está o {base_path}. Era isto: {exp}")

    idle_legs, run_legs = [], []
    for fname in sorted(os.listdir(base_path)):
        if not fname.lower().endswith(".png"):
            continue
        lower = fname.lower()
        if lower.startswith(f"idlelegs_{used_stem}"):
            img = pygame.image.load(os.path.join(base_path, fname)).convert_alpha()
            img = pygame.transform.smoothscale(img, (width, height // 2))
            idle_legs.append(img)
        elif lower.startswith(f"runlegs_{used_stem}"):
            img = pygame.image.load(os.path.join(base_path, fname)).convert_alpha()
            img = pygame.transform.smoothscale(img, (width, height // 2))
            run_legs.append(img)

    if not idle_legs:
        raise FileNotFoundError(f"[Erro] Onde estão sprites idlelegs_{used_stem}* em {base_path}")
    if not run_legs:
        raise FileNotFoundError(f"[Erro] Onde estão sprites runlegs_{used_stem}* em {base_path}")

    print(f"[DEBUG Sprites] pasta={character} stem={used_stem} -> idle={len(idle_legs)} run={len(run_legs)}")

    return {
        "torso": torso,
        "idle_legs": idle_legs,
        "run_legs": run_legs,
        "legs_height": height // 2,
        "torso_height": height // 2,
    }

# Inimigos

def load_enemy(width=80, height=80, filename="rebel1.png"):
    enemy_dir = os.path.join(ASSETS_DIR, "enemy")
    path = os.path.join(enemy_dir, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"[resource] Inimigo onde está: {path}")

    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (width, height))


# Sons

def load_sound_path(filename):
    sounds_dir = os.path.join(ASSETS_DIR, "sounds")
    path = os.path.join(sounds_dir, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"[resource] Som não encontrado: {path}")

    return os.path.abspath(path)
