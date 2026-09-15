# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""F9 on the admissible campaign set (data-ruling whitelist), two readings.

RUNS = baseline-seed1 (no-graph) + ghx-seed1-partial + ghx-seed1 (graph).  The banned
shakedown campaigns (M24/M25) are excluded, retiring the pooled 1.04.

Reading A (as-is)      — same eligibility as audit_candidate_prediction_lift.py:
                         predicted task failed fresh in R(k-1) and ran fresh in
                         Rk.  Reproduces M22 1.99 and M26b 0.64 (n=8).
Reading B (full-batch) — additionally requires round k to be a FULL batch
                         (fresh rows >= FULL_MIN), removing the noop-audit
                         denominator confound in M26b (noop-scoped rounds run
                         only ~25 tasks, shrinking and biasing both the
                         eligible set and the base pool).

Also prints per-arm passive flip-back base rates for the F18 cross-check.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_candidate_prediction_lift import predicted_ids  # noqa: E402
from run_paths import require_path, runs_root  # noqa: E402

RUNS = [
    ("baseline-seed1", "no-graph"),
    ("ghx-seed1", "graph"),
]
FULL_MIN = 80  # fresh rows >= this => full batch round


def load_run(root: Path):
    curves = json.loads((root / "curves.json").read_text(encoding="utf-8"))
    sb = root / "scoreboard.json"
    ships = (json.loads(sb.read_text(encoding="utf-8")).get("ships") or []) if sb.exists() else []
    fresh: dict[tuple[int, str], bool] = {}
    per_round: dict[int, int] = {}
    for line in (root / "data" / "task_history.jsonl").open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("carried"):
            continue
        k = int(r.get("round", -1))
        fresh[(k, str(r.get("task_id")))] = bool(r.get("passed"))
        per_round[k] = per_round.get(k, 0) + 1
    return curves, ships, fresh, per_round


def score(root: Path, ships, fresh, per_round, require_full: bool):
    rows = []
    max_round = max((k for k, _ in fresh), default=-1)
    for s in ships:
        k, cid = int(s["round"]), str(s["cid"])
        if k > max_round:
            continue
        if require_full and per_round.get(k, 0) < FULL_MIN:
            continue
        if require_full == "both" and per_round.get(k - 1, 0) < FULL_MIN:
            continue
        manifest = root / f"R{k}" / "candidates" / f"{cid}.md"
        if not manifest.exists():
            continue
        pred = predicted_ids(manifest)
        if not pred:
            continue
        elig = [t for t in pred if fresh.get((k - 1, t)) is False and (k, t) in fresh]
        if not elig:
            continue
        hits = sum(1 for t in elig if fresh[(k, t)])
        base_pool = [t for (r, t), v in fresh.items() if r == k - 1 and v is False and (k, t) in fresh]
        base_hits = sum(1 for t in base_pool if fresh[(k, t)])
        rows.append((root.name, cid, k, len(elig), hits, base_hits, len(base_pool)))
    return rows


def pooled(rows):
    elig = sum(r[3] for r in rows)
    hits = sum(r[4] for r in rows)
    seen = {}
    for r in rows:
        seen[(r[0], r[2])] = (r[5], r[6])
    bh = sum(v[0] for v in seen.values())
    bn = sum(v[1] for v in seen.values())
    hr = hits / elig if elig else 0.0
    br = bh / bn if bn else 0.0
    return elig, hits, hr, bh, bn, br, (hr / br if br else 0.0)


def flipback(fresh):
    """Passive flip-back rate: fresh-failed at k-1, fresh-run at k, passed at k
    — over ALL consecutive round pairs (F18's base consistency number)."""
    n = h = 0
    for (k, t), v in fresh.items():
        if v is False and (k + 1, t) in fresh:
            n += 1
            h += 1 if fresh[(k + 1, t)] else 0
    return h, n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", help="Campaign runs directory (default: GHX_RUNS_ROOT or repository runs)")
    args = parser.parse_args()
    root_dir = runs_root(args.runs_root)
    missing = [root_dir / name for name, _ in RUNS if not (root_dir / name).is_dir()]
    if missing:
        parser.error(f"missing campaign run: {missing[0]}")
    for label, require_full in (
        ("A (as-is)", False),
        ("B (full-batch landing round)", True),
        ("C (both k-1 and k full: confound-free windows)", "both"),
    ):
        print(f"\n==== reading {label} ====")
        arm_rows = {"no-graph": [], "graph": []}
        for name, arm in RUNS:
            root = require_path(root_dir / name, "campaign run")
            _, ships, fresh, per_round = load_run(root)
            rows = score(root, ships, fresh, per_round, require_full)
            arm_rows[arm].extend(rows)
            e, h, hr, bh, bn, br, lift = pooled(rows)
            print(
                f"  {name:14} cand={len(rows):2d} elig={e:3d} hit={h:3d} "
                f"hit_rate={100 * hr:5.1f}%  base={bh}/{bn}={100 * br:5.1f}%  lift={lift:.2f}"
            )
        for arm, rows in arm_rows.items():
            e, h, hr, bh, bn, br, lift = pooled(rows)
            print(
                f"  arm {arm:9} cand={len(rows):2d} elig={e:3d} hit={h:3d} "
                f"hit_rate={100 * hr:5.1f}%  base={bh}/{bn}={100 * br:5.1f}%  lift={lift:.2f}"
            )

    print("\n==== F18 cross-check: passive flip-back base rates (all round pairs) ====")
    for name, arm in RUNS:
        _, _, fresh, _ = load_run(root_dir / name)
        h, n = flipback(fresh)
        print(f"  {name:14} ({arm:8}): {h}/{n} = {100 * h / n if n else 0:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
