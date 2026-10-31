from .checks import bundled, pair, pairs, result
from .grid import cell_cost, in_bounds, is_open, neighbors

MAX_CELLS = 100


def verify_input(value):
    grid, _, _ = bundled(value.puzzle_id)
    cells = pairs(value.cells)
    if not 1 <= len(cells) <= MAX_CELLS:
        return result(False, f"explore takes 1 to {MAX_CELLS} cells, not {len(cells)}")
    if len(set(cells)) != len(cells):
        return result(False, "explore's cells must be distinct")
    for cell in cells:
        if not in_bounds(grid, cell):
            return result(False, f"cell {list(cell)} is off the grid")
        if not is_open(grid, cell):
            return result(False, f"cell {list(cell)} is a wall")
    return result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    grid, _, _ = bundled(input_value.puzzle_id)
    if output_value.puzzle_id != input_value.puzzle_id:
        return result(False, f"the output is puzzle {output_value.puzzle_id.value}, not {input_value.puzzle_id.value}")
    asked = pairs(input_value.cells)
    given = [pair(entry.cell) for entry in output_value.cells]
    if given != asked:
        return result(False, "the output does not answer the cells asked, in the order asked")
    for entry in output_value.cells:
        cell = pair(entry.cell)
        if entry.cost != cell_cost(grid, cell):
            return result(False, f"cell {list(cell)} costs {cell_cost(grid, cell)}, not {entry.cost}")
        expected = [(step, cell_cost(grid, step)) for step in neighbors(grid, cell)]
        actual = [(pair(step.cell), step.cost) for step in entry.neighbors]
        if actual != expected:
            return result(False, f"cell {list(cell)}'s open neighbors are not the ones given")
    return result(True, f"{len(asked)} cell(s) explored")
