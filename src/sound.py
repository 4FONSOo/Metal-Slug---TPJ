# sound.py
"""
Gestor de som extremamente simples.

Encapsula o acesso ao mixer/música do pygame através do pg_engine,
para o resto do código não ter de saber que o pygame existe.

Agora também trata de:
  - SFX genéricos (play_sfx)
  - Volume e mute de SFX
  - Sons de eventos do jogo:
      * início de nível   → start.mp3
      * fim de nível OK   → end.mp3
      * game over         → gameover.mp3
      * tiro              → tiro1.mp3 / tiro2.mp3 (aleatório)
      * melee             → faca1.mp3 / faca2.mp3 (aleatório)
      * explosão granada  → explosão.mp3
      * morte inimigo     → MorteInimigo1..5.mp3 (aleatório)
"""

import random
import pg_engine as pg
import pygame as _pygame
from resource import load_sound_path


class SoundManager:
    def __init__(self):
        self.enabled = False
        self._sfx_cache: dict[str, _pygame.mixer.Sound] = {}

        # Volume SFX (0.0 a 1.0) e estado de mute
        self._sfx_volume: float = 1.0
        self._sfx_muted: bool = False

        # Listas de ficheiros para sons aleatórios
        self._melee_sounds = [
            "faca1.mp3",
            "faca2.mp3",   # se for "faca2.mpe", troca aqui
        ]
        self._shot_sounds = [
            "tiro1.mp3",
            "tiro2.mp3",
        ]
        self._enemy_death_sounds = [
            f"MorteInimigo{i}.mp3" for i in range(1, 6)
        ]

        try:
            pg.mixer_init()
            self.enabled = True
        except Exception as e:
            print(f"[Som] Falha ao iniciar mixer: {e}")
            self.enabled = False

    # ---------------------------------------------------------
    # Música
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # SFX genérico
    # ---------------------------------------------------------
    def play_sfx(self, filename: str):
        """
        Toca um efeito sonoro curto (SFX).

        'filename' deve ser algo tipo "PickUp1.mp3", "start.mp3", etc.,
        igual ao nome que passas para load_sound_path().
        """
        if not self.enabled:
            return

        try:
            snd = self._sfx_cache.get(filename)
            if snd is None:
                path = load_sound_path(filename)
                snd = _pygame.mixer.Sound(path)
                self._sfx_cache[filename] = snd

            # aplicar volume/mute actual
            vol = 0.0 if self._sfx_muted else self._sfx_volume
            snd.set_volume(vol)

            snd.play()
        except Exception as e:
            print(f"[Som] Erro ao tocar SFX '{filename}': {e}")

    # ---------------------------------------------------------
    # Controlo de SFX (volume/mute)
    # ---------------------------------------------------------
    def set_sfx_volume(self, volume: float) -> None:
        """
        Define o volume base dos SFX (0.0 a 1.0).
        Se estiver em mute, o mute continua activo (não "desmuta").
        """
        volume = max(0.0, min(1.0, float(volume)))
        self._sfx_volume = volume

        if self._sfx_muted:
            # continua tudo mudo, mas guardamos o volume para quando desmutar
            return

        # actualizar volume de todos os SFX já em cache
        for snd in self._sfx_cache.values():
            try:
                snd.set_volume(self._sfx_volume)
            except Exception:
                pass

    def mute_sfx(self) -> None:
        """Desliga todos os SFX (mute ON)."""
        self._sfx_muted = True
        for snd in self._sfx_cache.values():
            try:
                snd.set_volume(0.0)
            except Exception:
                pass

    def unmute_sfx(self) -> None:
        """Liga os SFX (mute OFF) e aplica o volume actual."""
        self._sfx_muted = False
        for snd in self._sfx_cache.values():
            try:
                snd.set_volume(self._sfx_volume)
            except Exception:
                pass

    def toggle_sfx_mute(self) -> None:
        """Alterna entre mute ON/OFF para SFX."""
        if self._sfx_muted:
            self.unmute_sfx()
        else:
            self.mute_sfx()

    def is_sfx_muted(self) -> bool:
        return self._sfx_muted

    def get_sfx_volume(self) -> float:
        return self._sfx_volume

    # ---------------------------------------------------------
    # Helpers internos
    # ---------------------------------------------------------
    def _play_random_from_list(self, filenames: list[str]) -> None:
        """Escolhe um ficheiro aleatório da lista e toca-o."""
        if not filenames:
            return
        filename = random.choice(filenames)
        self.play_sfx(filename)

    # ---------------------------------------------------------
    # Eventos de jogo – interface de alto nível
    # ---------------------------------------------------------
    # Início / fim de nível / game over
    def play_level_start(self) -> None:
        """Som tocado no início do nível."""
        self.play_sfx("start.mp3")

    def play_level_end(self) -> None:
        """
        Som tocado no fim do nível bem sucedido:
        - neste projecto, quando o tempo chega a 0 e o player está vivo.
        """
        self.play_sfx("end.mp3")

    def play_game_over_sfx(self) -> None:
        """Som de game over (quando o player morre ou falha o nível)."""
        self.play_sfx("gameover.mp3")

    # Combate: tiro / melee / granada
    def play_shot(self) -> None:
        """Som ao disparar tiros (tiro1/tiro2 aleatório)."""
        self._play_random_from_list(self._shot_sounds)

    def play_melee(self) -> None:
        """Som de ataque melee (faca1/faca2 aleatório)."""
        self._play_random_from_list(self._melee_sounds)

    def play_grenade_explosion(self) -> None:
        """Som quando a granada explode."""
        self.play_sfx("explosão.mp3")

    def play_enemy_death(self) -> None:
        """Som de morte de inimigo (MorteInimigo1..5 aleatório)."""
        self._play_random_from_list(self._enemy_death_sounds)
