# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M23 (B3) — outcome-annotated tool nodes.

M22's dominant failure mechanism (Bash → empty stdout → retry loop → 20-step
budget death) was invisible at bare-node granularity: ``tool:Bash`` carried
lift 1.73 / at-risk 40 — statistically true, mechanically useless. The runloop
now stamps each tool invocation's outcome (error/empty/ok) on its U node, and
cone signatures grow annotated members (``tool:Bash#empty``) so the lift table
ranks the mechanism, not the tool.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.evidence_files import materialize_graph_evidence
from harnessx.graph.causal import DATA
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedEdge, UnfoldedGraph, UnfoldedNode, UnfoldRecorder


def _n(base: str, ordinal: int, hook: str, step: int, outcome: str = "") -> UnfoldedNode:
    return UnfoldedNode(
        id=unfolded_id(base, ordinal),
        static_node_id=base,
        graphed=True,
        hook=hook,
        step=step,
        ordinal=ordinal,
        label=base,
        outcome=outcome,
    )


def _u(run_id: str, outcome: str) -> UnfoldedGraph:
    t2 = _n("tool:Bash", 2, "tool", 1, outcome=outcome)
    t3 = _n("Eval", 3, "after_tool", 1)
    t4 = _n("End", 4, "task_end", 2)
    edges = [
        UnfoldedEdge(source=t2.id, target=t3.id, edge_type=DATA, metadata={"slot_key": "plan"}),
        UnfoldedEdge(source=t3.id, target=t4.id, edge_type=DATA, metadata={"slot_key": "verdict"}),
    ]
    return UnfoldedGraph(run_id=run_id, session_id="s", nodes=[t2, t3, t4], edges=edges)


def test_recorder_annotates_outcome_after_the_fact():
    rec = UnfoldRecorder("r", "s")
    inv = rec.record_tool_invocation("Bash", 1, None)
    rec.annotate_outcome(inv, "empty")
    assert rec._nodes[-1].outcome == "empty"
    rec.annotate_outcome("nonexistent@t99", "error")  # unknown id: ignored, never invents
    assert rec._nodes[-1].outcome == "empty"


def test_failure_outcome_becomes_a_rankable_signature_member(tmp_path: Path):
    run = tmp_path / "run"
    us = {"alpha": _u("a", "empty"), "beta": _u("b", "empty"), "gamma": _u("g", "ok")}
    summary = materialize_graph_evidence(
        run, 1, ["alpha", "beta"], lambda t: us.get(t), passed_task_ids=["gamma"]
    )

    sigs = json.loads(Path(summary["cone_sigs_path"]).read_text(encoding="utf-8"))
    assert "tool:Bash#empty" in sigs["failing"]["alpha"]
    assert "tool:Bash" in sigs["failing"]["alpha"]  # bare id still present
    assert "tool:Bash#empty" not in sigs["passing"]["gamma"]  # ok adds nothing
    assert "tool:Bash#ok" not in sigs["passing"]["gamma"]

    # Shared across two failing tasks and absent from the passing side → it is in
    # the facts shared-node section AND perfectly discriminating in the lift table.
    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "tool:Bash#empty" in facts
    assert summary["lift"]["tool:Bash#empty"]["lift"] is None  # never passes → n/a (top rank)
    assert summary["lift"]["tool:Bash"]["lift"] == 1.0  # the bare tool explains nothing

    # The cone map itself marks the outcome on the invocation line.
    cone = (run / "R1" / "graph_evidence" / "cones" / "alpha.md").read_text(encoding="utf-8")
    assert "outcome: empty" in cone


def test_pre_m23_u_files_read_back_as_not_annotated(tmp_path: Path):
    # A node record without the outcome key loads with outcome="" (not "ok").
    from harnessx.graph.unfold import _node_record

    n = _n("tool:Bash", 2, "tool", 1, outcome="error")
    rec = _node_record(n)
    assert rec["outcome"] == "error"
    rec.pop("outcome")
    legacy = UnfoldedNode(
        id=rec["id"], static_node_id=rec["static_node_id"], graphed=rec["graphed"],
        hook=rec["hook"], step=rec["step"], ordinal=rec["ordinal"],
        label=rec.get("label", ""), intervention=rec.get("intervention", ""),
        outcome=rec.get("outcome", ""),
    )
    assert legacy.outcome == ""


def test_classify_tool_outcome_judges_flattened_payload():
    """M24 fix #4: structured-block returns with no text are EMPTY (the model
    saw nothing), media blocks are content, raw-string behavior unchanged."""
    from harnessx.graph.unfold import classify_tool_outcome

    assert classify_tool_outcome("real text") == "ok"
    assert classify_tool_outcome("   \n ") == "empty"
    assert classify_tool_outcome(None) == "empty"
    assert classify_tool_outcome("x", error="boom") == "error"
    # the WebFetch shell shape: blocks with empty text → the model saw nothing
    assert classify_tool_outcome([{"type": "text", "text": ""}]) == "empty"
    assert classify_tool_outcome("", content_blocks=({"type": "text", "text": ""},)) == "empty"
    assert classify_tool_outcome([{"type": "text", "text": "body"}]) == "ok"
    # media counts as content (multimodal is not empty)
    assert classify_tool_outcome([{"type": "image", "source": "x"}]) == "ok"
    # content_blocks wins over result when present
    assert classify_tool_outcome("raw shell", content_blocks=({"type": "text", "text": ""},)) == "empty"


def test_classify_tool_outcome_judges_structured_empty_payload():
    """Outcome-fidelity fix: a custom tool's JSON-shaped nothing must grade
    ``empty`` too, not just a blank string — loop_health's ``ghx outcome
    fidelity`` check measured the digest's flattened-text view calling these
    empty while U's raw-content view still said ``ok`` (drift x20 on one
    sampled batch). payload_is_empty is the one predicate both sides share."""
    from harnessx.graph.unfold import classify_tool_outcome, payload_is_empty

    # regression: plain blank text is still empty, unparseable prose still ok
    assert payload_is_empty("") is True
    assert payload_is_empty("   \n ") is True
    assert classify_tool_outcome("") == "empty"
    assert classify_tool_outcome("real text") == "ok"
    assert classify_tool_outcome("not json: still prose") == "ok"

    # structured empties, textually non-blank
    assert classify_tool_outcome("[]") == "empty"
    assert classify_tool_outcome("{}") == "empty"
    assert classify_tool_outcome('{"results": []}') == "empty"
    assert classify_tool_outcome('{"data": {"items": []}}') == "empty"  # nested container, not just top-level
    # error-only payload: a failure signal, not a result, however long the message
    assert classify_tool_outcome('{"error": "rate limited, try again later"}') == "empty"
    assert classify_tool_outcome('{"errors": ["not found"]}') == "empty"

    # real content survives — even when an error key rides along, or the
    # number is a legitimate (falsy) scalar rather than an absence
    assert classify_tool_outcome('{"results": ["Paris", "London"]}') == "ok"
    assert classify_tool_outcome('{"error": "partial", "results": ["a"]}') == "ok"
    assert classify_tool_outcome('{"count": 0}') == "ok"

    # error kwarg still short-circuits before any payload parsing
    assert classify_tool_outcome('{"results": []}', error="boom") == "error"
