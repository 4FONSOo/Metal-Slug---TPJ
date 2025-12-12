# scenes/game_over.py
#
# Cena de Game Over com:
#   - Ecrã "GAME OVER" + score final
#   - Se for highscore, pede nome
#   - Mostra tabela de highscores
#   - ENTER / ESC / SPACE → volta ao Menu
#
# Usa o ScoreManager existente em game.score_manager
# e NUNCA faz loops while True (é uma Scene normal).

from __future__ import annotations

from typing import TYPE_CHECKING

import pg_engine as pg
import config
from scene import Scene

if TYPE_CHECKING:
    from game_state import Game

from scenes.menu import Menu as MenuScene


WIDTH = config.WIDTH
HEIGHT = config.HEIGHT


# -----------------------------
# Helpers de teclas (via key_name)
# -----------------------------
def _key_name(event) -> str:
    try:
        name = pg.key_name(event.key)
    except Exception:
        return ""
    return (name or "").lower()


def _is_escape(event) -> bool:
    return _key_name(event) == "escape"


def _is_return(event) -> bool:
    name = _key_name(event)
    return name in ("return", "enter", "kp_enter")


def _is_backspace(event) -> bool:
    return _key_name(event) == "backspace"


def _is_space(event) -> bool:
    return _key_name(event) == "space"


class GameOverScene(Scene):
    """
    Cena de Game Over em 2 fases:
      - "enter_name": se houver novo highscore → pede nome
      - "table": mostra a tabela de highscores e volta ao menu
    """

    def __init__(self, game: Game):
        super().__init__(game)

        self.phase: str = "enter_name"  # "enter_name" ou "table"
        self.name: str = ""
        self.max_name_length: int = 8
        self.final_score: int = 0
        self.is_highscore: bool = False
        self.running: bool = True  # apenas guardamos estado lógico

        # Fonts
        self.title_font = pg.create_font(config.HUD_FONT_NAME, 64)
        self.text_font = pg.create_font(config.HUD_FONT_NAME, 32)

    # ---------------------------------
    # Lifecycle
    # ---------------------------------
    def on_enter(self):
        """
        Chamado quando a cena se torna activa.
        Decide se vamos pedir nome ou ir directo à tabela.
        """
        game = self.game

        # Sincronizar pontuação actual (por segurança)
        if game.game_state is not None:
            game.score_manager.current_score = game.game_state.score

        self.final_score = game.score_manager.current_score
        self.is_highscore = game.score_manager.qualifies_for_highscore()

        # Se não for highscore ou score <= 0, saltamos logo para a tabela
        if not self.is_highscore or self.final_score <= 0:
            self.phase = "table"
        else:
            self.phase = "enter_name"

        # DEBUG: ver no terminal se temos scores
        print("[GAME_OVER] final_score:", self.final_score)
        print("[GAME_OVER] qualifies_for_highscore:", self.is_highscore)
        print("[GAME_OVER] highscores actuais:", game.score_manager.get_high_scores())

    def handle_input(self, events: list):
        if not self.running:
            return

        if self.phase == "enter_name":
            self._handle_input_enter_name(events)
        elif self.phase == "table":
            self._handle_input_table(events)

    def update(self, dt: float):
        # Aqui não há animações dependentes de dt por agora
        pass

    def draw(self, screen: pg.Surface):
        if self.phase == "enter_name":
            self._draw_enter_name(screen)
        elif self.phase == "table":
            self._draw_table(screen)

    # ---------------------------------
    # Fase 1: Introduzir Nome (Highscore)
    # ---------------------------------
    def _handle_input_enter_name(self, events: list):
        game = self.game

        for event in events:
            if event.type == pg.QUIT:
                try:
                    game.sound.stop_music()
                except Exception:
                    pass
                pg.quit()
                raise SystemExit

            if event.type == pg.KEYDOWN:
                if _is_escape(event):
                    # Cancela highscore, salta para a tabela
                    self.name = ""
                    self.phase = "table"
                    return

                elif _is_return(event):
                    # Confirma nome (se vazio, usa "???")
                    if self.name.strip():
                        game.score_manager.register_current_score(self.name)
                    else:
                        # Se não escreveu nada, ainda assim registamos algo,
                        # ou então simplesmente não registamos. Aqui vou registar "???"
                        game.score_manager.register_current_score("???")
                    self.phase = "table"
                    return

                elif _is_backspace(event):
                    self.name = self.name[:-1]

                else:
                    char = getattr(event, "unicode", "")
                    if (
                        char
                        and (char.isalnum() or char in " _-")
                        and len(self.name) < self.max_name_length
                    ):
                        self.name += char.upper()

    def _draw_enter_name(self, screen: pg.Surface):
        game = self.game
        screen.fill((10, 10, 10))

        title = "GAME OVER"
        subtitle = "NOVO HIGH SCORE! Escreve o teu nome:"
        hint = "ENTER = confirmar   ESC = saltar"
        name_display = self.name if self.name else "..."

        score_text = f"Score: {self.final_score}"

        # Título
        title_surf = pg.render_text(self.title_font, title, (255, 50, 50))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        screen.blit(title_surf, title_rect)

        # Score
        score_surf = pg.render_text(self.text_font, score_text, (255, 255, 0))
        score_rect = score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(score_surf, score_rect)

        # Subtítulo
        subtitle_surf = pg.render_text(self.text_font, subtitle, (255, 255, 255))
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(subtitle_surf, subtitle_rect)

        # Caixa de input
        rect_w = 300
        rect_h = 50
        rect_x = WIDTH // 2 - rect_w // 2
        rect_y = HEIGHT // 2

        pg.draw_rect(
            screen,
            (0, 0, 0),
            (rect_x - 2, rect_y - 2, rect_w + 4, rect_h + 4),
        )
        pg.draw_rect(
            screen,
            (255, 255, 255),
            (rect_x, rect_y, rect_w, rect_h),
        )

        name_surf = pg.render_text(self.text_font, name_display, (0, 255, 0))
        name_rect = name_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + rect_h // 2))
        screen.blit(name_surf, name_rect)

        # Hint
        hint_surf = pg.render_text(self.text_font, hint, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        screen.blit(hint_surf, hint_rect)

        # DEBUG: nº de scores já registados
        debug_text = f"[DEBUG] highscores: {len(game.score_manager.get_high_scores())}"
        debug_surf = pg.render_text(self.text_font, debug_text, (100, 255, 100))
        debug_rect = debug_surf.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        screen.blit(debug_surf, debug_rect)

    # ---------------------------------
    # Fase 2: Mostrar Tabela de Highscores
    # ---------------------------------
    def _handle_input_table(self, events: list):
        game = self.game

        for event in events:
            if event.type == pg.QUIT:
                try:
                    game.sound.stop_music()
                except Exception:
                    pass
                pg.quit()
                raise SystemExit

            if event.type == pg.KEYDOWN:
                if _is_escape(event) or _is_return(event) or _is_space(event):
                    # Voltar ao menu principal
                    game.reset_all_state()
                    game.change_scene(MenuScene(game))
                    return

    def _draw_table(self, screen: pg.Surface):
        game = self.game
        screen.fill((15, 15, 40))

        title = "HIGH SCORES"
        title_surf = pg.render_text(self.title_font, title, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        screen.blit(title_surf, title_rect)

        scores = game.score_manager.get_high_scores()

        if not scores:
            texto = "Ainda não há ninguém no topo..."
            text_surf = pg.render_text(self.text_font, texto, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text_surf, text_rect)
        else:
            start_y = HEIGHT // 3
            line_height = 40

            for i, entry in enumerate(scores):
                rank = i + 1
                name = entry["name"]
                score = entry["score"]

                line = f"{rank:2}. {name:<12}  {score:>7}"
                line_surf = pg.render_text(self.text_font, line, (255, 255, 255))
                line_rect = line_surf.get_rect(
                    topleft=(WIDTH // 2 - 180, start_y + i * line_height)
                )
                screen.blit(line_surf, line_rect)

        # Hint
        hint = "ENTER / ESC / SPACE = voltar ao menu"
        hint_surf = pg.render_text(self.text_font, hint, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        screen.blit(hint_surf, hint_rect)

        # DEBUG: nº de scores
        # debug_text = f"[DEBUG] highscores: {len(scores)}"
        # debug_surf = pg.render_text(self.text_font, debug_text, (100, 255, 100))
        # debug_rect = debug_surf.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        # screen.blit(debug_surf, debug_rect)
