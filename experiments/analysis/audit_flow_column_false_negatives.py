# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Verified false negatives of the digest's ``next_uses_result`` column.

The column claims to grade whether a tool call's output was used.  Its check is
a >=20-character verbatim overlap with the NEXT assistant message.  This audit
needs no instrument of ours: restrict to PASSING rollouts, take the tool calls
whose result literally contains the final answer string — those results were
used, the task's own pass is the proof — and read the column's verdict.

Companion numbers (audit_flow_column_rate.py): over ALL non-empty calls on the
same arm the column says NO 68.1% of the time and "used" only 6.9%.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harnessx.aegis.stages.trace_facts import extract_trace_facts  # noqa: E402

ROOT = Path("recipe/gaia_evolver/runs/baseline-seed1")
ANS = re.compile(r"FINAL ANSWER[:\s]*(.+)", re.I)


def _passed_map() -> dict:
    out = {}
    for line in (ROOT / "data" / "task_history.jsonl").open(encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            out[(int(r.get("round", -1)), str(r.get("task_id")))] = bool(r.get("passed"))
    return out


def _events(traj: Path):
    for line in traj.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except ValueError:
            continue


def _answer(traj: Path) -> str:
    out = ""
    for r in _events(traj):
        if r.get("type") in ("raw_assistant", "assistant"):
            c = (r.get("message") or {}).get("content")
            if isinstance(c, str):
                m = ANS.search(c)
                if m:
                    out = m.group(1).strip().strip("*` .")
    return out


def _payloads(traj: Path) -> dict:
    out, pend = {}, {}
    for r in _events(traj):
        msg = r.get("message") or {}
        if r.get("type") in ("raw_assistant", "assistant"):
            for tc in msg.get("tool_calls") or []:
                pend[str(tc.get("id"))] = (int(r.get("step", 0) or 0), str(tc.get("name")))
        elif r.get("type") == "raw_tool":
            k = pend.get(str(msg.get("tool_call_id")))
            if k:
                c = msg.get("content")
                out[k] = (out.get(k, "") + (c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)))[:40000]
    return out


def main() -> int:
    passed = _passed_map()
    tot: Counter = Counter()
    fn_answer_lens: list[int] = []
    rollouts = 0
    for rnd in range(1, 17):
        tdir = ROOT / f"R{rnd}" / "trajectories"
        if not tdir.is_dir():
            continue
        for traj in sorted(tdir.glob("*_r0.jsonl")):
            tid = traj.name.split("_r0")[0]
            if not passed.get((rnd - 1, tid), False):  # R{k}/trajectories hold batch k-1
                continue
            a = _answer(traj)
            if len(a) < 4 or len(a) > 120:
                continue
            rollouts += 1
            pays = _payloads(traj)
            try:
                facts = extract_trace_facts(tid, [traj])
            except Exception:
                continue
            for c in facts.tool_calls:
                if c.return_len < 20:
                    continue
                text = pays.get((c.step, c.tool))
                if not text or a.lower() not in text.lower():
                    continue
                tot["contains_answer"] += 1
                if c.next_uses_result is False:
                    tot["graded_NO"] += 1
                    fn_answer_lens.append(len(a))
                elif c.next_uses_result is True:
                    tot["graded_used"] += 1
                else:
                    tot["abstain"] += 1

    d = tot["contains_answer"]
    print(f"passing rollouts with a parseable FINAL ANSWER: {rollouts}")
    print(f"tool calls whose result literally contains that answer: {d}")
    if d:
        print(f'  column graded "not referenced": {tot["graded_NO"]:4d} = {100*tot["graded_NO"]/d:.1f}%  <- verified false negatives')
        print(f"  column graded used            : {tot['graded_used']:4d} = {100*tot['graded_used']/d:.1f}%")
        print(f"  abstained                     : {tot['abstain']:4d}")
    if fn_answer_lens:
        fn_answer_lens.sort()
        short = sum(1 for x in fn_answer_lens if x < 20)
        print("\nmechanism, same population (the false negatives above):")
        print(f"  answer length median {fn_answer_lens[len(fn_answer_lens)//2]}, "
              f"p90 {fn_answer_lens[int(.9*len(fn_answer_lens))]}, max {fn_answer_lens[-1]}")
        print(f"  shorter than the column's own 20-char floor: {short} = {100*short/len(fn_answer_lens):.1f}%")
        print("  -> the use of a short fact is invisible to this column by construction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
