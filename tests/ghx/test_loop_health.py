# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The sweep has to distinguish a lost ship from a refused one.

``decision.md`` is the Critic's raw output. A stage-4 gate can reject that
decision afterwards, and the round is then a correct ``no_op`` while decision.md
still reads ``decision_type: ship``. Keying the check on the doc made it call
two correctly-gated rounds a silent loss — L2_103x10 R1 and M15_smoke_L0 R1, both
IV-6 refusals reading ``decision cites unknown candidate``.

A monitoring tool that cries wolf on correct behaviour gets ignored, which costs
more than not having it. So the authority is the journal's RoundEntry — what the
orchestrator recorded — with ship_outcomes as the fallback for rounds the journal
never got to.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.loop_health import audit


def _round(run: Path, n: int, *, composed: bool, decision: str | None = None) -> None:
    d = run / f"R{n}" / "applied"
    d.mkdir(parents=True, exist_ok=True)
    if composed:
        (d / "merged.yaml").write_text("processors: []\n", encoding="utf-8")
    if decision:
        (run / f"R{n}" / "decision.md").write_text(
            f"---\nround: {n}\ndecision_type: {decision}\n---\n", encoding="utf-8"
        )


def _journal(run: Path, entries: list[dict]) -> None:
    body = "\n".join(
        f"# Round {e['round']}\n```json\n{json.dumps(e, indent=2)}\n```\n" for e in entries
    )
    (run / "journal.md").write_text(body, encoding="utf-8")


def _outcomes(run: Path, rows: list[dict]) -> None:
    (run / "data").mkdir(parents=True, exist_ok=True)
    (run / "data" / "ship_outcomes.json").write_text(json.dumps(rows), encoding="utf-8")


def _statuses(run: Path) -> dict[str, str]:
    return {c.channel: c.status for c in audit(run)}


def test_a_gate_refusing_the_critics_decision_is_not_a_lost_ship(tmp_path: Path):
    """L2_103x10 R1 and M15_smoke_L0 R1. decision.md says ship, the IV-6 gate
    refused it, the journal records no_op, nothing composed. Correct all round."""
    _round(tmp_path, 1, composed=False, decision="ship")
    _journal(
        tmp_path,
        [
            {
                "round": 1,
                "action": "no_op",
                "shipped_cids": [],
                "narrative": "decision_chain_broken:decision cites unknown candidate C-R1-01 (IV-6)",
            }
        ],
    )
    assert _statuses(tmp_path)["ships landed"] == "ok"


def test_a_recorded_ship_that_never_composed_is_still_caught(tmp_path: Path):
    """The journal says it shipped and there is no merged.yaml — the round ran
    the previous config while the ledger credited the ship."""
    _round(tmp_path, 1, composed=False, decision="ship")
    _round(tmp_path, 2, composed=True, decision="ship")
    _journal(
        tmp_path,
        [
            {"round": 1, "action": "ship", "shipped_cids": ["C-R1-01"]},
            {"round": 2, "action": "ship", "shipped_cids": ["C-R2-01"]},
        ],
    )
    assert _statuses(tmp_path)["ships landed"] == "BROKEN"


def test_a_round_the_journal_never_reached_falls_back_to_the_ledger(tmp_path: Path):
    """M14_L0_arm R3: two round=3 rows in ship_outcomes and no journal entry,
    because the campaign ended before the round was finalised. Without the
    fallback this round would be invisible, and it is exactly the one P-16
    marks unscoreable."""
    _round(tmp_path, 3, composed=False, decision="ship")
    _journal(tmp_path, [{"round": 2, "action": "ship", "shipped_cids": ["C-R2-01"]}])
    _round(tmp_path, 2, composed=True)
    _outcomes(
        tmp_path,
        [
            {"ship_id": "C-R2-01", "round": 2, "predicted_tasks": []},
            {"ship_id": "C-R3-01", "round": 3, "predicted_tasks": []},
        ],
    )
    # R3 is the last round, so it is the benign shape P-16 already handles.
    assert _statuses(tmp_path)["ships landed"] == "DEGRADED"


def test_an_empty_reputation_is_only_broken_when_something_shipped(tmp_path: Path):
    """M14_L2_arm's shape versus a smoke run that never shipped. Same empty
    file, opposite verdicts."""
    _round(tmp_path, 1, composed=True)
    _journal(tmp_path, [{"round": 1, "action": "ship", "shipped_cids": ["C-R1-01"]}])
    (tmp_path / "reputation.json").write_text(
        json.dumps({"prompt": [], "tools": [], "config": [], "processor": []}),
        encoding="utf-8",
    )
    assert _statuses(tmp_path)["reputation"] == "BROKEN"

    quiet = tmp_path / "quiet"
    (quiet / "R1").mkdir(parents=True)
    _journal(quiet, [{"round": 1, "action": "no_op", "shipped_cids": []}])
    assert _statuses(quiet)["reputation"] == "ok"


def test_a_stringified_list_bucket_key_is_caught(tmp_path: Path):
    """M14_L2_arm's scoreboard: str() on a list bucket yields a rollup key that
    never aggregates with a real bucket name."""
    (tmp_path / "data").mkdir(parents=True)
    (tmp_path / "data" / "scoreboard.json").write_text(
        json.dumps({"by_bucket": {"['tools']": {"ships": 1}}}), encoding="utf-8"
    )
    assert _statuses(tmp_path)["scoreboard buckets"] == "BROKEN"


def test_unresolvable_predicted_ids_are_caught(tmp_path: Path):
    """M14_L0_arm: 8-char ids against a history keyed on full UUIDs. Every
    prediction grades unknown and hit_rate reads a confident zero."""
    (tmp_path / "data").mkdir(parents=True)
    (tmp_path / "data" / "task_history.jsonl").write_text(
        json.dumps({"round": 1, "task_id": "33d8ea3b-6c6b-4ff1-803d-7e270dea8a57"}) + "\n",
        encoding="utf-8",
    )
    _outcomes(tmp_path, [{"ship_id": "C-R2-01", "round": 2, "predicted_tasks": ["33d8ea3b"]}])
    assert _statuses(tmp_path)["hit_rate"] == "BROKEN"
