"""M29 seed-3 same-config window audit (F15/F41 seed-3 columns).

Bed convention: everything is computed on the 100-task nopixel subset
(webthinker_gaia_dev_nopixel.json), which is an order-preserving subset of
the 103-task bed. baseline-seed3 ran 103 tasks for R0-R6 and 100 for R7-R15
(user ruling 08-28: "100 not 103"); restricting R0-R6 to the subset makes
every round comparable. ghx-seed3 ran 100 throughout.

L0 (no --noop-audit): each same-config round is a full-bed re-measurement.
Same-config rounds are those with evolve_status noop OR crashed (a crashed
evolve leaves the config untouched - see runs/baseline-seed3/INDEX.md), plus the
gateway-resume pair (R6,R7), config equality verified semantically, reported
separately (not pooled) like M28's (R11,R12).

GHX (--noop-audit 25): noop windows re-run only the volatile family; fresh-
subset re-flip rate is the F41 analog. The post-outage restart from R9 runs
R6's validated config (R8 rolled back C-R8-01/02, preflight reseeded from
R6/config.yaml; R6 == R9 semantically) -> (R6,R9) is a documented non-
adjacent same-config full-bed pair, reported separately, not pooled.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = ROOT / "runs"
SUBSET = {
    t["task_id"]
    for t in json.loads((ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))
}
assert len(SUBSET) == 100, len(SUBSET)


def load(tag: str):
    run = RUNS / tag
    curves = json.loads((run / "curves.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (run / "data" / "task_history.jsonl").open(encoding="utf-8")]
    by_round: dict[int, dict[str, dict]] = {}
    for r in rows:
        if r["task_id"] in SUBSET:
            by_round.setdefault(int(r["round"]), {})[r["task_id"]] = r
    return curves, by_round


def p1(row: dict) -> bool:
    flags = row.get("passed_flags") or [row.get("passed")]
    return bool(flags[0])


def window(prev: dict[str, dict], cur: dict[str, dict], fresh_only: bool):
    fp = pf = total = 0
    for tid, row in cur.items():
        if fresh_only and row.get("carried"):
            continue
        if tid not in prev:
            continue
        total += 1
        a, b = p1(prev[tid]), p1(row)
        if not a and b:
            fp += 1
        elif a and not b:
            pf += 1
    return fp, pf, total


def score(d: dict[str, dict]) -> int:
    return sum(1 for r in d.values() if p1(r))


def report_pair(label: str, prev, cur, fresh_only=False):
    fp, pf, n = window(prev, cur, fresh_only)
    f = fp + pf
    extra = "" if fresh_only else f"  score {score(prev)}->{score(cur)} swing {score(cur)-score(prev):+d}"
    print(f"  {label}: flips {f}/{n} = {f/n:.1%} (f->p {fp}, p->f {pf}){extra}")
    return fp, pf, n


def main() -> None:
    print("=" * 72)
    print("L0 seed-3 (baseline-seed3, 100-subset): full-bed same-config windows  [F15 analog]")
    curves, hist = load("baseline-seed3")
    print("  per-round (100-subset):", " ".join(f"R{e['round']}={score(hist[e['round']])}" for e in curves if e["round"] in hist))
    pooled = [0, 0, 0]
    swings = []
    for e in curves:
        k = e["round"]
        if e["evolve_status"] not in ("noop", "crashed") or k - 1 not in hist:
            continue
        fp, pf, n = report_pair(f"(R{k-1},R{k}) [{e['evolve_status']}]", hist[k - 1], hist[k])
        pooled[0] += fp
        pooled[1] += pf
        pooled[2] += n
        swings.append(score(hist[k]) - score(hist[k - 1]))
    f = pooled[0] + pooled[1]
    print(
        f"  pooled: {f}/{pooled[2]} = {f/pooled[2]:.1%} (f->p {pooled[0]}, p->f {pooled[1]})"
        f"  swings {min(swings):+d}..{max(swings):+d} / 100"
    )
    if 7 in hist:
        report_pair("documented gateway-resume pair (R6,R7), NOT pooled", hist[6], hist[7])

    print("=" * 72)
    print("GHX seed-3 (ghx-seed3): noop-window fresh-subset re-flips  [F41 analog]")
    curves, hist = load("ghx-seed3")
    print("  per-round:", " ".join(f"R{e['round']}={score(hist[e['round']])}" for e in curves if e["round"] in hist))
    pooled = [0, 0, 0]
    for e in curves:
        k = e["round"]
        if e["evolve_status"] != "noop" or k - 1 not in hist:
            continue
        fp, pf, n = report_pair(f"(R{k-1},R{k})", hist[k - 1], hist[k], fresh_only=True)
        pooled[0] += fp
        pooled[1] += pf
        pooled[2] += n
    f = pooled[0] + pooled[1]
    print(f"  pooled: {f}/{pooled[2]} = {f/pooled[2]:.1%}   (M26b F41: 74/178 = 41.6%; M28 s2: 49/130 = 37.7%)")
    if 9 in hist:
        report_pair("documented non-adjacent same-config pair (R6,R9), NOT pooled", hist[6], hist[9])


if __name__ == "__main__":
    main()
