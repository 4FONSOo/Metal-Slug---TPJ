# scenes/flow.py
"""
Cenas de fluxo / transições:
  - LevelCompleteScene: ecrã "COMPLETE" com end.mp3.
  - LoadingScene: ecrã "Loading..." com barra de progresso.
  - NoMoreLevelsScene: ecrã "CHEATER / no more levels" (debug).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List
import sys

import pg_engine as pg
import config

from scene import Scene

if TYPE_CHECKING:
    from game_state import Game


class LevelCompleteScene(Scene):
    """
    Ecrã de 'COMPLETE' no fim de um nível.

    - Mostra texto "COMPLETE" + hint.
    - Pára a música anterior e toca end.mp3.
    - ENTER / SPACE / ESC → avança para LoadingScene.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self.big_font = None
        self.small_font = None
        self.title_surf = None
        self.hint_surf = None

    def on_enter(self) -> None:
        # Fonts / textos
        try:
            big_font_name = getattr(config, "MENU_FONT_NAME", config.HUD_FONT_NAME)
            small_font_name = getattr(
                config, "MENU_OPTIONS_FONT_NAME", config.HUD_FONT_NAME
            )
            big_font = pg.create_font(big_font_name, 72)
            small_font = pg.create_font(small_font_name, 26)
        except Exception:
            big_font = self.game.font
            small_font = self.game.font

        self.big_font = big_font
        self.small_font = small_font

        self.title_surf = pg.render_text(big_font, "COMPLETE", (255, 255, 0))
        self.hint_surf = pg.render_text(
            small_font,
            "ENTER para continuar",
            (220, 220, 220),
        )

        # Música de fim de nível
        try:
            self.game.sound.stop_music()
        except Exception:
            pass

        try:
            self.game.sound.play_music("end.mp3")
        except Exception:
            try:
                self.game.sound.play_sfx("end.mp3")
            except Exception:
                pass

    def handle_input(self, events: List[pg.Event]) -> None:
        for event in events:
            if event.type == pg.QUIT:
                try:
                    self.game.sound.stop_music()
                except Exception:
                    pass
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_RETURN, pg.K_SPACE, pg.K_ESCAPE):
                    # Avança para ecrã de loading
                    from scenes.flow import LoadingScene  # import local p/ evitar ciclos

                    self.game.change_scene(LoadingScene(self.game))
                    return

    def update(self, dt: float) -> None:
        # Ecrã estático; nada a actualizar.
        pass

    def draw(self, screen: pg.Surface) -> None:
        screen.fill((0, 0, 0))

        if not self.title_surf or not self.hint_surf:
            return

        screen.blit(
            self.title_surf,
            (
                config.WIDTH // 2 - self.title_surf.get_width() // 2,
                config.HEIGHT // 2 - 100,
            ),
        )
        screen.blit(
            self.hint_surf,
            (
                config.WIDTH // 2 - self.hint_surf.get_width() // 2,
                config.HEIGHT // 2 + 20,
            ),
        )


class LoadingScene(Scene):
    """
    Ecrã de 'Loading...' com barra de progresso.

    Quando o tempo 'duration' termina, chama game.go_to_next_level()
    (que trata de start_game + restauro de score/HP/etc.).
    """

    def __init__(self, game: "Game", seconds: float = 4.0) -> None:
        super().__init__(game)
        self.duration = max(0.1, float(seconds))
        self.elapsed = 0.0

        self.font = None
        self.text_surf = None

        self.bar_width = 0
        self.bar_height = 0
        self.bar_x = 0
        self.bar_y = 0

    def on_enter(self) -> None:
        # Preparar fontes / texto
        try:
            font_name = getattr(config, "MENU_FONT_NAME", config.HUD_FONT_NAME)
            font_size = getattr(config, "MENU_TITLE_FONT_SIZE", 48)
            font = pg.create_font(font_name, font_size)
        except Exception:
            font = self.game.font

        self.font = font
        self.text_surf = pg.render_text(font, "Loading...", (255, 255, 255))

        self.bar_width = int(config.WIDTH * 0.6)
        self.bar_height = 20
        self.bar_x = (config.WIDTH - self.bar_width) // 2
        self.bar_y = config.HEIGHT // 2 + 40

        self.elapsed = 0.0

    def handle_input(self, events: List[pg.Event]) -> None:
        # Normalmente ignoramos input (só QUIT)
        for event in events:
            if event.type == pg.QUIT:
                try:
                    self.game.sound.stop_music()
                except Exception:
                    pass
                pg.quit()
                sys.exit()

    def update(self, dt: float) -> None:
        # dt em ms
        self.elapsed += (dt or 0.0) / 1000.0

        if self.elapsed >= self.duration:
            # Tempo de loading terminou → avança logicamente de nível
            self.game.go_to_next_level()
            return

    def draw(self, screen: pg.Surface) -> None:
        screen.fill((0, 0, 0))

        if self.text_surf:
            screen.blit(
                self.text_surf,
                (
                    config.WIDTH // 2 - self.text_surf.get_width() // 2,
                    config.HEIGHT // 2 - self.text_surf.get_height() // 2 - 30,
                ),
            )

        # Fundo da barra
        pg.draw_rect(
            screen,
            (60, 60, 60),
            (self.bar_x, self.bar_y, self.bar_width, self.bar_height),
        )

        # Progresso
        if self.duration > 0.0:
            progress = max(0.0, min(1.0, self.elapsed / self.duration))
        else:
            progress = 1.0

        pg.draw_rect(
            screen,
            (200, 200, 50),
            (
                self.bar_x,
                self.bar_y,
                int(self.bar_width * progress),
                self.bar_height,
            ),
        )


class NoMoreLevelsScene(Scene):
    """
    Ecrã de debug quando já não há mais níveis para o cheat.

    Mostra:
      CHEATER
      no more levels

    ENTER: volta ao menu principal e faz reset do debug_level_index para 0.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self.big_font = None
        self.small_font = None
        self.title_surf = None
        self.msg_surf = None
        self.hint_surf = None

    def on_enter(self) -> None:
        try:
            big_font_name = getattr(config, "MENU_FONT_NAME", config.HUD_FONT_NAME)
            small_font_name = getattr(
                config, "MENU_OPTIONS_FONT_NAME", config.HUD_FONT_NAME
            )
            big_font = pg.create_font(big_font_name, 72)
            small_font = pg.create_font(small_font_name, 26)
        except Exception:
            big_font = self.game.font
            small_font = self.game.font

        self.big_font = big_font
        self.small_font = small_font

        self.title_surf = pg.render_text(big_font, "CHEATER", (255, 50, 50))
        self.msg_surf = pg.render_text(big_font, "no more levels", (255, 255, 255))
        self.hint_surf = pg.render_text(
            small_font,
            "ENTER: voltar ao nível 1",
            (200, 200, 200),
        )

        # Flash vermelho para dar ênfase
        try:
            self.game.flash((255, 50, 50))
        except Exception:
            pass

    def handle_input(self, events: List[pg.Event]) -> None:
        for event in events:
            if event.type == pg.QUIT:
                try:
                    self.game.sound.stop_music()
                except Exception:
                    pass
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                # Reset para nível 1 e volta ao menu
                self.game.debug_level_index = 0
                print("[CHEAT] Reset para nível 1 após 'no more levels'")

                from scenes.menu import Menu as MenuScene

                self.game.change_scene(MenuScene(self.game))
                return

    def update(self, dt: float) -> None:
        # Ecrã estático
        pass

    def draw(self, screen: pg.Surface) -> None:
        screen.fill((0, 0, 0))

        if not self.title_surf or not self.msg_surf or not self.hint_surf:
            return

        screen.blit(
            self.title_surf,
            (
                config.WIDTH // 2 - self.title_surf.get_width() // 2,
                config.HEIGHT // 2 - 150,
            ),
        )
        screen.blit(
            self.msg_surf,
            (
                config.WIDTH // 2 - self.msg_surf.get_width() // 2,
                config.HEIGHT // 2 - 40,
            ),
        )
        screen.blit(
            self.hint_surf,
            (
                config.WIDTH // 2 - self.hint_surf.get_width() // 2,
                config.HEIGHT // 2 + 60,
            ),
        )
