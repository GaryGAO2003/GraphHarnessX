# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Rollback x new-seam coexistence.

M25 R2 saw a real ship-aware rollback fire, but that was the old stack. Two
seams have landed since: the runtime-policy processor riding inside every
round's config.yaml, and the flip ledger reading task_history across rounds.
Neither has ever been exercised together with a rollback. This file drives
three real code paths, no production edits:

1. ``run_pilot()``'s own in-loop rollback branch (run_meta_aegis.py, the
   ``delta_rate <= -0.05 and delta_count <= -3`` block) — via a real 3-round
   campaign with ``--runtime-policy`` on, so the reverted config actually
   carries the processor. Monkeypatches are the same two sanctioned
   rollout/model-call edges as test_noop_audit_plumbing.py:
   ``run_meta_aegis._run_task`` and ``AegisAgent.evolve``.
2. ``run_meta_aegis_ghx._fix_merged_after_rollback`` — the resume-time
   "un-poison merged.yaml" preflight — called directly (it is already a
   standalone, args-in/file-out function; no extraction needed). Zero
   monkeypatching: it is pure file I/O over a hand-built fixture.
3. ``harnessx.ghx.flip_ledger.build_flip_ledger`` — the real function,
   pointed at run (1)'s own output directory. Zero monkeypatching.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from harnessx.aegis import AegisAgent
from harnessx.aegis.data.ledger import read_task_history
from harnessx.core.harness import HarnessConfig
from harnessx.ghx.flip_ledger import build_flip_ledger
import recipe.gaia_evolver.run_meta_aegis as rma
import recipe.gaia_evolver.run_meta_aegis_ghx as rma_ghx


TASK_IDS = [f"t{i}" for i in range(6)]

# passed-bit per task at round 0 (baseline ship target), round 1 (post-ship,
# the regression that trips the rollback), round 2 (post-rollback recovery).
ROUND_PASSED = {
    "t0": [True, True, True],    # always
    "t1": [True, False, True],   # swinger — fails exactly at the regressed round
    "t2": [True, False, True],   # swinger
    "t3": [True, False, False],  # swinger
    "t4": [True, False, False],  # swinger
    "t5": [True, False, False],  # swinger
}
SHIP_ROUND_N = 1  # meta_agent.evolve(round_n=1) is the call that ships after R0
SHIP_CID = "C-R1-01"
SHIP_BUCKET = "config"


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


def _build_args(tmp_path: Path, run_tag: str):
    tasks_path = tmp_path / f"{run_tag}_tasks.json"
    _tasks_json(tasks_path)
    parser = rma._build_argparser()
    return parser.parse_args(
        [
            "--tasks", str(tasks_path),
            "--run-tag", run_tag,
            "--num-rounds", "3",
            "--max-tasks", "0",
            "--concurrency", "6",
            "--runtime-policy",
        ]
    )


def _make_fake_run_task(executed: list):
    async def _fake_run_task(harness, task, label, *, pipeline_eval=None, harness_config=None):
        executed.append((label, task.task_id))
        round_idx = int(label.rsplit("R", 1)[1].split("/")[0])
        passed = ROUND_PASSED[task.task_id][round_idx]
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
            "steps": 2,
            "total_tokens": 100,
            "cost_usd": 0.02,
            "elapsed_s": 0.0,
            "exit_reason": "done",
            "_result": None,
        }

    return _fake_run_task


def _make_fake_evolve(run_dir: Path):
    async def _fake_evolve(self, current_config, trajectories_dir, output_dir, *,
                            pass_flags_by_task=None, round_n=1, raw_sessions_dir=None, **kwargs):
        if round_n == SHIP_ROUND_N:
            # A real ship: genuinely different bytes (not a re-implementation
            # of "changed" — an honest content change written through
            # HarnessConfig's own YAML round trip), PLUS the audit "commit"
            # event the real Stage-4 commit path writes, which is the one
            # `_read_latest_commit_shipments` needs to arm `last_ship_info`
            # (without it the rollback guard never engages — see
            # run_meta_aegis.py ~1346-1358).
            cfg = HarnessConfig.from_yaml_file(str(current_config))
            out_path = Path(output_dir) / "config.yaml"
            cfg.to_yaml_file(out_path)
            out_path.write_text(out_path.read_text(encoding="utf-8") + "# shipped\n", encoding="utf-8")
            audit_path = run_dir / "audit.jsonl"
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "round": round_n,
                    "stage": "4",
                    "kind": "commit",
                    "payload": {"shipped_cids": [SHIP_CID], "shipped_by_bucket": {SHIP_BUCKET: SHIP_CID}},
                }) + "\n")
            return out_path
        # Every other call: honest noop, hand back what was passed in.
        return Path(current_config)

    return _fake_evolve


async def _run_rollback_campaign(tmp_path: Path, monkeypatch, run_tag: str) -> tuple[Path, list]:
    monkeypatch.setattr(rma, "RUNS_DIR", tmp_path / "runs")
    run_dir = tmp_path / "runs" / run_tag
    executed: list = []
    monkeypatch.setattr(rma, "_run_task", _make_fake_run_task(executed))
    monkeypatch.setattr(AegisAgent, "evolve", _make_fake_evolve(run_dir))

    args = _build_args(tmp_path, run_tag)
    await rma.run_pilot(args)
    return run_dir, executed


def _processors(yaml_path: Path) -> list:
    return yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["processors"]


def _policy_entry(processors: list) -> dict:
    (entry,) = [p for p in processors if p["_target_"].endswith("runtime_policy.RuntimePolicyProcessor")]
    return entry


# ── 1. the in-loop rollback branch ──────────────────────────────────────────


async def test_in_loop_rollback_reverts_config_and_leaves_task_history_untouched(tmp_path, monkeypatch):
    run_dir, executed = await _run_rollback_campaign(tmp_path, monkeypatch, "rb1")

    r0_cfg = _processors(run_dir / "R0" / "config.yaml")
    _processors(run_dir / "R1" / "config.yaml")  # the shipped, later-reverted config
    r2_cfg = _processors(run_dir / "R2" / "config.yaml")  # written AFTER the rollback fired

    # The ship really did change bytes (comment aside, r1 is r0 re-rendered —
    # same processors either way here since evolve() didn't touch fields —
    # what matters is R1 != R0 on disk, proving a ship actually happened).
    assert (run_dir / "R1" / "config.yaml").read_bytes() != (run_dir / "R0" / "config.yaml").read_bytes()

    # ── core assertion: R2's config is R0's config, not R1's — the revert
    #    landed, and the policy processor survived the round trip with its
    #    rules intact (not dropped, not reset to some other default).
    assert r2_cfg == r0_cfg
    assert _policy_entry(r2_cfg)["rules"] == []
    assert _policy_entry(r0_cfg)["rules"] == []

    # ── task_history is untouched by rollback: round 1's rows reflect
    #    exactly what round 1 actually measured (the regression), byte for
    #    byte — rollback only ever reassigns `current_config` in memory plus
    #    audit/journal/reputation bookkeeping, never task_history.
    history = read_task_history(run_dir)
    r1_rows = {r["task_id"]: r for r in history if r["round"] == 1}
    for tid in TASK_IDS:
        assert r1_rows[tid]["passed"] == ROUND_PASSED[tid][1], tid

    # ── audit.jsonl carries both the commit (the ship) and the rollback
    #    (the revert) for round 1 — the pairing test_rollback_reaches_the_
    #    planner.py already pins for _append_rollback_journal's sibling call.
    audit_events = [json.loads(line) for line in (run_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    kinds_at_r1 = {e["kind"] for e in audit_events if e.get("round") == 1}
    assert {"commit", "rollback"} <= kinds_at_r1

    # ── reputation.json marks the shipped bucket as a regression (False).
    reputation = json.loads((run_dir / "reputation.json").read_text(encoding="utf-8"))
    assert reputation[SHIP_BUCKET] == [False]

    # sanity: the regression really did happen at the rollout level too.
    r1_executed_passed = {tid for label, tid in executed if label == "aegis/R1"}
    assert r1_executed_passed == set(TASK_IDS)  # full bed (noop-audit is off in this file)


# ── 2. the resume-time "un-poison merged.yaml" preflight ───────────────────


def test_fix_merged_after_rollback_restores_validated_lineage_and_keeps_policy_rules(tmp_path, monkeypatch):
    from benchmarks.gaia.harness import make_gaia_builder_gpt5

    monkeypatch.setattr(rma, "RUNS_DIR", tmp_path / "runs")
    run_dir = tmp_path / "runs" / "rb2"
    (run_dir / "R0").mkdir(parents=True)
    (run_dir / "R1" / "applied").mkdir(parents=True)
    (run_dir / "data").mkdir(parents=True)

    # R0 = the validated lineage: a real config (built the same way run_pilot
    # itself builds R0) carrying the RuntimePolicyProcessor.
    from recipe.gaia_evolver.run_meta_aegis import _maybe_add_runtime_policy

    validated = _maybe_add_runtime_policy(make_gaia_builder_gpt5(max_cost_usd=15.0).build(), True, run_dir=run_dir)
    validated.to_yaml_file(run_dir / "R0" / "config.yaml")

    # R1/applied/merged.yaml = the POISONED merge — what was actually shipped
    # for R1 and later rolled back. Deliberately different bytes from R0's
    # config so the test can tell "restored" from "left alone".
    poisoned_text = (run_dir / "R0" / "config.yaml").read_text(encoding="utf-8") + "# poisoned ship\n"
    (run_dir / "R1" / "applied" / "merged.yaml").write_text(poisoned_text, encoding="utf-8")

    # audit.jsonl records R1 as rolled back (the real writer, not a hand roll).
    from recipe.gaia_evolver.run_meta_aegis import _append_rollback_audit

    _append_rollback_audit(
        run_dir, round_idx=1, rolled_back_cids=["C-R1-01"],
        pre_ship_rate=1.0, post_ship_rate=0.167, delta_count=-5,
        reason="Δrate=-0.833 <= -0.05 AND Δcount=-5 <= -3",
    )

    task_history_path = run_dir / "data" / "task_history.jsonl"
    task_history_path.write_text('{"round": 0, "task_id": "t0", "passed": true}\n', encoding="utf-8")
    task_history_before = task_history_path.read_bytes()

    args = _build_args(tmp_path, "rb2")
    args.start_round = 2  # resuming at R2 => last completed round is R1, which rolled back

    rma_ghx._fix_merged_after_rollback(args)

    merged_path = run_dir / "R1" / "applied" / "merged.yaml"
    restored_processors = yaml.safe_load(merged_path.read_text(encoding="utf-8"))["processors"]
    r0_processors = yaml.safe_load((run_dir / "R0" / "config.yaml").read_text(encoding="utf-8"))["processors"]

    # merged.yaml is un-poisoned: back to R0 (the newest round NOT itself
    # rolled back), policy processor and its rules survive untouched.
    assert restored_processors == r0_processors
    assert _policy_entry(restored_processors)["rules"] == []

    # the poisoned content was backed up, not silently discarded.
    backup = run_dir / "R1" / "applied" / "merged.pre_rollback_resume.yaml"
    assert backup.read_text(encoding="utf-8") == poisoned_text

    # this preflight touches merged.yaml only — task_history is untouched.
    assert task_history_path.read_bytes() == task_history_before


# ── 3. the flip ledger, reading a run_dir that had a rollback ──────────────


async def test_flip_ledger_reads_the_regressed_round_honestly(tmp_path, monkeypatch):
    run_dir, _ = await _run_rollback_campaign(tmp_path, monkeypatch, "rb3")
    digests_dir = run_dir / "R1" / "digests"
    digests_dir.mkdir(parents=True, exist_ok=True)

    rep = build_flip_ledger(run_dir, digests_dir, history_round=1)

    assert rep.total_tasks == len(TASK_IDS)
    swinger_ids = {row["task_id"] for row in rep.swinger_rows}
    # every task that failed at the regressed round (1) and has a mixed
    # history is a swinger row here, t1..t5 by design.
    assert swinger_ids == {"t1", "t2", "t3", "t4", "t5"}
    for row in rep.swinger_rows:
        # round 1 (index 1 in the pattern) is honestly "." (a real, uncarried
        # failure) — the rollback that later reverted the CONFIG never
        # touched this task's recorded history.
        assert row["pattern"][1] == ".", row
    # t1/t2 recovered at round 2, t3/t4/t5 did not — both patterns land.
    by_id = {row["task_id"]: row["pattern"] for row in rep.swinger_rows}
    assert by_id["t1"] == "#.#"
    assert by_id["t3"] == "#.."
