"""
bfs.py
------
Breadth-First Search utilities.

Used for:
    1. Baseline "Nearest Flower" strategy -- picking whichever
       available flower has the smallest number of grid steps away.
    2. Generic shortest-path-by-steps queries (unweighted grid, so
       BFS gives a true shortest path just like A* would, but without
       the heuristic guidance -- good for teaching the contrast).
"""

from collections import deque


def bfs_path(env, start, goal):
    """
    Shortest path (list of (x,y) cells, including start and goal) from
    start to goal on the grid, avoiding obstacles. Returns None if no
    path exists.
    """
    if start == goal:
        return [start]

    visited = {start}
    queue = deque([start])
    parent = {}

    found = False
    while queue:
        current = queue.popleft()
        if current == goal:
            found = True
            break
        x, y = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if env.is_blocked(*nxt):
                continue
            if nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = current
            queue.append(nxt)

    if not found:
        return None

    # Reconstruct path from goal back to start
    path = [goal]
    node = goal
    while node != start:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


def bfs_nearest_flower(env, start, flowers):
    """
    Baseline "Nearest Flower" strategy.

    Computes the BFS shortest path from `start` to every available
    flower and returns the (flower, path) pair with the fewest steps.

    Returns (None, None) if no flower is reachable.
    """
    available = [f for f in flowers if f.is_available()]
    if not available:
        return None, None

    best_flower = None
    best_path = None
    best_dist = None

    for f in available:
        path = bfs_path(env, start, (f.x, f.y))
        if path is None:
            continue
        dist = len(path) - 1
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_flower = f
            best_path = path

    return best_flower, best_path
