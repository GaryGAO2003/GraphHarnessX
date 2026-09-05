# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Offline tests for AnswerGroundingProcessor (M27 T3.2).

All fully offline — no network, no rollouts, no LLM.
"""

from __future__ import annotations

import asyncio

from harnessx.core.events import (
    BeforeModelEvent,
    Message,
    ModelResponseEvent,
    TaskEndEvent,
    TaskStartEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from harnessx.processors.control.answer_grounding import (
    GROUNDING_MARKER,
    _SYNTHETIC_TOOL,
    AnswerGroundingProcessor,
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


def _tool_result(step: int, text: str):
    return ToolResultEvent(run_id="r1", step_id=step, tool_name="WebSearch", tool_call_id=f"c{step}", result=text)


def _final_answer(step: int, content: str, run_id: str = "r1"):
    return ModelResponseEvent(run_id=run_id, step_id=step, content=content, finish_reason="end_turn", tool_calls=())


def _start(proc, prompt: str = "What is the capital of France?", run_id: str = "r1"):
    _run(proc, TaskStartEvent(run_id=run_id, step_id=0, task_description=prompt))


# ===========================================================================
# Groundedness: containment (short answers) and overlap (long answers)
# ===========================================================================


def test_short_answer_grounded_by_full_containment():
    proc = AnswerGroundingProcessor()
    _start(proc)
    _run(proc, _tool_result(0, "The capital of France is Paris, population 2.1M."))
    resp = _run(proc, _final_answer(1, "Paris"))
    assert resp.tool_calls == ()  # allowed through, no forced retry
    assert not proc._retried


def test_ungrounded_answer_triggers_forced_retry_keepalive():
    proc = AnswerGroundingProcessor()
    _start(proc)
    _run(proc, _tool_result(0, "Nothing relevant found here at all."))
    resp = _run(proc, _final_answer(1, "The Eiffel Tower is 330 meters tall."))
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == _SYNTHETIC_TOOL
    assert proc._retried is True


def test_long_answer_grounded_by_20char_overlap():
    proc = AnswerGroundingProcessor()
    _start(proc)
    evidence = "According to the 2023 census, the population of the city was 8.4 million residents in total."
    _run(proc, _tool_result(0, evidence))
    # Answer paraphrases but shares a long contiguous chunk with the evidence.
    answer = "Based on my research, the population of the city was 8.4 million residents according to records."
    resp = _run(proc, _final_answer(1, answer))
    assert resp.tool_calls == ()


def test_no_evidence_at_all_is_ungrounded():
    proc = AnswerGroundingProcessor()
    _start(proc)
    resp = _run(proc, _final_answer(1, "The answer is 42."))
    assert len(resp.tool_calls) == 1


# ===========================================================================
# Task-echo exclusion — critical C1 lesson
# ===========================================================================


def test_task_echo_excluded_even_if_verbatim_in_tool_result():
    prompt = "What is the capital of France, a country in Western Europe with a long coastline?"
    proc = AnswerGroundingProcessor()
    _start(proc, prompt=prompt)
    # Tool result happens to also contain the prompt text verbatim (e.g. a
    # search engine echoing the query) plus nothing else useful.
    _run(proc, _tool_result(0, f"Search query: {prompt}"))
    answer = "a country in Western Europe with a long coastline"
    resp = _run(proc, _final_answer(1, answer))
    assert len(resp.tool_calls) == 1  # excluded as echo -> still ungrounded


def test_task_echo_does_not_block_genuine_new_evidence():
    prompt = "What is the capital of France?"
    proc = AnswerGroundingProcessor()
    _start(proc, prompt=prompt)
    _run(proc, _tool_result(0, f"{prompt} The capital of France is Paris."))
    resp = _run(proc, _final_answer(1, "Paris"))
    assert resp.tool_calls == ()  # "Paris" isn't in the prompt -> genuine evidence


# ===========================================================================
# At most one forced retry per run
# ===========================================================================


def test_only_one_forced_retry_per_run_then_answer_passes():
    proc = AnswerGroundingProcessor()
    _start(proc)
    _run(proc, _tool_result(0, "irrelevant text"))
    resp1 = _run(proc, _final_answer(1, "unsupported claim one"))
    assert len(resp1.tool_calls) == 1  # first ungrounded answer -> forced retry

    resp2 = _run(proc, _final_answer(2, "unsupported claim two"))
    assert resp2.tool_calls == ()  # second ungrounded answer -> allowed through


# ===========================================================================
# Synthetic keepalive interception (never a real tool call)
# ===========================================================================


def test_keepalive_tool_call_intercepted_not_executed():
    proc = AnswerGroundingProcessor()
    tc = ToolCallEvent(run_id="r1", step_id=1, tool_name=_SYNTHETIC_TOOL, tool_call_id="grnd-1")
    out = _run(proc, tc)
    assert out.approved is False
    assert out.synthetic_result


def test_unrelated_tool_call_passes_through():
    proc = AnswerGroundingProcessor()
    tc = ToolCallEvent(run_id="r1", step_id=1, tool_name="Bash", tool_call_id="c1")
    out = _run(proc, tc)
    assert out.approved is True
    assert out.synthetic_result is None


# ===========================================================================
# Nudge delivery via on_before_model
# ===========================================================================


def test_nudge_delivered_next_before_model_after_forced_retry():
    proc = AnswerGroundingProcessor()
    _start(proc)
    _run(proc, _tool_result(0, "irrelevant"))
    _run(proc, _final_answer(1, "unsupported claim"))  # sets pending message
    tail = _tool_tail(1)
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=2, messages=tail))
    assert len(bm.messages) == len(tail) + 1
    assert GROUNDING_MARKER in bm.messages[-1].content

    # not injected again on the following step
    bm2 = _run(proc, BeforeModelEvent(run_id="r1", step_id=3, messages=_tool_tail(3)))
    assert not any(isinstance(m.content, str) and GROUNDING_MARKER in m.content for m in bm2.messages)


def test_nudge_edits_last_user_when_tail_is_user():
    proc = AnswerGroundingProcessor()
    _start(proc)
    _run(proc, _tool_result(0, "irrelevant"))
    _run(proc, _final_answer(1, "unsupported claim"))
    base = (Message(role="system", content="sys"), Message(role="user", content="continue?"))
    bm = _run(proc, BeforeModelEvent(run_id="r1", step_id=2, messages=base))
    assert len(bm.messages) == len(base)
    assert GROUNDING_MARKER in bm.messages[-1].content
    assert bm.messages[:-1] == base[:-1]


# ===========================================================================
# Per-task reset
# ===========================================================================


def test_reset_on_task_end():
    proc = AnswerGroundingProcessor()
    _start(proc)
    _run(proc, _tool_result(0, "some evidence text"))
    _run(proc, _final_answer(1, "unsupported"))
    assert proc._retried is True
    assert proc._tool_results

    _run(proc, TaskEndEvent(run_id="r1", step_id=2))
    assert proc._retried is False
    assert proc._tool_results == []
    assert proc._task_prompt == ""
