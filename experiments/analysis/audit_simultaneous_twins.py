# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""One-window observations and a conditional repetition sensitivity model.

F15/F9e measure the flip rate between two ADJACENT ship-free rounds: the config
is identical but the two draws are separated by a scheduling window (tens of
minutes).  That reading cannot tell apart two very different worlds:

  (a) the bed is stable within an instant and DRIFTS between windows, or
  (b) the bed is already this noisy at a single instant and time adds nothing.

The observations establish draw-level variation within one scheduling batch.
They do not test independence among task errors, repeated draws, or windows.

The M22-L0 baseline campaign scored round 0 at k=2: every task carries TWO
rollouts issued in the same batch under one config.  That is a same-instant
re-measurement of the whole bed.  It supports the following comparison:

  * simultaneous flip rate  = E[2p(1-p)]                      -- instant only
  * adjacent-window flip rate = E[p_w(1-p_w') + p_w'(1-p_w)]  -- instant + drift

The variance and repetition calculations below are a sensitivity model.  They
assume conditionally independent task-level errors and independent repeated
Bernoulli draws at fixed task propensities, transferring the no-graph window's
variance model to both arms.  No graph whole-bed same-configuration window
tests that equality.  One twin window does not test the independence assumptions.  The observed
paired-change SD over 20 windows remains a directly measured descriptive scale.

Scope: the 100-task subset every number in the thesis is read on, baseline
seed 1 (the only campaign with a k=2 round).  Fresh rows only.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

REPO = Path(os.environ.get("GHX_REPO", Path(__file__).resolve().parents[2]))
ROOT = REPO / "recipe/gaia_evolver/runs/baseline-seed1"
BED = REPO / "recipe/gaia_evolver/data/webthinker_gaia_dev_nopixel.json"

# F15/F9e, already class A, quoted here as the comparison targets.
ADJACENT_SEED1 = (126, 600)
ADJACENT_POOLED = (402, 2000)
PAIRED_CHANGE_SD = 3.70          # F15, 20 adjacent same-config windows
BETWEEN_SEED_SE = 2.8            # F46, three seeds per arm
OBSERVED_ARM_DIFF = 2.7          # F46, graph minus no-graph plateau means


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def main() -> None:
    subset = {t["task_id"] for t in json.loads(BED.read_text(encoding="utf-8"))}
    assert len(subset) == 100, len(subset)

    rows = [json.loads(l) for l in (ROOT / "data" / "task_history.jsonl").open(encoding="utf-8") if l.strip()]
    r0 = [r for r in rows
          if int(r["round"]) == 0 and str(r["task_id"]) in subset and not r.get("carried")]
    flags = [r["passed_flags"][:2] for r in r0 if isinstance(r.get("passed_flags"), list)
             and len(r["passed_flags"]) >= 2]
    n = len(flags)
    assert n == 100, f"expected the full subset at k=2, got {n}"

    dis = sum(1 for a, b in flags if a != b)
    lo, hi = wilson(dis, n)
    s0 = sum(1 for a, _ in flags if a)
    s1 = sum(1 for _, b in flags if b)

    a_k, a_n = ADJACENT_SEED1
    alo, ahi = wilson(a_k, a_n)
    p_k, p_n = ADJACENT_POOLED
    plo, phi = wilson(p_k, p_n)

    # Conditional sensitivity model: Var(score | window) = sum_i p_i(1-p_i)
    # requires zero cross-task covariance; 1/sqrt(k) additionally assumes
    # independent repeats at fixed propensities.  The data do not test these.
    e_pq = (dis / n) / 2
    sd_window = math.sqrt(n * e_pq)
    sd_paired_pred = sd_window * math.sqrt(2)
    sd_se = PAIRED_CHANGE_SD / math.sqrt(2 * 19)   # SE of an SD on 20 windows

    print("=== Same-instant re-measurement (M22-L0 R0, k=2, 100-task subset) ===")
    print(f"tasks                       : {n}")
    print(f"simultaneous disagreements  : {dis}")
    print(f"SIMULTANEOUS flip rate      : {100*dis/n:.1f}%  95% Wilson [{lo:.1f}, {hi:.1f}]")
    print(f"two whole-bed scores        : {s0} and {s1}   same-instant swing {s1-s0:+d} tasks")
    print()
    print("=== Against the adjacent-window rate (F15 / F9e) ===")
    print(f"adjacent, seed 1            : {100*a_k/a_n:.1f}%  [{alo:.1f}, {ahi:.1f}]  ({a_k}/{a_n})")
    print(f"adjacent, pooled 3 seeds    : {100*p_k/p_n:.1f}%  [{plo:.1f}, {phi:.1f}]  ({p_k}/{p_n})")
    overlap = lo <= ahi and alo <= hi
    print(f"intervals overlap           : {overlap}  -> drift component not resolved")
    print()
    print("=== Conditional sensitivity model (independence assumptions untested) ===")
    print(f"model per-window score SD   : {sd_window:.2f} tasks")
    print(f"model paired-change SD      : {sd_paired_pred:.2f} tasks (two independent windows)")
    print(f"observed paired-change SD   : {PAIRED_CHANGE_SD:.2f} tasks (F15, 20 windows, SE {sd_se:.2f})")
    print(f"gap in SE units             : {abs(sd_paired_pred-PAIRED_CHANGE_SD)/sd_se:.1f}")
    print()
    print("=== Model-conditional repetition sensitivity (80% power, two-sided 0.05) ===")
    mult = 2.80  # t_{.975} + t_{.80}, large df
    print(f"paired one-window contrast  : MDE = {mult*sd_paired_pred:.1f}/sqrt(k) tasks")
    for k in (1, 2, 4, 8, 16, 32):
        print(f"   k={k:<3d} averaged repeats   : {mult*sd_paired_pred/math.sqrt(k):5.1f} tasks")
    need = (mult * sd_paired_pred / OBSERVED_ARM_DIFF) ** 2
    print(f"repeats needed for the observed {OBSERVED_ARM_DIFF:+.1f}: k = {need:.0f}")
    print()
    print("=== Flown composition versus the conditional model ===")
    draws = 13 * 3
    print(f"no-graph whole-bed rounds   : {draws} (13 plateau rounds x 3 seeds)")
    print("graph whole-bed rounds      : 24; plus 15 25-task audit batches (F58)")
    print(f"model MDE for 39 iid repeats: {mult*sd_paired_pred/math.sqrt(draws):.1f} tasks")
    # F46 reads its MDE at 4 df, where the multiplier is t_{.975,4}+t_{.80,4}.
    mult_df4 = 2.776 + 0.941
    print(f"actual, from between-seed SE: MDE = {mult_df4*BETWEEN_SEED_SE:.1f} tasks (F46, 4 df)")
    print("   -> campaigns evolved configurations and did not supply iid repeats;")
    print("      the reported arm summary has three seed-level replicates.")


if __name__ == "__main__":
    main()
