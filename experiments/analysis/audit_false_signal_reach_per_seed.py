"""Audit per-seed reach of the legacy false-output-use dossier signal.

F4 counts no-graph dossiers with at least one entry under the legacy heuristic
heading; its denominator is every dossier in the arm. F7 counts graph-arm
dossiers that retain the heading; seed 1 uses M26b R2--R15 and seeds 2/3 use all
rounds. The recorded seed-1 F4 and F7 values are fail-closed self-checks.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_ROOT = Path(
    os.environ.get("GHX_RUNS_ROOT", ROOT / "recipe/gaia_evolver/runs")
)
HEADING = "### Tool calls whose output the next step did NOT reference"
ENTRY_RE = re.compile(r"^- \*\*r", re.MULTILINE)
NEXT_HEADING_RE = re.compile(r"\n#{2,3} ")
ROUND_RE = re.compile(r"^R(\d+)$")


def scan_run(
    runs_root: Path, run: str, lower: int | None = None, upper: int | None = None
) -> tuple[int, int, int]:
    total = present = reach = 0
    for path in (runs_root / run).glob("**/digests/*.md"):
        round_number = next(
            (int(match.group(1)) for part in path.parts if (match := ROUND_RE.match(part))),
            None,
        )
        if lower is not None and (round_number is None or round_number < lower):
            continue
        if upper is not None and (round_number is None or round_number > upper):
            continue
        total += 1
        text = path.read_text(encoding="utf-8")
        if HEADING not in text:
            continue
        present += 1
        body = text.split(HEADING, 1)[1]
        next_heading = NEXT_HEADING_RE.search(body)
        body = body[: next_heading.start()] if next_heading else body
        reach += bool(ENTRY_RE.search(body))
    return total, present, reach


def percentage(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="campaign archive root (default: GHX_RUNS_ROOT or repository runs path)",
    )
    args = parser.parse_args()
    required = ("M22_L0_ghx0", "M26_100x16b")
    missing = [name for name in required if not (args.runs_root / name).is_dir()]
    if missing:
        print(f"PREREQUISITE: missing campaign archives: {', '.join(missing)}")
        return 2

    m22_total, _, m22_reach = scan_run(args.runs_root, "M22_L0_ghx0")
    m26_total, m26_present, _ = scan_run(
        args.runs_root, "M26_100x16b", lower=2, upper=15
    )
    expected = ((m22_reach, m22_total), (m26_present, m26_total))
    if expected != ((1239, 1441), (0, 859)):
        print(
            "ERROR: recorded self-check failed: "
            f"F4={m22_reach}/{m22_total}, F7={m26_present}/{m26_total}"
        )
        return 1

    print(
        f"F4 seed 1 M22_L0_ghx0: {m22_reach}/{m22_total} "
        f"({percentage(m22_reach, m22_total):.1f}%)"
    )
    for seed, run in ((2, "M28_L0_s2"), (3, "M29_L0_s3")):
        total, _, reach = scan_run(args.runs_root, run)
        print(f"F4 seed {seed} {run}: {reach}/{total} ({percentage(reach, total):.1f}%)")
    print(f"F7 seed 1 M26_100x16b R2-R15: {m26_present}/{m26_total}")
    for seed, run in ((2, "M28_GHX_s2"), (3, "M29_GHX_s3")):
        total, present, _ = scan_run(args.runs_root, run)
        print(f"F7 seed {seed} {run}: {present}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
