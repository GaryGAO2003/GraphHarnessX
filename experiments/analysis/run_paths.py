"""Shared path resolution for offline campaign-analysis scripts."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def runs_root(value: str | None = None) -> Path:
    """Resolve an explicit runs root, GHX_RUNS_ROOT, or the repository default."""
    configured = value or os.environ.get("GHX_RUNS_ROOT")
    return Path(configured).expanduser().resolve() if configured else REPO_ROOT / "recipe" / "gaia_evolver" / "runs"


def require_path(path: Path, description: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"missing {description}: {path}")
    return path
