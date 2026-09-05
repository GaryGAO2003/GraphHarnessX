# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Layer A takeover — the digest's mechanical table becomes a graph projection (M24 · P2).

Stage P's ``extract_trace_facts`` is the loop's staple food: 103 tables per
round, read by the Digester, prepended to every digest, quoted by Planner /
Evolver / Critic.  Two of its columns are wrong in ways measured on finished
campaigns: ``next_uses_result`` is a substring heuristic that grades 88–90%
of consumed results **NO** (observed_data edges show 98% consumed), and its
empty counts never reach the graph plane (U's outcome stamp is blind to
structured empties, ×6–28 drift).  The three-arm probe showed the roles copy
the false signal when both stories are on the table — so the fix is not a
second story, it is replacing the table's columns at the source.

This module patches the ONE call site (``preprocess.extract_trace_facts``)
with a graph-projected builder:

* payload columns (``return_type`` / ``return_len`` / ``args_sha``) — same
  classifier, same trajectory, byte-compatible semantics;
* flow columns from U's ``observed_data`` edges (``result_readers``,
  ``consumed_by_final``) replace the substring heuristic;
* a deterministic motif section (:mod:`harnessx.ghx.motifs`) replaces the
  false-signal shortlist.

Surgery, not reimplementation: the official extractor still runs, and its
markdown is edited between stable section markers — Exits, repeated-run and
burst sections stay byte-identical, anchors keep the
``trajectories/<file>#step_N`` scheme Layer B/C cite.  Honesty ladder, top to
bottom: no round-dir layout → official markdown unchanged; no U for a rollout
→ that rollout keeps official columns and says so; markers missing → official
markdown unchanged.  The takeover can only ever ADD graph truth, never lose
official truth.

Flag: ``HARNESSX_GHX_LAYER_A`` (read at call time, default off).  Install is a
context manager around the round call — the same restore-in-finally seam
pattern every other GHX overlay uses; vendored bytes untouched.
"""

from __future__ import annotations

import contextlib
import os
import re
from pathlib import Path

from .motifs import evaluate_motifs
from .projection import ProjectionReport, find_task_u, project_rollout

FLAG = "HARNESSX_GHX_LAYER_A"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_ROUND_DIR_RE = re.compile(r"^R(\d+)$")

# Section markers in the official to_markdown() — the surgery seams.
_M_TOOLS = "### Tool calls"
_M_REPEATS = "### Repeated tool calls"
_M_NOREF = "### Tool calls whose output the next step did NOT reference"
_M_PROVENANCE = "> These facts were extracted deterministically from trajectory jsonl."


def layer_a_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def _prev_round_dir(traj_path: Path):
    """R{n}/trajectories/<file> → (R{n-1} dir, n) — or (None, None) off-layout."""
    round_dir = traj_path.parent.parent
    m = _ROUND_DIR_RE.fullmatch(round_dir.name)
    if not m:
        return None, None
    n = int(m.group(1))
    prev = round_dir.parent / f"R{n-1}"
    return (prev if prev.is_dir() else None), n


def _u_for_trajectory(traj_path: Path, task_id: str):
    """``(U path, the round whose ledger row describes this rollout)`` or ``(None, None)``.

    Which round dir holds a trajectory's U is a *bed* convention, not a graph
    one: GAIA's ``R{n}/trajectories`` carry batch n−1, whose sessions live in
    ``R{n-1}``; τ²'s carry round n's own rollouts, whose sessions live right
    beside them.  Rather than take a flag for it, look: try the GAIA pairing
    first (unchanged for that bed, and it is the one that must not regress),
    then the same round dir.  Existence decides, so a third bed with either
    shape needs no new code — and one with neither still degrades to the
    official markdown, which is the honest outcome.
    """
    round_dir = traj_path.parent.parent
    prev, n = _prev_round_dir(traj_path)
    if prev is not None:
        u_path = find_task_u(prev, task_id)
        if u_path is not None:
            return u_path, n - 1
    if n is None:
        return None, None
    u_path = find_task_u(round_dir, task_id)
    return (u_path, n) if u_path is not None else (None, None)


def _fmt_row(c) -> str:
    prev = c.args_preview.replace("|", "/").replace("\n", " ")
    if c.ordinal >= 0:
        # Compressed readers column (M24 批改 #3): the full ordinal list ran to
        # 15 ids per row and carried no information beyond count + span — under
        # sliding-window context every reader from first to final is contiguous.
        ro = c.reader_ordinals
        if not ro:
            readers = "(none)"
        elif len(ro) <= 3:
            readers = ",".join(f"t{o}" for o in ro)
        else:
            readers = f"n={len(ro)}(t{ro[0]}→t{ro[-1]})"
        consumed = "yes" if c.consumed_by_final else ("**NO**" if c.return_len > 0 else "—")
    else:
        readers, consumed = "?", "?"
    return (
        f"| {c.step} | `{c.tool}` | {c.args_sha} | {prev} | {c.return_type} | "
        f"{c.return_len} | {readers} | {consumed} |"
    )


def _render_tools_section(official, projections: dict) -> list[str]:
    """The superset per-rollout table; official columns for U-less rollouts."""
    lines: list[str] = [_M_TOOLS, ""]
    for rollout in official.rollouts:
        rep: ProjectionReport | None = projections.get(rollout)
        fname = official.trajectory_file_by_rollout.get(rollout, "")
        if rep is None or not rep.u_available:
            calls = [c for c in official.tool_calls if c.rollout == rollout]
            if not calls:
                lines += [f"**{rollout}** — no tool calls.", ""]
                continue
            lines += [
                f"**{rollout}** → `trajectories/{fname}` _(no U for this rollout — official columns)_",
                "",
                "| step | tool | args_sha | args_preview | return_type | return_len | next_uses_result |",
                "|---|---|---|---|---|---|---|",
            ]
            for c in calls:
                nu = "—" if c.next_uses_result is None else ("yes" if c.next_uses_result else "**NO**")
                prev = c.args_preview.replace("|", "/").replace("\n", " ")
                lines.append(
                    f"| {c.step} | `{c.tool}` | {c.args_sha} | {prev} | {c.return_type} | {c.return_len} | {nu} |"
                )
            lines.append("")
            continue
        if not rep.tool_calls:
            lines += [f"**{rollout}** — no tool calls.", ""]
            continue
        lines += [
            f"**{rollout}** → `trajectories/{fname}`",
            "",
            "| step | tool | args_sha | args_preview | return_type | return_len | result_readers | consumed_by_final |",
            "|---|---|---|---|---|---|---|---|",
        ]
        lines += [_fmt_row(c) for c in rep.tool_calls]
        if rep.pairing_conflicts:
            lines.append("")
            lines.append(
                "_U↔trajectory pairing conflicts (flow columns may be shifted for these):_ "
                + "; ".join(rep.pairing_conflicts)
            )
        lines.append("")
    return lines


def _render_flow_sections(official, projections: dict) -> list[str]:
    """Replaces the substring-heuristic shortlist with edge truth + motifs."""
    lines: list[str] = ["### Tool results that reached NO model call (observed_data edges)", ""]
    dead: list[str] = []
    for rollout, rep in projections.items():
        if not rep.u_available:
            continue
        for c in rep.tool_calls:
            if c.ordinal >= 0 and c.return_len > 0 and not c.reader_ordinals:
                dead.append(
                    f"- **{rollout}** step {c.step} `{c.tool}` (return_type={c.return_type}, "
                    f"len={c.return_len}) — `{official.anchor(rollout, c.step)}`"
                )
    if dead:
        lines += [
            "_These results were produced and then never entered any model call's "
            "context — the graph-observed replacement for the retired substring "
            "heuristic (which graded 88–90% of consumed results NO)._",
            "",
            *dead,
        ]
    else:
        lines.append(
            "_None — every non-empty tool result entered at least one model call's context "
            "(observed_data edges; the retired substring heuristic is not evidence)._"
        )
    lines.append("")

    lines += ["### Mechanism signatures (deterministic motifs over U)", ""]
    any_hit = False
    for rollout, rep in projections.items():
        m = evaluate_motifs(rep, exit_reason=getattr(rep, "ledger_exit", None))
        if not m.hits:
            continue
        any_hit = True
        lines.append(f"**{rollout}** — primary: `{m.primary}`")
        for h in m.hits:
            extra = ""
            if h.params.get("search_only"):
                extra = " [search_only]"
            if h.params.get("degraded"):
                extra += " [no-U degraded]"
            lines.append(f"- `{h.motif}`{extra} ×{h.count} — {h.detail}")
            for a in h.anchors[:3]:
                # backticked so the vendored IV-1 anchor regex ([`\[]-wrapped)
                # counts these as citation anchors — bare paths score zero
                lines.append(f"  - `{a}`")
        lines.append("")
    if not any_hit:
        lines += ["_No motif fired (or no U available to evaluate flow motifs)._", ""]
    return lines


class GraphedTraceFacts:
    """Duck-typed stand-in for the vendored ``TraceFacts`` at its one call site
    (``preprocess`` uses only ``.to_markdown()``); everything else delegates."""

    def __init__(self, official, projections: dict):
        self._official = official
        self._projections = projections

    def __getattr__(self, name):
        return getattr(self._official, name)

    def to_markdown(self) -> str:
        md = self._official.to_markdown()
        if not self._projections or not any(p.u_available for p in self._projections.values()):
            return md  # full fallback: no U anywhere → official, byte-identical

        i_tools = md.find(_M_TOOLS)
        i_repeats = md.find(_M_REPEATS)
        i_noref = md.find(_M_NOREF)
        if not (0 <= i_tools < i_repeats and i_repeats < i_noref):
            return md  # markers missing/reordered → official, never worse

        provenance = (
            "> Layer A′ (graph-projected): the tool table's flow columns come from the "
            "unfolded graph U's observed_data edges joined with the trajectory message "
            "plane — `result_readers` lists the model invocations whose context the "
            "result entered, `consumed_by_final` whether the terminal (answer-producing) "
            "call read it. The substring next-step heuristic is retired. Rollouts "
            "without a U keep official columns and are marked."
        )
        head = md[:i_tools]
        if _M_PROVENANCE in head:
            head = head.replace(_M_PROVENANCE, _M_PROVENANCE + "\n" + provenance, 1)

        middle = md[i_repeats:i_noref]  # repeats + bursts, byte-identical official
        tools = "\n".join(_render_tools_section(self._official, self._projections))
        tail = "\n".join(_render_flow_sections(self._official, self._projections))
        return head + tools + "\n" + middle + tail


def _ledger_exit(run_root: Path, batch_round: int, task_id: str):
    """The ledger's exit for (batch_round, task_id) — authoritative over the
    trajectory's own episode_end (measured: 4/103 disagree on one round)."""
    import json

    path = run_root / "data" / "task_history.jsonl"
    if not path.exists():
        return None
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("task_id")) == task_id and int(row.get("round", -1)) == batch_round:
                return row.get("exit")
    except OSError:
        return None
    return None


def extract_trace_facts_graphed(task_id: str, trajectory_paths):
    """Drop-in for ``preprocess.extract_trace_facts`` — official facts plus the
    graph projection, joined per rollout via the R{n}→R{n-1} layout."""
    from harnessx.aegis.stages.trace_facts import extract_trace_facts as _official_extract

    official = _official_extract(task_id, trajectory_paths)
    projections: dict[str, ProjectionReport] = {}
    for path in trajectory_paths:
        path = Path(path)
        u_path, ledger_round = _u_for_trajectory(path, task_id)
        if u_path is None:
            continue
        rep = project_rollout(task_id, path, u_path)
        # The ledger row for the batch this trajectory came from is the
        # authoritative exit (feeds budget_no_commit); which round that is
        # follows from where the U was found, not from a fixed offset.
        rep.ledger_exit = _ledger_exit(path.parent.parent.parent, ledger_round, task_id)
        projections[rep.rollout] = rep
    return GraphedTraceFacts(official, projections)


@contextlib.contextmanager
def install_layer_a():
    """Patch the Stage-P seam for one round; restore even on exception.

    Patches the *preprocess* module's bound name — the call site resolves it as
    a module global at call time — and never touches ``trace_facts`` itself,
    which the graphed builder still calls for the official half.
    """
    import harnessx.aegis.stages.preprocess as _pp

    original = _pp.extract_trace_facts
    _pp.extract_trace_facts = extract_trace_facts_graphed
    try:
        yield
    finally:
        _pp.extract_trace_facts = original
