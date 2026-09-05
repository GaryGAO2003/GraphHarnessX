# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Single-shot digester — the pass@1 adaptation of Stage P (M24 · 批改 #1).

The vendored digester is an agentic session (Read/Bash/Grep over trajectory
files, 200-step budget) whose stated design case is pass@2 cross-rollout
analysis. Under pass@1 that capability is structurally idle while the loop
shape re-bills the file content every step: measured ×9 tokens for the same
digests, with 2× self-variance. The single-shot form — template + Layer A
facts + the COMPLETE trajectory inlined into one completion — was validated
five ways on 40 paired tasks (proxy metrics at the self-agreement ceiling;
×0.11 tokens reproduced across three runs; vendored IV-1 anchor validator
38-39/40 vs agentic 35/40; randomized blind judge 25-15 for single-shot;
vendored aggregate_digests byte-identical output).

Routing preserves the official form's design domain: k ≥ 2 rollouts or a
trajectory bundle over the char cap falls back to the vendored agentic
digester, as does any single-shot failure (exception or empty reply — a
digest must never be lost to the optimization).

Seam: patch ``preprocess._run_digester`` for the round (the stage resolves it
from module globals at call time). Flag: ``HARNESSX_GHX_SINGLESHOT_DIGESTER``
(call-time read, default off). Char cap: ``HARNESSX_GHX_SINGLESHOT_MAX_CHARS``
(default 240_000 ≈ 60K tokens, well inside the flash window).
"""

from __future__ import annotations

import contextlib
import logging
import os

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_SINGLESHOT_DIGESTER"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})
MAX_CHARS_ENV = "HARNESSX_GHX_SINGLESHOT_MAX_CHARS"
DEFAULT_MAX_CHARS = 240_000

SINGLE_SHOT_NOTE = """

---
## EXECUTION MODE OVERRIDE (single-shot)

You have NO tools in this session. The complete trajectory jsonl content is
provided in the user message below — it is the same content you would have
read with the Read tool. Do NOT attempt tool calls. Produce the digest
markdown (exactly what you would have written to the digest file, same
format, same frontmatter, same citation anchors like
`trajectories/<name>.jsonl#step_k`) directly as your reply, and nothing else.
"""


def singleshot_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def _max_chars() -> int:
    try:
        return int(os.environ.get(MAX_CHARS_ENV, "") or DEFAULT_MAX_CHARS)
    except ValueError:
        return DEFAULT_MAX_CHARS


_ORIGINAL_RUN = None


async def run_digester_singleshot(inputs, harness):
    """Single-completion digest with agentic fallback — drop-in for ``_run_digester``."""
    vendored = _ORIGINAL_RUN
    if vendored is None:
        from harnessx.aegis.stages.preprocess import _run_digester as vendored
    if not singleshot_enabled() or harness is None:
        return await vendored(inputs, harness)
    try:
        paths = list(inputs.trajectory_paths)
        if len(paths) != 1:
            _LOG.info(
                "singleshot digester: %s has %d rollouts — agentic fallback (design domain)",
                inputs.task_id, len(paths),
            )
            return await vendored(inputs, harness)
        texts = [p.read_text(encoding="utf-8") for p in paths]
        total = sum(len(t) for t in texts)
        if total > _max_chars():
            _LOG.info(
                "singleshot digester: %s trajectory %d chars > cap %d — agentic fallback",
                inputs.task_id, total, _max_chars(),
            )
            return await vendored(inputs, harness)

        from harnessx import BaseTask
        from harnessx.core.builder import HarnessBuilder
        from harnessx.processors.context.system_prompt import SystemPromptProcessor
        from harnessx.aegis._prompt import StaticSystemPromptBuilder, render_template
        from harnessx.aegis.agents.digester import _select_template
        from harnessx.tools.inmemory import InMemoryToolRegistry

        rendered = render_template(
            _select_template(inputs.pattern),
            task_id=inputs.task_id,
            digest_out_path=str(inputs.digest_out_path),
            trajectory_paths=[str(p) for p in paths],
            trajectory_refs=[f"trajectories/{p.name}" for p in paths],
            trace_facts_md=inputs.trace_facts_md or "",
        )
        parts = []
        for p, t in zip(paths, texts):
            parts.append(f"=== FILE trajectories/{p.name} (complete content) ===")
            parts.append(t)
        user_msg = (
            "Below is the complete trajectory content for this task. "
            "Reply with the digest markdown only.\n\n" + "\n".join(parts)
        )
        cfg = (
            HarnessBuilder()
            .slot(tool_registry=InMemoryToolRegistry())
            .add(SystemPromptProcessor(StaticSystemPromptBuilder(text=rendered + SINGLE_SHOT_NOTE)))
            .build()
        )
        single = harness.model_config.agentic(cfg)
        result = await single.run(BaseTask(description=user_msg, max_steps=3, max_cost_usd=10.0))
        text = (result.final_output or "").strip()
        if not text:
            _LOG.warning(
                "singleshot digester: %s returned empty — agentic fallback", inputs.task_id
            )
            return await vendored(inputs, harness)
        inputs.digest_out_path.parent.mkdir(parents=True, exist_ok=True)
        inputs.digest_out_path.write_text(text + "\n", encoding="utf-8")
        return result
    except Exception as exc:  # noqa: BLE001 — a digest must never be lost to the optimization
        _LOG.warning(
            "singleshot digester failed for %s (%s) — agentic fallback",
            getattr(inputs, "task_id", "?"), exc,
        )
        return await vendored(inputs, harness)


@contextlib.contextmanager
def install_singleshot_digester():
    """Patch ``preprocess._run_digester`` for one round."""
    global _ORIGINAL_RUN
    import harnessx.aegis.stages.preprocess as _pre

    original = _pre._run_digester
    _ORIGINAL_RUN = original
    _pre._run_digester = run_digester_singleshot
    try:
        yield
    finally:
        _pre._run_digester = original
        _ORIGINAL_RUN = None
