class Bee:
    def __init__(self, hive_pos, max_energy=180, max_nectar_capacity=90, max_steps=400):
        self.hive_pos, self.pos, self.prev_pos = hive_pos, hive_pos, hive_pos
        self.facing, self.activity = "right", "idle"
        self.max_energy, self.energy = max_energy, max_energy
        self.max_nectar_capacity, self.nectar, self.total_nectar_collected = max_nectar_capacity, 0, 0
        self.distance_travelled, self.energy_consumed, self.flowers_visited, self.time_steps, self.max_steps = 0, 0, 0, 0, max_steps
        self.current_target, self.current_path, self._target_flower = None, [], None
        self.current_decision, self.reason = "Idle", "Waiting to start"
        self.finished, self.at_hive = False, True

    def step_along_path(self):
        if len(self.current_path) < 2: return False
        nxt = self.current_path[1]
        dx, dy = nxt[0] - self.pos[0], nxt[1] - self.pos[1]
        self.facing = "right" if dx > 0 else "left" if dx < 0 else "down" if dy > 0 else "up" if dy < 0 else self.facing
        self.activity, self.prev_pos, self.pos = "fly", self.pos, nxt
        self.current_path.pop(0)
        self.distance_travelled, self.energy_consumed, self.time_steps = self.distance_travelled + 1, self.energy_consumed + 1, self.time_steps + 1
        self.energy, self.at_hive = max(0, self.energy - 1), (self.pos == self.hive_pos)
        return True

    def harvest_flower(self, flower):
        self.activity = "harvest"
        taken = flower.harvest(self.max_nectar_capacity - self.nectar)
        self.nectar += taken
        if taken > 0: self.flowers_visited += 1
        return taken

    def deposit_at_hive(self):
        self.activity, self.total_nectar_collected, self.nectar, self.energy = "deposit", self.total_nectar_collected + self.nectar, 0, self.max_energy

    def efficiency(self):
        return round(self.total_nectar_collected / self.distance_travelled, 3) if self.distance_travelled else 0.0

    def status_dict(self):
        return {
            "energy": self.energy, "max_energy": self.max_energy, "nectar": self.nectar,
            "max_nectar_capacity": self.max_nectar_capacity, "total_nectar_collected": self.total_nectar_collected,
            "distance": self.distance_travelled, "flowers_visited": self.flowers_visited,
            "time_steps": self.time_steps, "max_steps": self.max_steps, "target": self.current_target,
            "decision": self.current_decision, "reason": self.reason, "finished": self.finished,
        }
