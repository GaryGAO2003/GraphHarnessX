# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
from __future__ import annotations

import dataclasses
import re
import uuid

from ...core.events import (
    BeforeModelEvent,
    Message,
    ModelResponseEvent,
    TaskEndEvent,
    TaskStartEvent,
    ToolCall,
    ToolCallEvent,
    ToolResultEvent,
)
from ...core.processor import MultiHookProcessor

try:
    from ...graph.unfold import classify_tool_outcome
except ImportError:  # pragma: no cover - defensive; harnessx.graph ships with this package

    def classify_tool_outcome(result, error=None, content_blocks=()) -> str:
        if error:
            return "error"
        payload = content_blocks or result
        if isinstance(payload, (list, tuple)):
            parts = []
            for blk in payload:
                if isinstance(blk, dict):
                    parts.append(str(blk.get("text") or blk.get("content") or ""))
                else:
                    parts.append("" if blk is None else str(blk))
            text = "\n".join(parts)
        elif payload is None:
            text = ""
        else:
            text = str(payload)
        return "empty" if not text.strip() else "ok"


#: Synthetic tool intercepted (never actually executed) to buy one more model
#: step for the forced verification retry — same trick as ``SelfVerifyProcessor``.
_SYNTHETIC_TOOL = "_answer_grounding_keepalive"
_KEEPALIVE_ACK = "Verification check initiated. See the message above for what to verify."

#: Stable marker prefixing the injected nudge.
GROUNDING_MARKER = "[answer-grounding]"

_VERIFY_NUDGE = (
    "[answer-grounding] Your answer above does not clearly match anything retrieved "
    "in this conversation — it may be unsupported or fabricated. Before finalizing: "
    "do ONE more verification retrieval step (re-check a tool result, search again, "
    "or re-read the relevant file) that directly supports your answer, then restate "
    "your FINAL ANSWER. If you still cannot find supporting evidence, say so "
    "explicitly and flag low confidence instead of asserting the answer as fact."
)

_MIN_OVERLAP_CHARS = 20
_WHITESPACE_RE = re.compile(r"\s+")


def _flatten(payload) -> str:
    """Best-effort flatten of a str / content-block-list payload to plain text.

    Mirrors the flatten :func:`classify_tool_outcome` (graph/unfold.py) uses,
    so "what counts as evidence text" here is the same text the model actually
    saw, not a re-derived approximation.
    """
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (list, tuple)):
        parts = []
        for blk in payload:
            if isinstance(blk, dict):
                parts.append(str(blk.get("text") or blk.get("content") or ""))
            else:
                parts.append("" if blk is None else str(blk))
        return "\n".join(parts)
    if payload is None:
        return ""
    return str(payload)


def _normalize(text: str) -> str:
    """Casefold + collapse whitespace so trivial formatting differences don't
    defeat containment/overlap checks."""
    return _WHITESPACE_RE.sub(" ", text).strip().casefold()


def _overlap_segment(answer: str, evidence: str, min_len: int) -> "str | None":
    """First contiguous substring of *answer*, length >= *min_len*, found in
    *evidence* — or ``None``. Both inputs are assumed already normalized."""
    if len(answer) < min_len:
        return None
    for i in range(len(answer) - min_len + 1):
        seg = answer[i : i + min_len]
        if seg in evidence:
            return seg
    return None


class AnswerGroundingProcessor(MultiHookProcessor):
    """Require a final answer to be grounded in retrieved evidence (W4·C1 stabilizer #2).

    Evidence (docs/ghx-overnight-0823-research.md, W4·C1): 62% of fixable-task
    failures are "done with a wrong answer" after a long, unproductive path —
    the model asserts an answer that traces to nothing it actually retrieved.
    This is also the paper-level symmetry the doc calls out: V3's audit
    framework names "whether output was actually used" (F1-F8) as a quantity
    the *measurement* loop cannot test — this processor forces exactly that
    quantity at the one place it CAN be forced: the answer boundary.

    Groundedness check (normalized, casefold + whitespace-collapsed)
        1. **Containment** — the full answer string appears inside some
           non-empty tool result seen this run. Primary direction: V3's F3
           lesson was that a naive character-length floor fails on short
           answers ("Paris", "42") — containment has no length floor, so it
           covers exactly that case.
        2. **Overlap** — failing (1), a contiguous substring of the answer of
           length >= 20 chars is found inside some tool result.
        Either match is discarded (does NOT count as grounding) if the
        matched text ALSO appears in the task prompt — otherwise the model
        gets credit for merely echoing the question back, which the C1
        analysis flagged as the critical false-positive to avoid.

    Enforcement (M13 lesson: nudge, never hard-stop)
        On an ungrounded final answer, ONE forced verification retry is
        injected per run (a synthetic keep-alive tool call — mirrors
        :class:`SelfVerifyProcessor` — buys one more model step, then a
        verification nudge is delivered via ``on_before_model``). After that
        one retry the answer is allowed to pass regardless of groundedness —
        this is a nudge, not a gate that can loop or block.

    Args:
        enabled: Set to ``False`` to disable without removing from the builder.
    """

    _singleton_group = "answer_grounding"
    _order = 95  # post-verification tier, after SelfVerifyProcessor (90)

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

        self._tool_results: list[str] = []  # normalized, non-empty tool-result texts
        self._task_prompt: str = ""  # normalized task prompt text (for echo exclusion)
        self._retried: bool = False  # at most one forced retry per run
        self._pending_user_message: str = ""

    # ------------------------------------------------------------------
    # Per-task reset
    # ------------------------------------------------------------------

    def _reset(self) -> None:
        self._tool_results = []
        self._task_prompt = ""
        self._retried = False
        self._pending_user_message = ""

    async def on_task_start(self, event: TaskStartEvent):
        self._reset()
        self._task_prompt = _normalize(_flatten(event.task_description))
        yield event

    # ------------------------------------------------------------------
    # Evidence collection
    # ------------------------------------------------------------------

    async def on_after_tool(self, event: ToolResultEvent):
        outcome = classify_tool_outcome(event.result, error=event.error, content_blocks=event.content_blocks)
        if outcome == "ok":
            payload = event.content_blocks if event.content_blocks else event.result
            norm = _normalize(_flatten(payload))
            if norm:
                self._tool_results.append(norm)
        yield event

    # ------------------------------------------------------------------
    # Groundedness check
    # ------------------------------------------------------------------

    def _is_grounded(self, answer: str) -> bool:
        norm_answer = _normalize(answer)
        if not norm_answer:
            return True  # nothing to check; not this processor's concern
        for evidence in self._tool_results:
            if norm_answer in evidence:
                if norm_answer in self._task_prompt:
                    continue  # task-echo exclusion: not real evidence
                return True
            seg = _overlap_segment(norm_answer, evidence, _MIN_OVERLAP_CHARS)
            if seg is not None and seg not in self._task_prompt:
                return True
        return False

    # ------------------------------------------------------------------
    # Enforcement — keepalive + nudge (SelfVerifyProcessor pattern)
    # ------------------------------------------------------------------

    async def on_after_model(self, event: ModelResponseEvent):
        if not self.enabled:
            yield event
            return

        exit_intent = event.finish_reason in ("end_turn", "stop") and not event.tool_calls
        if not exit_intent or self._retried:
            yield event
            return

        answer = (event.content or "").strip()
        if not answer or self._is_grounded(answer):
            yield event
            return

        self._retried = True  # gate: at most one forced retry per run
        self._pending_user_message = _VERIFY_NUDGE
        keepalive = ToolCall(id=f"grnd-{uuid.uuid4().hex[:8]}", name=_SYNTHETIC_TOOL, input={})
        yield dataclasses.replace(event, tool_calls=(keepalive,))

    async def on_before_tool(self, event: ToolCallEvent):
        if event.tool_name == _SYNTHETIC_TOOL:
            yield dataclasses.replace(event, approved=False, synthetic_result=_KEEPALIVE_ACK)
        else:
            yield event

    async def on_before_model(self, event: BeforeModelEvent):
        if not self.enabled or not self._pending_user_message:
            yield event
            return
        line = self._pending_user_message
        self._pending_user_message = ""

        msgs = event.messages
        if msgs and msgs[-1].role == "user" and isinstance(msgs[-1].content, str):
            last = msgs[-1]
            merged = f"{last.content}\n\n{line}" if last.content else line
            new_last = dataclasses.replace(last, content=merged)
            yield dataclasses.replace(event, messages=msgs[:-1] + (new_last,))
        else:
            yield dataclasses.replace(event, messages=msgs + (Message(role="user", content=line),))

    async def on_task_end(self, event: TaskEndEvent):
        self._reset()
        yield event
