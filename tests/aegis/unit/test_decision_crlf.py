# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""P-26 — CRLF line endings murdered a legitimate ship decision.

M22_L2_ghx5 R3: the Critic wrote a complete, valid ship decision; the file
began with bytes ``2D 2D 2D 0D 0A`` (``---\\r\\n``) because the write tool
followed the model's Windows line endings that day. ``_FRONTMATTER_RE`` knows
only ``---\\n``, so parse_decision declared "No valid frontmatter found", the
journal recorded ``narrative="Critic failed"`` (blaming the innocent stage),
and the arm ran its third straight round on the base config while a $47.5
Evolver run and its accepted candidate went in the bin.

The fix normalizes line endings before matching. YAML semantics, the
frontmatter requirement, and every failure path stay byte-identical.
"""
from __future__ import annotations

import pytest

from harnessx.aegis.agents.critic import parse_decision

# The murdered decision, byte-faithful in shape: CRLF everywhere, including
# the delimiter lines that killed it.
_CRLF_DECISION = (
    "---\r\n"
    "round: 3\r\n"
    "decision_type: ship\r\n"
    "ship_ranking:\r\n"
    "  - candidate_id: C-R3-01\r\n"
    "---\r\n"
    "\r\n"
    "## Reasoning\r\n"
    "\r\n"
    "- **C-R3-01 accepted**: real, additive processor.\r\n"
)


def test_a_crlf_decision_parses_instead_of_voiding_the_round():
    decision, body = parse_decision(_CRLF_DECISION)
    assert decision["decision_type"] == "ship"
    assert decision["ship_ranking"][0]["candidate_id"] == "C-R3-01"
    assert "C-R3-01 accepted" in body


def test_lone_cr_is_tolerated_too():
    decision, _ = parse_decision(_CRLF_DECISION.replace("\r\n", "\r"))
    assert decision["decision_type"] == "ship"


def test_an_lf_decision_is_byte_identical_behavior():
    lf = _CRLF_DECISION.replace("\r\n", "\n")
    decision, body = parse_decision(lf)
    assert decision["round"] == 3
    # today's parser keeps the blank line after the closing delimiter — pin it
    assert body.startswith("\n## Reasoning")


def test_actually_missing_frontmatter_still_raises():
    """The tolerance is for line endings only — a decision without frontmatter
    is still refused with the same message."""
    with pytest.raises(ValueError, match="No valid frontmatter found"):
        parse_decision("just prose, no delimiters\r\n")
