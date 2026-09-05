"""Pre-registered proof statistics over all clean same-window paired cells.

Cells: (task, batch) net-win difference. Dirty tasks (8b3379c0, 8131e2c0 —
leak-route) excluded everywhere.
Primary:   sign test over nonzero cells — reported BOTH all-cells
           (retrospective-contaminated, labeled) and prospective-only
           (_proof1/_proof2, the clean pre-registered test).
Secondary: pooled one-tailed Fisher on clean cells.
Mechanism: confident-wrong share among fails (exit=done, no UNVERIFIED in tail).
"""
import json
from math import comb
from pathlib import Path

REPO = Path(r"D:\PycharmProj\HarnessX")
D5 = REPO / "recipe/gaia_evolver/runs/PROBE_DOSSIER5"
D6 = REPO / "recipe/gaia_evolver/runs/PROBE_DOSSIER6"
DIRTY = ("8b3379c0", "8131e2c0")
BATCHES = [  # (label, dir, tag, prospective)
    ("w3", D5, "_w3", False),
    ("cov", D6, "_cov", False),
    ("transfer", D6, "_transfer", False),
    ("canary", D6, "_canary", False),
    ("proof1", D6, "_proof1", True),
    ("proof2", D6, "_proof2", True),
]


def load(dirp, tag, arm):
    p = dirp / f"trial_{arm}{tag}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def fisher_one_tail(a, b, c, d):
    """P(applied wins >= a) under fixed margins; a=applied wins, b=applied losses,
    c=parent wins, d=parent losses."""
    n = a + b + c + d
    row1 = a + b
    col1 = a + c
    denom = comb(n, col1)
    p = 0.0
    for x in range(a, min(row1, col1) + 1):
        if col1 - x <= n - row1 and col1 - x >= 0:
            p += comb(row1, x) * comb(n - row1, col1 - x) / denom
    return p


cells = []
tot = {"pw": 0, "pn": 0, "aw": 0, "an": 0}
mech = {"p_cw": 0, "p_f": 0, "a_cw": 0, "a_f": 0}
for label, dirp, tag, prosp in BATCHES:
    par, app = load(dirp, tag, "parent"), load(dirp, tag, "applied")
    if not par or not app:
        continue
    for tid in sorted(par):
        if any(tid.startswith(x) for x in DIRTY):
            continue
        pv = [r for r in par[tid] if r.get("valid")]
        av = [r for r in app.get(tid, []) if r.get("valid")]
        pw = sum(1 for r in pv if r["passed"])
        aw = sum(1 for r in av if r["passed"])
        cells.append({"batch": label, "tid": tid[:8], "d": aw - pw,
                      "pw": pw, "pn": len(pv), "aw": aw, "an": len(av),
                      "prospective": prosp})
        tot["pw"] += pw; tot["pn"] += len(pv)
        tot["aw"] += aw; tot["an"] += len(av)
        for r in pv:
            if not r["passed"]:
                mech["p_f"] += 1
                if r.get("exit") == "done" and "UNVERIFIED" not in (r.get("tail") or ""):
                    mech["p_cw"] += 1
        for r in av:
            if not r["passed"]:
                mech["a_f"] += 1
                if r.get("exit") == "done" and "UNVERIFIED" not in (r.get("tail") or ""):
                    mech["a_cw"] += 1


def sign_test(cs):
    pos = sum(1 for c in cs if c["d"] > 0)
    neg = sum(1 for c in cs if c["d"] < 0)
    n = pos + neg
    if n == 0:
        return pos, neg, 1.0
    p = sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n
    return pos, neg, p


print("=== cells ===")
for c in cells:
    mark = "P" if c["prospective"] else " "
    print(f"[{mark}] {c['batch']:>8} {c['tid']}  parent {c['pw']}/{c['pn']}  "
          f"applied {c['aw']}/{c['an']}  d={c['d']:+d}")

for name, sel in (("ALL cells (retro-contaminated, descriptive)", cells),
                  ("PROSPECTIVE only (pre-registered primary)",
                   [c for c in cells if c["prospective"]])):
    pos, neg, p = sign_test(sel)
    print(f"\n{name}: {len(sel)} cells, +{pos}/-{neg}, one-tailed sign p={p:.4f}")

a, b = tot["aw"], tot["an"] - tot["aw"]
c_, d = tot["pw"], tot["pn"] - tot["pw"]
print(f"\npooled clean: parent {tot['pw']}/{tot['pn']} vs applied {tot['aw']}/{tot['an']}"
      f"  Fisher(one-tail)={fisher_one_tail(a, b, c_, d):.4f}")
print(f"mechanism: confident-wrong among fails  parent {mech['p_cw']}/{mech['p_f']}"
      f"  applied {mech['a_cw']}/{mech['a_f']}")
