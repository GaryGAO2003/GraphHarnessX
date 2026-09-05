# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""P-23 — whether a rejected idea came back, and whether anyone can tell.

Rejection is usually "not now" — wrong bucket, thin evidence, bad timing —
rather than "never". backfill_rejected_revivals exists to answer whether
archived ideas return and whether the second attempt works, and it was dead
twice over: it scanned R<n>/briefs/B-R<n>-NN.md for `lead_pointer: archive:<cid>`
from a dispatch model that had been retired (zero briefs directories and zero
B-R*.md files anywhere in the corpus), and nothing ever called it.

The live signal is the candidate manifest's `iterates_from`. M16_L0_ghx0's
R3/C-R3-02 declares `iterates_from: C-R2-03`, and C-R2-03 sits in the archive
as rejected — one revival the old scan would have missed forever.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.aegis.data import ledger


def _rejected(run: Path, cids: list[str], round_n: int = 2) -> None:
    ledger.append_rejected_candidates(
        run, round_n,
        [{"candidate_id": c, "bucket": "tools", "predicted_tasks": [],
          "rejection_text_excerpt": "thin evidence"} for c in cids],
    )


def _candidate(run: Path, round_n: int, cid: str, iterates_from: str | None = None) -> None:
    d = run / f"R{round_n}" / "candidates"
    d.mkdir(parents=True, exist_ok=True)
    fm = f"candidate_id: {cid}\nbucket: tools\n"
    if iterates_from:
        fm += f"iterates_from: {iterates_from}\n"
    (d / f"{cid}.md").write_text(f"---\n{fm}---\n\nbody\n", encoding="utf-8")


def _rows(run: Path) -> dict:
    p = ledger.data_dir(run) / "rejected_candidates.jsonl"
    return {json.loads(l)["candidate_id"]: json.loads(l)
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def test_a_later_candidate_iterating_from_a_rejection_is_recorded(tmp_path: Path):
    """M16_L0_ghx0's shape."""
    _rejected(tmp_path, ["C-R2-03"])
    _candidate(tmp_path, 3, "C-R3-02", iterates_from="C-R2-03")
    ledger.backfill_rejected_revivals(tmp_path)
    assert _rows(tmp_path)["C-R2-03"]["revived_as"] == [
        {"round": 3, "candidate_id": "C-R3-02"}
    ]


def test_iterating_from_something_that_was_not_rejected_is_not_a_revival(tmp_path: Path):
    """Most iterates_from links point at a candidate that shipped. Building on a
    success is ordinary progress; building on a rejection is the thing worth
    counting."""
    _rejected(tmp_path, ["C-R2-03"])
    _candidate(tmp_path, 3, "C-R3-01", iterates_from="C-R2-01")  # shipped, not rejected
    ledger.backfill_rejected_revivals(tmp_path)
    assert _rows(tmp_path)["C-R2-03"].get("revived_as") in (None, [])


def test_two_later_candidates_reviving_the_same_rejection_both_count(tmp_path: Path):
    _rejected(tmp_path, ["C-R2-03"])
    _candidate(tmp_path, 3, "C-R3-02", iterates_from="C-R2-03")
    _candidate(tmp_path, 4, "C-R4-01", iterates_from="C-R2-03")
    ledger.backfill_rejected_revivals(tmp_path)
    got = _rows(tmp_path)["C-R2-03"]["revived_as"]
    assert {e["round"] for e in got} == {3, 4}


def test_running_twice_changes_nothing(tmp_path: Path):
    """Called once per round, so it re-reads the same links every time."""
    _rejected(tmp_path, ["C-R2-03"])
    _candidate(tmp_path, 3, "C-R3-02", iterates_from="C-R2-03")
    ledger.backfill_rejected_revivals(tmp_path)
    first = (ledger.data_dir(tmp_path) / "rejected_candidates.jsonl").read_bytes()
    ledger.backfill_rejected_revivals(tmp_path)
    assert (ledger.data_dir(tmp_path) / "rejected_candidates.jsonl").read_bytes() == first


def test_the_retired_briefs_layout_is_gone_from_the_signature(tmp_path: Path):
    """all_briefs_dirs named a directory the system stopped producing. Keeping
    the parameter would keep the claim that briefs exist."""
    import inspect

    params = inspect.signature(ledger.backfill_rejected_revivals).parameters
    assert list(params) == ["run_root"]
    assert not hasattr(ledger, "_LEAD_ARCHIVE_RE"), "the retired pointer regex should go too"


def test_the_orchestrator_actually_calls_it():
    """The other half of the bug: the function was correct-ish and never ran."""
    import inspect

    from harnessx.aegis import orchestrator as _orch

    src = inspect.getsource(_orch.AegisOrchestrator.run_round)
    assert "backfill_rejected_revivals(" in src
    assert src.index("append_rejected_candidates(") < src.index("backfill_rejected_revivals("), (
        "this round's own rejections must be in the set before matching against it"
    )
