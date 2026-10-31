"""An independent answer: Bellman-Ford over the grid's cells, written apart from plugin.grid (it shares
no code with it), so a bug in the shared Dijkstra cannot hide in both."""

from __future__ import annotations


def minimum_cost(grid: tuple[str, ...], start: tuple[int, int], target: tuple[int, int]) -> int | None:
    rows, cols = len(grid), len(grid[0])
    open_cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] != "#"]
    if start not in open_cells or target not in open_cells:
        return None
    best: dict[tuple[int, int], int] = {start: int(grid[start[0]][start[1]])}
    for _ in range(len(open_cells)):
        changed = False
        for (r, c), cost in list(best.items()):
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if (nr, nc) in open_cells:
                    candidate = cost + int(grid[nr][nc])
                    if candidate < best.get((nr, nc), candidate + 1):
                        best[(nr, nc)] = candidate
                        changed = True
        if not changed:
            break
    return best.get(target)
