"""Report bed-level reference-answer lengths (not F3 sample statistics).

The F3 sample median and p90 are computed from the false-negative sample by a
separate analysis. This program checks only the related bed-level statement for
the common 100-task subset and, when available, the initial 103-task bed.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(
    os.environ.get("GHX_DATA_ROOT", ROOT / "recipe/gaia_evolver/data")
)
FILES = {
    "100-task no-pixel subset": "webthinker_gaia_dev_nopixel.json",
    "103-task text-only bed": "webthinker_gaia_dev.json",
}
ANSWER_KEYS = (
    "final_answer", "Final answer", "answer", "true_answer",
    "expected_answer", "ground_truth",
)


def answer_of(task: dict) -> str | None:
    for key in ANSWER_KEYS:
        if key in task and task[key] is not None:
            return str(task[key])
    return None


def percentile_90(values: list[int]) -> float:
    ordered = sorted(values)
    index = 0.9 * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="GAIA bed directory (default: GHX_DATA_ROOT or repository data path)",
    )
    args = parser.parse_args()
    found = False
    for label, filename in FILES.items():
        path = args.data_root / filename
        if not path.is_file():
            print(f"PREREQUISITE: {label} not present: {path}")
            continue
        found = True
        tasks = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(tasks, dict):
            tasks = list(tasks.values())
        lengths = [len(answer.strip()) for task in tasks if (answer := answer_of(task))]
        if not lengths:
            print(f"ERROR: {label} has no recognised reference-answer field")
            return 1
        under_20 = sum(length < 20 for length in lengths)
        print(
            f"{label}: n={len(lengths)} median={statistics.median(lengths):.0f} "
            f"p90={percentile_90(lengths):.0f} mean={statistics.mean(lengths):.1f} "
            f"max={max(lengths)} under20={under_20}/{len(lengths)}"
        )
    return 0 if found else 2


if __name__ == "__main__":
    raise SystemExit(main())
