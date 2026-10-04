import sys, pygame
from simulation.environment import Environment, GRID_COLS, GRID_ROWS
from simulation.bee import Bee
from simulation.decision import SimulationController, STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT, STRATEGY_LABELS
from simulation.sprites import SpriteManager
from analysis import comparison
from ui.theme import (
    CELL, MAP_W, MAP_H, GRID_X, GRID_Y, GRID_RADIUS, WINDOW_W, WINDOW_H, PANEL_X, PANEL_W, DEFAULT_SPEED,
    SV_WOOD_DARK, SV_WOOD_MAIN, SV_WOOD_HI, SV_WOOD_SH, SV_WOOD_RIVET, SV_WOOD_HEADER,
    SV_PARCHMENT, SV_PARCHMENT_LIGHT, SV_PARCHMENT_DARK, SV_PARCHMENT_INSET,
    SV_TEXT_DARK, SV_TEXT_MUTED, SV_TEXT_TITLE, SV_TEXT_LIGHT, SV_TEXT_HI_SHADOW,
    SV_ENERGY_MAIN, SV_NECTAR_MAIN, SV_NECTAR_HI, SV_GOLD_STAR, SV_GOLD_WINNER, SV_GOLD_BORDER,
    SV_BTN_NORMAL_FILL, SV_BTN_ACTIVE_FILL, SV_BTN_DANGER_FILL, SV_BTN_DANGER_HI, SV_BTN_DANGER_SH,
    SV_HIVE_FILL, BG, OBSTACLE, OBSTACLE_BORDER,
)
from ui.widgets import draw_text_shadow, draw_stardew_frame, draw_stardew_grid_border, draw_stardew_slot, draw_stardew_bar, draw_glass_rect, Button, Dropdown

def draw_star(surface, x, y, size=5):
    pygame.draw.polygon(surface, SV_WOOD_DARK, [(x, y - size), (x + size, y), (x, y + size), (x - size, y)])
    pygame.draw.polygon(surface, SV_GOLD_STAR, [(x, y - size + 1), (x + size - 1, y), (x, y + size - 1), (x - size + 1, y)])

class BeeLogicApp:
    def __init__(self, seed=42, fullscreen=True, initial_strategy=STRATEGY_INTELLIGENT, initial_speed=DEFAULT_SPEED, max_steps=400, event_step=45):
        pygame.init()
        pygame.display.set_caption("BeeLogic - Intelligent Bee Foraging Simulation [1080p Stardew Theme]")
        self.base_w, self.base_h, self.fullscreen, self.clock = WINDOW_W, WINDOW_H, fullscreen, pygame.time.Clock()
        self.canvas = pygame.Surface((self.base_w, self.base_h))
        try: self.screen = pygame.display.set_mode((self.base_w, self.base_h), (pygame.FULLSCREEN | pygame.DOUBLEBUF) if fullscreen else pygame.RESIZABLE)
        except Exception: self.screen = pygame.display.set_mode((self.base_w, self.base_h))
        ff = "Segoe UI, DejaVu Sans, Liberation Sans, Arial, sans-serif"
        self.font_hero, self.font_title = pygame.font.SysFont(ff, 30, bold=True), pygame.font.SysFont(ff, 24, bold=True)
        self.font_header, self.font_body = pygame.font.SysFont(ff, 18, bold=True), pygame.font.SysFont(ff, 16)
        self.font_body_bold, self.font_small = pygame.font.SysFont(ff, 16, bold=True), pygame.font.SysFont(ff, 14)
        self.font_small_bold, self.font_badge, self.font_button = pygame.font.SysFont(ff, 14, bold=True), pygame.font.SysFont(ff, 13, bold=True), pygame.font.SysFont(ff, 16, bold=True)
        self.seed, self.max_steps, self.event_step, self.sim_speed = seed, max_steps, event_step, initial_speed
        self.strategies, self.sprite_mgr = [STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT], SpriteManager(cell_size=CELL, window_size=(WINDOW_W, WINDOW_H))
        self.anim_time, self.running_sim, self.move_accumulator, self.comparison_results, self.show_comparison = 0.0, False, 0.0, None, False
        self.grid_x, self.grid_y = GRID_X, GRID_Y
        self.grid_surface, self.grid_mask = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA), pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        self.grid_mask.fill((0, 0, 0, 0))
        pygame.draw.rect(self.grid_mask, (255, 255, 255, 255), (0, 0, MAP_W, MAP_H), border_radius=GRID_RADIUS)
        self._build_controls(selected_idx=self.strategies.index(initial_strategy) if initial_strategy in self.strategies else 2)
        self.reset_simulation()

    def draw_glass_rect(self, surface, color_rgba, rect, border_radius=0, border_color=None, border_width=1):
        draw_glass_rect(surface, color_rgba, rect, border_radius=border_radius, border_color=border_color, border_width=border_width)

    def _build_controls(self, selected_idx=2):
        y, h = self.grid_y + MAP_H + 14, 50
        self.btn_start, self.btn_pause, self.btn_reset = Button((24, y, 110, h), "Start"), Button((144, y, 110, h), "Pause"), Button((264, y, 110, h), "Reset")
        self.strategy_dropdown = Dropdown((384, y, 360, h), [(s, STRATEGY_LABELS[s]) for s in self.strategies], selected_idx=selected_idx)
        self.btn_speed, self.btn_trigger = Button((754, y, 150, h), f"Speed: {self.sim_speed:.1f}x"), Button((914, y, 220, h), "Deplete Flower", is_danger=False)
        self.btn_compare, self.btn_exit = Button((1144, y, 260, h), "Run Benchmark (C)", is_benchmark=True), Button((1770, y, 126, h), "Quit (Esc)", is_danger=True)
        self.buttons = [self.btn_start, self.btn_pause, self.btn_reset, self.btn_speed, self.btn_trigger, self.btn_compare, self.btn_exit]

    def reset_simulation(self):
        self.env, self.bee = Environment(seed=self.seed), Bee(hive_pos=(1, 1), max_steps=self.max_steps)
        self.controller = SimulationController(self.env, self.bee, self.strategies[self.strategy_dropdown.selected_idx], event_step=self.event_step)
        self.running_sim, self.move_accumulator, self.event_banner, self.event_banner_timer = False, 0.0, None, 0

    def toggle_speed(self):
        speeds = [1.0, 2.0, 3.0, 5.0, 10.0]
        self.sim_speed = speeds[((speeds.index(self.sim_speed) if self.sim_speed in speeds else 2) + 1) % len(speeds)]
        self.btn_speed.label = f"Speed: {self.sim_speed:.1f}x"

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit(0)
            win_w, win_h = self.screen.get_size()
            mpos = (int(event.pos[0] * self.base_w / win_w), int(event.pos[1] * self.base_h / win_h)) if hasattr(event, 'pos') else (0, 0)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    if self.show_comparison: self.show_comparison = False
                    else: pygame.quit(); sys.exit(0)
                elif event.key == pygame.K_SPACE: self.running_sim = not self.running_sim
                elif event.key == pygame.K_r: self.reset_simulation()
                elif event.key == pygame.K_c: self.run_comparison()
                elif event.key in (pygame.K_t, pygame.K_e):
                    fl = self.controller.trigger_dynamic_event()
                    if fl: self.event_banner, self.event_banner_timer = f"Dynamic Event: Flower #{fl.id} depleted! Bee redirecting...", 3.5
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                adj = pygame.event.Event(event.type, pos=mpos, button=getattr(event, 'button', 1))
                if adj.type == pygame.MOUSEMOTION:
                    for b in self.buttons: b.update_hover(adj.pos)
                dd = self.strategy_dropdown.handle_event(adj)
                if dd is True: continue
                elif isinstance(dd, int): self.reset_simulation(); continue
                if adj.type == pygame.MOUSEBUTTONDOWN and adj.button == 1:
                    pos = adj.pos
                    if self.show_comparison: self.show_comparison = False; continue
                    if self.btn_start.clicked(pos): self.running_sim, self.show_comparison = True, False
                    elif self.btn_pause.clicked(pos): self.running_sim = False
                    elif self.btn_reset.clicked(pos): self.reset_simulation(); self.show_comparison = False
                    elif self.btn_speed.clicked(pos): self.toggle_speed()
                    elif self.btn_trigger.clicked(pos):
                        fl = self.controller.trigger_dynamic_event()
                        if fl: self.event_banner, self.event_banner_timer = f"Dynamic Event: Flower #{fl.id} depleted! Bee redirecting...", 3.5
                    elif self.btn_compare.clicked(pos): self.run_comparison()
                    elif self.btn_exit.clicked(pos): pygame.quit(); sys.exit(0)
                    elif self.grid_x <= pos[0] < self.grid_x + MAP_W and self.grid_y <= pos[1] < self.grid_y + MAP_H:
                        cf = self.env.get_flower_at((pos[0] - self.grid_x) // CELL, (pos[1] - self.grid_y) // CELL)
                        if cf and cf.is_available():
                            fl = self.controller.trigger_dynamic_event(target_flower=cf)
                            if fl: self.event_banner, self.event_banner_timer = f"Flower #{fl.id} depleted! Bee redirecting...", 3.5

    def run_comparison(self):
        self.comparison_results = comparison.run_comparison(seed=self.seed, max_steps=self.max_steps, event_step=self.event_step)
        try: comparison.save_chart(self.comparison_results, path="out/comparison_chart.png")
        except Exception: pass
        self.show_comparison, self.running_sim = True, False

    def update(self, dt):
        self.anim_time += dt * (min(2.5, self.sim_speed * 0.7 + 0.3) if self.running_sim else 1.0)
        if not self.running_sim or self.show_comparison: return
        prev_log = self.controller.event_log
        self.move_accumulator += dt * self.sim_speed
        while self.move_accumulator >= 1.0:
            self.controller.tick()
            self.move_accumulator -= 1.0
            if self.bee.finished: self.running_sim = False; break
        if self.controller.event_log and self.controller.event_log != prev_log:
            self.event_banner, self.event_banner_timer = self.controller.event_log, 3.5
        if self.event_banner_timer > 0:
            self.event_banner_timer -= dt
            if self.event_banner_timer <= 0: self.event_banner = None

    def cell_rect(self, x, y):
        return pygame.Rect(x * CELL, y * CELL, CELL, CELL)

    def draw_flower(self, surface, x, y, nectar, is_available, flower_id=None):
        sprite = self.sprite_mgr.get_flower_sprite(flower_id or 1, is_available)
        surface.blit(sprite, (x * CELL + (CELL - sprite.get_width()) // 2, y * CELL + (CELL - sprite.get_height()) // 2))
        cx, cy = x * CELL, (y + 1) * CELL
        if flower_id is not None:
            id_txt = f"#{flower_id}"
            tw, th = self.font_badge.size(id_txt)
            r = pygame.Rect(cx + 2, cy - th - 5, tw + 6, th + 3)
            pygame.draw.rect(surface, SV_WOOD_DARK if is_available else (140, 110, 85), r, border_radius=3)
            pygame.draw.rect(surface, (252, 240, 205) if is_available else (225, 210, 190), r.inflate(-2, -2), border_radius=2)
            if is_available: draw_text_shadow(surface, id_txt, self.font_badge, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (r.x + 3, r.y + 1), (0, 1))
            else: surface.blit(self.font_badge.render(id_txt, True, (140, 110, 85)), (r.x + 3, r.y + 1))
        n_txt = str(nectar if is_available else 0)
        tw, th = self.font_badge.size(n_txt)
        r = pygame.Rect(cx + CELL - tw - 10, cy - th - 5, tw + 8, th + 3)
        pygame.draw.rect(surface, SV_WOOD_DARK if is_available else (140, 110, 85), r, border_radius=4 if is_available else 3)
        pygame.draw.rect(surface, SV_NECTAR_MAIN if is_available else (225, 210, 190), r.inflate(-2, -2), border_radius=3 if is_available else 2)
        if is_available:
            pygame.draw.line(surface, SV_NECTAR_HI, (r.x + 2, r.y + 2), (r.right - 3, r.y + 2), 1)
            draw_text_shadow(surface, n_txt, self.font_badge, (255, 255, 245), (70, 35, 10), (r.x + 4, r.y + 1), (1, 1))
        else: surface.blit(self.font_badge.render(n_txt, True, (140, 110, 85)), (r.x + 4, r.y + 1))

    def draw_bee(self, surface, x, y):
        act = "idle" if not self.running_sim or self.bee.finished else getattr(self.bee, "activity", "fly")
        act = act if act in ("fly", "harvest", "deposit", "idle") else "fly"
        frame = self.sprite_mgr.get_bee_frame(act, getattr(self.bee, "facing", "right"), self.anim_time)
        vx, vy = x, y
        if self.running_sim and hasattr(self.bee, "prev_pos") and self.bee.prev_pos != (x, y):
            t = min(1.0, max(0.0, self.move_accumulator))
            vx, vy = self.bee.prev_pos[0] + (x - self.bee.prev_pos[0]) * t, self.bee.prev_pos[1] + (y - self.bee.prev_pos[1]) * t
        cx, cy = vx * CELL + CELL // 2, vy * CELL + CELL // 2
        sh = pygame.Surface((36, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (15, 23, 42, 60), (0, 0, 36, 14))
        surface.blit(sh, (int(cx - 18), int(cy + 18)))
        surface.blit(frame, (int(cx - frame.get_width() // 2), int(cy - frame.get_height() // 2 - 2)))
        cur, mcap = self.bee.nectar, self.bee.max_nectar_capacity
        if self.bee.finished: b_txt, b_bg, tc = f"[{cur}/{mcap} FINISHED]", (235, 185, 35), SV_TEXT_DARK
        elif cur >= mcap: b_txt, b_bg, tc = f"[{cur}/{mcap} FULL -> RETURNING]", SV_BTN_DANGER_FILL, (255, 255, 255)
        elif act in ("harvest", "deposit"): b_txt, b_bg, tc = f"[{cur}/{mcap} {act.upper()}ING]", ((220, 125, 25) if act == "harvest" else (210, 135, 30)), (255, 255, 255)
        elif cur > 0: b_txt, b_bg, tc = f"[{cur}/{mcap} FORAGING]", SV_BTN_ACTIVE_FILL, (255, 255, 255)
        else: b_txt, b_bg, tc = f"[{cur}/{mcap} EMPTY]", (245, 230, 190), SV_TEXT_DARK
        tw, th = self.font_badge.size(b_txt)
        bx, by = (int(cx - tw - 40) if int(cx + 26) + tw + 14 > MAP_W else int(cx + 26)), (int(cy + 22) if int(cy - 28) < 8 else int(cy - 28))
        r = pygame.Rect(bx, by, tw + 14, th + 6)
        pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=5)
        pygame.draw.rect(surface, b_bg, r.inflate(-2, -2), border_radius=4)
        draw_text_shadow(surface, b_txt, self.font_badge, tc, (50, 20, 8) if tc == (255, 255, 255) else SV_TEXT_HI_SHADOW, (bx + 7, by + 3), (1 if tc == (255, 255, 255) else 0, 1))

    def draw_grid(self):
        self.grid_surface.fill((0, 0, 0, 0))
        self.grid_surface.blit(self.sprite_mgr.get_grass_grid_surface(GRID_COLS, GRID_ROWS), (0, 0))
        gl_surf = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        for gx in range(1, GRID_COLS): pygame.draw.line(gl_surf, (255, 255, 255, 40), (gx * CELL, 0), (gx * CELL, MAP_H), 1)
        for gy in range(1, GRID_ROWS): pygame.draw.line(gl_surf, (255, 255, 255, 40), (0, gy * CELL), (MAP_W, gy * CELL), 1)
        self.grid_surface.blit(gl_surf, (0, 0))
        for (ox, oy) in self.env.obstacles:
            cx, cy = ox * CELL + CELL // 2, oy * CELL + CELL // 2
            sh = pygame.Surface((int(CELL * 0.78), int(CELL * 0.28)), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (15, 35, 10, 85), (0, 0, int(CELL * 0.78), int(CELL * 0.28)))
            self.grid_surface.blit(sh, (cx - int(CELL * 0.78) // 2, cy + CELL // 4 - 4))
            st = self.sprite_mgr.get_stone_sprite(ox * 7 + oy)
            if st: self.grid_surface.blit(st, (cx - st.get_width() // 2, cy - st.get_height() // 2 - 2))
            else:
                r = pygame.Rect(ox * CELL + 4, oy * CELL + 4, CELL - 8, CELL - 8)
                pygame.draw.rect(self.grid_surface, OBSTACLE, r, border_radius=8)
                pygame.draw.rect(self.grid_surface, OBSTACLE_BORDER, r, width=1, border_radius=8)
        if self.bee.current_path and len(self.bee.current_path) > 1:
            pts = [(px * CELL + CELL // 2, py * CELL + CELL // 2) for (px, py) in self.bee.current_path]
            pygame.draw.lines(self.grid_surface, (230, 160, 20), False, pts, 5)
            pygame.draw.lines(self.grid_surface, (255, 220, 80), False, pts, 2)
            for (px, py) in self.bee.current_path:
                pygame.draw.rect(self.grid_surface, (255, 230, 110), self.cell_rect(px, py).inflate(-44, -44), border_radius=4)
        hx, hy = self.env.hive
        h_rect = pygame.Rect(hx * CELL + 4, hy * CELL + 4, CELL - 8, CELL - 8)
        pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, h_rect, border_radius=8)
        in_h = h_rect.inflate(-4, -4)
        pygame.draw.rect(self.grid_surface, SV_HIVE_FILL, in_h, border_radius=6)
        pygame.draw.line(self.grid_surface, SV_WOOD_SH, (in_h.left, in_h.centery - 6), (in_h.right - 1, in_h.centery - 6), 2)
        pygame.draw.line(self.grid_surface, SV_WOOD_SH, (in_h.left, in_h.centery + 6), (in_h.right - 1, in_h.centery + 6), 2)
        pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, (in_h.centerx - 12, in_h.bottom - 10, 24, 6), border_radius=2)
        sign_r = pygame.Rect(h_rect.centerx - 22, h_rect.top + 5, 44, 18)
        pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, sign_r, border_radius=3)
        pygame.draw.rect(self.grid_surface, SV_PARCHMENT, sign_r.inflate(-2, -2), border_radius=2)
        draw_text_shadow(self.grid_surface, "HIVE", self.font_badge, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (sign_r.x + 8, sign_r.y + 1), (0, 1))
        tf = getattr(self.bee, "_target_flower", None)
        if tf:
            r = self.cell_rect(tf.x, tf.y)
            pygame.draw.rect(self.grid_surface, (245, 175, 25), r.inflate(8, 8), width=3, border_radius=10)
            lbl = f"★ TARGET #{getattr(tf, 'id', 'Target')} ★"
            tw, th = self.font_badge.size(lbl)
            pr = pygame.Rect(r.x + (CELL - tw - 12) // 2, r.y - th - 8, tw + 12, th + 4)
            pygame.draw.rect(self.grid_surface, SV_WOOD_DARK, pr, border_radius=4)
            pygame.draw.rect(self.grid_surface, (254, 240, 205), pr.inflate(-2, -2), border_radius=3)
            draw_text_shadow(self.grid_surface, lbl, self.font_badge, (180, 85, 15), SV_TEXT_HI_SHADOW, (pr.x + 6, pr.y + 2), (0, 1))
        for f in self.env.flowers: self.draw_flower(self.grid_surface, f.x, f.y, f.nectar, f.is_available(), flower_id=f.id)
        self.draw_bee(self.grid_surface, self.bee.pos[0], self.bee.pos[1])
        self.grid_surface.blit(self.grid_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        g_rect = pygame.Rect(self.grid_x, self.grid_y, MAP_W, MAP_H)
        draw_stardew_grid_border(self.canvas, g_rect)
        self.canvas.blit(self.grid_surface, (self.grid_x, self.grid_y))
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, g_rect, width=2, border_radius=GRID_RADIUS)

    def draw_progress_bar(self, surface, x, y, width, height, current, max_val, fill_color):
        draw_stardew_bar(surface, x, y, width, height, current, max_val, bar_type='energy')

    def draw_panel(self):
        x, card_w, y, s = PANEL_X, PANEL_W, self.grid_y, self.bee.status_dict()
        draw_stardew_frame(self.canvas, (x, y, card_w, 236), is_inset=False, corner_radius=8)
        cx, cy = x + 18, y + 16
        draw_text_shadow(self.canvas, "AGENT TELEMETRY & VITALS", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        act = getattr(self.bee, 'activity', 'FLYING').upper()
        if self.bee.finished: st_txt, st_bg, st_fg = "COMPLETED", (235, 185, 35), SV_TEXT_DARK
        elif self.bee.nectar >= self.bee.max_nectar_capacity: st_txt, st_bg, st_fg = "RETURNING (FULL)", SV_BTN_DANGER_FILL, (255, 255, 255)
        elif act in ("HARVEST", "DEPOSIT"): st_txt, st_bg, st_fg = f"{act}ING", ((220, 125, 25) if act == "HARVEST" else (210, 135, 30)), (255, 255, 255)
        else: st_txt, st_bg, st_fg = "FORAGING", SV_BTN_ACTIVE_FILL, (255, 255, 255)
        stw, sth = self.font_badge.size(st_txt)
        st_r = pygame.Rect(x + card_w - stw - 36, cy - 2, stw + 16, sth + 6)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, st_r, border_radius=4)
        pygame.draw.rect(self.canvas, st_bg, st_r.inflate(-2, -2), border_radius=3)
        draw_text_shadow(self.canvas, st_txt, self.font_badge, st_fg, (50, 20, 10) if st_fg == (255, 255, 255) else SV_TEXT_HI_SHADOW, (st_r.x + 8, st_r.y + 3), (1 if st_fg == (255, 255, 255) else 0, 1))
        cy += 32

        for icon, name, cur, mx, btype, cmain in (("E", "Energy Level:", s['energy'], s['max_energy'], 'energy', SV_ENERGY_MAIN), ("N", "Nectar Load:", s['nectar'], s['max_nectar_capacity'], 'nectar', SV_NECTAR_MAIN)):
            ir = pygame.Rect(cx, cy + 1, 20, 20)
            pygame.draw.rect(self.canvas, SV_WOOD_DARK, ir, border_radius=4)
            pygame.draw.rect(self.canvas, cmain, ir.inflate(-2, -2), border_radius=3)
            draw_text_shadow(self.canvas, icon, self.font_small_bold, (255, 255, 255), (20, 50, 10) if icon == "E" else (60, 25, 6), (cx + (5 if icon == "E" else 4), cy + 2), (1, 1))
            draw_text_shadow(self.canvas, name, self.font_body_bold, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (cx + 28, cy), (0, 1))
            self.canvas.blit(self.font_small.render(f"{cur} / {mx} ({int(cur / mx * 100)}%)", True, SV_TEXT_MUTED), (cx + 138, cy + 1))
            draw_stardew_bar(self.canvas, cx + 265, cy + 2, card_w - 305, 18, cur, mx, btype)
            cy += 28 if icon == "E" else 32

        tw, th = (card_w - 48) // 2, 52
        for i, (ml, mv, mc) in enumerate([("Nectar Deposited", f"{s['total_nectar_collected']} units", (180, 85, 12)), ("Distance Travelled", f"{s['distance']} steps", SV_TEXT_DARK), ("Flowers Visited", f"{s['flowers_visited']} flowers", SV_TEXT_DARK), ("Simulation Step", f"{s['time_steps']} / {s['max_steps']}", SV_TEXT_DARK)]):
            tx, ty = cx + (i % 2) * (tw + 12), cy + (i // 2) * (th + 8)
            draw_stardew_slot(self.canvas, (tx, ty, tw, th))
            self.canvas.blit(self.font_badge.render(ml, True, SV_TEXT_MUTED), (tx + 12, ty + 6))
            draw_text_shadow(self.canvas, mv, self.font_header, mc, SV_TEXT_HI_SHADOW, (tx + 12, ty + 24), (0, 1))
        y += 250

        draw_stardew_frame(self.canvas, (x, y, card_w, 224), is_inset=False, corner_radius=8)
        cx, cy = x + 18, y + 16
        draw_text_shadow(self.canvas, "DECISION ENGINE & ACTIVE RULES", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        cy += 30
        tf = getattr(self.bee, "_target_flower", None)
        t_str, tc = (f"Target: Flower #{tf.id} at ({tf.x}, {tf.y}) — Nectar: {tf.nectar}", (185, 90, 15)) if tf else ((f"Target: Hive at ({self.env.hive[0]}, {self.env.hive[1]}) — Depositing Load", (195, 110, 20)) if s['target'] == "Hive" else (f"Target: {s['target'] or 'None (Simulation Finished)'}", SV_TEXT_DARK))
        draw_text_shadow(self.canvas, t_str, self.font_body_bold, tc, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        cy += 28
        dist_h = abs(self.bee.pos[0] - self.env.hive[0]) + abs(self.bee.pos[1] - self.env.hive[1])
        if self.bee.nectar >= self.bee.max_nectar_capacity: r_str, r_bg, r_bd, r_tc = "Active Rule [Capacity Max]: Capacity reached (90/90) -> Return to Hive via A*", (248, 222, 220), (180, 50, 45), (150, 25, 20)
        elif self.bee.energy <= dist_h + 2: r_str, r_bg, r_bd, r_tc = "Active Rule [Safety Reserve]: Energy low -> Immediate emergency return", (248, 222, 220), (180, 50, 45), (150, 25, 20)
        elif self.bee.nectar > 0: r_str, r_bg, r_bd, r_tc = f"Active Rule [Partial Load ({self.bee.nectar}/90)]: Seeking optimal nectar source", (248, 235, 195), (195, 130, 30), (155, 80, 12)
        else: r_str, r_bg, r_bd, r_tc = "Active Rule [Empty Capacity]: Foraging for initial high-yield flowers", (235, 215, 175), (150, 105, 60), SV_TEXT_DARK
        r_box = pygame.Rect(cx, cy, card_w - 36, 34)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, r_box, border_radius=5)
        pygame.draw.rect(self.canvas, r_bg, r_box.inflate(-2, -2), border_radius=4)
        pygame.draw.rect(self.canvas, r_bd, r_box.inflate(-2, -2), width=1, border_radius=4)
        draw_text_shadow(self.canvas, r_str, self.font_badge, r_tc, SV_TEXT_HI_SHADOW, (cx + 10, cy + 9), (0, 1))
        cy += 44
        draw_text_shadow(self.canvas, "Reasoning Explanation:", self.font_small_bold, SV_TEXT_MUTED, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        self._draw_wrapped(s["reason"], cx, cy + 20, card_w - 40, self.font_small, SV_TEXT_DARK)
        y += 238

        draw_stardew_frame(self.canvas, (x, y, card_w, 472), is_inset=False, corner_radius=8)
        cx, cy = x + 18, y + 16
        draw_text_shadow(self.canvas, "CANDIDATE DECISION MATRIX", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (cx, cy), (0, 1))
        ftag = self.font_badge.render("Score = Nectar / (Dist ^ 1.5)", True, SV_TEXT_MUTED)
        self.canvas.blit(ftag, (x + card_w - ftag.get_width() - 20, cy + 2))
        cy += 30
        evals = getattr(self.bee, 'evaluations', [])
        if evals:
            cols = [cx + 8, cx + 96, cx + 184, cx + 276, cx + 386]
            th_r = pygame.Rect(cx, cy, card_w - 36, 28)
            pygame.draw.rect(self.canvas, SV_WOOD_DARK, th_r, border_radius=4)
            th_in = th_r.inflate(-2, -2)
            pygame.draw.rect(self.canvas, SV_WOOD_HEADER, th_in, border_radius=3)
            pygame.draw.line(self.canvas, SV_WOOD_HI, (th_in.left, th_in.top), (th_in.right - 1, th_in.top), 1)
            for hx, h in zip(cols, ["Flower ID", "Distance", "Nectar", "Score", "Decision Status"]):
                draw_text_shadow(self.canvas, h, self.font_badge, (255, 230, 160), (45, 20, 8), (hx, cy + 6), (1, 1))
            cy += 34
            for rk, cand in enumerate(evals[:6]):
                is_sel = cand.get("selected", False)
                row_r = pygame.Rect(cx, cy, card_w - 36, 34)
                pygame.draw.rect(self.canvas, SV_WOOD_DARK, row_r, border_radius=5 if is_sel else 0, width=0 if is_sel else 1)
                pygame.draw.rect(self.canvas, SV_GOLD_WINNER if is_sel else (SV_PARCHMENT_LIGHT if rk % 2 == 0 else SV_PARCHMENT_INSET), row_r.inflate(-2, -2), border_radius=4 if is_sel else 3)
                if is_sel:
                    pygame.draw.rect(self.canvas, SV_GOLD_BORDER, row_r.inflate(-2, -2), width=1, border_radius=4)
                    draw_star(self.canvas, cols[0] - 2, cy + 17, 5)
                tc = (50, 22, 8) if is_sel else SV_TEXT_DARK
                draw_text_shadow(self.canvas, f"Flower #{cand['id']}", self.font_body_bold, tc, SV_TEXT_HI_SHADOW, (cols[0] + (8 if is_sel else 0), cy + 8), (0, 1))
                draw_text_shadow(self.canvas, f"{cand['dist']} steps", self.font_body, tc, SV_TEXT_HI_SHADOW, (cols[1], cy + 8), (0, 1))
                draw_text_shadow(self.canvas, f"{cand['nectar']} u", self.font_body, tc, SV_TEXT_HI_SHADOW, (cols[2], cy + 8), (0, 1))
                draw_text_shadow(self.canvas, f"{cand['score']:.2f}", self.font_body, tc, SV_TEXT_HI_SHADOW, (cols[3], cy + 8), (0, 1))
                st_txt = "SELECTED" if is_sel else f"Rank #{rk + 1}"
                st_s = self.font_badge.render(st_txt, True, (255, 255, 255) if is_sel else SV_TEXT_MUTED)
                st_box = pygame.Rect(cols[4], cy + 6, st_s.get_width() + (14 if is_sel else 10), st_s.get_height() + 4)
                pygame.draw.rect(self.canvas, SV_WOOD_DARK, st_box, border_radius=4, width=0 if is_sel else 1)
                pygame.draw.rect(self.canvas, (180, 50, 15) if is_sel else (240, 220, 180), st_box.inflate(-2, -2), border_radius=3)
                if is_sel: draw_text_shadow(self.canvas, st_txt, self.font_badge, (255, 245, 220), (50, 15, 6), (cols[4] + 7, cy + 8), (1, 1))
                else: self.canvas.blit(st_s, (cols[4] + 5, cy + 8))
                cy += 40
        else:
            draw_text_shadow(self.canvas, "No active evaluations (Bee is currently returning to Hive or idle)", self.font_body, SV_TEXT_MUTED, SV_TEXT_HI_SHADOW, (cx + 10, cy + 40), (0, 1))

    def _draw_wrapped(self, text, x, y, max_width, font, color, max_lines=3):
        words, line, lines = text.split(" "), "", []
        for w in words:
            test = (line + " " + w).strip()
            if font.size(test)[0] > max_width and line: lines.append(line); line = w
            else: line = test
        if line: lines.append(line)
        for i, l in enumerate(lines[:max_lines]):
            draw_text_shadow(self.canvas, l, font, color, SV_TEXT_HI_SHADOW, (x, y + i * 20), (0, 1))

    def draw_buttons_bar(self):
        self.btn_start.active, self.btn_pause.active = self.running_sim, (not self.running_sim and not self.bee.finished)
        y = self.grid_y + MAP_H + 8
        tray_r = pygame.Rect(16, y, WINDOW_W - 32, 62)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, tray_r, border_radius=8)
        t_in = tray_r.inflate(-4, -4)
        pygame.draw.rect(self.canvas, (145, 82, 30), t_in, border_radius=6)
        pygame.draw.line(self.canvas, SV_WOOD_HI, (t_in.left + 2, t_in.top + 1), (t_in.right - 3, t_in.top + 1), 2)
        pygame.draw.line(self.canvas, (90, 44, 16), (t_in.left + 2, t_in.bottom - 2), (t_in.right - 3, t_in.bottom - 2), 2)
        pygame.draw.rect(self.canvas, (65, 34, 15), t_in.inflate(-6, -6), border_radius=4)
        for b in self.buttons: b.draw(self.canvas, self.font_button)
        self.strategy_dropdown.draw(self.canvas, self.font_button)
        draw_text_shadow(self.canvas, "Shortcuts: [Space] Start / Pause   |   [R] Reset Simulation   |   [C] Run Benchmark   |   [Esc / Q] Quit Application", self.font_small_bold, (255, 246, 225), (42, 20, 8), (24, 1054), (1, 1))
        info_txt = f"Environment Seed: {self.seed}"
        draw_text_shadow(self.canvas, info_txt, self.font_small_bold, (255, 246, 225), (42, 20, 8), (WINDOW_W - self.font_small_bold.size(info_txt)[0] - 24, 1054), (1, 1))

    def draw_event_banner(self):
        txt = self.font_header.render(self.event_banner, True, (255, 255, 245))
        rect = pygame.Rect(self.grid_x + (MAP_W - txt.get_width() - 56) // 2, self.grid_y + 18, txt.get_width() + 56, txt.get_height() + 24)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, rect, border_radius=8)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(self.canvas, SV_BTN_DANGER_FILL, inner, border_radius=6)
        pygame.draw.line(self.canvas, SV_BTN_DANGER_HI, (inner.left + 2, inner.top + 1), (inner.right - 3, inner.top + 1), 2)
        pygame.draw.line(self.canvas, SV_BTN_DANGER_SH, (inner.left + 2, inner.bottom - 2), (inner.right - 3, inner.bottom - 2), 2)
        draw_text_shadow(self.canvas, self.event_banner, self.font_header, (255, 250, 235), (50, 15, 8), (rect.x + 28, rect.y + 12), (1, 1))

    def draw_comparison_overlay(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((30, 18, 10, 235))
        self.canvas.blit(overlay, (0, 0))
        draw_stardew_frame(self.canvas, (70, 36, 1780, 1008), is_inset=False, corner_radius=12)
        h_ban = pygame.Rect(100, 60, 1720, 66)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, h_ban, border_radius=8)
        b_in = h_ban.inflate(-4, -4)
        pygame.draw.rect(self.canvas, (138, 32, 28), b_in, border_radius=6)
        pygame.draw.line(self.canvas, (215, 75, 65), (b_in.left + 2, b_in.top + 1), (b_in.right - 3, b_in.top + 1), 2)
        pygame.draw.line(self.canvas, (80, 18, 14), (b_in.left + 2, b_in.bottom - 2), (b_in.right - 3, b_in.bottom - 2), 2)
        pygame.draw.rect(self.canvas, SV_WOOD_RIVET, b_in.inflate(-4, -4), width=1, border_radius=4)
        title_str = "STRATEGY COMPARISON & PERFORMANCE BENCHMARK"
        tw, th = self.font_hero.size(title_str)
        tx = 100 + (1720 - tw) // 2
        for dx in (tx - 26, tx + tw + 26): draw_star(self.canvas, dx, 92, 8)
        draw_text_shadow(self.canvas, title_str, self.font_hero, (255, 225, 120), (50, 12, 8), (tx, 76), (1, 2))
        draw_text_shadow(self.canvas, "Empirical field trial of Nearest Neighbor (BFS), Greedy (Highest Nectar), and Intelligent Weighted A* Search", self.font_body, SV_TEXT_MUTED, SV_TEXT_HI_SHADOW, (110, 136), (0, 1))
        cols, y = [120, 520, 760, 1000, 1220, 1420, 1600], 168
        th_b = pygame.Rect(100, y, 1720, 36)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, th_b, border_radius=6)
        th_in = th_b.inflate(-2, -2)
        pygame.draw.rect(self.canvas, SV_WOOD_HEADER, th_in, border_radius=5)
        pygame.draw.line(self.canvas, SV_WOOD_HI, (th_in.left, th_in.top), (th_in.right - 1, th_in.top), 1)
        for cx, h in zip(cols, ["Strategy", "Nectar Collected", "Distance Travelled", "Energy Consumed", "Flowers Visited", "Time Steps", "Efficiency Ratio"]):
            draw_text_shadow(self.canvas, h, self.font_header, (255, 230, 150), (45, 18, 6), (cx, y + 6), (1, 1))
        y += 46
        if self.comparison_results:
            best_eff = max(r["efficiency"] for r in self.comparison_results)
            for r in self.comparison_results:
                win = (r["efficiency"] == best_eff)
                r_box = pygame.Rect(100, y, 1720, 42)
                pygame.draw.rect(self.canvas, SV_WOOD_DARK, r_box, border_radius=6, width=0 if win else 1)
                pygame.draw.rect(self.canvas, SV_GOLD_WINNER if win else (SV_PARCHMENT_LIGHT if (y // 48) % 2 == 0 else SV_PARCHMENT_INSET), r_box.inflate(-2, -2), border_radius=5)
                if win:
                    pygame.draw.rect(self.canvas, SV_GOLD_BORDER, r_box.inflate(-2, -2), width=1, border_radius=5)
                    draw_star(self.canvas, cols[0] - 8, y + 21, 7)
                vals = [r["label"] + (" [WINNER]" if win else ""), f"{r['nectar_collected']} units", f"{r['distance_travelled']} steps", f"{r['energy_consumed']} units", f"{r['flowers_visited']} flowers", f"{r['time_steps']} steps", f"{r['efficiency']:.3f} (Nectar/Dist)"]
                for cx, v in zip(cols, vals):
                    draw_text_shadow(self.canvas, v, self.font_body_bold if win else self.font_body, (54, 22, 6) if win else SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (cx + (10 if win and cx == cols[0] else 0), y + 10), (0, 1))
                y += 48
            y += 18
            draw_stardew_slot(self.canvas, (100, y, 1720, 230))
            draw_star(self.canvas, 120, y + 24, 5)
            draw_text_shadow(self.canvas, "VISUAL EFFICIENCY BENCHMARK (Nectar Collected / Distance Travelled)", self.font_header, SV_TEXT_TITLE, SV_TEXT_HI_SHADOW, (135, y + 14), (0, 1))
            max_e = max(r["efficiency"] for r in self.comparison_results) or 1.0
            b_cols = [((58, 135, 215), (115, 185, 245), (35, 95, 165)), ((235, 135, 35), (255, 185, 95), (170, 85, 15)), ((245, 195, 35), (255, 235, 115), (180, 135, 15))]
            bar_y = y + 52
            for i, r in enumerate(self.comparison_results):
                draw_text_shadow(self.canvas, r["label"].split(" (")[0], self.font_body_bold, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (130, bar_y + 4), (0, 1))
                bw = max(6, int((r["efficiency"] / max_e) * 1100))
                tr = pygame.Rect(380, bar_y, 1100, 28)
                pygame.draw.rect(self.canvas, SV_WOOD_DARK, tr, border_radius=5)
                gr = tr.inflate(-2, -2)
                pygame.draw.rect(self.canvas, (68, 38, 18), gr, border_radius=4)
                c_m, c_h, c_s = b_cols[i % len(b_cols)]
                fr = pygame.Rect(gr.x, gr.y, bw, gr.h)
                pygame.draw.rect(self.canvas, c_m, fr, border_radius=4)
                pygame.draw.line(self.canvas, c_h, (fr.left + 1, fr.top + 1), (fr.right - 2, fr.top + 1), 2)
                pygame.draw.line(self.canvas, c_s, (fr.left + 1, fr.bottom - 2), (fr.right - 2, fr.bottom - 2), 2)
                draw_text_shadow(self.canvas, f"{r['efficiency']:.3f} Nectar/Step", self.font_header, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (1500, bar_y + 4), (0, 1))
                bar_y += 46
        f_box = pygame.Rect(100, 960, 1720, 48)
        pygame.draw.rect(self.canvas, SV_WOOD_DARK, f_box, border_radius=8)
        f_in = f_box.inflate(-4, -4)
        pygame.draw.rect(self.canvas, (105, 52, 20), f_in, border_radius=6)
        pygame.draw.line(self.canvas, SV_WOOD_HI, (f_in.left + 2, f_in.top + 1), (f_in.right - 3, f_in.top + 1), 2)
        pygame.draw.line(self.canvas, (55, 24, 8), (f_in.left + 2, f_in.bottom - 2), (f_in.right - 3, f_in.bottom - 2), 2)
        for rx in (f_box.left + 16, f_box.right - 16):
            pygame.draw.circle(self.canvas, SV_WOOD_DARK, (rx, f_box.centery), 5)
            pygame.draw.circle(self.canvas, SV_WOOD_RIVET, (rx, f_box.centery), 3)
        h_str = "Click anywhere or press [ ESC ] / [ SPACE ] to return to simulation"
        hw, hh = self.font_body_bold.size(h_str)
        draw_text_shadow(self.canvas, h_str, self.font_body_bold, (255, 248, 220), (35, 12, 4), (f_box.centerx - hw // 2, f_box.centery - hh // 2), (1, 1))

    def draw(self):
        backdrop = self.sprite_mgr.get_backdrop_frame(self.anim_time)
        if backdrop is not None: self.canvas.blit(backdrop, (0, 0))
        else: self.canvas.fill(BG)
        self.draw_grid()
        self.draw_panel()
        self.draw_buttons_bar()
        if self.show_comparison: self.draw_comparison_overlay()
        if self.event_banner: self.draw_event_banner()
        win_size = self.screen.get_size()
        if win_size == (self.base_w, self.base_h): self.screen.blit(self.canvas, (0, 0))
        else: self.screen.blit(pygame.transform.smoothscale(self.canvas, win_size), (0, 0))
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

def run_gui(seed=42, fullscreen=True, initial_strategy=STRATEGY_INTELLIGENT, initial_speed=DEFAULT_SPEED, max_steps=400, event_step=45):
    BeeLogicApp(seed=seed, fullscreen=fullscreen, initial_strategy=initial_strategy, initial_speed=initial_speed, max_steps=max_steps, event_step=event_step).run()
