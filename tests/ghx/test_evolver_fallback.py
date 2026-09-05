# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 fix #2 — evolver-burnout revival from the rejected pool."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from harnessx.ghx.evolver_fallback import (
    install_evolver_fallback,
    revive_candidate,
    run_stage_2_with_fallback,
)


def _mk_run(tmp_path: Path) -> Path:
    run = tmp_path / "arm"
    (run / "data").mkdir(parents=True)
    rows = [
        {"round": 2, "candidate_id": "C-R2-01", "bucket": "processor", "rejection_text_excerpt": "IV-3 no anchors"},
        {"round": 3, "candidate_id": "C-R3-03", "bucket": "tools", "rejection_text_excerpt": "strategy_concern"},
        {"round": 3, "candidate_id": "C-R3-05", "bucket": "prompt", "rejection_text_excerpt": "no applied dir"},
    ]
    with (run / "data" / "rejected_candidates.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    for rnd, cid in ((2, "C-R2-01"), (3, "C-R3-03")):
        (run / f"R{rnd}" / "candidates").mkdir(parents=True, exist_ok=True)
        (run / f"R{rnd}" / "candidates" / f"{cid}.md").write_text(
            f"---\ncandidate_id: {cid}\nbucket: x\n---\n\nbody of {cid}\n", encoding="utf-8"
        )
        adir = run / f"R{rnd}" / "applied" / cid
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "config.yaml").write_text("cfg: 1\n", encoding="utf-8")
        (adir / "asset.py").write_text("# asset\n", encoding="utf-8")
    # C-R3-05 deliberately has NO source files → not revivable
    (run / "R5" / "candidates").mkdir(parents=True)
    return run


def test_revive_picks_newest_revivable(tmp_path):
    run = _mk_run(tmp_path)
    out = revive_candidate(run, 5, run / "R5" / "candidates")
    assert out is not None and out.name == "C-R5-91.md"
    text = out.read_text(encoding="utf-8")
    assert "candidate_id: C-R5-91" in text and "candidate_id: C-R3-03" not in text
    assert "Revival note" in text and "C-R3-03" in text and "R3" in text
    # applied dir copied with assets
    assert (run / "R5" / "applied" / "C-R5-91" / "config.yaml").exists()
    assert (run / "R5" / "applied" / "C-R5-91" / "asset.py").exists()


def test_revive_none_when_pool_empty(tmp_path):
    run = tmp_path / "bare"
    (run / "R5" / "candidates").mkdir(parents=True)
    assert revive_candidate(run, 5, run / "R5" / "candidates") is None


def test_wrapper_amends_only_empty_results(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_EVOLVER_FALLBACK", "1")
    run = _mk_run(tmp_path)

    async def burned(**kw):
        return {"results": [], "ok_count": 0, "candidate_paths": [], "error": "boom"}

    async def healthy(**kw):
        return {"results": [("C-R5-01", True, "ok")], "ok_count": 1, "candidate_paths": [Path("x")]}

    kw = {"round_n": 5, "candidates_dir": run / "R5" / "candidates"}
    out = asyncio.run(run_stage_2_with_fallback(burned, **kw))
    assert len(out["candidate_paths"]) == 1 and out["candidate_paths"][0].stem == "C-R5-91"
    assert out["ok_count"] == 1 and "revived" in out["results"][-1][2]
    # healthy stage-2 untouched (same object)
    out2 = asyncio.run(run_stage_2_with_fallback(healthy, **kw))
    assert out2["candidate_paths"] == [Path("x")]
    # flag off → burnout stays a burnout
    monkeypatch.delenv("HARNESSX_GHX_EVOLVER_FALLBACK")
    out3 = asyncio.run(run_stage_2_with_fallback(burned, **kw))
    assert out3["candidate_paths"] == []


def test_installer_patches_and_restores():
    import harnessx.aegis.orchestrator as om

    original = om.run_stage_2
    with install_evolver_fallback():
        assert om.run_stage_2 is not original
    assert om.run_stage_2 is original
