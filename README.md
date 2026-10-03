# BeeLogic: Classical AI Foraging Agent Simulation

An interactive Classical AI simulation comparing search algorithms and decision-making strategies (Nearest Flower BFS, Highest Nectar Greedy, and Heuristic A* Intelligent Foraging) in an obstacle-laden grid world.

## Project Structure

```text
BeeLogic/
├── algorithms/                 # Pathfinding & search algorithms
│   ├── astar.py                # A* search with Manhattan heuristic
│   └── bfs.py                  # Breadth-First Search utilities
├── simulation/                 # World state and agent simulation
│   ├── bee.py                  # Bee agent state, mechanics & telemetry
│   ├── decision.py             # Decision engine, production rules & controller
│   └── environment.py          # Grid environment, obstacles & flower states
├── analysis/                   # Benchmarking & performance evaluation
│   └── comparison.py           # Multi-strategy benchmark runner & plotting
├── out/                        # Generated output assets (charts, plots)
│   └── comparison_chart.png    # Visual benchmark comparison results
├── main.py                     # Interactive Pygame visualizer & GUI
├── pyproject.toml              # Project configuration & dependencies
└── README.md
```

## Quick Start

### 1. Run Interactive GUI
Launch the Pygame visualization:
```bash
python main.py
```

### 2. Run Benchmark Comparison (CLI)
Run all 3 strategies under identical seeds and generate the comparison chart:
```bash
python analysis/comparison.py
```
Output charts are saved directly to `out/comparison_chart.png`.
