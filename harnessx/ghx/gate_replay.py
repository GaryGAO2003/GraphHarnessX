# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Gate-B prerequisite — a REAL replay U for the sixth gate (M24 · gates batch).

The sixth gate (:mod:`harnessx.ghx.graph_gate`) has been honestly inert since
birth: the official Stage-4 replay boots candidate configs against a synthetic
task, so no candidate's new mechanism could ever fire in it, and the launcher's
resolver returned ``None`` by design — 6/6 evaluations ``checked=False`` across
M23.  This module is the "future module" that docstring promised: run ONE real
GAIA task under the candidate's applied config with U recording on, and hand
that U back per candidate (~$0.4, ~1–2 min inside the evolve stage).

Division of labour (layering: ``harnessx`` never imports ``recipe``):

* here — everything generic: replay-task selection, the per-round binding, the
  sync→async bridge (the gate's resolver contract is synchronous; the replay
  coroutine runs on a fresh event loop in a worker thread), and the honesty
  ladder (any failure → ``None`` → the gate's pass-through path, never a new
  rejection);
* the launcher — the injected ``runner`` coroutine that actually builds the
  harness from the applied config and runs the task (it owns args/model/tasks).

Replay-task selection is the gate's, not the candidate's: the candidate's
predicted task with the LONGEST consecutive fail streak (most informative —
a hard-fail flipping in replay is gold-grade evidence; a swinger flipping is
noise, which is why the gate reads ``fired``, not ``flip``, for those).

Flag: ``HARNESSX_GHX_GATE_REPLAY`` (call-time read, default off — off keeps
today's inert-resolver behaviour byte-for-byte).
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_GATE_REPLAY"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_CID_ROUND_RE = re.compile(r"^C-R(\d+)-\d+")


def gate_replay_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def _fail_streaks(run_root: Path) -> dict:
    """task_id → consecutive-fail streak ending at that task's latest round."""
    per_task: dict = {}
    path = run_root / "data" / "task_history.jsonl"
    if not path.exists():
        return {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        tid = str(row.get("task_id") or "")
        if not tid:
            continue
        flags = row.get("passed_flags")
        if not isinstance(flags, list) or not flags:
            flags = [bool(row.get("passed", False))]
        per_task.setdefault(tid, {})[int(row.get("round", 0))] = any(flags)
    out: dict = {}
    for tid, by_round in per_task.items():
        streak = 0
        r = max(by_round)
        while r in by_round and not by_round[r]:
            streak += 1
            r -= 1
        out[tid] = streak
    return out


def pick_replay_task(predicted: list, run_root: Path) -> str | None:
    """The gate's choice: longest fail streak wins; ties break lexicographically
    (deterministic).  Tasks with no history sort as streak 0 — still eligible,
    a prediction is a prediction."""
    preds = [str(p) for p in (predicted or []) if p]
    if not preds:
        return None
    streaks = _fail_streaks(run_root)
    return sorted(preds, key=lambda t: (-streaks.get(t, 0), t))[0]


def _predicted_from_manifest(fm: dict | None) -> list:
    """Every task the candidate claims a positive effect on.

    The machine manifest's predicted_impact keys are MODEL-IMPROVISED per run
    — three spellings observed in three smokes (tasks_will_unlock,
    tasks_will_stabilize, tasks_will_pass) — so enumeration loses by
    construction.  Collect every list-valued ``tasks_*`` key under
    predicted_impact EXCEPT ``tasks_at_risk`` (a harm prediction, not a
    target), plus the legacy top-level ``predicted_tasks``.  Deduped in
    order; unlock-style keys naturally sort first via the caller's
    fail-streak ordering."""
    if not isinstance(fm, dict):
        return []
    out: list = []
    pi = fm.get("predicted_impact")
    if isinstance(pi, dict):
        for key in sorted(pi):
            if not str(key).startswith("tasks_") or str(key) == "tasks_at_risk":
                continue
            val = pi.get(key)
            if isinstance(val, list):
                out.extend(str(t) for t in val)
    if isinstance(fm.get("predicted_tasks"), list):
        out.extend(str(t) for t in fm["predicted_tasks"])
    seen: set = set()
    return [t for t in out if not (t in seen or seen.add(t))]


def run_coro_bounded(coro_factory, *, timeout_s: float, name: str = "ghx-bridge"):
    """Run an async callable on a fresh event loop in a DAEMON thread; bounded.

    The sync→async bridge every replay-shaped caller needs (gate replay,
    counterfactual).  Two bounds and one exit guarantee:

    * inner ``asyncio.wait_for`` cancels the coroutine so the worker loop
      tears down and the thread ends on its own;
    * the outer join is a belt for a coroutine that ignores cancellation;
    * the thread is a DAEMON — ThreadPoolExecutor's non-daemon workers are
      joined at interpreter exit, so one truly-wedged replay used to keep the
      finished process alive until someone killed it by hand (M24 30×5).

    Returns ``(ok, value)``: ``(True, result)`` on success, ``(False, exc|None)``
    on timeout/crash — the caller owns the honesty ladder.
    """
    import asyncio
    import threading

    box: dict = {}

    def _worker() -> None:
        try:
            async def _bounded():
                return await asyncio.wait_for(coro_factory(), timeout=timeout_s)

            box["value"] = asyncio.run(_bounded())
            box["ok"] = True
        except BaseException as exc:  # noqa: BLE001 — carried to the caller
            box["ok"] = False
            box["value"] = exc

    t = threading.Thread(target=_worker, name=name, daemon=True)
    t.start()
    t.join(timeout=timeout_s + 60.0)
    if t.is_alive():
        return False, TimeoutError(f"{name}: worker still running after {timeout_s + 60.0:.0f}s")
    return bool(box.get("ok")), box.get("value")


class GateReplayResolver:
    """Callable matching the sixth gate's resolver contract: ``cid → U path | None``.

    ``runner`` is the launcher-injected coroutine function
    ``async runner(config_path: str, task_id: str, session_id: str) -> str | None``
    returning the recorded U's file path.  ``bind_round(run_dir, round_n)`` is
    called by the round wrapper before each round's overlays dispatch; a call
    before any bind, with the flag off, for an unparseable cid, a missing
    manifest/config, an empty prediction set, or a crashing runner all resolve
    to ``None`` — the gate then records WHY it could not check and passes the
    candidate through, exactly today's behaviour.
    """

    def __init__(self, runner, *, timeout_s: float = 600.0):
        self._runner = runner
        self._timeout_s = timeout_s
        self._run_dir: Path | None = None
        self._round_n: int | None = None

    def bind_round(self, run_dir, round_n: int) -> None:
        self._run_dir = Path(run_dir)
        self._round_n = int(round_n)

    def __call__(self, cid: str):
        if not gate_replay_enabled():
            return None
        if self._run_dir is None:
            return None
        m = _CID_ROUND_RE.match(str(cid) or "")
        round_n = int(m.group(1)) if m else self._round_n
        if round_n is None:
            return None

        manifest_path = self._run_dir / f"R{round_n}" / "candidates" / f"{cid}.md"
        config_path = self._run_dir / f"R{round_n}" / "applied" / cid / "config.yaml"
        if not manifest_path.exists() or not config_path.exists():
            return None
        try:
            from harnessx.aegis.agents.evolver import parse_candidate_manifest

            fm, _body = parse_candidate_manifest(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        task_id = pick_replay_task(_predicted_from_manifest(fm), self._run_dir)
        if not task_id:
            return None

        session_id = f"gatereplay/R{round_n}-{cid}"
        # Timeout discipline, learned the expensive way (30x5 R2 hung 2h+, then
        # a finished process that would not exit): run_coro_bounded's inner
        # wait_for cancels the replay so its loop tears down; the outer join is
        # a belt; and the worker is a DAEMON thread, so a truly-wedged replay
        # can never block the round OR the interpreter's exit.
        ok, value = run_coro_bounded(
            lambda: self._runner(str(config_path), task_id, session_id),
            timeout_s=self._timeout_s,
            name=f"gatereplay-{cid}",
        )
        if not ok:
            _LOG.warning("gate replay: %s on task %s failed (%s) — unavailable U", cid, task_id, value)
            return None
        u_path = value
        if not u_path:
            return None
        _LOG.info("gate replay: %s ran %s → U %s", cid, task_id, u_path)
        return u_path
