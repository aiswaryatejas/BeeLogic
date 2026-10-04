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
│   ├── environment.py          # Grid environment, obstacles & flower states
│   └── sprites.py              # Pixel art and animation sprite manager
├── ui/                         # User interface & visualizer package
│   ├── __init__.py             # Package exports (BeeLogicApp, run_gui)
│   ├── app.py                  # Pygame application loop & rendering pipeline
│   ├── theme.py                # Layout constants & Stardew aesthetic tokens
│   └── widgets.py              # Tactile buttons, dropdowns, and UI primitives
├── analysis/                   # Benchmarking & performance evaluation
│   └── comparison.py           # Multi-strategy benchmark runner & plotting
├── out/                        # Generated output assets (charts, plots)
│   └── comparison_chart.png    # Visual benchmark comparison results
├── main.py                     # Clean entry point: simulation & algorithm dispatcher
├── pyproject.toml              # Project configuration & dependencies
└── README.md
```

## Quick Start

### 1. Run Interactive GUI
Launch the Pygame visualization:
```bash
python main.py
```
*(Optional flags: `--windowed`, `--seed <int>`, `--speed <float>`, `--strategy <nearest|greedy|intelligent>`)*

### 2. Run Simulation via CLI (Headless)
Run the simulation directly in the terminal without opening a GUI window:
```bash
python main.py --cli --strategy intelligent
```

### 3. Run Benchmark Comparison
Run all 3 strategies under identical seeds and generate the comparison chart:
```bash
python main.py --benchmark
# or: python analysis/comparison.py
```
Output charts are saved directly to `out/comparison_chart.png`.

