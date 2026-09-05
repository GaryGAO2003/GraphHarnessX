# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""P-24 — two gates could not see, or be seen to see.

(a) The audit recorded a reason only when a gate failed. A gate that skips
    returns ok=True with "skipped: ...", so the reason was dropped and the
    record showed plain `true` — indistinguishable from a real pass. counterfactual
    has two skip paths and replay has one.

(b) IV-11 turns the Critic's strategy_concern from advice into a structural gate:
    a candidate must target the flagged bucket or prove the direction infeasible
    with evidence. It reads strategy_concern_flagged_buckets from the landscape
    frontmatter. The Critic writes strategy_concern (22 decision.md files have
    it), the Planner was told to relay it in prose, and nothing ever asked for
    the structured field — zero landscapes carry it, so the gate never fired and
    the concern stayed advisory.
"""
from __future__ import annotations

import inspect

from harnessx.aegis import orchestrator as _orch
from harnessx.aegis._prompt import render_template

_PLANNER = "harnessx/aegis/templates/planner.md"
from harnessx.aegis.gates.structure import _check_exploration_response


# --- (a) a skip must be visible in the record --------------------------------


def test_the_audit_keeps_every_reason_not_only_failures():
    src = inspect.getsource(_orch.AegisOrchestrator.run_round)
    assert '"reasons": {k: v.reason for k, v in gr.items() if v.reason}' in src, (
        "filtering on `not v.ok` discards the skip reason, which is the only "
        "thing separating a skipped gate from a passed one"
    )


def test_a_skipping_gate_carries_a_reason_to_record():
    """The reason exists; the audit just used to throw it away."""
    import asyncio

    from harnessx.aegis.gates.replay import check_replay_smoke

    r = asyncio.run(check_replay_smoke("unused.yaml", model_config=None))
    assert r.ok is True, "a skip is not a rejection"
    assert "skipped" in r.reason, "and it says so — that is what has to survive"


# --- (b) the concern has to reach the gate -----------------------------------


def test_the_planner_is_asked_for_the_field_the_gate_reads():
    t = render_template(_PLANNER, round=3, round_minus_1=2)
    assert "strategy_concern_flagged_buckets" in t, (
        "the prose relay was instructed and the structured field was not, which "
        "is the one hop that kept IV-11 inert"
    )


def test_the_planner_is_told_why_the_field_matters():
    """An unexplained field gets left empty. It has to say that leaving it empty
    demotes the concern back to advice."""
    t = render_template(_PLANNER, round=3, round_minus_1=2)
    assert "gate" in t.lower()
    assert "advice" in t.lower() or "advisory" in t.lower()


def test_iv11_binds_only_once_a_bucket_is_flagged():
    """Empty flags is a no-op — which is exactly the state the whole corpus was
    in, so the gate had never once run."""
    manifest = {"bucket": "prompt"}
    assert _check_exploration_response(manifest, "body", None) is None
    assert _check_exploration_response(manifest, "body", set()) is None


def test_iv11_refuses_a_candidate_that_ignores_the_flagged_bucket():
    manifest = {"bucket": "prompt"}
    out = _check_exploration_response(manifest, "no such section", {"config"})
    assert out is not None and "config" in out


def test_iv11_accepts_a_candidate_that_targets_the_flagged_bucket():
    assert _check_exploration_response({"bucket": "config"}, "body", {"config"}) is None
    assert _check_exploration_response({"bucket": ["tools", "config"]}, "b", {"config"}) is None


def test_iv11_accepts_a_documented_infeasibility_instead():
    # Deliberately substantial: the gate wants tool output, not an assertion,
    # which is how it keeps "prompt iteration is easier" from counting.
    body = (
        "## Why flagged direction is infeasible\n\n"
        "Ran the provider probe under bash and got NXDOMAIN; web_search returns a "
        "shutdown notice; web_fetch of the docs host 404s. No config-only change "
        "can reach a provider that is gone.\n"
    )
    assert _check_exploration_response({"bucket": "prompt"}, body, {"config"}) is None


def test_iv11_rejects_a_one_line_excuse():
    """The heading alone is not evidence — that loophole would make the gate
    cosmetic, which is what it exists to stop being."""
    thin = "## Why flagged direction is infeasible\n\nToo hard."
    out = _check_exploration_response({"bucket": "prompt"}, thin, {"config"})
    assert out is not None and "too short" in out
