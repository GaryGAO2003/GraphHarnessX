# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M26 — graph-conditioned runtime interventions.

The loop's first in-run edit surface: rules are the processor's ``rules`` param
(so the Evolver edits policy via mutate_params), predicates run over the live
unfolded recorder, a fire injects one marked steer line on the StepCountdown
seam, and the same predicate replays offline against a recorded U so a gate can
know a rule's firing set before it costs a batch.
"""

from __future__ import annotations

import asyncio

from harnessx.core.attribution import install_unfold_recorder, reset_unfold_recorder
from harnessx.core.events import BeforeModelEvent, Message
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedGraph, UnfoldedNode, UnfoldRecorder
from harnessx.ghx.runtime_policy import (
    POLICY_MARKER,
    RuntimePolicyProcessor,
    fired_on_recorded_u,
    rule_fires,
)


def _n(base: str, ordinal: int, outcome: str = "", step: int = 0) -> UnfoldedNode:
    return UnfoldedNode(
        id=unfolded_id(base, ordinal),
        static_node_id=base,
        graphed=True,
        hook="tool" if base.startswith("tool:") else "before_model",
        step=step,
        ordinal=ordinal,
        label=base,
        outcome=outcome,
    )


STEER = {
    "name": "stop-search-thrash",
    "when": {"predicate": "search_without_page", "searches": 3},
    "then": {"action": "steer", "text": "Fetch a page now."},
    "min_step": 2,
    "max_fires": 1,
}


async def _drain(gen):
    out = []
    async for e in gen:
        out.append(e)
    return out


def _event(step: int, msgs=()) -> BeforeModelEvent:
    return BeforeModelEvent(run_id="r", step_id=step, messages=tuple(msgs))


# ── predicates ───────────────────────────────────────────────────────────────


def test_search_without_page_counts_since_the_last_page_grade_call():
    searches = [_n("tool:WebSearch", i) for i in range(3)]
    assert rule_fires(STEER, searches, step=5)
    # a page-grade fetch resets the streak
    broken = searches + [_n("tool:WebFetch", 3), _n("tool:WebSearch", 4)]
    assert not rule_fires(STEER, broken, step=5)


def test_consecutive_empty_reads_the_live_outcome_stamps():
    rule = {"when": {"predicate": "consecutive_empty", "count": 2}, "then": {"action": "steer", "text": "x"}}
    ok_then_two_empty = [
        _n("tool:WebFetch", 0, outcome="ok"),
        _n("tool:Bash", 1, outcome="empty"),
        _n("tool:Bash", 2, outcome="error"),
    ]
    assert rule_fires(rule, ok_then_two_empty, step=3)
    # an unstamped outcome ("") is not empty — a not-yet-annotated node must
    # never count toward a death signature
    assert not rule_fires(rule, [_n("tool:Bash", 0), _n("tool:Bash", 1)], step=3)


def test_consecutive_empty_counts_structured_empty_payloads():
    """End-to-end outcome-fidelity fix: classify_tool_outcome is the only
    place "empty" gets decided before it reaches this predicate, so a custom
    tool's JSON-shaped nothing must count toward the death signature the same
    way a blank string does — no separate empty-check to keep in sync here."""
    from harnessx.graph.unfold import classify_tool_outcome

    rule = {"when": {"predicate": "consecutive_empty", "count": 2}, "then": {"action": "steer", "text": "x"}}
    nodes = [
        _n("tool:WebFetch", 0, outcome="ok"),
        _n("tool:CustomSearch", 1, outcome=classify_tool_outcome('{"results": []}')),
        _n("tool:CustomSearch", 2, outcome=classify_tool_outcome('{"error": "rate limited"}')),
    ]
    assert rule_fires(rule, nodes, step=3)


def test_min_step_and_unknown_predicate_never_fire():
    assert not rule_fires(STEER, [_n("tool:WebSearch", i) for i in range(9)], step=1)  # min_step=2
    typo = {"when": {"predicate": "serach_without_page"}, "then": {"action": "steer", "text": "x"}}
    assert not rule_fires(typo, [_n("tool:WebSearch", i) for i in range(9)], step=9)


# ── live processor ───────────────────────────────────────────────────────────


def _run_with_recorder(proc, nodes, step=5, msgs=()):
    rec = UnfoldRecorder(run_id="r", session_id="s")
    rec._nodes = list(nodes)
    token = install_unfold_recorder(rec)
    try:
        return asyncio.run(_drain(proc.on_before_model(_event(step, msgs))))
    finally:
        reset_unfold_recorder(token)


def test_fire_injects_one_marked_steer_line():
    proc = RuntimePolicyProcessor(rules=[STEER])
    (out,) = _run_with_recorder(proc, [_n("tool:WebSearch", i) for i in range(3)])
    assert out.messages[-1].role == "user"
    assert out.messages[-1].content == f"{POLICY_MARKER} Fetch a page now."


def test_max_fires_is_respected_across_calls():
    proc = RuntimePolicyProcessor(rules=[STEER])
    nodes = [_n("tool:WebSearch", i) for i in range(3)]
    (first,) = _run_with_recorder(proc, nodes)
    assert POLICY_MARKER in first.messages[-1].content
    (second,) = _run_with_recorder(proc, nodes)
    assert second.messages == ()  # spent — pass-through


def test_task_start_resets_the_fire_budget():
    proc = RuntimePolicyProcessor(rules=[STEER])
    nodes = [_n("tool:WebSearch", i) for i in range(3)]
    _run_with_recorder(proc, nodes)

    async def _reset():
        async for _ in proc.on_task_start(object()):
            pass

    asyncio.run(_reset())
    (again,) = _run_with_recorder(proc, nodes)
    assert POLICY_MARKER in again.messages[-1].content


def test_refreshes_its_own_marker_instead_of_stacking():
    proc = RuntimePolicyProcessor(rules=[dict(STEER, max_fires=5)])
    prior = Message(role="user", content=f"{POLICY_MARKER} old line")
    (out,) = _run_with_recorder(proc, [_n("tool:WebSearch", i) for i in range(3)], msgs=(prior,))
    assert len(out.messages) == 1
    assert out.messages[-1].content.endswith("Fetch a page now.")


def test_no_recorder_and_no_rules_are_pass_throughs():
    async def _bare(proc):
        return await _drain(proc.on_before_model(_event(5)))

    (out,) = asyncio.run(_bare(RuntimePolicyProcessor(rules=[STEER])))  # no recorder installed
    assert out.messages == ()
    (out2,) = asyncio.run(_bare(RuntimePolicyProcessor()))  # no rules
    assert out2.messages == ()


# ── the offline replay half ──────────────────────────────────────────────────


def test_fired_on_recorded_u_replays_prefixes_exactly():
    """The gate's question: would this rule have fired on THIS recorded run?
    Prefix semantics matter — a page fetch AFTER the thrash must not launder
    the earlier firing."""
    thrash_then_fetch = UnfoldedGraph(
        run_id="r",
        session_id="s",
        nodes=[_n("tool:WebSearch", i, step=i) for i in range(3)] + [_n("tool:WebFetch", 3, step=3)],
    )
    assert fired_on_recorded_u(dict(STEER, min_step=0), thrash_then_fetch)
    healthy = UnfoldedGraph(
        run_id="r",
        session_id="s",
        nodes=[
            _n("tool:WebSearch", 0, step=0),
            _n("tool:WebFetch", 1, step=1),
            _n("tool:WebSearch", 2, step=2),
            _n("tool:WebFetch", 3, step=3),
        ],
    )
    assert not fired_on_recorded_u(dict(STEER, min_step=0), healthy)


# ── the edit surface ─────────────────────────────────────────────────────────


def test_rules_are_the_processors_params_and_survive_config_serialization():
    """The whole design premise: policy edits ride the existing mutate_params
    surface, so the rules must round-trip through processor serialization."""
    from harnessx.core.harness import _serialize_processor

    proc = RuntimePolicyProcessor(rules=[STEER])
    d = _serialize_processor(proc)
    assert d["_target_"].endswith("runtime_policy.RuntimePolicyProcessor")
    assert d["rules"] == [STEER]


# ── the graph-native predicate: own_death_cone ───────────────────────────────
# The counters above are expressible as a worker-local processor (the loop has
# evolved that family itself). This one is not: it needs the task's identity
# (recorder session id), its cross-round failing cone signatures
# (cone_sigs.json), and the live run's structural shape — all graph plane.

import json as _json

TID = "aaaa1111-2222-3333-4444-555566667777"


def _write_sigs(run: "Path", rnd: int, failing: dict, passing: dict) -> None:
    d = run / f"R{rnd}" / "graph_evidence"
    d.mkdir(parents=True, exist_ok=True)
    (d / "cone_sigs.json").write_text(
        _json.dumps({"round": rnd, "failing": failing, "passing": passing}), encoding="utf-8"
    )


def _seed_death_history(run, streak=3):
    """TID died three rounds running on {Bash, loop_detection}; a ubiquitous
    node (system_prompt, present in every sig on both sides) rides along."""
    for r in range(1, streak + 1):
        _write_sigs(
            run, r,
            failing={TID: ["proc:system_prompt_processor", "tool:Bash", "proc:loop_detection_processor"]},
            passing={"other": ["proc:system_prompt_processor", "tool:WebSearch"]},
        )


def _cone_rule(run, **over) -> dict:
    rule = {
        "name": "own-death-cone",
        "when": {"predicate": "own_death_cone", "run_dir": str(run), "min_streak": 3, "overlap": 0.8},
        "then": {"action": "steer", "text": "You are on the exact path this task died on before."},
        "min_step": 0, "max_fires": 1,
    }
    rule["when"].update(over)
    return rule


def _ctx(task_id=TID):
    return {"task_id": task_id}


def test_own_death_cone_fires_when_the_live_run_retraces_the_recorded_one(tmp_path):
    from harnessx.ghx.runtime_policy import _SIG_CACHE

    _SIG_CACHE.clear()
    _seed_death_history(tmp_path)
    # discriminative core = {tool:Bash, proc:loop_detection} minus the ubiquitous
    # system_prompt; the live tool plane touching Bash covers 1/2 of it.
    live = [_n("tool:Bash", 0)]
    rule = _cone_rule(tmp_path, overlap=0.5)
    assert rule_fires(rule, live, step=2, ctx=_ctx())
    # a different task with no such history never fires
    assert not rule_fires(rule, live, step=2, ctx=_ctx("bbbb0000-0000-0000-0000-000000000000"))


def test_own_death_cone_needs_the_full_streak(tmp_path):
    from harnessx.ghx.runtime_policy import _SIG_CACHE

    _SIG_CACHE.clear()
    _seed_death_history(tmp_path, streak=2)  # only two failing rounds on record
    assert not rule_fires(_cone_rule(tmp_path, overlap=0.5), [_n("tool:Bash", 0)], step=2, ctx=_ctx())


def test_a_death_cone_of_only_ubiquitous_nodes_abstains(tmp_path):
    """The cone ruler and the attribution guard each learned this after the
    fact; here it is built in: a signature that survives only as always-on
    framework nodes matches every run ever and must never fire."""
    from harnessx.ghx.runtime_policy import _SIG_CACHE

    _SIG_CACHE.clear()
    for r in range(1, 4):
        _write_sigs(
            tmp_path, r,
            failing={TID: ["proc:system_prompt_processor"]},
            passing={"other": ["proc:system_prompt_processor"]},
        )
    assert not rule_fires(
        _cone_rule(tmp_path, overlap=0.1),
        [_n("proc:system_prompt_processor", 0)], step=5, ctx=_ctx(),
    )


def test_missing_history_and_missing_ctx_never_fire(tmp_path):
    rule = _cone_rule(tmp_path / "empty")
    assert not rule_fires(rule, [_n("tool:Bash", 0)], step=2, ctx=_ctx())
    assert not rule_fires(rule, [_n("tool:Bash", 0)], step=2, ctx=None)


def test_offline_replay_resolves_the_task_from_the_us_own_session_id(tmp_path):
    from harnessx.ghx.runtime_policy import _SIG_CACHE

    _SIG_CACHE.clear()
    _seed_death_history(tmp_path)
    u = UnfoldedGraph(run_id="r", session_id=f"aegis/R4-{TID}",
                      nodes=[_n("tool:Bash", 0, step=0)])
    assert fired_on_recorded_u(_cone_rule(tmp_path, overlap=0.5), u)
    other = UnfoldedGraph(run_id="r", session_id="aegis/R4-cccc0000-0000-0000-0000-000000000000",
                          nodes=[_n("tool:Bash", 0, step=0)])
    assert not fired_on_recorded_u(_cone_rule(tmp_path, overlap=0.5), other)
