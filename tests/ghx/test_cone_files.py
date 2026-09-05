# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""G1 test 1 + 6 — cone maps per failing task, and stable round-scoped layout.

The materialiser is pure, so these run on hand-built U's whose cone is obvious
by inspection: a control+data chain into a terminal task_end anchor, with one
deliberately-unrelated node that must stay OUT of the cone. We assert ordinal
ordering, the slot data-flow line, the INVOKES frontier, the trajectory step
pointers, caller-driven failing-task selection (solved tasks get nothing), and
the honest missing-U path.
"""

from __future__ import annotations

from pathlib import Path

from harnessx.ghx.evidence_files import materialize_graph_evidence
from harnessx.graph.causal import CONTROL, DATA
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedEdge, UnfoldedGraph, UnfoldedInvokes, UnfoldedNode


def _n(base: str, ordinal: int, hook: str, step: int, intervention: str = "") -> UnfoldedNode:
    return UnfoldedNode(
        id=unfolded_id(base, ordinal),
        static_node_id=base,
        graphed=True,
        hook=hook,
        step=step,
        ordinal=ordinal,
        label=base,
        intervention=intervention,
    )


def _alpha_u() -> UnfoldedGraph:
    """A U whose attribution cone is {t0, t2, t3, t4}; t1 is in the control chain but out.

    Both halves of :func:`~harnessx.ghx.evidence_files._attribution_cone` are exercised,
    and each is the ONLY reason its node is in:

    t1 Passthrough --control--> t2 tool:Bash --control--> t3 Eval --control--> t4 End
    t2 tool:Bash   --data(plan)---> t3 Eval --data(verdict)---> t4 End
    t0 Sys         intervened, NO edges at all
    t2 --INVOKES--> child-run-1

    t2/t3 are in on data ancestry alone.  t0 is in on its intervention alone — nothing
    connects it to the anchor.  t1 is a control-only ancestor of the anchor that changed
    nothing, so it is OUT: sitting upstream in the firing is no longer membership.
    """
    t0 = _n("Sys", 0, "before_model", 0, intervention="context_truncated")
    t1 = _n("Passthrough", 1, "before_model", 0)
    t2 = _n("tool:Bash", 2, "tool", 1)
    t3 = _n("Eval", 3, "after_tool", 1)
    t4 = _n("End", 4, "task_end", 2)
    edges = [
        UnfoldedEdge(source=t1.id, target=t2.id, edge_type=CONTROL),
        UnfoldedEdge(source=t2.id, target=t3.id, edge_type=CONTROL),
        UnfoldedEdge(source=t3.id, target=t4.id, edge_type=CONTROL),
        UnfoldedEdge(source=t2.id, target=t3.id, edge_type=DATA, metadata={"slot_key": "plan"}),
        UnfoldedEdge(source=t3.id, target=t4.id, edge_type=DATA, metadata={"slot_key": "verdict"}),
    ]
    return UnfoldedGraph(
        run_id="alpha-run",
        session_id="s",
        nodes=[t0, t1, t2, t3, t4],
        edges=edges,
        invokes=[UnfoldedInvokes(source=t2.id, child_run_id="child-run-1")],
    )


def test_cone_file_content(tmp_path: Path):
    run_dir = tmp_path / "run"
    summary = materialize_graph_evidence(
        run_dir,
        1,
        ["alpha"],
        lambda t: _alpha_u() if t == "alpha" else None,
    )
    cone = Path(summary["cones_dir"]) / "alpha.md"
    body = cone.read_text(encoding="utf-8")

    # Invocations section: ordinal order, unrelated node excluded.
    inv = body.split("## Invocations (ordinal order)")[1].split("##")[0]
    assert inv.index("t0:") < inv.index("t2:") < inv.index("t3:") < inv.index("t4:")
    # A control-only ancestor of the anchor that changed nothing is NOT in the cone.
    assert "t1:" not in inv
    assert "Passthrough" not in body
    # Step pointers travel on each invocation line.
    assert "- t2: tool tool:Bash [step 1]" in body
    assert "- t4: task_end End [step 2]" in body
    # An invocation that intervened says so, and is in on that alone.
    assert "- t0: before_model Sys [step 0] — CHANGED THE RUN: context_truncated" in body

    # Data-flow section (slot and message planes share it).
    assert "## Data-flow (writer -> reader)" in body
    assert "- plan: t2 -> t3" in body
    assert "- verdict: t3 -> t4" in body

    # INVOKES frontier (cone reached a subagent boundary).
    assert "## INVOKES frontier" in body
    assert "child-run-1" in body

    # Trajectory step pointers — the map the reader opens.
    steps = body.split("## Trajectory steps that causally mattered")[1]
    assert "0, 1, 2" in steps
    # It is a MAP, not a payload — say so.
    assert "MAP, not a payload" in body


def test_selection_is_caller_driven(tmp_path: Path):
    """Only tasks in the failing list get cones; solved tasks get none even when
    the resolver could produce a U for them; a failing task with no U is honestly
    reported (no empty cone file implying 'no cone')."""
    run_dir = tmp_path / "run"

    def resolver(task: str):
        if task in ("alpha", "beta"):
            return _alpha_u()
        return None  # gamma: failing but U unavailable

    summary = materialize_graph_evidence(run_dir, 1, ["alpha", "gamma"], resolver)
    cones_dir = Path(summary["cones_dir"])

    assert (cones_dir / "alpha.md").exists()
    assert not (cones_dir / "beta.md").exists()  # solved (not in failing list)
    assert not (cones_dir / "gamma.md").exists()  # failing but U unavailable
    assert summary["cones_written"] == ["alpha"]
    assert summary["missing_u"] == ["gamma"]


def _beta_u() -> UnfoldedGraph:
    """A second run whose cone shares only the terminal node with ``_alpha_u``'s."""
    t0 = _n("Other", 0, "before_model", 0, intervention="loop_warning")
    t1 = _n("tool:WebFetch", 1, "tool", 0)
    t2 = _n("End", 2, "task_end", 1)
    return UnfoldedGraph(
        run_id="beta-run",
        session_id="s",
        nodes=[t0, t1, t2],
        edges=[UnfoldedEdge(source=t1.id, target=t2.id, edge_type=DATA, metadata={"slot_key": "answer"})],
    )


def test_degenerate_map_is_named_not_hidden(tmp_path: Path):
    """Two failing tasks whose cones are identical carry zero bits about either one.

    This is the check the evidence channel most needs, because the failure is invisible
    by construction: every task still gets a full, plausible cone file. Nothing raises —
    the round is fine, the *evidence* is not — but the state is named in ``facts.md``
    and in the returned summary rather than reading as coverage.
    """
    run_dir = tmp_path / "run"
    summary = materialize_graph_evidence(run_dir, 1, ["alpha", "beta"], lambda t: _alpha_u())

    disc = summary["discrimination"]
    assert disc["tasks"] == 2
    assert disc["distinct_signatures"] == 1
    assert disc["mean_jaccard"] == 1.0
    assert disc["degenerate"] is True

    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "carries no information" in facts
    assert "1 distinct cone signature(s)" in facts


def test_discriminating_map_is_not_flagged(tmp_path: Path):
    """Two failing tasks with different cones: the map is a real function of the task."""
    run_dir = tmp_path / "run"
    summary = materialize_graph_evidence(
        run_dir, 1, ["alpha", "beta"], lambda t: _alpha_u() if t == "alpha" else _beta_u()
    )

    disc = summary["discrimination"]
    assert disc["distinct_signatures"] == 2
    assert disc["degenerate"] is False
    assert 0.0 < disc["mean_jaccard"] < 1.0  # they share "End", nothing else

    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "carries no information" not in facts


def test_single_task_is_never_degenerate(tmp_path: Path):
    """One failing task cannot show whether the map varies — absence of evidence, not
    evidence of a constant map."""
    run_dir = tmp_path / "run"
    summary = materialize_graph_evidence(run_dir, 1, ["alpha"], lambda t: _alpha_u())

    disc = summary["discrimination"]
    assert disc["tasks"] == 1
    assert disc["mean_jaccard"] is None  # no pairs to compare
    assert disc["degenerate"] is False


def test_stable_round_scoped_layout(tmp_path: Path):
    """Files land under R{n}/graph_evidence/ with stable names."""
    run_dir = tmp_path / "run"
    summary = materialize_graph_evidence(run_dir, 7, ["alpha"], lambda t: _alpha_u())

    ev = run_dir / "R7" / "graph_evidence"
    assert Path(summary["evidence_dir"]) == ev
    assert Path(summary["facts_path"]) == ev / "facts.md"
    assert Path(summary["cones_dir"]) == ev / "cones"
    assert (ev / "cones" / "alpha.md").exists()
    assert (ev / "facts.md").exists()
