# scenes/menu.py
"""
Menus do jogo:
- Menu principal (Menu)
- Opções (MenuOptions)
- Controlos (MenuControls)
- Dificuldade (MenuDifficulty)
- Áudio (MenuAudio)
- Menu de pausa in-game (PauseMenu)

Tudo isto são Scenes, integradas no loop global do Game.
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
    MENU_VOLUME_STEP,
    MENU_VOLUME_HOLD_REPEAT_FRAMES,
    DIFFICULTY_PRESETS,
)
import controls


# -------------------------------------------------------------------
# MENU PRINCIPAL
# -------------------------------------------------------------------
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

    def handle_input(self, events: list):
        for event in events:
            if event.type == pg.QUIT:
                if getattr(self.game, "sound", None):
                    self.game.sound.stop_music()
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                # Primeiro: tentar cheats (TROCA, GOD, etc.)
                cheat_consumed = self.game.process_cheats(event)
                if cheat_consumed:
                    # Letra foi usada para um cheat → não mexe no menu
                    continue

                if event.key == pg.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pg.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pg.K_RETURN:
                    self.handle_selection()

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill((20, 20, 40))

        title = pg.render_text(self.font, MENU_TITLE, (255, 255, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (150, 150, 150)
            surf = pg.render_text(self.font, text, color)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 250 + i * 60))

    def handle_selection(self):
        if self.selected == 0:
            self.game.player_choice = "player1"
            self.game.start_game()

        elif self.selected == 1:
            self.show_coming_soon()

        elif self.selected == 2:
            self.game.change_scene(MenuOptions(self.game))

        elif self.selected == 3:
            if getattr(self.game, "sound", None):
                self.game.sound.stop_music()
            pg.quit()
            sys.exit()

    def show_coming_soon(self):
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
                    if getattr(self.game, "sound", None):
                        self.game.sound.stop_music()
                    pg.quit()
                    sys.exit()
                elif event.type == pg.KEYDOWN:
                    return

            self.screen.fill((10, 10, 30))

            self.screen.blit(
                title_surf,
                (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 120),
            )
            self.screen.blit(
                msg_surf,
                (WIDTH // 2 - msg_surf.get_width() // 2, HEIGHT // 2 - 20),
            )
            self.screen.blit(
                hint_surf,
                (WIDTH // 2 - hint_surf.get_width() // 2, HEIGHT // 2 + 40),
            )

            pg.display_flip()
            self.clock.tick(FPS)


# -------------------------------------------------------------------
# MENU OPÇÕES (NO MENU PRINCIPAL)
# -------------------------------------------------------------------
class MenuOptions(Scene):
    """
    Menu de opções (nível 1 no menu principal):
      - Dificuldade
      - Controlos
      - Áudio
      - Voltar
    """

    def __init__(self, game):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE)
        self.small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 26)

        self.selected = 0
        self.options = ["Dificuldade", "Controlos", "Áudio", "Voltar"]

    def handle_input(self, events: list):
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
                    self.handle_selection()
                elif event.key == pg.K_ESCAPE:
                    self.game.change_scene(Menu(self.game))

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill((10, 10, 25))
        title = pg.render_text(self.font, "Opções", (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        base_y = 220
        row_spacing = 60

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (120, 120, 120)
            surf = pg.render_text(self.font, text, color)
            x = WIDTH // 2 - surf.get_width() // 2
            y = base_y + i * row_spacing
            screen.blit(surf, (x, y))

        hint = "ESC: voltar ao menu principal"
        hint_surf = pg.render_text(self.small_font, hint, (200, 200, 200))
        screen.blit(
            hint_surf,
            (WIDTH // 2 - hint_surf.get_width() // 2, HEIGHT - 80),
        )

    def handle_selection(self):
        current = self.options[self.selected]

        if current == "Dificuldade":
            self.game.change_scene(MenuDifficulty(self.game))
        elif current == "Controlos":
            # back_scene = eu próprio (MenuOptions)
            self.game.change_scene(MenuControls(self.game, back_scene=self))
        elif current == "Áudio":
            self.game.change_scene(MenuAudio(self.game, back_scene=self))
        elif current == "Voltar":
            self.game.change_scene(Menu(self.game))


# -------------------------------------------------------------------
# MENU DE PAUSA (IN-GAME)
# -------------------------------------------------------------------
class PauseMenu(Scene):
    """
    Menu de pausa durante o jogo:
      - Retomar Jogo
      - Controlos
      - Áudio
      - Sair para Menu

    previous_scene: normalmente a LevelScene de onde vieste.
    """

    def __init__(self, game, previous_scene: Scene):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE)
        self.small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 26)

        self.selected = 0
        self.options = ["Retomar Jogo", "Controlos", "Áudio", "Sair para Menu"]
        self.previous_scene = previous_scene

    def handle_input(self, events: list):
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
                    self.handle_selection()
                elif event.key == pg.K_ESCAPE:
                    # ESC = retomar jogo
                    self._resume_game()

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill((0, 0, 0))

        # Fundo ligeiramente escurecido
        overlay = pg.create_surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        title = pg.render_text(self.font, "Pausa", (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        base_y = 220
        row_spacing = 60

        for i, text in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected else (150, 150, 150)
            surf = pg.render_text(self.font, text, color)
            x = WIDTH // 2 - surf.get_width() // 2
            y = base_y + i * row_spacing
            screen.blit(surf, (x, y))

        hint = "↑/↓: escolher  |  ENTER: confirmar  |  ESC: retomar jogo"
        hint_surf = pg.render_text(self.small_font, hint, (200, 200, 200))
        screen.blit(
            hint_surf,
            (WIDTH // 2 - hint_surf.get_width() // 2, HEIGHT - 80),
        )

    def handle_selection(self):
        current = self.options[self.selected]

        if current == "Retomar Jogo":
            self._resume_game()

        elif current == "Controlos":
            # Controlos in-game: voltam a este PauseMenu
            self.game.change_scene(MenuControls(self.game, back_scene=self))

        elif current == "Áudio":
            self.game.change_scene(MenuAudio(self.game, back_scene=self))

        elif current == "Sair para Menu":
            # Mata o jogo actual e volta ao menu principal
            if hasattr(self.game, "reset_all_state"):
                self.game.reset_all_state()
            self.game.change_scene(Menu(self.game))

    def _resume_game(self):
        # Volta à cena de jogo de onde vieste
        self.game.change_scene(self.previous_scene)


# -------------------------------------------------------------------
# MENU ÁUDIO (reutilizado por menu principal e pausa)
# -------------------------------------------------------------------
class MenuAudio(Scene):
    """
    Menu de Áudio:
      - Master
      - Música
      - SFX
      - Voltar

    Controlo:
      - ↑/↓: escolher linha
      - ←/→ em Master/Música/SFX: ajustar volume em passos (com tecla contínua)
      - M: mute/unmute na linha seleccionada
      - ENTER em Voltar: voltar
      - ESC: voltar

    back_scene:
      - cena para onde volta (MenuOptions ou PauseMenu, por exemplo).
    """

    def __init__(self, game, back_scene: Scene | None = None):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE)
        self.small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 26)

        self.back_scene = back_scene
        self.selected = 0
        self.options = ["Master", "Música", "SFX", "Voltar"]

        sound = getattr(self.game, "sound", None)

        # Volume base de música
        base_music = 1.0
        if sound is not None and hasattr(sound, "music_volume"):
            try:
                base_music = float(sound.music_volume)
            except Exception:
                base_music = 1.0
        else:
            try:
                if pg.mixer_get_init():
                    base_music = pg.music_get_volume()
            except Exception:
                base_music = 1.0

        # Volume base de SFX
        base_sfx = 1.0
        if sound is not None:
            try:
                if hasattr(sound, "sfx_volume"):
                    base_sfx = float(sound.sfx_volume)
                elif hasattr(sound, "get_sfx_volume"):
                    base_sfx = float(sound.get_sfx_volume())
            except Exception:
                base_sfx = 1.0

        # Volumes 0–100
        self.master_volume = 100
        self.music_volume = int(max(0.0, min(1.0, base_music)) * 100)
        self.sfx_volume = int(max(0.0, min(1.0, base_sfx)) * 100)

        # Mutes
        self.master_muted = False
        self.music_muted = False
        self.sfx_muted = False

        # Rects clicáveis (toggle mute com rato)
        self.master_mute_rect = None
        self.music_mute_rect = None
        self.sfx_mute_rect = None

        # Timer para ajuste contínuo
        self.hold_timer = 0

        self._apply_sound_volumes()

    # ---------- helpers de áudio ----------
    def _apply_sound_volumes(self):
        sound = getattr(self.game, "sound", None)

        master_factor = 0.0 if self.master_muted else self.master_volume / 100.0
        music_factor = 0.0 if self.music_muted else self.music_volume / 100.0
        sfx_factor = 0.0 if self.sfx_muted else self.sfx_volume / 100.0

        eff_music = master_factor * music_factor
        eff_sfx = master_factor * sfx_factor

        if sound is not None:
            # Música via pg_engine
            try:
                if hasattr(pg, "music_set_volume"):
                    pg.music_set_volume(eff_music)
            except Exception:
                pass

            # SFX via sound.py (set_sfx_volume)
            if hasattr(sound, "set_sfx_volume"):
                try:
                    sound.set_sfx_volume(eff_sfx)
                except Exception:
                    pass
        else:
            # Sem backend de som, pelo menos tenta música
            if hasattr(pg, "music_set_volume"):
                try:
                    pg.music_set_volume(eff_music)
                except Exception:
                    pass

    # ---------- input ----------
    def handle_input(self, events: list):
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                current = self.options[self.selected]

                if event.key == pg.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)

                elif event.key == pg.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)

                elif event.key in (pg.K_LEFT, pg.K_RIGHT):
                    # Ajuste imediato no KEYDOWN
                    change = -MENU_VOLUME_STEP if event.key == pg.K_LEFT else MENU_VOLUME_STEP

                    if current == "Master":
                        self.adjust_master_volume(change)
                    elif current == "Música":
                        self.adjust_music_volume(change)
                    elif current == "SFX":
                        self.adjust_sfx_volume(change)

                elif event.key == pg.K_RETURN:
                    if current == "Voltar":
                        self._go_back()

                elif event.key == pg.K_M:
                    if current == "Master":
                        self.toggle_master_mute()
                    elif current == "Música":
                        self.toggle_music_mute()
                    elif current == "SFX":
                        self.toggle_sfx_mute()

                elif event.key == pg.K_ESCAPE:
                    self._go_back()

            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.master_mute_rect and self.master_mute_rect.collidepoint(mx, my):
                    self.toggle_master_mute()
                elif self.music_mute_rect and self.music_mute_rect.collidepoint(mx, my):
                    self.toggle_music_mute()
                elif self.sfx_mute_rect and self.sfx_mute_rect.collidepoint(mx, my):
                    self.toggle_sfx_mute()

    def _go_back(self):
        if self.back_scene is not None:
            self.game.change_scene(self.back_scene)
        else:
            # fallback paranoid: volta ao MenuOptions
            self.game.change_scene(MenuOptions(self.game))

    # ---------- update / draw ----------
    def update(self, dt: float):
        """
        Ajuste contínuo do volume quando manténs LEFT/RIGHT.
        """
        keys = pg.get_keys()
        current = self.options[self.selected]

        if current in ("Master", "Música", "SFX"):
            change = 0
            if keys[pg.K_LEFT]:
                change = -MENU_VOLUME_STEP
            elif keys[pg.K_RIGHT]:
                change = MENU_VOLUME_STEP

            if change != 0:
                self.hold_timer += 1
                if self.hold_timer % MENU_VOLUME_HOLD_REPEAT_FRAMES == 0:
                    if current == "Master":
                        self.adjust_master_volume(change)
                    elif current == "Música":
                        self.adjust_music_volume(change)
                    elif current == "SFX":
                        self.adjust_sfx_volume(change)
            else:
                self.hold_timer = 0
        else:
            self.hold_timer = 0

    def draw(self, screen):
        screen.fill((10, 10, 25))
        title = pg.render_text(self.font, "Áudio", (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        self.master_mute_rect = None
        self.music_mute_rect = None
        self.sfx_mute_rect = None

        base_y = 220
        row_spacing = 60

        for i, opt_text in enumerate(self.options):
            y = base_y + i * row_spacing

            if opt_text == "Master":
                box = "[X]" if self.master_muted else "[ ]"
                mv_text = "MUTE" if self.master_muted else f"{self.master_volume}%"
                mv_icon = "🔇" if self.master_muted else "🎚"
                label_line = f"Master: {box} {mv_icon} {mv_text}"
                base_color = (255, 80, 80) if self.master_muted else (0, 200, 255)
            elif opt_text == "Música":
                box = "[X]" if self.music_muted else "[ ]"
                mu_text = "MUTE" if self.music_muted else f"{self.music_volume}%"
                mu_icon = "🔇" if self.music_muted else "🔊"
                label_line = f"Música: {box} {mu_icon} {mu_text}"
                base_color = (255, 80, 80) if self.music_muted else (0, 200, 255)
            elif opt_text == "SFX":
                box = "[X]" if self.sfx_muted else "[ ]"
                sx_text = "MUTE" if self.sfx_muted else f"{self.sfx_volume}%"
                sx_icon = "🔇" if self.sfx_muted else "🎵"
                label_line = f"SFX: {box} {sx_icon} {sx_text}"
                base_color = (255, 80, 80) if self.sfx_muted else (0, 200, 255)
            elif opt_text == "Voltar":
                label_line = "Voltar"
                base_color = (255, 255, 255)
            else:
                label_line = opt_text
                base_color = (255, 255, 255)

            color = (255, 255, 0) if i == self.selected else base_color
            surf = pg.render_text(self.font, label_line, color)
            x = WIDTH // 2 - surf.get_width() // 2
            rect = surf.get_rect(topleft=(x, y))
            screen.blit(surf, rect)

            if opt_text == "Master":
                self.master_mute_rect = rect
            elif opt_text == "Música":
                self.music_mute_rect = rect
            elif opt_text == "SFX":
                self.sfx_mute_rect = rect

        # Ajuda em baixo
        line1 = "↑/↓: escolher   |   ←/→: ajustar volume Master/Música/SFX (tecla contínua)"
        line2 = "M: mute/unmute   |   ENTER/ESC em 'Voltar': sair"

        l1_surf = pg.render_text(self.small_font, line1, (200, 200, 200))
        l2_surf = pg.render_text(self.small_font, line2, (200, 200, 200))
        screen.blit(
            l1_surf,
            (WIDTH // 2 - l1_surf.get_width() // 2, HEIGHT - 95),
        )
        screen.blit(
            l2_surf,
            (WIDTH // 2 - l2_surf.get_width() // 2, HEIGHT - 65),
        )

    # ---------- lógica volumes ----------
    def adjust_master_volume(self, change: int):
        if self.master_muted:
            return
        self.master_volume = max(0, min(100, self.master_volume + change))
        self._apply_sound_volumes()

    def adjust_music_volume(self, change: int):
        if self.music_muted:
            return
        self.music_volume = max(0, min(100, self.music_volume + change))
        self._apply_sound_volumes()

    def adjust_sfx_volume(self, change: int):
        if self.sfx_muted:
            return
        self.sfx_volume = max(0, min(100, self.sfx_volume + change))
        self._apply_sound_volumes()

    def toggle_master_mute(self):
        self.master_muted = not self.master_muted
        self._apply_sound_volumes()

    def toggle_music_mute(self):
        self.music_muted = not self.music_muted
        self._apply_sound_volumes()

    def toggle_sfx_mute(self):
        self.sfx_muted = not self.sfx_muted
        self._apply_sound_volumes()


# -------------------------------------------------------------------
# MENU CONTROLOS (reutilizado por menu principal e pausa)
# -------------------------------------------------------------------
class MenuControls(Scene):
    """
    Menu de remapeamento de teclas.

    back_scene:
      - cena para onde volta (MenuOptions ou PauseMenu, por exemplo).
    """

    def __init__(self, game, back_scene: Scene | None = None):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock

        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE - 4)
        self.small_font = pg.create_font(MENU_OPTIONS_FONT_NAME, 20)

        self.selected = 0
        self.remapping = False
        self.back_scene = back_scene

        self.entries = [
            (controls.MOVE_LEFT, "Mover Esquerda"),
            (controls.MOVE_RIGHT, "Mover Direita"),
            (controls.UP, "Mirar Cima"),
            (controls.DOWN, "Mirar Baixo"),
            (controls.JUMP, "Saltar"),
            (controls.FIRE, "Disparar"),
            (controls.GRANADE, "Granada"),
            (controls.MENU, "Menu / Sair"),
            (controls.PAUSE, "Pausa"),
            (None, "Voltar"),
        ]

    def _go_back(self):
        if self.back_scene is not None:
            self.game.change_scene(self.back_scene)
        else:
            self.game.change_scene(MenuOptions(self.game))

    def handle_input(self, events: list):
        last_index = len(self.entries) - 1
        grid_count = last_index
        rows, cols = 4, 2

        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                if self.remapping:
                    if event.key == pg.K_ESCAPE:
                        self.remapping = False
                    else:
                        action, _ = self.entries[self.selected]
                        if action is not None:
                            controls.set_key(action, event.key)
                        self.remapping = False
                    continue

                if event.key in (pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT):
                    idx = self.selected

                    if idx == last_index:
                        if event.key == pg.K_UP:
                            self.selected = grid_count - 2
                        continue

                    row = idx // 2
                    col = idx % 2

                    if event.key == pg.K_UP:
                        row = (row - 1) % rows
                    elif event.key == pg.K_DOWN:
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

                if event.key == pg.K_RETURN:
                    if self.selected == last_index:
                        self._go_back()
                    else:
                        self.remapping = True

                elif event.key == pg.K_ESCAPE:
                    self._go_back()

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
                x = WIDTH // 2 - surf.get_width() // 2
                y = 180 + 4 * 60
            else:
                col = i % 2
                row = i // 2
                x_center = int(WIDTH * (0.25 if col == 0 else 0.75))
                x = x_center - surf.get_width() // 2
                y = 180 + row * 55

            screen.blit(surf, (x, y))

        if self.remapping:
            help_text = "Prima a nova tecla... (ESC para cancelar)"
        else:
            help_text = "ENTER: remapear | ESC: voltar"

        help_surf = pg.render_text(self.small_font, help_text, (200, 200, 200))
        screen.blit(
            help_surf,
            (WIDTH // 2 - help_surf.get_width() // 2, HEIGHT - 80),
        )


# -------------------------------------------------------------------
# MENU DIFICULDADE (só no menu principal)
# -------------------------------------------------------------------
class MenuDifficulty(Scene):
    """
    Menu para escolher dificuldade.
    Só acessível a partir do menu principal.
    """

    def __init__(self, game):
        super().__init__(game)
        self.screen = game.screen
        self.clock = game.clock
        self.font = pg.create_font(MENU_OPTIONS_FONT_NAME, MENU_OPTIONS_FONT_SIZE)
        self.selected = 0

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
                        self.game.change_scene(MenuOptions(self.game))
                    else:
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
                base_color = (0, 200, 255)
            color = (255, 255, 0) if i == self.selected else base_color

            surf = pg.render_text(self.font, text, color)
            y = 220 + i * 60
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
