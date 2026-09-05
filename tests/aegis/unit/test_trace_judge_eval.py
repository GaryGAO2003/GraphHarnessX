# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Unit tests for ``GAIAPipelineEvaluator.evaluate_with_trace_judge``.

The legacy ``evaluate_answer`` path relied on a regex over ``final_output``.
It false-negatives whenever the agent emits ``FINAL ANSWER: X`` on an
assistant turn that is not the last one (e.g. after a mid-trajectory
CommitNudge), because ``final_output`` ends up empty. The new path sends
the recent assistant turns + ground truth to an LLM judge.

These tests use a stub provider so they run without any real model call.
"""
from __future__ import annotations

import pytest

from benchmarks.gaia.evaluator import GAIAPipelineEvaluator
from harnessx.core.events import Message


class _StubResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _StubProvider:
    """Echo-style judge: the test sets ``reply`` and every ``.complete``
    call returns it. Also records the prompt it received for inspection."""

    def __init__(self, reply: str = "PASS\ncorrect") -> None:
        self.reply = reply
        self.last_prompt: str = ""
        self.call_count: int = 0

    async def complete(self, messages, tools=None, **kwargs):  # noqa: ARG002
        self.call_count += 1
        self.last_prompt = messages[-1].content if messages else ""
        return _StubResponse(self.reply)


@pytest.mark.asyncio
async def test_judge_primary_path_fires_when_provider_available():
    """With a judge provider, the LLM judge is the PRIMARY grader — not
    the string-match fallback."""
    stub = _StubProvider(reply="PASS\nanswer matches")
    ev = GAIAPipelineEvaluator(judge_provider=stub)

    msgs = [
        Message(role="user", content="what is 2+2?"),
        Message(role="assistant", content="Let me compute... FINAL ANSWER: 4"),
    ]
    result = await ev.evaluate_with_trace_judge(
        task_description="what is 2+2?",
        ground_truth="4",
        final_output="",  # deliberately empty to mimic the bug
        trajectory_messages=msgs,
    )
    assert result.passed is True
    assert stub.call_count == 1
    assert "GROUND TRUTH" in stub.last_prompt
    assert "4" in stub.last_prompt  # gt appears


@pytest.mark.asyncio
async def test_judge_sees_final_answer_on_earlier_turn():
    """The e4e91f1c regression case: FINAL ANSWER emitted at step 17, then
    a later assistant turn (or the final_output extractor) ends up empty.
    Judge should still see the commit and pass."""
    stub = _StubProvider(reply="PASS\nFINAL ANSWER cloak present")
    ev = GAIAPipelineEvaluator(judge_provider=stub)

    msgs = [
        Message(role="user", content="find the word"),
        Message(role="assistant", content="Let me search the database..."),
        Message(role="tool", content="result: cloak"),  # noqa: E501
        Message(role="assistant", content="FINAL ANSWER: cloak"),
        # Post-commit: agent turned once more to verify and produced empty.
        Message(role="assistant", content=""),
    ]
    result = await ev.evaluate_with_trace_judge(
        task_description="find the word",
        ground_truth="cloak",
        final_output="",  # empty despite valid commit earlier
        trajectory_messages=msgs,
    )
    assert result.passed is True
    # The judge's view should include "cloak" from the commit turn.
    assert "cloak" in stub.last_prompt


@pytest.mark.asyncio
async def test_judge_rejects_wrong_answer():
    stub = _StubProvider(reply="FAIL\nanswer says 5 but gt is 4")
    ev = GAIAPipelineEvaluator(judge_provider=stub)

    msgs = [
        Message(role="assistant", content="FINAL ANSWER: 5"),
    ]
    result = await ev.evaluate_with_trace_judge(
        task_description="what is 2+2?",
        ground_truth="4",
        final_output="FINAL ANSWER: 5",
        trajectory_messages=msgs,
    )
    assert result.passed is False


@pytest.mark.asyncio
async def test_falls_back_to_string_match_without_judge():
    """If no judge_provider is configured (e.g. unit tests that don't want
    to mock a model), the method must degrade to ``evaluate_answer``."""
    ev = GAIAPipelineEvaluator(judge_provider=None)

    msgs = [Message(role="assistant", content="FINAL ANSWER: 4")]
    result = await ev.evaluate_with_trace_judge(
        task_description="x",
        ground_truth="4",
        final_output="FINAL ANSWER: 4",
        trajectory_messages=msgs,
    )
    assert result.passed is True


@pytest.mark.asyncio
async def test_empty_trajectory_without_final_output():
    """Empty everywhere — must not raise, must grade FAIL."""
    stub = _StubProvider(reply="FAIL\nempty trace")
    ev = GAIAPipelineEvaluator(judge_provider=stub)
    result = await ev.evaluate_with_trace_judge(
        task_description="x",
        ground_truth="4",
        final_output="",
        trajectory_messages=[],
    )
    assert result.passed is False
    # Judge should NOT have been invoked on empty content — the method
    # short-circuits to FAIL directly.
    assert stub.call_count == 0


@pytest.mark.asyncio
async def test_recent_assistant_turns_capped():
    """The prompt must cap how many assistant turns it includes so a very
    long trajectory doesn't blow the judge's context."""
    stub = _StubProvider(reply="PASS")
    ev = GAIAPipelineEvaluator(judge_provider=stub)

    many_turns = [
        Message(role="assistant", content=f"turn_{i}")
        for i in range(25)
    ]
    # Inject the real answer at the SECOND-TO-LAST turn so the cap (20)
    # still catches it.
    many_turns.append(Message(role="assistant", content="FINAL ANSWER: 42"))
    many_turns.append(Message(role="assistant", content=""))

    await ev.evaluate_with_trace_judge(
        task_description="x",
        ground_truth="42",
        final_output="",
        trajectory_messages=many_turns,
    )
    # Only the last 20 assistant turns with content should appear in the
    # prompt (26 contentful turns above → turn_0..turn_5 fall off).
    assert "turn_0" not in stub.last_prompt
    assert "turn_5" not in stub.last_prompt
    # The boundary turn and the FINAL ANSWER turn (recent) SHOULD be there.
    assert "turn_6" in stub.last_prompt
    assert "42" in stub.last_prompt


@pytest.mark.asyncio
async def test_judge_exception_falls_back_to_string_match():
    """If the judge call raises (network/timeout), fall back to string
    match rather than crashing the whole round."""

    class _FailingProvider:
        async def complete(self, messages, tools=None, **kwargs):  # noqa: ARG002
            raise RuntimeError("simulated network timeout")

    ev = GAIAPipelineEvaluator(judge_provider=_FailingProvider())
    msgs = [Message(role="assistant", content="FINAL ANSWER: 4")]
    result = await ev.evaluate_with_trace_judge(
        task_description="x",
        ground_truth="4",
        final_output="FINAL ANSWER: 4",
        trajectory_messages=msgs,
    )
    # String-match fallback returns True for exact match.
    assert result.passed is True


@pytest.mark.asyncio
async def test_a_commit_at_the_end_of_a_long_turn_reaches_the_judge():
    """Head-only truncation deleted exactly what the grader is told to look for.

    Step 2 of the grading procedure asks the judge to QUOTE the sentence where the
    agent commits, and step 3 makes QUOTE: NONE a mandatory FAIL. A commit lands at
    the end of the turn that makes it, so cutting the head off a long turn hides it.

    Measured on M14's R0: two of thirty-six failing tasks had a correct FINAL ANSWER
    past the cut, one at char 27,249 of 27,275. Both were graded FAIL with the right
    answer sitting in the trajectory.
    """
    judge = _StubProvider(reply="QUOTE: FINAL ANSWER: Green, White\nVERDICT: PASS\nREASON: matches")
    ev = GAIAPipelineEvaluator(judge_provider=judge)

    long_turn = ("filler. " * 6000) + "\nFINAL ANSWER: Green, White"
    assert len(long_turn) > 40_000

    res = await ev.evaluate_with_trace_judge(
        task_description="which two colours",
        ground_truth="green, white",
        final_output="",
        trajectory_messages=[Message(role="assistant", content=long_turn)],
    )

    assert "FINAL ANSWER: Green, White" in judge.last_prompt, (
        "the commit sentence must survive truncation — it is the one thing the "
        "grading procedure asks the judge to find"
    )
    assert res.passed is True


@pytest.mark.asyncio
async def test_the_opening_of_a_long_turn_is_kept_too():
    """Tail-only would lose what the turn set out to do, which is how the judge
    tells a commit from a restatement of the question."""
    judge = _StubProvider(reply="QUOTE: NONE\nVERDICT: FAIL\nREASON: none")
    ev = GAIAPipelineEvaluator(judge_provider=judge)

    turn = "OPENING-MARKER I will check three sources. " + ("x" * 40_000) + " CLOSING-MARKER"
    await ev.evaluate_with_trace_judge(
        task_description="q", ground_truth="a", final_output="",
        trajectory_messages=[Message(role="assistant", content=turn)],
    )
    assert "OPENING-MARKER" in judge.last_prompt
    assert "CLOSING-MARKER" in judge.last_prompt
    assert "elided" in judge.last_prompt, "the gap must be marked, not silently closed"


@pytest.mark.asyncio
async def test_a_short_turn_is_passed_through_untouched():
    judge = _StubProvider(reply="QUOTE: x\nVERDICT: PASS\nREASON: y")
    ev = GAIAPipelineEvaluator(judge_provider=judge)
    await ev.evaluate_with_trace_judge(
        task_description="q", ground_truth="a", final_output="",
        trajectory_messages=[Message(role="assistant", content="short and whole")],
    )
    assert "short and whole" in judge.last_prompt
    assert "elided" not in judge.last_prompt
