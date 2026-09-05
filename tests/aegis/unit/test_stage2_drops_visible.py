# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""P-25 — Stage 2's drops were invisible to the Critic, and one ghost voided a round.

The verified chain from M15_smoke_L0 R1: the Evolver put a bare Windows path in
C-R1-02's frontmatter, the backslashes broke the YAML, Stage 2 dropped it with
``propose_fail "manifest parse failed"`` (recorded in audit.jsonl, read by
nobody), the Critic — handed the raw candidates/ directory — verdicted and
ranked the corpse, and IV-6 no-op'd the whole round, taking the perfectly good
C-R1-01 down with it.

Two halves: (a) a ghost citation is stripped loudly and the round survives on
the real candidates, with the old whole-round no-op kept for a ranking that is
ghosts all the way down; (b) the Critic is told what was dropped and why, so it
stops spending verdict budget on corpses.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from harnessx.aegis.gates.structure import GateResult
from harnessx.aegis.stages.commit import _partition_ranking, run_stage_4
from harnessx.aegis.stages.judge import _dropped_note


# ── the partition itself ─────────────────────────────────────────────────────


def test_partition_separates_survivors_from_ghosts():
    decision = {"ship_ranking": [{"candidate_id": "C-R1-01"}, {"candidate_id": "C-R1-02"}]}
    known, ghosts = _partition_ranking(decision, {"C-R1-01": ({}, "")})
    assert known == [{"candidate_id": "C-R1-01"}]
    assert ghosts == ["C-R1-02"]


def test_partition_with_no_ghosts_changes_nothing():
    decision = {"ship_ranking": [{"candidate_id": "C-R1-01"}]}
    known, ghosts = _partition_ranking(decision, {"C-R1-01": ({}, "")})
    assert (len(known), ghosts) == (1, [])


# ── (a) strip-and-survive at stage 4 ─────────────────────────────────────────


def _mk_candidate(tmp_path: Path, cid: str) -> tuple[Path, Path]:
    manifest = tmp_path / f"{cid}.md"
    manifest.write_text("---\nbucket: tools\n---\n\nbody\n", encoding="utf-8")
    config = tmp_path / cid / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("processors: []\n", encoding="utf-8")
    return manifest, config


@pytest.mark.asyncio
async def test_a_ranking_of_only_ghosts_still_noops_the_round(tmp_path: Path):
    """The old loud failure is the right answer when there is nothing real to
    proceed with — that part of IV-6 does not soften."""
    archived = []
    out = await run_stage_4(
        round_n=1,
        decision={"decision_type": "ship", "ship_ranking": [{"candidate_id": "C-R1-99"}]},
        candidates_info={},
        refuted_signatures=set(),
        commit_fn=None,
        archive_fn=lambda cid, info: archived.append(cid),
    )
    assert out["shipped_cid"] is None
    assert out["reason"].startswith("decision_chain_broken")
    assert "C-R1-99" in out["reason"]


@pytest.mark.asyncio
async def test_one_ghost_no_longer_takes_the_real_candidate_down(tmp_path: Path):
    """M15_smoke_L0 R1's shape, replayed: C-R1-01 is real, C-R1-02 is a ghost.
    Before P-25 the whole round no-op'd; now the ghost is stripped and the real
    one ships."""
    manifest, config = _mk_candidate(tmp_path, "C-R1-01")
    committed = []
    with patch(
        "harnessx.aegis.stages.commit._run_all_gates",
        new=AsyncMock(return_value={"structure": GateResult(ok=True)}),
    ):
        out = await run_stage_4(
            round_n=1,
            decision={
                "decision_type": "ship",
                "ship_ranking": [
                    {"candidate_id": "C-R1-02"},  # the ghost, ranked first
                    {"candidate_id": "C-R1-01"},
                ],
            },
            candidates_info={"C-R1-01": (manifest, config)},
            refuted_signatures=set(),
            commit_fn=lambda cid, cfg: committed.append(cid),
            archive_fn=lambda cid, info: None,
        )
    assert out["shipped_cids"] == ["C-R1-01"], "the round proceeds on the real candidate"
    assert committed == ["C-R1-01"]
    # The strip is loud: the ghost sits in gate_results with a reason, which the
    # orchestrator's P-24a audit path then records without new plumbing.
    ghost = out["gate_results"]["C-R1-02"]["decision_chain"]
    assert ghost.ok is False
    assert "stripped" in ghost.reason and "IV-6" in ghost.reason


@pytest.mark.asyncio
async def test_a_clean_ranking_is_untouched(tmp_path: Path):
    manifest, config = _mk_candidate(tmp_path, "C-R1-01")
    with patch(
        "harnessx.aegis.stages.commit._run_all_gates",
        new=AsyncMock(return_value={"structure": GateResult(ok=True)}),
    ):
        out = await run_stage_4(
            round_n=1,
            decision={"decision_type": "ship", "ship_ranking": [{"candidate_id": "C-R1-01"}]},
            candidates_info={"C-R1-01": (manifest, config)},
            refuted_signatures=set(),
            commit_fn=None,
            archive_fn=lambda cid, info: None,
        )
    assert out["shipped_cids"] == ["C-R1-01"]
    assert "C-R1-02" not in out["gate_results"]


# ── (b) the Critic is told ───────────────────────────────────────────────────


def test_the_note_names_the_corpse_and_the_reason():
    note = _dropped_note([("C-R1-02", "manifest parse failed: while parsing a block mapping")])
    assert "C-R1-02" in note
    assert "manifest parse failed" in note
    assert "Do NOT" in note, "it must forbid, not merely inform"
    assert "ship_ranking" in note, "and say where the citation would be stripped"


def test_no_drops_means_no_note():
    assert _dropped_note(None) == ""
    assert _dropped_note([]) == ""


def test_a_long_reason_is_truncated():
    note = _dropped_note([("C-R1-02", "x" * 500)])
    assert "x" * 200 in note and "x" * 201 not in note


def test_the_critic_task_carries_the_note(tmp_path: Path):
    """Capture the BaseTask the Critic actually receives."""
    import asyncio

    from harnessx.aegis.stages.judge import run_stage_3

    seen = {}

    class _Harness:
        async def run(self, task):
            seen["description"] = task.description
            raise RuntimeError("stop after capture")

    class _MC:
        def agentic(self, cfg):
            return _Harness()

    with patch("harnessx.aegis.stages.judge.build_critic_harness", return_value=object()):
        with pytest.raises(RuntimeError, match="stop after capture"):
            asyncio.run(
                run_stage_3(
                    round_n=1,
                    candidates_dir=tmp_path,
                    verdicts_dir=tmp_path / "verdicts",
                    decision_path=tmp_path / "decision.md",
                    digests_dir=tmp_path,
                    trajectories_dir=tmp_path,
                    sessions_dir=tmp_path,
                    journal_path=tmp_path / "journal.md",
                    current_config_path=tmp_path / "config.yaml",
                    evolver_runner=None,
                    model_config=_MC(),
                    dropped_candidates=[("C-R1-02", "manifest parse failed: boom")],
                )
            )
    assert "C-R1-02" in seen["description"]
    assert "manifest parse failed" in seen["description"]


def test_the_orchestrator_passes_the_drops():
    from harnessx.aegis import orchestrator as _orch

    src = inspect.getsource(_orch.AegisOrchestrator.run_round)
    assert "dropped_candidates=" in src
    assert 'stage_2["results"] if not ok' in src, (
        "the reasons Stage 2 already returns are the payload — nothing new is computed"
    )
