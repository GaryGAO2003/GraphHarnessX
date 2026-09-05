# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Compose multiple shipped candidates' applied configs onto a base.

Each candidate's applied YAML is a FULL HarnessConfig derived from the
round's base config + the candidate's bucket-specific change. When
multiple candidates ship in the same round, we can't just take "last
wins" — each candidate's unchanged fields would silently overwrite
earlier candidates' changes.

This helper diffs each candidate's bucket-relevant fields against the
frozen parent and applies only those changes to the running base:

  prompt     — take candidate's `template_path` for the SystemPromptProcessor
  tools      — merge candidate's `tool_registry.custom` vs parent: drop
               entries parent had but candidate removed, append entries
               candidate added
  config     — replace matching processor kwargs (matched by `_target_`)
  processor  — apply candidate's processor diff vs parent: drop processors
               parent had but candidate removed, append processors candidate
               added (matched by `_target_`)

Multi-ship is only valid when each shipped candidate's bucket is
DISJOINT from the others. Stage 4 enforces that constraint before
calling this function.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComposeResult:
    """What actually landed, as opposed to what was shipped.

    Before P-18 this function returned the output path and the caller assumed
    every shipped candidate was in it. That assumption held only because a
    candidate compose could not express took the whole round down with it, so
    there was never a partial result to report — see M15_smoke_L2 R1, where one
    mis-bucketed candidate discarded two good ones.

    Now the caller needs to know the difference, because only ``landed`` may be
    recorded as shipped.

    ``output_path`` is None when every candidate was rejected and no merged.yaml
    was written.
    """

    output_path: Path | None
    landed: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)

    # Back-compat: the old return value was the path, and callers read it
    # directly. Keeping those two work rather than churning every call site.
    def read_text(self, *a, **kw) -> str:
        if self.output_path is None:
            raise FileNotFoundError("compose wrote no merged.yaml — every candidate was rejected")
        return self.output_path.read_text(*a, **kw)

    def exists(self) -> bool:
        return self.output_path is not None and self.output_path.exists()


class BucketCannotExpressCandidate(RuntimeError):
    """A bucket applier was handed a change its bucket cannot make.

    Raised rather than skipped because the skip is invisible: the candidate has
    already been accepted, ranked and written into ``decision.md`` by the time an
    applier runs, so a silent no-op leaves the round claiming a ship that is not in
    ``merged.yaml``. ``_assert_merged_differs_from_base`` does not catch it either —
    a second, correctly-bucketed candidate satisfies that guard on its own.
    """


def _is_system_prompt(proc: dict) -> bool:
    tgt = str(proc.get("_target_", ""))
    return tgt.endswith(".SystemPromptProcessor") or "SystemPromptProcessor" in tgt


def _apply_prompt(base: dict, candidate: dict, parent: dict) -> None:
    """Copy the candidate's SystemPromptProcessor template_path into base.

    Falls back to _apply_config-style kwarg diffing when no template_path
    change is detected — this handles Evolvers that mutate prompt content
    via AppendSystemPromptProcessor.prompt_path or similar non-template_path
    patterns.
    """
    cand_tp = None
    for p in candidate.get("processors", []) or []:
        if isinstance(p, dict) and _is_system_prompt(p):
            sb = p.get("system_builder") or {}
            if isinstance(sb, dict):
                cand_tp = sb.get("template_path")
                if cand_tp:
                    break
    if cand_tp:
        for bp in base.get("processors", []) or []:
            if isinstance(bp, dict) and _is_system_prompt(bp):
                sb = bp.setdefault("system_builder", {})
                if isinstance(sb, dict):
                    sb["template_path"] = cand_tp
    else:
        # No template_path swap found — fall through to config-style kwarg
        # diffing so AppendSystemPromptProcessor.prompt_path changes and
        # similar patterns are still applied to the base.
        _apply_config(base, candidate, parent)


def _apply_tools(base: dict, candidate: dict, parent: dict) -> None:
    """Apply candidate's tool_registry.custom diff vs parent onto base.

    Drops entries parent had but candidate removed; appends entries candidate
    added. Ensures a candidate that intends to *replace* a custom tool (by
    dropping the old entry and adding a new one in its own config.yaml) does
    not end up with both sitting side-by-side in merged.yaml.
    """
    cand_tr = candidate.get("tool_registry") or {}
    parent_tr = parent.get("tool_registry") or {}
    if not isinstance(cand_tr, dict) or not isinstance(parent_tr, dict):
        return
    cand_custom = cand_tr.get("custom") or []
    parent_custom = parent_tr.get("custom") or []
    if not isinstance(cand_custom, list) or not isinstance(parent_custom, list):
        return

    dropped = [e for e in parent_custom if e not in cand_custom]
    added = [e for e in cand_custom if e not in parent_custom]
    if not dropped and not added:
        return

    base_tr = base.setdefault("tool_registry", {})
    if not isinstance(base_tr, dict):
        base_tr = {}
        base["tool_registry"] = base_tr
    base_custom = base_tr.setdefault("custom", [])
    if not isinstance(base_custom, list):
        base_custom = []
        base_tr["custom"] = base_custom

    if dropped:
        base_custom[:] = [e for e in base_custom if e not in dropped]
    for entry in added:
        if entry not in base_custom:
            base_custom.append(entry)


def _apply_config(base: dict, candidate: dict, parent: dict) -> None:
    """Replace matching processor kwargs (matched by _target_) in base.

    Writes a kwarg only where the CANDIDATE differs from ``parent`` — the frozen
    round base — never merely where it differs from ``base``.

    ``base`` is mutated in place by each applier in turn, so "differs from base"
    also matches every field a previous candidate just changed. A candidate's
    config.yaml is a full config, so it carries the parent's value for everything
    it did not touch; comparing against the mutated base therefore writes those
    untouched originals back and silently reverts the earlier ship. Comparing
    against ``parent`` asks the right question — did this candidate intend this
    value — and a candidate with no opinion leaves the field alone.
    """
    base_procs = base.get("processors") or []
    cand_procs = candidate.get("processors") or []
    parent_by_target: dict[str, dict] = {
        p["_target_"]: p
        for p in (parent.get("processors") or [])
        if isinstance(p, dict) and p.get("_target_")
    }
    base_by_target: dict[str, dict] = {}
    for bp in base_procs:
        if isinstance(bp, dict):
            tgt = bp.get("_target_")
            if tgt:
                base_by_target[tgt] = bp
    for cp in cand_procs:
        if not isinstance(cp, dict):
            continue
        tgt = cp.get("_target_")
        if not tgt:
            continue
        if tgt not in base_by_target:
            if tgt in parent_by_target:
                # A previous applier removed it this round. Not this candidate's
                # doing and not something it can express; skipping is correct.
                continue
            # In neither the round base nor the parent, so the candidate is ADDING
            # a processor while declaring the config bucket — which this applier
            # cannot do. Skipping it silently is how a candidate gets accepted,
            # ranked, written into decision.md and never landed: M13's only real
            # ship accepted two and delivered one, with no error anywhere and the
            # empty-ship guard satisfied by the other.
            raise BucketCannotExpressCandidate(
                f"config bucket cannot add a processor: {tgt!r} is absent from both "
                f"the round base and the parent. This candidate belongs in the "
                f"processor bucket. Re-derive its bucket or re-propose it."
            )
        bp = base_by_target[tgt]
        pp = parent_by_target.get(tgt) or {}
        for k, v in cp.items():
            if k in ("_target_", "_code_hash", "_hook_"):
                continue
            if pp.get(k) != v:
                bp[k] = v


def _apply_processor(base: dict, candidate: dict, parent: dict) -> None:
    """Apply candidate's processor diff vs parent onto base.

    Matches by ``_target_`` string. Drops entries parent had but candidate
    removed (the candidate's intent to *replace* an existing processor is
    expressed by omitting it from its config.yaml); appends entries candidate
    added that aren't already present in base.
    """
    parent_targets = {
        p.get("_target_") for p in (parent.get("processors") or []) if isinstance(p, dict) and p.get("_target_")
    }
    cand_procs = candidate.get("processors") or []
    cand_targets = {p.get("_target_") for p in cand_procs if isinstance(p, dict) and p.get("_target_")}

    removed_targets = parent_targets - cand_targets
    added_targets = cand_targets - parent_targets

    base_procs = base.setdefault("processors", [])
    if not isinstance(base_procs, list):
        return

    if removed_targets:
        base_procs[:] = [p for p in base_procs if not (isinstance(p, dict) and p.get("_target_") in removed_targets)]

    existing = {p.get("_target_") for p in base_procs if isinstance(p, dict)}
    for cp in cand_procs:
        if not isinstance(cp, dict):
            continue
        tgt = cp.get("_target_")
        if tgt in added_targets and tgt not in existing:
            base_procs.append(cp)
            existing.add(tgt)


_BUCKET_APPLIERS = {
    "prompt": _apply_prompt,
    "tools": _apply_tools,
    "config": _apply_config,
    "processor": _apply_processor,
}


def compose_shipped_configs(
    base_config_path: Path,
    shipped: Iterable[tuple[str, str, Path]],
    output_path: Path,
) -> "ComposeResult":
    """Merge shipped candidates' bucket-specific changes onto the base.

    Args:
        base_config_path: the round's starting config (pre-ship).
        shipped: iterable of ``(candidate_id, bucket, applied_yaml_path)``
            tuples, in rank order. Each candidate's `bucket` field names
            which fields of the base to overlay.
        output_path: where to write the merged result.

    Returns:
        A :class:`ComposeResult`. A candidate whose bucket cannot express it is
        dropped on its own and named in ``rejected``; the rest still land. Only
        ``landed`` may be recorded as shipped.

    v0.9.3: ``bucket`` may be a str (legacy) OR a list of str (cross-
    bucket bundle). When a list is given, each bucket's applier is
    invoked in the declared order so the candidate's diff is merged in
    full. Stage 4 no longer enforces bucket-disjointness — merge
    conflicts are handled per-applier (later writes overwrite earlier
    for the same key).
    """
    base = yaml.safe_load(base_config_path.read_text(encoding="utf-8")) or {}
    # Freeze a parent snapshot so each applier can diff candidate vs parent
    # instead of candidate vs running base (which earlier appliers may have
    # mutated). Without this, a processor candidate that intends to replace
    # v1 with v2 by omitting v1 from its config.yaml would leave v1 in the
    # merged output alongside v2.
    parent = copy.deepcopy(base)
    landed: list[str] = []
    rejected: list[tuple[str, str]] = []
    for cid, bucket, applied_path in shipped:
        cand = yaml.safe_load(applied_path.read_text(encoding="utf-8")) or {}
        # Normalize bucket to a list.
        if isinstance(bucket, list):
            bucket_list = [str(b) for b in bucket if b]
        elif isinstance(bucket, str) and bucket:
            bucket_list = [bucket]
        else:
            continue
        # Each candidate is applied to a scratch copy and only committed once
        # every one of its buckets succeeded. Applying straight to `base` meant
        # a raising applier killed the loop before write_text — no merged.yaml
        # at all, and the other candidates' work discarded along with it.
        #
        # M15_smoke_L2 R1: the Critic shipped three, C-R1-01 declared bucket
        # `config` while adding a processor (P-9 refuses that, correctly), and
        # C-R1-02 (prompt) and C-R1-03 (processor) — both fine — went down with
        # it. The round then ran the parent config. One bad bucket, a wasted
        # round.
        #
        # A candidate that fails halfway through a cross-bucket bundle is also
        # why the copy is per candidate rather than per bucket: half a bundle is
        # not a smaller version of the ship, it is a config nobody proposed.
        scratch = copy.deepcopy(base)
        try:
            for b in bucket_list:
                apply_fn = _BUCKET_APPLIERS.get(b)
                if apply_fn is None:
                    continue
                apply_fn(scratch, cand, parent)
        except BucketCannotExpressCandidate as exc:
            rejected.append((cid, str(exc)))
            _log.warning(
                "compose: dropping %s and keeping the rest of the round — %s", cid, exc
            )
            continue
        base = scratch
        landed.append(cid)
    if rejected and not landed:
        # Nothing to write. The caller must not record these as shipped; the
        # ledger's not_scoreable path (P-16) covers a round that gets here.
        _log.warning(
            "compose: every shipped candidate was rejected (%s) — writing no merged.yaml",
            ", ".join(cid for cid, _ in rejected),
        )
        return ComposeResult(output_path=None, landed=[], rejected=rejected)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(base, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return ComposeResult(output_path=output_path, landed=landed, rejected=rejected)
