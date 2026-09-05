# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""τ² port: the trajectory the Digester reads must be the whole conversation."""
from __future__ import annotations

from harnessx.ghx.tau2_trace import merge_environment_turns, merged_trajectory_lines


def _j(t, step=0, **kw):
    return {"type": t, "step": step, **kw}


def _m(role, content, **kw):
    return {"role": role, "content": content, **kw}


def test_environment_turns_land_between_the_agent_turns():
    journal = [_j("session_start"), _j("raw_assistant", 1), _j("raw_assistant", 2), _j("episode_end", 3)]
    tau2 = [
        _m("user", "hi"),
        _m("assistant", "one moment"),
        _m("tool", "{'order': 42}", id="c1", name="get_order"),
        _m("assistant", "found it"),
        _m("user", "thanks"),
    ]
    out = merge_environment_turns(journal, tau2, "R0-3")
    kinds = [e["type"] for e in out]
    assert kinds == [
        "session_start",
        "raw_user",       # before the first agent turn
        "raw_assistant",
        "raw_tool",       # the environment's answer to that turn
        "raw_assistant",
        "raw_user",       # the tail, after the last agent turn
        "episode_end",    # still last
    ]


def test_journal_only_events_keep_their_places():
    """Injected steers and step boundaries exist only in the journal; a merge
    that replaced the file with tau2's view would erase exactly the records GHX
    cares most about."""
    journal = [_j("raw_user", 0, meta={"synthetic": True}), _j("raw_assistant", 1), _j("episode_end", 2)]
    out = merge_environment_turns(journal, [_m("user", "hi"), _m("assistant", "ok")], "s")
    assert out[0]["meta"] == {"synthetic": True}
    assert [e["type"] for e in out] == ["raw_user", "raw_user", "raw_assistant", "episode_end"]


def test_tool_results_carry_id_and_name():
    out = merge_environment_turns(
        [_j("raw_assistant", 1)],
        [_m("assistant", "x"), _m("tool", "payload", id="call-9", name="get_user_details")],
        "s",
    )
    tool = next(e for e in out if e["type"] == "raw_tool")
    assert tool["message"]["tool_call_id"] == "call-9"
    assert tool["message"]["name"] == "get_user_details"
    assert tool["message"]["content"] == "payload"


def test_assistant_turns_are_never_duplicated():
    """The journal's assistant record is the richer one (tool_calls, ids); tau2's
    copy of the same turn must not be emitted beside it."""
    journal = [_j("raw_assistant", 1), _j("raw_assistant", 2)]
    tau2 = [_m("assistant", "a"), _m("assistant", "b")]
    out = merge_environment_turns(journal, tau2, "s")
    assert [e["type"] for e in out] == ["raw_assistant", "raw_assistant"]


def test_empty_tau2_record_degrades_to_the_journal():
    journal = [_j("raw_assistant", 1), _j("episode_end", 2)]
    assert merge_environment_turns(journal, [], "s") == journal
    assert merge_environment_turns(journal, None, "s") == journal


def test_more_agent_turns_in_the_journal_than_in_tau2_does_not_crash():
    """A truncated tau2 record (timeout mid-write) must not index past its end."""
    journal = [_j("raw_assistant", 1), _j("raw_assistant", 2), _j("raw_assistant", 3)]
    out = merge_environment_turns(journal, [_m("user", "hi"), _m("assistant", "a")], "s")
    assert [e["type"] for e in out] == ["raw_user", "raw_assistant", "raw_assistant", "raw_assistant"]


def test_lines_are_valid_jsonl():
    import json

    lines = merged_trajectory_lines([_j("raw_assistant", 1)], [_m("user", "hé")], "s")
    assert all(line.endswith("\n") for line in lines)
    assert json.loads(lines[0])["message"]["content"] == "hé"


def test_per_turn_episode_ends_collapse_into_one():
    """The adapter calls run() per turn, so the journal holds an episode_end for
    each; the vendored fact extractor takes the FIRST, which said interrupted /
    zero steps for every tau2 task ever recorded."""
    journal = [
        _j("raw_assistant", 1),
        _j("episode_end", 1, exit_reason="interrupted", total_steps=2),
        _j("raw_assistant", 2),
        _j("episode_end", 2, exit_reason="done", total_steps=3),
    ]
    out = merge_environment_turns(journal, [_m("assistant", "a"), _m("assistant", "b")], "s")
    ends = [e for e in out if e["type"] == "episode_end"]
    assert len(ends) == 1
    assert ends[0]["exit_reason"] == "done"       # the turn that ended the conversation
    assert ends[0]["total_steps"] == 5            # summed over turns, not the last one's
    assert ends[0]["meta"]["collapsed_turn_ends"] == 2
    assert out[-1]["type"] == "episode_end"


def test_a_single_episode_end_is_left_alone():
    journal = [_j("raw_assistant", 1), _j("episode_end", 1, exit_reason="done", total_steps=4)]
    out = merge_environment_turns(journal, [_m("assistant", "a")], "s")
    assert [e["type"] for e in out] == ["raw_assistant", "episode_end"]
    assert "meta" not in out[-1] or "collapsed_turn_ends" not in (out[-1].get("meta") or {})
