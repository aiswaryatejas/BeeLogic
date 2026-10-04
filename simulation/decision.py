from algorithms.bfs import bfs_path, bfs_nearest_flower
from algorithms.astar import astar_path

STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT = "nearest", "greedy", "intelligent"
STRATEGY_LABELS = {
    STRATEGY_NEAREST: "Nearest Flower (BFS)",
    STRATEGY_GREEDY: "Highest Nectar (Greedy)",
    STRATEGY_INTELLIGENT: "Intelligent Bee (Heuristic + A*)",
}

def heuristic_score(effective_nectar, distance):
    return effective_nectar / (max(distance, 1) ** 1.5)

def estimate_round_trip_energy(env, flower_pos, one_way_distance):
    return_path = bfs_path(env, flower_pos, env.hive)
    return one_way_distance + ((len(return_path) - 1) if return_path else one_way_distance)

class SimulationController:
    def __init__(self, env, bee, strategy, event_step=None):
        self.env, self.bee, self.strategy, self.event_step = env, bee, strategy, event_step
        self.event_triggered, self.event_log = False, None

    def tick(self):
        b = self.bee
        if b.finished:
            return
        if b.time_steps >= b.max_steps:
            b.finished, b.current_decision, b.reason = True, "End", "Maximum simulation steps reached"
            return
        if self.event_step is not None and b.time_steps >= self.event_step and not self.event_triggered:
            self.trigger_dynamic_event()
        if b._target_flower and not b._target_flower.is_available():
            dep_id = b._target_flower.id
            b.current_path, b.current_target, b._target_flower = [], None, None
            b.current_decision, b.reason = f"Redirecting (Flower #{dep_id} Depleted)", f"Target Flower #{dep_id} depleted mid-flight; re-evaluating optimal target"
            if not b.finished:
                self._decide_next_target()
        if b.current_path and len(b.current_path) > 1:
            b.step_along_path()
            if len(b.current_path) == 1:
                self._handle_arrival()
        else:
            self._handle_arrival()
            if not b.finished:
                self._decide_next_target()

    def trigger_dynamic_event(self, target_flower=None):
        self.event_triggered = True
        target = target_flower if target_flower and target_flower.is_available() else (self.bee._target_flower if self.bee._target_flower and self.bee._target_flower.is_available() else None)
        flower = self.env.trigger_dynamic_event(target_flower=target)
        self.event_log = f"Dynamic Event: Flower #{flower.id} became depleted!" if flower else "Dynamic Event: No available flowers to deplete."
        if self.bee._target_flower and not self.bee._target_flower.is_available():
            dep_id = self.bee._target_flower.id
            self.bee.current_path, self.bee.current_target, self.bee._target_flower = [], None, None
            self.bee.current_decision, self.bee.reason = f"Redirecting (Flower #{dep_id} Depleted)", f"Target Flower #{dep_id} depleted mid-flight; re-evaluating optimal target"
            if not self.bee.finished:
                self._decide_next_target()
        return flower

    def _trigger_environment_change(self):
        return self.trigger_dynamic_event()

    def _handle_arrival(self):
        b = self.bee
        if b.current_target == "Hive" and b.pos == b.hive_pos:
            b.deposit_at_hive()
            b.current_target, b.current_path, b._target_flower = None, [], None
        elif b._target_flower and b.pos == b._target_flower.pos():
            fl = b._target_flower
            taken = b.harvest_flower(fl)
            b.current_decision = f"Collected nectar from Flower {fl.id}"
            b.reason = f"Took {taken} nectar (flower now {'depleted' if fl.depleted else 'has ' + str(fl.nectar) + ' left'})"
            b.current_target, b.current_path, b._target_flower = None, [], None

    def _go_to_hive(self, reason):
        path = astar_path(self.env, self.bee.pos, self.bee.hive_pos) or bfs_path(self.env, self.bee.pos, self.bee.hive_pos)
        self.bee.current_target, self.bee.current_path, self.bee._target_flower = "Hive", (path or [self.bee.pos]), None
        self.bee.current_decision, self.bee.reason, self.bee.evaluations = "Return to Hive", reason, []

    def _end_simulation(self, reason):
        self.bee.finished, self.bee.current_target, self.bee.current_path = True, None, []
        self.bee.current_decision, self.bee.reason, self.bee.evaluations = "End", reason, []

    def _set_target(self, flower, path, decision, reason, evaluations=None):
        self.bee._target_flower, self.bee.current_target, self.bee.current_path = flower, f"Flower {flower.id}", path
        self.bee.current_decision, self.bee.reason = decision, reason
        self.bee.evaluations = evaluations or []

    def _decide_next_target(self):
        avail = self.env.available_flowers()
        if self.bee.nectar >= self.bee.max_nectar_capacity:
            return self._go_to_hive("Nectar capacity full")
        if not avail:
            return self._end_simulation("No suitable flower exists - mission complete") if self.bee.pos == self.bee.hive_pos and self.bee.nectar == 0 else self._go_to_hive("No available flowers remain")
        if self.strategy == STRATEGY_NEAREST:
            self._decide_nearest(avail)
        elif self.strategy == STRATEGY_GREEDY:
            self._decide_greedy(avail)
        else:
            self._decide_intelligent(avail)

    def _decide_nearest(self, available):
        flower, path = bfs_nearest_flower(self.env, self.bee.pos, available)
        if not flower:
            return self._go_to_hive("No reachable flower")
        dist = len(path) - 1
        if estimate_round_trip_energy(self.env, flower.pos(), dist) > self.bee.energy:
            return self._go_to_hive("Energy too low to safely reach flower and return")
        self._set_target(flower, path, f"Move to Flower {flower.id} (Nearest Flower)", f"Closest available flower, distance {dist}", [{"id": flower.id, "dist": dist, "nectar": flower.nectar, "score": 1.0 / max(1, dist), "selected": True}])

    def _decide_greedy(self, available):
        flower = max(available, key=lambda f: f.nectar)
        path = astar_path(self.env, self.bee.pos, flower.pos()) or bfs_path(self.env, self.bee.pos, flower.pos())
        if not path:
            return self._go_to_hive("No path to highest-nectar flower")
        dist = len(path) - 1
        if estimate_round_trip_energy(self.env, flower.pos(), dist) > self.bee.energy:
            return self._go_to_hive("Energy too low to safely reach flower and return")
        evals = [{"id": f.id, "dist": abs(f.x - self.bee.pos[0]) + abs(f.y - self.bee.pos[1]), "nectar": f.nectar, "score": float(f.nectar), "selected": (f.id == flower.id)} for f in sorted(available, key=lambda x: x.nectar, reverse=True)[:4]]
        self._set_target(flower, path, f"Move to Flower {flower.id} (Highest Nectar)", f"Highest nectar available ({flower.nectar}), ignoring distance", evals)

    def _decide_intelligent(self, available):
        best_f, best_p, best_s, evals = None, None, -1.0, []
        for f in available:
            path = astar_path(self.env, self.bee.pos, f.pos()) or bfs_path(self.env, self.bee.pos, f.pos())
            if not path:
                continue
            dist = len(path) - 1
            if estimate_round_trip_energy(self.env, f.pos(), dist) > self.bee.energy:
                continue
            ret = bfs_path(self.env, f.pos(), self.bee.hive_pos)
            score = heuristic_score(min(f.nectar, self.bee.max_nectar_capacity - self.bee.nectar), dist + ((len(ret) - 1) if ret else dist))
            evals.append({"id": f.id, "dist": dist, "nectar": f.nectar, "score": score, "selected": False})
            if score > best_s:
                best_s, best_f, best_p = score, f, path
        if not best_f:
            return self._go_to_hive("No flower reachable within a safe energy budget")
        evals.sort(key=lambda x: x["score"], reverse=True)
        for item in evals:
            item["selected"] = (item["id"] == best_f.id)
        self._set_target(best_f, best_p, f"Move to Flower {best_f.id} (Intelligent Bee)", f"Best score {best_s:.2f} (nectar {best_f.nectar}, distance {len(best_p) - 1})", evals[:4])