# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
from __future__ import annotations

import dataclasses

from ...core.events import (
    BeforeModelEvent,
    Message,
    StepEndEvent,
    StepStartEvent,
    TaskEndEvent,
    TaskStartEvent,
)
from ...core.processor import MultiHookProcessor

#: Stable marker prefixing the injected nudge — distinct from RunLoop's own
#: unmarked "[COST WARNING: ...]" line (runloop.py ~523-540) so the two never
#: read as the same signal to the model or to a log grep.
CHECKPOINT_MARKER = "[soft-budget-checkpoint]"

_NUDGE_TEMPLATE = (
    "[soft-budget-checkpoint] Checkpoint reached — {dims} of budget used "
    "({pct:.0%} of at least one dimension, threshold {ratio:.0%}). This is a soft "
    "checkpoint, not the hard cutoff: stop opening new lines of investigation and "
    "commit to your current best-guess FINAL ANSWER now. If evidence is incomplete, "
    "say so explicitly in the answer rather than continuing to explore toward the "
    "hard budget limit."
)


class SoftBudgetCheckpointProcessor(MultiHookProcessor):
    """Nudge a best-guess answer at a soft checkpoint, before the hard cutoff (W4·C1 stabilizer #3).

    Evidence (docs/ghx-overnight-0823-research.md, W4·C1): 5-10 fixable tasks
    fail budget_exceeded with 83-100% of budget already spent and no answer
    committed; the mechanism revives M25's C-R2-02 (a budget-checkpoint
    commit that showed real value before being killed by an unrelated
    triage-gate bug — the doc notes that gate is fixed upstream in T1.1).

    Differentiation from RunLoop's own 70% cost-only warning
    (``runloop.py`` ~523-540)
        That warning: cost-only, fixed 70% threshold, fires via
        ``state.add_raw_message`` directly (not a processor), unmarked text
        starting ``"[COST WARNING: ..."``. This processor: covers
        steps/tokens/cost (whichever budgets the task actually sets — not
        cost alone), a configurable ratio (default 0.75, intentionally later
        than 70% so the two don't fire back-to-back on the same run), a
        distinct marker (:data:`CHECKPOINT_MARKER`) and a more directive
        message ("commit ... now" vs "start wrapping up"). The two are
        independent and may both fire in the same run — that is acceptable
        (two differently-worded nudges, not a duplicate).

    Budgets read
        ``task.max_steps`` (always set, default 50), ``task.token_budget``
        and ``task.max_cost_usd`` (``None`` = that dimension is not tracked
        and is skipped). Captured once per task at ``on_step_start`` — the
        run loop's own budget source (same seam :class:`StepCountdownProcessor`
        uses for ``max_steps``).

    Cumulative usage read
        Steps: ``event.step_id`` (every event carries it) is exact and
        real-time. Cost: ``BeforeModelEvent.cumulative_cost_usd`` is exact and
        real-time (same field :class:`CostGuardProcessor` reads). Tokens: no
        event at ``before_model`` carries a running token total, so it is
        cached from the most recent ``StepEndEvent.cumulative_tokens`` — up to
        one step stale, acceptable for a soft, one-shot checkpoint.

    Enforcement (M13 lesson: nudge, never hard-stop)
        Fires at most ONCE per run, the first time any tracked dimension's
        ratio crosses ``ratio``. Injected via ``on_before_model`` using the
        same edit-last-user-or-append-once seam as
        :class:`StepCountdownProcessor`.

    Args:
        ratio: Fraction of budget that triggers the checkpoint (default 0.75).
    """

    _singleton_group = "soft_budget_checkpoint"
    _order = 15  # CostGuard (10) extension — right after it, before loop_detection (20)

    def __init__(self, ratio: float = 0.75):
        self.ratio = ratio

        self._max_steps: "int | None" = None
        self._token_budget: "int | None" = None
        self._max_cost_usd: "float | None" = None
        self._cumulative_tokens: int = 0
        self._fired: bool = False
        self._current_run_id: str = ""

    # ------------------------------------------------------------------
    # Per-task reset
    # ------------------------------------------------------------------

    def _reset(self) -> None:
        self._max_steps = None
        self._token_budget = None
        self._max_cost_usd = None
        self._cumulative_tokens = 0
        self._fired = False

    async def on_task_start(self, event: TaskStartEvent):
        self._reset()
        self._current_run_id = event.run_id
        yield event

    async def on_step_start(self, event: StepStartEvent):
        if event.run_id != self._current_run_id:
            self._reset()
            self._current_run_id = event.run_id
        task = getattr(event, "task", None)
        if task is not None:
            self._max_steps = getattr(task, "max_steps", None) or self._max_steps
            self._token_budget = getattr(task, "token_budget", None) or self._token_budget
            self._max_cost_usd = getattr(task, "max_cost_usd", None) or self._max_cost_usd
        yield event

    async def on_step_end(self, event: StepEndEvent):
        self._cumulative_tokens = event.cumulative_tokens
        yield event

    # ------------------------------------------------------------------
    # Checkpoint check + injection
    # ------------------------------------------------------------------

    def _triggered_dims(self, event: BeforeModelEvent) -> dict:
        """{dim: (used, budget, pct)} for every configured dimension whose
        ratio has crossed ``self.ratio``."""
        dims: dict = {}
        if isinstance(self._max_steps, int) and self._max_steps > 0:
            used = event.step_id + 1
            pct = used / self._max_steps
            if pct >= self.ratio:
                dims["steps"] = (used, self._max_steps, pct)
        if isinstance(self._token_budget, int) and self._token_budget > 0:
            pct = self._cumulative_tokens / self._token_budget
            if pct >= self.ratio:
                dims["tokens"] = (self._cumulative_tokens, self._token_budget, pct)
        if isinstance(self._max_cost_usd, (int, float)) and self._max_cost_usd > 0:
            pct = event.cumulative_cost_usd / self._max_cost_usd
            if pct >= self.ratio:
                dims["cost"] = (event.cumulative_cost_usd, self._max_cost_usd, pct)
        return dims

    async def on_before_model(self, event: BeforeModelEvent):
        if self._fired:
            yield event
            return

        triggered = self._triggered_dims(event)
        if not triggered:
            yield event
            return

        self._fired = True  # at most once per run
        max_pct = max(pct for _, _, pct in triggered.values())
        dims_desc = "; ".join(
            f"{dim} {used}/{budget}" for dim, (used, budget, _pct) in sorted(triggered.items())
        )
        line = _NUDGE_TEMPLATE.format(dims=dims_desc, pct=max_pct, ratio=self.ratio)

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
