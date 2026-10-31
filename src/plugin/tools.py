from __future__ import annotations

from pathlib import Path

from contract import (
    RULE,
    Cell,
    CellNeighbors,
    ExploreInput,
    ExploreOutput,
    Neighbor,
    PinOutput,
    PuzzleInput,
    PuzzleOutput,
)
from plugin.grid import cell_cost, fingerprint, in_bounds, is_open, neighbors, size, solve
from plugin.puzzles import PUZZLES

MAX_EXPLORE = 100


def puzzle(puzzle_id):
    """The bundled puzzle's grid, start and target."""
    entry = PUZZLES[puzzle_id.value]
    return entry["grid"], entry["start"], entry["target"]


def as_cell(cell: tuple[int, int]) -> Cell:
    return Cell(row=cell[0], col=cell[1])


def pin_path(given: PuzzleInput, workspace: Path) -> PinOutput:
    """The answer key: the puzzle, its fingerprint, and its minimum cost with one path of that cost."""
    grid, start, target = puzzle(given.puzzle_id)
    cost, path = solve(grid, start, target)
    return PinOutput(
        puzzle_id=given.puzzle_id,
        grid=list(grid),
        start=as_cell(start),
        target=as_cell(target),
        sha256=fingerprint(grid, start, target),
        reachable=cost is not None,
        optimal_cost=cost,
        example_path=[as_cell(cell) for cell in path],
    )


def get_puzzle(given: PuzzleInput, workspace: Path) -> PuzzleOutput:
    grid, start, target = puzzle(given.puzzle_id)
    rows, cols = size(grid)
    return PuzzleOutput(
        puzzle_id=given.puzzle_id,
        rows=rows,
        cols=cols,
        grid=list(grid),
        start=as_cell(start),
        target=as_cell(target),
        rule=RULE,
    )


def explore(given: ExploreInput, workspace: Path) -> ExploreOutput:
    grid, _, _ = puzzle(given.puzzle_id)
    cells = [(cell.row, cell.col) for cell in given.cells]
    if not 1 <= len(cells) <= MAX_EXPLORE:
        raise ValueError(f"explore takes 1 to {MAX_EXPLORE} cells, not {len(cells)}")
    if len(set(cells)) != len(cells):
        raise ValueError("explore's cells must be distinct")
    for cell in cells:
        if not in_bounds(grid, cell):
            raise ValueError(f"cell {list(cell)} is off the {size(grid)[0]} x {size(grid)[1]} grid")
        if not is_open(grid, cell):
            raise ValueError(f"cell {list(cell)} is a wall")
    return ExploreOutput(
        puzzle_id=given.puzzle_id,
        cells=[
            CellNeighbors(
                cell=as_cell(cell),
                cost=cell_cost(grid, cell),
                neighbors=[Neighbor(cell=as_cell(step), cost=cell_cost(grid, step)) for step in neighbors(grid, cell)],
            )
            for cell in cells
        ],
    )
