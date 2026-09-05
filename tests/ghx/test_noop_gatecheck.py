# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M27 T1.2 — the rejected-candidates ledger fix (always on) and the
gate-confirmed no_op (HARNESSX_GHX_NOOP_GATECHECK)."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from harnessx.ghx.noop_gatecheck import (
    append_noop_gatecheck_audit,
    install_noop_gatecheck,
    install_noop_ledger_fix,
    noop_gatecheck_enabled,
    pick_top_candidate,
    run_minimal_gate_subset,
    write_rejected_ledger_on_critic_failed,
)


def _write_manifest(path: Path, frontmatter: dict, body: str = "\n## Failure Evidence\n") -> None:
    front = yaml.safe_dump(frontmatter)
    path.write_text(f"---\n{front}---\n{body}", encoding="utf-8")


# ── enabled() ─────────────────────────────────────────────────────────────────


def test_noop_gatecheck_enabled_default_off(monkeypatch):
    monkeypatch.delenv("HARNESSX_GHX_NOOP_GATECHECK", raising=False)
    assert noop_gatecheck_enabled() is False


def test_noop_gatecheck_enabled_on(monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_NOOP_GATECHECK", "1")
    assert noop_gatecheck_enabled() is True


# ── T1.2(a): ledger fix ──────────────────────────────────────────────────────


def test_write_rejected_ledger_on_critic_failed(tmp_path):
    run_dir = tmp_path
    cdir = run_dir / "R1" / "candidates"
    cdir.mkdir(parents=True)
    _write_manifest(
        cdir / "C-R1-01.md",
        {
            "candidate_id": "C-R1-01",
            "bucket": "tools",
            "predicted_impact": {"tasks_will_unlock": ["t1", "t2"]},
        },
    )
    _write_manifest(
        cdir / "C-R1-02.md",
        {"candidate_id": "C-R1-02", "bucket": "config", "predicted_impact": {}},
    )

    write_rejected_ledger_on_critic_failed(run_dir, 1, cdir)

    rej_path = run_dir / "data" / "rejected_candidates.jsonl"
    rows = [json.loads(l) for l in rej_path.read_text(encoding="utf-8").splitlines()]
    by_cid = {r["candidate_id"]: r for r in rows}
    assert set(by_cid) == {"C-R1-01", "C-R1-02"}
    assert by_cid["C-R1-01"]["predicted_tasks"] == ["t1", "t2"]
    assert "critic_failed" in by_cid["C-R1-01"]["rejection_text_excerpt"]
    assert by_cid["C-R1-01"]["round"] == 1


def test_write_rejected_ledger_empty_dir_is_noop(tmp_path):
    run_dir = tmp_path
    cdir = run_dir / "R1" / "candidates"
    cdir.mkdir(parents=True)
    write_rejected_ledger_on_critic_failed(run_dir, 1, cdir)
    assert not (run_dir / "data" / "rejected_candidates.jsonl").exists()


async def test_install_noop_ledger_fix_wraps_critic_failed_path(tmp_path, monkeypatch):
    import harnessx.aegis.orchestrator as orch_mod

    cdir = tmp_path / "R2" / "candidates"
    cdir.mkdir(parents=True)
    _write_manifest(cdir / "C-R2-01.md", {"candidate_id": "C-R2-01", "bucket": "tools"})

    async def _fake_run_stage_3(**kwargs):
        return {"critic_failed": True, "decision": None}

    monkeypatch.setattr(orch_mod, "run_stage_3", _fake_run_stage_3)

    with install_noop_ledger_fix():
        result = await orch_mod.run_stage_3(candidates_dir=cdir, round_n=2)

    assert result == {"critic_failed": True, "decision": None}
    rej_path = tmp_path / "data" / "rejected_candidates.jsonl"
    assert rej_path.exists()
    rows = [json.loads(l) for l in rej_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["candidate_id"] == "C-R2-01"

    # restored afterward
    assert orch_mod.run_stage_3 is _fake_run_stage_3


async def test_install_noop_ledger_fix_skips_when_critic_succeeded(tmp_path, monkeypatch):
    import harnessx.aegis.orchestrator as orch_mod

    cdir = tmp_path / "R3" / "candidates"
    cdir.mkdir(parents=True)
    _write_manifest(cdir / "C-R3-01.md", {"candidate_id": "C-R3-01", "bucket": "tools"})

    async def _fake_run_stage_3(**kwargs):
        return {"critic_failed": False, "decision": {"decision_type": "no_op"}}

    monkeypatch.setattr(orch_mod, "run_stage_3", _fake_run_stage_3)

    with install_noop_ledger_fix():
        await orch_mod.run_stage_3(candidates_dir=cdir, round_n=3)

    assert not (tmp_path / "data" / "rejected_candidates.jsonl").exists()


# ── T1.2(b): gate-confirmed no_op ───────────────────────────────────────────


def test_pick_top_candidate_is_deterministic():
    assert pick_top_candidate({}) is None
    assert pick_top_candidate({"C-2": (), "C-1": (), "C-10": ()}) == "C-1"


def test_run_minimal_gate_subset_explorer_slot_passes(tmp_path):
    manifest_path = tmp_path / "C-R1-01.md"
    _write_manifest(
        manifest_path,
        {
            "candidate_id": "C-R1-01",
            "bucket": "tools",
            "file_changes": [{"path": "foo.py", "action": "modify"}],
            "predicted_impact": {},
            "slot_type": "explorer",
        },
    )
    candidates_info = {"C-R1-01": (manifest_path, tmp_path / "applied.yaml")}
    result = run_minimal_gate_subset("C-R1-01", candidates_info, current_round=1)
    assert result["structure"]["ok"] is True
    assert result["graph_existence"]["checked"] is False  # no replay U in eval-only mode
    assert result["graph_existence"]["ok"] is True  # unavailable → pass-through, never fabricated


def test_run_minimal_gate_subset_missing_key_fails(tmp_path):
    manifest_path = tmp_path / "C-R1-02.md"
    _write_manifest(manifest_path, {"candidate_id": "C-R1-02"})  # no bucket/file_changes
    candidates_info = {"C-R1-02": (manifest_path, tmp_path / "applied.yaml")}
    result = run_minimal_gate_subset("C-R1-02", candidates_info, current_round=1)
    assert result["structure"]["ok"] is False
    assert "IV-3" in result["structure"]["reason"]


def test_run_minimal_gate_subset_unknown_cid_returns_empty():
    assert run_minimal_gate_subset("nope", {}) == {}


def test_append_noop_gatecheck_audit_writes_a_distinct_kind(tmp_path):
    append_noop_gatecheck_audit(
        tmp_path, 4, "C-R4-01",
        {"structure": {"ok": True, "reason": ""}, "graph_existence": {"ok": True, "checked": False, "reason": "n/a"}},
    )
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    assert entry["kind"] == "noop_gatecheck"
    assert entry["payload"]["cid"] == "C-R4-01"
    assert entry["payload"]["results"] == {"structure": True, "graph_existence": True}
    assert "novelty" in entry["payload"]["excluded_gates"]


async def test_install_noop_gatecheck_fires_on_genuine_noop(tmp_path, monkeypatch):
    import harnessx.aegis.orchestrator as orch_mod

    cdir = tmp_path / "R5" / "candidates"
    cdir.mkdir(parents=True)
    manifest_path = cdir / "C-R5-01.md"
    _write_manifest(
        manifest_path,
        {
            "candidate_id": "C-R5-01",
            "bucket": "tools",
            "file_changes": [{"path": "foo.py", "action": "modify"}],
            "predicted_impact": {},
            "slot_type": "explorer",
        },
    )
    candidates_info = {"C-R5-01": (manifest_path, cdir / "applied.yaml")}

    async def _fake_run_stage_4(**kwargs):
        return {"shipped_cid": None, "shipped_cids": [], "reason": "no_op"}

    monkeypatch.setattr(orch_mod, "run_stage_4", _fake_run_stage_4)
    monkeypatch.setenv("HARNESSX_GHX_NOOP_GATECHECK", "1")

    with install_noop_gatecheck():
        result = await orch_mod.run_stage_4(
            round_n=5, decision={"decision_type": "no_op"}, candidates_info=candidates_info,
        )

    assert result["shipped_cids"] == []  # never ships on its own
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    assert entry["kind"] == "noop_gatecheck"
    assert entry["payload"]["cid"] == "C-R5-01"


async def test_install_noop_gatecheck_skips_when_something_shipped(tmp_path, monkeypatch):
    import harnessx.aegis.orchestrator as orch_mod

    async def _fake_run_stage_4(**kwargs):
        return {"shipped_cid": "C-R6-01", "shipped_cids": ["C-R6-01"], "reason": "shipped C-R6-01"}

    monkeypatch.setattr(orch_mod, "run_stage_4", _fake_run_stage_4)
    monkeypatch.setenv("HARNESSX_GHX_NOOP_GATECHECK", "1")

    with install_noop_gatecheck():
        await orch_mod.run_stage_4(
            round_n=6, decision={"decision_type": "ship"}, candidates_info={"C-R6-01": (Path("x"), Path("y"))},
        )

    assert not (tmp_path / "audit.jsonl").exists()
