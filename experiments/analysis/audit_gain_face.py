# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F48 -- the gain face: single-round moves that leave the same-config envelope.

Why this exists: the thesis's positive control (F39) is one round pair in one
campaign -- M22 R2->R3, the round that shipped the Windows bash guard. The claim
resting on it -- that the score axis resolves an effect only when the effect is
roughly three times the size of the effects this loop actually produces -- needs
the other side of that ledger: every OTHER single-round move, in all six
whitelist campaigns, measured against the same band. Without the sweep the jump
is an anecdote. With it, it is a count.

The band is the same-config re-draw envelope, not a standard deviation. It is
the union of the round-pair swings observed under an UNCHANGED configuration
across the three no-graph seeds (F15/F44/F45): -6..+5 on seed 1 (103-task bed),
-5..+2 on seed 2 (103-task bed), -8..+5 on seed 3 (100-task bed). The union,
-8..+5, is the band used here. Two conservatisms are deliberate: the union is
wider than any single seed's band, and two of its three sources were measured on
the 103-task bed while every score below is recomputed on the 100-task subset.
Both make a flag harder to earn, so the flagged set is a lower bound.

R0 is excluded, as in F47. It is a single baseline draw, it anchors a
regression-to-the-mean artifact across the six arms (F46, r = -0.87), and on the
seed-1 no-graph campaign it is the one round scored at k=2, so its pass@1
identity differs from every round after it (registry error 11). The sweep runs
over R1..R15, giving 14 pairs per campaign.

A ship recorded at round k first scores at round k+1. That mapping is not
assumed, it is checked: on the seed-1 no-graph campaign the Windows bash guard
first appears in R2/config.yaml and the starvation exits collapse between R2 and
R3; on the seed-2 graph campaign the runtime-policy rule first appears in
R4/config.yaml and the starvation exits collapse between R4 and R5. Rk/config.yaml
is written at the end of round k and is what round k+1 runs.

What it reports, per campaign:
  * per-round score on the common 100-task no-pixel subset and the round-to-round
    delta, over the 16-round presentation window (ruling III);
  * every delta outside the band, annotated with what shipped into the receiving
    round (scoreboard.json) and with how the budget-exhaustion exit count moved
    across the pair;
  * whether both rounds of the pair were full fresh batches, since a delta that
    straddles a no-op audit window is a partial re-draw, not a round-to-round move.

Then, across all six campaigns: how many round pairs there are, how many left
the band, and the split between rounds that shipped something and rounds that
did not -- both over all pairs and over full-batch pairs only. Finally a
sensitivity pass over three bands, because the band is a choice and the count
depends on it.

Deliberately NOT reported: any attribution of a flagged move to the ship that
landed in the same round. Co-occurrence is not attribution. The band says only
that a move that size is not a re-draw of the same configuration -- and a round
that ships is also a round that re-draws. The exit-count column carries the
mechanism evidence where there is any; where there is none, the row says so.

Scope: whitelist only (ruling II). Read-only over runs/.

Usage:  python experiments/analysis/audit_gain_face.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = [("baseline-seed1", "L0", 1), ("baseline-seed2", "L0", 2), ("baseline-seed3", "L0", 3),
        ("ghx-seed1", "GHX", 1), ("ghx-seed2", "GHX", 2), ("ghx-seed3", "GHX", 3)]
WINDOW = range(1, 16)          # 16-round presentation window (ruling III), R0 dropped
FULL_MIN = 80                  # fresh subset rows at or above this = full batch
LO, HI = -8, 5                 # same-config envelope, union over three seeds
BANDS = [(-8, 5, "union of the three seeds' observed same-config swings"),
         (-7, 7, "the +/-7 single-pair ceiling quoted in F14"),
         (-6, 5, "seed 1's own band, the narrowest of the three")]

SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def per_round(run: str):
    """(score, fresh, starved) per round on the 100-task subset.

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
    starved: dict[int, int] = collections.defaultdict(int)
    for (k, _), r in last.items():
        score[k] += 1 if r.get("passed") else 0
        if not r.get("carried"):
            fresh[k] += 1
        if r.get("exit") == "budget_exceeded":
            starved[k] += 1
    return score, fresh, starved


def ships_by_round(run: str) -> dict[int, list[tuple[str, str]]]:
    """{round -> [(candidate_id, bucket)]} from the campaign scoreboard."""
    path = ROOT / "runs" / run / "scoreboard.json"
    if not path.exists():
        return {}
    out: dict[int, list[tuple[str, str]]] = collections.defaultdict(list)
    for s in json.load(path.open(encoding="utf-8")).get("ships", []):
        out[int(s["round"])].append((s.get("cid", "?"), s.get("bucket", "?")))
    return out


def main() -> None:
    print("=" * 104)
    print("F48  The gain face -- single-round moves against the same-config envelope "
          f"[{LO:+d}, {HI:+d}]")
    print("=" * 104)

    flagged_all: list[tuple] = []          # every pair, for the sensitivity pass
    flagged: list[tuple] = []              # pairs outside the headline band
    pairs_total = 0
    pairs_full = 0

    for run, arm, seed in RUNS:
        score, fresh, starved = per_round(run)
        ships = ships_by_round(run)
        ks = [k for k in WINDOW if k in score]
        print(f"\n--- {run}  ({arm}, seed {seed}) "
              f"{'-' * (72 - len(run) - len(arm))}")
        print(f"{'pair':>9s} {'score':>12s} {'delta':>6s} {'full':>5s} "
              f"{'starved':>14s}  ships into the round")
        for a, b in zip(ks, ks[1:]):
            d = score[b] - score[a]
            pairs_total += 1
            full = fresh.get(a, 0) >= FULL_MIN and fresh.get(b, 0) >= FULL_MIN
            pairs_full += 1 if full else 0
            landed = ships.get(a, [])                 # a ship at round a scores at b
            row = (run, arm, seed, a, b, d, full,
                   starved.get(a, 0), starved.get(b, 0), landed)
            flagged_all.append(row)
            mark = "" if LO <= d <= HI else "   <-- OUTSIDE"
            if mark:
                flagged.append(row)
            print(f"  R{a:<2d}->R{b:<2d} {score[a]:5d}->{score[b]:<5d} {d:+6d} "
                  f"{'yes' if full else 'NO':>5s} "
                  f"{starved.get(a, 0):6d}->{starved.get(b, 0):<6d} "
                  f" {', '.join(f'{c} [{k}]' for c, k in landed) or '(none)'}{mark}")

    print("\n" + "=" * 104)
    print(f"Flagged moves: {len(flagged)} of {pairs_total} round pairs "
          f"({pairs_full} of which had a full fresh batch on both sides)")
    print("=" * 104)
    if not flagged:
        print("  none")
    up = [f for f in flagged if f[5] > 0]
    down = [f for f in flagged if f[5] < 0]
    for label, group in (("ABOVE the envelope", up), ("BELOW the envelope", down)):
        print(f"\n{label}: {len(group)}")
        for run, arm, seed, a, b, d, full, sa, sb, landed in group:
            print(f"  {run:14s} {arm}/s{seed}  R{a}->R{b}  {d:+3d} tasks   "
                  f"full={'yes' if full else 'NO':3s}  "
                  f"starved {sa}->{sb} ({sb - sa:+d})")
            print(f"  {'':14s} shipped into it: "
                  f"{', '.join(f'{c} [{k}]' for c, k in landed) or '(nothing)'}")

    shipped_up = [f for f in up if f[9]]
    up_full = [f for f in up if f[6]]
    up_full_shipped = [f for f in up_full if f[9]]
    print("\n" + "-" * 104)
    print(f"Above-envelope moves that a ship landed into: {len(shipped_up)} of {len(up)}")
    print(f"  restricted to full-batch pairs:             "
          f"{len(up_full_shipped)} of {len(up_full)}")
    print("Buckets on the full-batch ship-bearing moves: "
          + (", ".join(sorted({k for f in up_full_shipped for _, k in f[9]})) or "(none)"))
    big = [f for f in up_full_shipped if f[8] - f[7] <= -10]
    print(f"  ... of which show a starvation collapse of 10 exits or more: {len(big)}"
          + (" -- " + ", ".join(f"{f[0]} R{f[3]}->R{f[4]}" for f in big) if big else ""))
    print("-" * 104)

    print("\nBand sensitivity (above-band count / of which ship-bearing), R1..R15:")
    print(f"  {'band':>10s} {'all pairs':>22s} {'full-batch pairs':>22s}   basis")
    for lo, hi, why in BANDS:
        a = [f for f in flagged_all if f[5] > hi]
        af = [f for f in a if f[6]]
        print(f"  [{lo:+d},{hi:+d}]  {len(a):>10d} / {sum(1 for f in a if f[9]):<9d} "
              f"{len(af):>10d} / {sum(1 for f in af if f[9]):<9d}   {why}")

    print("\n" + "=" * 104)
    print("F49  The other face: pairs where the starvation mechanism moved, "
          "whatever the score did")
    print("=" * 104)
    print("Budget-exhaustion exits are the one failure mode with a mechanical "
          "reading on this\nbed: a task that exits budget_exceeded ran out of steps "
          "rather than answering wrongly.\nEvery pair below drops that count by 10 "
          "or more -- an intervention of a size the loop\nrarely achieves. The "
          "question is what the score axis did with it.")
    print(f"\n{'campaign':16s} {'pair':>9s} {'starved':>17s} {'delta':>7s} "
          f"{'full':>5s} {'in band':>8s}  ships into the round")
    collapses = sorted((f for f in flagged_all if f[8] - f[7] <= -10),
                       key=lambda f: f[8] - f[7])
    for run, arm, seed, a, b, d, full, sa, sb, landed in collapses:
        print(f"{run:16s} R{a:<2d}->R{b:<2d} {sa:6d}->{sb:<4d} ({sb - sa:+4d}) "
              f"{d:+7d} {'yes' if full else 'NO':>5s} "
              f"{'yes' if LO <= d <= HI else 'NO':>8s}  "
              f"{', '.join(f'{c} [{k}]' for c, k in landed) or '(nothing)'}")
    inside = [f for f in collapses if LO <= f[5] <= HI]
    print(f"\n  {len(collapses)} such pairs; {len(inside)} moved the score by an "
          f"amount the band cannot\n  separate from a re-draw of the same "
          f"configuration.")
    cfull = [f for f in collapses if f[6]]
    print(f"\n  Restricted to full-batch pairs, where the delta is a whole-bed "
          f"re-draw rather\n  than a 25-task no-op window: {len(cfull)} pairs.")
    for run, arm, seed, a, b, d, full, sa, sb, landed in cfull:
        print(f"    {run:14s} R{a}->R{b}  starvation {sb - sa:+d}, "
              f"score {d:+d}  <-  "
              f"{', '.join(f'{c} [{k}]' for c, k in landed) or 'nothing shipped'}")
    print("\n  What this pair set does NOT show: that a starvation collapse ought "
          "to raise the\n  score. A task that stops running out of steps starts "
          "answering, and the answer can\n  be wrong. What it does show is the "
          "spread: mechanical interventions of the same\n  measured size land on "
          "both sides of the band, and one lands below zero.")

    print("\n" + "-" * 104)
    print("Reminder: co-occurrence is not attribution. A round that ships also "
          "re-draws;\nthe envelope only says the move is larger than a re-draw "
          "of an unchanged config.")


if __name__ == "__main__":
    main()
