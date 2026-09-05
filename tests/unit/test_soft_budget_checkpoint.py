# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Offline tests for SoftBudgetCheckpointProcessor (M27 T3.3).

All fully offline — no network, no rollouts, no LLM.
"""

from __future__ import annotations

import asyncio

from harnessx.core.events import (
    BeforeModelEvent,
    Message,
    StepEndEvent,
    StepStartEvent,
    TaskEndEvent,
    TaskStartEvent,
)
from harnessx.processors.control.soft_budget_checkpoint import (
    CHECKPOINT_MARKER,
    SoftBudgetCheckpointProcessor,
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


class _Task:
    def __init__(self, max_steps=50, token_budget=None, max_cost_usd=None):
        self.max_steps = max_steps
        self.token_budget = token_budget
        self.max_cost_usd = max_cost_usd


def _has_marker(msgs) -> bool:
    return any(isinstance(m.content, str) and CHECKPOINT_MARKER in m.content for m in msgs)


def _start(proc, task: "_Task | None" = None, run_id: str = "r1"):
    _run(proc, TaskStartEvent(run_id=run_id, step_id=0))
    if task is not None:
        _run(proc, StepStartEvent(run_id=run_id, step_id=0, task=task, messages=_tool_tail(0)))


# ===========================================================================
# Steps dimension
# ===========================================================================


def test_no_nudge_below_ratio_on_steps():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=10))
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=6, messages=_tool_tail(6)))  # 7/10 = 0.70
    assert not _has_marker(bm.messages)


def test_nudge_fires_at_ratio_crossing_on_steps():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=10))
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=7, messages=_tool_tail(7)))  # 8/10 = 0.80
    assert _has_marker(bm.messages)
    assert "steps" in bm.messages[-1].content


def test_fires_at_most_once_per_run():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=10))
    bm1 = _run(proc, BeforeModelEvent(run_id="r1", step_id=7, messages=_tool_tail(7)))
    assert _has_marker(bm1.messages)
    bm2 = _run(proc, BeforeModelEvent(run_id="r1", step_id=8, messages=_tool_tail(8)))
    assert not _has_marker(bm2.messages)


# ===========================================================================
# Token dimension (cached from StepEndEvent)
# ===========================================================================


def test_token_ratio_triggers_from_step_end_cache():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=1000, token_budget=1000))
    _run(proc, StepEndEvent(run_id="r1", step_id=0, cumulative_tokens=800))  # 0.80
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=1, messages=_tool_tail(1)))
    assert _has_marker(bm.messages)
    assert "tokens" in bm.messages[-1].content


def test_token_dimension_skipped_when_no_budget_set():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=1000, token_budget=None))
    _run(proc, StepEndEvent(run_id="r1", step_id=0, cumulative_tokens=10_000_000))  # huge, but untracked
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=1, messages=_tool_tail(1)))
    assert not _has_marker(bm.messages)


# ===========================================================================
# Cost dimension (real-time from BeforeModelEvent)
# ===========================================================================


def test_cost_ratio_triggers_from_before_model_event():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=1000, max_cost_usd=1.0))
    bm = _run(
        proc,
        BeforeModelEvent(run_id="r1", step_id=1, messages=_tool_tail(1), cumulative_cost_usd=0.80),
    )
    assert _has_marker(bm.messages)
    assert "cost" in bm.messages[-1].content


def test_cost_below_ratio_no_trigger():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=1000, max_cost_usd=1.0))
    bm = _run(
        proc,
        BeforeModelEvent(run_id="r1", step_id=1, messages=_tool_tail(1), cumulative_cost_usd=0.50),
    )
    assert not _has_marker(bm.messages)


# ===========================================================================
# Injection seam: append vs edit-last-user
# ===========================================================================


def test_appends_user_message_when_tail_is_not_user():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=10))
    tail = _tool_tail(7)
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=7, messages=tail))
    assert len(bm.messages) == len(tail) + 1
    assert bm.messages[-1].role == "user"
    assert CHECKPOINT_MARKER in bm.messages[-1].content


def test_edits_last_user_content_when_tail_is_user():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=10))
    base = (Message(role="system", content="sys"), Message(role="user", content="the task?"))
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=7, messages=base))
    assert len(bm.messages) == len(base)
    assert bm.messages[-1].content.startswith("the task?")
    assert CHECKPOINT_MARKER in bm.messages[-1].content
    assert bm.messages[:-1] == base[:-1]


# ===========================================================================
# Distinct from RunLoop's own 70% cost warning
# ===========================================================================


def test_marker_distinct_from_runloop_cost_warning_text():
    assert CHECKPOINT_MARKER != "[COST WARNING:"
    assert "COST WARNING" not in CHECKPOINT_MARKER


# ===========================================================================
# Per-task reset
# ===========================================================================


def test_reset_on_task_end_and_new_run_id():
    proc = SoftBudgetCheckpointProcessor(ratio=0.75)
    _start(proc, _Task(max_steps=10))
    _run(proc, BeforeModelEvent(run_id="r1", step_id=7, messages=_tool_tail(7)))
    assert proc._fired is True

    _run(proc, TaskEndEvent(run_id="r1", step_id=8))
    assert proc._fired is False
    assert proc._max_steps is None

    # new run_id also resets defensively via on_step_start
    proc._fired = True
    _run(proc, StepStartEvent(run_id="r2", step_id=0, task=_Task(max_steps=10), messages=_tool_tail(0)))
    assert proc._fired is False
