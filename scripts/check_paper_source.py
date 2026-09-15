#!/usr/bin/env python3
"""Verify or refresh the paper source manifest without campaign data."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "experiments/docs/thesis"
MANIFEST = PAPER / "SOURCE-MANIFEST.json"
SOURCE_PATTERNS = (
    "main.tex",
    "preamble.tex",
    "macros.tex",
    "latexmkrc",
    "frontmatter/*.tex",
    "chapters/*.tex",
    "appendices/*.tex",
    "bibliography/references.tex",
    "figures/harness_graph.tex",
    "figures/loop.tex",
    "figures/scores-table.tex",
    "figures/scores.pdf",
    "figures/harnessx_architecture.jpg",
    "figures/ucl_logo.png",
)
EXTERNAL_INPUTS = ("figures/ucl_logo.png",)
ANALYSIS_INPUTS = (
    "experiments/analysis/audit_candidate_bucket_and_aim.py",
    "experiments/analysis/audit_proposal_face.py",
)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def aggregate(files: dict[str, str]) -> str:
    payload = "".join(f"{path}\0{value}\n" for path, value in sorted(files.items()))
    return hashlib.sha256(payload.encode()).hexdigest()


def requires_lf(path: Path) -> bool:
    return path.suffix in {".tex", ".py"} or path.name == "latexmkrc"


def has_carriage_return(path: Path) -> bool:
    return requires_lf(path) and b"\r" in path.read_bytes()


def input_paths() -> list[Path]:
    paths: set[Path] = set()
    for pattern in SOURCE_PATTERNS:
        paths.update(path for path in PAPER.glob(pattern) if path.is_file())
    paths.update(ROOT / path for path in ANALYSIS_INPUTS)
    return sorted(paths)


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip()


def build_manifest(
    source_head: str | None = None,
    source_dirty: bool | None = None,
    snapshot_state: str = "pending_stable_source_sync",
    source_sync_aggregate: str | None = None,
    capture_source_paper: Path | None = None,
) -> dict[str, object]:
    invalid_line_endings = [
        path.relative_to(ROOT).as_posix() for path in input_paths() if has_carriage_return(path)
    ]
    if invalid_line_endings:
        raise ValueError(
            "repository text inputs are not LF-normalised: "
            + ", ".join(invalid_line_endings)
        )
    repository_files = {
        path.relative_to(ROOT).as_posix(): digest(path)
        for path in input_paths()
        if path.is_file()
    }
    missing = [
        (PAPER / path).relative_to(ROOT).as_posix()
        for path in EXTERNAL_INPUTS
        if not (PAPER / path).is_file()
    ]
    previous: dict[str, object] = {}
    if MANIFEST.is_file():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prior_source = previous.get("source_paper_inputs")
    if capture_source_paper is not None:
        source_files = {}
        for pattern in SOURCE_PATTERNS:
            for path in capture_source_paper.glob(pattern):
                if path.is_file():
                    relative = path.relative_to(capture_source_paper).as_posix()
                    source_files[f"experiments/docs/thesis/{relative}"] = digest(path)
        source_files = dict(sorted(source_files.items()))
    elif isinstance(prior_source, dict) and isinstance(prior_source.get("files"), dict):
        source_files = prior_source["files"]
    else:
        legacy_files = previous.get("files", {})
        source_files = {
            path: value
            for path, value in legacy_files.items()
            if path.startswith("experiments/docs/thesis/")
        }
    return {
        "schema_version": 2,
        "title": "Provenance-Grounded Self-Evolution of LLM Agent Harnesses",
        "source_repository": "https://github.com/GaryGAO2003/GraphHarnessX.git",
        "source_head": source_head or git("rev-parse", "HEAD"),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_dirty": (
            bool(git("status", "--porcelain")) if source_dirty is None else source_dirty
        ),
        "snapshot_state": snapshot_state,
        "review_state": "draft_not_final_or_accepted",
        "missing_external_prerequisites": missing,
        "source_paper_inputs": {
            "byte_policy": "raw bytes captured from the authorised source checkout",
            "aggregate_sha256": aggregate(source_files),
            "sync_aggregate_sha256": source_sync_aggregate
            or (prior_source or {}).get("sync_aggregate_sha256"),
            "sync_aggregate_path_namespace": "paths relative to experiments/docs/thesis",
            "files": source_files,
        },
        "repository_inputs": {
            "byte_policy": "Git-normalised bytes; paper text and named analysis use LF",
            "aggregate_sha256": aggregate(repository_files),
            "files": repository_files,
        },
        "formatting_only_transforms": [
            "removed trailing ASCII space at chapters/baseline.tex:150",
            "removed trailing ASCII space at chapters/results.tex:387",
            "removed trailing ASCII space at chapters/results.tex:600",
            "removed one extra EOF blank line from chapters/discussion.tex",
            "removed one extra EOF blank line from chapters/introduction.tex",
            "normalised paper text inputs to LF through .gitattributes",
        ],
    }


def check() -> int:
    if not MANIFEST.is_file():
        print(f"ERROR: missing manifest: {MANIFEST.relative_to(ROOT)}")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    repository = manifest.get("repository_inputs", {})
    files = repository.get("files") if isinstance(repository, dict) else None
    if not isinstance(files, dict) or not files:
        failures.append("manifest has no file hashes")
    else:
        for relative, expected in sorted(files.items()):
            path = ROOT / relative
            if not path.is_file():
                failures.append(f"missing input: {relative}")
            elif has_carriage_return(path):
                failures.append(f"non-LF repository input: {relative}")
            elif digest(path) != expected:
                failures.append(f"hash mismatch: {relative}")
    listed = set(files or {})
    actual = {path.relative_to(ROOT).as_posix() for path in input_paths()}
    for relative in sorted(actual - listed):
        failures.append(f"unmanifested input: {relative}")
    if "experiments/docs/thesis/SOURCE-MANIFEST.json" in listed:
        failures.append("manifest must not hash itself")
    if isinstance(files, dict) and repository.get("aggregate_sha256") != aggregate(files):
        failures.append("repository input aggregate mismatch")
    source = manifest.get("source_paper_inputs", {})
    source_files = source.get("files") if isinstance(source, dict) else None
    if not isinstance(source_files, dict) or not source_files:
        failures.append("manifest has no captured source-paper hashes")
    elif source.get("aggregate_sha256") != aggregate(source_files):
        failures.append("source-paper input aggregate mismatch")
    for failure in failures:
        print(f"ERROR: {failure}")
    for relative in manifest.get("missing_external_prerequisites", []):
        print(f"PREREQUISITE: supply authorised external input: {relative}")
    if failures:
        return 1
    print(f"OK: verified {len(listed)} paper inputs")
    print(f"snapshot_state={manifest.get('snapshot_state')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-pending",
        action="store_true",
        help="write hashes for the current checkout as a pending, draft snapshot",
    )
    parser.add_argument("--source-head", help="source checkout commit for a refresh")
    parser.add_argument("--source-dirty", action="store_true")
    parser.add_argument("--snapshot-state", default="pending_stable_source_sync")
    parser.add_argument("--source-sync-aggregate")
    parser.add_argument(
        "--capture-source-paper",
        type=Path,
        help="capture raw paper hashes from this already consistency-checked source tree",
    )
    args = parser.parse_args()
    if args.refresh_pending:
        MANIFEST.write_text(
            json.dumps(
                build_manifest(
                    args.source_head,
                    args.source_dirty,
                    args.snapshot_state,
                    args.source_sync_aggregate,
                    args.capture_source_paper,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"WROTE: {MANIFEST.relative_to(ROOT)}")
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
