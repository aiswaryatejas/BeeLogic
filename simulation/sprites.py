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

    def __init__(self, base_dir=None, cell_size=64):
        self.cell_size = cell_size
        if base_dir is None:
            # Default to repo root sprites/
            self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sprites")
        else:
            self.base_dir = base_dir

        self.flowers = {}
        self.flowers_depleted = {}
        self.bee_anims = {}
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

        self._loaded = True

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
