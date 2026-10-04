"""
ui/widgets.py
-------------
Reusable UI components and drawing primitives for BeeLogic's Stardew Valley theme.
"""

import pygame
from ui.theme import (
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
    SV_TEXT_LIGHT,
    SV_TEXT_SHADOW,
    SV_TEXT_HI_SHADOW,
    SV_ENERGY_MAIN,
    SV_ENERGY_HI,
    SV_ENERGY_SH,
    SV_NECTAR_MAIN,
    SV_NECTAR_HI,
    SV_NECTAR_SH,
    SV_BTN_NORMAL_FILL,
    SV_BTN_NORMAL_HI,
    SV_BTN_NORMAL_SH,
    SV_BTN_HOVER_FILL,
    SV_BTN_HOVER_HI,
    SV_BTN_HOVER_SH,
    SV_BTN_ACTIVE_FILL,
    SV_BTN_ACTIVE_HI,
    SV_BTN_ACTIVE_SH,
    SV_BTN_DANGER_FILL,
    SV_BTN_DANGER_HI,
    SV_BTN_DANGER_SH,
    SV_BTN_BENCH_FILL,
    SV_BTN_BENCH_HI,
    SV_BTN_BENCH_SH,
)


def draw_text_shadow(surface, text, font, color, shadow_color, pos, offset=(1, 1)):
    """Renders text with a 1px shadow for classic retro/tactile game UI."""
    x, y = pos
    s_surf = font.render(text, True, shadow_color)
    surface.blit(s_surf, (x + offset[0], y + offset[1]))
    t_surf = font.render(text, True, color)
    surface.blit(t_surf, (x, y))
    return t_surf.get_width(), t_surf.get_height()


def draw_stardew_frame(surface, rect, is_inset=False, corner_radius=6):
    """
    Renders an authentic Stardew Valley menu window/card:
    Heavy timber outer frame, 3D golden bevels, inner dark border, warm parchment canvas,
    and brass corner rivets.
    """
    r = pygame.Rect(rect)
    # 1. Outer dark timber border
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=corner_radius)

    # 2. Beveled Wood Frame
    inner1 = r.inflate(-4, -4)
    pygame.draw.rect(surface, SV_WOOD_MAIN, inner1, border_radius=max(2, corner_radius - 2))

    # Top and left golden oak highlight
    pygame.draw.line(surface, SV_WOOD_HI, (inner1.left + 2, inner1.top + 1), (inner1.right - 3, inner1.top + 1), 2)
    pygame.draw.line(surface, SV_WOOD_HI, (inner1.left + 1, inner1.top + 2), (inner1.left + 1, inner1.bottom - 3), 2)
    # Bottom and right chestnut shadow
    pygame.draw.line(surface, SV_WOOD_SH, (inner1.left + 2, inner1.bottom - 2), (inner1.right - 3, inner1.bottom - 2), 2)
    pygame.draw.line(surface, SV_WOOD_SH, (inner1.right - 2, inner1.top + 2), (inner1.right - 2, inner1.bottom - 3), 2)

    # 3. Inner dark line
    inner2 = inner1.inflate(-10, -10)
    pygame.draw.rect(surface, SV_WOOD_DARK, inner2, border_radius=max(2, corner_radius - 3))

    # 4. Parchment background
    inner3 = inner2.inflate(-2, -2)
    bg_color = SV_PARCHMENT if not is_inset else SV_PARCHMENT_INSET
    pygame.draw.rect(surface, bg_color, inner3, border_radius=max(1, corner_radius - 4))

    # Inner parchment shadow (top and left)
    pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner3.left, inner3.top), (inner3.right - 1, inner3.top), 2)
    pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner3.left, inner3.top), (inner3.left, inner3.bottom - 1), 2)

    # 5. Brass Corner Rivets
    rivet_size = 6
    corners = [
        (r.left + 5, r.top + 5),
        (r.right - 5 - rivet_size, r.top + 5),
        (r.left + 5, r.bottom - 5 - rivet_size),
        (r.right - 5 - rivet_size, r.bottom - 5 - rivet_size),
    ]
    for cx, cy in corners:
        pygame.draw.rect(surface, SV_WOOD_DARK, (cx, cy, rivet_size, rivet_size))
        pygame.draw.rect(surface, SV_WOOD_RIVET, (cx + 1, cy + 1, rivet_size - 2, rivet_size - 2))
        pygame.draw.rect(surface, SV_WOOD_SH, (cx + 2, cy + 2, rivet_size - 4, rivet_size - 4))


def draw_stardew_grid_border(surface, grid_rect):
    """
    Renders an authentic Stardew Valley timber border framing the meadow grid canvas,
    matching the aesthetic of HUD cards and menus.
    """
    r = pygame.Rect(grid_rect.x - 8, grid_rect.y - 8, grid_rect.w + 16, grid_rect.h + 16)

    # 1. Outer dark timber border
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=8)

    # 2. Beveled Golden Wood Frame
    inner1 = r.inflate(-4, -4)
    pygame.draw.rect(surface, SV_WOOD_MAIN, inner1, border_radius=6)

    # Top and left golden oak highlight
    pygame.draw.line(surface, SV_WOOD_HI, (inner1.left + 2, inner1.top + 1), (inner1.right - 3, inner1.top + 1), 2)
    pygame.draw.line(surface, SV_WOOD_HI, (inner1.left + 1, inner1.top + 2), (inner1.left + 1, inner1.bottom - 3), 2)
    # Bottom and right chestnut shadow
    pygame.draw.line(surface, SV_WOOD_SH, (inner1.left + 2, inner1.bottom - 2), (inner1.right - 3, inner1.bottom - 2), 2)
    pygame.draw.line(surface, SV_WOOD_SH, (inner1.right - 2, inner1.top + 2), (inner1.right - 2, inner1.bottom - 3), 2)

    # 3. Inner dark boundary outline enclosing the meadow
    inner2 = inner1.inflate(-10, -10)
    pygame.draw.rect(surface, SV_WOOD_DARK, inner2, border_radius=4)

    # 4. Brass Corner Rivets
    rivet_size = 7
    corners = [
        (r.left + 5, r.top + 5),
        (r.right - 5 - rivet_size, r.top + 5),
        (r.left + 5, r.bottom - 5 - rivet_size),
        (r.right - 5 - rivet_size, r.bottom - 5 - rivet_size),
    ]
    for cx, cy in corners:
        pygame.draw.rect(surface, SV_WOOD_DARK, (cx, cy, rivet_size, rivet_size))
        pygame.draw.rect(surface, SV_WOOD_RIVET, (cx + 1, cy + 1, rivet_size - 2, rivet_size - 2))
        pygame.draw.rect(surface, SV_WOOD_SH, (cx + 2, cy + 2, rivet_size - 4, rivet_size - 4))


def draw_stardew_slot(surface, rect):
    """Renders a 3D recessed parchment item slot / telemetry tile."""
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=4)
    inner = r.inflate(-2, -2)
    pygame.draw.rect(surface, SV_PARCHMENT_INSET, inner, border_radius=3)
    # Recessed shadow top/left
    pygame.draw.line(surface, SV_INSET_SHADOW, (inner.left, inner.top), (inner.right - 1, inner.top), 2)
    pygame.draw.line(surface, SV_INSET_SHADOW, (inner.left, inner.top), (inner.left, inner.bottom - 1), 2)
    # Recessed highlight bottom/right
    pygame.draw.line(surface, SV_INSET_HI, (inner.left, inner.bottom - 1), (inner.right - 1, inner.bottom - 1), 1)
    pygame.draw.line(surface, SV_INSET_HI, (inner.right - 1, inner.top), (inner.right - 1, inner.bottom - 1), 1)


def draw_stardew_bar(surface, x, y, width, height, current, max_val, bar_type='energy'):
    """
    Renders an iconic Stardew Valley gauge bar with wooden casing,
    deep recessed soil groove, and 3D glossy highlight fill.
    """
    r = pygame.Rect(x, y, width, height)
    # Outer dark casing
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=5)
    # Inner dark groove
    groove = r.inflate(-4, -4)
    pygame.draw.rect(surface, (68, 38, 18), groove, border_radius=3)
    # Fill
    ratio = min(1.0, max(0.0, current / max(1, max_val)))
    if ratio > 0:
        fill_w = max(4, int(groove.w * ratio))
        fill_rect = pygame.Rect(groove.x, groove.y, fill_w, groove.h)
        if bar_type == 'energy':
            c_main = SV_ENERGY_MAIN
            c_hi = SV_ENERGY_HI
            c_sh = SV_ENERGY_SH
        else:  # nectar
            c_main = SV_NECTAR_MAIN
            c_hi = SV_NECTAR_HI
            c_sh = SV_NECTAR_SH

        pygame.draw.rect(surface, c_main, fill_rect, border_radius=3)
        # 3D gloss line on top
        pygame.draw.line(surface, c_hi, (fill_rect.left + 1, fill_rect.top + 1), (fill_rect.right - 2, fill_rect.top + 1), 2)
        # 3D shadow on bottom
        pygame.draw.line(surface, c_sh, (fill_rect.left + 1, fill_rect.bottom - 2), (fill_rect.right - 2, fill_rect.bottom - 2), 2)


def draw_glass_rect(surface, color_rgba, rect, border_radius=0, border_color=None, border_width=1):
    """Draws a translucent rectangle with optional border and border radius."""
    r = pygame.Rect(rect)
    if len(color_rgba) == 4 and color_rgba[3] < 255:
        shape_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(shape_surf, color_rgba, (0, 0, r.w, r.h), border_radius=border_radius)
        surface.blit(shape_surf, (r.x, r.y))
    else:
        pygame.draw.rect(surface, color_rgba[:3], r, border_radius=border_radius)

    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, r, width=border_width, border_radius=border_radius)


class Button:
    """Stardew-themed tactile wooden button with hover, active, and danger styling."""

    def __init__(self, rect, label, is_danger=False, is_benchmark=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.is_danger = is_danger
        self.is_benchmark = is_benchmark
        self.active = False
        self.hovered = False

    def draw(self, surface, font):
        r = self.rect
        if self.active:
            c_fill = SV_BTN_ACTIVE_FILL
            c_hi = SV_BTN_ACTIVE_HI
            c_sh = SV_BTN_ACTIVE_SH
            t_col = (255, 255, 255)
            s_col = (24, 60, 18)
        elif self.is_danger:
            if self.hovered:
                c_fill = (215, 60, 52)
                c_hi = (245, 110, 105)
                c_sh = (140, 32, 26)
            else:
                c_fill = SV_BTN_DANGER_FILL
                c_hi = SV_BTN_DANGER_HI
                c_sh = SV_BTN_DANGER_SH
            t_col = (255, 248, 240)
            s_col = (54, 15, 12)
        elif self.is_benchmark:
            if self.hovered:
                c_fill = (145, 75, 190)
                c_hi = (185, 120, 235)
                c_sh = (95, 45, 130)
            else:
                c_fill = SV_BTN_BENCH_FILL
                c_hi = SV_BTN_BENCH_HI
                c_sh = SV_BTN_BENCH_SH
            t_col = (255, 248, 240)
            s_col = (45, 18, 65)
        elif self.hovered:
            c_fill = SV_BTN_HOVER_FILL
            c_hi = SV_BTN_HOVER_HI
            c_sh = SV_BTN_HOVER_SH
            t_col = (255, 255, 245)
            s_col = (54, 26, 12)
        else:
            c_fill = SV_BTN_NORMAL_FILL
            c_hi = SV_BTN_NORMAL_HI
            c_sh = SV_BTN_NORMAL_SH
            t_col = (255, 250, 235)
            s_col = (54, 26, 12)

        # Draw outer dark outline
        pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=6)

        # Inner wood fill
        b_inner = r.inflate(-4, -4)
        pygame.draw.rect(surface, c_fill, b_inner, border_radius=4)

        # 3D Bevel
        if self.active:
            # Inset pressed bevel
            pygame.draw.line(surface, c_sh, (b_inner.left + 1, b_inner.top + 1), (b_inner.right - 2, b_inner.top + 1), 2)
            pygame.draw.line(surface, c_sh, (b_inner.left + 1, b_inner.top + 1), (b_inner.left + 1, b_inner.bottom - 2), 2)
            pygame.draw.line(surface, c_hi, (b_inner.left + 1, b_inner.bottom - 2), (b_inner.right - 2, b_inner.bottom - 2), 2)
            pygame.draw.line(surface, c_hi, (b_inner.right - 2, b_inner.top + 1), (b_inner.right - 2, b_inner.bottom - 2), 2)
        else:
            # Raised button bevel
            pygame.draw.line(surface, c_hi, (b_inner.left + 1, b_inner.top + 1), (b_inner.right - 2, b_inner.top + 1), 2)
            pygame.draw.line(surface, c_hi, (b_inner.left + 1, b_inner.top + 1), (b_inner.left + 1, b_inner.bottom - 2), 2)
            pygame.draw.line(surface, c_sh, (b_inner.left + 1, b_inner.bottom - 2), (b_inner.right - 2, b_inner.bottom - 2), 2)
            pygame.draw.line(surface, c_sh, (b_inner.right - 2, b_inner.top + 1), (b_inner.right - 2, b_inner.bottom - 2), 2)

        # Label with Stardew text shadow
        tw = font.size(self.label)[0]
        th = font.size(self.label)[1]
        tx = r.x + (r.w - tw) // 2
        ty = r.y + (r.h - th) // 2
        if self.active:
            tx += 1
            ty += 1
        draw_text_shadow(surface, self.label, font, t_col, s_col, (tx, ty), (1, 2))

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class Dropdown:
    """Stardew-styled selection dropdown menu."""

    def __init__(self, rect, options, selected_idx=0):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.selected_idx = selected_idx
        self.is_open = False
        self.hovered_option = -1
        self.item_height = 48

    def draw(self, surface, font):
        r = self.rect
        # Outer dark timber
        pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=6)
        inner = r.inflate(-4, -4)
        pygame.draw.rect(surface, SV_PARCHMENT, inner, border_radius=4)

        # 3D inner inset
        pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner.left, inner.top), (inner.right - 1, inner.top), 2)
        pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner.left, inner.top), (inner.left, inner.bottom - 1), 2)

        label = self.options[self.selected_idx][1]
        draw_text_shadow(surface, label, font, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (r.x + 16, r.y + (r.h - font.get_height()) // 2), (0, 1))

        # Wooden arrow button on the right
        btn_w = 40
        btn_r = pygame.Rect(r.right - btn_w - 4, r.top + 4, btn_w, r.h - 8)
        pygame.draw.rect(surface, SV_WOOD_DARK, btn_r, border_radius=4)
        btn_inner = btn_r.inflate(-2, -2)
        pygame.draw.rect(surface, SV_WOOD_MAIN, btn_inner, border_radius=3)
        pygame.draw.line(surface, SV_WOOD_HI, (btn_inner.left, btn_inner.top), (btn_inner.right - 1, btn_inner.top), 1)
        pygame.draw.line(surface, SV_WOOD_HI, (btn_inner.left, btn_inner.top), (btn_inner.left, btn_inner.bottom - 1), 1)
        pygame.draw.line(surface, SV_WOOD_SH, (btn_inner.left, btn_inner.bottom - 1), (btn_inner.right - 1, btn_inner.bottom - 1), 1)
        pygame.draw.line(surface, SV_WOOD_SH, (btn_inner.right - 1, btn_inner.top), (btn_inner.right - 1, btn_inner.bottom - 1), 1)

        ax = btn_r.centerx
        ay = btn_r.centery
        if self.is_open:
            pygame.draw.polygon(surface, (255, 235, 160), [(ax - 6, ay + 4), (ax + 6, ay + 4), (ax, ay - 4)])
            pygame.draw.polygon(surface, SV_WOOD_DARK, [(ax - 6, ay + 4), (ax + 6, ay + 4), (ax, ay - 4)], 1)
        else:
            pygame.draw.polygon(surface, (255, 235, 160), [(ax - 6, ay - 4), (ax + 6, ay - 4), (ax, ay + 4)])
            pygame.draw.polygon(surface, SV_WOOD_DARK, [(ax - 6, ay - 4), (ax + 6, ay - 4), (ax, ay + 4)], 1)

        if self.is_open:
            menu_h = len(self.options) * self.item_height + 12
            menu_rect = pygame.Rect(r.x, r.y - menu_h - 4, r.w, menu_h)

            # Draw Stardew frame for popup menu
            draw_stardew_frame(surface, menu_rect, is_inset=False, corner_radius=6)

            for i, (_, opt_label) in enumerate(self.options):
                opt_rect = pygame.Rect(menu_rect.x + 8, menu_rect.y + 6 + (i * self.item_height), menu_rect.w - 16, self.item_height - 2)
                if i == self.hovered_option:
                    pygame.draw.rect(surface, SV_BTN_HOVER_FILL, opt_rect, border_radius=4)
                    pygame.draw.rect(surface, SV_WOOD_DARK, opt_rect, width=1, border_radius=4)
                    draw_text_shadow(surface, opt_label, font, (255, 255, 245), SV_WOOD_DARK, (opt_rect.x + 12, opt_rect.y + (opt_rect.h - font.get_height()) // 2), (1, 1))
                elif i == self.selected_idx:
                    pygame.draw.rect(surface, (245, 195, 85), opt_rect, border_radius=4)
                    pygame.draw.rect(surface, (190, 125, 25), opt_rect, width=1, border_radius=4)
                    draw_text_shadow(surface, opt_label, font, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (opt_rect.x + 12, opt_rect.y + (opt_rect.h - font.get_height()) // 2), (0, 1))
                else:
                    draw_text_shadow(surface, opt_label, font, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (opt_rect.x + 12, opt_rect.y + (opt_rect.h - font.get_height()) // 2), (0, 1))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.is_open:
            menu_h = len(self.options) * self.item_height + 12
            menu_y = self.rect.y - menu_h - 4
            for i in range(len(self.options)):
                opt_rect = pygame.Rect(self.rect.x + 8, menu_y + 6 + (i * self.item_height), self.rect.w - 16, self.item_height - 2)
                if opt_rect.collidepoint(event.pos):
                    self.hovered_option = i
                    return
            self.hovered_option = -1
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            if self.is_open:
                menu_h = len(self.options) * self.item_height + 12
                menu_y = self.rect.y - menu_h - 4
                for i in range(len(self.options)):
                    opt_rect = pygame.Rect(self.rect.x + 8, menu_y + 6 + (i * self.item_height), self.rect.w - 16, self.item_height - 2)
                    if opt_rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        return i
                self.is_open = False
        return None
