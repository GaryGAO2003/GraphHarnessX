# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 P1 — loop_health's five GHX channels.

Each fixture rebuilds the exact failure the channel exists for: the 6/6
never-answered gate, the outcome stamp blind to structured empties, the
all-joint ledger, thinning U coverage, dead cone links.  And the L0 contract:
a run with no graph anywhere grades ok — the sweeper must never fail an arm
that never promised a graph.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.loop_health import (
    _ghx_active,
    check_ghx_attribution_backend,
    check_ghx_cone_presence,
    check_ghx_gate_answered,
    check_ghx_outcome_fidelity,
    check_ghx_u_coverage,
)

T1 = "aaaaaaaa-1111-2222-3333-444444444444"
T2 = "bbbbbbbb-1111-2222-3333-444444444444"


def _mk_session_u(run: Path, rnd: int, task: str, tool_outcomes) -> None:
    g = run / f"R{rnd}" / "sessions" / "aegis" / f"R{rnd}-{task}" / "graph"
    g.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"kind": "meta", "run_id": "x", "session_id": f"aegis/R{rnd}-{task}"})]
    for i, (tool, outcome) in enumerate(tool_outcomes):
        lines.append(
            json.dumps(
                {
                    "kind": "node",
                    "id": f"tool:{tool}@t{i}",
                    "static_node_id": f"tool:{tool}",
                    "graphed": True,
                    "hook": "tool",
                    "step": i,
                    "ordinal": i,
                    "outcome": outcome,
                }
            )
        )
    (g / "run_unfolded.jsonl").write_text("\n".join(lines), encoding="utf-8")


def _mk_digest(run: Path, rnd: int, task: str, rows) -> None:
    d = run / f"R{rnd}" / "digests"
    d.mkdir(parents=True, exist_ok=True)
    body = ["pattern: ALL_FAIL", "", "## Trace Facts (Layer A — mechanical; do not rewrite)", ""]
    body.append("| step | tool | args_sha | args_preview | return_type | return_len | next_uses_result |")
    body.append("|---|---|---|---|---|---|---|")
    for i, (tool, rtype, rlen) in enumerate(rows):
        body.append(f"| {i} | `{tool}` | 0123abcd | {{}} | {rtype} | {rlen} | — |")
    (d / f"{task}.md").write_text("\n".join(body), encoding="utf-8")


def _bare_round(run: Path, rnd: int) -> None:
    (run / f"R{rnd}").mkdir(parents=True, exist_ok=True)


# ── GHX-off contract ──────────────────────────────────────────────────────────


def test_l0_run_grades_ok_everywhere(tmp_path):
    run = tmp_path / "l0"
    _bare_round(run, 1)
    _mk_digest(run, 1, T1, [("Bash", "empty", 0)] * 12)
    assert not _ghx_active(run)
    for chk in (
        check_ghx_u_coverage,
        check_ghx_cone_presence,
        check_ghx_gate_answered,
        check_ghx_outcome_fidelity,
        check_ghx_attribution_backend,
    ):
        c = chk(run, False)
        assert c.status == "ok" and "GHX off" in c.detail, c


# ── u coverage ────────────────────────────────────────────────────────────────


def test_u_coverage_broken_when_sessions_thin(tmp_path):
    run = tmp_path / "arm"
    _mk_session_u(run, 2, T1, [("Bash", "ok")])
    # a second session dir with NO graph file
    (run / "R2" / "sessions" / "aegis" / f"R2-{T2}").mkdir(parents=True)
    (run / "R2" / "sessions" / "aegis" / f"R2-{T2}" / "x.txt").write_text("", encoding="utf-8")
    assert _ghx_active(run)
    c = check_ghx_u_coverage(run, True)
    assert c.status == "BROKEN" and "1/2" in c.detail


def test_u_coverage_ok_when_full(tmp_path):
    run = tmp_path / "arm"
    _mk_session_u(run, 2, T1, [("Bash", "ok")])
    _mk_session_u(run, 2, T2, [("Bash", "ok")])
    # sidecar session FILES sit beside every session dir; they must not enter
    # the denominator (real-run smoke: 103 dirs + 103 sidecars read as 103/206)
    (run / "R2" / "sessions" / "aegis" / f"R2-{T1}.json").write_text("{}", encoding="utf-8")
    (run / "R2" / "sessions" / "aegis" / f"R2-{T2}.json").write_text("{}", encoding="utf-8")
    c = check_ghx_u_coverage(run, True)
    assert c.status == "ok" and "2/2" in c.detail


# ── cone presence ─────────────────────────────────────────────────────────────


def test_cone_presence_broken_on_dead_links(tmp_path):
    run = tmp_path / "arm"
    ge = run / "R3" / "graph_evidence"
    (ge / "cones").mkdir(parents=True)
    (ge / "cone_sigs.json").write_text(json.dumps({"failing": {T1: ["tool:Bash"], T2: ["tool:WebFetch"]}}), encoding="utf-8")
    (ge / "cones" / f"{T1}.md").write_text("# cone", encoding="utf-8")  # T2's cone missing
    c = check_ghx_cone_presence(run, True)
    assert c.status == "BROKEN" and "2 failing task(s) but cones/ holds 1" in c.detail


# ── gate answered ─────────────────────────────────────────────────────────────


def _mk_gate(run: Path, rnd: int, cid: str, checked: bool) -> None:
    g = run / f"R{rnd}" / "graph_evidence" / "gate"
    g.mkdir(parents=True, exist_ok=True)
    (g / f"{cid}.md").write_text(f"# gate\n\n- ok: True\n- checked: {checked}\n", encoding="utf-8")


def test_gate_never_answered_is_loud(tmp_path):
    run = tmp_path / "arm"
    for i, rnd in enumerate((2, 3, 4)):
        _mk_gate(run, rnd, f"C-R{rnd}-01", False)
    c = check_ghx_gate_answered(run, True)
    assert c.status == "DEGRADED" and "every one checked=False" in c.detail


def test_gate_one_answer_clears(tmp_path):
    run = tmp_path / "arm"
    _mk_gate(run, 2, "C-R2-01", False)
    _mk_gate(run, 3, "C-R3-01", True)
    c = check_ghx_gate_answered(run, True)
    assert c.status == "ok" and "1/2" in c.detail


# ── outcome fidelity ──────────────────────────────────────────────────────────


def test_outcome_drift_is_broken(tmp_path):
    run = tmp_path / "arm"
    # batch 2's U: 12 Bash calls all stamped ok…
    _mk_session_u(run, 2, T1, [("Bash", "ok")] * 12)
    # …while R3's digest (describing batch 2) says all 12 flattened empty.
    _mk_digest(run, 3, T1, [("Bash", "empty", 0)] * 12)
    c = check_ghx_outcome_fidelity(run, True)
    assert c.status == "BROKEN" and "digest-empty=12" in c.detail and "U-outcome-empty=0" in c.detail


def test_outcome_agreement_is_ok(tmp_path):
    run = tmp_path / "arm"
    _mk_session_u(run, 2, T1, [("Bash", "empty")] * 12)
    _mk_digest(run, 3, T1, [("Bash", "empty", 0)] * 12)
    assert check_ghx_outcome_fidelity(run, True).status == "ok"


# ── attribution backend ───────────────────────────────────────────────────────


def _mk_ships(run: Path, grades_per_ship) -> None:
    (run / "data").mkdir(parents=True, exist_ok=True)
    outcomes = [
        {"ship_id": f"C-R{i}-01", "round": i, "evidence_per_task": {f"t{j}": g for j, g in enumerate(gs)}}
        for i, gs in enumerate(grades_per_ship, start=2)
    ]
    (run / "data" / "ship_outcomes.json").write_text(json.dumps(outcomes), encoding="utf-8")


def test_all_joint_ledger_degrades(tmp_path):
    run = tmp_path / "arm"
    _mk_ships(run, [["joint", "joint"], ["joint"]])
    c = check_ghx_attribution_backend(run, True)
    assert c.status == "DEGRADED" and "all joint" in c.detail


def test_direct_or_orphan_clears(tmp_path):
    run = tmp_path / "arm"
    _mk_ships(run, [["joint", "direct"], ["orphan"]])
    assert check_ghx_attribution_backend(run, True).status == "ok"
