import asyncio
import json
from pathlib import Path
from unittest.mock import patch
import pytest


@pytest.mark.asyncio
async def test_stage_p_end_to_end(tmp_path):
    raw_dir = tmp_path / "sessions"
    raw_dir.mkdir()
    (raw_dir / "task_01_r1.jsonl.raw").write_text(
        '{"type":"message","content":"hi"}\n'
        '{"type":"tool_result","tool":"Bash","output":"ok"}\n'
    )

    pass_flags = {"task_01": [False]}

    async def fake_run_digester(inputs, harness):
        inputs.digest_out_path.parent.mkdir(parents=True, exist_ok=True)
        inputs.digest_out_path.write_text(
            "pattern: FAIL\n"
            "failure_mode: tool_error\n"
            "observation [trajectories/task_01_r1.jsonl.raw#msg_0]\n"
        )

    from harnessx.aegis.stages.preprocess import run_stage_p
    with patch("harnessx.aegis.stages.preprocess._run_digester", new=fake_run_digester):
        result = await run_stage_p(
            raw_dir=raw_dir,
            trajectories_dir=tmp_path / "trajectories",
            digests_dir=tmp_path / "digests",
            summary_path=tmp_path / "summary.md",
            pass_flags_by_task=pass_flags,
            harness_factory=None,
            concurrency=2,
        )
    assert (tmp_path / "summary.md").exists()
    assert (tmp_path / "digests" / "task_01.md").exists()
    summary = (tmp_path / "summary.md").read_text()
    # The per-task index should list the tool_error failure_mode tag.
    assert "tool_error" in summary


class _Result:
    """The two fields the other three meta stages read off a HarnessResult."""

    def __init__(self, cost: float, tokens: int):
        self.total_cost_usd = cost
        self.total_tokens = tokens


def _one_raw(tmp_path: Path, *task_ids: str):
    raw = tmp_path / "sessions"
    raw.mkdir(exist_ok=True)
    for t in task_ids:
        (raw / f"{t}_r0.jsonl.raw").write_text('{"type":"message","content":"hi"}\n')
    return raw


def _writes_digest(result):
    async def fake(inputs, harness):
        inputs.digest_out_path.parent.mkdir(parents=True, exist_ok=True)
        inputs.digest_out_path.write_text("pattern: FAIL\nfailure_mode: x\n")
        return result

    return fake


@pytest.mark.asyncio
async def test_stage_p_reports_what_it_spent(tmp_path):
    """Stage P's spend used to appear on no ledger at all.

    _run_digester was typed ``-> None`` and dropped the HarnessResult, so a round
    could report eval, Planner, Evolver and Critic in dollars and this stage as
    nothing — on a 103-task round that is roughly forty percent of the meta spend
    off-book, and the aggregate was reconstructible only by guessing from a blended
    token price.
    """
    from harnessx.aegis.stages.preprocess import run_stage_p

    raw = _one_raw(tmp_path, "t1", "t2", "t3")
    with patch(
        "harnessx.aegis.stages.preprocess._run_digester",
        new=_writes_digest(_Result(1.25, 1000)),
    ):
        result = await run_stage_p(
            raw_dir=raw,
            trajectories_dir=tmp_path / "traj",
            digests_dir=tmp_path / "digests",
            summary_path=tmp_path / "summary.md",
            pass_flags_by_task={t: [False] for t in ("t1", "t2", "t3")},
        )

    assert result["cost_usd"] == pytest.approx(3.75)  # 3 digesters x $1.25
    assert result["total_tokens"] == 3000


@pytest.mark.asyncio
async def test_stage_p_accounting_tolerates_a_digester_that_returns_nothing(tmp_path):
    """The no-harness path and every monkey-patching test return None.

    Accounting must not turn that into a crash — a cost line is not worth breaking
    the stage over.
    """
    from harnessx.aegis.stages.preprocess import run_stage_p

    raw = _one_raw(tmp_path, "t1")
    with patch(
        "harnessx.aegis.stages.preprocess._run_digester", new=_writes_digest(None)
    ):
        result = await run_stage_p(
            raw_dir=raw,
            trajectories_dir=tmp_path / "traj",
            digests_dir=tmp_path / "digests",
            summary_path=tmp_path / "summary.md",
            pass_flags_by_task={"t1": [False]},
        )

    assert result["cost_usd"] == 0.0
    assert result["total_tokens"] == 0
    assert result["missing_digest_count"] == 0  # the digest was still written
