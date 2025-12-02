import os
import pytmx

import pg_engine as pg
from config import ASSETS_DIR, HEIGHT


def load_level():
    """
    Carrega o nível 1 a partir de um ficheiro TMX do Tiled.
    """

    tmx_path = os.path.join(ASSETS_DIR, "background", "Lvl1.tmx")
    if not os.path.isfile(tmx_path):
        raise FileNotFoundError(f"[Erro] Mapa TMX não encontrado: {tmx_path}")

    # Carrega TMX com suporte a transparência (usa pygame por baixo)
    tmx_data = pytmx.load_pygame(tmx_path, pixelalpha=True)
    map_width = tmx_data.width * tmx_data.tilewidth
    map_height = tmx_data.height * tmx_data.tileheight

    original_surface = pg.create_surface((map_width, map_height), alpha=True)

    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    original_surface.blit(
                        tile,
                        (x * tmx_data.tilewidth, y * tmx_data.tileheight),
                    )

    scale_factor = HEIGHT / map_height
    new_width = int(map_width * scale_factor)
    new_height = HEIGHT
    background = pg.scale_image(original_surface, (new_width, new_height))

    platforms = []
    if "Mapa_Col" in tmx_data.layernames:
        for obj in tmx_data.get_layer_by_name("Mapa_Col"):
            rect = pg.Rect(
                obj.x * scale_factor,
                obj.y * scale_factor,
                obj.width * scale_factor,
                obj.height * scale_factor,
            )
            platforms.append(rect)
    else:
        print("[Lvl1] Aviso: Sem colisões!!! (layer 'Mapa_Col' em falta)")

    return {
        "background": background,
        "bg_width": new_width,
        "bg_height": new_height,
        "platforms": platforms,
    }
