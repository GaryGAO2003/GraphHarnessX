# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""VERIFY-4a: recompute the CH4 cone-compression illustration on whitelist data.

The thesis outline's 4.5/4.6 example (228 nodes / 70,090 chars -> 41 / 16,879
-> 14) was measured during V6 commissioning (pre-M22, excluded by the data
ruling).  This script re-derives the same three-row table from ghx-seed1
failed fresh tasks, using cone_semantics_probe's faithful reimplementation of
the cone pipeline.

Measures (stated, recomputable):
  * whole U     — node count; serialized chars = sum of non-empty JSONL line
                  lengths of the U file.
  * full cone   — data cone (observed_data ancestors of the anchors) union
                  intervention nodes, exactly process_task_graph's full_cone;
                  chars = node records in the cone + edge records with both
                  endpoints inside it.
  * data cone   — observed_data ancestors only.

Prints per-task rows, medians, and the representative task whose U size is
the median (for the thesis's worked example).
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cone_semantics_probe import (  # noqa: E402
    EDGE_DATA,
    build_task_index,
    causal_cone,
    closed_rounds,
    cone_anchors,
    load_task_history,
    load_unfolded,
    resolve_unfolded,
)

RUN = Path(r"D:\PycharmProj\HarnessX") / "recipe/gaia_evolver/runs/ghx-seed1"
MAX_ROUNDS = 2  # R0+R1 failed cohort is a big enough sample for an illustration

failed_by_round: dict[int, set] = {}
for r in load_task_history(RUN):
    if r.get("carried"):
        continue
    if not r.get("passed"):
        failed_by_round.setdefault(int(r["round"]), set()).add(str(r["task_id"]))

rows = []
for rn in closed_rounds(RUN)[:MAX_ROUNDS]:
    idx = build_task_index(RUN, rn)
    for tid in sorted(failed_by_round.get(rn, ())):
        leaf = idx.get(tid)
        if leaf is None:
            continue
        upath = resolve_unfolded(leaf)
        if upath is None:
            continue
        g = load_unfolded(upath)
        if not g.nodes:
            continue
        anchors = cone_anchors(g)
        if not anchors:
            continue
        data_cone = causal_cone(g.edges, anchors, {EDGE_DATA})
        full_cone = set(data_cone) | {n.id for n in g.nodes if n.intervention}
        raw_lines = [
            ln for ln in upath.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
        total_chars = sum(len(ln) for ln in raw_lines)
        sub_chars = 0
        for ln in raw_lines:
            rec = json.loads(ln)
            kind = rec.get("kind")
            if kind == "node" and rec.get("id") in full_cone:
                sub_chars += len(ln)
            elif (
                kind == "edge"
                and rec.get("source") in full_cone
                and rec.get("target") in full_cone
            ):
                sub_chars += len(ln)
        rows.append(
            dict(
                round=rn,
                task=tid[:8],
                n_nodes=len(g.nodes),
                u_chars=total_chars,
                cone_nodes=len(full_cone),
                cone_chars=sub_chars,
                data_nodes=len(data_cone),
            )
        )

if not rows:
    print("NO ROWS — check layout assumptions")
    sys.exit(1)

print(f"ghx-seed1 failed fresh tasks with a resolvable U, rounds {sorted({r['round'] for r in rows})}: n={len(rows)}")
print(f"{'rnd':>3} {'task':8} {'U_nodes':>7} {'U_chars':>8} {'cone_n':>6} {'cone_chars':>10} {'ratio':>6} {'data_n':>6}")
for r in sorted(rows, key=lambda x: (x["round"], x["task"])):
    print(
        f"{r['round']:>3} {r['task']:8} {r['n_nodes']:>7} {r['u_chars']:>8} "
        f"{r['cone_nodes']:>6} {r['cone_chars']:>10} "
        f"{r['cone_chars']/max(1,r['u_chars']):>6.3f} {r['data_nodes']:>6}"
    )

med = lambda k: statistics.median(r[k] for r in rows)  # noqa: E731
print("\nmedians:")
print(f"  whole U   : {med('n_nodes'):.0f} nodes / {med('u_chars'):.0f} chars")
print(f"  full cone : {med('cone_nodes'):.0f} nodes / {med('cone_chars'):.0f} chars")
print(f"  data cone : {med('data_nodes'):.0f} nodes")
print(f"  cone/U char ratio (median of ratios): {statistics.median(r['cone_chars']/max(1,r['u_chars']) for r in rows):.3f}")

rep = sorted(rows, key=lambda r: r["n_nodes"])[len(rows) // 2]
print(
    f"\nrepresentative (median-size U): R{rep['round']} task {rep['task']} — "
    f"{rep['n_nodes']} nodes / {rep['u_chars']:,} chars -> full cone "
    f"{rep['cone_nodes']} nodes / {rep['cone_chars']:,} chars -> data cone {rep['data_nodes']} nodes"
)
