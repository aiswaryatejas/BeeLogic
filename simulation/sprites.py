"""
sprites.py
----------
Sprite and animation manager for BeeLogic.
Loads, scales, caches, and provides sprites and animated frames for:
    - Spring Flowers (active and depleted/wilted states)
    - Animated Bee (Flying, Idle, Harvesting/Watering, Depositing/PutDown)
"""

import os
import pygame


class SpriteManager:
    """Loads and manages pixel-art sprites and animated strips for BeeLogic."""

    def __init__(self, base_dir=None, cell_size=64, window_size=(1920, 1080)):
        self.cell_size = cell_size
        self.window_size = window_size
        if base_dir is None:
            # Default to repo root sprites/
            self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sprites")
        else:
            self.base_dir = base_dir

        self.flowers = {}
        self.flowers_depleted = {}
        self.bee_anims = {}
        self.grass_tiles = []
        self.grass_detail_tiles = []
        self.grass_grid_surface = None
        self.stone_sprites = []
        self.backdrop_frames = []
        self.backdrop_durations = []
        self.backdrop_total_duration = 0.0
        self._loaded = False
        self.load_all()

    def _load_strip(self, rel_path, num_frames, target_size=None):
        if target_size is None:
            target_size = (int(self.cell_size * 0.82), int(self.cell_size * 0.92))
        path = os.path.join(self.base_dir, rel_path)
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        frame_w = w // num_frames
        frames = []
        for i in range(num_frames):
            frame_surf = img.subsurface(pygame.Rect(i * frame_w, 0, frame_w, h))
            scaled = pygame.transform.scale(frame_surf, target_size)
            frames.append(scaled)
        return frames

    def load_all(self):
        # --------------------------------------------------------------
        # 1. Spring Flowers (1.png to 12.png)
        # --------------------------------------------------------------
        target_f_size = int(self.cell_size * 0.75)
        for i in range(1, 13):
            path = os.path.join(self.base_dir, "SpringFlowers", f"{i}.png")
            img = pygame.image.load(path).convert_alpha()
            w, h = img.get_size()
            if w == h:
                scaled = pygame.transform.scale(img, (target_f_size, target_f_size))
            else:
                aspect = w / h
                if w > h:
                    scaled = pygame.transform.scale(img, (target_f_size, int(target_f_size / aspect)))
                else:
                    scaled = pygame.transform.scale(img, (int(target_f_size * aspect), target_f_size))

            self.flowers[i] = scaled

            # Depleted flower (grayscale + subtle transparency)
            gray = pygame.transform.grayscale(scaled)
            depleted = gray.copy()
            depleted.set_alpha(150)
            self.flowers_depleted[i] = depleted

        # --------------------------------------------------------------
        # 2. Bee Animations
        # --------------------------------------------------------------
        bee_size = (int(self.cell_size * 0.82), int(self.cell_size * 0.92))

        # Flying (6 frames each direction)
        fly_down = self._load_strip(os.path.join("Bee", "Flying", "FlyDown.png"), 6, bee_size)
        fly_left = self._load_strip(os.path.join("Bee", "Flying", "FlyLeft.png"), 6, bee_size)
        fly_right = self._load_strip(os.path.join("Bee", "Flying", "FlyRight.png"), 6, bee_size)
        fly_up = self._load_strip(os.path.join("Bee", "Flying", "flyUp.png"), 6, bee_size)

        self.bee_anims["fly"] = {
            "down": fly_down,
            "left": fly_left,
            "right": fly_right,
            "up": fly_up,
        }

        # Idle (4-5 frames each direction)
        idle_down = self._load_strip(os.path.join("Bee", "Idle", "IdleDown.png"), 4, bee_size)
        idle_left = self._load_strip(os.path.join("Bee", "Idle", "IdleLeft.png"), 4, bee_size)
        idle_right = self._load_strip(os.path.join("Bee", "Idle", "IdleRight.png"), 4, bee_size)
        idle_up = self._load_strip(os.path.join("Bee", "Idle", "IdleUp.png"), 5, bee_size)

        self.bee_anims["idle"] = {
            "down": idle_down,
            "left": idle_left,
            "right": idle_right,
            "up": idle_up,
        }

        # Harvesting / Watering (11 frames)
        harv_down = self._load_strip(os.path.join("Bee", "watering", "wateringDown.png"), 11, bee_size)
        harv_left = self._load_strip(os.path.join("Bee", "watering", "wateringLeft.png"), 11, bee_size)
        harv_right = self._load_strip(os.path.join("Bee", "watering", "wateringRight.png"), 11, bee_size)
        harv_up = [pygame.transform.flip(f, True, False) for f in harv_down]

        self.bee_anims["harvest"] = {
            "down": harv_down,
            "left": harv_left,
            "right": harv_right,
            "up": harv_up,
        }

        # Depositing / PutDown (6 frames)
        dep_down = self._load_strip(os.path.join("Bee", "PutDown", "PutDownDown.png"), 6, bee_size)
        dep_left = self._load_strip(os.path.join("Bee", "PutDown", "PutDownLeft.png"), 6, bee_size)
        dep_up = self._load_strip(os.path.join("Bee", "PutDown", "PutDownUp.png"), 6, bee_size)
        dep_right = [pygame.transform.flip(f, True, False) for f in dep_left]

        self.bee_anims["deposit"] = {
            "down": dep_down,
            "left": dep_left,
            "right": dep_right,
            "up": dep_up,
        }

        # --------------------------------------------------------------
        # 3. Grass Sprites (grass.png)
        # --------------------------------------------------------------
        self._load_grass()

        # --------------------------------------------------------------
        # 4. Stone Obstacle Sprites (stone.png / stone.jpg)
        # --------------------------------------------------------------
        self._load_stone()

        # --------------------------------------------------------------
        # 5. Animated Waterfall Backdrop
        # --------------------------------------------------------------
        self.load_backdrop(target_size=self.window_size)

        self._loaded = True

    def _load_grass(self):
        """Loads grass pixel-art tiles from grass.png and prepares tile variants."""
        paths_to_try = [
            os.path.join(self.base_dir, "grass.png"),
            os.path.join(self.base_dir, "grass.jpg"),
        ]
        grass_path = next((p for p in paths_to_try if os.path.exists(p)), None)
        self.grass_tiles = []
        self.grass_detail_tiles = []

        if grass_path:
            try:
                grass_img = pygame.image.load(grass_path).convert_alpha()
                gw, gh = grass_img.get_size()
                if gh >= 48 and gw >= 96:
                    for r in range(3):
                        for c in range(3, 6):
                            sub = grass_img.subsurface(pygame.Rect(c * 16, r * 16, 16, 16))
                            if c == 3:
                                self.grass_tiles.append(sub)
                            else:
                                self.grass_detail_tiles.append(sub)
                else:
                    scaled = pygame.transform.scale(grass_img, (self.cell_size, self.cell_size))
                    self.grass_tiles.append(scaled)
            except Exception as e:
                print(f"Warning: Could not load grass sprite '{grass_path}': {e}")

        if not self.grass_tiles:
            fallback = pygame.Surface((16, 16))
            fallback.fill((129, 186, 68))
            self.grass_tiles.append(fallback)
        if not self.grass_detail_tiles:
            self.grass_detail_tiles = list(self.grass_tiles)

    def get_grass_tile(self, gx=0, gy=0):
        """Returns a 64x64 grass cell surface constructed from grass sprite tiles."""
        cell_surf = pygame.Surface((self.cell_size, self.cell_size))
        sub_count = max(1, self.cell_size // 16)
        sub_size = self.cell_size // sub_count
        for sy in range(sub_count):
            for sx in range(sub_count):
                r_val = ((gx * 37 + gy * 73 + sx * 13 + sy * 29) % 100) / 100.0
                if r_val < 0.12 and self.grass_detail_tiles:
                    tile = self.grass_detail_tiles[(gx + gy + sx + sy) % len(self.grass_detail_tiles)]
                else:
                    tile = self.grass_tiles[(gx * 2 + gy + sx) % len(self.grass_tiles)]
                if tile.get_size() != (sub_size, sub_size):
                    tile = pygame.transform.scale(tile, (sub_size, sub_size))
                cell_surf.blit(tile, (sx * sub_size, sy * sub_size))
        return cell_surf

    def build_grass_grid_surface(self, cols=20, rows=15):
        """Builds and caches a seamless full-grid grass surface."""
        w = cols * self.cell_size
        h = rows * self.cell_size
        surf = pygame.Surface((w, h))
        sub_count = max(1, self.cell_size // 16)
        sub_size = self.cell_size // sub_count
        for gy in range(rows):
            for gx in range(cols):
                for sy in range(sub_count):
                    for sx in range(sub_count):
                        px = gx * self.cell_size + sx * sub_size
                        py = gy * self.cell_size + sy * sub_size
                        r_val = ((gx * 37 + gy * 73 + sx * 13 + sy * 29) % 100) / 100.0
                        if r_val < 0.12 and self.grass_detail_tiles:
                            tile = self.grass_detail_tiles[(gx + gy + sx + sy) % len(self.grass_detail_tiles)]
                        else:
                            tile = self.grass_tiles[(gx * 2 + gy + sx) % len(self.grass_tiles)]
                        if tile.get_size() != (sub_size, sub_size):
                            tile = pygame.transform.scale(tile, (sub_size, sub_size))
                        surf.blit(tile, (px, py))
        self.grass_grid_surface = surf
        return surf

    def get_grass_grid_surface(self, cols=20, rows=15):
        """Returns the pre-rendered full grid grass surface (caching it if needed)."""
        if self.grass_grid_surface is None or self.grass_grid_surface.get_size() != (cols * self.cell_size, rows * self.cell_size):
            self.build_grass_grid_surface(cols, rows)
        return self.grass_grid_surface

    def _load_stone(self):
        """Loads and prepares stone obstacle sprites from stone.png or stone.jpg."""
        paths_to_try = [
            os.path.join(self.base_dir, "stone.png"),
            os.path.join(self.base_dir, "stone.jpg"),
            os.path.join(self.base_dir, "stone.jpeg"),
        ]
        stone_path = next((p for p in paths_to_try if os.path.exists(p)), None)
        self.stone_sprites = []
        target_size = (int(self.cell_size * 0.88), int(self.cell_size * 0.88))

        if stone_path:
            try:
                if stone_path.lower().endswith(".png"):
                    img = pygame.image.load(stone_path).convert_alpha()
                    scaled = pygame.transform.smoothscale(img, target_size)
                    self.stone_sprites.append(scaled)
                else:
                    from PIL import Image, ImageFilter
                    import numpy as np
                    from collections import deque

                    pil_img = Image.open(stone_path).convert("RGB")
                    pw, ph = pil_img.size

                    if pw > 1000 and ph > 1000:
                        crop_box = (int(pw * 0.50), int(ph * 0.45), int(pw * 0.63), int(ph * 0.56))
                        pil_crop = pil_img.crop(crop_box)
                    else:
                        pil_crop = pil_img

                    c_img = pil_crop.resize((256, 256), Image.Resampling.LANCZOS)
                    arr = np.array(c_img, dtype=np.float32)
                    is_bg = np.all(arr > 232, axis=-1)
                    h_s, w_s = is_bg.shape
                    visited = np.zeros((h_s, w_s), dtype=bool)
                    q = deque()
                    for y in range(h_s):
                        for x in [0, w_s - 1]:
                            if is_bg[y, x] and not visited[y, x]:
                                visited[y, x] = True
                                q.append((y, x))
                    for x in range(w_s):
                        for y in [0, h_s - 1]:
                            if is_bg[y, x] and not visited[y, x]:
                                visited[y, x] = True
                                q.append((y, x))
                    while q:
                        cy, cx = q.popleft()
                        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h_s and 0 <= nx < w_s and not visited[ny, nx] and is_bg[ny, nx]:
                                visited[ny, nx] = True
                                q.append((ny, nx))
                    alpha = np.where(visited, 0, 255).astype(np.uint8)
                    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.8))
                    alpha_arr = np.array(alpha_img, dtype=np.float32)
                    alpha_arr = np.clip((alpha_arr - 25) / (230 - 25) * 255.0, 0, 255).astype(np.uint8)
                    rgba = np.dstack([np.array(c_img, dtype=np.uint8), alpha_arr])
                    res_pil = Image.fromarray(rgba, "RGBA")
                    surf = pygame.image.fromstring(res_pil.tobytes(), res_pil.size, "RGBA")
                    scaled = pygame.transform.smoothscale(surf, target_size)
                    self.stone_sprites.append(scaled)
            except Exception as e:
                print(f"Warning: Could not load stone obstacle sprite '{stone_path}': {e}")

        if not self.stone_sprites:
            fallback = pygame.Surface(target_size, pygame.SRCALPHA)
            pygame.draw.rect(fallback, (100, 116, 139), (0, 0, target_size[0], target_size[1]), border_radius=8)
            pygame.draw.rect(fallback, (71, 85, 105), (0, 0, target_size[0], target_size[1]), width=2, border_radius=8)
            self.stone_sprites.append(fallback)

    def get_stone_sprite(self, obstacle_id=0):
        """Returns a stone obstacle sprite surface."""
        if not self.stone_sprites:
            return None
        return self.stone_sprites[obstacle_id % len(self.stone_sprites)]

    def load_backdrop(self, target_size=(1920, 1080)):
        """Loads and prepares animated backdrop frames from waterfall.gif."""
        paths_to_try = [
            os.path.join(self.base_dir, "waterfall.gif"),
            os.path.join(self.base_dir, "waterfal.gif"),
        ]
        gif_path = None
        for p in paths_to_try:
            if os.path.exists(p):
                gif_path = p
                break

        self.backdrop_frames = []
        self.backdrop_durations = []
        self.backdrop_total_duration = 0.0

        if gif_path:
            try:
                from PIL import Image, ImageSequence
                im = Image.open(gif_path)
                for frame in ImageSequence.Iterator(im):
                    rgba = frame.convert("RGBA")
                    surf = pygame.image.fromstring(rgba.tobytes(), rgba.size, "RGBA")
                    if target_size and surf.get_size() != target_size:
                        surf = pygame.transform.smoothscale(surf, target_size)
                    self.backdrop_frames.append(surf)
                    dur = frame.info.get("duration", 140) / 1000.0
                    if dur <= 0:
                        dur = 0.14
                    self.backdrop_durations.append(dur)
                self.backdrop_total_duration = sum(self.backdrop_durations)
            except Exception as e:
                print(f"Warning: Could not load animated backdrop GIF '{gif_path}': {e}")

    def get_backdrop_frame(self, anim_time):
        """Returns the current backdrop frame surface based on elapsed animation time."""
        if not self.backdrop_frames:
            return None
        if self.backdrop_total_duration <= 0:
            return self.backdrop_frames[0]
        
        t = anim_time % self.backdrop_total_duration
        elapsed = 0.0
        for frame, dur in zip(self.backdrop_frames, self.backdrop_durations):
            elapsed += dur
            if t <= elapsed:
                return frame
        return self.backdrop_frames[-1]

    def get_flower_sprite(self, flower_id, is_available=True):
        """Returns the flower surface for the given flower id."""
        idx = ((flower_id - 1) % 12) + 1
        return self.flowers[idx] if is_available else self.flowers_depleted[idx]

    def get_bee_frame(self, action, direction, anim_time):
        """
        Returns the appropriate animation frame for the bee given:
            - action: 'fly', 'idle', 'harvest', 'deposit'
            - direction: 'down', 'left', 'right', 'up'
            - anim_time: elapsed time in seconds (used to compute current frame index)
        """
        action_map = self.bee_anims.get(action, self.bee_anims["idle"])
        dir_frames = action_map.get(direction, action_map.get("down", action_map.get("right")))

        fps = 12 if action == "fly" else (10 if action == "harvest" else (8 if action == "deposit" else 5))
        frame_idx = int(anim_time * fps) % len(dir_frames)
        return dir_frames[frame_idx]
