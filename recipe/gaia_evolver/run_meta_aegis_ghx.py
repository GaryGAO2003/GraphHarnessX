#!/usr/bin/env python3
# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""GHX ladder launcher — the vendored AEGIS pilot plus the graph-hardening overlays.

This is the single launchable entry that connects the GHX modules (G1 evidence,
G2 gate, and the core U/identity flags) to the vendored GAIA-AEGIS pilot.  It adds
nothing to the pilot's science: it reuses the vendored
:func:`recipe.gaia_evolver.run_meta_aegis.run_pilot` verbatim and only injects the
overlays at the one seam the design names — where the round loop's
``orchestrator.run_round`` fires.

The ladder (``--ghx-level``):

* **L0** — every flag off.  The launcher applies no environment and delegates to the
  vendored ``run_pilot`` unchanged, so L0 through here is indistinguishable from
  running ``run_meta_aegis`` directly.
* **L1** — ``+HARNESSX_GHX_UNFOLD`` (record the unfolded graph U per run) and
  ``+HARNESSX_GHX_IDENTITY`` (record the three run-identity hashes).  Both are
  call-time env reads inside the core, so L1 is *still* the vendored pilot: no round
  wiring, just U/identity files appearing next to the trajectories.
* **L2** — ``+HARNESSX_GHX_AEGIS_EVIDENCE``.  Now the launcher wires the round through
  :func:`~harnessx.ghx.overlay.run_round_with_graph_evidence`, materialising causal
  cones + cross-task facts for the round's *failing* tasks before Stage P dispatches
  the Digester.
* **L3** — currently identical to L2.  The cross-task ``facts.md`` is written by L2's
  materialiser, so the "facts" step is not yet a separate switch; the level exists so
  the ladder can split it later without renumbering.
* **L4** — ``+HARNESSX_GHX_GRAPH_GATE``.  Additionally wraps the round with
  :func:`~harnessx.ghx.graph_gate.run_round_with_graph_gate`, the sixth (graph-
  existence) gate.
* **L5** — ``+HARNESSX_GHX_GRAPH_PROPOSALS``.  Rebinds the Evolver's builder (both
  the Stage 2 call site and the ask-more lazy-import call site — see
  :func:`~harnessx.ghx.proposal_seam.install_graph_proposals`) so its session gets
  the four graph-native ``GraphProposal*`` tools in place of hand-written
  manifests/config.yaml.  The rebind itself installs unconditionally alongside the
  round-loop seam; the flag gates only what the *wrapper* does, so — like every
  other flag on this ladder — it can be switched independently of the level.

Precedence.  ``--ghx-level`` is a convenience that sets each flag with
``setdefault`` — an environment variable the user exported already wins.  So
``HARNESSX_GHX_AEGIS_EVIDENCE=0 ... --ghx-level 2`` leaves evidence OFF, and
``HARNESSX_GHX_GRAPH_GATE=1 ... --ghx-level 1`` leaves the gate ON.  The actual
overlay behaviour is driven by the flags (each wrapper re-reads its own flag at call
time), never by the level number directly, so "explicit env wins" holds end to end.
``HARNESSX_GHX_RUNTIME`` (graph dispatch) is deliberately **not** on this ladder — the
evidence and gate overlays do not require runtime graph dispatch.

Reuse shape (reported for the record).  The vendored ``run_pilot`` is monolithic and
never calls ``orchestrator.run_round`` itself — it calls ``AegisAgent.evolve``, which
constructs the :class:`~harnessx.aegis.orchestrator.AegisOrchestrator` internally and
calls ``run_round`` two levels down.  There is therefore no ``run_round`` call site in
the pilot to wrap, and the orchestrator is byte-identity vendored code we may not edit.
So the launcher installs the overlay at that buried seam with a runtime monkeypatch of
``AegisOrchestrator.run_round`` — the exact pattern the vendored-integrity-safe gate
wrapper already uses on ``run_stage_4`` — restored in a ``finally``.  This keeps 100%
of the vendored pilot (rollouts, focus sets, rollback, curves, resume) running
unchanged; only the single round call is routed through the overlays.  No vendored
file's bytes change, so ``tests/ghx/test_vendored_integrity.py`` stays green.

Usage::

    python recipe/gaia_evolver/run_meta_aegis_ghx.py --ghx-level 2 \\
        --smoke --run-tag ghx_smoke_l2
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import gc
import os
import re
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# The vendored pilot is reused wholesale; importing it also runs its .env bootstrap
# and logging setup, which we want to share verbatim.
import recipe.gaia_evolver.run_meta_aegis as _pilot  # noqa: E402
from harnessx.aegis.orchestrator import AegisOrchestrator  # noqa: E402
from harnessx.ghx.evidence_files import core_layout_resolver  # noqa: E402
from harnessx.ghx.proposal_seam import install_graph_proposals  # noqa: E402
from harnessx.ghx.round_router import run_ghx_round  # noqa: E402

# ─── Level → flag table ───────────────────────────────────────────────────────
#
# Each level is the CUMULATIVE set of core/overlay flags it turns on.  RUNTIME is
# intentionally absent (see the module docstring).  L2 == L3 today (one materialiser
# writes both cones and facts); the split is deferred, not forgotten.
# The ladder table lives in harnessx.ghx.ladder so the tau2 launcher reads the
# same one; re-exported here because callers and tests import it from this module.
from harnessx.ghx.ladder import (  # noqa: E402,F401
    _EVIDENCE,
    _GATE,
    _GUIDANCE,
    _IDENTITY,
    _PROPOSALS,
    _PROVEN_SEAMS,
    _UNFOLD,
    LEVEL_FLAGS,
    MAX_LEVEL,
    apply_level_flags,
)


# ─── Resolvers ────────────────────────────────────────────────────────────────

_ROUND_RE = re.compile(r"R(\d+)")


def _round_from_label(label: str | None) -> int | None:
    """Parse the round index out of a rollout ``label`` (``"aegis/R0"``, ``"aegis/R2/r1"``)."""
    if not label:
        return None
    m = _ROUND_RE.search(label)
    return int(m.group(1)) if m else None


def _make_evidence_resolver(base_dir, session_run_by_task: dict):
    """A task→U resolver for GAIA's per-(round, task) session layout.

    ``session_run_by_task`` maps ``task_id -> (session_id, run_id)`` captured at the
    rollout call site (see :func:`_ghx_round_wiring`).  GAIA writes one U per rollout
    under ``session_id = f"{label}-{task_id}"`` (``run_meta._run_task`), so a single
    fixed session does not name every task's U —
    :func:`~harnessx.ghx.evidence_files.core_layout_resolver` assumes exactly one.  We
    therefore delegate to ``core_layout_resolver`` **per task**, handing it that task's
    own session_id, which is the same primitive (``find_unfolded`` + ``load_unfolded``)
    the fixed-session resolver is built from.  A task with no captured run id, or whose
    U file is absent, resolves to ``None`` (unavailable), never an empty graph.
    """

    def resolve(task_id: str):
        entry = session_run_by_task.get(task_id)
        if not entry:
            return None
        session_id, run_id = entry
        return core_layout_resolver(base_dir, session_id, {task_id: run_id})(task_id)

    return resolve


def _gate_u_resolver(candidate_id: str):
    """The honest gate resolver: no REAL replay U exists yet, so always ``None``.

    The vendored Stage-4 replay boots each candidate config against a trivial synthetic
    task, not a real GAIA task under ``HARNESSX_GHX_UNFOLD`` — so there is no U in which
    a candidate's newly-added ``tool:<name>`` would actually fire.  Two tempting shortcuts
    are both lies and are refused here:

    * the **parent round's U** — the candidate's new tool cannot appear in a run that
      predates the candidate, so checking against it would refuse every real tool add;
    * the **synthetic-smoke U** — the added tool is never exercised there either.

    Returning ``None`` makes :func:`~harnessx.ghx.graph_gate.check_graph_gate` take the
    pass-through path (``checked=False``, ``ok=True``) and record *why* it could not
    check.  The gate goes live the day a future module makes Stage-4 replay run a real
    task under ``HARNESSX_GHX_UNFOLD`` and hands that replay's U back here per candidate;
    until then this seam is wired but honestly inert.
    """
    return None



def _make_gate_replay_runner(args: argparse.Namespace):
    """The launcher-owned execution half of the Gate-B replay (M24 gates batch).

    ``async runner(config_path, task_id, session_id) -> U file path | None``.
    Builds the harness exactly the way the pilot's rollout site does
    (``model_config.agentic(round_config)``), runs the ONE task the gate chose
    under the candidate's applied config (U recording is already on at L1+),
    and locates the recorded U through the same ``find_unfolded`` primitive the
    evidence resolver uses.  No judge — the gate reads signature-fire, not
    pass/fail.  Layering note: this lives in the launcher because it imports
    recipe machinery; the generic half (task choice, honesty ladder, the
    sync→thread bridge) lives in :mod:`harnessx.ghx.gate_replay`.
    """
    from dataclasses import replace as _dc_replace


    from harnessx.core.harness import HarnessConfig
    from harnessx.core.model_config import ModelConfig
    from harnessx.graph.unfold import find_unfolded
    from recipe.gaia_evolver.run_meta import _make_provider

    domains = _pilot._load_classified_tasks(args.tasks)
    tasks_by_id = {t.task_id: t for t_list in domains.values() for t in t_list}

    async def runner(config_path: str, task_id: str, session_id: str):
        task = tasks_by_id.get(task_id)
        if task is None:
            return None
        task = _dc_replace(task, max_cost_usd=args.max_cost, max_steps=args.max_steps)
        cfg = HarnessConfig.from_yaml_file(str(config_path))
        provider = _make_provider(
            args.model, args.provider_id, api_base=args.api_base, api_key=args.api_key
        )
        harness = ModelConfig(main=provider).agentic(cfg)
        result = await harness.run(task, session_id=session_id)
        run_id = getattr(result, "run_id", "") or ""
        # Locate the U the run just recorded.  base_dir is NOT a top-level
        # sessions: key — it lives inside whichever block owns session output
        # (the journal tracer's, in every real config; smoke #5 proved the
        # top-level read finds nothing while the U sits under the journal's
        # base_dir).  Try every base_dir: value in the config, then fall back
        # to the run-root glob over the session layout the recorder actually
        # writes (R*/sessions/<session_id>/graph/<run_id>_unfolded.jsonl).
        import re as _re

        cfg_text = Path(config_path).read_text(encoding="utf-8", errors="replace")
        for m in _re.finditer(r"base_dir:\s*(.+)", cfg_text):
            base_dir = m.group(1).strip().strip("'\"")
            if not base_dir:
                continue
            u_path = find_unfolded(base_dir, session_id, run_id)
            if u_path:
                return str(u_path)
        run_root = Path(config_path).parents[3]
        hits = sorted(
            run_root.glob(f"R*/sessions/{session_id}/graph/*_unfolded.jsonl"),
            key=lambda q: q.stat().st_mtime,
        )
        exact = [q for q in hits if run_id and q.name.startswith(run_id)]
        chosen = (exact or hits)[-1] if (exact or hits) else None
        return str(chosen) if chosen else None

    return runner


# ─── Round-seam composition ───────────────────────────────────────────────────


# The overlay router and its two composition proxies now live in
# harnessx.ghx.round_router — the tau2 arm routes its rounds through the very
# same code, which is the whole claim of a bed-agnostic graph runtime.
_ghx_run_round = run_ghx_round

# ever_passed moved to harnessx.ghx.round_router (both beds keep the same
# lottery-loser filter); the private name stays for this module's callers.
from harnessx.ghx.round_router import ever_passed as _ever_passed  # noqa: E402

def _make_capability_resolver(run_dir, rollout_round: int):
    """Read each task's ``missing_capability`` out of R{n}/trajectories frontmatter.

    The pilot writes one ``<task_id>_r<i>.md`` per rollout and P-12 puts the judge's
    verdict in its frontmatter. A task can have several rollouts; the first that
    reports a gap wins, because the claim is "this run needed something it did not
    have" and one rollout saying so is enough to place the gap.

    Returns ``{}`` for anything unreadable — a missing verdict must read as *no claim*,
    never as *no gap*, and the caller renders nothing for an empty payload either way.
    """
    import json as _json

    # R{n}/trajectories holds round n's OWN rollouts — the same task reads
    # exit_reason=done/steps=9 under R0 and budget_exceeded/steps=20 under R1. The
    # evidence being materialised is about ``rollout_round``, so that is the directory,
    # matching the sibling U resolver's ``R{rollout_round}/sessions``. Off by one here
    # is silent: the glob matches nothing, every task resolves to {}, and facts.md
    # renders no section — which reads as "no gaps found" rather than "wrong folder".
    traj_dir = Path(run_dir) / f"R{rollout_round}" / "trajectories"

    def resolve(task_id: str) -> dict:
        # Two namings, because ``_write_task_trajectory`` writes ``{task.task_id}.md``
        # and the pass-k caller bakes the rollout index into ``task_id`` itself: at
        # k=2 the files are ``<task>_r0.md`` / ``<task>_r1.md``, at k=1 just
        # ``<task>.md``. Globbing only the suffixed form matches nothing under k=1 —
        # which is the configuration this campaign runs — and every task resolves to
        # {} with no error anywhere.
        for path in sorted(traj_dir.glob(f"{task_id}.md")) + sorted(
            traj_dir.glob(f"{task_id}_r*.md")
        ):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                if not line.startswith("llm_judge_verdict:"):
                    if line.strip() == "---" and text.index(line) > 0:
                        break
                    continue
                try:
                    verdict = _json.loads(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    break
                mc = verdict.get("missing_capability") if isinstance(verdict, dict) else None
                if isinstance(mc, dict) and mc.get("present"):
                    return mc
                break
        return {}

    return resolve


def _make_wrapped_run_round(orig_run_round, capture: dict, gate_u_resolver, evolve_max_steps: int = 200):
    """Build the ``AegisOrchestrator.run_round`` replacement that routes through the overlays.

    The first entry for a given orchestrator instance builds the round's overlay inputs
    and dispatches through :func:`_ghx_run_round`; because the overlays ultimately call
    ``orchestrator.run_round`` again, a re-entry guard (keyed on ``id(self)``) sends that
    inner call to the original method — otherwise the wrapper would recurse into itself.
    """
    active: set[int] = set()

    async def _wrapped(self, **kwargs):
        if id(self) in active:
            return await orig_run_round(self, **kwargs)
        active.add(id(self))
        try:
            # Set per-instance rather than on the class: a dataclass bakes its
            # defaults into __init__ at class-creation time, so assigning the class
            # attribute afterwards would look like it worked and change nothing.
            self.evolve_max_steps = evolve_max_steps
            round_n = kwargs["round_n"]
            # M24: a stateful gate resolver (real-replay) learns this round's
            # run_dir/round before the overlays dispatch; the inert function
            # resolver has no bind_round and is left alone.
            _bind = getattr(gate_u_resolver, "bind_round", None)
            if _bind is not None:
                try:
                    _bind(self.run_dir, round_n)
                except Exception:  # noqa: BLE001 — a bind failure means an unbound resolver → None → pass-through
                    pass
            # The pilot always evolves round_n from the rollouts that JUST ran in
            # R{round_n-1} (run_meta_aegis passes round_n=round_idx+1 with
            # raw_sessions_dir pointing at R{round_idx}); the orchestrator confirms
            # this ("round_n here is the round whose rollouts ALREADY ran").  So the
            # failing tasks and their U files belong to R{round_n-1}.
            rollout_round = round_n - 1
            pass_flags = kwargs.get("pass_flags_by_task") or {}
            # Drop tasks this config lineage has already solved. Under k=1 a single
            # draw decides, and this bed's rollouts disagree on ~21% of tasks, so a
            # raw failing set carries ~23% lottery losers into the cones, the lift
            # numerator and every Digester.
            solved_before = _ever_passed(self.run_dir, rollout_round)
            failed = [
                tid
                for tid, flags in pass_flags.items()
                if not any(flags) and tid not in solved_before
            ]
            # M23 (B4): the flip family — failed THIS rollout, excluded from `failed`
            # only by lineage. They are exactly the same-task cross-round diff channel's
            # subject, so they get cones + cone_sigs (no statistics). Without this the
            # lottery filter starves regression_diffs.md structurally: a P→F flip has
            # by definition passed before, so it could never reach the materialiser.
            flipped = [
                tid
                for tid, flags in pass_flags.items()
                if not any(flags) and tid in solved_before
            ]
            # Honest passing side for the diff baseline: only runs that ACTUALLY
            # passed this rollout may seed next round's pass-vs-fail comparison.
            passed_now = [tid for tid, flags in pass_flags.items() if any(flags)]
            # The control arm for facts.md's lift: solved on at least one rollout. Exact
            # complement of `failed` over the same dict, so every task lands on one side
            # and a node's fail%/pass% are measured over the SAME round's cones.
            # Control arm: solved now, or solved before. Keeping the two sides an
            # exact partition matters — a task filtered out of `failed` must land here
            # or the lift denominators stop describing the same task set.
            solved = [
                tid
                for tid, flags in pass_flags.items()
                if any(flags) or tid in solved_before
            ]
            base_dir = Path(self.run_dir) / f"R{rollout_round}" / "sessions"
            resolver = _make_evidence_resolver(base_dir, capture.get(rollout_round, {}))
            return await _ghx_run_round(
                self,
                failed_task_ids=failed,
                passed_task_ids=solved,
                evidence_resolver=resolver,
                capability_resolver=_make_capability_resolver(self.run_dir, rollout_round),
                flip_task_ids=flipped,
                passed_now_task_ids=passed_now,
                gate_u_resolver=gate_u_resolver,
                parent_config_path=kwargs.get("current_config_path"),
                **kwargs,
            )
        finally:
            active.discard(id(self))

    return _wrapped


@contextlib.contextmanager
def _ghx_round_wiring(evolve_max_steps: int = 200, gate_u_resolver=None):
    """Install the run-id capture + overlay seam for the duration of a pilot run.

    Three runtime patches, all restored on exit (no vendored bytes touched):

    1. ``run_meta_aegis._run_task`` → a wrapper that records ``(session_id, run_id)`` per
       ``(round, task_id)`` from each rollout's ``HarnessResult`` — the pilot itself keeps
       no task→run_id map, so we capture it here at the rollout call site.
    2. ``AegisOrchestrator.run_round`` → the overlay router (see :func:`_make_wrapped_run_round`).
    3. ``install_graph_proposals()`` → the Evolver-builder double rebind (see
       :func:`~harnessx.ghx.proposal_seam.install_graph_proposals`), installed
       unconditionally at the same level as #2 — the flag it guards is read inside
       its own wrapper at call time, not here, so ``HARNESSX_GHX_GRAPH_PROPOSALS``
       stays independently switchable exactly like the evidence/gate flags are.

    Yields the capture dict so callers/tests can inspect it.
    """
    capture: dict[int, dict[str, tuple[str, str]]] = {}
    orig_run_task = _pilot._run_task
    orig_run_round = AegisOrchestrator.run_round

    async def _capturing_run_task(harness, task, label, **kw):
        record = await orig_run_task(harness, task, label, **kw)
        try:
            result = record.get("_result")
            run_id = getattr(result, "run_id", None)
            tid = getattr(task, "task_id", None)
            rnd = _round_from_label(label)
            if run_id and tid and rnd is not None:
                # session_id is exactly what _run_task handed harness.run(): f"{label}-{tid}".
                capture.setdefault(rnd, {})[tid] = (f"{label}-{tid}", run_id)
        except Exception:  # noqa: BLE001 — capture is best-effort; never sink a rollout
            pass
        return record

    with contextlib.ExitStack() as stack:
        stack.enter_context(install_graph_proposals())
        _pilot._run_task = _capturing_run_task
        AegisOrchestrator.run_round = _make_wrapped_run_round(
            orig_run_round,
            capture,
            _gate_u_resolver if gate_u_resolver is None else gate_u_resolver,
            evolve_max_steps,
        )
        try:
            yield capture
        finally:
            _pilot._run_task = orig_run_task
            AegisOrchestrator.run_round = orig_run_round


# ─── CLI ──────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """The vendored pilot's parser plus ``--ghx-level``.

    Reuses ``run_meta_aegis._build_argparser`` (a fresh parser each call, so adding an
    argument here never mutates the vendored surface) to keep the CLI identical.
    """
    p = _pilot._build_argparser()
    p.description = "GHX ladder launcher over the GAIA AEGIS pilot (adds --ghx-level)."
    # The vendored default bakes in an Anthropic meta model at import time; with a
    # single-key setup (e.g. only a LiteLLM/DeepSeek key) that crashes the first meta
    # phase.  None here means "not given on the CLI" so _resolve_meta_model can fall
    # back to GAIA_META_MODEL, then to the MAIN model — one key runs the whole ladder.
    p.set_defaults(meta_model=None)
    p.add_argument(
        "--ghx-level",
        type=int,
        default=0,
        choices=sorted(LEVEL_FLAGS),
        help=(
            "Graph-hardening ladder (cumulative, off by default): "
            "0=vendored pilot; 1=+UNFOLD+IDENTITY; 2=+AEGIS_EVIDENCE; "
            "3=same as 2 (facts share L2's materialiser); 4=+GRAPH_GATE; "
            "5=+GRAPH_PROPOSALS (graph-native Evolver candidate tools); "
            "6=campaign profile (5 + every proven M24/M25 seam — layer A, triage, "
            "population, scope/replay gates, fallback, attribution, single-shot "
            "digester, cheatsheet, anchor repair; strategy_pop stays frozen out). "
            "Explicit HARNESSX_GHX_* env vars always win over the level."
        ),
    )
    p.add_argument(
        "--evolve-max-steps",
        type=int,
        default=200,
        help=(
            "Evolver tool-step ceiling (default 200 = the official value). This is the "
            "constraint that binds: Evolver runs end exit=budget_exceeded at exactly "
            "200 steps having spent a quarter of their dollar cap, so --evolve-cost "
            "does nothing. The vendored --evolve-steps reaches the old MetaAgent path, "
            "not the AEGIS Evolver."
        ),
    )
    return p


def _resolve_meta_model(args: argparse.Namespace) -> None:
    """Fill ``args.meta_model`` when ``--meta-model`` was not given.

    Precedence (mirrors the ladder's "explicit wins" contract):
    explicit ``--meta-model`` > ``GAIA_META_MODEL`` env > follow ``--model``.
    The vendored runner's own default (an Anthropic model) is deliberately NOT in the
    chain: it requires a second credential the common single-key setup does not have.
    """
    if args.meta_model is None:
        args.meta_model = os.environ.get("GAIA_META_MODEL") or args.model


def _print_ghx_plan(level: int, applied: tuple[str, ...], meta_model: str | None = None) -> None:
    print("=" * 70)
    print(f"  GHX ladder — level {level}")
    print(f"  flags set (setdefault; explicit env wins): {', '.join(applied) or '(none)'}")
    if meta_model is not None:
        print(f"  meta model (explicit > GAIA_META_MODEL > follows --model): {meta_model}")
    on = [
        f
        for f in (
            _UNFOLD,
            _IDENTITY,
            _EVIDENCE,
            _GUIDANCE,
            _GATE,
            _PROPOSALS,
            "HARNESSX_GHX_LAYER_A",
            "HARNESSX_GHX_REGRESSION_TRIAGE",
            "HARNESSX_GHX_POPULATION",
            "HARNESSX_GHX_GATE_SCOPE",
            "HARNESSX_GHX_GATE_REPLAY",
            "HARNESSX_GHX_EVOLVER_FALLBACK",
            "HARNESSX_GHX_ATTRIBUTION",
            "HARNESSX_GHX_SINGLESHOT_DIGESTER",
            "HARNESSX_GHX_CHEATSHEET",
            "HARNESSX_GHX_STRATEGY_POP",
            "HARNESSX_GHX_ANCHOR_REPAIR",
        )
        if os.environ.get(f, "").strip().lower() in {"1", "true", "on", "yes"}
    ]
    print(f"  flags effective now: {', '.join(on) or '(none)'}")
    print("=" * 70)



def _fix_merged_after_rollback(args: argparse.Namespace) -> None:
    """Resume pre-flight: un-poison merged.yaml when the last round rolled back.

    The vendored resume loads ``R{last}/applied/merged.yaml`` — the merge as
    written at commit time, BEFORE any post-batch rollback.  The rollback
    machinery reverts ``current_config`` in memory and writes audit/journal
    entries, but never rewrites merged.yaml, so a resume after a rollback
    round silently reinstates the reverted ships (measured on M24_smoke_30x5:
    R1's rolled-back pair ran batches 2–4).  This pre-flight walks
    ``audit.jsonl`` for rollback events at the last completed round and, when
    found, replaces merged.yaml with the newest prior round's config that was
    NOT itself rolled back (the validated lineage), backing up the poisoned
    file beside it.  No-op for fresh runs, rollback-free resumes, or runs
    without the files.
    """
    if int(getattr(args, "start_round", 0) or 0) <= 0:
        return
    run_dir = _pilot.RUNS_DIR / (args.run_tag or "")
    audit_path = run_dir / "audit.jsonl"
    last_round = int(args.start_round) - 1
    merged = run_dir / f"R{last_round}" / "applied" / "merged.yaml"
    if not audit_path.exists() or not merged.exists():
        return
    import json as _json

    rolled_rounds: set[int] = set()
    try:
        for line in audit_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = _json.loads(line)
            except ValueError:
                continue
            if ev.get("kind") == "rollback":
                rolled_rounds.add(int(ev.get("round", -1)))
    except OSError:
        return
    if last_round not in rolled_rounds:
        return
    restore = last_round - 1
    while restore >= 0 and restore in rolled_rounds:
        restore -= 1
    restore_cfg = run_dir / f"R{restore}" / "config.yaml"
    if restore < 0 or not restore_cfg.exists():
        print(
            f"  !! resume pre-flight: R{last_round} rolled back but no restorable "
            f"config found — resuming with merged.yaml AS-IS (poisoned)"
        )
        return
    backup = merged.with_name("merged.pre_rollback_resume.yaml")
    backup.write_bytes(merged.read_bytes())
    merged.write_bytes(restore_cfg.read_bytes())
    print(
        f"  resume pre-flight: R{last_round} had a rollback — merged.yaml replaced "
        f"with R{restore}/config.yaml (validated lineage); poisoned merge backed up "
        f"as {backup.name}"
    )


async def _dispatch(args: argparse.Namespace) -> None:
    """Run the pilot, wiring the overlay seam only when an overlay flag is effective."""
    _fix_merged_after_rollback(args)
    from harnessx.ghx.attribution_backfill import attribution_backfill_enabled as attribution_backfill_enabled_top
    from harnessx.ghx.candidate_scope import scope_gate_enabled
    from harnessx.ghx.evolver_fallback import evolver_fallback_enabled as evolver_fallback_enabled_top
    from harnessx.ghx.gate_replay import GateReplayResolver, gate_replay_enabled
    from harnessx.ghx.graph_gate import graph_gate_enabled
    from harnessx.ghx.graph_proposals import graph_proposals_enabled
    from harnessx.ghx.guidance import guidance_enabled
    from harnessx.ghx.layer_a import layer_a_enabled
    from harnessx.ghx.overlay import aegis_evidence_enabled
    from harnessx.ghx.population import population_enabled
    from harnessx.ghx.regression_triage import regression_triage_enabled
    from harnessx.ghx.singleshot_digester import singleshot_enabled
    from harnessx.ghx.strategy_population import strategy_population_enabled
    from harnessx.ghx.anchor_repair import anchor_repair_enabled

    # graph_proposals_enabled() is in this OR on purpose: it is the only thing that
    # installs install_graph_proposals() at all (see _ghx_round_wiring), so without
    # it here, setting HARNESSX_GHX_GRAPH_PROPOSALS=1 at a level below 5 (or with no
    # --ghx-level given) would never wire the seam — breaking the "explicit env wins
    # at any level" contract every other GHX flag already has.
    # The wiring is also installed for a non-default step ceiling with every overlay
    # off, which is how L0 gets the same ceiling as L2. Both arms must carry the same
    # value or the comparison is between two different Evolvers; refusing the flag at
    # L0 (the previous behaviour) guaranteed that asymmetry instead of preventing it.
    # With the flags off every overlay inside the wrapper is a pass-through, so the
    # only thing it does at L0 is set the field.
    if (
        aegis_evidence_enabled()
        or graph_gate_enabled()
        or graph_proposals_enabled()
        or guidance_enabled()
        or layer_a_enabled()
        or regression_triage_enabled()
        or population_enabled()
        or scope_gate_enabled()
        or gate_replay_enabled()
        or singleshot_enabled()
        or strategy_population_enabled()
        or anchor_repair_enabled()
        or evolver_fallback_enabled_top()
        or attribution_backfill_enabled_top()
        or args.evolve_max_steps != 200
    ):
        # M24 gates batch: with the replay flag on, the sixth gate's resolver is a
        # REAL one — it runs the candidate's longest-fail-streak predicted task under
        # the candidate's applied config (U recording is already on at L1+) and hands
        # back that replay's U. Off, the honest inert resolver stays.
        resolver = (
            GateReplayResolver(_make_gate_replay_runner(args))
            if gate_replay_enabled()
            else _gate_u_resolver
        )
        with _ghx_round_wiring(args.evolve_max_steps, gate_u_resolver=resolver):
            await _pilot.run_pilot(args)
    else:
        # L0/L1 (or any run with no effective overlay flag): the vendored round loop,
        # unwrapped. U/identity recording, if on, happens inside the core by flag.
        await _pilot.run_pilot(args)


async def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    _resolve_meta_model(args)

    # Mirror run_meta_aegis.main's preset handling (kept in lock-step by intent).
    if args.smoke:
        args.num_rounds = 2
        args.max_tasks = 1
        args.num_evolvers = 2

    applied = apply_level_flags(args.ghx_level)

    if args.dry_run:
        _pilot._print_dry_run_plan(args)
        _print_ghx_plan(args.ghx_level, applied, args.meta_model)
        return

    _print_ghx_plan(args.ghx_level, applied, args.meta_model)
    await _dispatch(args)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        gc.collect()
        loop.close()
        gc.collect()
