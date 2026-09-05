# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""P-21 — a rollback has to land where the Planner reads.

``RoundEntry.action`` has declared ``"ship" | "rollback" | "no_op"`` since the
journal was written, and across seven runs and 47 entries the middle value was
never once written: ship 32, no_op 15, rollback 0. M13_pro_meta_103x3 R3 really
did roll back — Δ=-7 tasks, reverting C-R3-04 and C-R3-02 — and it went to the
console and to audit.jsonl, which no agent reads. The Planner reads the journal
and reputation, so the strongest negative signal the system produces reached it
only as an anonymous miss in a bucket.
"""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.aegis.data.journal import Journal
from recipe.gaia_evolver.run_meta_aegis import _append_rollback_journal


def _entries(run_dir: Path):
    return Journal(run_dir / "journal.md").read_all()


def test_a_rollback_becomes_a_journal_entry(tmp_path: Path):
    _append_rollback_journal(
        tmp_path,
        round_idx=3,
        rolled_back_cids=["C-R3-04", "C-R3-02"],
        delta_count=-7,
        reason="Δrate=-0.068 ≤ -0.05 AND Δcount=-7 ≤ -3 (vs last_validated R at 69 passed)",
    )
    got = _entries(tmp_path)
    assert len(got) == 1
    e = got[0]
    assert e.action == "rollback", "the value the schema reserved and nothing wrote"
    assert e.round == 3


def test_the_entry_names_what_was_reverted_and_why(tmp_path: Path):
    """A Planner that reads "rollback" and nothing else cannot act on it."""
    _append_rollback_journal(
        tmp_path,
        round_idx=3,
        rolled_back_cids=["C-R3-04", "C-R3-02"],
        delta_count=-7,
        reason="Δrate=-0.068 ≤ -0.05 AND Δcount=-7 ≤ -3 (vs last_validated R at 69 passed)",
    )
    n = _entries(tmp_path)[0].narrative
    assert "C-R3-04" in n and "C-R3-02" in n, "which ships went back"
    assert "-7 tasks" in n, "how bad it was"
    assert "-0.05" in n, "the threshold that fired, verbatim"
    assert "last validated config" in n, "what the next round actually starts from"


def test_a_reverted_ship_is_not_recorded_as_shipped(tmp_path: Path):
    """shipped_cids is what downstream reads as "this round shipped". Leaving the
    reverted ids there would assert the opposite of what happened."""
    _append_rollback_journal(
        tmp_path, round_idx=3, rolled_back_cids=["C-R3-04"], delta_count=-7, reason="x"
    )
    e = _entries(tmp_path)[0]
    assert e.shipped_cids == []
    assert e.shipped_cid is None


def test_a_broken_journal_does_not_kill_the_campaign(tmp_path: Path, caplog):
    """Same contract as the audit sibling: this is bookkeeping, and a rollback
    round is already a bad round without also losing the run."""
    import logging

    blocked = tmp_path / "journal.md"
    blocked.mkdir()  # a directory where the file should be
    with caplog.at_level(logging.WARNING):
        _append_rollback_journal(
            tmp_path, round_idx=3, rolled_back_cids=["C-R3-04"], delta_count=-7, reason="x"
        )
    assert "rollback journal append failed" in caplog.text


def test_the_rollback_branch_writes_both_records():
    """audit.jsonl for post-hoc inspection, journal.md for the Planner. The bug
    was having only the first, so the pairing is what this pins."""
    import inspect

    from recipe.gaia_evolver import run_meta_aegis

    src = inspect.getsource(run_meta_aegis)
    branch = src[src.index("ROLLBACK — post-ship regression") :][:2500]
    assert "_append_rollback_audit(" in branch
    assert "_append_rollback_journal(" in branch, (
        "the journal is the half the Planner can read"
    )
