import pygame
from resource import load_sound_path


class SoundManager:
    def __init__(self):
        """Inicializa o mixer de som."""
        self.enabled = False
        try:
            pygame.mixer.init()
            self.enabled = True
            print("[Som] Mixer inicializado com sucesso.")
        except Exception as e:
            print(f"[Som] ⚠️ Falha ao iniciar mixer: {e}")
            self.enabled = False

    # -------------------------------------------------
    # 🎵 MÚSICA DE FUNDO
    # -------------------------------------------------
    def play_music(self, filename: str):
        """
        Carrega e toca música de fundo em loop infinito.
        Exemplo: play_music("theme.mp3")
        """
        if not self.enabled:
            print("[Som] Mixer não disponível — música ignorada.")
            return

        try:
            path = load_sound_path(filename)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)  # -1 = loop infinito
            print(f"[Som] ▶️ Música iniciada: {path}")
        except FileNotFoundError as e:
            print(f"[Som] ⚠️ {e}")
        except Exception as e:
            print(f"[Som] ❌ Erro ao tocar música: {e}")

    def stop_music(self):
        """Para a música atual."""
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
            print("[Som] ⏹️ Música parada.")
        except Exception as e:
            print(f"[Som] ⚠️ Erro ao parar música: {e}")