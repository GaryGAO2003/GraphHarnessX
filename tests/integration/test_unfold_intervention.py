# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""v6 M13 — an invocation records whether it CHANGED anything, and the cone uses it.

Before M13 the evidence cone followed ``OBSERVED_CONTROL`` as well as data edges, so a
node was in it for sitting upstream of the anchor inside one hook firing.  Nearly every
invocation does, so the cone was dominated by pass-throughs and — measured on the real
bed — contained none of the invocations that actually intervened.  Membership said
nothing about causality.

M13 records the dispatcher's own primary-event diff on the U node (the SAME diff
``ProcessorTriggerEvent`` is built from, so U and the trace cannot disagree), and the
evidence cone becomes DATA-only ancestry unioned with the invocations that intervened.
These run real harnesses with ``HARNESSX_GHX_UNFOLD`` on and pin:

  * a pure pass-through records no intervention; a processor that mutates the event does;
  * the label round-trips through the U file;
  * a pre-M13 U (no ``intervention`` field) still loads;
  * the attribution cone contains an intervening invocation that NO edge connects to the
    anchor, and excludes pass-throughs the control chain would have pulled in.
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fixtures.mock_provider import MockProvider  # noqa: E402
from fixtures.mock_tools import add_tool, make_registry  # noqa: E402

from harnessx import (  # noqa: E402
    BaseTask,
    HarnessConfig,
    ModelConfig,
    MultiHookProcessor,
)
from harnessx.core.events import Message  # noqa: E402
from harnessx.ghx.evidence_files import _attribution_cone, _cone_anchors  # noqa: E402
from harnessx.graph.causal import causal_cone  # noqa: E402
from harnessx.graph.unfold import (  # noqa: E402
    load_unfolded,
    session_unfolded_files,
    write_unfolded,
)
from harnessx.tracing.journal import HarnessJournal  # noqa: E402


def _tool_turn(tag: str) -> dict:
    return {"content": tag, "tool_calls": [{"id": tag, "name": "add", "input": {"a": 1, "b": 1}}]}


class Passthrough(MultiHookProcessor):
    """Fires on every hook and mutates nothing — one node per firing, all inert."""


class Injector(MultiHookProcessor):
    """Appends a message on before_model — a real change to the primary event."""

    async def on_before_model(self, event):
        yield dataclasses.replace(event, messages=tuple(event.messages) + (Message(role="user", content="hint"),))


class ParamFixer(MultiHookProcessor):
    """Rewrites a tool call's input on before_tool.

    A real intervention that leaves NO trace on either data plane: it writes no slot and
    touches no message, so a data-only cone cannot see it.  This is the shape the union
    term exists for — and the shape most control processors have.
    """

    async def on_before_tool(self, event):
        yield dataclasses.replace(event, tool_input={**event.tool_input, "b": 41})


async def _run_and_load(tmp_path, processors, responses, *, tools=None, session_id="isess"):
    journal = HarnessJournal(base_dir=str(tmp_path), export_jsonl=True, session_id=session_id, silent=True)
    config = HarnessConfig(
        tool_registry=make_registry(*(tools or [])),
        tracer=journal,
        processors=processors,
    )
    mc = ModelConfig(main=MockProvider(responses=responses))
    result = await mc.agentic(config).run(BaseTask(description="q", max_steps=10))
    written = session_unfolded_files(tmp_path / session_id)
    assert written, f"expected a U under {tmp_path / session_id}"
    return result, max((load_unfolded(p) for p in written), key=lambda g: len(g.nodes))


# ── 1. the diff lands on the node ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_passthrough_records_no_intervention(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_UNFOLD", "1")
    _r, graph = await _run_and_load(
        tmp_path,
        processors=[Passthrough()],
        responses=[_tool_turn("c"), "done"],
        tools=[add_tool],
    )
    proc_nodes = [n for n in graph.nodes if n.hook not in ("tool", "model")]
    assert proc_nodes, "the pass-through fired somewhere"
    assert all(n.intervention == "" for n in proc_nodes)


@pytest.mark.asyncio
async def test_mutating_processor_records_its_intervention(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_UNFOLD", "1")
    _r, graph = await _run_and_load(
        tmp_path,
        processors=[Injector(), Passthrough()],
        responses=[_tool_turn("c"), "done"],
        tools=[add_tool],
    )
    injector = [n for n in graph.nodes if n.label == "Injector" and n.hook == "before_model"]
    assert injector, "Injector ran on before_model"
    assert all(n.intervention for n in injector), "a processor that changed the event says so"

    # The inert processor in the SAME firings stays blank — the flag tracks the
    # invocation's own diff, not the firing it belongs to.
    inert = [n for n in graph.nodes if n.label == "Passthrough" and n.hook == "before_model"]
    assert inert and all(n.intervention == "" for n in inert)

    # Tools and model calls are not processor dispatches — nothing diffs them.
    assert all(n.intervention == "" for n in graph.nodes if n.hook in ("tool", "model"))


# ── 2. it survives the file ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_intervention_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_UNFOLD", "1")
    _r, graph = await _run_and_load(
        tmp_path,
        processors=[Injector()],
        responses=["done"],
    )
    marked = {n.id: n.intervention for n in graph.nodes if n.intervention}
    assert marked, "something intervened"

    path = write_unfolded(graph, base_dir=str(tmp_path / "rt"))
    reloaded = {n.id: n.intervention for n in load_unfolded(path).nodes if n.intervention}
    assert reloaded == marked


def test_pre_m13_u_file_still_loads(tmp_path):
    """A U written before the field existed reads back as 'no intervention recorded' —
    which is what it is: the field did not exist to be set, so absence is honest."""
    path = tmp_path / "old_unfolded.jsonl"
    path.write_text(
        json.dumps({"kind": "meta", "run_id": "r", "session_id": "s"})
        + "\n"
        + json.dumps(
            {
                "kind": "node",
                "id": "A@t0",
                "static_node_id": "A",
                "graphed": True,
                "hook": "task_end",
                "step": 0,
                "ordinal": 0,
                "label": "A",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    graph = load_unfolded(path)
    assert [n.intervention for n in graph.nodes] == [""]


# ── 3. the cone uses it ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_attribution_cone_keeps_interventions_and_drops_passthroughs(tmp_path, monkeypatch):
    """The union term is load-bearing and the control chain is not.

    ``ParamFixer`` changes a tool call's input: a real intervention that writes no slot
    and touches no message, so no data edge can carry it and only the union term puts it
    in.  ``Injector``'s message write, by contrast, is already visible on the data plane —
    the two terms overlap, which is why the cone is their union and not a choice.
    """
    monkeypatch.setenv("HARNESSX_GHX_UNFOLD", "1")
    _r, graph = await _run_and_load(
        tmp_path,
        processors=[Injector(), ParamFixer(), Passthrough()],
        responses=[_tool_turn("c"), "done"],
        tools=[add_tool],
    )
    anchors = _cone_anchors(graph)
    assert anchors

    attribution = _attribution_cone(graph, anchors)
    data_only = causal_cone(graph, anchors, edge_types="observed_data", include_anchors=True)
    all_edges = causal_cone(graph, anchors, include_anchors=True)

    by_id = {n.id: n for n in graph.nodes}
    intervened = {n.id for n in graph.nodes if n.intervention}
    assert {by_id[nid].label for nid in intervened} >= {"Injector", "ParamFixer"}

    # Every intervention is in, whether or not a data edge carried it.
    assert intervened <= attribution
    invisible = intervened - data_only
    assert invisible, "at least one intervention is in on the union term alone"
    assert {by_id[nid].label for nid in invisible} == {"ParamFixer"}

    # The cone is strictly the two terms — no control-chain membership survives.
    assert attribution == data_only | intervened
    assert attribution < all_edges, "following control edges only ever added inert nodes"

    # Nothing inert that the control chain would have pulled in remains, unless a data
    # edge genuinely carries it.
    for nid in attribution - data_only:
        assert by_id[nid].intervention, f"{nid} is in the cone for no reason"
