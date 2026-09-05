# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Integration test for the ``--noop-audit`` carry-to-ledger PLUMBING.

``tests/recipe/test_noop_audit.py`` already pins the pure selection logic
(``_select``) as a specification mirror — the block is inline in
``run_pilot``'s ~700-line async loop, so that file mirrors it rather than
importing it. This file does NOT re-test selection; it drives the REAL,
unmodified ``run_pilot()`` end to end and checks everything selection feeds
into: the carried task_history rows, the curves fresh/carried fields, the
zero-cost carry, and the "carried task never actually runs" invariant.

The only two monkeypatches are the sanctioned rollout/model-call edges:
``recipe.gaia_evolver.run_meta_aegis._run_task`` (the per-task rollout
executor — replaced with canned, instant results) and
``harnessx.aegis.AegisAgent.evolve`` (the meta-model call that plans the
next round's config — replaced with a function that returns the round's own
config path unchanged, i.e. an honest "noop" evolve outcome). Every other
line that runs — task loading (``_load_classified_tasks``), the scoped-audit
selection block, ``_ledger.append_task_history``, ``_save_curves``,
``prev_lite`` chaining — is real ``recipe/gaia_evolver/run_meta_aegis.py``
code, unmodified.

``RUNS_DIR`` is monkeypatched to a tmp path purely to keep test output out of
the real ``recipe/gaia_evolver/runs/`` tree (a live campaign is using that
tree concurrently) — that is a path redirect, not a logic stub.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from harnessx.aegis import AegisAgent
from harnessx.aegis.data.ledger import append_task_history, read_task_history
import recipe.gaia_evolver.run_meta_aegis as rma

# pyproject.toml sets asyncio_mode = "auto" — plain `async def test_...` is
# enough, no per-test/module asyncio mark needed (and one would misfire on
# the sync KNOWN_BUG repro test below).


TASK_IDS = [f"t{i}" for i in range(6)]

# Passed-bit per task at round -2, round -1 (seeded fixture rounds) and round
# 0 (the real, canned round this test drives). t2 / t3 flip somewhere in that
# 3-round window; the other four are constant — exactly the "volatile family
# vs. stable bed" split the scoped-audit selection is supposed to separate.
SEED_ROUNDS = {
    "t0": [True, True],
    "t1": [False, False],
    "t2": [True, True],
    "t3": [False, True],
    "t4": [True, True],
    "t5": [False, False],
}
ROUND0_PASSED = {"t0": True, "t1": False, "t2": False, "t3": True, "t4": True, "t5": False}
FLIPPY = {"t2", "t3"}  # the two tasks whose value differs somewhere across [-2, -1, 0]

AUDIT_N = 3  # floor: FLIPPY (2) + 1 deterministic fill


def _tasks_json(path: Path) -> None:
    blob = {
        "questions": [
            {
                "task_id": tid,
                "Question": f"Question for {tid}",
                "Level": 1,
                "answer": "42",
                "category": "Multi-hop (Multi-hop)",
                "Annotator_Metadata": {},
            }
            for tid in TASK_IDS
        ]
    }
    path.write_text(json.dumps(blob), encoding="utf-8")


def _seed_prior_rounds(run_dir: Path) -> None:
    """Two real prior rounds on disk, via the real ledger writer — the carry
    source a scoped round reads back via ``read_task_history``."""
    for i, rnd in enumerate((-2, -1)):
        append_task_history(
            run_dir,
            [
                {
                    "round": rnd,
                    "task_id": tid,
                    "level": "1",
                    "passed": SEED_ROUNDS[tid][i],
                    "steps": 4,
                    "cost_usd": 0.05,
                    "exit": "done",
                }
                for tid in TASK_IDS
            ],
        )


def _build_args(tmp_path: Path, run_tag: str):
    tasks_path = tmp_path / f"{run_tag}_tasks.json"
    _tasks_json(tasks_path)
    parser = rma._build_argparser()
    return parser.parse_args(
        [
            "--tasks", str(tasks_path),
            "--run-tag", run_tag,
            "--num-rounds", "2",
            "--max-tasks", "0",
            "--noop-audit", str(AUDIT_N),
            "--concurrency", "6",
        ]
    )


def _make_fake_run_task(executed: list):
    async def _fake_run_task(harness, task, label, *, pipeline_eval=None, harness_config=None):
        executed.append((label, task.task_id))
        round_idx = int(label.rsplit("R", 1)[1].split("/")[0])
        passed = ROUND0_PASSED[task.task_id] if round_idx == 0 else True
        # Steps deliberately differ by round (2 vs 9) so a carried row's
        # "steps" field can be told apart from "a fresh R1 rollout" — see
        # the KNOWN BUG test below.
        steps = 2 if round_idx == 0 else 9
        return {
            "task_id": task.task_id,
            "level": task.level,
            "question": (task.question or "")[:150],
            "expected": task.final_answer,
            "output": "canned",
            "final_output": "canned",
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": "canned",
            "steps": steps,
            "total_tokens": 100,
            "cost_usd": 0.02,
            "elapsed_s": 0.0,
            "exit_reason": "done",
            "_result": None,  # skips trajectory building — _run_one only touches it `if raw is not None`
        }

    return _fake_run_task


async def _fake_evolve(self, current_config, trajectories_dir, output_dir, *,
                        pass_flags_by_task=None, round_n=1, raw_sessions_dir=None, **kwargs):
    """Honest 'noop' outcome: hand back the same file unchanged so
    ``round_config_path.read_bytes() == new_yaml_path.read_bytes()`` — no
    fabricated diff logic, just the same real Path round_pilot already has."""
    return Path(current_config)


async def _run_one_campaign(tmp_path: Path, monkeypatch, run_tag: str) -> tuple[Path, list]:
    monkeypatch.setattr(rma, "RUNS_DIR", tmp_path / "runs")
    executed: list = []
    monkeypatch.setattr(rma, "_run_task", _make_fake_run_task(executed))
    monkeypatch.setattr(AegisAgent, "evolve", _fake_evolve)

    run_dir = tmp_path / "runs" / run_tag
    _seed_prior_rounds(run_dir)

    args = _build_args(tmp_path, run_tag)
    await rma.run_pilot(args)
    return run_dir, executed


def _round1_partition(executed: list) -> tuple[set, set]:
    r1_executed = {tid for label, tid in executed if label == "aegis/R1"}
    return r1_executed


async def test_noop_audit_carry_plumbing(tmp_path: Path, monkeypatch):
    run_dir, executed = await _run_one_campaign(tmp_path, monkeypatch, "carryA")

    r0_executed = {tid for label, tid in executed if label == "aegis/R0"}
    r1_executed = {tid for label, tid in executed if label == "aegis/R1"}

    # Sanity: round 0 is baseline, always the full bed.
    assert r0_executed == set(TASK_IDS)

    history = read_task_history(run_dir)
    r1_rows = {r["task_id"]: r for r in history if r["round"] == 1}
    assert set(r1_rows) == set(TASK_IDS)  # one row per task, fresh and carried alike

    # Partition round 1 by the REAL call log — the ground truth for "did this
    # task run" — and cross-check it against row["carried"] below. The vendored
    # ledger writer still drops that key (see the KNOWN BUG pin test), but the
    # pilot now re-attaches it on disk right after the append, so the two views
    # must agree.
    r1_carried_ids = set(TASK_IDS) - r1_executed
    flagged_carried = {tid for tid, row in r1_rows.items() if row.get("carried")}
    assert flagged_carried == r1_carried_ids, (
        "on-disk carried flags disagree with the execution call log: "
        f"flagged={sorted(flagged_carried)} vs not-executed={sorted(r1_carried_ids)}"
    )

    # ── core assertion: a carried task must never actually run ──────────────
    assert r1_executed.isdisjoint(r1_carried_ids), (
        f"carried task(s) {r1_executed & r1_carried_ids} were executed in R1 — "
        "scoping did not actually skip them"
    )

    # ── flip family is always in the audit, never carried ───────────────────
    assert FLIPPY <= r1_executed
    assert FLIPPY.isdisjoint(r1_carried_ids)

    # ── deterministic fill to N: floor reached, not exceeded (flippy=2 < N=3) ─
    assert len(r1_executed) == AUDIT_N
    assert len(r1_carried_ids) == len(TASK_IDS) - AUDIT_N

    # ── carried rows: score copied from the most recent real measurement
    #    (round 0, since nothing ran between round 0 and round 1); a carried
    #    row contributes NO cost and NO steps — it ran nothing, and steps=2
    #    leaking through (round 0's own count) is the spec mismatch this
    #    block used to pin before the pilot zeroed it at the carry source.
    for tid in r1_carried_ids:
        row = r1_rows[tid]
        assert row["passed"] == ROUND0_PASSED[tid], (tid, row, ROUND0_PASSED[tid])
        assert row["cost_usd"] == 0.0
        assert row["steps"] == 0, (tid, row["steps"])
        assert row["carried"] is True  # re-attached on disk by the pilot

    # ── curves: this round carries fresh_tasks/carried_tasks; round 0 (full
    #    bed, no carried_lite) must NOT — that key is conditional on carrying
    #    having actually happened. Unlike task_history rows, curve_point is
    #    built and saved by run_meta_aegis.py itself (_save_curves), never
    #    passing through the ledger's fixed-schema row builder, so it is not
    #    affected by the dropped-"carried"-key bug below.
    curves = json.loads((run_dir / "curves.json").read_text(encoding="utf-8"))
    curve_r0, curve_r1 = curves[0], curves[1]
    assert "fresh_tasks" not in curve_r0 and "carried_tasks" not in curve_r0
    assert curve_r1["fresh_tasks"] == AUDIT_N
    assert curve_r1["carried_tasks"] == len(TASK_IDS) - AUDIT_N

    # ── round-level cost/token/step accounting excludes carried tasks
    #    entirely (they never enter `records`, the flattened list these sums
    #    are drawn from) — the round's reported spend is exactly what the
    #    AUDIT_N fresh rollouts cost, not the full bed.
    assert curve_r1["cost_usd"] == pytest.approx(0.02 * AUDIT_N)
    assert curve_r1["total_tokens"] == 100 * AUDIT_N
    assert curve_r1["total_steps"] == 9 * AUDIT_N


def test_KNOWN_BUG_append_task_history_drops_the_carried_flag(tmp_path: Path):
    """Not a production fix (a live campaign is running against this repo) —
    a minimal, direct repro of a real defect found while writing the test
    above.

    ``recipe/gaia_evolver/run_meta_aegis.py`` (~line 1172) builds each
    task_history row with ``**({"carried": True} if first.get("carried")
    else {})``, and its own ``--noop-audit`` help text promises tasks are
    "marked 'carried' ... in task_history". But
    ``harnessx/aegis/data/ledger.py``'s ``append_task_history`` rebuilds every
    row from a FIXED field set (round/task_id/level/passed/passed_flags/k/
    exit/steps/cost_usd/final_output_len/tools_used — see its dict literal,
    and the equally carried-less ``TaskRecord`` dataclass) that never
    includes "carried". The key is silently dropped on write; no row in
    task_history.jsonl EVER carries a "carried" marker, regardless of what
    the caller passed in.
    """
    append_task_history(tmp_path, [{"task_id": "x", "round": 1, "passed": True, "carried": True}])
    (row,) = read_task_history(tmp_path)
    assert "carried" not in row  # documents current behavior: the promised marker never lands


async def test_noop_audit_selection_is_deterministic_across_independent_runs(tmp_path, monkeypatch):
    """Same round index, same history, same audit_n, run through two
    completely independent ``run_pilot()`` invocations — the audit selection
    (flip family + hash fill) must land on the identical task set both times.
    This is the real-code counterpart to test_noop_audit.py's ``run1 ==
    run2`` check on the ``_select`` mirror."""
    _, executed_a = await _run_one_campaign(tmp_path, monkeypatch, "detA")
    _, executed_b = await _run_one_campaign(tmp_path, monkeypatch, "detB")

    r1_a = {tid for label, tid in executed_a if label == "aegis/R1"}
    r1_b = {tid for label, tid in executed_b if label == "aegis/R1"}
    assert r1_a == r1_b
    assert len(r1_a) == AUDIT_N


async def test_noop_audit_never_engages_when_evolve_status_is_ok(tmp_path, monkeypatch):
    """A ship round (evolve_status='ok', i.e. the config actually changed)
    always runs the full bed — the scoped path must not intervene even
    though --noop-audit is set."""
    monkeypatch.setattr(rma, "RUNS_DIR", tmp_path / "runs")
    executed: list = []
    monkeypatch.setattr(rma, "_run_task", _make_fake_run_task(executed))

    run_tag = "shipped"
    run_dir = tmp_path / "runs" / run_tag
    _seed_prior_rounds(run_dir)

    async def _changed_evolve(self, current_config, trajectories_dir, output_dir, *,
                               pass_flags_by_task=None, round_n=1, raw_sessions_dir=None, **kwargs):
        # A real diff: write a byte-different (but still valid) config so
        # round_pilot's own byte-comparison honestly sees a change.
        from harnessx.core.harness import HarnessConfig

        cfg = HarnessConfig.from_yaml_file(str(current_config))
        out_path = Path(output_dir) / "config.yaml"
        cfg.to_yaml_file(out_path)
        # Touch a byte so it's provably not identical to the parent file.
        out_path.write_text(out_path.read_text(encoding="utf-8") + "# shipped\n", encoding="utf-8")
        return out_path

    monkeypatch.setattr(AegisAgent, "evolve", _changed_evolve)

    args = _build_args(tmp_path, run_tag)
    await rma.run_pilot(args)

    r1_executed = {tid for label, tid in executed if label == "aegis/R1"}
    assert r1_executed == set(TASK_IDS)  # full bed, nothing carried

    history = read_task_history(run_dir)
    r1_rows = [r for r in history if r["round"] == 1]
    assert all(not r.get("carried") for r in r1_rows)

    curves = json.loads((run_dir / "curves.json").read_text(encoding="utf-8"))
    assert curves[1]["evolve_status"] == "ok"
    assert "carried_tasks" not in curves[1]
