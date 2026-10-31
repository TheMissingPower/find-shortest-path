from contract import RULE

from .checks import bundled, pair, result
from .grid import size


def verify_input(value):
    return result(True, "input is valid")


def puzzle_problem(puzzle_id, output):
    """Why ``output`` is not get_puzzle's answer for ``puzzle_id``, or None."""
    if output.puzzle_id != puzzle_id:
        return f"the output is puzzle {output.puzzle_id.value}, not {puzzle_id.value}"
    grid, start, target = bundled(puzzle_id)
    if tuple(output.grid) != grid:
        return f"the grid is not puzzle {puzzle_id.value}'s"
    if (output.rows, output.cols) != size(grid):
        return f"the grid is {size(grid)[0]} x {size(grid)[1]}, not {output.rows} x {output.cols}"
    if pair(output.start) != start or pair(output.target) != target:
        return f"the start or target is not puzzle {puzzle_id.value}'s: {list(start)} to {list(target)}"
    if output.rule != RULE:
        return "the rule is not the puzzle's rule"
    return None


def verify_output(input_value, output_value, workspace):
    problem = puzzle_problem(input_value.puzzle_id, output_value)
    return result(False, problem) if problem else result(True, "the puzzle is the bundled one")


def verify_task(arguments, output, reference, workspace):
    problem = puzzle_problem(arguments.puzzle_id, output)
    return result(False, problem) if problem else result(True, f"puzzle {arguments.puzzle_id.value} is shown")
