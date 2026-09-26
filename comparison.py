"""
comparison.py
-------------
Runs all three strategies (Nearest Flower / Highest Nectar / Intelligent
Bee) on IDENTICAL copies of the same environment (same seed, same
dynamic event timing) so the comparison is fair, and measures REAL
results from the simulation -- nothing here is hardcoded.

Can be run standalone:
    python comparison.py

or imported and called from main.py when the user clicks
"Run Comparison" inside the Pygame app.
"""
from environment import Environment
from bee import Bee
from decision import (
    SimulationController,
    STRATEGY_NEAREST,
    STRATEGY_GREEDY,
    STRATEGY_INTELLIGENT,
    STRATEGY_LABELS,
)

STRATEGIES = [STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT]


def run_strategy(base_env_seed, strategy, max_steps=400, event_step=None):
    """Runs a single strategy to completion on a fresh environment built from the given seed."""
    env = Environment(seed=base_env_seed)
    bee = Bee(hive_pos=env.hive, max_steps=max_steps)
    controller = SimulationController(env, bee, strategy, event_step=event_step)

    safety_cap = max_steps * 20
    ticks = 0
    while not bee.finished and ticks < safety_cap:
        controller.tick()
        ticks += 1

    return {
        "strategy": strategy,
        "label": STRATEGY_LABELS[strategy],
        "nectar_collected": bee.total_nectar_collected,
        "distance_travelled": bee.distance_travelled,
        "energy_consumed": bee.energy_consumed,
        "flowers_visited": bee.flowers_visited,
        "time_steps": bee.time_steps,
        "efficiency": bee.efficiency(),
    }


def run_comparison(seed=42, max_steps=400, event_step=None):
    """Runs all three strategies and returns a list of result dicts."""
    results = []
    for strategy in STRATEGIES:
        results.append(run_strategy(seed, strategy, max_steps=max_steps, event_step=event_step))
    return results


def print_table(results):
    header = f"{'Strategy':<26}{'Nectar':>8}{'Distance':>10}{'Energy':>9}{'Flowers':>9}{'Steps':>8}{'Efficiency':>12}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['label']:<26}"
            f"{r['nectar_collected']:>8}"
            f"{r['distance_travelled']:>10}"
            f"{r['energy_consumed']:>9}"
            f"{r['flowers_visited']:>9}"
            f"{r['time_steps']:>8}"
            f"{r['efficiency']:>12.3f}"
        )


def save_chart(results, path="comparison_chart.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [r["label"] for r in results]
    nectar = [r["nectar_collected"] for r in results]
    distance = [r["distance_travelled"] for r in results]
    energy = [r["energy_consumed"] for r in results]
    efficiency = [r["efficiency"] for r in results]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.suptitle("BeeLogic - Strategy Comparison Benchmark")

    metrics = [
        ("Nectar Collected", nectar, axes[0][0]),
        ("Distance Travelled", distance, axes[0][1]),
        ("Energy Consumed", energy, axes[1][0]),
        ("Collection Efficiency (Nectar / Distance)", efficiency, axes[1][1]),
    ]

    colors = ["#5B8FB9", "#E0A458", "#6FBF73"]
    x = np.arange(len(labels))

    for title, values, ax in metrics:
        ax.bar(x, values, color=colors)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(["Nearest", "Greedy", "Intelligent"], fontsize=8)
        for i, v in enumerate(values):
            ax.text(i, v, f"{v:.2f}" if isinstance(v, float) else str(v),
                    ha="center", va="bottom", fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":
    results = run_comparison()
    print_table(results)
    chart_path = save_chart(results)
    print(f"\nChart saved to: {chart_path}")