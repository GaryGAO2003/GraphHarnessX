# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Where do two runs of the SAME task under the SAME config part ways?

The campaigns' real headroom is reliability (20.5% of outcomes flip on an
identical config), and nothing in either arm ever localised where that variance
enters.  This audit does, mechanically, on two twin populations:

* **A — simultaneous twins**: M22-L0 round 0 ran k=2; every task whose two
  rollouts disagreed gives a same-instant, same-config pass/fail pair.
* **B — adjacent-round twins**: the eight ship-free semantically-identical
  config pairs (audit_same_config_flips), tasks whose pass@1 flipped.

Each run is reduced to its tool spine — the ordered (tool, args-hash,
payload-class) sequence parsed from the trajectory — and the pair is scanned
with a TWO-LEVEL alignment.  A strict args-level comparison is uninformative:
at nonzero temperature the model almost never words the same first query twice
(measured on the 100-task bed: 89/99 adjacent twins with a tool spine fork
on (tool, args-hash) at index 0).  So level 1
aligns tool NAMES (the plan shape) and level 2 walks the shared name prefix
looking for the first payload-CLASS difference:

* ``env-first``   — same plan so far, the world answered differently
* ``plan-fork``   — a different tool chosen before any visible outcome delta
* ``plan-length`` — one name spine is a proper prefix of the other
* ``same-plan``   — identical names and outcomes end to end: the flip lives in
                    argument wording / payload content / the final answer

``plan-fork`` is an UPPER bound on sampling variance: same-class payloads can
still differ in content, so a fork may be a reaction to unseen content, not a
free choice.  ``env-first`` is correspondingly a LOWER bound on environmental
variance.  Only index-0 plan forks are sampling with certainty.

Payload class uses the same emptiness judge the graph plane uses
(payload_is_empty), so 'environment' means empty-vs-nonempty — a conservative
lower bound on environmental variance (same-class different-content is not
counted).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harnessx.graph.unfold import payload_is_empty  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "recipe/gaia_evolver/runs/baseline-seed1"

# The thesis reports every number on the 100-task bed; restrict the twin
# population to it (the three pixel tasks the DeepSeek solver cannot attempt
# are dropped).
SUBSET = {t["task_id"] for t in json.loads(
    (ROOT.parent.parent / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))}
assert len(SUBSET) == 100, len(SUBSET)


def spine(traj: Path):
    """Ordered (tool, argsha8, payload_class) triples from one trajectory."""
    calls: list[tuple[str, str]] = []  # (id, ) order of issuance
    meta: dict[str, tuple[str, str]] = {}  # id -> (tool, argsha)
    result: dict[str, str] = {}  # id -> payload class
    for line in traj.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        msg = r.get("message") or {}
        if r.get("type") in ("raw_assistant", "assistant"):
            for tc in msg.get("tool_calls") or []:
                cid = str(tc.get("id"))
                try:
                    sha = hashlib.sha1(
                        json.dumps(tc.get("input") or {}, sort_keys=True, default=str).encode()
                    ).hexdigest()[:8]
                except Exception:
                    sha = "?"
                meta[cid] = (str(tc.get("name")), sha)
                calls.append((cid, ""))
        elif r.get("type") == "raw_tool":
            cid = str(msg.get("tool_call_id"))
            c = msg.get("content")
            text = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
            result[cid] = "empty" if payload_is_empty(text or "") else "ok"
    out = []
    for cid, _ in calls:
        if cid in meta:
            tool, sha = meta[cid]
            out.append((tool, sha, result.get(cid, "noresult")))
    return out


def first_fork(sp_pass, sp_fail):
    """Two-level fork report.

    Level 1 aligns tool NAMES only — at nonzero temperature the model almost
    never words the same first query twice, so an args-level comparison forks
    at index 0 for ~90% of twins and says nothing (measured before this
    refinement).  Level 2 walks the shared name prefix and asks where the
    payload CLASS first differs — the environment answering differently to the
    same tool.  Returns (kind, index, tool, extra):

    * ``env-first``   — outcomes diverge at i, strictly inside the shared name
                        prefix (extra says who got the empty)
    * ``plan-fork``   — tool names diverge at i before any outcome difference
    * ``plan-length`` — one name spine is a proper prefix of the other
    * ``same-plan``   — name spines identical, outcomes identical all the way:
                        the flip lives in content/answer, not in plan shape
    """
    names_p = [t for t, _, _ in sp_pass]
    names_f = [t for t, _, _ in sp_fail]
    n = min(len(names_p), len(names_f))
    name_fork = None
    for i in range(n):
        if names_p[i] != names_f[i]:
            name_fork = ("plan-fork", i, names_f[i])
            break
    if name_fork is None and len(names_p) != len(names_f):
        longer = names_f if len(names_f) > len(names_p) else names_p
        name_fork = ("plan-length", n, longer[n] if n < len(longer) else "-")
    limit = name_fork[1] if name_fork else n
    for i in range(limit):
        if sp_pass[i][2] != sp_fail[i][2]:
            who = "fail-got-empty" if sp_fail[i][2] == "empty" else "pass-got-empty"
            return "env-first", i, sp_fail[i][0], who
    if name_fork:
        return name_fork[0], name_fork[1], name_fork[2], ""
    return "same-plan", n, "-", ""


def pass1(flags) -> bool:
    return bool(flags[0]) if isinstance(flags, list) and flags else False


def main() -> int:
    hist_rows = [
        json.loads(line)
        for line in (ROOT / "data" / "task_history.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    by_rt = {(int(r["round"]), str(r["task_id"])): r for r in hist_rows
             if not r.get("carried") and str(r["task_id"]) in SUBSET}

    pairs = []  # (population, task, pass_traj, fail_traj)

    # A — simultaneous twins: R0 ran k=2; flags disagree
    for (rnd, tid), r in by_rt.items():
        flags = r.get("passed_flags")
        if rnd != 0 or not isinstance(flags, list) or len(flags) < 2 or flags[0] == flags[1]:
            continue
        # raw/ carries NO offset: R{k}/raw holds batch k's own rollouts, while
        # R{k}/trajectories holds batch k-1 — one more shape trap of the family.
        d = ROOT / "R0" / "raw"
        t0, t1 = d / f"{tid}_r0.jsonl", d / f"{tid}_r1.jsonl"
        if t0.exists() and t1.exists():
            tp, tf = (t0, t1) if flags[0] else (t1, t0)
            pairs.append(("A-simultaneous", tid, tp, tf))

    # B — adjacent same-config pairs (from audit_same_config_flips: semantic
    # equality after neutralising base_dir, and no ship in round b)
    import subprocess  # noqa: F401  (documentational; pairs are re-derived here)

    def semantic(p: Path) -> str:
        t = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        return re.sub(r"^\s*base_dir:.*$", "  base_dir: <x>", t, flags=re.M)

    curves = json.loads((ROOT / "curves.json").read_text(encoding="utf-8"))
    ships = {int(s["round"]) for s in json.loads((ROOT / "scoreboard.json").read_text(encoding="utf-8")).get("ships") or []}
    sem = {int(c["round"]): semantic(ROOT / f"R{int(c['round'])}" / "config.yaml") for c in curves}
    round_pairs = [
        (k - 1, k)
        for k in sorted(sem)
        if k - 1 in sem and sem[k] == sem[k - 1] and k not in ships
    ]
    for a, b in round_pairs:
        for (rnd, tid), r in by_rt.items():
            if rnd != a:
                continue
            rb = by_rt.get((b, tid))
            if rb is None:
                continue
            pa, pb = pass1(r.get("passed_flags")) or bool(r.get("passed")) and False, None
            pa = pass1(r.get("passed_flags")) if r.get("passed_flags") else bool(r.get("passed"))
            pb = pass1(rb.get("passed_flags")) if rb.get("passed_flags") else bool(rb.get("passed"))
            if pa == pb:
                continue
            ta = ROOT / f"R{a+1}" / "trajectories" / f"{tid}_r0.jsonl"
            tb = ROOT / f"R{b+1}" / "trajectories" / f"{tid}_r0.jsonl"
            if not (ta.exists() and tb.exists()):
                continue
            tp, tf = (ta, tb) if pa else (tb, ta)
            pairs.append(("B-adjacent", tid, tp, tf))

    print(f"twin pairs: {Counter(p[0] for p in pairs)}")

    kinds = {"A-simultaneous": Counter(), "B-adjacent": Counter()}
    fork_idx = {"A-simultaneous": [], "B-adjacent": []}
    env_tools: Counter = Counter()
    env_dir: Counter = Counter()
    plan_tools: Counter = Counter()
    sameplan_len: list[int] = []
    for pop, tid, tp, tf in pairs:
        sp, sf = spine(tp), spine(tf)
        if not sp and not sf:
            kinds[pop]["no-tools-at-all"] += 1
            continue
        kind, i, tool, extra = first_fork(sp, sf)
        kinds[pop][kind] += 1
        fork_idx[pop].append(i)
        if kind == "env-first":
            env_tools[tool] += 1
            env_dir[extra] += 1
        elif kind.startswith("plan"):
            plan_tools[tool] += 1
        elif kind == "same-plan":
            sameplan_len.append(len(sp))

    for pop in ("A-simultaneous", "B-adjacent"):
        print(f"\n== {pop} ==  fork kinds: {dict(kinds[pop])}")
        idx = sorted(fork_idx[pop])
        if idx:
            print(f"   fork index: median {idx[len(idx)//2]}, at-0 {sum(1 for x in idx if x == 0)}/{len(idx)}")
    print("\nenv-first forks — same tool name, different payload class:")
    print(f"   direction: {dict(env_dir)}")
    for t, c in env_tools.most_common(8):
        print(f"   {c:3d}  {t}")
    print("\nplan forks by failing-run tool at the fork:")
    for t, c in plan_tools.most_common(8):
        print(f"   {c:3d}  {t}")
    if sameplan_len:
        sameplan_len.sort()
        print(f"\nsame-plan pairs (flip lives past the tool spine): "
              f"n={len(sameplan_len)}, spine length median {sameplan_len[len(sameplan_len)//2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
