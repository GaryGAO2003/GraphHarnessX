"""Candidate-bucket census, aim selectivity, and graph-evidence node composition.

Recomputes, over the six whitelist campaigns (three no-graph seeds, three graph
seeds), four things that together separate *what the loop proposes* from *what
the loop aims at*:

  T1  Candidate-bucket census (tools / processor / prompt / config) per campaign,
      with each candidate's decision (shipped / rejected).
  T2  Aim selectivity: for every candidate, compare the class composition of its
      ``tasks_will_unlock`` targets against the class composition of the failing
      set it was written from (previous round). Enrichment = aim / failset. An
      enrichment of 1.0 means target selection is indistinguishable from uniform
      sampling of the current failing set.
  T3  Task classes over the whole whitelist on the 100-task no-pixel subset:
      never solved / volatile / always passing.
  T4  Node-type composition of the graph arms' cross-task lift tables
      (``graph_evidence/facts.md``) -- the coordinate system the graph arms'
      diagnosis is written in.

Only bare R<digits> round directories are read (quarantined *_poisoned_gateway
directories are skipped).
Scope: whitelist only (ruling II) -- M22-L0, M26b, and the M28/M29 replication
pairs. Shakedown campaigns (M24/M25) and pre-M22 runs are not read.
All readouts are restricted to the 100-task no-pixel subset so the 103-task and
100-task beds are comparable.

Usage:  python experiments/analysis/audit_candidate_bucket_and_aim.py
"""

from __future__ import annotations

import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = ROOT / "runs"

NO_GRAPH = ["baseline-seed1", "baseline-seed2", "baseline-seed3"]
GRAPH = ["ghx-seed1", "ghx-seed2", "ghx-seed3"]
ALL = NO_GRAPH + GRAPH
BUCKETS = ["tools", "processor", "prompt", "config"]
CAP = {"baseline-seed1": 15}  # the formal sixteen-round window, R0..R15 (ruling ii)

TID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
ROUND_OF = re.compile(r"R(\d+)")

SUBSET = {
    t["task_id"] for t in json.loads((ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))
}
assert len(SUBSET) == 100, len(SUBSET)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def round_dirs(root: Path, pat: str) -> list[Path]:
    """glob restricted to bare R<digits> round directories -- quarantined
    ``*_poisoned_gateway`` directories are never read."""
    return sorted(p for p in root.glob(pat) if re.fullmatch(r"R\d+", p.relative_to(root).parts[0]))


def card_buckets(text: str) -> list[str]:
    """Frontmatter ``bucket:`` -- scalar, inline list, or block list."""
    m = re.search(r"^bucket:\s*(.*)$", text, re.M)
    if not m:
        return []
    value = m.group(1).strip()
    if not value:  # block-list form on the following lines
        value = " ".join(re.findall(r"^\s*-\s*(\w+)", text[m.end() : m.end() + 200], re.M))
    return re.findall(r"\w+", value.strip("[]"))


def unlock_targets(text: str) -> set[str]:
    """Task ids under ``predicted_impact.tasks_will_unlock`` only.

    Deliberately excludes tasks_at_risk / tasks_will_stabilize: we are measuring
    what the candidate aims to fix, not what it might break.
    """
    m = re.search(
        r"tasks_will_unlock:(.*?)(?=^\s{2}tasks_|^\s{0,2}predicted_core|^[a-z_]+:)",
        text,
        re.M | re.S,
    )
    return set(TID.findall(m.group(1))) if m else set()


def load_history(run: str) -> tuple[dict[str, list[bool]], dict[int, dict[str, bool]]]:
    flat: dict[str, list[bool]] = collections.defaultdict(list)
    by_round: dict[int, dict[str, bool]] = {}
    cap = CAP.get(run)
    for line in (RUNS / run / "data" / "task_history.jsonl").open(encoding="utf-8", errors="replace"):
        row = json.loads(line)
        if row["task_id"] not in SUBSET:
            continue
        if cap is not None and int(row["round"]) > cap:
            continue
        flat[row["task_id"]].append(bool(row["passed"]))
        by_round.setdefault(int(row["round"]), {})[row["task_id"]] = bool(row["passed"])
    return flat, by_round


def decisions(run: str) -> tuple[set[str], set[str]]:
    shipped: set[str] = set()
    for d in round_dirs(RUNS / run, "R*/decision.md"):
        text = read(d)
        front = text.split("---")[1] if text.count("---") >= 2 else ""
        shipped |= set(re.findall(r"candidate_id:\s*(C-R\d+-\d+)", front))
    rejected: set[str] = set()
    p = RUNS / run / "data" / "rejected_candidates.jsonl"
    if p.exists():
        for line in p.open(encoding="utf-8", errors="replace"):
            try:
                rejected.add(json.loads(line)["candidate_id"])
            except Exception:
                pass
    return shipped, rejected


def main() -> None:
    history: dict[str, list[bool]] = collections.defaultdict(list)
    per_run: dict[str, dict[int, dict[str, bool]]] = {}
    for run in ALL:
        flat, by_round = load_history(run)
        per_run[run] = by_round
        for task, outcomes in flat.items():
            history[task].extend(outcomes)

    cls = {task: ("never" if not any(v) else "always" if all(v) else "volatile") for task, v in history.items()}
    counts = collections.Counter(cls.values())

    print("=" * 78)
    print("T3  Task classes on the 100-task no-pixel subset, six whitelist campaigns")
    print("=" * 78)
    print(f"  never solved : {counts['never']:3d}   {sorted(t for t, c in cls.items() if c == 'never')}")
    print(f"  volatile     : {counts['volatile']:3d}")
    print(f"  always pass  : {counts['always']:3d}")
    print(f"  evaluations  : {sum(len(v) for v in history.values()):,}")

    print()
    print("=" * 78)
    print("T1  Candidate-bucket census (primary bucket) with decisions")
    print("=" * 78)
    print(f"{'run':16s} {'N':>3s}  " + "  ".join(f"{b:>22s}" for b in BUCKETS))
    arm_totals = {"no-graph": collections.Counter(), "graph": collections.Counter()}
    for run in ALL:
        shipped, rejected = decisions(run)
        tot: collections.Counter = collections.Counter()
        state: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for card in sorted(round_dirs(RUNS / run, "R*/candidates/C-*.md")):
            buckets = card_buckets(read(card))
            if not buckets:
                continue
            b = buckets[0]
            tot[b] += 1
            state[b]["ship" if card.stem in shipped else "rej" if card.stem in rejected else "other"] += 1
        n = sum(tot.values())
        arm = "no-graph" if run in NO_GRAPH else "graph"
        arm_totals[arm].update(tot)
        cells = []
        for b in BUCKETS:
            if tot[b]:
                cells.append(f"{tot[b]:2d} {tot[b] / n * 100:4.1f}% s{state[b]['ship']:<2d}r{state[b]['rej']:<2d}")
            else:
                cells.append(" " * 22)
        print(f"{run:16s} {n:3d}  " + "  ".join(f"{c:>22s}" for c in cells))
    print("-" * 78)
    for arm in ("no-graph", "graph"):
        n = sum(arm_totals[arm].values())
        share = "  ".join(f"{b} {arm_totals[arm][b]}/{n} = {arm_totals[arm][b] / n * 100:.1f}%" for b in BUCKETS)
        print(f"  {arm:9s} pooled: {share}")

    print()
    print("=" * 78)
    print("T2  Aim selectivity: candidate targets vs. the failing set they came from")
    print("=" * 78)
    print(
        f"{'run':16s} {'cands':>5s} {'targets':>7s} {'aim %vol':>9s} {'fail %vol':>10s} {'enrich':>7s}"
        f" {'aim %never':>11s} {'fail %never':>12s}"
    )
    for run in ALL:
        aim_vol = aim_never = aim_n = 0
        fail_vol = fail_never = fail_n = 0
        cards = 0
        for card in sorted(round_dirs(RUNS / run, "R*/candidates/C-*.md")):
            rd = int(ROUND_OF.search(card.parts[-3]).group(1))
            targets = unlock_targets(read(card)) & set(cls)
            failing = {t for t, ok in (per_run[run].get(rd - 1) or {}).items() if not ok}
            if not targets or not failing:
                continue
            cards += 1
            for t in failing:
                fail_n += 1
                fail_vol += cls[t] == "volatile"
                fail_never += cls[t] == "never"
            for t in targets:
                aim_n += 1
                aim_vol += cls[t] == "volatile"
                aim_never += cls[t] == "never"
        if not (aim_n and fail_n):
            continue
        enrich = (aim_vol / aim_n) / (fail_vol / fail_n)
        print(
            f"{run:16s} {cards:5d} {aim_n:7d} {aim_vol / aim_n * 100:8.1f}% {fail_vol / fail_n * 100:9.1f}%"
            f" {enrich:7.2f} {aim_never / aim_n * 100:10.1f}% {fail_never / fail_n * 100:11.1f}%"
        )

    print()
    print("=" * 78)
    print("T4  Graph arms: node-type composition of the cross-task lift table")
    print("=" * 78)
    print(f"{'run':16s} {'rounds':>6s} {'nodes':>6s}  composition (all)          composition (lift >= 1.5)")
    row_re = re.compile(r"^\|\s*`([a-z]+):([^`]+)`\s*\|[^|]*\|[^|]*\|\s*([\d.]+)\s*\|", re.M)
    for run in GRAPH:
        every: collections.Counter = collections.Counter()
        high: collections.Counter = collections.Counter()
        rounds = 0
        for facts in sorted(round_dirs(RUNS / run, "R*/graph_evidence/facts.md")):
            rounds += 1
            for kind, _, lift in row_re.findall(read(facts)):
                every[kind] += 1
                if float(lift) >= 1.5:
                    high[kind] += 1
        n, h = sum(every.values()), sum(high.values())

        def fmt(counts, total):
            return " ".join(f"{k}:{v / total * 100:.0f}%" for k, v in counts.most_common())

        print(f"{run:16s} {rounds:6d} {n:6d}  {fmt(every, n):26s} {fmt(high, h)}")


if __name__ == "__main__":
    main()
