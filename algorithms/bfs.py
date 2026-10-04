from collections import deque

def bfs_path(env, start, goal):
    if start == goal:
        return [start]
    visited, queue, parent = {start}, deque([start]), {}
    while queue:
        current = queue.popleft()
        if current == goal:
            path, node = [goal], goal
            while node != start:
                node = parent[node]
                path.append(node)
            return path[::-1]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (current[0] + dx, current[1] + dy)
            if not env.is_blocked(*nxt) and nxt not in visited:
                visited.add(nxt)
                parent[nxt] = current
                queue.append(nxt)
    return None

def bfs_nearest_flower(env, start, flowers):
    best_flower, best_path, best_dist = None, None, float("inf")
    for f in (fl for fl in flowers if fl.is_available()):
        path = bfs_path(env, start, (f.x, f.y))
        if path and len(path) - 1 < best_dist:
            best_dist, best_flower, best_path = len(path) - 1, f, path
    return best_flower, best_path
