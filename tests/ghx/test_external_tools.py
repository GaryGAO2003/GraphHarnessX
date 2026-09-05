# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""τ² port: tool nodes in U when the environment, not the runloop, ran the tool."""
from __future__ import annotations

import asyncio

from harnessx.core.events import BeforeModelEvent, Message, ToolCall
from harnessx.ghx.external_tools import ExternalToolBridge, bridge_external_tools
from harnessx.graph.unfold import UnfoldRecorder


def _rec():
    return UnfoldRecorder(run_id="r", session_id="s")


def _turn(name="get_order_details", call_id="c1", content="{'order': 42}"):
    return [
        Message(role="assistant", content="", tool_calls=(ToolCall(id=call_id, name=name, input={}),)),
        Message(role="tool", content=content, tool_call_id=call_id),
    ]


def test_bridges_name_and_outcome():
    rec = _rec()
    ids = bridge_external_tools(_turn(), step=3, recorder=rec)
    assert len(ids) == 1
    u = rec.finalize(None)
    (node,) = [n for n in u.nodes if n.static_node_id.startswith("tool:")]
    assert node.static_node_id == "tool:get_order_details"
    assert node.step == 3
    assert node.outcome == "ok"


def test_empty_payload_is_stamped_empty():
    """The whole point of carrying the outcome across: the empty-result family is
    what the policy predicates read, and an env-executed tool must land in it."""
    rec = _rec()
    bridge_external_tools(_turn(content=""), step=1, recorder=rec)
    (node,) = [n for n in rec.finalize(None).nodes if n.static_node_id.startswith("tool:")]
    assert node.outcome == "empty"
    rec2 = _rec()
    bridge_external_tools(_turn(content='{"error": "not found"}'), step=1, recorder=rec2)
    (n2,) = [n for n in rec2.finalize(None).nodes if n.static_node_id.startswith("tool:")]
    assert n2.outcome == "empty"  # error-only payload — the shared emptiness judge


def test_idempotent_across_turns():
    """before_model fires once per turn and the context re-carries every past tool
    message; bridging must add only what is new or U would multiply-count."""
    rec = _rec()
    ctx = _turn(call_id="c1")
    assert len(bridge_external_tools(ctx, 1, rec)) == 1
    assert bridge_external_tools(ctx, 2, rec) == []  # same context again
    ctx = ctx + _turn(name="get_user_details", call_id="c2")
    assert len(bridge_external_tools(ctx, 3, rec)) == 1
    tools = [n for n in rec.finalize(None).nodes if n.static_node_id.startswith("tool:")]
    assert [n.static_node_id for n in tools] == ["tool:get_order_details", "tool:get_user_details"]


def test_unnamed_call_still_lands():
    rec = _rec()
    bridge_external_tools([Message(role="tool", content="x", tool_call_id="zz")], 0, rec)
    (node,) = [n for n in rec.finalize(None).nodes if n.static_node_id.startswith("tool:")]
    assert node.static_node_id == "tool:ExternalTool"


def test_no_recorder_is_a_noop():
    assert bridge_external_tools(_turn(), 0, None) == []


def test_processor_hook_bridges_and_passes_the_event_through():
    rec = _rec()
    from harnessx.core.attribution import install_unfold_recorder, reset_unfold_recorder

    token = install_unfold_recorder(rec)
    try:
        ev = BeforeModelEvent(run_id="r", step_id=7, messages=tuple(_turn()))
        out = asyncio.run(_drain(ExternalToolBridge(), ev))
    finally:
        reset_unfold_recorder(token)
    assert out == [ev]  # pass-through: the bridge observes, it never edits
    (node,) = [n for n in rec.finalize(None).nodes if n.static_node_id.startswith("tool:")]
    assert node.step == 7


async def _drain(proc, ev):
    return [x async for x in proc.on_before_model(ev)]


def test_bridged_tool_lands_on_the_message_plane():
    """A recorded-but-edgeless node is invisible: every cone walks edges backwards
    from its terminus, so without the write the tool is in U and in no cone."""
    rec = _rec()
    msgs = _turn()
    bridge_external_tools(msgs, 2, rec)
    tool_msg = msgs[-1]
    # the model call that reads it next is what closes the data edge
    model_inv = rec.record_model_invocation("m", 2, None)
    rec.log_message_access(tool_msg, "read", model_inv, 2)
    u = rec.finalize(None)
    tool_node = next(n for n in u.nodes if n.static_node_id.startswith("tool:"))
    data = [e for e in u.edges if e.source == tool_node.id and e.target == model_inv]
    assert data, "tool -> model data edge missing; the cone would never reach the tool"
