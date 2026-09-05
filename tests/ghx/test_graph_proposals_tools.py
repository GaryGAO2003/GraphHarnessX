# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""insert_tool / remove_tool — the tools-bucket edit surface (M24).

What must hold:
  * insert_tool with a file:// @tool asset lands the entry in the written
    config's tool_registry.custom, leaves the genotype hash unchanged, and
    survives a reload;
  * remove_tool drops an existing custom entry; removing a non-existent entry
    or a builtin is rejected with a parse issue and mutates nothing;
  * insert_tool preflights the import: a bogus path is rejected;
  * the vendored ``_apply_tools`` merge carries the custom diff to merged.yaml
    (the compose leg the ship rides);
  * the core loader OVERRIDES a same-name builtin with the custom tool instead
    of dropping it (the Bash/cmd.exe fix shape);
  * ``derive_candidate_surface`` reports the delta as ``tool:<name>`` node ids
    (added on insert, removed on drop) so the scope gate sees tool edits.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harnessx.ghx.graph_proposals import ProposalSession

from tests.ghx.test_graph_proposals import (  # reuse the working fixture set
    _PARENT_YAML,
    _make_session,
    _tools,
)

_TOOL_ASSET = '''
from harnessx.tools.base import tool


@tool(description="posix bash probe for tool-edit tests")
async def probe_shell(cmd: str) -> str:
    return "probe:" + cmd
'''

_BASH_OVERRIDE_ASSET = '''
from harnessx.tools.base import tool


@tool(name="Bash", description="override probe named like the builtin")
async def posix_bash(command: str) -> str:
    return "posix:" + command
'''


def _write_asset(tmp_path: Path, name: str, text: str) -> str:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8", newline="\n")
    return f"file:///{p.as_posix().lstrip('/')}" + "::" + text.split("async def ")[1].split("(")[0]


async def _open(session, tools, cid="C-R7-90"):
    res = await tools["GraphProposalOpen"].fn(candidate_id=cid, bucket="tools")
    assert res["ok"], res
    return cid


@pytest.mark.asyncio
async def test_insert_tool_lands_in_config_and_keeps_genotype(tmp_path: Path):
    session = _make_session(tmp_path)
    tools = _tools(session)
    cid = await _open(session, tools)
    entry = _write_asset(tmp_path, "probe_shell.py", _TOOL_ASSET)
    from harnessx.graph.identity import genotype_hash

    g0 = genotype_hash(session._candidates[cid].snapshot)
    res = await tools["GraphProposalEdit"].fn(
        candidate_id=cid,
        edits=[{"edit_type": "insert_tool", "tool_entry": entry}],
        reason="tools-bucket probe",
    )
    assert res["ok"], res
    assert res["genotype"] == g0  # tool edits never move the genotype
    cfg = yaml.safe_load(session._candidates[cid].config_path.read_text(encoding="utf-8"))
    assert entry in (cfg.get("tool_registry") or {}).get("custom", [])


@pytest.mark.asyncio
async def test_remove_tool_drops_entry_and_rejects_unknown(tmp_path: Path):
    session = _make_session(tmp_path)
    tools = _tools(session)
    cid = await _open(session, tools)
    entry = _write_asset(tmp_path, "probe_shell.py", _TOOL_ASSET)
    ok1 = await tools["GraphProposalEdit"].fn(
        candidate_id=cid, edits=[{"edit_type": "insert_tool", "tool_entry": entry}], reason="add"
    )
    assert ok1["ok"], ok1
    ok2 = await tools["GraphProposalEdit"].fn(
        candidate_id=cid, edits=[{"edit_type": "remove_tool", "tool_entry": entry}], reason="drop"
    )
    assert ok2["ok"], ok2
    cfg = yaml.safe_load(session._candidates[cid].config_path.read_text(encoding="utf-8"))
    assert entry not in (cfg.get("tool_registry") or {}).get("custom", [])

    bad = await tools["GraphProposalEdit"].fn(
        candidate_id=cid, edits=[{"edit_type": "remove_tool", "tool_entry": "no.such.entry"}], reason="x"
    )
    assert not bad["ok"]
    assert bad["issues"][0]["error_type"] == "bad_edit_shape"


@pytest.mark.asyncio
async def test_insert_tool_preflights_import(tmp_path: Path):
    session = _make_session(tmp_path)
    tools = _tools(session)
    cid = await _open(session, tools)
    res = await tools["GraphProposalEdit"].fn(
        candidate_id=cid,
        edits=[{"edit_type": "insert_tool", "tool_entry": "file:///Z:/nope/missing.py::ghost"}],
        reason="bogus",
    )
    assert not res["ok"]
    assert "preflight" in res["issues"][0]["message"]
    cfg_path = session._candidates[cid].config_path
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert not (cfg.get("tool_registry") or {}).get("custom")  # nothing landed


def test_vendored_apply_tools_merges_custom_diff():
    from harnessx.aegis.compose import _apply_tools

    parent = {"tool_registry": {"builtin": ["Bash"], "custom": ["a.b.old_tool"]}}
    candidate = {"tool_registry": {"builtin": ["Bash"], "custom": ["a.b.new_tool"]}}
    base = {"tool_registry": {"builtin": ["Bash"], "custom": ["a.b.old_tool"]}}
    _apply_tools(base, candidate, parent)
    assert base["tool_registry"]["custom"] == ["a.b.new_tool"]


def test_loader_overrides_same_name_builtin(tmp_path: Path):
    from harnessx.core.harness import HarnessConfig

    asset = tmp_path / "posix_bash.py"
    asset.write_text(_BASH_OVERRIDE_ASSET, encoding="utf-8", newline="\n")
    entry = f"file:///{asset.as_posix().lstrip('/')}::posix_bash"
    cfg = HarnessConfig.from_yaml(
        yaml.safe_dump(
            {
                "tool_registry": {"builtin": ["Bash", "Read"], "custom": [entry]},
                "processors": yaml.safe_load(_PARENT_YAML)["processors"],
            }
        )
    )
    from harnessx.core.harness import _build_tool_registry_from_config as _b

    registry = _b(cfg.tool_registry)
    bash = registry._tools.get("Bash")
    assert bash is not None
    assert getattr(bash, "__hx_target__", "").endswith("::posix_bash")


def test_surface_reports_tool_delta(tmp_path: Path):
    from harnessx.ghx.candidate_surface import derive_candidate_surface

    asset = tmp_path / "probe_shell.py"
    asset.write_text(_TOOL_ASSET, encoding="utf-8", newline="\n")
    entry = f"file:///{asset.as_posix().lstrip('/')}::probe_shell"
    parent = tmp_path / "p.yaml"
    child = tmp_path / "c.yaml"
    base = yaml.safe_load(_PARENT_YAML)
    parent.write_text(yaml.safe_dump(base), encoding="utf-8")
    base2 = dict(base)
    base2["tool_registry"] = {"custom": [entry]}
    child.write_text(yaml.safe_dump(base2), encoding="utf-8")
    s = derive_candidate_surface("C-T-01", parent, child)
    assert s.ok, s.reason
    assert "tool:probe_shell" in s.nodes_added
    # and the reverse direction reads as a removal
    s2 = derive_candidate_surface("C-T-02", child, parent)
    assert "tool:probe_shell" in s2.nodes_removed
