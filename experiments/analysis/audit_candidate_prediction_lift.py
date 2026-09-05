# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Re-derive the candidate prediction-lift comparison from raw artifacts.

Every shipped candidate names the tasks it expects to unlock
(``predicted_impact.tasks_will_unlock``).  This measures how often those tasks
actually flipped in the batch that ran under the shipped config, against the
base rate at which failing tasks flip anyway.

Alignment (proved by hashing, not assumed): sha256(R{k}/config.yaml)[:16]
equals curves.json[round==k].config_hash on the diagonal for every executed
round, so a candidate shipped in R{k} rides batch k — before = k-1, after = k.

First derived by an independent analysis on 2026-08-23; this script re-derives
it so the number is reproducible from the repo alone.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

RUNS = [
    ("baseline-seed1", "no-graph"),
    ("M24_103x3", "graph"),
    ("M25_103x16", "graph"),
    ("ghx-seed1", "graph"),
]
UUIDISH = re.compile(r"\b[0-9a-f]{8}-[0-9a-f\-]{10,}\b", re.I)


def predicted_ids(manifest: Path) -> list[str]:
    """tasks_will_unlock ids across the three shapes found in the wild.

    (a) block list (one ``- id`` per line), (b) inline flow list
    (``tasks_will_unlock: [id, id]``, M22 late rounds), and (c) the whole
    ``predicted_impact`` double-encoded as a YAML string containing YAML
    source (M25 C-R13-01).  All three reduce to: take the text from the key to
    the next sibling key and collect every task-id-shaped token in it — the
    sibling keys carry their own lists, so the window must stop before them.
    """
    text = manifest.read_text(encoding="utf-8", errors="replace")
    i = text.find("tasks_will_unlock")
    if i < 0:
        return []
    window = text[i : i + 3000]
    stop = re.search(
        r"tasks_will_stabilize|tasks_at_risk|tasks_will_pass|attribution_signature"
        r"|file_changes|capability_evidence",
        window[len("tasks_will_unlock") :],
    )
    if stop:
        window = window[: len("tasks_will_unlock") + stop.start()]
    out, seen = [], set()
    for m in UUIDISH.finditer(window):
        t = m.group(0)
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def audit_run(root: Path):
    curves = json.loads((root / "curves.json").read_text(encoding="utf-8"))
    hash_ok = 0
    for c in curves:
        k = int(c["round"])
        p = root / f"R{k}" / "config.yaml"
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()[:16] == c.get("config_hash"):
            hash_ok += 1
    ships = json.loads((root / "scoreboard.json").read_text(encoding="utf-8")).get("ships") or []

    fresh: dict[tuple[int, str], bool] = {}
    for line in (root / "data" / "task_history.jsonl").open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("carried"):
            continue
        fresh[(int(r.get("round", -1)), str(r.get("task_id")))] = bool(r.get("passed"))

    rows = []
    max_round = max((k for k, _ in fresh), default=-1)
    for s in ships:
        k, cid = int(s["round"]), str(s["cid"])
        if k > max_round:
            continue  # shipped config whose batch never ran (truncated campaign)
        manifest = root / f"R{k}" / "candidates" / f"{cid}.md"
        if not manifest.exists():
            continue
        pred = predicted_ids(manifest)
        if not pred:
            rows.append((root.name, cid, k, 0, 0, 0, None, "skipped: empty prediction"))
            continue
        elig = [t for t in pred if fresh.get((k - 1, t)) is False and (k, t) in fresh]
        hits = sum(1 for t in elig if fresh[(k, t)])
        base_pool = [t for (r, t), v in fresh.items() if r == k - 1 and v is False and (k, t) in fresh]
        base_hits = sum(1 for t in base_pool if fresh[(k, t)])
        rows.append((root.name, cid, k, len(pred), len(elig), hits, (base_hits, len(base_pool)), ""))
    return hash_ok, len(curves), rows


def pool(rows):
    elig = sum(r[4] for r in rows)
    hits = sum(r[5] for r in rows)
    # base pooled over distinct (run, round) transitions — round numbers repeat
    # across runs, so keying by round alone silently merges M24 R1 with M25 R1.
    seen = {}
    for r in rows:
        if r[6] and r[4] > 0:
            seen[(r[0], r[2])] = r[6]
    bh = sum(v[0] for v in seen.values())
    bn = sum(v[1] for v in seen.values())
    return elig, hits, bh, bn


def main() -> int:
    arms = {"no-graph": [], "graph": []}
    for name, arm in RUNS:
        root = Path("recipe/gaia_evolver/runs") / name
        hash_ok, n_rounds, rows = audit_run(root)
        scored = [r for r in rows if r[4] > 0]
        arms[arm].extend(scored)
        print(f"\n== {name} ({arm})  config-hash diagonal {hash_ok}/{n_rounds} ==")
        for _run, cid, k, npred, nelig, nhit, base, note in rows:
            b = f"{base[0]}/{base[1]}" if base else "-"
            print(f"  {cid:10} R{k:<2} pred={npred:2d} elig={nelig:2d} hit={nhit:2d} base={b:7} {note}")
    print("\n==== pooled per run ====")
    by_run: dict[str, list] = {}
    for rows in arms.values():
        for r in rows:
            by_run.setdefault(r[0], []).append(r)
    for run, rows in by_run.items():
        elig, hits, bh, bn = pool(rows)
        hr, br = hits / elig if elig else 0.0, bh / bn if bn else 0.0
        print(f"{run:14} candidates={len(rows):2d} eligible={elig:3d} hits={hits:3d} "
              f"hit_rate={100*hr:.1f}%  base={bh}/{bn}={100*br:.1f}%  lift={hr/br if br else 0:.2f}")
    print("\n==== pooled per arm ====")
    for arm, rows in arms.items():
        elig, hits, bh, bn = pool(rows)
        hr = hits / elig if elig else 0.0
        br = bh / bn if bn else 0.0
        print(
            f"{arm:9} candidates={len(rows):2d} eligible={elig:3d} hits={hits:3d} "
            f"hit_rate={100*hr:.1f}%  base={bh}/{bn}={100*br:.1f}%  lift={hr/br if br else 0:.2f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
