# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Give the τ² digester the whole conversation, not the harness's half.

The journal records what happens *inside* ``Harness.run``.  On τ² that is only
the agent's own turns: the user's replies and the tool results are produced by
the environment between two runs and injected by the adapter, so the journal
never witnesses them.  The trajectory the Digester reads was a copy of that
journal — eleven assistant messages, one user message, no tool results, for a
conversation that actually had twenty-odd turns.

Every downstream reader inherits that blindness.  It is not hypothetical: on the
first live round the Critic checked a candidate's premise against the recorded
trajectory, found no system message, and reported the premise fabricated — a
correct procedure over an incomplete record.

τ²'s own simulation record has the whole conversation (it is what the benchmark
grades), so nothing needs to be reconstructed: the two halves are merged, with
the journal's richer view of the agent's turns kept as-is and the environment's
turns inserted where they belong.
"""
from __future__ import annotations

import logging

_LOG = logging.getLogger(__name__)

_ASSISTANT_EVENTS = ("raw_assistant", "assistant")


def _attr(msg, name: str, default=None):
    """τ² messages are pydantic models here and plain dicts in fixtures."""
    if isinstance(msg, dict):
        return msg.get(name, default)
    return getattr(msg, name, default)


def _role(msg) -> str:
    return str(_attr(msg, "role", "") or "")


def _as_event(msg, session_id: str, step: int) -> dict | None:
    """One τ² message in the journal's event shape, or ``None`` to skip it."""
    role = _role(msg)
    if role == "user":
        etype, payload = "raw_user", {"role": "user", "content": _attr(msg, "content", "") or ""}
    elif role == "tool":
        # "raw_tool" is the name the vendored fact extractor indexes on
        # (trace_facts.py builds its tool_call_id → result map from it); an
        # event typed "tool" is silently invisible and every call reads back
        # return_type=missing.
        etype = "raw_tool"
        payload = {
            "role": "tool",
            "content": _attr(msg, "content", "") or "",
            "tool_call_id": _attr(msg, "id", None) or _attr(msg, "tool_call_id", None),
            "name": _attr(msg, "name", None) or _attr(msg, "requestor", None),
        }
    elif role == "system":
        etype, payload = "raw_system", {"role": "system", "content": _attr(msg, "content", "") or ""}
    else:
        return None  # assistant turns come from the journal, which knows more
    return {
        "session_id": session_id,
        "type": etype,
        "step": step,
        "message": payload,
        "meta": {"source": "tau2_env"},
    }


def merge_environment_turns(journal_events: list, tau2_messages: list, session_id: str = "") -> list:
    """The journal's events with τ²'s environment turns inserted in order.

    The two records agree on the agent's turns and on their order, so those are
    the seam: everything τ² shows before its k-th assistant message belongs
    before the journal's k-th assistant event.  Journal-only events (step
    boundaries, injected steers, ``episode_end``) keep their places, which is why
    this merges rather than replacing the file with τ²'s view.

    Degrades to the journal unchanged when τ² has nothing to add.
    """
    if not tau2_messages:
        return list(journal_events)

    # Where each assistant turn sits in tau2's transcript.
    assistant_at = [i for i, m in enumerate(tau2_messages) if _role(m) == "assistant"]
    out: list = []
    cursor = 0  # next unemitted tau2 message
    seen_assistants = 0

    def _flush(upto: int, step: int) -> None:
        nonlocal cursor
        while cursor < upto:
            ev = _as_event(tau2_messages[cursor], session_id, step)
            if ev is not None:
                out.append(ev)
            cursor += 1

    for event in journal_events:
        if str(event.get("type", "")) in _ASSISTANT_EVENTS:
            boundary = (
                assistant_at[seen_assistants] if seen_assistants < len(assistant_at) else len(tau2_messages)
            )
            _flush(boundary, int(event.get("step", 0) or 0))
            cursor = min(boundary + 1, len(tau2_messages))  # the journal owns this turn
            seen_assistants += 1
        out.append(event)

    # Whatever the conversation ended with (the final user turn, trailing tool
    # results) has no assistant event after it to anchor on.
    last_step = int(journal_events[-1].get("step", 0) or 0) if journal_events else 0
    _flush(len(tau2_messages), last_step)
    return _collapse_episode_ends(out)


def _collapse_episode_ends(events: list) -> list:
    """One ``episode_end`` for the conversation, not one per turn.

    A turn ending is not the episode ending: the adapter calls ``Harness.run``
    once per turn, so the journal holds an ``episode_end`` for each, and the
    first of them says ``interrupted`` with zero steps.  Readers that expect the
    GAIA shape take the FIRST one (vendored ``trace_facts.py`` does, and it is
    byte-frozen), so every tau2 trajectory reported a zero-step interrupted run.

    The surviving record is the last turn's — the one that actually ended the
    conversation — with ``total_steps`` summed over the turns, which is
    arithmetic over observed values rather than a new claim.
    """
    ends = [e for e in events if str(e.get("type", "")) == "episode_end"]
    if not ends:
        return events
    final = dict(ends[-1])
    if len(ends) > 1:
        total = 0
        for e in ends:
            try:
                total += int(e.get("total_steps") or 0)
            except (TypeError, ValueError):
                pass
        final["total_steps"] = total
        meta = final.get("meta")
        final["meta"] = {**meta, "collapsed_turn_ends": len(ends)} if isinstance(meta, dict) else {
            "collapsed_turn_ends": len(ends)
        }
    # Always last: a trailing environment turn is flushed after the journal's
    # own events, and an episode_end sitting mid-file reads as a truncated run.
    out = [e for e in events if str(e.get("type", "")) != "episode_end"]
    out.append(final)
    return out


def merged_trajectory_lines(journal_events: list, tau2_messages: list, session_id: str = "") -> list:
    """``merge_environment_turns`` rendered as JSONL text lines."""
    import json

    return [
        json.dumps(e, ensure_ascii=False) + "\n" for e in merge_environment_turns(journal_events, tau2_messages, session_id)
    ]


__all__ = ["merge_environment_turns", "merged_trajectory_lines"]
