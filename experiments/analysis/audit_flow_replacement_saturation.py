# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""GAIA half, done right: join the OFFICIAL fact table against the GRAPH
projection for the same rollout, then ask how often they disagree.

Previous attempt read next_uses_result off the projection object, where it does
not exist — every read returned None and the disagreement rate came out 0.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))

from harnessx.aegis.stages.trace_facts import extract_trace_facts
from harnessx.ghx.layer_a import extract_trace_facts_graphed

RUN = Path("recipe/gaia_evolver/runs/ghx-seed1")
tot = Counter()
rollouts = 0

for rnd in range(2, 13):
    tdir = RUN / f"R{rnd}" / "trajectories"
    if not tdir.is_dir():
        continue
    for traj in sorted(tdir.glob("*_r0.jsonl"))[:30]:
        tid = traj.name.split("_r0")[0]
        try:
            official = extract_trace_facts(tid, [traj])
            graphed = extract_trace_facts_graphed(tid, [traj])
        except Exception:
            continue
        proj = getattr(graphed, "_projections", {}) or {}
        if not proj:
            continue
        # graph side, keyed by (rollout, step, tool, args_sha)
        gmap = {}
        for rollout, rep in proj.items():
            for c in getattr(rep, "tool_calls", []) or []:
                gmap[(rollout, c.step, c.tool, getattr(c, "args_sha", ""))] = c
        matched_here = 0
        for c in official.tool_calls:
            if c.return_len <= 0:
                continue
            g = gmap.get((c.rollout, c.step, c.tool, c.args_sha))
            if g is None:
                tot["unmatched"] += 1
                continue
            matched_here += 1
            entered = bool(getattr(g, "reader_ordinals", None))
            final = bool(getattr(g, "consumed_by_final", False))
            tot["matched"] += 1
            if entered:
                tot["entered"] += 1
                if c.next_uses_result is False:
                    tot["entered_but_NO"] += 1
                elif c.next_uses_result is None:
                    tot["entered_but_abstain"] += 1
            if final:
                tot["final"] += 1
                if c.next_uses_result is False:
                    tot["final_but_NO"] += 1
        if matched_here:
            rollouts += 1
    if rollouts >= 50:
        break

print(f"rollouts joined: {rollouts}")
print(f"tool calls matched between the two tables: {tot['matched']}  (unmatched: {tot['unmatched']})")
if tot["entered"]:
    print(f"\nof calls the GRAPH says entered a later call's context: {tot['entered']}")
    print(f"  official column says NO      : {tot['entered_but_NO']}"
          f"  = {100*tot['entered_but_NO']/tot['entered']:.1f}%")
    print(f"  official column abstains     : {tot['entered_but_abstain']}")
if tot["final"]:
    print(f"\nof calls the GRAPH says the ANSWERING call read: {tot['final']}")
    print(f"  official column says NO      : {tot['final_but_NO']}"
          f"  = {100*tot['final_but_NO']/tot['final']:.1f}%")
