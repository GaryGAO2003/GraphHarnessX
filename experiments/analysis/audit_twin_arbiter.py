# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Can a mechanical rule pick the passing twin, using only submit-time signals?

If yes, k=2 sampling plus arbitration converts reliability variance directly
into score — an inference-time consumer of run records that never touches the
evolve loop.  Tested offline on the same twin pairs audit_divergence_points
builds: for each (passing, failing) pair, ask each candidate arbiter which run
it would submit, and score it against the known outcome.

Arbiters (all computable before any grading):
  grounding   — prefer the run whose FINAL ANSWER string appears verbatim in
                one of its own tool results
  page-grade  — prefer the run with more non-empty WebFetch/Browser payloads
  fewer-empty — prefer the run with the lower empty-payload fraction
  shorter     — prefer the run with the shorter tool spine (decisiveness)
  answered    — prefer the run that produced a parseable FINAL ANSWER at all
Each arbiter abstains when its feature ties; accuracy is over decided pairs.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_divergence_points import ROOT, pass1, spine  # noqa: E402

ANS = re.compile(r"FINAL ANSWER[:\s]*(.+)", re.I)


def run_features(traj: Path):
    sp = spine(traj)
    answer = ""
    payload_texts = []
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
            c = msg.get("content")
            if isinstance(c, str):
                m = ANS.search(c)
                if m:
                    answer = m.group(1).strip().strip("*` .")
        elif r.get("type") == "raw_tool":
            c = msg.get("content")
            payload_texts.append(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
    n = len(sp)
    empties = sum(1 for _, _, o in sp if o != "ok")
    page_ok = sum(1 for t, _, o in sp if t in ("WebFetch", "Browser") and o == "ok")
    grounded = bool(
        answer
        and 4 <= len(answer) <= 120
        and any(answer.lower() in (t or "").lower() for t in payload_texts)
    )
    return {
        "grounded": grounded,
        "page_ok": page_ok,
        "empty_frac": (empties / n) if n else 1.0,
        "spine_len": n,
        "answered": bool(answer),
    }


def build_pairs():
    hist = [
        json.loads(line)
        for line in (ROOT / "data" / "task_history.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    by_rt = {(int(r["round"]), str(r["task_id"])): r for r in hist if not r.get("carried")}
    pairs = []
    for (rnd, tid), r in by_rt.items():
        flags = r.get("passed_flags")
        if rnd != 0 or not isinstance(flags, list) or len(flags) < 2 or flags[0] == flags[1]:
            continue
        d = ROOT / "R0" / "raw"
        t0, t1 = d / f"{tid}_r0.jsonl", d / f"{tid}_r1.jsonl"
        if t0.exists() and t1.exists():
            tp, tf = (t0, t1) if flags[0] else (t1, t0)
            pairs.append(("A", tid, tp, tf))
    # B pairs: reuse the divergence module's derivation by importing main-level
    # logic would rerun prints; rebuild inline (same rules).
    import re as _re

    def semantic(p: Path) -> str:
        t = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        return _re.sub(r"^\s*base_dir:.*$", "  base_dir: <x>", t, flags=_re.M)

    curves = json.loads((ROOT / "curves.json").read_text(encoding="utf-8"))
    ships = {
        int(s["round"])
        for s in json.loads((ROOT / "scoreboard.json").read_text(encoding="utf-8")).get("ships") or []
    }
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
                tp, tf = (ta, tb) if pa else (tb, ta)
                pairs.append(("B", tid, tp, tf))
    return pairs


ARBITERS = {
    "grounding": lambda p, f: (p["grounded"], f["grounded"]),
    "page-grade": lambda p, f: (p["page_ok"], f["page_ok"]),
    "fewer-empty": lambda p, f: (-p["empty_frac"], -f["empty_frac"]),
    "shorter": lambda p, f: (-p["spine_len"], -f["spine_len"]),
    "answered": lambda p, f: (p["answered"], f["answered"]),
}


def main() -> int:
    pairs = build_pairs()
    print(f"pairs: {Counter(p[0] for p in pairs)}")
    feats = {}
    for _, _, tp, tf in pairs:
        for t in (tp, tf):
            if t not in feats:
                feats[t] = run_features(t)
    for name, key in ARBITERS.items():
        decided = correct = 0
        for _, _, tp, tf in pairs:
            vp, vf = key(feats[tp], feats[tf])
            if vp == vf:
                continue
            decided += 1
            correct += vp > vf
        acc = correct / decided if decided else 0.0
        print(f"{name:12} decided {decided:3d}/{len(pairs)}  picks the PASSING twin {100*acc:.0f}%")
    # combo: grounding first, then page-grade, then fewer-empty
    decided = correct = 0
    for _, _, tp, tf in pairs:
        p, f = feats[tp], feats[tf]
        pick = None
        for key in (ARBITERS["grounding"], ARBITERS["page-grade"], ARBITERS["fewer-empty"]):
            vp, vf = key(p, f)
            if vp != vf:
                pick = vp > vf
                break
        if pick is None:
            continue
        decided += 1
        correct += pick
    print(f"{'combo':12} decided {decided:3d}/{len(pairs)}  picks the PASSING twin {100*correct/max(1,decided):.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
