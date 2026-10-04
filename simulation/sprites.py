import os
import pygame

class SpriteManager:
    def __init__(self, base_dir=None, cell_size=64, window_size=(1920, 1080)):
        self.cell_size, self.window_size = cell_size, window_size
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sprites")
        self.flowers, self.flowers_depleted, self.bee_anims = {}, {}, {}
        self.grass_tiles, self.grass_detail_tiles, self.grass_grid_surface = [], [], None
        self.stone_sprites, self.backdrop_frames, self.backdrop_durations, self.backdrop_total_duration = [], [], [], 0.0
        self._loaded = False
        self.load_all()

    def _load_strip(self, rel_path, num_frames, target_size=None):
        target_size = target_size or (int(self.cell_size * 0.82), int(self.cell_size * 0.92))
        img = pygame.image.load(os.path.join(self.base_dir, rel_path)).convert_alpha()
        w, h = img.get_size()
        fw = w // num_frames
        return [pygame.transform.scale(img.subsurface(pygame.Rect(i * fw, 0, fw, h)), target_size) for i in range(num_frames)]

    def load_all(self):
        tfs = int(self.cell_size * 0.75)
        for i in range(1, 13):
            img = pygame.image.load(os.path.join(self.base_dir, "SpringFlowers", f"{i}.png")).convert_alpha()
            w, h = img.get_size()
            scaled = pygame.transform.scale(img, (tfs, tfs) if w == h else ((tfs, int(tfs / (w / h))) if w > h else (int(tfs * (w / h)), tfs)))
            self.flowers[i] = scaled
            dep = pygame.transform.grayscale(scaled).copy()
            dep.set_alpha(150)
            self.flowers_depleted[i] = dep

        bsize = (int(self.cell_size * 0.82), int(self.cell_size * 0.92))
        self.bee_anims["fly"] = {
            "down": self._load_strip(os.path.join("Bee", "Flying", "FlyDown.png"), 6, bsize),
            "left": self._load_strip(os.path.join("Bee", "Flying", "FlyLeft.png"), 6, bsize),
            "right": self._load_strip(os.path.join("Bee", "Flying", "FlyRight.png"), 6, bsize),
            "up": self._load_strip(os.path.join("Bee", "Flying", "flyUp.png"), 6, bsize),
        }
        self.bee_anims["idle"] = {
            "down": self._load_strip(os.path.join("Bee", "Idle", "IdleDown.png"), 4, bsize),
            "left": self._load_strip(os.path.join("Bee", "Idle", "IdleLeft.png"), 4, bsize),
            "right": self._load_strip(os.path.join("Bee", "Idle", "IdleRight.png"), 4, bsize),
            "up": self._load_strip(os.path.join("Bee", "Idle", "IdleUp.png"), 5, bsize),
        }
        h_down = self._load_strip(os.path.join("Bee", "watering", "wateringDown.png"), 11, bsize)
        self.bee_anims["harvest"] = {
            "down": h_down,
            "left": self._load_strip(os.path.join("Bee", "watering", "wateringLeft.png"), 11, bsize),
            "right": self._load_strip(os.path.join("Bee", "watering", "wateringRight.png"), 11, bsize),
            "up": [pygame.transform.flip(f, True, False) for f in h_down],
        }
        d_left = self._load_strip(os.path.join("Bee", "PutDown", "PutDownLeft.png"), 6, bsize)
        self.bee_anims["deposit"] = {
            "down": self._load_strip(os.path.join("Bee", "PutDown", "PutDownDown.png"), 6, bsize),
            "left": d_left,
            "right": [pygame.transform.flip(f, True, False) for f in d_left],
            "up": self._load_strip(os.path.join("Bee", "PutDown", "PutDownUp.png"), 6, bsize),
        }
        self._load_grass()
        self._load_stone()
        self.load_backdrop(target_size=self.window_size)
        self._loaded = True

    def _load_grass(self):
        paths = [os.path.join(self.base_dir, f"grass.{ext}") for ext in ("png", "jpg")]
        gp = next((p for p in paths if os.path.exists(p)), None)
        self.grass_tiles, self.grass_detail_tiles = [], []
        if gp:
            try:
                g = pygame.image.load(gp).convert_alpha()
                if g.get_height() >= 48 and g.get_width() >= 96:
                    for r in range(3):
                        for c in range(3, 6):
                            (self.grass_tiles if c == 3 else self.grass_detail_tiles).append(g.subsurface(pygame.Rect(c * 16, r * 16, 16, 16)))
                else:
                    self.grass_tiles.append(pygame.transform.scale(g, (self.cell_size, self.cell_size)))
            except Exception:
                pass
        if not self.grass_tiles:
            fb = pygame.Surface((16, 16))
            fb.fill((129, 186, 68))
            self.grass_tiles = [fb]
        self.grass_detail_tiles = self.grass_detail_tiles or list(self.grass_tiles)

    def get_grass_tile(self, gx=0, gy=0):
        cell_surf, sc = pygame.Surface((self.cell_size, self.cell_size)), max(1, self.cell_size // 16)
        ss = self.cell_size // sc
        for sy in range(sc):
            for sx in range(sc):
                r_val = ((gx * 37 + gy * 73 + sx * 13 + sy * 29) % 100) / 100.0
                tile = (self.grass_detail_tiles[(gx + gy + sx + sy) % len(self.grass_detail_tiles)] if r_val < 0.12 and self.grass_detail_tiles else self.grass_tiles[(gx * 2 + gy + sx) % len(self.grass_tiles)])
                if tile.get_size() != (ss, ss):
                    tile = pygame.transform.scale(tile, (ss, ss))
                cell_surf.blit(tile, (sx * ss, sy * ss))
        return cell_surf

    def build_grass_grid_surface(self, cols=20, rows=15):
        w, h = cols * self.cell_size, rows * self.cell_size
        surf, sc = pygame.Surface((w, h)), max(1, self.cell_size // 16)
        ss = self.cell_size // sc
        for gy in range(rows):
            for gx in range(cols):
                for sy in range(sc):
                    for sx in range(sc):
                        r_val = ((gx * 37 + gy * 73 + sx * 13 + sy * 29) % 100) / 100.0
                        tile = (self.grass_detail_tiles[(gx + gy + sx + sy) % len(self.grass_detail_tiles)] if r_val < 0.12 and self.grass_detail_tiles else self.grass_tiles[(gx * 2 + gy + sx) % len(self.grass_tiles)])
                        if tile.get_size() != (ss, ss):
                            tile = pygame.transform.scale(tile, (ss, ss))
                        surf.blit(tile, (gx * self.cell_size + sx * ss, gy * self.cell_size + sy * ss))
        self.grass_grid_surface = surf
        return surf

    def get_grass_grid_surface(self, cols=20, rows=15):
        if self.grass_grid_surface is None or self.grass_grid_surface.get_size() != (cols * self.cell_size, rows * self.cell_size):
            self.build_grass_grid_surface(cols, rows)
        return self.grass_grid_surface

    def _load_stone(self):
        paths = [os.path.join(self.base_dir, f"stone.{ext}") for ext in ("png", "jpg", "jpeg")]
        sp = next((p for p in paths if os.path.exists(p)), None)
        self.stone_sprites = []
        ts = (int(self.cell_size * 0.88), int(self.cell_size * 0.88))
        if sp:
            try:
                if sp.lower().endswith(".png"):
                    self.stone_sprites.append(pygame.transform.smoothscale(pygame.image.load(sp).convert_alpha(), ts))
                else:
                    from PIL import Image, ImageFilter
                    import numpy as np
                    from collections import deque
                    pimg = Image.open(sp).convert("RGB")
                    pw, ph = pimg.size
                    crop = pimg.crop((int(pw * 0.5), int(ph * 0.45), int(pw * 0.63), int(ph * 0.56))) if pw > 1000 and ph > 1000 else pimg
                    cimg = crop.resize((256, 256), Image.Resampling.LANCZOS)
                    arr = np.array(cimg, dtype=np.float32)
                    is_bg = np.all(arr > 232, axis=-1)
                    hs, ws = is_bg.shape
                    vis, q = np.zeros((hs, ws), dtype=bool), deque()
                    for y in range(hs):
                        for x in (0, ws - 1):
                            if is_bg[y, x] and not vis[y, x]:
                                vis[y, x], _ = True, q.append((y, x))
                    for x in range(ws):
                        for y in (0, hs - 1):
                            if is_bg[y, x] and not vis[y, x]:
                                vis[y, x], _ = True, q.append((y, x))
                    while q:
                        cy, cx = q.popleft()
                        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < hs and 0 <= nx < ws and not vis[ny, nx] and is_bg[ny, nx]:
                                vis[ny, nx], _ = True, q.append((ny, nx))
                    aimg = Image.fromarray(np.where(vis, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.8))
                    alpha = np.clip((np.array(aimg, dtype=np.float32) - 25) / 205 * 255.0, 0, 255).astype(np.uint8)
                    surf = pygame.image.fromstring(Image.fromarray(np.dstack([np.array(cimg, dtype=np.uint8), alpha]), "RGBA").tobytes(), (256, 256), "RGBA")
                    self.stone_sprites.append(pygame.transform.smoothscale(surf, ts))
            except Exception:
                pass
        if not self.stone_sprites:
            fb = pygame.Surface(ts, pygame.SRCALPHA)
            pygame.draw.rect(fb, (100, 116, 139), (0, 0, *ts), border_radius=8)
            pygame.draw.rect(fb, (71, 85, 105), (0, 0, *ts), width=2, border_radius=8)
            self.stone_sprites.append(fb)

    def get_stone_sprite(self, obstacle_id=0):
        return self.stone_sprites[obstacle_id % len(self.stone_sprites)] if self.stone_sprites else None

    def load_backdrop(self, target_size=(1920, 1080)):
        paths = [os.path.join(self.base_dir, f) for f in ("waterfall.gif", "waterfal.gif")]
        gp = next((p for p in paths if os.path.exists(p)), None)
        self.backdrop_frames, self.backdrop_durations, self.backdrop_total_duration = [], [], 0.0
        if gp:
            try:
                from PIL import Image, ImageSequence
                im = Image.open(gp)
                for f in ImageSequence.Iterator(im):
                    s = pygame.image.fromstring(f.convert("RGBA").tobytes(), f.size, "RGBA")
                    self.backdrop_frames.append(pygame.transform.smoothscale(s, target_size) if target_size and s.get_size() != target_size else s)
                    dur = f.info.get("duration", 140) / 1000.0
                    self.backdrop_durations.append(dur if dur > 0 else 0.14)
                self.backdrop_total_duration = sum(self.backdrop_durations)
            except Exception:
                pass

    def get_backdrop_frame(self, anim_time):
        if not self.backdrop_frames:
            return None
        if self.backdrop_total_duration <= 0:
            return self.backdrop_frames[0]
        t, elapsed = anim_time % self.backdrop_total_duration, 0.0
        for frame, dur in zip(self.backdrop_frames, self.backdrop_durations):
            elapsed += dur
            if t <= elapsed:
                return frame
        return self.backdrop_frames[-1]

    def get_flower_sprite(self, flower_id, is_available=True):
        idx = ((flower_id - 1) % 12) + 1
        return self.flowers[idx] if is_available else self.flowers_depleted[idx]

    def get_bee_frame(self, action, direction, anim_time):
        action_map = self.bee_anims.get(action, self.bee_anims["idle"])
        dir_frames = action_map.get(direction, action_map.get("down", action_map.get("right")))
        fps = 12 if action == "fly" else (10 if action == "harvest" else (8 if action == "deposit" else 5))
        return dir_frames[int(anim_time * fps) % len(dir_frames)]
