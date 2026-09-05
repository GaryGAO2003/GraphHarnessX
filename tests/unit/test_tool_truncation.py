# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The 50k cap on tool output, and the guard that once let 5 MB past it.

An Evolver ran a repo-wide grep. The result matched the guard's own source line in
``tools/base.py``, so the guard read "already truncated" and waved the whole 5 MB —
about 1.3M tokens — into the conversation. Compaction could not recover it:
``retention_window`` keeps recent messages intact, so a pass took the context from
2,776,876 tokens to 2,730,104. The next call exceeded the model's 512k window, the
400 is not retryable, and the Evolver and Critic both died with the round producing
nothing.
"""

from __future__ import annotations

from harnessx.tools.base import ToolResult, _truncate_result
from harnessx.tools.mcp import _MCP_TEXT_THRESHOLD


def _res(output: str) -> ToolResult:
    return ToolResult(output=output)


def test_small_output_is_untouched():
    out = "x" * (_MCP_TEXT_THRESHOLD - 1)
    assert _truncate_result(_res(out), "Bash").output == out


def test_oversized_output_is_capped_and_spilled():
    r = _truncate_result(_res("x" * (_MCP_TEXT_THRESHOLD * 3)), "Bash")
    assert len(r.output) < _MCP_TEXT_THRESHOLD * 2
    assert "[truncated" in r.output


def test_mentioning_the_marker_in_the_body_does_not_bypass_the_cap():
    """The bug: the guard scanned the whole string, so any output that merely
    mentions the marker skipped truncation. A grep over this repo matches it in
    tools/base.py, mcp.py and llm_judge.py."""
    body = "harnessx/tools/base.py:89:    if \"[truncated\" in output:\n"
    out = body + "y" * (_MCP_TEXT_THRESHOLD * 3)
    r = _truncate_result(_res(out), "Bash")
    assert len(r.output) < len(out), "oversized output mentioning the marker must still be capped"
    assert r.output.rstrip().endswith("]")


def test_an_already_truncated_output_is_not_truncated_again():
    """Why the guard exists: the notice sits past the threshold, so a second pass
    would cut it off and lose the pointer to the spilled file."""
    once = _truncate_result(_res("x" * (_MCP_TEXT_THRESHOLD * 3)), "Bash")
    twice = _truncate_result(once, "Bash")
    assert twice.output == once.output
