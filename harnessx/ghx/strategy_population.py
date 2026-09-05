# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Strategy population — the pass-side twin of the motif table (M24 · 批改 #5).

The vendored ``digester_all_pass`` template has extracted a per-task
``strategy:`` tag ("the reusable strategy") since AEGIS's first commit — and
nothing has ever read it: not ``aggregate_digests`` (regexes only ``pattern``
and ``failure_mode``), not the Planner/Evolver templates, not the upstream
repo in any branch (verified against Darwin-Agent/HarnessX, 2026-08-21). This
module is the field's first consumer.

What it adds at the same seam the motif population rides
(``preprocess.aggregate_digests``, chained after whatever is already
installed there): a deterministic table — canonicalized strategy tag → the
passing tasks carrying it this round → how many of those tasks also passed
the previous three recorded rounds (a stability proxy read off
``data/task_history.jsonl``). Written to
``R{n}/graph_evidence/strategy_population.md`` with a short section appended
to the aggregate summary so the Planner finally sees "what works", not only
"what fails".

Canonicalization note: the digester improvises tag wording (measured
self-agreement on identical input: 0/6), so tags are normalized
(lowercase, non-alphanumerics collapsed to ``_``) before counting; the raw
spellings are preserved in the table for audit.

Flag: ``HARNESSX_GHX_STRATEGY_POP`` (call-time read, default off).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_STRATEGY_POP"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_PATTERN_RE = re.compile(r"^pattern:\s*(\S+)", re.M)
_STRATEGY_RE = re.compile(r"^strategy:\s*(\S+)", re.M)
_PASS_PATTERNS = {"ALL_PASS", "PASS"}
_STABLE_WINDOW = 3


def strategy_population_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


def canonical_tag(raw: str) -> str:
    """Normalize the digester's improvised tag wording to a countable key."""
    return re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")


@dataclass
class StrategyPopulation:
    round_n: int | None = None
    # canonical tag -> {"tasks": [ids], "raw": {spellings}, "stable": int}
    tags: dict = field(default_factory=dict)
    pass_count: int = 0

    @property
    def has_data(self) -> bool:
        return bool(self.tags)


def _pass_history(run_root: Path) -> "dict[str, list[tuple[int, bool]]]":
    """task_id -> [(round, passed)] from data/task_history.jsonl; {} when absent."""
    hist_path = run_root / "data" / "task_history.jsonl"
    out: dict[str, list] = defaultdict(list)
    if not hist_path.exists():
        return {}
    try:
        for line in hist_path.open(encoding="utf-8"):
            r = json.loads(line)
            flags = r.get("passed_flags") or [r.get("passed")]
            passed = any(bool(x) for x in flags if x is not None)
            out[str(r.get("task_id"))].append((int(r.get("round", -1)), passed))
    except Exception as exc:  # noqa: BLE001 — stability column degrades, table survives
        _LOG.warning("strategy population: task_history unreadable (%s)", exc)
        return {}
    return out


def _stable(task_id: str, hist: dict) -> bool:
    """Passed in the last _STABLE_WINDOW recorded rounds (needs >= that many)."""
    rows = sorted(hist.get(task_id, ()))
    if len(rows) < _STABLE_WINDOW:
        return False
    return all(p for _, p in rows[-_STABLE_WINDOW:])


def build_strategy_population(digests_dir) -> StrategyPopulation:
    digests_dir = Path(digests_dir)
    rep = StrategyPopulation()
    m = re.search(r"R(\d+)", digests_dir.parent.name)
    rep.round_n = int(m.group(1)) if m else None
    hist = _pass_history(digests_dir.parent.parent)
    for f in sorted(digests_dir.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pat = _PATTERN_RE.search(text)
        if not pat or pat.group(1) not in _PASS_PATTERNS:
            continue
        rep.pass_count += 1
        st = _STRATEGY_RE.search(text)
        if not st:
            continue
        raw = st.group(1)
        key = canonical_tag(raw)
        if not key:
            continue
        slot = rep.tags.setdefault(key, {"tasks": [], "raw": set(), "stable": 0})
        slot["tasks"].append(f.stem)
        slot["raw"].add(raw)
        if _stable(f.stem, hist):
            slot["stable"] += 1
    return rep


def render_strategy_population(rep: StrategyPopulation) -> str:
    L = [
        f"# Strategy populations — R{rep.round_n} (pass side; first consumer of the digester's `strategy:` tag)",
        "",
        f"Aggregated from {rep.pass_count} passing digests. Tags are canonicalized "
        "(the digester improvises wording); raw spellings kept for audit. "
        f"`stable` = the task also passed the previous {_STABLE_WINDOW} recorded rounds.",
        "",
        "| strategy (canonical) | tasks | stable | raw spellings |",
        "|---|---|---|---|",
    ]
    for key, slot in sorted(rep.tags.items(), key=lambda kv: -len(kv[1]["tasks"])):
        L.append(
            f"| `{key}` | {len(slot['tasks'])} | {slot['stable']} | {', '.join(sorted(slot['raw']))} |"
        )
    L += ["", "### Task lists (full ids)", ""]
    for key, slot in sorted(rep.tags.items(), key=lambda kv: -len(kv[1]["tasks"])):
        L.append(f"- `{key}` ({len(slot['tasks'])}): " + ", ".join(f"`{t}`" for t in slot["tasks"]))
    L.append("")
    return "\n".join(L)


def summary_section_strategy(rep: StrategyPopulation) -> str:
    top = sorted(rep.tags.items(), key=lambda kv: -len(kv[1]["tasks"]))[:5]
    L = [
        "",
        "## Strategy populations (graph_evidence/strategy_population.md — pass side)",
        "",
        "What is WORKING and how stably — use it to protect winning mechanisms "
        "when proposing edits, and to transplant strategies onto failing kin:",
        "",
    ]
    for key, slot in top:
        L.append(f"- `{key}` ×{len(slot['tasks'])} (stable {slot['stable']})")
    L.append("")
    return "\n".join(L)


_ORIGINAL_AGGREGATE = None


def aggregate_digests_with_strategy(*, digests_dir, summary_path, cluster_path=None) -> dict:
    """Chained drop-in for ``preprocess.aggregate_digests`` — runs whatever was
    installed before it (official, or the motif-population wrapper), then adds
    the strategy artifacts. Additive only."""
    _inner = _ORIGINAL_AGGREGATE
    if _inner is None:
        from harnessx.aegis.stages.preprocess import aggregate_digests as _inner

    result = _inner(digests_dir=digests_dir, summary_path=summary_path, cluster_path=cluster_path)
    try:
        rep = build_strategy_population(digests_dir)
        if rep.has_data:
            ge = Path(digests_dir).parent / "graph_evidence"
            ge.mkdir(parents=True, exist_ok=True)
            (ge / "strategy_population.md").write_text(
                render_strategy_population(rep), encoding="utf-8"
            )
            sp = Path(summary_path)
            if sp.exists():
                sp.write_text(
                    sp.read_text(encoding="utf-8", errors="replace") + summary_section_strategy(rep),
                    encoding="utf-8",
                )
    except Exception as exc:  # noqa: BLE001 — the inner aggregate already happened
        _LOG.warning("strategy population failed (additive, skipped): %s", exc)
    return result


@contextlib.contextmanager
def install_strategy_population():
    """Chain-patch the preprocess aggregate seam (install AFTER install_population
    in the launcher's with-stack so both sections land)."""
    global _ORIGINAL_AGGREGATE
    import harnessx.aegis.stages.preprocess as _pp

    original = _pp.aggregate_digests
    _ORIGINAL_AGGREGATE = original
    _pp.aggregate_digests = aggregate_digests_with_strategy
    try:
        yield
    finally:
        _pp.aggregate_digests = original
        _ORIGINAL_AGGREGATE = None
