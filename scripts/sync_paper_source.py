#!/usr/bin/env python3
"""Stage and verify a paper-source snapshot from another Git checkout."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "experiments/docs/thesis"
PATTERNS = (
    "main.tex", "preamble.tex", "macros.tex", "latexmkrc",
    "frontmatter/*.tex", "chapters/*.tex", "appendices/*.tex",
    "bibliography/references.tex", "figures/*.tex", "figures/*.pdf",
    "figures/*.jpg", "figures/*.png",
)


def hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for pattern in PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                result[path.relative_to(root).as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    return dict(sorted(result.items()))


def is_text_input(relative: str) -> bool:
    path = Path(relative)
    return path.suffix == ".tex" or path.name == "latexmkrc"


def export_input(source: Path, destination: Path, relative: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if is_text_input(relative):
        raw = source.read_bytes()
        destination.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
    else:
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="stable GraphHarnessX checkout")
    parser.add_argument("--source-head", required=True, help="expected full source commit")
    parser.add_argument(
        "--allow-dirty-source",
        action="store_true",
        help="explicitly capture a dirty source after before/after hash checks",
    )
    parser.add_argument(
        "--destination-paper",
        type=Path,
        default=TARGET,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    source_repo = args.source.resolve()
    source = source_repo / "experiments/docs/thesis"
    if source_repo == ROOT.resolve():
        parser.error("source and destination repositories must differ")
    actual_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_repo, text=True
    ).strip()
    if actual_head != args.source_head:
        parser.error(f"source HEAD is {actual_head}, expected {args.source_head}")
    source_dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain", "--", "experiments/docs/thesis"],
        cwd=source_repo,
        text=True,
    ).strip())
    if source_dirty and not args.allow_dirty_source:
        parser.error("source paper tree is dirty; obtain an explicit stable snapshot first")
    before = hashes(source)
    if not before:
        parser.error("source contains no paper inputs")
    with tempfile.TemporaryDirectory(prefix="ghx-paper-sync-") as temporary:
        staged = Path(temporary) / "thesis"
        for relative in before:
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, destination)
        after = hashes(source)
        staged_hashes = hashes(staged)
        if before != after or before != staged_hashes:
            parser.error("source changed while being read; refusing torn snapshot")
        for relative in before:
            destination = args.destination_paper / relative
            export_input(staged / relative, destination, relative)
    snapshot_digest = hashlib.sha256(
        "".join(f"{path}\0{value}\n" for path, value in before.items()).encode()
    ).hexdigest()
    print(f"SYNCED: {len(before)} consistent inputs from {actual_head}")
    print(f"source_dirty={str(source_dirty).lower()} snapshot_sha256={snapshot_digest}")
    print("EXPORT: TeX/latexmkrc normalised to LF; binary inputs copied byte-for-byte")
    print("NEXT: review the diff, update PAPER_STATUS.md, then refresh the manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
