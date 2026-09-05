# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Find a τ² task's unfolded graph U.

GAIA hands the evidence plane a ``task_id -> (session_id, run_id)`` map captured
at the rollout call site, because its pilot knows both.  τ² does not: the harness
runs *inside* tau2's simulation, and the run id is minted per task by the agent
adapter where the pilot cannot see it.  What the adapter can do — and now does —
is name the session after the task (``{round}-{task_id}``), which makes the run
id unnecessary: the session directory holds exactly that task's U.

So this resolver is a directory lookup, not a map lookup.  It returns ``None``
(unavailable) rather than an empty graph whenever the session or its U is
missing, the same contract :func:`~harnessx.ghx.evidence_files.core_layout_resolver`
keeps — an absent U must never read as "the task ran nothing".
"""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from ..graph.unfold import load_unfolded, session_unfolded_files

_LOG = logging.getLogger(__name__)

#: Characters Windows refuses in a path component, plus the glob metacharacters
#: ``[`` and ``]`` — a slug is looked up by pattern as well as by path, and a
#: bracketed name reads as a character class and matches nothing.  Every telecom
#: task id trips both sets (``[service_issue]break_apn|lock_sim[PERSONA:Easy]``)
#: and they run to 215 characters; retail and airline ids are bare integers.
_ILLEGAL = re.compile(r'[<>:"/\\|?*\[\]\x00-\x1f]')
#: Truncation point when an id must be rewritten.
_MAX_SLUG = 48
#: Pass-through bound.  Wider than ``_MAX_SLUG`` on purpose, and it has to be:
#: a slug this function produced is ``_MAX_SLUG`` + ``-`` + 10 hex = 59, and
#: re-slugging one would hash it a second time.  Everything downstream depends
#: on ``task_slug`` being idempotent — the adapter names a session from τ²'s
#: real id while the pilot's records carry the slug, and the two must land on
#: the same directory.
_MAX_NAME = 64


def task_slug(task_id) -> str:
    """A path component that identifies this task, on any filesystem.

    An id that is already safe and short is returned unchanged, so retail and
    airline sessions keep the names earlier runs wrote and stay resolvable.
    Anything else is sanitised, truncated, and given a hash of the *full* id —
    truncation alone would collide, since telecom ids share long prefixes.
    """
    tid = str(task_id)
    safe = _ILLEGAL.sub("_", tid).strip(". ")
    if safe == tid and len(safe) <= _MAX_NAME:
        return safe
    digest = hashlib.sha1(tid.encode("utf-8")).hexdigest()[:10]
    head = safe[:_MAX_SLUG].rstrip(". _")
    return f"{head}-{digest}" if head else digest


def session_name(prefix: str, task_id) -> str:
    """The session directory a τ² task writes to (mirrors the agent adapter)."""
    return f"{prefix}-{task_slug(task_id)}"


def tau2_u_path(sessions_dir, prefix: str, task_id) -> Path | None:
    """Path to this task's U file, or ``None`` when it was not recorded.

    A session holds one U per run id.  Under accumulation there is exactly one;
    if a bed ever wrote several, the newest wins — an older sibling would be a
    superseded slice of the same conversation.
    """
    session = Path(sessions_dir) / session_name(prefix, task_id)
    if not session.is_dir():
        return None
    files = session_unfolded_files(session)
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def tau2_layout_resolver(sessions_dir, prefix: str):
    """``task_id -> UnfoldedGraph | None`` for one round's sessions directory."""

    def resolve(task_id):
        path = tau2_u_path(sessions_dir, prefix, task_id)
        if path is None:
            return None
        try:
            return load_unfolded(path)
        except Exception:  # noqa: BLE001 — a corrupt U is unavailable, never empty
            _LOG.warning("tau2 layout: unreadable U at %s", path, exc_info=True)
            return None

    return resolve


__all__ = ["session_name", "tau2_layout_resolver", "tau2_u_path"]
