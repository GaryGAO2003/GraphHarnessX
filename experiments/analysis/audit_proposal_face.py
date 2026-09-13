# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""The proposal face: what the six whitelist campaigns' Evolvers WROTE, what the
roles READ, and where the between-arm difference sits. Nothing here is an
outcome number; landing is read only to locate the shift.

Scope: the six whitelist campaigns (three no-graph seeds, three graph seeds),
evolve rounds R1..R15 (the formal sixteen-round window; R0 never evolves).
Only directories named exactly R<digits> are read -- quarantined
``*_poisoned_gateway`` directories are never opened.

Sections (each prints the numbers its ledger row cites):
  P1  proposal bucket census (primary bucket) per seed, pooled shares,
      seed-level exact permutation test on the tools share
  P2  where the shift sits: Critic acceptance per bucket, graph-existence gate
      outcome per bucket, landed ships per bucket, Planner-flagged bucket per
      round and the Evolver's compliance with it
  P3  what the cards cite (regex census) and the typed operations written
  P4  graph arms: does a card name the round's top-lift nodes
  P5  predictions per card; machine-derived core / halo split; hit rate of core
      against halo predictions under the F9 rule
  P6  Digester failure-tag vocabulary
  P7  regressions surfaced per round, decision types, rollback count
  P8  tool re-touch, rejected / revived candidates, missing dossiers
  P9  aim selectivity by task class (enrichment against the failing set)

Usage:  python experiments/analysis/audit_proposal_face.py
"""

from __future__ import annotations

import collections
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "recipe" / "gaia_evolver"
RUNS = ROOT / "runs"
NO_GRAPH = ["baseline-seed1", "baseline-seed2", "baseline-seed3"]
GRAPH = ["ghx-seed1", "ghx-seed2", "ghx-seed3"]
ALL = NO_GRAPH + GRAPH
BUCKETS = ["tools", "processor", "prompt", "config"]
WINDOW = 15  # R1..R15
RD = re.compile(r"^R(\d+)$")
TID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SUBSET = {
    t["task_id"] for t in json.loads((ROOT / "data" / "webthinker_gaia_dev_nopixel.json").read_text(encoding="utf-8"))
}
assert len(SUBSET) == 100, len(SUBSET)


def arm_of(run: str) -> str:
    return "no-graph" if run in NO_GRAPH else "graph"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def strict(root: Path, pat: str) -> list[Path]:
    """glob, keeping only paths whose first component is a bare R<digits> directory."""
    return sorted(p for p in root.glob(pat) if RD.fullmatch(p.relative_to(root).parts[0]))


def rnum(p: Path) -> int:
    for part in p.parts:
        m = RD.fullmatch(part)
        if m:
            return int(m.group(1))
    raise ValueError(p)


def card_buckets(text: str) -> list[str]:
    m = re.search(r"^bucket:\s*(.*)$", text, re.M)
    if not m:
        return []
    value = m.group(1).strip()
    if not value:
        value = " ".join(re.findall(r"^\s*-\s*(\w+)", text[m.end() : m.end() + 200], re.M))
    return re.findall(r"\w+", value.strip("[]"))


def id_block(text: str, key: str) -> set[str] | None:
    m = re.search(rf"^{key}:(.*?)(?=^[a-z_]+:|\Z)", text, re.M | re.S)
    return set(TID.findall(m.group(1))) if m else None


def unlock_targets(text: str) -> set[str]:
    m = re.search(r"tasks_will_unlock:(.*?)(?=^\s{2}tasks_|^\s{0,2}predicted_core|^[a-z_]+:)", text, re.M | re.S)
    return set(TID.findall(m.group(1))) if m else set()


def cards_of(run: str) -> list[tuple[int, str, list[str], str]]:
    out = []
    for c in strict(RUNS / run, "R*/candidates/C-*.md"):
        rd = rnum(c)
        if rd > WINDOW:
            continue
        t = read(c)
        b = card_buckets(t)
        if b:
            out.append((rd, c.stem, b, t))
    return out


def critic_accepted(run: str) -> set[str]:
    ok: set[str] = set()
    for d in strict(RUNS / run, "R*/decision.md"):
        if rnum(d) > WINDOW:
            continue
        text = read(d)
        front = text.split("---")[1] if text.count("---") >= 2 else ""
        ok |= set(re.findall(r"candidate_id:\s*(C-R\d+-\d+)", front))
    return ok


def scoreboard_ships(run: str) -> list[tuple[int, str]]:
    sb = RUNS / run / "scoreboard.json"
    ships = (json.loads(read(sb)).get("ships") or []) if sb.exists() else []
    return [(int(s["round"]), str(s["cid"])) for s in ships if int(s["round"]) <= WINDOW]


def fresh_history(run: str) -> dict[tuple[int, str], bool]:
    fresh: dict[tuple[int, str], bool] = {}
    for line in (RUNS / run / "data" / "task_history.jsonl").open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("carried") or r["task_id"] not in SUBSET:
            continue
        fresh[(int(r["round"]), str(r["task_id"]))] = bool(r["passed"])
    return fresh


NAME = re.compile(
    r"attribution_signature:\s*\n(?:.*\n){0,6}?\s*(?:name|tool|tool_name|value):\s*['\"]?([A-Za-z_]\w*)", re.M
)
NODE = re.compile(r"\b(?:tool|proc|model):[A-Za-z_][\w#]*")
BUCKET_RX = re.compile(r"\b(tools|processor|prompt|config)\b")


def flagged_bucket(run: str, rd: int) -> str | None:
    """Bucket the round's landscape relays as the prior Critic's strategy_concern
    (its section 0), else a 'neglected bucket' line; None when neither names one."""
    p = RUNS / run / f"R{rd}" / "landscape.md"
    if not p.exists():
        return None
    t = read(p)
    m = re.search(r"^### 0\..*?(?=^### |\Z)", t, re.M | re.S)
    words = collections.Counter(BUCKET_RX.findall(m.group(0) if m else ""))
    if words:
        return words.most_common(1)[0][0]
    m = re.search(r"neglected bucket[^\n]*?`?(tools|processor|prompt|config)`?", t, re.I)
    return m.group(1).lower() if m else None


def hdr(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main() -> None:
    cards = {run: cards_of(run) for run in ALL}

    # ------------------------------------------------------------------ P1
    hdr("P1  proposal bucket census, primary bucket, R1..R15")
    pooled = {"no-graph": collections.Counter(), "graph": collections.Counter()}
    multi = collections.Counter()
    share = {}
    for run in ALL:
        c = collections.Counter(b[0] for _, _, b, _ in cards[run])
        n = sum(c.values())
        pooled[arm_of(run)].update(c)
        multi[arm_of(run)] += sum(len(b) > 1 for _, _, b, _ in cards[run])
        share[run] = c["tools"] / n
        print(
            f"  {run:15s} N {n:2d}  "
            + "  ".join(f"{k} {c[k]:2d}" for k in BUCKETS)
            + f"   tools share {share[run] * 100:.1f}%"
        )
    for arm in ("no-graph", "graph"):
        n = sum(pooled[arm].values())
        print(
            f"  {arm:9s} N {n}  "
            + "  ".join(f"{k} {pooled[arm][k]} ({pooled[arm][k] / n * 100:.1f}%)" for k in BUCKETS)
            + f"   multi-bucket cards {multi[arm]}/{n}"
        )
    ng = [share[r] for r in NO_GRAPH]
    g = [share[r] for r in GRAPH]
    obs = sum(g) / 3 - sum(ng) / 3
    vals = ng + g
    cnt = sum(
        (sum(vals[i] for i in combo) / 3 - sum(vals[i] for i in range(6) if i not in combo) / 3) >= obs - 1e-12
        for combo in itertools.combinations(range(6), 3)
    )
    print(
        f"  seed-level tools share: no-graph {[round(x * 100, 1) for x in ng]}  graph {[round(x * 100, 1) for x in g]}"
        f"  diff {obs * 100:.1f} pp  exact one-sided permutation p = {cnt}/20 = {cnt / 20:.2f}"
    )

    # ------------------------------------------------------------------ P2
    hdr("P2  where the shift sits")
    for arm, runs in (("no-graph", NO_GRAPH), ("graph", GRAPH)):
        acc = collections.Counter()
        tot = collections.Counter()
        for run in runs:
            ok = critic_accepted(run)
            for _, cid, b, _ in cards[run]:
                tot[b[0]] += 1
                acc[b[0]] += cid in ok
        print(
            f"  Critic acceptance {arm:9s} "
            + "  ".join(f"{k} {acc[k]}/{tot[k]} ({acc[k] / max(tot[k], 1) * 100:.0f}%)" for k in BUCKETS)
        )
    gate = collections.Counter()
    labels = collections.Counter()
    for run in GRAPH:
        bucket_of = {cid: b[0] for _, cid, b, _ in cards[run]}
        for gf in strict(RUNS / run, "R*/graph_evidence/gate/C-*.md"):
            if rnum(gf) > WINDOW:
                continue
            t = read(gf)
            ok = re.search(r"^- ok:\s*(\w+)", t, re.M)
            checked = re.search(r"^- checked:\s*(\w+)", t, re.M)
            label = re.search(r"^- label:\s*(\S+)", t, re.M)
            key = (
                "refused"
                if ok and ok.group(1) == "False"
                else "unchecked"
                if checked and checked.group(1) == "False"
                else "passed"
            )
            b = bucket_of.get(gf.stem, "?")
            gate[(b, key)] += 1
            if key == "refused":
                labels[label.group(1) if label else "?"] += 1
    print(
        "  graph-existence gate, three graph seeds: "
        + "  ".join(f"{k} {gate[(k, 'refused')]}R/{gate[(k, 'passed')]}P/{gate[(k, 'unchecked')]}U" for k in BUCKETS)
        + f"   refusal labels {dict(labels)}"
    )
    for arm, runs in (("no-graph", NO_GRAPH), ("graph", GRAPH)):
        landed = collections.Counter()
        n_ships = 0
        for run in runs:
            bucket_of = {cid: b[0] for _, cid, b, _ in cards[run]}
            for _, cid in scoreboard_ships(run):
                n_ships += 1
                landed[bucket_of.get(cid, "?")] += 1
        print(f"  landed (scoreboard) {arm:9s} N {n_ships}  " + "  ".join(f"{k} {landed[k]}" for k in BUCKETS + ["?"]))
    for arm, runs in (("no-graph", NO_GRAPH), ("graph", GRAPH)):
        flags = collections.Counter()
        comply = [0, 0]
        fl = [0, 0]
        other = [0, 0]
        for run in runs:
            fb = {rd: flagged_bucket(run, rd) for rd in range(1, WINDOW + 1)}
            flags.update(v for v in fb.values() if v)
            for rd, _, b, _ in cards[run]:
                if fb.get(rd):
                    comply[1] += 1
                    comply[0] += b[0] == fb[rd]
                slot = fl if fb.get(rd) == "tools" else other
                slot[1] += 1
                slot[0] += b[0] == "tools"
        print(
            f"  flagged rounds {arm:9s} {dict(flags)}  cards in flagged rounds matching the flag {comply[0]}/{comply[1]}"
            f" ({comply[0] / max(comply[1], 1) * 100:.0f}%)  tools cards: tools-flagged rounds {fl[0]}/{fl[1]} ({fl[0] / max(fl[1], 1) * 100:.0f}%),"
            f" other rounds {other[0]}/{other[1]} ({other[0] / max(other[1], 1) * 100:.0f}%)"
        )

    # ------------------------------------------------------------------ P3
    hdr("P3  what the cards cite; typed operations written")
    CITE = {
        "trajectory step anchors": re.compile(r"#step[s_]?\d|#steps?_\d|_r\d+\.jsonl", re.I),
        "graph node names": NODE,
        "lift": re.compile(r"\blift\b", re.I),
        "cone / unfold / motif": re.compile(
            r"\bcone\b|\bunfold|\bmotif|empty_consumed|budget_no_commit|ungrounded_commit", re.I
        ),
        "fire / false-positive / at-risk": re.compile(r"\bfired?\b|false[- ]positive|\bat risk\b", re.I),
        "replay": re.compile(r"\breplay", re.I),
        "prompt / template": re.compile(r"system[_ ]prompt|template|instruction", re.I),
    }
    for arm, runs in (("no-graph", NO_GRAPH), ("graph", GRAPH)):
        n = 0
        tot = collections.Counter()
        present = collections.Counter()
        for run in runs:
            for _, _, _, t in cards[run]:
                n += 1
                for k, rx in CITE.items():
                    c = len(rx.findall(t))
                    tot[k] += c
                    present[k] += c > 0
        print(f"  {arm:9s} cards {n}")
        for k in CITE:
            print(f"      {k:32s} mean {tot[k] / n:5.2f}/card   in {present[k] / n * 100:3.0f}% of cards")
    OPS = re.compile(r"graph edit\(s\):\s*([^\n']+)")
    ops = collections.Counter()
    for run in GRAPH:
        for _, _, _, t in cards[run]:
            for m in OPS.findall(t):
                for name, k in re.findall(r"(\w+?)x(\d+)", m):
                    ops[name] += int(k)
    print(
        f"  typed operations, three graph seeds: {dict(ops.most_common())}  (never used: "
        f"{[o for o in ['change_dependency', 'swap_subgraph', 'mutate_inactive'] if ops[o] == 0]})"
    )

    # ------------------------------------------------------------------ P4
    hdr("P4  graph arms: writing against the round's lift table")
    ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)\s*\|", re.M)
    by_top = {"tool": [0, 0], "proc": [0, 0]}
    for run in GRAPH:
        facts = {}
        for f in strict(RUNS / run, "R*/graph_evidence/facts.md"):
            if rnum(f) > WINDOW:
                continue
            rows = sorted([(nm, float(lift)) for nm, _, _, lift in ROW.findall(read(f))], key=lambda x: -x[1])
            facts[rnum(f)] = rows
        n = top3 = top1 = 0
        for rd, _, b, t in cards[run]:
            rows = facts.get(rd)
            if not rows:
                continue
            n += 1
            names = set(NODE.findall(t))
            top3 += bool(names & {x[0] for x in rows[:3]})
            top1 += rows[0][0] in names
            kind = rows[0][0].split(":")[0]
            if kind in by_top:
                by_top[kind][1] += 1
                by_top[kind][0] += b[0] == "tools"
        print(
            f"  {run}: cards with a lift table {n}; naming a top-3 node {top3} ({top3 / max(n, 1) * 100:.0f}%); naming the top-1 {top1} ({top1 / max(n, 1) * 100:.0f}%)"
        )
    print(
        f"  P(tools card | top-1 node is a tool) = {by_top['tool'][0]}/{by_top['tool'][1]};"
        f"  P(tools card | top-1 node is a processor) = {by_top['proc'][0]}/{by_top['proc'][1]}"
    )

    # ------------------------------------------------------------------ P5
    hdr("P5  predictions per card; core / halo; hit rate by class under the F9 rule")
    for run in ALL:
        u = [len(unlock_targets(t)) for _, _, _, t in cards[run]]
        core = [len(id_block(t, "predicted_core") or set()) for _, _, _, t in cards[run]]
        halo = [len(id_block(t, "predicted_halo") or set()) for _, _, _, t in cards[run]]
        nocone = [len(id_block(t, "predicted_no_cone") or set()) for _, _, _, t in cards[run]]
        with_split = sum(id_block(t, "predicted_core") is not None for _, _, _, t in cards[run])
        outside = sum(
            len(
                unlock_targets(t)
                - (id_block(t, "predicted_core") or set())
                - (id_block(t, "predicted_halo") or set())
                - (id_block(t, "predicted_no_cone") or set())
            )
            for _, _, _, t in cards[run]
            if id_block(t, "predicted_core") is not None
        )
        n = len(u)
        print(
            f"  {run:15s} cards {n:2d}  unlock/card mean {sum(u) / n:.1f} median {sorted(u)[n // 2]} max {max(u)}"
            f"  | cards with split {with_split:2d}  core {sum(core) / n:.1f}  halo {sum(halo) / n:.1f}  no_cone {sum(nocone) / n:.2f}"
            f"  unlock outside the split {outside}"
        )
    for arm, runs in (("no-graph", NO_GRAPH), ("graph", GRAPH)):
        n = sum(len(cards[r]) for r in runs)
        u = sum(len(unlock_targets(t)) for r in runs for _, _, _, t in cards[r])
        core = sum(len(id_block(t, "predicted_core") or set()) for r in runs for _, _, _, t in cards[r])
        halo = sum(len(id_block(t, "predicted_halo") or set()) for r in runs for _, _, _, t in cards[r])
        print(
            f"  pooled {arm:9s} cards {n}  unlock/card {u / n:.2f}  core/card {core / n:.2f}  halo/card {halo / n:.2f}"
            + (f"  halo share of unlock {halo / max(u, 1) * 100:.0f}%" if halo else "")
        )
    hit = {"core": [0, 0], "halo": [0, 0]}
    base = [0, 0]
    seen_rounds = set()
    for run in GRAPH:
        fresh = fresh_history(run)
        for k, cid in scoreboard_ships(run):
            card = RUNS / run / f"R{k}" / "candidates" / f"{cid}.md"
            if not card.exists():
                continue
            t = read(card)
            for cls in ("core", "halo"):
                pred = id_block(t, f"predicted_{cls}") or set()
                elig = [x for x in pred if fresh.get((k - 1, x)) is False and (k, x) in fresh]
                hit[cls][1] += len(elig)
                hit[cls][0] += sum(fresh[(k, x)] for x in elig)
            if (run, k) not in seen_rounds:
                seen_rounds.add((run, k))
                pool = [x for (r, x), v in fresh.items() if r == k - 1 and v is False and (k, x) in fresh]
                base[1] += len(pool)
                base[0] += sum(fresh[(k, x)] for x in pool)
    print(
        f"  three graph seeds, landed ships, F9 rule (fresh-failed at k-1, fresh at k, passes at k):"
        f"  core {hit['core'][0]}/{hit['core'][1]} = {hit['core'][0] / max(hit['core'][1], 1) * 100:.0f}%"
        f"  halo {hit['halo'][0]}/{hit['halo'][1]} = {hit['halo'][0] / max(hit['halo'][1], 1) * 100:.0f}%"
        f"  passive base pool {base[0]}/{base[1]} = {base[0] / max(base[1], 1) * 100:.0f}%"
    )

    # ------------------------------------------------------------------ P6
    hdr("P6  Digester failure-tag vocabulary (failing tasks, R0..R15 summaries)")
    IDX = re.compile(r"^- `([0-9a-f-]{36})` — pattern=(\w+) tag=`([^`]*)`", re.M)
    for arm, runs in (("no-graph", NO_GRAPH), ("graph", GRAPH)):
        tags = collections.Counter()
        for run in runs:
            for s in strict(RUNS / run, "R*/summary.md"):
                if rnum(s) > WINDOW:
                    continue
                for _t, pat, tag in IDX.findall(read(s)):
                    if pat != "ALL_PASS" and tag not in ("none", ""):
                        tags[tag] += 1
        n = sum(tags.values())
        top3 = sum(v for _, v in tags.most_common(3))
        once = sum(1 for v in tags.values() if v == 1)
        print(
            f"  {arm:9s} failing digests {n}  distinct tags {len(tags)}  used once {once} ({once / len(tags) * 100:.0f}% of the vocabulary)"
            f"  top-3 share {top3 / n * 100:.0f}%  top tags {tags.most_common(4)}"
        )

    # ------------------------------------------------------------------ P7
    hdr("P7  regressions surfaced; decision types; rollbacks")
    for run in ALL:
        dec = collections.Counter()
        forgiven = 0
        for d in strict(RUNS / run, "R*/decision.md"):
            if rnum(d) > WINDOW:
                continue
            t = read(d)
            m = re.search(r"^decision_type:\s*(\w+)", t, re.M)
            dec[m.group(1) if m else "?"] += 1
            forgiven += bool(re.search(r"regression is acceptable", t, re.I))
        hard = {}
        for r in strict(RUNS / run, "R*/regressions.md"):
            if 1 <= rnum(r) <= WINDOW:
                m = re.search(r"\*\*regressed_hard\*\*:\s*(\d+)", read(r))
                hard[rnum(r)] = int(m.group(1)) if m else 0
        nz = sum(1 for v in hard.values() if v > 0)
        print(
            f"  {run:15s} decisions {dict(dec)}  regression files {len(hard)}, with hard regressions {nz}, "
            f"mean/round {sum(hard.values()) / max(len(hard), 1):.1f}, max {max(hard.values()) if hard else 0}  'regression is acceptable' in {forgiven} decisions"
        )

    # ------------------------------------------------------------------ P8
    hdr("P8  tool re-touch; rejected / revived; missing dossiers")
    for run in ALL:
        names = collections.Counter()
        for _, _, b, t in cards[run]:
            if b[0] == "tools":
                m = NAME.search(t)
                names[m.group(1) if m else "?"] += 1
        rows = [
            json.loads(line)
            for line in (RUNS / run / "data" / "rejected_candidates.jsonl").open(encoding="utf-8", errors="replace")
        ]
        rows = [r for r in rows if int(r.get("round", 0)) <= WINDOW]
        miss = 0
        for s in strict(RUNS / run, "R*/summary.md"):
            if rnum(s) > WINDOW:
                continue
            m = re.search(r"## Missing digests[^\n]*\n(.*?)(?=\n## |\Z)", read(s), re.S)
            if m:
                miss += len(re.findall(r"^\s*[-*]\s", m.group(1), re.M))
        multi_names = {k: v for k, v in names.items() if v >= 2 and k != "?"}
        print(
            f"  {run:15s} tools cards {sum(names.values()):2d} over {len(names):2d} tool names, touched>=2 {multi_names}"
            f"  | rejected {len(rows)} revived {sum(1 for r in rows if r.get('revived_as'))}  | missing dossiers {miss}"
        )

    # ------------------------------------------------------------------ P9
    hdr("P9  aim selectivity by task class (targets vs the failing set they came from)")
    history: dict[str, list[bool]] = collections.defaultdict(list)
    per_run: dict[str, dict[int, dict[str, bool]]] = {}
    for run in ALL:
        by_round: dict[int, dict[str, bool]] = {}
        for line in (RUNS / run / "data" / "task_history.jsonl").open(encoding="utf-8", errors="replace"):
            row = json.loads(line)
            if row["task_id"] not in SUBSET or int(row["round"]) > WINDOW:
                continue
            history[row["task_id"]].append(bool(row["passed"]))
            by_round.setdefault(int(row["round"]), {})[row["task_id"]] = bool(row["passed"])
        per_run[run] = by_round
    cls = {t: ("never" if not any(v) else "always" if all(v) else "volatile") for t, v in history.items()}
    for run in ALL:
        aim_vol = aim_n = fail_vol = fail_n = 0
        for rd, _, _, t in cards[run]:
            targets = unlock_targets(t) & set(cls)
            failing = {x for x, ok in (per_run[run].get(rd - 1) or {}).items() if not ok}
            if not targets or not failing:
                continue
            fail_n += len(failing)
            fail_vol += sum(cls[x] == "volatile" for x in failing)
            aim_n += len(targets)
            aim_vol += sum(cls[x] == "volatile" for x in targets)
        if aim_n and fail_n:
            print(
                f"  {run:15s} targets {aim_n:3d}  aim %volatile {aim_vol / aim_n * 100:5.1f}  failing-set %volatile {fail_vol / fail_n * 100:5.1f}"
                f"  enrichment {(aim_vol / aim_n) / (fail_vol / fail_n):.2f}"
            )


if __name__ == "__main__":
    main()
