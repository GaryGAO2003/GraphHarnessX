# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M24 fix #1 — the ledger's evidence learns to count U (graph-first backfill)."""
from __future__ import annotations

import json
from pathlib import Path

from harnessx.ghx.attribution_backfill import (
    compute_evidence_graph_first,
    install_attribution_backfill,
)

T_FIRED = "aaaaaaaa-0000-0000-0000-000000000001"
T_SILENT = "bbbbbbbb-0000-0000-0000-000000000002"
T_NO_U = "cccccccc-0000-0000-0000-000000000003"


def _mk_u(run: Path, rnd: int, task: str, nodes: list) -> None:
    g = run / f"R{rnd}" / "sessions" / "aegis" / f"R{rnd}-{task}" / "graph"
    g.mkdir(parents=True, exist_ok=True)
    recs = [{"kind": "meta", "run_id": "x", "session_id": f"aegis/R{rnd}-{task}"}]
    for i, base in enumerate(nodes):
        recs.append(
            {
                "kind": "node",
                "id": f"{base}@t{i}",
                "static_node_id": base,
                "graphed": True,
                "hook": "tool" if base.startswith("tool:") else "before_tool",
                "step": i,
                "ordinal": i,
            }
        )
    (g / "u_unfolded.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")


def _manifest_processor():
    # file-URI ship: class EvidenceGuardProcessor → node proc:py::_evidence_guard_processor
    return {
        "bucket": "processor",
        "file_changes": [{"path": "x/evidence_guard.py", "action": "create"}],
    }


def test_graph_answers_processor_ship_dual_form(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESSX_GHX_ATTRIBUTION", "1")
    run = tmp_path / "arm"
    # the vendored inference pascals evidence_guard.py → EvidenceGuardProcessor;
    # the U node carries the FILE-URI form of that class name
    _mk_u(run, 3, T_FIRED, ["proc:py::_evidence_guard_processor", "tool:Bash"])
    _mk_u(run, 3, T_SILENT, ["tool:Bash"])

    with install_attribution_backfill():
        import harnessx.aegis.data.attribution as attr

        out = attr.compute_evidence(
            run,
            round_n=3,
            bucket="processor",
            predicted_tasks=[T_FIRED, T_SILENT, T_NO_U],
            manifest=_manifest_processor(),
        )
    assert out[T_FIRED] == "direct"  # dual-form counting found the py::_ node
    assert out[T_SILENT] == "orphan"  # U present, node absent → mechanically silent
    # no U → per-task VENDORED fallback, whatever it says for a missing trajectory
    from harnessx.ghx.attribution_backfill import _ORIGINAL_COMPUTE  # noqa: F401
    import harnessx.aegis.data.attribution as attr_mod

    vendored = attr_mod.compute_evidence(
        run, round_n=3, bucket="processor", predicted_tasks=[T_NO_U], manifest=_manifest_processor()
    )
    assert out[T_NO_U] == vendored[T_NO_U]


def test_prompt_ship_stays_joint_and_flag_off_is_vendored(tmp_path, monkeypatch):
    run = tmp_path / "arm"
    monkeypatch.setenv("HARNESSX_GHX_ATTRIBUTION", "1")
    with install_attribution_backfill():
        import harnessx.aegis.data.attribution as attr

        out = attr.compute_evidence(
            run, round_n=2, bucket="prompt", predicted_tasks=[T_FIRED], manifest=None
        )
    assert out == {T_FIRED: "joint"}
    # flag off → byte-identical to the vendored function
    monkeypatch.delenv("HARNESSX_GHX_ATTRIBUTION")
    import harnessx.aegis.data.attribution as attr_plain

    expected = attr_plain.compute_evidence(
        run, round_n=2, bucket="processor", predicted_tasks=[T_FIRED], manifest=_manifest_processor()
    )
    with install_attribution_backfill():
        import harnessx.aegis.data.attribution as attr

        out2 = attr.compute_evidence(
            run, round_n=2, bucket="processor", predicted_tasks=[T_FIRED], manifest=_manifest_processor()
        )
    assert out2 == expected


def test_installer_restores():
    import harnessx.aegis.data.attribution as attr

    original = attr.compute_evidence
    with install_attribution_backfill():
        assert attr.compute_evidence is not original
    assert attr.compute_evidence is original


def test_vacuous_signature_grades_joint(tmp_path, monkeypatch):
    """A signature on an always-firing node (declared system_prompt_processor,
    any '*'-hook guard) must NOT grade direct everywhere — presence without
    discrimination is vacuous (observed live: 30x5's prompt ships declared
    system_prompt_processor and would have graded 11/11 direct)."""
    monkeypatch.setenv("HARNESSX_GHX_ATTRIBUTION", "1")
    run = tmp_path / "arm"
    ubiq = "proc:py::_evidence_guard_processor"
    # fires on the predicted task AND on every non-predicted task → vacuous
    _mk_u(run, 3, T_FIRED, [ubiq, "tool:Bash"])
    for i in range(10):
        _mk_u(run, 3, f"dddddddd-0000-0000-0000-0000000000{i:02d}", [ubiq])
    with install_attribution_backfill():
        import harnessx.aegis.data.attribution as attr

        out = attr.compute_evidence(
            run, round_n=3, bucket="processor", predicted_tasks=[T_FIRED], manifest=_manifest_processor()
        )
    assert out == {T_FIRED: "joint"}
    # …but once the node is silent on a real share of the batch it discriminates,
    # and the graph's per-task answer stands.
    for i in range(4):
        _mk_u(run, 3, f"eeeeeeee-0000-0000-0000-0000000000{i:02d}", ["tool:Bash"])
    with install_attribution_backfill():
        import harnessx.aegis.data.attribution as attr

        out2 = attr.compute_evidence(
            run, round_n=3, bucket="processor", predicted_tasks=[T_FIRED], manifest=_manifest_processor()
        )
    assert out2 == {T_FIRED: "direct"}


def test_a_common_but_not_universal_node_still_grades(tmp_path, monkeypatch):
    """The live regression: `tool:Bash` runs in ~45% of this bed's tasks and
    `tool:WebFetch` in ~78%. The old three-sample guard called that vacuous —
    all three sampled tasks fired — and threw away every graph answer, which is
    how M25's ledger came to read 10 ships x 0 direct. A signature fires on some
    other tasks; that makes the evidence weak, not absent."""
    monkeypatch.setenv("HARNESSX_GHX_ATTRIBUTION", "1")
    run = tmp_path / "arm"
    common = "proc:py::_evidence_guard_processor"
    _mk_u(run, 3, T_FIRED, [common, "tool:Bash"])
    # 8 of 12 non-predicted tasks also fire it — 67%, well above what a
    # three-sample guard would ever survive, well below "fires on everything".
    for i in range(8):
        _mk_u(run, 3, f"dddddddd-0000-0000-0000-0000000000{i:02d}", [common])
    for i in range(4):
        _mk_u(run, 3, f"eeeeeeee-0000-0000-0000-0000000000{i:02d}", ["tool:Bash"])
    with install_attribution_backfill():
        import harnessx.aegis.data.attribution as attr

        out = attr.compute_evidence(
            run, round_n=3, bucket="processor", predicted_tasks=[T_FIRED], manifest=_manifest_processor()
        )
    assert out == {T_FIRED: "direct"}
