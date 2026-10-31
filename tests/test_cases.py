"""The scripted cases under tests/cases/, replayed through the real tools and the real verifier as
NanoAgent runs a task: the reference tool first, every tool call checked by verify_input and
verify_output, and the submitted answer judged by verify_task. Each gets the verdict it expects."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, PuzzleInput, Task, Tool
from plugin.__main__ import IMPLEMENTATIONS

CASES = sorted((Path(__file__).resolve().parent / "cases").glob("*.json"))


def run_tool(name: str, arguments: dict, workspace: Path):
    given_class, made_class = TOOLS[Tool(name)]
    given = build_output(arguments, given_class)
    checked = verifier.verify_input(name, given)
    if not checked["valid"]:
        raise ValueError(checked["message"])
    made = build_output(plain_output(IMPLEMENTATIONS[Tool(name)](given, workspace)), made_class)
    checked = verifier.verify_output(name, given, made, str(workspace))
    assert checked["valid"], f"{name}'s own output fails its verifier: {checked['message']}"
    return made


def replay(case: dict, workspace: Path) -> dict:
    task = Task(case["task"])
    arguments = build_output(case["arguments"], TASKS[task][0])
    reference = run_tool("pin_path", plain_output(arguments), workspace)
    for step in case["steps"]:
        if step["tool"] == "submit":
            output = build_output(step["arguments"], TASKS[task][1])
            return verifier.verify_task(task.value, arguments, output, reference, str(workspace))
        run_tool(step["tool"], step["arguments"], workspace)
    raise AssertionError("the case never submits")


def test_there_are_gold_wrong_and_error_cases() -> None:
    names = {case.stem for case in CASES}
    assert {"gold_warmup", "gold_tie", "gold_detour", "gold_gen_10x10", "gold_unreachable"} <= names
    assert {"fewest_steps", "wall_step", "diagonal_step", "wrong_cost", "gave_up", "explore_a_wall"} <= names


@pytest.mark.parametrize("case_file", CASES, ids=[case.stem for case in CASES])
def test_each_case_gets_its_verdict(tmp_path: Path, case_file: Path) -> None:
    case = json.loads(case_file.read_text(encoding="utf-8"))
    expect = case["expect"]
    if "error_contains" in expect:
        with pytest.raises(ValueError, match=expect["error_contains"]):
            replay(case, tmp_path)
        return
    verdict = replay(case, tmp_path)
    assert verdict["valid"] is expect["valid"], verdict["message"]
    assert verdict["score"] == pytest.approx(expect["score"], abs=1e-6)
    failed = [entry["id"] for entry in verdict["details"]["constraints"] if entry["ok"] is False]
    assert failed == expect.get("failed", [])


@pytest.mark.parametrize("case_file", CASES, ids=[case.stem for case in CASES])
def test_each_case_keeps_to_the_task_tools(case_file: Path) -> None:
    case = json.loads(case_file.read_text(encoding="utf-8"))
    tools = [step["tool"] for step in case["steps"]]
    assert set(tools) <= {"get_puzzle", "explore", "submit"}
    assert tools[0] == "get_puzzle" and len(tools) <= 4
    assert build_output(case["arguments"], PuzzleInput).puzzle_id.value == case["arguments"]["puzzle_id"]
