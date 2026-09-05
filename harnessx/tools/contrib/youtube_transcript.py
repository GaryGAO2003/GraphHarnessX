# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Captions for a YouTube video — the media channel the bed has been guessing at.

Adopted, near-verbatim, from the Evolver's own candidate ``C-R11-02`` in the
M25_103x16 campaign.  The loop wrote this tool, its Critic ranked it first and
decided ``ship``, and the deterministic structure gate then refused the whole
round for an unrelated manifest-formatting rule (IV-3, "candidate manifest body
has zero evidence anchors"), so the round committed nothing.  The diagnosis in
the candidate's own header is correct and worth preserving:

    In 0383a3ee every retrieval path to the target video's captions failed:
    youtube.com returned only a JS footer shell to WebFetch, Browser get_text
    returned empty payloads three times, youtubetotranscript.com hit a
    Cloudflare bot-wall, youtubetranscript.com returned a loading shell, and a
    Bash youtube-transcript-api attempt returned HTTP 403.  The model then
    fabricated "ostrich" to satisfy the countdown.

That is the ``empty_consumed`` motif with a name: every path returns nothing,
the nothing reaches the terminal model call, and an answer is invented.  This
bed carries fourteen media questions; ten of them pass today only because the
answer happens to be restated in a description, a fan wiki or a news article,
and four of those ten pass in fewer than half the rounds.

Changed from the candidate: the error path reported ``getattr(last_error,
"str", None)``, which is always ``None`` — the failure reason never reached the
model.  It now reports the exception.  Everything else is the loop's.
"""

from __future__ import annotations

import asyncio
import logging
import re

from ..base import tool

logger = logging.getLogger(__name__)

_YOUTUBE_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)"
    r"([A-Za-z0-9_-]{11})"
)
_BARE_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")


def _extract_video_id(url_or_id: str) -> str | None:
    s = (url_or_id or "").strip()
    if not s:
        return None
    if _BARE_ID_RE.fullmatch(s):
        return s
    m = _YOUTUBE_ID_RE.search(s)
    return m.group(1) if m else None


@tool(
    name="YouTubeTranscript",
    description=(
        "Fetch the captions/subtitles of a YouTube video by URL or 11-character video id. "
        "Uses the official timedtext API, which is not behind the Cloudflare walls that block "
        "youtube.com scraping and third-party transcript sites. Returns the transcript as "
        "timestamped lines so a question about a specific moment can be answered. "
        "Args: url (video URL or id), language_codes (comma-separated, default 'en,en-US,auto'), "
        "with_timestamps (default true — set false for prose)."
    ),
)
async def youtube_transcript_tool(
    url: str,
    language_codes: str = "en,en-US,auto",
    with_timestamps: bool = True,
) -> str:
    """Return a YouTube video's transcript as readable text."""
    video_id = _extract_video_id(url or "")
    if not video_id:
        return (
            "[TRANSCRIPT UNAVAILABLE] Could not parse a YouTube video id from "
            f"{url!r}. Provide a youtube.com/watch?v= URL, a youtu.be/ URL, or a bare "
            "11-character video id."
        )

    def _fetch() -> str:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        langs = [c.strip() for c in (language_codes or "").split(",") if c.strip()] or ["en"]
        last_error: Exception | None = None
        for attempt in (langs, ["en"], ["auto"]):
            try:
                data = list(api.fetch(video_id, languages=attempt))
            except Exception as exc:  # noqa: BLE001 — try the next language set
                last_error = exc
                continue
            if not data:
                last_error = RuntimeError("transcript is empty")
                continue
            parts = []
            for snip in data:
                text = (getattr(snip, "text", None) or getattr(snip, "line", "") or "").strip()
                if not text:
                    continue
                if with_timestamps:
                    start = float(getattr(snip, "start", 0.0) or 0.0)
                    parts.append(f"[{int(start) // 60:d}:{int(start) % 60:02d}] {text}")
                else:
                    parts.append(text)
            if parts:
                return "\n".join(parts)
            last_error = RuntimeError("transcript joined empty")
        return (
            f"[TRANSCRIPT UNAVAILABLE] No captions for video id {video_id} "
            f"({type(last_error).__name__}: {last_error}). The video may have no captions, or "
            "none in the requested languages. Do NOT fabricate the video's content — say the "
            "transcript is unobtainable and try another source."
        )

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as exc:  # noqa: BLE001 — a tool must not raise into the run loop
        logger.warning("YouTubeTranscript failed for %s: %s", video_id, exc)
        return (
            f"[TRANSCRIPT UNAVAILABLE] Unexpected error for {video_id}: {exc}. "
            "Do NOT fabricate the video's content."
        )


__all__ = ["youtube_transcript_tool"]


# A config serialised to YAML must round-trip this tool as a resolvable target
# (``tool_registry.custom``), the same convention serper_search.py follows —
# without it every evolved config would silently drop the capability at the
# first save/load, which is worse than never having added it.
youtube_transcript_tool.__hx_target__ = (
    "harnessx.tools.contrib.youtube_transcript.youtube_transcript_tool"
)
