# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 — counterfactual adjudication: plan gating, verdict semantics."""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.counterfactual import (
    CounterfactualPlan,
    plan_counterfactual,
    render_counterfactual,
    run_counterfactual,
)

T_STABLE = "bbbbbbbb-0000-0000-0000-000000000002"
T_SWING = "aaaaaaaa-0000-0000-0000-000000000001"


def _mk_run(tmp_path: Path) -> Path:
    run = tmp_path / "arm"
    (run / "data").mkdir(parents=True)
    rows = []
    for r in range(1, 9):
        rows.append({"round": r, "task_id": T_STABLE, "passed": 3 <= r <= 7, "passed_flags": [3 <= r <= 7]})
        rows.append({"round": r, "task_id": T_SWING, "passed": r == 7, "passed_flags": [r == 7]})
    with (run / "data" / "task_history.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    (run / "data" / "ship_outcomes.json").write_text(
        json.dumps([{"ship_id": "C-R8-01", "round": 8, "bucket": "processor"}]), encoding="utf-8"
    )
    (run / "R7").mkdir()
    (run / "R7" / "config.yaml").write_text("x: 1\n", encoding="utf-8")
    return run


def test_plan_gates_on_streak_and_prior_config(tmp_path):
    run = _mk_run(tmp_path)
    plan = plan_counterfactual(run, 8, 9)
    assert plan.eligible == [T_STABLE]  # streak 5; the swinger (streak 1) excluded
    assert plan.skipped_swingers == 1
    assert plan.config_path.endswith("config.yaml") and "R7" in plan.config_path
    assert plan.suspects == ["C-R8-01"]


def test_run_and_verdicts(tmp_path):
    run = _mk_run(tmp_path)
    plan = plan_counterfactual(run, 8, 9)
    calls = []

    async def passes(cfg, tid, sess):
        calls.append((cfg, tid, sess))
        return True

    async def fails(cfg, tid, sess):
        return False

    async def broken(cfg, tid, sess):
        raise RuntimeError("boom")

    v = run_counterfactual(plan, passes)[0]
    assert v.verdict == "passes" and calls[0][1] == T_STABLE and "counterfactual/R8" in calls[0][2]
    assert run_counterfactual(plan, fails)[0].verdict == "still_fails"
    assert run_counterfactual(plan, broken)[0].verdict == "unresolved"

    md = render_counterfactual(plan, [v])
    assert "ship-set removal" in md and f"`{T_STABLE}`: **passes**" in md


def test_empty_config_plan_refuses_to_run():
    plan = CounterfactualPlan(round_n=3, config_path="", eligible=["x"], stat_verdict="EXCESS")

    async def never(*a):  # pragma: no cover - must not be called
        raise AssertionError

    assert run_counterfactual(plan, never) == []
