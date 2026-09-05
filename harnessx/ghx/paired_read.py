# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Compare two arms by what CHANGED, not by their totals.

Four campaigns were read by subtracting one arm's score from the other's and
asking whether the difference cleared a noise envelope.  It never did, and it
could not have: at n≈100 the single-draw band is ±8 tasks while the plausible
effect is 5–11, so the design could only ever return "indistinguishable".

The band is wide because it prices *which tasks the bed drew*, and both arms
drew the same ones.  Hold the tasks fixed and that variance is gone: only the
tasks whose outcome differs between the arms carry any signal, and the question
becomes whether the fixes outnumber the breaks by more than a coin flip would.
Eight fixed against one broken is p≈0.04 — significant — while the same run read
as +7 tasks against ±8 is "no effect".  Same data, and only one of the two
readings is answering the question that was asked.

McNemar's exact test is used rather than the chi-square approximation: the
discordant counts here are single digits, which is exactly where the
approximation is known to be wrong.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class PairedResult:
    """One paired comparison of two arms over the same task set."""

    both_pass: list = field(default_factory=list)
    both_fail: list = field(default_factory=list)
    fixed: list = field(default_factory=list)  # failed in A, passes in B
    broken: list = field(default_factory=list)  # passed in A, fails in B
    missing: list = field(default_factory=list)  # not comparable — absent from an arm

    @property
    def n_paired(self) -> int:
        return len(self.both_pass) + len(self.both_fail) + len(self.fixed) + len(self.broken)

    @property
    def discordant(self) -> int:
        return len(self.fixed) + len(self.broken)

    @property
    def net(self) -> int:
        return len(self.fixed) - len(self.broken)

    @property
    def p_value(self) -> float:
        return mcnemar_exact(len(self.fixed), len(self.broken))

    def verdict(self, alpha: float = 0.05) -> str:
        if self.discordant == 0:
            return "identical — the arms disagree on no task, so there is nothing to test"
        if self.p_value <= alpha:
            direction = "B over A" if self.net > 0 else "A over B"
            return f"separated ({direction}, p={self.p_value:.3f})"
        return f"not separated (p={self.p_value:.3f}) — {self.discordant} task(s) disagree, net {self.net:+d}"


def mcnemar_exact(fixed: int, broken: int) -> float:
    """Two-sided exact McNemar p-value for ``fixed`` vs ``broken`` discordants.

    Under the null the two are exchangeable, so the count of one is Binomial(n,
    ½) with n their sum: the p-value is the two-sided tail beyond the more
    extreme of them.  Returns 1.0 when nothing disagrees.
    """
    n = fixed + broken
    if n == 0:
        return 1.0
    k = min(fixed, broken)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * tail)


def pair_arms(arm_a: dict, arm_b: dict) -> PairedResult:
    """Cross two ``{task_id: passed}`` maps into a paired result.

    A task missing from either arm is reported, never guessed: an absent task is
    not a failure, and counting it as one is how a crashed rollout turns into a
    regression that never happened.
    """
    res = PairedResult()
    for tid in sorted(set(arm_a) | set(arm_b)):
        if tid not in arm_a or tid not in arm_b:
            res.missing.append(tid)
            continue
        a, b = bool(arm_a[tid]), bool(arm_b[tid])
        if a and b:
            res.both_pass.append(tid)
        elif not a and not b:
            res.both_fail.append(tid)
        elif b:
            res.fixed.append(tid)
        else:
            res.broken.append(tid)
    return res


def render(res: PairedResult, name_a: str = "A", name_b: str = "B", limit: int = 12) -> str:
    """A markdown block a reader can check the arithmetic of."""
    lines = [
        f"## Paired read — {name_a} vs {name_b}",
        "",
        f"Paired over {res.n_paired} task(s). **{res.verdict()}**",
        "",
        f"|  | {name_b} passes | {name_b} fails |",
        "|---|---|---|",
        f"| **{name_a} passes** | {len(res.both_pass)} | {len(res.broken)} (broken) |",
        f"| **{name_a} fails** | {len(res.fixed)} (fixed) | {len(res.both_fail)} |",
        "",
        f"Totals would read {len(res.both_pass) + len(res.broken)} → "
        f"{len(res.both_pass) + len(res.fixed)}, a difference of {res.net:+d}; "
        f"the paired test reads the {res.discordant} task(s) that actually moved.",
        "",
    ]
    for label, ids in (("Fixed", res.fixed), ("Broken", res.broken)):
        if ids:
            shown = ", ".join(f"`{t}`" for t in ids[:limit])
            more = f" … +{len(ids) - limit} more" if len(ids) > limit else ""
            lines += [f"**{label} ({len(ids)})**: {shown}{more}", ""]
    if res.missing:
        lines += [
            f"**Not comparable ({len(res.missing)})** — absent from one arm, excluded rather than "
            "counted as failures.",
            "",
        ]
    return "\n".join(lines)


def arm_from_task_history(path, round_n: int | None = None) -> dict:
    """``{task_id: passed}`` from a run's ``data/task_history.jsonl``.

    With no ``round_n`` the latest non-carried row per task wins, which is the
    arm's final state; carried rows are skipped because they are a copy of an
    earlier round's draw, not a fresh one.
    """
    import json
    from pathlib import Path

    best: dict = {}
    p = Path(path)
    if p.is_dir():
        p = p / "data" / "task_history.jsonl"
    if not p.exists():
        return {}
    for line in p.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("carried"):
            continue
        r = int(row.get("round", -1))
        if round_n is not None and r != round_n:
            continue
        tid = str(row.get("task_id"))
        if tid not in best or r >= best[tid][0]:
            best[tid] = (r, bool(row.get("passed")))
    return {tid: passed for tid, (_, passed) in best.items()}


__all__ = ["PairedResult", "arm_from_task_history", "mcnemar_exact", "pair_arms", "render"]
