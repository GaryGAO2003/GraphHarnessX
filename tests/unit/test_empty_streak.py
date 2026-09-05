# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Offline tests for EmptyStreakEscalationProcessor (M27 T3.1).

All fully offline — no network, no rollouts, no LLM. Drives the processor
directly via its real ``_DISPATCH`` (``proc.process(event)``), same harness
used by ``experiments/variant_pool/tests/test_step_countdown.py``.
"""

from __future__ import annotations

import asyncio

from harnessx.core.events import (
    BeforeModelEvent,
    Message,
    StepStartEvent,
    TaskEndEvent,
    TaskStartEvent,
    ToolResultEvent,
)
from harnessx.processors.control.empty_streak import (
    EMPTY_STREAK_MARKER,
    EmptyStreakEscalationProcessor,
)


def _run(proc, event):
    async def _collect():
        return [ev async for ev in proc.process(event)]

    return asyncio.run(_collect())[-1]


def _tool_tail(step: int):
    return (
        Message(role="assistant", content=f"thinking {step}"),
        Message(role="tool", content=f"result {step}", tool_call_id=f"c{step}", name="web_search"),
    )


def _tool_result(step: int, *, result: str = "", error: "str | None" = None):
    return ToolResultEvent(run_id="r1", step_id=step, tool_name="WebSearch", tool_call_id=f"c{step}", result=result, error=error)


def _has_marker(msgs) -> bool:
    return any(isinstance(m.content, str) and EMPTY_STREAK_MARKER in m.content for m in msgs)


# ===========================================================================
# Outcome classification feeds the streak
# ===========================================================================


def test_error_result_counts_toward_streak():
    proc = EmptyStreakEscalationProcessor(k=2)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="timeout"))
    assert proc._streak == 1
    _run(proc, _tool_result(1, error="timeout"))
    assert proc._pending_nudge is True
    assert proc._streak == 0  # reset immediately on trigger


def test_empty_result_counts_toward_streak():
    proc = EmptyStreakEscalationProcessor(k=3)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, result=""))
    _run(proc, _tool_result(1, result="   "))
    assert proc._streak == 2
    assert proc._pending_nudge is False


def test_short_ok_result_counts_as_unhelpful():
    proc = EmptyStreakEscalationProcessor(k=2, min_content_chars=20)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, result="ok"))  # non-empty, non-error, but too short
    assert proc._streak == 1


def test_long_ok_result_resets_streak():
    proc = EmptyStreakEscalationProcessor(k=3, min_content_chars=20)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="timeout"))
    _run(proc, _tool_result(1, error="timeout"))
    assert proc._streak == 2
    _run(proc, _tool_result(2, result="a genuinely useful and long enough result here"))
    assert proc._streak == 0
    assert proc._pending_nudge is False


# ===========================================================================
# Nudge fires once per streak, via on_before_model
# ===========================================================================


def test_nudge_injected_exactly_once_after_k_unhelpful_results():
    proc = EmptyStreakEscalationProcessor(k=3)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    for i in range(3):
        _run(proc, _tool_result(i, error="err"))
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=3, messages=_tool_tail(3)))
    assert _has_marker(bm.messages)
    assert sum(isinstance(m.content, str) and EMPTY_STREAK_MARKER in m.content for m in bm.messages) == 1

    # a second before_model with no new unhelpful outcomes injects nothing
    bm2 = _run(proc, BeforeModelEvent(run_id="r1", step_id=4, messages=_tool_tail(4)))
    assert not _has_marker(bm2.messages)


def test_new_streak_after_reset_fires_again():
    proc = EmptyStreakEscalationProcessor(k=2)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="e"))
    _run(proc, _tool_result(1, error="e"))
    bm1 = _run(proc, BeforeModelEvent(run_id="r1", step_id=2, messages=_tool_tail(2)))
    assert _has_marker(bm1.messages)

    # build a second streak of length k
    _run(proc, _tool_result(2, error="e"))
    _run(proc, _tool_result(3, error="e"))
    bm2 = _run(proc, BeforeModelEvent(run_id="r1", step_id=4, messages=_tool_tail(4)))
    assert _has_marker(bm2.messages)


def test_below_threshold_never_fires():
    proc = EmptyStreakEscalationProcessor(k=3)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="e"))
    _run(proc, _tool_result(1, error="e"))  # only 2 of 3
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=2, messages=_tool_tail(2)))
    assert not _has_marker(bm.messages)


# ===========================================================================
# Injection seam: append vs edit-last-user, hook contract compliant
# ===========================================================================


def test_appends_user_message_when_tail_is_not_user():
    proc = EmptyStreakEscalationProcessor(k=1)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="e"))
    tail = _tool_tail(0)
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=0, messages=tail))
    assert len(bm.messages) == len(tail) + 1
    assert bm.messages[-1].role == "user"
    assert EMPTY_STREAK_MARKER in bm.messages[-1].content


def test_edits_last_user_content_when_tail_is_user():
    proc = EmptyStreakEscalationProcessor(k=1)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="e"))
    base = (Message(role="system", content="sys"), Message(role="user", content="the task?"))
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=0, messages=base))
    assert len(bm.messages) == len(base)  # no new message
    assert bm.messages[-1].content.startswith("the task?")
    assert EMPTY_STREAK_MARKER in bm.messages[-1].content
    assert bm.messages[:-1] == base[:-1]


# ===========================================================================
# Per-task reset
# ===========================================================================


def test_reset_on_task_end_and_new_run_id():
    proc = EmptyStreakEscalationProcessor(k=2)
    _run(proc, TaskStartEvent(run_id="r1", step_id=0))
    _run(proc, _tool_result(0, error="e"))
    assert proc._streak == 1

    _run(proc, TaskEndEvent(run_id="r1", step_id=1))
    assert proc._streak == 0
    assert proc._pending_nudge is False

    # a new run_id also resets defensively via on_step_start
    proc._streak = 1  # simulate stale state
    _run(proc, StepStartEvent(run_id="r2", step_id=0, messages=_tool_tail(0)))
    assert proc._streak == 0
