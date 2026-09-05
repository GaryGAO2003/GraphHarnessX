# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Flip ledger — the cross-round pass matrix stitched to this round's diagnosis (M25 seam).

M25 measured the gap this closes: each batch's ~17 "sometimes pass, sometimes
fail" tasks get a failure_mode label from the Digester every round, but those
labels live one-per-digest-file and are never placed side by side. The
"unverified commit" disease sat in 7/17 of a batch's failures for 14 rounds
before anyone noticed, because noticing it required opening 14 rounds of
digests by hand and counting a free-text tag across them. This module does
that counting, mechanically, every round: the per-task pass/fail matrix from
``data/task_history.jsonl`` crossed with this round's ``failure_mode``/
``strategy`` tags read off the digests that already exist.

Round alignment trap (read this before touching a round number here). The
``R{k}`` directory a round's digests live under and the ``round`` integer
``task_history.jsonl`` records for that batch are NOT guaranteed to be the
same number — M25 measured ``R13/``'s digests corresponding to history round
12. Nothing in this module derives a history round from an ``R{k}`` directory
name. In-loop, the seam below installs at the same point ``population``/
``strategy_population`` do (``preprocess.aggregate_digests``), which fires
after every digest is written and after ``task_history.jsonl`` has already
been appended to for this batch (history is written at batch end, before the
meta session starts) — so the correct history round at that moment is
``max(round)`` over the file, never a parse of ``digests_dir``'s parent name.
The offline CLI has no such moment to read off, so it takes
``--history-round`` from the caller instead of guessing.

Output: ``R{n}/graph_evidence/flip_ledger.md`` (same directory population.md
lands in). No summary.md section — the Evolver is pointed at this file via
``guidance.py``'s ``map.md`` stitch, same as population.md.

Flag: ``HARNESSX_GHX_FLIP_LEDGER`` (call-time read, default off).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_FLIP_LEDGER"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

_STRATEGY_RE = re.compile(r"^strategy:\s*(\S+)")
_FAILURE_MODE_RE = re.compile(r"^failure_mode:\s*(\S+)")
_DIGEST_HEAD_LINES = 12

_NO_DIGEST = "(no digest)"
_UNREADABLE = "(digest unreadable)"
_NO_FIELD = "(none)"
_PLACEHOLDERS = frozenset({_NO_DIGEST, _UNREADABLE, _NO_FIELD})

_LABEL_NOTE = (
    "labels are free text — cluster them yourself; a family of >=3 across "
    "different tasks is a structural disease worth one candidate; any "
    "candidate targeting it MUST list predicted task ids from this table"
)

_FLIP_NOTE = (
    "Reading discipline: a swinger flipping is not a regression signal by "
    "itself — this bed's same-config batches swing individual tasks by "
    "themselves (the measured ±5 envelope applies here too). A candidate "
    "citing this table must name its predicted task ids from it (full ids, "
    "not the 8-char column) — the scope gate charges predictions against "
    "sub_resolution, and a swinger reverting on its own is not evidence the "
    "candidate did anything."
)


def flip_ledger_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


# ── task history × per-task flip state ─────────────────────────────────────────


@dataclass
class TaskFlip:
    task_id: str
    level: object = ""
    rounds: dict = field(default_factory=dict)  # round -> (passed, carried)

    @property
    def _sorted(self) -> list:
        return sorted(self.rounds.items())

    @property
    def pattern(self) -> str:
        return "".join("~" if c else ("#" if p else ".") for _, (p, c) in self._sorted)

    @property
    def n_pass(self) -> int:
        return sum(1 for _, (p, c) in self._sorted if not c and p)

    @property
    def n_obs(self) -> int:
        return sum(1 for _, (_p, c) in self._sorted if not c)

    @property
    def bucket(self) -> "str | None":
        """always / swinger / never over non-carried rows only; None when every
        recorded row for this task is carried (no real draw ever happened)."""
        n, big_n = self.n_pass, self.n_obs
        if big_n == 0:
            return None
        if n == big_n:
            return "always"
        if n == 0:
            return "never"
        return "swinger"

    def passed_at(self, round_n: int):
        return self.rounds.get(round_n)


def _read_task_history(run_dir) -> "dict[str, TaskFlip]":
    """task_id -> TaskFlip from data/task_history.jsonl; {} on any total failure.

    A row missing task_id/round is skipped; a duplicate (task_id, round) pair
    keeps the LAST row seen (matches the k-aware dict-keyed convention in
    regression_triage's ``_task_flags_by_round``). Never raises.
    """
    path = Path(run_dir) / "data" / "task_history.jsonl"
    out: dict = {}
    if not path.exists():
        _LOG.warning("flip ledger: task_history.jsonl missing under %s", path.parent)
        return out
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            raw_lines = f.readlines()
    except OSError as exc:
        _LOG.warning("flip ledger: task_history.jsonl unreadable (%s)", exc)
        return out
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        tid = row.get("task_id")
        if not tid or "round" not in row:
            continue
        try:
            rnd = int(row["round"])
        except (TypeError, ValueError):
            continue
        level = row.get("level", "")
        tf = out.get(str(tid))
        if tf is None:
            tf = TaskFlip(task_id=str(tid), level=level)
            out[str(tid)] = tf
        elif level != "":
            tf.level = level
        tf.rounds[rnd] = (bool(row.get("passed", False)), bool(row.get("carried", False)))
    if not out:
        _LOG.warning("flip ledger: task_history.jsonl at %s had no usable rows", path)
    return out


def _max_history_round(run_dir) -> "int | None":
    """The in-loop round number: max(round) over task_history.jsonl right now."""
    tasks = _read_task_history(run_dir)
    best = None
    for tf in tasks.values():
        for rnd in tf.rounds:
            if best is None or rnd > best:
                best = rnd
    return best


# ── this round's digests ────────────────────────────────────────────────────


@dataclass
class DigestHead:
    exists: bool = False
    unreadable: bool = False
    filename: str = ""
    strategy: "str | None" = None
    strategy_line: "int | None" = None
    failure_mode: "str | None" = None
    failure_mode_line: "int | None" = None


def _read_digest_head(digests_dir, task_id: str) -> DigestHead:
    """Only the first _DIGEST_HEAD_LINES lines — pattern/strategy/failure_mode
    live in the frontmatter, and staying off the body avoids stray matches."""
    path = Path(digests_dir) / f"{task_id}.md"
    if not path.exists():
        return DigestHead(exists=False)
    head = DigestHead(exists=True, filename=path.name)
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        head.unreadable = True
        return head
    for i, raw in enumerate(lines[:_DIGEST_HEAD_LINES], start=1):
        line = raw.rstrip("\n")
        m = _STRATEGY_RE.match(line)
        if m:
            head.strategy = m.group(1)
            head.strategy_line = i
            continue
        m = _FAILURE_MODE_RE.match(line)
        if m:
            head.failure_mode = m.group(1)
            head.failure_mode_line = i
    return head


def _fm_raw(head: DigestHead) -> str:
    if not head.exists:
        return _NO_DIGEST
    if head.unreadable:
        return _UNREADABLE
    return head.failure_mode or _NO_FIELD


def _strategy_raw(head: DigestHead) -> str:
    if not head.exists:
        return _NO_DIGEST
    if head.unreadable:
        return _UNREADABLE
    return head.strategy or _NO_FIELD


def _wrap(raw: str) -> str:
    return raw if raw in _PLACEHOLDERS else f"`{raw}`"


def _anchor(head: DigestHead, line: "int | None") -> str:
    if not head.exists:
        return _NO_DIGEST
    if head.unreadable:
        return _UNREADABLE
    loc = f"#L{line}" if line else ""
    return f"`digests/{head.filename}{loc}`"


def _scan_leaks(digests_dir) -> list:
    """Every digest this round (pass or fail) whose strategy: line mentions
    'leak', case-insensitive. Independent of task_history — a whole-round scan."""
    digests_dir = Path(digests_dir)
    out: list = []
    if not digests_dir.exists():
        return out
    for path in sorted(digests_dir.glob("*.md")):
        try:
            with path.open(encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            continue
        for i, raw in enumerate(lines[:_DIGEST_HEAD_LINES], start=1):
            m = _STRATEGY_RE.match(raw.rstrip("\n"))
            if m and "leak" in m.group(1).lower():
                out.append({"task_id": path.stem, "strategy_raw": m.group(1), "anchor": f"`digests/{path.name}#L{i}`"})
                break
    return out


# ── report ───────────────────────────────────────────────────────────────────


@dataclass
class FlipLedgerReport:
    history_round: int = 0
    total_tasks: int = 0
    always: int = 0
    swinger: int = 0
    never: int = 0
    ever_passed: int = 0
    batch_pass: int = 0
    batch_total: int = 0
    batch_carried: int = 0
    swinger_rows: list = field(default_factory=list)
    never_rows: list = field(default_factory=list)
    leak_rows: list = field(default_factory=list)
    label_counts: Counter = field(default_factory=Counter)
    label_tasks: dict = field(default_factory=dict)

    @property
    def has_data(self) -> bool:
        return self.total_tasks > 0


def build_flip_ledger(run_dir, digests_dir, history_round: int) -> FlipLedgerReport:
    digests_dir = Path(digests_dir)
    tasks = _read_task_history(run_dir)
    rep = FlipLedgerReport(history_round=history_round, total_tasks=len(tasks))
    if not tasks:
        return rep

    for tf in tasks.values():
        bucket = tf.bucket
        if bucket == "always":
            rep.always += 1
        elif bucket == "swinger":
            rep.swinger += 1
        elif bucket == "never":
            rep.never += 1
        row = tf.passed_at(history_round)
        if row is not None:
            passed, carried = row
            rep.batch_total += 1
            if carried:
                rep.batch_carried += 1
            elif passed:
                rep.batch_pass += 1
    rep.ever_passed = rep.always + rep.swinger

    for tf in sorted(tasks.values(), key=lambda t: t.task_id):
        row = tf.passed_at(history_round)
        # a carried row at history_round is a copy-forward, not a fresh draw —
        # it does not make this task "this round's failure" either
        failing_now = row is not None and not row[0] and not row[1]
        if tf.bucket == "swinger" and failing_now:
            head = _read_digest_head(digests_dir, tf.task_id)
            fm_raw = _fm_raw(head)
            rep.swinger_rows.append(
                {
                    "task_id": tf.task_id,
                    "level": tf.level,
                    "n_pass": tf.n_pass,
                    "n_obs": tf.n_obs,
                    "pattern": tf.pattern,
                    "fm_raw": fm_raw,
                    "strategy_raw": _strategy_raw(head),
                    "anchor": _anchor(head, head.failure_mode_line),
                }
            )
            rep.label_counts[fm_raw] += 1
            rep.label_tasks.setdefault(fm_raw, []).append(tf.task_id)
        elif tf.bucket == "never":
            head = _read_digest_head(digests_dir, tf.task_id)
            rep.never_rows.append(
                {"task_id": tf.task_id, "level": tf.level, "n_obs": tf.n_obs, "fm_raw": _fm_raw(head)}
            )

    rep.leak_rows = _scan_leaks(digests_dir)
    return rep


def render_flip_ledger(rep: FlipLedgerReport) -> str:
    lines = [
        f"# Flip ledger — history round {rep.history_round} (cross-round pass matrix x this round's diagnosis)",
        "",
        f"Census over `data/task_history.jsonl` ({rep.total_tasks} tasks tracked): "
        f"always {rep.always} / swinger {rep.swinger} / never {rep.never} / "
        f"union ever-passed {rep.ever_passed}/{rep.total_tasks}.",
        "",
        f"This round's batch (history round {rep.history_round}): {rep.batch_pass}/{rep.batch_total} passed "
        f"({rep.batch_carried} carried row(s), excluded from that numerator).",
        "",
        "## This round's failing swingers (the actionable set)",
        "",
        "A swinger flips pass/fail across rounds instead of sitting chronically "
        "failed; listed here are swingers that are DOWN this round. Pattern reads "
        "oldest -> newest round: `#` passed, `.` failed, `~` carried (noop-audit "
        "carry-forward — excluded from `passed n/N`).",
        "",
        "| task_id | level | passed n/N | pattern | failure_mode | strategy | digest anchor |",
        "|---|---|---|---|---|---|---|",
    ]
    if rep.swinger_rows:
        for r in rep.swinger_rows:
            lines.append(
                f"| `{r['task_id'][:8]}` | {r['level']} | {r['n_pass']}/{r['n_obs']} | "
                f"`{r['pattern']}` | {_wrap(r['fm_raw'])} | {_wrap(r['strategy_raw'])} | {r['anchor']} |"
            )
    else:
        lines.append("| (none this round) |  |  |  |  |  |  |")
    lines += [
        "",
        "## Failure-mode labels, this round's failing swingers (exact string — no clustering here)",
        "",
        "| failure_mode | count | tasks |",
        "|---|---|---|",
    ]
    for label, count in rep.label_counts.most_common():
        tids = rep.label_tasks.get(label, [])
        lines.append(f"| {_wrap(label)} | {count} | " + ", ".join(f"`{t}`" for t in tids) + " |")
    if not rep.label_counts:
        lines.append("| (none) |  |  |")
    lines += [
        "",
        _LABEL_NOTE,
        "",
        "## Never-pass (chronic — not this table's target)",
        "",
        "| task_id | level | rounds observed | this round's failure_mode |",
        "|---|---|---|---|",
    ]
    if rep.never_rows:
        for r in rep.never_rows:
            lines.append(f"| `{r['task_id']}` | {r['level']} | {r['n_obs']} | {_wrap(r['fm_raw'])} |")
    else:
        lines.append("| (none) |  |  |  |")
    lines += [
        "",
        '## Leak scan (this round\'s digests, strategy: line containing "leak")',
        "",
    ]
    if rep.leak_rows:
        lines += ["| task_id | strategy | anchor |", "|---|---|---|"]
        for r in rep.leak_rows:
            lines.append(f"| `{r['task_id']}` | {_wrap(r['strategy_raw'])} | {r['anchor']} |")
    else:
        lines.append("none observed this round")
    lines += ["", "## Reading discipline", "", _FLIP_NOTE, ""]
    return "\n".join(lines)


# ── seam ──────────────────────────────────────────────────────────────────────

_ORIGINAL_AGGREGATE = None


def aggregate_digests_with_flip_ledger(*, digests_dir, summary_path, cluster_path=None) -> dict:
    """Chained drop-in for ``preprocess.aggregate_digests``: runs whatever was
    installed before it (official, or population/strategy_population's wrappers),
    then writes flip_ledger.md. Additive only — no summary.md change; the Evolver
    pointer lives in guidance.py's map.md stitch."""
    _inner = _ORIGINAL_AGGREGATE
    if _inner is None:
        from harnessx.aegis.stages.preprocess import aggregate_digests as _inner

    result = _inner(digests_dir=digests_dir, summary_path=summary_path, cluster_path=cluster_path)
    try:
        digests_dir_p = Path(digests_dir)
        run_dir = digests_dir_p.parent.parent
        history_round = _max_history_round(run_dir)
        if history_round is not None:
            rep = build_flip_ledger(run_dir, digests_dir_p, history_round)
            if rep.has_data:
                ge = digests_dir_p.parent / "graph_evidence"
                ge.mkdir(parents=True, exist_ok=True)
                with (ge / "flip_ledger.md").open("w", encoding="utf-8") as f:
                    f.write(render_flip_ledger(rep))
    except Exception as exc:  # noqa: BLE001 — the inner aggregate already happened
        _LOG.warning("flip ledger failed (additive, skipped): %s", exc)
    return result


@contextlib.contextmanager
def install_flip_ledger():
    """Chain-patch the same preprocess aggregate seam population/strategy_population
    use — the one place a round hands us digests_dir already resolved, which also
    supplies the moment the round-alignment trap (module docstring) needs."""
    global _ORIGINAL_AGGREGATE
    import harnessx.aegis.stages.preprocess as _pp

    original = _pp.aggregate_digests
    _ORIGINAL_AGGREGATE = original
    _pp.aggregate_digests = aggregate_digests_with_flip_ledger
    try:
        yield
    finally:
        _pp.aggregate_digests = original
        _ORIGINAL_AGGREGATE = None


# ── offline CLI (M25 retrospective use) ────────────────────────────────────────


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harnessx.ghx.flip_ledger")
    parser.add_argument("run_dir")
    parser.add_argument("digests_dir")
    parser.add_argument("--history-round", type=int, required=True)
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    rep = build_flip_ledger(args.run_dir, args.digests_dir, args.history_round)
    if not rep.has_data:
        print("flip ledger: no usable task_history — nothing to render", file=sys.stderr)
        return 1
    md = render_flip_ledger(rep)
    if args.out:
        with Path(args.out).open("w", encoding="utf-8") as f:
            f.write(md)
    else:
        print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
