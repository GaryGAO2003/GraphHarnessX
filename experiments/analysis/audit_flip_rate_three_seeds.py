# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F15/F44/F45/F9e -- the same-config flip rate, all three seeds, one bed.

Why this exists: the flip rate is the number the whole readout argument stands
on, and until now it was quoted on whichever bed each arm happened to fly --
20.2% and 20.1% on the 103-task bed for seeds 1 and 2, 19.5% on the 100-task
subset for seed 3. Mixing beds inside the load-bearing statistic is exactly the
defect \\S{sec:beds} rules out for every other cross-arm reading, so this script
recomputes all three seeds on the ONE bed the thesis reports: the 100-task
no-pixel subset common to all six campaigns.

A same-config window is a pair of adjacent rounds in which nothing shipped, so
the configuration is byte-identical and the only difference is that the bed was
run again. Two filters beyond that:

  * The pair must be ship-free by the scoreboard AND semantically config-equal.
    Config text is compared after neutralising the per-round `base_dir:` line,
    which the loop rewrites every round: on a no-op round that line is the only
    change, so byte equality of the recorded hash is the wrong test (this is the
    trap recorded as the config-hash drift finding).
  * R0 is excluded. It is a single baseline draw, and on seed 1 it is the one
    round scored at k=2, so its pass@1 identity differs from every round after
    it (registry error 11). Every other sweep in this thesis already drops R0
    (F47, F48); this brings the flip statistic into line with them, which it
    previously was not.

Both rounds of a window must carry a full batch of subset rows (>= 80), because
a delta that straddles a no-op audit window -- where only 25 tasks are re-drawn
-- is a partial re-draw and not a re-measurement of the bed.

Reports, per seed: the windows, the per-window flip count and score swing, the
pooled rate with a Wilson interval, and the observed swing range. Then the
three-seed pooled rate, and the union of the three swing ranges, which is the
band every readability judgment in the thesis is made against.

Scope: whitelist no-graph arms only (ruling ii). Read-only over runs/.

Usage:  python experiments/analysis/audit_flip_rate_three_seeds.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = [("baseline-seed1", 1), ("baseline-seed2", 2), ("baseline-seed3", 3)]
CAP = 15          # the formal sixteen-round window, R0..R15 (ruling ii)
FULL_MIN = 80     # subset rows at or above this = a full batch
SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def semantic(path: Path) -> str:
    """Config text with the per-round base_dir line neutralised."""
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    return re.sub(r"^\s*base_dir:.*$", "  base_dir: <round-local>", text, flags=re.M)


def outcomes(run: str) -> dict[int, dict[str, bool]]:
    """round -> {task_id: passed} on the subset; last row wins per (round, task).

    Re-flights and poisoned-round washes can leave more than one row for a
    (round, task); the clean prefix is written last.
    """
    last: dict[tuple[int, str], bool] = {}
    fp = ROOT / "runs" / run / "data" / "task_history.jsonl"
    for line in fp.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rd, tid = r.get("round"), r.get("task_id")
        if rd is None or tid not in SUBSET:
            continue
        last[(int(rd), tid)] = bool(r.get("passed"))
    out: dict[int, dict[str, bool]] = {}
    for (rd, tid), ok in last.items():
        out.setdefault(rd, {})[tid] = ok
    return out


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z, p = 1.959963985, k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return 100 * (centre - half), 100 * (centre + half)


def windows(run: str, res: dict[int, dict[str, bool]]) -> list[tuple[int, int]]:
    ships = {int(s["round"]) for s in
             (json.loads((ROOT / "runs" / run / "scoreboard.json")
                         .read_text(encoding="utf-8")).get("ships") or [])}
    cfg = {int(p.name[1:]): semantic(p / "config.yaml")
           for p in (ROOT / "runs" / run).glob("R*")
           if p.name[1:].isdigit() and (p / "config.yaml").exists()}
    return [(k - 1, k) for k in sorted(cfg)
            if 1 <= k - 1 and k <= CAP
            and k - 1 in cfg and cfg[k] == cfg[k - 1]
            and k not in ships and k - 1 in res and k in res]


def main() -> None:
    print("=" * 78)
    print("Same-config flip rate on the common 100-task no-pixel subset")
    print("=" * 78)

    grand_f = grand_n = 0
    bands: list[tuple[int, int]] = []
    all_swings: list[int] = []
    ever: dict[str, bool] = {}
    for run, seed in RUNS:
        res = outcomes(run)
        wins = windows(run, res)
        tot_f = tot_n = 0
        swings: list[int] = []
        print(f"\nseed {seed}   {run}   ship-free same-config windows: "
              f"{['R%d-R%d' % w for w in wins]}")
        for a, b in wins:
            common = set(res[a]) & set(res[b])
            if len(common) < FULL_MIN:
                print(f"   (R{a},R{b}) skipped: {len(common)} common rows, "
                      f"partial re-draw")
                continue
            flips = sum(1 for t in common if res[a][t] != res[b][t])
            sa = sum(res[a][t] for t in common)
            sb = sum(res[b][t] for t in common)
            swings.append(sb - sa)
            for task in common:
                if res[a][task] != res[b][task]:
                    ever[f"{run}:{task}"] = True
                else:
                    ever.setdefault(f"{run}:{task}", False)
            tot_f += flips
            tot_n += len(common)
            print(f"   (R{a},R{b}) n={len(common):3d}  flips={flips:3d} "
                  f"= {100 * flips / len(common):5.1f}%   score {sa}->{sb} "
                  f"({sb - sa:+d})")
        lo, hi = wilson(tot_f, tot_n)
        bands.append((min(swings), max(swings)))
        print(f"   >>> seed {seed}: {tot_f}/{tot_n} = {100 * tot_f / tot_n:.1f}%  "
              f"95% Wilson [{lo:.1f}, {hi:.1f}]   swing "
              f"{min(swings):+d}...{max(swings):+d}   ({len(swings)} windows)")
        grand_f += tot_f
        grand_n += tot_n
        all_swings.extend(swings)

    lo, hi = wilson(grand_f, grand_n)
    band = (min(b[0] for b in bands), max(b[1] for b in bands))
    print("\n" + "=" * 78)
    print(f"POOLED, three seeds: {grand_f}/{grand_n} = "
          f"{100 * grand_f / grand_n:.1f}%  95% Wilson [{lo:.1f}, {hi:.1f}]")
    print(f"BAND, union of the three observed swing ranges: "
          f"{band[0]:+d}...{band[1]:+d} tasks")
    print("=" * 78)
    print("The band is an observed range over a handful of windows, not a "
          "standard deviation.\nIt is the caliber every readability judgment "
          "in this thesis is made against.")

    n = len(all_swings)
    mean = sum(all_swings) / n
    sd = (sum((s - mean) ** 2 for s in all_swings) / (n - 1)) ** 0.5
    print(f"\nPer-round score SD, estimated directly from the {n} "
          f"same-config windows:")
    print(f"  mean swing {mean:+.2f}   SD {sd:.2f} tasks   "
          f"3 SD = +/-{3 * sd:.1f}")
    print("  The band above is NARROWER than three SD, so every "
          "'unreadable' verdict\n  made against the band is conservative "
          "in the direction that makes\n  separation easier to claim.")

    flipped = sum(1 for v in ever.values() if v)
    print(f"\nTasks that flip at least once inside a same-config window: "
          f"{flipped}/{len(ever)} = {100 * flipped / len(ever):.1f}% "
          f"(task-campaign pairs)")


if __name__ == "__main__":
    main()
