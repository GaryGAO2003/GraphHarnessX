# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Graph-first attribution backfill — the ledger's evidence learns to count U (M24 · fix #1).

The graph attribution backend (:mod:`harnessx.ghx.attribution_graph`) has
answered tool AND processor signatures structurally since M23 — but nothing
ever wired it into the one place evidence is actually produced:
``ledger`` backfills ``evidence_per_task`` through the vendored
``attribution.compute_evidence`` (a function-local import, resolved from the
module at call time), whose ``_check_signature`` regex-reads
``tool_call_counts`` from trajectory markdown.  Processor invocations never
appear there, so every processor ship in M22/M23/M24 graded ``joint`` —
direct/orphan only ever came from tools ships.

This wrapper is that wiring.  Per predicted task: resolve the batch U by the
run layout (``R{round}/sessions/aegis/*{task}*/graph``), ask
:func:`check_signature_in_u` (dual-form processor ids included), and take the
graph's answer when it actually answered (``backend="graph"``).  Everything
the graph cannot answer falls through to the vendored path per task — absent
U, prompt/config buckets, unrepresentable signatures: byte-identical labels
to today.  A crashing wrapper degrades to the vendored function wholesale.

Seam: patch ``harnessx.aegis.data.attribution.compute_evidence`` for the
round (the ledger resolves it at call time).  Flag:
``HARNESSX_GHX_ATTRIBUTION`` (call-time read, default off).
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_ATTRIBUTION"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})


def attribution_backfill_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


_ORIGINAL_COMPUTE = None


def compute_evidence_graph_first(
    run_root: Path,
    *,
    round_n: int,
    bucket=None,
    predicted_tasks=None,
    manifest=None,
    attribution_signature=None,
):
    _vendored = _ORIGINAL_COMPUTE
    if _vendored is None:
        from harnessx.aegis.data.attribution import compute_evidence as _vendored

    kwargs = dict(
        round_n=round_n,
        bucket=bucket,
        predicted_tasks=predicted_tasks or [],
        manifest=manifest,
        attribution_signature=attribution_signature,
    )
    if not attribution_backfill_enabled():
        return _vendored(run_root, **kwargs)
    try:
        from .attribution_graph import check_signature_in_u, infer_signature
        from .projection import find_task_u
        from harnessx.graph.unfold import load_unfolded

        sig = infer_signature(
            bucket if isinstance(bucket, str) else None, manifest, attribution_signature
        )
        if not isinstance(sig, dict):
            # prompt/config (or uninferable) — joint by definition, same as vendored
            return _vendored(run_root, **kwargs)

        # Discrimination guard.  Machine manifests happily DECLARE signatures
        # pointing at always-firing framework nodes (system_prompt_processor —
        # observed on the 30×5 ships), and any '*'-hook processor fires on
        # every task, so presence alone is vacuous there: it would grade
        # direct on every predicted task of every ship.  A signature only
        # counts as evidence when it does NOT also fire on sampled
        # NON-predicted tasks of the same batch; a signature that fires
        # everywhere answers joint, with the reason on record.  (Presence for
        # always-on mechanisms belongs to replay-flip / counterfactual, not
        # attribution — the M5 hierarchy.)
        if not _is_discriminative(sig, Path(run_root), round_n, set(map(str, kwargs["predicted_tasks"]))):
            _LOG.info(
                "attribution backfill: signature fires on sampled non-predicted tasks too "
                "(vacuous presence) — grading joint for round %d",
                round_n,
            )
            return {str(tid): "joint" for tid in kwargs["predicted_tasks"]}

        vendored_result = None
        out: dict = {}
        answered = 0
        for tid in kwargs["predicted_tasks"]:
            label = None
            u_path = find_task_u(Path(run_root) / f"R{round_n}", str(tid))
            if u_path is not None:
                try:
                    verdict = check_signature_in_u(sig, load_unfolded(u_path))
                    if verdict.answered_by_graph:
                        label = verdict.label
                        answered += 1
                except Exception as exc:  # noqa: BLE001 — one bad U must not sink the ledger
                    _LOG.warning("attribution backfill: U for %s unreadable (%s)", tid, exc)
            if label is None:
                if vendored_result is None:
                    vendored_result = _vendored(run_root, **kwargs)
                label = vendored_result.get(str(tid), "joint")
            out[str(tid)] = label
        if answered:
            _LOG.info(
                "attribution backfill: graph answered %d/%d predicted task(s) for round %d",
                answered,
                len(kwargs["predicted_tasks"]),
                round_n,
            )
        return out
    except Exception as exc:  # noqa: BLE001 — never trade the ledger for the wiring
        _LOG.warning("attribution backfill failed (vendored path): %s", exc)
        return _vendored(run_root, **kwargs)


@contextlib.contextmanager
def install_attribution_backfill():
    """Patch the attribution module's ``compute_evidence`` for one round."""
    global _ORIGINAL_COMPUTE
    import harnessx.aegis.data.attribution as _attr

    original = _attr.compute_evidence
    _ORIGINAL_COMPUTE = original
    _attr.compute_evidence = compute_evidence_graph_first
    try:
        yield
    finally:
        _attr.compute_evidence = original
        _ORIGINAL_COMPUTE = None


# A signature is vacuous when it fires on essentially EVERY task — the
# always-on framework nodes this guard was written for (system_prompt_processor,
# any '*'-hook processor).  It is not vacuous merely because it also fires
# somewhere else: `tool:Bash` runs in ~45% of this bed's tasks and `tool:WebFetch`
# in ~78%, and "the ship's tool ran here" is weak evidence at those rates, not
# absent evidence.  The first implementation could not tell the two apart — it
# sampled three tasks in sorted order and called the signature vacuous when all
# three fired, which at a 45–90% base rate is the common case.  Measured on
# M25's ledger: 10 of 11 ships graded joint on every predicted task
# (`{'direct': 0, 'joint': 16, 'orphan': 0}` and so on down the list), the sole
# exception being the one whose three sampled tasks happened to miss.  The
# ledger read as "attribution cannot answer" when the graph had answered and
# the answer was being discarded.
_VACUITY_RATE = 0.95
_VACUITY_MIN_SAMPLE = 8


def _signature_fire_rate(
    sig: dict, run_root: Path, round_n: int, predicted: set, sample: int
) -> tuple[int, int]:
    """``(fired, answered)`` over non-predicted tasks of this batch.

    Deterministic: sessions are globbed in sorted order and the first ``sample``
    graph-answerable tasks outside the predicted set are counted.  A task whose U
    is missing, unreadable, or unrepresentable for this signature is not counted
    on either side — it is absent from the estimate, never a silent "no".
    """
    from .attribution_graph import check_signature_in_u
    from harnessx.graph.unfold import load_unfolded

    sess_root = run_root / f"R{round_n}" / "sessions" / "aegis"
    if not sess_root.is_dir():
        return 0, 0
    fired = answered = 0
    for d in sorted(p for p in sess_root.iterdir() if p.is_dir()):
        tid = d.name.split("-", 1)[1] if "-" in d.name else d.name
        if tid in predicted:
            continue
        u_files = sorted(d.glob("graph/*_unfolded.jsonl"))
        if not u_files:
            continue
        try:
            verdict = check_signature_in_u(sig, load_unfolded(u_files[-1]))
        except Exception:  # noqa: BLE001 — an unreadable sample proves nothing
            continue
        if not verdict.answered_by_graph:
            continue
        answered += 1
        fired += bool(verdict.fired)
        if answered >= sample:
            break
    return fired, answered


def _is_discriminative(sig: dict, run_root: Path, round_n: int, predicted: set, sample: int = 40) -> bool:
    """False only when the signature fires on ~every non-predicted task.

    Too few answerable samples to estimate a rate → True: vacuity is a claim,
    and an unproven claim must not silently delete the graph's per-task answers.
    """
    fired, answered = _signature_fire_rate(sig, run_root, round_n, predicted, sample)
    if answered < _VACUITY_MIN_SAMPLE:
        return True
    rate = fired / answered
    if rate >= _VACUITY_RATE:
        _LOG.info(
            "attribution backfill: signature base rate %.0f%% (%d/%d non-predicted tasks) "
            "— fires on ~every task, presence proves nothing",
            100 * rate,
            fired,
            answered,
        )
        return False
    _LOG.info(
        "attribution backfill: signature base rate %.0f%% (%d/%d non-predicted tasks) "
        "— discriminative enough to grade",
        100 * rate,
        fired,
        answered,
    )
    return True
