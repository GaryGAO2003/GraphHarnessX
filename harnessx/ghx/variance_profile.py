# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Variance profile — a per-round, per-task instability x fixability read (M27 T2.1).

The M27 overnight survey (``docs/ghx-overnight-0823-research.md``) measured two
things this module exists to make visible every round instead of once, offline:

* **W2·B3** — no role ever saw a fate-bucket / conversion prior. ``flip_ledger.md``
  (M26 on) carries the raw pass/fail matrix and this round's failure labels, but not
  a bucket verdict or a fixability read — a task that has both passed and failed is
  listed the same way whether it is a coin-flip swinger or a task with a nameable,
  fixable instability.
* **W4·C1** — a 63-task cross-campaign census of exactly that "both passed and
  failed" population found the dominant fixable shape is **long-then-wrong**: 22/28
  of the localized-fixable tasks separate on ``total_steps`` alone — the failing
  runs run much longer than the same task's passing runs, and still terminate
  normally (``done``) with a wrong answer rather than dying on budget (62%
  done-wrong vs 38% budget-death in that pool). That census was a one-time offline
  script pass over ``experiments/analysis/overnight_0823/``; this module is the
  mechanical, in-loop, every-round version of the same read, scoped to what
  ``task_history.jsonl`` alone can answer (no session-trace parsing — see the
  module-level cost note below).

**What counts as "unstable" here** (deliberately broader than flip_ledger's
"swinger" bucket — a task need not have flipped yet to be worth watching): a task
with both a pass and a fail recorded so far in this campaign, OR a task with
``pass_rate < 0.8`` over ``>= 3`` observations. The first clause is exactly
flip_ledger's swinger bucket; the second additionally surfaces near-total-failure
tasks with enough draws that FUTURE conversion (or its absence) is a legible
question — a chronic-fail task with 2 observations is not yet distinguishable from
a lottery loss, but one with 5 is.

**Cost discipline.** This module reads ``data/task_history.jsonl`` only — the same
file :mod:`harnessx.ghx.flip_ledger` reads, twice through (once via
:func:`harnessx.ghx.flip_ledger._read_task_history` for the pass/carry/bucket
matrix — reused rather than re-derived, so the two modules can never disagree on
what a "pass" or a "carried row" means; once locally for the ``steps``/``exit``
columns ``TaskFlip`` does not carry). No digest, trajectory, or session file is
opened. On a 103-task x 16-round history (~1,650 lines) both passes together run
in well under a second — this is a linear scan of a small JSONL file, not an
analysis. Degrades to ``None`` (never raises) on any missing/unreadable/malformed
input; the caller logs and moves on, exactly like flip_ledger.

Output: ``R{round_n}/graph_evidence/variance_profile.md`` (rendered table, for
role prompts) and ``variance_profile.json`` (same data, for tooling/tests) — same
directory flip_ledger.md and population.md land in.

Flag: ``HARNESSX_GHX_VARIANCE_PROFILE`` (call-time read, default off). Installed on
the same ``preprocess.aggregate_digests`` chain-patch seam flip_ledger uses
(:mod:`harnessx.ghx.round_router`), so ordering against flip_ledger/population is
cosmetic, not load-bearing — each rebind captures whatever was bound at ITS entry
and chains through it.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import flip_ledger as _fl

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_VARIANCE_PROFILE"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

# exit values that mean "ran out of budget" rather than "finished and was wrong" —
# mirrors docs/agents.md's exit_reason vocabulary ("done" | "budget_exceeded" |
# "loop_detected" | "error"); task_history's "exit" column is sourced from the
# same field (harnessx/aegis/data/ledger.py: exit=r.get("exit", r.get("exit_reason"))).
_BUDGET_EXIT_VALUES = frozenset({"budget_exceeded"})
_UNKNOWN_EXIT = "(unknown)"


def variance_profile_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


# ── task_history, second pass (steps/exit — TaskFlip does not carry these) ────────


def _read_task_detail(run_dir) -> "dict[tuple[str, int], dict]":
    """(task_id, round) -> {"steps": int, "exit": str} — same file, same dedup
    convention as :func:`harnessx.ghx.flip_ledger._read_task_history` (last row for
    a duplicate (task_id, round) pair wins). Never raises; {} on any failure."""
    path = Path(run_dir) / "data" / "task_history.jsonl"
    out: dict = {}
    if not path.exists():
        return out
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            raw_lines = f.readlines()
    except OSError as exc:
        _LOG.warning("variance profile: task_history.jsonl unreadable (%s)", exc)
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
        out[(str(tid), rnd)] = {
            "steps": int(row.get("steps", 0) or 0),
            "exit": str(row.get("exit", row.get("exit_reason", "")) or ""),
        }
    return out


def _is_unstable(n_pass: int, n_obs: int) -> bool:
    if n_obs == 0:
        return False
    if 0 < n_pass < n_obs:  # has both a pass and a fail — flip_ledger's swinger
        return True
    return (n_pass / n_obs) < 0.8 and n_obs >= 3


# ── report ───────────────────────────────────────────────────────────────────


@dataclass
class TaskVarianceRow:
    task_id: str
    level: object = ""
    bucket: "str | None" = None
    n_pass: int = 0
    n_obs: int = 0
    flip_count: int = 0
    median_pass_steps: "float | None" = None
    median_fail_steps: "float | None" = None
    fail_exit_counts: Counter = field(default_factory=Counter)
    long_then_wrong: bool = False

    @property
    def pass_rate(self) -> "float | None":
        return (self.n_pass / self.n_obs) if self.n_obs else None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "level": self.level,
            "bucket": self.bucket,
            "n_pass": self.n_pass,
            "n_obs": self.n_obs,
            "pass_rate": self.pass_rate,
            "flip_count": self.flip_count,
            "median_pass_steps": self.median_pass_steps,
            "median_fail_steps": self.median_fail_steps,
            "fail_exit_counts": dict(self.fail_exit_counts),
            "long_then_wrong": self.long_then_wrong,
        }


@dataclass
class VarianceProfileReport:
    history_round: int = 0
    total_tasks: int = 0
    rows: list = field(default_factory=list)  # TaskVarianceRow, unstable only

    @property
    def has_data(self) -> bool:
        return self.total_tasks > 0

    def to_dict(self) -> dict:
        return {
            "history_round": self.history_round,
            "total_tasks": self.total_tasks,
            "unstable_count": len(self.rows),
            "rows": [r.to_dict() for r in self.rows],
        }


def build_variance_profile(run_dir, round_n: int) -> "VarianceProfileReport | None":
    """The mechanical, in-loop version of the W4·C1 census, scoped to one round's
    ``task_history.jsonl`` snapshot. Returns ``None`` (never raises) when there is
    no usable task history — the caller logs and treats it exactly like "no
    evidence materialised", never a hard failure."""
    try:
        tasks = _fl._read_task_history(run_dir)
    except Exception as exc:  # noqa: BLE001 — must never sink a round
        _LOG.warning("variance profile: task_history read failed (%s)", exc)
        return None
    if not tasks:
        _LOG.warning("variance profile: no usable task_history under %s", run_dir)
        return None

    detail = _read_task_detail(run_dir)
    rep = VarianceProfileReport(history_round=round_n, total_tasks=len(tasks))

    for tf in sorted(tasks.values(), key=lambda t: t.task_id):
        n_pass, n_obs = tf.n_pass, tf.n_obs
        if not _is_unstable(n_pass, n_obs):
            continue

        pass_steps: list = []
        fail_steps: list = []
        fail_exits: Counter = Counter()
        flips = 0
        prev: "bool | None" = None
        for rnd, (passed, carried) in sorted(tf.rounds.items()):
            if carried:
                continue
            d = detail.get((tf.task_id, rnd), {})
            steps = d.get("steps")
            if passed:
                if steps is not None:
                    pass_steps.append(steps)
            else:
                if steps is not None:
                    fail_steps.append(steps)
                fail_exits[d.get("exit") or _UNKNOWN_EXIT] += 1
            if prev is not None and passed != prev:
                flips += 1
            prev = passed

        median_pass = statistics.median(pass_steps) if pass_steps else None
        median_fail = statistics.median(fail_steps) if fail_steps else None
        dominant_fail_exit = fail_exits.most_common(1)[0][0] if fail_exits else None
        long_then_wrong = bool(
            median_pass is not None
            and median_fail is not None
            and median_fail > median_pass
            and dominant_fail_exit is not None
            and dominant_fail_exit not in _BUDGET_EXIT_VALUES
        )

        rep.rows.append(
            TaskVarianceRow(
                task_id=tf.task_id,
                level=tf.level,
                bucket=tf.bucket,
                n_pass=n_pass,
                n_obs=n_obs,
                flip_count=flips,
                median_pass_steps=median_pass,
                median_fail_steps=median_fail,
                fail_exit_counts=fail_exits,
                long_then_wrong=long_then_wrong,
            )
        )
    return rep


def render_variance_profile(rep: VarianceProfileReport) -> str:
    long_rows = [r for r in rep.rows if r.long_then_wrong]
    lines = [
        f"# Variance profile — history round {rep.history_round} "
        f"(unstable tasks: pass+fail so far, or pass rate < 0.8 over >=3 draws)",
        "",
        f"Census over `data/task_history.jsonl` ({rep.total_tasks} tasks tracked): "
        f"{len(rep.rows)} unstable ({len(long_rows)} flagged `long_then_wrong`).",
        "",
        "`long_then_wrong` (docs/ghx-overnight-0823-research.md §W4·C1 — the",
        "dominant fixable shape, 22/28 of that census's localized-fixable pool):",
        "failing rounds run longer (median steps) than this task's own passing",
        "rounds, AND the failures terminate normally (`done`) rather than dying on",
        "`budget_exceeded` — a nameable stall-then-guess pattern, not budget",
        "starvation and not raw sampling noise.",
        "",
        "| task_id | level | bucket | pass n/N (rate) | flips | median steps pass/fail | fail exit anatomy | long_then_wrong |",
        "|---|---|---|---|---|---|---|---|",
    ]
    if rep.rows:
        for r in rep.rows:
            rate = f"{r.pass_rate:.0%}" if r.pass_rate is not None else "?"
            mp = f"{r.median_pass_steps:g}" if r.median_pass_steps is not None else "-"
            mf = f"{r.median_fail_steps:g}" if r.median_fail_steps is not None else "-"
            anatomy = ", ".join(f"{k}:{v}" for k, v in r.fail_exit_counts.most_common()) or "(none)"
            lines.append(
                f"| `{r.task_id[:8]}` | {r.level} | {r.bucket or '?'} | "
                f"{r.n_pass}/{r.n_obs} ({rate}) | {r.flip_count} | {mp}/{mf} | "
                f"{anatomy} | {'YES' if r.long_then_wrong else ''} |"
            )
    else:
        lines.append("| (no unstable tasks this round) |  |  |  |  |  |  |  |")
    lines += [
        "",
        "## Highest-value targets (long_then_wrong)",
        "",
    ]
    if long_rows:
        for r in long_rows:
            lines.append(
                f"- `{r.task_id}` — median {r.median_pass_steps:g} steps passing vs "
                f"{r.median_fail_steps:g} steps failing, fails end "
                f"{', '.join(f'{k} x{v}' for k, v in r.fail_exit_counts.most_common())}"
            )
    else:
        lines.append("(none this round)")
    lines.append("")
    return "\n".join(lines)


# ── seam ──────────────────────────────────────────────────────────────────────

_ORIGINAL_AGGREGATE = None


def aggregate_digests_with_variance_profile(*, digests_dir, summary_path, cluster_path=None) -> dict:
    """Chained drop-in for ``preprocess.aggregate_digests`` — same shape as
    flip_ledger's own chain wrapper, own storage cell, composes in either
    install order with flip_ledger/population's wrappers."""
    _inner = _ORIGINAL_AGGREGATE
    if _inner is None:
        from harnessx.aegis.stages.preprocess import aggregate_digests as _inner

    result = _inner(digests_dir=digests_dir, summary_path=summary_path, cluster_path=cluster_path)
    try:
        digests_dir_p = Path(digests_dir)
        run_dir = digests_dir_p.parent.parent
        history_round = _fl._max_history_round(run_dir)
        if history_round is not None:
            rep = build_variance_profile(run_dir, history_round)
            if rep is not None and rep.has_data:
                ge = digests_dir_p.parent / "graph_evidence"
                ge.mkdir(parents=True, exist_ok=True)
                (ge / "variance_profile.md").write_text(render_variance_profile(rep), encoding="utf-8")
                (ge / "variance_profile.json").write_text(
                    json.dumps(rep.to_dict(), indent=2), encoding="utf-8"
                )
    except Exception as exc:  # noqa: BLE001 — the inner aggregate already happened
        _LOG.warning("variance profile failed (additive, skipped): %s", exc)
    return result


@contextlib.contextmanager
def install_variance_profile():
    """Chain-patch the same preprocess aggregate seam flip_ledger/population use."""
    global _ORIGINAL_AGGREGATE
    import harnessx.aegis.stages.preprocess as _pp

    original = _pp.aggregate_digests
    _ORIGINAL_AGGREGATE = original
    _pp.aggregate_digests = aggregate_digests_with_variance_profile
    try:
        yield
    finally:
        _pp.aggregate_digests = original
        _ORIGINAL_AGGREGATE = None


# ── offline CLI (retrospective use, same shape as flip_ledger's) ──────────────


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harnessx.ghx.variance_profile")
    parser.add_argument("run_dir")
    parser.add_argument("--round", type=int, dest="round_n", required=True)
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    rep = build_variance_profile(args.run_dir, args.round_n)
    if rep is None or not rep.has_data:
        print("variance profile: no usable task_history — nothing to render", file=sys.stderr)
        return 1
    md = render_variance_profile(rep)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
    else:
        print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))


__all__ = [
    "FLAG",
    "TaskVarianceRow",
    "VarianceProfileReport",
    "build_variance_profile",
    "render_variance_profile",
    "install_variance_profile",
    "variance_profile_enabled",
]
