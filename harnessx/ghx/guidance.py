# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Evidence into the prescription-writing roles (module G1c, M23).

M22 measured exactly where the evidence chain broke. G1 wrote cones/facts every
round and G1b pointed the Digester and Planner at them — landscapes engaged the
evidence 16/16 times. But the two roles that WRITE and JUDGE prescriptions were
never told it exists: candidates cited ``graph_evidence/`` 0 times in 31, the
Evolver's per-candidate cost was flat against the no-evidence arm ($13.0 vs
$13.7), and predicted sets sprawled to 27 tasks because nothing asked "is the
edited node in this task's own cone?". This module closes that half:

* **Evolver pointer + cone-first protocol** — the same double rebind
  :mod:`harnessx.ghx.proposal_seam` documents (``stages.propose``'s own copy of
  the name plus the defining module for the ask-more lazy import), appending
  the evidence paths and the reading/prediction discipline to the session
  prompt. Ask-more subcalls are passed through untouched, same as the seam.
* **Critic pointer** — ``stages.judge``'s module-level copy of
  ``build_critic_harness``; the Critic is told to price predicted tasks against
  their own cones and to cite the evidence files instead of re-deriving them
  with throwaway scripts (M22 L1 R6: the Critic hand-verified a regression with
  scripts, wrote the result as prose, and the candidate died on IV-3).
* **Evolver step-countdown** — three Evolver sessions burned through the
  400-step ceiling at ~$50 each (one produced zero candidates). The exact
  processor that cured rollout budget-starvation in M22 L0 R3
  (:class:`~harnessx.processors.control.step_countdown.StepCountdownProcessor`,
  auto-discovering the session's own ``max_steps``) is appended to the meta
  session's processor list.
* **Gate-refusal routing** — P-19 routed COMPOSE refusals into
  ``rejected_candidates.jsonl`` and the loop closed (L0's re-bucketed revival
  shipped and cured its arm). GATE refusals stayed in
  ``archive/*.context.json`` where no next-round reader looks, and M22 L1's
  revived C-R8-02 died on the same wall its ancestor was never told about.
  A wrap of ``run_stage_4`` writes every failed gate's reason to
  ``R{n}/graph_evidence/gate_refusals.md``; the NEXT round's Evolver pointer
  lists the previous round's file. (The sixth graph gate adds its refusals to
  the stage result AFTER this writer runs — those are already written
  separately under ``graph_evidence/gate/``.)

M27 T2.2/T2.3 add the two pieces the overnight survey's W2·B3 verdict pinned as
missing (``docs/ghx-overnight-0823-research.md``, "Planner 结构性失明(码上钉死)"):
``PlannerInputs`` (``agents/planner.py:30-46``) carries no bucket/flip/conversion
prior, and this module's own rebind list — B3 named the exact lines,
``guidance.py:328-330,372-374`` in the pre-fix state — rebound Evolver and Critic
but never the Planner. Both new pieces ride the SAME flag,
``HARNESSX_GHX_PLANNER_SENSES``, deliberately: the Planner's target selection and
the Critic's hit pricing are two halves of one capability (fate-bucket base
rates), and splitting them across two flags risks a Planner that justifies a
target against a base rate the Critic was never told to price against, or the
reverse.

* **Planner fate-bucket priors** — rebinds ``stages.plan.build_planner_harness``
  (the CALLING module's own copy of the name — see
  :mod:`harnessx.ghx.brief_pointers`'s module docstring for why rebinding the
  DEFINING module, ``agents.planner``, does not reach Stage 1's call site;
  verified there empirically, not re-verified here) to point the Planner at
  ``variance_profile.md``/``flip_ledger.md`` and append the fate-bucket base-rate
  text (NEVER converts passively at ~17-24%, PROB swingers at ~50% with
  targeting adding nothing) plus the "long-then-wrong" fixable-pool pointer.
* **Critic base-rate pricing** — extends the existing Critic pointer
  (``_critic_section``) with the same base-rate numbers, so a predicted-task hit
  is priced against its fate bucket's passive conversion rate instead of at face
  value — text only, no scoring code changes; the Critic is an LLM reading
  instructions.

Flag ``HARNESSX_GHX_GUIDANCE`` (call-time read, default off) gates the whole
module exactly as before; ``HARNESSX_GHX_PLANNER_SENSES`` (call-time read,
default off, independent flag) additionally gates the two M27 pieces so a
config already running with guidance on does not pick up the Planner rebind for
free. Nothing here writes a byte under ``harnessx/aegis/`` — runtime rebinds
restored in a ``finally``, the same technique as graph_gate / brief_pointers /
proposal_seam.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path

from .brief_pointers import (
    _append_pointer_to_config,
    _evidence_dir,
    _facts_path,
    _record_injection,
    _regression_diffs_path,
)

_LOG = logging.getLogger("harnessx.ghx.guidance")
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})
FLAG = "HARNESSX_GHX_GUIDANCE"
PLANNER_SENSES_FLAG = "HARNESSX_GHX_PLANNER_SENSES"

_COUNTDOWN_TARGET = "harnessx.processors.control.step_countdown.StepCountdownProcessor"

# ── M27 T2.2/T2.3: fate-bucket base rates + fixable-pool shape ─────────────────
#
# Sourced from docs/ghx-overnight-0823-research.md §W2·B3 ("瞄准账" — the
# targeting-vs-fate-bucket verdict table, ~line 116) and §W4·C1 ("方差来源普查" —
# the fixable-pool census, ~line 173). Both were one-time offline script passes
# over experiments/analysis/overnight_0823/; recompute before citing these past
# M27 rather than treating them as a permanent constant.
#
# W2·B3: targeted vs untargeted conversion rate, by fate bucket.
_NEVER_TARGETED_RATE = 0.244  # NEVER-so-far, targeted: 24.4%
_NEVER_UNTARGETED_RATE = 0.169  # NEVER-so-far, untargeted: 16.9%
_NEVER_P_VALUE = 0.128  # direction only, not significant
_PROB_TARGETED_RATE = 0.500  # PROB swinger, targeted: 50.0%
_PROB_UNTARGETED_RATE = 0.515  # PROB swinger, untargeted: 51.5%
_PROB_P_VALUE = 0.865  # targeting adds nothing on the dominant bucket
# CONFIG-LINKED: 85.7% vs 65.5%, n=7 — too small to price against; not cited below.

# W4·C1: the fixable-pool shape ("long-then-wrong" — see variance_profile.py,
# which computes this per-task, per-round; these are the census-level fractions).
_FIXABLE_LOCALIZED_FRACTION = "28/63 (44%)"
_LONG_THEN_WRONG_FRACTION = "22/28"
_FIXABLE_DONE_WRONG_PCT = 0.62  # runs to completion, wrong answer
_FIXABLE_BUDGET_DEATH_PCT = 0.38  # dies on budget instead


def guidance_enabled() -> bool:
    """True when the prescription-side guidance should be installed.

    Read at call time (never cached at import), default OFF — same convention as
    every other GHX flag.
    """
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def planner_senses_enabled() -> bool:
    """True when the M27 Planner-rebind + Critic-baserate pieces should fire.

    Read at call time, default OFF, independent of :func:`guidance_enabled` — a
    config already running ``HARNESSX_GHX_GUIDANCE=1`` does not pick up the
    Planner rebind for free; both flags must be on (``install_guidance`` is only
    entered at all when ``guidance_enabled()`` is true).
    """
    return os.environ.get(PLANNER_SENSES_FLAG, "").strip().lower() in _ENABLE_VALUES


def _gate_refusals_path(run_dir, round_n: int) -> Path:
    return _evidence_dir(run_dir, round_n) / "gate_refusals.md"


# ── pointer text ─────────────────────────────────────────────────────────────


def _evolver_paths(run_dir, round_n: int) -> "list[str]":
    """The Evolver's reading list — ONE stitched map plus the prior gate refusals.

    By M25 this seam handed the Evolver five separate files (facts,
    population, regression diffs, cheatsheet, refusals) beside the digests and
    the landscape it already reads — a per-session reading burden that grew a
    file per campaign.  They are now stitched into a single ``map.md`` in a
    fixed order (survival rules first, then the lift/at-risk map, populations,
    the flip ledger, diffs), so the Evolver opens one map instead of
    re-assembling it from five tabs every fresh session.  The source files
    keep being written — they are
    per-audience artifacts (Planner pointers, SOP checks, tests) — this only
    changes what the EVOLVER is pointed at.

    Refusals stay separate: they are the previous round's document, and folding
    last round's text into this round's map would misdate every anchor in it.
    Any stitch failure degrades to the old five-file list — guidance must never
    sink the round.
    """
    # Cheatsheet (M24 批改 #2): written fresh each round so the fresh session's
    # survival rules can never be stale.
    from .cheatsheet import cheatsheet_enabled, write_cheatsheet

    cheat_path = None
    if cheatsheet_enabled():
        try:
            cheat_path = write_cheatsheet(run_dir, round_n)
        except Exception as exc:  # noqa: BLE001 — guidance must not sink the round
            _LOG.warning("cheatsheet write failed (skipped): %s", exc)

    parts = [
        p
        for p in (
            cheat_path,
            _facts_path(run_dir, round_n),
            _evidence_dir(run_dir, round_n) / "population.md",
            _evidence_dir(run_dir, round_n) / "flip_ledger.md",
            _regression_diffs_path(run_dir, round_n),
        )
        if p is not None and p.exists()
    ]
    out: list[str] = []
    if parts:
        try:
            body = ["# Round map — every table the Evolver needs, one file", ""]
            for p in parts:
                body.append(f"<!-- stitched from {p.name} -->")
                body.append(p.read_text(encoding="utf-8").rstrip())
                body.append("")
            map_path = _evidence_dir(run_dir, round_n) / "map.md"
            map_path.parent.mkdir(parents=True, exist_ok=True)
            map_path.write_text("\n".join(body) + "\n", encoding="utf-8")
            out.append(str(map_path.resolve()))
        except Exception as exc:  # noqa: BLE001 — fall back to the per-file list
            _LOG.warning("map.md stitch failed (%s) — pointing at the parts", exc)
            out.extend(str(p.resolve()) for p in parts)
    refusals = _gate_refusals_path(run_dir, round_n - 1)
    if refusals.exists():
        out.append(str(refusals.resolve()))
    return out


def _evolver_section(run_dir, round_n: int, paths: "list[str]") -> str:
    cones_dir = _evidence_dir(run_dir, round_n) / "cones"
    lines = [
        "",
        "",
        "## Graph evidence (GHX) — read before proposing",
        "",
        "Causal evidence for this round's failures, derived from the recorded",
        "execution graph (not from trace text):",
        "",
    ]
    lines += [f"- {p}" for p in paths]
    lines += [
        f"- per-task cone maps: {cones_dir.resolve()}\\<task_id>.md",
        "",
        "Cone-first protocol: for EVERY task you intend to name in predicted_impact,",
        "open its cone file FIRST (a ~2KB map) and read only the trajectory steps the",
        "cone says causally mattered. Do not spelunk whole trajectories before the",
        "cone has told you where to look — the map exists so your session budget goes",
        "into designing the fix, not into re-deriving the diagnosis.",
        "",
        "Prediction discipline: predict a task ONLY when your edit touches a node",
        "that appears in that task's own cone (cone_sigs.json in the same directory",
        "lists each task's cone nodes). A cluster-wide prediction backed only by the",
        "shared lift table is a halo claim — it dilutes your hit rate and the Critic",
        "is told to price it as unsupported.",
    ]
    if any(p.endswith("gate_refusals.md") for p in paths):
        lines += [
            "",
            "gate_refusals.md above lists WHY last round's ranked candidates died at",
            "the commit gates. Read it before writing anything — a candidate that",
            "repeats a listed death burns a slot to learn nothing.",
        ]
    if any(p.endswith(("map.md", "evolver_cheatsheet.md")) for p in paths):
        lines += [
            "",
            "map.md above is THE round map — survival rules first (the IV-11",
            "evidence requirement that killed four prior candidates, current",
            "GraphProposalEdit examples — do NOT re-learn the API by probing),",
            "then the lift/at-risk table, motif populations, the flip ledger",
            "(cross-round pass matrix x this round's failure labels), and",
            "same-task regression diffs, stitched in that order. Read it FIRST.",
        ]
    lines.append("")
    return "\n".join(lines)


def _critic_section(run_dir, round_n: int, paths: "list[str]") -> str:
    cones_dir = _evidence_dir(run_dir, round_n) / "cones"
    lines = [
        "",
        "",
        "## Graph evidence (GHX) — verification aids",
        "",
        "Causal evidence files for this round, derived from the recorded execution",
        "graph:",
        "",
    ]
    lines += [f"- {p}" for p in paths]
    lines += [
        f"- per-task cone maps: {cones_dir.resolve()}\\<task_id>.md",
        "",
        "Price every predicted task against its own cone: an edit that touches no",
        "node in a task's cone (see cone_sigs.json) is a halo claim — treat it as",
        "unsupported, whatever the cluster-level lift table says. facts.md's",
        "`at risk` column prices the collateral of removing/gating a node.",
        "regression_diffs.md (when present) is the same-task pass-vs-fail cone diff",
        "— cite it for revert/regression reasoning instead of re-deriving the",
        "comparison with throwaway scripts; a citation to these files is a legal,",
        "durable anchor where prose re-derivation is not.",
        "",
    ]
    if planner_senses_enabled():
        lines += [
            "## Fate-bucket base-rate pricing (GHX, M27)",
            "",
            "Price a predicted task's hit against its fate bucket's PASSIVE conversion",
            "rate, not against 0% (docs/ghx-overnight-0823-research.md §W2·B3 —",
            "recompute before trusting these numbers past M27):",
            f"- NEVER-so-far: passive conversion runs {_NEVER_UNTARGETED_RATE:.1%}-"
            f"{_NEVER_TARGETED_RATE:.1%} whether or not anyone targeted the task "
            f"(p={_NEVER_P_VALUE:.3f}, direction only, not significant). Full credit",
            "  for a NEVER-bucket flip only above that band — the rest is base rate",
            "  the candidate did not earn.",
            f"- PROB swinger: {_PROB_TARGETED_RATE:.1%} targeted vs "
            f"{_PROB_UNTARGETED_RATE:.1%} untargeted (p={_PROB_P_VALUE:.3f}) —",
            "  targeting buys nothing on this bucket. Price a PROB-swinger flip near",
            "  zero, whatever the candidate's prose claims about it.",
            "flip_ledger.md (when present, above) names each task's bucket; a",
            "candidate's own predicted_impact prose is not evidence of which bucket a",
            "task is in.",
            "",
        ]
    return "\n".join(lines)


def _critic_paths(run_dir, round_n: int) -> "list[str]":
    out: list[str] = []
    for p in (_facts_path(run_dir, round_n), _regression_diffs_path(run_dir, round_n)):
        if p.exists():
            out.append(str(p.resolve()))
    if planner_senses_enabled():
        for p in (
            _evidence_dir(run_dir, round_n) / "flip_ledger.md",
            _evidence_dir(run_dir, round_n) / "variance_profile.md",
        ):
            if p.exists():
                out.append(str(p.resolve()))
    return out


# ── planner fate-bucket priors (M27 T2.2) ───────────────────────────────────────


def _planner_senses_paths(run_dir, round_n: int) -> "list[str]":
    out: list[str] = []
    for name in ("variance_profile.md", "flip_ledger.md"):
        p = _evidence_dir(run_dir, round_n) / name
        if p.exists():
            out.append(str(p.resolve()))
    return out


def _planner_senses_section(paths: "list[str]") -> str:
    lines = [
        "",
        "",
        "## Fate-bucket priors (GHX, M27) — read before choosing what to target",
        "",
    ]
    lines += [f"- {p}" for p in paths]
    lines += [
        "",
        "Base rates a target choice must beat, not merely cite (docs/ghx-overnight-",
        "0823-research.md §W2·B3 — recompute before trusting these numbers past",
        "M27):",
        f"- NEVER-so-far tasks convert passively {_NEVER_UNTARGETED_RATE:.1%}-"
        f"{_NEVER_TARGETED_RATE:.1%} of the time whether or not anyone targets them "
        f"(p={_NEVER_P_VALUE:.3f}, direction only, not significant). Naming a",
        "  NEVER-bucket task is not itself a contribution — name the mechanism that",
        "  would move it, or spend the slot elsewhere.",
        f"- PROB swingers convert {_PROB_TARGETED_RATE:.1%} targeted vs "
        f"{_PROB_UNTARGETED_RATE:.1%} untargeted (p={_PROB_P_VALUE:.3f}) — targeting",
        "  the median swinger buys nothing over the coin flip it already was.",
        "",
        "variance_profile.md above flags tasks matching the fixable pool's dominant",
        "shape, `long_then_wrong`: failing rounds run much longer (median steps)",
        "than this task's own passing rounds, and still terminate normally (`done`)",
        f"with a wrong answer rather than dying on budget ({_FIXABLE_DONE_WRONG_PCT:.0%}",
        f"done-wrong vs {_FIXABLE_BUDGET_DEATH_PCT:.0%} budget-death in that census's",
        f"fixable pool; {_LONG_THEN_WRONG_FRACTION} of the "
        f"{_FIXABLE_LOCALIZED_FRACTION} localized-fixable set separate on this",
        "signal alone). A task marked `long_then_wrong` is the highest-value target",
        "on this list — it names a nameable, fixable instability instead of a bucket",
        "base rate.",
        "",
    ]
    return "\n".join(lines)


# ── evolver session step-countdown (A4) ──────────────────────────────────────


def _append_step_countdown(cfg) -> bool:
    """Append a serialized StepCountdownProcessor to the config's processor list.

    Idempotent: a config that already carries one (however it got there) is left
    alone. Uses the core's own serializer so the entry is indistinguishable from
    a built one; the processor auto-discovers the session's ``max_steps`` per
    task, so no ceiling is hard-coded here.
    """
    for p in cfg.processors:
        if isinstance(p, dict) and "StepCountdownProcessor" in str(p.get("_target_", "")):
            return False
    from harnessx.core.harness import _serialize_processor
    from harnessx.processors.control.step_countdown import StepCountdownProcessor

    # escalate_within scales with the session: the class default (2) was tuned for
    # 20-step rollouts, where 2-before is 10% of budget. An Evolver session runs
    # 400 steps — a warning at step 398 is no warning (M23_L2 R5 burned through at
    # 400 with the default installed). 40-before ≈ the same 10% share.
    entry = _serialize_processor(StepCountdownProcessor(escalate_within=40))
    if not isinstance(entry, dict):
        return False
    cfg.processors.append(entry)
    return True


# ── gate-refusal routing (B7g) ───────────────────────────────────────────────


def _gate_result_fields(v) -> "tuple[bool, str]":
    """(ok, reason) from a GateResult-like object OR a plain dict."""
    if isinstance(v, dict):
        return bool(v.get("ok")), str(v.get("reason") or "")
    return bool(getattr(v, "ok", True)), str(getattr(v, "reason", "") or "")


def write_gate_refusals(run_dir, round_n: int, stage_4: dict) -> "str | None":
    """Write every failed gate's reason to ``R{n}/graph_evidence/gate_refusals.md``.

    Returns the path when at least one refusal was written, else ``None`` (no
    file — an absent file means "no gate refusals this round", never an empty
    header). Skipped gates ("skipped: earlier gate failed") are folded away so
    the file names the ACTUAL wall, not its shadow.
    """
    gate_results = (stage_4 or {}).get("gate_results") or {}
    rows: list[tuple[str, list[tuple[str, str]]]] = []
    for cid in sorted(gate_results):
        fails: list[tuple[str, str]] = []
        for gate_name, verdict in (gate_results[cid] or {}).items():
            ok, reason = _gate_result_fields(verdict)
            if ok or reason.startswith("skipped:"):
                continue
            fails.append((str(gate_name), reason))
        if fails:
            rows.append((cid, fails))
    if not rows:
        return None

    lines = [
        f"# Gate refusals — R{round_n}",
        "",
        "Candidates the Critic ranked that died at the commit gates, with the exact",
        "refusal text. This is the gate-layer extension of P-19 (compose refusals",
        "already flow into rejected_candidates.jsonl): a refusal names the fix, and",
        "a next-round candidate that repeats a death listed here is a wasted slot.",
        "",
    ]
    for cid, fails in rows:
        lines.append(f"## {cid}")
        for gate_name, reason in fails:
            lines.append(f"- {gate_name}: {reason}")
        lines.append("")
    path = _gate_refusals_path(run_dir, round_n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


# ── the install ──────────────────────────────────────────────────────────────


@contextlib.contextmanager
def install_guidance(run_dir, round_n: int):
    """Rebind the Evolver/Critic/Planner builders and ``run_stage_4`` for one round.

    Restored in a ``finally``, including when the wrapped body raises. Each
    wrapper calls whatever was bound when this installed — so it composes with
    :mod:`harnessx.ghx.proposal_seam` (which may already hold the evolver name)
    in either nesting order, and with :mod:`harnessx.ghx.brief_pointers`'s own
    Planner rebind (G1b) the same way. Off-path (no evidence files on disk)
    appends the step-countdown only; a config with no evidence pointer is
    otherwise exactly what the underlying builder produced. The Planner rebind
    (M27 T2.2) is additionally gated by :func:`planner_senses_enabled` — see
    module docstring for why it rides its own flag.
    """
    import harnessx.aegis.agents.evolver as _evolver_mod
    import harnessx.aegis.orchestrator as _orch_mod
    import harnessx.aegis.stages.judge as _judge_mod
    import harnessx.aegis.stages.plan as _plan_mod
    import harnessx.aegis.stages.propose as _propose_mod

    cur_propose = _propose_mod.build_evolver_harness
    cur_agents = _evolver_mod.build_evolver_harness
    cur_critic = _judge_mod.build_critic_harness
    cur_stage4 = _orch_mod.run_stage_4
    cur_planner = _plan_mod.build_planner_harness

    def _make_evolver_wrapper(orig):
        def _wrapped(inputs):
            cfg = orig(inputs)
            try:
                if getattr(inputs, "ask_more_brief_path", None) is not None:
                    return cfg  # ask-more: passthrough, same as the L5 seam
                paths = _evolver_paths(run_dir, round_n)
                if paths:
                    _append_pointer_to_config(cfg, _evolver_section(run_dir, round_n, paths))
                    _record_injection(run_dir, round_n, "evolver", None, paths)
                _append_step_countdown(cfg)
            except Exception as exc:  # noqa: BLE001 — guidance must never sink a round
                _LOG.warning("guidance: evolver injection failed (non-fatal): %s", exc)
            return cfg

        return _wrapped

    def _wrapped_critic(inputs, *args, **kwargs):
        cfg = cur_critic(inputs, *args, **kwargs)
        try:
            paths = _critic_paths(run_dir, round_n)
            if paths:
                _append_pointer_to_config(cfg, _critic_section(run_dir, round_n, paths))
                _record_injection(run_dir, round_n, "critic", None, paths)
        except Exception as exc:  # noqa: BLE001 — guidance must never sink a round
            _LOG.warning("guidance: critic injection failed (non-fatal): %s", exc)
        return cfg

    async def _wrapped_stage4(**kwargs):
        result = await cur_stage4(**kwargs)
        try:
            n = kwargs.get("round_n", round_n)
            written = write_gate_refusals(run_dir, int(n), result)
            if written:
                _LOG.info("guidance: gate refusals routed to %s", written)
        except Exception as exc:  # noqa: BLE001 — routing must never sink a round
            _LOG.warning("guidance: gate-refusal routing failed (non-fatal): %s", exc)
        return result

    def _wrapped_planner(inputs):
        cfg = cur_planner(inputs)
        try:
            paths = _planner_senses_paths(run_dir, round_n)
            if paths:
                _append_pointer_to_config(cfg, _planner_senses_section(paths))
                _record_injection(run_dir, round_n, "planner_senses", None, paths)
        except Exception as exc:  # noqa: BLE001 — guidance must never sink a round
            _LOG.warning("guidance: planner senses injection failed (non-fatal): %s", exc)
        return cfg

    _propose_mod.build_evolver_harness = _make_evolver_wrapper(cur_propose)
    _evolver_mod.build_evolver_harness = _make_evolver_wrapper(cur_agents)
    _judge_mod.build_critic_harness = _wrapped_critic
    _orch_mod.run_stage_4 = _wrapped_stage4
    if planner_senses_enabled():
        _plan_mod.build_planner_harness = _wrapped_planner
    try:
        yield
    finally:
        _propose_mod.build_evolver_harness = cur_propose
        _evolver_mod.build_evolver_harness = cur_agents
        _judge_mod.build_critic_harness = cur_critic
        _orch_mod.run_stage_4 = cur_stage4
        _plan_mod.build_planner_harness = cur_planner


__all__ = [
    "FLAG",
    "PLANNER_SENSES_FLAG",
    "guidance_enabled",
    "planner_senses_enabled",
    "install_guidance",
    "write_gate_refusals",
]
