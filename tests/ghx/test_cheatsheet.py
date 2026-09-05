# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Evolver cheatsheet — write, guidance-path pickup, and section text."""

from __future__ import annotations

from pathlib import Path

import harnessx.ghx.cheatsheet as cs
from harnessx.ghx.guidance import _evolver_paths, _evolver_section


def test_write_cheatsheet_content(tmp_path: Path):
    p = cs.write_cheatsheet(tmp_path, 3)
    assert p == tmp_path / "R3" / "graph_evidence" / "evolver_cheatsheet.md"
    text = p.read_text(encoding="utf-8")
    # the survival rules the page exists for
    assert "IV-11" in text
    assert "Why flagged direction is infeasible" in text
    assert "insert_tool" in text
    assert "_verify.py" in text
    assert "tasks_will_unlock" in text


def test_guidance_picks_up_cheatsheet_when_flagged(tmp_path: Path, monkeypatch):
    monkeypatch.setenv(cs.FLAG, "1")
    paths = _evolver_paths(tmp_path, 2)
    # M26 slim: the cheatsheet rides inside the stitched map.md, survival rules first
    maps = [p for p in paths if p.endswith("map.md")]
    assert maps
    body = Path(maps[0]).read_text(encoding="utf-8")
    assert "stitched from evolver_cheatsheet.md" in body
    section = _evolver_section(tmp_path, 2, paths)
    assert "Read it FIRST" in section


def test_guidance_omits_cheatsheet_when_off(tmp_path: Path, monkeypatch):
    monkeypatch.delenv(cs.FLAG, raising=False)
    paths = _evolver_paths(tmp_path, 2)
    assert not any(p.endswith("evolver_cheatsheet.md") for p in paths)
