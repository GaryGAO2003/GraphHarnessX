# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Two ways a shipped candidate can fail to land, both silently. P-7 and P-9.

Neither needs a campaign to reproduce: both are pure functions over three dicts,
so the situation can be built directly.

The shared root is that ``_apply_config`` used to ``del parent``. A candidate's
config.yaml is a FULL config, carrying the parent's value for every field it did not
touch, and ``base`` is mutated in place by each applier in turn. Diffing candidate
against the running base therefore cannot tell "I want this value" from "I never
thought about this value", and the second kind overwrites whatever the previous
candidate just shipped.
"""

from __future__ import annotations

import pytest
import yaml

from harnessx.aegis.compose import BucketCannotExpressCandidate, compose_shipped_configs

_LOOP = "harnessx.processors.control.loop_detection.LoopDetectionProcessor"
_COST = "harnessx.processors.control.cost_guard.CostGuardProcessor"
_NEW = "harnessx.processors.control.step_countdown.StepCountdownProcessor"


def _write(path, cfg):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return path


def _base():
    return {
        "processors": [
            {"_target_": _LOOP, "threshold": 4, "action": "warn"},
            {"_target_": _COST, "max_usd": 20.0},
        ]
    }


def _merged(tmp_path, shipped):
    out = compose_shipped_configs(
        _write(tmp_path / "base.yaml", _base()), shipped, tmp_path / "merged.yaml"
    )
    procs = (yaml.safe_load(out.read_text(encoding="utf-8")) or {}).get("processors") or []
    return {p["_target_"]: p for p in procs}


# ── P-7 ───────────────────────────────────────────────────────────────────────


def test_a_later_config_candidate_does_not_revert_an_earlier_one(tmp_path):
    """The rollback. Candidate A raises the loop threshold; candidate B touches only
    the cost guard but its config still carries the parent's threshold. Diffed against
    the mutated base that untouched value reads as a change and writes A's ship away.
    """
    a = _base()
    a["processors"][0]["threshold"] = 9  # A's actual change
    b = _base()
    b["processors"][1]["max_usd"] = 50.0  # B's actual change; threshold left at 4

    got = _merged(
        tmp_path,
        [
            ("C-A", "config", _write(tmp_path / "a" / "config.yaml", a)),
            ("C-B", "config", _write(tmp_path / "b" / "config.yaml", b)),
        ],
    )
    assert got[_LOOP]["threshold"] == 9, "B silently reverted A's change"
    assert got[_COST]["max_usd"] == 50.0, "B's own change must still land"


def test_a_candidate_that_changes_nothing_changes_nothing(tmp_path):
    """A no-opinion candidate must not write the parent back over a live base."""
    a = _base()
    a["processors"][0]["action"] = "halt"
    got = _merged(
        tmp_path,
        [
            ("C-A", "config", _write(tmp_path / "a" / "config.yaml", a)),
            ("C-B", "config", _write(tmp_path / "b" / "config.yaml", _base())),
        ],
    )
    assert got[_LOOP]["action"] == "halt"


# ── P-9 ───────────────────────────────────────────────────────────────────────


def test_config_bucket_asked_to_add_a_processor_is_rejected_by_name(tmp_path):
    """The silent drop, reproduced.

    M13's only real ship: the Critic accepted two candidates, one landed, nothing was
    logged, decision.md recorded both, and the empty-ship guard was satisfied by the
    one that did land. The mis-bucketed one was adding a processor while declaring
    bucket=config, which this applier cannot express.

    P-18 changed where the refusal surfaces, not whether there is one: the applier
    still raises, compose catches it per candidate, and the candidate comes back in
    ``rejected`` instead of taking the round down. What must never happen — the
    candidate landing anyway — is what both versions of this test guard.
    """
    cand = _base()
    cand["processors"].append({"_target_": _NEW, "escalate_within": 2})
    applied = _write(tmp_path / "c" / "config.yaml", cand)

    res = compose_shipped_configs(
        _write(tmp_path / "base.yaml", _base()),
        [("C-1", "config", applied)],
        tmp_path / "merged.yaml",
    )
    assert res.landed == []
    assert [cid for cid, _ in res.rejected] == ["C-1"]
    assert "cannot add a processor" in res.rejected[0][1]
    assert res.output_path is None, "nothing landed, so there is no merged config"
    assert not (tmp_path / "merged.yaml").exists()


def test_the_applier_itself_still_raises(tmp_path):
    """P-9's contract is unchanged one level down — compose is what catches it."""
    from harnessx.aegis.compose import _apply_config

    cand = _base()
    cand["processors"].append({"_target_": _NEW, "escalate_within": 2})
    with pytest.raises(BucketCannotExpressCandidate, match="cannot add a processor"):
        _apply_config(_base(), cand, _base())


def test_a_good_candidate_survives_a_bad_sibling(tmp_path):
    """P-18. Applying to `base` in place meant one raising applier killed the loop
    before write_text, so no merged.yaml was written and every other candidate's
    work went with it.

    M15_smoke_L2 R1: three shipped, C-R1-01 declared bucket config while adding a
    processor, and C-R1-02 and C-R1-03 — both fine — were discarded too. The round
    ran the parent config.
    """
    bad = _base()
    bad["processors"].append({"_target_": _NEW, "escalate_within": 2})
    good = _base()
    good["processors"].append({"_target_": _NEW, "escalate_within": 2})

    res = compose_shipped_configs(
        _write(tmp_path / "base.yaml", _base()),
        [
            ("C-1", "config", _write(tmp_path / "bad" / "config.yaml", bad)),
            ("C-2", "processor", _write(tmp_path / "good" / "config.yaml", good)),
        ],
        tmp_path / "merged.yaml",
    )
    assert res.landed == ["C-2"]
    assert [cid for cid, _ in res.rejected] == ["C-1"]
    procs = (yaml.safe_load(res.read_text(encoding="utf-8")) or {}).get("processors") or []
    got = {p["_target_"]: p for p in procs if isinstance(p, dict)}
    assert _NEW in got, "the good sibling must land"


def test_a_rejected_candidate_leaves_no_trace_in_the_merged_config(tmp_path):
    """Isolation, not just error handling: the bad candidate is applied to a scratch
    copy, so a half-applied bundle cannot leak into what the round runs."""
    bad = _base()
    bad["processors"].append({"_target_": _NEW, "escalate_within": 2})
    bad["tool_registry"] = {"custom": ["file:///tmp/leaked.py::leaked_tool"]}
    good = _base()
    good["processors"].append({"_target_": _NEW, "escalate_within": 2})

    res = compose_shipped_configs(
        _write(tmp_path / "base.yaml", _base()),
        [
            # tools applies cleanly, config then raises — the tools half must
            # not survive.
            ("C-1", ["tools", "config"], _write(tmp_path / "bad" / "config.yaml", bad)),
            ("C-2", "processor", _write(tmp_path / "good" / "config.yaml", good)),
        ],
        tmp_path / "merged.yaml",
    )
    assert res.landed == ["C-2"]
    merged = yaml.safe_load(res.read_text(encoding="utf-8")) or {}
    assert "leaked_tool" not in str(merged.get("tool_registry") or {}), (
        "half of a rejected bundle leaked into the round's config"
    )


def test_the_same_candidate_lands_when_bucketed_as_a_processor(tmp_path):
    """The error names the fix, so the fix has to actually work."""
    cand = _base()
    cand["processors"].append({"_target_": _NEW, "escalate_within": 2})

    got = _merged(tmp_path, [("C-1", "processor", _write(tmp_path / "c" / "config.yaml", cand))])
    assert _NEW in got and got[_NEW]["escalate_within"] == 2


def test_a_target_a_previous_candidate_removed_is_skipped_not_raised(tmp_path):
    """Absent from base but present in parent means someone else removed it this
    round — not this candidate's doing, and not something it can express. Raising
    there would turn a legitimate multi-ship into a crash."""
    remover = {"processors": [p for p in _base()["processors"] if p["_target_"] != _COST]}
    later = _base()
    later["processors"][0]["threshold"] = 7

    got = _merged(
        tmp_path,
        [
            ("C-A", "processor", _write(tmp_path / "a" / "config.yaml", remover)),
            ("C-B", "config", _write(tmp_path / "b" / "config.yaml", later)),
        ],
    )
    assert _COST not in got, "A's removal stands"
    assert got[_LOOP]["threshold"] == 7, "B's change still lands"
