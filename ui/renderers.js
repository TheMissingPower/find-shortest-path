// How this plugin's page draws its tasks' outputs: a puzzle as a grid of costs with its walls, start
// and target marked, and an answer as its cost and its path, step by step. Every other output is drawn
// from its JSON Schema. Each renderer is (value, {task, verdict, send}) => Element.
import { h } from "./kit/components.js";

const cellKey = (cell) => `${cell.row},${cell.col}`;
const cellText = (cell) => `(${cell.row}, ${cell.col})`;

function puzzleGrid(puzzle) {
  const start = cellKey(puzzle.start);
  const target = cellKey(puzzle.target);
  const rows = puzzle.grid.map((line, row) =>
    h(
      "tr",
      {},
      [...line].map((char, col) => {
        const key = `${row},${col}`;
        const classes = ["cell"];
        if (char === "#") classes.push("wall");
        if (key === start) classes.push("start");
        if (key === target) classes.push("target");
        const label = key === start ? "S" : key === target ? "T" : "";
        return h("td", { class: classes.join(" "), title: `(${row}, ${col})` }, char === "#" ? "" : char, label ? h("sup", { text: label }) : null);
      }),
    ),
  );
  return h("table", { class: "grid" }, h("tbody", {}, rows));
}

function drawPuzzle(puzzle) {
  return h(
    "div",
    { class: "puzzle" },
    h("p", { class: "heading", text: `${puzzle.puzzle_id}: ${puzzle.rows} x ${puzzle.cols}, from ${cellText(puzzle.start)} to ${cellText(puzzle.target)}` }),
    puzzleGrid(puzzle),
    h("p", { class: "rule", text: puzzle.rule }),
  );
}

function drawPath(answer) {
  if (!answer.reachable) {
    return h("div", { class: "answer" }, h("p", { class: "heading", text: `${answer.puzzle_id}: the target cannot be reached` }));
  }
  return h(
    "div",
    { class: "answer" },
    h("p", { class: "heading", text: `${answer.puzzle_id}: cost ${answer.cost}, ${answer.path.length} cell(s)` }),
    h("p", { class: "steps", text: answer.path.map(cellText).join(" → ") }),
  );
}

export default { PuzzleOutput: drawPuzzle, PathOutput: drawPath };
