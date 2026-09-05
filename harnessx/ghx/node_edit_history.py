# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""What has already been tried on each graph node, and what happened (M25).

``facts.md`` has been telling every reader that node-level edit history "is not
yet recorded".  It has been recorded all along, in the wrong shape: the
candidate surface written per proposal
(``R{n}/graph_evidence/candidates/C-R{n}-NN.md``) carries the exact node ids a
candidate mutates, and the three round ledgers say what became of that
candidate.  Nothing ever joined them, so the loop had no memory of its own
edits — which is the machinery behind the most expensive repeat in this
project's record: M22 shipped a countdown processor, softened it seven rounds
later, and lost the mechanism; M25 shipped one, had it rolled back, and
proposed the softened version in the very next round.  Both times the node had
a history and nobody could read it.

Sources, all already on disk, all optional — a missing one narrows the answer
and never fabricates it:

* ``R{k}/graph_evidence/candidates/*.md`` — the surface, with a machine-readable
  ``nodes_added`` / ``nodes_removed`` / ``nodes_mutated`` block;
* ``data/ship_outcomes.json`` — which candidates shipped;
* ``data/rejected_candidates.jsonl`` — which were refused, and why;
* ``audit.jsonl`` ``kind="rollback"`` — which ships were later reverted whole.

An outcome we cannot establish is reported as ``unknown``, never as ``rejected``:
absence of a ledger row is absence of knowledge.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

SHIPPED = "shipped"
ROLLED_BACK = "shipped, then rolled back"
REJECTED = "rejected"
UNKNOWN = "unknown"

_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)
_EDIT_KINDS = (("nodes_added", "added"), ("nodes_removed", "removed"), ("nodes_mutated", "mutated"))


@dataclass(frozen=True)
class NodeEdit:
    node: str
    round_n: int
    candidate_id: str
    kind: str  # added | removed | mutated
    outcome: str  # shipped | shipped, then rolled back | rejected | unknown
    bucket: str = ""

    def __lt__(self, other) -> bool:  # deterministic rendering
        return (self.node, self.round_n, self.candidate_id, self.kind) < (
            other.node,
            other.round_n,
            other.candidate_id,
            other.kind,
        )


def _read_json_block(path: Path) -> dict | None:
    try:
        m = _JSON_BLOCK.search(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — an unreadable surface narrows history, never sinks it
        return None
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:  # noqa: BLE001
        return None


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _iter_jsonl(path: Path):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:  # noqa: BLE001
        return
    for line in lines:
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except Exception:  # noqa: BLE001
            continue


def _outcomes(run_dir: Path) -> dict[str, tuple[str, str]]:
    """``{candidate_id: (outcome, bucket)}`` from the three ledgers."""
    out: dict[str, tuple[str, str]] = {}
    ships = _load_json(run_dir / "data" / "ship_outcomes.json")
    for s in ships or ():
        if isinstance(s, dict) and s.get("ship_id"):
            out[str(s["ship_id"])] = (SHIPPED, str(s.get("bucket") or ""))
    for r in _iter_jsonl(run_dir / "data" / "rejected_candidates.jsonl"):
        cid = str(r.get("candidate_id") or "")
        if cid and cid not in out:  # a shipped id is never overwritten by a rejection row
            out[cid] = (REJECTED, str(r.get("bucket") or ""))
    # A rollback reverts a ship after the fact and is the single most important
    # thing a later round can know about a node — it overwrites `shipped`.
    for row in _iter_jsonl(run_dir / "audit.jsonl"):
        if str(row.get("kind")) != "rollback":
            continue
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                import ast

                payload = ast.literal_eval(payload)
            except Exception:  # noqa: BLE001
                payload = None
        if not isinstance(payload, dict):
            continue
        for cid in payload.get("rolled_back_cids") or ():
            prev = out.get(str(cid))
            out[str(cid)] = (ROLLED_BACK, prev[1] if prev else "")
    return out


def collect_node_edits(run_dir, round_n: int) -> dict[str, list[NodeEdit]]:
    """Every node edit proposed in rounds < ``round_n``, keyed by node id.

    Rounds are read from disk rather than assumed contiguous: a resumed or
    partially-archived run simply contributes the rounds it still has.
    """
    run_dir = Path(run_dir)
    outcomes = _outcomes(run_dir)
    by_node: dict[str, list[NodeEdit]] = {}
    for k in range(0, int(round_n)):
        cand_dir = run_dir / f"R{k}" / "graph_evidence" / "candidates"
        if not cand_dir.is_dir():
            continue
        for path in sorted(cand_dir.glob("*.md")):
            block = _read_json_block(path)
            if not isinstance(block, dict):
                continue
            cid = str(block.get("candidate_id") or path.stem)
            outcome, bucket = outcomes.get(cid, (UNKNOWN, ""))
            for field, kind in _EDIT_KINDS:
                for node in block.get(field) or ():
                    rec = NodeEdit(str(node), k, cid, kind, outcome, bucket)
                    by_node.setdefault(str(node), []).append(rec)
    for recs in by_node.values():
        recs.sort()
    return by_node


_HEADER = (
    "What has already been tried on each node, and what became of it. A node that was "
    "edited and rolled back is not an untouched node, and the softened re-run of a "
    "reverted mechanism is not a new idea — this project has lost the same countdown "
    "mechanism twice that way, once per campaign, because nothing carried the node's "
    "history across rounds."
)

_EMPTY = (
    "No node edits recorded in earlier rounds of this run. This is *nothing tried yet*, "
    "not *nothing to try*."
)


_UBIQUITOUS_SHARE = 0.8

_UBIQUITOUS_NOTE = (
    "Read `mutated` on these with suspicion: they carry a params diff against the "
    "parent config in nearly every candidate regardless of what the candidate was "
    "for, which is the shape of a config-serialisation artifact, not of an edit "
    "aimed at the node. `added` / `removed` rows are unaffected — those are "
    "structural."
)


def render_node_edit_history(by_node: dict[str, list[NodeEdit]], priority=None) -> list[str]:
    """facts.md's history section. ``priority`` (the lift table's nodes) sorts first."""
    lines = ["## Node edit history", ""]
    if not by_node:
        lines.append(_EMPTY)
        lines.append("")
        return lines
    lines.append(_HEADER)
    lines.append("")
    lines.append("| node | round | candidate | edit | bucket | outcome |")
    lines.append("|---|---|---|---|---|---|")
    front = [n for n in (priority or ()) if n in by_node]
    rest = sorted(n for n in by_node if n not in set(front))
    for node in front + rest:
        for e in by_node[node]:
            lines.append(
                f"| `{e.node}` | R{e.round_n} | {e.candidate_id} | {e.kind} | "
                f"{e.bucket or '—'} | {e.outcome} |"
            )
    lines.append("")
    all_cids = {e.candidate_id for recs in by_node.values() for e in recs}
    if len(all_cids) >= 5:
        ubiquitous = sorted(
            n
            for n, recs in by_node.items()
            if len({e.candidate_id for e in recs}) >= _UBIQUITOUS_SHARE * len(all_cids)
        )
        if ubiquitous:
            lines.append(
                "Touched by ≥"
                f"{int(100 * _UBIQUITOUS_SHARE)}% of all {len(all_cids)} candidates: "
                + ", ".join(f"`{n}`" for n in ubiquitous)
                + ". "
                + _UBIQUITOUS_NOTE
            )
            lines.append("")
    return lines


__all__ = [
    "NodeEdit",
    "SHIPPED",
    "ROLLED_BACK",
    "REJECTED",
    "UNKNOWN",
    "collect_node_edits",
    "render_node_edit_history",
]
