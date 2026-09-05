# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Graph-conditioned runtime interventions — the loop's first IN-RUN edit surface (M26).

Everything the evolution loop could change until now was static: a prompt, a
processor, a tool, applied uniformly to every step of every task of the next
batch.  The campaign data says the remaining failures are not static-shaped.
With the evidence plane restored, 24 of 33 residual failures carry NO motif —
content fetched, read, and the answer still wrong — and the paired swinger
analysis says failing runs are the LONG ones (+4.5 steps over the same task's
passing runs, 47/56 tasks; 217 ran-longer-and-still-failed vs 66 gave-up-early).
The failure happens mid-run, on a path, and the only medicine that could reach
it so far was a countdown that ends the run sooner.

This module is a different kind of edit: a **policy** — declarative rules,
evaluated during the run against the live unfolded graph, that fire targeted
actions when the run enters a known death signature.

    rule := when(graph predicate over live U) -> then(action), scoped by
            min_step / max_fires

Why rules-as-data instead of another evolved processor:

* **The rules are this processor's ``rules`` param**, so they serialize into
  the round config and the Evolver edits policy with the ``mutate_params``
  edit it already has — no new proposal bucket, and the scope gate prices a
  policy change exactly as it prices any other node mutation.
* **A predicate is replayable.**  Arbitrary evolved code cannot be tested
  without spending a batch; a declarative predicate can be evaluated offline
  against last round's recorded U's, so a gate can state "this rule would have
  fired on exactly these k tasks" before a dollar is spent
  (:func:`fired_on_recorded_u`).
* **Firing is attributable for free.**  The injection modifies the
  before_model event, so the ProcessorChain diff stamps ``intervention`` on
  this invocation in U — the fire lands in the same channel attribution
  already reads, selective by construction (no vacuity problem).

v1 predicates — the two death signatures the campaign actually measured:

* ``search_without_page`` — N snippet-grade searches since the last page-grade
  read.  Snippets are this bed's dominant carried payload (83%) and its own
  motif library rules them out as grounding; a run accumulating searches
  without ever committing to a page is wandering, not researching.
* ``consecutive_empty`` — the last N tool calls all returned empty/error.  The
  feed line of the (true-plane) ``empty_consumed`` family: nothing is coming
  back and the run keeps pulling.

v1 action: ``steer`` — inject one marked user message before the next model
call (the StepCountdown seam: model-visible, nothing persisted back into
history).  Deliberately not in v1: context surgery and forced restarts —
actions that rewrite state need the probation-gate story first.

No recorder installed (flag off, non-GHX arm) → every hook is a pass-through.
"""

from __future__ import annotations

import dataclasses
import logging

from ..core.events import BeforeModelEvent, Message
from ..core.processor import MultiHookProcessor

_LOG = logging.getLogger(__name__)

#: Stable marker prefixing every injected line — recognisable to the model,
#: greppable in trajectories, and the dedup key that keeps one firing from
#: stacking into a chant.
POLICY_MARKER = "[graph-policy]"

_PAGE_GRADE = frozenset({"tool:WebFetch", "tool:Browser", "tool:Read", "tool:SmartFetch"})
_SNIPPET_GRADE = frozenset({"tool:WebSearch"})
_EMPTYISH = frozenset({"empty", "error"})


def _tool_nodes(nodes) -> list:
    return [n for n in nodes if str(getattr(n, "static_node_id", "")).startswith("tool:")]


def _base(node) -> str:
    # tool:Bash#empty style suffixes never appear on live nodes, but cost nothing to strip.
    return str(getattr(node, "static_node_id", "")).split("#", 1)[0]


# ── predicates ───────────────────────────────────────────────────────────────
# Each takes (live_nodes, params) and returns bool. Pure, total, and cheap —
# they run before every model call.


def _pred_search_without_page(nodes, params: dict) -> bool:
    """>= ``searches`` snippet-grade calls since the last page-grade call."""
    floor = int(params.get("searches", 6))
    streak = 0
    for n in reversed(_tool_nodes(nodes)):
        b = _base(n)
        if b in _PAGE_GRADE:
            break
        if b in _SNIPPET_GRADE:
            streak += 1
            if streak >= floor:
                return True
    return streak >= floor


def _pred_consecutive_empty(nodes, params: dict) -> bool:
    """The last ``count`` tool calls all came back empty/error."""
    floor = int(params.get("count", 3))
    tools = _tool_nodes(nodes)
    if len(tools) < floor:
        return False
    return all(str(getattr(n, "outcome", "")) in _EMPTYISH for n in tools[-floor:])


# ── the graph-native predicate ───────────────────────────────────────────────
# The two counters above are honest about what they are: expressible as a
# plain local-state processor, and the loop has in fact evolved processors of
# that family (the empty-guard line).  What a worker-local processor CANNOT
# have is anything beyond its own run: this task's cross-round record (the
# official loop fresh-sessions every role by design) and the other 102 tasks'
# statistics.  Both live only on the graph plane — which is what this
# predicate consumes.

#: How much of the campaign a signature node may appear in before it stops
#: meaning anything.  The cone ruler and the attribution guard each had to
#: learn this the hard way (always-on framework nodes grade everything
#: everywhere); here the lesson is built in from the start.
_UBIQUITY_CEILING = 0.9

_SIG_CACHE: dict = {}


def _load_signature_history(run_dir: str):
    """``{task_id: [most-recent-first failing sigs]}`` + node ubiquity, cached.

    Read from the ``R*/graph_evidence/cone_sigs.json`` files GHX already writes
    each round; the cache key includes which files exist, so a new round's file
    refreshes the picture without a restart.
    """
    from pathlib import Path

    root = Path(run_dir)
    files = tuple(sorted(root.glob("R*/graph_evidence/cone_sigs.json")))
    key = (str(root), files)
    hit = _SIG_CACHE.get(key)
    if hit is not None:
        return hit
    import json as _json
    import re as _re

    def _rnd(p) -> int:
        m = _re.search(r"R(\d+)", p.parent.parent.name)
        return int(m.group(1)) if m else -1

    fails: dict = {}
    node_seen: dict = {}
    sig_count = 0
    for p in sorted(files, key=_rnd, reverse=True):
        try:
            j = _json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — one bad round file never blanks history
            continue
        for side in ("failing", "passing"):
            for sig in (j.get(side) or {}).values():
                sig_count += 1
                for n in set(sig):
                    node_seen[n] = node_seen.get(n, 0) + 1
        for tid, sig in (j.get("failing") or {}).items():
            fails.setdefault(str(tid), []).append(frozenset(sig))
    ubiquitous = {
        n for n, c in node_seen.items() if sig_count and c / sig_count >= _UBIQUITY_CEILING
    }
    out = (fails, ubiquitous)
    _SIG_CACHE.clear()  # one run dir per process; never grow unbounded
    _SIG_CACHE[key] = out
    return out


def _pred_own_death_cone(nodes, params: dict, ctx: dict | None = None) -> bool:
    """This run is walking into ITS OWN task's recorded death cone.

    Fires when (a) this task's failing cone signatures exist for at least
    ``min_streak`` recent rounds, (b) those signatures share a discriminative
    core (their intersection minus campaign-ubiquitous nodes — a signature of
    always-on nodes matches every run ever and must never fire), and (c) the
    live run has already touched at least ``overlap`` of that core.

    Everything here is graph-plane: the task identity comes from the recorder's
    session id, the history from cone_sigs.json across rounds, the live shape
    from U.  A worker-local processor has none of the three.
    """
    task_id = str((ctx or {}).get("task_id") or "")
    run_dir = str(params.get("run_dir") or "")
    if not task_id or not run_dir:
        return False
    fails, ubiquitous = _load_signature_history(run_dir)
    sigs = fails.get(task_id) or []
    min_streak = int(params.get("min_streak", 3))
    if len(sigs) < min_streak:
        return False
    core = frozenset.intersection(*sigs[:min_streak]) - ubiquitous
    if not core:
        return False  # the death cone has no discriminative shape — abstain
    live = {_base(n) for n in _tool_nodes(nodes)}
    overlap = float(params.get("overlap", 0.8))
    return len(core & live) / len(core) >= overlap


PREDICATES = {
    "search_without_page": _pred_search_without_page,
    "consecutive_empty": _pred_consecutive_empty,
    "own_death_cone": _pred_own_death_cone,
}

#: Predicates that receive the evaluation context (task identity) as a third
#: argument. The counters stay two-argument — their whole point is that they
#: need nothing beyond the live nodes.
_CTX_PREDICATES = frozenset({"own_death_cone"})


def rule_fires(rule: dict, nodes, step: int, ctx: dict | None = None) -> bool:
    """Does ``rule`` fire on this live node list at this step?

    Unknown predicate names never fire — an Evolver typo must degrade to a
    no-op rule, not to an exception inside every model call, and not to a rule
    that fires everywhere.
    """
    if step < int(rule.get("min_step", 0)):
        return False
    when = rule.get("when") or {}
    name = str(when.get("predicate", ""))
    fn = PREDICATES.get(name)
    if fn is None:
        return False
    try:
        if name in _CTX_PREDICATES:
            return bool(fn(nodes, when, ctx))
        return bool(fn(nodes, when))
    except Exception:  # noqa: BLE001 — a broken predicate is a silent no, never a crash
        return False


def _task_id_from_session(session_id: str) -> str:
    """``aegis/R10-<uuid>`` → ``<uuid>`` (the GAIA session naming convention)."""
    return str(session_id or "").split("-", 1)[1] if "-" in str(session_id or "") else ""


def fired_on_recorded_u(rule: dict, u) -> bool:
    """Would ``rule`` have fired at any point of a RECORDED run?

    The offline replay half: evaluated against every prefix of the U's tool
    nodes, exactly as the live evaluation would have seen them grow — task
    identity resolved from the U's own session id, the same source the live
    evaluation uses.  This is what makes a policy edit gateable before it
    costs a batch — and what arbitrary evolved code cannot offer.
    """
    nodes = sorted(u.nodes, key=lambda n: n.ordinal)
    tools = _tool_nodes(nodes)
    ctx = {"task_id": _task_id_from_session(getattr(u, "session_id", ""))}
    for i in range(1, len(tools) + 1):
        prefix_last = tools[i - 1]
        step = int(getattr(prefix_last, "step", 0))
        if rule_fires(rule, tools[:i], step, ctx):
            return True
    return False


class RuntimePolicyProcessor(MultiHookProcessor):
    """Evaluate the policy rules before each model call; steer when one fires.

    ``rules`` is the whole policy and the whole edit surface::

        RuntimePolicyProcessor(rules=[
            {"name": "stop-search-thrash",
             "when": {"predicate": "search_without_page", "searches": 6},
             "then": {"action": "steer",
                      "text": "You have searched repeatedly without opening any result. "
                              "Pick the most promising source found so far and fetch it now."},
             "min_step": 4, "max_fires": 1},
        ])
    """

    def __init__(self, rules: list | None = None):
        self.rules = list(rules or [])
        self._fires: dict = {}

    async def on_task_start(self, event):
        self._fires = {}
        yield event

    async def on_before_model(self, event: BeforeModelEvent):
        if not self.rules:
            yield event
            return
        from ..core.attribution import current_unfold_recorder

        rec = current_unfold_recorder()
        if rec is None:  # non-GHX arm / U off — behave as if absent
            yield event
            return
        nodes = rec.live_nodes()
        step = int(getattr(event, "step_id", 0) or 0)
        ctx = {"task_id": _task_id_from_session(getattr(rec, "session_id", ""))}
        for idx, rule in enumerate(self.rules):
            if not isinstance(rule, dict):
                continue
            fired = self._fires.get(idx, 0)
            if fired >= int(rule.get("max_fires", 1)):
                continue
            if not rule_fires(rule, nodes, step, ctx):
                continue
            then = rule.get("then") or {}
            if str(then.get("action", "steer")) != "steer":
                continue  # v1 vocabulary ends at steer; unknown actions are no-ops
            text = str(then.get("text", "")).strip()
            if not text:
                continue
            self._fires[idx] = fired + 1
            line = f"{POLICY_MARKER} {text}"
            name = str(rule.get("name", f"rule{idx}"))
            _LOG.info("runtime policy: rule %r fired at step %d", name, step)
            # One marked line, refreshed rather than stacked, on the same
            # injection seam StepCountdown uses: model-visible this call,
            # never persisted back into history.
            msgs = event.messages
            if msgs and getattr(msgs[-1], "role", "") == "user" and POLICY_MARKER in str(
                getattr(msgs[-1], "content", "")
            ):
                new_last = dataclasses.replace(msgs[-1], content=line)
                yield dataclasses.replace(event, messages=msgs[:-1] + (new_last,))
            else:
                yield dataclasses.replace(
                    event, messages=msgs + (Message(role="user", content=line),)
                )
            return
        yield event


__all__ = [
    "POLICY_MARKER",
    "PREDICATES",
    "RuntimePolicyProcessor",
    "fired_on_recorded_u",
    "rule_fires",
]
