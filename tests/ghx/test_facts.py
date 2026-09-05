# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""G1 test 2 — facts.md shared-node section and the honest edit-history line.

The shared-node section is a cross-task fact: a static node in the cone of MORE
THAN ONE failing task. Present when >=2 tasks share a node; absent (no header,
not an empty header) when the cones are disjoint. The edit-history line is the
honest 'not yet recorded' text — the distinction between unknown and never that
has bitten this codebase repeatedly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harnessx.ghx.evidence_files import materialize_graph_evidence
from harnessx.graph.causal import DATA
from harnessx.graph.types import unfolded_id
from harnessx.graph.unfold import UnfoldedEdge, UnfoldedGraph, UnfoldedNode


def _linear_u(run_id: str, bases: list[tuple[str, str, int]]) -> UnfoldedGraph:
    """A DATA chain t0->t1->...->tN; the terminal-anchored cone is every node, so the
    cone's static-node set is exactly the ``bases`` provided.

    The chain is data, not control: since v6 M13 the cone follows data ancestry, so a
    control-only chain would collapse to the anchor and this fixture would silently stop
    testing anything about sharing."""
    nodes = [
        UnfoldedNode(
            id=unfolded_id(base, i),
            static_node_id=base,
            graphed=True,
            hook=hook,
            step=step,
            ordinal=i,
            label=base,
        )
        for i, (base, hook, step) in enumerate(bases)
    ]
    edges = [
        UnfoldedEdge(
            source=nodes[i].id,
            target=nodes[i + 1].id,
            edge_type=DATA,
            metadata={"slot_key": f"k{i}"},
        )
        for i in range(len(nodes) - 1)
    ]
    return UnfoldedGraph(run_id=run_id, session_id="s", nodes=nodes, edges=edges)


# The section must always distinguish "nothing has been tried on this node" from
# "we do not track what has been tried" — a run with no earlier rounds says the
# former (M25), a run whose history could not be built says the latter.
_EDIT_HISTORY_MARK = "nothing tried yet"


def test_shared_section_present_when_two_tasks_share_a_node(tmp_path: Path):
    run_dir = tmp_path / "run"

    def resolver(task: str):
        if task == "alpha":
            return _linear_u("a", [("Sys", "before_model", 0), ("tool:Bash", "tool", 1), ("End", "task_end", 2)])
        if task == "beta":
            return _linear_u("b", [("SysB", "before_model", 0), ("tool:Bash", "tool", 1), ("EndB", "task_end", 2)])
        return None

    summary = materialize_graph_evidence(run_dir, 1, ["alpha", "beta"], resolver)
    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")

    # Only tool:Bash is shared; Sys/End vs SysB/EndB are task-local.
    assert summary["shared_nodes"] == {"tool:Bash": ["alpha", "beta"]}
    assert "## Shared cone nodes" in facts
    assert "`tool:Bash` — tasks: alpha, beta" in facts

    # Edit-history line is always present and honest.
    assert "## Node edit history" in facts
    assert _EDIT_HISTORY_MARK in facts


def test_lift_sinks_the_always_on_node_that_frequency_ranks_first(tmp_path: Path):
    """A node in EVERY cone on both sides explains nothing, however often it appears.

    This is the defect the old facts.md invited: it reported failure frequency, so the
    most common node read as the most important one — and the most common node is the
    universal stack, which is equally common when the task succeeds. `stack` here is in
    100% of failures AND 100% of passes (lift 1.0); `tool:Browser` is in half the failures
    and none of the passes. Frequency ranks `stack` first; lift ranks it last.
    """
    run_dir = tmp_path / "run"
    chain = lambda *b: _linear_u("x", list(b))  # noqa: E731

    def resolver(task: str):
        if task in ("f1", "f2"):
            return chain(("stack", "before_model", 0), ("tool:Browser", "tool", 1), ("End", "task_end", 2))
        # f3 and every passing control: the stack is there too, Browser never is
        return chain(("stack", "before_model", 0), ("tool:Bash", "tool", 1), ("End", "task_end", 2))

    summary = materialize_graph_evidence(
        run_dir, 1, ["f1", "f2", "f3"], resolver, passed_task_ids=["p1", "p2", "p3", "p4"]
    )
    lift = summary["lift"]

    assert summary["control_tasks"] == 4
    assert lift["stack"]["fail_rate"] == 1.0 and lift["stack"]["pass_rate"] == 1.0
    assert lift["stack"]["lift"] == 1.0, "always-on node carries no information"
    # Bash: a third of the failures, ALL the passes — lift below 1.0, i.e. its presence
    # tracks success. The old frequency view could not express this at all.
    assert lift["tool:Bash"]["lift"] == pytest.approx(0.333, abs=1e-3)
    assert lift["tool:Browser"]["lift"] is None, "never appears in a pass — undefined, not infinite"

    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "| lift |" in facts
    assert "control: 4 passing task(s)" in facts
    # Browser (the discriminating one) is ranked above the always-on stack.
    assert facts.index("`tool:Browser`") < facts.index("`stack`")


def test_no_control_arm_says_lift_was_not_measured(tmp_path: Path):
    """Without passing cones there is no lift. Say that, rather than let the frequency
    list read as if it had been checked against a control."""
    run_dir = tmp_path / "run"

    def resolver(task: str):
        return _linear_u("x", [("stack", "before_model", 0), ("tool:Bash", "tool", 1), ("End", "task_end", 2)])

    summary = materialize_graph_evidence(run_dir, 1, ["f1", "f2"], resolver)
    assert summary["control_tasks"] == 0
    assert all(v["pass_rate"] == 0.0 and v["lift"] is None for v in summary["lift"].values())

    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "lift is not computed" in facts
    assert "unmeasured, not 1.0" in facts
    assert "| lift |" not in facts


def test_shared_section_absent_when_cones_disjoint(tmp_path: Path):
    run_dir = tmp_path / "run"

    def resolver(task: str):
        if task == "alpha":
            return _linear_u("a", [("SysA", "before_model", 0), ("tool:Read", "tool", 1), ("EndA", "task_end", 2)])
        if task == "beta":
            return _linear_u("b", [("SysB", "before_model", 0), ("tool:Write", "tool", 1), ("EndB", "task_end", 2)])
        return None

    summary = materialize_graph_evidence(run_dir, 1, ["alpha", "beta"], resolver)
    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")

    # No node is shared: the section header is ABSENT, not an empty header.
    assert summary["shared_nodes"] == {}
    assert "## Shared cone nodes" not in facts

    # The edit-history line is still there — honesty does not depend on sharing.
    assert "## Node edit history" in facts
    assert _EDIT_HISTORY_MARK in facts


def test_survival_column_says_how_often_a_high_lift_node_still_wins(tmp_path: Path):
    """The column that exists because lift alone cost a campaign seven tasks.

    `M13_pro_meta_103x3` R3 shipped a hard abort on `proc:loop_detection_processor`
    because it topped the table at lift 4.95. It was the right node — failures really
    do concentrate there — and the ship still dropped the score 7 tasks below a
    same-config envelope of 67/71/69. The reason is not in the lift column: of the
    tasks where that node appeared, 29% passed anyway. Aborting on it threw those away.

    Lift compares two rates over DIFFERENT denominators, so the share that survives
    cannot be read off the table without the task counts. Printing it is the whole
    point of the column.

    Here: `hot` is in 2 of 2 failing cones and 1 of 4 passing ones — lift 4.0, top of
    the table, yet one of the three tasks carrying it succeeded.
    """
    run_dir = tmp_path / "run"
    chain = lambda *b: _linear_u("x", list(b))  # noqa: E731

    def resolver(task: str):
        if task in ("f1", "f2"):
            return chain(("stack", "before_model", 0), ("hot", "tool", 1), ("End", "task_end", 2))
        if task == "p1":  # one passing task carries the hot node too
            return chain(("stack", "before_model", 0), ("hot", "tool", 1), ("End", "task_end", 2))
        return chain(("stack", "before_model", 0), ("End", "task_end", 1))

    summary = materialize_graph_evidence(
        run_dir, 1, ["f1", "f2"], resolver, passed_task_ids=["p1", "p2", "p3", "p4"]
    )
    assert summary["lift"]["hot"]["lift"] == pytest.approx(4.0)

    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "| still passes |" in facts
    hot_row = next(ln for ln in facts.splitlines() if ln.startswith("| `hot`"))
    # 2 failing + 1 passing carry it -> 1/3 survive. Not derivable from 100%/25%.
    assert "| 33% |" in hot_row, hot_row
    # The always-on node is present in every task, so its survival is the base rate.
    stack_row = next(ln for ln in facts.splitlines() if ln.startswith("| `stack`"))
    assert "| 67% |" in stack_row, stack_row
    # And the table says out loud what the column is for.
    assert "removes, gates, aborts on, or replaces" in facts


def test_survival_column_is_absent_without_a_control_arm(tmp_path: Path):
    """No passing arm means no denominator; the section must not invent one."""
    run_dir = tmp_path / "run"
    chain = lambda *b: _linear_u("x", list(b))  # noqa: E731
    summary = materialize_graph_evidence(
        run_dir, 1, ["f1", "f2"],
        lambda t: chain(("stack", "before_model", 0), ("hot", "tool", 1), ("End", "task_end", 2)),
    )
    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "still passes" not in facts


def _u_with_steps(run_id: str, bases_steps):
    """A DATA chain of tool-hook nodes.

    ``evidence_steps`` index the judge's rendered trace, which counts tool results
    from 1 — so position in this list, not the step number, is what resolves. The
    step numbers are kept deliberately unequal to the positions so a resolver that
    goes back to matching ``node.step`` fails these tests instead of passing by
    coincidence.
    """
    return _linear_u(run_id, [(b, "tool", s) for b, s in bases_steps])


def test_absent_capabilities_are_grouped_by_where_they_bit_not_by_wording(tmp_path):
    """The half the cone structurally cannot see, and the reason it is graph-native.

    A capability that does not exist is never invoked, so it has no node and lift can
    never rank it — the lift table ranks what ran. The judge's missing_capability
    carries what was absent, and its evidence_steps land on real invocations, so the
    gap can be located in the graph rather than only described in prose.

    Grouping by that location is the point. `f1` and `f2` word their gap completely
    differently and are one group because both bit at `tool:Bash`; `f3` uses wording
    close to `f1`'s and is a separate group because it bit somewhere else. Clustering
    the text would have got both of those backwards.
    """
    run_dir = tmp_path / "run"

    # Step numbers deliberately differ from positions: evidence_steps index the
    # judge's tool-result count, so position 1 is the first tool node whatever step
    # it ran at. A resolver that goes back to matching node.step fails here.
    us = {
        "f1": _u_with_steps("a", [("tool:Bash", 5), ("End", 9)]),
        "f2": _u_with_steps("b", [("tool:Bash", 3), ("End", 8)]),
        "f3": _u_with_steps("c", [("tool:Browser", 4), ("End", 7)]),
        "p1": _u_with_steps("d", [("tool:Bash", 2), ("End", 6)]),
    }
    caps = {
        "f1": {"present": True, "summary": "a working in-process compute path", "evidence_steps": [1]},
        "f2": {"present": True, "summary": "some way to run python that isn't a broken shell", "evidence_steps": [1]},
        "f3": {"present": True, "summary": "a working in-process compute path", "evidence_steps": [1]},
        "p1": {"present": False, "summary": "", "evidence_steps": []},
    }

    summary = materialize_graph_evidence(
        run_dir, 1, ["f1", "f2", "f3"], lambda t: us.get(t),
        passed_task_ids=["p1"], capability_resolver=lambda t: caps.get(t),
    )

    gaps = {g["nodes"]: g for g in summary["capability_gaps"]}
    assert set(gaps) == {("tool:Bash",), ("tool:Browser",)}
    assert sorted(gaps[("tool:Bash",)]["fail"]) == ["f1", "f2"], "different words, same place = one gap"
    assert gaps[("tool:Browser",)]["fail"] == ["f3"], "same words, different place = separate gap"
    # A passing task that reports no gap is not counted against either.
    assert gaps[("tool:Bash",)]["pass"] == []

    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")
    assert "## Absent capabilities" in facts
    assert "`tool:Bash`" in facts
    assert "2/3" in facts  # two of three failing tasks bit there


def test_a_gap_the_winners_also_report_is_visible_as_control(tmp_path):
    """A capability the passing runs also lacked did not separate them from the losers."""
    run_dir = tmp_path / "run"
    us = {t: _u_with_steps(t, [("tool:Bash", 5), ("End", 9)]) for t in ("f1", "p1", "p2")}
    caps = {
        t: {"present": True, "summary": "a compute path", "evidence_steps": [1]}
        for t in ("f1", "p1", "p2")
    }
    summary = materialize_graph_evidence(
        run_dir, 1, ["f1"], lambda t: us.get(t),
        passed_task_ids=["p1", "p2"], capability_resolver=lambda t: caps.get(t),
    )
    g = summary["capability_gaps"][0]
    assert len(g["fail"]) == 1 and len(g["pass"]) == 2
    assert "1/1 | 2/2" in Path(summary["facts_path"]).read_text(encoding="utf-8")


def test_the_section_is_absent_without_a_capability_resolver(tmp_path):
    """No verdicts wired means no section — never an empty header."""
    run_dir = tmp_path / "run"
    chain = lambda *b: _linear_u("x", list(b))  # noqa: E731
    summary = materialize_graph_evidence(
        run_dir, 1, ["f1", "f2"],
        lambda t: chain(("stack", "before_model", 0), ("hot", "tool", 1), ("End", "task_end", 2)),
        passed_task_ids=["p1"],
    )
    assert summary["capability_gaps"] == []
    assert "Absent capabilities" not in Path(summary["facts_path"]).read_text(encoding="utf-8")


def test_evidence_steps_index_tool_results_not_harness_steps(tmp_path):
    """The coordinate system the judge actually writes in.

    ``llm_judge._render_trace_from_event`` numbers the trace it shows the judge by
    counting ``role == "tool"`` messages from 1. A harness step may fire several tools
    or none, so the two counters diverge: the first production render had a 20-step run
    whose judge cited steps 22 and 23, matched nothing against ``node.step``, and put a
    real gap in the unlocated bucket — which reads as "the graph could not place this"
    when the two sides were simply counting different things.

    Here the two tool nodes ran at harness steps 40 and 41. Position 2 must resolve to
    the second tool node, and step-number 40 must resolve to nothing.
    """
    run_dir = tmp_path / "run"
    u = _u_with_steps("a", [("tool:Read", 40), ("tool:Bash", 41)])

    def gaps_for(evidence_steps):
        s = materialize_graph_evidence(
            run_dir, 1, ["f1"], lambda t: u, passed_task_ids=[],
            capability_resolver=lambda t: {
                "present": True, "summary": "x", "evidence_steps": evidence_steps
            },
        )
        return s["capability_gaps"][0]["nodes"]

    assert gaps_for([2]) == ("tool:Bash",), "position 2 is the second tool result"
    assert gaps_for([1, 2]) == ("tool:Bash", "tool:Read")
    # Harness step numbers must NOT resolve — they are a different counter, and
    # clamping them onto a node would attribute the gap to whatever happened to sit
    # at that index.
    assert gaps_for([40, 41]) == (), "out-of-range indices stay unresolved, never clamped"


def test_at_risk_states_the_price_as_a_count_not_a_share(tmp_path):
    """A percentage reads as a caveat and gets quoted past; a count reads as a price.

    Twice a candidate has targeted the strongest failure signal and lost more passing
    tasks than it recovered — a hard abort on a detector with 29% survival cost 7
    tasks, and swapping the Bash backend at 60% survival cost 13 ALL_PASS to ALL_FAIL
    flips. The second candidate quoted the survival share in its own manifest and did
    it anyway, so the share alone demonstrably does not carry.

    `at risk` is the same quantity in tasks: how many currently-passing runs an edit to
    this node would gamble.
    """
    run_dir = tmp_path / "run"
    chain = lambda *b: _linear_u("x", list(b))  # noqa: E731

    def resolver(task: str):
        if task.startswith("f"):
            return chain(("stack", "before_model", 0), ("hot", "tool", 1), ("End", "task_end", 2))
        # three of the four passing tasks also carry `hot` — that is the price
        if task in ("p1", "p2", "p3"):
            return chain(("stack", "before_model", 0), ("hot", "tool", 1), ("End", "task_end", 2))
        return chain(("stack", "before_model", 0), ("End", "task_end", 1))

    summary = materialize_graph_evidence(
        run_dir, 1, ["f1", "f2"], resolver, passed_task_ids=["p1", "p2", "p3", "p4"]
    )
    facts = Path(summary["facts_path"]).read_text(encoding="utf-8")

    assert "| at risk |" in facts
    hot = next(ln for ln in facts.splitlines() if ln.startswith("| `hot`"))
    assert hot.rstrip().endswith("**3** |"), hot  # the three passing tasks that use it
    assert "reads as a price" in facts, "the column must say what it is for"
