# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""τ² port: locating a task's U by session name instead of a captured run id."""
from __future__ import annotations

from harnessx.ghx.tau2_layout import session_name, tau2_layout_resolver, tau2_u_path
from harnessx.graph.unfold import UnfoldRecorder, write_unfolded


def _write_u(sessions, prefix, task_id, run_id="run-a", tool="get_order_details"):
    rec = UnfoldRecorder(run_id=run_id, session_id=session_name(prefix, task_id))
    inv = rec.record_tool_invocation(tool, 1, None)
    rec.annotate_outcome(inv, "ok")
    return write_unfolded(rec.finalize(None), base_dir=str(sessions))


def test_resolves_by_session_name(tmp_path):
    sessions = tmp_path / "R3" / "sessions"
    _write_u(sessions, "R3", "42")
    u = tau2_layout_resolver(sessions, "R3")("42")
    assert u is not None
    assert [n.static_node_id for n in u.nodes] == ["tool:get_order_details"]


def test_missing_session_and_missing_u_are_unavailable(tmp_path):
    sessions = tmp_path / "R0" / "sessions"
    sessions.mkdir(parents=True)
    resolve = tau2_layout_resolver(sessions, "R0")
    assert resolve("nope") is None  # no session directory at all
    (sessions / session_name("R0", "7")).mkdir()  # session exists, U never written
    assert resolve("7") is None
    assert tau2_u_path(sessions, "R0", "7") is None


def test_numeric_ids_do_not_collide(tmp_path):
    """tau2 task ids are bare integers as strings: '1' must not resolve to '11'."""
    sessions = tmp_path / "R0" / "sessions"
    _write_u(sessions, "R0", "1", tool="tool_one")
    _write_u(sessions, "R0", "11", tool="tool_eleven")
    resolve = tau2_layout_resolver(sessions, "R0")
    assert [n.static_node_id for n in resolve("1").nodes] == ["tool:tool_one"]
    assert [n.static_node_id for n in resolve("11").nodes] == ["tool:tool_eleven"]


def test_newest_wins_when_a_session_holds_several(tmp_path):
    import os
    import time

    sessions = tmp_path / "R0" / "sessions"
    old = _write_u(sessions, "R0", "5", run_id="old", tool="stale")
    time.sleep(0.01)
    new = _write_u(sessions, "R0", "5", run_id="new", tool="fresh")
    os.utime(old, (1, 1))  # make the ordering unambiguous on a coarse clock
    assert tau2_u_path(sessions, "R0", "5") == new
    assert [n.static_node_id for n in tau2_layout_resolver(sessions, "R0")("5").nodes] == ["tool:fresh"]


def test_corrupt_u_reads_as_unavailable_not_empty(tmp_path):
    sessions = tmp_path / "R0" / "sessions"
    path = _write_u(sessions, "R0", "9")
    path.write_text("{not json at all\n", encoding="utf-8")
    assert tau2_layout_resolver(sessions, "R0")("9") is None


def test_slug_leaves_a_safe_id_alone():
    """retail/airline ids are bare integers — earlier runs' sessions must stay
    resolvable, so a safe id is never rewritten."""
    from harnessx.ghx.tau2_layout import task_slug

    assert task_slug("7") == "7"
    assert task_slug(7) == "7"
    assert session_name("R3", "7") == "R3-7"


def test_slug_makes_a_telecom_id_a_legal_path_component():
    from harnessx.ghx.tau2_layout import task_slug

    tid = "[service_issue]break_apn_settings|lock_sim_card_pin[PERSONA:Easy]"
    slug = task_slug(tid)
    assert not set(slug) & set('<>:"/\|?*')
    assert len(slug) <= 60
    # the hash is over the FULL id: telecom ids share long prefixes, so a bare
    # truncation would map different tasks to one directory
    other = "[service_issue]break_apn_settings|lock_sim_card_pin[PERSONA:Hard]"
    assert task_slug(other) != slug


def test_resolver_round_trips_a_sanitised_id(tmp_path):
    from harnessx.ghx.tau2_layout import task_slug
    from harnessx.graph.unfold import UnfoldRecorder, write_unfolded

    tid = "[mobile_data_issue]airplane_mode_on|roaming_off[PERSONA:None]"
    sessions = tmp_path / "R2" / "sessions"
    rec = UnfoldRecorder(run_id="r", session_id=session_name("R2", tid))
    rec.annotate_outcome(rec.record_tool_invocation("get_bill", 1, None), "ok")
    write_unfolded(rec.finalize(None), base_dir=str(sessions))
    u = tau2_layout_resolver(sessions, "R2")(tid)
    assert u is not None and [n.static_node_id for n in u.nodes] == ["tool:get_bill"]
    from harnessx.ghx.projection import find_task_u

    assert find_task_u(tmp_path / "R2", tid) is not None
    assert task_slug(tid) in str(find_task_u(tmp_path / "R2", tid))


def test_slug_is_idempotent():
    """The pilot's records carry the slug while the adapter names its session
    from tau2's real id; both must land on one directory, so slugging a slug has
    to be a no-op — and a produced slug is longer than the truncation point."""
    from harnessx.ghx.tau2_layout import task_slug

    tid = "[service_issue]break_apn_settings|lock_sim_card_pin|overdue_bill[PERSONA:Easy]"
    once = task_slug(tid)
    assert task_slug(once) == once
    assert len(once) > 48  # would re-hash under the truncation bound
    assert session_name("R0", once) == session_name("R0", tid)
