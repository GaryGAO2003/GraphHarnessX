# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The AEGIS pilot used to pay for a verdict and then drop it.

``run_meta.py:845`` appends ``LLMJudgeProcessor`` to every round's config, so it runs
on each rollout's ``task_end`` and writes a structured verdict — cause / missing /
lesson / missing_capability — into its own sink. Nothing in ``run_meta.py`` ever read
that sink, while ``run.py`` (the same pilot family) harvests it at 1097-1110. The
call was billed and the answer discarded.

These pin the harvest and the byte-identity of the no-judge case.
"""

from __future__ import annotations

import pytest

import recipe.gaia_evolver.run_meta as _rm

_VERDICT = {
    "verdict": "wrong_answer",
    "confidence": 0.9,
    "cause": "fetched page returned empty body",
    "missing": "a working content fetch",
    "lesson": "verify the fetch returned bytes before answering",
    # The real shape, per llm_judge._empty_missing_capability / the judge prompt's
    # schema: a presence flag, a generic tool-shape summary, and the trace steps that
    # show the gap. evidence_steps is what lets GHX locate the gap on graph nodes.
    "missing_capability": {
        "present": True,
        "summary": "A client for this service with backoff and an alt-endpoint fallback.",
        "evidence_steps": [8, 12],
    },
}


def test_frontmatter_carries_the_verdict_when_there_is_one():
    fm = _rm._render_trajectory_frontmatter(
        {
            "task_id": "t1",
            "exit_reason": "done",
            "steps": 3,
            "cost_usd": 0.5,
            "passed": False,
            "score": 0.0,
            "llm_judge_verdict": _VERDICT,
            "extracted_answer": "42",
        }
    )
    assert "llm_judge_verdict:" in fm
    assert "missing_capability" in fm  # the field the Planner reconstructs by hand
    assert "extracted_answer:" in fm


def test_frontmatter_is_unchanged_when_the_judge_produced_nothing():
    """A run without the judge — or with it failing — must render exactly as before.

    The fields are appended only when non-empty precisely so that turning the judge
    off, or having it error, does not silently alter the official output shape.
    """
    base = {
        "task_id": "t1",
        "exit_reason": "done",
        "steps": 3,
        "cost_usd": 0.5,
        "passed": False,
        "score": 0.0,
    }
    without = _rm._render_trajectory_frontmatter(base)
    empty = _rm._render_trajectory_frontmatter(
        {**base, "llm_judge_verdict": {}, "extracted_answer": ""}
    )
    assert without == empty
    assert "llm_judge_verdict" not in without
    assert "extracted_answer" not in without


def test_the_launcher_reads_missing_capability_back_out_of_frontmatter(tmp_path):
    """The round trip: run_meta writes the verdict, the GHX resolver reads it.

    These are two files apart and the format between them is a single frontmatter
    line of JSON. If either side changes shape the absent-capability table silently
    empties, which reads as "no gaps" rather than "no data" — the failure mode this
    codebase keeps paying for.
    """
    import json

    from recipe.gaia_evolver.run_meta_aegis_ghx import _make_capability_resolver

    traj = tmp_path / "R0" / "trajectories"
    traj.mkdir(parents=True)
    (traj / "t1_r0.md").write_text(
        _rm._render_trajectory_frontmatter(
            {
                "task_id": "t1",
                "exit_reason": "done",
                "steps": 3,
                "cost_usd": 0.5,
                "passed": False,
                "score": 0.0,
                "llm_judge_verdict": _VERDICT,
            }
        ),
        encoding="utf-8",
    )

    resolve = _make_capability_resolver(tmp_path, rollout_round=0)
    mc = resolve("t1")
    assert mc == _VERDICT["missing_capability"]
    assert json.dumps(mc)  # round-trips as JSON, which is what the writer emitted


def test_a_task_with_no_verdict_resolves_to_no_claim(tmp_path):
    """Absent must read as 'said nothing', which renders no row — not as 'no gap'."""
    from recipe.gaia_evolver.run_meta_aegis_ghx import _make_capability_resolver

    traj = tmp_path / "R0" / "trajectories"
    traj.mkdir(parents=True)
    (traj / "t1_r0.md").write_text(
        _rm._render_trajectory_frontmatter(
            {"task_id": "t1", "exit_reason": "done", "steps": 1, "cost_usd": 0.1}
        ),
        encoding="utf-8",
    )
    assert _make_capability_resolver(tmp_path, rollout_round=0)("t1") == {}
    assert _make_capability_resolver(tmp_path, rollout_round=0)("nosuchtask") == {}


def test_the_resolver_reads_the_rollout_round_not_the_round_being_planned(tmp_path):
    """Off by one here is silent, so it gets its own test.

    R{n}/trajectories holds round n's OWN rollouts — the same task reads
    exit_reason=done under R0 and budget_exceeded under R1. Evidence for round_n is
    materialised about round_n-1's rollouts, so the resolver must read R{n-1}. Point
    it one round forward and the glob matches nothing, every task resolves to {}, and
    facts.md renders no absent-capability section — which reads as "no gaps found"
    rather than "wrong folder".
    """
    from recipe.gaia_evolver.run_meta_aegis_ghx import _make_capability_resolver

    def _write(round_dir: str, summary: str):
        d = tmp_path / round_dir / "trajectories"
        d.mkdir(parents=True, exist_ok=True)
        (d / "t1_r0.md").write_text(
            _rm._render_trajectory_frontmatter(
                {
                    "task_id": "t1",
                    "exit_reason": "done",
                    "steps": 1,
                    "cost_usd": 0.1,
                    "llm_judge_verdict": {
                        "missing_capability": {
                            "present": True,
                            "summary": summary,
                            "evidence_steps": [1],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    _write("R0", "the rollout round's gap")
    _write("R1", "the planned round's gap")

    assert _make_capability_resolver(tmp_path, rollout_round=0)("t1")["summary"] == (
        "the rollout round's gap"
    )
    assert _make_capability_resolver(tmp_path, rollout_round=1)("t1")["summary"] == (
        "the planned round's gap"
    )


@pytest.mark.parametrize("filename", ["t1.md", "t1_r0.md"])
def test_both_pass_k_namings_resolve(tmp_path, filename):
    """k=1 writes ``<task>.md``; k=2 writes ``<task>_r0.md`` / ``_r1.md``.

    ``_write_task_trajectory`` writes ``{task.task_id}.md`` and the pass-k caller bakes
    the rollout index into task_id itself, so the filename shape depends on k. Globbing
    only the suffixed form matched nothing under k=1 — the configuration this campaign
    runs — and every task resolved to {} with no error raised, no log line, and an
    absent-capability section that simply never appeared.
    """
    from recipe.gaia_evolver.run_meta_aegis_ghx import _make_capability_resolver

    d = tmp_path / "R0" / "trajectories"
    d.mkdir(parents=True)
    (d / filename).write_text(
        _rm._render_trajectory_frontmatter(
            {
                "task_id": "t1",
                "exit_reason": "done",
                "steps": 1,
                "cost_usd": 0.1,
                "llm_judge_verdict": _VERDICT,
            }
        ),
        encoding="utf-8",
    )
    assert _make_capability_resolver(tmp_path, rollout_round=0)("t1") == (
        _VERDICT["missing_capability"]
    )
