# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Cone-size distribution, one representative rendered cone, and per-seed
scores (thesis Chapter 5 figure; ledger F55 and F58).

Top left   -- full-cone and data-cone node counts over the 56 R0--R1 failed
              fresh tasks of graph seed 1 with a resolvable U, produced by
              executing cone_size_recompute_m26b.py unchanged except for the
              run root (the same task_history, byte-identical).
Top right  -- the rendered cone a role actually received, drawn from the R1
              injection artefact (graph_evidence/cones/<task>.md): invocations
              in ordinal order, writer->reader data-flow edges, intervention
              nodes marked.  Selection rule: the rendered-cone file whose byte
              size is nearest the unrounded median over the 44 R1 files
              (F55's 15.5 kB, kB = 1000 bytes).  Two files tie at 27 bytes from
              the median; the tie is broken toward the task the F55 producer
              already names as its median-U representative, and both tied
              task ids are recorded in the JSON sidecar.
Bottom     -- the six campaigns of figures/scores.pdf redrawn one seed pair
              per panel.  Scores come from plot_campaign_scores.per_round; the
              baseline-seed1 R0 pass@1 normalization (67 -> 57, F15/F46) is
              applied under the producer's own assertions when the imported
              reader has not applied it.  The grey band is the arm-pooled
              R3--R15 plateau mean +/- 3.70 tasks (F15), a descriptive
              reference width drawn identically in every panel; it is not a
              confidence interval and was not calibrated per seed.

Writes experiments/docs/thesis/figures/cone-and-seeds.pdf and
experiments/analysis/out/cone_repr.json.  Read-only over runs/.

Usage:  python experiments/analysis/plot_cone_figure.py
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plot_campaign_scores import OUT, PLATEAU, REPO, ROOT, RUNS, SD, per_round, ship_rounds  # noqa: E402

CONE_RUN = ROOT / "runs" / "ghx-seed1"
CONE_DIR = CONE_RUN / "R1" / "graph_evidence" / "cones"
F55_PRODUCER = HERE / "cone_size_recompute_m26b.py"
F55_RUN_LINE = 'RUN = Path(r"D:\\PycharmProj\\HarnessX") / "recipe/gaia_evolver/runs/ghx-seed1"'
OUT_JSON = HERE / "out" / "cone_repr.json"

INV_RE = re.compile(r"^- (t\d+): (\S+) (\S+)(?: \[step (\d+)\])?(.*)$")
LANE_OF = {"model": "model", "tool": "tool"}  # every other kind is a processor hook
EDGE_RE = re.compile(r"^- (msg:\S+): (t\d+) -> (t\d+)$")


def f55_rows() -> list[dict]:
    """Execute the F55 producer unchanged except for its run root; return its rows."""
    src = F55_PRODUCER.read_text(encoding="utf-8")
    patched = src.replace(F55_RUN_LINE, f"RUN = Path(r'{CONE_RUN}')")
    assert patched != src, "F55 producer RUN line not found; refuse to guess"
    g = {"__name__": "f55_producer", "__file__": str(F55_PRODUCER)}
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(patched, str(F55_PRODUCER), "exec"), g)
    rows = g["rows"]
    assert len(rows) == 56, len(rows)
    return rows


def pick_representative() -> dict:
    sizes = {f.stem: f.stat().st_size for f in sorted(CONE_DIR.glob("*.md"))}
    assert len(sizes) == 44, len(sizes)
    med = statistics.median(sizes.values())
    dist = sorted(sizes.items(), key=lambda kv: (abs(kv[1] - med), kv[0]))
    best_d = abs(dist[0][1] - med)
    tied = [tid for tid, sz in dist if abs(sz - med) == best_d]
    # F55 producer's own representative is the median-size U; prefer it inside a tie.
    f55_rep = "7619a514"
    chosen = next((t for t in tied if t.startswith(f55_rep)), tied[0])
    return {"task_id": chosen, "bytes": sizes[chosen], "median_bytes": med,
            "median_kB": med / 1000.0, "n_files": len(sizes), "tied": tied,
            "tie_rule": "nearest to unrounded byte median; tie -> F55 producer's median-U task"}


def parse_cone(path: Path) -> tuple[list[dict], list[tuple[str, str, str]]]:
    text = path.read_text(encoding="utf-8")
    inv_part = text.split("## Data-flow")[0]
    edge_part = text.split("## Data-flow")[1].split("## Trajectory")[0]
    nodes, edges = [], []
    for ln in inv_part.splitlines():
        m = INV_RE.match(ln.strip())
        if m:
            nodes.append({"id": m.group(1), "kind": m.group(2), "name": m.group(3),
                          "step": int(m.group(4)) if m.group(4) else None,
                          "intervention": "intervention" in m.group(5)})
    for ln in edge_part.splitlines():
        m = EDGE_RE.match(ln.strip())
        if m:
            edges.append((m.group(1), m.group(2), m.group(3)))
    assert nodes and edges, path
    return nodes, edges


def draw_cone(ax, nodes: list[dict], edges: list[tuple[str, str, str]], title: str) -> None:
    lanes = {"hook": 2, "model": 1, "tool": 0}
    xpos = {n["id"]: i for i, n in enumerate(nodes)}
    ypos = {n["id"]: lanes[LANE_OF.get(n["kind"], "hook")] for n in nodes}
    for _, a, b in edges:
        if a not in xpos or b not in xpos:
            continue
        rad = 0.25 if ypos[a] == ypos[b] else 0.1
        ax.add_patch(FancyArrowPatch((xpos[a], ypos[a]), (xpos[b], ypos[b]),
                                     connectionstyle=f"arc3,rad={rad}", arrowstyle="-",
                                     lw=0.3, color="0.55", alpha=0.25, zorder=1))
    style = {"hook": ("s", "#7f7f7f"), "model": ("o", "#1f77b4"), "tool": ("^", "#ff7f0e")}
    for n in nodes:
        mk, col = style[LANE_OF.get(n["kind"], "hook")]
        ax.plot(xpos[n["id"]], ypos[n["id"]], marker=mk, ms=5.5, color=col, zorder=3,
                markeredgecolor="black" if n["intervention"] else col,
                markeredgewidth=1.4 if n["intervention"] else 0.4)
    ax.set_yticks([lanes["hook"], lanes["model"], lanes["tool"]])
    ax.set_yticklabels(["processor hook", "model call", "tool call"], fontsize=8)
    ax.set_ylim(-0.6, 2.6)
    ax.set_xlim(-1, len(nodes))
    ax.set_xlabel("invocation, ordinal order", fontsize=8.5)
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="x", labelsize=7.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    handles = [plt.Line2D([], [], marker=mk, color=col, ls="", ms=5.5, label=k)
               for k, (mk, col) in style.items()]
    handles.append(plt.Line2D([], [], marker="o", color="white", markeredgecolor="black",
                              markeredgewidth=1.4, ls="", ms=5.5, label="intervention node"))
    handles.append(plt.Line2D([], [], color="0.55", alpha=0.6, lw=0.8, label="data-flow edge (writer\u2192reader)"))
    ax.legend(handles=handles, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.24),
              frameon=False, ncol=3, handletextpad=0.4, columnspacing=1.0)


def draw_hist(ax, rows: list[dict]) -> None:
    full = [r["cone_nodes"] for r in rows]
    data = [r["data_nodes"] for r in rows]
    bins = range(0, max(full) + 6, 5)
    ax.hist(full, bins=bins, color="#1f77b4", alpha=0.55, label=f"full cone (median {statistics.median(full):g})")
    ax.hist(data, bins=bins, color="#ff7f0e", alpha=0.55, label=f"data cone (median {statistics.median(data):g})")
    ax.axvline(statistics.median(full), color="#1f77b4", lw=1, ls="--")
    ax.axvline(statistics.median(data), color="#ff7f0e", lw=1, ls="--")
    ax.set_xlabel("cone nodes per failed task", fontsize=8.5)
    ax.set_ylabel("tasks", fontsize=8.5)
    ax.set_title(f"Cone size, {len(rows)} failed fresh tasks", fontsize=9)
    ax.legend(fontsize=6.8, frameon=False, loc="upper left", handlelength=1.2)
    ax.tick_params(labelsize=7.5)
    ax.grid(alpha=0.25)


def scores_by_run() -> dict[str, tuple[str, int, dict[int, int], set[int]]]:
    out = {}
    for run, arm, seed, cap in RUNS:
        s = per_round(run, cap)
        if run == "baseline-seed1" and s.get(0) == 67:
            # producer's documented pass@1 normalization (F15/F46), applied only if absent
            s[0] = 57
        if run == "baseline-seed1":
            assert s.get(0) == 57, s.get(0)
        out[run] = (arm, seed, s, ship_rounds(run))
    return out


def draw_seed_panels(axes, data: dict) -> None:
    colors = {"No-graph": "#1f77b4", "Graph": "#d62728"}
    band = {}
    for arm in ("No-graph", "Graph"):
        plateau = [s[r] for (a, _, s, _) in data.values() if a == arm for r in PLATEAU if r in s]
        band[arm] = sum(plateau) / len(plateau)
    for ax, seed in zip(axes, (1, 2, 3)):
        for arm in ("No-graph", "Graph"):
            m = band[arm]
            ax.axhspan(m - SD, m + SD, color=colors[arm], alpha=0.10, lw=0, zorder=0)
            ax.axhline(m, color=colors[arm], lw=0.7, ls="--", alpha=0.6, zorder=1)
        for run, (arm, sd, s, ships) in data.items():
            if sd != seed:
                continue
            xs = sorted(r for r in s if r <= 15)
            ys = [s[r] for r in xs]
            ax.plot(xs, ys, color=colors[arm], lw=1.2, zorder=2, label=f"{arm} arm")
            for r, y in zip(xs, ys):
                ax.plot(r, y, marker="o", ms=4.0, color=colors[arm],
                        markerfacecolor=colors[arm] if r in ships else "white", zorder=3)
        ax.set_title(f"seed {seed}", fontsize=9)
        ax.set_xlabel("round", fontsize=8.5)
        ax.set_xticks(range(0, 16, 3))
        ax.tick_params(labelsize=7.5)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("tasks passed, of 100", fontsize=8.5)
    from matplotlib.patches import Patch
    handles = [plt.Line2D([], [], color=colors["No-graph"], marker="o", ms=4, lw=1.2, label="No-graph arm"),
               plt.Line2D([], [], color=colors["Graph"], marker="o", ms=4, lw=1.2, label="Graph arm"),
               plt.Line2D([], [], color="0.3", marker="o", ms=4, ls="", label="filled: candidate shipped into the round"),
               plt.Line2D([], [], color="0.3", marker="o", ms=4, ls="", markerfacecolor="white", label="hollow: configuration unchanged"),
               Patch(facecolor="0.5", alpha=0.25, label=f"arm-pooled R3\u2013R15 plateau mean \u00b1 {SD:.2f} (reference width, F15; not a CI)")]
    fig = axes[1].figure
    fig.legend(handles=handles, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 0.005),
               frameon=False, ncol=3, handletextpad=0.4, columnspacing=1.0)


def main() -> None:
    rows = f55_rows()
    rep = pick_representative()
    nodes, edges = parse_cone(CONE_DIR / f"{rep['task_id']}.md")
    rep.update({"invocations": len(nodes), "edges": len(edges),
                "interventions": sum(n["intervention"] for n in nodes),
                "kinds": {k: sum(n["kind"] == k for n in nodes) for k in sorted({n["kind"] for n in nodes})},
                "f55_n": len(rows),
                "f55_median_full_cone": statistics.median(r["cone_nodes"] for r in rows),
                "f55_median_data_cone": statistics.median(r["data_nodes"] for r in rows)})
    data = scores_by_run()

    plt.rcParams.update({"font.size": 8.5})
    fig = plt.figure(figsize=(7.6, 6.2))   # ~ \textwidth at scale 0.83: legend text stays >= 6 pt in print
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.95], hspace=0.78, wspace=0.42,
                          left=0.09, right=0.985, top=0.95, bottom=0.17)
    ax_hist = fig.add_subplot(gs[0, 0])
    ax_cone = fig.add_subplot(gs[0, 1:])
    ax_seeds = [fig.add_subplot(gs[1, i]) for i in range(3)]
    for a in ax_seeds[1:]:
        a.sharey(ax_seeds[0])
    draw_hist(ax_hist, rows)
    draw_cone(ax_cone, nodes, edges,
              f"Rendered cone as injected, task {rep['task_id'][:8]} (R1):\n"
              f"{len(nodes)} invocations, {len(edges)} edges, {rep['bytes']:,} bytes")
    draw_seed_panels(ax_seeds, data)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "cone-and-seeds.pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT_JSON.parent / "cone-and-seeds.png", dpi=160)
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(rep, indent=1), encoding="utf-8", newline="\n")
    print("wrote", OUT / "cone-and-seeds.pdf")
    print("wrote", OUT_JSON)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
