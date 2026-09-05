# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Which round dir holds a trajectory's U is a bed convention — resolve by looking."""
from __future__ import annotations

from harnessx.ghx.layer_a import _u_for_trajectory
from harnessx.ghx.projection import find_task_u
from harnessx.graph.unfold import UnfoldRecorder, write_unfolded


def _u(sessions_dir, session_name, run_id="r"):
    rec = UnfoldRecorder(run_id=run_id, session_id=session_name)
    rec.annotate_outcome(rec.record_tool_invocation("get_order_details", 1, None), "ok")
    return write_unfolded(rec.finalize(None), base_dir=str(sessions_dir))


def _traj(round_dir, name="7_r0.jsonl"):
    d = round_dir / "trajectories"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("", encoding="utf-8")
    return p


def test_gaia_pairing_still_wins(tmp_path):
    """R{n}/trajectories carry batch n-1 there; that join must not regress."""
    (tmp_path / "R4").mkdir()
    _u(tmp_path / "R3" / "sessions" / "aegis", "R3-7")
    u, rnd = _u_for_trajectory(_traj(tmp_path / "R4"), "7")
    assert u is not None and "R3" in str(u) and rnd == 3


def test_tau2_pairing_is_found_by_looking(tmp_path):
    """Here the rollouts and their sessions share a round dir, and there is no
    aegis/ level — no flag says so, the lookup just finds one and not the other."""
    _u(tmp_path / "R4" / "sessions", "R4-7")
    u, rnd = _u_for_trajectory(_traj(tmp_path / "R4"), "7")
    assert u is not None and "R4" in str(u) and rnd == 4


def test_neither_layout_degrades_rather_than_guessing(tmp_path):
    (tmp_path / "R2").mkdir()
    assert _u_for_trajectory(_traj(tmp_path / "R2"), "7") == (None, None)


def test_numeric_ids_do_not_match_by_substring(tmp_path):
    """tau2 ids are bare integers: task 1 must not resolve to task 11's graph."""
    _u(tmp_path / "R0" / "sessions", "R0-11")
    assert find_task_u(tmp_path / "R0", "1") is None
    _u(tmp_path / "R0" / "sessions", "R0-1")
    hit = find_task_u(tmp_path / "R0", "1")
    assert hit is not None and hit.parent.parent.name == "R0-1"


def test_gaia_substring_glob_is_untouched(tmp_path):
    """GAIA session names embed a uuid task id; the old glob must keep matching."""
    _u(tmp_path / "R3" / "sessions" / "aegis", "R3-aaaa1111-0-0-0-1")
    assert find_task_u(tmp_path / "R3", "aaaa1111-0-0-0-1") is not None
