# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The GHX ladder: which env flags each ``--ghx-level`` turns on.

Extracted from the GAIA launcher when the tau2 arm needed the same ladder.  The
levels describe the graph runtime, not a bed, so both launchers read this one
table and a level means the same thing wherever it is quoted.
"""
from __future__ import annotations

import os


_UNFOLD = "HARNESSX_GHX_UNFOLD"
_IDENTITY = "HARNESSX_GHX_IDENTITY"
_EVIDENCE = "HARNESSX_GHX_AEGIS_EVIDENCE"
_GATE = "HARNESSX_GHX_GRAPH_GATE"
_PROPOSALS = "HARNESSX_GHX_GRAPH_PROPOSALS"  # matches harnessx.ghx.graph_proposals.FLAG
_GUIDANCE = "HARNESSX_GHX_GUIDANCE"  # matches harnessx.ghx.guidance.FLAG (M23, G1c)

#: The M24/M25 seams that proved themselves and joined the profile. STRATEGY_POP is
#: deliberately absent — the strategy tag's self-agreement measured 0/6 and the table
#: had no consumer; frozen, not deleted (the flag still works if exported by hand).
_PROVEN_SEAMS: tuple[str, ...] = (
    "HARNESSX_GHX_LAYER_A",
    "HARNESSX_GHX_REGRESSION_TRIAGE",
    "HARNESSX_GHX_POPULATION",
    "HARNESSX_GHX_GATE_SCOPE",
    "HARNESSX_GHX_GATE_REPLAY",
    "HARNESSX_GHX_EVOLVER_FALLBACK",
    "HARNESSX_GHX_ATTRIBUTION",
    "HARNESSX_GHX_SINGLESHOT_DIGESTER",
    "HARNESSX_GHX_CHEATSHEET",
    "HARNESSX_GHX_ANCHOR_REPAIR",
)

LEVEL_FLAGS: dict[int, tuple[str, ...]] = {
    0: (),
    1: (_UNFOLD, _IDENTITY),
    2: (_UNFOLD, _IDENTITY, _EVIDENCE, _GUIDANCE),
    3: (_UNFOLD, _IDENTITY, _EVIDENCE, _GUIDANCE),
    4: (_UNFOLD, _IDENTITY, _EVIDENCE, _GUIDANCE, _GATE),
    5: (_UNFOLD, _IDENTITY, _EVIDENCE, _GUIDANCE, _GATE, _PROPOSALS),
    # 6 = the campaign profile: level 5 plus every proven M24/M25 seam, as ONE
    # switch. M25 was launched by exporting eleven env vars beside --ghx-level 5;
    # a profile is how a 17-flag surface stays operable — and how two arms of a
    # campaign can be byte-certain they ran the same set.
    6: (_UNFOLD, _IDENTITY, _EVIDENCE, _GUIDANCE, _GATE, _PROPOSALS, *_PROVEN_SEAMS),
}
MAX_LEVEL = max(LEVEL_FLAGS)


def apply_level_flags(level: int, environ: dict | None = None) -> tuple[str, ...]:
    """Set the level's flags in ``environ`` (default ``os.environ``) via ``setdefault``.

    ``setdefault`` is the whole precedence contract: a flag the user exported already
    (to any value, including ``"0"``) is left untouched, so an explicit environment
    variable always beats the level.  Returns the level's flag tuple for logging/tests.
    """
    if level not in LEVEL_FLAGS:
        raise ValueError(f"unknown ghx level {level!r}; expected 0..{MAX_LEVEL}")
    env = os.environ if environ is None else environ
    flags = LEVEL_FLAGS[level]
    for flag in flags:
        env.setdefault(flag, "1")
    return flags


__all__ = ["LEVEL_FLAGS", "MAX_LEVEL", "apply_level_flags"]
