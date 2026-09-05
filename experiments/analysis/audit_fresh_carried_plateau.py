# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F58 -- fresh vs carried composition of the R3--R15 plateau window, per arm.

Why this exists: F46's headline plateau gap (no-graph arm mean 63.4, graph arm
mean 66.1, difference +2.7 tasks) is computed with carried rows included --
"a carried task is part of that round's bed score" -- because the no-op cost
mechanism restricts a no-ship round to a 25-task audit batch and carries the
other 75 tasks forward (Appendix B.2). Ship rate differs sharply by arm and
seed (F10: no-graph 0.88, graph 0.50/0.92/0.60), so the two arms plausibly
differ in how many audit-batch (partial re-draw) rounds they accumulate inside
the 13-round plateau window -- and until this script, no row stated the
fresh-vs-carried split, so a reader could not check whether the gap tracks
batching frequency rather than the graph (R4 Devil's Advocate, Issue #3 /
MAJOR #3).

Method mirrors audit_gain_face.py's per_round(): the last task_history row
wins per (round, task) on the common 100-task no-pixel subset (re-flights and
poisoned-round washes can leave more than one row; the clean prefix is
written last). A round with a carried row present is counted as-is, per F46's
own convention -- carrying is not undone here, only tallied.

Full-batch round: all 100 subset rows fresh (a whole-bed re-draw). Audit-batch
round: at least one carried row present (the 25-task no-op mechanism of
Appendix B.2).

Reports, per campaign: the 13 plateau rounds' fresh/carried counts and kind,
campaign totals, and full-batch vs audit-batch round counts; then arm totals
(three seeds pooled) for both arms.

Scope: whitelist only (ruling ii). Read-only over runs/.

Usage:  python experiments/analysis/audit_fresh_carried_plateau.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = [("baseline-seed1", "L0", 1), ("baseline-seed2", "L0", 2), ("baseline-seed3", "L0", 3),
        ("ghx-seed1", "GHX", 1), ("ghx-seed2", "GHX", 2), ("ghx-seed3", "GHX", 3)]
PLATEAU = range(3, 16)          # R3..R15, the plateau window F46 reports

SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def per_round_fresh_carried(run: str) -> dict[int, tuple[int, int]]:
    """round -> (n_fresh, n_carried) on the subset; last row wins per (round, task)."""
    last: dict[tuple[int, str], dict] = {}
    for line in (ROOT / "runs" / run / "data" / "task_history.jsonl").open(
            encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        tid = str(r.get("task_id"))
        if tid not in SUBSET:
            continue
        last[(int(r.get("round", -1)), tid)] = r
    fresh: dict[int, int] = {}
    carried: dict[int, int] = {}
    for (k, _), r in last.items():
        if r.get("carried"):
            carried[k] = carried.get(k, 0) + 1
        else:
            fresh[k] = fresh.get(k, 0) + 1
    return {k: (fresh.get(k, 0), carried.get(k, 0))
            for k in set(fresh) | set(carried)}


def main() -> None:
    print("=" * 96)
    print("F58  Fresh vs carried composition of the R3--R15 plateau window, "
          "six whitelist campaigns")
    print("=" * 96)

    # arm -> [fresh, carried, full-batch rounds, audit-batch rounds]
    arm_totals: dict[str, list[int]] = {"L0": [0, 0, 0, 0], "GHX": [0, 0, 0, 0]}
    for run, arm, seed in RUNS:
        rc = per_round_fresh_carried(run)
        print(f"\n--- {run}  ({arm}, seed {seed}) " + "-" * 40)
        print(f"{'round':>7s} {'fresh':>7s} {'carried':>9s}  kind")
        c_fresh = c_carried = c_full = c_audit = 0
        for k in PLATEAU:
            f, c = rc.get(k, (0, 0))
            if f == 100:
                kind = "full-batch"
            elif f + c > 0:
                kind = "audit-batch"
            else:
                kind = "MISSING"
            print(f"R{k:<6d} {f:7d} {c:9d}  {kind}")
            c_fresh += f
            c_carried += c
            c_full += 1 if kind == "full-batch" else 0
            c_audit += 1 if kind == "audit-batch" else 0
        print(f"  campaign totals: fresh={c_fresh}  carried={c_carried}  "
              f"full-batch rounds={c_full}/13  audit-batch rounds={c_audit}/13")
        arm_totals[arm][0] += c_fresh
        arm_totals[arm][1] += c_carried
        arm_totals[arm][2] += c_full
        arm_totals[arm][3] += c_audit

    print("\n" + "=" * 96)
    print("Arm totals, three seeds pooled, R3--R15 (13 rounds x 3 seeds = 39 "
          "round-campaign observations per arm)")
    print("=" * 96)
    for arm, (fresh, carried, full, audit) in arm_totals.items():
        total = fresh + carried
        pct = 100 * carried / total if total else 0.0
        print(f"{arm:6s}  fresh={fresh:5d}  carried={carried:5d}  "
              f"({pct:.1f}% of task-rounds carried)   "
              f"full-batch rounds={full}/39  audit-batch rounds={audit}/39")

    print("\nRead: a higher audit-batch-round count means more of that arm's "
          "plateau rounds\nheld 75 carried scores fixed and only re-drew 25 "
          "tasks -- a mechanical reason\nan arm's plateau could sit where it "
          "does independent of any graph effect.")


if __name__ == "__main__":
    main()
