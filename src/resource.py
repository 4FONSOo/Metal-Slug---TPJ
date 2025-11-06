# src/resource.py

import os
import pygame
from config import *  # ASSETS_DIR, BACKGROUND_FILE, HEIGHT, BACKGROUND_WIDTH_MANUAL, BACKGROUND_HEIGHT_MANUAL


# ---------- 🔍 UTILIDADES ----------
def find_asset(filename):
    """Procura recursivamente dentro de ASSETS_DIR e devolve o caminho completo."""
    for root, _, files in os.walk(ASSETS_DIR):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"Asset '{filename}' não encontrado em {ASSETS_DIR}")


# ---------- 🌄 BACKGROUND ----------
def load_background():
    bg_path = find_asset(BACKGROUND_FILE)
    background = pygame.image.load(bg_path).convert_alpha()
    bg_width = BACKGROUND_WIDTH_MANUAL or background.get_width()
    bg_height = BACKGROUND_HEIGHT_MANUAL or HEIGHT
    background = pygame.transform.scale(background, (bg_width, bg_height))
    return background, bg_width, bg_height


# ---------- 🧍‍♂️ JOGADOR (clássico) ----------
def load_player(width, height, base_name="player_2"):
    """Carrega sprite do jogador conforme o nome (modo simples)."""
    filename = f"{base_name}.png"
    path = find_asset(filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (width, height))


# ---------- 🧍‍♂️ JOGADOR (modular animado) ----------
def load_player_sprites(width, height, character="player1"):
    """
    Carrega sprites do jogador na estrutura:
        Assets/player/<character>/   # <character> é 'player1' ou 'player2'

    Nomes de ficheiros suportados DENTRO DA PASTA:
        tronco_<stem>.png
        idlelegs_<stem>*.png
        runlegs_<stem>*.png

    onde <stem> pode ser:
        - mapeado ('marco' para 'player1', 'tarma' para 'player2'), OU
        - o próprio <character> (fallback), p.ex.: 'tronco_player1.png'
    """
    import os

    base_path = os.path.join(ASSETS_DIR, "player", character)
    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"[Erro] Pasta da personagem não encontrada: {base_path}")

    # Mapa de pasta → stem de ficheiro (ajusta aqui se os teus nomes forem outros)
    folder_to_stem = {
        "player1": "marco",
        "player2": "tarma",
    }
    stems_to_try = []
    if character in folder_to_stem:
        stems_to_try.append(folder_to_stem[character])
    # fallback se usares player1 no nome dos ficheiros
    stems_to_try.append(character)

    # --- carregar tronco ---
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
        raise FileNotFoundError(f"[Erro] Não encontrei o tronco em {base_path}. Esperava: {exp}")

    # --- carregar pernas (idle/run) ---
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
        raise FileNotFoundError(f"[Erro] Não encontrei sprites idlelegs_{used_stem}* em {base_path}")
    if not run_legs:
        raise FileNotFoundError(f"[Erro] Não encontrei sprites runlegs_{used_stem}* em {base_path}")

    print(f"[DEBUG Sprites] pasta={character} stem={used_stem} -> idle={len(idle_legs)} run={len(run_legs)}")

    return {
        "torso": torso,
        "idle_legs": idle_legs,
        "run_legs": run_legs,
        "legs_height": height // 2,
        "torso_height": height // 2,
    }

# ---------- 👾 INIMIGOS ----------
def load_enemy(width=80, height=80, filename="rebel1.png"):
    """Carrega sprite do inimigo (ex: rebel1.png) a partir de Assets/enemy/"""
    enemy_dir = os.path.join(ASSETS_DIR, "enemy")
    path = os.path.join(enemy_dir, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"[resource] Sprite de inimigo não encontrada: {path}")

    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (width, height))


# ---------- 🔊 SONS ----------
def load_sound_path(filename):
    """Procura um ficheiro de som dentro de Assets/sounds/ e devolve o caminho absoluto."""
    sounds_dir = os.path.join(ASSETS_DIR, "sounds")
    path = os.path.join(sounds_dir, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"[resource] Som não encontrado: {path}")

    return os.path.abspath(path)
