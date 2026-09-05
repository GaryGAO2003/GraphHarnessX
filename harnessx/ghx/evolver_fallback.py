# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Evolver burnout fallback — revive from the rejected pool (M24 · fix #2).

A burned-out Evolver (exit=error or zero surviving candidates) costs a whole
ship window plus its own session spend and leaves the Critic uninvoked — L0's
R6 ($50, nothing), M24-30×5's R4 ($28, nothing).  The loop already keeps a
revival-shaped ledger (``data/rejected_candidates.jsonl`` carries a
``revived_as`` field by design); nothing ever wrote it.

This wrapper closes that: when Stage 2 returns no candidate paths, revive the
NEWEST rejected candidate whose source files still exist — copy its manifest
into this round's ``candidates/`` under a fresh id (``C-R{n}-9X``, digits only
so every ``C-R(\\d+)-\\d+`` parser downstream keeps working), copy its applied
dir (the config's ``file://`` asset references point at the ORIGINAL round's
files, which persist, so the copied config stays loadable), stamp the
manifest's ``candidate_id`` and a revival note, and hand the amended stage-2
result to the Critic — who judges it like any candidate; the five official
gates and both graph gates still stand between it and a ship.

Zero LLM.  Honesty ladder: no rejected pool / no revivable source files /
any copy failure → the original empty stage-2 result, byte-identical to
today's burnout no_op.

Seam: the orchestrator binds ``run_stage_2`` at module top-level, so the
installer patches ``harnessx.aegis.orchestrator.run_stage_2`` for the round
and restores it in ``finally`` — the same discipline as every other overlay.

Flag: ``HARNESSX_GHX_EVOLVER_FALLBACK`` (call-time read, default off).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_EVOLVER_FALLBACK"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_CID_RE = re.compile(r"^C-R\d+-\d+$")
_CID_LINE_RE = re.compile(r"^candidate_id:\s*(\S+)\s*$", re.M)


def evolver_fallback_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def _rejected_pool(run_root: Path) -> list:
    """Rejected candidates, newest first, deduped by id (an id can be rejected
    in several rounds; the newest rejection carries the freshest assets)."""
    path = run_root / "data" / "rejected_candidates.jsonl"
    if not path.exists():
        return []
    rows: list = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("candidate_id"):
            rows.append(row)
    seen: set = set()
    out: list = []
    for row in sorted(rows, key=lambda r: int(r.get("round", -1)), reverse=True):
        cid = str(row["candidate_id"])
        if cid in seen:
            continue
        seen.add(cid)
        out.append(row)
    return out


def revive_candidate(run_root: Path, round_n: int, candidates_dir: Path) -> Path | None:
    """Copy the newest revivable rejected candidate into this round; return the
    new manifest path, or None when nothing in the pool is revivable."""
    run_root = Path(run_root)
    candidates_dir = Path(candidates_dir)
    applied_dir = candidates_dir.parent / "applied"
    for row in _rejected_pool(run_root):
        src_cid = str(row["candidate_id"])
        src_round = int(row.get("round", -1))
        if not _CID_RE.match(src_cid) or src_round < 0:
            continue
        src_manifest = run_root / f"R{src_round}" / "candidates" / f"{src_cid}.md"
        src_applied = run_root / f"R{src_round}" / "applied" / src_cid
        if not src_manifest.exists() or not (src_applied / "config.yaml").exists():
            continue
        new_cid = f"C-R{round_n}-91"
        for bump in range(91, 99):
            new_cid = f"C-R{round_n}-{bump}"
            if not (candidates_dir / f"{new_cid}.md").exists():
                break
        try:
            candidates_dir.mkdir(parents=True, exist_ok=True)
            dst_applied = applied_dir / new_cid
            if dst_applied.exists():
                shutil.rmtree(dst_applied)
            shutil.copytree(src_applied, dst_applied)
            text = src_manifest.read_text(encoding="utf-8", errors="replace")
            text, n_sub = _CID_LINE_RE.subn(f"candidate_id: {new_cid}", text, count=1)
            if n_sub == 0:
                continue  # manifest without a rewritable id — not revivable
            note = (
                f"\n\n## Revival note (evolver-burnout fallback)\n\n"
                f"Revived verbatim from `{src_cid}` (rejected R{src_round}) because "
                f"this round's Evolver produced zero candidates. Prior rejection "
                f"excerpt: {str(row.get('rejection_text_excerpt') or '')[:200]!r}. "
                f"Judge it fresh — the round context has changed.\n"
            )
            dst_manifest = candidates_dir / f"{new_cid}.md"
            dst_manifest.write_text(text + note, encoding="utf-8")
        except OSError as exc:
            _LOG.warning("evolver fallback: reviving %s failed (%s) — trying next", src_cid, exc)
            continue
        _LOG.info(
            "evolver fallback: revived %s (rejected R%d) as %s", src_cid, src_round, new_cid
        )
        return dst_manifest
    return None


async def run_stage_2_with_fallback(_original, **kwargs):
    """Delegate to the vendored Stage 2; on an empty candidate set, revive."""
    result = await _original(**kwargs)
    try:
        if result.get("candidate_paths"):
            return result
        if not evolver_fallback_enabled():
            return result
        candidates_dir = Path(kwargs["candidates_dir"])
        round_n = int(kwargs["round_n"])
        run_root = candidates_dir.parents[1]
        revived = revive_candidate(run_root, round_n, candidates_dir)
        if revived is None:
            return result
        amended = dict(result)
        amended["candidate_paths"] = [revived]
        amended["results"] = list(result.get("results") or []) + [
            (revived.stem, True, "revived from the rejected pool (evolver burnout fallback)")
        ]
        amended["ok_count"] = int(result.get("ok_count") or 0) + 1
        return amended
    except Exception as exc:  # noqa: BLE001 — fallback failure must never worsen a burnout
        _LOG.warning("evolver fallback failed (keeping burnout result): %s", exc)
        return result


@contextlib.contextmanager
def install_evolver_fallback():
    """Patch the orchestrator's top-level ``run_stage_2`` binding for one round."""
    import harnessx.aegis.orchestrator as _orch_mod

    original = _orch_mod.run_stage_2

    async def _wrapped(**kwargs):
        return await run_stage_2_with_fallback(original, **kwargs)

    _orch_mod.run_stage_2 = _wrapped
    try:
        yield
    finally:
        _orch_mod.run_stage_2 = original
