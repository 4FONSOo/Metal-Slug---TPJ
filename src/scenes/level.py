# scenes/level.py
"""
Cena principal de jogo (nível actual).

Responsabilidades:
  - Delegar input para jogador / pause / menu.
  - Actualizar lógica de jogo (player, inimigos, boss, pickups, projécteis, granadas).
  - Detectar fim de nível (>=60% inimigos mortos e nenhum activo) e
    mudar para LevelCompleteScene.
  - Desenhar cena + HUD + overlay de FX (flash, slow-motion, etc.).
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, List

import pg_engine as pg
import config
import controls

from scene import Scene
from scenes.menu import Menu as MenuScene, PauseMenu
from scenes.flow import LevelCompleteScene

if TYPE_CHECKING:
    from game_state import Game


class LevelScene(Scene):
    """
    Cena que trata do jogo em si (nível actual).
    """

    # ------------------------------------------------------------------ #
    # INPUT
    # ------------------------------------------------------------------ #
    def handle_input(self, events: List[pg.Event]) -> None:
        game: "Game" = self.game
        menu_key = controls.get_key(controls.MENU)
        pause_key = controls.get_key(controls.PAUSE)

        for event in events:
            if event.type == pg.QUIT:
                game.sound.stop_music()
                pg.quit()
                sys.exit()

            cheat_consumed = game.process_cheats(event)

            if event.type == pg.KEYDOWN:
                if event.key == menu_key:
                    game.reset_all_state()
                    game.change_scene(MenuScene(game))
                    return

                if event.key == pause_key and not cheat_consumed:
                    game.change_scene(PauseMenu(game, previous_scene=self))
                    return

            if game.game_state and event.type == game.game_state.timer_event:
                if not game.infinite_time:
                    game.game_state.update_time()

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def update(self, dt: float) -> None:
        game: "Game" = self.game

        # dt "real" (antes de slow-motion)
        dt_seconds_raw = dt / 1000.0 if dt else 0.0

        # Actualizar FX em tempo real (flash, nuke, slow-motion, shake, …)
        if game.effects:
            game.effects.update(dt_seconds_raw)
            time_scale = game.effects.get_time_scale()
        else:
            time_scale = 1.0

        # dt afectado por slow-motion (para lógica de jogo)
        dt_seconds = dt_seconds_raw * time_scale
        dt_ms_scaled = dt * time_scale if dt else 0.0

        # Condição de timeout / fim de nível por tempo
        timeout = (
            game.game_state
            and game.game_state.time_left <= 0
            and not game.infinite_time
        )

        if timeout:
            player_alive = bool(game.player and game.player.alive)

            if player_alive:
                try:
                    game.sound.play_level_end()
                except Exception:
                    pass
            else:
                try:
                    game.sound.play_game_over_sfx()
                except Exception:
                    pass

            game.handle_game_over()
            return

        # Pausa lógica
        if game.game_state and game.game_state.paused:
            return

        # ---------------- JOGADOR ----------------
        keys = pg.get_keys()
        if game.player:
            game.player.handle_input(keys)
            game.player.update_animation(dt_ms_scaled)
            game.player.apply_gravity()
            game.handle_combat(dt_seconds)

        # ---------------- INIMIGOS ----------------
        if game.enemy_manager:
            game.enemy_manager.update(dt_seconds)
            game.enemies = game.enemy_manager.get_enemies()
            # projécteis de inimigos passam a ser geridos dentro dos inimigos
            # via ProjectileManager

        # ---------------- BOSS ----------------
        game.update_boss(dt_seconds)

        # ---------------- PICKUPS ----------------
        if game.pickup_manager:
            player_rect = game.player.rect if game.player else None
            pickup_events = game.pickup_manager.update(
                dt_seconds,
                player_rect=player_rect,
            )
            for ev in pickup_events:
                game.apply_pickup_effect(ev.effect)

        # ---------------- PROJÉCTEIS ----------------
        if game.projectile_manager:
            game.projectile_manager.update(dt_seconds)

        # ---------------- GRANADAS ----------------
        game.update_granades(dt_ms_scaled)

        # ---------------- COLISÕES ----------------
        game.handle_collisions()

        # Se a cena tiver mudado para outra (ex: Game Over / Menu),
        # não continuamos a actualizar lógica desta cena.
        if not isinstance(game.current_scene, LevelScene):
            return

        # ---------------- FIM DE NÍVEL (Lvl1 → Lvl2) ----------------
        # Só fazemos auto-transição quando estamos no 1.º nível
        # (debug_level_index == 0) e já não há inimigos vivos nem spawns.
        if (
            getattr(game, "debug_level_index", 0) == 0
            and game.enemy_manager is not None
        ):
            em = game.enemy_manager
            try:
                total_max = em.max_spawns
                total_spawned = em.total_spawned
                active_now = em.active_enemies_count
            except Exception:
                total_max = 0
                total_spawned = 0
                active_now = 0

            if total_max > 0:
                killed = max(0, total_spawned - active_now)
                kill_ratio = killed / float(total_max)

                enough_kills = kill_ratio >= 0.60
                no_active_enemies = active_now == 0

                if enough_kills and no_active_enemies:
                    # Transição para cena de 'COMPLETE';
                    # a própria LevelCompleteScene trata depois de LoadingScene
                    # e esta chama game.go_to_next_level().
                    game.change_scene(LevelCompleteScene(game))
                    return

        # ---------------- FLOATING TEXTS ----------------
        for text in game.floating_texts:
            text.update()
        game.floating_texts = [t for t in game.floating_texts if t.lifetime > 0]

        # ---------------- CÂMARA / POV ----------------
        if game.player:
            game.POV = game.player.rect.centerx - config.WIDTH // 2
            game.POV = max(0, min(game.POV, game.bg_width - config.WIDTH))

    # ------------------------------------------------------------------ #
    # DRAW
    # ------------------------------------------------------------------ #
    def draw(self, screen: pg.Surface) -> None:
        game: "Game" = self.game

        # Cena normal (background, inimigos, player, projécteis, HUD, etc.)
        game.draw_scene()
        game.draw_hud()

        # Overlay de flash / FX (NUKE, cheats, hits fortes, etc.)
        if game.effects:
            tint = game.effects.get_screen_tint()
            if tint is not None:
                color, intensity = tint
                if intensity > 0.0:
                    overlay = pg.create_surface(
                        (config.WIDTH, config.HEIGHT),
                        alpha=True,
                    )
                    alpha = int(max(0.0, min(1.0, intensity)) * 255)
                    overlay.fill((color[0], color[1], color[2], alpha))
                    screen.blit(overlay, (0, 0))
