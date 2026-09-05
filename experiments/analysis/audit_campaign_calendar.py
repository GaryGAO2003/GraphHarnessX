# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F59 -- calendar order and overlap of the six whitelist campaigns.

Why this exists: R4 Devil's Advocate MINOR #9 / P2-12 -- no row disclosed the
six campaigns' calendar order or overlap, so a reader could not rule out
gateway/model-routing drift (already documented as a real risk in Appendix
B.1: "Model names are routing keys that move") as a confound even for the
thesis's own hedged between-arm readings.

task_history.jsonl (the file every other ledger script reads) carries no
timestamp field. audit.jsonl does: every stage-audit row carries a Unix-epoch
float `ts`. This script takes the min and max `ts` across each campaign's
audit.jsonl as that campaign's start and end -- a record timestamp, not a
filesystem mtime, so it survives a later file touch or copy unchanged. Falls
back to `R*/` directory mtimes (and says so, class [B]) only for a campaign
whose audit.jsonl has no usable `ts` values -- not needed for any of the six
whitelist runs; all six resolve at class [A].

Overlap: two campaigns overlap if their [start, end] intervals intersect
(start_A <= end_B and start_B <= end_A). Printed in UTC, since `ts` is a bare
Unix epoch with no recorded timezone.

Scope: whitelist only (ruling ii). Read-only over runs/.

Usage:  python experiments/analysis/audit_campaign_calendar.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = [("baseline-seed1", "L0", 1), ("baseline-seed2", "L0", 2), ("baseline-seed3", "L0", 3),
        ("ghx-seed1", "GHX", 1), ("ghx-seed2", "GHX", 2), ("ghx-seed3", "GHX", 3)]


def span_from_audit(run: str) -> tuple[float, float, str] | None:
    """(start_ts, end_ts, 'A') from audit.jsonl's `ts` field, or None if unusable."""
    fp = ROOT / "runs" / run / "audit.jsonl"
    if not fp.exists():
        return None
    ts: list[float] = []
    for line in fp.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        t = r.get("ts")
        if isinstance(t, (int, float)):
            ts.append(float(t))
    if not ts:
        return None
    return min(ts), max(ts), "A"


def span_from_mtimes(run: str) -> tuple[float, float, str]:
    """Fallback: min/max mtime of R*/ round directories. Class [B]."""
    root = ROOT / "runs" / run
    times = [p.stat().st_mtime for p in root.glob("R*")
             if p.is_dir() and p.name[1:].isdigit()]
    return min(times), max(times), "B"


def fmt(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def overlaps(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def main() -> None:
    print("=" * 100)
    print("F59  Calendar order and overlap of the six whitelist campaigns")
    print("=" * 100)

    rows = []
    for run, arm, seed in RUNS:
        span = span_from_audit(run)
        if span is None:
            span = span_from_mtimes(run)
            print(f"NOTE: {run} has no usable audit.jsonl ts values; "
                  f"falling back to R*/ directory mtimes (class B).")
        start, end, cls = span
        rows.append((run, arm, seed, start, end, cls))

    rows.sort(key=lambda r: r[3])

    print(f"\n{'campaign':16s} {'arm':5s} {'seed':4s} {'start (UTC)':>19s} "
          f"{'end (UTC)':>19s}  class")
    for run, arm, seed, start, end, cls in rows:
        print(f"{run:16s} {arm:5s} {seed:<4d} {fmt(start):>19s} {fmt(end):>19s}  [{cls}]")

    print("\nOverlaps (interval [start, end] intersects another campaign's):")
    any_overlap = False
    for i, (run_a, arm_a, seed_a, sa, ea, _) in enumerate(rows):
        others = []
        for j, (run_b, arm_b, seed_b, sb, eb, _) in enumerate(rows):
            if i != j and overlaps((sa, ea), (sb, eb)):
                others.append(f"{run_b} ({arm_b}/s{seed_b})")
        if others:
            any_overlap = True
        print(f"  {run_a:16s} ({arm_a}/s{seed_a}): "
              f"{', '.join(others) if others else '(none -- runs in isolation)'}")
    if not any_overlap:
        print("  no two campaigns overlap")

    print()
    print("Read: an overlap means the two campaigns could have shared "
          "whatever the gateway\nwas doing at that moment (routing table "
          "state, backend load, a mapping change) --\na channel Appendix B.1 "
          "already documents as real ('Model names are routing keys that\n"
          "move'), though this script does not attempt to detect or size any "
          "such effect --\nit only establishes which campaigns could share "
          "one.")


if __name__ == "__main__":
    main()
