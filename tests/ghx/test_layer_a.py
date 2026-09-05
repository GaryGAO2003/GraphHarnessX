# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 P2 — Layer A takeover: surgery, superset, honest fallback.

The fixtures rebuild the run-dir layout the seam depends on
(``R{n}/trajectories`` beside ``R{n-1}/sessions``) with the 2dfc4c37 defect
shape, and pin the three contract points: official sections stay
byte-identical, the false-signal section is gone, and every fallback rung
returns official truth rather than losing it.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.aegis.stages.trace_facts import extract_trace_facts as official_extract
from harnessx.ghx.layer_a import (
    GraphedTraceFacts,
    extract_trace_facts_graphed,
    install_layer_a,
)

TASK = "2dfc4c37-0000-0000-0000-000000000000"


def _mk_traj(run: Path, rnd: int) -> Path:
    d = run / f"R{rnd}" / "trajectories"
    d.mkdir(parents=True, exist_ok=True)
    search = "result rows about worldwide grosses " * 3
    events = [
        {"type": "session_start", "step": 0, "message": None, "task": "q"},
        {
            "type": "raw_assistant",
            "step": 0,
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "c1", "name": "WebSearch", "input": {"query": "worldwide"}},
                    {"id": "c2", "name": "WebSearch", "input": {"query": "domestic"}},
                ],
            },
        },
        {"type": "raw_tool", "step": 0, "message": {"role": "tool", "tool_call_id": "c1", "content": search}},
        {"type": "raw_tool", "step": 0, "message": {"role": "tool", "tool_call_id": "c2", "content": search + "2"}},
        {
            "type": "raw_assistant",
            "step": 1,
            "message": {
                "role": "assistant",
                "content": "fetching",
                "tool_calls": [{"id": "c3", "name": "WebFetch", "input": {"url": "https://x/w"}}],
            },
        },
        {"type": "raw_tool", "step": 1, "message": {"role": "tool", "tool_call_id": "c3", "content": ""}},
        {"type": "raw_assistant", "step": 2, "message": {"role": "assistant", "content": "FINAL ANSWER: 3"}},
        {"type": "episode_end", "exit_reason": "done", "total_steps": 3},
    ]
    p = d / f"{TASK}_r0.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    return p


def _mk_u(run: Path, rnd: int) -> None:
    g = run / f"R{rnd}" / "sessions" / "aegis" / f"R{rnd}-{TASK}" / "graph"
    g.mkdir(parents=True)
    node = lambda base, o, hook, step, outcome="": {  # noqa: E731
        "kind": "node",
        "id": f"{base}@t{o}",
        "static_node_id": base,
        "graphed": True,
        "hook": hook,
        "step": step,
        "ordinal": o,
        "outcome": outcome,
    }
    edge = lambda s, t, key: {  # noqa: E731
        "kind": "edge",
        "edge_type": "observed_data",
        "source": s,
        "target": t,
        "metadata": {"plane": "message", "slot_key": key},
    }
    recs = [
        {"kind": "meta", "run_id": "r", "session_id": f"aegis/R{rnd}-{TASK}"},
        node("model:m", 10, "model", 0),
        node("tool:WebSearch", 20, "tool", 0, "ok"),
        node("tool:WebSearch", 30, "tool", 0, "ok"),
        node("model:m", 40, "model", 1),
        node("tool:WebFetch", 50, "tool", 1, "ok"),  # the drift: raw stamp says ok
        node("model:m", 60, "model", 2),
        edge("tool:WebSearch@t20", "model:m@t40", "msg:3:tool"),
        edge("tool:WebSearch@t20", "model:m@t60", "msg:3:tool"),
        edge("tool:WebSearch@t30", "model:m@t60", "msg:4:tool"),
        edge("tool:WebFetch@t50", "model:m@t60", "msg:6:tool"),
    ]
    (g / "run_unfolded.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")


# ── the takeover ──────────────────────────────────────────────────────────────


def test_superset_markdown(tmp_path):
    run = tmp_path / "arm"
    traj = _mk_traj(run, 3)
    _mk_u(run, 2)
    md = extract_trace_facts_graphed(TASK, [traj]).to_markdown()
    official_md = official_extract(TASK, [traj]).to_markdown()

    # header + Exits + repeats/bursts: byte-identical official sections
    assert md.startswith("## Trace Facts (Layer A — mechanical; do not rewrite)")
    for section in ("### Exits", "### Repeated tool calls", "### Tool burst"):
        assert section in md
    exits_official = official_md.split("### Tool calls")[0].split("### Exits")[1]
    assert exits_official in md
    repeats_official = official_md.split("### Repeated tool calls")[1].split(
        "### Tool calls whose output"
    )[0]
    assert repeats_official in md

    # superset table: flow columns present, WebFetch empty consumed by final
    assert "| result_readers | consumed_by_final |" in md
    assert "| 1 | `WebFetch` |" in md and "| empty | 0 | t60 | yes |" in md
    assert "| 0 | `WebSearch` |" in md and "t40,t60 | yes |" in md

    # the false-signal section is RETIRED, edge truth + motifs in its place
    assert "### Tool calls whose output the next step did NOT reference" not in md
    assert "### Tool results that reached NO model call (observed_data edges)" in md
    assert "### Mechanism signatures (deterministic motifs over U)" in md
    assert "`empty_consumed`" in md and "`ungrounded_commit` [search_only]" in md

    # anchors keep the Layer B/C citation scheme
    assert f"trajectories/{TASK}_r0.jsonl#step_" in md
    # provenance line inserted after the official quote
    assert "Layer A′ (graph-projected)" in md


def test_no_u_falls_back_byte_identical(tmp_path):
    run = tmp_path / "arm"
    traj = _mk_traj(run, 3)  # R2 exists? no — no sessions anywhere
    (run / "R2").mkdir()
    graphed = extract_trace_facts_graphed(TASK, [traj])
    assert graphed.to_markdown() == official_extract(TASK, [traj]).to_markdown()


def test_off_layout_falls_back(tmp_path):
    d = tmp_path / "loose"
    d.mkdir()
    # trajectory NOT under R{n}/trajectories — layout parse must fail soft
    src = _mk_traj(tmp_path / "arm", 3)
    loose = d / src.name
    loose.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    graphed = extract_trace_facts_graphed(TASK, [loose])
    assert graphed.to_markdown() == official_extract(TASK, [loose]).to_markdown()


def test_delegates_official_fields(tmp_path):
    run = tmp_path / "arm"
    traj = _mk_traj(run, 3)
    _mk_u(run, 2)
    graphed = extract_trace_facts_graphed(TASK, [traj])
    assert isinstance(graphed, GraphedTraceFacts)
    # duck-typed passthrough: anything preprocess or a future caller reads
    assert graphed.task_id == TASK
    assert graphed.rollouts == ["r0"]
    assert len(graphed.exits) == 1 and graphed.exits[0].exit_reason == "done"


def test_install_patches_and_restores():
    import harnessx.aegis.stages.preprocess as pp

    original = pp.extract_trace_facts
    with install_layer_a():
        assert pp.extract_trace_facts is extract_trace_facts_graphed
    assert pp.extract_trace_facts is original
    # restores on exception too
    try:
        with install_layer_a():
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert pp.extract_trace_facts is original


def test_readers_column_compression():
    """>3 readers → n=k(first→last); ≤3 → verbatim list; 0 → (none)."""
    from harnessx.ghx.layer_a import _fmt_row
    from harnessx.ghx.projection import ProjectedToolCall

    def row(readers):
        c = ProjectedToolCall(rollout="r0", step=1, tool="WebSearch", tool_call_id="tc1",
                              args_sha="deadbeef", args_preview="{}", return_type="text",
                              return_len=10)
        c.ordinal = 0
        c.reader_ordinals = tuple(readers)
        c.consumed_by_final = bool(readers)
        return _fmt_row(c)

    assert "n=5(t102→t477)" in row([102, 177, 252, 327, 477])
    assert "t102,t177" in row([102, 177])
    assert "(none)" in row([])
