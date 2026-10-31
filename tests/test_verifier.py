"""The shortest-path verdict on correct, incorrect, missing, malformed and boundary answers.

The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import PathOutput, PinOutput, PuzzleInput
from plugin import pin_path

# warmup-3x3:  1 4 2 / 3 1 9 / 1 2 1, from the top left to the bottom right; the minimum is 8.
DOWN_THEN_RIGHT = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]  # 1+3+1+2+1
THROUGH_MIDDLE = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]  # 1+3+1+2+1, a tie
COSTLIER = [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)]  # 1+4+1+2+1 = 9


def reference(name: str, tmp_path: Path) -> PinOutput:
    return build_output(plain_output(pin_path(build_output({"puzzle_id": name}, PuzzleInput), tmp_path)), PinOutput)


def judge(tmp_path: Path, name: str, path, cost, *, reachable=True, answer_id=None, pin="pinned"):
    arguments = build_output({"puzzle_id": name}, PuzzleInput)
    output = build_output(
        {
            "puzzle_id": answer_id or name,
            "reachable": reachable,
            "cost": cost,
            "path": [{"row": r, "col": c} for r, c in path],
        },
        PathOutput,
    )
    key = reference(name, tmp_path) if pin == "pinned" else pin
    first = verifier.verify_task("shortest-path", arguments, output, key, str(tmp_path))
    assert verifier.verify_task("shortest-path", arguments, output, key, str(tmp_path)) == first, "deterministic"
    return first


def checks(verdict) -> dict:
    return {entry["id"]: entry["ok"] for entry in verdict["details"]["constraints"]}


def failed(verdict) -> list[str]:
    return [key for key, ok in checks(verdict).items() if ok is False]


# --- correct ---------------------------------------------------------------------------------------


def test_accepts_a_cheapest_path(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT, 8)
    assert verdict["valid"] is True and verdict["score"] == 1.0
    assert all(ok is True for ok in checks(verdict).values())
    assert verdict["message"] == "All 12 checks hold: a cheapest path, of cost 8."


def test_accepts_any_tied_cheapest_path(tmp_path: Path) -> None:
    assert judge(tmp_path, "warmup-3x3", THROUGH_MIDDLE, 8)["valid"] is True


def test_accepts_the_example_path_on_every_reachable_puzzle(tmp_path: Path) -> None:
    from plugin.puzzles import PUZZLES

    for name in PUZZLES:
        key = reference(name, tmp_path)
        path = [(cell.row, cell.col) for cell in key.example_path]
        verdict = judge(tmp_path, name, path, key.optimal_cost, reachable=key.reachable)
        assert verdict["valid"] is True, (name, verdict["message"])


@pytest.mark.parametrize("name", ["walled-target", "boxed-start", "split-board"])
def test_accepts_unreachable_said_rightly(tmp_path: Path, name: str) -> None:
    verdict = judge(tmp_path, name, [], None, reachable=False)
    assert verdict["valid"] is True and "cannot be reached" in verdict["message"]
    assert checks(verdict)["starts-at-start"] is None  # no path to check


# --- incorrect ---------------------------------------------------------------------------------------


def test_a_costlier_path_scores_its_share(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", COSTLIER, 9)
    assert verdict["valid"] is False and failed(verdict) == ["cost-optimal"]
    assert verdict["score"] == pytest.approx(8 / 9)
    assert verdict["message"] == "cost-optimal: The path costs 9, but the minimum is 8"


def test_a_wrong_stated_cost_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT, 7)
    assert failed(verdict) == ["cost-matches-path"] and verdict["score"] == 0.0
    assert "sum to 8" in verdict["message"]


def test_a_diagonal_step_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", [(0, 0), (1, 1), (2, 2)], 3)
    assert failed(verdict) == ["adjacent-steps"] and verdict["score"] == 0.0
    assert checks(verdict)["cost-optimal"] is None


def test_a_jump_fails(tmp_path: Path) -> None:
    assert "adjacent-steps" in failed(judge(tmp_path, "warmup-3x3", [(0, 0), (2, 0), (2, 1), (2, 2)], 5))


def test_stepping_on_a_wall_fails(tmp_path: Path) -> None:
    # detour: 1999991 / 1#####1 / 1111111
    path = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6)]
    verdict = judge(tmp_path, "detour", path, 50)
    assert failed(verdict) == ["no-walls"] and "[1, 1] is a wall" in verdict["message"]
    assert checks(verdict)["cost-matches-path"] is None


def test_leaving_the_grid_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", [(0, 0), (-1, 0), (-1, 1), (0, 1)], 5)
    assert {"in-bounds", "ends-at-target"} <= set(failed(verdict))
    assert checks(verdict)["no-walls"] is None and verdict["score"] == 0.0


def test_a_wrong_start_or_end_fails(tmp_path: Path) -> None:
    assert failed(judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT[1:], 7)) == ["starts-at-start"]
    assert failed(judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT[:-1], 7)) == ["ends-at-target"]


def test_a_reversed_path_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT[::-1], 8)
    assert failed(verdict) == ["starts-at-start", "ends-at-target"]
    assert verdict["message"].endswith("(+1 more)")


def test_visiting_a_cell_twice_fails(tmp_path: Path) -> None:
    # all-zero costs nothing anywhere, so a loop does not raise the cost: only simple-path catches it.
    path = [(0, 0), (0, 1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (3, 4), (4, 4)]
    verdict = judge(tmp_path, "all-zero", path, 0)
    assert failed(verdict) == ["simple-path"] and verdict["score"] == 0.0


def test_the_wrong_puzzle_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT, 8, answer_id="all-ties")
    assert failed(verdict) == ["puzzle-id"] and verdict["score"] == 0.0


def test_saying_unreachable_when_it_is_not_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", [], None, reachable=False)
    assert failed(verdict) == ["reachability"] and "minimum cost 8" in verdict["message"]


def test_claiming_a_path_to_an_unreachable_target_fails(tmp_path: Path) -> None:
    # split-board: a wall across row 2; this path walks through it.
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5)]
    verdict = judge(tmp_path, "split-board", path, 25)
    assert {"reachability", "no-walls"} <= set(failed(verdict))
    assert checks(verdict)["cost-optimal"] is None and verdict["score"] == 0.0


# --- missing -----------------------------------------------------------------------------------------


def test_an_empty_path_for_a_reachable_target_fails(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", [], 8)
    assert failed(verdict) == ["shape"] and "no path" in verdict["message"]
    assert checks(verdict)["starts-at-start"] is None


def test_a_missing_cost_fails(tmp_path: Path) -> None:
    assert failed(judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT, None)) == ["shape"]


def test_unreachable_with_a_cost_or_path_fails(tmp_path: Path) -> None:
    assert failed(judge(tmp_path, "split-board", [], 0, reachable=False)) == ["shape"]
    assert failed(judge(tmp_path, "split-board", [(0, 0)], None, reachable=False)) == ["shape"]


# --- malformed answer key ------------------------------------------------------------------------------


def test_no_answer_key_fails_everything(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT, 8, pin=None)
    assert failed(verdict) == ["answer-key"] and verdict["score"] == 0.0
    assert all(ok is None for key, ok in checks(verdict).items() if key != "answer-key")


@pytest.mark.parametrize(
    ("change", "says"),
    [
        ({"grid": ["142", "311", "121"]}, "not the bundled puzzle"),
        ({"optimal_cost": 7}, "minimum cost 7"),
        ({"sha256": "0" * 64}, "sha256"),
        ({"puzzle_id": "all-ties"}, "for puzzle all-ties"),
        ({"example_path": [{"row": 0, "col": 0}, {"row": 1, "col": 1}, {"row": 2, "col": 2}]}, "not a path"),
        ({"example_path": [{"row": r, "col": c} for r, c in COSTLIER]}, "costs 9"),
    ],
)
def test_a_tampered_answer_key_fails(tmp_path: Path, change: dict, says: str) -> None:
    tampered = build_output({**plain_output(reference("warmup-3x3", tmp_path)), **change}, PinOutput)
    verdict = judge(tmp_path, "warmup-3x3", DOWN_THEN_RIGHT, 8, pin=tampered)
    assert failed(verdict) == ["answer-key"] and says in verdict["message"]


# --- boundary ------------------------------------------------------------------------------------------


def test_a_single_cell_path(tmp_path: Path) -> None:
    assert judge(tmp_path, "single-cell", [(0, 0)], 7)["valid"] is True
    assert judge(tmp_path, "start-is-target", [(2, 1)], 4)["valid"] is True
    assert failed(judge(tmp_path, "start-is-target", [(2, 1), (2, 2), (2, 1)], 9)) == ["simple-path"]


def test_one_row_and_one_column(tmp_path: Path) -> None:
    assert judge(tmp_path, "one-row", [(0, c) for c in range(8)], 31)["valid"] is True
    assert judge(tmp_path, "one-column", [(r, 0) for r in range(5, -1, -1)], 28)["valid"] is True


def test_zero_cost_minimum_gives_no_partial_score(tmp_path: Path) -> None:
    # zero-corridor: straight down through the 9s is a path (0+9+9+9+0+0), but the minimum is 0.
    verdict = judge(tmp_path, "zero-corridor", [(r, 0) for r in range(6)], 27)
    assert failed(verdict) == ["cost-optimal"] and verdict["score"] == 0.0


def test_partial_scores_stay_below_one(tmp_path: Path) -> None:
    # next-door: 1 9 / 1 1. The long way round costs 12 against 10.
    verdict = judge(tmp_path, "next-door", [(0, 0), (1, 0), (1, 1), (0, 1)], 12)
    assert verdict["valid"] is False and 0 < verdict["score"] <= 0.99


def test_verdicts_have_every_constraint_with_the_same_keys(tmp_path: Path) -> None:
    verdict = judge(tmp_path, "warmup-3x3", COSTLIER, 9)
    constraints = verdict["details"]["constraints"]
    assert len(constraints) == 12
    assert all(set(entry) == {"id", "constraint", "ok", "expected", "actual", "message"} for entry in constraints)
    assert verdict["details"]["expected"]["optimal_cost"] == 8 and verdict["details"]["path_cost"] == 9


def test_input_verifiers_accept_every_puzzle() -> None:
    from contract import PuzzleId

    for puzzle in PuzzleId:
        given = build_output({"puzzle_id": puzzle.value}, PuzzleInput)
        assert verifier.verify_input("pin_path", given)["valid"] is True
        assert verifier.verify_input("get_puzzle", given)["valid"] is True
