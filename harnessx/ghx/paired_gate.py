# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Paired-read evidence at the gate (M27 T1.3).

The rollback gate has one reading today: the raw total-score delta
(``run_meta_aegis.py``'s ``delta_rate``/``delta_count``), a design ``paired_read.py``
already showed is the wrong instrument — at n≈100 the single-draw band is wide
enough to swallow the plausible effect, while the *paired* question (did the
tasks THIS SHIP predicted actually move) is answerable at n as small as the
predicted set itself.

This module adds a second, ship-scoped paired reading: the ship's own declared
``predicted_impact`` task set (``tasks_will_unlock``/``tasks_will_stabilize``/
``tasks_will_pass`` — the same union ``orchestrator._extract_predicted_tasks``
computes, read back from the ``ship_outcomes.json`` rows the orchestrator
already writes rather than re-parsing candidate manifests) paired between the
previous validated round and this one, via ``paired_read.pair_arms``.

It is wired in **read/report-only** — no veto power. The rollback decision
still hangs on the raw rule (optionally softened by ``regression_triage`` under
T1.1); this module only writes a third, independent reading (round dir
evidence file + audit entry) alongside it, so the decision log shows all three
at once: raw delta, triage verdict, paired read.

Flag: ``HARNESSX_GHX_PAIRED_GATE`` (call-time read, default off).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .paired_read import PairedResult, arm_from_task_history, pair_arms, render

FLAG = "HARNESSX_GHX_PAIRED_GATE"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})


def paired_gate_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def predicted_tasks_for_round(run_dir, round_n: int, *, ship_ids: "set[str] | None" = None) -> list[str]:
    """Union of ``predicted_tasks`` from every ``ship_outcomes.json`` row tagged
    ``round_n`` (optionally narrowed to ``ship_ids``), first-seen order preserved.

    Returns ``[]`` on any missing/malformed ledger — never guessed, exactly the
    ``paired_read`` discipline of "absent is not a claim".
    """
    path = Path(run_dir) / "data" / "ship_outcomes.json"
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(rows, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or int(row.get("round", -1)) != round_n:
            continue
        if ship_ids is not None and row.get("ship_id") not in ship_ids:
            continue
        for t in row.get("predicted_tasks") or []:
            s = str(t)
            if s and s not in seen:
                seen.add(s)
                out.append(s)
    return out


def compute_predicted_task_paired_read(
    run_dir,
    *,
    round_idx: int,
    pre_ship_round: int,
    predicted_tasks: list[str],
) -> PairedResult | None:
    """Pair the ship's own predicted task set between ``pre_ship_round`` (the
    previous validated round) and ``round_idx`` (this round). ``None`` when
    there is nothing predicted to pair — a ship with an empty predicted set
    has nothing this reading can say."""
    if not predicted_tasks:
        return None
    keys = set(predicted_tasks)
    prev_arm = {k: v for k, v in arm_from_task_history(run_dir, round_n=pre_ship_round).items() if k in keys}
    curr_arm = {k: v for k, v in arm_from_task_history(run_dir, round_n=round_idx).items() if k in keys}
    return pair_arms(prev_arm, curr_arm)


def write_paired_gate_evidence(
    run_dir,
    round_idx: int,
    result: PairedResult,
    *,
    name_a: str = "pre-ship",
    name_b: str = "post-ship",
) -> Path:
    """Write the markdown + JSON evidence files into ``R{round_idx}/graph_evidence/``."""
    out_dir = Path(run_dir) / f"R{round_idx}" / "graph_evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "paired_gate.md"
    md_path.write_text(render(result, name_a, name_b), encoding="utf-8")
    json_path = out_dir / "paired_gate.json"
    json_path.write_text(
        json.dumps(
            {
                "round": round_idx,
                "both_pass": result.both_pass,
                "both_fail": result.both_fail,
                "fixed": result.fixed,
                "broken": result.broken,
                "missing": result.missing,
                "n_paired": result.n_paired,
                "discordant": result.discordant,
                "net": result.net,
                "p_value": result.p_value,
                "verdict": result.verdict(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return md_path


def append_paired_gate_audit(run_dir, round_idx: int, result: PairedResult) -> None:
    """Append a report-only ``paired_gate`` event to ``audit.jsonl``.

    Written the same way ``run_meta_aegis.py``'s ``_append_rollback_audit`` does
    (a raw JSONL line, not the vendored ``AuditLog``/``AuditEvent`` machinery,
    whose ``kind`` enum is fixed and vendored) — never fatal, same discipline as
    every other audit sibling on this path.
    """
    audit_path = Path(run_dir) / "audit.jsonl"
    entry = {
        "round": round_idx,
        "stage": "R",
        "kind": "paired_gate",
        "payload": {
            "n_paired": result.n_paired,
            "fixed": result.fixed,
            "broken": result.broken,
            "missing": result.missing,
            "net": result.net,
            "p_value": result.p_value,
            "verdict": result.verdict(),
        },
        "evidence_refs": [],
        "ts": time.time(),
    }
    try:
        with audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # evidence write must never break the round


__all__ = [
    "FLAG",
    "paired_gate_enabled",
    "predicted_tasks_for_round",
    "compute_predicted_task_paired_read",
    "write_paired_gate_evidence",
    "append_paired_gate_audit",
]
