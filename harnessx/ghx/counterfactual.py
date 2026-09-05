# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Counterfactual replay — the only causal-grade instrument in the ledger (M24).

Every attribution verdict the loop produces is existential (a mechanism was
present and a task flipped); ``direct`` still cannot say *because*.  The one
instrument that can is a replay of the world without the ship: run the task on
the PREVIOUS round's config (the last config that did not contain this round's
ships) and see whether the regression still happens.

Scoped exactly as reviewed, because unscoped it manufactures false causal
evidence:

* **trigger** — adjudication only: when the regression ledger would kill a
  round (the triage's statistical ruler says EXCESS), not per-ship, not
  routine;
* **eligibility** — only regressed tasks with a pre-regression pass streak
  ≥ 4 (L2-R9 measured: 11 of 12 "hard regressions" were swingers at streak
  ≤ 3 — a removal replay on those is a coin flip dressed as causal evidence);
* **interpretation** — this replays the round's SHIP-SET removal (the prior
  round's config), not one ship's; with multiple same-round ships the verdict
  binds the set, and the cone ruler apportions within it.

v1 is an adjudication tool with an injected runner (same contract as the gate
replay: the caller owns harness construction).  It is NOT wired into the live
round loop — the Critic's kill decision happens mid-round and spending
rollouts there is a policy question; the tool exists so a kill can be
adjudicated the moment it is proposed, manually or by a later wiring.

Verdict per task (k replays, default 1):

* ``still_fails``  — the regression reproduces WITHOUT the ships → the ships
  are exonerated for this task;
* ``passes``       — the task passes without the ships → the ship-set is the
  proximate cause (streak ≥ 4 makes the base rate low enough to read);
* ``mixed``        — k > 1 disagreed; treat as unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .regression_triage import compute_triage


@dataclass
class CounterfactualPlan:
    round_n: int
    config_path: str  # R{n-1}/config.yaml — the world without this round's ships
    suspects: list = field(default_factory=list)  # ship ids bound by the verdict
    eligible: list = field(default_factory=list)  # task ids, streak-gated
    skipped_swingers: int = 0
    stat_verdict: str = ""

    @property
    def worth_running(self) -> bool:
        return bool(self.eligible) and self.stat_verdict == "EXCESS"


def plan_counterfactual(run_root, round_n: int, evolve_round_n: int | None = None) -> CounterfactualPlan:
    """Build the adjudication plan from the same triage the mandate used."""
    run_root = Path(run_root)
    evolve = evolve_round_n if evolve_round_n is not None else round_n + 1
    t = compute_triage(run_root, round_n, evolve)
    eligible = t.counterfactual_eligible()
    prior = run_root / f"R{round_n - 1}" / "config.yaml"
    return CounterfactualPlan(
        round_n=round_n,
        config_path=str(prior) if prior.exists() else "",
        suspects=[s.ship_id for s in t.ships],
        eligible=eligible,
        skipped_swingers=len(t.streaks) - len(eligible),
        stat_verdict=t.stat_verdict,
    )


@dataclass
class CounterfactualVerdict:
    task_id: str
    results: list = field(default_factory=list)  # bool per replay (passed?)

    @property
    def verdict(self) -> str:
        if not self.results:
            return "unresolved"
        if all(self.results):
            return "passes"  # ship-set is the proximate cause
        if not any(self.results):
            return "still_fails"  # ships exonerated for this task
        return "mixed"


def run_counterfactual(plan: CounterfactualPlan, runner, *, k: int = 1, timeout_s: float = 1800.0) -> list:
    """Execute the plan with the injected runner.

    ``async runner(config_path, task_id, session_id) -> bool | None`` — passed?
    (None = replay itself failed; recorded as no result, never as a verdict.)
    Runs on a fresh event loop in a worker thread, same bridge as the gate
    replay — callers are usually inside a running loop.
    """
    from .gate_replay import run_coro_bounded

    out: list = []
    if not plan.config_path:
        return out
    for tid in plan.eligible:
        v = CounterfactualVerdict(task_id=tid)
        for i in range(max(1, k)):
            session_id = f"counterfactual/R{plan.round_n}-{tid}-k{i}"
            ok, res = run_coro_bounded(
                lambda cfg=plan.config_path, t=tid, s=session_id: runner(cfg, t, s),
                timeout_s=timeout_s,
                name=f"counterfactual-{tid[:8]}-k{i}",
            )
            if ok and res is not None:
                v.results.append(bool(res))
        out.append(v)
    return out


def render_counterfactual(plan: CounterfactualPlan, verdicts: list) -> str:
    L = [
        f"# Counterfactual adjudication — R{plan.round_n} ship-set removal",
        "",
        f"- statistical ruler said: **{plan.stat_verdict}**"
        + ("" if plan.worth_running else " — adjudication not warranted (run anyway = manual override)"),
        f"- world-without-ships config: `{plan.config_path or '(missing)'}`",
        f"- suspects bound by this verdict: {', '.join(f'`{s}`' for s in plan.suspects) or '(none)'}",
        f"- eligible (streak ≥ 4): {len(plan.eligible)}; swingers excluded: {plan.skipped_swingers}",
        "",
    ]
    for v in verdicts:
        L.append(f"- `{v.task_id}`: **{v.verdict}** (replays: {['pass' if r else 'fail' for r in v.results]})")
    if not verdicts:
        L.append("- (no replays executed)")
    L.append("")
    return "\n".join(L)
