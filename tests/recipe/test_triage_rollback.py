# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M27 T1.1 — the rollback gate reads the regression triage before reverting.

The full decision lives inline in ``run_pilot`` (a giant async function this
suite does not drive end-to-end — see ``tests/recipe/test_no_early_stop.py``
for the established source-inspection pattern this file also uses for the
wiring itself). What IS unit-testable in isolation:

* the flag readers (default off, same convention as every other GHX flag);
* ``_triage_downgrade_note`` — the pure decision the inline block defers to;
* the two new audit/journal side-effect helpers.
"""
from __future__ import annotations

import inspect
import json

from harnessx.ghx.regression_triage import Envelope, TriageResult
from recipe.gaia_evolver.run_meta_aegis import (
    _TRIAGE_MIN_HARD_REGRESSIONS,
    _append_triage_hold_audit,
    _append_triage_hold_journal,
    _noopstreak_fix_enabled,
    _triage_downgrade_note,
    _triage_rollback_enabled,
)


def _mk_triage(*, observed_hard: int, mean: float = 5.0, sd: float = 1.0, streaks: dict | None = None) -> TriageResult:
    return TriageResult(
        round_n=3,
        evolve_round_n=3,
        observed_hard=observed_hard,
        envelope=Envelope(mean=mean, sd=sd, n=5, source="run"),
        streaks=streaks or {},
    )


# ── flags ─────────────────────────────────────────────────────────────────────


def test_triage_rollback_enabled_default_off(monkeypatch):
    monkeypatch.delenv("HARNESSX_GHX_TRIAGE_ROLLBACK", raising=False)
    assert _triage_rollback_enabled() is False


def test_triage_rollback_enabled_on(monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_TRIAGE_ROLLBACK", "1")
    assert _triage_rollback_enabled() is True


def test_noopstreak_fix_enabled_default_off(monkeypatch):
    monkeypatch.delenv("HARNESSX_GHX_NOOPSTREAK_FIX", raising=False)
    assert _noopstreak_fix_enabled() is False


def test_noopstreak_fix_enabled_on(monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_NOOPSTREAK_FIX", "1")
    assert _noopstreak_fix_enabled() is True


# ── _triage_downgrade_note ──────────────────────────────────────────────────


def test_within_envelope_downgrades_even_with_many_eligible_regressions():
    """A within-envelope wave is what an unchanged config does on its own —
    it must downgrade regardless of how many regressions look stable."""
    triage = _mk_triage(observed_hard=5, mean=5.0, sd=1.0, streaks={f"t{i}": 5 for i in range(5)})
    assert triage.stat_verdict == "within-envelope"
    note = _triage_downgrade_note(triage)
    assert note is not None
    assert "within-envelope" in note


def test_excess_but_too_few_eligible_regressions_downgrades():
    triage = _mk_triage(observed_hard=8, mean=5.0, sd=1.0, streaks={"t0": 5, "t1": 1})
    assert triage.stat_verdict == "EXCESS"
    assert len(triage.counterfactual_eligible()) == 1 < _TRIAGE_MIN_HARD_REGRESSIONS
    note = _triage_downgrade_note(triage)
    assert note is not None
    assert "counterfactual_eligible=1" in note


def test_excess_and_enough_eligible_regressions_confirms_the_raw_rule():
    streaks = {f"t{i}": 4 for i in range(_TRIAGE_MIN_HARD_REGRESSIONS)}
    triage = _mk_triage(observed_hard=8, mean=5.0, sd=1.0, streaks=streaks)
    assert triage.stat_verdict == "EXCESS"
    assert len(triage.counterfactual_eligible()) == _TRIAGE_MIN_HARD_REGRESSIONS
    assert _triage_downgrade_note(triage) is None


def test_threshold_is_a_module_constant():
    assert isinstance(_TRIAGE_MIN_HARD_REGRESSIONS, int) and _TRIAGE_MIN_HARD_REGRESSIONS > 0


# ── side-effect helpers ──────────────────────────────────────────────────────


def test_append_triage_hold_audit_writes_expected_shape(tmp_path):
    _append_triage_hold_audit(
        tmp_path,
        round_idx=4,
        candidate_cids=["C-R4-01"],
        delta_rate=-0.06,
        delta_count=-4,
        reason="stat_verdict=within-envelope ...",
    )
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    assert entry["round"] == 4
    assert entry["kind"] == "triage_hold"
    assert entry["payload"]["candidate_cids"] == ["C-R4-01"]
    assert entry["payload"]["delta_count"] == -4


def test_append_triage_hold_journal_records_a_ship_not_a_rollback(tmp_path):
    from harnessx.aegis.data.journal import Journal

    _append_triage_hold_journal(
        tmp_path, round_idx=5, candidate_cids=["C-R5-01"], reason="stat_verdict=within-envelope",
    )
    entries = Journal(tmp_path / "journal.md").read_all()
    assert len(entries) == 1
    assert entries[0].action == "ship"  # the ship stands — not reverted
    assert entries[0].shipped_cids == ["C-R5-01"]
    assert "TRIAGE HOLD" in entries[0].narrative


# ── wiring (source-inspection, same pattern as test_no_early_stop.py) ──────


def test_flag_off_path_matches_the_original_raw_rule_exactly():
    """The vendored path (flag off) must be reachable with should_revert always
    True and triage_note always empty, so the rollback log message and
    _rollback_reason string are byte-identical to the pre-M27 code."""
    import recipe.gaia_evolver.run_meta_aegis as m

    src = inspect.getsource(m)
    # should_revert defaults True and is only ever set False inside the
    # triage-enabled branch — so flag off never reaches the downgrade path.
    assert "should_revert = True" in src
    assert "if _triage_rollback_enabled() and not triage_hold_used:" in src
    # the reason string only grows a suffix when triage_note is non-empty /
    # triage_hold_used is True — both stay falsy when the flag is off.
    assert '+ (f"; triage confirmed: {triage_note}" if triage_note else "")' in src
    assert '+ (" [second trip after a triage hold]" if triage_hold_used else "")' in src


def test_a_held_round_does_not_advance_the_validated_baseline():
    import recipe.gaia_evolver.run_meta_aegis as m

    src = inspect.getsource(m)
    assert "if not rollback_fired and not held_this_round:" in src
    assert "held_this_round = True" in src


def test_second_trip_after_a_hold_bypasses_the_triage_consult():
    """not triage_hold_used gates the triage import/consult — once True, the
    next trip's should_revert stays at its default True, obeying the raw
    rule unconditionally."""
    import recipe.gaia_evolver.run_meta_aegis as m

    src = inspect.getsource(m)
    assert "_triage_rollback_enabled() and not triage_hold_used" in src


def test_noopstreak_fix_compares_against_current_config_not_the_stale_file():
    import recipe.gaia_evolver.run_meta_aegis as m

    src = inspect.getsource(m)
    assert "if _noopstreak_fix_enabled():" in src
    assert "current_config.copy(tracer=round_journal).to_yaml_file(_baseline_path)" in src
    assert "baseline_bytes = round_config_path.read_bytes()" in src  # the flag-off else


def test_paired_gate_is_wired_into_the_same_rollback_site():
    """T1.3: read/report-only, wired alongside the T1.1 triage consult."""
    import recipe.gaia_evolver.run_meta_aegis as m

    src = inspect.getsource(m)
    assert "from harnessx.ghx.paired_gate import paired_gate_enabled" in src
    assert "predicted_tasks_for_round(RUN_DIR, round_idx, ship_ids=ship_ids)" in src
    assert "append_paired_gate_audit(RUN_DIR, round_idx, paired)" in src
