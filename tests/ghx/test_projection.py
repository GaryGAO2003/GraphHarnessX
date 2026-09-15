# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 P0 — the U↔trajectory projection join and the v1 motif library.

The fixtures rebuild the shape of the real defect this module exists for
(2dfc4c37, batch 11): two WebSearch calls whose text results DID flow into the
terminal model call (the official heuristic said **NO**), and two WebFetch
calls whose payloads flattened to empty yet still reached the terminal call
(U's raw-return outcome said ``ok``).  The projection must tell both truths at
once; the motifs must turn them into ``empty_consumed`` + ``ungrounded_commit``.
"""
from __future__ import annotations

import json
from pathlib import Path


from harnessx.graph.causal import DATA
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedEdge, UnfoldedGraph, UnfoldedNode
from harnessx.ghx.motifs import evaluate_motifs
from harnessx.ghx.projection import (
    args_sha,
    classify_return,
    content_to_text,
    project_rollout,
)

TASK = "0000feed-0000-0000-0000-00000000cafe"


# ── fixture builders ──────────────────────────────────────────────────────────


def _node(base: str, ordinal: int, hook: str, step: int, outcome: str = "") -> UnfoldedNode:
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


def _data_edge(src: UnfoldedNode, tgt: UnfoldedNode, key: str) -> UnfoldedEdge:
    return UnfoldedEdge(source=src.id, target=tgt.id, edge_type=DATA, metadata={"slot_key": key})


def _write_traj(tmp_path: Path, events: list[dict], name: str = f"{TASK}_r0.jsonl") -> Path:
    p = tmp_path / name
    p.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    return p


def _asst(step: int, content, tool_calls=None) -> dict:
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"type": "raw_assistant", "step": step, "message": msg}


def _tool_result(step: int, tcid: str, content) -> dict:
    return {"type": "raw_tool", "step": step, "message": {"role": "tool", "tool_call_id": tcid, "content": content}}


def _tc(tcid: str, name: str, args: dict) -> dict:
    return {"id": tcid, "name": name, "input": args}


def _end(exit_reason: str, total_steps: int) -> dict:
    return {"type": "episode_end", "exit_reason": exit_reason, "total_steps": total_steps}


def _defect_shape_traj(tmp_path: Path) -> Path:
    """Two WebSearch (text) at step 0, two WebFetch (payload flattens empty) at
    step 1, fabricated FINAL ANSWER at step 2."""
    search_a = "S" * 60 + " worldwide top 10 result rows " + "A" * 40
    search_b = "S" * 60 + " domestic top 10 result rows " + "B" * 40
    return _write_traj(
        tmp_path,
        [
            {"type": "session_start", "step": 0, "message": None, "task": "q"},
            _asst(0, "", [_tc("c1", "WebSearch", {"query": "worldwide"}), _tc("c2", "WebSearch", {"query": "domestic"})]),
            _tool_result(0, "c1", search_a),
            _tool_result(0, "c2", search_b),
            _asst(1, "fetching pages", [_tc("c3", "WebFetch", {"url": "https://x/world"}), _tc("c4", "WebFetch", {"url": "https://x/dom"})]),
            _tool_result(1, "c3", ""),
            _tool_result(1, "c4", None),
            _asst(2, "Based on the lists I retrieved... FINAL ANSWER: 3"),
            _end("done", 3),
        ],
    )


def _defect_shape_u() -> UnfoldedGraph:
    """U for the same rollout — outcomes stamped the way the CURRENT recorder
    does (WebFetch shells grade ``ok``: the drift this join corrects)."""
    m0 = _node("model:m", 10, "model", 0)
    s1 = _node("tool:WebSearch", 20, "tool", 0, outcome="ok")
    s2 = _node("tool:WebSearch", 30, "tool", 0, outcome="ok")
    m1 = _node("model:m", 40, "model", 1)
    f1 = _node("tool:WebFetch", 50, "tool", 1, outcome="ok")
    f2 = _node("tool:WebFetch", 60, "tool", 1, outcome="ok")
    m2 = _node("model:m", 70, "model", 2)
    nodes = [m0, s1, s2, m1, f1, f2, m2]
    edges = [
        _data_edge(s1, m1, "msg:3:tool"),
        _data_edge(s1, m2, "msg:3:tool"),
        _data_edge(s2, m1, "msg:4:tool"),
        _data_edge(s2, m2, "msg:4:tool"),
        _data_edge(f1, m2, "msg:7:tool"),
        _data_edge(f2, m2, "msg:8:tool"),
    ]
    return UnfoldedGraph(run_id="run", session_id=f"aegis/R11-{TASK}", nodes=nodes, edges=edges)


# ── classifier parity ─────────────────────────────────────────────────────────


def test_classifier_parity_with_vendored():
    from harnessx.aegis.stages import trace_facts as tf

    cases = [
        None,
        "",
        "   \n ",
        "plain text result " * 10,
        "Error: connection refused",
        "some Traceback (most recent call last) mid",
        "<image>",
        "[image displayed below]",
        [{"type": "text", "text": "hello"}, {"type": "image", "source": "x"}],
        [{"type": "text", "text": "only text block"}],
        ["bare", {"other": 1}],
        {"query": "x", "k": 2},
    ]
    for c in cases:
        assert content_to_text(c) == tf._content_to_text(c), c
        txt, structured = content_to_text(c)
        assert classify_return(txt, structured) == tf._classify_return(txt, structured), c
    for a in ({"q": 1}, [1, 2], "s", None, {"b": {"a": 1}}):
        assert args_sha(a) == tf._args_sha(a)


# ── projection join ───────────────────────────────────────────────────────────


def test_join_tells_both_truths(tmp_path):
    rep = project_rollout(TASK, _defect_shape_traj(tmp_path), _defect_shape_u())
    assert rep.u_available and not rep.pairing_conflicts
    assert rep.final_model_ordinal == 70
    assert rep.final_answer_emitted and rep.final_answer_step == 2
    assert rep.exit_reason == "done" and rep.total_steps == 3

    s1, s2, f1, f2 = rep.tool_calls
    # payload truth (message plane): searches text, fetches empty
    assert (s1.return_type, s2.return_type) == ("text", "text")
    assert f1.return_type == "empty" and f1.return_len == 0
    assert f2.return_type == "empty" and f2.return_len == 0
    # flow truth (U edges): ALL four reached the terminal model call
    assert s1.reader_ordinals == (40, 70) and s1.consumed_by_final
    assert f1.reader_ordinals == (70,) and f1.consumed_by_final
    # drift metric survives the join: U said ok where the message plane says empty
    assert f1.outcome_u == "ok" and f1.payload_empty
    # pairing carried U identities
    assert (s1.ordinal, s2.ordinal, f1.ordinal, f2.ordinal) == (20, 30, 50, 60)


def test_no_u_degrades_honestly(tmp_path):
    rep = project_rollout(TASK, _defect_shape_traj(tmp_path), None)
    assert not rep.u_available
    assert all(c.ordinal == -1 and c.reader_ordinals == () for c in rep.tool_calls)
    # payload columns still exact
    assert [c.return_type for c in rep.tool_calls] == ["text", "text", "empty", "empty"]


def test_pairing_conflict_is_loud_not_silent(tmp_path):
    u = _defect_shape_u()
    u.nodes = [n for n in u.nodes if n.ordinal != 60]  # drop one WebFetch node
    rep = project_rollout(TASK, _defect_shape_traj(tmp_path), u)
    assert len(rep.pairing_conflicts) == 1
    assert "step 1 tool WebFetch" in rep.pairing_conflicts[0]
    f1, f2 = rep.tool_calls[2], rep.tool_calls[3]
    assert f1.ordinal == 50  # first still pairs positionally
    assert f2.ordinal == -1  # unpaired emitted without flow columns


def test_structured_empty_payload_upgrades_return_type(tmp_path):
    """A custom tool's JSON-shaped nothing ('{"results": []}', an error-only
    object) must grade "empty" here too — not just via classify_tool_outcome
    on the U side — or projection's own return_type/outcome_u pairing
    reintroduces the drift this module exists to close, just pointed the
    other way (outcome_u=="empty", return_type=="text")."""
    traj = _write_traj(
        tmp_path,
        [
            _asst(
                0,
                "",
                [
                    _tc("c1", "CustomSearch", {"q": "x"}),
                    _tc("c2", "CustomSearch", {"q": "y"}),
                    _tc("c3", "CustomSearch", {"q": "z"}),
                ],
            ),
            _tool_result(0, "c1", '{"results": []}'),
            _tool_result(0, "c2", '{"error": "rate limited"}'),
            _tool_result(0, "c3", '{"results": ["a real hit"]}'),
            _end("done", 1),
        ],
    )
    rep = project_rollout(TASK, traj, None)
    empty1, empty2, ok1 = rep.tool_calls
    assert empty1.return_type == "empty" and empty1.payload_empty
    assert empty2.return_type == "empty" and empty2.payload_empty
    assert ok1.return_type == "text" and not ok1.payload_empty


def test_missing_result_grades_missing(tmp_path):
    traj = _write_traj(
        tmp_path,
        [
            _asst(0, "", [_tc("c1", "Bash", {"command": "x"})]),
            _end("error", 1),
        ],
    )
    rep = project_rollout(TASK, traj, None)
    assert rep.tool_calls[0].return_type == "missing"
    assert rep.exit_reason == "error"


# ── motifs ────────────────────────────────────────────────────────────────────


def test_motifs_on_defect_shape(tmp_path):
    rep = project_rollout(TASK, _defect_shape_traj(tmp_path), _defect_shape_u())
    m = evaluate_motifs(rep)
    assert m.get("empty_consumed") and m.get("empty_consumed").count == 2
    ug = m.get("ungrounded_commit")
    assert ug is not None and ug.params["search_only"] is True and ug.params["degraded"] is False
    assert m.primary == "ungrounded_commit"  # commit family outranks the feed line
    assert m.get("budget_no_commit") is None and m.get("retry_loop") is None


def test_m2_not_fired_when_page_evidence_consumed(tmp_path):
    traj = _write_traj(
        tmp_path,
        [
            _asst(0, "", [_tc("c1", "WebFetch", {"url": "u"})]),
            _tool_result(0, "c1", "real page body " * 20),
            _asst(1, "FINAL ANSWER: 42"),
            _end("done", 2),
        ],
    )
    f = _node("tool:WebFetch", 10, "tool", 0, outcome="ok")
    m1 = _node("model:m", 20, "model", 1)
    u = UnfoldedGraph(run_id="r", session_id="s", nodes=[f, m1], edges=[_data_edge(f, m1, "msg:2:tool")])
    m = evaluate_motifs(project_rollout(TASK, traj, u))
    assert m.get("ungrounded_commit") is None
    assert m.primary == "none"


def test_m2_degraded_without_u(tmp_path):
    traj = _write_traj(
        tmp_path,
        [
            _asst(0, "", [_tc("c1", "WebSearch", {"q": "x"})]),
            _tool_result(0, "c1", "snippet " * 30),
            _asst(1, "FINAL ANSWER: memory"),
            _end("done", 2),
        ],
    )
    m = evaluate_motifs(project_rollout(TASK, traj, None))
    ug = m.get("ungrounded_commit")
    assert ug is not None and ug.params["degraded"] is True and ug.params["search_only"] is True
    # M1 must ABSTAIN without U — never a hit it cannot know
    assert m.get("empty_consumed") is None


def test_m3a_budget_no_commit(tmp_path):
    traj = _write_traj(
        tmp_path,
        [
            _asst(0, "working", [_tc("c1", "Bash", {"command": "x"})]),
            _tool_result(0, "c1", ""),
            _end("budget_exceeded", 20),
        ],
    )
    m = evaluate_motifs(project_rollout(TASK, traj, None))
    assert m.get("budget_no_commit") is not None
    assert m.primary == "budget_no_commit"
    # ledger override wins over the trajectory's own exit
    m2 = evaluate_motifs(project_rollout(TASK, traj, None), exit_reason="done")
    assert m2.get("budget_no_commit") is None


def test_m4_retry_loop(tmp_path):
    same = {"command": "python3 -c ..."}
    traj = _write_traj(
        tmp_path,
        [
            _asst(0, "", [_tc("c1", "Bash", same)]),
            _tool_result(0, "c1", ""),
            _asst(1, "", [_tc("c2", "Bash", same)]),
            _tool_result(1, "c2", ""),
            _asst(2, "", [_tc("c3", "Bash", same)]),
            _tool_result(2, "c3", ""),
            _end("budget_exceeded", 20),
        ],
    )
    m = evaluate_motifs(project_rollout(TASK, traj, None))
    hit = m.get("retry_loop")
    assert hit is not None and hit.params["worst_len"] == 3
    assert m.primary == "budget_no_commit"  # outcome family outranks the loop cause


def test_consumed_rate_ignores_empties(tmp_path):
    rep = project_rollout(TASK, _defect_shape_traj(tmp_path), _defect_shape_u())
    assert rep.consumed_rate() == 1.0  # both non-empty searches were consumed
