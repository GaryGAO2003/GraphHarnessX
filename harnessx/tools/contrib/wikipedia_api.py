# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The MediaWiki API, reachable — the built-in web tools cannot reach it.

Wikipedia is this bed's dominant source, and the agent has never once been able
to call its API.  ``WebFetch`` sends a spoofed desktop-Safari User-Agent
(``harnessx/tools/builtin/_web_utils.py``), and Wikimedia answers ``api.php``
with **HTTP 403 and a link to its robot policy** for exactly that: a browser
string on an automated endpoint.  Measured here, same machine, same second:
the built-in fetch gets 403; a request identifying itself honestly gets 200.
So every question needing revision history, category membership, or the
wikitext behind a rendered page has been answered by scraping rendered HTML or
not at all.

That gap has a task attached.  ``d5141ca5`` ("when was a picture of St. Thomas
Aquinas first added to the Wikipedia page on the Principle of double effect")
has failed all twelve M25 batches, and it is not a perception task at all — the
answer is one row of revision history.  It failed for want of an API call.

Six actions, all read-only:

``search``     — find page titles for a query.
``page``       — plain-text extract of a page (no HTML soup, no navigation chrome).
``history``    — revisions, newest first: timestamp, user, comment, size.
``images``     — the File: names a page embeds, in their wikitext spelling.
``revision``   — the wikitext as it stood at a revid or on a date.
``first_with`` — the OLDEST revision whose wikitext contains a string, by
                 bisection over the revision list.

``first_with`` assumes the string, once added, stays.  True for an infobox image
or a citation; false for something added, removed and re-added, where it finds
*an* introduction rather than the first.  It says so in its own output rather
than letting a date look more certain than it is, and refuses outright when the
string is absent from the current revision — which is what happens when the
thing was later removed, or when it is rendered by a template and never appears
in this page's wikitext at all.  ``revision`` is the escape hatch for both: the
model walks ``history`` and reads the wikitext itself.

Deliberately NOT included: a "when did this page first show any image" special
case.  The bed has a task that wants exactly that, and building it into the
environment would be fitting the tool to a known answer rather than giving the
agent a capability.
"""

from __future__ import annotations

import asyncio
import json
import logging

from ..base import tool

logger = logging.getLogger(__name__)

# Wikimedia's robot policy asks automated clients to identify themselves and say
# where to complain. The built-in tools' browser string is what earns the 403.
_UA = "HarnessX-GAIA-Research/0.1 (research agent; https://github.com/darwin-agent/harnessx)"
_API = "https://{lang}.wikipedia.org/w/api.php"
_TIMEOUT = 30.0
_MAX_REVISIONS = 2000
_EXTRACT_CHARS = 20_000


def _get(params: dict, lang: str) -> dict:
    import httpx

    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True, headers={"User-Agent": _UA}) as c:
        r = c.get(_API.format(lang=lang), params={**params, "format": "json"})
        r.raise_for_status()
        return r.json()


def _revision_text(revid: int, lang: str) -> str:
    data = _get(
        {"action": "query", "prop": "revisions", "revids": str(revid),
         "rvprop": "content", "rvslots": "main"},
        lang,
    )
    for page in (data.get("query", {}).get("pages") or {}).values():
        for rev in page.get("revisions") or ():
            slot = (rev.get("slots") or {}).get("main") or {}
            return str(slot.get("*") or rev.get("*") or "")
    return ""


def _all_revisions(title: str, lang: str, limit: int) -> list[dict]:
    """The ``limit`` most recent revisions, returned OLDEST first.

    Walking forward from the page's creation instead would build a window that
    stops short of the present on any page with more revisions than the cap —
    and then the bisection's "is it in the newest one" precondition tests a
    revision from years ago. Caught in smoke: a file that the page demonstrably
    embeds today came back "not present in the newest of the 300 revisions
    examined", because revision 300 of ~470 predates it.
    """
    out: list[dict] = []
    cont: dict = {}
    while len(out) < limit:
        data = _get(
            {"action": "query", "prop": "revisions", "titles": title,
             "rvprop": "ids|timestamp|user|comment|size", "rvlimit": "max",
             "rvdir": "older", **cont},
            lang,
        )
        pages = data.get("query", {}).get("pages") or {}
        for page in pages.values():
            if "missing" in page:
                return []
            out.extend(page.get("revisions") or ())
        cont = data.get("continue") or {}
        if not cont:
            break
    return list(reversed(out[:limit]))


def _do_search(query: str, lang: str, limit: int) -> str:
    data = _get({"action": "query", "list": "search", "srsearch": query, "srlimit": str(limit)}, lang)
    hits = data.get("query", {}).get("search") or []
    if not hits:
        return f"[WIKIPEDIA] no results for {query!r}"
    return "\n".join(f"- {h['title']} ({h.get('wordcount', '?')} words)" for h in hits)


def _do_page(title: str, lang: str) -> str:
    data = _get(
        {"action": "query", "prop": "extracts", "titles": title,
         "explaintext": "1", "redirects": "1"},
        lang,
    )
    for page in (data.get("query", {}).get("pages") or {}).values():
        if "missing" in page:
            return f"[WIKIPEDIA] no page titled {title!r}"
        text = str(page.get("extract") or "")
        if not text:
            return f"[WIKIPEDIA] {title!r} exists but has no text extract"
        return f"# {page.get('title', title)}\n\n{text[:_EXTRACT_CHARS]}"
    return f"[WIKIPEDIA] no page titled {title!r}"


def _do_images(title: str, lang: str, limit: int) -> str:
    """The File: titles on a page — the missing first half of "when was picture X added".

    ``first_with`` needs the wikitext token, and the wikitext token is the file
    name, which the rendered page never shows.  Without this the model has to
    guess the filename from the caption, which is how ``d5141ca5`` was being
    lost: the caption says "St. Thomas Aquinas", the wikitext says
    ``Saint Thomas Aquinas.jpg``.
    """
    data = _get(
        {"action": "query", "prop": "images", "titles": title,
         "imlimit": str(min(limit, 100)), "redirects": "1"},
        lang,
    )
    for page in (data.get("query", {}).get("pages") or {}).values():
        if "missing" in page:
            return f"[WIKIPEDIA] no page titled {title!r}"
        imgs = [str(i.get("title") or "") for i in (page.get("images") or ())]
        if not imgs:
            return f"[WIKIPEDIA] {title!r} embeds no files"
        lines = [
            f"# files embedded in {page.get('title', title)}",
            "Pass the part after 'File:' as `needle` to first_with to date one of these.",
        ]
        lines += [f"- {i}" for i in imgs]
        return "\n".join(lines)
    return f"[WIKIPEDIA] no page titled {title!r}"


def _do_revision(title: str, revid: str, at: str, lang: str) -> str:
    """Wikitext at a revid, or as it stood on a date."""
    if revid:
        text = _revision_text(int(revid), lang)
        if not text:
            return f"[WIKIPEDIA] revision {revid} has no readable wikitext"
        return f"# wikitext of revision {revid}\n\n{text[:_EXTRACT_CHARS]}"
    if not at:
        return "[WIKIPEDIA] revision needs either `revid` or `at` (an ISO date)."
    data = _get(
        {"action": "query", "prop": "revisions", "titles": title,
         "rvprop": "ids|timestamp|user|comment", "rvlimit": "1",
         "rvstart": at, "rvdir": "older", "redirects": "1"},
        lang,
    )
    for page in (data.get("query", {}).get("pages") or {}).values():
        if "missing" in page:
            return f"[WIKIPEDIA] no page titled {title!r}"
        revs = page.get("revisions") or []
        if not revs:
            return f"[WIKIPEDIA] {title!r} had no revision at or before {at}"
        r = revs[0]
        text = _revision_text(int(r["revid"]), lang)
        return (
            f"# wikitext of {page.get('title', title)} as of {r.get('timestamp')} "
            f"(revid={r.get('revid')}, by {r.get('user')})\n\n{text[:_EXTRACT_CHARS]}"
        )
    return f"[WIKIPEDIA] no page titled {title!r}"


def _do_history(title: str, lang: str, limit: int) -> str:
    data = _get(
        {"action": "query", "prop": "revisions", "titles": title,
         "rvprop": "ids|timestamp|user|comment|size", "rvlimit": str(min(limit, 500)),
         "redirects": "1"},
        lang,
    )
    for page in (data.get("query", {}).get("pages") or {}).values():
        if "missing" in page:
            return f"[WIKIPEDIA] no page titled {title!r}"
        revs = page.get("revisions") or []
        if not revs:
            return f"[WIKIPEDIA] {title!r} has no revisions"
        lines = [f"# revision history — {page.get('title', title)} (newest first)"]
        for r in revs:
            lines.append(
                f"{r.get('timestamp')}  revid={r.get('revid')}  {r.get('size')}B  "
                f"{r.get('user')}  {str(r.get('comment') or '')[:110]}"
            )
        return "\n".join(lines)
    return f"[WIKIPEDIA] no page titled {title!r}"


def _do_first_with(title: str, needle: str, lang: str, limit: int) -> str:
    if not needle:
        return "[WIKIPEDIA] first_with needs a `needle` — the wikitext to look for."
    revs = _all_revisions(title, lang, min(limit, _MAX_REVISIONS))
    if not revs:
        return f"[WIKIPEDIA] no page titled {title!r}"
    key = needle.lower()

    def has(i: int) -> bool:
        return key in _revision_text(int(revs[i]["revid"]), lang).lower()

    if not has(len(revs) - 1):
        return (
            f"[WIKIPEDIA] {needle!r} is not present in the newest of the {len(revs)} revisions "
            f"examined for {title!r}. It was never added, was removed again, or is spelled "
            "differently in the wikitext (try the file name, not the caption)."
        )
    if has(0):
        return (
            f"[WIKIPEDIA] {needle!r} is already present in the OLDEST revision examined "
            f"({revs[0].get('timestamp')}, revid={revs[0].get('revid')}). It predates this "
            f"window of {len(revs)} revisions — raise `limit` for an earlier bound."
        )
    lo, hi = 0, len(revs) - 1  # has(lo) is False, has(hi) is True
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if has(mid):
            hi = mid
        else:
            lo = mid
    r = revs[hi]
    return (
        f"[WIKIPEDIA] {needle!r} first appears in revision {r.get('revid')} of "
        f"{title!r} at {r.get('timestamp')} by {r.get('user')} "
        f"(comment: {str(r.get('comment') or '')[:120]}).\n"
        f"Previous revision {revs[lo].get('revid')} at {revs[lo].get('timestamp')} does not "
        "contain it.\n"
        "Found by bisection over the revision list, which assumes the string stayed once added. "
        "If it was added, removed and re-added, this is AN introduction, not necessarily the "
        "first — check `history` around this date before answering."
    )


@tool(
    name="WikipediaAPI",
    description=(
        "Query the MediaWiki API directly (the built-in WebFetch is blocked from it by "
        "Wikimedia's robot policy). Actions: 'search' (find titles for `query`), 'page' "
        "(plain-text extract of `title`), 'history' (revisions of `title`, newest first, with "
        "timestamps/users/comments), 'images' (the File: names a page embeds — the wikitext "
        "spelling, which the rendered page never shows), 'revision' (the wikitext at `revid`, "
        "or as it stood on date `at`), 'first_with' (the oldest revision of `title` whose "
        "wikitext contains `needle` — this answers 'when was X first added to this page'; for "
        "an image, call 'images' first and pass the file name, never the caption). "
        "If first_with says the string is absent from the current revision, it was removed "
        "again or is rendered by a template — walk 'history' and read 'revision' yourself. "
        "Args: action, title, query, needle, revid, at, lang (default 'en'), limit (default 20)."
    ),
)
async def wikipedia_api_tool(
    action: str,
    title: str = "",
    query: str = "",
    needle: str = "",
    revid: str = "",
    at: str = "",
    lang: str = "en",
    limit: int = 20,
) -> str:
    """Read-only MediaWiki API access."""
    act = (action or "").strip().lower()
    lang = (lang or "en").strip() or "en"
    try:
        limit = max(1, int(limit))
    except Exception:  # noqa: BLE001
        limit = 20

    def _run() -> str:
        if act == "search":
            return _do_search(query or title, lang, min(limit, 50))
        if act == "page":
            return _do_page(title or query, lang)
        if act == "history":
            return _do_history(title or query, lang, limit)
        if act == "images":
            return _do_images(title or query, lang, limit)
        if act == "revision":
            return _do_revision(title or query, revid, at, lang)
        if act == "first_with":
            return _do_first_with(title or query, needle, lang, max(limit, 1000))
        return (
            f"[WIKIPEDIA] unknown action {action!r}. Use one of: "
            "search, page, history, images, revision, first_with."
        )

    try:
        return await asyncio.to_thread(_run)
    except Exception as exc:  # noqa: BLE001 — a tool must not raise into the run loop
        logger.warning("WikipediaAPI %s failed: %s", act, exc)
        return f"[WIKIPEDIA] {act} failed: {type(exc).__name__}: {exc}"


__all__ = ["wikipedia_api_tool"]


# See serper_search.py: the recorded target is what makes this survive a config
# YAML round-trip as a ``tool_registry.custom`` entry.
wikipedia_api_tool.__hx_target__ = "harnessx.tools.contrib.wikipedia_api.wikipedia_api_tool"
