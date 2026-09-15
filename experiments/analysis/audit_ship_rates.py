# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Did the graph arms actually ship MORE fixes than the official one?  (thesis F10)

Six whitelist campaigns, sixteen-round window: rounds R1..R15 only.  R0 never evolves and
the first no-graph campaign's R16 lies outside the presentation window (Appendix A).
  cands = candidate files written for R1..R15 (R*/candidates/C-*.md)
  ships = landed candidates, scoreboard.json ships with round <= 15
  s/rd  = ships per evolve round (15);  ship% = ships / cands
Read-only over runs/.

Usage:  python experiments/analysis/audit_ship_rates.py
"""
import json
import re
from collections import Counter
from pathlib import Path

RUNS = [
    ("baseline-seed1", "no-graph"),
    ("baseline-seed2", "no-graph"),
    ("baseline-seed3", "no-graph"),
    ("ghx-seed1", "graph"),
    ("ghx-seed2", "graph"),
    ("ghx-seed3", "graph"),
]
LAST = 15
RD = re.compile(r"^R(\d+)$")

print(f"{'run':16} {'arm':9} {'rounds':>6} {'cands':>6} {'ships':>6} {'c/rd':>6} {'s/rd':>6} {'ship%':>6}  buckets")
arm_tot: dict[str, list[int]] = {}
for name, arm in RUNS:
    root = Path("recipe/gaia_evolver/runs") / name
    cands = 0
    for p in root.glob("R*/candidates/C-*.md"):
        m = RD.match(p.parts[-3])          # skips quarantined dirs such as R7_poisoned_gateway
        if m and 1 <= int(m.group(1)) <= LAST:
            cands += 1
    sb = json.loads((root / "scoreboard.json").read_text(encoding="utf-8"))
    ships = [s for s in (sb.get("ships") or []) if int(s["round"]) <= LAST]
    buckets = Counter(s.get("bucket") for s in ships)
    t = arm_tot.setdefault(arm, [0, 0, 0])
    t[0] += LAST
    t[1] += cands
    t[2] += len(ships)
    print(
        f"{name:16} {arm:9} {LAST:6d} {cands:6d} {len(ships):6d} "
        f"{cands/LAST:6.2f} {len(ships)/LAST:6.2f} "
        f"{100*len(ships)/max(1,cands):5.0f}%  {dict(buckets)}"
    )

print()
for arm, (rounds, cands, ships) in arm_tot.items():
    print(f"{arm:9} arm: {ships} landed / {rounds} evolve rounds = {ships/rounds:.2f} per round; "
          f"{ships}/{cands} candidates = {100*ships/max(1,cands):.0f}%")
