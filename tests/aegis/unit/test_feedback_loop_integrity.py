# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""P-15 — the two ways M14's arms lost their feedback loop without saying so.

Both arms of the M14 comparison finished a whole campaign with a broken channel
into the Planner, each broken in a different place, and neither logged a thing:

  M14_L2_arm  every candidate declared ``bucket: [tools]``. The structure gate
              accepts a list (v0.9.3 cross-bucket bundle); ``reputation.record``
              used it as a dict key, raised TypeError, and landed in an
              ``except Exception: pass``. reputation.json stayed empty in all
              four buckets for four rounds while tools shipped twice.

  M14_L0_arm  the Evolver wrote 8-char truncated task ids. The backfill matches
              exactly, so all 16 predictions across two ships graded ``unknown``
              and hit_rate read 0/13 and 0/3 — numbers the next Planner then
              reasoned from.

These pin the real shapes, not invented ones.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from harnessx.aegis.data import ledger
from harnessx.aegis.data.regressions import render_regressions_md
from harnessx.aegis.data.reputation import BUCKETS, Reputation
from harnessx.aegis.gates.structure import _normalize_bucket
from harnessx.aegis.orchestrator import ShipNotLandedError, _build_shipped_entries

# The ids that actually appeared in M14_L0_arm's ship_outcomes.json, and the
# task they were truncations of.
_FULL = "33d8ea3b-6c6b-4ff1-803d-7e270dea8a57"
_TRUNC = "33d8ea3b"


# ---------------------------------------------------------------------------
# (a) bucket: the gate normalises, the consumers must too
# ---------------------------------------------------------------------------


def test_a_list_bucket_is_what_the_gate_hands_downstream():
    """Not a malformed manifest — a supported one. That is why it slipped."""
    assert _normalize_bucket(["tools"]) == ["tools"]
    assert _normalize_bucket("tools") == ["tools"]
    assert _normalize_bucket(["prompt", "config"]) == ["prompt", "config"]


def test_reputation_refuses_an_unusable_bucket_instead_of_raising(caplog):
    """The TypeError is what fed the swallowing except. A refusal plus a warning
    keeps the round alive and keeps the loss visible."""
    rep = Reputation(window=5)
    with caplog.at_level(logging.WARNING):
        rep.record(["tools"], hit=True)  # type: ignore[arg-type]
    assert rep.to_dict()["tools"] == []
    assert "refusing to record bucket" in caplog.text


def test_reputation_refuses_a_key_to_dict_would_silently_drop(caplog):
    """``to_dict`` only exports BUCKETS, so ``"['tools']"`` would look recorded
    all round and vanish at save time — the second, independent loss path."""
    rep = Reputation(window=5)
    with caplog.at_level(logging.WARNING):
        rep.record("['tools']", hit=True)
    assert all(not v for v in rep.to_dict().values())
    assert "refusing to record bucket" in caplog.text


def test_a_canonical_bucket_still_records():
    rep = Reputation(window=5)
    rep.record("tools", hit=True)
    rep.record("tools", hit=False)
    assert rep.to_dict()["tools"] == [True, False]
    assert set(rep.to_dict()) == set(BUCKETS)


def test_a_cross_bucket_bundle_credits_every_bucket_it_declared():
    """One ship, two buckets — the call site expands, so both windows move.
    This is the behaviour a list bucket was introduced for in the first place."""
    rep = Reputation(window=5)
    for b in _normalize_bucket(["tools", "processor"]):
        rep.record(b, hit=True)
    d = rep.to_dict()
    assert d["tools"] == [True] and d["processor"] == [True]
    assert d["prompt"] == [] and d["config"] == []


# ---------------------------------------------------------------------------
# (b) predicted_tasks: free text against an exact match
# ---------------------------------------------------------------------------


def _history(run_root: Path, ids: list[str], rounds: int = 3) -> None:
    for r in range(rounds):
        ledger.append_task_history(
            run_root,
            [{"round": r, "task_id": t, "passed_flags": [False]} for t in ids],
        )


def test_a_unique_prefix_resolves_to_the_full_id(tmp_path: Path, caplog):
    _history(tmp_path, [_FULL, "b" * 36])
    with caplog.at_level(logging.WARNING):
        out = ledger.resolve_task_ids(tmp_path, [_TRUNC])
    assert out == [_FULL]
    assert "expanded 1 abbreviated task id" in caplog.text


def test_an_id_matching_nothing_is_kept_but_named(tmp_path: Path, caplog):
    """Keeping it preserves the count in ``X/N``; the warning is what stops it
    from being read as a real zero."""
    _history(tmp_path, [_FULL])
    with caplog.at_level(logging.WARNING):
        out = ledger.resolve_task_ids(tmp_path, ["deadbeef"])
    assert out == ["deadbeef"]
    assert "match no task in history" in caplog.text
    assert "deadbeef" in caplog.text


def test_an_ambiguous_prefix_is_not_guessed(tmp_path: Path, caplog):
    _history(tmp_path, ["ab-1", "ab-2"])
    with caplog.at_level(logging.WARNING):
        out = ledger.resolve_task_ids(tmp_path, ["ab"])
    assert out == ["ab"], "two candidates is not a resolution"
    assert "2 matches" in caplog.text


def test_exact_ids_pass_through_without_noise(tmp_path: Path, caplog):
    _history(tmp_path, [_FULL])
    with caplog.at_level(logging.WARNING):
        assert ledger.resolve_task_ids(tmp_path, [_FULL]) == [_FULL]
    assert caplog.text == ""


def test_an_empty_history_leaves_ids_alone(tmp_path: Path):
    """Round 0 records a ship before any task row exists; resolving against an
    empty universe must not rewrite or warn."""
    assert ledger.resolve_task_ids(tmp_path, [_TRUNC]) == [_TRUNC]


def test_the_m14_l0_failure_now_produces_a_real_hit_rate(tmp_path: Path):
    """End to end on the actual shape: a ship predicting truncated ids, one of
    which then flips ALL_FAIL -> ALL_PASS. Before P-15b this scored 0/2 with
    both tasks graded ``unknown``."""
    other = "56137764-1111-2222-3333-444455556666"
    ledger.append_task_history(
        tmp_path,
        [
            {"round": 1, "task_id": _FULL, "passed_flags": [False]},
            {"round": 1, "task_id": other, "passed_flags": [False]},
        ],
    )
    ledger.record_ship_outcome(
        tmp_path,
        round_n=2,
        shipped_cid="C-R2-01",
        bucket="tools",
        predicted_tasks=[_TRUNC, "56137764"],  # what the Evolver wrote
        rejected_sibling_cids=[],
    )
    ledger.append_task_history(
        tmp_path,
        [
            {"round": 2, "task_id": _FULL, "passed_flags": [True]},
            {"round": 2, "task_id": other, "passed_flags": [False]},
        ],
    )
    ledger.backfill_ship_outcomes(tmp_path)

    entry = json.loads(
        (ledger.data_dir(tmp_path) / "ship_outcomes.json").read_text(encoding="utf-8")
    )[0]
    assert entry["predicted_tasks"] == [_FULL, other], "stored canonical, not as typed"
    assert entry["hit_rate"] == "1/2"
    assert entry["flipped_to_pass_in_ship_round"] == [_FULL]
    assert entry["predicted_tasks_status_latest"] == {
        _FULL: "passing",
        other: "still_failing",
    }
    assert "unknown" not in entry["predicted_tasks_status_latest"].values()


def test_a_row_written_before_the_fix_heals_on_the_next_backfill(tmp_path: Path):
    """M14's ship_outcomes.json already holds truncated ids. The read side
    resolves too, so those runs report the truth the next time they are read."""
    ledger.append_task_history(
        tmp_path, [{"round": 1, "task_id": _FULL, "passed_flags": [False]}]
    )
    path = ledger.data_dir(tmp_path) / "ship_outcomes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([{"ship_id": "C-R2-01", "round": 2, "predicted_tasks": [_TRUNC]}]),
        encoding="utf-8",
    )
    ledger.append_task_history(
        tmp_path, [{"round": 2, "task_id": _FULL, "passed_flags": [True]}]
    )
    ledger.backfill_ship_outcomes(tmp_path)
    entry = json.loads(path.read_text(encoding="utf-8"))[0]
    assert entry["hit_rate"] == "1/1"
    assert entry["predicted_tasks"] == [_FULL]


def test_the_watchlist_shows_ids_an_agent_can_quote_back():
    """It rendered ``task_id[:8]``, and an agent that copies what it reads then
    writes an id the ledger cannot match."""
    md = render_regressions_md(
        round_n=2,
        regressions=[
            {
                "task_id": _FULL,
                "prev_state": "ALL_PASS",
                "curr_state": "ALL_FAIL",
                "prev_flags": [True],
                "curr_flags": [False],
                "grade": "regressed_hard",
            },
        ],
    )
    summary = next(ln for ln in md.splitlines() if ln.startswith("- **regressed_hard**"))
    assert _FULL in summary
    assert _FULL in md
    assert f"`{_TRUNC}`" not in md


# ---------------------------------------------------------------------------
# (c) a ship that was accepted but never composed
# ---------------------------------------------------------------------------


def _round_that_ran(run_root: Path, n: int, *, composed: bool) -> None:
    d = run_root / f"R{n}" / "applied"
    d.mkdir(parents=True, exist_ok=True)
    if composed:
        (d / "merged.yaml").write_text("processors: []\n", encoding="utf-8")


def test_a_ship_that_never_composed_is_left_unscored(tmp_path: Path, caplog):
    """M14's last round, exactly: `decision_type: ship`, two candidates accepted,
    no merged.yaml, and R3/config.yaml pointing only at R2's applied dirs. The
    round's rollouts still ran — on R2's config — so R2-vs-R3 measures a
    same-config repeat. Scored anyway those two ships read 2/2 and 4/4, a
    flawless record made of noise, and the read-side healing added for P-15b is
    what would have surfaced it to the next Planner.
    """
    a, b = "aaaa1111-" + "0" * 27, "bbbb2222-" + "0" * 27
    for r, flags in ((2, [False]), (3, [True])):
        ledger.append_task_history(
            tmp_path,
            [{"round": r, "task_id": t, "passed_flags": flags} for t in (a, b)],
        )
    _round_that_ran(tmp_path, 2, composed=True)
    _round_that_ran(tmp_path, 3, composed=False)

    path = ledger.data_dir(tmp_path) / "ship_outcomes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([{"ship_id": "C-R3-01", "round": 3, "predicted_tasks": [a, b]}]),
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING):
        ledger.backfill_ship_outcomes(tmp_path)

    entry = json.loads(path.read_text(encoding="utf-8"))[0]
    assert entry["hit_rate"] is None, "both tasks flipped, but not because of this ship"
    assert "never composed" in entry["not_scoreable"]
    assert "accepted but never composed" in caplog.text


def test_a_ship_that_did_compose_is_scored_normally(tmp_path: Path):
    """The same data one round earlier, where merged.yaml is present."""
    a = "aaaa1111-" + "0" * 27
    ledger.append_task_history(tmp_path, [{"round": 1, "task_id": a, "passed_flags": [False]}])
    ledger.append_task_history(tmp_path, [{"round": 2, "task_id": a, "passed_flags": [True]}])
    _round_that_ran(tmp_path, 2, composed=True)

    path = ledger.data_dir(tmp_path) / "ship_outcomes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([{"ship_id": "C-R2-01", "round": 2, "predicted_tasks": [a]}]),
        encoding="utf-8",
    )
    ledger.backfill_ship_outcomes(tmp_path)
    entry = json.loads(path.read_text(encoding="utf-8"))[0]
    assert entry["hit_rate"] == "1/1"
    assert "not_scoreable" not in entry


def test_a_run_root_without_an_applied_dir_is_not_judged(tmp_path: Path):
    """No applied/ directory at all says nothing about whether compose ran, and
    absence of evidence must not become evidence of a dropped ship."""
    a = "aaaa1111-" + "0" * 27
    ledger.append_task_history(tmp_path, [{"round": 1, "task_id": a, "passed_flags": [False]}])
    ledger.append_task_history(tmp_path, [{"round": 2, "task_id": a, "passed_flags": [True]}])
    ledger.record_ship_outcome(
        tmp_path,
        round_n=2,
        shipped_cid="C-R2-01",
        bucket="tools",
        predicted_tasks=[a],
        rejected_sibling_cids=[],
    )
    ledger.backfill_ship_outcomes(tmp_path)
    entry = json.loads(
        (ledger.data_dir(tmp_path) / "ship_outcomes.json").read_text(encoding="utf-8")
    )[0]
    assert entry["hit_rate"] == "1/1"


# ---------------------------------------------------------------------------
# (d) P-17 — a ship dropped before compose is even called
# ---------------------------------------------------------------------------


def _candidate(round_dir: Path, cid: str) -> None:
    d = round_dir / "applied" / cid
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.yaml").write_text("processors: []\n", encoding="utf-8")


def test_a_ship_with_no_applied_config_stops_the_round(tmp_path: Path):
    """L2_103x10 R1's shape. decision.md ranked two candidates and neither
    reached compose, so no merged.yaml was written, the assertion that guards
    compose never ran, and ten rounds built on the broken chain."""
    with pytest.raises(ShipNotLandedError) as e:
        _build_shipped_entries(
            round_dir=tmp_path,
            round_n=1,
            shipped_cids=["C-R1-01", "C-R1-02"],
            manifests_by_cid={"C-R1-01": {"bucket": "config"}, "C-R1-02": {"bucket": "tools"}},
        )
    assert "2 never reached compose" in str(e.value)
    assert "no applied/config.yaml" in str(e.value)


def test_a_ship_with_an_empty_bucket_stops_the_round(tmp_path: Path):
    """The other half of the filter. A bucket-less candidate has nothing for
    compose to dispatch on, so it lands nowhere."""
    _candidate(tmp_path, "C-R2-01")
    with pytest.raises(ShipNotLandedError, match="empty bucket"):
        _build_shipped_entries(
            round_dir=tmp_path,
            round_n=2,
            shipped_cids=["C-R2-01"],
            manifests_by_cid={"C-R2-01": {}},
        )


def test_one_good_ship_does_not_excuse_a_dropped_sibling(tmp_path: Path):
    """The nastier case: merged.yaml IS written and DOES differ from base, so
    _assert_merged_differs_from_base passes and the missing candidate is
    invisible. Only a check on the filter itself catches a partial loss."""
    _candidate(tmp_path, "C-R2-01")
    with pytest.raises(ShipNotLandedError) as e:
        _build_shipped_entries(
            round_dir=tmp_path,
            round_n=2,
            shipped_cids=["C-R2-01", "C-R2-02"],
            manifests_by_cid={"C-R2-01": {"bucket": "tools"}, "C-R2-02": {"bucket": "prompt"}},
        )
    assert "1 never reached compose" in str(e.value)
    assert "C-R2-02" in str(e.value) and "C-R2-01 (" not in str(e.value)


def test_a_cross_bucket_bundle_reaches_compose_as_a_list(tmp_path: Path):
    """str() on the list is what produced "['prompt', 'processor']" and made
    compose skip every applier — the list must survive to dispatch."""
    _candidate(tmp_path, "C-R2-01")
    entries = _build_shipped_entries(
        round_dir=tmp_path,
        round_n=2,
        shipped_cids=["C-R2-01"],
        manifests_by_cid={"C-R2-01": {"bucket": ["prompt", "processor"]}},
    )
    assert entries == [
        ("C-R2-01", ["prompt", "processor"], tmp_path / "applied" / "C-R2-01" / "config.yaml")
    ]


def test_a_healthy_round_is_unchanged(tmp_path: Path):
    for cid in ("C-R2-01", "C-R2-02"):
        _candidate(tmp_path, cid)
    entries = _build_shipped_entries(
        round_dir=tmp_path,
        round_n=2,
        shipped_cids=["C-R2-01", "C-R2-02"],
        manifests_by_cid={"C-R2-01": {"bucket": "tools"}, "C-R2-02": {"bucket": "prompt"}},
    )
    assert [c for c, _, _ in entries] == ["C-R2-01", "C-R2-02"]


# ---------------------------------------------------------------------------
# (e) P-18 — compose runs before anything is recorded
# ---------------------------------------------------------------------------


def _round_with_candidate(round_dir: Path, cid: str, cfg: str) -> None:
    d = round_dir / "applied" / cid
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.yaml").write_text(cfg, encoding="utf-8")


def test_only_what_lands_is_returned_as_shipped(tmp_path: Path):
    """The ordering is the point. Recording ran before compose, so a candidate
    compose could not express was already in reputation, the scoreboard and
    ship_outcomes by the time it was dropped — M15_smoke_L2 R1 recorded three
    ships for a round that composed none of them.

    _compose_shipped now runs first and hands back only what landed.
    """
    from unittest.mock import MagicMock

    from harnessx.aegis.orchestrator import AegisOrchestrator

    base = "processors: []\n"
    (tmp_path / "config.yaml").write_text(base, encoding="utf-8")
    rd = tmp_path / "R1"
    proc = "harnessx.processors.control.step_countdown.StepCountdownProcessor"
    # C-R1-01 declares config while adding a processor — P-9 refuses it.
    _round_with_candidate(rd, "C-R1-01", f"processors:\n  - _target_: {proc}\n")
    _round_with_candidate(rd, "C-R1-02", "processors:\n  - _target_: X.Fine\n")

    orch = AegisOrchestrator(run_dir=tmp_path, num_evolvers=1, model_config=MagicMock())
    merged, landed, _rejected = orch._compose_shipped(
        round_n=1,
        round_dir=rd,
        current_config_path=tmp_path / "config.yaml",
        shipped_cids=["C-R1-01", "C-R1-02"],
        manifests_by_cid={
            "C-R1-01": {"bucket": "config"},
            "C-R1-02": {"bucket": "processor"},
        },
    )
    assert landed == ["C-R1-02"], "the good sibling ships, the bad one does not"
    assert merged is not None and merged.exists()
    assert "X.Fine" in merged.read_text(encoding="utf-8")
    assert proc not in merged.read_text(encoding="utf-8")


def test_a_round_where_everything_is_rejected_reports_no_merged_config(tmp_path: Path):
    """Nothing landed, so there is no config change to assert on and nothing may
    be recorded as shipped. P-16 then marks the round unscoreable."""
    from unittest.mock import MagicMock

    from harnessx.aegis.orchestrator import AegisOrchestrator

    (tmp_path / "config.yaml").write_text("processors: []\n", encoding="utf-8")
    rd = tmp_path / "R1"
    proc = "harnessx.processors.control.step_countdown.StepCountdownProcessor"
    _round_with_candidate(rd, "C-R1-01", f"processors:\n  - _target_: {proc}\n")

    orch = AegisOrchestrator(run_dir=tmp_path, num_evolvers=1, model_config=MagicMock())
    merged, landed, _rejected = orch._compose_shipped(
        round_n=1,
        round_dir=rd,
        current_config_path=tmp_path / "config.yaml",
        shipped_cids=["C-R1-01"],
        manifests_by_cid={"C-R1-01": {"bucket": "config"}},
    )
    assert (merged, landed) == (None, [])
    assert [cid for cid, _ in _rejected] == ["C-R1-01"]
    assert not (rd / "applied" / "merged.yaml").exists()


def test_compose_precedes_every_recording_call(tmp_path: Path):
    """A structural check, because the bug was ordering rather than logic: any
    future edit that moves a record above the compose reintroduces it."""
    import inspect

    from harnessx.aegis import orchestrator as _orch

    src = inspect.getsource(_orch.AegisOrchestrator.run_round)
    compose_at = src.index("self._compose_shipped(")
    for marker in ("self.reputation.record(", "self.scoreboard.add_ship(", "record_ship_outcome("):
        assert compose_at < src.index(marker), (
            f"{marker} runs before compose — it would record a ship that compose "
            f"then drops"
        )


# ---------------------------------------------------------------------------
# (f) P-19 — the refusal names the fix, so the fix has to reach a reader
# ---------------------------------------------------------------------------


def test_compose_refusals_are_returned_so_they_can_be_written_down(tmp_path: Path):
    """The Evolver filed StepCountdownProcessor under `config` in M14_L0_arm R3
    and again in every round of M15's smoke, was refused every time, and burned
    a candidate slot every time. The refusal says "This candidate belongs in the
    processor bucket" — and went only to a log file, so the next round had the
    same information and made the same call.

    _compose_shipped hands the refusals back; the caller writes them into
    rejected_candidates.jsonl, which the Critic already reads.
    """
    from unittest.mock import MagicMock

    from harnessx.aegis.orchestrator import AegisOrchestrator

    (tmp_path / "config.yaml").write_text("processors: []\n", encoding="utf-8")
    rd = tmp_path / "R2"
    proc = "harnessx.processors.control.step_countdown.StepCountdownProcessor"
    _round_with_candidate(rd, "C-R2-01", f"processors:\n  - _target_: {proc}\n")
    _round_with_candidate(rd, "C-R2-02", "processors:\n  - _target_: X.Fine\n")

    orch = AegisOrchestrator(run_dir=tmp_path, num_evolvers=1, model_config=MagicMock())
    _merged, landed, rejected = orch._compose_shipped(
        round_n=2,
        round_dir=rd,
        current_config_path=tmp_path / "config.yaml",
        shipped_cids=["C-R2-01", "C-R2-02"],
        manifests_by_cid={
            "C-R2-01": {"bucket": "config"},
            "C-R2-02": {"bucket": "processor"},
        },
    )
    assert landed == ["C-R2-02"]
    assert [cid for cid, _ in rejected] == ["C-R2-01"]
    assert "belongs in the processor bucket" in rejected[0][1], (
        "the actionable half of the message is what has to survive"
    )


def test_a_clean_round_returns_no_refusals(tmp_path: Path):
    from unittest.mock import MagicMock

    from harnessx.aegis.orchestrator import AegisOrchestrator

    (tmp_path / "config.yaml").write_text("processors: []\n", encoding="utf-8")
    rd = tmp_path / "R2"
    _round_with_candidate(rd, "C-R2-01", "processors:\n  - _target_: X.Fine\n")
    orch = AegisOrchestrator(run_dir=tmp_path, num_evolvers=1, model_config=MagicMock())
    _merged, landed, rejected = orch._compose_shipped(
        round_n=2,
        round_dir=rd,
        current_config_path=tmp_path / "config.yaml",
        shipped_cids=["C-R2-01"],
        manifests_by_cid={"C-R2-01": {"bucket": "processor"}},
    )
    assert (landed, rejected) == (["C-R2-01"], [])


def test_the_refusal_reaches_the_file_the_critic_reads():
    """The whole point is the destination, not the return value. Pin that the
    write goes to rejected_candidates.jsonl and carries the compose text."""
    import inspect

    from harnessx.aegis import orchestrator as _orch

    src = inspect.getsource(_orch.AegisOrchestrator.run_round)
    assert "compose_reason = dict(compose_rejected)" in src
    reason_at = src.index("compose_reason = dict(compose_rejected)")
    write_at = src.index("append_rejected_candidates")
    assert reason_at < write_at, "the reason must be resolved before the rows are written"
    assert "compose refused this candidate" in src


# ---------------------------------------------------------------------------
# (g) P-20 — the right prefix with an invented tail
# ---------------------------------------------------------------------------

_REAL = "7673d772-ef80-4f0f-a602-1bf4485c9b43"
_TYPO = "7673d772-ef80-4f0a-a602-1bf4485c9b43"  # one character, at index 17


def test_an_id_the_model_got_wrong_partway_is_repaired(tmp_path: Path, caplog):
    """M16_L0_ghx0's shape. Both of that arm's ships predicted _TYPO, which
    differs from a real task in the bed by a single character. Exact match
    fails, and prefix expansion cannot help because the typed id is not a
    prefix of anything — same length, forks at 17."""
    _history(tmp_path, [_REAL, "b" * 36])
    with caplog.at_level(logging.WARNING):
        out = ledger.resolve_task_ids(tmp_path, [_TYPO])
    assert out == [_REAL]
    assert "invented past it" in caplog.text
    assert "diverges at char 17" in caplog.text


def test_a_repair_is_reported_separately_from_an_abbreviation(tmp_path: Path, caplog):
    """Both end in the same id, but one is the writer being terse and the other
    is the writer being wrong. The log has to distinguish them."""
    _history(tmp_path, [_REAL])
    with caplog.at_level(logging.WARNING):
        ledger.resolve_task_ids(tmp_path, ["7673d772"])
    assert "expanded" in caplog.text and "invented past it" not in caplog.text
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        ledger.resolve_task_ids(tmp_path, [_TYPO])
    assert "invented past it" in caplog.text and "expanded 1 abbreviated" not in caplog.text


def test_a_short_coincidence_is_not_a_repair(tmp_path: Path, caplog):
    """Below the threshold the agreement is not evidence the model was copying
    anything, so guessing would be inventing an answer of our own."""
    _history(tmp_path, ["7673d772-ef80-4f0f-a602-1bf4485c9b43"])
    with caplog.at_level(logging.WARNING):
        out = ledger.resolve_task_ids(tmp_path, ["7673xxxx-0000-0000-0000-000000000000"])
    assert out == ["7673xxxx-0000-0000-0000-000000000000"]
    assert "match no task in history" in caplog.text


def test_two_tasks_sharing_the_divergence_point_are_not_guessed(tmp_path: Path, caplog):
    """A tie means we cannot tell which one was meant."""
    a = "aaaaaaaa-0000-1111-2222-333333333333"
    b = "aaaaaaaa-0000-1111-2222-444444444444"
    _history(tmp_path, [a, b])
    typed = "aaaaaaaa-0000-1111-2222-555555555555"
    with caplog.at_level(logging.WARNING):
        assert ledger.resolve_task_ids(tmp_path, [typed]) == [typed]
    assert "match no task in history" in caplog.text


def test_an_ambiguous_abbreviation_is_not_rescued_by_prefix_length(tmp_path: Path, caplog):
    """The repair runs only when prefix expansion found nothing. An
    abbreviation that matches two tasks must stay unresolved, not be handed to
    whichever of them shares one more character by chance."""
    _history(tmp_path, ["ab" + "1" * 34, "ab" + "2" * 34])
    with caplog.at_level(logging.WARNING):
        assert ledger.resolve_task_ids(tmp_path, ["ab"]) == ["ab"]
    assert "2 matches" in caplog.text


def test_the_m16_arm_heals_on_the_next_backfill(tmp_path: Path):
    """End to end: a ship predicting the typo, on a task that then flips."""
    ledger.append_task_history(tmp_path, [{"round": 1, "task_id": _REAL, "passed_flags": [False]}])
    ledger.record_ship_outcome(
        tmp_path, round_n=2, shipped_cid="C-R2-01", bucket="processor",
        predicted_tasks=[_TYPO], rejected_sibling_cids=[],
    )
    ledger.append_task_history(tmp_path, [{"round": 2, "task_id": _REAL, "passed_flags": [True]}])
    ledger.backfill_ship_outcomes(tmp_path)
    entry = json.loads(
        (ledger.data_dir(tmp_path) / "ship_outcomes.json").read_text(encoding="utf-8")
    )[0]
    assert entry["predicted_tasks"] == [_REAL]
    assert entry["hit_rate"] == "1/1"
