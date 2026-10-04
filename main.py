import sys, argparse
from simulation.environment import Environment
from simulation.bee import Bee
from simulation.decision import SimulationController, STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT, STRATEGY_LABELS
from analysis.comparison import run_comparison, print_table, save_chart
from ui import run_gui, BeeLogicApp

def run_simulation(seed=42, strategy=STRATEGY_INTELLIGENT, max_steps=400, event_step=45, verbose=True):
    env, bee = Environment(seed=seed), Bee(hive_pos=(1, 1), max_steps=max_steps)
    controller = SimulationController(env, bee, strategy, event_step=event_step)
    safety, ticks = max_steps * 20, 0
    while not bee.finished and ticks < safety:
        controller.tick()
        ticks += 1
    m = {
        "strategy": strategy, "label": STRATEGY_LABELS.get(strategy, strategy), "seed": seed,
        "nectar_collected": bee.total_nectar_collected, "distance_travelled": bee.distance_travelled,
        "energy_consumed": bee.energy_consumed, "flowers_visited": bee.flowers_visited,
        "time_steps": bee.time_steps, "efficiency": bee.efficiency(),
    }
    if verbose:
        print("=" * 60 + f"\n BeeLogic Simulation Run: {m['label']}\n" + "=" * 60)
        print(f" Environment Seed   : {seed}\n Nectar Collected   : {m['nectar_collected']} units\n Distance Travelled : {m['distance_travelled']} steps\n Energy Consumed    : {m['energy_consumed']} units\n Flowers Visited    : {m['flowers_visited']}\n Total Time Steps   : {m['time_steps']} / {max_steps}\n Efficiency Ratio   : {m['efficiency']:.3f} (Nectar / Distance)\n" + "=" * 60)
    return m

def run_benchmark(seed=42, max_steps=400, event_step=45, chart_path="out/comparison_chart.png"):
    print(f"\nRunning BeeLogic Strategy Benchmark (Seed: {seed}, Max Steps: {max_steps})...\n")
    results = run_comparison(seed=seed, max_steps=max_steps, event_step=event_step)
    print_table(results)
    if chart_path:
        try: save_chart(results, path=chart_path); print(f"\nChart successfully saved to: {chart_path}")
        except Exception as e: print(f"\nWarning: Could not save chart image: {e}")
    return results

def parse_args():
    p = argparse.ArgumentParser(description="BeeLogic: Classical AI Foraging Agent Simulation & Search Algorithms")
    p.add_argument("--cli", "--headless", action="store_true", help="Run simulation directly in terminal without GUI.")
    p.add_argument("--benchmark", "--compare", action="store_true", help="Run multi-strategy comparison benchmark.")
    p.add_argument("--strategy", "-s", type=str, default=STRATEGY_INTELLIGENT, choices=[STRATEGY_NEAREST, STRATEGY_GREEDY, STRATEGY_INTELLIGENT], help="Strategy to run.")
    p.add_argument("--seed", type=int, default=42, help="Random seed.")
    p.add_argument("--steps", type=int, default=400, help="Max simulation steps.")
    p.add_argument("--event-step", type=int, default=45, help="Step for dynamic depletion.")
    p.add_argument("--speed", type=float, default=3.0, help="Initial speed multiplier.")
    p.add_argument("--windowed", action="store_true", help="Run in windowed mode.")
    p.add_argument("--chart-path", type=str, default="out/comparison_chart.png", help="Path to save chart.")
    return p.parse_args()

def main():
    args = parse_args()
    if args.benchmark: run_benchmark(seed=args.seed, max_steps=args.steps, event_step=args.event_step, chart_path=args.chart_path)
    elif args.cli: run_simulation(seed=args.seed, strategy=args.strategy, max_steps=args.steps, event_step=args.event_step, verbose=True)
    else: run_gui(seed=args.seed, fullscreen=not args.windowed, initial_strategy=args.strategy, initial_speed=args.speed, max_steps=args.steps, event_step=args.event_step)

if __name__ == "__main__":
    main()