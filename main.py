"""
main.py
-------
Core entry point for BeeLogic Classical AI simulation and search algorithms.
Coordinates simulation execution, algorithmic decision models, comparative
benchmarking, and GUI visualization.
"""

import sys
import argparse

from simulation.environment import Environment
from simulation.bee import Bee
from simulation.decision import (
    SimulationController,
    STRATEGY_NEAREST,
    STRATEGY_GREEDY,
    STRATEGY_INTELLIGENT,
    STRATEGY_LABELS,
)
from analysis.comparison import run_comparison, print_table, save_chart
from ui import run_gui, BeeLogicApp


def run_simulation(
    seed=42,
    strategy=STRATEGY_INTELLIGENT,
    max_steps=400,
    event_step=45,
    verbose=True,
):
    """
    Executes a single simulation run using the selected decision algorithm.

    Args:
        seed: Random seed for deterministic environment generation.
        strategy: Strategy name ('nearest', 'greedy', or 'intelligent').
        max_steps: Maximum allowable simulation time steps.
        event_step: Step number at which a dynamic depletion event triggers.
        verbose: If True, prints a summary of the simulation results.

    Returns:
        dict: Final metrics and telemetry of the bee agent.
    """
    env = Environment(seed=seed)
    bee = Bee(hive_pos=env.hive, max_steps=max_steps)
    controller = SimulationController(env, bee, strategy, event_step=event_step)

    safety_cap = max_steps * 20
    ticks = 0
    while not bee.finished and ticks < safety_cap:
        controller.tick()
        ticks += 1

    metrics = {
        "strategy": strategy,
        "label": STRATEGY_LABELS.get(strategy, strategy),
        "seed": seed,
        "nectar_collected": bee.total_nectar_collected,
        "distance_travelled": bee.distance_travelled,
        "energy_consumed": bee.energy_consumed,
        "flowers_visited": bee.flowers_visited,
        "time_steps": bee.time_steps,
        "efficiency": bee.efficiency(),
    }

    if verbose:
        print("=" * 60)
        print(f" BeeLogic Simulation Run: {metrics['label']}")
        print("=" * 60)
        print(f" Environment Seed   : {seed}")
        print(f" Nectar Collected   : {metrics['nectar_collected']} units")
        print(f" Distance Travelled : {metrics['distance_travelled']} steps")
        print(f" Energy Consumed    : {metrics['energy_consumed']} units")
        print(f" Flowers Visited    : {metrics['flowers_visited']}")
        print(f" Total Time Steps   : {metrics['time_steps']} / {max_steps}")
        print(f" Efficiency Ratio   : {metrics['efficiency']:.3f} (Nectar / Distance)")
        print("=" * 60)

    return metrics


def run_benchmark(seed=42, max_steps=400, event_step=45, chart_path="out/comparison_chart.png"):
    """
    Runs an empirical benchmark comparing all three decision strategies
    (Nearest Neighbor BFS, Highest Nectar Greedy, Intelligent A*) on
    identical environments and prints a comparison table.

    Args:
        seed: Random seed for deterministic environment generation.
        max_steps: Maximum allowable simulation time steps.
        event_step: Step number to trigger dynamic flower depletion.
        chart_path: Path to save the visual comparison chart (or None to skip).

    Returns:
        list[dict]: Benchmark results for each strategy.
    """
    print(f"\nRunning BeeLogic Strategy Benchmark (Seed: {seed}, Max Steps: {max_steps})...\n")
    results = run_comparison(seed=seed, max_steps=max_steps, event_step=event_step)
    print_table(results)

    if chart_path:
        try:
            save_chart(results, path=chart_path)
            print(f"\nChart successfully saved to: {chart_path}")
        except Exception as e:
            print(f"\nWarning: Could not save chart image: {e}")

    return results


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="BeeLogic: Classical AI Foraging Agent Simulation & Search Algorithms"
    )
    parser.add_argument(
        "--cli",
        "--headless",
        action="store_true",
        help="Run simulation directly in terminal without launching the GUI visualizer.",
    )
    parser.add_argument(
        "--benchmark",
        "--compare",
        action="store_true",
        help="Run multi-strategy comparison benchmark across all algorithms.",
    )
    parser.add_argument(
        "--strategy",
        "-s",
        type=str,
        default=STRATEGY_INTELLIGENT,
        choices=[STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT],
        help="Search and decision strategy to run (default: intelligent).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for environment generation (default: 42).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=400,
        help="Maximum simulation steps (default: 400).",
    )
    parser.add_argument(
        "--event-step",
        type=int,
        default=45,
        help="Step at which dynamic flower depletion occurs (default: 45).",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=3.0,
        help="Initial GUI playback speed multiplier (default: 3.0).",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Run GUI in windowed mode instead of fullscreen.",
    )
    parser.add_argument(
        "--chart-path",
        type=str,
        default="out/comparison_chart.png",
        help="Path for saving benchmark comparison plot (default: out/comparison_chart.png).",
    )
    return parser.parse_args()


def main():
    """Main application dispatcher."""
    args = parse_args()

    if args.benchmark:
        run_benchmark(
            seed=args.seed,
            max_steps=args.steps,
            event_step=args.event_step,
            chart_path=args.chart_path,
        )
    elif args.cli:
        run_simulation(
            seed=args.seed,
            strategy=args.strategy,
            max_steps=args.steps,
            event_step=args.event_step,
            verbose=True,
        )
    else:
        # Launch Interactive Pygame GUI by default
        run_gui(
            seed=args.seed,
            fullscreen=not args.windowed,
            initial_strategy=args.strategy,
            initial_speed=args.speed,
            max_steps=args.steps,
            event_step=args.event_step,
        )


if __name__ == "__main__":
    main()