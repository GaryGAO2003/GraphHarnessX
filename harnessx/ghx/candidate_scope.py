# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Candidate scope — the cone-reach gate (C) and the resolution annotation (A).

Two questions the five official gates and the sixth (existence) gate never ask,
both answerable from files already on disk at Stage 4, zero LLM:

* **Gate C (refusal, modify-type only)** — a candidate that EDITS an existing
  mechanism, whose node appears in NONE of its own predicted tasks' failure
  cones, is structurally incapable of the effect it predicts; refuse it with
  the evidence.  Additive candidates (new tool / new processor) are exempt by
  construction — a new node cannot appear in cones that predate it (the exact
  trap the sixth gate's resolver docstring warned about); their check is the
  replay gate's ``fired``.
* **Annotation A (never a refusal)** — a candidate whose mechanism population
  (failing cones containing its node) is below the bed's resolution cannot be
  credited or blamed from curve movement; it ships, tagged ``sub_resolution``,
  so its accounting comes from its predicted tasks only.  Refusing small
  fixes would have blocked real ships (L0's OcrImage: predicted 3, hit 2/3).

Alias identity mirrors :mod:`harnessx.ghx.regression_triage`: the attribution
signature (declared, else the vendored inference) PLUS ``proc:py::_<stem>``
for the manifest's non-scratch ``.py`` file_changes — evolved processors are
file-URI loaded and their U nodes are minted from the FILE stem, never the
class slug.

Edit-kind is decided structurally, two independent producers ORed: the L5
graph-op names in ``file_changes[].diff_summary`` (``replace_same_group`` /
``mutate_params`` / ``remove``), and alias-stem presence in the PARENT config
text (an alias already wired in the parent = this candidate targets an
existing mechanism).

Seam: same shape as the sixth gate — wrap ``run_stage_4`` for the round, apply
to the shipped set before commit bookkeeping, evidence per candidate under
``graph_evidence/gate/scope_{cid}.md`` plus a round-level ``resolution.json``.
Every unanswerable case passes through with the reason recorded.

Flag: ``HARNESSX_GHX_GATE_SCOPE`` (call-time read, default off).
Threshold: ``HARNESSX_GHX_RESOLUTION_THRESHOLD`` (default 6 — the bed's
same-config pass@1 range; calibrate against the motif-population envelope).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_GATE_SCOPE"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})
_THRESHOLD_ENV = "HARNESSX_GHX_RESOLUTION_THRESHOLD"
_DEFAULT_THRESHOLD = 6

_GRAPH_OP_MARKERS = ("replace_same_group", "mutate_params", "remove_")
_SURFACE_JSON_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def scope_gate_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def resolution_threshold() -> int:
    try:
        return int(os.environ.get(_THRESHOLD_ENV, "") or _DEFAULT_THRESHOLD)
    except ValueError:
        return _DEFAULT_THRESHOLD


# ── identity / classification ─────────────────────────────────────────────────


def alias_nodes(fm: dict | None) -> set:
    """The candidate's mechanical alias set (see module docstring)."""
    if not isinstance(fm, dict):
        return set()
    from .attribution_graph import (
        infer_signature,
        processor_file_uri_static_id,
        processor_static_id,
    )

    aliases: set = set()
    sig = infer_signature(fm.get("bucket") if isinstance(fm.get("bucket"), str) else None, fm, fm.get("attribution_signature"))
    if isinstance(sig, dict):
        if sig.get("type") == "tool_call" and sig.get("tool_name"):
            aliases.add(f"tool:{sig['tool_name']}")
        elif sig.get("type") == "processor_invocation" and (sig.get("class_name") or sig.get("tool_name")):
            cn = str(sig.get("class_name") or sig.get("tool_name"))
            aliases.add(processor_static_id(cn))
            aliases.add(processor_file_uri_static_id(cn))
    bucket = fm.get("bucket")
    buckets = bucket if isinstance(bucket, list) else [bucket]
    for fc in fm.get("file_changes") or []:
        if not isinstance(fc, dict):
            continue
        path = str(fc.get("path") or "")
        if not path.endswith(".py"):
            continue
        stem = Path(path).stem
        if not stem or stem.startswith("_"):
            continue
        if "processor" in buckets:
            aliases.add(f"proc:py::_{stem}")
        if "tools" in buckets:
            aliases.add("tool:" + "".join(p.title() for p in stem.split("_")))
    return aliases


def load_surface(run_dir, round_n: int, cid: str) -> dict | None:
    """The candidate's graph mutation surface (piece-2 artifact) — the structural
    truth about WHICH existing nodes it removes/mutates.  Parses the file's
    machine-readable JSON block; ``None`` when absent/unreadable."""
    path = Path(run_dir) / f"R{round_n}" / "graph_evidence" / "candidates" / f"{cid}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = _SURFACE_JSON_RE.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def edit_kind(fm: dict | None, aliases: set, parent_config_text: str | None, surface: dict | None = None) -> str:
    """``"modify"`` when the candidate targets an existing mechanism, else ``"additive"``.

    The mutation surface is the structural authority (removed/mutated nodes != empty
    -> modify); the diff_summary markers and parent-text stem check are the
    fallback for rounds without surface files."""
    if isinstance(surface, dict):
        # Order matters: removed → modify; else ADDED → additive even when
        # params were incidentally mutated alongside (real case C-R2-02: adds
        # guard v1 + tweaks the judge's params — its mechanism is the new node,
        # and grading it modify made the judge param the reach target → a
        # false out-of-reach refusal); mutated-only → modify.
        if surface.get("nodes_removed"):
            return "modify"
        if surface.get("nodes_added"):
            return "additive"
        if surface.get("nodes_mutated"):
            return "modify"
    for fc in (fm or {}).get("file_changes") or []:
        summary = str((fc or {}).get("diff_summary") or "")
        if any(m in summary for m in _GRAPH_OP_MARKERS):
            return "modify"
    if parent_config_text:
        for a in aliases:
            stem = a.split("py::_", 1)[1] if "py::_" in a else None
            if stem and f"{stem}.py" in parent_config_text:
                return "modify"
    return "additive"


def reach_aliases(aliases: set, surface: dict | None) -> set:
    """The nodes the reach test should look for in the predicted tasks' cones.

    For a replace/remove candidate the true target is the node being TAKEN OUT
    — the new node cannot appear in cones that predate it (the resolver-trap
    the sixth gate's docstring named).  Removed nodes win; mutated nodes are
    the fallback; the manifest aliases cover surface-less rounds."""
    if isinstance(surface, dict):
        removed = {str(n) for n in surface.get("nodes_removed") or []}
        if removed:
            return removed
        mutated = {str(n) for n in surface.get("nodes_mutated") or []}
        if mutated:
            return mutated
    return set(aliases)


def _base_nodes(sig_list) -> set:
    return {str(s).split("#", 1)[0] for s in (sig_list or [])}


def _predicted(fm: dict | None) -> list:
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


# ── verdicts ──────────────────────────────────────────────────────────────────


@dataclass
class ScopeVerdict:
    cid: str
    checked: bool
    ok: bool
    kind: str = "unknown"  # additive | modify | unknown
    aliases: set = field(default_factory=set)
    population: int | None = None  # failing cones containing any alias
    threshold: int = _DEFAULT_THRESHOLD
    sub_resolution: bool = False
    predicted_with_cones: int = 0
    predicted_in_cone: list = field(default_factory=list)
    reason: str = ""


class ScopeGateResult:
    """gate_results entry — attribute-shaped because the vendored audit reads
    ``v.ok`` on every value it finds there (orchestrator.py:699)."""

    __slots__ = ("ok", "reason")

    def __init__(self, ok: bool, reason: str):
        self.ok = ok
        self.reason = reason


def check_candidate_scope(
    cid: str,
    fm: dict | None,
    *,
    cones: dict | None,
    parent_config_text: str | None,
    surface: dict | None = None,
    threshold: int | None = None,
) -> ScopeVerdict:
    thr = resolution_threshold() if threshold is None else threshold
    v = ScopeVerdict(cid=cid, checked=False, ok=True, threshold=thr)
    v.aliases = alias_nodes(fm)
    v.kind = edit_kind(fm, v.aliases, parent_config_text, surface)
    if cones is None:
        v.reason = "cone_sigs.json unavailable — cannot scope; passing through"
        return v
    base_by_task = {tid: _base_nodes(sig) for tid, sig in cones.items()}
    preds = _predicted(fm)

    # Annotation A — resolution = the candidate's effect-size upper bound on
    # THIS bed: how many of its predicted tasks are failing (have cones) this
    # round.  Kind-independent: an additive ship's own node has population 0
    # by construction (it does not exist yet), which says nothing about
    # whether the bed can see its effect.
    v.predicted_with_cones = sum(1 for t in preds if t in base_by_task)
    v.sub_resolution = v.predicted_with_cones < thr

    targets = reach_aliases(v.aliases, surface)
    v.population = (
        sum(1 for bases in base_by_task.values() if targets & bases) if targets else None
    )

    if not targets:
        v.reason = "no mechanical alias (prompt/config) — scope gate abstains"
        return v
    # Refusal C only for modify-type candidates; the reach test looks for the
    # REPLACED/MUTATED node — the new node cannot appear in cones that predate it.
    if v.kind != "modify":
        v.checked = True
        v.reason = (
            f"additive candidate — fire test is the replay gate's job; predicted "
            f"failing {v.predicted_with_cones}/{len(preds) or 0}"
        )
        return v
    with_cones = [t for t in preds if t in base_by_task]
    if not with_cones:
        v.reason = (
            "modify-type but no predicted task has a failing cone this round — "
            "cannot scope; passing through"
        )
        return v
    v.checked = True
    v.predicted_in_cone = [t for t in with_cones if targets & base_by_task[t]]
    if v.predicted_in_cone:
        v.ok = True
        v.reason = (
            f"targeted node ({', '.join(sorted(targets))}) reaches "
            f"{len(v.predicted_in_cone)}/{len(with_cones)} of its predicted tasks' cones"
        )
    elif not v.population:
        # Zero presence in ANY failing cone this round — dormant machinery, not
        # proof of incapability. An armed-but-empty engine changes no event, so
        # "attribute by what it CHANGED" keeps its node out of every U until its
        # first firing; refusing here deadlocks exactly the candidate whose job
        # is to arm it (hit live: M26 R1, the loop's first runtime-policy
        # rule-fill). Downgrade to additive-equivalent accounting — bed-level
        # claims stay stripped, the prediction ledger prices the hit rate.
        v.ok = True
        v.sub_resolution = True
        v.reason = (
            f"targeted node ({', '.join(sorted(targets))}) fired in ZERO failing "
            f"cones this round — dormant machinery; additive-equivalent "
            f"(sub_resolution accounting; the fire test is the replay gate's job)"
        )
    else:
        v.ok = False
        v.reason = (
            f"targeted node ({', '.join(sorted(targets))}) appears in NONE of the "
            f"{len(with_cones)} predicted tasks' failure cones — structurally "
            f"incapable of the predicted effect"
        )
    return v


# ── evidence + stage-4 application ────────────────────────────────────────────


def _render(v: ScopeVerdict) -> str:
    head = "REFUSED" if (v.checked and not v.ok) else ("CHECKED — ok" if v.checked else "PASSED THROUGH (not checked)")
    return "\n".join(
        [
            f"# Scope gate — {v.cid}",
            "",
            f"**{head}**",
            "",
            f"- kind: {v.kind}",
            f"- aliases: {', '.join(sorted(v.aliases)) or '(none)'}",
            f"- target population: {v.population if v.population is not None else '(n/a)'} failing cones",
            f"- predicted failing (effect-size bound): {v.predicted_with_cones} (threshold {v.threshold})",
            f"- sub_resolution: {v.sub_resolution}"
            + (" — bed-level curve claims are OUT for this ship; account it on its predicted tasks only" if v.sub_resolution else ""),
            f"- predicted-in-cone: {', '.join(v.predicted_in_cone) or '(none)'}",
            "",
            v.reason,
            "",
        ]
    )


def _cone_sigs(run_dir, round_n: int) -> dict | None:
    path = Path(run_dir) / f"R{round_n}" / "graph_evidence" / "cone_sigs.json"
    if not path.exists():
        return None
    try:
        failing = json.loads(path.read_text(encoding="utf-8")).get("failing")
    except json.JSONDecodeError:
        return None
    return failing if isinstance(failing, dict) else None


def apply_scope_gate_to_stage4(
    result: dict,
    *,
    candidates_info: dict,
    run_dir,
    round_n: int | None,
    parent_config_path=None,
) -> dict:
    shipped = list(result.get("shipped_cids") or ([] if not result.get("shipped_cid") else [result["shipped_cid"]]))
    if not shipped or round_n is None:
        return result

    parent_text = None
    if parent_config_path is not None:
        try:
            parent_text = Path(parent_config_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            parent_text = None
    cones = _cone_sigs(run_dir, round_n)

    gate_results = dict(result.get("gate_results") or {})
    resolution: dict = {}
    kept: list = []
    refusals: list = []

    for cid in shipped:
        fm = None
        info = candidates_info.get(cid)
        if info:
            try:
                from harnessx.aegis.agents.evolver import parse_candidate_manifest

                fm, _ = parse_candidate_manifest(Path(info[0]).read_text(encoding="utf-8"))
            except Exception:
                fm = None
        v = check_candidate_scope(
            cid,
            fm,
            cones=cones,
            parent_config_text=parent_text,
            surface=load_surface(run_dir, round_n, cid),
        )
        try:
            gate_dir = Path(run_dir) / f"R{round_n}" / "graph_evidence" / "gate"
            gate_dir.mkdir(parents=True, exist_ok=True)
            (gate_dir / f"scope_{cid}.md").write_text(_render(v), encoding="utf-8")
        except OSError:
            pass
        resolution[cid] = {
            "population": v.population,
            "predicted_failing": v.predicted_with_cones,
            "threshold": v.threshold,
            "sub_resolution": v.sub_resolution,
            "kind": v.kind,
            "aliases": sorted(v.aliases),
        }
        if v.checked and not v.ok:
            gr = dict(gate_results.get(cid) or {})
            # An OBJECT, not a dict: the vendored audit does `.ok` on every
            # gate_results value (orchestrator.py:699) — a dict here crashed the
            # whole evolve on the scope gate's first-ever live refusal (M26 R1).
            gr["scope"] = ScopeGateResult(False, v.reason)
            gate_results[cid] = gr
            refusals.append({"cid": cid, "reason": v.reason})
        else:
            kept.append(cid)

    try:
        ge = Path(run_dir) / f"R{round_n}" / "graph_evidence"
        ge.mkdir(parents=True, exist_ok=True)
        (ge / "resolution.json").write_text(json.dumps({"round": round_n, "candidates": resolution}, indent=1), encoding="utf-8")
    except OSError:
        pass

    if not refusals:
        return result
    new_result = dict(result)
    new_result["shipped_cids"] = kept
    new_result["shipped_cid"] = kept[0] if kept else None
    new_result["gate_results"] = gate_results
    new_result["scope_gate_refusals"] = refusals
    if not kept:
        new_result["reason"] = "all_candidates_failed_scope_gate"
    return new_result


async def run_round_with_scope_gate(
    orchestrator,
    *,
    parent_config_path=None,
    gate_enabled: bool | None = None,
    **run_round_kwargs,
):
    """Flag-gated wrapper, same seam discipline as the sixth gate: wrap the
    vendored ``run_stage_4`` name for this one round, restore in ``finally``."""
    if gate_enabled is None:
        gate_enabled = scope_gate_enabled()
    if not gate_enabled:
        return await orchestrator.run_round(**run_round_kwargs)

    import harnessx.aegis.orchestrator as _orch_mod

    run_dir = getattr(orchestrator, "run_dir", None)
    original = _orch_mod.run_stage_4

    async def _wrapped(**s4_kwargs):
        stage_4 = await original(**s4_kwargs)
        try:
            stage_4 = apply_scope_gate_to_stage4(
                stage_4,
                candidates_info=s4_kwargs.get("candidates_info") or {},
                run_dir=run_dir,
                round_n=s4_kwargs.get("round_n"),
                parent_config_path=parent_config_path,
            )
        except Exception as exc:  # noqa: BLE001 — a crashing gate fails open
            _LOG.warning("scope gate: apply failed (passing stage-4 through): %s", exc)
        return stage_4

    _orch_mod.run_stage_4 = _wrapped
    try:
        return await orchestrator.run_round(**run_round_kwargs)
    finally:
        _orch_mod.run_stage_4 = original
