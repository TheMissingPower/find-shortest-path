"""The grid rules, shared by the tools and the verifier: verifier/grid.py is a byte-for-byte copy.

A grid is a tuple of equal-length rows; each character is a digit 0-9, the cost of entering that open
cell, or # for a wall. A cell is (row, col), 0-indexed from the top left. A path moves up, down, left
or right, one cell a step, never onto a wall or off the grid, and never visits a cell twice. Its cost
is the sum of the costs of every cell on it, the start and the target included.

Pure standard library and nothing the verifier may not import: there is no heapq, so Dijkstra takes
the next cell by a scan, smallest (cost, row, col) first, which is fast enough for grids of at most
10 x 10 and makes the example path the same on every run.
"""

import hashlib
import json

WALL = "#"
MAX_SIDE = 10
# up, right, down, left
MOVES = ((-1, 0), (0, 1), (1, 0), (0, -1))


def size(grid):
    return len(grid), len(grid[0])


def in_bounds(grid, cell):
    row, col = cell
    rows, cols = size(grid)
    return 0 <= row < rows and 0 <= col < cols


def is_open(grid, cell):
    return in_bounds(grid, cell) and grid[cell[0]][cell[1]] != WALL


def cell_cost(grid, cell):
    return int(grid[cell[0]][cell[1]])


def neighbors(grid, cell):
    """The open cells one move from ``cell``, in the order up, right, down, left."""
    row, col = cell
    steps = ((row + dr, col + dc) for dr, dc in MOVES)
    return [step for step in steps if is_open(grid, step)]


def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def path_cost(grid, path):
    return sum(cell_cost(grid, cell) for cell in path)


def grid_problem(grid, start, target):
    """Why a puzzle is malformed, or None: a rectangle of at most 10 x 10 digits and walls, open start and target."""
    if not grid or not grid[0]:
        return "the grid is empty"
    rows, cols = size(grid)
    if rows > MAX_SIDE or cols > MAX_SIDE:
        return f"the grid is {rows} x {cols}, larger than {MAX_SIDE} x {MAX_SIDE}"
    if any(len(line) != cols for line in grid):
        return "the grid's rows are not all the same length"
    if any(char != WALL and char not in "0123456789" for line in grid for char in line):
        return "the grid holds a character that is neither a digit nor #"
    for name, cell in (("start", start), ("target", target)):
        if not is_open(grid, cell):
            return f"the {name} {list(cell)} is not an open cell of the grid"
    return None


def solve(grid, start, target):
    """The minimum cost from start to target and one path of that cost, or (None, []) when unreachable."""
    if not is_open(grid, start) or not is_open(grid, target):
        return None, []
    best = {start: cell_cost(grid, start)}
    previous = {}
    done = set()
    while True:
        frontier = [(cost, cell) for cell, cost in best.items() if cell not in done]
        if not frontier:
            return None, []
        cost, cell = min(frontier)
        if cell == target:
            break
        done.add(cell)
        for step in neighbors(grid, cell):
            candidate = cost + cell_cost(grid, step)
            if step not in done and (step not in best or (candidate, cell) < (best[step], previous[step])):
                best[step] = candidate
                previous[step] = cell
    path = [target]
    while path[-1] != start:
        path.append(previous[path[-1]])
    return best[target], path[::-1]


def fingerprint(grid, start, target):
    """sha256 of the puzzle's canonical JSON: its grid rows, start and target."""
    canonical = json.dumps({"grid": list(grid), "start": list(start), "target": list(target)}, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
