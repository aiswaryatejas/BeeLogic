import pygame
from ui.theme import (
    SV_WOOD_DARK, SV_WOOD_MAIN, SV_WOOD_HI, SV_WOOD_SH, SV_WOOD_RIVET, SV_WOOD_HEADER,
    SV_PARCHMENT, SV_PARCHMENT_LIGHT, SV_PARCHMENT_DARK, SV_PARCHMENT_INSET, SV_INSET_SHADOW, SV_INSET_HI,
    SV_TEXT_DARK, SV_TEXT_MUTED, SV_TEXT_LIGHT, SV_TEXT_SHADOW, SV_TEXT_HI_SHADOW,
    SV_ENERGY_MAIN, SV_ENERGY_HI, SV_ENERGY_SH, SV_NECTAR_MAIN, SV_NECTAR_HI, SV_NECTAR_SH,
    SV_BTN_NORMAL_FILL, SV_BTN_NORMAL_HI, SV_BTN_NORMAL_SH, SV_BTN_HOVER_FILL, SV_BTN_HOVER_HI, SV_BTN_HOVER_SH,
    SV_BTN_ACTIVE_FILL, SV_BTN_ACTIVE_HI, SV_BTN_ACTIVE_SH, SV_BTN_DANGER_FILL, SV_BTN_DANGER_HI, SV_BTN_DANGER_SH,
    SV_BTN_BENCH_FILL, SV_BTN_BENCH_HI, SV_BTN_BENCH_SH,
)

def draw_text_shadow(surface, text, font, color, shadow_color, pos, offset=(1, 1)):
    surface.blit(font.render(text, True, shadow_color), (pos[0] + offset[0], pos[1] + offset[1]))
    t_surf = font.render(text, True, color)
    surface.blit(t_surf, pos)
    return t_surf.get_width(), t_surf.get_height()

def _draw_bevel(surface, r, c_hi, c_sh, width=2):
    pygame.draw.line(surface, c_hi, (r.left + 2, r.top + 1), (r.right - 3, r.top + 1), width)
    pygame.draw.line(surface, c_hi, (r.left + 1, r.top + 2), (r.left + 1, r.bottom - 3), width)
    pygame.draw.line(surface, c_sh, (r.left + 2, r.bottom - 2), (r.right - 3, r.bottom - 2), width)
    pygame.draw.line(surface, c_sh, (r.right - 2, r.top + 2), (r.right - 2, r.bottom - 3), width)

def _draw_rivets(surface, r, size=6):
    for cx, cy in ((r.left + 5, r.top + 5), (r.right - 5 - size, r.top + 5), (r.left + 5, r.bottom - 5 - size), (r.right - 5 - size, r.bottom - 5 - size)):
        pygame.draw.rect(surface, SV_WOOD_DARK, (cx, cy, size, size))
        pygame.draw.rect(surface, SV_WOOD_RIVET, (cx + 1, cy + 1, size - 2, size - 2))
        pygame.draw.rect(surface, SV_WOOD_SH, (cx + 2, cy + 2, size - 4, size - 4))

def draw_stardew_frame(surface, rect, is_inset=False, corner_radius=6):
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=corner_radius)
    inner1 = r.inflate(-4, -4)
    pygame.draw.rect(surface, SV_WOOD_MAIN, inner1, border_radius=max(2, corner_radius - 2))
    _draw_bevel(surface, inner1, SV_WOOD_HI, SV_WOOD_SH, 2)
    inner2 = inner1.inflate(-10, -10)
    pygame.draw.rect(surface, SV_WOOD_DARK, inner2, border_radius=max(2, corner_radius - 3))
    inner3 = inner2.inflate(-2, -2)
    pygame.draw.rect(surface, SV_PARCHMENT if not is_inset else SV_PARCHMENT_INSET, inner3, border_radius=max(1, corner_radius - 4))
    pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner3.left, inner3.top), (inner3.right - 1, inner3.top), 2)
    pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner3.left, inner3.top), (inner3.left, inner3.bottom - 1), 2)
    _draw_rivets(surface, r, 6)

def draw_stardew_grid_border(surface, grid_rect):
    r = pygame.Rect(grid_rect.x - 8, grid_rect.y - 8, grid_rect.w + 16, grid_rect.h + 16)
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=8)
    inner1 = r.inflate(-4, -4)
    pygame.draw.rect(surface, SV_WOOD_MAIN, inner1, border_radius=6)
    _draw_bevel(surface, inner1, SV_WOOD_HI, SV_WOOD_SH, 2)
    inner2 = inner1.inflate(-10, -10)
    pygame.draw.rect(surface, SV_WOOD_DARK, inner2, border_radius=4)
    _draw_rivets(surface, r, 7)

def draw_stardew_slot(surface, rect):
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=4)
    inner = r.inflate(-2, -2)
    pygame.draw.rect(surface, SV_PARCHMENT_INSET, inner, border_radius=3)
    pygame.draw.line(surface, SV_INSET_SHADOW, (inner.left, inner.top), (inner.right - 1, inner.top), 2)
    pygame.draw.line(surface, SV_INSET_SHADOW, (inner.left, inner.top), (inner.left, inner.bottom - 1), 2)
    pygame.draw.line(surface, SV_INSET_HI, (inner.left, inner.bottom - 1), (inner.right - 1, inner.bottom - 1), 1)
    pygame.draw.line(surface, SV_INSET_HI, (inner.right - 1, inner.top), (inner.right - 1, inner.bottom - 1), 1)

def draw_stardew_bar(surface, x, y, width, height, current, max_val, bar_type='energy'):
    r = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=5)
    groove = r.inflate(-4, -4)
    pygame.draw.rect(surface, (68, 38, 18), groove, border_radius=3)
    ratio = min(1.0, max(0.0, current / max(1, max_val)))
    if ratio > 0:
        fill_rect = pygame.Rect(groove.x, groove.y, max(4, int(groove.w * ratio)), groove.h)
        c_main, c_hi, c_sh = (SV_ENERGY_MAIN, SV_ENERGY_HI, SV_ENERGY_SH) if bar_type == 'energy' else (SV_NECTAR_MAIN, SV_NECTAR_HI, SV_NECTAR_SH)
        pygame.draw.rect(surface, c_main, fill_rect, border_radius=3)
        pygame.draw.line(surface, c_hi, (fill_rect.left + 1, fill_rect.top + 1), (fill_rect.right - 2, fill_rect.top + 1), 2)
        pygame.draw.line(surface, c_sh, (fill_rect.left + 1, fill_rect.bottom - 2), (fill_rect.right - 2, fill_rect.bottom - 2), 2)

def draw_glass_rect(surface, color_rgba, rect, border_radius=0, border_color=None, border_width=1):
    r = pygame.Rect(rect)
    if len(color_rgba) == 4 and color_rgba[3] < 255:
        shape = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(shape, color_rgba, (0, 0, r.w, r.h), border_radius=border_radius)
        surface.blit(shape, (r.x, r.y))
    else:
        pygame.draw.rect(surface, color_rgba[:3], r, border_radius=border_radius)
    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, r, width=border_width, border_radius=border_radius)

class Button:
    def __init__(self, rect, label, is_danger=False, is_benchmark=False):
        self.rect, self.label, self.is_danger, self.is_benchmark = pygame.Rect(rect), label, is_danger, is_benchmark
        self.active = self.hovered = False

    def draw(self, surface, font):
        r = self.rect
        if self.active:
            fill, hi, sh, tc, sc = SV_BTN_ACTIVE_FILL, SV_BTN_ACTIVE_HI, SV_BTN_ACTIVE_SH, (255, 255, 255), (24, 60, 18)
        elif self.is_danger:
            fill, hi, sh = ((215, 60, 52), (245, 110, 105), (140, 32, 26)) if self.hovered else (SV_BTN_DANGER_FILL, SV_BTN_DANGER_HI, SV_BTN_DANGER_SH)
            tc, sc = (255, 248, 240), (54, 15, 12)
        elif self.is_benchmark:
            fill, hi, sh = ((145, 75, 190), (185, 120, 235), (95, 45, 130)) if self.hovered else (SV_BTN_BENCH_FILL, SV_BTN_BENCH_HI, SV_BTN_BENCH_SH)
            tc, sc = (255, 248, 240), (45, 18, 65)
        else:
            fill, hi, sh = (SV_BTN_HOVER_FILL, SV_BTN_HOVER_HI, SV_BTN_HOVER_SH) if self.hovered else (SV_BTN_NORMAL_FILL, SV_BTN_NORMAL_HI, SV_BTN_NORMAL_SH)
            tc, sc = ((255, 255, 245) if self.hovered else (255, 250, 235)), (54, 26, 12)
        pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=6)
        b_in = r.inflate(-4, -4)
        pygame.draw.rect(surface, fill, b_in, border_radius=4)
        _draw_bevel(surface, b_in, sh if self.active else hi, hi if self.active else sh, 2)
        tw, th = font.size(self.label)
        off = 1 if self.active else 0
        draw_text_shadow(surface, self.label, font, tc, sc, (r.x + (r.w - tw) // 2 + off, r.y + (r.h - th) // 2 + off), (1, 2))

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

class Dropdown:
    def __init__(self, rect, options, selected_idx=0):
        self.rect, self.options, self.selected_idx = pygame.Rect(rect), options, selected_idx
        self.is_open, self.hovered_option, self.item_height = False, -1, 48

    def draw(self, surface, font):
        r = self.rect
        pygame.draw.rect(surface, SV_WOOD_DARK, r, border_radius=6)
        inner = r.inflate(-4, -4)
        pygame.draw.rect(surface, SV_PARCHMENT, inner, border_radius=4)
        pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner.left, inner.top), (inner.right - 1, inner.top), 2)
        pygame.draw.line(surface, SV_PARCHMENT_DARK, (inner.left, inner.top), (inner.left, inner.bottom - 1), 2)
        draw_text_shadow(surface, self.options[self.selected_idx][1], font, SV_TEXT_DARK, SV_TEXT_HI_SHADOW, (r.x + 16, r.y + (r.h - font.get_height()) // 2), (0, 1))

        btn_r = pygame.Rect(r.right - 44, r.top + 4, 40, r.h - 8)
        pygame.draw.rect(surface, SV_WOOD_DARK, btn_r, border_radius=4)
        btn_in = btn_r.inflate(-2, -2)
        pygame.draw.rect(surface, SV_WOOD_MAIN, btn_in, border_radius=3)
        _draw_bevel(surface, btn_in, SV_WOOD_HI, SV_WOOD_SH, 1)

        ax, ay = btn_r.centerx, btn_r.centery
        poly = [(ax - 6, ay + 4), (ax + 6, ay + 4), (ax, ay - 4)] if self.is_open else [(ax - 6, ay - 4), (ax + 6, ay - 4), (ax, ay + 4)]
        pygame.draw.polygon(surface, (255, 235, 160), poly)
        pygame.draw.polygon(surface, SV_WOOD_DARK, poly, 1)

        if self.is_open:
            menu_h = len(self.options) * self.item_height + 12
            menu_rect = pygame.Rect(r.x, r.y - menu_h - 4, r.w, menu_h)
            draw_stardew_frame(surface, menu_rect, is_inset=False, corner_radius=6)
            for i, (_, opt_label) in enumerate(self.options):
                opt_r = pygame.Rect(menu_rect.x + 8, menu_rect.y + 6 + (i * self.item_height), menu_rect.w - 16, self.item_height - 2)
                is_h, is_s = (i == self.hovered_option), (i == self.selected_idx)
                if is_h or is_s:
                    pygame.draw.rect(surface, SV_BTN_HOVER_FILL if is_h else (245, 195, 85), opt_r, border_radius=4)
                    pygame.draw.rect(surface, SV_WOOD_DARK if is_h else (190, 125, 25), opt_r, width=1, border_radius=4)
                tc, sc = ((255, 255, 245), SV_WOOD_DARK) if is_h else (SV_TEXT_DARK, SV_TEXT_HI_SHADOW)
                draw_text_shadow(surface, opt_label, font, tc, sc, (opt_r.x + 12, opt_r.y + (opt_r.h - font.get_height()) // 2), (1 if is_h else 0, 1))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.is_open:
            menu_y = self.rect.y - (len(self.options) * self.item_height + 12) - 4
            for i in range(len(self.options)):
                if pygame.Rect(self.rect.x + 8, menu_y + 6 + (i * self.item_height), self.rect.w - 16, self.item_height - 2).collidepoint(event.pos):
                    self.hovered_option = i
                    return
            self.hovered_option = -1
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            if self.is_open:
                menu_y = self.rect.y - (len(self.options) * self.item_height + 12) - 4
                for i in range(len(self.options)):
                    if pygame.Rect(self.rect.x + 8, menu_y + 6 + (i * self.item_height), self.rect.w - 16, self.item_height - 2).collidepoint(event.pos):
                        self.selected_idx, self.is_open = i, False
                        return i
                self.is_open = False
        return None
