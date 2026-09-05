# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""U for beds where the *environment* executes the tools.

GAIA runs every tool inside the runloop, so the tool site records a
``tool:<name>`` node and stamps its outcome, and every cone the evidence plane
draws is a statement about what the agent actually did.  τ² inverts that: the
agent's tool call is intercepted (``interrupt_on``), the domain executes it, and
the result comes back as a ``role="tool"`` message on the next turn.  The
runloop's tool site never fires — so without this bridge U holds processors and
model calls only, every cone signature is identical across tasks, and the
predicates that read tool outcomes (``consecutive_empty``) can never fire.

This processor reads the tool results the bed feeds back and records one tool
invocation per result, using the same node id (``tool:<name>``) and the same
outcome vocabulary the runloop stamps, so everything downstream — cones,
signatures, the policy predicates, the flip ledger — reads a τ² run exactly the
way it reads a GAIA one.

What it does NOT do: invent control edges.  A bridged tool ran outside this
process, with no ``before_tool`` firing to link from, so it enters U as a node
in ordinal order and nothing more.  Inventing an edge would be a claim about
causality nobody observed.
"""
from __future__ import annotations

import logging

from ..core.attribution import current_unfold_recorder
from ..core.processor import MultiHookProcessor
from ..graph.unfold import classify_tool_outcome

_LOG = logging.getLogger(__name__)

#: Attribute the memo of already-bridged tool_call_ids hangs off, so it lives
#: exactly as long as the recorder does (one per task under accumulation) and a
#: replayed or restarted run starts clean.
_MEMO_ATTR = "_ghx_bridged_tool_ids"


def _names_by_call_id(messages) -> dict:
    """``tool_call_id -> tool name`` from the assistant messages that made them.

    A ``role="tool"`` message carries the id and the payload but not the name;
    the name is on the assistant turn that requested it.
    """
    out: dict = {}
    for m in messages:
        for tc in getattr(m, "tool_calls", ()) or ():
            tc_id = getattr(tc, "id", None)
            name = getattr(tc, "name", None)
            if tc_id and name:
                out[str(tc_id)] = str(name)
    return out


def bridge_external_tools(messages, step: int, recorder=None) -> list[str]:
    """Record every not-yet-bridged tool result in ``messages``; return their ids.

    Idempotent per recorder: a message already bridged is skipped, so the
    repeated ``before_model`` firings of a multi-turn task each add only what
    is new.  Returns the invocation ids minted, newest last.
    """
    rec = recorder if recorder is not None else current_unfold_recorder()
    if rec is None:
        return []
    seen = getattr(rec, _MEMO_ATTR, None)
    if seen is None:
        seen = set()
        setattr(rec, _MEMO_ATTR, seen)

    names = _names_by_call_id(messages)
    minted: list[str] = []
    for m in messages:
        if getattr(m, "role", "") != "tool":
            continue
        call_id = getattr(m, "tool_call_id", None)
        # No id (some beds omit it) → fall back to identity so the message is
        # still bridged exactly once, rather than every turn.
        key = str(call_id) if call_id else f"obj:{id(m)}"
        if key in seen:
            continue
        seen.add(key)
        name = names.get(str(call_id), "") or "ExternalTool"
        content = getattr(m, "content", "")
        try:
            inv_id = rec.record_tool_invocation(name, step, None)
            rec.annotate_outcome(inv_id, classify_tool_outcome(content))
            # The tool authored this message; the model call that is about to read
            # it consumes it. Logging the write puts the node on the message plane,
            # where reaching-definitions draws the observed tool → model data edge —
            # the same edge the runloop's own tool site gets, and the reason a
            # bridged node is reachable from the cone's terminus at all. Without it
            # the node is recorded and invisible: present in U, absent from every
            # cone that walks edges backwards.
            rec.log_message_access(m, "write", inv_id, step)
            minted.append(inv_id)
        except Exception:  # noqa: BLE001 — U is evidence, never a reason to sink a run
            _LOG.warning("external tool bridge: failed to record %r", name, exc_info=True)
    return minted


class ExternalToolBridge(MultiHookProcessor):
    """Put environment-executed tool calls into U.

    Register once under ``"*"``.  Costs one pass over the assembled context per
    model call and writes nothing when U recording is off (no recorder → no-op).
    """

    async def on_before_model(self, event):
        bridge_external_tools(getattr(event, "messages", ()) or (), int(getattr(event, "step_id", 0) or 0))
        yield event


def build_external_tool_bridge():
    """Factory for ``config.yaml`` (``file://…/external_tools.py::build_external_tool_bridge``)."""
    return ExternalToolBridge()


__all__ = [
    "ExternalToolBridge",
    "bridge_external_tools",
    "build_external_tool_bridge",
]
