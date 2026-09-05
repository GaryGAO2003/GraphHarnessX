# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Flip ledger — cross-round census, this-round swinger diagnosis, leak scan, seam chaining."""

from __future__ import annotations

import contextlib
import json
import logging
from pathlib import Path

import harnessx.ghx.flip_ledger as fl

T_ALWAYS = "a1111111-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
T_NEVER = "b2222222-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
T_SWING = "c3333333-cccc-cccc-cccc-cccccccccccc"
T_SWINGC = "d4444444-dddd-dddd-dddd-dddddddddddd"


def _history_rows() -> list:
    rows = []
    for rd in (1, 2, 3, 4):
        rows.append({"task_id": T_ALWAYS, "round": rd, "level": "1", "passed": True})
        rows.append({"task_id": T_NEVER, "round": rd, "level": "2", "passed": False})
    rows += [
        {"task_id": T_SWING, "round": 1, "level": "2", "passed": True},
        {"task_id": T_SWING, "round": 2, "level": "2", "passed": False},
        {"task_id": T_SWING, "round": 3, "level": "2", "passed": True},
        {"task_id": T_SWING, "round": 4, "level": "2", "passed": False},
        # round 2 is carried and stores passed=True — must not count as a pass
        {"task_id": T_SWINGC, "round": 1, "level": "3", "passed": True},
        {"task_id": T_SWINGC, "round": 2, "level": "3", "passed": True, "carried": True},
        {"task_id": T_SWINGC, "round": 3, "level": "3", "passed": False},
        {"task_id": T_SWINGC, "round": 4, "level": "3", "passed": False},
    ]
    return rows


def _mk_run(tmp_path: Path, round_dir_name: str = "R4"):
    """run_dir with data/task_history.jsonl (rounds 1..4, history max = 4) and
    round_dir_name/digests holding this round's diagnosis: two ALL_FAIL swinger
    digests sharing a failure_mode, one ALL_PASS digest with a leaking strategy;
    T_NEVER gets no digest this round at all."""
    run = tmp_path
    (run / "data").mkdir(parents=True)
    (run / "data" / "task_history.jsonl").write_text(
        "\n".join(json.dumps(r) for r in _history_rows()), encoding="utf-8"
    )
    d = run / round_dir_name / "digests"
    d.mkdir(parents=True)
    (d / f"{T_SWING}.md").write_text(
        "pattern: ALL_FAIL\nfailure_mode: unverified_commit\n\nbody\n", encoding="utf-8"
    )
    (d / f"{T_SWINGC}.md").write_text(
        "pattern: ALL_FAIL\nfailure_mode: unverified_commit\n\nbody\n", encoding="utf-8"
    )
    (d / f"{T_ALWAYS}.md").write_text(
        "pattern: ALL_PASS\nstrategy: leak_snippet_commit\nfailure_mode: none\n\nbody\n",
        encoding="utf-8",
    )
    return run, d


def test_census_and_batch(tmp_path):
    run, d = _mk_run(tmp_path)
    rep = fl.build_flip_ledger(run, d, 4)
    assert rep.total_tasks == 4
    assert rep.always == 1 and rep.swinger == 2 and rep.never == 1
    assert rep.ever_passed == 3
    assert rep.batch_total == 4 and rep.batch_pass == 1 and rep.batch_carried == 0


def test_pattern_strings_and_carried_excluded_from_pass_count(tmp_path):
    run, d = _mk_run(tmp_path)
    rep = fl.build_flip_ledger(run, d, 4)
    rows = {r["task_id"]: r for r in rep.swinger_rows}
    assert rows[T_SWING]["pattern"] == "#.#."
    assert rows[T_SWING]["n_pass"] == 2 and rows[T_SWING]["n_obs"] == 4
    assert rows[T_SWINGC]["pattern"] == "#~.."
    # the carried round stored passed=True — it must not inflate the pass count
    assert rows[T_SWINGC]["n_pass"] == 1 and rows[T_SWINGC]["n_obs"] == 3


def test_swinger_table_has_failure_mode_and_backtick_anchor(tmp_path):
    run, d = _mk_run(tmp_path)
    rep = fl.build_flip_ledger(run, d, 4)
    md = fl.render_flip_ledger(rep)
    assert "`unverified_commit`" in md
    assert f"`digests/{T_SWING}.md#L2`" in md
    assert f"`digests/{T_SWINGC}.md#L2`" in md


def test_label_grouping_is_exact_string_no_clustering(tmp_path):
    run, d = _mk_run(tmp_path)
    rep = fl.build_flip_ledger(run, d, 4)
    assert rep.label_counts["unverified_commit"] == 2
    assert sorted(rep.label_tasks["unverified_commit"]) == sorted([T_SWING, T_SWINGC])
    md = fl.render_flip_ledger(rep)
    assert "labels are free text — cluster them yourself" in md
    assert "predicted task ids from this table" in md


def test_leak_scan_hits_strategy_line(tmp_path):
    run, d = _mk_run(tmp_path)
    rep = fl.build_flip_ledger(run, d, 4)
    assert len(rep.leak_rows) == 1
    assert rep.leak_rows[0]["task_id"] == T_ALWAYS
    assert rep.leak_rows[0]["strategy_raw"] == "leak_snippet_commit"
    md = fl.render_flip_ledger(rep)
    assert f"`digests/{T_ALWAYS}.md#L2`" in md


def test_leak_scan_none_observed_this_round(tmp_path):
    run = tmp_path
    (run / "data").mkdir(parents=True)
    (run / "data" / "task_history.jsonl").write_text(
        json.dumps({"task_id": T_ALWAYS, "round": 1, "level": "1", "passed": True}), encoding="utf-8"
    )
    d = run / "R1" / "digests"
    d.mkdir(parents=True)
    (d / f"{T_ALWAYS}.md").write_text(
        "pattern: ALL_PASS\nstrategy: normal_tag\nfailure_mode: none\n", encoding="utf-8"
    )
    rep = fl.build_flip_ledger(run, d, 1)
    assert rep.leak_rows == []
    md = fl.render_flip_ledger(rep)
    assert "none observed this round" in md


def test_never_pass_section(tmp_path):
    run, d = _mk_run(tmp_path)
    rep = fl.build_flip_ledger(run, d, 4)
    assert len(rep.never_rows) == 1
    row = rep.never_rows[0]
    assert row["task_id"] == T_NEVER and row["n_obs"] == 4
    assert row["fm_raw"] == "(no digest)"
    md = fl.render_flip_ledger(rep)
    assert f"`{T_NEVER}`" in md


def test_history_missing_is_no_op_not_a_crash(tmp_path, caplog):
    d = tmp_path / "R1" / "digests"
    d.mkdir(parents=True)
    with caplog.at_level(logging.WARNING, logger="harnessx.ghx.flip_ledger"):
        rep = fl.build_flip_ledger(tmp_path, d, 1)
    assert not rep.has_data and rep.total_tasks == 0
    assert "task_history" in caplog.text


def test_seam_resolves_round_from_history_max_not_dir_name(tmp_path, monkeypatch):
    # R13/ digests, but task_history's own rounds only go up to 4 — the
    # round-alignment trap the module docstring documents.
    run, d = _mk_run(tmp_path, round_dir_name="R13")
    summary = run / "R13" / "summary.md"

    def fake_official(*, digests_dir, summary_path, cluster_path=None):
        Path(summary_path).write_text("# Aggregate\n", encoding="utf-8")
        return {"actionability": 1.0}

    monkeypatch.setattr(fl, "_ORIGINAL_AGGREGATE", fake_official)
    result = fl.aggregate_digests_with_flip_ledger(digests_dir=d, summary_path=summary)
    assert result == {"actionability": 1.0}

    out = run / "R13" / "graph_evidence" / "flip_ledger.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "history round 4" in text
    assert "history round 13" not in text


def test_seam_skips_write_when_history_missing(tmp_path, monkeypatch):
    d = tmp_path / "R1" / "digests"
    d.mkdir(parents=True)
    summary = tmp_path / "R1" / "summary.md"

    def fake_official(*, digests_dir, summary_path, cluster_path=None):
        Path(summary_path).write_text("# Aggregate\n", encoding="utf-8")
        return {"actionability": 1.0}

    monkeypatch.setattr(fl, "_ORIGINAL_AGGREGATE", fake_official)
    result = fl.aggregate_digests_with_flip_ledger(digests_dir=d, summary_path=summary)
    assert result == {"actionability": 1.0}
    assert not (tmp_path / "R1" / "graph_evidence" / "flip_ledger.md").exists()


def test_install_restores_and_flag_off_is_noop(monkeypatch):
    import harnessx.aegis.stages.preprocess as pp

    monkeypatch.delenv(fl.FLAG, raising=False)
    original = pp.aggregate_digests
    assert not fl.flip_ledger_enabled()
    # the exact conditional the launcher uses
    ctx = fl.install_flip_ledger() if fl.flip_ledger_enabled() else contextlib.nullcontext()
    with ctx:
        assert pp.aggregate_digests is original
    assert pp.aggregate_digests is original

    monkeypatch.setenv(fl.FLAG, "1")
    assert fl.flip_ledger_enabled()
    with fl.install_flip_ledger():
        assert pp.aggregate_digests is fl.aggregate_digests_with_flip_ledger
    assert pp.aggregate_digests is original
    assert fl._ORIGINAL_AGGREGATE is None


def test_guidance_stitches_flip_ledger_between_population_and_regression_diffs(tmp_path):
    from harnessx.ghx.guidance import _evolver_paths

    run = tmp_path / "run"
    ev = run / "R5" / "graph_evidence"
    ev.mkdir(parents=True)
    (ev / "facts.md").write_text("# facts", encoding="utf-8")
    (ev / "population.md").write_text("# population", encoding="utf-8")
    (ev / "flip_ledger.md").write_text("# flip", encoding="utf-8")
    (ev / "regression_diffs.md").write_text("# diffs", encoding="utf-8")

    paths = _evolver_paths(run, 5)
    map_path = ev / "map.md"
    assert str(map_path.resolve()) in paths
    text = map_path.read_text(encoding="utf-8")
    assert (
        text.index("stitched from population.md")
        < text.index("stitched from flip_ledger.md")
        < text.index("stitched from regression_diffs.md")
    )


def test_guidance_stitch_silently_skips_missing_flip_ledger(tmp_path):
    """Unchanged degrade behavior: no flip_ledger.md written -> just absent from map.md."""
    from harnessx.ghx.guidance import _evolver_paths

    run = tmp_path / "run"
    ev = run / "R5" / "graph_evidence"
    ev.mkdir(parents=True)
    (ev / "facts.md").write_text("# facts", encoding="utf-8")

    paths = _evolver_paths(run, 5)
    map_path = ev / "map.md"
    text = map_path.read_text(encoding="utf-8")
    assert "flip_ledger" not in text


def test_cli_out_file(tmp_path):
    run, d = _mk_run(tmp_path)
    out = tmp_path / "out.md"
    code = fl.main([str(run), str(d), "--history-round", "4", "--out", str(out)])
    assert code == 0
    assert out.exists()
    assert "Flip ledger" in out.read_text(encoding="utf-8")


def test_cli_no_data_returns_1(tmp_path, capsys):
    d = tmp_path / "R1" / "digests"
    d.mkdir(parents=True)
    code = fl.main([str(tmp_path), str(d), "--history-round", "1"])
    assert code == 1
    assert "no usable task_history" in capsys.readouterr().err
