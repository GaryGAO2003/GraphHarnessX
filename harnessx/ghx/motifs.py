# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Deterministic failure motifs over a projected rollout (M24 · P0).

A motif is a named, mechanically-checkable pattern over the joined
U↔trajectory view (:mod:`harnessx.ghx.projection`) — the controlled vocabulary
that replaces the Digester's free-text ``failure_mode`` (M22 measured: 510
failures, 493 distinct labels — the loop could not aggregate its own failures
across rounds).  Zero LLM: every predicate is a query, every hit carries
anchors.

v1 library — only what the graph can actually decide (review r2 shrank this:
"answer was in hand" and "evidence ignored" need content/semantics and belong
to the Digester, not here):

* **M1 empty_consumed** — a tool call returned an empty payload AND its result
  message flowed into the terminal model call.  The fabrication feed line.
* **M2 ungrounded_commit** — a FINAL ANSWER was emitted with no ok-grade
  non-snippet tool result reaching the terminal model call.  Parameterised, not
  binary: ``search_only=True`` means snippets did reach it (answers leak into
  snippets — the contamination audit's 10–12% — so the two shades must stay
  distinguishable).  Evaluated on PASSING tasks this same predicate is the
  luck/leak flag (M2-on-pass: measured 11/63 on one batch).
* **M3a budget_no_commit** — budget-wall exit with no FINAL ANSWER ever
  emitted.  The "answer in hand" refinement is Layer C's job.
* **M4 retry_loop** — ≥ ``retry_min`` consecutive identical (tool, args_sha)
  calls with nothing else between.

Primary label = the family closest to the outcome: no-commit beats
ungrounded-commit beats loop beats feed-line detail.  Co-occurring motifs stay
as annotations — populations may overlap, the primary may not.

Degradation contract: with no U (``rep.u_available`` False) flow columns are
unknown, so M1 abstains (it *requires* flow) and M2 falls back to
payload-presence ("a non-snippet ok result existed at all"), marking
``degraded=True`` in its detail.  An abstention is never a hit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .projection import ProjectionReport

_OK_GRADES = ("text", "multimodal")

DEFAULT_SNIPPET_TOOLS = frozenset({"WebSearch"})


@dataclass
class MotifHit:
    motif: str
    count: int
    detail: str
    anchors: list = field(default_factory=list)  # trajectory step anchors
    params: dict = field(default_factory=dict)


@dataclass
class MotifReport:
    task_id: str
    rollout: str
    hits: list = field(default_factory=list)  # list[MotifHit]
    primary: str = "none"

    @property
    def labels(self) -> list:
        return [h.motif for h in self.hits]

    def get(self, motif: str):
        for h in self.hits:
            if h.motif == motif:
                return h
        return None


def _anchor(rep: ProjectionReport, step: int) -> str:
    import os

    return f"trajectories/{os.path.basename(rep.traj_path)}#step_{step}"


def evaluate_motifs(
    rep: ProjectionReport,
    *,
    exit_reason: str | None = None,
    retry_min: int = 3,
    snippet_tools=DEFAULT_SNIPPET_TOOLS,
) -> MotifReport:
    """Run the v1 motif library over one projected rollout.

    ``exit_reason`` overrides the trajectory's own episode_end when the caller
    has the ledger row (task_history is authoritative for exits).
    """
    out = MotifReport(task_id=rep.task_id, rollout=rep.rollout)
    exit_r = exit_reason if exit_reason is not None else rep.exit_reason

    # M1 empty_consumed — requires flow truth; abstains without U.
    if rep.u_available:
        m1 = [
            c
            for c in rep.tool_calls
            if c.return_type == "empty" and c.ordinal >= 0 and c.consumed_by_final
        ]
        if m1:
            out.hits.append(
                MotifHit(
                    motif="empty_consumed",
                    count=len(m1),
                    detail=(
                        "empty payloads reached the terminal model call: "
                        + ", ".join(f"t{c.ordinal} {c.tool}" for c in m1)
                    ),
                    anchors=[_anchor(rep, c.step) for c in m1],
                )
            )

    # M2 ungrounded_commit — only meaningful when an answer was committed.
    if rep.final_answer_emitted:
        if rep.u_available:
            # Grounding = the result entered SOME model call's context.  Not
            # ``consumed_by_final``: sliding-window context management evicts
            # early evidence from the terminal call's list after the model has
            # already digested it into its own assistant messages — requiring
            # presence-at-final would flag those as ungrounded (measured: 21 vs
            # the lenient count's 11 M2-on-pass in one batch).  M1 keeps the
            # stricter final-call criterion because *its* claim is precisely
            # "this empty fed the answer-producing call".
            grounded_page = any(
                c.tool not in snippet_tools
                and c.return_type in _OK_GRADES
                and c.return_len > 0
                and c.reader_ordinals
                for c in rep.tool_calls
            )
            snippet_reached = any(
                c.tool in snippet_tools
                and c.return_type in _OK_GRADES
                and c.return_len > 0
                and c.reader_ordinals
                for c in rep.tool_calls
            )
            degraded = False
        else:
            grounded_page = any(
                c.tool not in snippet_tools and c.return_type in _OK_GRADES and c.return_len > 0
                for c in rep.tool_calls
            )
            snippet_reached = any(
                c.tool in snippet_tools and c.return_type in _OK_GRADES and c.return_len > 0
                for c in rep.tool_calls
            )
            degraded = True
        if not grounded_page:
            out.hits.append(
                MotifHit(
                    motif="ungrounded_commit",
                    count=1,
                    detail=(
                        "FINAL ANSWER with no ok non-snippet tool result "
                        + ("reaching the terminal model call" if not degraded else "anywhere in the rollout (no-U degraded)")
                        + ("; snippets present" if snippet_reached else "; no snippets either")
                    ),
                    anchors=[_anchor(rep, rep.final_answer_step or 0)],
                    params={"search_only": snippet_reached, "degraded": degraded},
                )
            )

    # M3a budget_no_commit
    if exit_r == "budget_exceeded" and not rep.final_answer_emitted:
        out.hits.append(
            MotifHit(
                motif="budget_no_commit",
                count=1,
                detail=f"exit=budget_exceeded after {rep.total_steps} steps, FINAL ANSWER never emitted",
                anchors=[_anchor(rep, (rep.total_steps or 1) - 1)],
            )
        )

    # M4 retry_loop — consecutive identical (tool, args_sha)
    runs: list[tuple[str, str, list[int]]] = []
    for c in rep.tool_calls:
        if runs and runs[-1][0] == c.tool and runs[-1][1] == c.args_sha:
            runs[-1][2].append(c.step)
        else:
            runs.append((c.tool, c.args_sha, [c.step]))
    loops = [(t, sha, steps) for t, sha, steps in runs if len(steps) >= retry_min]
    if loops:
        worst = max(loops, key=lambda r: len(r[2]))
        out.hits.append(
            MotifHit(
                motif="retry_loop",
                count=len(loops),
                detail=(
                    f"{len(loops)} run(s) of >={retry_min} identical calls; worst "
                    f"{worst[0]} args_sha={worst[1]} ×{len(worst[2])} at steps {worst[2]}"
                ),
                anchors=[_anchor(rep, worst[2][0])],
                params={"worst_len": len(worst[2])},
            )
        )

    labels = set(out.labels)
    if "budget_no_commit" in labels:
        out.primary = "budget_no_commit"
    elif "ungrounded_commit" in labels:
        out.primary = "ungrounded_commit"
    elif "retry_loop" in labels:
        out.primary = "retry_loop"
    elif "empty_consumed" in labels:
        out.primary = "empty_consumed"
    return out
