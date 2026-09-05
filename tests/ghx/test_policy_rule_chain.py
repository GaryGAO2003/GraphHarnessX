# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M26 -- the full chain the Evolver actually walks for a policy edit.

``test_runtime_policy.py`` proves ``rule_fires``/``fired_on_recorded_u``/
``RuntimePolicyProcessor`` in isolation, and ``test_graph_proposals.py`` proves
``mutate_params`` round-trips a processor's constructor kwargs through a single
in-memory edit. Neither proves the seam between them: a rule the Evolver writes
via ``GraphProposalEdit`` must survive materialization into config YAML text,
reload through ``HarnessConfig.from_yaml``, and instantiation into a REAL
``RuntimePolicyProcessor`` that still fires on a live event -- and the offline
replay predicate must agree with that same live behaviour.

Every step below drives the real production seam: ``ProposalSession._open`` /
``._edit`` (via the ``GraphProposalOpen``/``GraphProposalEdit`` tool wrappers),
``ProposalSession._render_config_yaml``, ``HarnessConfig.from_yaml``,
``RuntimePolicyProcessor``, ``rule_fires``, and ``fired_on_recorded_u``. No
monkeypatching anywhere -- this subsystem has no model/network call to patch
around.
"""

from __future__ import annotations

from pathlib import Path

from harnessx.core.attribution import install_unfold_recorder, reset_unfold_recorder
from harnessx.core.events import BeforeModelEvent
from harnessx.core.harness import HarnessConfig
from harnessx.ghx.runtime_policy import POLICY_MARKER, RuntimePolicyProcessor, fired_on_recorded_u
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedGraph, UnfoldedNode, UnfoldRecorder

from tests.ghx.test_graph_proposals import _make_session, _node_ids, _tools

_RTP_TARGET = "harnessx.ghx.runtime_policy.RuntimePolicyProcessor"

#: A parent config carrying one live-shaped RuntimePolicyProcessor node with an
#: empty policy -- the same _hook_/_singleton_group_/_order_ shape the
#: _EchoProbe fixture in test_graph_proposals.py already proves round-trips
#: (that file's _PARENT_YAML), just pointed at the real processor target.
_POLICY_PARENT_YAML = f"""processors:
  - _target_: {_RTP_TARGET}
    _hook_: "*"
    _singleton_group_: runtime_policy_sg
    _order_: 15
    rules: []
"""

SEARCH_RULE = {
    "name": "chain-stop-search-thrash",
    "when": {"predicate": "search_without_page", "searches": 3},
    "then": {"action": "steer", "text": "Fetch a page now -- chain test."},
    "min_step": 2,
    "max_fires": 1,
}

# (e): one rule per unknown-vocabulary axis -- predicate lookup miss and
# then.action vocabulary miss are two different branches inside rule_fires /
# on_before_model, so each gets its own no-op proof.
UNKNOWN_PREDICATE_RULE = {
    "name": "chain-typo-predicate",
    "when": {"predicate": "serach_without_page", "searches": 3},
    "then": {"action": "steer", "text": "should never appear"},
    "min_step": 2,
    "max_fires": 1,
}

UNKNOWN_ACTION_RULE = {
    "name": "chain-unknown-action",
    "when": {"predicate": "search_without_page", "searches": 3},
    "then": {"action": "rewrite_context", "text": "should never appear"},
    "min_step": 2,
    "max_fires": 1,
}


def _n(base: str, ordinal: int, step: int = 0) -> UnfoldedNode:
    return UnfoldedNode(
        id=unfolded_id(base, ordinal),
        static_node_id=base,
        graphed=True,
        hook="tool" if base.startswith("tool:") else "before_model",
        step=step,
        ordinal=ordinal,
        label=base,
    )


def _event(step: int) -> BeforeModelEvent:
    return BeforeModelEvent(run_id="r", step_id=step, messages=())


async def _drain(gen):
    out = []
    async for e in gen:
        out.append(e)
    return out


async def _materialize_reload_rule(tmp_path: Path, rule: dict, candidate_id: str = "C-R7-01") -> dict:
    """Drive ``rule`` through the exact tool surface the Evolver uses --
    GraphProposalOpen -> GraphProposalEdit(mutate_params on the
    RuntimePolicyProcessor node's ``rules`` kwarg) -- then materialize the
    candidate's config YAML text and reload it through the real
    ``HarnessConfig.from_yaml``.

    Returns the reloaded processors-list dict for the RuntimePolicyProcessor
    node. Asserts (a) the rendered text carries the rule and (b) the reloaded
    config's ``rules`` field equals what was written, so every caller gets (a)
    and (b) re-proven on its own tmp_path rather than trusting a prior test's
    side effect.
    """
    session = _make_session(tmp_path, round_n=7, parent_yaml=_POLICY_PARENT_YAML)
    tools = _tools(session)

    opened = await tools["GraphProposalOpen"].fn(candidate_id=candidate_id, bucket="config")
    assert opened["ok"] is True, opened

    node_id = _node_ids(session)[_RTP_TARGET]
    edited = await tools["GraphProposalEdit"].fn(
        candidate_id=candidate_id,
        edits=[{
            "edit_type": "mutate_params",
            "target_node_id": node_id,
            "node_changes": {"rules": [rule]},
        }],
        reason="policy rule chain test",
    )
    assert edited["ok"] is True, edited

    candidate = session._candidates[candidate_id]

    # (a) the candidate's materialized config TEXT carries the new rule.
    text = session._render_config_yaml(candidate)
    assert rule["name"] in text
    assert rule["when"]["predicate"] in text

    # (b) HarnessConfig.from_yaml loads that text back with the rule intact.
    cfg = HarnessConfig.from_yaml(text)
    entry = next(p for p in cfg.processors if p["_target_"] == _RTP_TARGET)
    assert entry["rules"] == [rule]
    return entry


# ── (a) + (b): materialize -> config text -> HarnessConfig.from_yaml ────────


async def test_mutate_params_materializes_and_reloads_with_the_rule_intact(tmp_path: Path):
    """GraphProposalEdit's mutate_params op on the RuntimePolicyProcessor node
    writes ``rules`` into the candidate's config text, and HarnessConfig.from_yaml
    reads that exact rule back -- not just a hash match, the literal dict."""
    entry = await _materialize_reload_rule(tmp_path, SEARCH_RULE)
    assert entry["rules"] == [SEARCH_RULE]


# ── (c): the reloaded rule instantiates a REAL processor that actually fires ─


async def test_reloaded_rule_fires_on_a_live_event_and_injects_one_steer_line(tmp_path: Path):
    entry = await _materialize_reload_rule(tmp_path, SEARCH_RULE)
    proc = RuntimePolicyProcessor(rules=entry["rules"])

    rec = UnfoldRecorder(run_id="r", session_id="s")
    rec._nodes = [_n("tool:WebSearch", i) for i in range(3)]  # continuous snippet streak, no page fetch
    token = install_unfold_recorder(rec)
    try:
        before = _event(5)
        assert before.messages == ()
        (out,) = await _drain(proc.on_before_model(before))
    finally:
        reset_unfold_recorder(token)

    assert out.messages != before.messages
    assert out.messages[-1].role == "user"
    assert out.messages[-1].content == f"{POLICY_MARKER} {SEARCH_RULE['then']['text']}"


# ── (d): the offline replay predicate agrees, non-vacuously ──────────────────


async def test_reloaded_rule_replays_offline_with_both_a_fire_and_a_non_fire(tmp_path: Path):
    entry = await _materialize_reload_rule(tmp_path, SEARCH_RULE)
    # min_step=0 for the synthetic U's own step numbering, exactly the
    # dict(STEER, min_step=0) trick test_runtime_policy.py uses for the same
    # replay-prefix check -- the rule under test is otherwise untouched.
    replay_rule = dict(entry["rules"][0], min_step=0)

    thrash_then_fetch = UnfoldedGraph(
        run_id="r", session_id="s",
        nodes=[_n("tool:WebSearch", i, step=i) for i in range(3)] + [_n("tool:WebFetch", 3, step=3)],
    )
    healthy = UnfoldedGraph(
        run_id="r", session_id="s",
        nodes=[
            _n("tool:WebSearch", 0, step=0),
            _n("tool:WebFetch", 1, step=1),
            _n("tool:WebSearch", 2, step=2),
            _n("tool:WebFetch", 3, step=3),
        ],
    )
    # non-empty AND non-universal: one U fires, one does not.
    assert fired_on_recorded_u(replay_rule, thrash_then_fetch) is True
    assert fired_on_recorded_u(replay_rule, healthy) is False


# ── (e): an unknown predicate / unknown action is a no-op through the WHOLE
# chain, not just at the rule_fires unit level ───────────────────────────────


async def test_unknown_predicate_survives_the_full_chain_as_a_silent_noop(tmp_path: Path):
    entry = await _materialize_reload_rule(tmp_path, UNKNOWN_PREDICATE_RULE)
    proc = RuntimePolicyProcessor(rules=entry["rules"])

    rec = UnfoldRecorder(run_id="r", session_id="s")
    rec._nodes = [_n("tool:WebSearch", i) for i in range(3)]  # would satisfy searches=3 if spelled right
    token = install_unfold_recorder(rec)
    try:
        (out,) = await _drain(proc.on_before_model(_event(5)))
    finally:
        reset_unfold_recorder(token)

    assert out.messages == ()  # unknown predicate name never fires, never raises


async def test_unknown_action_survives_the_full_chain_as_a_silent_noop(tmp_path: Path):
    entry = await _materialize_reload_rule(tmp_path, UNKNOWN_ACTION_RULE)
    proc = RuntimePolicyProcessor(rules=entry["rules"])

    rec = UnfoldRecorder(run_id="r", session_id="s")
    rec._nodes = [_n("tool:WebSearch", i) for i in range(3)]  # the predicate DOES fire here
    token = install_unfold_recorder(rec)
    try:
        (out,) = await _drain(proc.on_before_model(_event(5)))
    finally:
        reset_unfold_recorder(token)

    assert out.messages == ()  # v1 vocabulary ends at "steer" -- an unknown action is still a no-op
