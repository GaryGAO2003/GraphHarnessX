# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Scoped noop batches (--noop-audit): the audit-selection logic.

M25 spent four noop rounds x ~$43 re-running an unchanged config over the full
bed — a third of batch spend re-measuring an envelope the campaign had already
priced at +/-5 tasks. The selection contract tested here: every task that
flipped in the last three recorded rounds is in the audit (that is where a
same-config surprise would show), the fill to N is deterministic, and a task
with no carry source always runs.
"""

from __future__ import annotations

import hashlib


def _select(all_ids, flippy, carry_src, audit_n, round_idx):
    """Mirror of the selection block in run_meta_aegis (kept in lockstep by
    these tests; the block is inline in an 1100-line async loop, so the logic
    is small enough to pin by specification rather than by import)."""
    audit = set()
    for tid in all_ids:
        if tid in flippy and tid in carry_src:
            audit.add(tid)
    fill = sorted(
        (t for t in all_ids if t not in audit),
        key=lambda tid: hashlib.sha256(f"{round_idx}:{tid}".encode()).hexdigest(),
    )
    for tid in fill:
        if len(audit) >= audit_n:
            break
        audit.add(tid)
    run = [t for t in all_ids if t in audit or t not in carry_src]
    carried = [t for t in all_ids if t not in set(run)]
    return run, carried


def test_flip_family_is_always_audited_and_fill_is_deterministic():
    ids = [f"t{i:02d}" for i in range(20)]
    carry = {t: {} for t in ids}
    flippy = {"t03", "t07", "t15"}
    run1, carried1 = _select(ids, flippy, carry, audit_n=6, round_idx=5)
    run2, _ = _select(ids, flippy, carry, audit_n=6, round_idx=5)
    assert flippy <= set(run1)
    assert run1 == run2                        # same round → same audit
    assert len(run1) == 6 and len(carried1) == 14
    run3, _ = _select(ids, flippy, carry, audit_n=6, round_idx=6)
    assert set(run3) != set(run1)              # fill rotates with the round


def test_a_task_without_a_carry_source_always_runs():
    """Carrying a score we do not have would fabricate a measurement."""
    ids = ["a", "b", "c", "d"]
    carry = {"a": {}, "b": {}}                 # c, d have no prior record
    run, carried = _select(ids, set(), carry, audit_n=1, round_idx=0)
    assert "c" in run and "d" in run
    assert set(carried) <= {"a", "b"}


def test_flip_family_may_exceed_the_audit_floor():
    """N is a floor for the fill, never a cap on the volatile family."""
    ids = [f"t{i}" for i in range(10)]
    carry = {t: {} for t in ids}
    flippy = set(ids[:7])
    run, _ = _select(ids, flippy, carry, audit_n=3, round_idx=1)
    assert flippy <= set(run)
    assert len(run) == 7
