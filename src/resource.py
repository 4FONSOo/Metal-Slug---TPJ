# resource.py
"""
Funções de carregamento de recursos (imagens, sons, etc.).

Tudo o que for buscar ficheiros ao disco devia passar por aqui,
para quando mudares a estrutura de pastas não andares a chorar
por 20 sítios diferentes.
"""

import os
import pg_engine as pg
from config import ASSETS_DIR


def find_asset(filename: str) -> str:
    """
    Procura recursivamente dentro de ASSETS_DIR e devolve o caminho completo.
    """
    for root, _, files in os.walk(ASSETS_DIR):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"Asset '{filename}' não encontrado em {ASSETS_DIR}")


def load_player_sprites(width: int, height: int, character: str = "player1") -> dict:
    """
    Carrega sprites avançados do jogador (tronco + pernas idle/run).
    """
    base_path = os.path.join(ASSETS_DIR, "player", character)
    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"[Erro] Pasta da personagem não encontrada: {base_path}")

    folder_to_stem = {
        "player1": "marco",
        "player2": "tarma",
    }

    stems_to_try: list[str] = []
    if character in folder_to_stem:
        stems_to_try.append(folder_to_stem[character])
        stems_to_try.append(character)  # fallback marado

    torso = None
    used_stem = None

    for stem in stems_to_try:
        torso_name = f"tronco_{stem}.png"
        torso_path = os.path.join(base_path, torso_name)
        if os.path.isfile(torso_path):
            used_stem = stem
            torso = pg.load_image(torso_path)
            torso = pg.scale_image(torso, (width, height // 2))
            break

    if torso is None or used_stem is None:
        raise FileNotFoundError(f"[Erro] Não encontrei tronco_* válido em {base_path}")

    idle_legs = []
    run_legs = []

    for fname in sorted(os.listdir(base_path)):
        if not fname.lower().endswith(".png"):
            continue
        lower = fname.lower()
        full_path = os.path.join(base_path, fname)

        if lower.startswith(f"idlelegs_{used_stem}"):
            img = pg.load_image(full_path)
            img = pg.scale_image(img, (width, height // 2))
            idle_legs.append(img)
        elif lower.startswith(f"runlegs_{used_stem}"):
            img = pg.load_image(full_path)
            img = pg.scale_image(img, (width, height // 2))
            run_legs.append(img)

    if not idle_legs:
        raise FileNotFoundError(f"[Erro] Falta idlelegs_{used_stem}* em {base_path}")
    if not run_legs:
        raise FileNotFoundError(f"[Erro] Falta runlegs_{used_stem}* em {base_path}")

    print(
        f"[DEBUG Sprites] pasta={character} stem={used_stem} "
        f"-> idle={len(idle_legs)} run={len(run_legs)}"
    )

    return {
        "torso": torso,
        "idle_legs": idle_legs,
        "run_legs": run_legs,
        "legs_height": height // 2,
        "torso_height": height // 2,
    }


def load_enemy(width: int = 80, height: int = 80, filename: str = "Rebel1.png"):
    """
    Carrega um sprite de inimigo a partir de ASSETS_DIR/enemy/<filename>.
    """
    enemy_dir = os.path.join(ASSETS_DIR, "enemy")
    path = os.path.join(enemy_dir, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"[resource] Inimigo onde está: {path}")

    img = pg.load_image(path)
    return pg.scale_image(img, (width, height))


def load_sound_path(filename: str) -> str:
    """
    Devolve o caminho absoluto para um ficheiro de som em ASSETS_DIR/sounds.
    """
    sounds_dir = os.path.join(ASSETS_DIR, "sounds")
    path = os.path.join(sounds_dir, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"[resource] Som não encontrado: {path}")

    return os.path.abspath(path)
