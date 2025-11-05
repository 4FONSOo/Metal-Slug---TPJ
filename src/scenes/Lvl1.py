import os
import pygame
import pytmx
from config import ASSETS_DIR, HEIGHT


def load_level():
    """
    Carrega o mapa Lvl1.tmx (renderizado com todas as camadas visíveis),
    ajustando a altura do mapa à altura da janela do jogo (HEIGHT)
    e mantendo a proporção original da largura.
    """

    # Caminho do ficheiro TMX
    tmx_path = os.path.join(ASSETS_DIR, "background", "Lvl1.tmx")
    if not os.path.isfile(tmx_path):
        raise FileNotFoundError(f"[Erro] Mapa TMX não encontrado: {tmx_path}")

    # Carregar mapa TMX
    tmx_data = pytmx.load_pygame(tmx_path, pixelalpha=True)

    # Tamanho original do mapa (em píxeis)
    map_width = tmx_data.width * tmx_data.tilewidth
    map_height = tmx_data.height * tmx_data.tileheight

    # Criar superfície original
    original_surface = pygame.Surface((map_width, map_height), pygame.SRCALPHA)

    # 🔹 Desenhar todas as camadas de tiles visíveis
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    original_surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

    # 🔹 Calcular fator de escala proporcional à altura da janela
    scale_factor = HEIGHT / map_height
    new_width = int(map_width * scale_factor)
    new_height = HEIGHT  # sempre igual à altura da janela

    # Redimensionar o mapa
    background = pygame.transform.smoothscale(original_surface, (new_width, new_height))

    # 🔹 Extrair retângulos de colisão da camada "Mapa_Col"
    platforms = []
    if "Mapa_Col" in tmx_data.layernames:
        for obj in tmx_data.get_layer_by_name("Mapa_Col"):
            rect = pygame.Rect(
                obj.x * scale_factor,
                obj.y * scale_factor,
                obj.width * scale_factor,
                obj.height * scale_factor
            )
            platforms.append(rect)
    else:
        print("[Aviso] Nenhuma camada 'Mapa_Col' encontrada no TMX.")

    print(f"[Mapa] Carregado: {os.path.basename(tmx_path)}")
    print(f"[Mapa] Original: {map_width}x{map_height}px → Escalado: {new_width}x{new_height}px")
    print(f"[Mapa] {len(platforms)} colisões detetadas (ajustadas à escala).")

    return {
        "background": background,
        "bg_width": new_width,
        "bg_height": new_height,
        "platforms": platforms,
    }
