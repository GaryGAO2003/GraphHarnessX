# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The reading discipline four campaigns lacked: compare what moved."""
from __future__ import annotations

import json

from harnessx.ghx.paired_read import (
    arm_from_task_history,
    mcnemar_exact,
    pair_arms,
    render,
)


def test_the_case_that_motivates_the_whole_module():
    """Eight fixed against one broken separates; the same run read as a total
    difference of +7 against a +-8 band does not. Same data, one question."""
    a = {f"t{i}": True for i in range(100)}
    b = dict(a)
    for i in range(8):  # arm B fixes eight of A's failures
        a[f"t{i}"] = False
    b["t50"] = False  # and breaks one
    res = pair_arms(a, b)
    assert (len(res.fixed), len(res.broken)) == (8, 1)
    assert res.net == 7
    assert res.p_value < 0.05
    assert "separated" in res.verdict()


def test_no_disagreement_is_not_a_null_result():
    res = pair_arms({"a": True, "b": False}, {"a": True, "b": False})
    assert res.discordant == 0
    assert res.p_value == 1.0
    assert "nothing to test" in res.verdict()


def test_a_wash_does_not_separate():
    a = {f"t{i}": i % 2 == 0 for i in range(20)}
    b = {f"t{i}": i % 3 == 0 for i in range(20)}
    res = pair_arms(a, b)
    assert res.p_value > 0.05
    assert "not separated" in res.verdict()


def test_exact_test_matches_the_binomial_by_hand():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(1, 0) == 1.0        # 2 * (1/2)
    assert abs(mcnemar_exact(5, 0) - 2 / 32) < 1e-12
    assert abs(mcnemar_exact(8, 1) - 2 * (1 + 9) / 512) < 1e-12
    assert mcnemar_exact(3, 3) == 1.0        # symmetric discordants: no evidence
    assert mcnemar_exact(2, 7) == mcnemar_exact(7, 2)  # direction-free


def test_a_task_missing_from_one_arm_is_never_counted_as_a_failure():
    """A crashed rollout must not read as a regression that never happened."""
    res = pair_arms({"a": True, "b": True}, {"a": True})
    assert res.missing == ["b"]
    assert res.broken == [] and res.n_paired == 1


def test_arm_from_history_takes_the_latest_fresh_row(tmp_path):
    rows = [
        {"round": 0, "task_id": "7", "passed": False},
        {"round": 1, "task_id": "7", "passed": True},
        {"round": 2, "task_id": "7", "passed": False, "carried": True},  # a copy, not a draw
        {"round": 0, "task_id": "9", "passed": True},
    ]
    d = tmp_path / "data"
    d.mkdir()
    (d / "task_history.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    arm = arm_from_task_history(tmp_path)
    assert arm == {"7": True, "9": True}
    assert arm_from_task_history(tmp_path, round_n=0) == {"7": False, "9": True}


def test_render_shows_both_readings(tmp_path):
    a = {"t1": False, "t2": True, "t3": True}
    b = {"t1": True, "t2": False, "t3": True}
    out = render(pair_arms(a, b), "L0", "L2")
    assert "L0" in out and "L2" in out
    assert "Fixed (1)" in out and "Broken (1)" in out
    assert "the paired test reads the 2 task(s) that actually moved" in out
