# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F60 -- Spearman-Brown repetition-pricing for the same-config flip rate.

Why this exists: ch/05-design.tex:186-190 and ch/07-discussion.tex:312-318
both promise this calculation and never carry it out (R3 Perspective,
"Other"; P2-10). Bed reliability cannot be bought by item selection (F54: the
21 stable tasks carry no variance, the 79 volatile ones are the instrument,
not noise to be filtered out) -- only by repeated measurement. This prices
that in repeats, using only figures already on the page.

Single-draw reliability r1 is recovered from two numbers, both restricted to
exactly the population F15/F9e's flip rate is measured over (the three
no-graph seeds' full-batch same-config windows, common 100-task subset): the
flip rate f (self-checked against F15/F9e's printed 402/2000 below) and the
marginal pass rate p_bar over every task-round cell entering that same
computation. Model: each task has its own pass propensity pi_i; two
independent draws of the same task are Bernoulli(pi_i) given pi_i. Standard
result for that model (the two-rater, equal-marginals identity behind Scott's
pi / Fleiss's kappa): two draws disagree with probability
    f = 2 * p_bar * (1 - p_bar) * (1 - r1)
where r1 = Var(true pi_i) / Var(observed X) is exactly the classical-test-
theory reliability of one draw. Solving: r1 = 1 - f / (2 * p_bar * (1 - p_bar)).

Spearman-Brown then prices k repeats, averaged: r_k = k*r1 / (1 + (k-1)*r1).
The target used to headline one number, 0.80, is not imported from outside
the thesis -- it is this thesis's own bar for calling a task "reliable"
(F16/F54: pass rate >= 80%).

Scope: whitelist no-graph arms only (ruling ii), same population as F15/F9e.
Read-only over runs/.

Usage:  python experiments/analysis/audit_spearman_brown.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_flip_rate_three_seeds as base  # noqa: E402

TARGET = 0.80   # this thesis's own "reliable" bar (F16/F54: pass rate >= 80%)
MAX_K = 30


def main() -> int:
    flips = total = passes = obs = 0
    for run, _seed in base.RUNS:
        res = base.outcomes(run)
        for a, b in base.windows(run, res):
            common = set(res[a]) & set(res[b])
            if len(common) < base.FULL_MIN:
                continue
            for t in common:
                flips += res[a][t] != res[b][t]
                passes += res[a][t] + res[b][t]
                total += 1
                obs += 2

    print("=" * 78)
    print("F60  Spearman-Brown repetition pricing on F15/F9e's population")
    print("=" * 78)
    if (flips, total) != (402, 2000):
        print(f"REFUSING TO REPORT -- flip count {flips}/{total} disagrees "
              f"with F15/F9e's printed 402/2000")
        return 1
    print(f"self-check: {flips}/{total} reproduces F15/F9e's pooled flip "
          f"count exactly.\n")

    f = flips / total
    p = passes / obs
    r1 = 1 - f / (2 * p * (1 - p))
    print(f"flip rate            f     = {flips}/{total} = {100*f:.2f}%")
    print(f"marginal pass rate   p_bar = {passes}/{obs} = {100*p:.2f}%")
    print(f"single-draw reliability r1 = 1 - f/(2 p_bar (1-p_bar)) = {r1:.3f}")

    print(f"\nSpearman-Brown price schedule (k repeats, averaged):")
    print(f"{'k':>3s} {'r_k':>7s}")
    crossed = None
    for k in range(1, MAX_K + 1):
        rk = k * r1 / (1 + (k - 1) * r1)
        mark = ""
        if crossed is None and rk >= TARGET:
            crossed = (k, rk)
            mark = f"  <-- first k reaching this thesis's own 0.80 " \
                   f"'reliable' bar (F16/F54)"
        print(f"{k:3d} {rk:7.3f}{mark}")
        if crossed is not None:
            break

    print()
    if crossed:
        k, rk = crossed
        print(f"HEADLINE: r1={r1:.2f}; k={k} averaged repeats reach "
              f"Spearman-Brown reliability {rk:.2f} >= {TARGET:.2f}.")
    else:
        print(f"HEADLINE: r1={r1:.2f} does not reach {TARGET:.2f} within "
              f"{MAX_K} repeats.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
