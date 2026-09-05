# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Did the graph arms actually ship MORE fixes than the official one?"""
import json
from collections import Counter
from pathlib import Path

RUNS = [
    ("baseline-seed1", "no-graph"),
    ("M24_103x3", "graph"),
    ("M25_103x16", "graph"),
    ("ghx-seed1", "graph"),
]

print(f"{'run':16} {'arm':9} {'rounds':>6} {'cands':>6} {'ships':>6} {'c/rd':>6} {'s/rd':>6} {'ship%':>6}  buckets")
for name, arm in RUNS:
    root = Path("recipe/gaia_evolver/runs") / name
    curves = json.loads((root / "curves.json").read_text(encoding="utf-8"))
    rounds = len(curves)
    cands = len(list(root.glob("R*/candidates/C-*.md")))
    sb = json.loads((root / "scoreboard.json").read_text(encoding="utf-8"))
    ships = sb.get("ships") or []
    buckets = Counter(s.get("bucket") for s in ships)
    # evolve rounds = rounds that could ship (round 0 never evolves)
    evolve_rounds = max(1, rounds - 1)
    print(
        f"{name:16} {arm:9} {rounds:6d} {cands:6d} {len(ships):6d} "
        f"{cands/evolve_rounds:6.2f} {len(ships)/evolve_rounds:6.2f} "
        f"{100*len(ships)/max(1,cands):5.0f}%  {dict(buckets)}"
    )

print("\nnoop rounds (evolve produced nothing that shipped):")
for name, arm in RUNS:
    root = Path("recipe/gaia_evolver/runs") / name
    curves = json.loads((root / "curves.json").read_text(encoding="utf-8"))
    st = Counter(c.get("evolve_status") for c in curves)
    print(f"  {name:16} {dict(st)}")
