"""Checks shared by the tool verifiers. Pure functions of their arguments."""

from .grid import adjacent, fingerprint, in_bounds, is_open, path_cost, solve
from .puzzles import PUZZLES


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def bundled(puzzle_id):
    """The bundled puzzle's grid, start and target, as the verifier's own copy of puzzles.py holds them."""
    entry = PUZZLES[puzzle_id.value]
    return entry["grid"], entry["start"], entry["target"]


def pair(cell):
    return (cell.row, cell.col)


def pairs(cells):
    return [pair(cell) for cell in cells]


def path_checks(grid, start, target, path):
    """The checks a non-empty path of (row, col) pairs must pass, in order: {id: (ok, message, actual)}.

    ok is None when the check needs one that failed (a wall can only be told on the grid).
    """
    checks = {}
    checks["starts-at-start"] = (
        (True, "", list(path[0]))
        if path[0] == start
        else (False, f"The path begins at {list(path[0])}, not at the start {list(start)}", list(path[0]))
    )
    checks["ends-at-target"] = (
        (True, "", list(path[-1]))
        if path[-1] == target
        else (False, f"The path ends at {list(path[-1])}, not at the target {list(target)}", list(path[-1]))
    )
    off = [list(cell) for cell in path if not in_bounds(grid, cell)]
    rows, cols = len(grid), len(grid[0])
    checks["in-bounds"] = (
        (True, "", None) if not off else (False, f"{_listed(off)} {_is(off)} off the {rows} x {cols} grid", off)
    )
    if off:
        checks["no-walls"] = (None, "Not checked: in-bounds did not hold.", None)
    else:
        walls = [list(cell) for cell in path if not is_open(grid, cell)]
        message = f"{_listed(walls)} {_is(walls)} a wall (#)"
        checks["no-walls"] = (True, "", None) if not walls else (False, message, walls)
    jumps = [[list(a), list(b)] for a, b in zip(path, path[1:]) if not adjacent(a, b)]
    checks["adjacent-steps"] = (
        (True, "", None)
        if not jumps
        else (
            False,
            f"{len(jumps)} step(s) are not one move up, down, left or right, "
            f"the first from {jumps[0][0]} to {jumps[0][1]}",
            jumps,
        )
    )
    seen, repeats = set(), []
    for cell in path:
        if cell in seen and list(cell) not in repeats:
            repeats.append(list(cell))
        seen.add(cell)
    checks["simple-path"] = (
        (True, "", None) if not repeats else (False, f"The path visits {_listed(repeats)} more than once", repeats)
    )
    return checks


def answer_key_problem(puzzle_id, pin):
    """Why ``pin`` is not the answer key of the bundled puzzle ``puzzle_id``, or None."""
    if pin is None:
        return "There is no answer key: pin_path's output is missing"
    if pin.puzzle_id != puzzle_id:
        return f"The answer key is for puzzle {pin.puzzle_id.value}, not {puzzle_id.value}"
    grid, start, target = bundled(puzzle_id)
    if tuple(pin.grid) != grid or pair(pin.start) != start or pair(pin.target) != target:
        return f"The answer key's grid, start or target is not the bundled puzzle {puzzle_id.value}'s"
    if pin.sha256 != fingerprint(grid, start, target):
        return "The answer key's sha256 is not the puzzle's"
    cost, _ = solve(grid, start, target)
    if pin.reachable != (cost is not None) or pin.optimal_cost != cost:
        return f"The answer key gives minimum cost {pin.optimal_cost}; the puzzle's is {cost}"
    path = pairs(pin.example_path)
    if cost is None:
        return None if not path else "The answer key gives a path to a target that cannot be reached"
    if not path:
        return "The answer key gives no example path"
    failed = [message for ok, message, _ in path_checks(grid, start, target, path).values() if ok is not True]
    if failed:
        return f"The answer key's example path is not a path: {failed[0]}"
    if path_cost(grid, path) != cost:
        return f"The answer key's example path costs {path_cost(grid, path)}, not the minimum {cost}"
    return None


def _listed(cells):
    shown = ", ".join(str(cell) for cell in cells[:3])
    return shown + (f" and {len(cells) - 3} more" if len(cells) > 3 else "")


def _is(cells):
    return "is" if len(cells) == 1 else "are"
