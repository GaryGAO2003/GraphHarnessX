# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F57 -- task-clustered bootstrap CI on F15/F9e's pooled same-config flip rate.

Why this exists: F15/F9e report a 95% Wilson interval on the same-config flip
rate as though each of the 2,000 task-pairs were an independent Bernoulli draw.
But F41/F54 already establish that flip propensity is a property of the TASK,
not of the draw -- 21 tasks with zero variance across every window they sit
in, 79 "volatile" tasks, and a recently-flipped task re-flipping at 1.6-2.1x
the bed rate. Twenty window-level observations per task are repeated measures
on 100 heterogeneous units, not 2,000 independent draws; treating them as
independent typically understates the true sampling variance (a
design-effect/ICC problem), the same fix the thesis already applies to the
candidate-level lift bootstrap (audit_lift_uncertainty.py) but had not yet
applied here (R1 methodology review, W1).

This script imports its window definitions -- RUNS, FULL_MIN, SUBSET,
outcomes(), windows(), wilson() -- unchanged from audit_flip_rate_three_seeds.py
(F15's own script) rather than redefining them, so the pairs entering this
bootstrap are byte-identical to the ones F15/F9e already report. A self-check
below refuses to print anything unless the per-seed and pooled point estimates
reproduce that script's numbers exactly.

Resampling unit: the TASK (one of the common 100-task subset), not the pair.
Drawing task t in a replicate means drawing every flip/no-flip outcome t
contributed across every full-batch same-config window in scope, so a task
that sat in eight windows carries all eight into the replicate together. This
preserves whatever within-task correlation exists; resampling pairs directly
(the naive/Wilson approach) does not.

10,000 replicates, fixed seed 20260904, percentile interval, for the pooled
rate (all three seeds' windows, resampling the one shared 100-task population)
and for each seed on its own windows.

Scope: whitelist no-graph arms only (ruling ii), same as the imported script.
Read-only over runs/.

Usage:  python experiments/analysis/audit_flip_rate_cluster_ci.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_flip_rate_three_seeds as base  # noqa: E402

N_BOOT = 10_000
SEED = 20260904

# Ledger point estimates (F9e) this script must reproduce before it will report.
EXPECTED_SEED = {1: (126, 600), 2: (161, 800), 3: (115, 600)}
EXPECTED_POOLED = (402, 2000)


def task_flip_lists(run: str) -> dict[str, list[int]]:
    """task_id -> [0/1 flip indicator, one per full-batch same-config window].

    Reproduces exactly the filtering audit_flip_rate_three_seeds.py's main()
    applies (base.windows() for the pairs, >= base.FULL_MIN common rows to
    count as a full batch) so the pooled counts below match that script's
    printed per-seed line -- checked in main() before any interval is
    reported.
    """
    res = base.outcomes(run)
    wins = base.windows(run, res)
    data: dict[str, list[int]] = {t: [] for t in base.SUBSET}
    for a, b in wins:
        common = set(res[a]) & set(res[b])
        if len(common) < base.FULL_MIN:
            continue
        for t in common:
            data[t].append(1 if res[a][t] != res[b][t] else 0)
    return data


def counts(data: dict[str, list[int]]) -> tuple[int, int]:
    return sum(sum(v) for v in data.values()), sum(len(v) for v in data.values())


def cluster_ci(data: dict[str, list[int]], tasks: list[str], rng: random.Random,
               n_boot: int = N_BOOT) -> tuple[float, float]:
    """Percentile 95% CI, resampling `tasks` (with replacement) as clusters."""
    n_tasks = len(tasks)
    boots: list[float] = []
    for _ in range(n_boot):
        f = n = 0
        for _ in range(n_tasks):
            v = data[tasks[rng.randrange(n_tasks)]]
            f += sum(v)
            n += len(v)
        if n:
            boots.append(f / n)
    boots.sort()
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return lo, hi


def main() -> int:
    rng = random.Random(SEED)
    tasks = sorted(base.SUBSET)

    print("=" * 88)
    print("F57  Task-clustered bootstrap 95% CI on the same-config flip rate "
          f"(F15/F9e), N={N_BOOT} replicates, seed={SEED}")
    print("=" * 88)

    per_seed: dict[int, dict[str, list[int]]] = {}
    pooled: dict[str, list[int]] = {t: [] for t in base.SUBSET}
    for run, seed in base.RUNS:
        data = task_flip_lists(run)
        per_seed[seed] = data
        for t, v in data.items():
            pooled[t].extend(v)

    # --- refusal gate: reproduce F15/F9e's printed point estimates exactly ---
    bad = []
    for seed, expected in EXPECTED_SEED.items():
        got = counts(per_seed[seed])
        if got != expected:
            bad.append(f"seed {seed}: got {got[0]}/{got[1]}, ledger says "
                        f"{expected[0]}/{expected[1]}")
    got_pooled = counts(pooled)
    if got_pooled != EXPECTED_POOLED:
        bad.append(f"pooled: got {got_pooled[0]}/{got_pooled[1]}, ledger says "
                    f"{EXPECTED_POOLED[0]}/{EXPECTED_POOLED[1]}")
    if bad:
        print("\nREFUSING TO REPORT -- point estimates disagree with F15/F9e:")
        for b in bad:
            print("   ", b)
        return 1
    print("\nself-check: per-seed and pooled point estimates reproduce F15/F9e "
          "exactly\n(126/600, 161/800, 115/600, pooled 402/2000).\n")

    print(f"{'group':>9s} {'k/n':>11s} {'point':>7s} "
          f"{'naive Wilson 95%':>19s}   {'task-clustered 95%':>19s}")
    for seed in (1, 2, 3):
        f, n = counts(per_seed[seed])
        point = 100 * f / n
        wlo, whi = base.wilson(f, n)
        clo, chi = cluster_ci(per_seed[seed], tasks, rng)
        print(f"{'seed ' + str(seed):>9s} {f:4d}/{n:<6d} {point:6.1f}% "
              f"  [{wlo:5.1f}, {whi:5.1f}]      "
              f"  [{100*clo:5.1f}, {100*chi:5.1f}]")

    f, n = got_pooled
    point = 100 * f / n
    wlo, whi = base.wilson(f, n)
    clo, chi = cluster_ci(pooled, tasks, rng)
    print(f"{'pooled':>9s} {f:4d}/{n:<6d} {point:6.1f}% "
          f"  [{wlo:5.1f}, {whi:5.1f}]      "
          f"  [{100*clo:5.1f}, {100*chi:5.1f}]")

    print("\n" + "=" * 88)
    print("Read: the task-clustered interval is the wider of the two whenever "
          "flip\npropensity is a property of the task rather than of the draw; "
          "the naive Wilson\ninterval treats every task-pair as an independent "
          "Bernoulli trial, which F41/F54\nalready show it is not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
