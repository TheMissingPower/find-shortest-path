"""The shortest-path task's verdict: 12 constraints, in order, every one of which must hold.

The ground truth is the verifier's own solve of its own copy of the bundled puzzle (puzzles.py and
grid.py), never a stored answer: the answer key, pin_path's pinned output, must agree with it before
anything else is judged. Each constraint is {id, constraint, ok, expected, actual, message}: ok is
True (holds), False (fails) or None (not checked, because a check it needs failed, or not needed,
because there is no path to check).
"""

from .checks import answer_key_problem, bundled, pairs, path_checks, result
from .grid import path_cost, solve

CONSTRAINTS = (
    ("answer-key", "The answer key is the bundled puzzle, solved"),
    ("puzzle-id", "The answer names the task's puzzle"),
    ("reachability", "The answer says rightly whether the target can be reached"),
    ("shape", "An unreachable answer has no path and a null cost; a reachable one has both"),
    ("starts-at-start", "The path begins at the start"),
    ("ends-at-target", "The path ends at the target"),
    ("in-bounds", "Every cell of the path is on the grid"),
    ("no-walls", "No cell of the path is a wall"),
    ("adjacent-steps", "Each step moves one cell up, down, left or right"),
    ("simple-path", "No cell is visited twice"),
    ("cost-matches-path", "The stated cost is the sum of the path's cells"),
    ("cost-optimal", "The path's cost is the minimum"),
)
PATH_IDS = ("starts-at-start", "ends-at-target", "in-bounds", "no-walls", "adjacent-steps", "simple-path")
# A valid but costlier path earns its share of the minimum, never a full score.
PARTIAL_CAP = 0.99


def verify_task(arguments, output, reference, workspace):
    grid, start, target = bundled(arguments.puzzle_id)
    optimal, example = solve(grid, start, target)
    reachable = optimal is not None
    path = pairs(output.path)
    found = {}

    def record(key, ok, message="", expected=None, actual=None):
        found[key] = {"ok": ok, "expected": expected, "actual": actual, "message": message}

    def skip(keys, message):
        for key in keys:
            if key not in found:
                record(key, None, message)

    problem = answer_key_problem(arguments.puzzle_id, reference)
    if problem:
        record("answer-key", False, problem)
        skip([key for key, _ in CONSTRAINTS], "Not checked: answer-key did not hold.")
        return _verdict(found, optimal, example, None)
    record("answer-key", True)

    if output.puzzle_id == arguments.puzzle_id:
        record("puzzle-id", True, expected=arguments.puzzle_id.value, actual=output.puzzle_id.value)
    else:
        message = f"The answer is for puzzle {output.puzzle_id.value}, not the task's {arguments.puzzle_id.value}"
        record("puzzle-id", False, message, arguments.puzzle_id.value, output.puzzle_id.value)

    if output.reachable == reachable:
        record("reachability", True, expected=reachable, actual=output.reachable)
    elif reachable:
        message = f"The target can be reached (minimum cost {optimal}), but the answer says it cannot"
        record("reachability", False, message, reachable, output.reachable)
    else:
        message = "The target cannot be reached (walls cut it off from the start), but the answer says it can"
        record("reachability", False, message, reachable, output.reachable)

    if output.reachable:
        shape = None if path else "The answer says the target can be reached but gives no path"
        shape = shape or (None if output.cost is not None else "The answer gives a path but a null cost")
    else:
        shape = None if not path else "The answer says the target cannot be reached but gives a path"
        costed = f"The answer says the target cannot be reached but gives cost {output.cost}"
        shape = shape or (None if output.cost is None else costed)
    record("shape", shape is None, shape or "")

    if shape or not output.reachable:
        reason = "Not checked: shape did not hold." if shape else "Not needed: the answer gives no path."
        skip([key for key, _ in CONSTRAINTS], reason)
        return _verdict(found, optimal, example, None)

    for key, (ok, message, actual) in path_checks(grid, start, target, path).items():
        record(key, ok, message, actual=actual)
    expected_end = {"starts-at-start": list(start), "ends-at-target": list(target)}
    for key, cell in expected_end.items():
        found[key]["expected"] = cell

    on_grid = found["in-bounds"]["ok"] and found["no-walls"]["ok"]
    actual_cost = path_cost(grid, path) if on_grid else None
    if not on_grid:
        record("cost-matches-path", None, "Not checked: the path leaves the open cells of the grid.")
    elif output.cost == actual_cost:
        record("cost-matches-path", True, expected=actual_cost, actual=output.cost)
    else:
        message = f"The answer states cost {output.cost}, but its path's cells sum to {actual_cost}"
        record("cost-matches-path", False, message, actual_cost, output.cost)

    if not all(found[key]["ok"] for key in PATH_IDS):
        record("cost-optimal", None, "Not checked: the answer is not a path from the start to the target.")
    elif not reachable:
        record("cost-optimal", None, "Not checked: the target cannot be reached.")
    elif actual_cost == optimal:
        record("cost-optimal", True, expected=optimal, actual=actual_cost)
    else:
        message = f"The path costs {actual_cost}, but the minimum is {optimal}"
        record("cost-optimal", False, message, optimal, actual_cost)
    return _verdict(found, optimal, example, actual_cost)


def _verdict(found, optimal, example, actual_cost):
    constraints = [{"id": key, "constraint": text, **found[key]} for key, text in CONSTRAINTS]
    failed = [entry for entry in constraints if entry["ok"] is False]
    details = {
        "constraints": constraints,
        "expected": {
            "reachable": optimal is not None,
            "optimal_cost": optimal,
            "example_path": [list(cell) for cell in example],
        },
        "path_cost": actual_cost,
    }
    if not failed:
        if optimal is None:
            message = "All 12 checks hold: the target cannot be reached, as the answer says."
        else:
            message = f"All 12 checks hold: a cheapest path, of cost {optimal}."
        return result(True, message, **details)
    first = failed[0]
    more = f" (+{len(failed) - 1} more)" if len(failed) > 1 else ""
    message = f"{first['id']}: {first['message']}{more}"
    if [entry["id"] for entry in failed] == ["cost-optimal"] and actual_cost and optimal:
        score = min(PARTIAL_CAP, optimal / actual_cost)
    else:
        score = 0.0
    return result(False, message, score=score, **details)
