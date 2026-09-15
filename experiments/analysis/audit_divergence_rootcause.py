# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""What SEEDS a plan fork — the model, or the world it was shown?

audit_divergence_points found 74% of same-config twins fork in tool choice, but
payload CLASS (empty/ok) cannot see content: two 'ok' search returns can be
different pages.  This audit compares the CONTENT of every argument and return
along the shared prefix before the fork, token-set Jaccard over normalised
text, and classifies each plan-fork pair by root cause:

* ``sampling``        — prefix returns are near-identical (>= HI): the model
                        saw the same world and still chose differently
* ``env-nondet``      — some prefix return diverged (< LO) while the ARGS that
                        produced it were near-identical: the world answered the
                        same question differently
* ``self-seeded``     — the earliest content divergence is in the model's OWN
                        argument wording (args < LO at or before the first
                        diverged return): a paraphrase changed what the world
                        returned, which changed the plan
* ``mixed/ambiguous`` — everything in between

The chain matters for medicine: ``env-nondet`` is fixed by pinning/replaying
recorded returns; ``self-seeded`` by canonicalising queries (or pinning too —
serve the recorded return for the semantically-same call); pure ``sampling``
only by arbitration/voting.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_divergence_points import ROOT, SUBSET, first_fork, pass1, spine  # noqa: E402

import os
HI = float(os.environ.get("RC_HI", "0.8"))
LO = float(os.environ.get("RC_LO", "0.5"))
_TOK = re.compile(r"[a-z0-9]{3,}")


def rich_calls(traj: Path):
    """Ordered (tool, args_text, return_text) with real content, capped."""
    order: list[str] = []
    args: dict[str, tuple[str, str]] = {}
    rets: dict[str, str] = {}
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
                order.append(cid)
                args[cid] = (
                    str(tc.get("name")),
                    json.dumps(tc.get("input") or {}, ensure_ascii=False, sort_keys=True)[:3000],
                )
        elif r.get("type") == "raw_tool":
            cid = str(msg.get("tool_call_id"))
            c = msg.get("content")
            rets[cid] = (c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))[:3000]
    out = []
    for cid in order:
        if cid in args:
            tool, at = args[cid]
            out.append((tool, at, rets.get(cid, "")))
    return out


def jac(a: str, b: str) -> float:
    ta, tb = set(_TOK.findall(a.lower())), set(_TOK.findall(b.lower()))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def build_pairs():
    hist = [
        json.loads(line)
        for line in (ROOT / "data" / "task_history.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    by_rt = {(int(r["round"]), str(r["task_id"])): r for r in hist
             if not r.get("carried") and str(r["task_id"]) in SUBSET}
    pairs = []
    for (rnd, tid), r in by_rt.items():
        flags = r.get("passed_flags")
        if rnd != 0 or not isinstance(flags, list) or len(flags) < 2 or flags[0] == flags[1]:
            continue
        d = ROOT / "R0" / "raw"
        t0, t1 = d / f"{tid}_r0.jsonl", d / f"{tid}_r1.jsonl"
        if t0.exists() and t1.exists():
            pairs.append((t0, t1) if flags[0] else (t1, t0))
    def semantic(p: Path) -> str:
        t = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        return re.sub(r"^\s*base_dir:.*$", "  base_dir: <x>", t, flags=re.M)
    curves = json.loads((ROOT / "curves.json").read_text(encoding="utf-8"))
    ships = {int(s["round"]) for s in json.loads((ROOT / "scoreboard.json").read_text(encoding="utf-8")).get("ships") or []}
    sem = {int(c["round"]): semantic(ROOT / f"R{int(c['round'])}" / "config.yaml") for c in curves}
    for k in sorted(sem):
        if k - 1 not in sem or sem[k] != sem[k - 1] or k in ships:
            continue
        a, b = k - 1, k
        for (rnd, tid), r in by_rt.items():
            if rnd != a or (b, tid) not in by_rt:
                continue
            rb = by_rt[(b, tid)]
            pa = pass1(r.get("passed_flags")) if r.get("passed_flags") else bool(r.get("passed"))
            pb = pass1(rb.get("passed_flags")) if rb.get("passed_flags") else bool(rb.get("passed"))
            if pa == pb:
                continue
            ta = ROOT / f"R{a+1}" / "trajectories" / f"{tid}_r0.jsonl"
            tb = ROOT / f"R{b+1}" / "trajectories" / f"{tid}_r0.jsonl"
            if ta.exists() and tb.exists():
                pairs.append((ta, tb) if pa else (tb, ta))
    return pairs


def main() -> int:
    pairs = build_pairs()
    kinds: Counter = Counter()
    detail: Counter = Counter()
    seed_tool: Counter = Counter()
    for tp, tf in pairs:
        sp, sf = spine(tp), spine(tf)
        if not sp and not sf:
            continue
        kind, i, _, _ = first_fork(sp, sf)
        if not kind.startswith("plan"):
            kinds[kind] += 1
            continue
        kinds["plan-*"] += 1
        if i == 0:
            detail["sampling (fork at 0, no prefix)"] += 1
            continue
        rp, rf = rich_calls(tp), rich_calls(tf)
        n = min(i, len(rp), len(rf))
        first_ret_div = None
        args_div_before = False
        min_ret = 1.0
        for j in range(n):
            aj = jac(rp[j][1], rf[j][1])
            rj = jac(rp[j][2], rf[j][2])
            min_ret = min(min_ret, rj)
            if rj < LO and first_ret_div is None:
                first_ret_div = (j, aj)
                seed_tool[rp[j][0]] += 1
            if aj < LO and first_ret_div is None:
                args_div_before = True
        if first_ret_div is None:
            if min_ret >= HI:
                detail["sampling (prefix content identical)"] += 1
            else:
                detail["ambiguous (prefix mildly diverged)"] += 1
        else:
            j, aj = first_ret_div
            if aj >= HI and not args_div_before:
                detail["env-nondet (same question, different answer)"] += 1
            elif aj < LO or args_div_before:
                detail["self-seeded (own wording changed the world)"] += 1
            else:
                detail["mixed"] += 1
    print(f"pairs classified: {sum(kinds.values())}  ({dict(kinds)})")
    print("\nplan-fork root causes:")
    total = sum(detail.values())
    for k, c in detail.most_common():
        print(f"  {c:3d}  ({100*c/max(1,total):4.1f}%)  {k}")
    print("\nfirst diverged RETURN sits at tool:")
    for t, c in seed_tool.most_common(6):
        print(f"  {c:3d}  {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
