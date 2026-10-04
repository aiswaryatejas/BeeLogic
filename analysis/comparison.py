import os, sys, matplotlib
from pathlib import Path
matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path: sys.path.insert(0, str(ROOT_DIR))

from simulation.environment import Environment
from simulation.bee import Bee
from simulation.decision import SimulationController, STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT, STRATEGY_LABELS

STRATEGIES = [STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT]

def run_strategy(base_env_seed, strategy, max_steps=400, event_step=None):
    env, bee = Environment(seed=base_env_seed), Bee(hive_pos=(1, 1), max_steps=max_steps)
    controller = SimulationController(env, bee, strategy, event_step=event_step)
    safety, ticks = max_steps * 20, 0
    while not bee.finished and ticks < safety:
        controller.tick()
        ticks += 1
    return {
        "strategy": strategy, "label": STRATEGY_LABELS[strategy], "nectar_collected": bee.total_nectar_collected,
        "distance_travelled": bee.distance_travelled, "energy_consumed": bee.energy_consumed,
        "flowers_visited": bee.flowers_visited, "time_steps": bee.time_steps, "efficiency": bee.efficiency(),
    }

def run_comparison(seed=42, max_steps=400, event_step=None):
    return [run_strategy(seed, s, max_steps=max_steps, event_step=event_step) for s in STRATEGIES]

def print_table(results):
    h = f"{'Strategy':<26}{'Nectar':>8}{'Distance':>10}{'Energy':>9}{'Flowers':>9}{'Steps':>8}{'Efficiency':>12}"
    print(f"{h}\n{'-' * len(h)}")
    for r in results:
        print(f"{r['label']:<26}{r['nectar_collected']:>8}{r['distance_travelled']:>10}{r['energy_consumed']:>9}{r['flowers_visited']:>9}{r['time_steps']:>8}{r['efficiency']:>12.3f}")

def save_chart(results, path="out/comparison_chart.png"):
    if os.path.dirname(path): os.makedirs(os.path.dirname(path), exist_ok=True)
    labels, x = [r["label"] for r in results], np.arange(len(results))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.suptitle("BeeLogic - Strategy Comparison Benchmark")
    metrics = [("Nectar Collected", [r["nectar_collected"] for r in results]), ("Distance Travelled", [r["distance_travelled"] for r in results]), ("Energy Consumed", [r["energy_consumed"] for r in results]), ("Collection Efficiency (Nectar / Distance)", [r["efficiency"] for r in results])]
    for (title, values), ax in zip(metrics, axes.flat):
        ax.bar(x, values, color=["#5B8FB9", "#E0A458", "#6FBF73"])
        ax.set_title(title, fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(["Nearest", "Greedy", "Intelligent"], fontsize=8)
        for i, v in enumerate(values): ax.text(i, v, f"{v:.2f}" if isinstance(v, float) else str(v), ha="center", va="bottom", fontsize=8)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path

if __name__ == "__main__":
    res = run_comparison()
    print_table(res)
    print(f"\nChart saved to: {save_chart(res)}")