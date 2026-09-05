# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Evolver cheatsheet — institutional memory the fresh session cannot lose (M24 · 批改 #2).

Every round's Evolver is a brand-new session. Measured consequences on
M24_103x3: the GraphProposal API was re-learned by trial each round (ten
``_gp_inspect``/``_gp_dump`` probe scripts in R2's applied dir), three
sessions burned to the 400-step cap, and FOUR Critic-accepted candidates died
on the same IV-11 evidence rule the session had no way to remember
(R2/R11/R12×2 — every death the same missing '## Why flagged direction is
infeasible' evidence).

The fix is not a bigger archive the model might read — it is a one-page crib
placed in the material the guidance seam already injects into the Evolver's
brief. Content: the edit-type quick reference (including the tools-bucket ops
that dissolve the IV-11 deadlock), the IV-11 survival rule with the death
count, the capability-evidence recipe, and the manifest field checklist.

Flag: ``HARNESSX_GHX_CHEATSHEET`` (call-time read, default off). Rides the
guidance seam — GUIDANCE must be on for the injection to reach the session.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

_LOG = logging.getLogger(__name__)

FLAG = "HARNESSX_GHX_CHEATSHEET"
_ENABLE_VALUES = frozenset({"1", "true", "on", "yes"})


def cheatsheet_enabled() -> bool:
    return os.environ.get(FLAG, "").strip().lower() in _ENABLE_VALUES


CHEATSHEET_MD = """# Evolver cheatsheet — survival rules (read BEFORE your first tool call)

Prior sessions lost four Critic-accepted candidates and three 400-step
burnouts to the mistakes this page prevents. Read it in full; it is one page.

## 1. IV-11 — the rule that killed 4 prior candidates

If a `strategy_concern` flags a bucket (read the landscape's top section) and
your candidate targets a DIFFERENT bucket, the commit gate demands a
`## Why flagged direction is infeasible` body section containing CONCRETE
tool output (bash / web_search / web_fetch results) proving the flagged
direction is genuinely unreachable. A short essay does not pass; evidence
does. Two ways to survive:

* **Attack the flagged bucket directly.** The `tools` bucket IS expressible
  now: `insert_tool` / `remove_tool` edits (below). A flagged-tools round
  wants a tools candidate, not an exemption essay.
* **If you truly must go elsewhere**, run the probes and paste their output
  into the section: show the command you ran and what came back.

## 2. Edit types — GraphProposalEdit quick reference

Graph ops (processor plane): `insert_node`, `remove_node`,
`replace_same_group`, `change_dependency`, `swap_subgraph`, `mutate_inactive`,
`mutate_params`.

Config-section ops (tools plane): `insert_tool`, `remove_tool`.

Worked examples (shapes that passed all gates before):

```json
{"edit_type": "insert_node", "node_spec": {"_target_": "file:///ABS/PATH/my_proc.py::MyProcessor", "_hook_": "*", "_order_": 12, "_singleton_group_": "my_proc_sg"}}
```
```json
{"edit_type": "mutate_params", "target_node_id": "<node id from the inventory>", "node_changes": {"kwarg_name": "new_value"}}
```
```json
{"edit_type": "insert_tool", "tool_entry": "file:///ABS/PATH/my_tool.py::my_tool_fn"}
```

`insert_tool` notes: the file must define an async function decorated with
`@tool` (`from harnessx.tools.base import tool`); the entry is
import-preflighted at edit time; a custom tool named like a builtin (e.g.
`@tool(name="Bash")`) OVERRIDES the builtin at load — that is the sanctioned
way to replace a builtin's behavior. Do NOT probe the API with throwaway
scripts — the examples above are current.

## 3. Capability evidence — the recipe the Critic and gates accept

Every candidate needs Level-1 AND Level-2 evidence in
`capability_evidence`. Write ONE `_verify.py` in your applied dir and run it:

```python
# _verify.py — L1: the artifact loads; L2: the mechanism round-trips
import importlib.util as iu
spec = iu.spec_from_file_location("cand", r"ABS/PATH/your_asset.py")
mod = iu.module_from_spec(spec); spec.loader.exec_module(mod)   # L1
obj = getattr(mod, "YourClassOrFn")
print("L1 OK:", obj)
# L2: drive the actual hook/tool path once and print what the model would see
```

Paste the script's real stdout into the evidence — the gate checks substance,
not adjectives.

## 4. Manifest checklist (machine-read; wrong keys are silently lost)

* `predicted_impact.tasks_will_unlock` / `tasks_will_stabilize` /
  `tasks_at_risk` — task ids, full UUIDs, never truncated.
* `attribution_signature`: `{type: processor_invocation|tool_invocation,
  tool_name: <ClassName or tool name>, expected_min_calls: 1}`.
* Predict a task ONLY if your edit touches a node in that task's own cone
  (`cone_sigs.json`). Halo claims dilute your hit rate.
* Cite anchors with FULL paths — `trajectories/<full-uuid>_r0.jsonl#step_k`.
  Literal `...` in an anchor is a validation flag on your digest sources.

## 5. Runtime policy — steer a run WHILE it is failing (if the node is present)

If the processor inventory shows `runtime_policy_processor`, its `rules` param
is an editable POLICY: rules are evaluated before every model call against the
live execution graph, and a hit injects one steering line into that run. This
is the only edit surface that acts mid-run — every other edit waits for the
next batch. Edit it with ordinary `mutate_params` (`node_changes: {"rules":
[...]}`; the list you write REPLACES the old one, so carry forward rules you
keep).

```json
{"name": "stop-search-thrash",
 "when": {"predicate": "search_without_page", "searches": 6},
 "then": {"action": "steer", "text": "Open the best result found so far and answer from page content."},
 "min_step": 4, "max_fires": 1}
```

Predicates: `search_without_page` (N snippet searches since the last
page-grade read), `consecutive_empty` (last N tool calls empty/error),
`own_death_cone` (this run is retracing the task's own recorded failure cone;
params `run_dir`+`min_streak`+`overlap` — copy `run_dir` from an existing rule
or the config, never invent it). Action: `steer` only. Unknown
predicates/actions are silent no-ops.

Evidence for a policy candidate is cheap and strong: replay the rule offline
against last round's recorded graphs and paste the firing list —

```python
from harnessx.ghx.runtime_policy import fired_on_recorded_u
from harnessx.graph.unfold import load_unfolded
# for each R{n-1}/sessions/aegis/*/graph/*_unfolded.jsonl:
#   fired_on_recorded_u(rule, load_unfolded(path)) -> True/False
```

That output IS the predicted_impact task list: fired-on failing tasks are your
`tasks_will_unlock` candidates, fired-on passing tasks are `tasks_at_risk` —
measured, not guessed.
"""


def write_cheatsheet(run_dir, round_n: int) -> Path:
    """Write the cheatsheet into the round's graph_evidence dir; returns the path."""
    out = Path(run_dir) / f"R{round_n}" / "graph_evidence" / "evolver_cheatsheet.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(CHEATSHEET_MD, encoding="utf-8", newline="\n")
    _LOG.info("cheatsheet: wrote %s", out)
    return out
