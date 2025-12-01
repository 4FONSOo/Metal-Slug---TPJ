# sound.py
"""
Gestor de som extremamente simples.

Encapsula o acesso ao mixer/música do pygame através do pg_engine,
para o resto do código não ter de saber que o pygame existe.
"""

import pg_engine as pg
from resource import load_sound_path


class SoundManager:
    def __init__(self):
        self.enabled = False
        try:
            pg.mixer_init()
            self.enabled = True
        except Exception as e:
            print(f"[Som] Falha ao iniciar mixer: {e}")
            self.enabled = False

    def play_music(self, filename: str):
        """
        Toca uma faixa de música em loop infinito.
        """
        if not self.enabled:
            return
        try:
            path = load_sound_path(filename)
            pg.music_load_and_play(path, loop=-1)
        except Exception as e:
            print(f"[Som] Erro ao tocar '{filename}': {e}")

    def stop_music(self):
        """Pára a música actual. Não rebenta se não houver nada a tocar."""
        if not self.enabled:
            return
        try:
            pg.music_stop()
        except Exception as e:
            print(f"[Som] Erro ao parar música: {e}")
