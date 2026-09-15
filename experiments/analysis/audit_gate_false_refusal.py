# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Sixth gate (graph-existence gate, harnessx/ghx/graph_gate.py): its false-refusal rate,
bounded by a landing-round recount.  (thesis F70; wording in F11, sections 4.7, 5.2.2, 6.2)

Read-only over the six whitelist campaigns (baseline-seed1..3 = no-graph, ghx-seed1..3 = graph),
rounds R1..R15; quarantined *_poisoned_gateway directories are skipped by the ^R\\d+$ rule.

Parts
  A   the gate's actual record: graph-existence verdict files only (the scope gate writes
      'CHECKED' files into the same directory; they are excluded)
  B   replay forensics per checked verdict: the replayed task, what its U holds, the verdict
      recomputed from the U, the draw recomputed with history <= k-1 (pick_replay_task's rule:
      longest consecutive-failure streak among the predicted tasks, ties lexicographic)
  D   shipped tool_call candidates: the landing round's own trajectories are a second recorded
      draw; absence on a random task / on the predicted set / on the task the gate would draw
  E   the 18 refusals one by one
  B2  shipped processor_invocation candidates: graph arm by the landing-round U graphs (the
      gate's own criterion: intervening invocations >= floor); no-graph arm by the official
      HarnessJournal trace (processor_trigger events with action == intervention)
  B3  same task, two recorded draws: the gate's replay verdict against the landing round
  C2  null-hypothesis probability of each existing-tool verdict from the task's own history
  C3  replay informativeness (steps, tool calls, cost)
  D1  design number: draw k predicted tasks, refuse only when all k are absent
  D2  bookkeeping identities: trajectory tool_call_counts == U tool nodes; U interventions ==
      trace intervention events
  F70 the numbers the ledger row cites, in one block

Usage:  python experiments/analysis/audit_gate_false_refusal.py [--out F70.json] [--cache DIR]
        (--cache keeps per-round U/trace summaries on disk so a rerun is cheap; default: none)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from harnessx.aegis.agents.evolver import parse_candidate_manifest  # noqa: E402
from harnessx.ghx.attribution_graph import (  # noqa: E402
    infer_signature,
    processor_file_uri_static_id,
    processor_static_id,
)
from harnessx.ghx.gate_replay import _predicted_from_manifest  # noqa: E402
from harnessx.graph.unfold import load_unfolded  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="", help="write the F70 numbers and per-candidate rows as JSON")
ap.add_argument("--cache", default="", help="directory for per-round summaries (optional)")
ap.add_argument("--runs", default="", help="runs root (default: recipe/gaia_evolver/runs under the repo)")
ARGS = ap.parse_args()

RUNS = Path(ARGS.runs) if ARGS.runs else REPO / "recipe" / "gaia_evolver" / "runs"
CACHE = Path(ARGS.cache) if ARGS.cache else None
if CACHE:
    CACHE.mkdir(parents=True, exist_ok=True)
CAMPAIGNS = [
    ("baseline-seed1", "no-graph"),
    ("baseline-seed2", "no-graph"),
    ("baseline-seed3", "no-graph"),
    ("ghx-seed1", "graph"),
    ("ghx-seed2", "graph"),
    ("ghx-seed3", "graph"),
]
LAST = 15
RD = re.compile(r"^R(\d+)$")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TOOL_PAIR = re.compile(r'"([^"]+)"\s*:\s*(\d+)')
F70: dict = {}


def rounds_of(run: Path) -> list[tuple[int, Path]]:
    out = []
    for p in run.iterdir():
        m = RD.match(p.name)
        if m and p.is_dir():
            out.append((int(m.group(1)), p))
    return sorted(out)


def frontmatter(path: Path, max_lines: int = 60) -> str:
    lines = []
    with open(path, encoding="utf-8", errors="replace") as f:
        first = f.readline()
        if not first.startswith("---"):
            return ""
        for _ in range(max_lines):
            line = f.readline()
            if not line or line.startswith("---"):
                break
            lines.append(line)
    return "".join(lines)


def parse_traj(path: Path) -> tuple[str, dict[str, int], bool | None]:
    fm = frontmatter(path)
    m = re.search(r'^task_id:\s*"?([^"\n]+)"?', fm, re.M)
    tid = m.group(1).strip() if m else path.stem.split("_r")[0]
    counts: dict[str, int] = {}
    m = re.search(r"^tool_call_counts:\s*(\{[^}]*\})", fm, re.M)
    if m:
        for tm in TOOL_PAIR.finditer(m.group(1)):
            counts[tm.group(1)] = int(tm.group(2))
    m = re.search(r"^eval_passed:\s*(true|false)", fm, re.M)
    passed = None if not m else (m.group(1) == "true")
    return tid, counts, passed


def task_text(path: Path) -> str:
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Task\s*\n(.*?)\n## ", t, re.S | re.M)
    return " ".join((m.group(1) if m else "").split())


def wilson(x, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def pct(x, n):
    lo, hi = wilson(x, n)
    return f"{x}/{n} = {100 * x / max(1, n):.0f}% [{lo:.0f}, {hi:.0f}]"


# ---------------------------------------------------------------- trajectory index
TRAJ: dict[str, dict[int, dict[str, dict[str, int]]]] = {}   # run -> round -> task -> counts
TEXT: dict[str, dict[str, str]] = {}                            # run -> normalized R0 task text -> task
for run, arm in CAMPAIGNS:
    TRAJ[run] = {}
    TEXT[run] = {}
    for k, rd in rounds_of(RUNS / run):
        tr = rd / "trajectories"
        if not tr.exists():
            continue
        by_task: dict[str, dict[str, int]] = {}
        for md in tr.glob("*.md"):
            tid, counts, _passed = parse_traj(md)
            cur = by_task.setdefault(tid, {})
            for name, n in counts.items():
                cur[name] = max(cur.get(name, 0), n)
            if k == 0 and tid not in TEXT[run].values():
                txt = task_text(md)
                if txt:
                    TEXT[run][txt[:160]] = tid
        TRAJ[run][k] = by_task


def task_from_text(run: str, text: str) -> str | None:
    key = " ".join((text or "").split())[:160]
    if key in TEXT[run]:
        return TEXT[run][key]
    for t, tid in TEXT[run].items():
        if key and (t.startswith(key[:80]) or key.startswith(t[:80])):
            return tid
    return None


# ---------------------------------------------------------------- history / the gate's draw
def history(run: str) -> dict[str, dict[int, bool]]:
    per: dict[str, dict[int, bool]] = {}
    path = RUNS / run / "data" / "task_history.jsonl"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        tid = str(row.get("task_id") or "")
        if not tid:
            continue
        flags = row.get("passed_flags")
        if not isinstance(flags, list) or not flags:
            flags = [bool(row.get("passed", False))]
        per.setdefault(tid, {})[int(row.get("round", 0))] = any(flags)
    return per


HIST = {run: history(run) for run, _ in CAMPAIGNS}


def streaks_upto(run: str, upto: int) -> dict[str, int]:
    out = {}
    for tid, by_round in HIST[run].items():
        rounds = {r: v for r, v in by_round.items() if r <= upto}
        if not rounds:
            continue
        streak, r = 0, max(rounds)
        while r in rounds and not rounds[r]:
            streak += 1
            r -= 1
        out[tid] = streak
    return out


def ordered_preds(preds, run: str, upto: int) -> list[str]:
    st = streaks_upto(run, upto)
    return sorted([str(p) for p in (preds or []) if p], key=lambda t: (-st.get(t, 0), t))


def pick(preds, run: str, upto: int) -> str | None:
    order = ordered_preds(preds, run, upto)
    return order[0] if order else None


def manifest(run: str, k: int, cid: str):
    p = RUNS / run / f"R{k}" / "candidates" / f"{cid}.md"
    if not p.exists():
        return None
    fm, _ = parse_candidate_manifest(p.read_text(encoding="utf-8"))
    return fm if isinstance(fm, dict) else None


def floor_of(sig: dict) -> int:
    for key in ("expected_min_calls", "min_calls"):
        if sig.get(key) is not None:
            try:
                return int(sig[key])
            except (TypeError, ValueError):
                continue
    return 1


# ================================================================== A. the gate's record
GATE_HEAD = "# Graph-existence gate"
verdicts: list[dict] = []
for run, arm in CAMPAIGNS:
    if arm != "graph":
        continue
    for k, rd in rounds_of(RUNS / run):
        gd = rd / "graph_evidence" / "gate"
        if not gd.exists():
            continue
        for f in sorted(gd.glob("*.md")):
            t = f.read_text(encoding="utf-8", errors="replace")
            if not t.startswith(GATE_HEAD):
                continue
            head = re.search(r"^\*\*(.+?)\*\*", t, re.M).group(1)
            ok = "- ok: True" in t
            checked = "- checked: True" in t
            tool = re.search(r"- tool: `tool:(.+?)`", t)
            cnt = re.search(r"invocations in replay U: (\d+) \(floor (\d+)\)", t)
            verdicts.append({
                "run": run, "round": k, "cid": f.stem, "head": head, "ok": ok, "checked": checked,
                "target": tool.group(1) if tool else "", "count": int(cnt.group(1)) if cnt else None,
                "floor": int(cnt.group(2)) if cnt else None,
                "kind": ("proc" if tool and tool.group(1).startswith("proc:") else "tool") if tool else "none",
            })

print("=" * 100)
print("A. The gate's record (graph-existence verdict files, R1-R15, quarantined dirs skipped)")
tot = Counter()
for run, arm in CAMPAIGNS:
    if arm != "graph":
        continue
    vs = [v for v in verdicts if v["run"] == run and 1 <= v["round"] <= LAST]
    c = Counter("refused" if not v["ok"] else ("passed" if v["checked"] else "through") for v in vs)
    kinds = Counter((("refused" if not v["ok"] else "passed"), v["kind"]) for v in vs if v["checked"])
    print(f"  {run:14} put {len(vs):2d}  refused {c['refused']:2d}  passed {c['passed']:2d}  pass-through {c['through']}"
          f"   refused by signature: tool {kinds[('refused','tool')]}, proc {kinds[('refused','proc')]}"
          f" | passed: tool {kinds[('passed','tool')]}, proc {kinds[('passed','proc')]}")
    tot.update(c)
print(f"  {'graph arm':14} put {sum(tot.values()):2d}  refused {tot['refused']:2d}  passed {tot['passed']:2d}  pass-through {tot['through']}")
F70["gate_record"] = {"put": sum(tot.values()), "refused": tot["refused"], "passed": tot["passed"], "pass_through": tot["through"]}
F70["refused_by_kind"] = dict(Counter(v["kind"] for v in verdicts if v["checked"] and not v["ok"] and 1 <= v["round"] <= LAST))
F70["pass_throughs"] = [(v["run"], v["round"], v["cid"]) for v in verdicts if not v["checked"] and 1 <= v["round"] <= LAST]


# ================================================================== B. replay forensics
def replay_session(run: str, k: int, cid: str):
    hits = list((RUNS / run).glob(f"R*/sessions/gatereplay/R{k}-{cid}"))
    hits = [h for h in hits if RD.match(h.parts[-4])]
    return hits[0] if hits else None


def replay_info(run: str, k: int, cid: str) -> dict:
    d = replay_session(run, k, cid)
    info: dict = {"session": str(d.relative_to(RUNS)) if d else None}
    if not d:
        return info
    for seg in d.glob("*.jsonl"):
        if seg.name.endswith("_trace.jsonl"):
            continue
        with open(seg, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") == "session_start":
                    info["task_text"] = rec.get("task") or ""
                    break
        break
    for st in d.glob("*_state.json"):
        s = json.loads(st.read_text(encoding="utf-8"))
        info["steps"] = s.get("step")
        info["max_steps"] = s.get("max_steps")
        info["end"] = s.get("segment_end_reason")
        info["cost"] = s.get("cumulative_cost_usd")
        break
    us = list(d.glob("graph/*_unfolded.jsonl"))
    if us:
        u = load_unfolded(us[0])
        info["u_tools"] = dict(Counter(n.static_node_id[5:] for n in u.nodes if n.hook == "tool"))
        info["u_nodes"] = len(u.nodes)
        info["u_records_intervention"] = any((n.intervention or "").strip() for n in u.nodes)
        info["_u"] = u
    info["task"] = task_from_text(run, info.get("task_text", ""))
    return info


def recompute(v: dict, info: dict, sig: dict | None) -> str:
    u = info.get("_u")
    if u is None or not sig:
        return "n/a"
    fl = floor_of(sig)
    if v["kind"] == "tool":
        n = info["u_tools"].get(v["target"], 0)
        return f"{'fired' if n >= fl else 'absent'} ({n}>={fl})"
    snake = v["target"].split(":", 1)[-1]
    # module-path form proc:<snake> and file-URI form proc:py::_<snake> (see attribution_graph.py)
    matched = [n for n in u.nodes if n.static_node_id == v["target"]
               or n.static_node_id.endswith(":" + snake) or n.static_node_id.endswith("_" + snake)]
    acted = [n for n in matched if (n.intervention or "").strip()]
    if info["u_records_intervention"]:
        n = len(acted)
        return f"{'fired' if n >= fl else 'absent'} ({n} intervening of {len(matched)} present, floor {fl})"
    n = len(matched)
    return f"{'fired' if n >= fl else 'absent'} ({n} present, presence only, floor {fl})"


print("=" * 100)
print("B. Replay forensics: recorded verdict vs recomputed from the U; the replayed task vs the recomputed draw")
draw_ok = Counter()
agree_n = Counter()
for v in verdicts:
    if not (1 <= v["round"] <= LAST):
        continue
    fm = manifest(v["run"], v["round"], v["cid"])
    sig = infer_signature(fm.get("bucket"), fm, fm.get("attribution_signature")) if fm else None
    preds = _predicted_from_manifest(fm) if fm else []
    info = replay_info(v["run"], v["round"], v["cid"])
    v["replay"] = {k2: val for k2, val in info.items() if k2 not in ("_u", "task_text")}
    v["preds"] = preds
    v["sig"] = sig
    v["bucket"] = fm.get("bucket") if fm else None
    if info.get("task"):
        for upto, label in ((v["round"] - 1, "k-1"), (v["round"], "k")):
            p = pick(preds, v["run"], upto)
            v[f"draw_{label}"] = p
            draw_ok[(label, p == info["task"])] += 1
    rec = recompute(v, info, sig)
    v["recomputed"] = rec
    agree = ("fired" in rec) == (v["ok"] and v["checked"]) if rec != "n/a" else None
    agree_n[agree] += 1
    print(f"  {v['run']:10} R{v['round']:<2} {v['cid']:9} {v['head'][:8]:8} {v['kind']:4} {v['target']:38} "
          f"rec={v['count']}/{v['floor']}  recomputed={rec:52} agree={agree}  task={str(info.get('task'))[:8]}"
          f"  draw(k-1)={'same' if v.get('draw_k-1') == info.get('task') else str(v.get('draw_k-1'))[:8]}"
          f"  steps={info.get('steps')}/{info.get('max_steps')} end={info.get('end')}")
print(f"  verdict recomputation agrees {agree_n[True]}, disagrees {agree_n[False]}, n/a {agree_n[None]}")
print(f"  draw recomputation: history<=k-1 matches {draw_ok[('k-1', True)]} / mismatches {draw_ok[('k-1', False)]};"
      f" history<=k matches {draw_ok[('k', True)]} / mismatches {draw_ok[('k', False)]}")
F70["verdicts_recomputed_agree"] = [agree_n[True], agree_n[False]]
F70["draw_recomputed_k_minus_1"] = [draw_ok[("k-1", True)], draw_ok[("k-1", False)]]

# ================================================================== D. shipped tool_call candidates
print("=" * 100)
print("D. Shipped tool_call candidates: the landing round's own trajectories as the second recorded draw")
print("   (k = ship round = landing round; 'prev' = R{k-1}, the pre-edit configuration)")
SHIPS: dict[str, list] = {}
MULTI: dict[str, set] = {}
for run, arm in CAMPAIGNS:
    sb = json.loads((RUNS / run / "scoreboard.json").read_text(encoding="utf-8"))
    ships = [s for s in (sb.get("ships") or []) if 1 <= int(s["round"]) <= LAST]
    SHIPS[run] = ships
    c = Counter(int(s["round"]) for s in ships)
    MULTI[run] = {r for r, n in c.items() if n > 1}

rows: list[dict] = []
for run, arm in CAMPAIGNS:
    for s in SHIPS[run]:
        k, cid = int(s["round"]), s["cid"]
        fm = manifest(run, k, cid)
        if fm is None:
            continue
        sig = infer_signature(fm.get("bucket"), fm, fm.get("attribution_signature"))
        if not sig or str(sig.get("type")) != "tool_call" or not sig.get("tool_name"):
            continue
        tool, fl = str(sig["tool_name"]), floor_of(sig)
        explicit = isinstance(fm.get("attribution_signature"), dict)
        # The vendored inference PascalCases the file stem (write_tool.py -> "WriteTool"); the
        # asset registers @tool(name="Write") (R13/applied/C-R13-03/write_tool.py).
        if (run, k, cid) == ("baseline-seed2", 13, "C-R13-03"):
            tool = "Write"
        preds = _predicted_from_manifest(fm) or [str(t) for t in (s.get("predicted_tasks") or [])]
        cur = TRAJ[run].get(k, {})
        prev = TRAJ[run].get(k - 1, {})
        n_tasks = len(cur)
        with_tool = [t for t, c in cur.items() if c.get(tool, 0) >= fl]
        prev_with = [t for t, c in prev.items() if c.get(tool, 0) >= fl]
        pred_run = [t for t in preds if t in cur]
        pred_absent = [t for t in pred_run if cur[t].get(tool, 0) < fl]
        order = ordered_preds(preds, run, k - 1)
        d = order[0] if order else None
        d_run = d in cur if d else False
        d_absent = (cur[d].get(tool, 0) < fl) if d_run else None
        nxt = next((j for j in sorted(TRAJ[run]) if j > k and len(TRAJ[run][j]) >= 100), None)
        nxt_prev = None
        if nxt is not None:
            nc = TRAJ[run][nxt]
            nxt_prev = (sum(1 for c in nc.values() if c.get(tool, 0) >= fl), len(nc))
        gate = next((v["head"][:7] for v in verdicts if v["run"] == run and v["round"] == k and v["cid"] == cid), "-")
        row = {
            "run": run, "arm": arm, "round": k, "cid": cid, "kind": "tool", "name": tool, "tool": tool, "floor": fl,
            "explicit_sig": explicit, "bucket": fm.get("bucket"), "gate": gate,
            "n_tasks": n_tasks, "n_with_tool": len(with_tool), "n_fired": len(with_tool), "ran_round_level": bool(with_tool),
            "prev_n_tasks": len(prev), "prev_with_tool": len(prev_with), "new_tool": not prev_with, "new": not prev_with,
            "n_pred": len(preds), "n_pred_run": len(pred_run), "n_pred_absent": len(pred_absent),
            "draw": d, "draw_run": d_run, "draw_absent": d_absent,
            "next_full_round": nxt, "next_full_prev": nxt_prev,
            "multi_ship_round": k in MULTI[run],
            "pred_order_absent": [(t, cur[t].get(tool, 0) < fl) for t in order if t in cur],
        }
        rows.append(row)
        print(f"  {run:14} R{k:<2} {cid:9} {gate:7} {tool:16} floor {fl} {'explicit' if explicit else 'inferred'} "
              f"| R{k}: {len(with_tool):3d}/{n_tasks:3d} tasks used it (prev R{k-1}: {len(prev_with)}/{len(prev)}; "
              f"{'NEW' if not prev_with else 'existing'}) | predicted run {len(pred_run)}/{len(preds)}, absent {len(pred_absent)} "
              f"| draw {str(d)[:8]} {'absent' if d_absent else ('present' if d_absent is False else 'not run')}"
              f"{'' if nxt is None else f' | next full R{nxt}: {nxt_prev[0]}/{nxt_prev[1]}'}")


def agg(sel: list[dict], label: str) -> dict:
    ran = [r for r in sel if r["ran_round_level"]]
    never = [r for r in sel if not r["ran_round_level"]]
    bg_abs = sum(r["n_tasks"] - r["n_fired"] for r in ran)
    bg_n = sum(r["n_tasks"] for r in ran)
    pr_abs = sum(r["n_pred_absent"] for r in ran)
    pr_n = sum(r["n_pred_run"] for r in ran)
    dr = [r for r in ran if r["draw_run"]]
    dr_abs = sum(1 for r in dr if r["draw_absent"])
    print(f"  {label:40} ships {len(sel):2d}, ran {len(ran):2d}, never ran {len(never)} "
          f"| background absence {bg_abs}/{bg_n} = {100 * bg_abs / max(1, bg_n):.0f}% "
          f"| predicted-set {pct(pr_abs, pr_n)} | drawn-task {pct(dr_abs, len(dr))}")
    if never:
        print(f"      never ran at round level: {[(r['run'], r['round'], r['cid'], r['name']) for r in never]}")
    return {"ships": len(sel), "ran": len(ran), "never_ran": [(r["run"], r["round"], r["cid"], r["name"]) for r in never],
            "background": [bg_abs, bg_n], "predicted_set": [pr_abs, pr_n], "drawn": [dr_abs, len(dr)],
            "drawn_wilson": [round(x, 1) for x in wilson(dr_abs, len(dr))]}


print("  --- aggregates (candidates whose tool ran at round level; a tool that never ran is a true refusal, not a false one)")
F70["tools"] = {
    "all": agg(rows, "tools, six campaigns"),
    "no_graph": agg([r for r in rows if r["arm"] == "no-graph"], "tools, no-graph arm (no gate)"),
    "graph": agg([r for r in rows if r["arm"] == "graph"], "tools, graph arm (gate-passed survivors)"),
    "existing": agg([r for r in rows if not r["new_tool"]], "tools, existing (edited, not added)"),
    "new": agg([r for r in rows if r["new_tool"]], "tools, new (added by the candidate)"),
}

# ================================================================== E. the 18 refusals
print("=" * 100)
print("E. The refusals, one by one")
_proc_cache: dict[tuple[str, int], dict[str, dict]] = {}


def round_u_procs(run: str, k: int) -> dict[str, dict]:
    """task -> {static_id: [present, intervening]} for every solver session U of round k."""
    key = (run, k)
    if key in _proc_cache:
        return _proc_cache[key]
    summ = round_u_summary(run, k)
    out = {t: {"procs": rec["procs"], "records_intervention": rec["records_intervention"]}
           for t, rec in summ.items() if not t.endswith("#dup")}
    _proc_cache[key] = out
    return out


_u_cache: dict[tuple[str, int], dict] = {}


def round_u_summary(run: str, k: int) -> dict:
    """task -> {procs: {static_id: [present, intervening]}, tools: {name: calls}, nodes, records_intervention}
    for every solver session of round k that has an unfolded graph."""
    key = (run, k)
    if key in _u_cache:
        return _u_cache[key]
    cache = (CACHE / f"{run}_R{k}.json") if CACHE else None
    if cache and cache.exists():
        _u_cache[key] = json.load(open(cache, encoding="utf-8"))
        return _u_cache[key]
    out: dict = {}
    sess = RUNS / run / f"R{k}" / "sessions" / "aegis"
    if sess.exists():
        for sd in sess.iterdir():
            us = list(sd.glob("graph/*_unfolded.jsonl"))
            if not us:
                continue
            stem = re.sub(r"^R\d+-", "", sd.name)
            tid = stem if UUID.match(stem) else None
            if tid is None:
                for seg in sd.glob("*.jsonl"):
                    if seg.name.endswith("_trace.jsonl"):
                        continue
                    with open(seg, encoding="utf-8", errors="replace") as f:
                        for line in f:
                            try:
                                rec = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if rec.get("type") == "session_start":
                                tid = task_from_text(run, rec.get("task") or "")
                                break
                    break
            if tid is None:
                tid = sd.name
            u = load_unfolded(us[0])
            procs: dict[str, list] = {}
            tools: Counter = Counter()
            for n in u.nodes:
                sid = n.static_node_id
                if n.hook == "tool" and sid.startswith("tool:"):
                    tools[sid[5:]] += 1
                elif sid.startswith("proc:"):
                    p = procs.setdefault(sid, [0, 0])
                    p[0] += 1
                    if (n.intervention or "").strip():
                        p[1] += 1
            rec = {"procs": procs, "tools": dict(tools), "nodes": len(u.nodes),
                   "records_intervention": any((n.intervention or "").strip() for n in u.nodes)}
            if tid in out:
                out[tid + "#dup"] = rec
            else:
                out[tid] = rec
    if cache:
        json.dump(out, open(cache, "w", encoding="utf-8"))
    _u_cache[key] = out
    return out


for v in verdicts:
    if v["ok"] or not (1 <= v["round"] <= LAST):
        continue
    run, k, cid, target, fl = v["run"], v["round"], v["cid"], v["target"], v["floor"] or 1
    info = v["replay"]
    d = info.get("task")
    prev = TRAJ[run].get(k - 1, {})
    print(f"  {run} R{k} {cid} [{v['bucket']}] target {target} floor {fl} | replayed task {str(d)[:8]} "
          f"steps {info.get('steps')}/{info.get('max_steps')} end={info.get('end')} cost=${info.get('cost') or 0:.2f} "
          f"| replay's own tools: {info.get('u_tools')}")
    if v["kind"] == "tool":
        tool = target
        prev_with = [t for t, c in prev.items() if c.get(tool, 0) >= fl]
        ever_before = sorted({j for j in TRAJ[run] if j <= k - 1 for t, c in TRAJ[run][j].items() if c.get(tool, 0) >= fl})
        d_prev = (prev.get(d, {}).get(tool, 0) if d else None)
        d_ever = sorted(j for j in TRAJ[run] if j <= k - 1 and d in TRAJ[run][j] and TRAJ[run][j][d].get(tool, 0) >= fl) if d else []
        later = sorted(j for j in TRAJ[run] if j > k and any(c.get(tool, 0) >= fl for c in TRAJ[run][j].values()))
        line = (f"      tool {'EXISTING' if prev_with else 'NEW'}: R{k-1} prevalence {len(prev_with)}/{len(prev)}; "
                f"rounds<=R{k-1} where any task used it: {ever_before}; drawn task used it in R{k-1}: {d_prev}; in rounds {d_ever}")
        if later:
            j = later[0]
            jc = TRAJ[run][j]
            jw = sum(1 for c in jc.values() if c.get(tool, 0) >= fl)
            on_d = jc.get(d, {}).get(tool, 0) if d in jc else "not run"
            line += f" | tool appears later from R{j}: {jw}/{len(jc)} tasks, on the drawn task: {on_d}; rounds with it: {later}"
        else:
            line += " | tool never appears later in this campaign"
        print(line)
        v["forensics"] = {"existing": bool(prev_with), "prev_prevalence": [len(prev_with), len(prev)], "later_rounds": later}
    else:
        procs = round_u_procs(run, k - 1)
        snake = target.split(":", 1)[-1]

        def _alias(sid: str) -> bool:
            return sid == target or sid.endswith(":" + snake) or sid.endswith("_" + snake)

        aliases = {sid for rec in procs.values() for sid in rec["procs"] if _alias(sid)} | {target}
        present = [t for t, rec in procs.items() if any(a in rec["procs"] for a in aliases)]
        acted = [t for t, rec in procs.items() if any(rec["procs"].get(a, [0, 0])[1] >= fl for a in aliases)]
        recs_int = sum(1 for rec in procs.values() if rec["records_intervention"])
        on_d = None
        if d in procs:
            on_d = {a: procs[d]["procs"].get(a) for a in aliases if a in procs[d]["procs"]}
        print(f"      processor in R{k-1} U graphs ({len(procs)} sessions, {recs_int} record interventions): "
              f"present on {len(present)} tasks, INTERVENING (>= floor) on {len(acted)} tasks "
              f"({'EXISTING' if present else 'NEW - not in the pre-edit configuration'}); on the drawn task: {on_d}")
        v["forensics"] = {"existing": bool(present), "present": len(present), "intervening": len(acted), "sessions": len(procs)}


# ================================================================== official tracer summaries per round
def slug_of(name: str) -> str:
    """Class name -> the graph's slug, through the same authority the U uses."""
    return processor_static_id(name)[5:]


_trace_cache: dict[tuple[str, int], dict] = {}


def round_trace_summary(run: str, k: int) -> dict:
    """task -> {procs: {processor class name: [triggers, interventions]}, actions} from the official
    HarnessJournal trace (processor_trigger events) for every solver session of round k. Works on
    both arms; replay-smoke sessions (synthetic task text) do not map to a task and are skipped."""
    key = (run, k)
    if key in _trace_cache:
        return _trace_cache[key]
    cache = (CACHE / f"{run}_R{k}_trace.json") if CACHE else None
    if cache and cache.exists():
        _trace_cache[key] = json.load(open(cache, encoding="utf-8"))
        return _trace_cache[key]
    out: dict = {}
    sess = RUNS / run / f"R{k}" / "sessions"
    dirs = ([d for d in sess.glob("*/") if d.name not in ("aegis", "gatereplay")] + list((sess / "aegis").glob("*/"))) if sess.exists() else []
    for sd in dirs:
        traces = list(sd.glob("*_trace.jsonl"))
        if not traces:
            continue
        stem = re.sub(r"^R\d+-", "", sd.name)
        tid = stem if UUID.match(stem) and (RUNS / run / "R0" / "trajectories" / f"{stem}.md").exists() else None
        if tid is None:
            for seg in sd.glob("*.jsonl"):
                if seg.name.endswith("_trace.jsonl"):
                    continue
                with open(seg, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if rec.get("type") == "session_start":
                            tid = task_from_text(run, rec.get("task") or "")
                            break
                break
        if tid is None:
            continue
        procs: dict[str, list] = {}
        actions: Counter = Counter()
        with open(traces[0], encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("event_type") != "processor_trigger":
                    continue
                nm = str(rec.get("processor") or "")
                act = str(rec.get("action") or "")
                actions[act] += 1
                p = procs.setdefault(nm, [0, 0])
                p[0] += 1
                if act == "intervention":
                    p[1] += 1
        rec = {"procs": procs, "actions": dict(actions)}
        if tid in out:
            out[tid + "#dup"] = rec
        else:
            out[tid] = rec
    if cache:
        json.dump(out, open(cache, "w", encoding="utf-8"))
    _trace_cache[key] = out
    return out


def match_trace_names(summ: dict, name: str) -> set[str]:
    target = slug_of(name)
    seen = {nm for rec in summ.values() for nm in rec["procs"]}
    exact = {nm for nm in seen if nm == name or slug_of(nm) == target}
    if exact:
        return exact
    return {nm for nm in seen if target in slug_of(nm) or slug_of(nm) in target}


def proc_fired(rec: dict, ids: set, snake: str, fl: int):
    """The gate's processor semantics on one task's U summary."""
    matched = {sid: v for sid, v in rec["procs"].items()
               if sid in ids or sid.endswith(":" + snake) or sid.endswith("_" + snake)}
    present = sum(v[0] for v in matched.values())
    acted = sum(v[1] for v in matched.values())
    count = acted if rec["records_intervention"] else present
    return count >= fl, present, acted


# ================================================================== B2. shipped processor candidates
print("=" * 100)
print("B2. Shipped processor_invocation candidates: graph arm by the landing-round U graphs (the gate's own")
print("    semantics: intervening invocations >= floor); no-graph arm by the tracer's intervention events")
proc_rows: list[dict] = []
text_proxy = [0, 0]
for run, arm in CAMPAIGNS:
    for s in SHIPS[run]:
        k, cid = int(s["round"]), s["cid"]
        fm = manifest(run, k, cid)
        if fm is None:
            continue
        sig = infer_signature(fm.get("bucket"), fm, fm.get("attribution_signature"))
        if not sig or str(sig.get("type")) != "processor_invocation":
            continue
        name = str(sig.get("class_name") or sig.get("tool_name") or "")
        if not name:
            continue
        fl = floor_of(sig)
        ids = {processor_static_id(name), processor_file_uri_static_id(name)} | {str(a) for a in (sig.get("node_aliases") or [])}
        snake = processor_static_id(name)[5:]
        new_asset = any(str(fc.get("path", "")).endswith(".py") and fc.get("action") == "create"
                        for fc in (fm.get("file_changes") or []) if isinstance(fc, dict))
        preds = _predicted_from_manifest(fm) or [str(t) for t in (s.get("predicted_tasks") or [])]
        gate = next((v["head"][:7] for v in verdicts if v["run"] == run and v["round"] == k and v["cid"] == cid), "-")
        if arm == "graph":
            summ = round_u_summary(run, k)
            tasks = {t: rec for t, rec in summ.items() if not t.endswith("#dup")}
            fired = {t: proc_fired(rec, ids, snake, fl) for t, rec in tasks.items()}
            n_tasks = len(tasks)
            n_fired = sum(1 for f in fired.values() if f[0])
            n_present = sum(1 for f in fired.values() if f[1] > 0)
            basis = "U:intervention"
        else:
            summ = round_trace_summary(run, k)
            tasks = {t: rec for t, rec in summ.items() if not t.endswith("#dup")}
            keys = match_trace_names(tasks, name)
            fired = {}
            for t, rec in tasks.items():
                trig = sum(rec["procs"].get(x, [0, 0])[0] for x in keys)
                act = sum(rec["procs"].get(x, [0, 0])[1] for x in keys)
                fired[t] = (act >= fl, trig, act)
            n_tasks = len(fired)
            n_fired = sum(1 for f in fired.values() if f[0])
            n_present = sum(1 for f in fired.values() if f[1] > 0)
            basis = "trace:intervention" if keys else "trace:NAME-NOT-SEEN"
            # the vendored text proxy (class name appearing in the trajectory), for the record
            tr = RUNS / run / f"R{k}" / "trajectories"
            mds = list(tr.glob("*.md"))
            text_hits = sum(1 for md in mds if name in md.read_text(encoding="utf-8", errors="replace"))
            text_proxy[0] += text_hits
            text_proxy[1] += len(mds)
            print(f"      [{run} R{k} {cid}] trace names matched: {sorted(keys) or 'NONE'}; vendored text proxy hits {text_hits}/{len(mds)}")
        pred_run = [t for t in preds if t in fired]
        pred_absent = [t for t in pred_run if not fired[t][0]]
        order = ordered_preds(preds, run, k - 1)
        d = order[0] if order else None
        d_run = d in fired if d else False
        d_absent = (not fired[d][0]) if d_run else None
        row = {"run": run, "arm": arm, "round": k, "cid": cid, "kind": "proc", "name": name, "floor": fl, "gate": gate,
               "basis": basis, "new": new_asset, "n_tasks": n_tasks, "n_fired": n_fired, "n_present": n_present,
               "ran_round_level": n_fired > 0, "n_pred": len(preds), "n_pred_run": len(pred_run),
               "n_pred_absent": len(pred_absent), "draw": d, "draw_run": d_run, "draw_absent": d_absent,
               "multi_ship_round": k in MULTI[run],
               "pred_order_absent": [(t, not fired[t][0]) for t in order if t in fired]}
        proc_rows.append(row)
        print(f"  {run:14} R{k:<2} {cid:9} {gate:7} {name:34} floor {fl} {'NEW' if new_asset else 'existing':8} {basis:18} "
              f"| R{k}: fired {n_fired:3d}/{n_tasks:3d} (present {n_present}) "
              f"| predicted run {len(pred_run)}/{len(preds)}, absent {len(pred_absent)} "
              f"| draw {str(d)[:8]} {'absent' if d_absent else ('present' if d_absent is False else 'not run')}"
              f"{' | multi-ship round' if k in MULTI[run] else ''}")

print("  --- aggregates")
F70["processors"] = {
    "graph": agg([r for r in proc_rows if r["arm"] == "graph"], "processors, graph arm (U intervention)"),
    "graph_new": agg([r for r in proc_rows if r["arm"] == "graph" and r["new"]], "processors, graph arm, new asset"),
    "graph_existing": agg([r for r in proc_rows if r["arm"] == "graph" and not r["new"]], "processors, graph arm, existing (rules/params)"),
    "no_graph": agg([r for r in proc_rows if r["arm"] == "no-graph"], "processors, no-graph arm (trace intervention)"),
    "graph_always_on": sum(1 for r in proc_rows if r["arm"] == "graph" and r["n_tasks"] and r["n_fired"] == r["n_tasks"]),
    "vendored_text_proxy_hits": text_proxy,
}
print(f"  graph-arm processors intervening on every task of the landing round: {F70['processors']['graph_always_on']} of "
      f"{sum(1 for r in proc_rows if r['arm'] == 'graph')}; vendored text proxy hits {text_proxy[0]}/{text_proxy[1]}")
F70["multi_ship_rounds"] = {"tools": [sum(1 for r in rows if r["multi_ship_round"]), len(rows)],
                            "processors": [sum(1 for r in proc_rows if r["multi_ship_round"]), len(proc_rows)]}
print("  tool rows in multi-ship rounds:", F70["multi_ship_rounds"]["tools"], "| processor rows in multi-ship rounds:", F70["multi_ship_rounds"]["processors"])

# ================================================================== B3. same-task agreement
print("=" * 100)
print("B3. Same task, two recorded draws: the gate's replay verdict against the same task in the landing round")
F70["same_task_agreement"] = {}
for label, rr in (("tools", rows), ("processors", proc_rows)):
    passed = [r for r in rr if r["arm"] == "graph" and r["gate"].startswith("PASSED") and r["draw_run"]]
    agree = sum(1 for r in passed if r["draw_absent"] is False)
    F70["same_task_agreement"][label] = [agree, len(passed)]
    print(f"  gate PASSED, {label:10}: landing round shows the mechanism on the same task {pct(agree, len(passed))}"
          f"  (disagreements: {[(r['run'], r['round'], r['cid']) for r in passed if r['draw_absent']]})")
print("  gate REFUSED tools whose tool later landed in the same campaign: the drawn task in every later round that has the tool")
F70["refused_tools_later"] = []
for v in verdicts:
    if v["ok"] or v["kind"] != "tool" or not (1 <= v["round"] <= LAST):
        continue
    run, k, tool, d = v["run"], v["round"], v["target"], (v.get("replay") or {}).get("task")
    later = [(j, TRAJ[run][j][d].get(tool, 0) if d in TRAJ[run][j] else "not run")
             for j in sorted(TRAJ[run]) if j > k and any(c.get(tool, 0) >= 1 for c in TRAJ[run][j].values())]
    if later:
        absent = sum(1 for j, c in later if c == 0)
        run_later = sum(1 for j, c in later if c != "not run")
        F70["refused_tools_later"].append({"run": run, "round": k, "cid": v["cid"], "tool": tool,
                                           "drawn_task_run_in": run_later, "absent_in": absent})
        print(f"    {run} R{k} {v['cid']} {tool:16} drawn {str(d)[:8]}: later rounds with the tool {[(j, c) for j, c in later]}"
              f" | task run in {run_later} of them, absent in {absent}, present in {run_later - absent}")

# ================================================================== C2. null-hypothesis draw probabilities
print("=" * 100)
print("C2. Existing tools: how likely the drawn task's verdict was under 'nothing changed' (the task's own history)")
for v in verdicts:
    if not v["checked"] or v["kind"] != "tool" or not (1 <= v["round"] <= LAST):
        continue
    run, k, tool, d = v["run"], v["round"], v["target"], (v.get("replay") or {}).get("task")
    fl = v["floor"] or 1
    prev_any = any(c.get(tool, 0) >= fl for j in TRAJ[run] if j <= k - 1 for c in TRAJ[run][j].values())
    if not prev_any:
        continue
    rounds_run = [j for j in sorted(TRAJ[run]) if j <= k - 1 and d in TRAJ[run][j]]
    used = [j for j in rounds_run if TRAJ[run][j][d].get(tool, 0) >= fl]
    p_present = len(used) / max(1, len(rounds_run))
    prev = TRAJ[run].get(k - 1, {})
    prev_rate = sum(1 for c in prev.values() if c.get(tool, 0) >= fl) / max(1, len(prev))
    verdict = "REFUSED" if not v["ok"] else "PASSED"
    p_verdict_null = (1 - p_present) if not v["ok"] else p_present
    print(f"  {run} R{k} {v['cid']:9} {verdict:7} {tool:10} drawn {str(d)[:8]}: task used the tool in {len(used)}/{len(rounds_run)} earlier rounds "
          f"(bed-level rate in R{k-1} {100*prev_rate:.0f}%) -> P(this verdict | nothing changed) = {100*p_verdict_null:.0f}%")

# ================================================================== C3. replay informativeness
print("=" * 100)
print("C3. Replay informativeness (checked verdicts with a replay U)")
F70["replay"] = {}
for label, sel in (("REFUSED", [v for v in verdicts if v["checked"] and not v["ok"]]),
                   ("PASSED", [v for v in verdicts if v["checked"] and v["ok"]])):
    sel = [v for v in sel if 1 <= v["round"] <= LAST and (v.get("replay") or {}).get("steps") is not None]
    steps = [v["replay"]["steps"] for v in sel]
    calls = [sum((v["replay"].get("u_tools") or {}).values()) for v in sel]
    at_cap = sum(1 for v in sel if v["replay"]["steps"] == v["replay"]["max_steps"])
    short = sum(1 for s in steps if s <= 2)
    zero = sum(1 for c in calls if c == 0)
    cost = [v["replay"].get("cost") or 0 for v in sel]
    F70["replay"][label] = {"n": len(sel), "steps_median": statistics.median(steps), "at_cap": at_cap,
                            "le2_steps": short, "zero_tool_calls": zero, "cost_total": round(sum(cost), 2)}
    print(f"  {label:8} n={len(sel):2d} steps median {statistics.median(steps):.0f} (min {min(steps)}, max {max(steps)}), "
          f"at the 20-step cap {at_cap}, <=2 steps {short}, zero tool calls {zero}, tool calls median {statistics.median(calls):.0f}, "
          f"cost median ${statistics.median(cost):.2f} total ${sum(cost):.2f}")
F70["replay"]["cost_total_all"] = round(F70["replay"]["REFUSED"]["cost_total"] + F70["replay"]["PASSED"]["cost_total"], 2)
print(f"  replay bill, all checked verdicts: ${F70['replay']['cost_total_all']:.2f}")

# ================================================================== D1. k-draw design number
print("=" * 100)
print("D1. If the gate drew k predicted tasks and refused only when all k miss (mechanisms that ran at round level)")


def hyper_all_absent(a: int, n: int, k: int) -> float:
    if k > n:
        k = n
    if k == 0:
        return 0.0
    return math.comb(a, k) / math.comb(n, k) if a >= k else 0.0


F70["k_draw"] = {}
for label, rr in (("tools, all", [r for r in rows if r["ran_round_level"]]),
                  ("tools, new", [r for r in rows if r["ran_round_level"] and r["new"]]),
                  ("tools, existing", [r for r in rows if r["ran_round_level"] and not r["new"]]),
                  ("processors (graph arm)", [r for r in proc_rows if r["arm"] == "graph" and r["ran_round_level"]]),
                  ("tools + graph-arm processors", [r for r in rows if r["ran_round_level"]] + [r for r in proc_rows if r["arm"] == "graph" and r["ran_round_level"]])):
    rr = [r for r in rr if r["pred_order_absent"]]
    line = f"  {label:30} n={len(rr):2d}"
    F70["k_draw"][label] = {"n": len(rr)}
    for k in (1, 2, 3, 5):
        det = sum(1 for r in rr if all(a for _, a in r["pred_order_absent"][:k]))
        rnd = statistics.mean(hyper_all_absent(sum(1 for _, a in r["pred_order_absent"] if a), len(r["pred_order_absent"]), k) for r in rr)
        F70["k_draw"][label][f"k{k}"] = [det, len(rr)]
        line += f" | k={k}: streak-ordered {det}/{len(rr)} = {100*det/max(1,len(rr)):.0f}%, random-draw expectation {100*rnd:.0f}%"
    print(line)
sizes = [len(r["pred_order_absent"]) for r in rows + [r for r in proc_rows if r["arm"] == "graph"]]
F70["predicted_tasks_available"] = {"n": len(sizes), "median": statistics.median(sizes), "lt2": sum(1 for s in sizes if s < 2), "lt3": sum(1 for s in sizes if s < 3)}
print(f"  predicted tasks available in the landing round per candidate: median {statistics.median(sizes):.0f}, min {min(sizes)}, max {max(sizes)}, "
      f"<2 tasks: {sum(1 for s in sizes if s < 2)}, <3: {sum(1 for s in sizes if s < 3)} of {len(sizes)}")

# ================================================================== D2. bookkeeping identities
print("=" * 100)
print("D2. tool_call_counts (trajectory frontmatter) against tool:<name> nodes in the same task's U (graph arm, full rounds)")
d2 = [0, 0]
for run, k in (("ghx-seed1", 2), ("ghx-seed2", 6), ("ghx-seed3", 7), ("ghx-seed1", 15)):
    summ = round_u_summary(run, k)
    md = TRAJ[run].get(k, {})
    both = [t for t in md if t in summ]
    equal = sum(1 for t in both if md[t] == summ[t]["tools"])
    diffs: Counter = Counter()
    presence_equal = 0
    for t in both:
        a, b = md[t], summ[t]["tools"]
        if {x for x, n in a.items() if n > 0} == {x for x, n in b.items() if n > 0}:
            presence_equal += 1
        for name in set(a) | set(b):
            if a.get(name, 0) != b.get(name, 0):
                diffs[(name, "md>U" if a.get(name, 0) > b.get(name, 0) else "U>md")] += 1
    d2[0] += equal
    d2[1] += len(both)
    print(f"  {run} R{k}: tasks with both records {len(both)}/{len(md)} md, {len(summ)} U | exact count equality {equal}/{len(both)} "
          f"| presence-set equality (what the gate reads at floor 1) {presence_equal}/{len(both)} | mismatches by tool: {dict(diffs) or 'none'}")
F70["identity_tools"] = d2

print("=" * 100)
print("D2b. processors: U intervening count against the official trace's processor_trigger/intervention events, per task")


def sid_slug(sid: str) -> str:
    s = sid[5:] if sid.startswith("proc:") else sid
    return s[5:] if s.startswith("py::_") else s


d2b = [0, 0]
for run, k in (("ghx-seed1", 2), ("ghx-seed2", 7), ("ghx-seed3", 10)):
    su = round_u_summary(run, k)
    st = round_trace_summary(run, k)
    both = [t for t in su if t in st and not t.endswith("#dup")]
    eq = 0
    mism: Counter = Counter()
    for t in both:
        u_int: Counter = Counter()
        for sid, (pres, act) in su[t]["procs"].items():
            u_int[sid_slug(sid)] += act
        tr_int: Counter = Counter()
        for nm, (trig, act) in st[t]["procs"].items():
            tr_int[slug_of(nm)] += act
        u_int = Counter({a: b for a, b in u_int.items() if b})
        tr_int = Counter({a: b for a, b in tr_int.items() if b})
        if u_int == tr_int:
            eq += 1
        else:
            for nm in set(u_int) | set(tr_int):
                if u_int[nm] != tr_int[nm]:
                    mism[nm] += 1
    actions: Counter = Counter()
    for rec in st.values():
        actions.update(rec.get("actions", {}))
    d2b[0] += eq
    d2b[1] += len(both)
    print(f"  {run} R{k}: tasks with both records {len(both)} (U {len(su)}, trace {len(st)}) | per-task intervention multisets equal {eq}/{len(both)} "
          f"| tasks disagreeing by processor: {dict(mism) or 'none'} | trace action values: {dict(actions)}")
F70["identity_processors"] = d2b

# ================================================================== F70 block
print("=" * 100)
print("F70. The ledger row's numbers")
T = F70["tools"]
P = F70["processors"]
print(f"  gate record: put {F70['gate_record']['put']}, refused {F70['gate_record']['refused']}, passed {F70['gate_record']['passed']}, "
      f"pass-through {F70['gate_record']['pass_through']} {F70['pass_throughs']}; refused by signature {F70['refused_by_kind']}")
print(f"  tools: shipped {T['all']['ships']}, drawn-task absence {pct(*T['all']['drawn'])}; new {T['new']['drawn'][0]}/{T['new']['drawn'][1]}, "
      f"existing {T['existing']['drawn'][0]}/{T['existing']['drawn'][1]}; no-graph {T['no_graph']['drawn'][0]}/{T['no_graph']['drawn'][1]}, "
      f"graph {T['graph']['drawn'][0]}/{T['graph']['drawn'][1]}; predicted-set {T['all']['predicted_set'][0]}/{T['all']['predicted_set'][1]}; "
      f"random task {T['all']['background'][0]}/{T['all']['background'][1]}; never ran: no-graph {len(T['no_graph']['never_ran'])}/{T['no_graph']['ships']}")
kd = F70["k_draw"]["tools, all"]
print(f"  k-draw, tools: " + ", ".join(f"k={k} {kd[f'k{k}'][0]}/{kd[f'k{k}'][1]}" for k in (1, 2, 3, 5))
      + f"; candidates with <3 predicted tasks {F70['predicted_tasks_available']['lt3']}/{F70['predicted_tasks_available']['n']}")
print(f"  processors: graph drawn-task absence {P['graph']['drawn'][0]}/{P['graph']['drawn'][1]}, always-on {P['graph_always_on']}/{P['graph']['ships']}; "
      f"no-graph never intervened {len(P['no_graph']['never_ran'])}/{P['no_graph']['ships']} {P['no_graph']['never_ran']}, "
      f"remaining drawn-task absence {P['no_graph']['drawn'][0]}/{P['no_graph']['drawn'][1]}; vendored text proxy {text_proxy[0]}/{text_proxy[1]}")
print(f"  same-task agreement: tools {F70['same_task_agreement']['tools']}, processors {F70['same_task_agreement']['processors']}")
print(f"  identities: tool counts {d2[0]}/{d2[1]}, processor interventions {d2b[0]}/{d2b[1]}; replay bill ${F70['replay']['cost_total_all']:.2f}; "
      f"multi-ship rounds tools {F70['multi_ship_rounds']['tools']}, processors {F70['multi_ship_rounds']['processors']}")

if ARGS.out:
    json.dump({"F70": F70,
               "verdicts": [{k2: val for k2, val in v.items() if k2 not in ("_u", "sig")} for v in verdicts],
               "tool_rows": rows, "proc_rows": proc_rows},
              open(ARGS.out, "w", encoding="utf-8"), indent=1, default=str)
    print("wrote", ARGS.out)
