# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 P3 — regression triage: three rulers on the official regressions.md.

Fixtures rebuild the L2-R9 shape in miniature: a batch where swingers revert
(streak 1) beside one genuinely stable break (streak 5), a processor suspect
whose node reaches only some cones, and a prompt suspect the cone ruler must
abstain for out loud.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.aegis.data.regressions import write_regressions_md
from harnessx.ghx.regression_triage import (
    compute_triage,
    hard_p2f_envelope,
    install_regression_triage,
    pass_streak,
    triage_markdown,
    write_regressions_md_triaged,
)

T_SWING = "aaaaaaaa-0000-0000-0000-000000000001"
T_STABLE = "bbbbbbbb-0000-0000-0000-000000000002"
T_OUT = "cccccccc-0000-0000-0000-000000000003"


def _mk_history(run: Path, rows) -> None:
    (run / "data").mkdir(parents=True, exist_ok=True)
    with (run / "data" / "task_history.jsonl").open("w", encoding="utf-8") as f:
        for rnd, tid, passed in rows:
            f.write(json.dumps({"round": rnd, "task_id": tid, "passed": passed, "passed_flags": [passed]}) + "\n")


def _mk_ships(run: Path, round_n: int, ships) -> None:
    (run / "data").mkdir(parents=True, exist_ok=True)
    (run / "data" / "ship_outcomes.json").write_text(
        json.dumps([{"ship_id": sid, "round": round_n, "bucket": bucket} for sid, bucket in ships]),
        encoding="utf-8",
    )


def _mk_manifest(run: Path, round_n: int, ship_id: str, signature: dict) -> None:
    d = run / f"R{round_n}" / "candidates"
    d.mkdir(parents=True, exist_ok=True)
    import yaml

    front = yaml.safe_dump({"candidate_id": ship_id, "attribution_signature": signature})
    (d / f"{ship_id}.md").write_text(f"---\n{front}---\n\nbody\n", encoding="utf-8")


def _mk_cones(run: Path, evolve_round: int, failing: dict) -> None:
    d = run / f"R{evolve_round}" / "graph_evidence"
    d.mkdir(parents=True, exist_ok=True)
    (d / "cone_sigs.json").write_text(json.dumps({"round": evolve_round, "failing": failing}), encoding="utf-8")


def _standard_run(tmp_path: Path) -> Path:
    """Rounds 1..8; regression window R7→R8; suspects ship at R8; evolve at R9."""
    run = tmp_path / "arm"
    rows = []
    # T_SWING: fails 1-6, passes 7, fails 8  → streak 1 (swinger reverting)
    for r in range(1, 9):
        rows.append((r, T_SWING, r == 7))
    # T_STABLE: fails 1-2, passes 3-7, fails 8 → streak 5 (stable break)
    for r in range(1, 9):
        rows.append((r, T_STABLE, 3 <= r <= 7))
    # T_OUT: passes 7 only, fails 8 → streak 1, and its cone lacks the node
    for r in range(1, 9):
        rows.append((r, T_OUT, r == 7))
    # a stable passer so no-ship transitions have material
    for r in range(1, 9):
        rows.append((r, "dddddddd-0000-0000-0000-000000000004", True))
    _mk_history(run, rows)
    _mk_ships(run, 8, [("C-R8-01", "processor"), ("C-R8-02", "prompt")])
    _mk_manifest(run, 8, "C-R8-01", {"type": "processor_invocation", "class_name": "BashWindowsGuardProcessor"})
    # cones for the failing tasks at evolve round 9
    from harnessx.ghx.attribution_graph import processor_static_id

    node = processor_static_id("BashWindowsGuardProcessor")
    _mk_cones(
        run,
        9,
        {
            T_SWING: [node + "#empty", "tool:Bash"],  # annotated member → base match
            T_STABLE: [node, "tool:WebSearch"],
            T_OUT: ["tool:WebFetch"],  # node absent → out of cone
        },
    )
    return run


# ── rulers ────────────────────────────────────────────────────────────────────


def test_streak_and_envelope(tmp_path):
    run = _standard_run(tmp_path)
    t = compute_triage(run, 8, 9)
    assert t.observed_hard == 3
    assert t.streaks == {T_SWING: 1, T_STABLE: 5, T_OUT: 1}
    assert t.counterfactual_eligible() == [T_STABLE]
    # 5 no-ship transitions (R2..R7? R8 shipped) with tiny counts → run-sourced envelope
    env = t.envelope
    assert env.source == "run" and env.n >= 3
    assert t.stat_verdict == "EXCESS"  # 3 hard vs ~0-mean run envelope


def test_envelope_falls_back_when_thin(tmp_path):
    run = tmp_path / "thin"
    _mk_history(run, [(1, T_SWING, True), (2, T_SWING, False)])
    _mk_ships(run, 2, [("C-R2-01", "processor")])
    env = hard_p2f_envelope(run, 2)
    assert env.source == "fallback" and env.mean == 9.3


def test_pass_streak_unit():
    by_round = {3: [True], 4: [True], 5: [True], 6: [False], 7: [True]}
    assert pass_streak(by_round, 7) == 1
    assert pass_streak(by_round, 5) == 3
    assert pass_streak(by_round, 6) == 0


def test_cone_ruler_scopes_and_abstains(tmp_path):
    run = _standard_run(tmp_path)
    t = compute_triage(run, 8, 9)
    proc = next(s for s in t.ships if s.ship_id == "C-R8-01")
    prompt = next(s for s in t.ships if s.ship_id == "C-R8-02")
    assert proc.nodes and sorted(proc.in_cone) == sorted([T_SWING, T_STABLE])
    assert proc.out_of_cone == [T_OUT]
    assert prompt.nodes == set()  # cone ruler abstains for prompt


# ── rendering + seam ──────────────────────────────────────────────────────────


def test_triaged_markdown_replaces_mandate(tmp_path):
    run = _standard_run(tmp_path)
    path = write_regressions_md(run, 8, for_evolve_round_n=9)
    official = path.read_text(encoding="utf-8")
    assert "**Required action**: Evolver MUST" in official

    md = triage_markdown(official, run, 8, 9)
    # official sections preserved
    assert "## Per-task detail" in md and f"`{T_STABLE}`" in md
    # old blanket mandate gone, triage-aware one present
    assert "**Required action**: Evolver MUST" not in md
    assert "**Required action (triage-aware)**" in md
    assert "## Graph triage (M24" in md
    assert "EXCESS" in md
    assert "out-of-cone" in md and f"`{T_OUT}`" in md
    assert "cone ruler abstains" in md  # prompt ship
    assert "swinger reverting" in md and "stable task actually broken" in md


def test_within_envelope_mandate_forbids_noise_kill(tmp_path):
    run = _standard_run(tmp_path)
    # inflate the envelope via fallback: rewrite history so run-envelope is thin
    _mk_history(
        run,
        [(r, tid, p) for r, tid, p in [(7, T_SWING, True), (8, T_SWING, False)]],
    )
    md = triage_markdown("**Required action**: Evolver MUST x", run, 8, 9)
    assert "within-envelope" in md
    assert "MUST NOT drive a no_op" in md
    assert "NOT grounds to reject" in md


def test_seam_writes_triaged_file_and_restores(tmp_path):
    run = _standard_run(tmp_path)
    import harnessx.aegis.data.regressions as reg

    original = reg.write_regressions_md
    with install_regression_triage():
        assert reg.write_regressions_md is write_regressions_md_triaged
        path = reg.write_regressions_md(run, 8, for_evolve_round_n=9)
        assert "Graph triage" in Path(path).read_text(encoding="utf-8")
    assert reg.write_regressions_md is original


def test_triage_failure_returns_official(tmp_path):
    # run_root with nothing in it → compute_triage still works (0 regressions)…
    md = triage_markdown("# Regressions\n\n_No regressions detected this round._\n", tmp_path, 3, 4)
    # …and empty files get the rulers appended without a mandate to replace
    assert "Graph triage" in md and "_No regressions detected" in md


def test_cone_ruler_abstains_on_ubiquitous_nodes():
    """A ship on an always-firing node is in EVERY cone; the ruler must abstain
    rather than rubber-stamp in-cone N/N (M25_103x16 R2, step_countdown)."""
    from harnessx.ghx.regression_triage import _nodes_are_ubiquitous

    nodes = {"proc:step_countdown_processor"}
    everywhere = {f"t{i}": ["proc:step_countdown_processor", f"tool:X{i}#empty"] for i in range(6)}
    assert _nodes_are_ubiquitous(nodes, everywhere, {"t0", "t1"}) is True

    # discriminative: silent on a non-regressed task
    mixed = dict(everywhere)
    mixed["t5"] = ["tool:X5"]
    assert _nodes_are_ubiquitous(nodes, mixed, {"t0", "t1"}) is False

    # nothing to sample (every task regressed) → no vacuity claim
    assert _nodes_are_ubiquitous(nodes, {"t0": ["proc:step_countdown_processor"]}, {"t0"}) is False


def test_ubiquitous_ship_renders_abstention():
    from harnessx.ghx.regression_triage import ShipTriage, TriageResult, render_triage_section

    from harnessx.ghx.regression_triage import Envelope

    t = TriageResult(round_n=2, evolve_round_n=3, observed_hard=12,
                     envelope=Envelope(mean=9.3, sd=2.2, n=0, source="fallback"))
    t.cone_data_available = True
    t.ships.append(
        ShipTriage(ship_id="C-R2-02", bucket="processor",
                   nodes={"proc:step_countdown_processor"},
                   in_cone=[f"t{i}" for i in range(12)], ubiquitous=True)
    )
    md = render_triage_section(t)
    assert "ABSTAINS" in md
    assert "Presence everywhere is not reach" in md
