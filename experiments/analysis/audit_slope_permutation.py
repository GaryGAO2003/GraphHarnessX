# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F47 -- within-campaign trend and the between-arm slope gap, with the exact
3-versus-3 permutation test the thesis quotes.

Why this exists: the thesis states six per-campaign slopes, a 1/64 sign test,
an arm-mean slope gap of +0.37 tasks per round at an exact permutation
p = 0.10, and a last-four-rounds gap of +5.25 at p = 0.15 -- and the ledger row
pointed at the plateau script, which computes none of them. A number with no
recompute script is the thing the fact ledger exists to prevent, so this lands
the recompute.

Per-round scores are recomputed from task_history on the common 100-task
no-pixel subset, last row per (round, task), carried rows included, exactly as
the plateau script does. The slope is ordinary least squares over R1..R15 with
R0 excluded (single baseline draw; seed 1's R0 is the k=2 round). The
permutation test is exact: with three seeds per arm there are C(6,3) = 20 ways
to assign six slopes to two arms of three, so the smallest attainable one-sided
p is 1/20 = 0.05 -- the design floor the thesis names.

Scope: whitelist only (ruling ii). Read-only over runs/.

Usage:  python experiments/analysis/audit_slope_permutation.py
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = [("baseline-seed1", "L0", 1, 15), ("baseline-seed2", "L0", 2, None), ("baseline-seed3", "L0", 3, None),
        ("ghx-seed1", "GHX", 1, None), ("ghx-seed2", "GHX", 2, None), ("ghx-seed3", "GHX", 3, None)]
WINDOW = range(1, 16)        # R1..R15, R0 dropped
LAST4 = range(12, 16)        # R12..R15
SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def per_round(run: str, cap: int | None) -> dict[int, int]:
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
    score: dict[int, int] = {}
    for (rd, tid), ok in last.items():
        score[rd] = score.get(rd, 0) + int(ok)
    return score


def ols_slope(xs: list[int], ys: list[int]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx


def sd(v: list[float]) -> float:
    m = sum(v) / len(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def exact_perm_p(a: list[float], b: list[float]) -> tuple[float, int, int]:
    """One-sided exact permutation p for mean(b) - mean(a) >= observed."""
    obs = sum(b) / len(b) - sum(a) / len(a)
    pool = a + b
    idx = range(len(pool))
    hits = total = 0
    for comb in itertools.combinations(idx, len(b)):
        bb = [pool[i] for i in comb]
        aa = [pool[i] for i in idx if i not in comb]
        total += 1
        if sum(bb) / len(bb) - sum(aa) / len(aa) >= obs - 1e-12:
            hits += 1
    return hits / total, hits, total


def main() -> None:
    print("=" * 78)
    print("F47  Within-campaign trend, R1..R15, common 100-task subset")
    print("=" * 78)
    slopes: dict[str, list[float]] = {"L0": [], "GHX": []}
    last4: dict[str, list[float]] = {"L0": [], "GHX": []}
    for run, arm, seed, cap in RUNS:
        s = per_round(run, cap)
        xs = [r for r in WINDOW if r in s]
        ys = [s[r] for r in xs]
        b = ols_slope(xs, ys)
        l4 = sum(s[r] for r in LAST4 if r in s) / len([r for r in LAST4 if r in s])
        slopes[arm].append(b)
        last4[arm].append(l4)
        print(f"  {run:14s} {arm:4s} seed {seed}   slope {b:+.3f} tasks/round   "
              f"last-4 mean {l4:5.2f}   rounds {[s[r] for r in range(0, 16) if r in s]}")

    pos = sum(1 for v in slopes["L0"] + slopes["GHX"] if v > 0)
    print(f"\n  positive slopes: {pos}/6   sign-test p under no-trend null = 1/64 = {1/64:.3f}")
    for arm in ("L0", "GHX"):
        v = slopes[arm]
        print(f"  {arm:4s} slopes {['%+.2f' % x for x in v]}  arm mean {sum(v)/3:+.3f}  SD {sd(v):.3f}")
    gap = sum(slopes["GHX"]) / 3 - sum(slopes["L0"]) / 3
    p, h, n = exact_perm_p(slopes["L0"], slopes["GHX"])
    print(f"  slope gap (GHX - L0) {gap:+.3f} tasks/round   exact one-sided permutation p = {h}/{n} = {p:.2f}")
    for arm in ("L0", "GHX"):
        v = last4[arm]
        print(f"  {arm:4s} last-4 means {['%.2f' % x for x in v]}  arm mean {sum(v)/3:.2f}")
    gap4 = sum(last4["GHX"]) / 3 - sum(last4["L0"]) / 3
    p4, h4, n4 = exact_perm_p(last4["L0"], last4["GHX"])
    print(f"  last-4 gap (GHX - L0) {gap4:+.2f} tasks   exact one-sided permutation p = {h4}/{n4} = {p4:.2f}")
    print("\n  Design floor: with 3 seeds per arm the smallest attainable one-sided p is 1/20 = 0.05.")


if __name__ == "__main__":
    main()
