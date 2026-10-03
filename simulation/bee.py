"""
bee.py
------
Defines the Bee agent's internal state:
    position, energy, nectar, distance travelled, flowers visited,
    time/steps used, current target & path, and the reasoning trail
    that is shown to the user (current decision + reason).

Movement / harvesting mechanics live here; WHICH flower to choose and
WHEN to return to the hive is decided by decision.py -- this keeps a
clean split between "state + mechanics" (bee.py) and "intelligence"
(decision.py), matching the project's classical-AI structure.
"""


class Bee:
    def __init__(self, hive_pos, max_energy=180, max_nectar_capacity=90, max_steps=400):
        self.hive_pos = hive_pos
        self.pos = hive_pos
        self.prev_pos = hive_pos
        self.facing = "right"          # "down", "left", "right", "up"
        self.activity = "idle"         # "fly", "idle", "harvest", "deposit"

        self.max_energy = max_energy
        self.energy = max_energy

        self.max_nectar_capacity = max_nectar_capacity
        self.nectar = 0                 # currently carried nectar
        self.total_nectar_collected = 0  # deposited at hive (final score)

        self.distance_travelled = 0
        self.energy_consumed = 0
        self.flowers_visited = 0
        self.time_steps = 0
        self.max_steps = max_steps

        self.current_target = None      # e.g. "Flower 5" or "Hive"
        self.current_path = []          # list of (x,y) cells, path[0] == self.pos
        self._target_flower = None      # internal reference to the Flower object

        self.current_decision = "Idle"
        self.reason = "Waiting to start"

        self.finished = False
        self.at_hive = True

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def step_along_path(self):
        """Advance one grid cell along self.current_path. Returns True if moved."""
        if not self.current_path or len(self.current_path) < 2:
            return False

        next_cell = self.current_path[1]
        dx = next_cell[0] - self.pos[0]
        dy = next_cell[1] - self.pos[1]
        if dx > 0:
            self.facing = "right"
        elif dx < 0:
            self.facing = "left"
        elif dy > 0:
            self.facing = "down"
        elif dy < 0:
            self.facing = "up"
        self.activity = "fly"

        self.prev_pos = self.pos
        self.pos = next_cell
        self.current_path.pop(0)

        self.distance_travelled += 1
        self.energy = max(0, self.energy - 1)
        self.energy_consumed += 1
        self.time_steps += 1
        self.at_hive = (self.pos == self.hive_pos)
        return True

    # ------------------------------------------------------------------
    # Harvesting / depositing
    # ------------------------------------------------------------------
    def harvest_flower(self, flower):
        self.activity = "harvest"
        capacity_left = self.max_nectar_capacity - self.nectar
        taken = flower.harvest(capacity_left)
        self.nectar += taken
        if taken > 0:
            self.flowers_visited += 1
        return taken

    def deposit_at_hive(self):
        self.activity = "deposit"
        self.total_nectar_collected += self.nectar
        self.nectar = 0
        self.energy = self.max_energy  # recharge fully at the hive

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def efficiency(self):
        if self.distance_travelled == 0:
            return 0.0
        return round(self.total_nectar_collected / self.distance_travelled, 3)

    def status_dict(self):
        return {
            "energy": self.energy,
            "max_energy": self.max_energy,
            "nectar": self.nectar,
            "max_nectar_capacity": self.max_nectar_capacity,
            "total_nectar_collected": self.total_nectar_collected,
            "distance": self.distance_travelled,
            "flowers_visited": self.flowers_visited,
            "time_steps": self.time_steps,
            "max_steps": self.max_steps,
            "target": self.current_target,
            "decision": self.current_decision,
            "reason": self.reason,
            "finished": self.finished,
        }
