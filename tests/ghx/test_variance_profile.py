# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Variance profile — unstable-task census, long-then-wrong flag, seam chaining."""

from __future__ import annotations

import contextlib
import json
import logging
from pathlib import Path

import harnessx.ghx.variance_profile as vp

T_LTW = "11111111-1111-1111-1111-111111111111"  # long-then-wrong, done-with-wrong
T_BUDGET = "22222222-2222-2222-2222-222222222222"  # longer fails, but budget-death
T_NEVER3 = "33333333-3333-3333-3333-333333333333"  # chronic fail, >=3 obs
T_ALWAYS = "44444444-4444-4444-4444-444444444444"  # always passes — not unstable
T_TOO_FEW = "55555555-5555-5555-5555-555555555555"  # 2 obs, all fail — excluded
T_CARRIED = "66666666-6666-6666-6666-666666666666"  # swinger with a carried row


def _history_rows() -> list:
    rows = [
        {"task_id": T_LTW, "round": 1, "level": "2", "passed": True, "steps": 5, "exit": "done"},
        {"task_id": T_LTW, "round": 2, "level": "2", "passed": False, "steps": 25, "exit": "done"},
        {"task_id": T_LTW, "round": 3, "level": "2", "passed": True, "steps": 6, "exit": "done"},
        {"task_id": T_LTW, "round": 4, "level": "2", "passed": False, "steps": 30, "exit": "done"},

        {"task_id": T_BUDGET, "round": 1, "level": "2", "passed": True, "steps": 5, "exit": "done"},
        {"task_id": T_BUDGET, "round": 2, "level": "2", "passed": False, "steps": 50, "exit": "budget_exceeded"},
        {"task_id": T_BUDGET, "round": 3, "level": "2", "passed": True, "steps": 6, "exit": "done"},
        {"task_id": T_BUDGET, "round": 4, "level": "2", "passed": False, "steps": 55, "exit": "budget_exceeded"},

        {"task_id": T_NEVER3, "round": 1, "level": "1", "passed": False, "steps": 10, "exit": "done"},
        {"task_id": T_NEVER3, "round": 2, "level": "1", "passed": False, "steps": 12, "exit": "error"},
        {"task_id": T_NEVER3, "round": 3, "level": "1", "passed": False, "steps": 11, "exit": "done"},

        {"task_id": T_ALWAYS, "round": 1, "level": "1", "passed": True, "steps": 5, "exit": "done"},
        {"task_id": T_ALWAYS, "round": 2, "level": "1", "passed": True, "steps": 5, "exit": "done"},
        {"task_id": T_ALWAYS, "round": 3, "level": "1", "passed": True, "steps": 5, "exit": "done"},
        {"task_id": T_ALWAYS, "round": 4, "level": "1", "passed": True, "steps": 5, "exit": "done"},

        {"task_id": T_TOO_FEW, "round": 1, "level": "1", "passed": False, "steps": 9, "exit": "done"},
        {"task_id": T_TOO_FEW, "round": 2, "level": "1", "passed": False, "steps": 8, "exit": "done"},

        {"task_id": T_CARRIED, "round": 1, "level": "3", "passed": True, "steps": 5, "exit": "done"},
        {"task_id": T_CARRIED, "round": 2, "level": "3", "passed": True, "steps": 999, "exit": "done", "carried": True},
        {"task_id": T_CARRIED, "round": 3, "level": "3", "passed": False, "steps": 20, "exit": "done"},
        {"task_id": T_CARRIED, "round": 4, "level": "3", "passed": False, "steps": 22, "exit": "done"},
    ]
    return rows


def _mk_run(tmp_path: Path) -> Path:
    run = tmp_path
    (run / "data").mkdir(parents=True)
    (run / "data" / "task_history.jsonl").write_text(
        "\n".join(json.dumps(r) for r in _history_rows()), encoding="utf-8"
    )
    return run


def _row(rep, task_id):
    for r in rep.rows:
        if r.task_id == task_id:
            return r
    raise AssertionError(f"{task_id} not in unstable rows")


def test_unstable_filter_selects_the_right_tasks(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    assert rep is not None
    assert rep.total_tasks == 6
    ids = {r.task_id for r in rep.rows}
    assert ids == {T_LTW, T_BUDGET, T_NEVER3, T_CARRIED}
    assert T_ALWAYS not in ids  # rate 1.0, not < 0.8
    assert T_TOO_FEW not in ids  # rate 0 < 0.8 but n_obs=2 < 3


def test_buckets_match_flip_ledger_semantics(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    assert _row(rep, T_LTW).bucket == "swinger"
    assert _row(rep, T_NEVER3).bucket == "never"
    assert _row(rep, T_CARRIED).bucket == "swinger"


def test_flip_count_counts_transitions_over_non_carried_rounds(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    assert _row(rep, T_LTW).flip_count == 3  # T F T F
    # carried round (999 steps) is skipped entirely: T . F F -> one transition
    assert _row(rep, T_CARRIED).flip_count == 1


def test_median_steps_pass_vs_fail(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    row = _row(rep, T_LTW)
    assert row.median_pass_steps == 5.5
    assert row.median_fail_steps == 27.5
    carried_row = _row(rep, T_CARRIED)
    assert carried_row.median_pass_steps == 5  # only the non-carried r1 counts
    assert carried_row.median_fail_steps == 21


def test_fail_exit_anatomy(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    assert dict(_row(rep, T_BUDGET).fail_exit_counts) == {"budget_exceeded": 2}
    assert dict(_row(rep, T_NEVER3).fail_exit_counts) == {"done": 2, "error": 1}


def test_long_then_wrong_flag(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    assert _row(rep, T_LTW).long_then_wrong is True
    # fails longer than passes, but exit is budget_exceeded -> not long-then-wrong
    assert _row(rep, T_BUDGET).long_then_wrong is False
    # no passing round to compare against
    assert _row(rep, T_NEVER3).long_then_wrong is False
    assert _row(rep, T_CARRIED).long_then_wrong is True


def test_pass_rate_property(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    assert _row(rep, T_LTW).pass_rate == 0.5
    assert _row(rep, T_NEVER3).pass_rate == 0.0


def test_render_lists_highest_value_targets(tmp_path):
    run = _mk_run(tmp_path)
    rep = vp.build_variance_profile(run, 4)
    md = vp.render_variance_profile(rep)
    assert "## Highest-value targets (long_then_wrong)" in md
    assert f"`{T_LTW}`" in md
    assert f"`{T_CARRIED}`" in md
    assert f"`{T_BUDGET}`" not in md.split("## Highest-value targets")[1]
    assert "YES" in md


def test_history_missing_returns_none_not_a_crash(tmp_path, caplog):
    with caplog.at_level(logging.WARNING, logger="harnessx.ghx.variance_profile"):
        rep = vp.build_variance_profile(tmp_path, 1)
    assert rep is None
    assert "task_history" in caplog.text


def test_no_unstable_tasks_still_returns_report(tmp_path):
    run = tmp_path
    (run / "data").mkdir(parents=True)
    (run / "data" / "task_history.jsonl").write_text(
        json.dumps({"task_id": T_ALWAYS, "round": 1, "level": "1", "passed": True, "steps": 5, "exit": "done"}),
        encoding="utf-8",
    )
    rep = vp.build_variance_profile(run, 1)
    assert rep is not None and rep.has_data and rep.rows == []
    md = vp.render_variance_profile(rep)
    assert "no unstable tasks this round" in md
    assert "(none this round)" in md


# ── seam ──────────────────────────────────────────────────────────────────────


def test_seam_writes_md_and_json(tmp_path, monkeypatch):
    run = _mk_run(tmp_path)
    digests_dir = run / "R4" / "digests"
    digests_dir.mkdir(parents=True)
    summary = run / "R4" / "summary.md"

    def fake_official(*, digests_dir, summary_path, cluster_path=None):
        Path(summary_path).write_text("# Aggregate\n", encoding="utf-8")
        return {"actionability": 1.0}

    monkeypatch.setattr(vp, "_ORIGINAL_AGGREGATE", fake_official)
    result = vp.aggregate_digests_with_variance_profile(digests_dir=digests_dir, summary_path=summary)
    assert result == {"actionability": 1.0}

    md_path = run / "R4" / "graph_evidence" / "variance_profile.md"
    json_path = run / "R4" / "graph_evidence" / "variance_profile.json"
    assert md_path.exists() and json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["history_round"] == 4
    ids = {r["task_id"] for r in data["rows"]}
    assert ids == {T_LTW, T_BUDGET, T_NEVER3, T_CARRIED}


def test_seam_skips_write_when_history_missing(tmp_path, monkeypatch):
    d = tmp_path / "R1" / "digests"
    d.mkdir(parents=True)
    summary = tmp_path / "R1" / "summary.md"

    def fake_official(*, digests_dir, summary_path, cluster_path=None):
        Path(summary_path).write_text("# Aggregate\n", encoding="utf-8")
        return {"actionability": 1.0}

    monkeypatch.setattr(vp, "_ORIGINAL_AGGREGATE", fake_official)
    result = vp.aggregate_digests_with_variance_profile(digests_dir=d, summary_path=summary)
    assert result == {"actionability": 1.0}
    assert not (tmp_path / "R1" / "graph_evidence" / "variance_profile.md").exists()


def test_install_restores_and_flag_off_is_noop(monkeypatch):
    import harnessx.aegis.stages.preprocess as pp

    monkeypatch.delenv(vp.FLAG, raising=False)
    original = pp.aggregate_digests
    assert not vp.variance_profile_enabled()
    ctx = vp.install_variance_profile() if vp.variance_profile_enabled() else contextlib.nullcontext()
    with ctx:
        assert pp.aggregate_digests is original
    assert pp.aggregate_digests is original

    monkeypatch.setenv(vp.FLAG, "1")
    assert vp.variance_profile_enabled()
    with vp.install_variance_profile():
        assert pp.aggregate_digests is vp.aggregate_digests_with_variance_profile
    assert pp.aggregate_digests is original
    assert vp._ORIGINAL_AGGREGATE is None


def test_seam_composes_with_flip_ledger_in_either_order(tmp_path, monkeypatch):
    """Both overlays chain-patch the same preprocess.aggregate_digests seam —
    installing both (either nesting order) must not clobber either output."""
    import harnessx.ghx.flip_ledger as fl
    import harnessx.aegis.stages.preprocess as pp

    run = _mk_run(tmp_path)
    digests_dir = run / "R4" / "digests"
    digests_dir.mkdir(parents=True)
    summary = run / "R4" / "summary.md"

    def fake_official(*, digests_dir, summary_path, cluster_path=None):
        Path(summary_path).write_text("# Aggregate\n", encoding="utf-8")
        return {"actionability": 1.0}

    monkeypatch.setattr(pp, "aggregate_digests", fake_official)
    with fl.install_flip_ledger(), vp.install_variance_profile():
        result = pp.aggregate_digests(digests_dir=digests_dir, summary_path=summary)
    assert result == {"actionability": 1.0}
    assert (run / "R4" / "graph_evidence" / "flip_ledger.md").exists()
    assert (run / "R4" / "graph_evidence" / "variance_profile.md").exists()
    assert pp.aggregate_digests is fake_official


# ── offline CLI ──────────────────────────────────────────────────────────────


def test_cli_out_file(tmp_path):
    run = _mk_run(tmp_path)
    out = tmp_path / "out.md"
    code = vp.main([str(run), "--round", "4", "--out", str(out)])
    assert code == 0
    assert out.exists()
    assert "Variance profile" in out.read_text(encoding="utf-8")


def test_cli_no_data_returns_1(tmp_path, capsys):
    code = vp.main([str(tmp_path), "--round", "1"])
    assert code == 1
    assert "no usable task_history" in capsys.readouterr().err
