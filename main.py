import sys
import math
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

# Layout constants
CELL = 36
MAP_W = GRID_COLS * CELL
MAP_H = GRID_ROWS * CELL
PANEL_W = 350
BUTTON_BAR_H = 60

WINDOW_W = MAP_W + PANEL_W
WINDOW_H = MAP_H + BUTTON_BAR_H

DEFAULT_SPEED = 3.0

# Academic Palette
BG = (245, 247, 250)
GRID_LINE = (226, 232, 240)
OBSTACLE = (100, 116, 139)
OBSTACLE_BORDER = (71, 85, 105)

HIVE_COLOR = (245, 158, 11)
HIVE_BORDER = (180, 83, 9)

PETAL_ACTIVE = (244, 114, 182)
CENTER_ACTIVE = (234, 88, 12)
PETAL_DEPLETED = (203, 213, 225)
CENTER_DEPLETED = (148, 163, 184)

PATH_COLOR = (147, 197, 253)
PATH_LINE_COLOR = (37, 99, 235)
TARGET_HIGHLIGHT = (250, 204, 21)

PANEL_BG = (255, 255, 255)
CARD_BG = (248, 250, 252)
CARD_BORDER = (226, 232, 240)
TEXT_DARK = (15, 23, 42)
TEXT_MUTED = (100, 116, 139)
ACCENT = (37, 99, 235)

BUTTON_BG = (255, 255, 255)
BUTTON_BORDER = (203, 213, 225)
BUTTON_HOVER = (241, 245, 249)
BUTTON_ACTIVE = (37, 99, 235)

BAR_BG = (226, 232, 240)
ENERGY_BAR = (34, 197, 94)
NECTAR_BAR = (249, 115, 22)


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.active = False
        self.hovered = False

    def draw(self, surface, font):
        bg = BUTTON_ACTIVE if self.active else (BUTTON_HOVER if self.hovered else BUTTON_BG)
        text_color = (255, 255, 255) if self.active else TEXT_DARK
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, self.rect, width=1, border_radius=8)
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

    def draw(self, surface, font):
        pygame.draw.rect(surface, BUTTON_BG, self.rect, border_radius=8)
        pygame.draw.rect(surface, ACCENT if self.is_open else BUTTON_BORDER, self.rect, width=1, border_radius=8)
        
        label = self.options[self.selected_idx][1]
        text = font.render(label, True, TEXT_DARK)
        surface.blit(text, (self.rect.x + 10, self.rect.y + (self.rect.h - text.get_height()) // 2))

        arrow_color = ACCENT if self.is_open else TEXT_MUTED
        ax = self.rect.right - 14
        ay = self.rect.centery
        if self.is_open:
            pygame.draw.polygon(surface, arrow_color, [(ax - 4, ay + 2), (ax + 4, ay + 2), (ax, ay - 3)])
        else:
            pygame.draw.polygon(surface, arrow_color, [(ax - 4, ay - 2), (ax + 4, ay - 2), (ax, ay + 3)])

        if self.is_open:
            menu_h = len(self.options) * self.rect.h
            menu_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 4, self.rect.w, menu_h)
            pygame.draw.rect(surface, BUTTON_BG, menu_rect, border_radius=8)
            pygame.draw.rect(surface, BUTTON_BORDER, menu_rect, width=1, border_radius=8)

            for i, (_, opt_label) in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 4 + (i * self.rect.h), self.rect.w, self.rect.h)
                if i == self.hovered_option:
                    pygame.draw.rect(surface, BUTTON_HOVER, opt_rect, border_radius=6)
                if i == self.selected_idx:
                    pygame.draw.rect(surface, CARD_BG, opt_rect, border_radius=6)
                
                t = font.render(opt_label, True, ACCENT if i == self.selected_idx else TEXT_DARK)
                surface.blit(t, (opt_rect.x + 10, opt_rect.y + (opt_rect.h - t.get_height()) // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.is_open:
            menu_h = len(self.options) * self.rect.h
            for i in range(len(self.options)):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 4 + (i * self.rect.h), self.rect.w, self.rect.h)
                if opt_rect.collidepoint(event.pos):
                    self.hovered_option = i
                    return
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            if self.is_open:
                menu_h = len(self.options) * self.rect.h
                for i in range(len(self.options)):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.y - menu_h - 4 + (i * self.rect.h), self.rect.w, self.rect.h)
                    if opt_rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        return i
                self.is_open = False
        return None


class BeeLogicApp:
    def __init__(self, seed=42):
        pygame.init()
        pygame.display.set_caption("BeeLogic - Intelligent Bee Foraging Agent")
        
        self.base_w = WINDOW_W
        self.base_h = WINDOW_H
        self.canvas = pygame.Surface((self.base_w, self.base_h))
        
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode((self.base_w, self.base_h), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Segoe UI", 13)
        self.font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 11)
        self.font_badge = pygame.font.SysFont("Segoe UI", 10, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 19, bold=True)

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
        y = MAP_H + 12
        h = BUTTON_BAR_H - 24
        
        self.btn_start = Button((10, y, 65, h), "Start")
        self.btn_pause = Button((80, y, 65, h), "Pause")
        self.btn_reset = Button((150, y, 65, h), "Reset")
        
        dropdown_options = [(s, STRATEGY_LABELS[s].split(" (")[0]) for s in self.strategies]
        self.strategy_dropdown = Dropdown((220, y, 160, h), dropdown_options, selected_idx=2)
        
        self.btn_speed = Button((385, y, 90, h), f"Speed: {self.sim_speed:.1f}x")
        self.btn_trigger = Button((480, y, 110, h), "Deplete Flower")
        self.btn_compare = Button((595, y, 115, h), "Run Compare")
        
        self.buttons = [self.btn_start, self.btn_pause, self.btn_reset, self.btn_speed, self.btn_trigger, self.btn_compare]

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.base_w, self.base_h), pygame.RESIZABLE)

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
        speeds = [1.0, 3.0, 6.0, 10.0]
        curr_idx = speeds.index(self.sim_speed) if self.sim_speed in speeds else 1
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
                if event.key in (pygame.K_F11, pygame.K_f):
                    self.toggle_fullscreen()
                elif event.key == pygame.K_SPACE:
                    self.running_sim = not self.running_sim
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_c:
                    self.run_comparison()

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

    def run_comparison(self):
        self.comparison_results = comparison.run_comparison(seed=self.seed, max_steps=400, event_step=45)
        try:
            comparison.save_chart(self.comparison_results, path="out/comparison_chart.png")
        except Exception:
            pass
        self.show_comparison = True
        self.running_sim = False

    def update(self, dt):
        # Advance animation clock continuously so idle / wing flapping is active
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
                surface.blit(id_tag, (center_x - id_tag.get_width() // 2, y * CELL - 1))

            # Nectar count pill badge at bottom
            num_surf = self.font_badge.render(str(nectar), True, (255, 255, 255))
            pw = num_surf.get_width() + 6
            ph = num_surf.get_height() + 2
            px = center_x - pw // 2
            py = y * CELL + CELL - ph - 1
            pill_bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(pill_bg, (15, 23, 42, 210), (0, 0, pw, ph), border_radius=4)
            surface.blit(pill_bg, (px, py))
            surface.blit(num_surf, (px + 3, py + 1))
        else:
            # Depleted flower ID and indicator
            if flower_id is not None:
                id_tag = self.font_badge.render(f"#{flower_id}", True, (148, 163, 184))
                surface.blit(id_tag, (center_x - id_tag.get_width() // 2, y * CELL - 1))
            d_tag = self.font_badge.render("0", True, (148, 163, 184))
            surface.blit(d_tag, (center_x - d_tag.get_width() // 2, y * CELL + CELL - 12))

    def draw_bee(self, surface, x, y):
        # Determine action and direction
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
        shadow_surf = pygame.Surface((22, 9), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (15, 23, 42, 65), (0, 0, 22, 9))
        surface.blit(shadow_surf, (int(cx - 11), int(cy + 10)))

        # Blit animated bee frame
        bw = frame.get_width()
        bh = frame.get_height()
        surface.blit(frame, (int(cx - bw // 2), int(cy - bh // 2 - 2)))

        # On-Bee Capacity Badge
        current_load = self.bee.nectar
        max_cap = self.bee.max_nectar_capacity

        if current_load >= max_cap:
            badge_str = f"[{current_load}/{max_cap} FULL -> RETURNING]"
            badge_bg = (220, 38, 38)
        elif current_load > 0:
            badge_str = f"[{current_load}/{max_cap} SEARCHING]"
            badge_bg = (37, 99, 235)
        else:
            badge_str = f"[{current_load}/{max_cap} EMPTY]"
            badge_bg = (100, 116, 139)

        text_surf = self.font_badge.render(badge_str, True, (255, 255, 255))
        bx = int(cx + 16)
        by = int(cy - 20)
        bw_badge = text_surf.get_width() + 8
        bh_badge = text_surf.get_height() + 4

        if bx + bw_badge > MAP_W:
            bx = int(cx - bw_badge - 16)
        if by < 5:
            by = int(cy + 14)

        badge_rect = pygame.Rect(bx, by, bw_badge, bh_badge)
        pygame.draw.rect(surface, badge_bg, badge_rect, border_radius=4)
        surface.blit(text_surf, (bx + 4, by + 2))

    def draw_grid(self):
        for gx in range(GRID_COLS + 1):
            pygame.draw.line(self.canvas, GRID_LINE, (gx * CELL, 0), (gx * CELL, MAP_H))
        for gy in range(GRID_ROWS + 1):
            pygame.draw.line(self.canvas, GRID_LINE, (0, gy * CELL), (MAP_W, gy * CELL))

        for (ox, oy) in self.env.obstacles:
            r = self.cell_rect(ox, oy)
            pygame.draw.rect(self.canvas, OBSTACLE, r, border_radius=4)
            pygame.draw.rect(self.canvas, OBSTACLE_BORDER, r, width=1, border_radius=4)

        if self.bee.current_path and len(self.bee.current_path) > 1:
            points = [(px * CELL + CELL // 2, py * CELL + CELL // 2) for (px, py) in self.bee.current_path]
            pygame.draw.lines(self.canvas, PATH_LINE_COLOR, False, points, 3)
            for (px, py) in self.bee.current_path:
                r = self.cell_rect(px, py)
                pygame.draw.rect(self.canvas, PATH_COLOR, r.inflate(-20, -20), border_radius=4)

        hx, hy = self.env.hive
        hive_rect = self.cell_rect(hx, hy)
        pygame.draw.rect(self.canvas, HIVE_COLOR, hive_rect, border_radius=6)
        pygame.draw.rect(self.canvas, HIVE_BORDER, hive_rect, width=2, border_radius=6)
        label = self.font_small.render("HIVE", True, (255, 255, 255))
        self.canvas.blit(label, (hive_rect.x + (CELL - label.get_width()) // 2, hive_rect.y + 10))

        # Dynamic Glowing Target Outline & Floating Target Badge
        target_flower = getattr(self.bee, "_target_flower", None)
        if target_flower is not None:
            r = self.cell_rect(target_flower.x, target_flower.y)
            pygame.draw.rect(self.canvas, TARGET_HIGHLIGHT, r.inflate(6, 6), width=3, border_radius=6)
            
            tf_id = getattr(target_flower, 'id', 'Target')
            lbl = self.font_badge.render(f"TARGET #{tf_id}", True, (234, 88, 12))
            self.canvas.blit(lbl, (r.x + (CELL - lbl.get_width()) // 2, r.y - 14))

        for f in self.env.flowers:
            self.draw_flower(self.canvas, f.x, f.y, f.nectar, f.is_available(), flower_id=f.id)

        bx, by = self.bee.pos
        self.draw_bee(self.canvas, bx, by)

        self.draw_legend()

    def draw_legend(self):
        leg_w, leg_h = 280, 26
        leg_rect = pygame.Rect(10, MAP_H - 36, leg_w, leg_h)
        pygame.draw.rect(self.canvas, (255, 255, 255, 230), leg_rect, border_radius=6)
        pygame.draw.rect(self.canvas, CARD_BORDER, leg_rect, width=1, border_radius=6)

        flower_icon = pygame.transform.scale(self.sprite_mgr.get_flower_sprite(1, True), (14, 14))
        bee_icon = pygame.transform.scale(self.sprite_mgr.get_bee_frame("fly", "right", self.anim_time), (14, 16))

        lx = 18
        # Hive
        pygame.draw.rect(self.canvas, HIVE_COLOR, (lx, MAP_H - 28, 10, 10), border_radius=2)
        t = self.font_small.render("Hive", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 14, MAP_H - 30))
        lx += 52

        # Obstacle
        pygame.draw.rect(self.canvas, OBSTACLE, (lx, MAP_H - 28, 10, 10), border_radius=2)
        t = self.font_small.render("Obstacle", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 14, MAP_H - 30))
        lx += 68

        # Flower
        self.canvas.blit(flower_icon, (lx, MAP_H - 30))
        t = self.font_small.render("Flower", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 18, MAP_H - 30))
        lx += 60

        # Bee
        self.canvas.blit(bee_icon, (lx, MAP_H - 31))
        t = self.font_small.render("Bee", True, TEXT_DARK)
        self.canvas.blit(t, (lx + 18, MAP_H - 30))

    def draw_progress_bar(self, surface, x, y, width, height, current, max_val, fill_color):
        ratio = min(1.0, max(0.0, current / max_val))
        bg_rect = pygame.Rect(x, y, width, height)
        fill_rect = pygame.Rect(x, y, int(width * ratio), height)
        pygame.draw.rect(surface, BAR_BG, bg_rect, border_radius=4)
        if ratio > 0:
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=4)

    def draw_panel(self):
        panel_rect = pygame.Rect(MAP_W, 0, PANEL_W, MAP_H)
        pygame.draw.rect(self.canvas, PANEL_BG, panel_rect)
        pygame.draw.line(self.canvas, CARD_BORDER, (MAP_W, 0), (MAP_W, MAP_H), 1)

        x = MAP_W + 16
        y = 14

        title_surf = self.font_title.render("BeeLogic Simulation", True, ACCENT)
        self.canvas.blit(title_surf, (x, y))
        y += 24
        sub_surf = self.font_small.render("Autonomous Foraging Agent", True, TEXT_MUTED)
        self.canvas.blit(sub_surf, (x, y))
        y += 22

        s = self.bee.status_dict()

        # Card 1: Telemetry
        card1 = pygame.Rect(x, y, PANEL_W - 32, 150)
        pygame.draw.rect(self.canvas, CARD_BG, card1, border_radius=8)
        pygame.draw.rect(self.canvas, CARD_BORDER, card1, width=1, border_radius=8)

        cx = x + 12
        cy = y + 8
        self.canvas.blit(self.font_bold.render("AGENT STATUS", True, ACCENT), (cx, cy))
        cy += 20

        self.canvas.blit(self.font_small.render(f"Energy: {s['energy']}/{s['max_energy']}", True, TEXT_DARK), (cx, cy))
        self.draw_progress_bar(self.canvas, cx + 120, cy + 2, 160, 11, s['energy'], s['max_energy'], ENERGY_BAR)
        cy += 18

        self.canvas.blit(self.font_small.render(f"Nectar: {s['nectar']}/{s['max_nectar_capacity']}", True, TEXT_DARK), (cx, cy))
        self.draw_progress_bar(self.canvas, cx + 120, cy + 2, 160, 11, s['nectar'], s['max_nectar_capacity'], NECTAR_BAR)
        cy += 20

        self.canvas.blit(self.font_small.render(f"Nectar Deposited: {s['total_nectar_collected']}", True, TEXT_DARK), (cx, cy))
        cy += 18
        self.canvas.blit(self.font_small.render(f"Distance Travelled: {s['distance']} steps", True, TEXT_DARK), (cx, cy))
        cy += 18
        self.canvas.blit(self.font_small.render(f"Flowers Visited: {s['flowers_visited']}", True, TEXT_DARK), (cx, cy))
        cy += 18
        self.canvas.blit(self.font_small.render(f"Time Step: {s['time_steps']} / {s['max_steps']}", True, TEXT_DARK), (cx, cy))

        y += 158

        # Card 2: Decision Log & Rules
        card2 = pygame.Rect(x, y, PANEL_W - 32, 135)
        pygame.draw.rect(self.canvas, CARD_BG, card2, border_radius=8)
        pygame.draw.rect(self.canvas, CARD_BORDER, card2, width=1, border_radius=8)

        cx = x + 12
        cy = y + 8
        self.canvas.blit(self.font_bold.render("DECISION & AI REASONING", True, ACCENT), (cx, cy))
        cy += 20

        target_flower = getattr(self.bee, "_target_flower", None)
        target_str = f"Target: {s['target']} at ({target_flower.x}, {target_flower.y})" if target_flower else f"Target: {s['target'] if s['target'] else 'None'}"
        self.canvas.blit(self.font.render(target_str, True, TEXT_DARK), (cx, cy))
        cy += 18

        hx, hy = self.env.hive
        bx, by = self.bee.pos
        dist_to_hive = abs(bx - hx) + abs(by - hy)

        if self.bee.nectar >= self.bee.max_nectar_capacity:
            rule_str = "Rule: Full Load (90/90) -> Return to Hive"
            rule_color = (220, 38, 38)
        elif self.bee.energy <= dist_to_hive:
            rule_str = "Rule: Low Energy Safety -> Immediate Return"
            rule_color = (220, 38, 38)
        elif self.bee.nectar > 0:
            rule_str = f"Rule: Partial Capacity ({self.bee.nectar}/90) -> Seeking Next"
            rule_color = (37, 99, 235)
        else:
            rule_str = "Rule: Empty Capacity (0/90) -> Seeking First Flower"
            rule_color = (100, 116, 139)

        self.canvas.blit(self.font_small.render(rule_str, True, rule_color), (cx, cy))
        cy += 20

        self.canvas.blit(self.font_bold.render("Reasoning:", True, TEXT_MUTED), (cx, cy))
        cy += 15
        self._draw_wrapped(s["reason"], cx, cy, PANEL_W - 56, self.font_small, TEXT_DARK)

        y += 143

        # CHANGE 3: Live Candidate Decision Matrix Table
        card3 = pygame.Rect(x, y, PANEL_W - 32, 180)
        pygame.draw.rect(self.canvas, CARD_BG, card3, border_radius=8)
        pygame.draw.rect(self.canvas, CARD_BORDER, card3, width=1, border_radius=8)

        cx = x + 12
        cy = y + 8
        self.canvas.blit(self.font_bold.render("CANDIDATE DECISION MATRIX", True, ACCENT), (cx, cy))
        cy += 20

        evals = getattr(self.bee, 'evaluations', [])
        if evals:
            headers = ["ID", "Dist", "Nectar", "Score"]
            col_x = [cx, cx + 50, cx + 110, cx + 180]
            for hx_pos, h in zip(col_x, headers):
                self.canvas.blit(self.font_badge.render(h, True, TEXT_MUTED), (hx_pos, cy))
            cy += 16
            pygame.draw.line(self.canvas, CARD_BORDER, (cx, cy - 2), (cx + 290, cy - 2), 1)

            for cand in evals[:4]:
                bg_c = (239, 246, 255) if cand.get("selected") else CARD_BG
                txt_c = ACCENT if cand.get("selected") else TEXT_DARK
                
                row_r = pygame.Rect(cx - 2, cy - 2, 294, 18)
                if cand.get("selected"):
                    pygame.draw.rect(self.canvas, bg_c, row_r, border_radius=4)

                self.canvas.blit(self.font_small.render(f"#{cand['id']}", True, txt_c), (col_x[0], cy))
                self.canvas.blit(self.font_small.render(f"{cand['dist']} steps", True, txt_c), (col_x[1], cy))
                self.canvas.blit(self.font_small.render(f"{cand['nectar']}", True, txt_c), (col_x[2], cy))
                self.canvas.blit(self.font_small.render(f"{cand['score']:.2f}", True, txt_c), (col_x[3], cy))
                cy += 18
        else:
            self.canvas.blit(self.font_small.render("No active evaluations (returning or idle)", True, TEXT_MUTED), (cx, cy + 20))

    def _draw_wrapped(self, text, x, y, max_width, font, color):
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
        for i, l in enumerate(lines[:2]):
            surf = font.render(l, True, color)
            self.canvas.blit(surf, (x, y + i * 14))

    def draw_buttons_bar(self):
        bar_rect = pygame.Rect(0, MAP_H, WINDOW_W, BUTTON_BAR_H)
        pygame.draw.rect(self.canvas, PANEL_BG, bar_rect)
        pygame.draw.line(self.canvas, CARD_BORDER, (0, MAP_H), (WINDOW_W, MAP_H), 1)

        self.btn_start.active = self.running_sim

        for b in self.buttons:
            b.draw(self.canvas, self.font)

        self.strategy_dropdown.draw(self.canvas, self.font)

    def draw_event_banner(self):
        text = self.font_bold.render(self.event_banner, True, (255, 255, 255))
        pad = 10
        w = text.get_width() + pad * 2
        h = text.get_height() + pad * 2
        rect = pygame.Rect((MAP_W - w) // 2, 12, w, h)
        pygame.draw.rect(self.canvas, (220, 38, 38), rect, border_radius=8)
        self.canvas.blit(text, (rect.x + pad, rect.y + pad))

    def draw_comparison_overlay(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 230))
        self.canvas.blit(overlay, (0, 0))

        title = self.font_title.render("Strategy Comparison Results", True, (255, 255, 255))
        self.canvas.blit(title, (40, 30))

        headers = ["Strategy", "Nectar", "Distance", "Energy", "Flowers", "Steps", "Efficiency"]
        col_x = [40, 290, 390, 490, 590, 690, 790]

        y = 80
        for cx, h in zip(col_x, headers):
            surf = self.font_bold.render(h, True, (250, 204, 21))
            self.canvas.blit(surf, (cx, y))
        y += 28

        pygame.draw.line(self.canvas, (100, 116, 139), (40, y - 6), (920, y - 6), 1)

        if self.comparison_results:
            for r in self.comparison_results:
                values = [
                    r["label"],
                    str(r["nectar_collected"]),
                    str(r["distance_travelled"]),
                    str(r["energy_consumed"]),
                    str(r["flowers_visited"]),
                    str(r["time_steps"]),
                    f"{r['efficiency']:.3f}",
                ]
                for cx, v in zip(col_x, values):
                    surf = self.font.render(v, True, (255, 255, 255))
                    self.canvas.blit(surf, (cx, y))
                y += 28

            y += 15
            chart_box = pygame.Rect(40, y, 920, 140)
            pygame.draw.rect(self.canvas, (30, 41, 59), chart_box, border_radius=8)
            
            self.canvas.blit(self.font_bold.render("VISUAL EFFICIENCY BENCHMARK", True, (250, 204, 21)), (55, y + 10))

            max_eff = max(r["efficiency"] for r in self.comparison_results) or 1.0
            colors = [(91, 143, 185), (224, 164, 88), (111, 191, 115)]

            bar_y = y + 40
            for i, r in enumerate(self.comparison_results):
                lbl = self.font_small.render(r["label"].split(" (")[0], True, (255, 255, 255))
                self.canvas.blit(lbl, (55, bar_y))
                
                bar_w = int((r["efficiency"] / max_eff) * 550)
                pygame.draw.rect(self.canvas, (51, 65, 85), (180, bar_y, 550, 16), border_radius=4)
                pygame.draw.rect(self.canvas, colors[i], (180, bar_y, bar_w, 16), border_radius=4)
                
                eff_txt = self.font_bold.render(f"{r['efficiency']:.3f}", True, (255, 255, 255))
                self.canvas.blit(eff_txt, (740, bar_y))
                bar_y += 28

            y += 155
            v_box = pygame.Rect(40, y, 920, 95)
            pygame.draw.rect(self.canvas, (30, 41, 59), v_box, border_radius=8)
            pygame.draw.rect(self.canvas, (37, 99, 235), v_box, width=1, border_radius=8)

            intel = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_INTELLIGENT)
            greedy = next(r for r in self.comparison_results if r["strategy"] == STRATEGY_GREEDY)
            
            eff_diff = ((intel["efficiency"] - greedy["efficiency"]) / max(0.001, greedy["efficiency"])) * 100
            dist_diff = ((greedy["distance_travelled"] - intel["distance_travelled"]) / max(1, intel["distance_travelled"])) * 100

            self.canvas.blit(self.font_bold.render("PERFORMANCE BREAKDOWN SUMMARY", True, (37, 99, 235)), (55, y + 10))
            v_text1 = f"• Intelligent Bee achieved {eff_diff:.1f}% higher efficiency than Highest Nectar by avoiding long travels."
            v_text2 = f"• Greedy strategy traveled {dist_diff:.1f}% farther due to unweighted heuristic choices."
            
            self.canvas.blit(self.font_small.render(v_text1, True, (226, 232, 240)), (55, y + 36))
            self.canvas.blit(self.font_small.render(v_text2, True, (226, 232, 240)), (55, y + 58))

        hint = self.font_small.render("Click Start or Reset to return. Chart saved to out/comparison_chart.png. Press F11 for Fullscreen.", True, (148, 163, 184))
        self.canvas.blit(hint, (40, WINDOW_H - 30))

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