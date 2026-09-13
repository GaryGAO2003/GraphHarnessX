# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The seam where a GHX artifact could be mistaken for a rollout.

``run_meta_aegis._flatten_sessions_to_raw`` copies a session dir into the flat ``raw/``
that AEGIS Stage P globs, numbering what it finds ``<task>_r<i>.jsonl``. Its filter is a
one-entry blacklist — *every* ``.jsonl`` in the session dir except ``*_trace.jsonl``
counts as one rollout — so any new artifact written beside the trajectory silently
becomes a phantom rollout AND shifts the real rollouts' indices.

That is not hypothetical: U (``*_unfolded.jsonl``) sat there from L1 through
``M13_lift_103x2`` and was read back by ``trace_facts`` as a rollout with
``steps=0, exit=unknown``, so every GHX-arm digest carried a Layer A table where half
the rows were parse garbage — while the whole unit suite stayed green, because nothing
exercised this function. These tests exist so that cannot repeat silently.

The vendored function is imported and run as-is; nothing here patches it.
"""

from __future__ import annotations

import json
from pathlib import Path

import recipe.gaia_evolver.run_meta_aegis as _pilot
from harnessx.graph.unfold import (
    UnfoldedGraph,
    UnfoldedNode,
    legacy_unfolded_path,
    write_unfolded,
)

RUN_ID = "run-a"
TASK = "task-1"
SESSION_ID = f"aegis/R0-{TASK}"


def _u() -> UnfoldedGraph:
    return UnfoldedGraph(
        run_id=RUN_ID,
        session_id=SESSION_ID,
        nodes=[
            UnfoldedNode(
                id="n@t0",
                static_node_id="n",
                graphed=True,
                hook="task_start",
                step=0,
                ordinal=0,
            )
        ],
        edges=[],
        invokes=[],
    )


def _session_dir(sessions: Path) -> Path:
    """``sessions/aegis/R0-<task>/`` — the layout ``run_meta._run_task`` writes."""
    d = sessions / SESSION_ID
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_rollout_artifacts(sessions: Path) -> Path:
    """The two files the vendored runner itself writes for one rollout."""
    sdir = _session_dir(sessions)
    (sdir / f"{RUN_ID}.jsonl").write_text(
        json.dumps({"session_id": SESSION_ID, "type": "session_start", "step": 0}) + "\n",
        encoding="utf-8",
    )
    (sdir / f"{RUN_ID}_trace.jsonl").write_text(
        json.dumps({"type": "trace"}) + "\n", encoding="utf-8"
    )
    return sdir


def _flatten(tmp_path: Path) -> list[Path]:
    raw = tmp_path / "raw"
    _pilot._flatten_sessions_to_raw(tmp_path / "sessions", raw, [{"task_id": TASK}])
    return sorted(raw.glob("*.jsonl"))


def _is_u(path: Path) -> bool:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0]).get("schema") == (
        "ghx-unfolded-v1"
    )


def test_u_in_the_graph_subdir_is_not_flattened_as_a_rollout(tmp_path):
    """The fix: one rollout in, one rollout out, and it is the trajectory."""
    _write_rollout_artifacts(tmp_path / "sessions")
    write_unfolded(_u(), base_dir=str(tmp_path / "sessions"))

    raw_files = _flatten(tmp_path)

    assert [p.name for p in raw_files] == [f"{TASK}_r0.jsonl"]
    assert not _is_u(raw_files[0])


def test_u_in_the_legacy_position_would_be_flattened_as_a_rollout(tmp_path):
    """Why U had to move — this is the defect, reproduced against the real function.

    Two files land for ONE rollout, and the U file takes ``_r1``: with a second rollout
    present the real one would be numbered ``_r2``, which is how a k=2 round came out
    looking like a k=4 round with two zero-step rollouts.

    If a future vendored patch tightens that blacklist into an allowlist, this test
    fails — and that failure is the *good* news, not a regression. Update it then.
    """
    sdir = _write_rollout_artifacts(tmp_path / "sessions")
    legacy = legacy_unfolded_path(str(tmp_path / "sessions"), SESSION_ID, RUN_ID)
    assert legacy.parent == sdir  # the position U used to be written to
    write_unfolded(_u(), base_dir=str(tmp_path / "sessions"))
    (sdir / "graph" / f"{RUN_ID}_unfolded.jsonl").replace(legacy)

    raw_files = _flatten(tmp_path)

    assert [p.name for p in raw_files] == [f"{TASK}_r0.jsonl", f"{TASK}_r1.jsonl"]
    assert _is_u(raw_files[1])


def test_trace_files_are_excluded_and_consume_no_rollout_index(tmp_path):
    """``_trace.jsonl`` is the one thing the blacklist names — pin that it still holds
    and that skipping it does not burn an index (the ``continue`` precedes the ++)."""
    _write_rollout_artifacts(tmp_path / "sessions")

    raw_files = _flatten(tmp_path)

    assert [p.name for p in raw_files] == [f"{TASK}_r0.jsonl"]


def test_two_real_rollouts_keep_consecutive_indices(tmp_path):
    """With U out of the way, k=2 numbers as r0/r1 — not r0/r2."""
    sessions = tmp_path / "sessions"
    for label, run_id in (("aegis/R0", "run-a"), ("aegis/R1", "run-b")):
        sdir = sessions / f"{label}-{TASK}"
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / f"{run_id}.jsonl").write_text(
            json.dumps({"session_id": f"{label}-{TASK}", "type": "session_start"}) + "\n",
            encoding="utf-8",
        )
        write_unfolded(
            UnfoldedGraph(run_id=run_id, session_id=f"{label}-{TASK}", nodes=[], edges=[], invokes=[]),
            base_dir=str(sessions),
        )

    raw_files = _flatten(tmp_path)

    assert [p.name for p in raw_files] == [f"{TASK}_r0.jsonl", f"{TASK}_r1.jsonl"]
    assert not any(_is_u(p) for p in raw_files)


def test_externalized_tool_results_are_restored_inline(tmp_path):
    """The journal externalizes any tool result over 2 KB (content:"" +
    meta.content_ref -> tool_results/*.txt). The live model saw the payload;
    every reader of the flattened copy did not. Measured on M25 batch R10: of
    204 tool results reading as empty, 195 were externalized successes — the
    dominant failure motif (empty_consumed 29 as-recorded, 6 restored) was
    built on the journal's inline-size encoding. The flattener is the single
    seam every reader sits behind."""
    sdir = _write_rollout_artifacts(tmp_path / "sessions")
    payload = "R" * 5000
    (sdir / "tool_results").mkdir()
    (sdir / "tool_results" / "call1.txt").write_text(payload, encoding="utf-8")
    lines = [
        json.dumps({"session_id": SESSION_ID, "type": "session_start", "step": 0}),
        json.dumps(
            {
                "type": "raw_tool",
                "step": 1,
                "message": {"role": "tool", "content": "", "tool_call_id": "call1", "name": "WebFetch"},
                "meta": {"content_ref": "tool_results/call1.txt", "content_size": 5000},
            }
        ),
        json.dumps(
            {
                "type": "raw_tool",
                "step": 2,
                "message": {"role": "tool", "content": "small inline", "tool_call_id": "call2", "name": "Bash"},
            }
        ),
    ]
    (sdir / f"{RUN_ID}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = _flatten(tmp_path)
    assert len(out) == 1
    rows = [json.loads(line) for line in out[0].read_text(encoding="utf-8").splitlines()]
    restored = rows[1]
    assert restored["message"]["content"] == payload
    assert restored["meta"]["content_restored"] is True
    assert restored["meta"]["content_ref"] == "tool_results/call1.txt"  # provenance kept
    assert rows[2]["message"]["content"] == "small inline"  # untouched


def test_missing_ref_file_leaves_the_line_as_recorded(tmp_path):
    """A restore must never invent content the journal cannot produce."""
    sdir = _write_rollout_artifacts(tmp_path / "sessions")
    (sdir / f"{RUN_ID}.jsonl").write_text(
        json.dumps(
            {
                "type": "raw_tool",
                "step": 1,
                "message": {"role": "tool", "content": "", "tool_call_id": "gone", "name": "WebFetch"},
                "meta": {"content_ref": "tool_results/gone.txt", "content_size": 9999},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = _flatten(tmp_path)
    row = json.loads(out[0].read_text(encoding="utf-8").splitlines()[0])
    assert row["message"]["content"] == ""
    assert "content_restored" not in (row.get("meta") or {})


def test_lines_without_content_ref_are_byte_identical(tmp_path):
    """The restore only rewrites lines it restores — everything else must
    survive the copy byte-for-byte, or the flattener becomes a second place
    trajectories can silently drift from the session record."""
    sdir = _write_rollout_artifacts(tmp_path / "sessions")
    original = (sdir / f"{RUN_ID}.jsonl").read_text(encoding="utf-8")
    out = _flatten(tmp_path)
    assert out[0].read_text(encoding="utf-8") == original
