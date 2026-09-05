# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""U ↔ trajectory projection — the single evidence join (M24 · P0).

The official Layer A (:mod:`harnessx.aegis.stages.trace_facts`) and the unfolded
graph U record the *same* batch from two vantage points, and each is blind where
the other sees:

* the digest knows a WebFetch came back empty (it reads the flattened tool
  message — what the model actually saw) but judges "was the result used" with a
  substring heuristic that mislabels real consumption as **NO**;
* U knows exactly which model invocations read the result message
  (``observed_data`` edges) but its ``outcome`` stamp reads the *raw* tool return
  before message flattening, so structured empties (WebFetch / Read / Browser
  shells) all grade ``ok`` — measured 869 digest-empties vs 101 U-empties over
  309 correctly-paired tasks (8.6× undercount).

This module joins the two at projection time — no recorder change, works on every
historical U — producing per-tool-call records that carry BOTH the payload truth
(``return_type``/``return_len`` computed on the message plane with the same
classification the vendored extractor uses) AND the flow truth (which model
ordinals consumed the result, whether the terminal model call did).

The classifier trio (:func:`content_to_text` / :func:`classify_return` /
:func:`args_sha`) is deliberately a byte-for-byte port of the vendored
``trace_facts`` versions rather than an import: ``harnessx/ghx`` must stay
importable without touching the vendored package, and
``tests/ghx/test_projection.py::test_classifier_parity_with_vendored`` pins the
two against drift.

Pairing contract.  Trajectory-side pairing is exact (``tool_call_id`` joins the
assistant's call to its ``raw_tool`` result).  U-side pairing is positional
within ``(step, tool_name)`` — U nodes do not carry ``tool_call_id`` (recorder
addition deferred post-freeze) — and every count mismatch is surfaced in
``pairing_conflicts``, never silently absorbed.  The trajectory is the base
sequence: a U node with no trajectory call is reported as a conflict and not
emitted, a trajectory call with no U node is emitted with ``ordinal=-1`` and no
flow columns.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from harnessx.graph.causal import DATA
from harnessx.graph.unfold import UnfoldedGraph, load_unfolded, payload_is_empty

# ── classifier trio: byte-parity port of harnessx.aegis.stages.trace_facts ────
# (parity pinned by tests/ghx/test_projection.py::test_classifier_parity_with_vendored)

_MULTIMODAL_MARKERS = (
    "[image displayed below]",
    "image displayed below",
    "[content omitted",
    "content omitted for length",
    "<image>",
    "<file>",
)


def args_sha(args: object) -> str:
    try:
        blob = json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        blob = repr(args)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:8]


def content_to_text(content: object) -> tuple[str, bool]:
    """Flatten assistant/tool content to a plain string. Returns (text, had_structured_blocks)."""
    if content is None:
        return "", False
    if isinstance(content, str):
        return content, False
    if isinstance(content, list):
        parts: list[str] = []
        structured = False
        for blk in content:
            if isinstance(blk, dict):
                if blk.get("type") in ("image", "file", "image_url", "input_image"):
                    structured = True
                    parts.append(f"<{blk.get('type')}>")
                else:
                    txt = blk.get("text") or blk.get("content") or ""
                    parts.append(str(txt))
            else:
                parts.append(str(blk))
        return "\n".join(parts), structured
    return str(content), False


def classify_return(text: str, had_structured: bool) -> str:
    """text / multimodal / multimodal_coerced / short_marker / empty / error"""
    if not text.strip():
        return "empty"
    low = text.strip().lower()
    if low.startswith("error") or "traceback" in low[:200]:
        return "error"
    if had_structured:
        return "multimodal"
    if len(text) < 120 and any(m in low for m in (m.lower() for m in _MULTIMODAL_MARKERS)):
        return "multimodal_coerced"
    return "text"


# ── projected records ─────────────────────────────────────────────────────────

_FINAL_ANSWER_RE = re.compile(r"FINAL ANSWER", re.IGNORECASE)


@dataclass
class ProjectedToolCall:
    """One trajectory tool call, enriched with U flow columns when paired."""

    rollout: str
    step: int
    tool: str
    tool_call_id: str
    args_sha: str
    args_preview: str
    return_type: str  # text | multimodal | multimodal_coerced | empty | error | missing
    return_len: int
    ordinal: int = -1  # U invocation ordinal; -1 when unpaired / U unavailable
    node_id: str | None = None
    outcome_u: str = ""  # what U's recorder stamped (drift metric vs return_type)
    reader_ordinals: tuple = ()  # model invocation ordinals that read the result msg
    consumed_by_final: bool = False

    @property
    def payload_empty(self) -> bool:
        return self.return_type == "empty"


@dataclass
class ProjectionReport:
    """One rollout's joined view: trajectory payload truth × U flow truth."""

    task_id: str
    rollout: str
    traj_path: str
    u_path: str | None
    u_available: bool
    tool_calls: list = field(default_factory=list)  # list[ProjectedToolCall]
    final_model_ordinal: int | None = None
    final_answer_emitted: bool = False
    final_answer_step: int | None = None
    terminal_snippet: str = ""
    exit_reason: str | None = None
    total_steps: int | None = None
    pairing_conflicts: list = field(default_factory=list)  # list[str]

    def consumed_rate(self) -> float | None:
        """Fraction of non-empty paired calls whose result reached ANY model call."""
        paired = [c for c in self.tool_calls if c.ordinal >= 0 and c.return_len > 0]
        if not paired:
            return None
        return sum(1 for c in paired if c.reader_ordinals) / len(paired)


def _rollout_tag(path: Path) -> str:
    stem = path.name.replace(".jsonl", "")
    if "_r" in stem:
        return "r" + stem.rsplit("_r", 1)[1]
    return stem


def _parse_trajectory(path: Path):
    """→ (calls, results_by_id, exit_reason, total_steps, final_answer(step|None), terminal_snippet)

    ``calls``: ordered [(step, tool, args, tool_call_id)] — assistant emission order.
    """
    calls: list[tuple[int, str, object, str]] = []
    results: dict[str, object] = {}
    exit_reason: str | None = None
    total_steps: int | None = None
    fa_step: int | None = None
    terminal = ""
    n_assistant = 0
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        etype = ev.get("type")
        msg = ev.get("message") or {}
        if etype == "raw_assistant":
            n_assistant += 1
            step = int(ev.get("step", 0))
            txt, _ = content_to_text(msg.get("content"))
            if txt.strip():
                terminal = txt[-200:]
                if fa_step is None and _FINAL_ANSWER_RE.search(txt):
                    fa_step = step
            for tc in msg.get("tool_calls") or []:
                if not isinstance(tc, dict):
                    continue
                calls.append(
                    (
                        step,
                        tc.get("name") or "?",
                        tc.get("input") or tc.get("arguments") or {},
                        tc.get("id") or "",
                    )
                )
        elif etype == "raw_tool":
            tid = msg.get("tool_call_id")
            if tid:
                results[tid] = msg.get("content")
        elif etype == "episode_end":
            exit_reason = str(ev.get("exit_reason", "?"))
            total_steps = int(ev.get("total_steps", n_assistant))
    if total_steps is None:
        total_steps = n_assistant
    return calls, results, exit_reason, total_steps, fa_step, terminal


def _u_flow_index(u: UnfoldedGraph):
    """→ (tool_nodes ordered by ordinal, readers: node_id → sorted model ordinals,
          final_model_ordinal | None, outcome_by_id)"""
    by_id = {n.id: n for n in u.nodes}
    tool_nodes = sorted(
        (n for n in u.nodes if str(n.static_node_id).startswith("tool:")),
        key=lambda n: n.ordinal,
    )
    model_ordinals = sorted(
        n.ordinal for n in u.nodes if str(n.static_node_id).startswith("model:")
    )
    final_model = model_ordinals[-1] if model_ordinals else None
    readers: dict[str, list[int]] = {}
    for e in u.edges_of_type(DATA):
        src = by_id.get(e.source)
        tgt = by_id.get(e.target)
        if src is None or tgt is None:
            continue
        if str(src.static_node_id).startswith("tool:") and str(tgt.static_node_id).startswith("model:"):
            readers.setdefault(src.id, []).append(tgt.ordinal)
    return tool_nodes, {k: tuple(sorted(v)) for k, v in readers.items()}, final_model


def project_rollout(
    task_id: str,
    traj_path,
    u=None,
) -> ProjectionReport:
    """Join one rollout's trajectory with its U (``UnfoldedGraph`` | path | None).

    ``u=None`` (or an unreadable path) degrades honestly: every call is emitted
    from the trajectory alone with ``ordinal=-1`` and no flow columns, and
    ``u_available`` is False — the shape the Layer A builder needs for its
    official-extractor fallback decision.
    """
    traj_path = Path(traj_path)
    u_path: str | None = None
    graph: UnfoldedGraph | None = None
    if u is not None:
        if isinstance(u, UnfoldedGraph):
            graph = u
        else:
            u_path = str(u)
            try:
                graph = load_unfolded(u)
            except Exception:
                graph = None

    calls, results, exit_reason, total_steps, fa_step, terminal = _parse_trajectory(traj_path)

    rep = ProjectionReport(
        task_id=task_id,
        rollout=_rollout_tag(traj_path),
        traj_path=str(traj_path),
        u_path=u_path,
        u_available=graph is not None,
        exit_reason=exit_reason,
        total_steps=total_steps,
        final_answer_emitted=fa_step is not None,
        final_answer_step=fa_step,
        terminal_snippet=terminal,
    )

    # payload columns from the trajectory (exact, tool_call_id-keyed)
    projected: list[ProjectedToolCall] = []
    for step, tool, args, tcid in calls:
        try:
            preview = json.dumps(args, ensure_ascii=False, default=str)[:120]
        except Exception:
            preview = str(args)[:120]
        if tcid in results:
            rtext, structured = content_to_text(results[tcid])
            rtype = classify_return(rtext, structured)
            # Structured-empty upgrade (shared with U's classify_tool_outcome via
            # payload_is_empty): classify_return alone only sees text.strip(), so
            # a custom tool's '{"results": []}' or an error-only object grades
            # "text" here even though it carries nothing. Applied after the
            # vendored-parity classifier, not inside it — content_to_text /
            # classify_return stay a byte-for-byte port (test_projection.py::
            # test_classifier_parity_with_vendored pins them); "error" is left
            # alone, it is already the more specific label.
            if rtype not in ("empty", "error") and payload_is_empty(rtext):
                rtype = "empty"
            rlen = len(rtext)
        else:
            rtype, rlen = "missing", 0
        projected.append(
            ProjectedToolCall(
                rollout=rep.rollout,
                step=step,
                tool=tool,
                tool_call_id=tcid,
                args_sha=args_sha(args),
                args_preview=preview,
                return_type=rtype,
                return_len=rlen,
            )
        )

    # flow columns from U (positional within (step, tool))
    if graph is not None:
        tool_nodes, readers, final_model = _u_flow_index(graph)
        rep.final_model_ordinal = final_model
        traj_groups: dict[tuple[int, str], list[ProjectedToolCall]] = {}
        for c in projected:
            traj_groups.setdefault((c.step, c.tool), []).append(c)
        u_groups: dict[tuple[int, str], list] = {}
        for n in tool_nodes:
            u_groups.setdefault((n.step, str(n.static_node_id).split(":", 1)[1]), []).append(n)

        for key in sorted(set(traj_groups) | set(u_groups)):
            tcs = traj_groups.get(key, [])
            uns = u_groups.get(key, [])
            if len(tcs) != len(uns):
                rep.pairing_conflicts.append(
                    f"step {key[0]} tool {key[1]}: trajectory has {len(tcs)} call(s), U has {len(uns)} node(s)"
                )
            for c, n in zip(tcs, uns):
                c.ordinal = n.ordinal
                c.node_id = n.id
                c.outcome_u = n.outcome
                c.reader_ordinals = readers.get(n.id, ())
                c.consumed_by_final = final_model is not None and final_model in c.reader_ordinals

    rep.tool_calls = projected
    return rep


def find_task_u(round_dir, task_id: str):
    """Locate the U file for one task's batch session under ``R{n}/sessions``.

    Returns the newest ``*_unfolded.jsonl`` for the task's aegis session, or
    None.  Round convention: batch n's sessions (and its U) live under
    ``R{n}/sessions/aegis/R{n}-<task_id>/graph/`` — the SAME round dir whose
    ``trajectories/`` land in ``R{n+1}`` at preprocess time, so callers pairing
    digests must pass the *previous* round's dir here.
    """
    round_dir = Path(round_dir)
    hits = sorted(
        round_dir.glob(f"sessions/aegis/*{task_id}*/graph/*_unfolded.jsonl"),
        key=lambda p: p.stat().st_mtime,
    )
    if hits:
        return hits[-1]
    # τ² has no `aegis/` level and numeric task ids, so the substring glob above
    # matches nothing here and would match too much if it did ("1" inside
    # "R0-11"). Its sessions are named exactly `{round}-{slug}`, where the slug
    # is the id itself unless it needs sanitising for the filesystem.
    from .tau2_layout import task_slug

    slug = task_slug(task_id)
    exact = [
        p
        for p in round_dir.glob(f"sessions/*-{slug}/graph/*_unfolded.jsonl")
        if p.parent.parent.name.rsplit("-", 1)[-1] == slug.rsplit("-", 1)[-1]
    ]
    if not exact:
        return None
    return max(exact, key=lambda p: p.stat().st_mtime)
