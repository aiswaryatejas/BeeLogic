"""
environment.py
----------------
Defines the 2D grid world for BeeLogic:
    - Hive location
    - Flowers (with nectar amount + availability state)
    - Obstacles
    - Helper queries used by BFS / A* / decision logic

This module contains ONLY environment/state representation.
No pathfinding or decision-making logic lives here (see bfs.py,
astar.py, decision.py) -- this keeps the "state representation"
requirement of the project cleanly separated.
"""

import random
import copy

GRID_COLS = 20
GRID_ROWS = 15


class Flower:
    """A single flower cell in the environment."""

    def __init__(self, flower_id, x, y, nectar):
        self.id = flower_id
        self.x = x
        self.y = y
        self.nectar = nectar
        self.max_nectar = nectar
        self.depleted = False

    def is_available(self):
        return (not self.depleted) and self.nectar > 0

    def harvest(self, amount):
        """Remove up to `amount` nectar from the flower. Returns amount taken."""
        if self.depleted:
            return 0
        taken = min(amount, self.nectar)
        self.nectar -= taken
        if self.nectar <= 0:
            self.nectar = 0
            self.depleted = True
        return taken

    def pos(self):
        return (self.x, self.y)

    def __repr__(self):
        return f"Flower(id={self.id}, pos=({self.x},{self.y}), nectar={self.nectar}, depleted={self.depleted})"


class Environment:
    """
    Holds the full world state:
        - hive position
        - obstacle set
        - list of flowers
    Provides grid queries (blocked cells, available flowers, etc.)
    """

    def __init__(self, seed=42, cols=GRID_COLS, rows=GRID_ROWS):
        self.seed = seed
        self.cols = cols
        self.rows = rows
        self.hive = (1, 1)
        self.obstacles = set()
        self.flowers = []
        self._generate(seed)

    # ------------------------------------------------------------------
    # World generation
    # ------------------------------------------------------------------
    def _generate(self, seed):
        rng = random.Random(seed)
        occupied = {self.hive}

        # --- Obstacles ---
        num_obstacles = rng.randint(14, 20)
        attempts = 0
        while len(self.obstacles) < num_obstacles and attempts < 2000:
            attempts += 1
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if (x, y) in occupied:
                continue
            self.obstacles.add((x, y))
            occupied.add((x, y))

        # --- Flowers ---
        num_flowers = rng.randint(9, 12)
        fid = 1
        attempts = 0
        while len(self.flowers) < num_flowers and attempts < 2000:
            attempts += 1
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if (x, y) in occupied:
                continue
            nectar = rng.randint(10, 60)
            self.flowers.append(Flower(fid, x, y, nectar))
            occupied.add((x, y))
            fid += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def is_blocked(self, x, y):
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return True
        return (x, y) in self.obstacles

    def available_flowers(self):
        return [f for f in self.flowers if f.is_available()]

    def get_flower_at(self, x, y):
        for f in self.flowers:
            if f.x == x and f.y == y:
                return f
        return None

    def get_flower_by_id(self, flower_id):
        for f in self.flowers:
            if f.id == flower_id:
                return f
        return None

    # ------------------------------------------------------------------
    # Dynamic environment change
    # ------------------------------------------------------------------
    def trigger_dynamic_event(self, rng=None, target_flower=None):
        """
        Deplete a specific flower or randomly deplete one currently-available flower
        to simulate a change in the environment (e.g. another forager emptied it, or
        it wilted). Returns the affected Flower, or None if there were
        no available flowers left to affect.
        """
        if target_flower is not None and target_flower.is_available():
            flower = target_flower
        else:
            rng = rng or random
            available = self.available_flowers()
            if not available:
                return None
            flower = rng.choice(available)
        flower.nectar = 0
        flower.depleted = True
        return flower

    def clone(self):
        """Deep copy of the environment (used so each strategy in the
        comparison runs on an identical, independent copy of the world)."""
        return copy.deepcopy(self)
