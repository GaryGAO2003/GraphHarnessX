# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Strategy population — tag canonicalization, stability column, seam chaining."""

from __future__ import annotations

import json
from pathlib import Path

import harnessx.ghx.strategy_population as sp


def _mk_run(tmp_path: Path) -> Path:
    """R4/digests with two spelling-variant pass strategies + one fail digest,
    and a task_history where exactly one task has a 3-round pass streak."""
    d = tmp_path / "R4" / "digests"
    d.mkdir(parents=True)
    (d / "aaaa.md").write_text(
        "pattern: ALL_PASS\nstrategy: Decompose-LII-Navigation\nfailure_mode: none\n", encoding="utf-8"
    )
    (d / "bbbb.md").write_text(
        "pattern: PASS\nstrategy: decompose_lii_navigation\nfailure_mode: none\n", encoding="utf-8"
    )
    (d / "cccc.md").write_text(
        "pattern: ALL_FAIL\nfailure_mode: budget_no_commit\n", encoding="utf-8"
    )
    hist = tmp_path / "data"
    hist.mkdir()
    rows = []
    for rd in (1, 2, 3):
        rows.append({"task_id": "aaaa", "round": rd, "passed_flags": [True]})
        rows.append({"task_id": "bbbb", "round": rd, "passed_flags": [rd == 3]})
    (hist / "task_history.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows), encoding="utf-8"
    )
    return d


def test_build_canonicalizes_and_counts(tmp_path: Path):
    d = _mk_run(tmp_path)
    rep = sp.build_strategy_population(d)
    assert rep.round_n == 4
    assert rep.pass_count == 2
    assert list(rep.tags) == ["decompose_lii_navigation"]  # two spellings, one key
    slot = rep.tags["decompose_lii_navigation"]
    assert sorted(slot["tasks"]) == ["aaaa", "bbbb"]
    assert slot["stable"] == 1  # aaaa has the 3-round streak; bbbb does not
    md = sp.render_strategy_population(rep)
    assert "| `decompose_lii_navigation` | 2 | 1 |" in md
    assert "Decompose-LII-Navigation" in md  # raw spelling preserved for audit


def test_seam_chains_and_appends_summary(tmp_path: Path, monkeypatch):
    d = _mk_run(tmp_path)
    summary = tmp_path / "R4" / "summary.md"
    calls = []

    def fake_official(*, digests_dir, summary_path, cluster_path=None):
        calls.append("official")
        Path(summary_path).write_text("# Aggregate\n", encoding="utf-8")
        return {"actionability": 1.0}

    monkeypatch.setattr(sp, "_ORIGINAL_AGGREGATE", fake_official)
    result = sp.aggregate_digests_with_strategy(digests_dir=d, summary_path=summary)
    assert calls == ["official"] and result["actionability"] == 1.0
    table = tmp_path / "R4" / "graph_evidence" / "strategy_population.md"
    assert table.exists()
    assert "Strategy populations" in summary.read_text(encoding="utf-8")


def test_install_restores():
    import harnessx.aegis.stages.preprocess as pp

    original = pp.aggregate_digests
    with sp.install_strategy_population():
        assert pp.aggregate_digests is sp.aggregate_digests_with_strategy
    assert pp.aggregate_digests is original
    assert sp._ORIGINAL_AGGREGATE is None
