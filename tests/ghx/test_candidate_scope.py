# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 gates batch — Gate C (cone reach, modify-type only) + annotation A."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import yaml

from harnessx.ghx.candidate_scope import (
    ScopeGateResult,
    alias_nodes,
    apply_scope_gate_to_stage4,
    check_candidate_scope,
    edit_kind,
    run_round_with_scope_gate,
)

T1, T2 = "aaaa1111-0-0-0-1", "bbbb2222-0-0-0-2"


def _fm(bucket="processor", stems=("bash_guard_v2",), predicted=(T1,), diff="1 graph edit(s): replace_same_groupx1", sig=None):
    fm = {
        "candidate_id": "C-R5-01",
        "bucket": bucket,
        "predicted_impact": {"tasks_will_unlock": list(predicted)},
        "file_changes": [
            {"path": f"D:/x/applied/C-R5-01/{s}.py", "action": "create", "diff_summary": diff} for s in stems
        ]
        + [{"path": "D:/x/applied/C-R5-01/_scratch.py", "action": "create", "diff_summary": "probe"}],
    }
    if sig:
        fm["attribution_signature"] = sig
    return fm


def test_alias_nodes_file_stems_and_signature():
    a = alias_nodes(_fm())
    assert "proc:py::_bash_guard_v2" in a
    assert not any("_scratch" in x for x in a)
    a2 = alias_nodes(_fm(bucket="tools", stems=("smart_fetch",)))
    assert "tool:SmartFetch" in a2
    a3 = alias_nodes(_fm(sig={"type": "tool_call", "tool_name": "OcrImage"}))
    assert "tool:OcrImage" in a3
    assert alias_nodes({"bucket": "prompt", "file_changes": []}) == set()


def test_edit_kind():
    fm = _fm()
    assert edit_kind(fm, alias_nodes(fm), None) == "modify"  # graph-op marker
    fm2 = _fm(diff="new tool")
    assert edit_kind(fm2, alias_nodes(fm2), None) == "additive"
    # parent config already wires the stem → modify even without markers
    assert edit_kind(fm2, alias_nodes(fm2), "file://x/bash_guard_v2.py::G") == "modify"


def test_check_scope_verdicts():
    cones = {T1: ["proc:py::_bash_guard_v2#empty", "tool:Bash"], T2: ["tool:WebFetch"]}
    # modify + predicted task's cone contains the node → ok
    v = check_candidate_scope("c", _fm(), cones=cones, parent_config_text=None, threshold=6)
    assert v.checked and v.ok and v.predicted_in_cone == [T1]
    assert v.population == 1 and v.sub_resolution  # 1 < 6 → annotation A fires
    # modify + node in NO predicted cone → refused
    v2 = check_candidate_scope("c", _fm(predicted=(T2,)), cones=cones, parent_config_text=None)
    assert v2.checked and not v2.ok and "NONE" in v2.reason
    # additive → exempt from C, still annotated
    v3 = check_candidate_scope("c", _fm(diff="new"), cones=cones, parent_config_text=None)
    assert v3.checked and v3.ok and v3.kind == "additive"
    # no aliases (prompt) → abstain
    v4 = check_candidate_scope("c", {"bucket": "prompt"}, cones=cones, parent_config_text=None)
    assert not v4.checked and v4.ok
    # cones unavailable → pass-through
    v5 = check_candidate_scope("c", _fm(), cones=None, parent_config_text=None)
    assert not v5.checked and v5.ok
    # modify but predicted tasks have no cones this round → pass-through
    v6 = check_candidate_scope("c", _fm(predicted=("zzzz",)), cones=cones, parent_config_text=None)
    assert not v6.checked and v6.ok


def test_surface_removed_node_drives_reach():
    """replace_same_group: the REPLACED node (v1) is the reach target — the new
    node (v2) cannot appear in cones that predate it (the real C-R8-01 shape,
    which the manifest-alias-only version falsely refused)."""
    cones = {T1: ["proc:py::_bash_guard", "tool:Bash"]}  # v1 in the cone; v2 nowhere
    fm = _fm(stems=("bash_guard_v2",), predicted=(T1,))
    surface = {"nodes_added": ["proc:py::_bash_guard_v2"], "nodes_removed": ["proc:py::_bash_guard"], "nodes_mutated": []}
    v = check_candidate_scope("c", fm, cones=cones, parent_config_text=None, surface=surface)
    assert v.kind == "modify" and v.checked and v.ok
    assert v.predicted_in_cone == [T1] and v.population == 1
    # without the surface, the manifest alias (v2) reaches nothing — population 0,
    # which since the dormant-node rule is no longer a refusal but an
    # additive-equivalent downgrade (sub_resolution accounting). The surface
    # still changes the PATH: in-cone ok above vs dormant downgrade here.
    v_old = check_candidate_scope("c", fm, cones=cones, parent_config_text=None, surface=None)
    assert v_old.checked and v_old.ok
    assert v_old.population == 0 and v_old.sub_resolution is True
    assert v_old.predicted_in_cone == []
    # annotation A keys on predicted∩failing, not on own-node population
    assert v.sub_resolution is True and v.predicted_with_cones == 1


def _mk_stage4_env(tmp_path: Path, predicted):
    run = tmp_path / "arm"
    ge = run / "R5" / "graph_evidence"
    ge.mkdir(parents=True)
    (ge / "cone_sigs.json").write_text(
        json.dumps({"failing": {T1: ["proc:py::_bash_guard_v2"], T2: ["tool:WebFetch"]}}), encoding="utf-8"
    )
    cdir = run / "R5" / "candidates"
    cdir.mkdir(parents=True)
    (cdir / "C-R5-01.md").write_text("---\n" + yaml.safe_dump(_fm(predicted=predicted)) + "---\nbody\n", encoding="utf-8")
    info = {"C-R5-01": (cdir / "C-R5-01.md", run / "R5" / "applied" / "C-R5-01" / "config.yaml")}
    return run, info


def test_apply_refuses_and_writes_evidence(tmp_path):
    run, info = _mk_stage4_env(tmp_path, predicted=(T2,))  # node not in T2's cone
    result = {"shipped_cids": ["C-R5-01"], "gate_results": {}}
    out = apply_scope_gate_to_stage4(result, candidates_info=info, run_dir=run, round_n=5)
    assert out["shipped_cids"] == [] and out["reason"] == "all_candidates_failed_scope_gate"
    # attribute-shaped: the vendored audit does `.ok` on every gate_results value
    assert out["gate_results"]["C-R5-01"]["scope"].ok is False
    md = (run / "R5" / "graph_evidence" / "gate" / "scope_C-R5-01.md").read_text(encoding="utf-8")
    assert "REFUSED" in md
    res = json.loads((run / "R5" / "graph_evidence" / "resolution.json").read_text(encoding="utf-8"))
    assert res["candidates"]["C-R5-01"]["sub_resolution"] is True


def test_apply_keeps_ok_candidates(tmp_path):
    run, info = _mk_stage4_env(tmp_path, predicted=(T1,))
    result = {"shipped_cids": ["C-R5-01"]}
    out = apply_scope_gate_to_stage4(result, candidates_info=info, run_dir=run, round_n=5)
    assert out is result  # untouched object when nothing refused
    assert (run / "R5" / "graph_evidence" / "gate" / "scope_C-R5-01.md").exists()


def test_wrapper_patches_and_restores(tmp_path, monkeypatch):
    import harnessx.aegis.orchestrator as om

    run, info = _mk_stage4_env(tmp_path, predicted=(T2,))
    seen = {}

    async def fake_stage4(**kw):
        return {"shipped_cids": ["C-R5-01"]}

    monkeypatch.setattr(om, "run_stage_4", fake_stage4)
    base = om.run_stage_4

    class FakeOrch:
        run_dir = run

        async def run_round(self, **kw):
            # is the wrapper's stage-4 shim installed right now?
            seen["patched"] = om.run_stage_4 is not base
            return await om.run_stage_4(candidates_info=info, round_n=5)
    out = asyncio.run(run_round_with_scope_gate(FakeOrch(), gate_enabled=True))
    assert seen["patched"] is True and om.run_stage_4 is base  # restored
    assert out["shipped_cids"] == []
    # flag off → pure delegate, no patching
    seen.clear()
    out2 = asyncio.run(run_round_with_scope_gate(FakeOrch(), gate_enabled=False))
    assert seen["patched"] is False and out2["shipped_cids"] == ["C-R5-01"]


def test_dormant_node_zero_population_downgrades_to_additive_equivalent():
    # Target fires in NO failing cone at all: an armed-but-idle engine never
    # enters U under attribute-by-what-CHANGED, so refusing "not in predicted
    # cones" would deadlock the very candidate that arms it (live: M26 R1,
    # the loop's first runtime-policy rule-fill). Downgrade, never refuse.
    cones = {T1: ["tool:Bash"], T2: ["tool:WebFetch"]}
    fm = _fm(stems=("runtime_policy_processor",), predicted=(T1, T2))
    v = check_candidate_scope("c", fm, cones=cones, parent_config_text=None, threshold=6)
    assert v.checked and v.ok
    assert v.population == 0
    assert v.sub_resolution is True
    assert "dormant" in v.reason


def test_present_elsewhere_but_not_predicted_still_refuses():
    # The original protection stands: a node that DOES fire in some failing
    # cone, just none of the predicted ones, is structurally incapable of the
    # predicted effect and stays refused.
    cones = {T1: ["proc:py::_bash_guard_v2#empty", "tool:Bash"], T2: ["tool:WebFetch"]}
    v = check_candidate_scope("c", _fm(predicted=(T2,)), cones=cones, parent_config_text=None)
    assert v.checked and not v.ok
    assert v.population == 1
    assert "structurally incapable" in v.reason


def test_refusal_entry_is_attribute_shaped_for_the_vendored_audit():
    # orchestrator.py:699 runs `{k: v.ok for k, v in gr.items()}` over every
    # gate_results value. The scope entry must expose .ok/.reason as
    # attributes — a plain dict here crashed the whole evolve on the scope
    # gate's first live refusal (M26 R1, 'dict' object has no attribute 'ok').
    entry = ScopeGateResult(False, "why")

    class _GraphVerdictLike:  # graph_gate stores objects at the same spot
        ok = True
        reason = "fine"

    gr = {"scope": entry, "graph_existence": _GraphVerdictLike()}
    audited = {k: val.ok for k, val in gr.items()}  # vendored audit shape
    assert audited == {"scope": False, "graph_existence": True}
    assert entry.reason == "why"
