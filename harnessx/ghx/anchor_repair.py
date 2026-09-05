# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Anchor repair + IV-1b semantic spot-check (M24 · 批改 #6).

Two upgrades at the Stage-P validation seam
(``gates.structure.validate_digest_anchors``, resolved by ``run_stage_p`` at
call time):

* **Repair, not flag.** The digester abbreviates its own trajectory path with
  a literal ``...`` (``trajectories/..._r0.jsonl#step_19`` — ten flags per
  campaign). But every digest also carries intact full anchors (the Layer A
  table is prepended before validation runs), so the task id is recoverable
  from the SAME text — the ellipsis is reconstructed deterministically, the
  file is rewritten, and the vendored validator re-checks the repaired text.
  A wrong reconstruction simply stays degraded; nothing is force-passed.

* **IV-1b (advisory).** The vendored IV-1 proves the anchor's TARGET exists;
  it never checks the citation's ``snippet:`` quote actually appears in the
  trajectory. Frontier measurement (Onweller 2026, arXiv:2605.06635): pointer
  validity ~99-100% while content support runs 48-77%. IV-1b normalizes each
  quoted snippet and greps it against the task's trajectory text; misses are
  logged as warnings (advisory only — no digest is failed on it in v1).

Flag: ``HARNESSX_GHX_ANCHOR_REPAIR`` (call-time read, default off; covers
both behaviors).
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_ANCHOR_REPAIR"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_FULL_ANCHOR_RE = re.compile(r"trajectories/([0-9a-f]{8}-[0-9a-f-]{27,})_r(\d+)\.jsonl")
# the digester abbreviates either `{tid}` (leaving `..._r0.jsonl`) or `{tid}_`
# (leaving `...r0.jsonl`) — both suffix shapes must be consumed, else the
# reconstruction glues (`{tid}_r0.jsonlr1.jsonl`, seen live in M25_30x3 R2)
_ELLIPSIS_RE = re.compile(r"trajectories/\.\.\.(?:_?r(\d+))?(?:\.jsonl)?")
_SNIPPET_RE = re.compile(r'snippet:\s*"([^"\n]{10,200})')
_SQUISH_RE = re.compile(r"[^a-z0-9]+")


def anchor_repair_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def repair_digest_text(text: str) -> "tuple[str, int]":
    """Reconstruct ``trajectories/..._rK.jsonl`` ellipses from the digest's own
    intact anchors. Returns (repaired_text, replacements). Zero replacements
    when no ellipsis exists or the task id is not unambiguously recoverable."""
    tids = {m.group(1) for m in _FULL_ANCHOR_RE.finditer(text)}
    if len(tids) != 1:
        return text, 0
    tid = next(iter(tids))
    n = 0

    def _sub(m: "re.Match[str]") -> str:
        nonlocal n
        n += 1
        rollout = m.group(1) or "0"
        return f"trajectories/{tid}_r{rollout}.jsonl"

    return _ELLIPSIS_RE.sub(_sub, text), n


def _squish(s: str) -> str:
    return _SQUISH_RE.sub("", s.lower())


def snippet_misses(text: str, digest_root: Path) -> "tuple[int, int]":
    """IV-1b: (misses, total) — quoted snippets not found in the task's own
    trajectory text after normalization (dodges JSON escaping/whitespace)."""
    tids = {m.group(1) for m in _FULL_ANCHOR_RE.finditer(text)}
    if len(tids) != 1:
        return 0, 0
    tid = next(iter(tids))
    traj_files = sorted(Path(digest_root).glob(f"trajectories/{tid}_r*.jsonl"))
    if not traj_files:
        return 0, 0
    haystack = _squish(
        "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in traj_files)
    )
    total = misses = 0
    for m in _SNIPPET_RE.finditer(text):
        needle = _squish(m.group(1))[:80]
        if len(needle) < 10:
            continue
        total += 1
        if needle not in haystack:
            misses += 1
    return misses, total


_ORIGINAL_VALIDATE = None


def validate_digest_anchors_with_repair(digest_md: str, digest_root: Path):
    """Drop-in for ``validate_digest_anchors``: repair → persist → re-validate →
    advisory IV-1b. Degrades to the vendored validator on any wiring failure."""
    _vendored = _ORIGINAL_VALIDATE
    if _vendored is None:
        from harnessx.aegis.gates.structure import validate_digest_anchors as _vendored
    if not anchor_repair_enabled():
        return _vendored(digest_md, digest_root)
    try:
        repaired, n = repair_digest_text(digest_md)
        if n:
            tids = {m.group(1) for m in _FULL_ANCHOR_RE.finditer(repaired)}
            tid = next(iter(tids))
            dest = Path(digest_root) / "digests" / f"{tid}.md"
            if dest.exists():
                dest.write_text(repaired, encoding="utf-8")
                _LOG.info("anchor repair: %s — %d ellipsis anchor(s) reconstructed", dest.name, n)
        misses, total = snippet_misses(repaired, Path(digest_root))
        if misses:
            _LOG.warning(
                "IV-1b: %d/%d cited snippet(s) not found in the task's trajectory "
                "(pointer-valid but content-unsupported — advisory)",
                misses, total,
            )
        return _vendored(repaired, digest_root)
    except Exception as exc:  # noqa: BLE001 — never trade validation for the upgrade
        _LOG.warning("anchor repair failed (vendored validation): %s", exc)
        return _vendored(digest_md, digest_root)


@contextlib.contextmanager
def install_anchor_repair():
    """Patch ``gates.structure.validate_digest_anchors`` for one round (the
    Stage-P call site imports it from the module at call time)."""
    global _ORIGINAL_VALIDATE
    import harnessx.aegis.gates.structure as _gs

    original = _gs.validate_digest_anchors
    _ORIGINAL_VALIDATE = original
    _gs.validate_digest_anchors = validate_digest_anchors_with_repair
    try:
        yield
    finally:
        _gs.validate_digest_anchors = original
        _ORIGINAL_VALIDATE = None
