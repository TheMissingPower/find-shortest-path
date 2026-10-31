"""Print the generated puzzles of src/plugin/puzzles.py: run once, by hand, and paste the output there.

The puzzle set is frozen in puzzles.py; nothing generates a puzzle at run time. Each puzzle here is
drawn from a fixed seed and kept only when its target is reachable and its cheapest path is not
just the fewest-steps one, so a breadth-first search alone does not solve it.

    uv run python src/plugin/tools_dev/make_puzzles.py
"""

import random

from plugin.grid import WALL, solve

# id, rows, cols, wall share, highest cost, seed
SPECS = [
    ("gen-5x5", 5, 5, 0.15, 9, 4801),
    ("gen-6x6", 6, 6, 0.20, 9, 4802),
    ("gen-7x7", 7, 7, 0.20, 9, 4803),
    ("gen-7x7-low-costs", 7, 7, 0.25, 3, 4804),
    ("gen-8x8", 8, 8, 0.20, 9, 4805),
    ("gen-8x8-dense-walls", 8, 8, 0.35, 9, 4806),
    ("gen-9x9", 9, 9, 0.20, 9, 4807),
    ("gen-10x10", 10, 10, 0.20, 9, 4808),
    ("gen-10x10-maze", 10, 10, 0.30, 5, 4809),
]


def fewest_steps_cost(grid, start, target):
    """The cost of the cheapest path among those with the fewest steps (a BFS answer at best)."""
    flat = tuple("1" if char != WALL else WALL for char in "".join(grid))
    cols = len(grid[0])
    unit = tuple("".join(flat[row * cols : (row + 1) * cols]) for row in range(len(grid)))
    steps, _ = solve(unit, start, target)
    best = None
    for path in _paths_of_length(grid, start, target, steps):
        cost = sum(int(grid[r][c]) for r, c in path)
        best = cost if best is None else min(best, cost)
    return best


def _paths_of_length(grid, start, target, length):
    def walk(path):
        if len(path) == length:
            if path[-1] == target:
                yield list(path)
            return
        row, col = path[-1]
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            step = (row + dr, col + dc)
            r, c = step
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] != WALL and step not in path:
                if abs(r - target[0]) + abs(c - target[1]) <= length - len(path) - 1:
                    yield from walk(path + [step])

    yield from walk([start])


def make(rows, cols, walls, high, seed):
    rng = random.Random(seed)

    def cell():
        return WALL if rng.random() < walls else str(rng.randint(0, high))

    while True:
        grid = tuple("".join(cell() for _ in range(cols)) for _ in range(rows))
        start, target = (0, 0), (rows - 1, cols - 1)
        if WALL in (grid[0][0], grid[-1][-1]):
            continue
        cost, _ = solve(grid, start, target)
        if cost is not None and cost < fewest_steps_cost(grid, start, target):
            return grid, start, target, cost


def main():
    for name, rows, cols, walls, high, seed in SPECS:
        grid, start, target, cost = make(rows, cols, walls, high, seed)
        print(f'    "{name}": {{')
        print(f'        "note": "Generated: {rows} x {cols}, about {round(walls * 100)}% walls, costs 0 to {high}.",')
        print('        "grid": (')
        for line in grid:
            print(f'            "{line}",')
        print("        ),")
        print(f'        "start": {start},')
        print(f'        "target": {target},')
        print(f"    }},  # minimum cost {cost}")


if __name__ == "__main__":
    main()
