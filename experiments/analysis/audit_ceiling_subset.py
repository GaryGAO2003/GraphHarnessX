# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F16 -- reachability and reliability ceilings, on the reported bed.

Why this exists: F16 was computed over two seed-1 runs on the 103-task bed
(96 reachable, 7 never solved, 46 unreliable) while F54 was computed over all
six campaigns on the 100-task no-pixel subset (3 never solved, 18 always pass,
79 volatile). Two scopes for the same family of facts is exactly the
inconsistency the one-bed rule exists to remove, so this recomputes the ceiling
family on the bed the thesis reports -- the 100-task subset -- over the same six
claim-bearing campaigns F54 uses, each read over its formal sixteen-round
window.

A task's outcome in a round is the last row for that (round, task): re-flights
and poisoned-round washes leave more than one, and the clean prefix is written
last. Carried rows count, because a carried task is part of that round's score.

Scope: whitelist only (ruling ii). Read-only over runs/.

Usage:  python experiments/analysis/audit_ceiling_subset.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = {"baseline-seed1": 15, "ghx-seed1": None, "baseline-seed2": None,
        "ghx-seed2": None, "baseline-seed3": None, "ghx-seed3": None}
SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def cells() -> tuple[dict[str, list[bool]], dict[tuple[str, int], int]]:
    """(task -> outcomes across all campaign rounds, (run, round) -> score)."""
    per: dict[str, list[bool]] = collections.defaultdict(list)
    scores: dict[tuple[str, int], int] = collections.Counter()
    for run, cap in RUNS.items():
        last: dict[tuple[int, str], bool] = {}
        fp = ROOT / "runs" / run / "data" / "task_history.jsonl"
        for line in fp.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            rd, tid = r.get("round"), r.get("task_id")
            if rd is None or tid not in SUBSET:
                continue
            rd = int(rd)
            if cap is not None and rd > cap:
                continue
            last[(rd, tid)] = bool(r.get("passed"))
        for (rd, tid), ok in last.items():
            per[tid].append(ok)
            if ok:
                scores[(run, rd)] += 1
    return per, scores


def main() -> None:
    per, scores = cells()
    n_cells = sum(len(v) for v in per.values())

    never = sorted(t for t, v in per.items() if not any(v))
    always = [t for t, v in per.items() if all(v)]
    reachable = [t for t, v in per.items() if any(v)]

    print("=" * 76)
    print("Ceilings on the common 100-task no-pixel subset, six campaigns")
    print("=" * 76)
    print(f"tasks: {len(per)}   task-round cells: {n_cells}")
    print(f"  reachable (solved at least once) : {len(reachable)}")
    print(f"  NEVER solved                     : {len(never)}")
    for t in never:
        print(f"      {t[:8]}  attempts={len(per[t])}")
    print(f"  always solved (100%)             : {len(always)}")

    print("\nreliability of the reachable tasks:")
    bands = collections.Counter()
    for t in reachable:
        v = per[t]
        rate = sum(v) / len(v)
        if rate == 1.0:
            bands["always (100%)"] += 1
        elif rate >= 0.8:
            bands["reliable (>=80%)"] += 1
        elif rate >= 0.2:
            bands["flaky (20-80%)"] += 1
        else:
            bands["rare (<20%)"] += 1
    for k in ["always (100%)", "reliable (>=80%)", "flaky (20-80%)", "rare (<20%)"]:
        print(f"  {k:20s} {bands[k]:3d}")
    unreliable = len(reachable) - bands["always (100%)"] - bands["reliable (>=80%)"]
    print(f"\nreachable but unreliable (<80%): {unreliable} tasks")

    best_run, best_round = max(scores, key=scores.get)
    best = scores[max(scores, key=scores.get)]
    print(f"\nbest single round ever recorded : {best} "
          f"({best_run} R{best_round})")
    print(f"union of tasks ever solved      : {len(reachable)}")
    print(f"gap between them                : {len(reachable) - best} tasks")
    print("\nRead: a loop optimising one round's score is optimising a number "
          f"{len(reachable) - best}\nbelow what its own history has already "
          "achieved.")


if __name__ == "__main__":
    main()
