import heapq

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar_path(env, start, goal):
    if start == goal:
        return [start]
    open_heap, g_score, came_from, closed = [(manhattan(start, goal), 0, start)], {start: 0}, {}, set()
    while open_heap:
        _, g, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        closed.add(current)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (current[0] + dx, current[1] + dy)
            if env.is_blocked(*nxt) or nxt in closed:
                continue
            tentative_g = g + 1
            if tentative_g < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative_g
                came_from[nxt] = current
                heapq.heappush(open_heap, (tentative_g + manhattan(nxt, goal), tentative_g, nxt))
    return None
