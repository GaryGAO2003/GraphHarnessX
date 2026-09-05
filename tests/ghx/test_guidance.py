# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""G1c (M23) — evidence into the prescription-writing roles.

M22's measured gap: landscapes engaged the graph evidence 16/16, digests ~30%,
candidates 0/31 — the Evolver and Critic were never told the evidence exists
(G1b rebinds only Digester+Planner). These tests pin the four pieces that close
it: the evolver pointer + cone-first protocol, the critic pointer, the evolver
session's own step-countdown, and gate-refusal routing (P-19 extended to the
gate layer, where L1's revived C-R8-02 died on a wall its ancestor was never
told about).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from harnessx.aegis.agents.critic import CriticInputs
from harnessx.aegis.agents.evolver import EvolverInputs
from harnessx.aegis.agents.planner import PlannerInputs
from harnessx.ghx.guidance import PLANNER_SENSES_FLAG, install_guidance, write_gate_refusals


def _prompt_text(cfg) -> str:
    for p in cfg.processors:
        if isinstance(p, dict) and "SystemPromptProcessor" in p.get("_target_", ""):
            return p["system_builder"]["text"]
    raise AssertionError("no SystemPromptProcessor entry found in config")


def _countdown_entries(cfg) -> list:
    return [
        p for p in cfg.processors
        if isinstance(p, dict) and "StepCountdownProcessor" in str(p.get("_target_", ""))
    ]


def _evolver_inputs(tmp_path: Path, **overrides) -> EvolverInputs:
    defaults = dict(
        round=5,
        current_config_path=tmp_path / "parent.yaml",
        landscape_path=tmp_path / "landscape.md",
        digests_dir=tmp_path / "digests",
        trajectories_dir=tmp_path / "trajectories",
        candidates_dir=tmp_path / "candidates",
        applied_root=tmp_path / "applied",
    )
    defaults.update(overrides)
    return EvolverInputs(**defaults)


def _critic_inputs(tmp_path: Path) -> CriticInputs:
    return CriticInputs(
        round=5,
        candidates_dir=tmp_path / "R5" / "candidates",
        verdicts_dir=tmp_path / "R5" / "verdicts",
        decision_path=tmp_path / "R5" / "decision.md",
        digests_dir=tmp_path / "R5" / "digests",
        trajectories_dir=tmp_path / "R5" / "trajectories",
        sessions_dir=tmp_path / "R5" / "sessions",
        journal_path=tmp_path / "journal.md",
        current_config_path=tmp_path / "R5" / "config.yaml",
    )


def _planner_inputs(tmp_path: Path, round_n: int = 5) -> PlannerInputs:
    return PlannerInputs(
        round=round_n,
        overview_path=tmp_path / f"R{round_n}" / "overview.md",
        journal_path=tmp_path / "journal.md",
        archive_dir=tmp_path / "archive",
        current_config_path=tmp_path / f"R{round_n}" / "config.yaml",
        landscape_path=tmp_path / f"R{round_n}" / "landscape.md",
        digests_dir=tmp_path / f"R{round_n}" / "digests",
        reputation_summary={},
    )


def _seed_variance_evidence(run: Path, round_n: int) -> None:
    ev = run / f"R{round_n}" / "graph_evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "variance_profile.md").write_text("# variance profile", encoding="utf-8")
    (ev / "flip_ledger.md").write_text("# flip ledger", encoding="utf-8")


def _seed_evidence(run: Path, round_n: int, *, prior_refusals: bool = False) -> None:
    ev = run / f"R{round_n}" / "graph_evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "facts.md").write_text("# facts", encoding="utf-8")
    if prior_refusals:
        prev = run / f"R{round_n - 1}" / "graph_evidence"
        prev.mkdir(parents=True, exist_ok=True)
        (prev / "gate_refusals.md").write_text("# refusals", encoding="utf-8")


# ── evolver: pointer + protocol + countdown ───────────────────────────────────


def test_evolver_gets_pointer_protocol_and_countdown(tmp_path: Path):
    run = tmp_path / "run"
    _seed_evidence(run, 5, prior_refusals=True)

    import harnessx.aegis.stages.propose as propose_mod

    with install_guidance(run, 5):
        cfg = propose_mod.build_evolver_harness(_evolver_inputs(tmp_path))

    text = _prompt_text(cfg)
    assert "## Graph evidence (GHX) — read before proposing" in text
    # M26 slim: the Evolver is pointed at ONE stitched map; facts.md is inside it
    map_path = run / "R5" / "graph_evidence" / "map.md"
    assert str(map_path.resolve()) in text
    assert "stitched from facts.md" in map_path.read_text(encoding="utf-8")
    assert "Cone-first protocol" in text
    assert "Prediction discipline" in text
    # prior round's gate refusals are pointed at, with the read-first instruction
    assert str((run / "R4" / "graph_evidence" / "gate_refusals.md").resolve()) in text
    assert "repeats a listed death" in text
    # the meta session gets its own step-countdown, exactly once
    assert len(_countdown_entries(cfg)) == 1


def test_evolver_countdown_is_idempotent_and_ask_more_untouched(tmp_path: Path):
    run = tmp_path / "run"
    _seed_evidence(run, 5)

    import harnessx.aegis.agents.evolver as evolver_mod

    baseline = _prompt_text(evolver_mod.build_evolver_harness(
        _evolver_inputs(tmp_path, ask_more_brief_path=tmp_path / "brief.md")
    ))

    with install_guidance(run, 5):
        # ask-more: byte-identical prompt, no countdown
        ask_cfg = evolver_mod.build_evolver_harness(
            _evolver_inputs(tmp_path, ask_more_brief_path=tmp_path / "brief.md")
        )
        assert _prompt_text(ask_cfg) == baseline
        assert _countdown_entries(ask_cfg) == []

        # nested install (double guidance) must not double the countdown
        with install_guidance(run, 5):
            cfg = evolver_mod.build_evolver_harness(_evolver_inputs(tmp_path))
            assert len(_countdown_entries(cfg)) == 1


def test_no_evidence_on_disk_still_adds_countdown_only(tmp_path: Path):
    run = tmp_path / "run"  # nothing materialised

    import harnessx.aegis.stages.propose as propose_mod

    orig_text = _prompt_text(propose_mod.build_evolver_harness(_evolver_inputs(tmp_path)))
    with install_guidance(run, 5):
        cfg = propose_mod.build_evolver_harness(_evolver_inputs(tmp_path))
    assert "Graph evidence (GHX)" not in _prompt_text(cfg)  # never point at nothing
    assert _prompt_text(cfg) == orig_text
    assert len(_countdown_entries(cfg)) == 1


# ── critic: verification aids ─────────────────────────────────────────────────


def test_critic_gets_verification_aids(tmp_path: Path):
    run = tmp_path
    _seed_evidence(run, 5)

    import harnessx.aegis.stages.judge as judge_mod

    async def _runner(cid: str, q: str) -> str:
        return "answer"

    with install_guidance(run, 5):
        cfg = judge_mod.build_critic_harness(_critic_inputs(tmp_path), _runner)

    text = _prompt_text(cfg)
    assert "## Graph evidence (GHX) — verification aids" in text
    assert str((run / "R5" / "graph_evidence" / "facts.md").resolve()) in text
    assert "halo claim" in text


# ── restore discipline ────────────────────────────────────────────────────────


def test_install_restores_all_four_bindings(tmp_path: Path):
    import harnessx.aegis.agents.evolver as evolver_mod
    import harnessx.aegis.orchestrator as orch_mod
    import harnessx.aegis.stages.judge as judge_mod
    import harnessx.aegis.stages.propose as propose_mod

    before = (
        propose_mod.build_evolver_harness,
        evolver_mod.build_evolver_harness,
        judge_mod.build_critic_harness,
        orch_mod.run_stage_4,
    )
    with pytest.raises(RuntimeError):
        with install_guidance(tmp_path, 5):
            raise RuntimeError("boom")
    after = (
        propose_mod.build_evolver_harness,
        evolver_mod.build_evolver_harness,
        judge_mod.build_critic_harness,
        orch_mod.run_stage_4,
    )
    assert all(a is b for a, b in zip(before, after))


# ── gate-refusal routing ──────────────────────────────────────────────────────


class _Verdict:
    def __init__(self, ok: bool, reason: str = "") -> None:
        self.ok = ok
        self.reason = reason


def test_write_gate_refusals_names_the_wall_not_its_shadow(tmp_path: Path):
    stage_4 = {
        "gate_results": {
            "C-R5-01": {
                "structure": _Verdict(False, "candidate manifest body has zero evidence anchors (IV-3)"),
                "novelty": _Verdict(True),
                "canonicalize": _Verdict(False, "skipped: earlier gate failed"),
            },
            "C-R5-02": {"structure": {"ok": True, "reason": ""}},
        }
    }
    path = write_gate_refusals(tmp_path, 5, stage_4)
    assert path is not None
    text = Path(path).read_text(encoding="utf-8")
    assert "## C-R5-01" in text
    assert "zero evidence anchors (IV-3)" in text
    assert "skipped: earlier gate failed" not in text  # the shadow is folded away
    assert "C-R5-02" not in text  # all-ok candidate not listed


def test_write_gate_refusals_absent_when_nothing_refused(tmp_path: Path):
    assert write_gate_refusals(tmp_path, 5, {"gate_results": {"C-R5-01": {"structure": _Verdict(True)}}}) is None
    assert not (tmp_path / "R5" / "graph_evidence" / "gate_refusals.md").exists()


def test_stage4_wrap_routes_refusals(tmp_path: Path):
    import harnessx.aegis.orchestrator as orch_mod

    true_original = orch_mod.run_stage_4

    async def _stub(**kwargs):
        return {"gate_results": {"C-R7-02": {"replay": _Verdict(False, "replay smoke returned falsy")}}}

    orch_mod.run_stage_4 = _stub
    try:
        async def _go():
            with install_guidance(tmp_path, 7):
                return await orch_mod.run_stage_4(round_n=7)

        result = asyncio.get_event_loop_policy().new_event_loop().run_until_complete(_go())
        assert "gate_results" in result  # result passes through unchanged
        text = (tmp_path / "R7" / "graph_evidence" / "gate_refusals.md").read_text(encoding="utf-8")
        assert "replay smoke returned falsy" in text
        assert orch_mod.run_stage_4 is _stub  # restored to what was bound at install
    finally:
        orch_mod.run_stage_4 = true_original


# ── planner fate-bucket priors (M27 T2.2) ──────────────────────────────────────


def test_planner_flag_off_by_default_no_rebind_no_prompt_change(tmp_path, monkeypatch):
    run = tmp_path / "run"
    _seed_variance_evidence(run, 5)
    monkeypatch.delenv(PLANNER_SENSES_FLAG, raising=False)

    import harnessx.aegis.stages.plan as plan_mod

    original = plan_mod.build_planner_harness
    baseline = _prompt_text(original(_planner_inputs(tmp_path)))
    with install_guidance(run, 5):
        assert plan_mod.build_planner_harness is original  # not rebound at all
        cfg = plan_mod.build_planner_harness(_planner_inputs(tmp_path))
    assert _prompt_text(cfg) == baseline
    assert plan_mod.build_planner_harness is original


def test_planner_gets_fate_bucket_priors_when_flag_on(tmp_path, monkeypatch):
    run = tmp_path / "run"
    _seed_variance_evidence(run, 5)
    monkeypatch.setenv(PLANNER_SENSES_FLAG, "1")

    import harnessx.aegis.stages.plan as plan_mod

    with install_guidance(run, 5):
        cfg = plan_mod.build_planner_harness(_planner_inputs(tmp_path))

    text = _prompt_text(cfg)
    assert "## Fate-bucket priors (GHX, M27)" in text
    assert str((run / "R5" / "graph_evidence" / "variance_profile.md").resolve()) in text
    assert str((run / "R5" / "graph_evidence" / "flip_ledger.md").resolve()) in text
    assert "NEVER-so-far tasks convert passively 16.9%-24.4%" in text
    assert "50.0%" in text and "51.5%" in text  # PROB swinger targeted vs untargeted
    assert "long_then_wrong" in text


def test_planner_no_evidence_on_disk_never_points_at_nothing(tmp_path, monkeypatch):
    run = tmp_path / "run"  # nothing materialised
    monkeypatch.setenv(PLANNER_SENSES_FLAG, "1")

    import harnessx.aegis.stages.plan as plan_mod

    baseline = _prompt_text(plan_mod.build_planner_harness(_planner_inputs(tmp_path)))
    with install_guidance(run, 5):
        cfg = plan_mod.build_planner_harness(_planner_inputs(tmp_path))
    assert "Fate-bucket priors" not in _prompt_text(cfg)
    assert _prompt_text(cfg) == baseline


def test_planner_composes_with_brief_pointers_in_either_nesting_order(tmp_path, monkeypatch):
    """guidance (M27 fate-bucket priors) and brief_pointers (G1b cone/facts
    pointer) both rebind stages.plan.build_planner_harness — the same shape
    proposal_seam/guidance already prove for the Evolver. Real dispatch nests
    guidance outer, brief_pointers inner (round_router.py -> overlay.py); both
    orders must still yield both sections."""
    from harnessx.ghx.brief_pointers import install_brief_pointers

    run = tmp_path / "run"
    _seed_evidence(run, 5)  # facts.md -> brief_pointers' own G1b pointer
    _seed_variance_evidence(run, 5)  # variance_profile.md + flip_ledger.md -> M27 pointer
    monkeypatch.setenv(PLANNER_SENSES_FLAG, "1")

    import harnessx.aegis.stages.plan as plan_mod

    with install_guidance(run, 5):
        with install_brief_pointers(run, 5, []):
            cfg = plan_mod.build_planner_harness(_planner_inputs(tmp_path))
    text = _prompt_text(cfg)
    assert "## Fate-bucket priors (GHX, M27)" in text
    assert "## Graph evidence (GHX)" in text  # brief_pointers' own header

    with install_brief_pointers(run, 5, []):
        with install_guidance(run, 5):
            cfg2 = plan_mod.build_planner_harness(_planner_inputs(tmp_path))
    text2 = _prompt_text(cfg2)
    assert "## Fate-bucket priors (GHX, M27)" in text2
    assert "## Graph evidence (GHX)" in text2


def test_planner_binding_restored_when_flag_on(tmp_path, monkeypatch):
    _seed_variance_evidence(tmp_path / "run", 5)
    monkeypatch.setenv(PLANNER_SENSES_FLAG, "1")

    import harnessx.aegis.stages.plan as plan_mod

    original = plan_mod.build_planner_harness
    with pytest.raises(RuntimeError):
        with install_guidance(tmp_path / "run", 5):
            assert plan_mod.build_planner_harness is not original
            raise RuntimeError("boom")
    assert plan_mod.build_planner_harness is original


# ── critic: fate-bucket base-rate pricing (M27 T2.3) ───────────────────────────


def test_critic_baserate_absent_when_flag_off(tmp_path, monkeypatch):
    run = tmp_path
    _seed_evidence(run, 5)
    _seed_variance_evidence(run, 5)
    monkeypatch.delenv(PLANNER_SENSES_FLAG, raising=False)

    import harnessx.aegis.stages.judge as judge_mod

    async def _runner(cid: str, q: str) -> str:
        return "answer"

    with install_guidance(run, 5):
        cfg = judge_mod.build_critic_harness(_critic_inputs(tmp_path), _runner)
    text = _prompt_text(cfg)
    assert "Fate-bucket base-rate pricing" not in text
    assert str((run / "R5" / "graph_evidence" / "flip_ledger.md").resolve()) not in text


def test_critic_gets_baserate_pricing_when_flag_on(tmp_path, monkeypatch):
    run = tmp_path
    _seed_evidence(run, 5)
    _seed_variance_evidence(run, 5)
    monkeypatch.setenv(PLANNER_SENSES_FLAG, "1")

    import harnessx.aegis.stages.judge as judge_mod

    async def _runner(cid: str, q: str) -> str:
        return "answer"

    with install_guidance(run, 5):
        cfg = judge_mod.build_critic_harness(_critic_inputs(tmp_path), _runner)
    text = _prompt_text(cfg)
    assert "## Fate-bucket base-rate pricing (GHX, M27)" in text
    assert str((run / "R5" / "graph_evidence" / "flip_ledger.md").resolve()) in text
    assert str((run / "R5" / "graph_evidence" / "variance_profile.md").resolve()) in text
    assert "PROB-swinger flip" in text
