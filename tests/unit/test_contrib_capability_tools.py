# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The two hand-added capability tools (M25).

Both fill gaps the evolution loop could not close by itself: the transcript
client was written by an Evolver, ranked first by its Critic, and lost with the
whole round on a manifest-formatting gate; the Wikipedia gap was never even
proposed, because the agent has no way to observe that api.php answers the
built-in User-Agent with 403.

Network is not required: the MediaWiki calls go through a single ``_get`` seam
these tests replace.  The live checks are gated on ``HARNESSX_LIVE_NET=1``.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from harnessx.tools.contrib import wikipedia_api as W
from harnessx.tools.contrib.youtube_transcript import _extract_video_id
from harnessx.tools.contrib.youtube_transcript import youtube_transcript_tool as YT

live = pytest.mark.skipif(
    os.environ.get("HARNESSX_LIVE_NET") != "1", reason="set HARNESSX_LIVE_NET=1 for live network"
)


def run(coro):
    return asyncio.run(coro)


# ── the tools must survive a config YAML round-trip ──────────────────────────


def test_both_tools_record_a_resolvable_target():
    """Without __hx_target__ the capability is dropped at the first config save,
    which is worse than never adding it: the run looks configured and is not."""
    import importlib

    for tool_obj in (W.wikipedia_api_tool, YT):
        target = getattr(tool_obj, "__hx_target__", None)
        assert target, f"{tool_obj.name} has no __hx_target__"
        mod, _, attr = target.rpartition(".")
        assert getattr(importlib.import_module(mod), attr) is tool_obj


# ── YouTubeTranscript ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://www.youtube.com/watch?v=1htKBjuUWec", "1htKBjuUWec"),
        ("https://youtu.be/1htKBjuUWec", "1htKBjuUWec"),
        ("https://www.youtube.com/shorts/1htKBjuUWec", "1htKBjuUWec"),
        ("1htKBjuUWec", "1htKBjuUWec"),
        ("https://www.youtube.com/watch?v=1htKBjuUWec&t=120s", "1htKBjuUWec"),
        ("not a video", None),
        ("", None),
    ],
)
def test_video_id_extraction(raw, expected):
    assert _extract_video_id(raw) == expected


def test_unparseable_input_explains_itself_and_does_not_raise():
    out = run(YT.fn(url="not a video"))
    assert "[TRANSCRIPT UNAVAILABLE]" in out
    assert "11-character video id" in out


def test_missing_captions_names_the_reason_and_forbids_fabrication(monkeypatch):
    """The candidate this was adopted from reported getattr(err, "str", None),
    which is always None — the model was told the fetch failed and never why,
    on the exact bed whose failure mode is inventing an answer instead."""

    class _Api:
        def fetch(self, *a, **k):
            raise RuntimeError("Subtitles are disabled for this video")

    import youtube_transcript_api

    monkeypatch.setattr(youtube_transcript_api, "YouTubeTranscriptApi", lambda: _Api())
    out = run(YT.fn(url="1htKBjuUWec"))
    assert "[TRANSCRIPT UNAVAILABLE]" in out
    assert "Subtitles are disabled" in out
    assert "Do NOT fabricate" in out


def test_timestamps_are_rendered_so_a_moment_can_be_asked_about(monkeypatch):
    class _Snip:
        def __init__(self, text, start):
            self.text, self.start = text, start

    class _Api:
        def fetch(self, *a, **k):
            return [_Snip("first", 0.4), _Snip("later", 125.0)]

    import youtube_transcript_api

    monkeypatch.setattr(youtube_transcript_api, "YouTubeTranscriptApi", lambda: _Api())
    assert run(YT.fn(url="1htKBjuUWec")) == "[0:00] first\n[2:05] later"
    assert run(YT.fn(url="1htKBjuUWec", with_timestamps=False)) == "first\nlater"


# ── WikipediaAPI ─────────────────────────────────────────────────────────────


def _revs(n: int) -> list[dict]:
    """Newest first, as the API returns them for rvdir=older."""
    return [
        {"revid": 100 - i, "timestamp": f"20{20 - i:02d}-01-01T00:00:00Z", "user": "u", "size": 1}
        for i in range(n)
    ]


def test_revision_window_ends_at_the_present(monkeypatch):
    """Walking forward from page creation builds a window that stops short of now
    on any page longer than the cap, and then the bisection's "is it in the newest
    revision" precondition tests a revision from years ago. Caught in live smoke:
    a file the page demonstrably embeds came back "not present"."""
    seen: dict = {}

    def fake_get(params, lang):
        seen.update(params)
        return {"query": {"pages": {"1": {"revisions": _revs(5)}}}}

    monkeypatch.setattr(W, "_get", fake_get)
    out = W._all_revisions("T", "en", 5)
    assert seen["rvdir"] == "older"  # newest first from the API...
    assert [r["revid"] for r in out] == [96, 97, 98, 99, 100]  # ...oldest first to the caller


def test_first_with_bisects_to_the_introducing_revision(monkeypatch):
    monkeypatch.setattr(W, "_get", lambda params, lang: {"query": {"pages": {"1": {"revisions": _revs(8)}}}})
    # present from revid 97 onward; the caller's list is oldest-first 93..100
    monkeypatch.setattr(W, "_revision_text", lambda revid, lang: "NEEDLE" if revid >= 97 else "")
    out = W._do_first_with("T", "needle", "en", 8)
    assert "revision 97" in out
    assert "Previous revision 96" in out
    assert "assumes the string stayed once added" in out


def test_first_with_refuses_when_the_string_is_gone_today(monkeypatch):
    """Live case: a page's images can come from a template, so they are in the
    rendered page and never in its wikitext. A date invented here would be a
    confident wrong answer."""
    monkeypatch.setattr(W, "_get", lambda params, lang: {"query": {"pages": {"1": {"revisions": _revs(8)}}}})
    monkeypatch.setattr(W, "_revision_text", lambda revid, lang: "nothing here")
    out = W._do_first_with("T", "File:X.jpg", "en", 8)
    assert "not present in the newest" in out
    assert "removed again" in out


def test_first_with_says_when_the_window_is_too_short(monkeypatch):
    monkeypatch.setattr(W, "_get", lambda params, lang: {"query": {"pages": {"1": {"revisions": _revs(8)}}}})
    monkeypatch.setattr(W, "_revision_text", lambda revid, lang: "NEEDLE always")
    out = W._do_first_with("T", "needle", "en", 8)
    assert "predates this window" in out
    assert "raise `limit`" in out


def test_missing_page_and_unknown_action_are_messages_not_exceptions(monkeypatch):
    monkeypatch.setattr(W, "_get", lambda params, lang: {"query": {"pages": {"1": {"missing": ""}}}})
    assert "no page titled" in run(W.wikipedia_api_tool.fn(action="page", title="Nope"))
    assert "unknown action" in run(W.wikipedia_api_tool.fn(action="frobnicate"))


def test_transport_failure_is_reported_not_raised(monkeypatch):
    def boom(params, lang):
        raise RuntimeError("connection reset")

    monkeypatch.setattr(W, "_get", boom)
    out = run(W.wikipedia_api_tool.fn(action="search", query="x"))
    assert "[WIKIPEDIA] search failed" in out
    assert "connection reset" in out


# ── live ─────────────────────────────────────────────────────────────────────


@live
def test_live_builtin_webfetch_is_blocked_but_this_tool_is_not():
    """The premise of the whole module, asserted rather than assumed."""
    import httpx

    from harnessx.tools.builtin._web_utils import _USER_AGENT

    url = "https://en.wikipedia.org/w/api.php?action=query&format=json&meta=siteinfo"
    assert httpx.get(url, headers={"User-Agent": _USER_AGENT}, timeout=30).status_code == 403
    assert httpx.get(url, headers={"User-Agent": W._UA}, timeout=30).status_code == 200


@live
def test_live_dates_the_template_that_renders_the_aquinas_picture():
    """Bed task d5141ca5, failed 12/12 M25 batches. Ground truth 19/02/2009."""
    out = run(
        W.wikipedia_api_tool.fn(
            action="first_with", title="Principle of double effect", needle="{{Thomism}}"
        )
    )
    assert "2009-02-19" in out
