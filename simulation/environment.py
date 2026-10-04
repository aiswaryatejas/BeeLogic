import random, copy

GRID_COLS, GRID_ROWS = 20, 15

class Flower:
    def __init__(self, flower_id, x, y, nectar):
        self.id, self.x, self.y, self.nectar, self.max_nectar, self.depleted = flower_id, x, y, nectar, nectar, False

    def is_available(self):
        return not self.depleted and self.nectar > 0

    def harvest(self, amount):
        if self.depleted: return 0
        taken = min(amount, self.nectar)
        self.nectar -= taken
        if self.nectar <= 0: self.nectar, self.depleted = 0, True
        return taken

    def pos(self):
        return (self.x, self.y)

    def __repr__(self):
        return f"Flower(id={self.id}, pos=({self.x},{self.y}), nectar={self.nectar}, depleted={self.depleted})"

class Environment:
    def __init__(self, seed=42, cols=GRID_COLS, rows=GRID_ROWS):
        self.seed, self.cols, self.rows, self.hive, self.obstacles, self.flowers = seed, cols, rows, (1, 1), set(), []
        self._generate(seed)

    def _generate(self, seed):
        rng = random.Random(seed)
        occupied = {self.hive}
        num_obstacles = rng.randint(14, 20)
        attempts = 0
        while len(self.obstacles) < num_obstacles and attempts < 2000:
            attempts += 1
            pos = (rng.randint(0, self.cols - 1), rng.randint(0, self.rows - 1))
            if pos not in occupied:
                self.obstacles.add(pos)
                occupied.add(pos)
        num_flowers = rng.randint(9, 12)
        fid, attempts = 1, 0
        while len(self.flowers) < num_flowers and attempts < 2000:
            attempts += 1
            x, y = rng.randint(0, self.cols - 1), rng.randint(0, self.rows - 1)
            if (x, y) not in occupied:
                self.flowers.append(Flower(fid, x, y, rng.randint(10, 60)))
                occupied.add((x, y))
                fid += 1

    def is_blocked(self, x, y):
        return x < 0 or x >= self.cols or y < 0 or y >= self.rows or (x, y) in self.obstacles

    def available_flowers(self):
        return [f for f in self.flowers if f.is_available()]

    def get_flower_at(self, x, y):
        return next((f for f in self.flowers if f.x == x and f.y == y), None)

    def get_flower_by_id(self, flower_id):
        return next((f for f in self.flowers if f.id == flower_id), None)

    def trigger_dynamic_event(self, rng=None, target_flower=None):
        if target_flower and target_flower.is_available(): flower = target_flower
        else:
            avail = self.available_flowers()
            if not avail: return None
            flower = (rng or random).choice(avail)
        flower.nectar, flower.depleted = 0, True
        return flower

    def clone(self):
        return copy.deepcopy(self)
