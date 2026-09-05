# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Tools-bucket forced end-to-end (M24 · 批改 #4 的强制 case).

No live Evolver has exercised insert_tool yet, so this constructs the entire
ship chain by hand and asserts every leg: proposal edit → candidate config →
vendored compose merge → loader override of the builtin → mutation surface →
scope-gate kind derivation. The one leg left to a real smoke is the LLM
behavioral one (will the Evolver choose the op) — everything mechanical is
pinned here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.ghx.test_graph_proposals import _PARENT_YAML, _make_session, _tools

_BASH_OVERRIDE = '''
from harnessx.tools.base import tool


@tool(name="Bash", description="posix bash override probe")
async def posix_bash(command: str) -> str:
    return "posix:" + command
'''


@pytest.mark.asyncio
async def test_full_chain_proposal_to_scope_kind(tmp_path: Path):
    # 1. proposal: open + insert_tool
    session = _make_session(tmp_path)
    tools = _tools(session)
    cid = "C-R7-77"
    assert (await tools["GraphProposalOpen"].fn(candidate_id=cid, bucket="tools"))["ok"]
    asset = tmp_path / "posix_bash.py"
    asset.write_text(_BASH_OVERRIDE, encoding="utf-8", newline="\n")
    entry = f"file:///{asset.as_posix().lstrip('/')}::posix_bash"
    res = await tools["GraphProposalEdit"].fn(
        candidate_id=cid,
        edits=[{"edit_type": "insert_tool", "tool_entry": entry}],
        reason="POSIX bash override for the cmd.exe mismatch class",
    )
    assert res["ok"], res

    # 2. candidate config carries the entry
    cand_cfg_path = session._candidates[cid].config_path
    cand = yaml.safe_load(cand_cfg_path.read_text(encoding="utf-8"))
    assert entry in cand["tool_registry"]["custom"]

    # 3. vendored compose merge carries the custom diff to the merged base
    from harnessx.aegis.compose import _apply_tools

    parent = yaml.safe_load(_PARENT_YAML)
    parent.setdefault("tool_registry", {"builtin": ["Bash", "Read"], "custom": []})
    cand_for_merge = dict(cand)
    cand_for_merge["tool_registry"] = {
        "builtin": ["Bash", "Read"],
        "custom": list(cand["tool_registry"]["custom"]),
    }
    base = {"tool_registry": {"builtin": ["Bash", "Read"], "custom": []}}
    _apply_tools(base, cand_for_merge, parent)
    assert entry in base["tool_registry"]["custom"]

    # 4. loader: the custom Bash OVERRIDES the builtin Bash
    from harnessx.core.harness import HarnessConfig, _build_tool_registry_from_config

    merged_cfg = HarnessConfig.from_yaml(
        yaml.safe_dump({"tool_registry": base["tool_registry"], "processors": parent["processors"]})
    )
    registry = _build_tool_registry_from_config(merged_cfg.tool_registry)
    bash = registry._tools["Bash"]
    assert getattr(bash, "__hx_target__", "").endswith("::posix_bash")

    # 5. mutation surface reports the tool node
    from harnessx.ghx.candidate_surface import derive_candidate_surface

    parent_path = tmp_path / "parent.yaml"  # written by _make_session
    surface = derive_candidate_surface(cid, parent_path, cand_cfg_path)
    assert surface.ok, surface.reason
    assert "tool:Bash" in surface.nodes_added

    # 6. scope-gate kind: added-only tool delta -> additive; removal -> modify
    from harnessx.ghx.candidate_scope import edit_kind

    kind = edit_kind({}, {"tool:Bash"}, None, surface={"nodes_added": ["tool:Bash"], "nodes_removed": [], "nodes_mutated": []})
    assert kind == "additive"
    kind_rm = edit_kind({}, {"tool:Bash"}, None, surface={"nodes_added": [], "nodes_removed": ["tool:Bash"], "nodes_mutated": []})
    assert kind_rm == "modify"
