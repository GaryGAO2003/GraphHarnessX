# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Offline majority@k simulation over the probe trials' parent-arm reps.

Zero gold exposure: a rep's ``passed`` flag was adjudicated at trial time, so
"the modal answer is correct" is decided by whether that answer string is the
answer of some passed rep.  Ties are conservative: unless every tied answer is
a passing one, the vote FAILS (that is exactly the "external discrimination"
a plain majority lacks).

For each (batch, task): pass@1 (mean of passed), exact majority@k for
k in {3,5,10} (expectation over all C(n,k) rep subsets), and a shape label:
consensus-right / consensus-wrong (modal share >= 0.5) / scatter.

Feeds CH7 7.5: does plain majority procure the wrong-closure cluster, or does
consensus lock in the confident-wrong answer?
"""

import argparse
import json
import re
from itertools import combinations
from collections import Counter

DIRTY = ("8b3379c0", "8131e2c0")
ANS = re.compile(r"FINAL ANSWER:\s*(.+?)\s*$", re.M | re.S)


def answer_of(rep) -> str | None:
    m = list(ANS.finditer(rep.get("tail") or ""))
    if not m:
        return None
    return re.sub(r"\s+", " ", m[-1].group(1)).strip().lower() or None


def vote(answers, good):
    """One subset's verdict: modal answer; ties fail unless all tied are good."""
    c = Counter(a for a in answers if a is not None)
    if not c:
        return False
    top = max(c.values())
    tied = [a for a, n in c.items() if n == top]
    return all(a in good for a in tied)


def majority_at_k(reps, k, good):
    n = len(reps)
    if n < k:
        return None
    subs = list(combinations(range(n), k))
    wins = sum(1 for idx in subs if vote([reps[i] for i in idx], good))
    return wins / len(subs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", help="Campaign runs directory (default: GHX_RUNS_ROOT or repository runs)")
    args = parser.parse_args()
    from run_paths import require_path, runs_root

    try:
        D5 = require_path(runs_root(args.runs_root) / "PROBE_DOSSIER5", "PROBE_DOSSIER5 run")
        D6 = require_path(runs_root(args.runs_root) / "PROBE_DOSSIER6", "PROBE_DOSSIER6 run")
    except FileNotFoundError as exc:
        parser.error(str(exc))
    BATCHES = [
        ("w3", D5, "_w3"),
        ("cov", D6, "_cov"),
        ("transfer", D6, "_transfer"),
        ("canary", D6, "_canary"),
        ("proof1", D6, "_proof1"),
        ("proof2", D6, "_proof2"),
    ]

    rows = []
    for label, root, tag in BATCHES:
        p = root / f"trial_parent{tag}.json"
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for tid, reps in data.items():
            if any(tid.startswith(d) for d in DIRTY):
                continue
            valid = [r for r in reps if r.get("valid", True)]
            if not valid:
                continue
            answers = [answer_of(r) for r in valid]
            good = {a for r, a in zip(valid, answers) if r.get("passed") and a}
            p1 = sum(1 for r in valid if r.get("passed")) / len(valid)
            m = {k: majority_at_k(answers, k, good) for k in (3, 5, 10)}
            c = Counter(a for a in answers if a)
            shape = "no-answer"
            if c:
                top_a, top_n = c.most_common(1)[0]
                share = top_n / len(valid)
                if share >= 0.5:
                    shape = "consensus-right" if top_a in good else "consensus-wrong"
                else:
                    shape = "scatter"
            rows.append((label, tid[:8], len(valid), p1, m, shape))

    print(f"{'batch':9} {'task':8} {'n':>2} {'p@1':>5}  {'maj@3':>6} {'maj@5':>6} {'maj@10':>6}  shape")
    for label, tid, n, p1, m, shape in rows:
        def f(v):
            return "  --  " if v is None else f"{v:6.2f}"

        print(f"{label:9} {tid:8} {n:>2} {p1:5.2f}  {f(m[3])} {f(m[5])} {f(m[10])}  {shape}")

    agg_shapes = Counter(r[5] for r in rows)
    print("\nshapes:", dict(agg_shapes))
    nc = [r for r in rows if r[0] != "canary"]
    for k in (3, 5, 10):
        have = [r for r in nc if r[4][k] is not None]
        if have:
            print(
                f"non-canary mean pass@1 {sum(r[3] for r in have) / len(have):.3f}  "
                f"vs mean majority@{k} {sum(r[4][k] for r in have) / len(have):.3f}  (n={len(have)} tasks)"
            )
    flips_up = [r for r in nc if r[4][10] is not None and r[3] < 0.5 and r[4][10] >= 0.5]
    flips_dn = [r for r in nc if r[4][10] is not None and r[3] >= 0.5 and r[4][10] < 0.5]
    print("fail-side tasks lifted by majority@10:", [(r[0], r[1]) for r in flips_up])
    print("pass-side tasks sunk by majority@10  :", [(r[0], r[1]) for r in flips_dn])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
