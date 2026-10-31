from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import RULE, ExploreInput, ExploreOutput, PinOutput, PuzzleInput, PuzzleOutput
from plugin import explore, get_puzzle, pin_path


def puzzle_input(name: str) -> PuzzleInput:
    return build_output({"puzzle_id": name}, PuzzleInput)


def explore_input(name: str, cells: list[tuple[int, int]]) -> ExploreInput:
    return build_output({"puzzle_id": name, "cells": [{"row": r, "col": c} for r, c in cells]}, ExploreInput)


def test_get_puzzle_gives_the_grid_and_rule(tmp_path: Path) -> None:
    made = build_output(plain_output(get_puzzle(puzzle_input("warmup-3x3"), tmp_path)), PuzzleOutput)
    assert made.grid == ["142", "319", "121"] and (made.rows, made.cols) == (3, 3)
    assert (made.start.row, made.start.col, made.target.row, made.target.col) == (0, 0, 2, 2)
    assert made.rule == RULE
    assert verifier.verify_output("get_puzzle", puzzle_input("warmup-3x3"), made, str(tmp_path))["valid"] is True
    assert verifier.verify_task("show-puzzle", puzzle_input("warmup-3x3"), made, None, str(tmp_path))["valid"] is True


def test_a_changed_puzzle_is_refused(tmp_path: Path) -> None:
    made = plain_output(get_puzzle(puzzle_input("warmup-3x3"), tmp_path))
    changed = build_output({**made, "grid": ["142", "311", "121"]}, PuzzleOutput)
    assert verifier.verify_output("get_puzzle", puzzle_input("warmup-3x3"), changed, str(tmp_path))["valid"] is False
    other = build_output({**made, "puzzle_id": "all-ties"}, PuzzleOutput)
    assert verifier.verify_task("show-puzzle", puzzle_input("warmup-3x3"), other, None, str(tmp_path))["valid"] is False


def test_explore_gives_open_neighbors_in_order(tmp_path: Path) -> None:
    given = explore_input("detour", [(0, 0), (2, 3), (0, 6)])
    made = build_output(plain_output(explore(given, tmp_path)), ExploreOutput)
    around = {(e.cell.row, e.cell.col): [(n.cell.row, n.cell.col, n.cost) for n in e.neighbors] for e in made.cells}
    assert around[(0, 0)] == [(0, 1, 9), (1, 0, 1)]  # right, down; up and left are off the grid
    assert around[(2, 3)] == [(2, 4, 1), (2, 2, 1)]  # up is a wall
    assert around[(0, 6)] == [(1, 6, 1), (0, 5, 9)]
    assert [entry.cost for entry in made.cells] == [1, 1, 1]
    assert verifier.verify_input("explore", given)["valid"] is True
    assert verifier.verify_output("explore", given, made, str(tmp_path))["valid"] is True


def test_explore_output_with_a_wrong_neighbor_is_refused(tmp_path: Path) -> None:
    given = explore_input("detour", [(0, 0)])
    made = plain_output(explore(given, tmp_path))
    made["cells"][0]["neighbors"][0]["cost"] = 1
    verdict = verifier.verify_output("explore", given, build_output(made, ExploreOutput), str(tmp_path))
    assert verdict["valid"] is False and "neighbors" in verdict["message"]


@pytest.mark.parametrize(
    ("cells", "says"),
    [
        ([(1, 1)], "wall"),
        ([(3, 0)], "off the"),
        ([(0, -1)], "off the"),
        ([(0, 0), (0, 0)], "distinct"),
        ([], "1 to 100"),
    ],
)
def test_explore_refuses_bad_cells(tmp_path: Path, cells, says: str) -> None:
    given = explore_input("detour", cells)
    with pytest.raises(ValueError, match=says):
        explore(given, tmp_path)
    verdict = verifier.verify_input("explore", given)
    assert verdict["valid"] is False and says in verdict["message"]


def test_pin_path_is_the_solved_puzzle(tmp_path: Path) -> None:
    made = build_output(plain_output(pin_path(puzzle_input("detour"), tmp_path)), PinOutput)
    assert made.reachable is True and made.optimal_cost == 11 and len(made.example_path) == 11
    assert verifier.verify_output("pin_path", puzzle_input("detour"), made, str(tmp_path))["valid"] is True
    blocked = build_output(plain_output(pin_path(puzzle_input("split-board"), tmp_path)), PinOutput)
    assert blocked.reachable is False and blocked.optimal_cost is None and blocked.example_path == []
    assert verifier.verify_output("pin_path", puzzle_input("split-board"), blocked, str(tmp_path))["valid"] is True


def test_the_server_implements_every_tool() -> None:
    from contract import Tool
    from plugin.__main__ import IMPLEMENTATIONS

    assert set(IMPLEMENTATIONS) == set(Tool)


def test_tools_write_nothing(tmp_path: Path) -> None:
    pin_path(puzzle_input("gen-10x10"), tmp_path)
    get_puzzle(puzzle_input("gen-10x10"), tmp_path)
    explore(explore_input("gen-10x10", [(0, 0)]), tmp_path)
    assert list(tmp_path.iterdir()) == []
