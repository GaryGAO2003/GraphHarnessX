# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F46 -- both arms, three seeds, recomputed on the common 100-task subset.

Why this exists: the arms flew different beds. The no-graph arm ran the full
103-task bed on seeds 1-2, the graph arms ran the 100-task no-pixel subset, and
the seed-3 no-graph arm switched beds at R7 mid-campaign. ``curves.json`` records
whatever bed each round actually ran, so its numbers are not comparable across
arms -- and the seed-3 no-graph curve is not even comparable with itself across
R6/R7. Every readout here is recomputed from ``task_history.jsonl`` restricted to
the 100-task no-pixel subset, which makes all six campaigns one denominator.

What it reports, per campaign:
  * per-round score on the 100-task subset (last row per (round, task); carried
    rows included, because a carried task is part of that round's bed score);
  * R0, terminal, and R0->terminal delta -- the number a reader reaches for and
    the one that misleads, since R0 is a single draw;
  * plateau R3--R15 (the thesis's standing readout) with its SD;
  * an early/late split, mean(R1--R7) vs mean(R8--R15), which is the campaign
    trend with R0's draw removed;
  * regression-to-the-mean check: correlation between R0 and the R0->terminal
    delta across the six arms. If R0 is a noisy draw this is strongly negative
    and the "improvement" ranking is an artifact of where each arm started.

Deliberately NOT reported: any between-arm difference test. The arms remain
non-comparable for the reasons in F9c (different candidate populations, gate
regimes); putting both on one bed fixes the denominator, not the design.

Scope: whitelist only (ruling II).

Usage:  python experiments/analysis/audit_three_seed_plateau.py
"""
from __future__ import annotations

import collections
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = [("baseline-seed1", "L0", 1), ("baseline-seed2", "L0", 2), ("baseline-seed3", "L0", 3),
        ("ghx-seed1", "GHX", 1), ("ghx-seed2", "GHX", 2), ("ghx-seed3", "GHX", 3)]
WINDOW = range(0, 16)          # the 16-round presentation convention (ruling ii)
FULL_MIN = 80                  # fresh subset rows at or above this = full batch

SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def per_round(run: str):
    """(score, fresh_count) per round on the 100-task subset.

    Last row wins per (round, task): re-flights and poisoned-round washes can
    leave more than one row, and the clean prefix is written last.
    """
    last: dict[tuple[int, str], dict] = {}
    for line in (ROOT / "runs" / run / "data" / "task_history.jsonl").open(
            encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        tid = str(r.get("task_id"))
        if tid not in SUBSET:
            continue
        last[(int(r.get("round", -1)), tid)] = r
    score: dict[int, int] = collections.defaultdict(int)
    fresh: dict[int, int] = collections.defaultdict(int)
    for (k, _), r in last.items():
        score[k] += 1 if r.get("passed") else 0
        if not r.get("carried"):
            fresh[k] += 1
    return score, fresh


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs):
    if len(xs) < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    mx, my = mean(xs), mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return num / den if den else float("nan")


def main() -> None:
    print("=" * 100)
    print("F46  Three seeds x two arms, all recomputed on the 100-task no-pixel subset")
    print("=" * 100)
    print(f"{'run':16s} {'arm':4s} {'seed':>4s} {'R0':>4s} {'Rend':>5s} {'delta':>6s} "
          f"{'plateau R3-15':>14s} {'early R1-7':>11s} {'late R8-15':>11s} {'late-early':>10s} {'full':>5s}")
    rows = []
    for run, arm, seed in RUNS:
        score, fresh = per_round(run)
        ks = [k for k in WINDOW if k in score]
        ys = [score[k] for k in ks]
        r0, rend = score.get(0, float("nan")), ys[-1]
        plat = [score[k] for k in range(3, 16) if k in score]
        early = [score[k] for k in range(1, 8) if k in score]
        late = [score[k] for k in range(8, 16) if k in score]
        nfull = sum(1 for k in ks if fresh.get(k, 0) >= FULL_MIN)
        rows.append((run, arm, seed, r0, rend, rend - r0,
                     mean(plat), sd(plat), mean(early), mean(late), mean(late) - mean(early)))
        print(f"{run:16s} {arm:4s} {seed:4d} {r0:4.0f} {rend:5.0f} {rend-r0:+6.0f} "
              f"{mean(plat):8.1f}+-{sd(plat):3.1f} {mean(early):11.1f} {mean(late):11.1f} "
              f"{mean(late)-mean(early):+10.1f} {nfull:3d}/{len(ks)}")
        print(f"{'':16s} per-round: {[int(v) for v in ys]}")

    print()
    print("=" * 100)
    print("Regression to the mean: does the R0->terminal 'improvement' just track where R0 landed?")
    print("=" * 100)
    r0s = [r[3] for r in rows]
    deltas = [r[5] for r in rows]
    print(f"  R0 across the six arms : {[int(x) for x in r0s]}")
    print(f"  R0->terminal delta     : {[int(x) for x in deltas]}")
    print(f"  Pearson r(R0, delta)   : {pearson(r0s, deltas):+.3f}   (n=6)")
    print("  Read: a strongly negative r means the arms that 'improved most' are the")
    print("  arms whose first round happened to land low. R0 is one draw from a bed")
    print("  whose same-config swing is -8..+5 tasks, so R0->terminal is not a trend.")

    print()
    print("=" * 100)
    print("The trend with R0 removed: mean(R8-R15) - mean(R1-R7), per arm")
    print("=" * 100)
    for arm in ("L0", "GHX"):
        d = [r[10] for r in rows if r[1] == arm]
        print(f"  {arm:4s} seeds 1/2/3: {['%+.1f' % x for x in d]}   mean {mean(d):+.1f}  SD {sd(d):.1f}")
    l0 = [r[10] for r in rows if r[1] == "L0"]
    gx = [r[10] for r in rows if r[1] == "GHX"]
    print(f"  gap (GHX - L0) of arm means: {mean(gx)-mean(l0):+.1f} tasks")
    print("  NOT a difference test: n=3 per arm, the SDs above, and F9c's population")
    print("  objections all stand. Reported so the direction is on the record, not so")
    print("  it can be read as separation.")

    print()
    print("=" * 100)
    print("Plateau, the thesis's standing readout, all six on one bed")
    print("=" * 100)
    for arm in ("L0", "GHX"):
        p = [r[6] for r in rows if r[1] == arm]
        print(f"  {arm:4s} plateaus: {['%.1f' % x for x in p]}   arm mean {mean(p):.1f}  SD {sd(p):.1f}")
    print(f"  arm-mean gap: {mean([r[6] for r in rows if r[1]=='GHX']) - mean([r[6] for r in rows if r[1]=='L0']):+.1f} tasks")
    print("  Same-config single-window envelope is -8..+5 tasks (F15/F44/F45).")


if __name__ == "__main__":
    main()
