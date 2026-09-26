"""
astar.py
--------
A* Search implementation used by the Intelligent Bee (and the Greedy
baseline) to plan an efficient, obstacle-avoiding route once a target
flower or the hive has been selected.

Heuristic used: Manhattan distance (admissible for a 4-directional
grid where every move costs 1), which keeps A* fast and easy for a
2nd-year student to explain in a viva.
"""

import heapq


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_path(env, start, goal):
    """
    Returns the shortest path (list of (x,y) cells from start to goal,
    inclusive) avoiding obstacles, using A* search. Returns None if
    unreachable.
    """
    if start == goal:
        return [start]

    open_heap = []
    heapq.heappush(open_heap, (manhattan(start, goal), 0, start))

    g_score = {start: 0}
    came_from = {}
    closed = set()

    while open_heap:
        _, g, current = heapq.heappop(open_heap)

        if current in closed:
            continue
        if current == goal:
            return _reconstruct(came_from, current)
        closed.add(current)

        x, y = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (x + dx, y + dy)
            if env.is_blocked(*neighbor):
                continue
            if neighbor in closed:
                continue

            tentative_g = g + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_score = tentative_g + manhattan(neighbor, goal)
                heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

    return None  # no path found


def _reconstruct(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path
