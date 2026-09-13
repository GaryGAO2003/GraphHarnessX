# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Materialise graph evidence as workspace files for the official AEGIS roles.

**The load-bearing idea.**  In the agentic-pull world a cone file is a *MAP for
the reader, not a payload*.  The official Digester is itself an agent that reads
trajectories; so a cone file does not copy trajectory content into itself — it
tells the Digester *which steps causally mattered* (by trajectory step number)
so its own reads go to the right places.  Everything here is a pointer, never a
transcript.

Two kinds of file are written under ``<run_dir>/R{n}/graph_evidence/``:

1. **Cone maps**, one per *failing* task, at ``cones/<task_id>.md``.  Each renders
   the attribution cone (:func:`_attribution_cone` — DATA-only ancestry unioned with the
   invocations that intervened, v6 M13) anchored by
   :func:`_cone_anchors` — the run's terminal invocation
   (:func:`~harnessx.graph.causal.terminal_node`) together with its last model call
   (v6 M12), because ``TaskEndEvent`` carries no messages and the terminal anchor
   alone cannot reach the message plane.  The file holds the cone's invocations in
   ordinal order (``t{ordinal}: hook label [step N]``), the data-flow section
   (``key: t{writer} -> t{reader}`` over the cone's ``OBSERVED_DATA`` edges, both
   the slot and the message plane), the ``INVOKES`` frontier when the cone reached a
   subagent boundary, and the set of trajectory step numbers the cone touched —
   the pointers the reader opens.

2. **Cross-task facts** at ``facts.md``.  From the cones just computed: the static
   nodes appearing in the cone of MORE THAN ONE failing task (emitted only when
   non-empty — an absent section, never an empty header).  Node edit history is
   written as a single honest line: the official ship ledger does not record
   graph node ids yet, so this is *not yet recorded*, which is distinct from
   *never edited* — absence here means unknown, not none.

This module is pure: it reads U files through a caller-supplied ``resolver`` and
writes evidence files.  It does not read the flag, does not re-derive pass/fail
(the caller passes the failing-task list — the orchestrator's Stage P already
knows outcomes), and imports nothing from ``harnessx.aegis``.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from ..graph.causal import DATA, causal_cone, invokes_frontier, select_nodes, terminal_node
from ..graph.unfold import UnfoldedGraph, find_unfolded, load_unfolded

_log = logging.getLogger(__name__)

# A static node counts as "shared" only when it appears in the cone of at least
# this many DISTINCT failing tasks.  Two is the whole point: a node in exactly
# one task's cone is task-local, not a cross-task fact.  Isolated here because it
# is the one line a broken gate would get wrong.
_SHARED_MIN_TASKS = 2


# ── resolvers (kept separate from the pure materialiser) ─────────────────────


def core_layout_resolver(base_dir, session_id: str, run_id_by_task: dict):
    """A resolver for the U-file layout :func:`harnessx.graph.unfold.write_unfolded`
    writes: ``{base_dir}/{session_id}/graph/{run_id}_unfolded.jsonl``, falling back to
    the pre-``graph/`` layout so runs recorded before the move still resolve.

    ``run_id_by_task`` maps a task id to the run id whose U file holds that task's
    run.  The returned callable takes a task id and returns a loaded
    :class:`~harnessx.graph.unfold.UnfoldedGraph`, or ``None`` when the task has no
    known run id or its U file is absent (so a missing file reads as *unavailable*,
    never as an empty graph).  The recipe wires its own resolver when the layout
    differs; the materialiser accepts any ``task_id -> (UnfoldedGraph | path | None)``.
    """

    def resolve(task_id: str):
        run_id = run_id_by_task.get(task_id)
        if not run_id:
            return None
        path = find_unfolded(str(base_dir), session_id, run_id)
        if path is None:
            return None
        return load_unfolded(path)

    return resolve


# ── U normalisation ──────────────────────────────────────────────────────────


def _load_u(resolved) -> UnfoldedGraph | None:
    """Normalise a resolver result (``UnfoldedGraph`` | path-like | ``None``)."""
    if resolved is None:
        return None
    if isinstance(resolved, UnfoldedGraph):
        return resolved
    path = Path(resolved)
    if not path.exists():
        return None
    return load_unfolded(path)


# ── rendering ────────────────────────────────────────────────────────────────


def _cone_anchors(u: UnfoldedGraph) -> list:
    """The anchors a failure cone is rooted at: the terminal invocation, plus the run's
    LAST model call when there was one (v6 M12).

    The terminal invocation is the run's final state, but ``TaskEndEvent`` carries no
    ``messages`` field, so a ``task_end`` processor can never touch the message plane and
    its cone reaches nothing the run actually did.  The last model call is the invocation
    that emitted the final answer and read the whole history that produced it — on the
    message plane that is where the run's causal chain is anchored.  Both are kept: the
    union only ever adds to what the terminal anchor already gave.
    """
    anchors: list = []
    term = terminal_node(u)
    if term is not None:
        anchors.append(term)
    model_nodes = select_nodes(u, lambda n: n.hook == "model")
    if model_nodes and model_nodes[-1] not in anchors:
        anchors.append(model_nodes[-1])
    return anchors


def _attribution_cone(u: UnfoldedGraph, anchors: list) -> set:
    """The cone this file reports: the DATA-only ancestry of ``anchors``, unioned with
    every invocation that intervened (v6 M13).

    Following ``OBSERVED_CONTROL`` as well makes membership mean "ran somewhere before
    the anchor in the same firing" — which is true of nearly every invocation and so
    names nothing.  Restricting to :data:`DATA` makes membership mean "a value this
    invocation produced reached the anchor", which is the claim the file's title makes.

    The union is not a softener: an invocation that *changed the primary event* acted on
    the run whether or not the change left a slot or message trace, and a data-only cone
    would drop exactly those.  Both halves are needed because U records data flow and
    event mutation on different planes; when interventions gain real data edges this
    union collapses back into the first term on its own.
    """
    cone = causal_cone(u, anchors, edge_types=DATA, include_anchors=True)
    cone |= {n.id for n in u.nodes if n.intervention}
    return cone


def _cone_static_signature(u: UnfoldedGraph, cone: set) -> set:
    """Static-node signature of a cone, with outcome-annotated variants (M23).

    A tool invocation whose recorded outcome is a failure shape (``error``/``empty``)
    contributes BOTH its bare id and an annotated member (``tool:Bash#empty``), so the
    lift table can rank the mechanism rather than the tool. ``ok`` adds nothing —
    presence is already the bare id's job — and a node recorded before the outcome
    field existed reads as not-annotated, never as ok. M22's motivating number: the
    dominant failure mechanism (Bash → empty stdout → retry → budget death) rendered
    as ``tool:Bash`` lift 1.73 / at-risk 40, which is unactionable; the annotated
    member is where that mechanism becomes rankable.
    """
    node_by_id = {n.id: n for n in u.nodes}
    out: set = set()
    for nid in cone:
        n = node_by_id.get(nid)
        if n is None:
            continue
        out.add(n.static_node_id)
        if n.hook == "tool" and n.outcome and n.outcome != "ok":
            out.add(f"{n.static_node_id}#{n.outcome}")
    return out


def _render_cone(task_id: str, u: UnfoldedGraph, anchors: list, cone: set) -> str:
    node_by_id = {n.id: n for n in u.nodes}
    cone_nodes = sorted(
        (node_by_id[nid] for nid in cone if nid in node_by_id),
        key=lambda n: n.ordinal,
    )

    def _desc(nid: str) -> str:
        n = node_by_id.get(nid)
        return f"t{n.ordinal}: {n.hook} {n.label}" if n else nid

    anchor_desc = "; ".join(_desc(a) for a in anchors)

    lines: list[str] = [
        f"# Causal cone — {task_id}",
        "",
        (
            f"Anchored at {anchor_desc}. The invocations "
            "below are the causal cone — every invocation that could have contributed to "
            "how this run ended — in ordinal order. This file is a MAP, not a payload: each "
            "`[step N]` points into this task's trajectory; read those steps yourself, no "
            "trajectory content is copied here."
        ),
        "",
        "## Invocations (ordinal order)",
    ]
    for n in cone_nodes:
        mark = f" — CHANGED THE RUN: {n.intervention}" if n.intervention else ""
        ocmark = f" — outcome: {n.outcome}" if n.hook == "tool" and n.outcome and n.outcome != "ok" else ""
        lines.append(f"- t{n.ordinal}: {n.hook} {n.label} [step {n.step}]{mark}{ocmark}")
    lines.append("")

    # Slot data-flow: OBSERVED_DATA edges with both endpoints inside the cone.
    data_rows: list[tuple[int, int, str]] = []
    for e in u.edges:
        if e.edge_type != DATA or e.source not in cone or e.target not in cone:
            continue
        w = node_by_id.get(e.source)
        r = node_by_id.get(e.target)
        if w is None or r is None:
            continue
        slot = (e.metadata or {}).get("slot_key", "?")
        data_rows.append((w.ordinal, r.ordinal, slot))
    if data_rows:
        lines.append("## Data-flow (writer -> reader)")
        for w_ord, r_ord, slot in sorted(data_rows):
            lines.append(f"- {slot}: t{w_ord} -> t{r_ord}")
        lines.append("")

    # INVOKES frontier: subagent boundaries the cone reached but did not descend.
    frontier = invokes_frontier(u, cone)
    if frontier:
        lines.append("## INVOKES frontier")
        for iv in sorted(
            frontier, key=lambda x: (node_by_id[x.source].ordinal if x.source in node_by_id else -1, x.child_run_id)
        ):
            src = node_by_id.get(iv.source)
            src_desc = f"t{src.ordinal} ({src.label})" if src else iv.source
            lines.append(f"- {src_desc} invokes child run {iv.child_run_id}")
        lines.append("")

    # Trajectory step pointers — the map the reader opens.
    steps = sorted({n.step for n in cone_nodes})
    lines.append("## Trajectory steps that causally mattered")
    lines.append(
        "Open these step numbers in this task's `trajectories/` file(s) — the cone above "
        "names which invocations mattered; these are the steps to read:"
    )
    lines.append(", ".join(str(s) for s in steps) if steps else "(none)")
    lines.append("")
    return "\n".join(lines)


def _compute_shared_nodes(per_task_static_nodes: dict) -> dict:
    """Map each static node id to the sorted list of failing tasks whose cone
    contains it, keeping only nodes shared by ``>= _SHARED_MIN_TASKS`` distinct tasks."""
    node_to_tasks: dict[str, set] = defaultdict(set)
    for task_id, statics in per_task_static_nodes.items():
        for s in statics:
            node_to_tasks[s].add(task_id)
    shared = {node: sorted(tasks) for node, tasks in node_to_tasks.items() if len(tasks) >= _SHARED_MIN_TASKS}
    return dict(sorted(shared.items()))


def _lift(failing_nodes: dict, passing_nodes: dict) -> dict:
    """How much MORE often each node appears in a failing cone than a passing one (v6 M13).

    ``facts.md`` used to report the nodes shared by many failing tasks, which sounds like
    evidence and is not: the universal processor stack runs on every task, so it is shared
    by every failing cone — and by every passing one too.  A reader given only failure
    frequency reaches for whatever is most common, which is exactly the thing that
    discriminates least.  Measured on the R0 bed, ``tool:Bash`` sits in 93.5% of failing
    cones and 61.1% of passing ones (lift 1.53) while ``tool:Browser`` sits in 54.8% vs
    13.9% (lift 3.95) — frequency ranks Bash first, lift ranks Browser first.

    Returns ``{node: {"fail_rate", "pass_rate", "lift", "n_fail"}}``.  A node in every
    cone on both sides gets lift 1.0 and sorts to the bottom on its own, so no
    hand-maintained exclusion list is needed — the statistic sinks it.  ``lift`` is
    ``None`` when the node never appears on the passing side (undefined, not infinite:
    with no passing occurrences there is no ratio, only a lower bound).
    """
    n_f = len(failing_nodes) or 1
    n_p = len(passing_nodes)
    out: dict[str, dict] = {}
    for node in set().union(*failing_nodes.values()) if failing_nodes else set():
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


def _discrimination(per_task_static_nodes: dict) -> dict:
    """How much the cone map actually varies with the task (v6 M13).

    The evidence channel's whole claim is that a cone is a function OF THE TASK.  A
    function that returns the same value for every input carries zero bits, and nothing
    downstream can tell — a constant map renders as a full, plausible, useless file per
    task.  This is the check that names that state instead of letting it read as
    coverage: ``distinct_signatures`` counts how many different static-node sets the
    failing tasks produced, ``mean_jaccard`` averages pairwise overlap (1.0 == identical
    for every pair), and ``degenerate`` is true when two or more tasks all got the same
    answer.

    Reported, not raised: a degenerate map is a defect in the evidence channel, not a
    reason to destroy a round that is otherwise fine.  It is written into ``facts.md``
    so the roles reading the evidence see it, and returned so the caller can log it.
    """
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


_DEGENERATE_LINE = (
    "**This map carries no information.** Every failing task's cone contains the SAME "
    "static nodes, so cone membership does not distinguish one failure from another. "
    "Treat the shared-node list below as a description of the pipeline, NOT as evidence "
    "about these failures — anything it appears to single out, it would have singled "
    "out for a task that passed."
)


_EDIT_HISTORY_LINE = (
    "Node-level edit history is not yet recorded: the ship ledger does not track "
    "graph node ids (that arrives with a later module). This is *not yet recorded*, "
    "NOT *never edited* — absence here means unknown, not none."
)


_NO_CONTROL_LINE = (
    "No passing-task cones were supplied, so **lift is not computed**: this section ranks "
    "by how OFTEN a node appears in failing cones, which is not the same as how well it "
    "distinguishes failure. The universal processor stack appears in every cone here and "
    "would also appear in every passing one. Absence of lift means unmeasured, not 1.0."
)


def _capability_gaps(
    failing_u: dict, passing_u: dict, cap_by_task: dict
) -> list[dict]:
    """Absent capabilities, grouped by WHERE in the graph they bit.

    The cone answers which invocation is implicated in a failure. It cannot answer
    what the run needed and did not have: a capability that does not exist has no
    invocation, so it has no node, so lift can never rank it. That half comes from
    the judge's ``missing_capability`` — and unlike a co-occurrence statistic, "the
    agent lacked X" is already a counterfactual claim, which is why it prescribes
    where lift only localises.

    The grouping key is the graph, not the prose. Two tasks reporting "a PDF table
    parser" and "a structured table extractor" are one gap if their
    ``evidence_steps`` land on the same static nodes; two reporting the same words
    are two gaps if they bit in different places. Free-text clustering would need a
    model and would get exactly this backwards.

    ``cap_by_task`` maps task id -> the judge's ``missing_capability`` payload.
    Passing tasks are the control: a capability the winners also report lacking is
    not what separated them.
    """
    def _signature(u, steps) -> tuple:
        """Resolve the judge's ``evidence_steps`` to static nodes.

        Those indices are NOT harness step numbers. ``llm_judge._render_trace_from_event``
        numbers the trace it shows the judge by counting ``role == "tool"`` messages from
        1, and a harness step may fire several tools or none — a 20-step run routinely
        renders 23 of them. Matching against ``node.step`` therefore lands out of range
        and every gap falls into the unlocated bucket, which reads as "the graph could
        not place this" when in fact the two sides were counting different things.

        The Nth tool-hook node in ordinal order is the Nth tool result the judge saw.
        Anything out of range stays unresolved rather than being clamped: a wrong node
        is worse than an honest blank.
        """
        if u is None or not steps:
            return ()
        wanted = {int(s) for s in steps if isinstance(s, (int, float)) or str(s).isdigit()}
        tool_nodes = sorted((n for n in u.nodes if n.hook == "tool"), key=lambda n: n.ordinal)
        return tuple(
            sorted(
                {
                    tool_nodes[s - 1].static_node_id
                    for s in wanted
                    if 1 <= s <= len(tool_nodes)
                }
            )
        )

    groups: dict[tuple, dict] = {}
    for side, us in (("fail", failing_u), ("pass", passing_u)):
        for task_id, u in us.items():
            mc = (cap_by_task or {}).get(task_id) or {}
            if not mc.get("present"):
                continue
            sig = _signature(u, mc.get("evidence_steps") or [])
            g = groups.setdefault(sig, {"nodes": sig, "fail": [], "pass": [], "summaries": []})
            g[side].append(task_id)
            summary = (mc.get("summary") or "").strip()
            if side == "fail" and summary and len(g["summaries"]) < 3:
                g["summaries"].append(summary)
    return sorted(groups.values(), key=lambda g: (-len(g["fail"]), g["nodes"]))


def _render_capability_gaps(gaps: list[dict], n_fail: int, n_pass: int) -> list[str]:
    if not gaps:
        return []
    lines = [
        "",
        "## Absent capabilities",
        "",
        "What failing runs report they **lacked**. A capability that does not exist is "
        "never invoked, so it has no node and cannot appear in the lift table above — "
        "that table ranks what ran, this one ranks what was missing. Grouped by the "
        "static nodes its `evidence_steps` land on, so the grouping is the graph's, not "
        "the wording's: same place bitten is one gap however differently it is phrased.",
        "",
        "Read the two tables together. A gap whose nodes are high-lift is corroborated "
        "from both sides — failures concentrate there *and* the runs say what was "
        "missing there. A gap on low-lift nodes is one model's opinion with nothing "
        "behind it.",
        "",
        "| where it bit (cone nodes) | failing tasks | passing tasks | reported gap |",
        "|---|---|---|---|",
    ]
    for g in gaps:
        where = ", ".join(f"`{n}`" for n in g["nodes"]) if g["nodes"] else "_(steps not in U)_"
        summary = g["summaries"][0] if g["summaries"] else ""
        if len(summary) > 150:
            summary = summary[:147] + "..."
        lines.append(
            f"| {where} | {len(g['fail'])}/{n_fail} | {len(g['pass'])}/{n_pass} | {summary} |"
        )
    return lines


def _rank_by_lift(lift: dict):
    """Sort key: highest lift first. A node that never appears in a passing cone has
    no finite ratio, but it is the MOST discriminating case, not the least — it sorts
    to the top, never to the bottom where a naive ``or 0`` would put it."""

    def key(n: str):
        lf = (lift.get(n) or {}).get("lift")
        return (-float("inf") if lf is None else -lf, n)

    return key


def _render_facts(
    round_n: int,
    shared: dict,
    disc: dict,
    lift: dict,
    n_pass: int,
    gaps=None,
    n_chronic=None,
    edit_history=None,
) -> str:
    lines: list[str] = [f"# Cross-task graph facts — R{round_n}", ""]
    lines.append(
        f"Cone discrimination over {disc['tasks']} failing task(s): "
        f"{disc['distinct_signatures']} distinct cone signature(s), "
        f"mean pairwise overlap {disc['mean_jaccard']}."
    )
    if n_pass or n_chronic is not None:
        lines.append("")
        part = (
            f"Partition — **{disc['tasks']} failed / {n_pass} passed** on this rollout; "
            "every rate below is measured over these two sets."
        )
        if n_chronic is not None and n_chronic < disc["tasks"]:
            part += (
                f" {n_chronic} of the failing tasks have never passed on this config "
                f"lineage; the other {disc['tasks'] - n_chronic} failed this round after "
                "passing before. Both count as failures here — a failure rate is a "
                "statement about runs, not about lineages."
            )
        lines.append(part)
    if disc["degenerate"]:
        lines.append("")
        lines.append(_DEGENERATE_LINE)
    lines.append("")
    if shared:
        lines.append("## Shared cone nodes")
        if n_pass:
            lines.append(
                f"Ranked by **lift** — how much more often a node sits in a FAILING cone than "
                f"in a passing one (control: {n_pass} passing task(s)). Lift 1.0 means the node "
                "appears just as much when the task succeeds, so it explains nothing about "
                "these failures however often it appears. Read the top of this list, not the "
                "most frequent entry."
            )
            lines.append("")
            lines.append(
                "**`at risk` is the number of tasks that PASS today with this node in their "
                "cone. Any edit that removes, gates, aborts on, or replaces the node puts every "
                "one of them on the table.** Read it before proposing such an edit; lift says "
                "where failures concentrate, it does not say the node is fatal.\n\n"
                "This is not hypothetical. Twice now a candidate has targeted the node with the "
                "strongest failure signal and lost more passing tasks than it recovered: a hard "
                "abort on a detector with 29% survival cost 7 tasks, and swapping the Bash "
                "backend — 60% survival — cost 13 ALL_PASS to ALL_FAIL flips. The second "
                "candidate quoted the survival share in its own manifest and did it anyway. A "
                "percentage reads as a caveat; a count of tasks you are about to gamble reads "
                "as a price."
            )
            lines.append("")
            lines.append("| node | in failures | in passes | lift | still passes | at risk |")
            lines.append("|---|---|---|---|---|---|")
            n_fail = disc["tasks"]
            for node in sorted(shared, key=_rank_by_lift(lift)):
                st = lift.get(node) or {}
                lf = st.get("lift")
                # Rebuilt from task counts, not from the two rates: they have different
                # denominators, so the share that survives cannot be read off either one.
                with_fail = st.get("fail_rate", 0) * n_fail
                with_pass = st.get("pass_rate", 0) * n_pass
                seen = with_fail + with_pass
                survives = f"{100 * with_pass / seen:.0f}%" if seen else "—"
                # The same quantity as `still passes`, stated as tasks rather than a
                # share. A share reads as a caveat and gets quoted past; a count of
                # currently-passing tasks an edit would gamble reads as a price.
                at_risk = round(with_pass)
                lines.append(
                    f"| `{node}` | {100 * st.get('fail_rate', 0):.1f}% | "
                    f"{100 * st.get('pass_rate', 0):.1f}% | "
                    f"{'n/a (never passes)' if lf is None else f'{lf:.2f}'} | "
                    f"{survives} | "
                    f"**{at_risk}** |"
                )
        else:
            lines.append("Static nodes appearing in the causal cone of more than one failing task:")
            lines.append("")
            lines.append(_NO_CONTROL_LINE)
        lines.append("")
        for node, tasks in shared.items():
            lines.append(f"- `{node}` — tasks: {', '.join(tasks)}")
        lines.append("")
    lines.extend(_render_capability_gaps(gaps or [], disc["tasks"], n_pass))
    lines.append("")
    if edit_history is None:
        lines.append("## Node edit history")
        lines.append(_EDIT_HISTORY_LINE)
        lines.append("")
    else:
        from .node_edit_history import render_node_edit_history

        lines.extend(
            render_node_edit_history(edit_history, priority=sorted(shared, key=_rank_by_lift(lift)))
        )
    return "\n".join(lines)


# ── same-task cross-round diffs (M23) ────────────────────────────────────────


def _load_prior_cone_sigs(run_dir, round_n: int) -> dict | None:
    """The previous round's ``cone_sigs.json``, or ``None`` when absent/unreadable.

    Absence is normal (first round, or a round materialised before this module
    started writing sigs) and reads as *no history*, never as an error.
    """
    path = Path(run_dir) / f"R{round_n - 1}" / "graph_evidence" / "cone_sigs.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _render_regression_diffs(round_n: int, prior_round, rows: list) -> str:
    lines = [
        f"# Same-task cross-round cone diffs — R{round_n}",
        "",
        (
            f"Each task below FAILED this round after PASSING in R{prior_round} under the "
            "then-current config. Unlike the lift table (same round, different tasks — "
            "confounded by task identity), this is the SAME task twice: the difference "
            "between its passing cone and its failing cone is the sharpest per-task causal "
            "evidence this channel produces. A candidate that reverts or targets a 'gained' "
            "node can cite this file directly; the step-level anchors live in the task's "
            "own cone file."
        ),
        "",
    ]
    for task_id, gained, lost in rows:
        lines.append(f"## {task_id}")
        g = ", ".join(f"`{n}`" for n in gained) if gained else "(none)"
        lost_text = ", ".join(f"`{n}`" for n in lost) if lost else "(none)"
        lines.append(f"- gained in the failing cone (absent when it passed): {g}")
        lines.append(f"- lost from the cone (present when it passed): {lost_text}")
        if not gained and not lost:
            lines.append(
                "- the two cones contain the SAME static nodes — the flip is not "
                "explained by cone membership; read the step-level trajectory instead"
            )
        lines.append("")
    return "\n".join(lines)


# ── the pure materialiser ────────────────────────────────────────────────────


def materialize_graph_evidence(
    run_dir,
    round_n: int,
    failed_task_ids,
    resolver,
    passed_task_ids=None,
    capability_resolver=None,
    flip_task_ids=None,
    passed_now_task_ids=None,
) -> dict:
    """Write cone maps + ``facts.md`` under ``<run_dir>/R{round_n}/graph_evidence/``.

    ``failed_task_ids`` is the caller's failing-task list — this function never
    re-derives pass/fail.  ``passed_task_ids`` is the optional CONTROL arm (v6 M13): their
    cones are computed but no cone file is written for them, and they exist only so
    ``facts.md`` can report lift instead of bare failure frequency (see :func:`_lift`).
    Omit it and the behaviour is exactly as before, with facts.md saying plainly that lift
    was not measured rather than implying every node is equally uninformative.

    ``flip_task_ids`` (M23) are tasks that failed THIS rollout but are excluded from
    ``failed_task_ids`` by the caller's lottery filter (they passed before). They get
    cone files and cone_sigs entries — and therefore same-task cross-round diffs, which
    is the whole point: the flip family IS the diff channel's subject.

    M25: they also count as failures in shared/lift/discrimination.  They did not
    until now, and the omission was not neutral — the caller's ``passed_task_ids``
    is the exact complement of ``failed_task_ids``, so every flip landed in the LIFT
    CONTROL ARM instead.  A column headed "in passes" was counting this round's
    failures as passes, and it degrades exactly where the statistic is supposed to
    work: a node concentrated in failures gets its pass-side rate inflated by the
    failing cones hiding there, so the most discriminating nodes are compressed the
    hardest.  Measured on M25 R11 (14 counted failing, 89 control, of which 19 had
    failed that rollout): ``tool:Read`` fell below the shared-node threshold and
    vanished from the table at a true lift of 8.48, and ``tool:Bash#empty`` published
    2.54 against a true 5.30.  The lottery filter's purpose — keeping lottery losers
    out of the DIGESTS — is untouched by this: ``failed_task_ids`` still decides who
    gets digested.  Lineage still shows up here, as the ``chronic`` count under the
    partition line.  ``passed_now_task_ids`` scopes the passing side (lift control,
    at-risk denominator, and cone_sigs' passing map) to tasks that ACTUALLY passed
    this rollout.  ``None`` keeps the legacy behaviour (every control task counts as
    passing).

    ``resolver`` maps a task id to its U
    (:class:`~harnessx.graph.unfold.UnfoldedGraph`), a path to a U JSONL file, or
    ``None`` when unavailable; a task whose U is unavailable or empty gets **no**
    cone file (its absence is unambiguous) and is reported under ``missing_u``.
    Solved tasks are simply not in ``failed_task_ids`` and get nothing.

    Returns a summary dict: ``cones_written`` (task ids), ``missing_u`` (task ids
    with no usable U), ``shared_nodes`` (the facts.md shared map), ``discrimination``
    (:func:`_discrimination` — how much the map varies with the task, including the
    ``degenerate`` flag), and the two written directories/paths — for the caller's
    audit trail and for tests.
    """
    ev_dir = Path(run_dir) / f"R{round_n}" / "graph_evidence"
    cones_dir = ev_dir / "cones"
    ev_dir.mkdir(parents=True, exist_ok=True)
    passing_now = (
        {str(t) for t in passed_now_task_ids} if passed_now_task_ids is not None else None
    )

    per_task_static_nodes: dict[str, set] = {}
    cones_written: list[str] = []
    missing_u: list[str] = []
    # Kept, not discarded with the loop: an absent capability is located by the
    # trajectory step indices the judge cited, and turning those into static nodes
    # needs the U itself, not the flattened node set.
    failing_u: dict[str, UnfoldedGraph] = {}
    passing_u: dict[str, UnfoldedGraph] = {}

    for task_id in failed_task_ids:
        u = _load_u(resolver(task_id))
        if u is None or not u.nodes:
            missing_u.append(task_id)
            continue
        anchors = _cone_anchors(u)
        if not anchors:
            missing_u.append(task_id)
            continue
        cone = _attribution_cone(u, anchors)
        cones_dir.mkdir(parents=True, exist_ok=True)
        (cones_dir / f"{task_id}.md").write_text(_render_cone(task_id, u, anchors, cone), encoding="utf-8")
        cones_written.append(task_id)
        per_task_static_nodes[task_id] = _cone_static_signature(u, cone)
        failing_u[task_id] = u

    # Flip tasks (M23): failed this rollout, filtered out of failed_task_ids because
    # they passed before. Cone files + sigs + diffs, and (M25) the failing side of the
    # statistics — they failed, and the alternative was counting them as passes.
    flip_sigs: dict[str, set] = {}
    for task_id in flip_task_ids or ():
        if task_id in per_task_static_nodes:
            continue
        u = _load_u(resolver(task_id))
        if u is None or not u.nodes:
            continue
        anchors = _cone_anchors(u)
        if not anchors:
            continue
        cone = _attribution_cone(u, anchors)
        cones_dir.mkdir(parents=True, exist_ok=True)
        (cones_dir / f"{task_id}.md").write_text(_render_cone(task_id, u, anchors, cone), encoding="utf-8")
        cones_written.append(task_id)
        flip_sigs[task_id] = _cone_static_signature(u, cone)
        failing_u[task_id] = u

    # Control arm: cones only, no files. A passing task whose U is unavailable is simply
    # absent from the control — it is never reported as missing_u, which names failing
    # tasks that got no cone file.
    control_nodes: dict[str, set] = {}
    for task_id in passed_task_ids or ():
        u = _load_u(resolver(task_id))
        if u is None or not u.nodes:
            continue
        anchors = _cone_anchors(u)
        if not anchors:
            continue
        control_nodes[task_id] = _cone_static_signature(u, _attribution_cone(u, anchors))
        # Only a run that actually passed may speak for the passing side — a flip's U
        # is this round's FAILING run and is already on the failing side above.
        if passing_now is None or task_id in passing_now:
            passing_u[task_id] = u

    # This rollout's outcome partition: everything that failed against everything that
    # passed.  See the docstring for why the flip family belongs on the failing side.
    all_failing_sigs = {**per_task_static_nodes, **flip_sigs}
    passing_now_sigs = (
        control_nodes
        if passing_now is None
        else {t: s for t, s in control_nodes.items() if t in passing_now}
    )
    shared = _compute_shared_nodes(all_failing_sigs)
    disc = _discrimination(all_failing_sigs)
    lift = _lift(all_failing_sigs, passing_now_sigs)
    cap_by_task = {}
    if capability_resolver is not None:
        for task_id in list(failing_u) + list(passing_u):
            try:
                cap_by_task[task_id] = capability_resolver(task_id) or {}
            except Exception:  # noqa: BLE001 — a missing verdict never sinks the round
                cap_by_task[task_id] = {}
    gaps = _capability_gaps(failing_u, passing_u, cap_by_task)
    # The loop's memory of its own edits. Failing to build it must never cost the
    # round its evidence file — an absent history renders as the honest
    # "not recorded" line, which is what every round said before M25.
    try:
        from .node_edit_history import collect_node_edits

        edit_history = collect_node_edits(run_dir, round_n)
    except Exception as exc:  # noqa: BLE001
        _log.warning("node edit history unavailable (%s) — facts.md falls back", exc)
        edit_history = None
    facts_path = ev_dir / "facts.md"
    facts_path.write_text(
        _render_facts(
            round_n,
            shared,
            disc,
            lift,
            len(passing_now_sigs),
            gaps,
            n_chronic=len(per_task_static_nodes),
            edit_history=edit_history,
        ),
        encoding="utf-8",
    )

    # M23: persist this round's cone signatures (both sides) so the NEXT round can
    # compute same-task cross-round diffs. The control cones existed only in memory
    # before this — a P→F flip's passing cone was recomputed nowhere and the sharpest
    # per-task causal comparison was silently impossible.
    sigs_path = ev_dir / "cone_sigs.json"
    sigs_path.write_text(
        json.dumps(
            {
                "round": round_n,
                "failing": {t: sorted(s) for t, s in all_failing_sigs.items()},
                # Only genuinely-passing runs may seed the diff baseline (see docstring).
                "passing": {t: sorted(s) for t, s in passing_now_sigs.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    regression_rows: list = []
    prior = _load_prior_cone_sigs(run_dir, round_n)
    if prior:
        prior_pass = prior.get("passing") or {}
        for t in sorted(all_failing_sigs):
            if t in prior_pass:
                before = set(prior_pass[t])
                now = set(all_failing_sigs[t])
                regression_rows.append((t, sorted(now - before), sorted(before - now)))
    diffs_path = None
    if regression_rows:
        diffs_path = ev_dir / "regression_diffs.md"
        diffs_path.write_text(
            _render_regression_diffs(round_n, prior.get("round", round_n - 1), regression_rows),
            encoding="utf-8",
        )

    return {
        "cone_sigs_path": str(sigs_path),
        "flip_cones_written": sorted(flip_sigs),
        "regression_diff_tasks": [t for t, _g, _l in regression_rows],
        "regression_diffs_path": str(diffs_path) if diffs_path else None,
        "discrimination": disc,
        "lift": lift,
        "control_tasks": len(control_nodes),
        "evidence_dir": str(ev_dir),
        "cones_dir": str(cones_dir),
        "facts_path": str(facts_path),
        "cones_written": cones_written,
        "missing_u": missing_u,
        "shared_nodes": shared,
        "capability_gaps": gaps,
    }
