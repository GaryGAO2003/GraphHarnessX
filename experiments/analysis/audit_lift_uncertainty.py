# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Uncertainty for the localization-lift readouts and the same-config flip rate.

The manuscript reported point lifts with no interval anywhere (round-3 guardrails
audit, finding E-1: zero confidence intervals against seven p-values in use).
This script supplies the missing intervals for the numbers that stayed in the
body after the arm comparison was withdrawn.

What it computes
----------------
1. **Cluster bootstrap CI on each arm's lift.** The resampling unit is the
   *candidate*, not the prediction: predictions inside one candidate share an
   edit, a round, and a base pool, so treating them as independent understates
   the variance. Percentile 95% CI over 20,000 resamples.
2. **Design effect** = var(cluster bootstrap) / var(naive binomial), i.e. how
   much clustering actually costs on this data.
3. **Minimum detectable lift** at each arm's realised sample: the smallest true
   lift whose one-sided exact-binomial test against the arm's own base pool
   would reject at alpha=0.05, reported both unclustered (anticonservative) and
   inflated by the measured design effect.
4. **Wilson 95% CI on the three same-config flip rates** (F15/F44/F45) and on
   their pooled value -- the interval that the thesis's central noise-floor
   claim has never carried.

Self-check: before reporting any interval, the script reproduces the point
estimates of ``audit_candidate_prediction_lift_whitelist.py`` (readings A and C)
and refuses to print if they disagree. The two scripts share no code beyond
``predicted_ids``; agreement is therefore a real cross-check, not a tautology.

Scope: whitelist only (ruling II) -- baseline-seed1 (no-graph) and
ghx-seed1-partial/ghx-seed1 (graph). Flip rates come from the three seed-pair ledger
rows, not recomputed here.

Usage:  python experiments/analysis/audit_lift_uncertainty.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_candidate_prediction_lift import predicted_ids  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNS = [("baseline-seed1", "no-graph"), ("ghx-seed1", "graph")]
FULL_MIN = 80
BOOT = 20_000
SEED = 20260831
MIN_CLUSTERS = 5   # below this a cluster bootstrap has too few distinct resamples

# Point estimates the whitelist script prints; used as a refusal gate.
EXPECTED = {("no-graph", "A"): 1.99, ("graph", "A"): 0.78,
            ("no-graph", "C"): 1.99, ("graph", "C"): 1.23}

# F15 / F44 / F45 same-config flip counts (hits, pairs) per seed.
FLIPS = [("seed 1 (M22-L0)", 146, 721), ("seed 2 (M28-L0-s2)", 145, 721),
         ("seed 3 (M29-L0-s3)", 117, 600)]


def load_run(root: Path):
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
    return ships, fresh, per_round


def score(root: Path, ships, fresh, per_round, require_full):
    """Per-candidate rows: (run, cid, round, n_elig, hits, base_hits, base_n).

    Eligibility identical to audit_candidate_prediction_lift_whitelist.py.
    """
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
        pool = [t for (r, t), v in fresh.items() if r == k - 1 and v is False and (k, t) in fresh]
        rows.append((root.name, cid, k, len(elig),
                     hits, sum(1 for t in pool if fresh[(k, t)]), len(pool)))
    return rows


def pooled_lift(rows) -> tuple[float, int, int, int, int]:
    elig = sum(r[3] for r in rows)
    hits = sum(r[4] for r in rows)
    seen = {(r[0], r[2]): (r[5], r[6]) for r in rows}
    bh = sum(v[0] for v in seen.values())
    bn = sum(v[1] for v in seen.values())
    if not (elig and bn and bh):
        return 0.0, elig, hits, bh, bn
    return (hits / elig) / (bh / bn), elig, hits, bh, bn


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def mde_lift(n: int, base: float, alpha: float = 0.05) -> tuple[int, float]:
    """Smallest hit count rejecting H0: p = base one-sided, and its lift."""
    for k in range(n + 1):
        if binom_sf(k, n, base) <= alpha:
            return k, (k / n) / base if base else 0.0
    return n, 0.0


def main() -> int:
    rng = random.Random(SEED)
    print("=" * 82)
    print("Localization lift -- cluster bootstrap over candidates (unit = candidate)")
    print("=" * 82)

    store: dict[tuple[str, str], list] = {}
    for tag, require_full in (("A", False), ("C", "both")):
        arm_rows: dict[str, list] = {"no-graph": [], "graph": []}
        for name, arm in RUNS:
            root = REPO / "recipe" / "gaia_evolver" / "runs" / name
            ships, fresh, per_round = load_run(root)
            arm_rows[arm].extend(score(root, ships, fresh, per_round, require_full))
        for arm, rows in arm_rows.items():
            store[(arm, tag)] = rows

    # --- refusal gate: reproduce the whitelist script's point estimates ------
    bad = []
    for (arm, tag), rows in store.items():
        got = round(pooled_lift(rows)[0], 2)
        want = EXPECTED[(arm, tag)]
        if abs(got - want) > 0.005:
            bad.append(f"{arm}/{tag}: got {got}, whitelist script says {want}")
    if bad:
        print("REFUSING TO REPORT -- point estimates disagree with the source script:")
        for b in bad:
            print("   ", b)
        return 1
    print("self-check: point estimates reproduce "
          "audit_candidate_prediction_lift_whitelist.py exactly (A and C).\n")

    print(f"{'arm':10s} {'read':4s} {'n_cand':>6s} {'n_pred':>6s} {'lift':>6s} "
          f"{'95% CI (cluster)':>20s} {'deff':>5s}  verdict")
    deffs = {}
    for tag in ("A", "C"):
        for arm in ("no-graph", "graph"):
            rows = store[(arm, tag)]
            lift, elig, hits, bh, bn = pooled_lift(rows)
            boots = []
            for _ in range(BOOT):
                draw = [rows[rng.randrange(len(rows))] for _ in rows]
                b = pooled_lift(draw)[0]
                if b:
                    boots.append(b)
            boots.sort()
            lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]
            p, b0 = hits / elig, bh / bn
            var_naive = (p * (1 - p) / elig) / (b0 * b0)
            var_boot = sum((x - lift) ** 2 for x in boots) / (len(boots) - 1)
            deff = var_boot / var_naive if var_naive else float("nan")
            deffs[(arm, tag)] = deff
            if len(rows) < MIN_CLUSTERS:
                # With k clusters the resample space has only C(2k-1,k) distinct
                # multisets; at k=2 that is 3. The interval is an artifact of the
                # resampler, not an estimate, and the collapsed design effect is
                # the symptom. Refuse it rather than print a spuriously tight CI.
                print(f"{arm:10s} {tag:4s} {len(rows):6d} {elig:6d} {lift:6.2f} "
                      f"  {'n/a':>18s}      {deff:5.2f}  "
                      f"**bootstrap degenerate at {len(rows)} clusters -- no interval**")
                continue
            verdict = "excludes 1.0" if (lo > 1.0 or hi < 1.0) else "**includes 1.0 -- not distinguishable from chance**"
            print(f"{arm:10s} {tag:4s} {len(rows):6d} {elig:6d} {lift:6.2f} "
                  f"  [{lo:5.2f}, {hi:5.2f}]      {deff:5.2f}  {verdict}")

    print()
    print("=" * 82)
    print("Minimum detectable lift at the realised samples (one-sided exact binomial)")
    print("=" * 82)
    for tag in ("A",):
        for arm in ("no-graph", "graph"):
            rows = store[(arm, tag)]
            _, elig, hits, bh, bn = pooled_lift(rows)
            base = bh / bn
            k, mde = mde_lift(elig, base)
            deff = deffs[(arm, tag)]
            print(f"{arm:10s} n_pred={elig:3d} base={base:.3f}  "
                  f"need >={k:3d} hits  MDE lift={mde:.2f} (unclustered)  "
                  f"~{1 + (mde - 1) * math.sqrt(max(deff, 1.0)):.2f} after deff={deff:.2f}")
    print("  Read: any true lift below the MDE could not have been distinguished from")
    print("  chance at this sample, whichever direction it pointed.")

    print()
    print("=" * 82)
    print("Same-config flip rate -- Wilson 95% CI per seed and pooled (F15/F44/F45)")
    print("=" * 82)
    tk = tn = 0
    for label, k, n in FLIPS:
        lo, hi = wilson(k, n)
        tk += k
        tn += n
        print(f"{label:22s} {k:3d}/{n:3d} = {100*k/n:5.2f}%   95% CI [{100*lo:5.2f}%, {100*hi:5.2f}%]")
    lo, hi = wilson(tk, tn)
    print(f"{'pooled':22s} {tk:3d}/{tn:3d} = {100*tk/tn:5.2f}%   95% CI [{100*lo:5.2f}%, {100*hi:5.2f}%]")
    print("  The three per-seed intervals overlap heavily: the noise floor is a")
    print("  property of the bed, and this is the interval that says so.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
