# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
from __future__ import annotations

import dataclasses

from ...core.events import (
    BeforeModelEvent,
    Message,
    StepStartEvent,
    TaskEndEvent,
    TaskStartEvent,
    ToolResultEvent,
)
from ...core.processor import MultiHookProcessor

try:
    # Canonical outcome stamp (M23/M24) — "error" / "empty" / "ok" judged on the
    # FLATTENED payload (text of content blocks), not a bare str(result). Reusing
    # it keeps "what counts as empty" identical to what U and the digest side
    # already use, instead of a third, drifting definition here.
    from ...graph.unfold import classify_tool_outcome
except ImportError:  # pragma: no cover - defensive; harnessx.graph ships with this package

    def classify_tool_outcome(result, error=None, content_blocks=()) -> str:
        """Minimal local fallback matching graph/unfold.py's contract."""
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


#: Stable marker prefixing the injected nudge — lets the model (and tests)
#: recognise it unambiguously.
EMPTY_STREAK_MARKER = "[empty-streak]"

_NUDGE_TEMPLATE = (
    "[empty-streak] {count} consecutive tool results in a row have come back empty, "
    "errored, or too short to be useful. Change your strategy now: reformulate your "
    "query with different terms, try a different tool, or — if the information "
    "genuinely cannot be found — say so explicitly and flag low confidence in your "
    "final answer instead of repeating the same approach."
)


class EmptyStreakEscalationProcessor(MultiHookProcessor):
    """Escalate when tool results stop returning anything useful (W4·C1 stabilizer #1).

    Evidence (docs/ghx-overnight-0823-research.md, W4·C1): of the 28-task
    LOCALIZED-FIXABLE pool, 11 failing trajectories show an empty-result rate
    >=20pp higher than the passing trajectory of the same task — the failing
    run hits empty/error results and does not change strategy ("撞空不改策略,
    磨到没劲然后编造"). This processor is the result-quality sibling of
    :class:`~harnessx.processors.control.loop_detection.LoopDetectionProcessor`
    (which keys on repeated *calls*; this one keys on repeated *outcomes*).

    Outcome classification
        Each ``ToolResultEvent`` is judged via :func:`classify_tool_outcome`
        (``"error"`` / ``"empty"`` / ``"ok"``, on the flattened payload — the
        same stamp U and the digest side use). An ``"ok"`` outcome whose
        flattened text is still shorter than ``min_content_chars`` after
        ``strip()`` is *also* treated as unhelpful — a technically-non-empty
        one-word result is not evidence either.

    Streak + escalation (M13 lesson: nudge, never hard-stop)
        Consecutive unhelpful outcomes are counted; an "ok"-and-long-enough
        result resets the streak to 0. On reaching ``k`` (default 3), exactly
        ONE user-role nudge is queued and the streak counter is reset to 0 —
        so it fires once per streak, not once per step thereafter, mirroring
        the escalate-once discipline other stabilizers in this package use.

    Injection seam — ``on_before_model``
        Same seam as :class:`StepCountdownProcessor` / ``CostGuardProcessor``'s
        neighbours: edit the last message's content when the tail is already a
        plain-text ``user`` turn (zero net length change); otherwise append
        exactly one fresh ``user`` message (the only insertion the
        ``before_model`` hook contract allows when the tail is not ``user``).

    Args:
        k:                Consecutive unhelpful-outcome count that triggers
                          the nudge (default 3).
        min_content_chars: Minimum stripped-text length for an "ok" outcome to
                          NOT be treated as unhelpful (default 20).
    """

    _singleton_group = "empty_streak"
    _order = 25  # right after loop_detection (20) — its result-quality sibling

    def __init__(self, k: int = 3, min_content_chars: int = 20):
        self.k = k
        self.min_content_chars = min_content_chars

        self._streak: int = 0
        self._pending_nudge: bool = False
        self._current_run_id: str = ""

    # ------------------------------------------------------------------
    # Per-task reset (LoopDetectionProcessor idiom)
    # ------------------------------------------------------------------

    def _reset(self) -> None:
        self._streak = 0
        self._pending_nudge = False

    async def on_task_start(self, event: TaskStartEvent):
        self._reset()
        self._current_run_id = event.run_id
        yield event

    async def on_step_start(self, event: StepStartEvent):
        if event.run_id != self._current_run_id:
            self._reset()
            self._current_run_id = event.run_id
        yield event

    # ------------------------------------------------------------------
    # Outcome tracking
    # ------------------------------------------------------------------

    def _is_unhelpful(self, event: ToolResultEvent) -> bool:
        outcome = classify_tool_outcome(event.result, error=event.error, content_blocks=event.content_blocks)
        if outcome != "ok":
            return True
        text = event.result if isinstance(event.result, str) else str(event.result or "")
        return len(text.strip()) < self.min_content_chars

    async def on_after_tool(self, event: ToolResultEvent):
        if self._is_unhelpful(event):
            self._streak += 1
            if self._streak >= self.k:
                self._pending_nudge = True
                self._streak = 0  # fires at most once per streak
        else:
            self._streak = 0
        yield event

    async def on_before_model(self, event: BeforeModelEvent):
        if not self._pending_nudge:
            yield event
            return
        self._pending_nudge = False
        line = _NUDGE_TEMPLATE.format(count=self.k)

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
