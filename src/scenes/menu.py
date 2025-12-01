# scenes/menu.py
"""
Menus do jogo:
- Menu principal (cena)
- Opções (cena)
- Controlos (cena)
- Dificuldade (cena)

Tudo isto agora são Scenes, integradas no loop global do Game.
"""

import sys

import pg_engine as pg
from scene import Scene
from config import (
    WIDTH,
    HEIGHT,
    FPS,
    MENU_TITLE,
    MENU_FONT_NAME,
    MENU_FONT_SIZE,
    MENU_OPTIONS_FONT_NAME,
    MENU_OPTIONS_FONT_SIZE,
    MENU_VOLUME_HOLD_REPEAT_FRAMES,
    MENU_VOLUME_STEP,
    DIFFICULTY_PRESETS,
)
import controls


class Menu(Scene):
    """
    Menu principal:
      - escolher personagem
      - ir para opções
      - bazar do jogo
    """

    def __init__(self, game):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_FONT_NAME, MENU_FONT_SIZE)

        self.selected = 0
        self.options = ["Marco Rossi", "Tarma Roving", "Opções", "Sair"]

    # ---- Scene API ----
    def handle_input(self, events: list):
        for event in events:
            if event.type == pg.QUIT:
                self.game.sound.stop_music()
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pg.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pg.K_RETURN:
                    self.handle_selection()

    def update(self, dt: float):
        # Menu principal não tem lógica de update contínua (por agora)
        pass

    def draw(self, screen):
        screen.fill((20, 20, 40))

        title = pg.render_text(self.font, MENU_TITLE, (255, 255, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (150, 150, 150)
            surf = pg.render_text(self.font, text, color)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 250 + i * 60))

    # ---- Lógica específica do menu ----
    def handle_selection(self):
        """Trata da opção escolhida no menu principal."""
        if self.selected == 0:
            # Player 1 disponível
            self.game.player_choice = "player1"
            self.game.start_game()

        elif self.selected == 1:
            # Player 2 ainda não tem sprites animadas -> ecrã "BREVEMENTE"
            self.show_coming_soon()

        elif self.selected == 2:
            # Ir para a cena de opções
            self.game.change_scene(MenuOptions(self.game))

        elif self.selected == 3:
            # Rage quit civilizado
            self.game.sound.stop_music()
            pg.quit()
            sys.exit()

    def show_coming_soon(self):
        """
        Mostra um ecrã a dizer "BREVEMENTE" e bloqueia até o jogador carregar
        numa tecla qualquer.
        """
        big_font = pg.create_font(MENU_FONT_NAME, 72)
        small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 26)

        title_surf = pg.render_text(big_font, "BREVEMENTE", (255, 255, 0))
        msg_surf = pg.render_text(
            small_font,
            "Esta personagem ainda está em produção",
            (230, 230, 230),
        )
        hint_surf = pg.render_text(
            small_font,
            "Carrega em qualquer tecla para voltar",
            (180, 180, 180),
        )

        while True:
            for event in pg.get_events():
                if event.type == pg.QUIT:
                    self.game.sound.stop_music()
                    pg.quit()
                    sys.exit()
                elif event.type == pg.KEYDOWN:
                    # Qualquer tecla volta ao menu
                    return

            self.screen.fill((10, 10, 30))

            self.screen.blit(
                title_surf,
                (
                    WIDTH // 2 - title_surf.get_width() // 2,
                    HEIGHT // 2 - 120,
                ),
            )
            self.screen.blit(
                msg_surf,
                (
                    WIDTH // 2 - msg_surf.get_width() // 2,
                    HEIGHT // 2 - 20,
                ),
            )
            self.screen.blit(
                hint_surf,
                (
                    WIDTH // 2 - hint_surf.get_width() // 2,
                    HEIGHT // 2 + 40,
                ),
            )

            pg.display_flip()
            self.clock.tick(FPS)


class MenuOptions(Scene):
    """
    Menu de opções:
      - dificuldade
      - controlos
      - volume/mute da música
    """

    def __init__(self, game):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE)
        self.small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 26)

        self.selected = 0

        # Volume actual da música (0-100). Se o mixer não arrancar, fingimos 100.
        if pg.mixer_get_init():
            self.volume = int(pg.music_get_volume() * 100)
        else:
            self.volume = 100

        self.muted = False
        self.hold_timer = 0           # para repetir alterações de volume ao segurar tecla
        self.hovering_mute = False    # rato em cima do texto de mute
        self.options = ["Dificuldade", "Controlos", "Volume Música", "Voltar"]
        self.vol_rect = None          # rect do texto de volume/mute para clique

        # Modo de input numérico do volume
        self.volume_input_mode = False
        self.volume_input_text = ""
        # Flag para engolir um ENTER logo a seguir a fechar a caixa de input
        self.ignore_next_enter = False

    # ---- Scene API ----
    def handle_input(self, events: list):
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                # Se estamos em modo de input numérico, tratamos isso primeiro
                if self.volume_input_mode:
                    self._handle_volume_numeric_input(event)
                    continue

                # Engolir o ENTER "repetido" logo a seguir a fechar a caixa
                if event.key == pg.K_RETURN and self.ignore_next_enter:
                    self.ignore_next_enter = False
                    continue

                # Navegação normal das opções
                if event.key == pg.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pg.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pg.K_RETURN:
                    self.handle_selection()
                elif event.key == pg.K_ESCAPE:
                    # Volta ao menu principal
                    self.game.change_scene(Menu(self.game))
                elif event.key == pg.K_M and self.selected == 2:
                    self.toggle_mute()

            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                # Clique no texto de volume/mute
                if self.vol_rect and self.vol_rect.collidepoint(event.pos):
                    self.toggle_mute()

    def _handle_volume_numeric_input(self, event):
        """Trata do modo em que o jogador digita um valor de 0 a 100."""
        # ESC -> cancelar
        if event.key == pg.K_ESCAPE:
            self.volume_input_mode = False
            self.volume_input_text = ""
            # próximo ENTER normal não precisa ser ignorado
            return

        # ENTER -> aceitar se houver algo
        if event.key == pg.K_RETURN:
            if self.volume_input_text:
                try:
                    value = int(self.volume_input_text)
                    value = max(0, min(100, value))
                    self.volume = value
                    if pg.mixer_get_init():
                        pg.music_set_volume(self.volume / 100)
                except ValueError:
                    pass

            self.volume_input_mode = False
            self.volume_input_text = ""
            # marca para engolir o próximo ENTER "repetido"
            self.ignore_next_enter = True
            return

        # BACKSPACE -> apaga último dígito
        key_name = pg.key_name(event.key)
        if key_name == "backspace":
            self.volume_input_text = self.volume_input_text[:-1]
            return

        # Dígitos 0–9
        ch = getattr(event, "unicode", "")
        if ch and ch.isdigit():
            candidate_str = (self.volume_input_text + ch)
            if len(candidate_str) > 3:
                return
            try:
                candidate_val = int(candidate_str)
            except ValueError:
                return

            if 0 <= candidate_val <= 100:
                # Normaliza para tirar zeros à esquerda
                self.volume_input_text = str(candidate_val)

    def update(self, dt: float):
        """Trata do ajuste contínuo do volume (tecla mantida)."""
        # Enquanto estamos em modo numérico, ignoramos o ajuste incremental
        if self.volume_input_mode:
            self.hold_timer = 0
            return

        keys = pg.get_keys()
        if self.selected == 2:
            change = 0
            if keys[pg.K_LEFT]:
                change = -MENU_VOLUME_STEP
            elif keys[pg.K_RIGHT]:
                change = +MENU_VOLUME_STEP

            if change != 0:
                self.hold_timer += 1
                if self.hold_timer % MENU_VOLUME_HOLD_REPEAT_FRAMES == 0:
                    self.adjust_volume(change)
            else:
                self.hold_timer = 0

    def draw(self, screen):
        screen.fill((10, 10, 25))
        title = pg.render_text(self.font, "Opções", (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        mouse_pos = pg.mouse_get_pos()

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (120, 120, 120)
            surf = pg.render_text(self.font, text, color)
            y = 220 + i * 60
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))

            # Mostrar dificuldade atual ao lado da opção
            if text == "Dificuldade":
                diff_label = self.game.difficulty
                diff_surf = pg.render_text(self.small_font, diff_label, (0, 200, 255))
                screen.blit(diff_surf, (WIDTH // 2 + 180, y))

            # Mostrar volume / mute ao lado da opção
            if text == "Volume Música":
                vol_text = "MUTE" if self.muted else f"{self.volume}%"
                vol_icon = "🔇" if self.muted else "🔊"
                vol_color = (255, 80, 80) if self.muted else (0, 200, 255)

                vol_surf = pg.render_text(self.small_font, f"{vol_icon} {vol_text}", vol_color)
                self.vol_rect = vol_surf.get_rect()
                self.vol_rect.topleft = (WIDTH // 2 + 180, y)

                # Se o rato estiver em cima do texto, damos highlight maroto
                self.hovering_mute = self.vol_rect.collidepoint(mouse_pos)
                if self.hovering_mute:
                    highlight = pg.create_surface(
                        (self.vol_rect.width + 10, self.vol_rect.height + 4)
                    )
                    highlight.fill((30, 60, 100))
                    screen.blit(highlight, (self.vol_rect.x - 5, self.vol_rect.y - 2))

                screen.blit(vol_surf, self.vol_rect)

        # Caixa de input numérico de volume
        if self.volume_input_mode:
            box_w, box_h = 420, 140
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2

            pg.draw_rect(screen, (0, 0, 0), (box_x - 4, box_y - 4, box_w + 8, box_h + 8))
            pg.draw_rect(screen, (30, 60, 120), (box_x, box_y, box_w, box_h))

            prompt = "Introduz volume (0-100)"
            value_text = self.volume_input_text or "-"
            value_line = f"Valor: {value_text}"
            hint = "ENTER: aceitar   |   ESC: cancelar"

            p_surf = pg.render_text(self.small_font, prompt, (230, 230, 255))
            v_surf = pg.render_text(self.small_font, value_line, (255, 255, 0))
            h_surf = pg.render_text(self.small_font, hint, (220, 220, 220))

            screen.blit(
                p_surf,
                (WIDTH // 2 - p_surf.get_width() // 2, box_y + 15),
            )
            screen.blit(
                v_surf,
                (WIDTH // 2 - v_surf.get_width() // 2, box_y + 55),
            )
            screen.blit(
                h_surf,
                (WIDTH // 2 - h_surf.get_width() // 2, box_y + 95),
            )

    # ---- Lógica específica ----
    def adjust_volume(self, change: int):
        """Sobe/desce volume em passos definidos na config (se não estiver mute)."""
        if self.muted:
            return

        self.volume = max(0, min(100, self.volume + change))

        if pg.mixer_get_init():
            pg.music_set_volume(self.volume / 100)

    def toggle_mute(self):
        """Liga/desliga mute da música. Simples, sem fade fancy."""
        self.muted = not self.muted

        if not pg.mixer_get_init():
            return

        if self.muted:
            pg.music_set_volume(0)
        else:
            pg.music_set_volume(self.volume / 100)

    def handle_selection(self):
        if self.selected == 0:
            # Dificuldade
            self.game.change_scene(MenuDifficulty(self.game))
        elif self.selected == 1:
            # Controlos
            self.game.change_scene(MenuControls(self.game))
        elif self.selected == 2:
            # Volume: entra em modo de input numérico (começa vazio)
            self.volume_input_mode = True
            self.volume_input_text = ""
            # Ao entrar, certificamos que o próximo ENTER conta
            self.ignore_next_enter = False
        elif self.selected == 3:
            # Voltar ao menu principal
            self.game.change_scene(Menu(self.game))


class MenuControls(Scene):
    """
    Menu de remapeamento de teclas:
      - mostra ação + tecla atual
      - permite escolher ação e carregar nova tecla
      - Layout em 2 colunas 50/50
      - Navegação com CIMA/BAIXO/ESQUERDA/DIREITA
    """

    def __init__(self, game):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock

        # Fonte ligeiramente mais pequena
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE - 4)  # ~26
        self.small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 20)

        self.selected = 0
        self.remapping = False  # se True, está à espera da nova tecla

        # Lista de entradas (ação, label)
        self.entries = [
            (controls.MOVE_LEFT, "Mover Esquerda"),
            (controls.MOVE_RIGHT, "Mover Direita"),
            (controls.UP, "Mirar Cima"),
            (controls.DOWN, "Mirar Baixo"),
            (controls.JUMP, "Saltar"),
            (controls.FIRE, "Disparar"),
            (controls.MENU, "Menu / Sair"),
            (controls.PAUSE, "Pausa"),
            (None, "Voltar"),
        ]

    def handle_input(self, events: list):
        last_index = len(self.entries) - 1      # índice de "Voltar" (8)
        grid_count = last_index                 # 0..7 são a grelha
        rows, cols = 4, 2                       # 4 linhas, 2 colunas

        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                if self.remapping:
                    # Estamos à espera da nova tecla para a ação selecionada
                    if event.key == pg.K_ESCAPE:
                        # Cancela remapeamento
                        self.remapping = False
                    else:
                        action, _ = self.entries[self.selected]
                        if action is not None:
                            controls.set_key(action, event.key)
                        self.remapping = False
                    continue

                # --- Navegação espacial com setas ---
                if event.key in (pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT):
                    idx = self.selected

                    # Se estamos em "Voltar"
                    if idx == last_index:
                        if event.key == pg.K_UP:
                            # Sobe para a última linha, coluna esquerda (index 6)
                            self.selected = grid_count - 2
                        # Esquerda/Direita/Baixo em "Voltar" não fazem nada
                        continue

                    # Estamos dentro da grelha 0..7
                    row = idx // 2
                    col = idx % 2

                    if event.key == pg.K_UP:
                        # sobe na mesma coluna (com wrap)
                        row = (row - 1) % rows

                    elif event.key == pg.K_DOWN:
                        # se estamos na última linha e carregamos baixo -> vai para "Voltar"
                        if row == rows - 1:
                            self.selected = last_index
                            continue
                        row = (row + 1) % rows

                    elif event.key == pg.K_LEFT:
                        col = (col - 1) % cols

                    elif event.key == pg.K_RIGHT:
                        col = (col + 1) % cols

                    self.selected = row * 2 + col
                    continue

                # --- ENTER / ESC ---

                if event.key == pg.K_RETURN:
                    if self.selected == last_index:
                        # Voltar às opções
                        self.game.change_scene(MenuOptions(self.game))
                    else:
                        # Entrar em modo de remapeamento
                        self.remapping = True

                elif event.key == pg.K_ESCAPE:
                    self.game.change_scene(MenuOptions(self.game))

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill((10, 10, 25))
        title = pg.render_text(self.font, "Controlos", (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

        last_index = len(self.entries) - 1

        for i, (action, label) in enumerate(self.entries):
            is_selected = (i == self.selected)
            base_color = (255, 255, 255)
            if action is None:
                base_color = (200, 200, 200)

            color = (255, 255, 0) if is_selected else base_color

            if action is None:
                text = label
            else:
                key_name = controls.get_key_name(action)
                text = f"{label}: {key_name}"

            surf = pg.render_text(self.font, text, color)

            if i == last_index:
                # "Voltar" centrado em baixo
                x = WIDTH // 2 - surf.get_width() // 2
                y = 180 + 4 * 60
            else:
                # 0..7 em 2 colunas
                col = i % 2            # 0 = esquerda, 1 = direita
                row = i // 2           # 0..3
                x_center = int(WIDTH * (0.25 if col == 0 else 0.75))
                x = x_center - surf.get_width() // 2
                y = 180 + row * 55

            screen.blit(surf, (x, y))

        # Mensagem de ajuda / remapeamento
        if self.remapping:
            help_text = "Prima a nova tecla... (ESC para cancelar)"
        else:
            help_text = "ENTER: remapear | ESC: voltar"

        help_surf = pg.render_text(self.small_font, help_text, (200, 200, 200))
        screen.blit(
            help_surf,
            (WIDTH // 2 - help_surf.get_width() // 2, HEIGHT - 80),
        )


class MenuDifficulty(Scene):
    """
    Menu para escolher dificuldade.
    Usa DIFFICULTY_PRESETS da config e avisa o Game para aplicar preset.
    """

    def __init__(self, game):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE)
        self.selected = 0

        # Todas as dificuldades conhecidas + opção "Voltar"
        self.options = list(DIFFICULTY_PRESETS.keys()) + ["Voltar"]

    def handle_input(self, events: list):
        last_index = len(self.options) - 1

        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pg.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pg.K_RETURN:
                    if self.selected == last_index:
                        # "Voltar"
                        self.game.change_scene(MenuOptions(self.game))
                    else:
                        # Mudar dificuldade actual e aplicar preset no Game
                        self.game.difficulty = self.options[self.selected]
                        self.game.update_difficulty_preset()
                        self.game.change_scene(MenuOptions(self.game))
                elif event.key == pg.K_ESCAPE:
                    self.game.change_scene(MenuOptions(self.game))

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill((10, 10, 25))
        title = pg.render_text(self.font, "Dificuldade", (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for i, text in enumerate(self.options):
            base_color = (255, 255, 255)
            if text == self.game.difficulty:
                base_color = (0, 200, 255)  # dificuldade actualmente activa
            color = (255, 255, 0) if i == self.selected else base_color

            surf = pg.render_text(self.font, text, color)
            y = 220 + i * 60
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
