# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The rate must be measured where the column was LIVE: M22-L0's own trajectories.

M26b is a graph-arm run whose digests never carried this column, so measuring
the heuristic there describes a counterfactual, not the arm's experience.

Also: state it without the graph as ground truth. "78% of results the graph says
were consumed" conditions on our own instrument. "78% of all non-empty tool
results" needs no instrument at all.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from harnessx.aegis.stages.trace_facts import extract_trace_facts

MAX_ROLLOUTS = int(__import__("os").environ.get("AUDIT_MAX_ROLLOUTS", "0"))  # 0 = the whole arm

tot = Counter()
rollouts = 0
for rnd in range(1, 17):
    tdir = Path(f"recipe/gaia_evolver/runs/baseline-seed1/R{rnd}/trajectories")
    if not tdir.is_dir():
        continue
    for traj in sorted(tdir.glob("*_r0.jsonl")):
        tid = traj.name.split("_r0")[0]
        try:
            f = extract_trace_facts(tid, [traj])
        except Exception:
            continue
        rollouts += 1
        for c in f.tool_calls:
            tot["all_calls"] += 1
            if c.return_len <= 0:
                tot["empty_or_missing"] += 1
                continue
            tot["with_payload"] += 1
            if c.next_uses_result is False:
                tot["NO"] += 1
            elif c.next_uses_result is True:
                tot["yes"] += 1
            else:
                tot["abstain"] += 1
    if MAX_ROLLOUTS and rollouts >= MAX_ROLLOUTS:
        break

n = tot["with_payload"]
print(f"M22-L0 (the arm where this column was live): {rollouts} rollouts")
print(f"tool calls total {tot['all_calls']}, of which non-empty payload {n}")
if n:
    print(f'  graded "output NOT referenced" : {tot["NO"]:5d}  = {100*tot["NO"]/n:.1f}%')
    print(f'  graded used                    : {tot["yes"]:5d}  = {100*tot["yes"]/n:.1f}%')
    print(f"  abstained (payload < 20 chars) : {tot['abstain']:5d}  = {100*tot['abstain']/n:.1f}%")
