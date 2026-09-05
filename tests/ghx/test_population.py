# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 P4 — motif population aggregation at the aggregate_digests seam."""
from __future__ import annotations

from pathlib import Path

from harnessx.ghx.population import (
    aggregate_digests_with_population,
    build_population,
    install_population,
    render_population,
    summary_section,
)

T1 = "aaaaaaaa-0000-0000-0000-000000000001"
T2 = "bbbbbbbb-0000-0000-0000-000000000002"
T3 = "cccccccc-0000-0000-0000-000000000003"
T4 = "dddddddd-0000-0000-0000-000000000004"


def _digest(pattern: str, motif_block: str | None) -> str:
    head = f"pattern: {pattern}\nfailure_mode: x\n\n## Trace Facts (Layer A — mechanical; do not rewrite)\n\nbody\n"
    if motif_block is None:
        return head + "\n## Pathology signals (Layer B — structured)\n\nnone\n"
    return (
        head
        + "\n### Mechanism signatures (deterministic motifs over U)\n\n"
        + motif_block
        + "\n\n## Pathology signals (Layer B — structured)\n\nnone\n"
    )


def _mk_round(tmp_path: Path) -> Path:
    d = tmp_path / "R5" / "digests"
    d.mkdir(parents=True)
    (d / f"{T1}.md").write_text(
        _digest(
            "ALL_FAIL",
            "**r0** — primary: `budget_no_commit`\n"
            "- `budget_no_commit` ×1 — exit=budget_exceeded after 20 steps\n"
            "- `retry_loop` ×2 — 2 run(s) of >=3 identical calls",
        ),
        encoding="utf-8",
    )
    (d / f"{T2}.md").write_text(
        _digest(
            "ALL_FAIL",
            "**r0** — primary: `ungrounded_commit`\n"
            "- `empty_consumed` ×2 — empty payloads reached the terminal model call\n"
            "- `ungrounded_commit` [search_only] ×1 — FINAL ANSWER with no ok non-snippet",
        ),
        encoding="utf-8",
    )
    (d / f"{T3}.md").write_text(
        _digest(
            "ALL_PASS",
            "**r0** — primary: `ungrounded_commit`\n"
            "- `ungrounded_commit` [search_only] ×1 — FINAL ANSWER with no ok non-snippet",
        ),
        encoding="utf-8",
    )
    (d / f"{T4}.md").write_text(_digest("ALL_PASS", None), encoding="utf-8")
    return d


def test_build_population_counts_tasks_not_hits(tmp_path):
    rep = build_population(_mk_round(tmp_path))
    assert rep.n_digests == 4 and rep.n_with_motifs == 3
    assert rep.failing_any == {"budget_no_commit": 1, "retry_loop": 1, "empty_consumed": 1, "ungrounded_commit": 1}
    assert rep.failing_primary == {"budget_no_commit": 1, "ungrounded_commit": 1}
    assert rep.m2_on_pass == [T3]
    assert rep.failing_tasks["budget_no_commit"] == [T1]


def test_render_and_summary(tmp_path):
    rep = build_population(_mk_round(tmp_path))
    md = render_population(rep)
    assert "| `budget_no_commit` | 1 | 1 |" in md
    assert f"`{T3}`" in md  # full ids, never truncated
    assert "Population noise" in md
    s = summary_section(rep)
    assert "## Motif populations" in s and "graph_evidence/population.md" in s


def test_no_motif_digests_is_honest_noop(tmp_path):
    d = tmp_path / "R5" / "digests"
    d.mkdir(parents=True)
    (d / f"{T1}.md").write_text(_digest("ALL_FAIL", None), encoding="utf-8")
    rep = build_population(d)
    assert not rep.has_data


def test_seam_writes_population_and_appends_summary(tmp_path):
    d = _mk_round(tmp_path)
    summary = tmp_path / "R5" / "summary.md"
    import harnessx.aegis.stages.preprocess as pp

    original = pp.aggregate_digests
    with install_population():
        assert pp.aggregate_digests is aggregate_digests_with_population
        result = pp.aggregate_digests(digests_dir=d, summary_path=summary)
    assert pp.aggregate_digests is original
    assert isinstance(result, dict) and "actionability" in result
    pop = tmp_path / "R5" / "graph_evidence" / "population.md"
    assert pop.exists() and "Motif populations" in pop.read_text(encoding="utf-8")
    assert "## Motif populations" in summary.read_text(encoding="utf-8")


def test_seam_noop_when_official_digests(tmp_path):
    d = tmp_path / "R5" / "digests"
    d.mkdir(parents=True)
    (d / f"{T1}.md").write_text(_digest("ALL_FAIL", None), encoding="utf-8")
    summary = tmp_path / "R5" / "summary.md"
    with install_population():
        import harnessx.aegis.stages.preprocess as pp

        pp.aggregate_digests(digests_dir=d, summary_path=summary)
    assert not (tmp_path / "R5" / "graph_evidence" / "population.md").exists()
    assert "Motif populations" not in summary.read_text(encoding="utf-8")
