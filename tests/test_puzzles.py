"""The bundled puzzle set: well formed, the same ids as the contract, and solved alike by the shared
Dijkstra and an independent oracle. The verifier's copies of the rules are byte-for-byte the tools'."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

import pytest
from oracle import minimum_cost

from contract import PuzzleId
from plugin.grid import adjacent, grid_problem, is_open, path_cost, solve
from plugin.puzzles import PUZZLES

ROOT = Path(__file__).resolve().parents[1]
# Puzzles with no path, on purpose.
UNREACHABLE = {"walled-target", "boxed-start", "split-board"}
# Minimum costs worked out by hand.
BY_HAND = {
    "warmup-3x3": 8,
    "single-cell": 7,
    "start-is-target": 4,
    "one-row": 31,
    "one-column": 28,
    "next-door": 10,
    "all-zero": 0,
    "all-ties": 5,
    "detour": 11,
    "toll-gate": 17,
    "zero-corridor": 0,
    "spiral": 31,
}


@pytest.mark.parametrize("module", ["grid.py", "puzzles.py"])
def test_the_verifier_copies_are_the_tools_rules(module: str) -> None:
    assert (ROOT / "verifier" / module).read_bytes() == (ROOT / "src" / "plugin" / module).read_bytes(), (
        f"verifier/{module} must be a byte-for-byte copy of src/plugin/{module}"
    )


def test_the_contract_lists_every_puzzle() -> None:
    assert [puzzle.value for puzzle in PuzzleId] == list(PUZZLES)


def test_there_are_edge_cases_and_generated_puzzles() -> None:
    assert len(PUZZLES) >= 20
    assert UNREACHABLE <= set(PUZZLES)
    assert sum(name.startswith("gen-") for name in PUZZLES) >= 8


@pytest.mark.parametrize("name", list(PUZZLES))
def test_each_puzzle_is_well_formed(name: str) -> None:
    puzzle = PUZZLES[name]
    assert grid_problem(puzzle["grid"], puzzle["start"], puzzle["target"]) is None
    assert puzzle["note"].strip()


@pytest.mark.parametrize("name", list(PUZZLES))
def test_dijkstra_agrees_with_the_oracle(name: str) -> None:
    grid, start, target = PUZZLES[name]["grid"], PUZZLES[name]["start"], PUZZLES[name]["target"]
    cost, path = solve(grid, start, target)
    assert cost == minimum_cost(grid, start, target)
    assert (cost is None) == (name in UNREACHABLE)
    if name in BY_HAND:
        assert cost == BY_HAND[name]
    if cost is None:
        assert path == []
        return
    assert path[0] == start and path[-1] == target
    assert all(is_open(grid, cell) for cell in path)
    assert all(adjacent(a, b) for a, b in pairwise(path))
    assert len(set(path)) == len(path)
    assert path_cost(grid, path) == cost


def test_solving_twice_gives_the_same_path() -> None:
    for puzzle in PUZZLES.values():
        assert solve(puzzle["grid"], puzzle["start"], puzzle["target"]) == solve(
            puzzle["grid"], puzzle["start"], puzzle["target"]
        )
