# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Anchor repair + IV-1b — reconstruction, persistence, advisory check, seam."""

from __future__ import annotations

import json
from pathlib import Path

import harnessx.ghx.anchor_repair as ar

TID = "0a3cd321-3e76-4622-911b-0fda2e5d6b1a"


def _mk(tmp_path: Path, snippet='the WebSearch tool returned empty content today'):
    root = tmp_path
    traj = root / "trajectories" / f"{TID}_r0.jsonl"
    traj.parent.mkdir(parents=True)
    rec = {"type": "tool", "step": 6, "message": {"role": "tool", "tool_call_id": "x",
           "content": f"prefix {snippet} suffix"}}
    traj.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    digest = root / "digests" / f"{TID}.md"
    digest.parent.mkdir(parents=True)
    text = (
        "pattern: ALL_FAIL\nfailure_mode: probe\n\n"
        f"**r0** -> `trajectories/{TID}_r0.jsonl`\n\n"
        "Bad cite: `trajectories/..._r0.jsonl#step_6` and bare `trajectories/...`.\n"
        f'- snippet: "{snippet}"\n'
        '- snippet: "this quote was fabricated by the digester entirely"\n'
    )
    digest.write_text(text, encoding="utf-8")
    return root, digest, text


def test_repair_reconstructs_both_forms(tmp_path: Path):
    _, _, text = _mk(tmp_path)
    repaired, n = ar.repair_digest_text(text)
    assert n == 2
    assert f"trajectories/{TID}_r0.jsonl#step_6" in repaired
    assert "trajectories/..." not in repaired


def test_repair_abstains_without_unambiguous_tid():
    repaired, n = ar.repair_digest_text("only `trajectories/..._r0.jsonl` here")
    assert n == 0 and "..." in repaired


def test_snippet_misses_counts_fabricated_quote(tmp_path: Path):
    root, _, text = _mk(tmp_path)
    misses, total = ar.snippet_misses(text, root)
    assert total == 2
    assert misses == 1  # the fabricated one


def test_wrapper_repairs_file_and_validates(tmp_path: Path, monkeypatch):
    root, digest, text = _mk(tmp_path)
    monkeypatch.setenv(ar.FLAG, "1")
    seen = {}

    def fake_validator(md, dr):
        seen["text"] = md

        class R:
            ok = True
            reason = ""

        return R()

    monkeypatch.setattr(ar, "_ORIGINAL_VALIDATE", fake_validator)
    r = ar.validate_digest_anchors_with_repair(text, root)
    assert r.ok
    assert "trajectories/..." not in seen["text"]  # validator saw the repaired text
    assert "trajectories/..." not in digest.read_text(encoding="utf-8")  # file rewritten


def test_flag_off_passthrough(tmp_path: Path, monkeypatch):
    root, digest, text = _mk(tmp_path)
    monkeypatch.delenv(ar.FLAG, raising=False)
    seen = {}

    def fake_validator(md, dr):
        seen["text"] = md

        class R:
            ok = False
            reason = "broken"

        return R()

    monkeypatch.setattr(ar, "_ORIGINAL_VALIDATE", fake_validator)
    r = ar.validate_digest_anchors_with_repair(text, root)
    assert not r.ok
    assert "trajectories/..." in seen["text"]  # untouched


def test_install_restores():
    import harnessx.aegis.gates.structure as gs

    original = gs.validate_digest_anchors
    with ar.install_anchor_repair():
        assert gs.validate_digest_anchors is ar.validate_digest_anchors_with_repair
    assert gs.validate_digest_anchors is original
    assert ar._ORIGINAL_VALIDATE is None


def test_repair_consumes_underscoreless_suffix():
    """Digester sometimes swallows the underscore too: `trajectories/...r1.jsonl`
    must reconstruct to `{tid}_r1.jsonl`, never glue (`_r0.jsonlr1.jsonl`)."""
    text = (
        f"good `trajectories/{TID}_r0.jsonl` and bad `trajectories/...r1.jsonl#step_3`"
    )
    repaired, n = ar.repair_digest_text(text)
    assert n == 1
    assert f"trajectories/{TID}_r1.jsonl#step_3" in repaired
    assert "jsonlr1" not in repaired
