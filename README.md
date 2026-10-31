# Shortest Path Grid

A `nanoagent.plugin/v0001` plugin with the structure of NanoAgent's reference
plugin, [arxiv-source](https://github.com/zeyuyang8/arxiv-source). Its task,
`shortest-path`, is a LeetCode-style weighted-grid puzzle: given a grid of cell
costs (digits 0-9) and walls (`#`), a start and a target, the agent must submit
a path of minimum total cost, moving up, down, left or right, or say rightly
that walls cut the target off. The 25 puzzles are bundled with the plugin, so
the environment needs no network. A rule-based verifier solves each puzzle
itself and judges the submitted path against 12 constraints, every one of
which must hold.

## Tools

| Tool | Does | Code |
|---|---|---|
| `pin_path` | The answer key. Solves the bundled puzzle (Dijkstra) and pins its grid, start, target, sha256, minimum cost and one path of that cost | `src/plugin/tools.py`, `src/plugin/grid.py` |
| `get_puzzle` | A puzzle's grid rows, size, start, target, and the move and cost rules in words | `src/plugin/tools.py` |
| `explore` | Up to 100 open cells at once: each one's cost and its open neighbors (up, right, down, left) with their costs. Refuses walls, cells off the grid and repeats | `src/plugin/tools.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `shortest-path` | Finds a cheapest path from the start to the target, or reports that none exists | `agent`, with `get_puzzle` and `explore`; reference `pin_path` |
| `show-puzzle` | Shows a puzzle's grid, start, target and rules | `tool` (`get_puzzle`) |

## The task

Before the agent starts, NanoAgent runs `pin_path` with the task input, out of
the agent's sight, and pins its output. The agent then has `get_puzzle`,
`explore` and `submit`:

1. `get_puzzle` once.
2. Optionally `explore` once, with every cell whose neighbors it wants.
3. `submit` with `{puzzle_id, reachable, cost, path}`.

**The rules.** A cell is `{row, col}`, 0-indexed from the top left. A path
moves one cell up, down, left or right per step, never diagonally, never onto
`#`, never off the grid, and never visits a cell twice. Its cost is the sum of
the digits of every cell on it, **the start and the target included** (the
LeetCode 64 convention). When the start is the target, the path is that one
cell. When no path exists, the answer is `reachable: false, cost: null, path: []`.
Any path of the minimum cost is accepted, since puzzles may have ties.

**The puzzles** (`src/plugin/puzzles.py`):

| Kind | Puzzles |
|---|---|
| Warm-up | `warmup-3x3` (two tied paths) |
| Degenerate shapes | `single-cell`, `start-is-target`, `one-row`, `one-column`, `next-door` |
| Costs that mislead | `all-zero`, `all-ties`, `detour` (the long way costs 11, the straight road 47), `toll-gate` (the near costly gap wins), `zero-corridor` (minimum 0), `spiral`, `reverse-corners` |
| Unreachable | `walled-target`, `boxed-start`, `split-board` |
| Generated, 5x5 to 10x10 | `gen-5x5`, `gen-6x6`, `gen-7x7`, `gen-7x7-low-costs`, `gen-8x8`, `gen-8x8-dense-walls`, `gen-9x9`, `gen-10x10`, `gen-10x10-maze` |

The generated puzzles were drawn once from fixed seeds by
`src/plugin/tools_dev/make_puzzles.py` and frozen into `puzzles.py`. Each was
kept only when its cheapest path costs less than every fewest-steps path, so a
breadth-first search alone gets it wrong.

## Ground truth

The ground truth is the verifier's own solve of its own copy of the puzzle,
never a stored answer. `verifier/grid.py` and `verifier/puzzles.py` are
byte-for-byte copies of `src/plugin/grid.py` and `src/plugin/puzzles.py`, and a
test enforces it. The verifier may not import `heapq`, so Dijkstra takes the
next cell by a scan, smallest `(cost, row, col)` first. That is deterministic
and fast enough for grids of at most 10x10. An independent Bellman-Ford oracle
(`tests/oracle.py`) agrees with it on every puzzle, as do minimum costs worked
out by hand.

## Constraints

`verifier/task.py` judges the submitted answer against 12 constraints, in
order. Every entry of the verdict's `details.constraints` has the keys
`{id, constraint, ok, expected, actual, message}`. `ok` takes one of three
values:
- `true`: the constraint holds.
- `false`: it fails.
- `null`: it was not checked, either because a check it needs failed, or because the answer has no path to check.

| # | id | What it checks | Example failure message |
|---|---|---|---|
| 1 | `answer-key` | The pinned answer key is this puzzle, its sha256, minimum cost and example path right | The answer key gives minimum cost 7; the puzzle's is 8 |
| 2 | `puzzle-id` | The answer names the task's puzzle | The answer is for puzzle all-ties, not the task's warmup-3x3 |
| 3 | `reachability` | `reachable` is right | The target can be reached (minimum cost 8), but the answer says it cannot |
| 4 | `shape` | Unreachable: `path == []` and `cost` null. Reachable: a path and a cost | The answer says the target can be reached but gives no path |
| 5 | `starts-at-start` | The path begins at the start | The path begins at [1, 0], not at the start [0, 0] |
| 6 | `ends-at-target` | The path ends at the target | The path ends at [2, 1], not at the target [2, 2] |
| 7 | `in-bounds` | Every cell is on the grid | [-1, 0], [-1, 1] are off the 3 x 3 grid |
| 8 | `no-walls` | No cell is a wall | [1, 1] is a wall (#) |
| 9 | `adjacent-steps` | Each step is one move up, down, left or right | 2 step(s) are not one move up, down, left or right, the first from [0, 0] to [1, 1] |
| 10 | `simple-path` | No cell is visited twice | The path visits [0, 0], [0, 1] more than once |
| 11 | `cost-matches-path` | The stated cost is the sum of the path's cells | The answer states cost 7, but its path's cells sum to 8 |
| 12 | `cost-optimal` | The path's cost is the minimum | The path costs 9, but the minimum is 8 |

How it is scored:

- **Valid** only when no constraint fails, and then the score is 1.0.
- **Score 0** when any of 1 to 11 fails: the answer is not a well-formed path, or not this puzzle's.
- **Otherwise** only `cost-optimal` fails: the path is valid but costlier, and the score is `minimum / cost`, at most 0.99. It is 0 when the minimum is 0.
- **The message** names the first failing constraint, why it fails, and how many more fail, e.g. `starts-at-start: The path begins at [2, 2], not at the start [0, 0] (+1 more)`. A valid verdict says `All 12 checks hold: a cheapest path, of cost 8.`
- **`details`** also holds `expected` (`reachable`, `optimal_cost`, an `example_path`) and `path_cost`, what the submitted path really costs.

Every tool call is checked as well:
- `verify_input` refuses `explore` cells that are walls, off the grid or repeated, and more than 100 cells.
- `verify_output` holds `get_puzzle` to the bundled puzzle, and holds `explore` to the exact open neighbors and costs.
- It also re-checks `pin_path` as constraint 1 does.
- `show-puzzle`'s verdict is that its output is the bundled puzzle.

## Limitations

- **The puzzles are public.** They ship in this repository, so a model trained on it could recall the answers instead of searching. Using a seed to draw a fresh puzzle per run would close this, at the cost of a fixed, reviewable set.
- **A fixed set of 25 puzzles, at most 10x10.** The hosted model replies in a few short steps, so grids stay small enough to solve by hand within them.
- **Only the final answer is judged.** The verifier checks the submitted path, not how the agent found it: a guessed path that happens to be cheapest passes.
- **Simple paths only.** A path may not revisit a cell. With costs of at least 0 a cheapest path never needs to, but an answer that loops through free cells is refused even though its cost is the minimum.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions (no network), tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # needed environment variable names (none here)
├── src/plugin/      # the MCP server (__main__.py), the tools (tools.py), the grid rules and Dijkstra (grid.py),
│                    #   the bundled puzzles (puzzles.py), and tools_dev/ (the puzzle generator and the case builder)
├── tests/           # offline tests: the verifier, the tools, the puzzle set against an independent oracle,
│                    #   and scripted cases under tests/cases/ replayed through the real tools and verifier
├── ui/              # how the page draws a puzzle and a path: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier: one module per tool, the task's 12 constraints in task.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Everything is offline and deterministic: no network, no clock, no randomness
at run time. The tools write nothing to `NANOAGENT_WORKSPACE`.

### Reproduce the verification without an LLM

Each case under `tests/cases/` scripts the agent: the `get_puzzle` and
`explore` calls it makes and the answer it submits, either the prescribed
path or the same run broken in one way. Each case also states the verdict it
expects:
- Gold cases hold all 12 constraints.
- Every other case fails the constraints it names, with the expected score.
- `explore_a_wall` expects the tool to refuse the call.

No model runs anywhere.

```bash
uv run pytest tests/test_cases.py -v
uv run python src/plugin/tools_dev/build_cases.py    # rebuilds tests/cases/
uv run python src/plugin/tools_dev/make_puzzles.py   # reprints the generated puzzles, as frozen in puzzles.py
```

Publishing checks every plugin rule: push the plugin to a public GitHub
repository and submit it on RUSH Lab.
