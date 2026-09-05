# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 gates batch — the Gate-B prerequisite: real-task replay resolver."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from harnessx.ghx.gate_replay import GateReplayResolver, pick_replay_task

CID = "C-R3-01"
T_HARD = "aaaaaaaa-0000-0000-0000-000000000001"  # fails 1-3 → streak 3
T_SOFT = "bbbbbbbb-0000-0000-0000-000000000002"  # passes 3 → streak 0


def _mk_run(tmp_path: Path) -> Path:
    run = tmp_path / "arm"
    (run / "data").mkdir(parents=True)
    with (run / "data" / "task_history.jsonl").open("w", encoding="utf-8") as f:
        for r in (1, 2, 3):
            f.write(json.dumps({"round": r, "task_id": T_HARD, "passed": False, "passed_flags": [False]}) + "\n")
            f.write(json.dumps({"round": r, "task_id": T_SOFT, "passed": r == 3, "passed_flags": [r == 3]}) + "\n")
    cdir = run / "R3" / "candidates"
    cdir.mkdir(parents=True)
    fm = yaml.safe_dump(
        {
            "candidate_id": CID,
            "bucket": "processor",
            "predicted_impact": {"tasks_will_unlock": [T_SOFT, T_HARD]},
            "file_changes": [{"path": "x/guard_v9.py", "action": "create", "diff_summary": "new"}],
        }
    )
    (cdir / f"{CID}.md").write_text(f"---\n{fm}---\n\nbody\n", encoding="utf-8")
    adir = run / "R3" / "applied" / CID
    adir.mkdir(parents=True)
    (adir / "config.yaml").write_text("sessions:\n  base_dir: x\n", encoding="utf-8")
    return run


def test_pick_replay_task_prefers_longest_fail_streak(tmp_path):
    run = _mk_run(tmp_path)
    assert pick_replay_task([T_SOFT, T_HARD], run) == T_HARD
    assert pick_replay_task([], run) is None
    # no history at all → deterministic lexicographic
    assert pick_replay_task(["zz", "aa"], tmp_path / "nowhere") == "aa"


def _resolver(run, calls, ret="U_PATH"):
    async def runner(config_path, task_id, session_id):
        calls.append((config_path, task_id, session_id))
        if isinstance(ret, Exception):
            raise ret
        return ret

    r = GateReplayResolver(runner)
    r.bind_round(run, 3)
    return r


def test_resolver_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_GATE_REPLAY", "1")
    run = _mk_run(tmp_path)
    calls: list = []
    r = _resolver(run, calls)
    assert r(CID) == "U_PATH"
    (cfg, task, sess) = calls[0]
    assert cfg.endswith("config.yaml") and CID in cfg
    assert task == T_HARD  # the gate's choice, not the candidate's
    assert sess == f"gatereplay/R3-{CID}"


def test_resolver_honesty_ladder(tmp_path, monkeypatch):
    run = _mk_run(tmp_path)
    calls: list = []
    # flag off → None, runner untouched
    monkeypatch.delenv("HARNESSX_GHX_GATE_REPLAY", raising=False)
    assert _resolver(run, calls)(CID) is None and not calls
    monkeypatch.setenv("HARNESSX_GHX_GATE_REPLAY", "1")
    # unbound → None
    assert GateReplayResolver(lambda *a: None)(CID) is None
    # missing manifest → None
    assert _resolver(run, calls)("C-R3-99") is None and not calls
    # crashing runner → None (never a rejection)
    assert _resolver(run, calls, ret=RuntimeError("boom"))(CID) is None
    # runner returning None → None
    assert _resolver(run, calls, ret=None)(CID) is None


def test_hung_runner_times_out_and_passes_through(tmp_path, monkeypatch):
    """The 30x5 deadlock shape: a runner that never returns must resolve to
    None within the inner wait_for bound — never wedge the round (the with-
    block executor's shutdown(wait=True) used to undo the timeout)."""
    import asyncio
    import time

    monkeypatch.setenv("HARNESSX_GHX_GATE_REPLAY", "1")
    run = _mk_run(tmp_path)

    async def hangs(config_path, task_id, session_id):
        await asyncio.sleep(3600)

    r = GateReplayResolver(hangs, timeout_s=1.5)
    r.bind_round(run, 3)
    t0 = time.monotonic()
    assert r(CID) is None
    assert time.monotonic() - t0 < 30  # bounded, not the 2h+ wedge


def test_bridge_worker_is_daemon(tmp_path, monkeypatch):
    """M24 fix #5: the replay worker must be a daemon thread — a wedged replay
    used to keep the finished interpreter alive (30x5 post-run zombie)."""
    import asyncio
    import threading

    monkeypatch.setenv("HARNESSX_GHX_GATE_REPLAY", "1")
    run = _mk_run(tmp_path)
    seen = {}

    async def probe(config_path, task_id, session_id):
        seen["daemon"] = threading.current_thread().daemon
        return "U"

    r = GateReplayResolver(probe, timeout_s=10)
    r.bind_round(run, 3)
    assert r(CID) == "U"
    assert seen["daemon"] is True
    # and a permanently-wedged worker still can't outlive its bound
    async def wedged(*a):
        await asyncio.sleep(3600)

    r2 = GateReplayResolver(wedged, timeout_s=1.0)
    r2.bind_round(run, 3)
    assert r2(CID) is None
    leftovers = [t for t in threading.enumerate() if t.name.startswith("gatereplay-")]
    assert all(t.daemon for t in leftovers)  # leaked-but-daemon: exit stays unblocked
