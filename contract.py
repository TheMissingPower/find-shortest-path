"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    PIN_PATH = "pin_path"
    GET_PUZZLE = "get_puzzle"
    EXPLORE = "explore"


class Task(Enum):
    SHORTEST_PATH = "shortest-path"
    SHOW_PUZZLE = "show-puzzle"


# The bundled puzzles, by id: src/plugin/puzzles.py holds each one, and a test keeps the two in step.
class PuzzleId(Enum):
    WARMUP_3X3 = "warmup-3x3"
    SINGLE_CELL = "single-cell"
    START_IS_TARGET = "start-is-target"
    ONE_ROW = "one-row"
    ONE_COLUMN = "one-column"
    NEXT_DOOR = "next-door"
    ALL_ZERO = "all-zero"
    ALL_TIES = "all-ties"
    DETOUR = "detour"
    TOLL_GATE = "toll-gate"
    ZERO_CORRIDOR = "zero-corridor"
    SPIRAL = "spiral"
    REVERSE_CORNERS = "reverse-corners"
    WALLED_TARGET = "walled-target"
    BOXED_START = "boxed-start"
    SPLIT_BOARD = "split-board"
    GEN_5X5 = "gen-5x5"
    GEN_6X6 = "gen-6x6"
    GEN_7X7 = "gen-7x7"
    GEN_7X7_LOW_COSTS = "gen-7x7-low-costs"
    GEN_8X8 = "gen-8x8"
    GEN_8X8_DENSE_WALLS = "gen-8x8-dense-walls"
    GEN_9X9 = "gen-9x9"
    GEN_10X10 = "gen-10x10"
    GEN_10X10_MAZE = "gen-10x10-maze"


PUZZLE = "The puzzle's id, e.g. warmup-3x3"
GRID = (
    "The grid's rows, top to bottom: each character is a digit 0-9, the cost of entering that open cell, or # for a "
    "wall. Row 0 is the top row and column 0 the leftmost"
)
RULE = (
    "Move up, down, left or right, one cell a step, never onto # or off the grid, never visiting a cell twice. A "
    "path's cost is the sum of the digits of every cell on it, the start and the target included"
)


@dataclass
class Cell(Output):
    row: Annotated[int, "Row index, 0 at the top"]
    col: Annotated[int, "Column index, 0 at the left"]


@dataclass
class PuzzleInput(Output):
    puzzle_id: Annotated[PuzzleId, PUZZLE]


@dataclass
class PuzzleOutput(Output):
    puzzle_id: Annotated[PuzzleId, PUZZLE]
    rows: Annotated[int, "How many rows the grid has"]
    cols: Annotated[int, "How many columns the grid has"]
    grid: Annotated[list[str], GRID]
    start: Annotated[Cell, "Where every path begins; its cost counts"]
    target: Annotated[Cell, "Where every path ends; its cost counts"]
    rule: Annotated[str, "The move and cost rules, in words"]


@dataclass
class ExploreInput(Output):
    puzzle_id: Annotated[PuzzleId, PUZZLE]
    cells: Annotated[list[Cell], "1 to 100 distinct open cells of the puzzle's grid to look around"]


@dataclass
class Neighbor(Output):
    cell: Cell
    cost: Annotated[int, "The cost of entering this cell"]


@dataclass
class CellNeighbors(Output):
    cell: Cell
    cost: Annotated[int, "The cost of entering this cell"]
    neighbors: Annotated[list[Neighbor], "The open cells one move away, in the order up, right, down, left"]


@dataclass
class ExploreOutput(Output):
    puzzle_id: Annotated[PuzzleId, PUZZLE]
    cells: Annotated[list[CellNeighbors], "Each asked cell, in the order asked, with its cost and open neighbors"]


@dataclass
class PinOutput(Output):
    puzzle_id: Annotated[PuzzleId, PUZZLE]
    grid: Annotated[list[str], GRID]
    start: Cell
    target: Cell
    sha256: Annotated[str, "sha256 of the puzzle's canonical JSON: its grid, start and target"]
    reachable: Annotated[bool, "Whether any path joins the start to the target"]
    optimal_cost: Annotated[int | None, "The minimum path cost; null when the target cannot be reached"]
    example_path: Annotated[list[Cell], "One path of the minimum cost, start to target; [] when unreachable"]


@dataclass
class PathOutput(Output):
    puzzle_id: Annotated[PuzzleId, PUZZLE]
    reachable: Annotated[bool, "Whether any path joins the start to the target"]
    cost: Annotated[
        int | None, "The cost of the path: the sum of the digits of every cell on it; null when unreachable"
    ]
    path: Annotated[
        list[Cell],
        "A cheapest path, every cell from the start to the target inclusive, each one move from the last; "
        "[] when unreachable",
    ]


TOOLS = {
    Tool.PIN_PATH: (PuzzleInput, PinOutput),
    Tool.GET_PUZZLE: (PuzzleInput, PuzzleOutput),
    Tool.EXPLORE: (ExploreInput, ExploreOutput),
}
TASKS = {
    Task.SHORTEST_PATH: (PuzzleInput, PathOutput),
    Task.SHOW_PUZZLE: (PuzzleInput, PuzzleOutput),
}
