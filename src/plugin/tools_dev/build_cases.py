"""Write tests/cases/*.json: scripted runs of the shortest-path task, each with the verdict it expects.

A case scripts the agent: the tool calls it makes (get_puzzle, explore) and the answer it submits,
the prescribed path or the same run broken in one way a weak agent breaks it. No model runs anywhere;
tests/test_cases.py replays each case through the real tools and the real verifier.

    uv run python src/plugin/tools_dev/build_cases.py
"""

import json
from pathlib import Path

from plugin.grid import path_cost, solve
from plugin.puzzles import PUZZLES

CASES = Path(__file__).resolve().parents[3] / "tests" / "cases"


def cells(path):
    return [{"row": r, "col": c} for r, c in path]


def answer(name, path, cost=None, reachable=True):
    grid = PUZZLES[name]["grid"]
    if reachable and cost is None:
        cost = path_cost(grid, path)
    return {"puzzle_id": name, "reachable": reachable, "cost": cost, "path": cells(path)}


def cheapest(name):
    puzzle = PUZZLES[name]
    return solve(puzzle["grid"], puzzle["start"], puzzle["target"])[1]


def case(note, name, submitted, expect, explored=None):
    steps = [{"tool": "get_puzzle", "arguments": {"puzzle_id": name}}]
    if explored is not None:
        steps.append({"tool": "explore", "arguments": {"puzzle_id": name, "cells": cells(explored)}})
    if submitted is not None:
        steps.append({"tool": "submit", "arguments": submitted})
    return {"note": note, "task": "shortest-path", "arguments": {"puzzle_id": name}, "steps": steps, "expect": expect}


def build():
    detour_top_row = [(0, c) for c in range(7)]
    return {
        "gold_warmup": case(
            "The warmup puzzle, answered with a cheapest path.",
            "warmup-3x3",
            answer("warmup-3x3", cheapest("warmup-3x3")),
            {"valid": True, "score": 1.0},
        ),
        "gold_tie": case(
            "The warmup puzzle, answered with the other path of the same minimum cost.",
            "warmup-3x3",
            answer("warmup-3x3", [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]),
            {"valid": True, "score": 1.0},
        ),
        "gold_detour": case(
            "The long way round, after exploring both ends.",
            "detour",
            answer("detour", cheapest("detour")),
            {"valid": True, "score": 1.0},
            explored=[(0, 0), (0, 6), (2, 0)],
        ),
        "gold_gen_10x10": case(
            "The largest generated puzzle, answered with a cheapest path.",
            "gen-10x10",
            answer("gen-10x10", cheapest("gen-10x10")),
            {"valid": True, "score": 1.0},
        ),
        "gold_unreachable": case(
            "A walled-in target, rightly answered as unreachable after exploring it.",
            "walled-target",
            answer("walled-target", [], reachable=False),
            {"valid": True, "score": 1.0},
            explored=[(3, 3)],
        ),
        "fewest_steps": case(
            "The straight road through the 9s: the fewest steps, not the least cost.",
            "detour",
            answer("detour", detour_top_row),
            {"valid": False, "failed": ["cost-optimal"], "score": round(11 / 47, 6)},
        ),
        "wall_step": case(
            "A shortcut through a wall.",
            "detour",
            answer("detour", [(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6)], cost=50),
            {"valid": False, "failed": ["no-walls"], "score": 0.0},
        ),
        "diagonal_step": case(
            "A diagonal step across the warmup grid.",
            "warmup-3x3",
            answer("warmup-3x3", [(0, 0), (1, 1), (2, 2)]),
            {"valid": False, "failed": ["adjacent-steps"], "score": 0.0},
        ),
        "wrong_cost": case(
            "A cheapest path whose stated cost is miscounted.",
            "warmup-3x3",
            answer("warmup-3x3", cheapest("warmup-3x3"), cost=7),
            {"valid": False, "failed": ["cost-matches-path"], "score": 0.0},
        ),
        "gave_up": case(
            "A reachable target answered as unreachable.",
            "gen-8x8-dense-walls",
            answer("gen-8x8-dense-walls", [], reachable=False),
            {"valid": False, "failed": ["reachability"], "score": 0.0},
        ),
        "explore_a_wall": case(
            "Exploring a wall cell: the tool refuses the call.",
            "detour",
            None,
            {"error_contains": "is a wall"},
            explored=[(1, 1)],
        ),
    }


def main():
    CASES.mkdir(parents=True, exist_ok=True)
    for name, body in build().items():
        (CASES / f"{name}.json").write_text(json.dumps(body, indent=1) + "\n", encoding="utf-8")
        print(f"wrote tests/cases/{name}.json")


if __name__ == "__main__":
    main()
