# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M25 — the loop's memory of its own node edits.

facts.md told every reader that node edit history "is not yet recorded". The
node ids were on disk the whole time, in the per-candidate graph surface; the
three round ledgers said what became of each candidate; nothing joined them.
"""

from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.node_edit_history import (
    REJECTED,
    ROLLED_BACK,
    SHIPPED,
    UNKNOWN,
    collect_node_edits,
    render_node_edit_history,
)


def _surface(run: Path, round_n: int, cid: str, **fields) -> None:
    d = run / f"R{round_n}" / "graph_evidence" / "candidates"
    d.mkdir(parents=True, exist_ok=True)
    block = {
        "candidate_id": cid,
        "nodes_added": [],
        "nodes_removed": [],
        "nodes_mutated": [],
    }
    block.update(fields)
    (d / f"{cid}.md").write_text(
        f"# Graph mutation surface — {cid}\n\n## Machine-readable\n```json\n"
        + json.dumps(block, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )


def _ledgers(run: Path, ships=(), rejects=(), rolled_back=()) -> None:
    data = run / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "ship_outcomes.json").write_text(
        json.dumps([{"ship_id": c, "bucket": b, "round": r} for c, b, r in ships]), encoding="utf-8"
    )
    (data / "rejected_candidates.jsonl").write_text(
        "\n".join(json.dumps({"candidate_id": c, "bucket": b, "round": r}) for c, b, r in rejects),
        encoding="utf-8",
    )
    if rolled_back:
        (run / "audit.jsonl").write_text(
            json.dumps({"round": "2", "kind": "rollback",
                        "payload": {"rolled_back_cids": list(rolled_back)}}),
            encoding="utf-8",
        )


def test_history_joins_surfaces_with_the_three_ledgers(tmp_path: Path):
    run = tmp_path / "run"
    _surface(run, 1, "C-R1-01", nodes_added=["proc:py::_step_countdown"])
    _surface(run, 2, "C-R2-01", nodes_mutated=["proc:py::_step_countdown"])
    _surface(run, 3, "C-R3-01", nodes_added=["tool:SmartFetch"])
    _ledgers(
        run,
        ships=[("C-R1-01", "processor", 1), ("C-R2-01", "processor", 2), ("C-R3-01", "tools", 3)],
        rolled_back=["C-R2-01"],
    )

    hist = collect_node_edits(run, 4)
    countdown = hist["proc:py::_step_countdown"]
    assert [(e.round_n, e.kind, e.outcome) for e in countdown] == [
        (1, "added", SHIPPED),
        (2, "mutated", ROLLED_BACK),
    ]
    assert hist["tool:SmartFetch"][0].outcome == SHIPPED
    assert hist["tool:SmartFetch"][0].bucket == "tools"


def test_rounds_at_or_after_the_current_one_are_not_history_yet(tmp_path: Path):
    run = tmp_path / "run"
    _surface(run, 1, "C-R1-01", nodes_added=["tool:A"])
    _surface(run, 5, "C-R5-01", nodes_added=["tool:B"])
    _ledgers(run, ships=[("C-R1-01", "tools", 1)])
    hist = collect_node_edits(run, 5)
    assert set(hist) == {"tool:A"}


def test_an_outcome_with_no_ledger_row_is_unknown_not_rejected(tmp_path: Path):
    """Absence of a ledger row is absence of knowledge. Reporting it as a
    rejection would tell the next round an idea was refused when nobody knows."""
    run = tmp_path / "run"
    _surface(run, 1, "C-R1-09", nodes_added=["tool:A"])
    _ledgers(run, ships=[], rejects=[])
    assert collect_node_edits(run, 2)["tool:A"][0].outcome == UNKNOWN


def test_rejection_is_recorded_and_a_ship_is_never_overwritten_by_one(tmp_path: Path):
    run = tmp_path / "run"
    _surface(run, 1, "C-R1-01", nodes_added=["tool:A"])
    _surface(run, 1, "C-R1-02", nodes_added=["tool:B"])
    _ledgers(run, ships=[("C-R1-01", "tools", 1)], rejects=[("C-R1-02", "tools", 1), ("C-R1-01", "tools", 1)])
    hist = collect_node_edits(run, 2)
    assert hist["tool:A"][0].outcome == SHIPPED
    assert hist["tool:B"][0].outcome == REJECTED


def test_render_puts_lift_table_nodes_first_and_says_empty_means_untried(tmp_path: Path):
    assert "nothing tried yet" in "\n".join(render_node_edit_history({}))
    run = tmp_path / "run"
    _surface(run, 1, "C-R1-01", nodes_added=["tool:Zeta"])
    _surface(run, 1, "C-R1-02", nodes_added=["tool:Alpha"])
    _ledgers(run, ships=[("C-R1-01", "tools", 1), ("C-R1-02", "tools", 1)])
    text = "\n".join(render_node_edit_history(collect_node_edits(run, 2), priority=["tool:Zeta"]))
    assert text.index("tool:Zeta") < text.index("tool:Alpha")


def test_a_node_touched_by_almost_every_candidate_is_flagged_as_an_artifact(tmp_path: Path):
    """Live on M25: `proc:llm_judge_processor` shows a params diff in all fifteen
    candidates, whatever bucket they were in — the shape of config serialisation,
    not of a targeted edit. Left in the table (it is what the surfaces say) but
    named, so fifteen rows of noise do not read as fifteen attempts."""
    run = tmp_path / "run"
    for i in range(6):
        _surface(run, i + 1, f"C-R{i+1}-01", nodes_mutated=["proc:llm_judge"], nodes_added=[f"tool:T{i}"])
    _ledgers(run, ships=[(f"C-R{i+1}-01", "processor", i + 1) for i in range(6)])
    text = "\n".join(render_node_edit_history(collect_node_edits(run, 9)))
    assert "`proc:llm_judge`" in text.split("|---|")[-1]
    assert "config-serialisation artifact" in text
    assert "tool:T0" not in text.split("Touched by")[-1]
