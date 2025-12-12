# score.py
#
# Sistema completo de scores:
#  - ScoreManager  → gere score atual + highscores em ficheiro JSON
#  - EnterNameScene → pede o nome quando há novo highscore
#  - HighScoreScene → mostra a tabela de highscores
#
# Usa pg_engine como wrapper do pygame (sem usar pg.font.* directamente).

import json
import os
import sys

import pg_engine as pg
import config
from config import WIDTH, HEIGHT


# ---------------------------------------------------------
# Utilitário: texto com contorno (usa pg.render_text)
# ---------------------------------------------------------
def draw_text_with_outline(surface, text, font, x, y, color, outline_color=(0, 0, 0)):
    """
    Desenha texto com contorno simples, deslocando o texto de contorno
    em volta do texto principal.
    """
    text_surface = pg.render_text(font, text, color)
    outline_surface = pg.render_text(font, text, outline_color)

    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                surface.blit(outline_surface, (x + dx, y + dy))

    surface.blit(text_surface, (x, y))


# ---------------------------------------------------------
# ScoreManager – lógica de scores e highscores (sem pygame)
# ---------------------------------------------------------

SCORE_FILE = "scores.json"
MAX_HIGH_SCORES = 7


class ScoreManager:
    """
    Gere o score atual e a tabela de highscores.
    Lê/escreve de um ficheiro JSON simples.
    """

    def __init__(self, filename: str = SCORE_FILE, max_scores: int = MAX_HIGH_SCORES):
        self.filename = filename
        self.max_scores = max_scores
        self.current_score = 0
        self.high_scores = []
        self.load_scores()

    # -----------------------------
    # Score da run atual
    # -----------------------------
    def reset_current(self):
        """Reseta o score atual (novo jogo, novo sofrimento)."""
        self.current_score = 0

    def add_points(self, pontos: int):
        """Adiciona pontos ao score atual."""
        if pontos <= 0:
            return
        self.current_score += pontos

    # -----------------------------
    # Highscores (ficheiro)
    # -----------------------------
    def load_scores(self):
        """Carrega highscores do ficheiro JSON. Se der merda, começa de novo."""
        if not os.path.exists(self.filename):
            self.high_scores = []
            return

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                # Normaliza, para o caso de o ficheiro estar meio marado
                self.high_scores = []
                for e in data:
                    try:
                        name = str(e.get("name", "???")).strip().upper()[:12]
                        score = int(e.get("score", 0))
                        self.high_scores.append({"name": name, "score": score})
                    except Exception:
                        # Ignora entradas maradas
                        continue

                self.high_scores.sort(key=lambda e: e["score"], reverse=True)
                self.high_scores = self.high_scores[: self.max_scores]
            else:
                self.high_scores = []
        except Exception as e:
            print(f"[SCORE] Ficheiro de scores marado, vou limpar. Erro: {e}")
            self.high_scores = []

    def save_scores(self):
        """Grava highscores no ficheiro JSON."""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.high_scores, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SCORE] Não consegui gravar scores: {e}")

    # -----------------------------
    # Lógica de highscore
    # -----------------------------
    def qualifies_for_highscore(self) -> bool:
        """
        Vê se o score atual entra no top.

        - Se ainda não tens MAX_HIGH_SCORES scores → entra sempre (desde que > 0)
        - Se já tens o máximo → tem de ser maior que o último
        """
        if self.current_score <= 0:
            return False

        if len(self.high_scores) < self.max_scores:
            return True

        return self.current_score > self.high_scores[-1]["score"]

    def register_current_score(self, name: str):
        """Regista o score atual na lista de highscores e grava em disco."""
        name = (name or "???").strip().upper()[:12]
        entry = {"name": name, "score": self.current_score}
        self.high_scores.append(entry)
        self.high_scores.sort(key=lambda e: e["score"], reverse=True)
        self.high_scores = self.high_scores[: self.max_scores]
        self.save_scores()

    def get_high_scores(self):
        """Devolve uma cópia da lista de highscores."""
        return list(self.high_scores)


# ---------------------------------------------------------
# Helpers para teclas via key_name (sem pg.K_*)
# ---------------------------------------------------------
def _key_name(event) -> str:
    """Devolve o nome da tecla em minúsculas, ou '' se falhar."""
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


# ---------------------------------------------------------
# EnterNameScene – pedir nome quando há novo highscore
# ---------------------------------------------------------
class EnterNameScene:
    """
    Ecrã simples para introduzir o nome quando há novo highscore.
    Bloqueia até o jogador carregar ENTER ou ESC.

    Uso típico:

        scene = EnterNameScene(screen, clock, score_manager)
        name = scene.run()
        if name:
            score_manager.register_current_score(name)
    """

    def __init__(self, screen, clock, score_manager: ScoreManager, max_length: int = 8):
        self.screen = screen
        self.clock = clock
        self.score_manager = score_manager
        self.max_length = max_length
        self.name = ""
        self.running = True

        # Usamos o mesmo tipo de fonte do HUD, mas com tamanhos diferentes
        self.title_font = pg.create_font(config.HUD_FONT_NAME, 64)
        self.text_font = pg.create_font(config.HUD_FONT_NAME, 32)

    def run(self):
        """
        Loop principal da cena.

        Retorna:
            - string com o nome introduzido
            - ou None se o jogador cancelar (ESC ou fechar janela)
        """
        while self.running:
            events = pg.get_events()
            self.handle_events(events)
            self.draw()
            self.clock.tick(config.FPS)

        return self.name if self.name.strip() else None

    def handle_events(self, events):
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                if _is_escape(event):
                    # Cancela, não grava nome
                    self.name = ""
                    self.running = False

                elif _is_return(event):
                    # Confirma
                    self.running = False

                elif _is_backspace(event):
                    self.name = self.name[:-1]

                else:
                    # Aceitar letras/números, limitar tamanho
                    char = getattr(event, "unicode", "")
                    if char and (char.isalnum() or char in " _-") and len(self.name) < self.max_length:
                        self.name += char.upper()

    def draw(self):
        self.screen.fill((10, 10, 10))

        title = "NOVO HIGH SCORE!"
        subtitle = "Escreve o teu nome:"
        hint = "ENTER = confirmar   ESC = cancelar"
        name_display = self.name if self.name else "..."

        # SCORE ACTUAL
        score_value = self.score_manager.current_score
        score_text = f"Score: {score_value}"

        # Título
        title_surf = pg.render_text(self.title_font, title, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        self.screen.blit(title_surf, title_rect)

        # Score
        score_surf = pg.render_text(self.text_font, score_text, (255, 255, 0))
        score_rect = score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))
        self.screen.blit(score_surf, score_rect)

        # Subtítulo
        subtitle_surf = pg.render_text(self.text_font, subtitle, (255, 255, 255))
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Caixa de input (simples, rect preenchido)
        rect_w = 300
        rect_h = 50
        rect_x = WIDTH // 2 - rect_w // 2
        rect_y = HEIGHT // 2

        # Fundo da caixa
        pg.draw_rect(
            self.screen,
            (0, 0, 0),
            (rect_x - 2, rect_y - 2, rect_w + 4, rect_h + 4),
        )
        # Borda
        pg.draw_rect(
            self.screen,
            (255, 255, 255),
            (rect_x, rect_y, rect_w, rect_h),
        )

        # Nome
        name_surf = pg.render_text(self.text_font, name_display, (0, 255, 0))
        name_rect = name_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + rect_h // 2))
        self.screen.blit(name_surf, name_rect)

        # Hint
        hint_surf = pg.render_text(self.text_font, hint, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        self.screen.blit(hint_surf, hint_rect)

        pg.display_flip()


# ---------------------------------------------------------
# HighScoreScene – mostrar tabela de highscores
# ---------------------------------------------------------
class HighScoreScene:
    """
    Ecrã que mostra a lista de highscores.
    Bloqueia até ENTER / ESC / SPACE / fechar janela.

    Uso típico:

        scene = HighScoreScene(screen, clock, score_manager)
        scene.run()
    """

    def __init__(self, screen, clock, score_manager: ScoreManager):
        self.screen = screen
        self.clock = clock
        self.score_manager = score_manager
        self.running = True

        self.title_font = pg.create_font(config.HUD_FONT_NAME, 64)
        self.text_font = pg.create_font(config.HUD_FONT_NAME, 32)

    def run(self):
        while self.running:
            events = pg.get_events()
            self.handle_events(events)
            self.draw()
            self.clock.tick(config.FPS)

    def handle_events(self, events):
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                if _is_escape(event) or _is_return(event) or _is_space(event):
                    self.running = False

    def draw(self):
        self.screen.fill((15, 15, 40))

        title = "HIGH SCORES"
        title_surf = pg.render_text(self.title_font, title, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        self.screen.blit(title_surf, title_rect)

        scores = self.score_manager.get_high_scores()[:8]

        if not scores:
            texto = "Ainda não há ninguém no topo... vai lá morrer com estilo!"
            text_surf = pg.render_text(self.text_font, texto, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(text_surf, text_rect)
        else:
            start_y = HEIGHT // 3
            line_height = 40

            for i, entry in enumerate(scores):
                rank = i + 1
                name = entry["name"]
                score = entry["score"]

                line = f"{rank:2}. {name:<12}  {score:>7}"
                draw_text_with_outline(
                    self.screen,
                    line,
                    self.text_font,
                    WIDTH // 2 - 180,
                    start_y + i * line_height,
                    (255, 255, 255),
                )

        hint = "ENTER / ESC / SPACE = voltar"
        hint_surf = pg.render_text(self.text_font, hint, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        self.screen.blit(hint_surf, hint_rect)

        pg.display_flip()
