# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Figure and table of per-round scores for the six whitelist campaigns on
the common 100-task no-pixel subset (thesis Chapter 6).

Except for the documented baseline-seed1 R0 normalization below, scores use
the last task_history row per (round, task) on the subset, carried rows included,
tasks passed out of 100. A filled marker means a candidate shipped into
that round (the configuration changed); a hollow marker means the round
re-ran the previous configuration. The grey band uses the directly measured
paired-change SD of 3.70 tasks (F15) as a descriptive reference width around
the arm's R3--R15 plateau mean.

Writes experiments/docs/thesis/figures/scores.pdf and figures/scores-table.tex.
Read-only over runs/.

The released baseline-seed1 R0 stored a k=2 aggregate of 67. The thesis's
accepted pass@1 reading is 57 (F15/F46). This producer applies that established
normalization only after asserting the run, round, bed size, and stored total;
it does not claim to rederive pass@1 from the aggregate task-history rows.

Usage:  python experiments/analysis/plot_campaign_scores.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "recipe" / "gaia_evolver"
OUT = REPO / "experiments" / "docs" / "thesis" / "figures"
RUNS = [("baseline-seed1", "No-graph", 1, 15), ("baseline-seed2", "No-graph", 2, None), ("baseline-seed3", "No-graph", 3, None),
        ("ghx-seed1", "Graph", 1, None), ("ghx-seed2", "Graph", 2, None), ("ghx-seed3", "Graph", 3, None)]
SD = 3.70
PLATEAU = range(3, 16)
SUBSET = {t["task_id"] for t in json.loads(
    (ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def per_round(run: str, cap: int | None) -> dict[int, int]:
    last: dict[tuple[int, str], bool] = {}
    for line in (ROOT / "runs" / run / "data" / "task_history.jsonl").open(encoding="utf-8", errors="replace"):
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
        rd = int(rd)
        if cap is not None and rd > cap:
            continue
        last[(rd, tid)] = bool(r.get("passed"))
    score: dict[int, int] = {}
    for (rd, _), ok in last.items():
        score[rd] = score.get(rd, 0) + int(ok)
    if run == "baseline-seed1":
        assert len({tid for rd, tid in last if rd == 0}) == 100
        assert score.get(0) == 67, score.get(0)
        score[0] = 57  # accepted pass@1 value recorded in thesis ledger F15/F46
    return score


def ship_rounds(run: str) -> set[int]:
    sb = ROOT / "runs" / run / "scoreboard.json"
    if not sb.exists():
        return set()
    ships = json.loads(sb.read_text(encoding="utf-8")).get("ships") or []
    # A ship recorded at scoreboard round k is a candidate named C-R{k}-NN: proposed while
    # planning round k and run in round k.  R{k}/config.yaml is round k's own configuration
    # (curves.json[k].config_hash equals its sha256 in every round), so the ship lands in
    # round k itself.  The earlier "+1" reading marked every landing one round late
    # (thesis Appendix C.2, ship-attribution correction).
    return {int(s["round"]) for s in ships}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = []
    for run, arm, seed, cap in RUNS:
        s = per_round(run, cap)
        data.append((run, arm, seed, s, ship_rounds(run)))

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), sharey=True)
    colors = {1: "#1f77b4", 2: "#d62728", 3: "#2ca02c"}
    for ax, arm in zip(axes, ("No-graph", "Graph")):
        rows = [d for d in data if d[1] == arm]
        plateau = [d[3][r] for d in rows for r in PLATEAU if r in d[3]]
        mean = sum(plateau) / len(plateau)
        ax.axhspan(mean - SD, mean + SD, color="0.85", lw=0, zorder=0)
        ax.axhline(mean, color="0.55", lw=0.8, ls="--", zorder=1)
        for run, _, seed, s, ships in rows:
            xs = sorted(r for r in s if r <= 15)
            ys = [s[r] for r in xs]
            ax.plot(xs, ys, color=colors[seed], lw=1.2, zorder=2, label=f"seed {seed}")
            for r, y in zip(xs, ys):
                filled = r in ships
                ax.plot(r, y, marker="o", ms=4.2, color=colors[seed],
                        markerfacecolor=colors[seed] if filled else "white", zorder=3)
        ax.set_title(f"{arm} arm  (plateau mean {mean:.1f}, band $\\pm${SD:.2f})", fontsize=9.5)
        ax.set_xlabel("round")
        ax.set_xticks(range(0, 16, 3))
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("tasks passed, of 100")
    axes[0].legend(fontsize=8, loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "scores.pdf")
    fig.savefig(
        OUT / "scores-pass1.pdf",
        metadata={"CreationDate": None, "ModDate": None},
    )
    print("wrote", OUT / "scores.pdf")
    print("wrote", OUT / "scores-pass1.pdf")

    # LaTeX table: rows = campaigns, columns = R0..R15
    lines = ["% generated by experiments/analysis/plot_campaign_scores.py -- do not edit",
             "\\begin{tabular}{@{}llrrrrrrrrrrrrrrrr@{}}", "\\toprule",
             "\\textbf{Arm} & \\textbf{Seed} & " + " & ".join(f"R{r}" for r in range(16)) + " \\\\", "\\midrule"]
    for run, arm, seed, s, ships in data:
        cells = []
        for r in range(16):
            v = s.get(r)
            cell = "--" if v is None else (f"\\textbf{{{v}}}" if r in ships else str(v))
            cells.append(cell)
        label = arm if seed == 1 else ""
        lines.append(f"{label} & {seed} & " + " & ".join(cells) + " \\\\")
        if seed == 3 and arm == "No-graph":
            lines.append("\\midrule")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "scores-table.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    print("wrote", OUT / "scores-table.tex")
    for run, arm, seed, s, ships in data:
        print(f"  {run:13s} {arm:8s} seed {seed}  R0={s.get(0)}  R15={s.get(15)}  ships into rounds {sorted(r for r in ships if r <= 15)}")


if __name__ == "__main__":
    main()
