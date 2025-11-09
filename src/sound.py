import pygame
from resource import load_sound_path

class SoundManager:
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception as e:
            print(f"[Som] Falha ao iniciar música: {e}")
            self.enabled = False

    def play_music(self, filename: str):
        if not self.enabled:
            return
        try:
            path = load_sound_path(filename)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            #print(f"[Som] Música iniciada: {path}")
        except Exception as e:
            print(f"[Som] Erro: {e}")

    def stop_music(self):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
            #print("[Som] Música parada.")
        except Exception as e:
            print(f"[Som] Erro ao parar: {e}")
