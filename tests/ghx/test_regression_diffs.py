# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M23 — same-task cross-round cone diffs.

The lift table compares failing tasks against OTHER passing tasks in the same
round, which is confounded by task identity. The sharpest per-task causal
evidence is the same task twice: its passing cone vs its failing cone across
rounds. Before this module wrote ``cone_sigs.json`` the passing side existed
only in memory and was discarded, so the comparison was silently impossible —
M22's C-R5-01 (9 ALL_PASS→ALL_FAIL flips) had to be hand-verified by the
Critic with throwaway scripts, and the revert candidate then died on IV-3 for
citing that hand-work in prose.
"""
from __future__ import annotations

from pathlib import Path

from harnessx.ghx.brief_pointers import digester_evidence_paths, planner_evidence_paths
from harnessx.ghx.evidence_files import materialize_graph_evidence
from harnessx.graph.causal import DATA
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedEdge, UnfoldedGraph, UnfoldedNode


def _n(base: str, ordinal: int, hook: str, step: int) -> UnfoldedNode:
    return UnfoldedNode(
        id=unfolded_id(base, ordinal),
        static_node_id=base,
        graphed=True,
        hook=hook,
        step=step,
        ordinal=ordinal,
        label=base,
    )


def _mk_u(run_id: str, tool_base: str) -> UnfoldedGraph:
    """A U whose attribution cone contains {tool_base, Eval, End}."""
    t2 = _n(tool_base, 2, "tool", 1)
    t3 = _n("Eval", 3, "after_tool", 1)
    t4 = _n("End", 4, "task_end", 2)
    edges = [
        UnfoldedEdge(source=t2.id, target=t3.id, edge_type=DATA, metadata={"slot_key": "plan"}),
        UnfoldedEdge(source=t3.id, target=t4.id, edge_type=DATA, metadata={"slot_key": "verdict"}),
    ]
    return UnfoldedGraph(run_id=run_id, session_id="s", nodes=[t2, t3, t4], edges=edges)


def test_flip_failures_do_not_wash_a_discriminating_node_out_of_the_lift_table(tmp_path: Path):
    """The live M25 R11 shape, shrunk: a node that only ever appears when the task
    fails, but whose failures are mostly flips.

    Routing flips into the control arm hits such a node twice — it falls under the
    shared-node threshold (too few *counted* failures to earn a row) and its pass
    rate is inflated by its own failing cones. On the live bed that erased
    ``tool:Read`` (true lift 8.48) from the table entirely and halved
    ``tool:Bash#empty`` (5.30 published as 2.54)."""
    run = tmp_path / "run"
    chronic, flips = ["f1"], ["f2", "f3"]
    passers = ["p1", "p2", "p3", "p4", "p5"]
    us = {t: _mk_u(t, "tool:Read") for t in chronic + flips}
    us.update({t: _mk_u(t, "tool:WebSearch") for t in passers})

    s = materialize_graph_evidence(
        run,
        1,
        chronic,
        lambda t: us.get(t),
        # the caller's lottery filter: flips are out of `failed` and, being its exact
        # complement, land in `passed_task_ids` — the shape this test pins down.
        passed_task_ids=flips + passers,
        flip_task_ids=flips,
        passed_now_task_ids=passers,
    )

    assert s["discrimination"]["tasks"] == 3          # 1 chronic + 2 flips
    read = s["lift"]["tool:Read"]
    assert read["fail_rate"] == 1.0                   # 3/3, not 1/1
    assert read["pass_rate"] == 0.0                   # 0/5, not 2/7
    assert read["lift"] is None                       # never passes → top of the table
    assert "tool:Read" in s["shared_nodes"]           # 3 tasks ≥ threshold → gets a row

    facts = (run / "R1" / "graph_evidence" / "facts.md").read_text(encoding="utf-8")
    assert "**3 failed / 5 passed**" in facts
    assert "`tool:Read`" in facts
    # at risk is a count of tasks that PASS today; none of the five do so via Read.
    row = [ln for ln in facts.splitlines() if ln.startswith("| `tool:Read`")][0]
    assert row.rstrip().endswith("**0** |")


def test_same_task_cross_round_diff_written_and_pointed_at(tmp_path: Path):
    run = tmp_path / "run"

    # R1: alpha PASSES (control side) using WebSearch; omega fails.
    r1 = {"alpha": _mk_u("a1", "tool:WebSearch"), "omega": _mk_u("o1", "tool:Bash")}
    s1 = materialize_graph_evidence(run, 1, ["omega"], lambda t: r1.get(t), passed_task_ids=["alpha"])
    sigs = Path(s1["cone_sigs_path"])
    assert sigs.exists()
    assert s1["regression_diffs_path"] is None  # no prior round → no diffs
    assert "alpha" in sigs.read_text(encoding="utf-8")  # control side persisted

    # R2: alpha now FAILS, using Bash instead; omega fails both rounds (not a flip).
    r2 = {"alpha": _mk_u("a2", "tool:Bash"), "omega": _mk_u("o2", "tool:Bash")}
    s2 = materialize_graph_evidence(run, 2, ["alpha", "omega"], lambda t: r2.get(t))

    assert s2["regression_diff_tasks"] == ["alpha"]
    text = Path(s2["regression_diffs_path"]).read_text(encoding="utf-8")
    assert "## alpha" in text and "## omega" not in text
    alpha_block = text.split("## alpha")[1]
    assert "`tool:Bash`" in alpha_block  # gained in the failing cone
    assert "`tool:WebSearch`" in alpha_block  # lost from the passing cone

    # Pointers: the flipped task's Digester gets the diffs file; the non-flipped
    # task does not; the Planner always gets it once it exists.
    assert any(p.endswith("regression_diffs.md") for p in digester_evidence_paths(run, 2, "alpha"))
    assert not any(p.endswith("regression_diffs.md") for p in digester_evidence_paths(run, 2, "omega"))
    assert any(p.endswith("regression_diffs.md") for p in planner_evidence_paths(run, 2))


def test_identical_cones_flip_is_named_not_faked(tmp_path: Path):
    """A flip whose two cones share every static node must say so plainly —
    an empty gained/lost pair is a finding, not a rendering accident."""
    run = tmp_path / "run"
    materialize_graph_evidence(
        run, 1, ["omega"], lambda t: _mk_u("x", "tool:Bash"), passed_task_ids=["alpha"]
    )
    s2 = materialize_graph_evidence(run, 2, ["alpha"], lambda t: _mk_u("y", "tool:Bash"))
    text = Path(s2["regression_diffs_path"]).read_text(encoding="utf-8")
    assert "SAME static nodes" in text


def test_no_history_no_diff_file(tmp_path: Path):
    run = tmp_path / "run"
    s = materialize_graph_evidence(run, 1, ["omega"], lambda t: _mk_u("x", "tool:Bash"))
    assert s["regression_diffs_path"] is None
    assert not (run / "R1" / "graph_evidence" / "regression_diffs.md").exists()


def test_flip_tasks_get_cones_and_diffs_and_count_as_failures(tmp_path: Path):
    """The launcher's lottery filter excludes ever-passed tasks from failed_task_ids —
    which is every P→F flip, so without a separate channel regression_diffs.md is
    structurally empty (found live in M23 R2-R4: three rounds, zero diff files).
    flip_task_ids is that channel: cones + sigs + diffs.

    M25: they also count on the FAILING side of the statistics. They used to be
    excluded from them, but `passed_task_ids` is the exact complement of
    `failed_task_ids`, so excluding them did not drop them — it moved them into the
    lift control, where this round's failures were counted as passes."""
    run = tmp_path / "run"
    # R1: alpha genuinely passes (control + passed_now); omega fails.
    materialize_graph_evidence(
        run, 1, ["omega"], lambda t: {"alpha": _mk_u("a1", "tool:WebSearch"),
                                      "omega": _mk_u("o1", "tool:Bash")}.get(t),
        passed_task_ids=["alpha"], passed_now_task_ids=["alpha"],
    )
    # R2: alpha fails now but is lineage-solved → caller keeps it OUT of failed and
    # IN the control, and hands it over as a flip.
    s2 = materialize_graph_evidence(
        run, 2, ["omega"], lambda t: {"alpha": _mk_u("a2", "tool:Bash"),
                                      "omega": _mk_u("o2", "tool:Bash")}.get(t),
        passed_task_ids=["alpha"], flip_task_ids=["alpha"], passed_now_task_ids=[],
    )
    assert "alpha" in s2["flip_cones_written"]
    assert (run / "R2" / "graph_evidence" / "cones" / "alpha.md").exists()
    assert s2["regression_diff_tasks"] == ["alpha"]
    text = Path(s2["regression_diffs_path"]).read_text(encoding="utf-8")
    assert "`tool:Bash`" in text.split("## alpha")[1]
    # the flip failed this rollout, so it is one of the round's two failing tasks —
    # and it is NOT on the passing side, where it would have inflated every node's
    # pass rate and deflated the lift of whatever it failed on.
    assert s2["discrimination"]["tasks"] == 2
    facts = (run / "R2" / "graph_evidence" / "facts.md").read_text(encoding="utf-8")
    assert "**2 failed / 0 passed**" in facts
    assert "1 of the failing tasks have never passed" in facts
    # honest passing side: alpha failed THIS rollout, so R2's sigs must not
    # record its (failing) cone as a passing baseline for R3.
    import json as _json
    sigs = _json.loads(Path(s2["cone_sigs_path"]).read_text(encoding="utf-8"))
    assert "alpha" not in sigs["passing"]
    assert "alpha" in sigs["failing"]
