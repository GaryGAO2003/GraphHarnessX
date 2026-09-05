# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Motif population table — the Planner's ranking becomes a count (M24 · P4).

The Planner's landscape ranks failure themes by prose intuition over 103
digests; the graph already knows the populations.  L0's measured cost of the
prose ranking: the dominant mechanism (``tool:Bash#empty``, present in 25/31
failing cones from round one) took three rounds to get targeted, and the
free-text ``failure_mode`` vocabulary (493 labels for 510 failures) made
cross-round aggregation impossible.

This module aggregates the per-digest motif sections that the Layer A
takeover (P2) writes, at the one seam that runs after every digest exists and
before the Planner reads anything: ``preprocess.aggregate_digests``.  Two
artifacts per round:

* ``R{n}/graph_evidence/population.md`` — full table: per-motif task counts
  (any-hit and primary) over failing digests, the same predicate evaluated on
  PASSING digests (``ungrounded_commit`` on a pass = the luck/leak flag, full
  task ids per P-15b), and the measured population-noise note so nobody reads
  a ±5 swing as signal;
* a compact ``## Motif populations`` section appended to the round's
  ``summary.md`` — the file the Planner already reads.

Node-level lift stays in ``facts.md`` (evidence_files owns it); this table is
the MOTIF plane.  Digests without motif sections (official Layer A) make the
whole pass an honest no-op: nothing written, nothing appended, official
aggregate result returned untouched.

Flag: ``HARNESSX_GHX_POPULATION`` (call-time read, default off).
"""

from __future__ import annotations

import contextlib
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

FLAG = "HARNESSX_GHX_POPULATION"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_PATTERN_RE = re.compile(r"^pattern:\s*(\w+)", re.M)
_PRIMARY_RE = re.compile(r"^\*\*(r\d+)\*\* — primary: `([a-z0-9_]+)`", re.M)
_HIT_RE = re.compile(r"^- `([a-z0-9_]+)`((?:\s*\[[a-zA-Z_\- ]+\])*)\s*×(\d+)", re.M)
_MOTIF_SECTION = "### Mechanism signatures (deterministic motifs over U)"

# Measured on M23_L2 same-config batches 3/5/6/7: tool:Bash#empty cone
# populations [8, 18, 9, 9].  A motif-population claim smaller than this swing
# is unresolved, not a finding.
_POPULATION_NOISE_NOTE = (
    "Population noise: on this bed, same-config batches swing a mechanism's "
    "population by ±5 on a 10–15 base (measured: Bash#empty across four "
    "unchanged-config batches = 8/18/9/9). A cross-round population move "
    "smaller than that is unresolved, not a finding."
)


def population_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


@dataclass
class PopulationReport:
    round_hint: str = ""
    n_digests: int = 0
    n_with_motifs: int = 0
    failing_any: Counter = field(default_factory=Counter)  # motif → tasks with any hit
    failing_primary: Counter = field(default_factory=Counter)
    passing_any: Counter = field(default_factory=Counter)
    failing_tasks: dict = field(default_factory=dict)  # motif → [task ids]
    m2_on_pass: list = field(default_factory=list)  # full task ids (P-15b)

    @property
    def has_data(self) -> bool:
        return self.n_with_motifs > 0


def build_population(digests_dir) -> PopulationReport:
    """One pass over the round's digests; counts are per TASK, not per hit."""
    digests_dir = Path(digests_dir)
    rep = PopulationReport(round_hint=digests_dir.parent.name)
    for md in sorted(digests_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        rep.n_digests += 1
        if _MOTIF_SECTION not in text:
            continue
        rep.n_with_motifs += 1
        section = text.split(_MOTIF_SECTION, 1)[1]
        # the motif section is the last graph section before Layer B
        section = section.split("## Pathology signals")[0]
        pat = _PATTERN_RE.search(text)
        failing = bool(pat and pat.group(1) != "ALL_PASS")
        tid = md.stem
        motifs = {m for m, _mods, _n in _HIT_RE.findall(section)}
        primaries = {p for _r, p in _PRIMARY_RE.findall(section)}
        if failing:
            for m in motifs:
                rep.failing_any[m] += 1
                rep.failing_tasks.setdefault(m, []).append(tid)
            for p in primaries:
                rep.failing_primary[p] += 1
        else:
            for m in motifs:
                rep.passing_any[m] += 1
            if "ungrounded_commit" in motifs:
                rep.m2_on_pass.append(tid)
    return rep


def render_population(rep: PopulationReport) -> str:
    L = [
        f"# Motif populations — {rep.round_hint} (graph-derived, deterministic)",
        "",
        f"Aggregated from {rep.n_with_motifs}/{rep.n_digests} digests carrying the "
        "graph-projected motif section. Counts are tasks, not hits. Node-level lift "
        "lives in `graph_evidence/facts.md`; this file is the motif plane.",
        "",
        "## Failing tasks",
        "",
        "| motif | tasks (any hit) | tasks (primary) |",
        "|---|---|---|",
    ]
    for m, c in rep.failing_any.most_common():
        L.append(f"| `{m}` | {c} | {rep.failing_primary.get(m, 0)} |")
    if not rep.failing_any:
        L.append("| (none fired) |  |  |")
    L += ["", "### Task lists (full ids — copy these, never truncate)", ""]
    for m, tids in sorted(rep.failing_tasks.items(), key=lambda kv: -len(kv[1])):
        L.append(f"- `{m}` ({len(tids)}): " + ", ".join(f"`{t}`" for t in tids))
    L += [
        "",
        "## Passing tasks (the luck/leak flag)",
        "",
        f"`ungrounded_commit` on a PASSING task means the answer was committed with no "
        f"page-grade evidence in any model call's context — a leak/luck candidate for "
        f"the decontamination ledger. This round: **{len(rep.m2_on_pass)}**.",
        "",
    ]
    if rep.m2_on_pass:
        L.append("- " + ", ".join(f"`{t}`" for t in rep.m2_on_pass))
        L.append("")
    L += ["## Reading discipline", "", _POPULATION_NOISE_NOTE, ""]
    return "\n".join(L)


def summary_section(rep: PopulationReport) -> str:
    top = ", ".join(f"`{m}`×{c}" for m, c in rep.failing_any.most_common(4)) or "(none)"
    return (
        "\n\n## Motif populations (M24 — graph-derived, deterministic)\n\n"
        f"Failing-task motif populations this round: {top}. "
        f"Luck/leak flags on passing tasks (`ungrounded_commit`-on-pass): "
        f"{len(rep.m2_on_pass)}. Full table with task lists: "
        f"`graph_evidence/population.md`. {_POPULATION_NOISE_NOTE}\n"
    )


# ── seam ──────────────────────────────────────────────────────────────────────

_ORIGINAL_AGGREGATE = None


def aggregate_digests_with_population(*, digests_dir, summary_path, cluster_path=None) -> dict:
    """Drop-in for ``preprocess.aggregate_digests``: official aggregation first,
    then the population artifacts — never at the expense of the official result."""
    _official = _ORIGINAL_AGGREGATE
    if _official is None:
        from harnessx.aegis.stages.preprocess import aggregate_digests as _official

    result = _official(digests_dir=digests_dir, summary_path=summary_path, cluster_path=cluster_path)
    try:
        rep = build_population(digests_dir)
        if rep.has_data:
            ge = Path(digests_dir).parent / "graph_evidence"
            ge.mkdir(parents=True, exist_ok=True)
            (ge / "population.md").write_text(render_population(rep), encoding="utf-8")
            sp = Path(summary_path)
            if sp.exists():
                sp.write_text(
                    sp.read_text(encoding="utf-8", errors="replace") + summary_section(rep),
                    encoding="utf-8",
                )
    except Exception:
        pass  # the official aggregate already happened — population is additive
    return result


@contextlib.contextmanager
def install_population():
    """Patch the module attribute the preprocess call site resolves per round."""
    global _ORIGINAL_AGGREGATE
    import harnessx.aegis.stages.preprocess as _pp

    original = _pp.aggregate_digests
    _ORIGINAL_AGGREGATE = original
    _pp.aggregate_digests = aggregate_digests_with_population
    try:
        yield
    finally:
        _pp.aggregate_digests = original
        _ORIGINAL_AGGREGATE = None
