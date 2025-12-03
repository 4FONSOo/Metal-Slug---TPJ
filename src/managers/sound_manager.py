# sound_manager.py
"""
Gestor de som de alto nível para o jogo.

Objectivo:
  - Fornecer uma API simples baseada em eventos de jogo:
      * disparo
      * granada lançada
      * granada explode
    e outros que quiseres adicionar.

  - NÃO lida directamente com pygame/pg_engine.
    Em vez disso, delega num backend que implementa métodos simples como:
      * play_music(track_id, loop=True)
      * stop_music()
      * play_sfx(sound_id)
      * set_music_volume(volume)
      * set_sfx_volume(volume)

Integração típica (no futuro):
  - No teu código de inicialização:
      from sound import SoundManager as LowLevelSoundManager
      from sound_manager import SoundManager, SoundConfig

      backend = LowLevelSoundManager()  # este fala com pg_engine / pygame.mixer
      cfg = SoundConfig(
          shoot_sfx="sfx_shoot",
          grenade_throw_sfx="sfx_grenade_throw",
          grenade_explode_sfx="sfx_grenade_explode",
      )
      sound = SoundManager(backend=backend, config=cfg)

  - No jogo:
      sound.play_shoot()
      sound.play_grenade_throw()
      sound.play_grenade_explode()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional


# ------------------------------------------------------------------ #
# Backend protocol
# ------------------------------------------------------------------ #

class SoundBackend(Protocol):
    """
    Interface mínima que o backend de som deve implementar.

    Podes adaptar o teu sound.py actual para cumprir isto.
    """

    def play_music(self, track_id: str, loop: bool = True) -> None:
        """Tocar uma faixa de música (por ID ou caminho)."""

    def stop_music(self) -> None:
        """Parar a música actual."""

    def set_music_volume(self, volume: float) -> None:
        """
        Ajustar volume da música.
        volume: 0.0 a 1.0
        """

    def play_sfx(self, sound_id: str) -> None:
        """Tocar um efeito sonoro curto (SFX)."""

    def set_sfx_volume(self, volume: float) -> None:
        """
        Ajustar volume global dos SFX.
        volume: 0.0 a 1.0
        """


# ------------------------------------------------------------------ #
# Configuração dos sons por evento
# ------------------------------------------------------------------ #

@dataclass
class SoundConfig:
    """
    Identificadores de som para eventos específicos do jogo.

    Estes IDs podem ser:
      - nomes lógicos (usados por um dicionário no backend)
      - caminhos para ficheiros
      - o que fizer sentido no backend.
    """

    # Música
    menu_music: str = "music_menu"
    level_music: str = "music_level"

    # SFX principais
    shoot_sfx: str = "sfx_shoot"
    grenade_throw_sfx: str = "sfx_grenade_throw"
    grenade_explode_sfx: str = "sfx_grenade_explode"

    # Podes ir adicionando mais:
    # pickup_sfx: str = "sfx_pickup"
    # nuke_sfx: str = "sfx_nuke_beep"
    # etc.


# ------------------------------------------------------------------ #
# SoundManager de alto nível
# ------------------------------------------------------------------ #

class SoundManager:
    """
    Gestor de som de alto nível.

    Usa um backend para fazer o trabalho sujo (pygame, mixer, etc.),
    e expõe métodos semânticos focados no jogo.
    """

    def __init__(
        self,
        backend: SoundBackend,
        config: Optional[SoundConfig] = None,
    ) -> None:
        self._backend = backend
        self._config = config or SoundConfig()

        # Volumes lógicos (0.0 a 1.0)
        self._music_volume: float = 1.0
        self._sfx_volume: float = 1.0

        # Track de música actual (opcional, só para referência)
        self._current_music_id: Optional[str] = None

        # Aplicar volumes iniciais no backend
        self._backend.set_music_volume(self._music_volume)
        self._backend.set_sfx_volume(self._sfx_volume)

    # ------------------------------------------------------------------ #
    # Música
    # ------------------------------------------------------------------ #

    def play_menu_music(self, loop: bool = True) -> None:
        """Tocar a música de menu."""
        track = self._config.menu_music
        self.play_music(track, loop=loop)

    def play_level_music(self, loop: bool = True) -> None:
        """Tocar a música do nível."""
        track = self._config.level_music
        self.play_music(track, loop=loop)

    def play_music(self, track_id: str, loop: bool = True) -> None:
        """Tocar uma faixa de música arbitrária."""
        self._current_music_id = track_id
        self._backend.play_music(track_id, loop=loop)

    def stop_music(self) -> None:
        """Parar a música actual."""
        self._backend.stop_music()
        self._current_music_id = None

    def set_music_volume(self, volume: float) -> None:
        """Definir volume da música (0.0 a 1.0)."""
        volume = max(0.0, min(1.0, float(volume)))
        self._music_volume = volume
        self._backend.set_music_volume(volume)

    # ------------------------------------------------------------------ #
    # SFX genéricos
    # ------------------------------------------------------------------ #

    def play_sfx(self, sound_id: str) -> None:
        """Tocar um efeito sonoro arbitrário."""
        self._backend.play_sfx(sound_id)

    def set_sfx_volume(self, volume: float) -> None:
        """Definir volume global dos SFX (0.0 a 1.0)."""
        volume = max(0.0, min(1.0, float(volume)))
        self._sfx_volume = volume
        self._backend.set_sfx_volume(volume)

    # ------------------------------------------------------------------ #
    # Eventos específicos do jogo
    # ------------------------------------------------------------------ #

    def play_shoot(self) -> None:
        """
        Som ao disparar (balas normais).
        Pode ser chamado sempre que o jogador / inimigo dispara.
        """
        sfx_id = self._config.shoot_sfx
        self._backend.play_sfx(sfx_id)

    def play_grenade_throw(self) -> None:
        """
        Som ao lançar granada.
        Idealmente chamado no momento em que a granada é criada.
        """
        sfx_id = self._config.grenade_throw_sfx
        self._backend.play_sfx(sfx_id)

    def play_grenade_explode(self) -> None:
        """
        Som quando a granada explode.
        Chamado no momento em que a lógica da explosão é processada.
        """
        sfx_id = self._config.grenade_explode_sfx
        self._backend.play_sfx(sfx_id)

    # ------------------------------------------------------------------ #
    # Info / utilitários
    # ------------------------------------------------------------------ #

    @property
    def music_volume(self) -> float:
        return self._music_volume

    @property
    def sfx_volume(self) -> float:
        return self._sfx_volume

    @property
    def current_music_id(self) -> Optional[str]:
        return self._current_music_id
