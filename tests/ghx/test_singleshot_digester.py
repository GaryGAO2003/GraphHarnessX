# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Single-shot digester seam — routing, fallback, and install/restore.

Forced cases per path: k=1-small routes single-shot (one completion, digest
written, vendored untouched); k=2 and oversize route vendored; an empty
single-shot reply falls back to vendored; install patches and restores
``preprocess._run_digester``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import harnessx.ghx.singleshot_digester as mod
from harnessx.aegis.agents.digester import DigesterInputs


class _FakeResult:
    def __init__(self, text):
        self.final_output = text
        self.total_cost_usd = 0.01
        self.total_tokens = 123
        self.exit_reason = "done"


class _FakeSingle:
    def __init__(self, text):
        self._text = text
        self.ran = 0

    async def run(self, task):
        self.ran += 1
        return _FakeResult(self._text)


class _FakeModelConfig:
    def __init__(self, text):
        self.single = _FakeSingle(text)

    def agentic(self, cfg):
        return self.single


class _FakeHarness:
    def __init__(self, text="pattern: ALL_FAIL\nfailure_mode: probe\n\n## Diagnosis\nok"):
        self.model_config = _FakeModelConfig(text)


def _traj(tmp_path: Path, name="t1_r0.jsonl", n_records=3, pad=0) -> Path:
    p = tmp_path / "trajectories" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    recs = [{"type": "assistant", "step": i, "message": {"role": "assistant", "content": "x" * (10 + pad)}} for i in range(n_records)]
    p.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    return p


def _inputs(tmp_path: Path, paths) -> DigesterInputs:
    return DigesterInputs(
        task_id="t1",
        pattern="ALL_FAIL",
        trajectory_paths=list(paths),
        digest_out_path=tmp_path / "digests" / "t1.md",
        trace_facts_md="## Trace Facts\n(probe)",
    )


def _arm(monkeypatch, calls):
    async def vendored(inputs, harness):
        calls.append("vendored")
        return _FakeResult("(vendored)")

    monkeypatch.setenv(mod.FLAG, "1")
    monkeypatch.setattr(mod, "_ORIGINAL_RUN", vendored)


@pytest.mark.asyncio
async def test_k1_small_routes_singleshot(tmp_path, monkeypatch):
    calls = []
    _arm(monkeypatch, calls)
    harness = _FakeHarness()
    inputs = _inputs(tmp_path, [_traj(tmp_path)])
    result = await mod.run_digester_singleshot(inputs, harness)
    assert harness.model_config.single.ran == 1
    assert calls == []  # vendored untouched
    assert inputs.digest_out_path.exists()
    assert "failure_mode: probe" in inputs.digest_out_path.read_text(encoding="utf-8")
    assert result.total_tokens == 123


@pytest.mark.asyncio
async def test_k2_falls_back_to_vendored(tmp_path, monkeypatch):
    calls = []
    _arm(monkeypatch, calls)
    harness = _FakeHarness()
    inputs = _inputs(tmp_path, [_traj(tmp_path, "t1_r0.jsonl"), _traj(tmp_path, "t1_r1.jsonl")])
    result = await mod.run_digester_singleshot(inputs, harness)
    assert calls == ["vendored"]
    assert harness.model_config.single.ran == 0
    assert result.final_output == "(vendored)"


@pytest.mark.asyncio
async def test_oversize_falls_back(tmp_path, monkeypatch):
    calls = []
    _arm(monkeypatch, calls)
    monkeypatch.setenv(mod.MAX_CHARS_ENV, "50")
    harness = _FakeHarness()
    inputs = _inputs(tmp_path, [_traj(tmp_path, pad=500)])
    await mod.run_digester_singleshot(inputs, harness)
    assert calls == ["vendored"]
    assert harness.model_config.single.ran == 0


@pytest.mark.asyncio
async def test_empty_reply_falls_back(tmp_path, monkeypatch):
    calls = []
    _arm(monkeypatch, calls)
    harness = _FakeHarness(text="   ")
    inputs = _inputs(tmp_path, [_traj(tmp_path)])
    result = await mod.run_digester_singleshot(inputs, harness)
    assert harness.model_config.single.ran == 1  # tried single-shot first
    assert calls == ["vendored"]  # then fell back
    assert result.final_output == "(vendored)"
    assert not inputs.digest_out_path.exists()


@pytest.mark.asyncio
async def test_flag_off_is_vendored(tmp_path, monkeypatch):
    calls = []
    _arm(monkeypatch, calls)
    monkeypatch.setenv(mod.FLAG, "0")
    harness = _FakeHarness()
    await mod.run_digester_singleshot(_inputs(tmp_path, [_traj(tmp_path)]), harness)
    assert calls == ["vendored"]


def test_install_patches_and_restores():
    import harnessx.aegis.stages.preprocess as pre

    original = pre._run_digester
    with mod.install_singleshot_digester():
        assert pre._run_digester is mod.run_digester_singleshot
        assert mod._ORIGINAL_RUN is original
    assert pre._run_digester is original
    assert mod._ORIGINAL_RUN is None
