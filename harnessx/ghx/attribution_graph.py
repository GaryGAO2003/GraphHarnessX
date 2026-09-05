# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Graph-backed signature check (module G2, piece 1).

The vendored official attributor (:mod:`harnessx.aegis.data.attribution`) answers
"did this ship's mechanical signature fire on a task?" by **regex-parsing digest
markdown** — ``_TOOL_COUNT_RE`` over a ``tool_call_counts`` table.  A trajectory
that merely *looks* like it invoked a tool (the string is present in the text)
satisfies that check.

The unfolded graph U records the same fact **structurally**: a ``tool:<name>``
invocation node exists in the run's U with N occurrences, or it does not.  This
module answers the identical direct/orphan/joint question by counting those nodes
instead of parsing text — an answer that cannot be forged by evidence-shaped
prose.

Signature schema (mirrors the vendored ``attribution.py`` docstring)::

    {type: tool_call, tool_name: <str>, expected_min_calls: <int>}   # tools bucket
    {type: processor_invocation, class_name: <str>}                  # processor bucket
    None                                                             # prompt/config → joint

``tool_call`` is answered by counting ``tool:<name>`` nodes.  ``processor_invocation``
is answered by counting ``proc:<slug>`` invocation nodes (M23 — U has recorded
processor invocations with graph static ids all along; abstaining was leaving an
answerable question unanswered, and every disaster ship in M22 was orphan-heavy in
ways this backend could have said out loud).  The class name is slugged through the
SAME :func:`harnessx.graph.snapshot._compute_slug` the graph uses to mint node ids,
so the two sides cannot drift.  For unknown types and the prompt/config buckets (no
signature at all), the result says so — it records ``backend="none"`` with a reason,
per the 4e0810f discipline of reporting what was actually answered rather than
guessing.  ``min_calls`` is read from ``expected_min_calls`` (official field) or
``min_calls`` (alias), defaulting to the same floor the vendored code uses.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..graph.unfold import UnfoldedGraph

# The floor the vendored attributor uses: a single accidental call does not credit
# a ship. Kept in sync with ``attribution._DEFAULT_MIN_CALLS``.
_DEFAULT_MIN_CALLS = 1

# The three official labels (attribution.py). We speak the same vocabulary so a
# downstream consumer never has to translate between the text backend and this
# graph backend.
DIRECT = "direct"
ORPHAN = "orphan"
JOINT = "joint"

# Which backend produced the answer. ``graph`` = counted ``tool:<name>`` nodes;
# ``none`` = the graph has no representation for this signature type, so it did
# NOT answer (the label is joint-by-honest-abstention, not a measured result).
BACKEND_GRAPH = "graph"
BACKEND_NONE = "none"

_TOOL_CALL = "tool_call"
_PROC_INVOCATION = "processor_invocation"


@dataclass(frozen=True)
class GraphSignatureResult:
    """The graph backend's answer for one signature against one U.

    ``label`` is one of the official ``direct``/``orphan``/``joint`` strings.
    ``backend`` states who answered: ``graph`` (a real node count) or ``none``
    (no graph representation — the label is an honest abstention, never a guess).
    ``fired`` is ``True``/``False`` only when the graph answered; ``None`` marks
    "not answered by this backend". The ``tool_name``/``count``/``min_calls`` fields
    carry the evidence a reader (or a mutation test) can check.
    """

    label: str
    backend: str
    reason: str
    fired: bool | None = None
    tool_name: str = ""
    count: int = 0
    min_calls: int = 0

    @property
    def answered_by_graph(self) -> bool:
        """True only when a ``tool:<name>`` node count actually decided the label."""
        return self.backend == BACKEND_GRAPH


def count_tool_invocations(u: UnfoldedGraph, tool_name: str) -> int:
    """Number of ``tool:<tool_name>`` invocation nodes in ``u``.

    A tool call mints one U node with ``static_node_id == f"tool:{tool_name}"`` and
    ``hook == "tool"`` (see :meth:`UnfoldRecorder.record_tool_invocation`).  Each
    such node is one distinct invocation (unique ordinal), so counting them is the
    structural equivalent of the vendored ``tool_call_counts[tool_name]``.
    """
    target = f"tool:{tool_name}"
    return sum(1 for n in u.nodes if n.static_node_id == target and n.hook == "tool")


def processor_static_id(class_name: str) -> str:
    """The ``proc:<slug>`` static node id for a processor class name.

    Accepts a bare class name (``StepCountdownProcessor``), a dotted path, or an
    already-prefixed ``proc:`` id (returned unchanged).  The slug computation is
    imported from the graph authority — never re-implemented — so a rename there
    cannot silently desynchronise this backend.
    """
    name = str(class_name or "")
    if name.startswith("proc:"):
        return name
    from ..graph.snapshot import _compute_slug

    return f"proc:{_compute_slug(name)}"


def processor_file_uri_static_id(class_name: str) -> str:
    """The ``proc:py::_<snake>`` id a FILE-URI-loaded processor mints.

    The slug authority splits the target on its LAST dot, so
    ``file://…/mod.py::ClassName`` slugs as ``py::ClassName`` →
    ``py::_class_name`` — the ``py::_`` prefix is an artifact of ``.py::``,
    and the tail is snake(ClassName), never the file stem (M23's
    ``…_guard_v2`` matched the stem only because the class was named
    ``…GuardV2``).  Derived through the same authority as
    :func:`processor_static_id` so a slug change cannot desynchronise it.
    """
    name = str(class_name or "")
    if name.startswith("proc:"):
        return name
    from ..graph.snapshot import _compute_slug

    short = name.rsplit(".", 1)[-1]
    return f"proc:{_compute_slug('py::' + short)}"


def count_processor_invocations(u: UnfoldedGraph, class_name: str) -> int:
    """Number of ``proc:<slug>`` invocation nodes for ``class_name`` in ``u``.

    A processor dispatch mints one U node per firing with ``static_node_id`` equal
    to its graph node id (``proc:<slug>``); counting them is the structural
    equivalent of "did this processor actually run, and how often".
    """
    target = processor_static_id(class_name)
    return sum(1 for n in u.nodes if n.static_node_id == target)


def _resolve_min_calls(signature: dict) -> int:
    """Read the invocation floor from ``expected_min_calls`` (official) or the
    ``min_calls`` alias; fall back to the vendored default on absent/garbage."""
    for key in ("expected_min_calls", "min_calls"):
        if signature.get(key) is not None:
            try:
                return int(signature[key])
            except (TypeError, ValueError):
                continue
    return _DEFAULT_MIN_CALLS


def check_signature_in_u(signature: dict | None, u: UnfoldedGraph) -> GraphSignatureResult:
    """Answer fired/not-fired for ``signature`` against ``u`` by node existence.

    - ``tool_call`` with a ``tool_name`` → counted structurally: ``direct`` when the
      count meets the floor, ``orphan`` when it does not (both ``backend="graph"``).
    - No signature (prompt/config bucket) → ``joint`` by definition, ``backend="none"``.
    - ``processor_invocation`` / unknown type / ``tool_call`` missing its name → no
      ``tool:<name>`` representation → ``joint`` with ``backend="none"`` and a reason
      that names why the graph did not answer. Never a guess.
    """
    if not signature:
        return GraphSignatureResult(
            label=JOINT,
            backend=BACKEND_NONE,
            fired=None,
            reason="no mechanical signature (prompt/config bucket) — joint by definition",
        )

    sig_type = str(signature.get("type") or "")
    if sig_type == _TOOL_CALL:
        tool_name = str(signature.get("tool_name") or "")
        if not tool_name:
            return GraphSignatureResult(
                label=JOINT,
                backend=BACKEND_NONE,
                fired=None,
                reason="tool_call signature carries no tool_name — the graph cannot answer it",
            )
        min_calls = _resolve_min_calls(signature)
        count = count_tool_invocations(u, tool_name)
        if count >= min_calls:
            return GraphSignatureResult(
                label=DIRECT,
                backend=BACKEND_GRAPH,
                fired=True,
                tool_name=tool_name,
                count=count,
                min_calls=min_calls,
                reason=f"tool:{tool_name} present in U with {count} invocation(s) (>= {min_calls})",
            )
        return GraphSignatureResult(
            label=ORPHAN,
            backend=BACKEND_GRAPH,
            fired=False,
            tool_name=tool_name,
            count=count,
            min_calls=min_calls,
            reason=f"tool:{tool_name} not present in U at the required floor ({count} < {min_calls})",
        )

    if sig_type == _PROC_INVOCATION:
        # Evolvers write the class name under class_name OR (frequently) tool_name —
        # M22's ledgers carry both spellings, so both are accepted here.
        class_name = str(signature.get("class_name") or signature.get("tool_name") or "")
        if not class_name:
            return GraphSignatureResult(
                label=JOINT,
                backend=BACKEND_NONE,
                fired=None,
                reason="processor_invocation signature carries no class name — the graph cannot answer it",
            )
        min_calls = _resolve_min_calls(signature)
        target = processor_static_id(class_name)
        # A processor answers under BOTH id forms: module-path loading mints
        # ``proc:<snake(Class)>``, file-URI loading mints ``proc:py::_<snake(Class)>``
        # (the ``py::_`` is an artifact of the slug authority splitting on the
        # last dot).  Counting the module form alone graded every working
        # evolved (file-URI) processor orphan — and would have made the replay
        # gate refuse working candidates (caught by smoke #1's offline check).
        # ``node_aliases`` stays as a caller-supplied extension point.
        aliases = (
            {target, processor_file_uri_static_id(class_name)}
            | {str(a) for a in (signature.get("node_aliases") or [])}
        )
        # Presence cannot attribute a processor.  A processor is dispatched on
        # every firing of its hook, so a '*'- or before_model-hook processor sits
        # in 100% of the batch's graphs by construction — measured on M25 R10,
        # every one of the ten processors present ran 5922 times across 103/103
        # tasks.  Grading on that says "direct" for every predicted task of every
        # processor ship, which is why the vacuity guard upstream then had to
        # throw the whole answer away, which is how the ledger came to read
        # 0 direct on ten consecutive ships.
        #
        # ``intervention`` is the field that separates them: the recorder stamps
        # it only when the invocation actually CHANGED the primary event, and
        # leaves it empty for a transparent pass-through.  Same batch, same
        # processors: `_reconcile_countdown` intervened on 103/103 tasks,
        # `_balanced_empty_guard` on 46/103, `loop_detection_processor` on
        # 9/103, and the other seven on 0/103.  That is a signature again.
        matched = [n for n in u.nodes if str(n.static_node_id) in aliases]
        acted = [n for n in matched if str(getattr(n, "intervention", "") or "").strip()]
        # Degradation: a U recorded before the field existed stamps "" on every
        # node, indistinguishable from "nothing intervened".  If NO node anywhere
        # in this U carries an intervention, the field is not being recorded here
        # and presence is all we have — say so rather than grading everything
        # orphan on a missing column.
        u_records_intervention = any(
            str(getattr(n, "intervention", "") or "").strip() for n in u.nodes
        )
        if u_records_intervention:
            count, basis = len(acted), "intervening invocation(s)"
        else:
            count, basis = len(matched), "invocation(s), presence only — this U records no intervention"
        if count >= min_calls:
            return GraphSignatureResult(
                label=DIRECT,
                backend=BACKEND_GRAPH,
                fired=True,
                tool_name=target,
                count=count,
                min_calls=min_calls,
                reason=f"{target} in U with {count} {basis} (>= {min_calls})",
            )
        return GraphSignatureResult(
            label=ORPHAN,
            backend=BACKEND_GRAPH,
            fired=False,
            tool_name=target,
            count=count,
            min_calls=min_calls,
            reason=(
                f"{target} below the required floor: {count} {basis} < {min_calls}"
                + (f" (present {len(matched)} time(s), none of them changed the event)"
                   if u_records_intervention and matched else "")
            ),
        )

    # Unknown types: no node representation. The result abstains honestly rather
    # than guess from labels.
    return GraphSignatureResult(
        label=JOINT,
        backend=BACKEND_NONE,
        fired=None,
        tool_name=str(signature.get("tool_name") or signature.get("class_name") or ""),
        reason=(
            f"signature type {sig_type!r} has no node representation in the graph — "
            "the graph backend does not answer it (no guess)"
        ),
    )


def infer_signature(
    bucket: str | None,
    manifest: dict | None,
    attribution_signature: dict | None = None,
) -> dict | None:
    """Resolve the signature to check for a candidate, exactly as the vendored
    attributor would.

    Mirrors ``attribution.compute_evidence``'s resolution order — an explicit
    ``attribution_signature`` wins; otherwise the default is inferred from the
    bucket + manifest by the **vendored** ``_infer_default_signature`` (reused, not
    reimplemented, so the graph gate checks the identical signature the official
    text attributor would).  ``None`` means "no mechanical signature" (prompt/config).
    """
    if isinstance(attribution_signature, dict):
        return attribution_signature
    from ..aegis.data.attribution import _infer_default_signature

    return _infer_default_signature(bucket, manifest)


__all__ = [
    "DIRECT",
    "ORPHAN",
    "JOINT",
    "BACKEND_GRAPH",
    "BACKEND_NONE",
    "GraphSignatureResult",
    "count_tool_invocations",
    "count_processor_invocations",
    "processor_static_id",
    "processor_file_uri_static_id",
    "check_signature_in_u",
    "infer_signature",
]
