"""
ui/app.py
---------
Interactive Pygame visualizer and user interface application for BeeLogic.
Provides a 1080p Stardew Valley-inspired HUD with real-time agent telemetry,
decision matrix inspection, live candidate ranking, dynamic obstacle events,
and side-by-side performance benchmarking.
"""

import sys
import os
import pygame

from simulation.environment import Environment, GRID_COLS, GRID_ROWS
from simulation.bee import Bee
from simulation.decision import (
    SimulationController,
    STRATEGY_NEAREST,
    STRATEGY_GREEDY,
    STRATEGY_INTELLIGENT,
    STRATEGY_LABELS,
)
from simulation.sprites import SpriteManager
from analysis import comparison

from ui.theme import (
    CELL,
    MAP_W,
    MAP_H,
    GRID_X,
    GRID_Y,
    GRID_RADIUS,
    WINDOW_W,
    WINDOW_H,
    PANEL_X,
    PANEL_W,
    DEFAULT_SPEED,
    SV_WOOD_DARK,
    SV_WOOD_MAIN,
    SV_WOOD_HI,
    SV_WOOD_SH,
    SV_WOOD_RIVET,
    SV_WOOD_HEADER,
    SV_PARCHMENT,
    SV_PARCHMENT_LIGHT,
    SV_PARCHMENT_DARK,
    SV_PARCHMENT_INSET,
    SV_INSET_SHADOW,
    SV_INSET_HI,
    SV_TEXT_DARK,
    SV_TEXT_MUTED,
    SV_TEXT_TITLE,
    SV_TEXT_LIGHT,
    SV_TEXT_SHADOW,
    SV_TEXT_HI_SHADOW,
    SV_ENERGY_MAIN,
    SV_ENERGY_HI,
    SV_ENERGY_SH,
    SV_NECTAR_MAIN,
    SV_NECTAR_HI,
    SV_NECTAR_SH,
    SV_GOLD_STAR,
    SV_GOLD_WINNER,
    SV_GOLD_BORDER,
    SV_BTN_NORMAL_FILL,
    SV_BTN_NORMAL_HI,
    SV_BTN_NORMAL_SH,
    SV_BTN_HOVER_FILL,
    SV_BTN_HOVER_HI,
    SV_BTN_HOVER_SH,
    SV_BTN_ACTIVE_FILL,
    SV_BTN_ACTIVE_HI,
    SV_BTN_ACTIVE_SH,
    SV_BTN_PAUSE_FILL,
    SV_BTN_PAUSE_HI,
    SV_BTN_PAUSE_SH,
    SV_BTN_DANGER_FILL,
    SV_BTN_DANGER_HI,
    SV_BTN_DANGER_SH,
    SV_BTN_BENCH_FILL,
    SV_BTN_BENCH_HI,
    SV_BTN_BENCH_SH,
    SV_HIVE_FILL,
    SV_HIVE_ROOF,
    SV_PATH_LINE,
    SV_PATH_STEP,
    BG,
    OBSTACLE,
    OBSTACLE_BORDER,
)
from ui.widgets import (
    draw_text_shadow,
    draw_stardew_frame,
    draw_stardew_grid_border,
    draw_stardew_slot,
    draw_stardew_bar,
    draw_glass_rect,
    Button,
    Dropdown,
)


class BeeLogicApp:
    """Main interactive graphical application for BeeLogic simulation and analysis."""

    def __init__(
        self,
        seed=42,
        fullscreen=True,
        initial_strategy=STRATEGY_INTELLIGENT,
        initial_speed=DEFAULT_SPEED,
        max_steps=400,
        event_step=45,
    ):
        pygame.init()
        pygame.display.set_caption("BeeLogic - Intelligent Bee Foraging Simulation [1080p Stardew Theme]")

        self.base_w = WINDOW_W
        self.base_h = WINDOW_H
        self.canvas = pygame.Surface((self.base_w, self.base_h))

        # Fullscreen / Windowed display setup
        self.fullscreen = fullscreen
        if self.fullscreen:
            try:
                self.screen = pygame.display.set_mode((self.base_w, self.base_h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            except Exception:
                self.screen = pygame.display.set_mode((self.base_w, self.base_h))
        else:
            self.screen = pygame.display.set_mode((self.base_w, self.base_h), pygame.RESIZABLE)

        self.clock = pygame.time.Clock()

        # Scaled Typography for 1080p
        font_family = "Segoe UI, DejaVu Sans, Liberation Sans, Arial, sans-serif"
        self.font_hero = pygame.font.SysFont(font_family, 30, bold=True)
        self.font_title = pygame.font.SysFont(font_family, 24, bold=True)
        self.font_header = pygame.font.SysFont(font_family, 18, bold=True)
        self.font_body = pygame.font.SysFont(font_family, 16)
        self.font_body_bold = pygame.font.SysFont(font_family, 16, bold=True)
        self.font_small = pygame.font.SysFont(font_family, 14)
        self.font_small_bold = pygame.font.SysFont(font_family, 14, bold=True)
        self.font_badge = pygame.font.SysFont(font_family, 13, bold=True)
        self.font_button = pygame.font.SysFont(font_family, 16, bold=True)

        self.seed = seed
        self.max_steps = max_steps
        self.event_step = event_step
        self.strategies = [STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT]
        self.sim_speed = initial_speed

        self.sprite_mgr = SpriteManager(cell_size=CELL, window_size=(WINDOW_W, WINDOW_H))
        self.anim_time = 0.0

        self.running_sim = False
        self.move_accumulator = 0.0

        self.comparison_results = None
        self.show_comparison = False

        self.grid_x = GRID_X
        self.grid_y = GRID_Y
        self.grid_surface = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        self.grid_mask = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        self.grid_mask.fill((0, 0, 0, 0))
        pygame.draw.rect(self.grid_mask, (255, 255, 255, 255), (0, 0, MAP_W, MAP_H), border_radius=GRID_RADIUS)

        # Initial selected strategy index
        sel_idx = self.strategies.index(initial_strategy) if initial_strategy in self.strategies else 2
        self._build_controls(selected_idx=sel_idx)
        self.reset_simulation()

    def draw_glass_rect(self, surface, color_rgba, rect, border_radius=0, border_color=None, border_width=1):
        """Draws a translucent rectangle with optional border and border radius."""
        draw_glass_rect(surface, color_rgba, rect, border_radius=border_radius, border_color=border_color, border_width=border_width)

    def _build_controls(self, selected_idx=2):
        y = self.grid_y + MAP_H + 14
        h = 50

        self.btn_start = Button((24, y, 110, h), "Start")
        self.btn_pause = Button((144, y, 110, h), "Pause")
        self.btn_reset = Button((264, y, 110, h), "Reset")

        dropdown_options = [(s, STRATEGY_LABELS[s]) for s in self.strategies]
        self.strategy_dropdown = Dropdown((384, y, 360, h), dropdown_options, selected_idx=selected_idx)

        self.btn_speed = Button((754, y, 150, h), f"Speed: {self.sim_speed:.1f}x")
        self.btn_trigger = Button((914, y, 220, h), "Deplete Flower", is_danger=False)
        self.btn_compare = Button((1144, y, 260, h), "Run Benchmark (C)", is_benchmark=True)
        self.btn_exit = Button((1770, y, 126, h), "Quit (Esc)", is_danger=True)

        self.buttons = [
            self.btn_start,
            self.btn_pause,
            self.btn_reset,
            self.btn_speed,
            self.btn_trigger,
            self.btn_compare,
            self.btn_exit,
        ]

    def reset_simulation(self):
        self.env = Environment(seed=self.seed)
        self.bee = Bee(hive_pos=self.env.hive, max_steps=self.max_steps)
        selected_strategy = self.strategies[self.strategy_dropdown.selected_idx]
        self.controller = SimulationController(self.env, self.bee, selected_strategy, event_step=self.event_step)
        self.running_sim = False
        self.move_accumulator = 0.0
        self.event_banner = None
        self.event_banner_timer = 0

    def toggle_speed(self):
        speeds = [1.0, 2.0, 3.0, 5.0, 10.0]
        curr_idx = speeds.index(self.sim_speed) if self.sim_speed in speeds else 2
        self.sim_speed = speeds[(curr_idx + 1) % len(speeds)]
        self.btn_speed.label = f"Speed: {self.sim_speed:.1f}x"

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            win_w, win_h = self.screen.get_size()
            scale_x = self.base_w / win_w
            scale_y = self.base_h / win_h

            mapped_pos = (0, 0)
            if hasattr(event, 'pos'):
                mapped_pos = (int(event.pos[0] * scale_x), int(event.pos[1] * scale_y))

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    if self.show_comparison:
                        self.show_comparison = False
                    else:
                        pygame.quit()
                        sys.exit(0)
                elif event.key == pygame.K_SPACE:
                    self.running_sim = not self.running_sim
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_c:
                    self.run_comparison()
                elif event.key in (pygame.K_t, pygame.K_e):
                    flower = self.controller.trigger_dynamic_event()
                    if flower:
                        self.event_banner = f"Dynamic Event: Flower #{flower.id} depleted! Bee redirecting..."
                        self.event_banner_timer = 3.5

            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                adjusted_event = pygame.event.Event(event.type, pos=mapped_pos, button=getattr(event, 'button', 1))

                if adjusted_event.type == pygame.MOUSEMOTION:
                    for b in self.buttons:
                        b.update_hover(adjusted_event.pos)

                dropdown_res = self.strategy_dropdown.handle_event(adjusted_event)
                if dropdown_res is True:
                    continue
                elif isinstance(dropdown_res, int):
                    self.reset_simulation()
                    continue

                if adjusted_event.type == pygame.MOUSEBUTTONDOWN and adjusted_event.button == 1:
                    pos = adjusted_event.pos
                    if self.show_comparison:
                        self.show_comparison = False
                        continue

                    if self.btn_start.clicked(pos):
                        self.running_sim = True
                        self.show_comparison = False
                    elif self.btn_pause.clicked(pos):
                        self.running_sim = False
                    elif self.btn_reset.clicked(pos):
                        self.reset_simulation()
                        self.show_comparison = False
                    elif self.btn_speed.clicked(pos):
                        self.toggle_speed()
                    elif self.btn_trigger.clicked(pos):
                        flower = self.controller.trigger_dynamic_event()
                        if flower:
                            self.event_banner = f"Dynamic Event: Flower #{flower.id} depleted! Bee redirecting..."
                            self.event_banner_timer = 3.5
                    elif self.btn_compare.clicked(pos):
                        self.run_comparison()
                    elif self.btn_exit.clicked(pos):
                        pygame.quit()
                        sys.exit(0)
                    elif self.grid_x <= pos[0] < self.grid_x + MAP_W and self.grid_y <= pos[1] < self.grid_y + MAP_H:
                        gx = (pos[0] - self.grid_x) // CELL
                        gy = (pos[1] - self.grid_y) // CELL
                        clicked_f = self.env.get_flower_at(gx, gy)
                        if clicked_f is not None and clicked_f.is_available():
                            flower = self.controller.trigger_dynamic_event(target_flower=clicked_f)
                            if flower:
                                self.event_banner = f"Flower #{flower.id} depleted! Bee redirecting..."
                                self.event_banner_timer = 3.5

    def run_comparison(self):
        self.comparison_results = comparison.run_comparison(seed=self.seed, max_steps=self.max_steps, event_step=self.event_step)
        try:
            comparison.save_chart(self.comparison_results, path="out/comparison_chart.png")
        except Exception:
            pass
        self.show_comparison = True
        self.running_sim = False

    def update(self, dt):
        self.anim_time += dt * (min(2.5, self.sim_speed * 0.7 + 0.3) if self.running_sim else 1.0)

        if not self.running_sim or self.show_comparison:
            return

        prev_event_log = self.controller.event_log
        self.move_accumulator += dt * self.sim_speed
        while self.move_accumulator >= 1.0:
            self.controller.tick()
            self.move_accumulator -= 1.0
            if self.bee.finished:
                self.running_sim = False
                break

        if self.controller.event_log and self.controller.event_log != prev_event_log:
            self.event_banner = self.controller.event_log
            self.event_banner_timer = 3.5

        if self.event_banner_timer > 0:
            self.event_banner_timer -= dt
            if self.event_banner_timer <= 0:
                self.event_banner = None

    def cell_rect(self, x, y):
        return pygame.Rect(x * CELL, y * CELL, CELL, CELL)

    def draw_flower(self, surface, x, y, nectar, is_available, flower_id=None):
        fid = flower_id if flower_id is not None else 1
        sprite = self.sprite_mgr.get_flower_sprite(fid, is_available)
        center_x = x * CELL + CELL // 2
        center_y = y * CELL + CELL // 2
        sw, sh = sprite.get_size()
        surface.blit(sprite, (center_x - sw // 2, center_y - sh // 2))

        cell_left = x * CELL
        cell_bottom = (y + 1) * CELL

        if is_available:
            # 1. Flower Number Badge (Bottom-Left)
            if flower_id is not None:
                id_txt = f"#{flower_id}"
                tw, th = self.font_badge.size(id_txt)
                pw_id = tw + 6
                ph_id = th + 3
                px_id = cell_left + 2
                py_id = cell_bottom - ph_id - 2
                id_rect = pygame.Rect(px_id, py_id, pw_id, ph_id)
                pygame.draw.rect(surface, SV_WOOD_DARK, id_rect, border_radius=3)
                pygame.draw.rect(surface, (252, 240, 205), id_rect.inflate(-2, -2), border_radius=2)
                draw_text_shadow(surface, id_txt, self.font_badge, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (px_id + 3, py_id + 1), (0, 1))

            # 2. Golden Nectar Level Badge (Bottom-Right)
            nec_txt = str(nectar)
            tw_n, th_n = self.font_badge.size(nec_txt)
            pw_n = tw_n + 8
            ph_n = th_n + 3
            px_n = cell_left + CELL - pw_n - 2
            py_n = cell_bottom - ph_n - 2
            nec_rect = pygame.Rect(px_n, py_n, pw_n, ph_n)
            pygame.draw.rect(surface, SV_WOOD_DARK, nec_rect, border_radius=4)
            pygame.draw.rect(surface, SV_NECTAR_MAIN, nec_rect.inflate(-2, -2), border_radius=3)
            pygame.draw.line(surface, SV_NECTAR_HI, (px_n + 2, py_n + 2), (px_n + pw_n - 3, py_n + 2), 1)
            draw_text_shadow(surface, nec_txt, self.font_badge, (255, 255, 245), (70, 35, 10), (px_n + 4, py_n + 1), (1, 1))
        else:
            # 1. Depleted Flower Number Badge (Bottom-Left)
            if flower_id is not None:
                id_txt = f"#{flower_id}"
                tw, th = self.font_badge.size(id_txt)
                pw_id = tw + 6
                ph_id = th + 3
                px_id = cell_left + 2
                py_id = cell_bottom - ph_id - 2
                id_rect = pygame.Rect(px_id, py_id, pw_id, ph_id)
                pygame.draw.rect(surface, (140, 110, 85), id_rect, width=1, border_radius=3)
                pygame.draw.rect(surface, (225, 210, 190), id_rect.inflate(-2, -2), border_radius=2)
                id_surf = self.font_badge.render(id_txt, True, (140, 110, 85))
                surface.blit(id_surf, (px_id + 3, py_id + 1))

            # 2. Depleted Nectar Badge "0" (Bottom-Right)
            nec_txt = "0"
            tw_n, th_n = self.font_badge.size(nec_txt)
            pw_n = tw_n + 8
            ph_n = th_n + 3
            px_n = cell_left + CELL - pw_n - 2
            py_n = cell_bottom - ph_n - 2
            nec_rect = pygame.Rect(px_n, py_n, pw_n, ph_n)
            pygame.draw.rect(surface, (140, 110, 85), nec_rect, width=1, border_radius=3)
            pygame.draw.rect(surface, (225, 210, 190), nec_rect.inflate(-2, -2), border_radius=2)
            d_tag = self.font_badge.render(nec_txt, True, (140, 110, 85))
            surface.blit(d_tag, (px_n + 4, py_n + 1))

    def draw_bee(self, surface, x, y):
        if not self.running_sim or self.bee.finished:
            action = "idle"
        else:
            action = getattr(self.bee, "activity", "fly")
            if action not in ("fly", "harvest", "deposit", "idle"):
                action = "fly"

        direction = getattr(self.bee, "facing", "right")
        frame = self.sprite_mgr.get_bee_frame(action, direction, self.anim_time)

        # Smooth position interpolation between steps
        if self.running_sim and hasattr(self.bee, "prev_pos") and self.bee.prev_pos != (x, y):
            t = min(1.0, max(0.0, self.move_accumulator))
            vx = self.bee.prev_pos[0] + (x - self.bee.prev_pos[0]) * t
            vy = self.bee.prev_pos[1] + (y - self.bee.prev_pos[1]) * t
        else:
            vx = x
            vy = y

        cx = vx * CELL + CELL // 2
        cy = vy * CELL + CELL // 2

        # Draw soft elevation shadow under bee
        shadow_surf = pygame.Surface((36, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (15, 23, 42, 60), (0, 0, 36, 14))
        surface.blit(shadow_surf, (int(cx - 18), int(cy + 18)))

        # Blit animated bee frame
        bw = frame.get_width()
        bh = frame.get_height()
        surface.blit(frame, (int(cx - bw // 2), int(cy - bh // 2 - 2)))

        # Stardew Wooden Plaque / Parchment Scroll above Bee
        current_load = self.bee.nectar
        max_cap = self.bee.max_nectar_capacity

        if self.bee.finished:
            badge_str = f"[{current_load}/{max_cap} FINISHED]"
            badge_bg = (235, 185, 35)  # starfruit gold
            text_color = SV_TEXT_DARK
        elif current_load >= max_cap:
            badge_str = f"[{current_load}/{max_cap} FULL -> RETURNING]"
            badge_bg = SV_BTN_DANGER_FILL  # crimson ruby
            text_color = (255, 255, 255)
        elif action == "harvest":
            badge_str = f"[{current_load}/{max_cap} HARVESTING]"
            badge_bg = (220, 125, 25)  # autumn amber
            text_color = (255, 255, 255)
        elif action == "deposit":
            badge_str = f"[{current_load}/{max_cap} DEPOSITING]"
            badge_bg = (210, 135, 30)  # golden oak
            text_color = (255, 255, 255)
        elif current_load > 0:
            badge_str = f"[{current_load}/{max_cap} FORAGING]"
            badge_bg = SV_BTN_ACTIVE_FILL  # spring green
            text_color = (255, 255, 255)
        else:
            badge_str = f"[{current_load}/{max_cap} EMPTY]"
            badge_bg = (245, 230, 190)  # warm parchment
            text_color = SV_TEXT_DARK

        tw = self.font_badge.size(badge_str)[0]
        th = self.font_badge.size(badge_str)[1]
        bw_badge = tw + 14
        bh_badge = th + 6

        bx = int(cx + 26)
        by = int(cy - 28)

        if bx + bw_badge > MAP_W:
            bx = int(cx - bw_badge - 26)
        if by < 8:
            by = int(cy + 22)

        badge_rect = pygame.Rect(bx, by, bw_badge, bh_badge)
        pygame.draw.rect(surface, SV_WOOD_DARK, badge_rect, border_radius=5)
        pygame.draw.rect(surface, badge_bg, badge_rect.inflate(-2, -2), border_radius=4)
        if text_color == (255, 255, 255):
            draw_text_shadow(surface, badge_str, self.font_badge, text_color, (50, 20, 8), (bx + 7, by + 3), (1, 1))
        else:
            draw_text_shadow(surface, badge_str, self.font_badge, text_color, SV_TEXT_HI_SHADOW, (bx + 7, by + 3), (0, 1))

    def draw_grid(self):
        # 1. Clear grid surface
        self.grid_surface.fill((0, 0, 0, 0))

        # 2. Solid Grass Meadow Canvas
        grass_grid = self.sprite_mgr.get_grass_grid_surface(GRID_COLS, GRID_ROWS)
        self.grid_surface.blit(grass_grid, (0, 0))

        # 3. Grid lines (crisp subtle overlay on grass)
        grid_line_surf = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        for gx in range(1, GRID_COLS):
            pygame.draw.line(grid_line_surf, (255, 255, 255, 40), (gx * CELL, 0), (gx * CELL, MAP_H), 1)
        for gy in range(1, GRID_ROWS):
            pygame.draw.line(grid_line_surf, (255, 255, 255, 40), (0, gy * CELL), (MAP_W, gy * CELL), 1)
        self.grid_surface.blit(grid_line_surf, (0, 0))

        # 4. Obstacles (Stone Sprites)
        for (ox, oy) in self.env.obstacles:
            cx = ox * CELL + CELL // 2
            cy = oy * CELL + CELL // 2

            # Subtle drop shadow under stone
            sh_w, sh_h = int(CELL * 0.78), int(CELL * 0.28)
            shadow_surf = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (15, 35, 10, 85), (0, 0, sh_w, sh_h))
            self.grid_surface.blit(shadow_surf, (cx - sh_w // 2, cy + CELL // 4 - 4))

            stone_surf = self.sprite_mgr.get_stone_sprite(ox * 7 + oy)
            if stone_surf:
                sw, sh = stone_surf.get_size()
                self.grid_surface.blit(stone_surf, (cx - sw // 2, cy - sh // 2 - 2))
            else:
                r = pygame.Rect(ox * CELL + 4, oy * CELL + 4, CELL - 8, CELL - 8)
                pygame.draw.rect(self.grid_surface, OBSTACLE, r, border_radius=8)
                pygame.draw.rect(self.grid_surface, OBSTACLE_BORDER, r, width=1, border_radius=8)

        # Bee path: warm golden pollen trail
        if self.bee.current_path and len(self.bee.current_path) > 1:
            points = [(px * CELL + CELL // 2, py * CELL + CELL // 2) for (px, py) in self.bee.current_path]
            pygame.draw.lines(self.grid_surface, (230, 160, 20), False, points, 5)
            pygame.draw.lines(self.grid_surface, (255, 220, 80), False, points, 2)
            for (px, py) in self.bee.current_path:
                r = self.cell_rect(px, py).inflate(-44, -44)
                pygame.draw.rect(self.grid_surface, (255, 230, 110), r, border_radius=4)

        # Cozy Stardew Apiary / Hive Structure
        hx, hy = self.env.hive
        hive_rect = pygame.Rect(hx * CELL + 4, hy * CELL + 4, CELL - 8, CELL - 8)
        pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, hive_rect, border_radius=8)
        inner_h = hive_rect.inflate(-4, -4)
        pygame.draw.rect(self.grid_surface, SV_HIVE_FILL, inner_h, border_radius=6)
        # Wooden slats
        pygame.draw.line(self.grid_surface, SV_WOOD_SH, (inner_h.left, inner_h.centery - 6), (inner_h.right - 1, inner_h.centery - 6), 2)
        pygame.draw.line(self.grid_surface, SV_WOOD_SH, (inner_h.left, inner_h.centery + 6), (inner_h.right - 1, inner_h.centery + 6), 2)
        # Entrance slot
        ent_r = pygame.Rect(inner_h.centerx - 12, inner_h.bottom - 10, 24, 6)
        pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, ent_r, border_radius=2)
        # Sign label
        label = self.font_badge.render("HIVE", True, SV_TEXT_DARK)
        sign_r = pygame.Rect(hive_rect.centerx - label.get_width() // 2 - 4, hive_rect.top + 5, label.get_width() + 8, label.get_height() + 2)
        pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, sign_r, border_radius=3)
        pygame.draw.rect(self.grid_surface, SV_PARCHMENT, sign_r.inflate(-2, -2), border_radius=2)
        draw_text_shadow(self.grid_surface, "HIVE", self.font_badge, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (sign_r.x + 4, sign_r.y + 1), (0, 1))

        # Glowing Target Outline & Ribbon Badge
        target_flower = getattr(self.bee, "_target_flower", None)
        if target_flower is not None:
            r = self.cell_rect(target_flower.x, target_flower.y)
            pygame.draw.rect(self.grid_surface, (245, 175, 25), r.inflate(8, 8), width=3, border_radius=10)

            tf_id = getattr(target_flower, 'id', 'Target')
            lbl_text = f"★ TARGET #{tf_id} ★"
            lbl_w = self.font_badge.size(lbl_text)[0]
            lbl_h = self.font_badge.size(lbl_text)[1]
            pw = lbl_w + 12
            ph = lbl_h + 4
            px = r.x + (CELL - pw) // 2
            py = r.y - ph - 4
            pill_rect = pygame.Rect(px, py, pw, ph)
            pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, pill_rect, border_radius=4)
            pygame.draw.rect(self.grid_surface, (254, 240, 205), pill_rect.inflate(-2, -2), border_radius=3)
            draw_text_shadow(self.grid_surface, lbl_text, self.font_badge, (180, 85, 15), SV_TEXT_HI_SHADOW, (px + 6, py + 2), (0, 1))

        for f in self.env.flowers:
            self.draw_flower(self.grid_surface, f.x, f.y, f.nectar, f.is_available(), flower_id=f.id)

        bx, by = self.bee.pos
        self.draw_bee(self.grid_surface, bx, by)

        # 5. Mask outer corners
        self.grid_surface.blit(self.grid_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # 6. Draw timber frame border and blit meadow canvas
        grid_rect = pygame.Rect(self.grid_x, self.grid_y, MAP_W, MAP_H)
        draw_stardew_grid_border(self.canvas, grid_rect)
        self.canvas.blit(self.grid_surface, (self.grid_x, self.grid_y))

        # 7. Subtle inner dark rim ensuring seamless grass-to-frame boundary
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, grid_rect, width=2, border_radius=GRID_RADIUS)

    def draw_progress_bar(self, surface, x, y, width, height, current, max_val, fill_color):
        draw_stardew_bar(surface, x, y, width, height, current, max_val, bar_type='energy')

    def draw_panel(self):
        x = PANEL_X
        card_w = PANEL_W
        y = self.grid_y

        s = self.bee.status_dict()

        # ==============================================================
        # Card 1: Telemetry & Vitals
        # ==============================================================
        card1_h = 236
        card1 = pygame.Rect(x, y, card_w, card1_h)
        draw_stardew_frame(self.canvas, card1, is_inset=False, corner_radius=8)

        cx = x + 18
        cy = y + 16
        draw_text_shadow(self.canvas, "AGENT TELEMETRY & VITALS", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))

        # State badge
        state_text = getattr(self.bee, 'activity', 'FLYING').upper()
        if self.bee.finished:
            state_text = "COMPLETED"
            st_bg = (235, 185, 35)  # starfruit gold
            st_fg = SV_TEXT_DARK
        elif self.bee.nectar >= self.bee.max_nectar_capacity:
            state_text = "RETURNING (FULL)"
            st_bg = SV_BTN_DANGER_FILL
            st_fg = (255, 255, 255)
        elif state_text == "HARVEST":
            state_text = "HARVESTING"
            st_bg = (220, 125, 25)
            st_fg = (255, 255, 255)
        elif state_text == "DEPOSIT":
            state_text = "DEPOSITING"
            st_bg = (210, 135, 30)
            st_fg = (255, 255, 255)
        else:
            state_text = "FORAGING"
            st_bg = SV_BTN_ACTIVE_FILL
            st_fg = (255, 255, 255)

        st_w = self.font_badge.size(state_text)[0] + 16
        st_h = self.font_badge.size(state_text)[1] + 6
        st_rect = pygame.Rect(x + card_w - st_w - 20, cy - 2, st_w, st_h)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, st_rect, border_radius=4)
        pygame.draw.rect(self.canvas, st_bg, st_rect.inflate(-2, -2), border_radius=3)
        if st_fg == (255, 255, 255):
            draw_text_shadow(self.canvas, state_text, self.font_badge, st_fg, (50, 20, 10), (st_rect.x + 8, st_rect.y + 3), (1, 1))
        else:
            draw_text_shadow(self.canvas, state_text, self.font_badge, st_fg, SV_TEXT_HI_SHADOW, (st_rect.x + 8, st_rect.y + 3), (0, 1))

        cy += 32

        # Progress bars with Stardew [E] and [N] icon tiles
        e_icon_rect = pygame.Rect(cx, cy + 1, 20, 20)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, e_icon_rect, border_radius=4)
        pygame.draw.rect(self.canvas, SV_ENERGY_MAIN, e_icon_rect.inflate(-2, -2), border_radius=3)
        draw_text_shadow(self.canvas, "E", self.font_small_bold, (255, 255, 255), (20, 50, 10), (cx + 5, cy + 2), (1, 1))

        draw_text_shadow(self.canvas, "Energy Level:", self.font_body_bold, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (cx + 28, cy), (0, 1))
        e_pct = int(s['energy'] / s['max_energy'] * 100)
        e_val = f"{s['energy']} / {s['max_energy']} ({e_pct}%)"
        self.canvas.blit(self.font_small.render(e_val, True, SV_TEXT_MUTED), (cx + 138, cy + 1))
        draw_stardew_bar(self.canvas, cx + 265, cy + 2, card_w - 305, 18, s['energy'], s['max_energy'], 'energy')
        cy += 28

        n_icon_rect = pygame.Rect(cx, cy + 1, 20, 20)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, n_icon_rect, border_radius=4)
        pygame.draw.rect(self.canvas, SV_NECTAR_MAIN, n_icon_rect.inflate(-2, -2), border_radius=3)
        draw_text_shadow(self.canvas, "N", self.font_small_bold, (255, 255, 255), (60, 25, 6), (cx + 4, cy + 2), (1, 1))

        draw_text_shadow(self.canvas, "Nectar Load:", self.font_body_bold, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (cx + 28, cy), (0, 1))
        n_pct = int(s['nectar'] / s['max_nectar_capacity'] * 100)
        n_val = f"{s['nectar']} / {s['max_nectar_capacity']} ({n_pct}%)"
        self.canvas.blit(self.font_small.render(n_val, True, SV_TEXT_MUTED), (cx + 138, cy + 1))
        draw_stardew_bar(self.canvas, cx + 265, cy + 2, card_w - 305, 18, s['nectar'], s['max_nectar_capacity'], 'nectar')
        cy += 32

        # 2x2 Inset Item Slots / Metric Tiles
        tile_w = (card_w - 48) // 2
        tile_h = 52

        metrics = [
            ("Nectar Deposited", f"{s['total_nectar_collected']} units", (180, 85, 12)),
            ("Distance Travelled", f"{s['distance']} steps", SV_TEXT_DARK),
            ("Flowers Visited", f"{s['flowers_visited']} flowers", SV_TEXT_DARK),
            ("Simulation Step", f"{s['time_steps']} / {s['max_steps']}", SV_TEXT_DARK),
        ]

        for i, (m_label, m_val, m_col) in enumerate(metrics):
            tx_pos = cx + (i % 2) * (tile_w + 12)
            ty_pos = cy + (i // 2) * (tile_h + 8)
            t_rect = pygame.Rect(tx_pos, ty_pos, tile_w, tile_h)
            draw_stardew_slot(self.canvas, t_rect)

            self.canvas.blit(self.font_badge.render(m_label, True, SV_TEXT_MUTED), (tx_pos + 12, ty_pos + 6))
            draw_text_shadow(self.canvas, m_val, self.font_header, m_col, SV_TEXT_HI_SHADOW, (tx_pos + 12, ty_pos + 24), (0, 1))

        y += card1_h + 14

        # ==============================================================
        # Card 2: Decision Log & Production Rules
        # ==============================================================
        card2_h = 224
        card2 = pygame.Rect(x, y, card_w, card2_h)
        draw_stardew_frame(self.canvas, card2, is_inset=False, corner_radius=8)

        cx = x + 18
        cy = y + 16
        draw_text_shadow(self.canvas, "DECISION ENGINE & ACTIVE RULES", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        cy += 30

        target_flower = getattr(self.bee, "_target_flower", None)
        if target_flower:
            target_str = f"Target: Flower #{target_flower.id} at ({target_flower.x}, {target_flower.y}) — Nectar: {target_flower.nectar}"
            t_col = (185, 90, 15)
        elif s['target'] == "Hive":
            target_str = f"Target: Hive at ({self.env.hive[0]}, {self.env.hive[1]}) — Depositing Load"
            t_col = (195, 110, 20)
        else:
            target_str = f"Target: {s['target'] if s['target'] else 'None (Simulation Finished)'}"
            t_col = SV_TEXT_DARK

        draw_text_shadow(self.canvas, target_str, self.font_body_bold, t_col, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        cy += 28

        hx, hy = self.env.hive
        bx, by = self.bee.pos
        dist_to_hive = abs(bx - hx) + abs(by - hy)

        if self.bee.nectar >= self.bee.max_nectar_capacity:
            rule_str = "Active Rule [Capacity Max]: Capacity reached (90/90) -> Return to Hive via A*"
            r_box_fill = (248, 222, 220)
            r_border = (180, 50, 45)
            r_text_col = (150, 25, 20)
        elif self.bee.energy <= dist_to_hive + 2:
            rule_str = "Active Rule [Safety Reserve]: Energy low -> Immediate emergency return"
            r_box_fill = (248, 222, 220)
            r_border = (180, 50, 45)
            r_text_col = (150, 25, 20)
        elif self.bee.nectar > 0:
            rule_str = f"Active Rule [Partial Load ({self.bee.nectar}/90)]: Seeking optimal nectar source"
            r_box_fill = (248, 235, 195)
            r_border = (195, 130, 30)
            r_text_col = (155, 80, 12)
        else:
            rule_str = "Active Rule [Empty Capacity]: Foraging for initial high-yield flowers"
            r_box_fill = (235, 215, 175)
            r_border = (150, 105, 60)
            r_text_col = SV_TEXT_DARK

        r_box = pygame.Rect(cx, cy, card_w - 36, 34)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, r_box, border_radius=5)
        pygame.draw.rect(self.canvas, r_box_fill, r_box.inflate(-2, -2), border_radius=4)
        pygame.draw.rect(self.canvas, r_border, r_box.inflate(-2, -2), width=1, border_radius=4)
        draw_text_shadow(self.canvas, rule_str, self.font_badge, r_text_col, SV_TEXT_HI_SHADOW, (cx + 10, cy + 9), (0, 1))
        cy += 44

        draw_text_shadow(self.canvas, "Reasoning Explanation:", self.font_small_bold, SV_TEXT_MUTED, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        cy += 20
        self._draw_wrapped(s["reason"], cx, cy, card_w - 40, self.font_small, SV_TEXT_DARK, max_lines=3)

        y += card2_h + 14

        # ==============================================================
        # Card 3: Live Candidate Decision Matrix
        # ==============================================================
        card3_h = 472
        card3 = pygame.Rect(x, y, card_w, card3_h)
        draw_stardew_frame(self.canvas, card3, is_inset=False, corner_radius=8)

        cx = x + 18
        cy = y + 16
        draw_text_shadow(self.canvas, "CANDIDATE DECISION MATRIX", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))

        formula_tag = self.font_badge.render("Score = Nectar / (Dist ^ 1.5)", True, SV_TEXT_MUTED)
        self.canvas.blit(formula_tag, (x + card_w - formula_tag.get_width() - 20, cy + 2))
        cy += 30

        evals = getattr(self.bee, 'evaluations', [])
        if evals:
            headers = ["Flower ID", "Distance", "Nectar", "Score", "Decision Status"]
            col_x = [cx + 8, cx + 96, cx + 184, cx + 276, cx + 386]

            # Stardew carved walnut header banner
            th_rect = pygame.Rect(cx, cy, card_w - 36, 28)
            pygame.draw.rect(self.canvas, SV_WOOD_DARK, th_rect, border_radius=4)
            th_inner = th_rect.inflate(-2, -2)
            pygame.draw.rect(self.canvas, SV_WOOD_HEADER, th_inner, border_radius=3)
            pygame.draw.line(self.canvas, SV_WOOD_HI, (th_inner.left, th_inner.top), (th_inner.right - 1, th_inner.top), 1)
            for hx_pos, h in zip(col_x, headers):
                draw_text_shadow(self.canvas, h, self.font_badge, (255, 230, 160), (45, 20, 8), (hx_pos, cy + 6), (1, 1))
            cy += 34

            for rank_idx, cand in enumerate(evals[:6]):
                is_sel = cand.get("selected", False)
                row_r = pygame.Rect(cx, cy, card_w - 36, 34)

                if is_sel:
                    # Stardew golden honey highlight row
                    pygame.draw.rect(self.canvas, SV_WOOD_DARK, row_r, border_radius=5)
                    pygame.draw.rect(self.canvas, SV_GOLD_WINNER, row_r.inflate(-2, -2), border_radius=4)
                    pygame.draw.rect(self.canvas, SV_GOLD_BORDER, row_r.inflate(-2, -2), width=1, border_radius=4)
                    txt_c = (50, 22, 8)
                else:
                    bg_c = SV_PARCHMENT_LIGHT if rank_idx % 2 == 0 else SV_PARCHMENT_INSET
                    pygame.draw.rect(self.canvas, SV_WOOD_DARK, row_r, width=1, border_radius=4)
                    pygame.draw.rect(self.canvas, bg_c, row_r.inflate(-2, -2), border_radius=3)
                    txt_c = SV_TEXT_DARK

                if is_sel:
                    # Small golden diamond icon on the left
                    dx = col_x[0] - 2
                    dy = cy + 17
                    pygame.draw.polygon(self.canvas, SV_WOOD_DARK, [(dx, dy - 5), (dx + 5, dy), (dx, dy + 5), (dx - 5, dy)])
                    pygame.draw.polygon(self.canvas, SV_GOLD_STAR, [(dx, dy - 4), (dx + 4, dy), (dx, dy + 4), (dx - 4, dy)])

                draw_text_shadow(self.canvas, f"Flower #{cand['id']}", self.font_body_bold, txt_c, SV_TEXT_HI_SHADOW, (col_x[0] + (8 if is_sel else 0), cy + 8), (0, 1))
                draw_text_shadow(self.canvas, f"{cand['dist']} steps", self.font_body, txt_c, SV_TEXT_HI_SHADOW, (col_x[1], cy + 8), (0, 1))
                draw_text_shadow(self.canvas, f"{cand['nectar']} u", self.font_body, txt_c, SV_TEXT_HI_SHADOW, (col_x[2], cy + 8), (0, 1))
                draw_text_shadow(self.canvas, f"{cand['score']:.2f}", self.font_body, txt_c, SV_TEXT_HI_SHADOW, (col_x[3], cy + 8), (0, 1))

                if is_sel:
                    status_str = "SELECTED"
                    st_surf = self.font_badge.render(status_str, True, (255, 255, 255))
                    st_w = st_surf.get_width() + 14
                    st_h = st_surf.get_height() + 4
                    st_box = pygame.Rect(col_x[4], cy + 6, st_w, st_h)
                    pygame.draw.rect(self.canvas, SV_WOOD_DARK, st_box, border_radius=4)
                    pygame.draw.rect(self.canvas, (180, 50, 15), st_box.inflate(-2, -2), border_radius=3)
                    draw_text_shadow(self.canvas, status_str, self.font_badge, (255, 245, 220), (50, 15, 6), (col_x[4] + 7, cy + 8), (1, 1))
                else:
                    status_str = f"Rank #{rank_idx + 1}"
                    st_surf = self.font_badge.render(status_str, True, SV_TEXT_MUTED)
                    st_w = st_surf.get_width() + 10
                    st_h = st_surf.get_height() + 4
                    st_box = pygame.Rect(col_x[4], cy + 6, st_w, st_h)
                    pygame.draw.rect(self.canvas, SV_WOOD_DARK, st_box, width=1, border_radius=4)
                    pygame.draw.rect(self.canvas, (240, 220, 180), st_box.inflate(-2, -2), border_radius=3)
                    self.canvas.blit(st_surf, (col_x[4] + 5, cy + 8))

                cy += 40
        else:
            empty_msg = "No active evaluations (Bee is currently returning to Hive or idle)"
            draw_text_shadow(self.canvas, empty_msg, self.font_body, SV_TEXT_MUTED, SV_TEXT_HI_SHADOW, (cx + 10, cy + 40), (0, 1))

    def _draw_wrapped(self, text, x, y, max_width, font, color, max_lines=3):
        words = text.split(" ")
        line_text = ""
        lines = []
        for w in words:
            test = (line_text + " " + w).strip()
            if font.size(test)[0] > max_width and line_text:
                lines.append(line_text)
                line_text = w
            else:
                line_text = test
        if line_text:
            lines.append(line_text)
        for i, l in enumerate(lines[:max_lines]):
            draw_text_shadow(self.canvas, l, font, color, SV_TEXT_HI_SHADOW, (x, y + i * 20), (0, 1))

    def draw_buttons_bar(self):
        self.btn_start.active = self.running_sim
        self.btn_pause.active = not self.running_sim and not self.bee.finished

        # Stardew wooden toolbar shelf tray
        y = self.grid_y + MAP_H + 8
        tray_rect = pygame.Rect(16, y, WINDOW_W - 32, 62)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, tray_rect, border_radius=8)
        t_inner = tray_rect.inflate(-4, -4)
        pygame.draw.rect(self.canvas, (145, 82, 30), t_inner, border_radius=6)
        pygame.draw.line(self.canvas, SV_WOOD_HI, (t_inner.left + 2, t_inner.top + 1), (t_inner.right - 3, t_inner.top + 1), 2)
        pygame.draw.line(self.canvas, (90, 44, 16), (t_inner.left + 2, t_inner.bottom - 2), (t_inner.right - 3, t_inner.bottom - 2), 2)

        # Shelf recessed groove
        groove = t_inner.inflate(-6, -6)
        pygame.draw.rect(self.canvas, (65, 34, 15), groove, border_radius=4)

        for b in self.buttons:
            b.draw(self.canvas, self.font_button)

        self.strategy_dropdown.draw(self.canvas, self.font_button)

        # Bottom Shortcut & Info Line with Stardew text shadow
        shortcut_text = "Shortcuts: [Space] Start / Pause   |   [R] Reset Simulation   |   [C] Run Benchmark   |   [Esc / Q] Quit Application"
        draw_text_shadow(self.canvas, shortcut_text, self.font_small_bold, (255, 246, 225), (42, 20, 8), (24, 1054), (1, 1))

        info_text = f"Environment Seed: {self.seed}"
        info_w = self.font_small_bold.size(info_text)[0]
        draw_text_shadow(self.canvas, info_text, self.font_small_bold, (255, 246, 225), (42, 20, 8), (WINDOW_W - info_w - 24, 1054), (1, 1))

    def draw_event_banner(self):
        text = self.font_header.render(self.event_banner, True, (255, 255, 245))
        pad_x = 28
        pad_y = 12
        w = text.get_width() + pad_x * 2
        h = text.get_height() + pad_y * 2
        rect = pygame.Rect(self.grid_x + (MAP_W - w) // 2, self.grid_y + 18, w, h)
        # Stardew wooden event plaque
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, rect, border_radius=8)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(self.canvas, SV_BTN_DANGER_FILL, inner, border_radius=6)
        pygame.draw.line(self.canvas, SV_BTN_DANGER_HI, (inner.left + 2, inner.top + 1), (inner.right - 3, inner.top + 1), 2)
        pygame.draw.line(self.canvas, SV_BTN_DANGER_SH, (inner.left + 2, inner.bottom - 2), (inner.right - 3, inner.bottom - 2), 2)
        draw_text_shadow(self.canvas, self.event_banner, self.font_header, (255, 250, 235), (50, 15, 8), (rect.x + pad_x, rect.y + pad_y), (1, 1))

    def draw_comparison_overlay(self):
        # Warm twilight dimming overlay
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((30, 18, 10, 235))
        self.canvas.blit(overlay, (0, 0))

        # Main Bulletin Board / Farmer's Journal Frame
        main_box = pygame.Rect(70, 36, 1780, 1008)
        draw_stardew_frame(self.canvas, main_box, is_inset=False, corner_radius=12)

        # Ornate Carved Wooden Header Banner Ribbon
        header_banner = pygame.Rect(100, 60, 1720, 66)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, header_banner, border_radius=8)
        banner_inner = header_banner.inflate(-4, -4)
        pygame.draw.rect(self.canvas, (138, 32, 28), banner_inner, border_radius=6)
        pygame.draw.line(self.canvas, (215, 75, 65), (banner_inner.left + 2, banner_inner.top + 1), (banner_inner.right - 3, banner_inner.top + 1), 2)
        pygame.draw.line(self.canvas, (80, 18, 14), (banner_inner.left + 2, banner_inner.bottom - 2), (banner_inner.right - 3, banner_inner.bottom - 2), 2)

        # Golden banner trim line
        pygame.draw.rect(self.canvas, SV_WOOD_RIVET, banner_inner.inflate(-4, -4), width=1, border_radius=4)

        title_str = "STRATEGY COMPARISON & PERFORMANCE BENCHMARK"
        tw, th = self.font_hero.size(title_str)
        tx = 100 + (1720 - tw) // 2
        ty = 76

        # Golden star emblems flanking title
        for dx in [tx - 26, tx + tw + 26]:
            pygame.draw.polygon(self.canvas, SV_WOOD_DARK, [(dx, ty + 16 - 8), (dx + 8, ty + 16), (dx, ty + 16 + 8), (dx - 8, ty + 16)])
            pygame.draw.polygon(self.canvas, SV_GOLD_STAR, [(dx, ty + 16 - 6), (dx + 6, ty + 16), (dx, ty + 16 + 6), (dx - 6, ty + 16)])

        draw_text_shadow(self.canvas, title_str, self.font_hero, (255, 225, 120), (50, 12, 8), (tx, ty), (1, 2))

        sub_str = "Empirical field trial of Nearest Neighbor (BFS), Greedy (Highest Nectar), and Intelligent Weighted A* Search"
        draw_text_shadow(self.canvas, sub_str, self.font_body, SV_TEXT_MUTED, SV_TEXT_HI_SHADOW, (110, 136), (0, 1))

        headers = ["Strategy", "Nectar Collected", "Distance Travelled", "Energy Consumed", "Flowers Visited", "Time Steps", "Efficiency Ratio"]
        col_x = [120, 520, 760, 1000, 1220, 1420, 1600]

        y = 168
        # Table Header Banner
        th_box = pygame.Rect(100, y, 1720, 36)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, th_box, border_radius=6)
        th_inner = th_box.inflate(-2, -2)
        pygame.draw.rect(self.canvas, SV_WOOD_HEADER, th_inner, border_radius=5)
        pygame.draw.line(self.canvas, SV_WOOD_HI, (th_inner.left, th_inner.top), (th_inner.right - 1, th_inner.top), 1)

        for cx, h in zip(col_x, headers):
            draw_text_shadow(self.canvas, h, self.font_header, (255, 230, 150), (45, 18, 6), (cx, y + 6), (1, 1))
        y += 46

        if self.comparison_results:
            best_eff = max(r["efficiency"] for r in self.comparison_results)
            for r in self.comparison_results:
                is_winner = (r["efficiency"] == best_eff)
                row_box = pygame.Rect(100, y, 1720, 42)

                if is_winner:
                    # Winner row in golden starfruit wood
                    pygame.draw.rect(self.canvas, SV_WOOD_DARK, row_box, border_radius=6)
                    pygame.draw.rect(self.canvas, SV_GOLD_WINNER, row_box.inflate(-2, -2), border_radius=5)
                    pygame.draw.rect(self.canvas, SV_GOLD_BORDER, row_box.inflate(-2, -2), width=1, border_radius=5)
                    txt_color = (54, 22, 6)
                    # Gold Star emblem
                    dx = col_x[0] - 8
                    dy = y + 21
                    pygame.draw.polygon(self.canvas, SV_WOOD_DARK, [(dx, dy - 7), (dx + 7, dy), (dx, dy + 7), (dx - 7, dy)])
                    pygame.draw.polygon(self.canvas, SV_GOLD_STAR, [(dx, dy - 5), (dx + 5, dy), (dx, dy + 5), (dx - 5, dy)])
                else:
                    pygame.draw.rect(self.canvas, SV_WOOD_DARK, row_box, width=1, border_radius=6)
                    row_bg = SV_PARCHMENT_LIGHT if (y // 48) % 2 == 0 else SV_PARCHMENT_INSET
                    pygame.draw.rect(self.canvas, row_bg, row_box.inflate(-2, -2), border_radius=5)
                    txt_color = SV_TEXT_DARK

                values = [
                    r["label"] + (" [WINNER]" if is_winner else ""),
                    f"{r['nectar_collected']} units",
                    f"{r['distance_travelled']} steps",
                    f"{r['energy_consumed']} units",
                    f"{r['flowers_visited']} flowers",
                    f"{r['time_steps']} steps",
                    f"{r['efficiency']:.3f} (Nectar/Dist)",
                ]
                for cx, v in zip(col_x, values):
                    fnt = self.font_body_bold if is_winner else self.font_body
                    draw_text_shadow(self.canvas, v, fnt, txt_color, SV_TEXT_HI_SHADOW, (cx + (10 if is_winner and cx == col_x[0] else 0), y + 10), (0, 1))
                y += 48

            y += 18
            # Inset Visual Efficiency Chart Box
            chart_box = pygame.Rect(100, y, 1720, 230)
            draw_stardew_slot(self.canvas, chart_box)

            chart_title = "VISUAL EFFICIENCY BENCHMARK (Nectar Collected / Distance Travelled)"
            cdx = 120
            cdy = y + 24
            pygame.draw.polygon(self.canvas, SV_WOOD_DARK, [(cdx, cdy - 5), (cdx + 5, cdy), (cdx, cdy + 5), (cdx - 5, cdy)])
            pygame.draw.polygon(self.canvas, SV_GOLD_STAR, [(cdx, cdy - 4), (cdx + 4, cdy), (cdx, cdy + 4), (cdx - 4, cdy)])
            draw_text_shadow(self.canvas, chart_title, self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (135, y + 14), (0, 1))

            max_eff = max(r["efficiency"] for r in self.comparison_results) or 1.0

            # Stardew harvest bar colors: Blueberry Blue, Pumpkin Orange, Starfruit Gold
            bar_colors = [
                ((58, 135, 215), (115, 185, 245), (35, 95, 165)),
                ((235, 135, 35), (255, 185, 95), (170, 85, 15)),
                ((245, 195, 35), (255, 235, 115), (180, 135, 15)),
            ]

            bar_y = y + 52
            for i, r in enumerate(self.comparison_results):
                lbl = r["label"].split(" (")[0]
                draw_text_shadow(self.canvas, lbl, self.font_body_bold, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (130, bar_y + 4), (0, 1))

                bar_max_w = 1100
                bar_w = max(6, int((r["efficiency"] / max_eff) * bar_max_w))

                # Dark soil recessed groove
                track_r = pygame.Rect(380, bar_y, bar_max_w, 28)
                pygame.draw.rect(self.canvas, SV_WOOD_DARK, track_r, border_radius=5)
                groove_r = track_r.inflate(-2, -2)
                pygame.draw.rect(self.canvas, (68, 38, 18), groove_r, border_radius=4)

                # Filled glossy bar
                c_main, c_hi, c_sh = bar_colors[i % len(bar_colors)]
                fill_r = pygame.Rect(groove_r.x, groove_r.y, bar_w, groove_r.h)
                pygame.draw.rect(self.canvas, c_main, fill_r, border_radius=4)
                pygame.draw.line(self.canvas, c_hi, (fill_r.left + 1, fill_r.top + 1), (fill_r.right - 2, fill_r.top + 1), 2)
                pygame.draw.line(self.canvas, c_sh, (fill_r.left + 1, fill_r.bottom - 2), (fill_r.right - 2, fill_r.bottom - 2), 2)

                eff_txt = f"{r['efficiency']:.3f} Nectar/Step"
                draw_text_shadow(self.canvas, eff_txt, self.font_header, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (1500, bar_y + 4), (0, 1))
                bar_y += 46

            y += 248

            # Two Pinned Summary Notes (Cards A and B)
            box_w = 845
            box_h = 160

            # Card A: Key Findings
            v_box1 = pygame.Rect(100, y, box_w, box_h)
            draw_stardew_slot(self.canvas, v_box1)
            pygame.draw.circle(self.canvas, SV_WOOD_DARK, (v_box1.centerx, v_box1.top + 6), 6)
            pygame.draw.circle(self.canvas, SV_WOOD_RIVET, (v_box1.centerx, v_box1.top + 6), 4)

            intel = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_INTELLIGENT)
            greedy = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_GREEDY)
            nearest = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_NEAREST)

            eff_diff = ((intel["efficiency"] - greedy["efficiency"]) / max(0.001, greedy["efficiency"])) * 100
            dist_diff = ((greedy["distance_travelled"] - intel["distance_travelled"]) / max(1, intel["distance_travelled"])) * 100

            draw_text_shadow(self.canvas, "KEY QUANTITATIVE FINDINGS", self.font_header, (180, 85, 15), SV_TEXT_HI_SHADOW, (130, y + 16), (0, 1))
            v_text1 = f"• Intelligent Bee achieved +{eff_diff:.1f}% higher efficiency than Highest Nectar (Greedy)."
            v_text2 = f"• Greedy strategy traveled {dist_diff:.1f}% farther due to unweighted heuristic choices."
            v_text3 = f"• Nearest Neighbor collected fewer total nectar units due to sub-optimal local clustering."

            draw_text_shadow(self.canvas, v_text1, self.font_body, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (130, y + 50), (0, 1))
            draw_text_shadow(self.canvas, v_text2, self.font_body, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (130, y + 80), (0, 1))
            draw_text_shadow(self.canvas, v_text3, self.font_body, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (130, y + 110), (0, 1))

            # Card B: Decision-Theoretic Summary
            v_box2 = pygame.Rect(975, y, box_w, box_h)
            draw_stardew_slot(self.canvas, v_box2)
            pygame.draw.circle(self.canvas, SV_WOOD_DARK, (v_box2.centerx, v_box2.top + 6), 6)
            pygame.draw.circle(self.canvas, SV_WOOD_RIVET, (v_box2.centerx, v_box2.top + 6), 4)

            draw_text_shadow(self.canvas, "CLASSICAL AI & DECISION-THEORETIC SUMMARY", self.font_header, (65, 140, 40), SV_TEXT_HI_SHADOW, (1005, y + 16), (0, 1))
            c_text1 = "• Production Rules: Capacity threshold (90/90) & energy reserve safety margins."
            c_text2 = "• Heuristic Formulation: Score = Nectar / (Distance ^ 1.5) balances yield & cost."
            c_text3 = "• Pathfinding: Optimal obstacle traversal via A* Search and BFS grid exploration."

            draw_text_shadow(self.canvas, c_text1, self.font_body, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (1005, y + 50), (0, 1))
            draw_text_shadow(self.canvas, c_text2, self.font_body, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (1005, y + 80), (0, 1))
            draw_text_shadow(self.canvas, c_text3, self.font_body, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (1005, y + 110), (0, 1))

        # High-contrast wooden footer prompt bar
        footer_box = pygame.Rect(100, 960, 1720, 48)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, footer_box, border_radius=8)
        f_inner = footer_box.inflate(-4, -4)
        pygame.draw.rect(self.canvas, (105, 52, 20), f_inner, border_radius=6)
        pygame.draw.line(self.canvas, SV_WOOD_HI, (f_inner.left + 2, f_inner.top + 1), (f_inner.right - 3, f_inner.top + 1), 2)
        pygame.draw.line(self.canvas, (55, 24, 8), (f_inner.left + 2, f_inner.bottom - 2), (f_inner.right - 3, f_inner.bottom - 2), 2)

        for rx in [footer_box.left + 16, footer_box.right - 16]:
            pygame.draw.circle(self.canvas, SV_WOOD_DARK, (rx, footer_box.centery), 5)
            pygame.draw.circle(self.canvas, SV_WOOD_RIVET, (rx, footer_box.centery), 3)

        hint_str = "Click anywhere or press [ ESC ] / [ SPACE ] to return to simulation"
        hw, hh = self.font_body_bold.size(hint_str)
        hx = footer_box.centerx - hw // 2
        hy = footer_box.centery - hh // 2
        draw_text_shadow(self.canvas, hint_str, self.font_body_bold, (255, 248, 220), (35, 12, 4), (hx, hy), (1, 1))

    def draw(self):
        backdrop = self.sprite_mgr.get_backdrop_frame(self.anim_time)
        if backdrop is not None:
            self.canvas.blit(backdrop, (0, 0))
        else:
            self.canvas.fill(BG)

        self.draw_grid()
        self.draw_panel()
        self.draw_buttons_bar()
        if self.show_comparison:
            self.draw_comparison_overlay()
        if self.event_banner:
            self.draw_event_banner()

        win_size = self.screen.get_size()
        if win_size == (self.base_w, self.base_h):
            self.screen.blit(self.canvas, (0, 0))
        else:
            scaled_surface = pygame.transform.smoothscale(self.canvas, win_size)
            self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()


def run_gui(seed=42, fullscreen=True, initial_strategy=STRATEGY_INTELLIGENT, initial_speed=DEFAULT_SPEED, max_steps=400, event_step=45):
    """Entry point helper to launch the graphical visualizer application."""
    app = BeeLogicApp(
        seed=seed,
        fullscreen=fullscreen,
        initial_strategy=initial_strategy,
        initial_speed=initial_speed,
        max_steps=max_steps,
        event_step=event_step,
    )
    app.run()
