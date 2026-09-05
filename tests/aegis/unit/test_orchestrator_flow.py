import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from harnessx.aegis.orchestrator import AegisOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_happy_path(tmp_path):
    orch = AegisOrchestrator(
        run_dir=tmp_path,
        num_evolvers=2,
        model_config=MagicMock(),
    )

    # A real shipping round always has these on disk: the Evolver's manifest
    # (which carries `bucket`) and the applied config compose overlays. Without
    # them the cid is dropped before compose, which P-17 now refuses to do
    # quietly — see L2_103x10 R1, where exactly that lost a campaign's first ship.
    (tmp_path / "C-R1-01.md").write_text(  # the path stage_2 below returns
        "---\nbucket: processor\n---\n\nmock candidate\n", encoding="utf-8"
    )
    (tmp_path / "R1" / "applied" / "C-R1-01").mkdir(parents=True, exist_ok=True)
    (tmp_path / "R1" / "applied" / "C-R1-01" / "config.yaml").write_text(
        "processors:\n  - _target_: X.NewProcessor\n", encoding="utf-8"
    )
    (tmp_path / "config.yaml").write_text("processors: []\n", encoding="utf-8")

    with patch("harnessx.aegis.orchestrator.run_stage_p", new=AsyncMock(
        return_value={"task_count": 2, "cluster_count": 1,
                      "actionability": 1.0, "actionability_reason": "mock"})), \
         patch("harnessx.aegis.orchestrator.run_stage_1", new=AsyncMock(
        return_value={"landscape_written": True,
                      "landscape_path": str(tmp_path / "R1" / "landscape.md"),
                      "frontmatter": {"round": 1, "top_themes": ["x"]}})), \
         patch("harnessx.aegis.orchestrator.run_stage_2", new=AsyncMock(
        return_value={"ok_count": 1,
                      "candidate_paths": [tmp_path / "C-R1-01.md"],
                      "results": [("C-R1-01", True, "")]})), \
         patch("harnessx.aegis.orchestrator.run_stage_3", new=AsyncMock(
        return_value={"decision": {"decision_type": "ship",
                                    "ship_ranking": [{"candidate_id": "C-R1-01"}]},
                      "decision_body": "ok", "critic_failed": False})), \
         patch("harnessx.aegis.orchestrator.run_stage_4", new=AsyncMock(
        return_value={"shipped_cid": "C-R1-01", "gate_results": {}, "reason": None})):

        result = await orch.run_round(
            round_n=1,
            raw_sessions_dir=tmp_path / "sessions",
            pass_flags_by_task={"t1": [False, False], "t2": [True, True]},
            current_config_path=tmp_path / "config.yaml",
        )
    assert result["shipped_cid"] == "C-R1-01"
    audit_path = tmp_path / "audit.jsonl"
    assert audit_path.exists()
    assert audit_path.stat().st_size > 0


def test_evolver_step_ceiling_defaults_to_the_official_200():
    """Unset reproduces the official build. This is the P-6 shape: a knob whose
    default is byte-identical semantics, so the vendored behaviour is unchanged
    unless a caller deliberately opts out of it."""
    import inspect as _inspect

    from harnessx.aegis.orchestrator import AegisOrchestrator
    from harnessx.aegis.stages.propose import run_stage_2

    assert AegisOrchestrator.__dataclass_fields__["evolve_max_steps"].default == 200
    assert _inspect.signature(run_stage_2).parameters["max_steps"].default == 200


@pytest.mark.asyncio
async def test_the_evolver_is_told_the_same_ceiling_it_is_held_to(tmp_path):
    """The limit appears twice — in the task prompt and in BaseTask.max_steps.

    They used to be two literal 200s. Tuning one without the other would tell the
    agent a number it is not actually held to, which is the exact failure P-2 was
    written to remove: an agent that cannot see where the wall is.
    """
    from unittest.mock import patch

    from harnessx.aegis.stages.propose import run_stage_2

    seen = {}

    class _Harness:
        async def run(self, task):
            seen["prompt"] = task.description
            seen["max_steps"] = task.max_steps
            raise RuntimeError("stop after capture")

    class _MC:
        def agentic(self, cfg):
            return _Harness()

    (tmp_path / "landscape.md").write_text("x", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("{}", encoding="utf-8")
    with patch("harnessx.aegis.stages.propose.build_evolver_harness", return_value=object()):
        try:
            await run_stage_2(
                round_n=1,
                landscape_path=tmp_path / "landscape.md",
                current_config_path=tmp_path / "config.yaml",
                candidates_dir=tmp_path / "cand",
                trajectories_dir=tmp_path / "traj",
                digests_dir=tmp_path / "dig",
                model_config=_MC(),
                max_steps=317,
            )
        except Exception:
            pass

    assert seen["max_steps"] == 317
    assert "317 tool steps" in seen["prompt"]
    assert "200 tool steps" not in seen["prompt"]


def test_every_meta_stage_takes_the_same_step_ceiling():
    """Planner, Evolver, Critic and the Critic's ask-more runner move together.

    Raising one alone starves whichever comes after it. The Critic is the concrete
    risk: it spent 153 of 200 steps judging four candidates, and a roomier Evolver
    produces more of them — a round that dies at judgment holding candidates is worse
    than one that never produced any.

    All four default to 200, so leaving the knob alone reproduces the official build.
    """
    import inspect as _inspect

    from harnessx.aegis.stages.judge import make_evolver_runner, run_stage_3
    from harnessx.aegis.stages.plan import run_stage_1
    from harnessx.aegis.stages.propose import run_stage_2

    for fn in (run_stage_1, run_stage_2, run_stage_3, make_evolver_runner):
        p = _inspect.signature(fn).parameters.get("max_steps")
        assert p is not None, f"{fn.__name__} does not take max_steps"
        assert p.default == 200, f"{fn.__name__} default is {p.default}, not the official 200"


@pytest.mark.asyncio
async def test_a_compose_refusal_reaches_rejected_candidates_jsonl(tmp_path):
    """P-19 end to end: the row has to land in the file, not just be returned.

    The refusal names the correct bucket, and that sentence used to reach only a
    log file — which is why the Evolver filed StepCountdownProcessor under
    `config` in M14_L0_arm R3 and in every round of M15's smoke, was refused each
    time, and burned a candidate slot each time.
    """
    import json as _json

    from harnessx.aegis.orchestrator import AegisOrchestrator

    orch = AegisOrchestrator(run_dir=tmp_path, num_evolvers=2, model_config=MagicMock())
    proc = "harnessx.processors.control.step_countdown.StepCountdownProcessor"

    for cid, bucket, target in (
        ("C-R1-01", "config", proc),      # the recurring mistake
        ("C-R1-02", "processor", "X.Fine"),
    ):
        (tmp_path / f"{cid}.md").write_text(
            f"---\nbucket: {bucket}\n---\n\nmock\n", encoding="utf-8"
        )
        d = tmp_path / "R1" / "applied" / cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "config.yaml").write_text(f"processors:\n  - _target_: {target}\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("processors: []\n", encoding="utf-8")

    with patch("harnessx.aegis.orchestrator.run_stage_p", new=AsyncMock(
        return_value={"task_count": 2, "cluster_count": 1,
                      "actionability": 1.0, "actionability_reason": "mock"})), \
         patch("harnessx.aegis.orchestrator.run_stage_1", new=AsyncMock(
        return_value={"landscape_written": True,
                      "landscape_path": str(tmp_path / "R1" / "landscape.md"),
                      "frontmatter": {"round": 1, "top_themes": ["x"]}})), \
         patch("harnessx.aegis.orchestrator.run_stage_2", new=AsyncMock(
        return_value={"ok_count": 2,
                      "candidate_paths": [tmp_path / "C-R1-01.md", tmp_path / "C-R1-02.md"],
                      "results": [("C-R1-01", True, ""), ("C-R1-02", True, "")]})), \
         patch("harnessx.aegis.orchestrator.run_stage_3", new=AsyncMock(
        return_value={"decision": {"decision_type": "ship",
                                    "ship_ranking": [{"candidate_id": "C-R1-01"},
                                                     {"candidate_id": "C-R1-02"}]},
                      "decision_body": "ok", "critic_failed": False})), \
         patch("harnessx.aegis.orchestrator.run_stage_4", new=AsyncMock(
        return_value={"shipped_cid": "C-R1-01", "shipped_cids": ["C-R1-01", "C-R1-02"],
                      "gate_results": {}, "reason": None})):

        result = await orch.run_round(
            round_n=1,
            raw_sessions_dir=tmp_path / "sessions",
            pass_flags_by_task={"t1": [False, False]},
            current_config_path=tmp_path / "config.yaml",
        )

    assert result["shipped_cids"] == ["C-R1-02"], "only the composable one ships"

    rows = [
        _json.loads(line)
        for line in (tmp_path / "data" / "rejected_candidates.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    refusal = [r for r in rows if r.get("candidate_id") == "C-R1-01"]
    assert refusal, "the refused candidate must be written down for the Critic"
    assert len(refusal) == 1, (
        "a compose-refused candidate is also a non-shipped sibling, so writing it "
        "twice — once blank — is how the useful half gets buried"
    )
    excerpt = refusal[0]["rejection_text_excerpt"]
    assert "compose refused this candidate" in excerpt
    assert "belongs in the processor bucket" in excerpt, (
        "the actionable half — which bucket it should have used — is the point"
    )

    # And it must not be recorded as a ship anywhere.
    outcomes = _json.loads((tmp_path / "data" / "ship_outcomes.json").read_text(encoding="utf-8"))
    assert [o["ship_id"] for o in outcomes] == ["C-R1-02"]


@pytest.mark.asyncio
async def test_a_zero_candidate_round_says_so_instead_of_blaming_the_critic(tmp_path):
    """P-22. ok_count was never read, so an empty candidate list still went to
    Stage 3: the Critic spent its budget judging nothing and the round landed in
    the critic_failed branch with narrative="Critic failed".

    narrative is read directly by the next Planner, and the two diagnoses call
    for opposite remedies — more Critic budget versus a narrower Evolver brief.
    L2_103x10 R5 and R9 both went this way.
    """
    from harnessx.aegis.data.journal import Journal
    from harnessx.aegis.orchestrator import AegisOrchestrator

    orch = AegisOrchestrator(run_dir=tmp_path, num_evolvers=2, model_config=MagicMock())
    critic = AsyncMock(return_value={"decision": {}, "decision_body": "", "critic_failed": True})

    with patch("harnessx.aegis.orchestrator.run_stage_p", new=AsyncMock(
        return_value={"task_count": 2, "cluster_count": 1,
                      "actionability": 1.0, "actionability_reason": "mock"})), \
         patch("harnessx.aegis.orchestrator.run_stage_1", new=AsyncMock(
        return_value={"landscape_written": True,
                      "landscape_path": str(tmp_path / "R1" / "landscape.md"),
                      "frontmatter": {"round": 1, "top_themes": ["x"]}})), \
         patch("harnessx.aegis.orchestrator.run_stage_2", new=AsyncMock(
        return_value={"ok_count": 0, "candidate_paths": [],
                      "results": [("C-R1-01", False, "apply_validation_failed: boom")]})), \
         patch("harnessx.aegis.orchestrator.run_stage_3", new=critic):

        result = await orch.run_round(
            round_n=1,
            raw_sessions_dir=tmp_path / "sessions",
            pass_flags_by_task={"t1": [False]},
            current_config_path=tmp_path / "config.yaml",
        )

    assert result["reason"] == "no_candidates"
    critic.assert_not_awaited(), "no point spending the Critic's budget on nothing"

    entry = Journal(tmp_path / "journal.md").read_all()[-1]
    assert entry.action == "no_op"
    assert "Evolver produced zero candidates" in entry.narrative
    assert "Critic failed" not in entry.narrative
    assert "apply_validation_failed: boom" in entry.narrative, (
        "Stage 2 already knows why each candidate died — carry it forward"
    )
