# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M27 T1.3 — paired-read evidence at the gate, read/report-only."""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.paired_gate import (
    append_paired_gate_audit,
    compute_predicted_task_paired_read,
    paired_gate_enabled,
    predicted_tasks_for_round,
    write_paired_gate_evidence,
)
from harnessx.ghx.paired_read import pair_arms


def _write_ship_outcomes(run_dir: Path, rows: list[dict]) -> None:
    (run_dir / "data").mkdir(parents=True, exist_ok=True)
    (run_dir / "data" / "ship_outcomes.json").write_text(json.dumps(rows), encoding="utf-8")


def _write_history(run_dir: Path, rows: list[tuple[int, str, bool]]) -> None:
    (run_dir / "data").mkdir(parents=True, exist_ok=True)
    with (run_dir / "data" / "task_history.jsonl").open("w", encoding="utf-8") as f:
        for rnd, tid, passed in rows:
            f.write(json.dumps({"round": rnd, "task_id": tid, "passed": passed}) + "\n")


def test_flag_default_off(monkeypatch):
    monkeypatch.delenv("HARNESSX_GHX_PAIRED_GATE", raising=False)
    assert paired_gate_enabled() is False
    monkeypatch.setenv("HARNESSX_GHX_PAIRED_GATE", "1")
    assert paired_gate_enabled() is True


def test_predicted_tasks_for_round_unions_and_dedupes(tmp_path):
    _write_ship_outcomes(tmp_path, [
        {"ship_id": "C-R3-01", "round": 3, "predicted_tasks": ["a", "b"]},
        {"ship_id": "C-R3-02", "round": 3, "predicted_tasks": ["b", "c"]},
        {"ship_id": "C-R2-01", "round": 2, "predicted_tasks": ["z"]},
    ])
    out = predicted_tasks_for_round(tmp_path, 3)
    assert out == ["a", "b", "c"]


def test_predicted_tasks_for_round_filters_by_ship_ids(tmp_path):
    _write_ship_outcomes(tmp_path, [
        {"ship_id": "C-R3-01", "round": 3, "predicted_tasks": ["a"]},
        {"ship_id": "C-R3-02", "round": 3, "predicted_tasks": ["b"]},
    ])
    out = predicted_tasks_for_round(tmp_path, 3, ship_ids={"C-R3-02"})
    assert out == ["b"]


def test_predicted_tasks_for_round_missing_ledger_returns_empty(tmp_path):
    assert predicted_tasks_for_round(tmp_path, 1) == []


def test_compute_predicted_task_paired_read_scopes_to_predicted_set(tmp_path):
    _write_history(tmp_path, [
        (2, "a", False), (2, "b", True), (2, "c", True),
        (3, "a", True), (3, "b", False), (3, "c", True),
    ])
    # "c" is not in predicted_tasks — must not affect the pairing.
    result = compute_predicted_task_paired_read(
        tmp_path, round_idx=3, pre_ship_round=2, predicted_tasks=["a", "b"],
    )
    assert result is not None
    assert result.fixed == ["a"]
    assert result.broken == ["b"]
    assert result.n_paired == 2


def test_compute_predicted_task_paired_read_empty_predicted_set_is_none(tmp_path):
    _write_history(tmp_path, [(2, "a", True), (3, "a", True)])
    assert compute_predicted_task_paired_read(
        tmp_path, round_idx=3, pre_ship_round=2, predicted_tasks=[],
    ) is None


def test_write_paired_gate_evidence(tmp_path):
    result = pair_arms({"a": False, "b": True}, {"a": True, "b": True})
    md_path = write_paired_gate_evidence(tmp_path, 4, result)
    assert md_path.exists()
    assert "Paired read" in md_path.read_text(encoding="utf-8")
    json_path = tmp_path / "R4" / "graph_evidence" / "paired_gate.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["round"] == 4
    assert data["fixed"] == ["a"]
    assert data["net"] == 1


def test_append_paired_gate_audit(tmp_path):
    result = pair_arms({"a": False}, {"a": True})
    append_paired_gate_audit(tmp_path, 7, result)
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    assert entry["round"] == 7
    assert entry["kind"] == "paired_gate"
    assert entry["payload"]["fixed"] == ["a"]
    assert "verdict" in entry["payload"]
