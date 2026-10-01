"""
decision.py
-----------
This is the "brain" of the project. It contains:

    1. The heuristic used by the Intelligent Bee:
           score = effective_nectar / distance
       (higher score = more nectar reward per step of travel)

    2. Rule-based reasoning (classical AI production rules):
           IF flower is depleted            -> ignore it
           IF nectar capacity is full        -> return to hive
           IF energy too low for round trip  -> return to hive
           IF no suitable flower exists       -> return to hive / end
           IF environment changes             -> re-evaluate & re-plan

    3. SimulationController -- a single class that runs ONE strategy
       ("nearest" / "greedy" / "intelligent") step by step.
"""

from algorithms.bfs import bfs_path, bfs_nearest_flower
from algorithms.astar import astar_path

STRATEGY_NEAREST = "nearest"
STRATEGY_GREEDY = "greedy"
STRATEGY_INTELLIGENT = "intelligent"

STRATEGY_LABELS = {
    STRATEGY_NEAREST: "Nearest Flower (BFS)",
    STRATEGY_GREEDY: "Highest Nectar (Greedy)",
    STRATEGY_INTELLIGENT: "Intelligent Bee (Heuristic + A*)",
}


def heuristic_score(effective_nectar, distance):
    """
    Computes candidate score using a non-linear distance penalty exponent (1.5).
    This forces the agent to strongly favor high nectar density relative to distance travelled,
    maximizing the Nectar / Distance efficiency ratio.
    """
    distance = max(distance, 1)
    return effective_nectar / (distance ** 1.5)


def estimate_round_trip_energy(env, flower_pos, one_way_distance):
    return_path = bfs_path(env, flower_pos, env.hive)
    back_distance = (len(return_path) - 1) if return_path else one_way_distance
    return one_way_distance + back_distance


class SimulationController:
    def __init__(self, env, bee, strategy, event_step=None):
        self.env = env
        self.bee = bee
        self.strategy = strategy
        self.event_step = event_step
        self.event_triggered = False
        self.event_log = None

    def tick(self):
        bee = self.bee
        if bee.finished:
            return

        if bee.time_steps >= bee.max_steps:
            bee.finished = True
            bee.current_decision = "End"
            bee.reason = "Maximum simulation steps reached"
            return

        if bee.current_path and len(bee.current_path) > 1:
            bee.step_along_path()
            if len(bee.current_path) == 1:
                self._handle_arrival()
        else:
            self._handle_arrival()
            if not bee.finished:
                self._decide_next_target()

    def _trigger_environment_change(self):
        self.event_triggered = True
        flower = self.env.trigger_dynamic_event()
        if flower is not None:
            self.event_log = f"Environment changed: Flower {flower.id} became depleted!"
        else:
            self.event_log = "Environment changed."

        bee = self.bee
        if bee._target_flower is not None and not bee._target_flower.is_available():
            bee.current_path = []
            bee.current_target = None
            bee._target_flower = None

    def _handle_arrival(self):
        bee = self.bee
        if bee.current_target == "Hive" and bee.pos == bee.hive_pos:
            bee.deposit_at_hive()
            bee.current_target = None
            bee.current_path = []
            bee._target_flower = None
        elif bee._target_flower is not None and bee.pos == bee._target_flower.pos():
            flower = bee._target_flower
            taken = bee.harvest_flower(flower)
            bee.current_decision = f"Collected nectar from Flower {flower.id}"
            bee.reason = f"Took {taken} nectar (flower now {'depleted' if flower.depleted else 'has ' + str(flower.nectar) + ' left'})"
            bee.current_target = None
            bee.current_path = []
            bee._target_flower = None

    def _go_to_hive(self, reason):
        bee, env = self.bee, self.env
        path = astar_path(env, bee.pos, bee.hive_pos) or bfs_path(env, bee.pos, bee.hive_pos)
        bee.current_target = "Hive"
        bee.current_path = path if path else [bee.pos]
        bee._target_flower = None
        bee.current_decision = "Return to Hive"
        bee.reason = reason
        bee.evaluations = []  # Clear table when heading to hive

    def _end_simulation(self, reason):
        bee = self.bee
        bee.finished = True
        bee.current_target = None
        bee.current_path = []
        bee.current_decision = "End"
        bee.reason = reason
        bee.evaluations = []

    def _decide_next_target(self):
        bee, env = self.bee, self.env
        available = env.available_flowers()

        if bee.nectar >= bee.max_nectar_capacity:
            self._go_to_hive("Nectar capacity full")
            return

        if not available:
            if bee.pos == bee.hive_pos and bee.nectar == 0:
                self._end_simulation("No suitable flower exists - mission complete")
            else:
                self._go_to_hive("No available flowers remain")
            return

        if self.strategy == STRATEGY_NEAREST:
            self._decide_nearest(available)
        elif self.strategy == STRATEGY_GREEDY:
            self._decide_greedy(available)
        else:
            self._decide_intelligent(available)

    def _decide_nearest(self, available):
        bee, env = self.bee, self.env
        flower, path = bfs_nearest_flower(env, bee.pos, available)
        if flower is None:
            self._go_to_hive("No reachable flower")
            return

        distance = len(path) - 1
        needed = estimate_round_trip_energy(env, flower.pos(), distance)
        if needed > bee.energy:
            self._go_to_hive("Energy too low to safely reach flower and return")
            return

        bee._target_flower = flower
        bee.current_target = f"Flower {flower.id}"
        bee.current_path = path
        bee.current_decision = f"Move to Flower {flower.id} (Nearest Flower)"
        bee.reason = f"Closest available flower, distance {distance}"

        # Decision Matrix evaluation for Nearest
        bee.evaluations = [
            {"id": flower.id, "dist": distance, "nectar": flower.nectar, "score": 1.0 / max(1, distance), "selected": True}
        ]

    def _decide_greedy(self, available):
        bee, env = self.bee, self.env
        flower = max(available, key=lambda f: f.nectar)
        path = astar_path(env, bee.pos, flower.pos()) or bfs_path(env, bee.pos, flower.pos())
        if path is None:
            self._go_to_hive("No path to highest-nectar flower")
            return

        distance = len(path) - 1
        needed = estimate_round_trip_energy(env, flower.pos(), distance)
        if needed > bee.energy:
            self._go_to_hive("Energy too low to safely reach flower and return")
            return

        bee._target_flower = flower
        bee.current_target = f"Flower {flower.id}"
        bee.current_path = path
        bee.current_decision = f"Move to Flower {flower.id} (Highest Nectar)"
        bee.reason = f"Highest nectar available ({flower.nectar}), ignoring distance"

        # Decision Matrix evaluation for Greedy (top 4 candidates by nectar)
        bee.evaluations = [
            {"id": f.id, "dist": abs(f.x - bee.pos[0]) + abs(f.y - bee.pos[1]), "nectar": f.nectar, "score": float(f.nectar), "selected": (f.id == flower.id)}
            for f in sorted(available, key=lambda x: x.nectar, reverse=True)[:4]
        ]

    def _decide_intelligent(self, available):
        bee, env = self.bee, self.env

        best_flower = None
        best_path = None
        best_score = -1.0
        eval_list = []

        for f in available:
            # 1. Path from current position to candidate flower
            path = astar_path(env, bee.pos, f.pos()) or bfs_path(env, bee.pos, f.pos())
            if path is None:
                continue
            distance = len(path) - 1

            # 2. Verify energy budget for safe trip
            needed = estimate_round_trip_energy(env, f.pos(), distance)
            if needed > bee.energy:
                continue

            # 3. Path from candidate flower back to hive (Round-trip evaluation)
            return_path = bfs_path(env, f.pos(), bee.hive_pos)
            return_dist = (len(return_path) - 1) if return_path else distance
            total_effective_distance = distance + return_dist

            # 4. Cap nectar reward to available storage capacity
            remaining_capacity = bee.max_nectar_capacity - bee.nectar
            effective_nectar = min(f.nectar, remaining_capacity)

            # 5. Compute utility score using non-linear penalty on total effective distance
            score = heuristic_score(effective_nectar, total_effective_distance)

            eval_list.append({
                "id": f.id,
                "dist": distance,
                "nectar": f.nectar,
                "score": score,
                "selected": False
            })

            if score > best_score:
                best_score = score
                best_flower = f
                best_path = path

        if best_flower is None:
            self._go_to_hive("No flower reachable within a safe energy budget")
            return

        # Sort candidate list descending by score
        eval_list.sort(key=lambda x: x["score"], reverse=True)
        for item in eval_list:
            if item["id"] == best_flower.id:
                item["selected"] = True

        # Pass top candidate evaluations to bee for rendering in the Decision Matrix panel
        bee.evaluations = eval_list[:4]

        distance = len(best_path) - 1
        bee._target_flower = best_flower
        bee.current_target = f"Flower {best_flower.id}"
        bee.current_path = best_path
        bee.current_decision = f"Move to Flower {best_flower.id} (Intelligent Bee)"
        bee.reason = f"Best score {best_score:.2f} (nectar {best_flower.nectar}, distance {distance})"