# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""U file layout: writes go under ``graph/``, reads still resolve the old place.

The move exists so the AEGIS runner's ``sorted(sdir.glob("*.jsonl"))`` sweep — which
treats every non-``_trace`` jsonl in a session dir as one rollout — stops picking U up
and feeding it to the digester as a zero-step rollout.  ``glob`` is not recursive, so
the subdirectory is enough and no vendored code changes.  Every run recorded before the
move still has to read back, which is what the fallback is for.
"""

from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.evidence_files import core_layout_resolver
from harnessx.graph.unfold import (
    UnfoldedGraph,
    UnfoldedNode,
    find_unfolded,
    legacy_unfolded_path,
    session_unfolded_files,
    unfolded_path,
    unfolded_records,
    write_unfolded,
)


def _u(run_id: str = "run-a", session_id: str = "sess") -> UnfoldedGraph:
    return UnfoldedGraph(
        run_id=run_id,
        session_id=session_id,
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


def _write_legacy(base: Path, graph: UnfoldedGraph) -> Path:
    """Write U where it used to live — directly in the session dir."""
    path = legacy_unfolded_path(str(base), graph.session_id, graph.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in unfolded_records(graph):
            fh.write(json.dumps(rec) + "\n")
    return path


def test_write_lands_under_the_graph_subdir(tmp_path):
    written = write_unfolded(_u(), base_dir=str(tmp_path))

    assert written == unfolded_path(str(tmp_path), "sess", "run-a")
    assert written.parent.name == "graph"
    # The whole point: the session dir's own non-recursive jsonl sweep sees nothing.
    assert sorted((tmp_path / "sess").glob("*.jsonl")) == []


def test_find_resolves_the_legacy_layout(tmp_path):
    legacy = _write_legacy(tmp_path, _u())

    assert find_unfolded(str(tmp_path), "sess", "run-a") == legacy


def test_find_prefers_current_layout_over_a_stale_legacy_sibling(tmp_path):
    _write_legacy(tmp_path, _u())
    current = write_unfolded(_u(), base_dir=str(tmp_path))

    # A re-recorded run must read its new file, not the leftover next to it.
    assert find_unfolded(str(tmp_path), "sess", "run-a") == current


def test_find_returns_none_when_neither_layout_has_it(tmp_path):
    assert find_unfolded(str(tmp_path), "sess", "missing") is None


def test_session_scan_covers_both_layouts(tmp_path):
    _write_legacy(tmp_path, _u(run_id="old"))
    write_unfolded(_u(run_id="new"), base_dir=str(tmp_path))

    found = session_unfolded_files(tmp_path / "sess")

    assert [p.name for p in found] == ["new_unfolded.jsonl", "old_unfolded.jsonl"]


def test_resolver_reads_a_pre_move_run(tmp_path):
    """The cross-arm comparison case: an old run's U must still feed the cone."""
    _write_legacy(tmp_path, _u())
    resolve = core_layout_resolver(tmp_path, "sess", {"alpha": "run-a"})

    graph = resolve("alpha")

    assert graph is not None
    assert [n.id for n in graph.nodes] == ["n@t0"]


def test_resolver_reports_a_missing_u_as_unavailable(tmp_path):
    resolve = core_layout_resolver(tmp_path, "sess", {"alpha": "run-a"})

    # None means *unavailable* — never an empty graph, which would read as
    # "this run touched nothing" and silently empty the cone.
    assert resolve("alpha") is None
