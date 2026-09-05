# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Is the evolution loop actually closed, or only shaped like it?

Every channel that carries a round's results back to the next round's Planner
has now been caught reporting confidently while carrying nothing:

  reputation.json      empty in all four buckets for a whole campaign, because
                       a list bucket raised into an ``except Exception: pass``
  hit_rate             0/13 and 0/3 on ships that actually landed 7/13 and 1/3,
                       because the Evolver typed abbreviated task ids
  merged.yaml          absent while decision.md said ship, so the round ran the
                       previous config and the ledger booked the noise as a win

None of the three raised, logged, or looked wrong from the outside. They were
found by reading two finished campaigns, which is the expensive way.

So: a read-only sweep that answers one question per channel, over any run
directory, in a second. Run it before launching an arm and after it lands.

    python -m harnessx.ghx.loop_health recipe/gaia_evolver/runs/M14_L0_arm
    python -m harnessx.ghx.loop_health recipe/gaia_evolver/runs/*

Exit code is the number of runs with at least one BROKEN channel, so it can
gate a launch script. DEGRADED is reported but does not fail: a campaign that
simply never shipped has an empty reputation for an honest reason.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_OK, _DEGRADED, _BROKEN = "ok", "DEGRADED", "BROKEN"


@dataclass
class Check:
    channel: str
    status: str
    detail: str


def _round_dirs(run: Path) -> list[Path]:
    return sorted(
        (p for p in run.glob("R*") if p.is_dir() and re.fullmatch(r"R\d+", p.name)),
        key=lambda p: int(p.name[1:]),
    )


def _load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _shipped_rounds(run: Path) -> set[int]:
    """Rounds where the system recorded a ship — not where the Critic asked for one.

    ``decision.md`` is the Critic's raw output and is the wrong source: a stage-4
    gate can refuse the decision afterwards, and the round is then correctly a
    no_op with a decision.md still saying ``decision_type: ship``. Reading the
    doc made this check cry wolf on exactly that, which is worse than useless in
    a tool whose whole job is to be believed — L2_103x10 R1 and M15_smoke_L0 R1
    are both IV-6 refusals (``decision cites unknown candidate``) that it called
    a lost ship.

    The journal's RoundEntry is what the orchestrator actually recorded. Rounds
    with no journal entry fall back to ship_outcomes rows, which is how a round
    that recorded ships and then never composed still gets caught.
    """
    out: set[int] = set()
    journal = run / "journal.md"
    seen_in_journal: set[int] = set()
    if journal.exists():
        text = journal.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"```json\s*(\{.*?\})\s*```", text, re.S):
            try:
                entry = json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
            if "round" not in entry or "action" not in entry:
                continue
            n = int(entry["round"])
            seen_in_journal.add(n)
            if entry.get("shipped_cids"):
                out.add(n)
    for o in _load(run / "data" / "ship_outcomes.json") or []:
        if isinstance(o, dict) and "round" in o:
            n = int(o["round"])
            if n not in seen_in_journal:
                out.add(n)
    return out


def check_reputation(run: Path, shipped: set[int]) -> Check:
    """A bucket window that never moves is either an honest no-ship campaign or
    P-15a. The discriminator is whether anything shipped at all."""
    data = _load(run / "reputation.json")
    if data is None:
        # The orchestrator only writes the file once there is something to
        # write, so a smoke run that never shipped legitimately has none.
        if not shipped:
            return Check("reputation", _OK, "absent, and nothing ever shipped — consistent")
        return Check("reputation", _BROKEN, "reputation.json missing or unparseable")
    total = sum(len(v) for v in data.values() if isinstance(v, list))
    if total:
        return Check("reputation", _OK, f"{total} record(s) across {len(data)} buckets")
    if not shipped:
        return Check("reputation", _OK, "empty, and nothing ever shipped — consistent")
    return Check(
        "reputation",
        _BROKEN,
        f"empty in every bucket while R{sorted(shipped)} shipped — the Planner saw a "
        f"flat unknown-boost all campaign (P-15a: a list bucket raised into a "
        f"swallowing except)",
    )


def check_hit_rates(run: Path) -> Check:
    """Predicted task ids that match nothing in task_history grade ``unknown``
    and drag hit_rate to a confident zero (P-15b)."""
    outcomes = _load(run / "data" / "ship_outcomes.json")
    if not isinstance(outcomes, list) or not outcomes:
        return Check("hit_rate", _OK, "no ships recorded")
    hist = run / "data" / "task_history.jsonl"
    known: set[str] = set()
    if hist.exists():
        for line in hist.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                tid = json.loads(line).get("task_id")
            except json.JSONDecodeError:
                continue
            if tid:
                known.add(str(tid))
    if not known:
        return Check("hit_rate", _DEGRADED, "task_history.jsonl empty — cannot check")

    bad: list[str] = []
    for o in outcomes:
        if not isinstance(o, dict) or o.get("not_scoreable"):
            continue
        preds = [str(p) for p in (o.get("predicted_tasks") or [])]
        unmatched = [p for p in preds if p not in known]
        if unmatched:
            bad.append(
                f"{o.get('ship_id')} R{o.get('round')}: {len(unmatched)}/{len(preds)} "
                f"unmatched (e.g. {unmatched[0]})"
            )
    if bad:
        return Check(
            "hit_rate",
            _BROKEN,
            "predicted ids absent from task_history — these score 0 no matter what "
            "the ship did: " + "; ".join(bad),
        )
    return Check("hit_rate", _OK, f"{len(outcomes)} ship(s), all predicted ids resolve")


def check_ships_landed(run: Path, shipped: set[int]) -> Check:
    """decision.md says ship; merged.yaml says whether it landed (P-9/P-16)."""
    dropped = [
        n
        for n in sorted(shipped)
        if not (run / f"R{n}" / "applied" / "merged.yaml").exists()
    ]
    if not dropped:
        return Check("ships landed", _OK, f"{len(shipped)} shipping round(s), all composed")
    last = max((int(p.name[1:]) for p in _round_dirs(run)), default=-1)
    tail = [n for n in dropped if n == last]
    mid = [n for n in dropped if n != last]
    if mid:
        return Check(
            "ships landed",
            _BROKEN,
            f"R{mid} decided to ship but produced no merged.yaml — those rounds ran "
            f"the previous config while the ledger attributed results to the ship",
        )
    return Check(
        "ships landed",
        _DEGRADED,
        f"R{tail} decided to ship at the campaign's last round and never composed; "
        f"unscoreable, not a loss (P-16 leaves it unscored)",
    )


def check_scoreboard_buckets(run: Path) -> Check:
    """``str()`` on a list bucket yields "['tools']", a rollup key that never
    aggregates with a real bucket name (P-15a)."""
    for cand in (run / "data" / "scoreboard.json", run / "scoreboard.json"):
        data = _load(cand)
        if data is None:
            continue
        keys = list((data.get("by_bucket") or {}).keys())
        malformed = [k for k in keys if k.startswith("[") or "," in k and " " in k]
        if malformed:
            return Check(
                "scoreboard buckets",
                _BROKEN,
                f"rollup keyed on stringified list(s) {malformed} — never aggregates",
            )
        return Check("scoreboard buckets", _OK, f"keys={keys or '(none)'}")
    return Check("scoreboard buckets", _OK, "no scoreboard.json")


def check_digest_coverage(run: Path) -> Check:
    """Stage P writes one digest per failing task; a round that produced none is
    a Planner reading an empty brief (P-8).

    This one has never fired across the archive — 51 runs, every round with a
    digests/ directory has digests in it. It is here because P-8 is a live
    registered defect, so the day it does fire is the day it matters.
    """
    empty = [
        rd.name
        for rd in _round_dirs(run)
        if (rd / "digests").is_dir() and not any((rd / "digests").glob("*.md"))
    ]
    if empty:
        return Check(
            "digest coverage",
            _BROKEN,
            f"R{empty} ran Stage P and produced no digest — the Planner read an "
            f"empty brief",
        )
    return Check("digest coverage", _OK, "every round with a digests/ dir has digests")


# ── GHX channels (M24 · P1) ───────────────────────────────────────────────────
#
# The module was born because four OFFICIAL feedback channels reported
# confidently while carrying nothing.  M23 then repeated the failure one layer
# up: GHX's own channels ran blind for a whole campaign — outcome stamps that
# grade structured empties ``ok`` (8.6× undercount), a sixth gate that answered
# 0 of 6 evaluations, cones nobody verified — and were found by hand-reading a
# finished run, which is the expensive way.  Same disease, same cure: one
# read-only question per channel.  Every check self-detects a GHX-off run
# (an L0 arm) and grades ``ok — GHX off`` rather than crying about an arm that
# never promised a graph.

_GATE_CHECKED_RE = re.compile(r"^- checked:\s*(True|False)\s*$", re.M)
# Prefix-match: preview is a single cell (pipes are stripped by both writers),
# return_type/len are the two cells after it. Deliberately does NOT anchor the
# row end, so it reads the official 7-column table and the graph-projected
# 8-column one (M24 P2) alike.
_LAYERA_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*[0-9a-f]{8}\s*\|[^|]*\|\s*(\w+)\s*\|\s*(\d+)\s*\|",
    re.M,
)


def _ghx_active(run: Path) -> bool:
    if any((rd / "graph_evidence").is_dir() for rd in _round_dirs(run)):
        return True
    for rd in reversed(_round_dirs(run)):
        if (rd / "sessions").is_dir():
            return any(rd.glob("sessions/aegis/*/graph/*_unfolded.jsonl"))
    return False


def check_ghx_u_coverage(run: Path, active: bool) -> Check:
    """Every batch session should have written a U; a thinning U silently thins
    every cone, signature and motif downstream of it."""
    if not active:
        return Check("ghx u coverage", _OK, "GHX off — skipped")
    for rd in reversed(_round_dirs(run)):
        # dirs only — every session dir has a sidecar .json FILE beside it, and
        # counting those halves the coverage into a false BROKEN (R14 smoke:
        # "103/206" that was really 103/103).
        sess = sorted(p for p in (rd / "sessions").glob("aegis/*") if p.is_dir())
        if not sess:
            continue
        with_u = sum(1 for s in sess if any((s / "graph").glob("*_unfolded.jsonl")))
        frac = with_u / len(sess)
        detail = f"{rd.name}: {with_u}/{len(sess)} sessions carry a U"
        if frac < 0.9:
            return Check("ghx u coverage", _BROKEN, detail + " — cones/motifs are starving")
        if frac < 1.0:
            return Check("ghx u coverage", _DEGRADED, detail)
        return Check("ghx u coverage", _OK, detail)
    return Check("ghx u coverage", _DEGRADED, "GHX active but no round has sessions to count")


def check_ghx_cone_presence(run: Path, active: bool) -> Check:
    """cone_sigs.json names the failing tasks the round materialised cones for;
    a cones/ dir thinner than that list means readers were handed dead links."""
    if not active:
        return Check("ghx cone presence", _OK, "GHX off — skipped")
    seen = False
    for rd in _round_dirs(run):
        sigs = _load(rd / "graph_evidence" / "cone_sigs.json")
        if not isinstance(sigs, dict):
            continue
        seen = True
        failing = sigs.get("failing") or {}
        cones = len(list((rd / "graph_evidence" / "cones").glob("*.md")))
        if failing and cones < len(failing):
            return Check(
                "ghx cone presence",
                _BROKEN,
                f"{rd.name}: cone_sigs lists {len(failing)} failing task(s) but cones/ holds {cones}",
            )
    if not seen:
        return Check("ghx cone presence", _DEGRADED, "GHX active but no cone_sigs.json anywhere")
    return Check("ghx cone presence", _OK, "every cone_sigs round has a full cones/ dir")


def check_ghx_gate_answered(run: Path, active: bool) -> Check:
    """The sixth gate's honesty contract records WHY it could not check; this
    channel makes a campaign of pure pass-throughs impossible to miss (M23
    measured: 6/6 ``checked=False``, resolver hardcoded None)."""
    if not active:
        return Check("ghx gate answered", _OK, "GHX off — skipped")
    answered = unanswered = 0
    for rd in _round_dirs(run):
        for md in (rd / "graph_evidence" / "gate").glob("*.md"):
            m = _GATE_CHECKED_RE.search(md.read_text(encoding="utf-8", errors="replace"))
            if m is None:
                continue
            if m.group(1) == "True":
                answered += 1
            else:
                unanswered += 1
    total = answered + unanswered
    if total == 0:
        return Check("ghx gate answered", _OK, "no gate evaluations recorded")
    if answered == 0 and total >= 3:
        return Check(
            "ghx gate answered",
            _DEGRADED,
            f"{total} evaluation(s), every one checked=False — the gate has never "
            f"answered; wire a real replay U (resolver returns None by design until then)",
        )
    return Check("ghx gate answered", _OK, f"{answered}/{total} evaluations answered")


def check_ghx_outcome_fidelity(run: Path, active: bool, sample: int = 12) -> Check:
    """U's outcome stamp vs the digest's message-plane empties, on the same batch.

    R{n}/digests describe batch n-1 whose U lives under R{n-1}/sessions — the
    pairing this module's own history got wrong once, encoded here so nobody
    repeats it.  Aggregate counts only (no row pairing): a >=3x undercount with
    >=10 digest empties means the graph is blind to the loop's dominant empty
    mechanism (M23 measured x6-14, WebFetch/Read/Browser all 0 on the U side).
    """
    if not active:
        return Check("ghx outcome fidelity", _OK, "GHX off — skipped")
    rounds = _round_dirs(run)
    for rd in reversed(rounds):
        n = int(rd.name[1:])
        digests = sorted((rd / "digests").glob("*.md"))
        prev = run / f"R{n-1}"
        if not digests or not (prev / "sessions").is_dir():
            continue
        digest_empty = 0
        u_empty = 0
        paired = 0
        for md in digests[:sample]:
            tid = md.stem
            rows = _LAYERA_ROW_RE.findall(md.read_text(encoding="utf-8", errors="replace"))
            u_files = sorted(prev.glob(f"sessions/aegis/*{tid}*/graph/*_unfolded.jsonl"))
            if not rows or not u_files:
                continue
            paired += 1
            digest_empty += sum(1 for _t, rt, _rl in rows if rt == "empty")
            for line in u_files[-1].read_text(encoding="utf-8", errors="replace").splitlines():
                if '"kind": "node"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(rec.get("static_node_id", "")).startswith("tool:") and rec.get("outcome") == "empty":
                    u_empty += 1
        if paired == 0:
            continue
        detail = f"{rd.name} sample n={paired}: digest-empty={digest_empty}, U-outcome-empty={u_empty}"
        if digest_empty >= 10 and digest_empty > 3 * max(u_empty, 1):
            return Check(
                "ghx outcome fidelity",
                _BROKEN,
                detail + f" — drift ×{digest_empty / max(u_empty, 1):.1f}, U is blind to "
                f"structured empties; join payload fields at projection time",
            )
        return Check("ghx outcome fidelity", _OK, detail)
    return Check("ghx outcome fidelity", _DEGRADED, "GHX active but no digest/U pair to sample")


def check_ghx_attribution_backend(run: Path, active: bool) -> Check:
    """With the graph backend live, ship evidence should sometimes grade
    direct/orphan; an all-joint ledger means signatures fell back to regex or
    were never graph-representable (prompt-only campaigns excepted — read the
    detail, not just the grade)."""
    if not active:
        return Check("ghx attribution", _OK, "GHX off — skipped")
    outcomes = _load(run / "data" / "ship_outcomes.json")
    if not isinstance(outcomes, list) or len(outcomes) < 2:
        return Check("ghx attribution", _OK, f"{0 if not outcomes else len(outcomes)} ship(s) — nothing to grade")
    grades: list[str] = []
    for o in outcomes:
        if isinstance(o, dict):
            grades.extend(str(v) for v in (o.get("evidence_per_task") or {}).values())
    if not grades:
        return Check("ghx attribution", _DEGRADED, "ships recorded but no evidence_per_task anywhere")
    non_joint = sum(1 for g in grades if g in ("direct", "orphan"))
    if non_joint == 0:
        return Check(
            "ghx attribution",
            _DEGRADED,
            f"{len(grades)} graded task(s) across {len(outcomes)} ship(s), all joint — "
            f"the graph backend never answered a signature",
        )
    return Check("ghx attribution", _OK, f"{non_joint}/{len(grades)} graded direct/orphan")


def audit(run: Path) -> list[Check]:
    shipped = _shipped_rounds(run)
    active = _ghx_active(run)
    return [
        check_reputation(run, shipped),
        check_hit_rates(run),
        check_ships_landed(run, shipped),
        check_scoreboard_buckets(run),
        check_digest_coverage(run),
        check_ghx_u_coverage(run, active),
        check_ghx_cone_presence(run, active),
        check_ghx_gate_answered(run, active),
        check_ghx_outcome_fidelity(run, active),
        check_ghx_attribution_backend(run, active),
    ]


def main(argv: list[str]) -> int:
    runs = [Path(a) for a in argv] or [Path(".")]
    failed = 0
    for run in runs:
        if not run.is_dir():
            continue
        checks = audit(run)
        worst = (
            _BROKEN
            if any(c.status == _BROKEN for c in checks)
            else _DEGRADED
            if any(c.status == _DEGRADED for c in checks)
            else _OK
        )
        if worst == _BROKEN:
            failed += 1
        print(f"\n{run.name}  [{worst}]")
        for c in checks:
            mark = {_OK: "  ok  ", _DEGRADED: " warn ", _BROKEN: " FAIL "}[c.status]
            print(f"  {mark} {c.channel:<20} {c.detail}")
    return failed


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
