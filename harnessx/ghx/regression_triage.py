# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Regression triage — the regression ledger gets a noise floor and a cone test (M24 · P3).

The official ``regressions.md`` is the mandate that killed good rounds: it
lists every worsened task, blames every same-round ship jointly, and demands
the next Evolver answer for all of it.  Measured on finished campaigns, that
mandate is mostly noise three separate ways:

* **no statistical zero point** — same-config transitions flip 8–9 tasks/round
  by themselves (L0 unchanged-pair envelope 9.3 ± 2.2); R16's "10 fresh
  regressions" was inside that envelope and still killed two candidates the
  Critic itself judged beneficial;
* **no per-ship scope** — a narrow processor ship is blamed for every flip in
  the batch; on L2 R9, 9 of the 12 tasks blamed on the guard ship had cones
  the guard's node never appears in (structurally out of reach);
* **grade inflation at k=1** — "ALL_PASS → ALL_FAIL" is one Bernoulli flip;
  11 of those same 12 had a pre-regression pass streak ≤ 2 (swingers
  reverting), and exactly one was a genuinely stable task breaking.

The triage appends a graph section and REWRITES the mandate paragraph:
the **statistical rule decides whether the wave is abnormal** (kill-grade),
the **cone rule decides which tasks a mechanical ship owes an answer for**
(targeting), and the **streak column decides which regressions are even
stable enough to reason about** (grading, and the counterfactual-replay
eligibility gate: streak ≥ 4).  Prompt/config ships have no mechanical node,
so the cone rule abstains for them out loud — for those the statistical rule
is the only honest instrument.

Seam: wraps ``write_regressions_md`` (orchestrator lazy-imports it per round,
so a module-attribute patch takes effect and restores cleanly).  The official
writer still runs first and its sections are preserved verbatim; the triage
only appends and replaces the final mandate paragraph.  Every fallback rung
returns the official file unchanged.

Flag: ``HARNESSX_GHX_REGRESSION_TRIAGE`` (call-time read, default off).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

FLAG = "HARNESSX_GHX_REGRESSION_TRIAGE"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})

# L0 (M22_L0_ghx0) unchanged-config adjacent pairs, hard p2f per transition:
# [8, 7, 13, 10, 11, 9, 7].  Used only until the run has >=3 no-ship
# transitions of its own to measure.
_FALLBACK_MEAN = 9.3
_FALLBACK_SD = 2.2
_FALLBACK_NOTE = "L0 documented envelope (M22, 7 unchanged-config transitions)"

_MANDATE_RE = re.compile(r"\*\*Required action\*\*:.*", re.S)
_COUNTERFACTUAL_STREAK = 4


def regression_triage_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


# ── inputs ────────────────────────────────────────────────────────────────────


def _task_flags_by_round(run_root: Path) -> dict:
    """task_id → {round → flags} from task_history.jsonl (k-aware)."""
    out: dict = {}
    path = run_root / "data" / "task_history.jsonl"
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        tid = row.get("task_id")
        if not tid:
            continue
        flags = row.get("passed_flags")
        if not isinstance(flags, list) or not flags:
            flags = [bool(row.get("passed", False))]
        out.setdefault(str(tid), {})[int(row.get("round", 0))] = [bool(b) for b in flags]
    return out


def _shipped_rounds(run_root: Path) -> set:
    out: set = set()
    path = run_root / "data" / "ship_outcomes.json"
    if not path.exists():
        return out
    try:
        for o in json.loads(path.read_text(encoding="utf-8")):
            if isinstance(o, dict) and "round" in o:
                out.add(int(o["round"]))
    except (json.JSONDecodeError, ValueError):
        pass
    return out


def _suspect_ships(run_root: Path, round_n: int) -> list:
    """[(ship_id, bucket)] for ships tagged round_n — the official suspects."""
    path = run_root / "data" / "ship_outcomes.json"
    if not path.exists():
        return []
    try:
        outcomes = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [
        (str(o.get("ship_id")), o.get("bucket"))
        for o in outcomes
        if isinstance(o, dict) and int(o.get("round", -1)) == round_n
    ]


def _load_manifest(run_root: Path, round_n: int, ship_id: str) -> dict | None:
    """Frontmatter of the shipped candidate's manifest, or None."""
    path = run_root / f"R{round_n}" / "candidates" / f"{ship_id}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    try:
        import yaml

        data = yaml.safe_load(text[3:end])
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _signature_nodes(run_root: Path, round_n: int, ship_id: str, bucket) -> set:
    """Every mechanical node this ship could appear as in a cone (alias set).

    Two producers, both needed:

    * the attribution signature (declared ``attribution_signature`` else the
      vendored bucket inference) → ``tool:<name>`` / ``proc:<class-slug>``;
    * ``file_changes`` ``.py`` stems → ``proc:py::_<stem>`` — because every
      EVOLVED processor is loaded through the config's ``file://…::Class``
      form, whose U node is minted from the FILE stem, and the class-name
      slug never matches it (real case: class slug
      ``proc:bash_windows_guard_v2_processor`` vs actual node
      ``proc:py::_bash_windows_guard_v2``).  Leading-underscore stems are
      session scratch files (``_verify_l1.py``) and are skipped.

    Empty set → no mechanical identity → the cone ruler abstains.
    """
    from .attribution_graph import (
        infer_signature,
        processor_file_uri_static_id,
        processor_static_id,
    )

    manifest = _load_manifest(run_root, round_n, ship_id)
    aliases: set = set()
    sig = infer_signature(
        bucket if isinstance(bucket, str) else None,
        manifest,
        (manifest or {}).get("attribution_signature") if isinstance(manifest, dict) else None,
    )
    if isinstance(sig, dict):
        if sig.get("type") == "tool_call" and sig.get("tool_name"):
            aliases.add(f"tool:{sig['tool_name']}")
        elif sig.get("type") == "processor_invocation" and (sig.get("class_name") or sig.get("tool_name")):
            cn = str(sig.get("class_name") or sig.get("tool_name"))
            aliases.add(processor_static_id(cn))
            aliases.add(processor_file_uri_static_id(cn))
    if isinstance(manifest, dict) and str(bucket) in ("processor", "tools"):
        for fc in manifest.get("file_changes") or []:
            if not isinstance(fc, dict):
                continue
            path = str(fc.get("path") or "")
            if not path.endswith(".py"):
                continue
            stem = Path(path).stem
            if not stem or stem.startswith("_"):
                continue
            if str(bucket) == "processor":
                aliases.add(f"proc:py::_{stem}")
            else:
                aliases.add("tool:" + "".join(p.title() for p in stem.split("_")))
    return aliases


def _cone_sigs(run_root: Path, evolve_round_n: int) -> dict | None:
    path = run_root / f"R{evolve_round_n}" / "graph_evidence" / "cone_sigs.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    failing = data.get("failing")
    return failing if isinstance(failing, dict) else None


def _base_nodes(sig_list) -> set:
    """Cone signature members with ``#outcome`` annotations stripped to base ids."""
    return {str(s).split("#", 1)[0] for s in (sig_list or [])}


# ── the three rulers ──────────────────────────────────────────────────────────


@dataclass
class Envelope:
    mean: float
    sd: float
    n: int
    source: str  # "run" | "fallback"

    def verdict(self, observed: int) -> str:
        return "EXCESS" if observed > self.mean + 2 * self.sd else "within-envelope"


def hard_p2f_envelope(run_root: Path, upto_round: int) -> Envelope:
    """ALL_PASS→ALL_FAIL count per no-ship transition, from this run's own
    history; the documented L0 constant until >=3 samples exist."""
    flags = _task_flags_by_round(run_root)
    shipped = _shipped_rounds(run_root)
    samples: list[int] = []
    for r in range(2, upto_round + 1):
        if r in shipped:
            continue  # config changed at r — not a noise sample
        count = 0
        for by_round in flags.values():
            prev, curr = by_round.get(r - 1), by_round.get(r)
            if prev and curr and all(prev) and not any(curr):
                count += 1
        if any(by_round.get(r) is not None for by_round in flags.values()):
            samples.append(count)
    if len(samples) >= 3:
        return Envelope(
            mean=statistics.mean(samples),
            sd=statistics.stdev(samples) if len(samples) > 1 else 0.0,
            n=len(samples),
            source="run",
        )
    return Envelope(mean=_FALLBACK_MEAN, sd=_FALLBACK_SD, n=len(samples), source="fallback")


def pass_streak(by_round: dict, before_round: int) -> int:
    """Consecutive all-pass rounds ending at ``before_round`` (inclusive)."""
    streak = 0
    r = before_round
    while r >= 0:
        flags = by_round.get(r)
        if flags and all(flags):
            streak += 1
            r -= 1
        else:
            break
    return streak


@dataclass
class ShipTriage:
    ship_id: str
    bucket: str
    nodes: set = field(default_factory=set)  # alias set; empty → cone ruler abstains
    in_cone: list = field(default_factory=list)
    out_of_cone: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)  # regressed task with no cone
    ubiquitous: bool = False  # nodes sit in every sampled cone → in-cone is vacuous


@dataclass
class TriageResult:
    round_n: int
    evolve_round_n: int
    observed_hard: int
    envelope: Envelope
    ships: list = field(default_factory=list)  # list[ShipTriage]
    streaks: dict = field(default_factory=dict)  # task_id → int
    cone_data_available: bool = False

    @property
    def stat_verdict(self) -> str:
        return self.envelope.verdict(self.observed_hard)

    def counterfactual_eligible(self) -> list:
        return sorted(t for t, s in self.streaks.items() if s >= _COUNTERFACTUAL_STREAK)


def _nodes_are_ubiquitous(nodes: set, cones: dict, regressed: set) -> bool:
    """True when the ship's nodes sit in EVERY sampled non-regressed task's cone.

    Discovered live (M25_103x16 R2, 08-22): a ship on an always-firing processor
    (``step_countdown``) scored in-cone 12/12 — not because it reached those
    tasks specifically, but because such a node is in every cone there is. Cone
    membership is then vacuous exactly the way a declared-but-always-firing
    attribution signature is (see ``attribution_backfill._is_discriminative``,
    same disease, same cure): the ruler must ABSTAIN rather than rubber-stamp.

    Unlike the attribution guard (which samples, because each check costs a U
    load), every cone signature is already in memory here — so this checks ALL
    non-regressed tasks: one silent cone anywhere is enough to prove the nodes
    discriminate. No non-regressed cone at all → False (cannot prove vacuity,
    so the ruler keeps its normal reading).
    """
    checked = 0
    for tid in sorted(cones):
        if tid in regressed:
            continue
        sig = cones.get(tid)
        if sig is None:
            continue
        if not (nodes & _base_nodes(sig)):
            return False  # silent somewhere → genuinely discriminative
        checked += 1
    return checked > 0


def compute_triage(run_root: Path, round_n: int, evolve_round_n: int) -> TriageResult:
    from harnessx.aegis.data.regressions import detect_regressions

    regressions = detect_regressions(run_root, round_n)
    hard = [r for r in regressions if r.get("grade") == "regressed_hard"]
    flags = _task_flags_by_round(run_root)

    result = TriageResult(
        round_n=round_n,
        evolve_round_n=evolve_round_n,
        observed_hard=len(hard),
        envelope=hard_p2f_envelope(run_root, round_n),
        streaks={
            r["task_id"]: pass_streak(flags.get(r["task_id"], {}), round_n - 1) for r in hard
        },
    )

    cones = _cone_sigs(run_root, evolve_round_n)
    result.cone_data_available = cones is not None
    for ship_id, bucket in _suspect_ships(run_root, round_n):
        st = ShipTriage(
            ship_id=ship_id,
            bucket=str(bucket),
            nodes=_signature_nodes(run_root, round_n, ship_id, bucket),
        )
        if st.nodes and cones is not None:
            st.ubiquitous = _nodes_are_ubiquitous(st.nodes, cones, {r["task_id"] for r in hard})
            for r in hard:
                tid = r["task_id"]
                sig = cones.get(tid)
                if sig is None:
                    st.unresolved.append(tid)
                elif st.nodes & _base_nodes(sig):
                    st.in_cone.append(tid)
                else:
                    st.out_of_cone.append(tid)
        result.ships.append(st)
    return result


# ── rendering ─────────────────────────────────────────────────────────────────


def render_triage_section(t: TriageResult) -> str:
    L: list[str] = ["## Graph triage (M24 — three rulers, three different decisions)", ""]

    env = t.envelope
    src = f"this run's {env.n} no-ship transition(s)" if env.source == "run" else _FALLBACK_NOTE
    L.append(
        f"- **Statistical ruler (kill decisions)**: observed hard regressions = "
        f"**{t.observed_hard}** vs same-config expectation {env.mean:.1f} ± {env.sd:.1f} "
        f"({src}) → **{t.stat_verdict}**."
    )
    if t.stat_verdict == "within-envelope":
        L.append(
            "  A wave inside the envelope is what an unchanged config does on its own; "
            "it is NOT evidence against this round's ships and MUST NOT drive a no_op by itself."
        )
    else:
        L.append(
            "  This wave exceeds the same-config envelope — treat it as a real signal "
            "and weigh the cone ruler below for ownership."
        )
    L.append("")

    L.append("- **Cone ruler (targeting — which ship owes which task an answer)**:")
    if not t.ships:
        L.append("  - no ships tagged this round — nothing to scope.")
    for s in t.ships:
        if not s.nodes:
            L.append(
                f"  - `{s.ship_id}` (bucket=`{s.bucket}`): no mechanical node — the cone "
                f"ruler abstains; the statistical ruler above is the only honest instrument "
                f"for this ship."
            )
        elif not t.cone_data_available:
            L.append(
                f"  - `{s.ship_id}` (nodes `{', '.join(sorted(s.nodes))}`): cone_sigs.json unavailable — cannot scope."
            )
        elif s.ubiquitous:
            L.append(
                f"  - `{s.ship_id}` (nodes `{', '.join(sorted(s.nodes))}`): **cone ruler ABSTAINS — "
                f"these nodes sit in every sampled cone (always-firing), so the raw in-cone "
                f"{len(s.in_cone)}/{len(s.in_cone) + len(s.out_of_cone)} carries no targeting "
                f"information.** Presence everywhere is not reach; do not read it as this ship "
                f"owing these tasks an answer. Use the statistical and streak rulers here."
            )
        else:
            L.append(
                f"  - `{s.ship_id}` (nodes `{', '.join(sorted(s.nodes))}`): **in-cone {len(s.in_cone)}** / "
                f"out-of-cone {len(s.out_of_cone)}"
                + (f" / no-cone {len(s.unresolved)}" if s.unresolved else "")
            )
            if s.in_cone:
                L.append("    - in-cone (this ship owes these an answer): " + ", ".join(f"`{x}`" for x in s.in_cone))
            if s.out_of_cone:
                L.append(
                    "    - out-of-cone (structurally out of this ship's reach — do not "
                    "spend candidates on them in this ship's name): "
                    + ", ".join(f"`{x}`" for x in s.out_of_cone)
                )
    L.append("")

    if t.streaks:
        L.append("- **Streak ruler (grading — how stable was each task before it broke)**:")
        L.append("")
        L.append("  | task_id | pre-regression pass streak | reading |")
        L.append("  |---|---|---|")
        for tid in sorted(t.streaks, key=lambda x: -t.streaks[x]):
            s = t.streaks[tid]
            reading = (
                "stable task actually broken — investigate"
                if s >= _COUNTERFACTUAL_STREAK
                else "swinger reverting to its base state — expected churn"
            )
            L.append(f"  | `{tid}` | {s} | {reading} |")
        L.append("")
        eligible = t.counterfactual_eligible()
        L.append(
            f"- **Counterfactual eligibility (streak ≥ {_COUNTERFACTUAL_STREAK})**: "
            + (", ".join(f"`{x}`" for x in eligible) if eligible else "none — a removal replay on swingers is a coin flip dressed as causal evidence.")
        )
        L.append("")
    return "\n".join(L)


def render_mandate(t: TriageResult) -> str:
    in_cone_all = sorted({tid for s in t.ships for tid in s.in_cone})
    if t.stat_verdict == "within-envelope":
        body = (
            "**Required action (triage-aware)**: The hard-regression count is inside the "
            "same-config noise envelope, so the wave as a whole requires NO per-task "
            "response and is NOT grounds to reject this round's candidates. "
        )
        if in_cone_all:
            body += (
                "Ships with a mechanical node still owe an answer for their in-cone tasks ("
                + ", ".join(f"`{x}`" for x in in_cone_all)
                + ") — address those or state why they are acceptable. "
            )
        body += (
            "Out-of-cone flips are expected churn: candidates must NOT be rejected for "
            "leaving them unaddressed."
        )
        return body
    body = (
        "**Required action (triage-aware)**: The hard-regression count EXCEEDS the "
        "same-config envelope — this wave is a real signal. Evolver MUST address the "
        "in-cone tasks of mechanical ships"
    )
    if in_cone_all:
        body += " (" + ", ".join(f"`{x}`" for x in in_cone_all) + ")"
    body += (
        ", and for node-less (prompt/config) suspects either iterate from the suspect "
        "ship or state why the regression is acceptable. Out-of-cone tasks still count "
        "toward the excess but no single mechanical ship owes them individually. "
        "Critic verifies in portfolio_audit."
    )
    return body


def triage_markdown(official_md: str, run_root: Path, round_n: int, evolve_round_n: int) -> str:
    """Official regressions.md → triaged version.  Any failure → official unchanged."""
    try:
        t = compute_triage(Path(run_root), round_n, evolve_round_n)
    except Exception:
        return official_md
    section = render_triage_section(t)
    mandate = render_mandate(t)
    if _MANDATE_RE.search(official_md):
        return _MANDATE_RE.sub(lambda _m: section + "\n" + mandate, official_md, count=1)
    # empty-regression files carry no mandate paragraph; still append the rulers
    return official_md.rstrip() + "\n\n" + section + "\n" + mandate + "\n"


# ── seam ──────────────────────────────────────────────────────────────────────


# The vendored writer as it was BEFORE the seam patched it.  Set by the
# installer; the lazy fallback covers a direct (uninstalled) call.  Reading the
# module attribute inside the wrapper would find the wrapper itself — the
# recursion the first test run demonstrated.
_ORIGINAL_WRITE = None


def write_regressions_md_triaged(
    run_root,
    round_n: int,
    out_path=None,
    *,
    for_evolve_round_n: int | None = None,
):
    """Drop-in for the vendored ``write_regressions_md``: official file first,
    then the triage post-pass on the same path."""
    _official = _ORIGINAL_WRITE
    if _official is None:
        from harnessx.aegis.data.regressions import write_regressions_md as _official

    path = _official(run_root, round_n, out_path, for_evolve_round_n=for_evolve_round_n)
    try:
        official_md = Path(path).read_text(encoding="utf-8")
        evolve = for_evolve_round_n if for_evolve_round_n is not None else round_n
        Path(path).write_text(
            triage_markdown(official_md, Path(run_root), round_n, evolve), encoding="utf-8"
        )
    except Exception:
        pass  # official file already on disk — never trade it for a triage crash
    return path


@contextlib.contextmanager
def install_regression_triage():
    """Patch the module attribute the orchestrator lazy-imports each round."""
    global _ORIGINAL_WRITE
    import harnessx.aegis.data.regressions as _reg

    original = _reg.write_regressions_md
    _ORIGINAL_WRITE = original
    _reg.write_regressions_md = write_regressions_md_triaged
    try:
        yield
    finally:
        _reg.write_regressions_md = original
        _ORIGINAL_WRITE = None
