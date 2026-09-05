#!/usr/bin/env python3
# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""GAIA Pilot for AEGIS v1.0 harness evolution.

Fork of ``run_meta.py`` using :class:`~harnessx.aegis.AegisAgent` instead of
:class:`~harnessx.meta_harness.MetaAgent`. Stage 5 auto-revert is disabled;
regression handling falls back to the recipe-level ``_score_and_gate``
(AEGIS + recipe gates would otherwise overlap).

Usage (smoke test, real LLM)::

    python -m recipe.gaia_evolver.run_meta_aegis --smoke --run-tag aegis_smoke1

Usage (full pilot)::

    python -m recipe.gaia_evolver.run_meta_aegis \\
        --num-rounds 4 --max-tasks 20 --num-evolvers 4 \\
        --evolve-cost 10.0 --run-tag aegis_full_v1

Usage (CLI smoke, no LLM cost)::

    python -m recipe.gaia_evolver.run_meta_aegis --dry-run --smoke --run-tag test_dry
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_env_path = Path(_PROJECT_ROOT) / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from harnessx.core.harness import HarnessConfig
from harnessx.core.model_config import ModelConfig
from harnessx.aegis import AegisAgent
from harnessx.tracing.journal import HarnessJournal

from benchmarks.gaia.evaluator import GAIAPipelineEvaluator
from benchmarks.gaia.harness import make_gaia_builder_gpt5
from benchmarks.gaia.task import GAIATask

# Reuse helpers from the MetaAgent driver — do not duplicate.
from recipe.gaia_evolver.run_meta import (
    _build_trajectory_text,
    _compute_tool_counts,
    _load_classified_tasks,
    _make_provider,
    _pick_pivotal_tool,
    _run_task,
    _score_and_gate,
    _write_task_trajectory,
)

logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(asctime)s\033[0m \033[1m%(levelname)-5s\033[0m \033[36m%(name)s\033[0m — \033[1m%(message)s\033[0m",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gaia_aegis_pilot")


def _maybe_use_serper_backend(config, backend: str):
    """Swap the ``WebSearch`` tool for the Serper drop-in (port of the
    identically-named helper in ``run_variant_pool.py``).

    ``chain`` (default) returns the config unchanged — byte-identical official
    behavior, ``harnessx/tools/contrib`` never imported. ``serper`` replaces the
    live registry's ``WebSearch`` entry in place with ``serper_web_search_tool``
    (identical name/description/schema, Serper-first fn, native-chain fallback).
    ``serper_only`` swaps in the fallback-free variant and fails fast without
    ``SERPER_API_KEY``. The swapped tool carries ``__hx_target__``, so round
    configs serialised to YAML round-trip as ``tool_registry.custom`` and every
    evolved config resolves ``WebSearch`` to the same backend.
    """
    if backend == "chain":
        return config
    if backend not in ("serper", "serper_only"):
        raise ValueError(f"--search-backend must be chain|serper|serper_only, got {backend!r}")

    if backend == "serper_only":
        if not os.environ.get("SERPER_API_KEY"):
            raise SystemExit(
                "--search-backend serper_only requires SERPER_API_KEY: the backend "
                "has no native fallback, so a run must not start without the key."
            )
        from harnessx.tools.contrib.serper_search import (
            serper_only_web_search_tool as swap_tool,
        )
    else:
        from harnessx.tools.contrib.serper_search import (
            serper_web_search_tool as swap_tool,
        )

    registry = getattr(config, "tool_registry", None)
    tools = getattr(registry, "_tools", None)
    if isinstance(tools, dict) and "WebSearch" in tools:
        registry.register(swap_tool, replace=True)
        logger.info("search-backend=%s: WebSearch swapped for Serper drop-in", backend)
    else:
        logger.warning(
            "--search-backend %s: no 'WebSearch' tool in the registry to swap; "
            "leaving the tool set unchanged",
            backend,
        )
    return config


#: Capabilities the loop is structurally unable to give itself, keyed by the name
#: ``--extra-tools`` accepts.  Each was proposed by an Evolver and lost, not on
#: merit: the transcript client was ranked first by its Critic at R11 and died
#: with the whole round on IV-3 ("candidate manifest body has zero evidence
#: anchors"); the Wikipedia gap was never proposed at all, because the agent had
#: no way to observe that ``api.php`` answers its User-Agent with 403.
_EXTRA_TOOLS = {
    "wikipedia": "harnessx.tools.contrib.wikipedia_api:wikipedia_api_tool",
    "youtube": "harnessx.tools.contrib.youtube_transcript:youtube_transcript_tool",
}


def _maybe_add_extra_tools(config, spec: str):
    """Register hand-added capability tools into the live registry.

    Same convention as :func:`_maybe_use_serper_backend`: empty (default) returns
    the config untouched and never imports ``harnessx/tools/contrib``, so the
    official behaviour stays byte-identical and every existing arm remains
    comparable.  The tools carry ``__hx_target__``, so a round config serialised
    to YAML round-trips them as ``tool_registry.custom`` entries and every
    evolved descendant keeps them.
    """
    names = [n.strip().lower() for n in (spec or "").split(",") if n.strip()]
    if not names:
        return config
    if "all" in names:
        names = sorted(_EXTRA_TOOLS)
    unknown = [n for n in names if n not in _EXTRA_TOOLS]
    if unknown:
        raise ValueError(
            f"--extra-tools: unknown {unknown}; choose from {sorted(_EXTRA_TOOLS)} or 'all'"
        )
    registry = getattr(config, "tool_registry", None)
    if registry is None:
        logger.warning("--extra-tools %s: config has no tool_registry; nothing added", spec)
        return config
    import importlib

    for name in names:
        module_path, _, attr = _EXTRA_TOOLS[name].partition(":")
        tool_obj = getattr(importlib.import_module(module_path), attr)
        registry.register(tool_obj, replace=True)
        logger.info("extra-tools: registered %s (%s)", tool_obj.name, name)
    return config


#: Seed rules for --runtime-policy: the two death signatures the campaign measured,
#: with steer texts. These are only the SEED — they land as the policy processor's
#: ``rules`` param in every round config, where the Evolver edits them with the
#: mutate_params edit it already has. The thresholds come from the paired swinger
#: analysis (failing runs are the long ones: +4.5 steps over the same task's passing
#: runs) and the restored-evidence landscape (24/33 residual failures fetch and read
#: fine, then wander).
_SEED_POLICY_RULES: list = [
    {
        "name": "stop-search-thrash",
        "when": {"predicate": "search_without_page", "searches": 6},
        "then": {
            "action": "steer",
            "text": (
                "You have run six or more searches without opening a single result. "
                "Searching again will show you the same snippets. Pick the most "
                "promising source already found and fetch/read it NOW, then answer "
                "from page content, not from snippets."
            ),
        },
        "min_step": 4,
        "max_fires": 1,
    },
    {
        "name": "dead-feed-change-approach",
        "when": {"predicate": "consecutive_empty", "count": 3},
        "then": {
            "action": "steer",
            "text": (
                "Your last three tool calls all returned nothing. This channel is "
                "dead — do not retry it. Change approach: different tool, different "
                "source, or reformulate. If no channel can reach the answer, say so "
                "in your FINAL ANSWER instead of guessing."
            ),
        },
        "min_step": 3,
        "max_fires": 1,
    },
]


def _maybe_add_runtime_policy(config, enabled: bool, run_dir=None, seed: bool = False):
    """Append the graph-conditioned runtime policy processor (M26).

    Same convention as the other base-environment switches: off (default) never
    imports the module and leaves the official pipeline byte-identical.

    **The engine ships EMPTY by default.**  The rules are the sentences and the
    sentences must be the loop's, or a gain measured on a self-evolution arm is
    the experimenter's medicine wearing the loop's jersey.  The engine + the
    predicate vocabulary are the LANGUAGE — the same status as the
    GraphProposal edit types, whose precedent is exact: within a day of
    ``insert_tool`` existing, the Evolver proposed three tools candidates on
    its own.  The rule language is documented in the Evolver cheatsheet the
    same way.  A rule that appears in any round config was authored by the
    loop via mutate_params, and the improvement accounting stays clean.

    ``seed=True`` (``--runtime-policy-seed``) installs the three hand-written
    seed rules instead — a DIAGNOSTIC arm for measuring the rules' standalone
    effect (e.g. L0 with no evolution).  Never combine it with a
    self-evolution arm whose gains you intend to attribute to the loop; the
    plan print names the seeding so a mislabelled launch is visible.
    """
    if not enabled:
        return config
    import dataclasses as _dcs

    from harnessx.core.harness import _serialize_processor
    from harnessx.ghx.runtime_policy import RuntimePolicyProcessor

    rules: list = []
    if seed:
        rules = [dict(r) for r in _SEED_POLICY_RULES]
        if run_dir is not None:
            rules.append(
                {
                    "name": "own-death-cone",
                    "when": {
                        "predicate": "own_death_cone",
                        "run_dir": str(run_dir),
                        "min_streak": 3,
                        "overlap": 0.8,
                    },
                    "then": {
                        "action": "steer",
                        "text": (
                            "This run is retracing the exact path on which this task has "
                            "failed in previous rounds. The approach you are following has "
                            "never worked here. Step back and take a materially different "
                            "route: different tool, different source, different method."
                        ),
                    },
                    "min_step": 4,
                    "max_fires": 1,
                }
            )
    proc_dict = _serialize_processor(RuntimePolicyProcessor(rules=rules))
    if not proc_dict:
        logger.warning("--runtime-policy: processor did not serialize; nothing added")
        return config
    if rules:
        logger.info(
            "runtime-policy: DIAGNOSTIC SEED — %d experimenter-authored rule(s) (%s); "
            "gains on this arm are NOT attributable to self-evolution",
            len(rules),
            ", ".join(r["name"] for r in rules),
        )
    else:
        logger.info(
            "runtime-policy: engine installed EMPTY — any rule that appears in a round "
            "config from here on was authored by the loop"
        )
    return _dcs.replace(config, processors=[*config.processors, proc_dict])
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
try:
    import litellm as _litellm

    _litellm.suppress_debug_info = True
    _litellm.set_verbose = False
except ImportError:
    pass

_RECIPE_DIR = Path(__file__).resolve().parent
RUNS_DIR = _RECIPE_DIR / "runs"
_GAIA_SKILLS_DIR = _RECIPE_DIR / "skills"

# ─── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_DATA_PATH = os.environ.get(
    "GAIA_DATA_PATH",
    str(_RECIPE_DIR / "data" / "webthinker_gaia_dev_classified.json"),
)
DEFAULT_MODEL = os.environ.get("GAIA_MODEL", "anthropic/claude-sonnet-4-6")
DEFAULT_META_MODEL = os.environ.get(
    "GAIA_META_MODEL",
    # Fall back to the user-configured Opus model from env, NOT a placeholder.
    # A placeholder like "anthropic/YOUR_PROVIDER/..." silently gets 400 Bad
    # Request on some OpenAI-compatible gateways and makes every meta call
    # return 0 output, which cascades into "0 digests -> actionability=0 ->
    # early-exit" and the whole round no-ops without any clear error.
    "anthropic/" + (os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or "claude-opus-4-7"),
)
DEFAULT_API_BASE = os.environ.get("OPENAI_API_BASE", "")
DEFAULT_PROVIDER_ID = os.environ.get("GAIA_PROVIDER_ID", "azure_openai")

NUM_ROUNDS = 3
MAX_STEPS = 20  # GAIA task agent loop cap; lower = cheaper but more baseline failures
MAX_COST_USD = 15.0
CONCURRENCY = 6
EVOLVE_COST = 100.0  # per-round meta budget cap (Planner 25 / N Evolvers 50 / Critic 30 by split).
# With 4 evolvers: Planner $25, each Evolver $12.5, Critic $30 — enough for 10+ rounds of archive/journal growth.
NUM_EVOLVERS = 2
MAX_TASKS_DEFAULT = 1  # smoke default — minimal cost run (1 task × 2 rounds × 2 evolvers)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _read_latest_commit_shipments(run_dir: Path, round_n: int) -> list[tuple[str, str]]:
    """Return shipped [(candidate_id, bucket), ...] for the given round.

    Reads the most recent "commit" audit entry for ``round_n`` from
    ``audit.jsonl``. Returns an empty list if the round noop'd or the
    audit file is unreadable — in which case the caller should treat it
    as "no ship to track" and skip rollback.
    """
    audit_path = run_dir / "audit.jsonl"
    if not audit_path.exists():
        return []
    latest_payload = None
    try:
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("round") == round_n and entry.get("stage") == "4" and entry.get("kind") == "commit":
                latest_payload = entry.get("payload") or {}
    except OSError:
        return []
    if not latest_payload:
        return []
    shipped_cids = latest_payload.get("shipped_cids") or []
    shipped_by_bucket = latest_payload.get("shipped_by_bucket") or {}
    # shipped_by_bucket is {bucket: cid}; flip to [(cid, bucket), ...] and
    # intersect with shipped_cids as a safety filter.
    result: list[tuple[str, str]] = []
    for bucket, cid in shipped_by_bucket.items():
        if cid in shipped_cids:
            result.append((cid, bucket))
    return result


def _append_rollback_reputation(run_dir: Path, buckets: list[str]) -> None:
    """Append ``False`` to each named bucket's reputation history on disk.

    Records a retroactive "ship was a regression" signal. The next
    ``AegisOrchestrator`` init reads this file via ``Reputation.from_dict``
    which applies a maxlen=5 deque, so older entries truncate naturally.
    """
    rep_path = run_dir / "reputation.json"
    try:
        data = json.loads(rep_path.read_text(encoding="utf-8")) if rep_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    for bucket in buckets:
        history = data.get(bucket)
        if not isinstance(history, list):
            history = []
        history.append(False)
        data[bucket] = history
    try:
        rep_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("failed to write rollback reputation update: %s", exc)


def _append_rollback_audit(
    run_dir: Path,
    *,
    round_idx: int,
    rolled_back_cids: list[str],
    pre_ship_rate: float,
    post_ship_rate: float,
    delta_count: int,
    reason: str,
) -> None:
    """Append a rollback event to audit.jsonl for post-hoc inspection."""
    audit_path = run_dir / "audit.jsonl"
    entry = {
        "round": round_idx,
        "stage": "R",
        "kind": "rollback",
        "payload": {
            "rolled_back_cids": rolled_back_cids,
            "pre_ship_rate": round(pre_ship_rate, 4),
            "post_ship_rate": round(post_ship_rate, 4),
            "delta_count": delta_count,
            "reason": reason,
        },
        "evidence_refs": [],
        "ts": time.time(),
    }
    try:
        with audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("rollback audit append failed: %s", exc)


def _append_rollback_journal(
    run_dir: Path,
    *,
    round_idx: int,
    rolled_back_cids: list[str],
    delta_count: int,
    reason: str,
) -> None:
    """Record the rollback where the Planner will actually read it.

    ``RoundEntry.action`` has declared ``"ship" | "rollback" | "no_op"`` all
    along and nothing ever wrote the middle one: across seven runs and 47
    entries it is ship 32, no_op 15, rollback 0. The rollback went to the
    console and to audit.jsonl, which no agent reads, so the strongest negative
    signal the system produces reached the next round's Planner only as an
    anonymous miss in a reputation bucket — no sign a revert happened, of what,
    or why (P-21).

    Sibling of :func:`_append_rollback_audit`, and equally non-fatal: a journal
    that cannot be appended must not take the campaign down with it.
    """
    from harnessx.aegis.data.journal import Journal, RoundEntry

    try:
        Journal(run_dir / "journal.md").append(
            RoundEntry(
                round=round_idx,
                action="rollback",
                shipped_cid=None,
                # Empty because they were reverted. Leaving them here would say
                # the round shipped, which is the thing being undone.
                shipped_cids=[],
                hypothesis_signatures=[],
                refuted_signatures=[],
                hit_rate=None,
                narrative=(
                    f"ROLLBACK: reverted {', '.join(rolled_back_cids)} after a "
                    f"post-ship regression of {delta_count:+d} tasks. {reason} "
                    f"The round's config was restored to the pre-ship state, so the "
                    f"next round starts from the last validated config, not from this "
                    f"round's."
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001 -- never fatal, same as the audit sibling
        logger.warning("rollback journal append failed: %s", exc)


def _triage_rollback_enabled() -> bool:
    return os.environ.get("HARNESSX_GHX_TRIAGE_ROLLBACK", "").strip().lower() in ("1", "true", "on", "yes")


def _noopstreak_fix_enabled() -> bool:
    return os.environ.get("HARNESSX_GHX_NOOPSTREAK_FIX", "").strip().lower() in ("1", "true", "on", "yes")


# T1.1 (docs/ghx-overnight-0823-research.md, W1·A1/A4): the raw rollback rule
# below fires on total-score-only evidence — ~14% of its trips were noise
# (M25-R2 being the one accident that mattered). A within-envelope statistical
# verdict, or too few counterfactual-eligible (streak >= 4) hard regressions,
# downgrades the FIRST trip to "flag and hold one more round" instead of a
# revert. This threshold roughly mirrors the raw rule's own delta_count <= -3
# magnitude, so the downgrade only fires when the triage genuinely disagrees
# with the raw rule's severity, not on a technicality.
_TRIAGE_MIN_HARD_REGRESSIONS = 3


def _triage_downgrade_note(triage, min_hard_regressions: int = _TRIAGE_MIN_HARD_REGRESSIONS) -> str | None:
    """``None`` → the triage confirms the raw rule (revert as usual). A
    non-empty string → the reason to downgrade the raw rule's trip to a
    flag-and-hold instead of a revert.

    Pulled out as a small pure function (takes a
    ``harnessx.ghx.regression_triage.TriageResult``) so the downgrade
    condition is unit-testable without a live run directory.
    """
    eligible = triage.counterfactual_eligible()
    if triage.stat_verdict != "EXCESS" or len(eligible) < min_hard_regressions:
        return (
            f"stat_verdict={triage.stat_verdict} "
            f"(observed_hard={triage.observed_hard} vs envelope "
            f"{triage.envelope.mean:.1f}±{triage.envelope.sd:.1f}), "
            f"counterfactual_eligible={len(eligible)}/{min_hard_regressions} required"
        )
    return None


def _append_triage_hold_audit(
    run_dir: Path,
    *,
    round_idx: int,
    candidate_cids: list[str],
    delta_rate: float,
    delta_count: int,
    reason: str,
) -> None:
    """Append a triage-downgrade event to audit.jsonl (sibling of
    :func:`_append_rollback_audit` — same raw-JSONL-line discipline, not the
    vendored ``AuditLog``, whose ``kind`` enum is fixed and vendored)."""
    audit_path = run_dir / "audit.jsonl"
    entry = {
        "round": round_idx,
        "stage": "R",
        "kind": "triage_hold",
        "payload": {
            "candidate_cids": candidate_cids,
            "delta_rate": round(delta_rate, 4),
            "delta_count": delta_count,
            "reason": reason,
        },
        "evidence_refs": [],
        "ts": time.time(),
    }
    try:
        with audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("triage-hold audit append failed: %s", exc)


def _append_triage_hold_journal(
    run_dir: Path,
    *,
    round_idx: int,
    candidate_cids: list[str],
    reason: str,
) -> None:
    """Record the triage downgrade where the Planner will actually read it
    (sibling of :func:`_append_rollback_journal` — same P-21 rationale)."""
    from harnessx.aegis.data.journal import Journal, RoundEntry

    try:
        Journal(run_dir / "journal.md").append(
            RoundEntry(
                round=round_idx,
                action="ship",  # the ship stands this round — it was NOT reverted
                shipped_cid=None,
                shipped_cids=list(candidate_cids),
                hypothesis_signatures=[],
                refuted_signatures=[],
                hit_rate=None,
                narrative=(
                    f"TRIAGE HOLD: the raw rollback rule tripped on "
                    f"{', '.join(candidate_cids)}, but the regression triage downgraded "
                    f"it ({reason}). Holding the ship for one more round instead of "
                    f"reverting; a second trip next round reverts unconditionally."
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001 -- never fatal, same as the rollback sibling
        logger.warning("triage-hold journal append failed: %s", exc)


def _restore_externalized_tool_results(jsonl_path: Path, dst: Path) -> None:
    """Copy one session JSONL, restoring journal-externalized tool results inline.

    The journal keeps its JSONL lines small: any tool result over 2 KB
    (``journal.INLINE_LIMIT``) is written to ``<session>/tool_results/*.txt``
    and the line records ``content: ""`` + ``meta.content_ref``. That is a
    TRACE encoding — the live model saw the full payload (verified by token
    accounting: a 25,381-byte externalized WebFetch moved the next call's
    input_tokens 5,786 → 13,581). But everything downstream of this copy reads
    the copy as the ground truth: Stage P's clean_trajectory, the Digester,
    Layer A, and the graph projection all saw ``content: ""`` for every large
    result.

    Measured on M25 batch R10 before this restore: of 204 tool results reading
    as empty, 195 were externalized successes (3.19 MB of fetched content the
    evidence plane never saw) and 9 were genuinely empty. The bed's dominant
    failure motif was built on that reading — ``empty_consumed`` counted 29
    failing tasks as-recorded and 6 restored — and three campaigns of medicine
    were aimed at it. Restoring here, at the single seam where sessions become
    round evidence, corrects every reader at once without touching a vendored
    byte.

    A missing or unreadable ref file leaves the line exactly as recorded — a
    restore must never invent content the journal cannot produce.
    """
    session_dir = jsonl_path.parent
    out_lines: list[str] = []
    restored = 0
    try:
        raw_lines = jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        shutil.copy2(jsonl_path, dst)
        return
    for line in raw_lines:
        if not line.strip():
            continue
        if '"content_ref"' in line:
            try:
                obj = json.loads(line)
                meta = obj.get("meta") or {}
                msg = obj.get("message") or {}
                ref = meta.get("content_ref")
                if ref and not msg.get("content"):
                    ref_path = session_dir / ref
                    if ref_path.is_file():
                        msg["content"] = ref_path.read_text(encoding="utf-8", errors="replace")
                        meta["content_restored"] = True
                        line = json.dumps(obj, ensure_ascii=False)
                        restored += 1
            except (json.JSONDecodeError, OSError):
                pass  # keep the recorded line — never trade the trace for the restore
        out_lines.append(line)
    dst.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    if restored:
        logger.debug("flatten: restored %d externalized tool result(s) into %s", restored, dst.name)


def _flatten_sessions_to_raw(sessions_dir: Path, raw_dir: Path, records: list[dict]) -> None:
    """Copy per-task JSONL files from nested sessions/<sid>/ layout into a
    single flat raw_dir that AEGIS Stage P can glob.

    GAIA writes ``sessions_dir/{session_id}/{run_id}.jsonl`` where session_id
    is ``f"{label}-{task_id}"`` (label is e.g. ``"aegis/R0"``). On disk this
    becomes ``sessions_dir/aegis/R0-<task_id>/<run_id>.jsonl``.

    AEGIS Stage P does ``raw_dir.glob("*.jsonl")`` and extracts the task_id
    from the filename via ``stem.rsplit("_r", 1)[0]``, so we emit
    ``<task_id>_r<i>.jsonl`` per rollout.

    Previously this used substring match on the parent dir name and
    ``break``-ed after the first match, silently dropping additional
    rollouts when k_rollouts > 1. Now we match exactly on the
    ``-<task_id>`` suffix of the parent dir name, copy every .jsonl inside
    (excluding ``*_trace.jsonl``), and number them sequentially.

    Each copy passes through :func:`_restore_externalized_tool_results`, so the
    round evidence carries what the model actually saw rather than the
    journal's inline-size encoding.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not sessions_dir.exists():
        return
    for r in records:
        tid = r.get("task_id")
        if not tid:
            continue
        # Collect all session dirs whose name ends with "-<task_id>".
        # rglob over *.jsonl and dedupe on the parent dir to find them.
        session_dirs: list[Path] = []
        seen_dirs: set[Path] = set()
        for session_path in sessions_dir.rglob("*.jsonl"):
            parent = session_path.parent
            if parent in seen_dirs:
                continue
            if parent.name.endswith(f"-{tid}"):
                session_dirs.append(parent)
                seen_dirs.add(parent)
        # Copy each rollout's trajectory .jsonl(s), numbered.
        rollout_idx = 0
        for sdir in sorted(session_dirs):
            for jsonl in sorted(sdir.glob("*.jsonl")):
                if jsonl.name.endswith("_trace.jsonl"):
                    continue
                dst = raw_dir / f"{tid}_r{rollout_idx}.jsonl"
                if not dst.exists():
                    _restore_externalized_tool_results(jsonl, dst)
                rollout_idx += 1


def _compute_focus_set(
    run_dir: Path,
    round_idx: int,
    max_focus: int,
) -> set[str]:
    """Pick up to ``max_focus`` tasks to run k=2 this round.

    Strategy (in priority order):
      1. Last ship's ``predicted_tasks`` — we want to verify whether the
         Evolver's prediction holds with a second rollout.
      2. Bouncer tasks — any task whose ``passed`` bit flipped at least
         once in recent history. These are exactly the noise-susceptible
         cases where a second sample tells us ALL_PASS vs PARTIAL_PASS vs
         ALL_FAIL. This is where the Digester's ``partial_pass`` template
         actually fires.

    Never includes R0 (no history yet) and tasks that are ALL_PASS across
    the entire history (stable passes — k=2 wastes money).

    Returns empty set if max_focus=0 or no history.
    """
    if max_focus <= 0 or round_idx == 0:
        return set()

    from harnessx.aegis.data import ledger as _ledger

    history = _ledger.read_task_history(run_dir)
    outcomes = _ledger.read_ship_outcomes(run_dir)

    if not history:
        return set()

    # Per-task pass bit history.
    per_task: dict[str, list[bool]] = {}
    for row in history:
        tid = row.get("task_id")
        if tid:
            per_task.setdefault(tid, []).append(bool(row.get("passed", False)))

    focus: list[str] = []

    # Priority 1: last ship's predicted tasks that are still failing.
    for entry in reversed(outcomes):
        preds = entry.get("predicted_tasks", []) or []
        status = entry.get("predicted_tasks_status_latest", {}) or {}
        for tid in preds:
            if tid in focus or len(focus) >= max_focus:
                continue
            # Prefer still_failing (highest info) but accept anything
            # the last ship claimed.
            if status.get(tid) in ("still_failing", "unknown"):
                focus.append(tid)
        if len(focus) >= max_focus:
            break

    # Priority 2: bouncer tasks — passed bit changed at least once.
    bouncer_candidates: list[tuple[str, int]] = []
    for tid, bits in per_task.items():
        if tid in focus:
            continue
        if len(set(bits)) <= 1:
            continue  # always_pass or always_fail
        # Score by recency of last flip (higher = more recent = more interesting)
        last_flip = 0
        for i in range(len(bits) - 1, 0, -1):
            if bits[i] != bits[i - 1]:
                last_flip = i
                break
        bouncer_candidates.append((tid, last_flip))
    bouncer_candidates.sort(key=lambda x: -x[1])
    for tid, _ in bouncer_candidates:
        if len(focus) >= max_focus:
            break
        focus.append(tid)

    return set(focus)


def _save_curves(scope_dir: Path, curves: list[dict]):
    (scope_dir / "curves.json").write_text(json.dumps(curves, indent=2, ensure_ascii=False), encoding="utf-8")


def _print_summary(curves: list[dict], best_idx: int, early_stopped: bool):
    print(f"\n{'=' * 70}")
    print(f"  AEGIS Pilot Summary  {'(EARLY STOPPED)' if early_stopped else ''}")
    print(f"{'=' * 70}")
    print(f"  {'Round':<8} {'Pass':>6} {'Rate':>8} {'Cost':>10} {'Tokens':>12} {'Status':<10}")
    print(f"  {'-' * 8} {'-' * 6} {'-' * 8} {'-' * 10} {'-' * 12} {'-' * 10}")
    for c in curves:
        marker = " <<<BEST" if c["round"] == best_idx else ""
        print(
            f"  R{c['round']:<7d} {c['passed']:>5d}/{c['total_tasks']}"
            f"  {c['pass_pct']:>7s}"
            f"  ${c['cost_usd']:>8.2f}"
            f"  {c['total_tokens']:>11,d}"
            f"  {c['evolve_status']:<10s}{marker}"
        )
    if len(curves) > 1:
        r0 = curves[0]["pass_rate"]
        rb = curves[best_idx]["pass_rate"]
        print(f"\n  >>> R0={r0 * 100:.1f}% → R{best_idx}={rb * 100:.1f}%  Δ={100 * (rb - r0):+.1f}pp")
    print(f"{'=' * 70}\n")


# ─── Dry run ─────────────────────────────────────────────────────────────────


def _print_dry_run_plan(args: argparse.Namespace) -> None:
    print("=" * 70)
    print("  AEGIS Pilot — DRY RUN (no LLM calls)")
    print("=" * 70)
    print(f"  model              : {args.model}")
    print(f"  meta-model         : {args.meta_model}")
    print(f"  provider-id        : {args.provider_id}")
    print(f"  api-base           : {args.api_base or '<env>'}")
    print(f"  data-path          : {args.tasks}")
    print(f"  num-rounds         : {args.num_rounds}")
    print(f"  max-tasks          : {args.max_tasks}")
    print(f"  num-evolvers       : {args.num_evolvers}")
    print(f"  evolve-cost (USD)  : {args.evolve_cost}")
    print(f"  max-cost (USD)     : {args.max_cost}")
    print(f"  max-steps          : {args.max_steps}")
    print(f"  concurrency        : {args.concurrency}")
    print(f"  run-tag            : {args.run_tag or '<auto>'}")
    print(f"  smoke              : {args.smoke}")
    print(f"  clean              : {args.clean}")
    print("=" * 70)
    print("  Would: load tasks → build baseline → run rounds → evolve via AegisAgent.")
    print("  Exiting without calling any provider.")
    print("=" * 70)


# ─── Core pilot ──────────────────────────────────────────────────────────────


async def run_pilot(args: argparse.Namespace) -> None:
    domains = _load_classified_tasks(args.tasks)
    for t_list in domains.values():
        for t in t_list:
            t.max_steps = args.max_steps

    # Flatten to a single global scope.
    all_tasks: list[GAIATask] = []
    for t_list in domains.values():
        all_tasks.extend(t_list)
    if args.seed is not None:
        import random

        random.Random(args.seed).shuffle(all_tasks)
        logger.info("Shuffled tasks with seed=%d", args.seed)
    if args.max_tasks > 0:
        all_tasks = all_tasks[: args.max_tasks]
    if not all_tasks:
        logger.error("No tasks to run (max-tasks=%d, domains loaded=%d).", args.max_tasks, len(domains))
        return

    logger.info(
        "Loaded %d tasks across %d domains; running %d",
        sum(len(v) for v in domains.values()),
        len(domains),
        len(all_tasks),
    )

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_tag = args.run_tag or f"aegis_pilot_{time.strftime('%Y%m%d_%H%M%S')}"
    RUN_DIR = RUNS_DIR / run_tag
    if args.clean and RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Run outputs → %s", RUN_DIR)

    # ── Providers ────────────────────────────────────────────────────────────
    provider = _make_provider(args.model, args.provider_id, api_base=args.api_base, api_key=args.api_key)
    model_config = ModelConfig(main=provider)

    judge_provider = _make_provider(args.meta_model, args.provider_id)
    # NOTE: some Bedrock-backed gateways reject ``thinking.type.enabled``
    # (only ``adaptive`` is supported there). Disable extended thinking
    # unless explicitly opted in via --extended-thinking.
    meta_provider = _make_provider(
        args.meta_model,
        args.provider_id,
        extended_thinking=args.extended_thinking,
        thinking_budget_tokens=32_000 if args.extended_thinking else 10_000,
        max_tokens=40_000 if args.extended_thinking else 16_000,
    )
    meta_model = ModelConfig(main=meta_provider)

    pipeline_eval = GAIAPipelineEvaluator(judge_provider=judge_provider)

    # ── Baseline config ──────────────────────────────────────────────────────
    import dataclasses as _dcs

    from harnessx.core.harness import _serialize_processor
    from harnessx.processors.evaluation.llm_judge import LLMJudgeProcessor

    original_base = make_gaia_builder_gpt5(max_cost_usd=args.max_cost).build()
    _judge_dict = _serialize_processor(LLMJudgeProcessor(judge_model=args.meta_model))
    if _judge_dict:
        original_base = _dcs.replace(original_base, processors=[*original_base.processors, _judge_dict])
    original_base = _maybe_use_serper_backend(original_base, args.search_backend)
    original_base = _maybe_add_extra_tools(original_base, getattr(args, "extra_tools", ""))
    original_base = _maybe_add_runtime_policy(
        original_base,
        bool(getattr(args, "runtime_policy", False)),
        run_dir=RUN_DIR,
        seed=bool(getattr(args, "runtime_policy_seed", False)),
    )

    # ── AegisAgent ────────────────────────────────────────────────────────────
    # ``replay_model`` is the GAIA model (not the meta-model); Stage 4's
    # replay gate runs candidate configs against it to verify they still
    # execute before shipping. Without this, the replay gate silently skips
    # every round. ``auto_revert_enabled`` is wired for forward-compat —
    # Stage 5 runs ACROSS rounds in the pilot driver, not inside
    # ``run_round``, so it is currently a no-op. Regression handling here
    # falls back to ``_score_and_gate``.
    meta_agent = AegisAgent(
        num_evolvers=args.num_evolvers,
        budget_per_round_usd=args.evolve_cost,
        max_ask_more=2,
        max_concurrency=args.concurrency,
        model_config=meta_model,
        replay_model=model_config,
        auto_revert_enabled=True,
    )

    current_config: HarnessConfig = original_base
    best_so_far = None
    next_evolve_status = "baseline"
    curves: list[dict] = []
    noop_streak = 0
    early_stopped = False
    # Tracks the most recent ship so the NEXT round's rollouts can be
    # compared against the pre-ship pass rate. If the ship caused a
    # measurable regression (tighter than _score_and_gate's noise floor),
    # we roll back the current config to the pre-ship snapshot and mark
    # the shipped buckets as regressions in reputation.json.
    # Shape: {"pre_ship_config": HarnessConfig, "pre_ship_rate": float,
    #         "pre_ship_passed": int, "shipped": [(cid, bucket), ...]}
    last_ship_info: dict | None = None
    # Separately tracks the pass rate of the most recent VALIDATED state
    # — i.e. the last round that was NOT rolled back. The plain
    # `last_ship_info.pre_ship_rate` anchors to the immediately-preceding
    # round's rate, which is wrong after a rollback: if R4 shipped and got
    # -6pp (rollback fired, reverting to R3's config), R5's new ship should
    # be compared against R3's 46, NOT against R4's broken 40. Without
    # this correction, a regression in R5 from R3's 46 to 42 shows up as
    # "+2 over R4" and escapes the rollback threshold.
    # Updated only: (a) at baseline R0, (b) after any round whose pass
    # count did NOT trigger a rollback.
    last_validated_passed: int | None = None
    last_validated_rate: float = 0.0
    # Which round produced the current validated baseline — T1.3's paired-gate
    # reading pairs THIS round's outcomes against that round's, not against the
    # (possibly several-rounds-stale) immediately-preceding round.
    last_validated_round_idx: int | None = None
    # T1.1: whether the triage already downgraded the most recent rollback trip
    # once. A downgrade holds exactly one round — a second consecutive trip
    # obeys the raw rule unconditionally (see the rollback block below).
    triage_hold_used = False

    # v0.9.2 resume support: --start-round N skips rounds 0..N-1 and seeds
    # current_config from R(N-1)/applied/merged.yaml if present (or
    # R(N-1)/config.yaml for baseline rounds). curves.json is restored
    # from disk so the summary printing shows the complete history.
    if args.start_round > 0:
        resume_json = RUN_DIR / "curves.json"
        if resume_json.exists():
            try:
                curves = json.loads(resume_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                curves = []
        # Seed current_config from previous round's merged (if shipped) else config.yaml.
        prev_round = args.start_round - 1
        merged_path = RUN_DIR / f"R{prev_round}" / "applied" / "merged.yaml"
        baseline_path = RUN_DIR / f"R{prev_round}" / "config.yaml"
        seed_path = merged_path if merged_path.exists() else baseline_path
        if not seed_path.exists():
            raise FileNotFoundError(
                f"--start-round={args.start_round} requires R{prev_round} state; "
                f"neither {merged_path} nor {baseline_path} exists."
            )
        logger.info(
            "resume: loading current_config from %s (curves has %d rounds)",
            seed_path,
            len(curves),
        )
        current_config = HarnessConfig.from_yaml_file(str(seed_path))
        next_evolve_status = "ok"
        if curves:
            last = curves[-1]
            last_validated_passed = int(last.get("passed", 0))
            last_validated_rate = float(last.get("pass_rate", 0.0))
            last_validated_round_idx = last.get("round")

    # Scoped noop batches (--noop-audit): per-task lite records of the last
    # completed batch, the carry-forward source when an unchanged config skips
    # its full re-measurement. Chains across consecutive noop rounds.
    prev_lite: dict[str, dict] = {}
    for round_idx in range(args.num_rounds):
        if round_idx < args.start_round:
            continue
        is_last = round_idx == args.num_rounds - 1

        round_dir = RUN_DIR / f"R{round_idx}"
        round_dir.mkdir(parents=True, exist_ok=True)
        traj_dir = round_dir / "trajectories"
        traj_dir.mkdir(parents=True, exist_ok=True)
        sessions_dir = round_dir / "sessions"

        round_journal = HarnessJournal(base_dir=str(sessions_dir), export_jsonl=True)
        round_config = current_config.copy(tracer=round_journal)

        round_config_path = round_dir / "config.yaml"
        round_config.to_yaml_file(round_config_path)

        config_hash = hashlib.sha256(round_config_path.read_bytes()).hexdigest()[:16]

        logger.info("\n" + "=" * 70)
        logger.info(
            "ROUND %d/%d  config=%s  evolve_status=%s",
            round_idx,
            args.num_rounds - 1,
            config_hash,
            next_evolve_status,
        )
        logger.info("=" * 70)

        # ── Compute focus set (k=2 subset) ───────────────────────────────────
        focus_set = _compute_focus_set(
            run_dir=RUN_DIR,
            round_idx=round_idx,
            max_focus=args.k_focus_max,
        )
        if focus_set:
            logger.info(
                "[R%d] k=2 focus set: %d tasks (bouncer + last-ship predicted)",
                round_idx,
                len(focus_set),
            )

        # ── Scoped noop batches (--noop-audit N) ─────────────────────────────
        # An unchanged config re-runs the full bed only to re-measure noise the
        # campaign has already priced (M25: four noop rounds x ~$43 = ~a third
        # of batch spend, envelope known to +/-5 tasks the whole time). With
        # N > 0, a noop round runs an AUDIT subset — every task that flipped in
        # the last three recorded rounds (the volatile family, exactly where a
        # same-config surprise would show), deterministically filled to N —
        # and carries the remaining tasks' scores forward, at $0, marked
        # `carried` in every ledger. A ship round always runs the full bed.
        audit_n = int(getattr(args, "noop_audit", 0) or 0)
        run_tasks = all_tasks
        carried_lite: dict[str, dict] = {}
        if audit_n > 0 and next_evolve_status == "noop":
            carry_src = dict(prev_lite)
            if not carry_src:
                try:
                    from harnessx.aegis.data import ledger as _ledger_ro

                    for row in _ledger_ro.read_task_history(RUN_DIR):
                        tid_h = str(row.get("task_id") or "")
                        if tid_h:
                            carry_src[tid_h] = {
                                "task_id": tid_h,
                                "passed": bool(row.get("passed")),
                                "passed_flags": list(row.get("passed_flags") or [bool(row.get("passed"))]),
                                "level": str(row.get("level") or "").lstrip("L") or None,
                                "steps": int(row.get("steps") or 0),
                                "exit_reason": str(row.get("exit") or ""),
                                "final_output": "",
                                "tools_used": list(row.get("tools_used") or []),
                            }
                except Exception as _exc:  # noqa: BLE001
                    logger.warning("noop-audit: carry source unavailable (%s) — full batch", _exc)
                    carry_src = {}
            if carry_src:
                flippy: set[str] = set()
                try:
                    from harnessx.aegis.data import ledger as _ledger_ro

                    by_task: dict[str, list] = {}
                    for row in _ledger_ro.read_task_history(RUN_DIR):
                        by_task.setdefault(str(row.get("task_id")), []).append(
                            (int(row.get("round", -1)), bool(row.get("passed")))
                        )
                    for tid_h, hist_rows in by_task.items():
                        recent = [v for _, v in sorted(hist_rows)[-3:]]
                        if len(set(recent)) > 1:
                            flippy.add(tid_h)
                except Exception:  # noqa: BLE001 — no history → deterministic fill only
                    pass
                audit: set[str] = set()
                for t in all_tasks:  # volatile family first, in bed order
                    if t.task_id in flippy and t.task_id in carry_src:
                        audit.add(t.task_id)
                fill = sorted(
                    (t.task_id for t in all_tasks if t.task_id not in audit),
                    key=lambda tid: hashlib.sha256(f"{round_idx}:{tid}".encode()).hexdigest(),
                )
                for tid_f in fill:
                    if len(audit) >= audit_n:
                        break
                    audit.add(tid_f)
                run_tasks = [t for t in all_tasks if t.task_id in audit or t.task_id not in carry_src]
                run_ids = {rt.task_id for rt in run_tasks}
                carried_lite = {
                    t.task_id: carry_src[t.task_id] for t in all_tasks if t.task_id not in run_ids
                }
                logger.info(
                    "[R%d] NOOP round scoped: running %d/%d (flip-family %d, fill %d); "
                    "carrying %d task score(s) forward at $0",
                    round_idx,
                    len(run_tasks),
                    len(all_tasks),
                    len(audit & flippy),
                    len(audit - flippy),
                    len(carried_lite),
                )

        # ── Run all tasks in parallel ────────────────────────────────────────
        sem = asyncio.Semaphore(max(1, args.concurrency))

        async def _run_one(task: GAIATask, k: int = 1) -> list[dict]:
            """Run a task k times; return k records (list always, even for k=1)."""
            from dataclasses import replace as _dc_replace

            results: list[dict] = []
            for rollout_idx in range(k):
                async with sem:
                    task_i = _dc_replace(task, max_cost_usd=args.max_cost, max_steps=args.max_steps)
                    harness = model_config.agentic(round_config)
                    # Distinct session_id per rollout — without /r{i} suffix
                    # both k=2 rollouts share session_id="aegis/R{N}-{tid}",
                    # the second call's HarnessJournal.wake() finds the first
                    # rollout's saved state on disk, harness.run() takes the
                    # resume branch (harness.py:1199), and:
                    #   * state.max_steps = state.step + task.max_steps
                    #     (so _r1 gets up to 2× the step budget)
                    #   * the prior conversation messages stay in state
                    #     (so _r1 sees _r0's attempts + tool results)
                    # This destroys the variance-reduction intent — _r1 isn't
                    # an independent sample, it's a continuation. For k=1 we
                    # keep the legacy label so existing logs/parsers don't
                    # change.
                    label = f"aegis/R{round_idx}" if k == 1 else f"aegis/R{round_idx}/r{rollout_idx}"
                    record = await _run_task(
                        harness,
                        task_i,
                        label,
                        pipeline_eval=pipeline_eval,
                        harness_config=round_config,
                    )
                raw = record.get("_result")
                if raw is not None:
                    record["pivotal_tool"] = _pick_pivotal_tool(raw)
                    cc, ec = _compute_tool_counts(raw)
                    record["tool_call_counts"] = cc
                    record["tool_error_counts"] = ec
                    record["tools_used"] = sorted(cc.keys())
                    traj_text = _build_trajectory_text(task, raw, harness_config=round_config)
                    # For k>1: write per-rollout trajectory md with _r{i} suffix
                    # so both rollouts' evidence survives for the Digester.
                    if k > 1:
                        tid = getattr(task, "task_id", "unknown")
                        from recipe.gaia_evolver.run_meta import _render_trajectory_frontmatter

                        fm = _render_trajectory_frontmatter(record)
                        (traj_dir / f"{tid}_r{rollout_idx}.md").write_text(
                            f"{fm}\n\n{traj_text.lstrip()}",
                            encoding="utf-8",
                        )
                    else:
                        _write_task_trajectory(traj_dir, task, traj_text, record=record)
                results.append(record)
            return results

        def _k_for(t: GAIATask) -> int:
            focus_k = 2 if t.task_id in focus_set else 1
            return max(args.k_all, focus_k)

        per_task_results = await asyncio.gather(*(_run_one(t, k=_k_for(t)) for t in run_tasks))
        # Flatten for legacy per-record consumers (stats, _flatten_sessions_to_raw).
        # Carried tasks are deliberately NOT in `records`: they ran nothing, so
        # they contribute no cost/tokens/steps and nothing to flatten.
        records = [r for task_rolls in per_task_results for r in task_rolls]
        if carried_lite:
            per_task_results = list(per_task_results) + [
                [dict(lite, carried=True, cost_usd=0.0, total_tokens=0, steps=0)]
                for lite in carried_lite.values()
            ]
        gc.collect()

        # Per-task pass flags (1-of-k, 2-of-k, etc). Feeds Stage P's
        # classify_pattern so PARTIAL_PASS actually fires for bouncer tasks.
        pass_flags_by_task_rd: dict[str, list[bool]] = {}
        for task_rolls in per_task_results:
            for r in task_rolls:
                tid = r.get("task_id")
                if tid:
                    pass_flags_by_task_rd.setdefault(tid, []).append(bool(r.get("passed", False)))

        # ── Stats (per-task; k=2 rollouts aggregated via any-pass) ────────────
        # When k=1 for all tasks, passed_any == passed_all == legacy behavior.
        # When any task ran k=2, we track both "any rollout passed" (optimistic)
        # and "all rollouts passed" (strict) so noise shows up as a gap.
        n_tasks = len(per_task_results)
        passed_any = sum(1 for task_rolls in per_task_results if any(r.get("passed") for r in task_rolls))
        passed_all = sum(
            1 for task_rolls in per_task_results if task_rolls and all(r.get("passed") for r in task_rolls)
        )
        # Legacy `passed` = passed_any (matches pre-k=2 behavior when k=1).
        passed = passed_any
        round_cost_usd = sum((r.get("cost_usd") or 0) for r in records)
        round_pass_rate = round(passed / n_tasks, 4) if n_tasks else 0.0
        round_pass_rate_all = round(passed_all / n_tasks, 4) if n_tasks else 0.0
        total_tokens = sum(int(r.get("total_tokens") or 0) for r in records)
        total_steps = sum(int(r.get("steps") or 0) for r in records)

        level_stats: dict[str, dict] = {}
        # Per-level counts use the FIRST rollout's record for level attribution
        # (all rollouts of a task share the same level).
        per_task_first = [rolls[0] for rolls in per_task_results if rolls]
        for lvl in sorted({r.get("level") for r in per_task_first if r.get("level")}):
            lrecs_first = [r for r in per_task_first if r.get("level") == lvl]
            lp = sum(
                1
                for rolls in per_task_results
                if rolls and rolls[0].get("level") == lvl and any(r.get("passed") for r in rolls)
            )
            level_stats[f"L{lvl}"] = {
                "total": len(lrecs_first),
                "passed": lp,
                "pass_rate": round(lp / len(lrecs_first), 4) if lrecs_first else 0.0,
            }

        k_focus_used = sum(1 for rolls in per_task_results if len(rolls) > 1)

        curve_point = {
            "round": round_idx,
            "config_hash": config_hash,
            "evolve_status": next_evolve_status,
            "total_tasks": n_tasks,
            "passed": passed,
            "pass_rate": round_pass_rate,
            "pass_pct": f"{round_pass_rate * 100:.1f}%",
            "pass_rate_all": round_pass_rate_all,  # strict (all k pass)
            "k_focus_tasks": k_focus_used,  # how many tasks ran k=2 this round
            **(
                {"fresh_tasks": n_tasks - len(carried_lite), "carried_tasks": len(carried_lite)}
                if carried_lite
                else {}
            ),
            "cost_usd": round(round_cost_usd, 4),
            "total_tokens": total_tokens,
            "total_steps": total_steps,
            "level_stats": level_stats,
        }
        curves.append(curve_point)
        _save_curves(RUN_DIR, curves)

        # Append per-task outcomes to data/task_history.jsonl — the MAS's
        # cross-round per-task pass bitmap. One row per task (NOT per rollout),
        # aggregating k rollouts into passed_flags. `passed` = any-k-pass for
        # backward compat; `passed_flags` is the full bit list and `k` is len.
        try:
            from harnessx.aegis.data import ledger as _ledger

            task_rows: list[dict] = []
            for task_rolls in per_task_results:
                if not task_rolls:
                    continue
                first = task_rolls[0]
                tid = first.get("task_id")
                if not tid:
                    continue
                flags = [bool(r.get("passed", False)) for r in task_rolls]
                # For k=2, aggregate exit/steps by picking the passing rollout's
                # trajectory info (it's the "successful shape"), else the first.
                primary = next((r for r in task_rolls if r.get("passed")), first)
                task_rows.append(
                    {
                        "round": round_idx,
                        "task_id": tid,
                        "level": f"L{first.get('level')}" if first.get("level") else None,
                        "passed": any(flags),  # any-k pass (optimistic) — legacy
                        "passed_flags": flags,  # full bit list for k>1
                        "k": len(flags),
                        "exit": str(primary.get("exit_reason", "") or ""),
                        "steps": int(primary.get("steps") or 0),
                        "cost_usd": sum(float(r.get("cost_usd") or 0.0) for r in task_rolls),
                        "final_output_len": len(str(primary.get("final_output", "") or "")),
                        "tools_used": list(primary.get("tools_used", []) or []),
                        **({"carried": True} if first.get("carried") else {}),
                    }
                )
            _ledger.append_task_history(RUN_DIR, task_rows)
            # The vendored serializer rebuilds each row from a fixed field set,
            # which drops the `carried` flag attached above. Re-attach it on the
            # written rows (schema stays vendored-authored; vendored bytes stay
            # untouched) — without it, carried rows are indistinguishable from
            # fresh measurements on disk, the exact confusion --noop-audit exists
            # to prevent.
            _carried_ids = {r["task_id"] for r in task_rows if r.get("carried")}
            if _carried_ids:
                _hist = _ledger.data_dir(RUN_DIR) / "task_history.jsonl"
                _lines = _hist.read_text(encoding="utf-8").splitlines()
                for _i, _ln in enumerate(_lines):
                    try:
                        _row = json.loads(_ln)
                    except Exception:
                        continue
                    if (
                        _row.get("round") == round_idx
                        and _row.get("task_id") in _carried_ids
                        and not _row.get("carried")
                    ):
                        _row["carried"] = True
                        _lines[_i] = json.dumps(_row, ensure_ascii=False)
                _tmp = _hist.with_suffix(".jsonl.tmp")
                _tmp.write_text("\n".join(_lines) + "\n", encoding="utf-8")
                _tmp.replace(_hist)
        except Exception as _exc:
            logger.warning("task_history append failed (non-fatal): %s", _exc)

        # Carry source for a possible scoped round next iteration: every task's
        # lite record, fresh and carried alike (a task can stay carried across
        # consecutive noop rounds without losing its last real measurement).
        prev_lite = {}
        for task_rolls in per_task_results:
            if not task_rolls:
                continue
            first = task_rolls[0]
            tid_p = first.get("task_id")
            if not tid_p:
                continue
            primary = next((r for r in task_rolls if r.get("passed")), first)
            prev_lite[tid_p] = {
                "task_id": tid_p,
                "passed": any(bool(r.get("passed")) for r in task_rolls),
                "passed_flags": [bool(r.get("passed", False)) for r in task_rolls],
                "level": first.get("level"),
                "steps": int(primary.get("steps") or 0),
                "exit_reason": str(primary.get("exit_reason", "") or ""),
                "final_output": "",
                "tools_used": list(primary.get("tools_used", []) or []),
            }

        logger.info(
            "[R%d] pass=%d/%d (%.1f%%)  cost=$%.2f  tokens=%d",
            round_idx,
            passed,
            n_tasks,
            round_pass_rate * 100,
            round_cost_usd,
            total_tokens,
        )
        for k, v in level_stats.items():
            logger.info("  %s: %d/%d (%.1f%%)", k, v["passed"], v["total"], v["pass_rate"] * 100)

        # ── Gating (recipe-level, since AEGIS Stage 5 is disabled in pilot) ──
        # _score_and_gate still updates best_so_far (used in the final
        # summary) but we no longer act on its reverted_cfg — the new
        # ship-aware rollback below is strictly more targeted. A "bad
        # ship detected via best vs current" check without ship context
        # reverts on pure variance whenever best is high and a noop
        # round happens to land low.
        _gate_decision, _gate_reason, best_so_far, _reverted_cfg = _score_and_gate(
            round_pass_rate=round_pass_rate,
            round_cost=round_cost_usd,
            round_idx=round_idx,
            round_config=current_config,
            round_passed=passed,
            best=best_so_far,
            tolerance=0.08,
            cost_weight=0.0,
            pass_count_noise_threshold=5,
        )

        # ── Ship-aware rollback ─────────────────────────────────────────────
        # Compares THIS round's pass count to ``last_validated_passed``, not
        # to the immediately-preceding round's count. Rationale: after a
        # rollback, the prior round's pass count is invalid (produced by
        # broken config that was reverted). Anchoring the rollback threshold
        # there lets a follow-on ship regress from the true baseline without
        # triggering. Observed in aegis_64_v4: R4 shipped → 40 (rollback),
        # R5 shipped → 42 appeared as +2 vs R4's 40 but was -4 vs R3's true
        # 46; the new ship hid under the rollback's skirts.
        #
        # Thresholds (5pp AND 3 tasks) are tighter than _score_and_gate's
        # 8pp/5-task noise floor. R0's observed variance was ±4 tasks, so
        # 5pp/3-task reliably catches zero-hit ships without firing on
        # single-task noise.
        rollback_fired = False
        held_this_round = False
        if last_ship_info is not None and last_validated_passed is not None:
            pre_passed = last_validated_passed
            pre_rate = last_validated_rate
            delta_rate = round_pass_rate - pre_rate
            delta_count = passed - pre_passed

            # T1.3 (paired-read evidence at the gate, HARNESSX_GHX_PAIRED_GATE):
            # report-only, no veto power — writes a third, independent reading
            # (the ship's OWN predicted task set, paired between the previous
            # validated round and this one) alongside the raw delta and the
            # T1.1 triage below, so the decision log shows all three at once.
            from harnessx.ghx.paired_gate import paired_gate_enabled

            if paired_gate_enabled() and last_validated_round_idx is not None:
                try:
                    from harnessx.ghx.paired_gate import (
                        append_paired_gate_audit,
                        compute_predicted_task_paired_read,
                        predicted_tasks_for_round,
                        write_paired_gate_evidence,
                    )

                    ship_ids = {cid for cid, _ in last_ship_info["shipped"]}
                    predicted = predicted_tasks_for_round(RUN_DIR, round_idx, ship_ids=ship_ids)
                    paired = compute_predicted_task_paired_read(
                        RUN_DIR,
                        round_idx=round_idx,
                        pre_ship_round=last_validated_round_idx,
                        predicted_tasks=predicted,
                    )
                    if paired is not None:
                        write_paired_gate_evidence(RUN_DIR, round_idx, paired)
                        append_paired_gate_audit(RUN_DIR, round_idx, paired)
                        logger.info("[R%d] paired-gate read: %s", round_idx, paired.verdict())
                except Exception as exc:
                    logger.warning("[R%d] paired-gate evidence failed (non-fatal): %s", round_idx, exc)

            if delta_rate <= -0.05 and delta_count <= -3:
                rolled_back = last_ship_info["shipped"]
                rolled_back_cids = [cid for cid, _ in rolled_back]
                rolled_back_buckets = [bucket for _, bucket in rolled_back]

                # T1.1 (triage-aware rollback, HARNESSX_GHX_TRIAGE_ROLLBACK):
                # the raw rule above is total-score-only. Consult the same
                # transition's three-ruler triage before trusting it; a
                # within-envelope statistical verdict, or too few
                # counterfactual-eligible hard regressions, downgrades a FIRST
                # trip to "flag and hold". A second consecutive trip
                # (triage_hold_used already True) obeys the raw rule
                # unconditionally.
                should_revert = True
                triage_note = ""
                if _triage_rollback_enabled() and not triage_hold_used:
                    try:
                        from harnessx.ghx.regression_triage import compute_triage

                        triage = compute_triage(RUN_DIR, round_idx, round_idx)
                        note = _triage_downgrade_note(triage)
                        if note is not None:
                            should_revert = False
                            triage_note = note
                    except Exception as exc:
                        logger.warning(
                            "[R%d] regression triage unavailable (%s) — "
                            "falling back to the vendored rollback rule",
                            round_idx,
                            exc,
                        )

                if should_revert:
                    logger.warning(
                        "[R%d] ROLLBACK — post-ship regression Δ=%+d tasks "
                        "(%+.1fpp vs last_validated=%d); reverting ships: %s",
                        round_idx,
                        delta_count,
                        delta_rate * 100,
                        pre_passed,
                        rolled_back_cids,
                    )
                    current_config = last_ship_info["pre_ship_config"]
                    _append_rollback_reputation(RUN_DIR, rolled_back_buckets)
                    _rollback_reason = (
                        f"Δrate={delta_rate:+.3f} ≤ -0.05 AND "
                        f"Δcount={delta_count} ≤ -3 "
                        f"(vs last_validated R at {pre_passed} passed)"
                        + (f"; triage confirmed: {triage_note}" if triage_note else "")
                        + (" [second trip after a triage hold]" if triage_hold_used else "")
                    )
                    _append_rollback_audit(
                        RUN_DIR,
                        round_idx=round_idx,
                        rolled_back_cids=rolled_back_cids,
                        pre_ship_rate=pre_rate,
                        post_ship_rate=round_pass_rate,
                        delta_count=delta_count,
                        reason=_rollback_reason,
                    )
                    # audit.jsonl is for post-hoc inspection and no agent reads it.
                    # The Planner reads the journal (P-21).
                    _append_rollback_journal(
                        RUN_DIR,
                        round_idx=round_idx,
                        rolled_back_cids=rolled_back_cids,
                        delta_count=delta_count,
                        reason=_rollback_reason,
                    )
                    rollback_fired = True
                else:
                    logger.warning(
                        "[R%d] rollback DOWNGRADED by triage — flagging and holding "
                        "one more round instead of reverting (%s)",
                        round_idx,
                        triage_note,
                    )
                    _append_triage_hold_audit(
                        RUN_DIR,
                        round_idx=round_idx,
                        candidate_cids=rolled_back_cids,
                        delta_rate=delta_rate,
                        delta_count=delta_count,
                        reason=triage_note,
                    )
                    _append_triage_hold_journal(
                        RUN_DIR,
                        round_idx=round_idx,
                        candidate_cids=rolled_back_cids,
                        reason=triage_note,
                    )
                    triage_hold_used = True
                    held_this_round = True
                    # Keep last_ship_info alive (do NOT clear it below): the
                    # next round is re-checked against this SAME pre-ship
                    # baseline, and a second trip reverts unconditionally.

            # Ship has been evaluated (kept or rolled back). Clear tracker —
            # unless a triage downgrade is holding it for one more round.
            if not held_this_round:
                last_ship_info = None
                triage_hold_used = False

        # Update the validated baseline only when this round was NOT rolled
        # back and is not being held for a second look. A rollback (or a
        # hold) means this round's pass count came from broken/unconfirmed
        # config; the NEXT ship should be compared against the prior
        # validated baseline, not this one.
        if not rollback_fired and not held_this_round:
            last_validated_passed = passed
            last_validated_rate = round_pass_rate
            last_validated_round_idx = round_idx

        if is_last:
            continue

        # ── Evolve via AegisAgent ─────────────────────────────────────────────
        next_round_dir = RUN_DIR / f"R{round_idx + 1}"
        next_round_dir.mkdir(parents=True, exist_ok=True)

        # Flatten sessions → raw_dir for Stage P glob.
        raw_dir = round_dir / "raw"
        _flatten_sessions_to_raw(sessions_dir, raw_dir, records)

        # Use the k-aware map built above so k=2 bouncer tasks produce
        # [True, False]-style lists that classify_pattern turns into
        # PARTIAL_PASS (the Digester's highest-signal template).
        pass_flags_by_task = pass_flags_by_task_rd

        logger.info("[R%d] evolve (planning R%d)", round_idx, round_idx + 1)
        try:
            new_yaml = await meta_agent.evolve(
                current_config=round_config_path,
                trajectories_dir=raw_dir,
                output_dir=next_round_dir,  # orchestrator ignores this; path
                # is derived from run_dir + round_n
                pass_flags_by_task=pass_flags_by_task,
                round_n=round_idx + 1,
                raw_sessions_dir=raw_dir,
            )

            new_yaml_path = Path(new_yaml)
            # T1.4 (HARNESSX_GHX_NOOPSTREAK_FIX): round_config_path is the
            # snapshot written at the TOP of this round, before the rollback
            # check above could mutate current_config. When a rollback fires
            # mid-round, round_config_path still holds the reverted (bad)
            # ship's bytes, so a real evolve change that merely undoes that
            # ship reads as "identical to round_config_path" — a false noop.
            # L0's 16-round run early-stopped at R13 on exactly this (evidence:
            # docs/ghx-overnight-0823-research.md W1·A4). Comparing against
            # current_config re-serialized the same way (same tracer, same
            # to_yaml()) reflects any rollback that just happened this round.
            if _noopstreak_fix_enabled():
                # Written through the SAME to_yaml_file() round_config_path used
                # (not a bare .encode()) so the two sides see identical newline
                # handling — text-mode writes translate line endings on Windows,
                # and a from-memory LF string vs an on-disk CRLF file would
                # never compare equal regardless of actual content.
                import tempfile

                with tempfile.TemporaryDirectory() as _td:
                    _baseline_path = Path(_td) / "post_rollback_config.yaml"
                    current_config.copy(tracer=round_journal).to_yaml_file(_baseline_path)
                    baseline_bytes = _baseline_path.read_bytes()
            else:
                baseline_bytes = round_config_path.read_bytes()
            if baseline_bytes == new_yaml_path.read_bytes():
                next_evolve_status = "noop"
                noop_streak += 1
            else:
                next_evolve_status = "ok"
                noop_streak = 0
                # Snapshot the pre-ship state BEFORE overwriting current_config,
                # so a regression in the NEXT round's rollouts can be rolled
                # back to exactly this config. Also read the audit log to
                # identify which candidates just shipped (and their buckets)
                # so the rollback can update reputation correctly.
                pre_ship_config = current_config
                pre_ship_rate = round_pass_rate
                pre_ship_passed = passed
                shipped_this_round = _read_latest_commit_shipments(
                    RUN_DIR,
                    round_n=round_idx + 1,
                )
                candidate_cfg = HarnessConfig.from_yaml_file(new_yaml_path).canonicalize()
                current_config = candidate_cfg
                if shipped_this_round:
                    last_ship_info = {
                        "pre_ship_config": pre_ship_config,
                        "pre_ship_rate": pre_ship_rate,
                        "pre_ship_passed": pre_ship_passed,
                        "shipped": shipped_this_round,
                    }

            logger.info(
                "[R%d] evolved config → %s  status=%s  noop_streak=%d",
                round_idx,
                new_yaml,
                next_evolve_status,
                noop_streak,
            )

            if noop_streak >= 2 and not args.no_early_stop:
                logger.info("EARLY STOP: %d consecutive unchanged configs", noop_streak)
                early_stopped = True
                break
            if noop_streak >= 2:
                # Fixed-horizon mode: note the streak that would have stopped a
                # default run, and keep going — an arm cut at a different round
                # than its siblings breaks every cross-arm reading downstream.
                logger.info(
                    "noop_streak=%d would have early-stopped; --no-early-stop keeps the horizon",
                    noop_streak,
                )

        except Exception as exc:
            next_evolve_status = "crashed"
            noop_streak = 0
            logger.exception("[R%d] evolve crashed: %s", round_idx, exc)
            # Keep current_config unchanged, continue to next round.

    # ── Final summary ────────────────────────────────────────────────────────
    _save_curves(RUN_DIR, curves)
    best_idx = max(range(len(curves)), key=lambda i: (curves[i]["passed"], -curves[i]["cost_usd"])) if curves else 0
    _print_summary(curves, best_idx, early_stopped)
    logger.info("All results → %s", RUN_DIR)


# ─── Main ────────────────────────────────────────────────────────────────────


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GAIA AEGIS Pilot: single-scope evolution using AegisAgent.")
    p.add_argument("--tasks", default=DEFAULT_DATA_PATH, help="Path to GAIA classified JSON.")
    p.add_argument("--num-rounds", type=int, default=NUM_ROUNDS)
    p.add_argument("--max-tasks", type=int, default=MAX_TASKS_DEFAULT, help="0 = all.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--meta-model", default=DEFAULT_META_MODEL)
    p.add_argument("--api-base", default=DEFAULT_API_BASE)
    p.add_argument("--api-key", default=None)
    p.add_argument("--provider-id", default=DEFAULT_PROVIDER_ID)
    p.add_argument("--max-cost", type=float, default=MAX_COST_USD)
    p.add_argument("--max-steps", type=int, default=MAX_STEPS)
    p.add_argument("--concurrency", type=int, default=CONCURRENCY)
    p.add_argument("--evolve-cost", type=float, default=EVOLVE_COST)
    p.add_argument("--num-evolvers", type=int, default=NUM_EVOLVERS)
    p.add_argument("--seed", type=int, default=None, help="Shuffle tasks with this seed before slicing (random pick).")
    p.add_argument(
        "--extended-thinking",
        action="store_true",
        help="Enable Anthropic extended thinking for meta model. Off by default — some gateways reject 'thinking.type.enabled'.",
    )
    p.add_argument("--run-tag", default=None)
    p.add_argument(
        "--search-backend",
        choices=("chain", "serper", "serper_only"),
        default="chain",
        help=(
            "chain (default) keeps the built-in WebSearch fallback chain "
            "byte-identical; serper swaps in the Serper-first drop-in "
            "(serper.dev, SERPER_API_KEY); serper_only is Serper with no "
            "native fallback."
        ),
    )
    p.add_argument(
        "--extra-tools",
        default="",
        help=(
            "Comma-separated capability tools to add to the base environment: "
            "wikipedia (MediaWiki API — the built-in WebFetch is 403'd by Wikimedia's "
            "robot policy), youtube (video captions), or 'all'. Empty (default) leaves "
            "the official tool set byte-identical."
        ),
    )
    p.add_argument(
        "--runtime-policy",
        action="store_true",
        help=(
            "Add the graph-conditioned runtime policy processor: declarative rules "
            "evaluated against the live unfolded graph before each model call, "
            "steering runs that enter a measured death signature (search-thrash, "
            "dead feed). Rules are the processor's params, so the Evolver edits "
            "policy via mutate_params. Off (default) = official pipeline untouched."
        ),
    )
    p.add_argument(
        "--runtime-policy-seed",
        action="store_true",
        help=(
            "DIAGNOSTIC: install the three experimenter-authored seed rules instead "
            "of an empty engine. For measuring the rules' standalone effect (e.g. an "
            "L0 arm); gains on a seeded arm are NOT attributable to self-evolution."
        ),
    )
    p.add_argument("--clean", action="store_true")
    p.add_argument(
        "--start-round",
        type=int,
        default=0,
        help=(
            "Resume from round N. Skips rounds 0..N-1. Requires "
            "R<N-1>/applied/merged.yaml (or R<N-1>/config.yaml) to "
            "exist in the run_tag dir, plus curves.json to carry history."
        ),
    )
    p.add_argument(
        "--k-focus-max",
        type=int,
        default=0,
        help=(
            "Adaptive k>1: up to N tasks per round (other than R0) will run "
            "TWICE instead of once. Focus set is bouncer tasks + last-ship "
            "predicted tasks. 0 disables (k=1 for all, default)."
        ),
    )
    p.add_argument(
        "--k-all",
        type=int,
        default=1,
        help=(
            "Floor on per-task rollouts: every task runs at least this many "
            "times every round (R0 included). Combines with --k-focus-max "
            "by taking the max. 2 = run all tasks twice for variance."
        ),
    )
    p.add_argument(
        "--noop-audit",
        type=int,
        default=0,
        help=(
            "Scoped noop batches: when the evolved config is byte-identical to the "
            "previous round's (evolve_status=noop), run only an audit subset of N "
            "tasks (all tasks that flipped in the last 3 rounds + deterministic "
            "fill) and carry the other tasks' scores forward at $0, marked "
            "'carried' in curves.json and task_history. Ship rounds always run "
            "the full bed. 0 (default) = official behavior, full re-run."
        ),
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke preset: num-rounds=2, max-tasks=2, num-evolvers=2.",
    )
    p.add_argument(
        "--no-early-stop",
        action="store_true",
        help=(
            "Disable the two-consecutive-noop early stop. Mirrors the baseline "
            "branch's 0b16a20: a fixed-horizon campaign needs every arm to reach "
            "the same round, and noop pairs are common — M20's L0 arm was cut at "
            "R2 of 3 by exactly this, and the 16-round reference run falsely "
            "early-stopped at R13. Without a fixed horizon, leave the stop on."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and exit (no LLM / no I/O).",
    )
    return p


async def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    if args.smoke:
        args.num_rounds = 2
        args.max_tasks = 1
        args.num_evolvers = 2

    if args.dry_run:
        _print_dry_run_plan(args)
        return

    await run_pilot(args)


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
