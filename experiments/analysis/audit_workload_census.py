# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F51 -- the workload census: what was run, and how little of it is evidence.

Why this exists: the thesis states its evidence base as 96 rounds and 8,393 fresh
task evaluations. That is a small fraction of what the project actually executed,
and the difference is the whole point of the whitelist ruling -- so the census has
to be reported in a form where the excluded remainder is visible rather than
folded into a larger, more impressive number.

Three tiers:
  * WHITELIST -- the six claim-bearing campaigns, each read over its formal
    sixteen-round window (R0..R15). Every number in the thesis body is computed
    inside this tier. Two executed rounds sit outside it and are counted in the
    third tier rather than dropped: M22's R16, which no reported window uses
    (ruling ii, 2026-08-27), and ghx-seed1-partial, the graph campaign's aborted first
    launch, which reached R0 and was restarted as ghx-seed1. Neither carries a
    ship, a candidate, or a uniquely-solved task, so no thesis number moves with
    them; the scope change is a matter of saying what was read, not what was run.
  * SHAKEDOWN -- the two graph campaigns flown before the graph layer was correct,
    excluded from every claim by the whitelist ruling and reported in Appendix B
    as operations record.
  * EVERYTHING ELSE -- smoke runs, pre-baseline campaigns, aborted campaigns,
    dress rehearsals, the K=8 pilot. Engineering, not evidence.

A "fresh" evaluation is a row not marked carried: a task the round actually ran.
Rows are counted from task_history.jsonl, so probe runs -- which record trials in
their own JSON and never write task_history -- do not appear here. Their workload
is in the ledger rows for the probes themselves.

Deliberately NOT reported: any pooled score, rate or effect over these tiers.
The census is a count of work done. Mixing tiers is exactly what the whitelist
ruling forbids.

Scope: read-only over runs/.

Usage:  python experiments/analysis/audit_workload_census.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver" / "runs"

# run -> last round inside the formal window (None = the whole run)
WHITELIST = {"baseline-seed1": 15, "ghx-seed1": None,
             "baseline-seed2": None, "ghx-seed2": None,
             "baseline-seed3": None, "ghx-seed3": None}
SHAKEDOWN = ["M24_103x3", "M25_103x16"]
# executed rounds of a whitelist run that fall outside its formal window
OVERAGE = [("baseline-seed1", 16)]


def census(run: str, lo: int | None = None,
           hi: int | None = None) -> tuple[int, int, int]:
    """(rounds, rows, fresh rows) for one run directory, over rounds lo..hi."""
    path = ROOT / run / "data" / "task_history.jsonl"
    if not path.exists():
        return 0, 0, 0
    rounds, rows, fresh = set(), 0, 0
    for line in path.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rd = int(r.get("round", -1))
        if (lo is not None and rd < lo) or (hi is not None and rd > hi):
            continue
        rounds.add(rd)
        rows += 1
        if not r.get("carried"):
            fresh += 1
    return len(rounds), rows, fresh


def main() -> None:
    all_runs = sorted(p.parent.parent.name
                      for p in ROOT.glob("*/data/task_history.jsonl"))
    # (label, lo, hi) triples so a capped whitelist run's tail lands in tier 3
    tiers = {
        "WHITELIST -- the evidence base":
            [(r, None, hi) for r, hi in WHITELIST.items()],
        "SHAKEDOWN -- excluded by the whitelist ruling":
            [(r, None, None) for r in SHAKEDOWN],
        "EVERYTHING ELSE -- engineering, not evidence":
            [(r, None, None) for r in all_runs
             if r not in WHITELIST and r not in SHAKEDOWN]
            + [(r, lo, None) for r, lo in OVERAGE],
    }

    print("=" * 84)
    print("F51  Workload census -- rounds and fresh task evaluations by tier")
    print("=" * 84)

    totals = {}
    for tier, runs in tiers.items():
        tr = tf = 0
        print(f"\n{tier}")
        detail = len(runs) <= 12
        for run, lo, hi in runs:
            rounds, _, fresh = census(run, lo, hi)
            tr += rounds
            tf += fresh
            if detail:
                span = ("" if (lo, hi) == (None, None)
                        else f"  R{0 if lo is None else lo}.."
                             f"{'end' if hi is None else 'R%d' % hi}")
                print(f"  {run:22s} {rounds:3d} rounds   {fresh:6d} fresh{span}")
        if not detail:
            print(f"  ({len(runs)} entries, listed in the run index; includes "
                  f"{len(OVERAGE)} out-of-window tail of a whitelist run)")
        print(f"  {'':22s} {tr:3d} rounds   {tf:6d} fresh   <-- tier total")
        totals[tier] = (tr, tf, len(runs))

    gr = sum(v[0] for v in totals.values())
    gf = sum(v[1] for v in totals.values())
    gn = len({r for runs in tiers.values() for r, _, _ in runs})
    print("\n" + "=" * 84)
    print(f"  PROJECT TOTAL          {gr:3d} rounds   {gf:6d} fresh   "
          f"across {gn} run directories")
    wr, wf, _ = totals["WHITELIST -- the evidence base"]
    print(f"  of which admissible    {wr:3d} rounds   {wf:6d} fresh   "
          f"= {100 * wf / gf:.1f}% of the executed workload")
    print("=" * 84)
    print("The remaining 100 - {:.1f}% is not a reserve of unused evidence. It is "
          "work done\nbefore the instrument was trustworthy, and the ruling that "
          "excluded it was made\nafter it had been read."
          .format(100 * wf / gf))


if __name__ == "__main__":
    main()
