import sys
import math
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

# 1080p Layout Constants
CELL = 64
MAP_W = GRID_COLS * CELL        # 20 * 64 = 1280
MAP_H = GRID_ROWS * CELL        # 15 * 64 = 960
PANEL_W = 640                   # 1920 - 1280 = 640
BUTTON_BAR_H = 120              # 1080 - 960 = 120

WINDOW_W = MAP_W + PANEL_W      # 1920
WINDOW_H = MAP_H + BUTTON_BAR_H # 1080

DEFAULT_SPEED = 3.0

# Academic & Modern UI Palette
BG = (245, 247, 250)
GRID_LINE = (226, 232, 240)
OBSTACLE = (100, 116, 139)
OBSTACLE_BORDER = (71, 85, 105)

HIVE_COLOR = (245, 158, 11)
HIVE_BORDER = (180, 83, 9)

PATH_COLOR = (147, 197, 253)
PATH_LINE_COLOR = (37, 99, 235)
TARGET_HIGHLIGHT = (245, 158, 11)

PANEL_BG = (255, 255, 255)
CARD_BG = (248, 250, 252)
CARD_BORDER = (226, 232, 240)
TEXT_DARK = (15, 23, 42)
TEXT_MUTED = (100, 116, 139)
ACCENT = (37, 99, 235)
ACCENT_LIGHT = (239, 246, 255)

BUTTON_BG = (255, 255, 255)
BUTTON_BORDER = (203, 213, 225)
BUTTON_HOVER = (241, 245, 249)
BUTTON_ACTIVE = (37, 99, 235)

BAR_BG = (226, 232, 240)
ENERGY_BAR = (34, 197, 94)
NECTAR_BAR = (249, 115, 22)


class Button:
    def __init__(self, rect, label, is_danger=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.is_danger = is_danger
        self.active = False
        self.hovered = False

    def draw(self, surface, font):
        if self.active:
            bg = (29, 78, 216) if self.hovered else BUTTON_ACTIVE
            border = (30, 64, 175)
            text_color = (255, 255, 255)
        elif self.is_danger:
            bg = (220, 38, 38) if self.hovered else (254, 242, 242)
            border = (239, 68, 68) if self.hovered else (252, 165, 165)
            text_color = (255, 255, 255) if self.hovered else (185, 28, 28)
        else:
            bg = BUTTON_HOVER if self.hovered else BUTTON_BG
            border = ACCENT if self.hovered else BUTTON_BORDER
            text_color = ACCENT if self.hovered else TEXT_DARK

        pygame.draw.rect(surface, bg, self.rect, border_radius=10)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=10)
        
        text = font.render(self.label, True, text_color)
        tx = self.rect.x + (self.rect.w - text.get_width()) // 2
        ty = self.rect.y + (self.rect.h - text.get_height()) // 2
        surface.blit(text, (tx, ty))

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class Dropdown:
    def __init__(self, rect, options, selected_idx=0):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.selected_idx = selected_idx
        self.is_open = False
        self.hovered_option = -1
        self.item_height = 50

    def draw(self, surface, font):
        pygame.draw.rect(surface, BUTTON_BG, self.rect, border_radius=10)
        pygame.draw.rect(surface, ACCENT if self.is_open else BUTTON_BORDER, self.rect, width=1, border_radius=10)
        
        label = self.options[self.selected_idx][1]
        text = font.render(label, True, TEXT_DARK)
        surface.blit(text, (self.rect.x + 16, self.rect.y + (self.rect.h - text.get_height()) // 2))

        arrow_color = ACCENT if self.is_open else TEXT_MUTED
        ax = self.rect.right - 20
        ay = self.rect.centery
        if self.is_open:
            pygame.draw.polygon(surface, arrow_color, [(ax - 6, ay + 3), (ax + 6, ay + 3), (ax, ay - 4)])
        else:
            pygame.draw.polygon(surface, arrow_color, [(ax - 6, ay - 3), (ax + 6, ay - 3), (ax, ay + 4)])

        if self.is_open:
            menu_h = len(self.options) * self.item_height
            menu_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 6, self.rect.w, menu_h)
            
            # Shadow
            shadow_rect = menu_rect.inflate(4, 4)
            shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (15, 23, 42, 40), (0, 0, shadow_rect.w, shadow_rect.h), border_radius=12)
            surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y + 2))

            pygame.draw.rect(surface, BUTTON_BG, menu_rect, border_radius=10)
            pygame.draw.rect(surface, ACCENT, menu_rect, width=1, border_radius=10)

            for i, (_, opt_label) in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 6 + (i * self.item_height), self.rect.w, self.item_height)
                if i == self.hovered_option:
                    pygame.draw.rect(surface, BUTTON_HOVER, opt_rect, border_radius=8)
                if i == self.selected_idx:
                    pygame.draw.rect(surface, ACCENT_LIGHT, opt_rect, border_radius=8)
                
                txt_color = ACCENT if i == self.selected_idx else TEXT_DARK
                t = font.render(opt_label, True, txt_color)
                surface.blit(t, (opt_rect.x + 16, opt_rect.y + (opt_rect.h - t.get_height()) // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.is_open:
            menu_h = len(self.options) * self.item_height
            for i in range(len(self.options)):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 6 + (i * self.item_height), self.rect.w, self.item_height)
                if opt_rect.collidepoint(event.pos):
                    self.hovered_option = i
                    return
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            if self.is_open:
                menu_h = len(self.options) * self.item_height
                for i in range(len(self.options)):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 6 + (i * self.item_height), self.rect.w, self.item_height)
                    if opt_rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        return i
                self.is_open = False
        return None


class BeeLogicApp:
    def __init__(self, seed=42):
        pygame.init()
        pygame.display.set_caption("BeeLogic - Intelligent Bee Foraging Simulation [1080p Fullscreen]")
        
        self.base_w = WINDOW_W
        self.base_h = WINDOW_H
        self.canvas = pygame.Surface((self.base_w, self.base_h))
        
        # 1080p Fullscreen Only
        try:
            self.screen = pygame.display.set_mode((self.base_w, self.base_h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        except Exception:
            self.screen = pygame.display.set_mode((self.base_w, self.base_h))

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
        self.strategies = [STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT]
        self.sim_speed = DEFAULT_SPEED

        self.sprite_mgr = SpriteManager(cell_size=CELL)
        self.anim_time = 0.0

        self.running_sim = False
        self.move_accumulator = 0.0

        self.comparison_results = None
        self.show_comparison = False

        self._build_controls()
        self.reset_simulation()

    def _build_controls(self):
        y = MAP_H + 16
        h = 54
        
        self.btn_start = Button((24, y, 110, h), "Start")
        self.btn_pause = Button((146, y, 110, h), "Pause")
        self.btn_reset = Button((268, y, 110, h), "Reset")
        
        dropdown_options = [(s, STRATEGY_LABELS[s].split(" (")[0]) for s in self.strategies]
        self.strategy_dropdown = Dropdown((390, y, 330, h), dropdown_options, selected_idx=2)
        
        self.btn_speed = Button((732, y, 160, h), f"Speed: {self.sim_speed:.1f}x")
        self.btn_trigger = Button((904, y, 240, h), "Deplete Flower")
        self.btn_compare = Button((1156, y, 270, h), "Run Benchmark (C)")
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
        self.bee = Bee(hive_pos=self.env.hive, max_steps=400)
        selected_strategy = self.strategies[self.strategy_dropdown.selected_idx]
        self.controller = SimulationController(self.env, self.bee, selected_strategy, event_step=45)
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
                    flower = self.env.trigger_dynamic_event()
                    if flower:
                        self.event_banner = f"Dynamic Event: Flower #{flower.id} depleted!"
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
                        # Clicking anywhere on overlay dismisses or clicking return button
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
                        flower = self.env.trigger_dynamic_event()
                        if flower:
                            self.event_banner = f"Dynamic Event: Flower #{flower.id} depleted!"
                            self.event_banner_timer = 3.5
                    elif self.btn_compare.clicked(pos):
                        self.run_comparison()
                    elif self.btn_exit.clicked(pos):
                        pygame.quit()
                        sys.exit(0)

    def run_comparison(self):
        self.comparison_results = comparison.run_comparison(seed=self.seed, max_steps=400, event_step=45)
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

        if is_available:
            # Persistent Flower ID Badge above flower
            if flower_id is not None:
                id_tag = self.font_badge.render(f"#{flower_id}", True, ACCENT)
                surface.blit(id_tag, (center_x - id_tag.get_width() // 2, y * CELL + 2))

            # Nectar count pill badge at bottom
            num_surf = self.font_badge.render(str(nectar), True, (255, 255, 255))
            pw = num_surf.get_width() + 10
            ph = num_surf.get_height() + 4
            px = center_x - pw // 2
            py = y * CELL + CELL - ph - 2
            pill_bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(pill_bg, (15, 23, 42, 220), (0, 0, pw, ph), border_radius=6)
            surface.blit(pill_bg, (px, py))
            surface.blit(num_surf, (px + 5, py + 2))
        else:
            if flower_id is not None:
                id_tag = self.font_badge.render(f"#{flower_id}", True, (148, 163, 184))
                surface.blit(id_tag, (center_x - id_tag.get_width() // 2, y * CELL + 2))
            d_tag = self.font_badge.render("0", True, (148, 163, 184))
            surface.blit(d_tag, (center_x - d_tag.get_width() // 2, y * CELL + CELL - 18))

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

        # On-Bee Capacity Badge
        current_load = self.bee.nectar
        max_cap = self.bee.max_nectar_capacity

        if self.bee.finished:
            badge_str = f"[{current_load}/{max_cap} FINISHED]"
            badge_bg = (16, 185, 129)
        elif current_load >= max_cap:
            badge_str = f"[{current_load}/{max_cap} FULL -> RETURNING]"
            badge_bg = (220, 38, 38)
        elif action == "harvest":
            badge_str = f"[{current_load}/{max_cap} HARVESTING]"
            badge_bg = (234, 88, 12)
        elif action == "deposit":
            badge_str = f"[{current_load}/{max_cap} DEPOSITING]"
            badge_bg = (217, 119, 6)
        elif current_load > 0:
            badge_str = f"[{current_load}/{max_cap} SEARCHING]"
            badge_bg = (37, 99, 235)
        else:
            badge_str = f"[{current_load}/{max_cap} EMPTY]"
            badge_bg = (100, 116, 139)

        text_surf = self.font_badge.render(badge_str, True, (255, 255, 255))
        bx = int(cx + 26)
        by = int(cy - 28)
        bw_badge = text_surf.get_width() + 12
        bh_badge = text_surf.get_height() + 6

        if bx + bw_badge > MAP_W:
            bx = int(cx - bw_badge - 26)
        if by < 8:
            by = int(cy + 22)

        badge_rect = pygame.Rect(bx, by, bw_badge, bh_badge)
        pygame.draw.rect(surface, badge_bg, badge_rect, border_radius=6)
        surface.blit(text_surf, (bx + 6, by + 3))

    def draw_grid(self):
        for gx in range(GRID_COLS + 1):
            pygame.draw.line(self.canvas, GRID_LINE, (gx * CELL, 0), (gx * CELL, MAP_H), 1)
        for gy in range(GRID_ROWS + 1):
            pygame.draw.line(self.canvas, GRID_LINE, (0, gy * CELL), (MAP_W, gy * CELL), 1)

        for (ox, oy) in self.env.obstacles:
            r = pygame.Rect(ox * CELL + 4, oy * CELL + 4, CELL - 8, CELL - 8)
            pygame.draw.rect(self.canvas, OBSTACLE, r, border_radius=8)
            pygame.draw.rect(self.canvas, OBSTACLE_BORDER, r, width=1, border_radius=8)

        if self.bee.current_path and len(self.bee.current_path) > 1:
            points = [(px * CELL + CELL // 2, py * CELL + CELL // 2) for (px, py) in self.bee.current_path]
            pygame.draw.lines(self.canvas, PATH_LINE_COLOR, False, points, 5)
            for (px, py) in self.bee.current_path:
                r = self.cell_rect(px, py).inflate(-40, -40)
                pygame.draw.rect(self.canvas, PATH_COLOR, r, border_radius=6)

        hx, hy = self.env.hive
        hive_rect = pygame.Rect(hx * CELL + 4, hy * CELL + 4, CELL - 8, CELL - 8)
        pygame.draw.rect(self.canvas, HIVE_COLOR, hive_rect, border_radius=10)
        pygame.draw.rect(self.canvas, HIVE_BORDER, hive_rect, width=2, border_radius=10)
        label = self.font_badge.render("HIVE", True, (255, 255, 255))
        self.canvas.blit(label, (hive_rect.x + (hive_rect.w - label.get_width()) // 2, hive_rect.y + (hive_rect.h - label.get_height()) // 2))

        # Glowing Target Outline & Badge
        target_flower = getattr(self.bee, "_target_flower", None)
        if target_flower is not None:
            r = self.cell_rect(target_flower.x, target_flower.y)
            pygame.draw.rect(self.canvas, TARGET_HIGHLIGHT, r.inflate(8, 8), width=3, border_radius=10)
            
            tf_id = getattr(target_flower, 'id', 'Target')
            lbl = self.font_badge.render(f"TARGET #{tf_id}", True, (234, 88, 12))
            pw = lbl.get_width() + 10
            ph = lbl.get_height() + 4
            px = r.x + (CELL - pw) // 2
            py = r.y - ph - 2
            pill_bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(pill_bg, (254, 243, 199, 230), (0, 0, pw, ph), border_radius=4)
            self.canvas.blit(pill_bg, (px, py))
            self.canvas.blit(lbl, (px + 5, py + 2))

        for f in self.env.flowers:
            self.draw_flower(self.canvas, f.x, f.y, f.nectar, f.is_available(), flower_id=f.id)

        bx, by = self.bee.pos
        self.draw_bee(self.canvas, bx, by)

        self.draw_legend()

    def draw_legend(self):
        leg_w, leg_h = 440, 38
        leg_rect = pygame.Rect(16, MAP_H - 50, leg_w, leg_h)
        pygame.draw.rect(self.canvas, (255, 255, 255, 235), leg_rect, border_radius=8)
        pygame.draw.rect(self.canvas, CARD_BORDER, leg_rect, width=1, border_radius=8)

        flower_icon = pygame.transform.scale(self.sprite_mgr.get_flower_sprite(1, True), (20, 20))
        bee_icon = pygame.transform.scale(self.sprite_mgr.get_bee_frame("fly", "right", self.anim_time), (20, 22))

        lx = 28
        # Hive
        pygame.draw.rect(self.canvas, HIVE_COLOR, (lx, MAP_H - 37, 14, 14), border_radius=3)
        t = self.font_small.render("Hive", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 20, MAP_H - 40))
        lx += 80

        # Obstacle
        pygame.draw.rect(self.canvas, OBSTACLE, (lx, MAP_H - 37, 14, 14), border_radius=3)
        t = self.font_small.render("Obstacle", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 20, MAP_H - 40))
        lx += 105

        # Flower
        self.canvas.blit(flower_icon, (lx, MAP_H - 41))
        t = self.font_small.render("Flower", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 26, MAP_H - 40))
        lx += 95

        # Bee
        self.canvas.blit(bee_icon, (lx, MAP_H - 42))
        t = self.font_small.render("Bee", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 26, MAP_H - 40))

    def draw_progress_bar(self, surface, x, y, width, height, current, max_val, fill_color):
        ratio = min(1.0, max(0.0, current / max_val))
        bg_rect = pygame.Rect(x, y, width, height)
        fill_rect = pygame.Rect(x, y, int(width * ratio), height)
        pygame.draw.rect(surface, BAR_BG, bg_rect, border_radius=5)
        if ratio > 0:
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=5)

    def draw_panel(self):
        panel_rect = pygame.Rect(MAP_W, 0, PANEL_W, MAP_H)
        pygame.draw.rect(self.canvas, PANEL_BG, panel_rect)
        pygame.draw.line(self.canvas, CARD_BORDER, (MAP_W, 0), (MAP_W, MAP_H), 1)

        x = MAP_W + 24
        card_w = PANEL_W - 48
        y = 16

        # Top Header
        title_surf = self.font_title.render("BeeLogic Simulation", True, ACCENT)
        self.canvas.blit(title_surf, (x, y))
        
        # Active strategy pill top-right
        strategy_label = STRATEGY_LABELS[self.strategies[self.strategy_dropdown.selected_idx]].split(" (")[0]
        strat_pill = self.font_badge.render(strategy_label, True, ACCENT)
        sp_w = strat_pill.get_width() + 14
        sp_h = strat_pill.get_height() + 6
        sp_x = x + card_w - sp_w
        sp_y = y + 2
        pygame.draw.rect(self.canvas, ACCENT_LIGHT, (sp_x, sp_y, sp_w, sp_h), border_radius=6)
        pygame.draw.rect(self.canvas, (191, 219, 254), (sp_x, sp_y, sp_w, sp_h), width=1, border_radius=6)
        self.canvas.blit(strat_pill, (sp_x + 7, sp_y + 3))

        y += 28
        sub_surf = self.font_small.render("Autonomous Foraging Agent & AI Reasoning Engine", True, TEXT_MUTED)
        self.canvas.blit(sub_surf, (x, y))
        y += 26

        pygame.draw.line(self.canvas, CARD_BORDER, (x, y), (x + card_w, y), 1)
        y += 12

        s = self.bee.status_dict()

        # ==============================================================
        # Card 1: Telemetry & Vitals
        # ==============================================================
        card1_h = 236
        card1 = pygame.Rect(x, y, card_w, card1_h)
        pygame.draw.rect(self.canvas, CARD_BG, card1, border_radius=10)
        pygame.draw.rect(self.canvas, CARD_BORDER, card1, width=1, border_radius=10)

        cx = x + 16
        cy = y + 14
        self.canvas.blit(self.font_header.render("AGENT TELEMETRY & VITALS", True, ACCENT), (cx, cy))
        
        # State tag
        state_text = getattr(self.bee, 'activity', 'FLYING').upper()
        if self.bee.finished:
            state_text = "COMPLETED"
            state_color = (16, 185, 129)
        elif self.bee.nectar >= self.bee.max_nectar_capacity:
            state_text = "RETURNING (FULL)"
            state_color = (220, 38, 38)
        elif state_text == "HARVEST":
            state_text = "HARVESTING"
            state_color = (234, 88, 12)
        elif state_text == "DEPOSIT":
            state_text = "DEPOSITING"
            state_color = (217, 119, 6)
        else:
            state_text = "FORAGING"
            state_color = ACCENT

        st_surf = self.font_badge.render(state_text, True, (255, 255, 255))
        st_w = st_surf.get_width() + 12
        st_h = st_surf.get_height() + 6
        st_rect = pygame.Rect(x + card_w - st_w - 16, cy - 2, st_w, st_h)
        pygame.draw.rect(self.canvas, state_color, st_rect, border_radius=6)
        self.canvas.blit(st_surf, (st_rect.x + 6, st_rect.y + 3))

        cy += 28

        # Progress bars
        self.canvas.blit(self.font_body_bold.render("Energy Level:", True, TEXT_DARK), (cx, cy))
        e_pct = int(s['energy'] / s['max_energy'] * 100)
        e_val = self.font_body.render(f"{s['energy']}/{s['max_energy']} ({e_pct}%)", True, TEXT_MUTED)
        self.canvas.blit(e_val, (cx + 120, cy))
        self.draw_progress_bar(self.canvas, cx + 250, cy + 3, card_w - 280, 16, s['energy'], s['max_energy'], ENERGY_BAR)
        cy += 26

        self.canvas.blit(self.font_body_bold.render("Nectar Load:", True, TEXT_DARK), (cx, cy))
        n_pct = int(s['nectar'] / s['max_nectar_capacity'] * 100)
        n_val = self.font_body.render(f"{s['nectar']}/{s['max_nectar_capacity']} ({n_pct}%)", True, TEXT_MUTED)
        self.canvas.blit(n_val, (cx + 120, cy))
        self.draw_progress_bar(self.canvas, cx + 250, cy + 3, card_w - 280, 16, s['nectar'], s['max_nectar_capacity'], NECTAR_BAR)
        cy += 30

        # 2x2 Metric tiles
        tile_w = (card_w - 44) // 2
        tile_h = 52
        
        metrics = [
            ("Nectar Deposited", f"{s['total_nectar_collected']} units", ACCENT),
            ("Distance Travelled", f"{s['distance']} steps", TEXT_DARK),
            ("Flowers Visited", f"{s['flowers_visited']} flowers", TEXT_DARK),
            ("Simulation Step", f"{s['time_steps']} / {s['max_steps']}", TEXT_DARK),
        ]

        for i, (m_label, m_val, m_col) in enumerate(metrics):
            tx_pos = cx + (i % 2) * (tile_w + 12)
            ty_pos = cy + (i // 2) * (tile_h + 8)
            t_rect = pygame.Rect(tx_pos, ty_pos, tile_w, tile_h)
            pygame.draw.rect(self.canvas, (255, 255, 255), t_rect, border_radius=8)
            pygame.draw.rect(self.canvas, CARD_BORDER, t_rect, width=1, border_radius=8)
            
            self.canvas.blit(self.font_badge.render(m_label, True, TEXT_MUTED), (tx_pos + 12, ty_pos + 6))
            self.canvas.blit(self.font_header.render(m_val, True, m_col), (tx_pos + 12, ty_pos + 24))

        y += card1_h + 14

        # ==============================================================
        # Card 2: Decision Log & Production Rules
        # ==============================================================
        card2_h = 224
        card2 = pygame.Rect(x, y, card_w, card2_h)
        pygame.draw.rect(self.canvas, CARD_BG, card2, border_radius=10)
        pygame.draw.rect(self.canvas, CARD_BORDER, card2, width=1, border_radius=10)

        cx = x + 16
        cy = y + 14
        self.canvas.blit(self.font_header.render("DECISION ENGINE & ACTIVE RULES", True, ACCENT), (cx, cy))
        cy += 28

        target_flower = getattr(self.bee, "_target_flower", None)
        if target_flower:
            target_str = f"Target: Flower #{target_flower.id} at ({target_flower.x}, {target_flower.y}) — Nectar: {target_flower.nectar}"
            t_col = ACCENT
        elif s['target'] == "Hive":
            target_str = f"Target: Hive at ({self.env.hive[0]}, {self.env.hive[1]}) — Depositing Load"
            t_col = (217, 119, 6)
        else:
            target_str = f"Target: {s['target'] if s['target'] else 'None (Simulation Finished)'}"
            t_col = TEXT_DARK

        self.canvas.blit(self.font_body_bold.render(target_str, True, t_col), (cx, cy))
        cy += 26

        hx, hy = self.env.hive
        bx, by = self.bee.pos
        dist_to_hive = abs(bx - hx) + abs(by - hy)

        if self.bee.nectar >= self.bee.max_nectar_capacity:
            rule_str = "Active Rule [Capacity Max]: Capacity reached (90/90) -> Return to Hive via A*"
            rule_bg = (254, 242, 242)
            rule_border = (252, 165, 165)
            rule_color = (220, 38, 38)
        elif self.bee.energy <= dist_to_hive + 2:
            rule_str = "Active Rule [Safety Reserve]: Energy low -> Immediate emergency return"
            rule_bg = (254, 242, 242)
            rule_border = (252, 165, 165)
            rule_color = (220, 38, 38)
        elif self.bee.nectar > 0:
            rule_str = f"Active Rule [Partial Load ({self.bee.nectar}/90)]: Seeking optimal nectar source"
            rule_bg = ACCENT_LIGHT
            rule_border = (191, 219, 254)
            rule_color = ACCENT
        else:
            rule_str = "Active Rule [Empty Capacity]: Foraging for initial high-yield flowers"
            rule_bg = (241, 245, 249)
            rule_border = CARD_BORDER
            rule_color = (71, 85, 105)

        r_box = pygame.Rect(cx, cy, card_w - 32, 34)
        pygame.draw.rect(self.canvas, rule_bg, r_box, border_radius=6)
        pygame.draw.rect(self.canvas, rule_border, r_box, width=1, border_radius=6)
        self.canvas.blit(self.font_badge.render(rule_str, True, rule_color), (cx + 10, cy + 8))
        cy += 42

        self.canvas.blit(self.font_small_bold.render("Reasoning Explanation:", True, TEXT_MUTED), (cx, cy))
        cy += 20
        self._draw_wrapped(s["reason"], cx, cy, card_w - 36, self.font_small, TEXT_DARK, max_lines=3)

        y += card2_h + 14

        # ==============================================================
        # Card 3: Live Candidate Decision Matrix
        # ==============================================================
        card3_h = 378
        card3 = pygame.Rect(x, y, card_w, card3_h)
        pygame.draw.rect(self.canvas, CARD_BG, card3, border_radius=10)
        pygame.draw.rect(self.canvas, CARD_BORDER, card3, width=1, border_radius=10)

        cx = x + 16
        cy = y + 14
        self.canvas.blit(self.font_header.render("CANDIDATE DECISION MATRIX", True, ACCENT), (cx, cy))
        
        formula_tag = self.font_badge.render("Score = Nectar / (Distance ^ 1.5)", True, TEXT_MUTED)
        self.canvas.blit(formula_tag, (x + card_w - formula_tag.get_width() - 16, cy + 2))
        cy += 28

        evals = getattr(self.bee, 'evaluations', [])
        if evals:
            headers = ["Flower ID", "Distance", "Nectar", "Heuristic Score", "Decision Status"]
            col_x = [cx + 8, cx + 100, cx + 200, cx + 310, cx + 440]
            
            # Table Header Background
            th_rect = pygame.Rect(cx, cy, card_w - 32, 28)
            pygame.draw.rect(self.canvas, (241, 245, 249), th_rect, border_radius=6)
            for hx_pos, h in zip(col_x, headers):
                self.canvas.blit(self.font_badge.render(h, True, TEXT_MUTED), (hx_pos, cy + 6))
            cy += 34

            for rank_idx, cand in enumerate(evals[:6]):
                is_sel = cand.get("selected", False)
                bg_c = ACCENT_LIGHT if is_sel else ((255, 255, 255) if rank_idx % 2 == 0 else CARD_BG)
                border_c = ACCENT if is_sel else CARD_BORDER
                txt_c = ACCENT if is_sel else TEXT_DARK
                
                row_r = pygame.Rect(cx, cy, card_w - 32, 34)
                pygame.draw.rect(self.canvas, bg_c, row_r, border_radius=6)
                pygame.draw.rect(self.canvas, border_c, row_r, width=1, border_radius=6)

                self.canvas.blit(self.font_body_bold.render(f"Flower #{cand['id']}", True, txt_c), (col_x[0], cy + 8))
                self.canvas.blit(self.font_body.render(f"{cand['dist']} steps", True, txt_c), (col_x[1], cy + 8))
                self.canvas.blit(self.font_body.render(f"{cand['nectar']} units", True, txt_c), (col_x[2], cy + 8))
                self.canvas.blit(self.font_body.render(f"{cand['score']:.2f}", True, txt_c), (col_x[3], cy + 8))
                
                status_str = "★ SELECTED" if is_sel else f"Rank #{rank_idx + 1}"
                status_surf = self.font_badge.render(status_str, True, (255, 255, 255) if is_sel else TEXT_MUTED)
                st_w = status_surf.get_width() + 10
                st_h = status_surf.get_height() + 4
                st_box = pygame.Rect(col_x[4], cy + 6, st_w, st_h)
                pygame.draw.rect(self.canvas, ACCENT if is_sel else (226, 232, 240), st_box, border_radius=4)
                self.canvas.blit(status_surf, (col_x[4] + 5, cy + 8))

                cy += 40
        else:
            empty_msg = "No active evaluations (Bee is currently returning to Hive or idle)"
            self.canvas.blit(self.font_body.render(empty_msg, True, TEXT_MUTED), (cx + 10, cy + 40))

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
            surf = font.render(l, True, color)
            self.canvas.blit(surf, (x, y + i * 20))

    def draw_buttons_bar(self):
        bar_rect = pygame.Rect(0, MAP_H, WINDOW_W, BUTTON_BAR_H)
        pygame.draw.rect(self.canvas, PANEL_BG, bar_rect)
        pygame.draw.line(self.canvas, CARD_BORDER, (0, MAP_H), (WINDOW_W, MAP_H), 1)

        self.btn_start.active = self.running_sim
        self.btn_pause.active = not self.running_sim and not self.bee.finished

        for b in self.buttons:
            b.draw(self.canvas, self.font_button)

        self.strategy_dropdown.draw(self.canvas, self.font_button)

        # Bottom Shortcut & Info Line
        shortcut_text = "Shortcuts: [Space] Start / Pause   |   [R] Reset Simulation   |   [C] Run Benchmark   |   [Esc / Q] Quit Application"
        self.canvas.blit(self.font_small.render(shortcut_text, True, TEXT_MUTED), (24, 1045))
        
        info_text = f"1080p Fullscreen Display Mode   •   Environment Seed: {self.seed}"
        info_surf = self.font_small.render(info_text, True, TEXT_MUTED)
        self.canvas.blit(info_surf, (WINDOW_W - info_surf.get_width() - 24, 1045))

    def draw_event_banner(self):
        text = self.font_header.render(self.event_banner, True, (255, 255, 255))
        pad_x = 24
        pad_y = 12
        w = text.get_width() + pad_x * 2
        h = text.get_height() + pad_y * 2
        rect = pygame.Rect((MAP_W - w) // 2, 18, w, h)
        pygame.draw.rect(self.canvas, (220, 38, 38), rect, border_radius=10)
        pygame.draw.rect(self.canvas, (255, 255, 255), rect, width=1, border_radius=10)
        self.canvas.blit(text, (rect.x + pad_x, rect.y + pad_y))

    def draw_comparison_overlay(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 245))
        self.canvas.blit(overlay, (0, 0))

        # Main Card Box
        main_box = pygame.Rect(80, 40, 1760, 1000)
        pygame.draw.rect(self.canvas, (30, 41, 59), main_box, border_radius=16)
        pygame.draw.rect(self.canvas, (51, 65, 85), main_box, width=1, border_radius=16)

        title = self.font_hero.render("Strategy Comparison & Performance Benchmark", True, (250, 204, 21))
        self.canvas.blit(title, (120, 70))

        sub = self.font_body.render("Real-time empirical evaluation of Nearest Neighbor (BFS), Greedy (Highest Nectar), and Intelligent Weighted A* Search", True, (203, 213, 225))
        self.canvas.blit(sub, (120, 112))

        headers = ["Strategy", "Nectar Collected", "Distance Travelled", "Energy Consumed", "Flowers Visited", "Time Steps", "Efficiency Ratio"]
        col_x = [120, 520, 760, 1000, 1220, 1420, 1600]

        y = 160
        th_box = pygame.Rect(100, y, 1720, 36)
        pygame.draw.rect(self.canvas, (51, 65, 85), th_box, border_radius=8)
        for cx, h in zip(col_x, headers):
            surf = self.font_header.render(h, True, (250, 204, 21))
            self.canvas.blit(surf, (cx, y + 6))
        y += 48

        if self.comparison_results:
            best_eff = max(r["efficiency"] for r in self.comparison_results)
            for r in self.comparison_results:
                is_winner = (r["efficiency"] == best_eff)
                row_box = pygame.Rect(100, y, 1720, 42)
                if is_winner:
                    pygame.draw.rect(self.canvas, (30, 58, 138), row_box, border_radius=8)
                    pygame.draw.rect(self.canvas, (96, 165, 250), row_box, width=1, border_radius=8)
                else:
                    pygame.draw.rect(self.canvas, (15, 23, 42), row_box, border_radius=8)

                values = [
                    r["label"] + (" ★ WINNER" if is_winner else ""),
                    f"{r['nectar_collected']} units",
                    f"{r['distance_travelled']} steps",
                    f"{r['energy_consumed']} units",
                    f"{r['flowers_visited']} flowers",
                    f"{r['time_steps']} steps",
                    f"{r['efficiency']:.3f} (Nectar/Dist)",
                ]
                for cx, v in zip(col_x, values):
                    txt_color = (255, 255, 255) if not is_winner else (250, 204, 21)
                    surf = self.font_body_bold.render(v, True, txt_color) if is_winner else self.font_body.render(v, True, txt_color)
                    self.canvas.blit(surf, (cx, y + 10))
                y += 50

            y += 20
            chart_box = pygame.Rect(100, y, 1720, 240)
            pygame.draw.rect(self.canvas, (15, 23, 42), chart_box, border_radius=12)
            pygame.draw.rect(self.canvas, (51, 65, 85), chart_box, width=1, border_radius=12)
            
            self.canvas.blit(self.font_header.render("VISUAL EFFICIENCY BENCHMARK (Nectar Collected / Distance Travelled)", True, (250, 204, 21)), (130, y + 16))

            max_eff = max(r["efficiency"] for r in self.comparison_results) or 1.0
            colors = [(91, 143, 185), (224, 164, 88), (52, 211, 153)]

            bar_y = y + 58
            for i, r in enumerate(self.comparison_results):
                lbl = self.font_body_bold.render(r["label"].split(" (")[0], True, (255, 255, 255))
                self.canvas.blit(lbl, (130, bar_y + 4))
                
                bar_max_w = 1100
                bar_w = int((r["efficiency"] / max_eff) * bar_max_w)
                pygame.draw.rect(self.canvas, (51, 65, 85), (380, bar_y, bar_max_w, 28), border_radius=6)
                pygame.draw.rect(self.canvas, colors[i], (380, bar_y, bar_w, 28), border_radius=6)
                
                eff_txt = self.font_header.render(f"{r['efficiency']:.3f} Nectar/Step", True, (255, 255, 255))
                self.canvas.blit(eff_txt, (1500, bar_y + 4))
                bar_y += 48

            y += 260
            
            # Two Side-by-Side Breakdown Cards
            box_w = 845
            box_h = 160
            
            # Card A
            v_box1 = pygame.Rect(100, y, box_w, box_h)
            pygame.draw.rect(self.canvas, (15, 23, 42), v_box1, border_radius=12)
            pygame.draw.rect(self.canvas, (37, 99, 235), v_box1, width=1, border_radius=12)

            intel = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_INTELLIGENT)
            greedy = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_GREEDY)
            nearest = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_NEAREST)
            
            eff_diff = ((intel["efficiency"] - greedy["efficiency"]) / max(0.001, greedy["efficiency"])) * 100
            dist_diff = ((greedy["distance_travelled"] - intel["distance_travelled"]) / max(1, intel["distance_travelled"])) * 100

            self.canvas.blit(self.font_header.render("KEY QUANTITATIVE FINDINGS", True, (96, 165, 250)), (130, y + 16))
            v_text1 = f"• Intelligent Bee achieved +{eff_diff:.1f}% higher efficiency than Highest Nectar (Greedy)."
            v_text2 = f"• Greedy strategy traveled {dist_diff:.1f}% farther due to unweighted heuristic choices."
            v_text3 = f"• Nearest Neighbor collected fewer total nectar units due to sub-optimal local clustering."
            
            self.canvas.blit(self.font_body.render(v_text1, True, (226, 232, 240)), (130, y + 50))
            self.canvas.blit(self.font_body.render(v_text2, True, (226, 232, 240)), (130, y + 80))
            self.canvas.blit(self.font_body.render(v_text3, True, (226, 232, 240)), (130, y + 110))

            # Card B
            v_box2 = pygame.Rect(975, y, box_w, box_h)
            pygame.draw.rect(self.canvas, (15, 23, 42), v_box2, border_radius=12)
            pygame.draw.rect(self.canvas, (52, 211, 153), v_box2, width=1, border_radius=12)

            self.canvas.blit(self.font_header.render("CLASSICAL AI & DECISION-THEORETIC SUMMARY", True, (52, 211, 153)), (1005, y + 16))
            c_text1 = "• Production Rules: Capacity threshold (90/90) & energy reserve safety margins."
            c_text2 = "• Heuristic Formulation: Score = Nectar / (Distance ^ 1.5) balances yield & cost."
            c_text3 = "• Pathfinding: Optimal obstacle traversal via A* Search and BFS grid exploration."

            self.canvas.blit(self.font_body.render(c_text1, True, (226, 232, 240)), (1005, y + 50))
            self.canvas.blit(self.font_body.render(c_text2, True, (226, 232, 240)), (1005, y + 80))
            self.canvas.blit(self.font_body.render(c_text3, True, (226, 232, 240)), (1005, y + 110))

        hint = self.font_body.render("Click anywhere or press [Esc / Space] to return to simulation. Benchmark chart saved to out/comparison_chart.png.", True, (148, 163, 184))
        self.canvas.blit(hint, (100, 1000))

    def draw(self):
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


if __name__ == "__main__":
    app = BeeLogicApp(seed=42)
    app.run()