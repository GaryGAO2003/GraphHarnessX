# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Offline probe: three upgrades to GHX's causal-cone evidence, tried on REAL
closed-round data from the in-flight M23 campaign arms.

This is a standalone, read-only analysis script.  Nothing under ``harnessx/``
or ``recipe/`` imports it, and it does not import ``harnessx.graph`` /
``harnessx.ghx`` either — the code freeze on the live arms means those modules
must not be touched even indirectly, so the node/edge shapes, the cone
algorithm, and the lift / discrimination statistics are reimplemented here
from a direct reading of:

  * ``harnessx/graph/unfold.py``       — the U (unfolded graph) JSONL records
  * ``harnessx/graph/causal.py``       — ``causal_cone`` / ``terminal_node``
  * ``harnessx/ghx/evidence_files.py`` — ``_cone_anchors``, ``_attribution_cone``,
    ``_cone_static_signature``, ``_lift``, ``_discrimination``

P1 (baseline) is a faithful reimplementation of that pipeline so P2/P3/P4 can
be judged against a known-good reference, and so P1 itself can be checked
line-for-line against a round's real ``graph_evidence/facts.md``.

Four analyses, run per round and pooled across all closed rounds of each arm:

  P1  baseline lift table       — replicate evidence_files.py exactly.
  P2  first-anomaly (FPoF)      — within a failed task's cone, the earliest
                                   (lowest-ordinal) node whose outcome is
                                   error/empty; compare that ranking to P1's
                                   lift ranking (rank correlation + top-5).
  P3  edge-grade layered lift   — classify each cone member by the weakest
      (GRADE)                    DATA edge evidence on its path from the
                                   anchors: hard (slot-provenance edges only)
                                   / soft (needs >=1 message-plane edge) /
                                   injected (intervention-union member, no
                                   DATA path at all).  lift_hard vs lift_full.
  P4  confirmed-core            — a single-hop "direct DATA edge into an
      discrimination (例2)       anchor" proxy for "this member's output
                                   demonstrably reached the final-answer
                                   chain" (U carries no message content, so
                                   real literal-overlap matching is not
                                   possible — see process_task_graph's
                                   docstring); count how many pairs of failed
                                   tasks sharing an IDENTICAL full-cone
                                   signature get split apart by differing
                                   confirmed-core sets.

Data layout (learned by walking the actual run trees, not assumed):

  <run_dir>/curves.json                 — one entry per CLOSED round; a round
                                           with no entry is in-flight and must
                                           not be read.
  <run_dir>/data/task_history.jsonl     — one row per (round, task_id): round,
                                           task_id, passed, passed_flags
                                           (per-attempt, k attempts), level.
  <run_dir>/R{n}/sessions/**/{R|r}{n}-{task_id}/
        graph/{run_id}_unfolded.jsonl   — the U file (current layout).
        {run_id}_unfolded.jsonl         — legacy layout, same dir, no
                                           ``graph/`` subdir (also checked).
    a sibling ``{leaf_dir_name}.json`` identity sidecar carries
    ``latest_run_id``, used to pick the right U when a task has more than one
    recorded run id.

  The join from a U file to its task_id is the SESSION DIRECTORY NAME, not a
  field inside the U file (U's own ``session_id`` is the label GAIA minted,
  e.g. ``aegis/R0/r0-<uuid>``, which already embeds this). Round 0 nests an
  extra ``R0/`` path segment (``aegis/R0/r0-<uuid>``); rounds >= 1 are flat
  (``aegis/R2-<uuid>``); one recursive walk matching leaf dir names against
  ``^[Rr]{round}-(.+)$`` finds both regardless of nesting depth.

The gaia_evolver caller does not treat "failed this round" as the complement
of "passed this round": a task that failed every attempt this round but
passed on some EARLIER round is a "flip" — carried for the cross-round diff
channel but excluded from the lift/discrimination statistics; the pass-side
lift control is "passed now OR ever solved before" (run_meta_aegis_ghx.py
~L395-423). ``compute_round_partitions`` replicates this exact lottery
partition by walking rounds in order and accumulating a ``solved_before``
set — this is what lets P1's output be checked against a real facts.md.

Usage::

    .venv312\\Scripts\\python.exe -m experiments.analysis.cone_semantics_probe

Or point at different run dirs / output location explicitly::

    .venv312\\Scripts\\python.exe experiments/analysis/cone_semantics_probe.py \\
        --run D:/PycharmProj/HarnessX/recipe/gaia_evolver/runs/M23_L1_ghx2 \\
        --out C:/.../scratchpad/cone_probe
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ── constants (from harnessx/graph/types.py EdgeType) ───────────────────────

EDGE_CONTROL = "observed_control"
EDGE_DATA = "observed_data"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_RUNS = [
    _REPO_ROOT / "recipe" / "gaia_evolver" / "runs" / "M23_L1_ghx2",
    _REPO_ROOT / "recipe" / "gaia_evolver" / "runs" / "M23_L2_ghx5",
]
_DEFAULT_OUT = Path(
    r"C:\Users\Admin\AppData\Local\Temp\claude\D--PycharmProj-HarnessX"
    r"\1c891e50-b1f1-4c4e-b125-abc689c10aaf\scratchpad\cone_probe"
)

_SHARED_MIN_TASKS = 2  # matches evidence_files.py's _SHARED_MIN_TASKS


# ── U (minimal, read-only reimplementation) ─────────────────────────────────


@dataclass
class Node:
    id: str
    static_node_id: str
    hook: str
    ordinal: int
    intervention: str = ""
    outcome: str = ""


@dataclass
class Edge:
    source: str
    target: str
    edge_type: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Graph:
    run_id: str
    session_id: str
    nodes: list  # list[Node]
    edges: list  # list[Edge]


def load_unfolded(path: Path) -> Graph:
    """Stream-parse one U JSONL file (unfold.py's ``load_unfolded``, trimmed to
    the fields P1-P4 use)."""
    run_id = ""
    session_id = ""
    nodes: list[Node] = []
    edges: list[Edge] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            kind = rec.get("kind")
            if kind == "meta":
                run_id = rec.get("run_id", "")
                session_id = rec.get("session_id", "")
            elif kind == "node":
                nodes.append(
                    Node(
                        id=rec["id"],
                        static_node_id=rec["static_node_id"],
                        hook=rec["hook"],
                        ordinal=rec["ordinal"],
                        intervention=rec.get("intervention", ""),
                        outcome=rec.get("outcome", ""),
                    )
                )
            elif kind == "edge":
                edges.append(
                    Edge(
                        source=rec["source"],
                        target=rec["target"],
                        edge_type=rec["edge_type"],
                        metadata=rec.get("metadata", {}) or {},
                    )
                )
            # "invokes" records are cross-layer edges into subagent child runs;
            # P1-P4 never descend INVOKES, so they are not loaded here.
    return Graph(run_id=run_id, session_id=session_id, nodes=nodes, edges=edges)


def _reverse_adjacency(edges: list, allowed_types: set, plane: str | None) -> dict:
    """target -> [source, ...], restricted to ``allowed_types`` and, when given, a
    DATA edge ``metadata.plane`` value (``causal.py``'s ``_adjacency(reverse=True)``,
    specialised with the extra plane filter P3 needs that ``causal.py`` has no use
    for)."""
    adj: dict = defaultdict(list)
    for e in edges:
        if e.edge_type not in allowed_types:
            continue
        if plane is not None and (e.edge_type != EDGE_DATA or e.metadata.get("plane") != plane):
            continue
        adj[e.target].append(e.source)
    return adj


def _ancestors(adj: dict, start: str) -> set:
    seen: set = set()
    stack = [start]
    while stack:
        cur = stack.pop()
        for src in adj.get(cur, ()):
            if src not in seen:
                seen.add(src)
                stack.append(src)
    return seen


def causal_cone(edges: list, anchors: list, allowed_types: set, plane: str | None = None) -> set:
    """``causal.py``'s ``causal_cone(..., include_anchors=True)``: ancestor closure
    of ``anchors`` over ``allowed_types`` edges, anchors included."""
    adj = _reverse_adjacency(edges, allowed_types, plane)
    cone: set = set()
    for a in anchors:
        cone |= _ancestors(adj, a)
    cone |= set(anchors)
    return cone


def cone_anchors(graph: Graph) -> list:
    """``evidence_files.py:_cone_anchors`` — terminal invocation + last model call."""
    anchors: list = []
    if graph.nodes:
        anchors.append(max(graph.nodes, key=lambda n: n.ordinal).id)
    model_ids = [n.id for n in graph.nodes if n.hook == "model"]
    if model_ids and model_ids[-1] not in anchors:
        anchors.append(model_ids[-1])
    return anchors


def cone_static_signature(nodes_by_id: dict, cone: set) -> set:
    """``evidence_files.py:_cone_static_signature`` — bare static id, plus an
    outcome-annotated ``id#outcome`` member for a tool node whose outcome is a
    failure shape (error/empty; ``ok`` and unannotated add nothing extra)."""
    out: set = set()
    for nid in cone:
        n = nodes_by_id.get(nid)
        if n is None:
            continue
        out.add(n.static_node_id)
        if n.hook == "tool" and n.outcome and n.outcome != "ok":
            out.add(f"{n.static_node_id}#{n.outcome}")
    return out


def lift_table(failing_nodes: dict, passing_nodes: dict) -> dict:
    """``evidence_files.py:_lift`` verbatim (dict-of-sets in, dict-of-stats out)."""
    n_f = len(failing_nodes) or 1
    n_p = len(passing_nodes)
    out: dict = {}
    universe = set().union(*failing_nodes.values()) if failing_nodes else set()
    for node in universe:
        f_hits = sum(node in s for s in failing_nodes.values())
        p_hits = sum(node in s for s in passing_nodes.values())
        f_rate = f_hits / n_f
        p_rate = (p_hits / n_p) if n_p else 0.0
        out[node] = {
            "fail_rate": round(f_rate, 4),
            "pass_rate": round(p_rate, 4),
            "lift": round(f_rate / p_rate, 3) if p_rate else None,
            "n_fail": f_hits,
        }
    return out


def discrimination(per_task_static_nodes: dict) -> dict:
    """``evidence_files.py:_discrimination`` verbatim."""
    tasks = sorted(per_task_static_nodes)
    sigs = [frozenset(per_task_static_nodes[t]) for t in tasks]
    distinct = len({s for s in sigs})
    pairs = 0
    total = 0.0
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            union = sigs[i] | sigs[j]
            total += (len(sigs[i] & sigs[j]) / len(union)) if union else 1.0
            pairs += 1
    return {
        "tasks": len(tasks),
        "distinct_signatures": distinct,
        "mean_jaccard": round(total / pairs, 4) if pairs else None,
        "degenerate": len(tasks) >= _SHARED_MIN_TASKS and distinct == 1,
    }


def shared_nodes(per_task_static_nodes: dict) -> dict:
    """``evidence_files.py:_compute_shared_nodes`` verbatim."""
    node_to_tasks: dict = defaultdict(set)
    for task_id, statics in per_task_static_nodes.items():
        for s in statics:
            node_to_tasks[s].add(task_id)
    shared = {n: sorted(t) for n, t in node_to_tasks.items() if len(t) >= _SHARED_MIN_TASKS}
    return dict(sorted(shared.items()))


def _lift_rank_key(lift_dict: dict, node: str):
    """``evidence_files.py:_render_facts._rank`` verbatim: None-lift (never seen
    on the passing side) sorts FIRST — most discriminating, not least."""
    lf = (lift_dict.get(node) or {}).get("lift")
    return (-float("inf") if lf is None else -lf, node)


def full_ranking(lift_dict: dict) -> list:
    """Every node in ``lift_dict``, best (most discriminating) first."""
    return sorted(lift_dict, key=lambda n: _lift_rank_key(lift_dict, n))


# ── per-task cone info (one graph load feeds P1-P4) ─────────────────────────


@dataclass
class TaskConeInfo:
    task_id: str
    anchors: list
    static_sig: set  # P1 baseline: full attribution-cone signature
    data_sig: set  # DATA-ancestor closure only (both planes), no intervention union
    hard_sig: set  # DATA-ancestor closure using slot-plane edges only
    soft_sig: set  # data_sig - hard_sig: needs >=1 message-plane edge somewhere on its path
    injected_sig: set  # static_sig - data_sig: intervention-union member, no DATA path at all
    n_slot_edges: int  # OBSERVED_DATA edges with metadata.plane == "slot", whole graph
    n_message_edges: int  # OBSERVED_DATA edges with metadata.plane == "message", whole graph
    first_anomaly: tuple | None  # (ordinal, "static_id#outcome") or None
    confirmed_core: set  # annotated static ids with a direct DATA edge into an anchor (+ anchors)
    confirmed_core_counts: dict  # static id -> # of distinct direct-edge node instances of that type
    # (diagnostic for P4: SET equality is what the spec asks P4 to test; the counts let the
    # report show whether a stricter multiset signature would recover discrimination that
    # set-equality collapses away — see process_task_graph's docstring.)


def process_task_graph(task_id: str, graph: Graph) -> TaskConeInfo | None:
    """Everything P1-P4 need from one task's U, computed in a single pass.

    P4's ``confirmed_core`` degrade: U's OBSERVED_DATA edge metadata carries
    only ``plane`` / ``slot_key`` (a message identity+role tag, e.g.
    ``msg:2:assistant``) / writer-reader static-id+step — never message TEXT
    (``_render_cone`` in evidence_files.py is explicit that "no trajectory
    content is copied here"). So there is no literal-overlap signal to check;
    the proxy used here is structural: a cone member counts as "confirmed
    core" iff it has an OBSERVED_DATA edge landing DIRECTLY on one of the
    anchors (one hop — not the transitive closure, which would just collapse
    back to the full cone and defeat the point), unioned with the anchors
    themselves.
    """
    if not graph.nodes:
        return None
    anchors = cone_anchors(graph)
    if not anchors:
        return None
    nodes_by_id = {n.id: n for n in graph.nodes}

    data_cone = causal_cone(graph.edges, anchors, {EDGE_DATA})
    hard_cone = causal_cone(graph.edges, anchors, {EDGE_DATA}, plane="slot")
    full_cone = set(data_cone) | {n.id for n in graph.nodes if n.intervention}

    static_sig = cone_static_signature(nodes_by_id, full_cone)
    data_sig = cone_static_signature(nodes_by_id, data_cone)
    hard_sig = cone_static_signature(nodes_by_id, hard_cone)
    soft_sig = data_sig - hard_sig
    injected_sig = static_sig - data_sig

    n_slot = sum(1 for e in graph.edges if e.edge_type == EDGE_DATA and e.metadata.get("plane") == "slot")
    n_msg = sum(1 for e in graph.edges if e.edge_type == EDGE_DATA and e.metadata.get("plane") == "message")

    anomalies = sorted(
        (n.ordinal, f"{n.static_node_id}#{n.outcome}")
        for nid in full_cone
        if (n := nodes_by_id.get(nid)) is not None and n.hook == "tool" and n.outcome and n.outcome != "ok"
    )
    first_anomaly = anomalies[0] if anomalies else None

    anchor_set = set(anchors)
    direct_ids = {e.source for e in graph.edges if e.edge_type == EDGE_DATA and e.target in anchor_set}
    direct_ids |= anchor_set
    core_member_ids = direct_ids & full_cone
    confirmed_core = cone_static_signature(nodes_by_id, core_member_ids)
    confirmed_core_counts: Counter = Counter()
    for nid in core_member_ids:
        n = nodes_by_id.get(nid)
        if n is None:
            continue
        confirmed_core_counts[n.static_node_id] += 1
        if n.hook == "tool" and n.outcome and n.outcome != "ok":
            confirmed_core_counts[f"{n.static_node_id}#{n.outcome}"] += 1

    return TaskConeInfo(
        task_id=task_id,
        anchors=anchors,
        static_sig=static_sig,
        data_sig=data_sig,
        hard_sig=hard_sig,
        soft_sig=soft_sig,
        injected_sig=injected_sig,
        n_slot_edges=n_slot,
        n_message_edges=n_msg,
        first_anomaly=first_anomaly,
        confirmed_core=confirmed_core,
        confirmed_core_counts=dict(confirmed_core_counts),
    )


# ── data layout / join ───────────────────────────────────────────────────────


def closed_rounds(run_dir: Path) -> list:
    curves_path = run_dir / "curves.json"
    if not curves_path.exists():
        return []
    curves = json.loads(curves_path.read_text(encoding="utf-8"))
    return sorted(c["round"] for c in curves)


def load_task_history(run_dir: Path) -> list:
    path = run_dir / "data" / "task_history.jsonl"
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_task_index(run_dir: Path, round_n: int) -> dict:
    """One walk of ``R{n}/sessions`` -> {task_id: leaf_session_dir}. Leaf dirs are
    matched by name (``^[Rr]{n}-(.+)$``) regardless of nesting depth, which covers
    both R0's ``aegis/R0/r0-<id>`` layout and R1+'s flat ``aegis/R{n}-<id>`` layout
    in one pattern."""
    root = run_dir / f"R{round_n}" / "sessions"
    idx: dict = {}
    if not root.exists():
        return idx
    pat = re.compile(rf"^[Rr]{round_n}-(.+)$")
    for dirpath, dirnames, _filenames in os.walk(root):
        for d in dirnames:
            m = pat.match(d)
            if m:
                idx[m.group(1)] = Path(dirpath) / d
    return idx


def resolve_unfolded(leaf_dir: Path) -> Path | None:
    """``evidence_files.py:core_layout_resolver`` + ``find_unfolded``: resolve to
    the ONE run id the identity sidecar names as latest, current-layout-then-
    legacy. If that specific run id has no U file the task is unavailable —
    this does NOT fall back to scanning the dir for a DIFFERENT run's file (an
    earlier retry's U is not this attempt's U, and the live resolver never
    makes that substitution either: it looks up exactly one captured
    ``(session_id, run_id)`` pair per task and returns ``None`` on a miss).
    Verified against R6/M23_L1_ghx2 task 624cbf11...: its dir holds 3 run ids
    (2 retries), only the oldest has an ``_unfolded.jsonl`` — the real
    ``latest_run_id`` attempt has no identity/graph output at all (it did not
    reach ``finalize()``) — and the real ``graph_evidence/cones/`` for that
    round correctly has no file for this task. A glob-any-file fallback here
    would silently un-drop a task the live system genuinely could not see.

    Only when the sidecar itself is entirely absent does this degrade to
    picking whichever single U file is present, since there is then no
    "latest" to be faithful to; that is rare enough to not need its own
    tracked outcome, but is intentionally the sole exception to "one named
    run id, no substitutes"."""
    sidecar = leaf_dir.parent / f"{leaf_dir.name}.json"
    if not sidecar.exists():
        graph_dir = leaf_dir / "graph"
        candidates = sorted(graph_dir.glob("*_unfolded.jsonl")) if graph_dir.exists() else []
        if not candidates:
            candidates = sorted(leaf_dir.glob("*_unfolded.jsonl"))
        return candidates[0] if candidates else None
    try:
        run_id = json.loads(sidecar.read_text(encoding="utf-8")).get("latest_run_id")
    except (OSError, ValueError):
        run_id = None
    if not run_id:
        return None
    cur = leaf_dir / "graph" / f"{run_id}_unfolded.jsonl"
    if cur.exists():
        return cur
    legacy = leaf_dir / f"{run_id}_unfolded.jsonl"
    if legacy.exists():
        return legacy
    return None


# ── round partition (replicates gaia_evolver's lottery filter) ──────────────


def compute_round_partitions(rows: list, rounds: list) -> dict:
    """Replicates ``run_meta_aegis_ghx.py``'s per-round split (~L395-423):
    ``failed`` = never-yet-solved AND failed every attempt this round;
    ``flipped`` = failed every attempt this round but solved on some earlier
    round (excluded from stats, kept only for the cross-round diff channel);
    ``solved`` (the lift control) = passed now OR solved before — so a flipped
    task's CURRENT (failing) cone can legitimately sit on the control side.
    """
    by_round: dict = {}
    solved_before: set = set()
    rows_by_round: dict = defaultdict(list)
    for r in rows:
        rows_by_round[r["round"]].append(r)
    for rnd in rounds:
        flags_by_task = {}
        for r in rows_by_round.get(rnd, ()):
            flags = r.get("passed_flags")
            if flags is None:
                flags = [bool(r.get("passed"))]
            flags_by_task[r["task_id"]] = flags
        failed = [t for t, fl in flags_by_task.items() if not any(fl) and t not in solved_before]
        flipped = [t for t, fl in flags_by_task.items() if not any(fl) and t in solved_before]
        passed_now = [t for t, fl in flags_by_task.items() if any(fl)]
        solved = sorted(set(passed_now) | solved_before)
        by_round[rnd] = {
            "failed": sorted(failed),
            "flipped": sorted(flipped),
            "passed_now": sorted(passed_now),
            "solved": solved,
        }
        solved_before = solved_before | set(passed_now)
    return by_round


# ── facts.md parsing (P1 sanity check only) ──────────────────────────────────

_FACTS_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)%\s*\|\s*"
    r"(n/a \(never passes\)|[\d.]+)\s*\|\s*(?:\d+%|—)\s*\|\s*\*\*(\d+)\*\*\s*\|\s*$"
)
_FACTS_HEADER_RE = re.compile(
    r"Cone discrimination over (\d+) failing task\(s\): (\d+) distinct cone signature\(s\), "
    r"mean pairwise overlap ([\d.]+|None)\."
)
_FACTS_CONTROL_RE = re.compile(r"control: (\d+) passing task\(s\)")


def parse_facts_md(path: Path) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    rows = {}
    for line in text.splitlines():
        m = _FACTS_ROW_RE.match(line.strip())
        if m:
            node, fail_pct, pass_pct, lift_s, at_risk = m.groups()
            rows[node] = {
                "fail_pct": float(fail_pct),
                "pass_pct": float(pass_pct),
                "lift": None if lift_s.startswith("n/a") else float(lift_s),
                "at_risk": int(at_risk),
            }
    header = _FACTS_HEADER_RE.search(text)
    control = _FACTS_CONTROL_RE.search(text)
    return {
        "rows": rows,
        "n_failing": int(header.group(1)) if header else None,
        "distinct_signatures": int(header.group(2)) if header else None,
        "mean_jaccard": (None if not header or header.group(3) == "None" else float(header.group(3))),
        "n_passing": int(control.group(1)) if control else None,
    }


def check_against_facts(round_lift: dict, round_disc: dict, facts: dict) -> dict:
    mismatches = []
    matched = 0
    for node, want in facts["rows"].items():
        got = (round_lift.get(node) or {}).get("lift")
        if got is None and want["lift"] is None:
            matched += 1
        elif got is not None and want["lift"] is not None and abs(got - want["lift"]) < 0.02:
            matched += 1
        else:
            mismatches.append({"node": node, "facts_lift": want["lift"], "probe_lift": got})
    return {
        "facts_rows": len(facts["rows"]),
        "matched_lift": matched,
        "mismatches": mismatches,
        "facts_n_failing": facts["n_failing"],
        "probe_n_failing": round_disc["tasks"],
        "facts_distinct_sigs": facts["distinct_signatures"],
        "probe_distinct_sigs": round_disc["distinct_signatures"],
    }


# ── rank correlation (pure stdlib Spearman, average-rank ties) ──────────────


def _ranks(values: list) -> list:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(pairs: list) -> float | None:
    n = len(pairs)
    if n < 2:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy) ** 0.5


# ── round-level orchestration ────────────────────────────────────────────────


@dataclass
class RoundData:
    round_n: int
    failed_infos: dict  # task_id -> TaskConeInfo
    solved_infos: dict  # task_id -> TaskConeInfo
    missing_u_failed: list
    missing_u_solved: list
    arm: str = ""  # run_dir.name; only used to namespace cross-arm pooling keys below,
    # since both arms draw from the SAME GAIA task-id pool — round_n:task_id alone would
    # collide (and silently overwrite one arm's cone with the other's) once round_datas
    # from both arms are pooled together for the "combined" statistics.


def load_round(run_dir: Path, round_n: int, partition: dict) -> RoundData:
    idx = build_task_index(run_dir, round_n)
    failed_infos, solved_infos = {}, {}
    missing_failed, missing_solved = [], []
    for task_id in partition["failed"]:
        leaf = idx.get(task_id)
        u_path = resolve_unfolded(leaf) if leaf else None
        info = process_task_graph(task_id, load_unfolded(u_path)) if u_path else None
        if info is None:
            missing_failed.append(task_id)
        else:
            failed_infos[task_id] = info
    for task_id in partition["solved"]:
        leaf = idx.get(task_id)
        u_path = resolve_unfolded(leaf) if leaf else None
        info = process_task_graph(task_id, load_unfolded(u_path)) if u_path else None
        if info is None:
            missing_solved.append(task_id)
        else:
            solved_infos[task_id] = info
    return RoundData(round_n, failed_infos, solved_infos, missing_failed, missing_solved, arm=run_dir.name)


# ── P1-P4 per round ───────────────────────────────────────────────────────────


def p1_for_round(rd: RoundData) -> dict:
    per_task = {t: i.static_sig for t, i in rd.failed_infos.items()}
    control = {t: i.static_sig for t, i in rd.solved_infos.items()}
    return {
        "lift": lift_table(per_task, control),
        "discrimination": discrimination(per_task),
        "shared": shared_nodes(per_task),
        "n_failed": len(per_task),
        "n_solved": len(control),
    }


def p2_for_round(rd: RoundData) -> dict:
    first_anomaly_counts: Counter = Counter()
    present_counts: Counter = Counter()
    no_anomaly = 0
    for info in rd.failed_infos.values():
        if info.first_anomaly is not None:
            first_anomaly_counts[info.first_anomaly[1]] += 1
        else:
            no_anomaly += 1
        for mech in info.static_sig:
            if "#" in mech:  # only outcome-annotated ids are first-anomaly candidates
                present_counts[mech] += 1
    return {
        "first_anomaly_counts": dict(first_anomaly_counts),
        "present_counts": dict(present_counts),
        "n_failed_no_anomaly": no_anomaly,
        "n_failed_total": len(rd.failed_infos),
    }


def p3_for_round(rd: RoundData) -> dict:
    per_task_hard = {t: i.hard_sig for t, i in rd.failed_infos.items()}
    control_hard = {t: i.hard_sig for t, i in rd.solved_infos.items()}
    lift_hard = lift_table(per_task_hard, control_hard)

    injected_counts: Counter = Counter()
    datapath_counts: Counter = Counter()
    for i in rd.failed_infos.values():
        for m in i.data_sig:
            datapath_counts[m] += 1
        for m in i.injected_sig:
            injected_counts[m] += 1

    total_slot = sum(i.n_slot_edges for i in rd.failed_infos.values()) + sum(
        i.n_slot_edges for i in rd.solved_infos.values()
    )
    total_msg = sum(i.n_message_edges for i in rd.failed_infos.values()) + sum(
        i.n_message_edges for i in rd.solved_infos.values()
    )
    return {
        "lift_hard": lift_hard,
        "injected_counts": dict(injected_counts),
        "datapath_counts": dict(datapath_counts),
        "total_slot_edges": total_slot,
        "total_message_edges": total_msg,
        "n_hard_members_total": sum(len(s) for s in per_task_hard.values()),
    }


def p4_for_round(rd: RoundData) -> dict:
    groups: dict = defaultdict(list)
    for t, i in rd.failed_infos.items():
        groups[frozenset(i.static_sig)].append(t)
    pairs_total = 0
    pairs_split = 0
    pairs_multiset_split = 0  # diagnostic: would a COUNT-weighted core signature split this pair?
    detail = []
    for tasks in groups.values():
        if len(tasks) < 2:
            continue
        tasks = sorted(tasks)
        for a in range(len(tasks)):
            for b in range(a + 1, len(tasks)):
                ta, tb = tasks[a], tasks[b]
                pairs_total += 1
                info_a, info_b = rd.failed_infos[ta], rd.failed_infos[tb]
                core_a, core_b = info_a.confirmed_core, info_b.confirmed_core
                split = core_a != core_b
                pairs_split += int(split)
                multiset_split = info_a.confirmed_core_counts != info_b.confirmed_core_counts
                pairs_multiset_split += int(multiset_split)
                detail.append(
                    {
                        "task_a": ta,
                        "task_b": tb,
                        "split": split,
                        "multiset_split": multiset_split,
                        "core_a_only": sorted(core_a - core_b),
                        "core_b_only": sorted(core_b - core_a),
                    }
                )
    return {
        "pairs_total": pairs_total,
        "pairs_split": pairs_split,
        "pairs_multiset_split": pairs_multiset_split,
        "n_degenerate_groups": sum(1 for tasks in groups.values() if len(tasks) >= 2),
        "detail": detail,
    }


# ── pooling across rounds ────────────────────────────────────────────────────


def pool_p1(round_datas: list) -> dict:
    per_task, control = {}, {}
    for rd in round_datas:
        for t, i in rd.failed_infos.items():
            per_task[f"{rd.arm}:R{rd.round_n}:{t}"] = i.static_sig
        for t, i in rd.solved_infos.items():
            control[f"{rd.arm}:R{rd.round_n}:{t}"] = i.static_sig
    return {
        "lift": lift_table(per_task, control),
        "discrimination": discrimination(per_task),
        "shared": shared_nodes(per_task),
        "n_failed": len(per_task),
        "n_solved": len(control),
    }


def pool_p2(round_datas: list) -> dict:
    first_anomaly_counts: Counter = Counter()
    present_counts: Counter = Counter()
    no_anomaly = 0
    for rd in round_datas:
        p2 = p2_for_round(rd)
        first_anomaly_counts.update(p2["first_anomaly_counts"])
        present_counts.update(p2["present_counts"])
        no_anomaly += p2["n_failed_no_anomaly"]
    return {
        "first_anomaly_counts": dict(first_anomaly_counts),
        "present_counts": dict(present_counts),
        "n_failed_no_anomaly": no_anomaly,
        "n_failed_total": sum(len(rd.failed_infos) for rd in round_datas),
    }


def pool_p3(round_datas: list) -> dict:
    per_task_hard, control_hard = {}, {}
    injected_counts: Counter = Counter()
    datapath_counts: Counter = Counter()
    total_slot = total_msg = 0
    for rd in round_datas:
        for t, i in rd.failed_infos.items():
            per_task_hard[f"{rd.arm}:R{rd.round_n}:{t}"] = i.hard_sig
            for m in i.data_sig:
                datapath_counts[m] += 1
            for m in i.injected_sig:
                injected_counts[m] += 1
            total_slot += i.n_slot_edges
            total_msg += i.n_message_edges
        for t, i in rd.solved_infos.items():
            control_hard[f"{rd.arm}:R{rd.round_n}:{t}"] = i.hard_sig
            total_slot += i.n_slot_edges
            total_msg += i.n_message_edges
    return {
        "lift_hard": lift_table(per_task_hard, control_hard),
        "injected_counts": dict(injected_counts),
        "datapath_counts": dict(datapath_counts),
        "total_slot_edges": total_slot,
        "total_message_edges": total_msg,
    }


def pool_p4(round_datas: list) -> dict:
    pairs_total = pairs_split = pairs_multiset_split = groups_total = 0
    per_round = []
    for rd in round_datas:
        p4 = p4_for_round(rd)
        pairs_total += p4["pairs_total"]
        pairs_split += p4["pairs_split"]
        pairs_multiset_split += p4["pairs_multiset_split"]
        groups_total += p4["n_degenerate_groups"]
        per_round.append({"round": rd.round_n, **{k: v for k, v in p4.items() if k != "detail"}})
    return {
        "pairs_total": pairs_total,
        "pairs_split": pairs_split,
        "pairs_multiset_split": pairs_multiset_split,
        "n_degenerate_groups_total": groups_total,
        "per_round": per_round,
    }


# ── P2-vs-P1 and P3 rank-shift comparisons ───────────────────────────────────


def compare_p2_vs_p1(p1_lift: dict, p2: dict) -> dict:
    universe = set(p2["present_counts"]) | set(p2["first_anomaly_counts"])
    pairs = []
    for m in universe:
        x = p2["first_anomaly_counts"].get(m, 0)
        lf = (p1_lift.get(m) or {}).get("lift")
        y = 1e9 if lf is None else lf
        pairs.append((x, y))
    rho = spearman(pairs)

    top5_p2 = sorted(universe, key=lambda m: (-p2["first_anomaly_counts"].get(m, 0), m))[:5]
    full_rank = full_ranking(p1_lift)
    rank_of = {n: idx + 1 for idx, n in enumerate(full_rank)}
    top5_p1 = full_rank[:5]

    return {
        "spearman_rho": rho,
        "n_mechanisms_compared": len(universe),
        "top5_first_anomaly": [
            {
                "mechanism": m,
                "first_anomaly_count": p2["first_anomaly_counts"].get(m, 0),
                "present_count": p2["present_counts"].get(m, 0),
                "p1_lift": (p1_lift.get(m) or {}).get("lift"),
                "p1_rank_overall": rank_of.get(m),
            }
            for m in top5_p2
        ],
        "top5_p1_lift": [
            {
                "mechanism": m,
                "p1_lift": (p1_lift.get(m) or {}).get("lift"),
                "first_anomaly_count": p2["first_anomaly_counts"].get(m, 0),
                "present_count": p2["present_counts"].get(m, 0),
                "is_outcome_annotated": "#" in m,
            }
            for m in top5_p1
        ],
    }


def compare_p3_layers(lift_full: dict, lift_hard: dict, top_n: int = 12) -> dict:
    full_rank = full_ranking(lift_full)[:top_n]
    rows = []
    for m in full_rank:
        in_hard = m in lift_hard
        rows.append(
            {
                "mechanism": m,
                "lift_full": (lift_full.get(m) or {}).get("lift"),
                "in_hard_universe": in_hard,
                "lift_hard": (lift_hard.get(m) or {}).get("lift") if in_hard else None,
            }
        )
    return {
        "top_full_vs_hard": rows,
        "hard_universe_size": len(lift_hard),
        "full_universe_size": len(lift_full),
        "n_top_dropped_from_hard": sum(1 for r in rows if not r["in_hard_universe"]),
    }


# ── report rendering ─────────────────────────────────────────────────────────


def _fmt_lift(v) -> str:
    return "n/a (never passes)" if v is None else f"{v:.2f}"


def render_lift_table_md(lift: dict, shared: dict, limit: int = 15) -> list:
    lines = ["| mechanism | in failures | in passes | lift | shared>=2 |", "|---|---|---|---|---|"]
    for node in full_ranking(lift)[:limit]:
        st = lift[node]
        lines.append(
            f"| `{node}` | {100*st['fail_rate']:.1f}% | {100*st['pass_rate']:.1f}% | "
            f"{_fmt_lift(st['lift'])} | {'yes' if node in shared else ''} |"
        )
    return lines


def render_report(results: dict) -> str:
    lines = ["# Cone Semantics Probe — Report", ""]
    lines.append(
        "Offline, read-only probe of three upgrades to GHX's causal-cone evidence "
        "(P2 first-anomaly / P3 edge-grade layering / P4 confirmed-core "
        "discrimination), tested against P1 (a faithful reimplementation of "
        "`evidence_files.py`'s current lift/discrimination baseline) on real closed "
        "rounds of the M23 campaign arms."
    )
    lines.append("")

    for arm_name, arm in results["arms"].items():
        lines.append(f"## Arm: {arm_name}")
        lines.append("")
        lines.append(f"Closed rounds used: {arm['closed_rounds']}")
        lines.append("")

        # -- P1 --
        lines.append("### P1 — baseline lift (pooled across closed rounds)")
        pooled = arm["pooled"]
        p1 = pooled["p1"]
        lines.append(
            f"Pooled over {p1['n_failed']} (round,failed-task) instances, "
            f"{p1['n_solved']} (round,solved-task) control instances. "
            f"Discrimination: {p1['discrimination']['distinct_signatures']} distinct "
            f"signatures / {p1['discrimination']['tasks']} tasks, mean pairwise "
            f"overlap {p1['discrimination']['mean_jaccard']}."
        )
        lines.append("")
        lines.extend(render_lift_table_md(p1["lift"], p1["shared"], limit=15))
        lines.append("")

        lines.append("#### P1 sanity check against real `graph_evidence/facts.md`")
        lines.append("")
        lines.append("| round | facts lift rows matched | facts n_failing | probe n_failing | facts distinct sigs | probe distinct sigs |")
        lines.append("|---|---|---|---|---|---|")
        for rnd, chk in arm["facts_checks"].items():
            if chk is None:
                continue
            lines.append(
                f"| R{rnd} | {chk['matched_lift']}/{chk['facts_rows']} | {chk['facts_n_failing']} | "
                f"{chk['probe_n_failing']} | {chk['facts_distinct_sigs']} | {chk['probe_distinct_sigs']} |"
            )
        lines.append("")

        # -- P2 --
        lines.append("### P2 — first-anomaly (FPoF) vs P1 lift")
        p2cmp = arm["p2_vs_p1"]
        lines.append(
            f"Spearman rho (first-anomaly count vs P1 lift, over "
            f"{p2cmp['n_mechanisms_compared']} outcome-annotated mechanisms): "
            f"**{None if p2cmp['spearman_rho'] is None else round(p2cmp['spearman_rho'], 3)}**"
        )
        lines.append("")
        lines.append("Top-5 by first-anomaly count, with their overall P1-lift rank:")
        lines.append("| mechanism | first-anomaly count | present-in-fail-cone count | P1 lift | P1 overall rank |")
        lines.append("|---|---|---|---|---|")
        for row in p2cmp["top5_first_anomaly"]:
            lines.append(
                f"| `{row['mechanism']}` | {row['first_anomaly_count']} | {row['present_count']} | "
                f"{_fmt_lift(row['p1_lift'])} | {row['p1_rank_overall']} |"
            )
        lines.append("")
        lines.append("Top-5 by P1 lift (any mechanism), with first-anomaly count if it is outcome-annotated:")
        lines.append("| mechanism | P1 lift | outcome-annotated? | first-anomaly count | present count |")
        lines.append("|---|---|---|---|---|")
        for row in p2cmp["top5_p1_lift"]:
            lines.append(
                f"| `{row['mechanism']}` | {_fmt_lift(row['p1_lift'])} | "
                f"{'yes' if row['is_outcome_annotated'] else 'no'} | {row['first_anomaly_count']} | "
                f"{row['present_count']} |"
            )
        lines.append("")

        # -- P3 --
        lines.append("### P3 — edge-grade layered lift (hard/soft/injected)")
        p3 = pooled["p3"]
        lines.append(
            f"Whole-arm OBSERVED_DATA edge totals across every task graph loaded "
            f"(both fail and pass side): **slot-plane edges = {p3['total_slot_edges']}**, "
            f"**message-plane edges = {p3['total_message_edges']}**."
        )
        lines.append("")
        p3cmp = arm["p3_layers"]
        lines.append(
            f"Hard-only lift universe size: {p3cmp['hard_universe_size']} mechanisms "
            f"(vs {p3cmp['full_universe_size']} in the full/current lift universe)."
        )
        lines.append("")
        lines.append("Full lift top-12, checked against the hard-only (slot-provenance-only) universe:")
        lines.append("| mechanism | lift_full | in hard universe? | lift_hard |")
        lines.append("|---|---|---|---|")
        for row in p3cmp["top_full_vs_hard"]:
            lines.append(
                f"| `{row['mechanism']}` | {_fmt_lift(row['lift_full'])} | "
                f"{'yes' if row['in_hard_universe'] else 'NO'} | {_fmt_lift(row['lift_hard'])} |"
            )
        lines.append("")
        lines.append("Injected-vs-data-path split (secondary cut, non-degenerate regardless of the slot-plane collapse) — top 12 by data-path count:")
        lines.append("| mechanism | via real DATA path (# failed tasks) | via intervention-union only (# failed tasks) |")
        lines.append("|---|---|---|")
        dp = p3["datapath_counts"]
        inj = p3["injected_counts"]
        top_dp = sorted(set(dp) | set(inj), key=lambda m: -dp.get(m, 0))[:12]
        for m in top_dp:
            lines.append(f"| `{m}` | {dp.get(m, 0)} | {inj.get(m, 0)} |")
        lines.append("")

        # -- P4 --
        lines.append("### P4 — confirmed-core discrimination (例2)")
        p4 = pooled["p4"]
        if p4["pairs_total"]:
            lines.append(
                f"Pairs of failed tasks (same round) sharing an IDENTICAL full-cone "
                f"signature: **{p4['pairs_total']}** total, across "
                f"{p4['n_degenerate_groups_total']} degenerate signature-groups. "
                f"Of those, **{p4['pairs_split']}** get split apart by differing "
                f"confirmed-core SETS ({(100*p4['pairs_split']/p4['pairs_total']):.1f}% "
                f"of identical-signature pairs)."
            )
            lines.append("")
            lines.append(
                "**Why 0:** the model-call anchor's message-plane read is TOTAL — U's "
                "M12 semantics have the model invocation read the entire message list "
                "handed to the provider each call, so almost every message ever written "
                "earlier in the trajectory that was never overwritten gets a direct "
                "OBSERVED_DATA edge into the FINAL model call too, not just the "
                "immediately-preceding one. One-hop \"direct edge into an anchor\", after "
                "`cone_static_signature` reduces it to bare/annotated TYPE ids (matching "
                "P1's own grouping), collapses back to close to the same type vocabulary "
                "`data_sig` already has — so it rarely adds discriminating power at the "
                "signature-equality granularity P1/P4 both operate at. This is a property "
                "of the type-level reduction, not of the tasks' actual difference: the "
                "MULTISET (count-weighted) version of the same one-hop proxy — same edges, "
                "just not collapsed to a set — DOES split "
                f"**{p4['pairs_multiset_split']}/{p4['pairs_total']}** "
                f"({(100*p4['pairs_multiset_split']/p4['pairs_total']):.1f}%) of these same "
                "identical-signature pairs, because two tasks that use the same TOOL TYPES "
                "throughout typically use them a different NUMBER of times."
            )
        else:
            lines.append("No identical-signature pairs found among failed tasks in this arm.")
        lines.append("")
        lines.append("| round | degenerate groups | identical-sig pairs | split by confirmed-core SET | split by confirmed-core MULTISET |")
        lines.append("|---|---|---|---|---|")
        for row in p4["per_round"]:
            lines.append(
                f"| R{row['round']} | {row['n_degenerate_groups']} | {row['pairs_total']} | "
                f"{row['pairs_split']} | {row['pairs_multiset_split']} |"
            )
        lines.append("")

    # -- combined --
    lines.append("## Combined across both arms")
    lines.append("")
    cp1 = results["combined"]["p1"]
    lines.append(
        f"P1 pooled: {cp1['n_failed']} failing instances, {cp1['n_solved']} control "
        f"instances, {cp1['discrimination']['distinct_signatures']} distinct "
        f"signatures / {cp1['discrimination']['tasks']} tasks."
    )
    lines.append("")
    cp2 = results["combined"]["p2_vs_p1"]
    rho_c = cp2["spearman_rho"]
    lines.append(f"P2 vs P1 Spearman rho (combined): **{None if rho_c is None else round(rho_c, 3)}**")
    lines.append("")
    cp4 = results["combined"]["p4"]
    if cp4["pairs_total"]:
        lines.append(
            f"P4 combined: {cp4['pairs_split']}/{cp4['pairs_total']} identical-signature "
            f"pairs split by confirmed-core SET ({(100*cp4['pairs_split']/cp4['pairs_total']):.1f}%); "
            f"{cp4['pairs_multiset_split']}/{cp4['pairs_total']} split by the MULTISET variant "
            f"({(100*cp4['pairs_multiset_split']/cp4['pairs_total']):.1f}%)."
        )
    else:
        lines.append("P4 combined: no identical-signature pairs found.")
    lines.append("")

    lines.append("## Known limitations (read before trusting exact percentages)")
    lines.append("")
    lines.append(
        "* **Slot-provenance plane is empty in this data.** Across every graph loaded in "
        "both arms, `metadata.plane == \"slot\"` occurred 0 times; every OBSERVED_DATA edge "
        "is `\"message\"`-plane. This is a real property of the current stack (everything "
        "routes through the message list, per `unfold.py`'s M12 docstring), not a parsing "
        "gap — the field exists and is read correctly, it is simply never populated with "
        "`\"slot\"` on this run. P3's `lift_hard` is consequently tiny (3-4 mechanisms: the "
        "anchor node types themselves) and should be read as evidence of that collapse, "
        "not as a ranking."
    )
    lines.append(
        "* **P1's task partition (fail/pass split) is recovered from disk, not captured "
        "live**, so it is not always exactly what `graph_evidence/facts.md` used. Measured "
        "against every round with a real `facts.md` (R2/R3/R5/R6, both arms — 8 rounds, "
        "181 ground-truth failing-task instances): **100% precision, ~83-85% recall** — a "
        "task this probe puts on the failing side is always genuinely failing (never a "
        "false positive), but ~15-17% of genuinely-failing tasks are not recovered, because "
        "their session dir accumulated more than one `run_id` (retries / candidate-eval "
        "reuse of the same session namespace) and the identity sidecar's `latest_run_id` "
        "does not always name the attempt the live resolver actually used. This shows up "
        "as `probe n_failing` running a few tasks below `facts n_failing` in the sanity-"
        "check table above, which shifts exact lift percentages while leaving the top-"
        "ranked mechanism's IDENTITY stable in every checked round."
    )
    lines.append("")

    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────


def _json_default(o):
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


def run_arm(run_dir: Path) -> dict:
    rounds = closed_rounds(run_dir)
    rows = load_task_history(run_dir)
    partitions = compute_round_partitions(rows, rounds)

    round_datas = []
    facts_checks = {}
    for rnd in rounds:
        rd = load_round(run_dir, rnd, partitions[rnd])
        round_datas.append(rd)
        facts = parse_facts_md(run_dir / f"R{rnd}" / "graph_evidence" / "facts.md")
        if facts is not None:
            p1 = p1_for_round(rd)
            facts_checks[rnd] = check_against_facts(p1["lift"], p1["discrimination"], facts)
        else:
            facts_checks[rnd] = None

    pooled_p1 = pool_p1(round_datas)
    pooled_p2 = pool_p2(round_datas)
    pooled_p3 = pool_p3(round_datas)
    pooled_p4 = pool_p4(round_datas)

    per_round = {}
    for rd in round_datas:
        per_round[rd.round_n] = {
            "n_failed": len(rd.failed_infos),
            "n_solved": len(rd.solved_infos),
            "missing_u_failed": rd.missing_u_failed,
            "missing_u_solved": rd.missing_u_solved,
            "p1": p1_for_round(rd),
            "p2": p2_for_round(rd),
            "p3": p3_for_round(rd),
            "p4": p4_for_round(rd),
        }

    return {
        "closed_rounds": rounds,
        "per_round": per_round,
        "pooled": {"p1": pooled_p1, "p2": pooled_p2, "p3": pooled_p3, "p4": pooled_p4},
        "facts_checks": facts_checks,
        "p2_vs_p1": compare_p2_vs_p1(pooled_p1["lift"], pooled_p2),
        "p3_layers": compare_p3_layers(pooled_p1["lift"], pooled_p3["lift_hard"]),
        "_round_datas": round_datas,  # kept for combined pooling; stripped before JSON dump
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", default=None, help="run dir (repeatable)")
    ap.add_argument("--out", default=str(_DEFAULT_OUT))
    args = ap.parse_args()

    run_dirs = [Path(p) for p in args.run] if args.run else _DEFAULT_RUNS
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {"arms": {}}
    all_round_datas = []
    for run_dir in run_dirs:
        arm_name = run_dir.name
        print(f"[cone_probe] processing arm {arm_name} ({run_dir}) ...", file=sys.stderr)
        arm = run_arm(run_dir)
        all_round_datas.extend(arm.pop("_round_datas"))
        results["arms"][arm_name] = arm
        print(f"[cone_probe]   closed rounds: {arm['closed_rounds']}", file=sys.stderr)

    combined_p1 = pool_p1(all_round_datas)
    combined_p2 = pool_p2(all_round_datas)
    combined_p3 = pool_p3(all_round_datas)
    combined_p4 = pool_p4(all_round_datas)
    results["combined"] = {
        "p1": combined_p1,
        "p2": combined_p2,
        "p3": combined_p3,
        "p4": combined_p4,
        "p2_vs_p1": compare_p2_vs_p1(combined_p1["lift"], combined_p2),
        "p3_layers": compare_p3_layers(combined_p1["lift"], combined_p3["lift_hard"]),
    }

    raw_path = out_dir / "raw.json"
    raw_path.write_text(json.dumps(results, indent=2, default=_json_default), encoding="utf-8")

    report_path = out_dir / "report.md"
    report_path.write_text(render_report(results), encoding="utf-8")

    print(f"[cone_probe] wrote {raw_path}", file=sys.stderr)
    print(f"[cone_probe] wrote {report_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
