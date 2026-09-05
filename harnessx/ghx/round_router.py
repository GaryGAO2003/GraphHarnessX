# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Route one round through the GHX overlays — the same way on every bed.

Extracted verbatim from the GAIA launcher when the tau2 arm needed it.  Nothing
here knows what a task looks like: the caller supplies the failing/passing sets
and the resolvers, and every overlay re-reads its own env flag at call time, so
one code path covers the whole ladder on any bed that runs the vendored
:class:`~harnessx.aegis.orchestrator.AegisOrchestrator`.
"""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

from .graph_gate import run_round_with_graph_gate
from .overlay import run_round_with_graph_evidence


class _ScopeProxy:
    """Compose the scope gate (M24: cone-reach refusal + resolution annotation)
    into the round exactly like _GateProxy composes the existence gate: the outer
    wrapper's ``run_round`` call lands here, and this wrapper's own ``run_round``
    call lands on the next layer down."""

    def __init__(self, orch, parent_config_path) -> None:
        self._orch = orch
        self.run_dir = orch.run_dir
        self._parent_config_path = parent_config_path

    async def run_round(self, **kwargs):
        from harnessx.ghx.candidate_scope import run_round_with_scope_gate

        return await run_round_with_scope_gate(
            self._orch,
            parent_config_path=self._parent_config_path,
            gate_enabled=None,  # re-reads HARNESSX_GHX_GATE_SCOPE
            **kwargs,
        )


class _GateProxy:
    """Make the evidence overlay's inner ``run_round`` *be* the graph-gate overlay.

    The evidence wrapper reads ``orchestrator.run_dir`` and then calls
    ``orchestrator.run_round(**kwargs)``.  Handing it this proxy composes the two named
    wrappers without either duplicating the other: the evidence wrapper materialises its
    cones/facts, then its ``run_round`` call lands in the gate wrapper, whose own
    ``run_round`` call lands on the real orchestrator.
    """

    def __init__(self, orch, gate_u_resolver, parent_config_path) -> None:
        self._orch = orch
        self.run_dir = orch.run_dir
        self._gate_u_resolver = gate_u_resolver
        self._parent_config_path = parent_config_path

    async def run_round(self, **kwargs):
        return await run_round_with_graph_gate(
            self._orch,
            u_resolver=self._gate_u_resolver,
            parent_config_path=self._parent_config_path,
            gate_enabled=None,  # re-reads HARNESSX_GHX_GRAPH_GATE
            **kwargs,
        )



async def run_ghx_round(
    orch,
    *,
    failed_task_ids,
    passed_task_ids,
    evidence_resolver,
    # Optional like every other resolver on this path: without it facts.md simply has
    # no absent-capability section, which is the correct reading of "no verdicts wired"
    # — never "no gaps found".
    capability_resolver=None,
    flip_task_ids=None,
    passed_now_task_ids=None,
    gate_u_resolver,
    parent_config_path,
    **run_round_kwargs,
):
    """Route one round through the GHX overlays, flag-driven.

    Both wrappers re-read their own env flag at call time and are pure pass-throughs
    when off, so this one code path covers every level:

    * evidence off, gate off  → plain ``orch.run_round`` (L0/L1);
    * evidence on,  gate off  → cones/facts materialised, then ``orch.run_round`` (L2/L3);
    * evidence off, gate on    → gate-wrapped ``orch.run_round``;
    * evidence on,  gate on    → cones/facts, then gate-wrapped ``orch.run_round`` (L4).

    ``failed_task_ids``/``evidence_resolver`` feed the evidence overlay;
    ``gate_u_resolver``/``parent_config_path`` feed the gate overlay; the remaining
    ``run_round_kwargs`` are forwarded verbatim to the real ``run_round``.
    """
    from harnessx.ghx.candidate_scope import scope_gate_enabled
    from harnessx.ghx.graph_gate import graph_gate_enabled
    from harnessx.ghx.guidance import guidance_enabled, install_guidance
    from harnessx.ghx.layer_a import install_layer_a, layer_a_enabled
    from harnessx.ghx.attribution_backfill import attribution_backfill_enabled, install_attribution_backfill
    from harnessx.ghx.evolver_fallback import evolver_fallback_enabled, install_evolver_fallback
    from harnessx.ghx.flip_ledger import flip_ledger_enabled, install_flip_ledger
    from harnessx.ghx.variance_profile import install_variance_profile, variance_profile_enabled
    from harnessx.ghx.population import install_population, population_enabled
    from harnessx.ghx.regression_triage import install_regression_triage, regression_triage_enabled
    from harnessx.ghx.singleshot_digester import install_singleshot_digester, singleshot_enabled
    from harnessx.ghx.strategy_population import install_strategy_population, strategy_population_enabled
    from harnessx.ghx.anchor_repair import anchor_repair_enabled, install_anchor_repair
    from harnessx.ghx.noop_gatecheck import install_noop_gatecheck, install_noop_ledger_fix, noop_gatecheck_enabled

    # M24 gates batch: scope gate (C + resolution annotation) wraps INSIDE the
    # sixth gate — its stage-4 shim is installed later, so at dispatch it runs
    # OUTER (official → existence gate → scope gate), i.e. scope sees the
    # existence-filtered shipped set.
    target = _ScopeProxy(orch, parent_config_path) if scope_gate_enabled() else orch
    target = _GateProxy(target, gate_u_resolver, parent_config_path) if graph_gate_enabled() else target
    # M23 G1c: evidence into the prescription-writing roles (Evolver/Critic
    # pointers, evolver step-countdown, gate-refusal routing). Installed OUTSIDE
    # the gate wrapper so the gate's own run_stage_4 wrap captures the guidance
    # wrap as its "original" and both compose; restored when the round returns.
    guidance_ctx = (
        install_guidance(orch.run_dir, run_round_kwargs["round_n"])
        if guidance_enabled()
        else contextlib.nullcontext()
    )
    # M24 P2: Layer A takeover — Stage P's extract_trace_facts swapped for the
    # graph-projected builder for the round's duration. Self-locating (derives
    # R{n-1} from each trajectory path), so no resolver plumbing; per-rollout
    # official fallback when a U is missing. Restored with the round.
    layer_a_ctx = install_layer_a() if layer_a_enabled() else contextlib.nullcontext()
    # M24 P3: regression triage — the official regressions.md gets its three
    # rulers (statistical kill-grade, per-ship cone scope, streak grading) and
    # a triage-aware mandate, at the writer seam. Restored with the round.
    triage_ctx = install_regression_triage() if regression_triage_enabled() else contextlib.nullcontext()
    # M24 P4: motif population table — aggregated after every digest is written,
    # before the Planner reads; population.md + a summary.md section.
    population_ctx = install_population() if population_enabled() else contextlib.nullcontext()
    # M25: flip ledger — cross-round pass matrix (task_history.jsonl) crossed with
    # this round's failure_mode/strategy tags; graph_evidence/flip_ledger.md only
    # (no summary.md section), so ordering against population/strategy_ctx below
    # is cosmetic, not load-bearing. Not in _PROVEN_SEAMS — unproven, own flag.
    flip_ctx = install_flip_ledger() if flip_ledger_enabled() else contextlib.nullcontext()
    # M27 T2.1: variance profile — per-round unstable-task pass/fail/steps/exit
    # read (flip_ledger's swinger/never census plus the "long-then-wrong" fixable
    # shape from W4·C1). Same aggregate_digests chain-patch seam as flip_ledger;
    # graph_evidence/variance_profile.md(+.json) only. Own flag, own storage cell.
    variance_ctx = install_variance_profile() if variance_profile_enabled() else contextlib.nullcontext()
    # M24 fix #2: evolver-burnout revival from the rejected pool (Stage 2 seam).
    fallback_ctx = install_evolver_fallback() if evolver_fallback_enabled() else contextlib.nullcontext()
    # M24 fix #1: the ledger's evidence backfill counts U (graph-first, per-task
    # vendored fallback) — direct/orphan finally reaches processor ships.
    attribution_ctx = install_attribution_backfill() if attribution_backfill_enabled() else contextlib.nullcontext()
    singleshot_ctx = install_singleshot_digester() if singleshot_enabled() else contextlib.nullcontext()
    # strategy_ctx must ENTER after population_ctx so its wrapper chains on top
    strategy_ctx = install_strategy_population() if strategy_population_enabled() else contextlib.nullcontext()
    repair_ctx = install_anchor_repair() if anchor_repair_enabled() else contextlib.nullcontext()
    # M27 T1.2(a): rejected-candidates ledger fix on the critic_failed path —
    # pure bookkeeping, installed unconditionally like graph_proposals (its own
    # wrapper adds a ledger row, never changes what ships).
    noop_ledger_ctx = install_noop_ledger_fix()
    # M27 T1.2(b): gate-confirmed no_op — own flag, installed conditionally like
    # every other overlay on this chain.
    noop_gate_ctx = install_noop_gatecheck() if noop_gatecheck_enabled() else contextlib.nullcontext()
    with guidance_ctx, layer_a_ctx, triage_ctx, population_ctx, flip_ctx, variance_ctx, strategy_ctx, fallback_ctx, attribution_ctx, singleshot_ctx, repair_ctx, noop_ledger_ctx, noop_gate_ctx:
        return await run_round_with_graph_evidence(
            target,
            failed_task_ids=failed_task_ids,
            passed_task_ids=passed_task_ids,
            resolver=evidence_resolver,
            capability_resolver=capability_resolver,
            flip_task_ids=flip_task_ids,
            passed_now_task_ids=passed_now_task_ids,
            evidence_enabled=None,  # re-reads HARNESSX_GHX_AEGIS_EVIDENCE
            **run_round_kwargs,
        )



def ever_passed(run_dir, before_round: int) -> set:
    """Task ids that passed at least once in any round strictly before this one.

    At k=1 a task fails or passes on a single draw, and this bed's two rollouts
    disagree on about a fifth of tasks — so roughly a quarter of any k=1 failing set
    are lottery losers that would pass on a re-draw. That set is the numerator for
    the lift table and the input to every Digester, and salting it with non-failures
    pulls every node's lift toward 1.0, which is exactly the separation GHX's claim
    rests on.

    History is free: a task that has already passed under this config lineage is not
    a failure of it, whatever this round's single draw said. Reads task_history.jsonl,
    which the pilot writes per round; returns an empty set when there is no history
    (round 1 has none, and round 1 is the round that matters least — it ships nothing).
    """

    path = Path(run_dir) / "data" / "task_history.jsonl"
    if not path.exists():
        return set()
    out = set()
    try:
        for line in path.open(encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if int(d.get("round", -1)) >= before_round:
                continue
            if d.get("passed") or any(d.get("passed_flags") or []):
                out.add(str(d.get("task_id")))
    except OSError:
        return set()
    return out


__all__ = ["ever_passed", "run_ghx_round"]
