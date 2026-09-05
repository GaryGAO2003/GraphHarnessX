# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""No-op ledger fix + gate-confirmed no_op (M27 T1.2).

W1·A1 measured the largest single funnel loss as the Critic's "no_op" verdict
(28.8% of 139 compose-surviving candidates, no mechanical gate ever run — the
Critic's ``ship_ranking`` comes back empty and Stage 4 has nothing to iterate
over) with two distinct problems inside it:

* **8 of those vanished with zero ledger record.** ``AegisOrchestrator.run_round``
  early-returns at the ``critic_failed`` branch (``decision.md`` missing or
  unparsable) *before* the rejected-candidates ledger write that normally runs
  after Stage 4 — the candidates Stage 2 produced are simply never written to
  ``rejected_candidates.jsonl``. This is pure bookkeeping (a ledger row that was
  previously skipped), not a behaviour change, so it is installed unconditionally
  — no flag of its own — via :func:`install_noop_ledger_fix`.
* **A legitimate no_op (Critic reached a decision, chose to ship nothing) never
  gets mechanically checked at all** — "not shipping" is as unverified as
  shipping used to be. :func:`install_noop_gatecheck` (flag
  ``HARNESSX_GHX_NOOP_GATECHECK``) runs a minimal, pure-function gate subset
  (structure + graph-existence — see module docstring below for what is
  deliberately excluded) against the top candidate whenever Stage 4 returns
  nothing shipped and the Critic's decision was ``no_op``, and records the
  result into ``audit.jsonl`` as a distinct, clearly-marked entry. The no_op
  still stands either way — this never ships a candidate on its own; it only
  makes "no_op" a gate-confirmed statement instead of an unverifiable one.

``harnessx/aegis/orchestrator.py`` is vendored (``tests/ghx/test_vendored_integrity.py``
hashes the whole ``harnessx/aegis/`` tree) — neither fix may edit it. Both install
as a call-time monkeypatch of the module-level ``run_stage_3``/``run_stage_4``
names the orchestrator resolves per round, restored in a ``finally``, exactly the
pattern ``graph_gate.py`` and ``regression_triage.py`` already use.
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import time
from pathlib import Path

_LOG = logging.getLogger("harnessx.ghx.noop_gatecheck")
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})
FLAG = "HARNESSX_GHX_NOOP_GATECHECK"

# The gates NOT run in eval-only mode, and why: novelty/canonicalize/counterfactual
# need the candidate's *applied* (composed) config, which does not exist for a
# candidate that never shipped; replay boots a real harness run (an LLM call this
# module must never make merely to confirm a "don't ship" verdict). structure and
# graph_existence are pure functions over the raw manifest (+ an optional replay U
# this eval-only path never has, so graph_existence honestly reads "unavailable,
# pass-through" here — see graph_gate.py's own honesty contract) — the "minimal
# viable subset" the spec calls for.
EXCLUDED_GATES: tuple[str, ...] = ("novelty", "canonicalize", "counterfactual", "replay")


def noop_gatecheck_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


# ── T1.2(a): rejected-candidates ledger, always on ──────────────────────────


def _candidate_manifests(candidates_dir: Path) -> dict[str, dict]:
    from harnessx.aegis.agents.evolver import parse_candidate_manifest

    out: dict[str, dict] = {}
    for path in sorted(Path(candidates_dir).glob("*.md")):
        try:
            fm, _body = parse_candidate_manifest(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 — one bad manifest must not sink the rest
            _LOG.warning("manifest read failed for %s (non-fatal): %s", path.name, exc)
            continue
        if isinstance(fm, dict):
            out[path.stem] = fm
    return out


def write_rejected_ledger_on_critic_failed(run_dir: Path, round_n: int, candidates_dir: Path) -> None:
    """Write ``rejected_candidates.jsonl`` rows for every candidate Stage 2 produced,
    for a round where the Critic never reached a decision.

    Every candidate under ``candidates_dir`` survived Stage 2 (propose) — Stage 2's
    own rejects never land a manifest file there — so all of them are the
    "compose-surviving candidates" the ledger fix is about. No-op when the
    directory is empty or unreadable.
    """
    from harnessx.aegis.data import ledger
    from harnessx.aegis.orchestrator import _extract_predicted_tasks

    manifests = _candidate_manifests(candidates_dir)
    if not manifests:
        return
    rows = [
        {
            "candidate_id": cid,
            "bucket": str(fm.get("bucket", "")),
            "predicted_tasks": _extract_predicted_tasks(fm),
            "rejection_text_excerpt": "critic_failed — no decision.md produced this round",
            "signature": "",
        }
        for cid, fm in manifests.items()
    ]
    try:
        ledger.append_rejected_candidates(run_dir, round_n, rows)
        ledger.backfill_rejected_revivals(run_dir)
    except Exception as exc:  # noqa: BLE001 — ledger write must never break a round
        _LOG.warning("rejected-candidate ledger write (critic_failed path) failed (non-fatal): %s", exc)


@contextlib.contextmanager
def install_noop_ledger_fix():
    """Patch ``run_stage_3`` (the name the orchestrator resolves) so a
    ``critic_failed`` round still ledgers its candidates. Always installed by the
    round router — pure bookkeeping, no flag of its own."""
    import harnessx.aegis.orchestrator as _orch_mod

    original = _orch_mod.run_stage_3

    async def _wrapped(**kwargs):
        result = await original(**kwargs)
        if result.get("critic_failed") or not result.get("decision"):
            candidates_dir = kwargs.get("candidates_dir")
            round_n = kwargs.get("round_n")
            if candidates_dir is not None and round_n is not None:
                try:
                    run_dir = Path(candidates_dir).parent.parent
                    write_rejected_ledger_on_critic_failed(run_dir, round_n, Path(candidates_dir))
                except Exception as exc:  # noqa: BLE001 — never break the round over this
                    _LOG.warning("noop ledger fix failed (non-fatal): %s", exc)
        return result

    _orch_mod.run_stage_3 = _wrapped
    try:
        yield
    finally:
        _orch_mod.run_stage_3 = original


# ── T1.2(b): gate-confirmed no_op ────────────────────────────────────────────


def pick_top_candidate(candidates_info: dict) -> "str | None":
    """A no_op decision's ``ship_ranking`` is empty by construction — there is no
    Critic-declared "top" candidate to defer to. Sorted-by-candidate-id first is a
    documented, reproducible stand-in, not a scoring claim."""
    if not candidates_info:
        return None
    return sorted(candidates_info)[0]


def run_minimal_gate_subset(cid: str, candidates_info: dict, *, current_round: "int | None" = None) -> dict:
    """Structure + graph-existence, both pure functions, against the raw manifest.
    See ``EXCLUDED_GATES`` for what this deliberately does not run and why."""
    from .attribution_graph import infer_signature
    from .graph_gate import check_graph_gate
    from ..aegis.agents.evolver import parse_candidate_manifest
    from ..aegis.gates.structure import validate_candidate_manifest

    info = candidates_info.get(cid)
    if not info:
        return {}
    manifest_path = info[0]
    try:
        manifest, body = parse_candidate_manifest(Path(manifest_path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — unreadable manifest is itself a structure failure
        return {"structure": {"ok": False, "reason": f"manifest unreadable: {exc!r}"}}
    if not isinstance(manifest, dict):
        manifest = {}
    slot_type = manifest.get("slot_type", "regular")
    sr = validate_candidate_manifest(manifest, body, slot_type=slot_type, current_round=current_round)
    signature = infer_signature(manifest.get("bucket"), manifest, manifest.get("attribution_signature"))
    # No replay U in eval-only mode (the candidate never composed/ran) — the gate's
    # own honesty contract reads this as "unavailable, pass-through", never a
    # fabricated pass.
    gr = check_graph_gate(signature, None)
    return {
        "structure": {"ok": sr.ok, "reason": sr.reason},
        "graph_existence": {"ok": gr.ok, "checked": gr.checked, "reason": gr.reason},
    }


def append_noop_gatecheck_audit(run_dir, round_n: "int | None", cid: str, gate_results: dict) -> None:
    """Raw JSONL append to ``audit.jsonl`` (bypasses the vendored ``AuditLog``'s
    fixed ``kind`` enum, same as ``run_meta_aegis.py``'s rollback-audit siblings) —
    ``kind="noop_gatecheck"`` keeps this readably distinct from a real Stage-4
    ``gate`` entry on a shipped candidate."""
    audit_path = Path(run_dir) / "audit.jsonl"
    entry = {
        "round": round_n,
        "stage": "4",
        "kind": "noop_gatecheck",
        "payload": {
            "cid": cid,
            "results": {k: v.get("ok") for k, v in gate_results.items()},
            "reasons": {k: v.get("reason") for k, v in gate_results.items() if v.get("reason")},
            "excluded_gates": list(EXCLUDED_GATES),
            "note": "evaluation-only — the no_op stands regardless; this does not ship",
        },
        "evidence_refs": [],
        "ts": time.time(),
    }
    try:
        with audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        _LOG.warning("noop_gatecheck audit append failed: %s", exc)


@contextlib.contextmanager
def install_noop_gatecheck():
    """Patch ``run_stage_4`` so a genuine no_op (Critic decided, chose to ship
    nothing) still runs the minimal gate subset against a candidate.

    Callers gate the install itself on :func:`noop_gatecheck_enabled` (the same
    convention ``regression_triage``/``population``/etc. use) — installing this
    unconditionally would still be safe (the wrapper only ever *adds* an audit
    entry, never changes ``shipped_cids``), but matching the convention keeps
    every GHX seam's on/off switch in the same place: the round router.
    """
    import harnessx.aegis.orchestrator as _orch_mod

    original = _orch_mod.run_stage_4

    async def _wrapped(**kwargs):
        stage_4 = await original(**kwargs)
        shipped = stage_4.get("shipped_cids") or ([stage_4["shipped_cid"]] if stage_4.get("shipped_cid") else [])
        decision = kwargs.get("decision") or {}
        candidates_info = kwargs.get("candidates_info") or {}
        round_n = kwargs.get("round_n")
        if not shipped and decision.get("decision_type") == "no_op" and candidates_info:
            try:
                cid = pick_top_candidate(candidates_info)
                if cid is not None:
                    run_dir = next(iter(candidates_info.values()))[0].parent.parent.parent
                    gate_results = run_minimal_gate_subset(cid, candidates_info, current_round=round_n)
                    if gate_results:
                        append_noop_gatecheck_audit(run_dir, round_n, cid, gate_results)
            except Exception as exc:  # noqa: BLE001 — confirmation must never break the round
                _LOG.warning("noop_gatecheck failed (non-fatal): %s", exc)
        return stage_4

    _orch_mod.run_stage_4 = _wrapped
    try:
        yield
    finally:
        _orch_mod.run_stage_4 = original


__all__ = [
    "FLAG",
    "EXCLUDED_GATES",
    "noop_gatecheck_enabled",
    "write_rejected_ledger_on_critic_failed",
    "install_noop_ledger_fix",
    "pick_top_candidate",
    "run_minimal_gate_subset",
    "append_noop_gatecheck_audit",
    "install_noop_gatecheck",
]
