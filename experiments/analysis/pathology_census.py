"""T1+T2: pathology clustering of the M26b swing queue + leak/contamination audit.

Bins (assignment priority order):
  leak-route   — >=50% of PASS trajectories touch benchmark-artifact markers
  wall         — >=50% of FAIL trajectories carry hard wall markers (403/503/
                 security verification/blocked) on page-grade fetches
  friction     — fails dominated by Bash empty/error streaks (851e family)
  divergence   — web-dominant, median fail calls >= pass calls + 6 (8b family)
  wrong-close  — fails mostly exit=done with fail calls close to pass calls
  starved      — fails mostly budget_exceeded at cap
  mixed        — none dominant
Also: T2b — per-rep leak audit of DOSSIER6 _cov applied 8131 passes.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(r"D:\PycharmProj\HarnessX")
RUN = REPO / "recipe/gaia_evolver/runs/ghx-seed1"
sys.path.insert(0, str(REPO / "experiments" / "analysis"))

LEAK = ("GAIA_web", "gaia_validation", "metadata.jsonl", "ground_truth",
        "Final_Assignment_Template", "adk-gaia")
WALL = ("HTTP 403", "HTTP Error 503", "503: Service Unavailable", "security verification",
        "You've been blocked", "Cloudflare", "[blocked]", "SEARCH UNAVAILABLE",
        "Performing security verification")

def traj(tid, rnd):
    for p in (RUN / f"R{rnd+1}" / "trajectories" / f"{tid}_r0.jsonl",
              RUN / f"R{rnd}" / "raw" / f"{tid}_r0.jsonl"):
        if p.exists():
            return p
    return None

def scan(path):
    """Return (n_calls, ws, bash, bash_err_streak_max, leak_hits, wall_hits)."""
    t = path.read_text(encoding="utf-8", errors="replace")
    leak = sum(t.count(m) for m in LEAK)
    wall = sum(t.count(m) for m in WALL)
    ws = t.count('"name": "WebSearch"') + t.count("'name': 'WebSearch'")
    bash = t.count('"name": "Bash"')
    calls = t.count('"type": "tool_use"')
    # crude bash-error streak: count '[stderr]'/'is not recognized'/empty results after Bash
    berr = t.count("is not recognized") + t.count("STDERR")
    return calls, ws, bash, berr, leak, wall

hist = defaultdict(list)
seen = {}
for line in (RUN / "data/task_history.jsonl").open(encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if "task_id" not in r or r.get("carried"):
        continue
    seen[(r["task_id"], r["round"])] = r
for (tid, rnd), r in sorted(seen.items(), key=lambda x: x[0][1]):
    fl = bool((r.get("passed_flags") or [r.get("passed")])[0])
    hist[tid].append((rnd, fl, str(r.get("exit", ""))[:6], r.get("steps")))

bins = defaultdict(list)
detail = {}
for tid, atts in sorted(hist.items()):
    np_ = sum(1 for a in atts if a[1])
    if not (0 < np_ < len(atts)):
        continue
    short = tid[:8]
    p_feats, f_feats = [], []
    p_leak = f_wall = f_traj = p_traj = 0
    for rnd, fl, ex, st in atts:
        tp = traj(tid, rnd)
        if not tp:
            continue
        c = scan(tp)
        if fl:
            p_traj += 1
            p_feats.append(c)
            if c[4] > 0:
                p_leak += 1
        else:
            f_traj += 1
            f_feats.append(c)
            if c[5] >= 2:
                f_wall += 1
    def med(v):
        v = sorted(v)
        return v[len(v) // 2] if v else 0
    pc = med([x[0] for x in p_feats]); fc = med([x[0] for x in f_feats])
    fws = med([x[1] for x in f_feats]); fb = med([x[2] for x in f_feats])
    fberr = med([x[3] for x in f_feats])
    f_exits = Counter(a[2] for a in atts if not a[1])
    n_f = sum(f_exits.values())
    done_share = f_exits.get("done", 0) / max(1, n_f)
    budget_share = f_exits.get("budget", 0) / max(1, n_f)
    leak_rate = p_leak / max(1, p_traj)
    wall_rate = f_wall / max(1, f_traj)
    if leak_rate >= 0.5:
        b = "leak-route"
    elif wall_rate >= 0.5:
        b = "wall"
    elif fb >= 5 and fberr >= 3:
        b = "friction"
    elif fc >= pc + 6 and fws >= fb:
        b = "divergence"
    elif budget_share >= 0.6:
        b = "starved"
    elif done_share >= 0.6:
        b = "wrong-close"
    else:
        b = "mixed"
    bins[b].append(short)
    detail[short] = (f"P{np_}/{len(atts)} callsP{pc}/F{fc} WSf{fws} Bf{fb} "
                     f"done{done_share:.0%} bud{budget_share:.0%} "
                     f"leakP{leak_rate:.0%} wallF{wall_rate:.0%}")

print("=== T1: pathology bins (M26b swing queue) ===")
for b in ("leak-route", "wall", "friction", "divergence", "wrong-close", "starved", "mixed"):
    ts = bins.get(b, [])
    print(f"\n[{b}] n={len(ts)}")
    for t in ts:
        print(f"  {t}  {detail[t]}")

# ---- T2b: DOSSIER6 _cov applied 8131 leak audit per rep ----
print("\n=== T2b: DOSSIER6 _cov applied 8131e2c0 per-rep leak markers ===")
ROOT = REPO / "recipe/gaia_evolver/runs/PROBE_DOSSIER6/verify_sessions_applied"
for sess in sorted(ROOT.iterdir()):
    m = re.search(r"CLTRIAL_cov-applied-8131e2c0-r(\d+)", sess.name)
    if not m:
        continue
    hits = Counter()
    for f in sess.glob("*.jsonl"):
        if "_trace" in f.name:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        for mk in LEAK:
            hits[mk] += t.count(mk)
    tot = sum(hits.values())
    print(f"r{m.group(1)}: leak_hits={tot} {dict((k, v) for k, v in hits.items() if v)}")
