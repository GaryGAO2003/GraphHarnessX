"""M28 seed-2 same-config window audit (F15/F41 seed-2 columns).

L0 (baseline-seed2, no --noop-audit): every noop-scoped round is a full-bed
same-config re-measurement -> flip rate + total-score swing per window
(F15 analog). The resumed (R11,R12) pair is a *documented* same-config
window (R11->R12 evolve killed by the 08-26 reboot; R12 ran R11's config,
curves label "ok" forced by --start-round — see runs/baseline-seed2/INDEX.md);
reported separately, not pooled.

GHX (ghx-seed2, --noop-audit 25): noop windows re-run only the volatile
family (fresh subset); carried tasks cannot flip by construction. Fresh-
subset re-flip rate is the F41 analog (M26b pooled: 74/178 = 41.6%).
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
    rows = [
        json.loads(line)
        for line in (run / "data" / "task_history.jsonl").open(encoding="utf-8")
    ]
    by_round: dict[int, dict[str, dict]] = {}
    for r in rows:
        if r["task_id"] not in SUBSET:
            continue
        by_round.setdefault(int(r["round"]), {})[r["task_id"]] = r
    return curves, by_round


def window(prev: dict[str, dict], cur: dict[str, dict], fresh_only: bool):
    flips = total = 0
    for tid, row in cur.items():
        if fresh_only and row.get("carried"):
            continue
        if tid not in prev:
            continue
        total += 1
        if prev[tid]["passed"] != row["passed"]:
            flips += 1
    return flips, total


def main() -> None:
    print("=" * 72)
    print("L0 seed-2 (baseline-seed2): full-bed same-config windows  [F15 analog]")
    curves, hist = load("baseline-seed2")
    pooled_f = pooled_n = 0
    swings = []
    for e in curves:
        k = e["round"]
        if e["evolve_status"] != "noop" or k - 1 not in hist:
            continue
        f, n = window(hist[k - 1], hist[k], fresh_only=False)
        prev_pass = sum(1 for r in hist[k - 1].values() if r["passed"])
        cur_pass = sum(1 for r in hist[k].values() if r["passed"])
        swing = cur_pass - prev_pass
        pooled_f += f
        pooled_n += n
        swings.append(swing)
        print(f"  (R{k-1},R{k}): flips {f}/{n} = {f/n:.1%}  score swing {swing:+d}")
    print(
        f"  pooled: {pooled_f}/{pooled_n} = {pooled_f/pooled_n:.1%}"
        f"  swings {min(swings):+d}..{max(swings):+d} / 100"
    )
    f, n = window(hist[11], hist[12], fresh_only=False)
    print(
        f"  documented resume pair (R11,R12), NOT pooled: flips {f}/{n} = {f/n:.1%}"
        f"  swing {sum(1 for r in hist[12].values() if r['passed']) - sum(1 for r in hist[11].values() if r['passed']):+d}"
    )

    print("=" * 72)
    print("GHX seed-2 (ghx-seed2): noop-window fresh-subset re-flips  [F41 analog]")
    curves, hist = load("ghx-seed2")
    pooled_f = pooled_n = 0
    for e in curves:
        k = e["round"]
        if e["evolve_status"] != "noop" or k - 1 not in hist:
            continue
        f, n = window(hist[k - 1], hist[k], fresh_only=True)
        pooled_f += f
        pooled_n += n
        print(f"  (R{k-1},R{k}): fresh re-flips {f}/{n} = {f/n:.1%}")
    print(
        f"  pooled: {pooled_f}/{pooled_n} = {pooled_f/pooled_n:.1%}"
        f"   (M26b F41: 74/178 = 41.6%)"
    )


if __name__ == "__main__":
    main()
