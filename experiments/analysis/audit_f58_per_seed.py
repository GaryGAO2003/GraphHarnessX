# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F58 per-seed and leave-one-seed-out companion (thesis Appendix ledger F58).

Reuses the exact readers of the two existing producers: fresh/carried
composition from audit_fresh_carried_plateau.per_round_fresh_carried and
per-round scores from plot_campaign_scores.per_round (last task_history row per
(round, task) on the common 100-task subset, carried rows included). Only
R3--R15 is used, so the baseline-seed1 R0 pass@1 normalization in the score
producer does not enter.

Full-batch rounds are rounds with 100 fresh draws (F58's definition); the
terminal round is R15. Differences are graph minus no-graph, per seed pair, and
means over the seed pairs that remain after leaving one seed out.

Writes experiments/analysis/out/f58_per_seed.json. Read-only over runs/.

Usage:  python experiments/analysis/audit_f58_per_seed.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_fresh_carried_plateau import PLATEAU, per_round_fresh_carried  # noqa: E402
from plot_campaign_scores import per_round  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
ARMS = {"L0": "baseline-seed{}", "GHX": "ghx-seed{}"}
SEEDS = (1, 2, 3)
TERMINAL = 15


def seed_block(arm: str, seed: int) -> dict:
    run = ARMS[arm].format(seed)
    rc = per_round_fresh_carried(run)
    sc = per_round(run, None)
    fresh = sum(rc.get(k, (0, 0))[0] for k in PLATEAU)
    carried = sum(rc.get(k, (0, 0))[1] for k in PLATEAU)
    full_rounds = [k for k in PLATEAU if rc.get(k, (0, 0))[0] == 100]
    audit_rounds = [k for k in PLATEAU if 0 < rc.get(k, (0, 0))[0] < 100]
    assert len(full_rounds) + len(audit_rounds) == len(PLATEAU), (run, full_rounds, audit_rounds)
    plateau = [sc[k] for k in PLATEAU]
    full = [sc[k] for k in full_rounds]
    return {
        "run": run, "arm": arm, "seed": seed,
        "fresh": fresh, "carried": carried, "task_rounds": fresh + carried,
        "carried_pct": 100.0 * carried / (fresh + carried),
        "full_batch_rounds": len(full_rounds), "audit_batch_rounds": len(audit_rounds),
        "plateau_mean": sum(plateau) / len(plateau),
        "full_batch_mean": sum(full) / len(full),
        "terminal": sc[TERMINAL],
    }


def mean_over(blocks: dict, arm: str, key: str, seeds: list[int]) -> float:
    return sum(blocks[arm][s][key] for s in seeds) / len(seeds)


def main() -> None:
    blocks = {arm: {s: seed_block(arm, s) for s in SEEDS} for arm in ARMS}

    pooled = {}
    for arm in ARMS:
        bs = list(blocks[arm].values())
        pooled[arm] = {
            "carried": sum(b["carried"] for b in bs),
            "task_rounds": sum(b["task_rounds"] for b in bs),
            "full_batch_rounds": sum(b["full_batch_rounds"] for b in bs),
            "audit_batch_rounds": sum(b["audit_batch_rounds"] for b in bs),
            "plateau_mean": sum(b["plateau_mean"] for b in bs) / 3,
            "full_batch_mean": sum(b["full_batch_mean"] for b in bs) / 3,
            "terminal_mean": sum(b["terminal"] for b in bs) / 3,
        }
    # pooled figures must reproduce F58 as printed
    assert pooled["L0"]["carried"] == 0 and pooled["L0"]["full_batch_rounds"] == 39
    assert pooled["GHX"]["carried"] == 1099 and pooled["GHX"]["task_rounds"] == 3900
    assert pooled["GHX"]["full_batch_rounds"] == 24 and pooled["GHX"]["audit_batch_rounds"] == 15

    per_seed = []
    for s in SEEDS:
        l0, g = blocks["L0"][s], blocks["GHX"][s]
        per_seed.append({
            "seed": s,
            "graph_carried": g["carried"], "graph_carried_pct": g["carried_pct"],
            "graph_audit_batch_rounds": g["audit_batch_rounds"],
            "graph_full_batch_rounds": g["full_batch_rounds"],
            "nograph_plateau": l0["plateau_mean"], "graph_plateau": g["plateau_mean"],
            "plateau_diff": g["plateau_mean"] - l0["plateau_mean"],
            "nograph_full_batch": l0["full_batch_mean"], "graph_full_batch": g["full_batch_mean"],
            "full_batch_diff": g["full_batch_mean"] - l0["full_batch_mean"],
            "nograph_terminal": l0["terminal"], "graph_terminal": g["terminal"],
            "terminal_diff": g["terminal"] - l0["terminal"],
        })

    loo = []
    for left_out in SEEDS:
        keep = [s for s in SEEDS if s != left_out]
        row = {"left_out": left_out, "seeds": keep}
        for key, name in (("plateau_mean", "plateau"), ("full_batch_mean", "full_batch"), ("terminal", "terminal")):
            ng = mean_over(blocks, "L0", key, keep)
            gr = mean_over(blocks, "GHX", key, keep)
            row["nograph_" + name] = ng
            row["graph_" + name] = gr
            row[name + "_diff"] = gr - ng
        row["graph_carried"] = sum(blocks["GHX"][s]["carried"] for s in keep)
        row["graph_task_rounds"] = sum(blocks["GHX"][s]["task_rounds"] for s in keep)
        loo.append(row)

    result = {"per_run": blocks, "pooled": pooled, "per_seed": per_seed, "leave_one_seed_out": loo}
    OUT.mkdir(exist_ok=True)
    (OUT / "f58_per_seed.json").write_text(json.dumps(result, indent=1), encoding="utf-8", newline="\n")

    print("F58 companion: per seed (graph minus no-graph)")
    hdr = ("seed", "g.carried", "pct", "audit", "ng.plat", "g.plat", "d.plat",
           "ng.full", "g.full", "d.full", "ng.T", "g.T", "d.T")
    print(" ".join(f"{h:>8}" for h in hdr))
    for r in per_seed:
        vals = (r["seed"], r["graph_carried"], f"{r['graph_carried_pct']:.1f}", r["graph_audit_batch_rounds"],
                f"{r['nograph_plateau']:.2f}", f"{r['graph_plateau']:.2f}", f"{r['plateau_diff']:+.2f}",
                f"{r['nograph_full_batch']:.2f}", f"{r['graph_full_batch']:.2f}", f"{r['full_batch_diff']:+.2f}",
                r["nograph_terminal"], r["graph_terminal"], f"{r['terminal_diff']:+d}")
        print(" ".join(f"{str(v):>8}" for v in vals))

    print("\nleave-one-seed-out (means over the two remaining seed pairs)")
    hdr = ("out", "ng.plat", "g.plat", "d.plat", "ng.full", "g.full", "d.full", "ng.T", "g.T", "d.T", "g.carried")
    print(" ".join(f"{h:>9}" for h in hdr))
    for r in loo:
        vals = (r["left_out"], f"{r['nograph_plateau']:.2f}", f"{r['graph_plateau']:.2f}", f"{r['plateau_diff']:+.2f}",
                f"{r['nograph_full_batch']:.2f}", f"{r['graph_full_batch']:.2f}", f"{r['full_batch_diff']:+.2f}",
                f"{r['nograph_terminal']:.1f}", f"{r['graph_terminal']:.1f}", f"{r['terminal_diff']:+.1f}",
                f"{r['graph_carried']}/{r['graph_task_rounds']}")
        print(" ".join(f"{str(v):>9}" for v in vals))

    p = pooled
    print("\npooled check:",
          f"plateau {p['L0']['plateau_mean']:.2f} vs {p['GHX']['plateau_mean']:.2f}",
          f"(d {p['GHX']['plateau_mean'] - p['L0']['plateau_mean']:+.2f});",
          f"full-batch {p['L0']['full_batch_mean']:.2f} vs {p['GHX']['full_batch_mean']:.2f}",
          f"(d {p['GHX']['full_batch_mean'] - p['L0']['full_batch_mean']:+.2f});",
          f"terminal {p['L0']['terminal_mean']:.2f} vs {p['GHX']['terminal_mean']:.2f};",
          f"graph carried {p['GHX']['carried']}/3900")
    print("wrote", OUT / "f58_per_seed.json")


if __name__ == "__main__":
    main()
