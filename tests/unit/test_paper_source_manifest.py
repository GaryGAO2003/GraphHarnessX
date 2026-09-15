from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/check_paper_source.py"
SYNC = ROOT / "scripts/sync_paper_source.py"
MANIFEST = ROOT / "experiments/docs/thesis/SOURCE-MANIFEST.json"


def make_fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "repo"
    (fixture / "scripts").mkdir(parents=True)
    shutil.copy2(CHECKER, fixture / "scripts/check_paper_source.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for relative in manifest["repository_inputs"]["files"]:
        destination = fixture / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    destination = fixture / MANIFEST.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST, destination)
    return fixture


def run_check(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", "scripts/check_paper_source.py"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def test_manifest_accepts_untouched_fixture(tmp_path: Path) -> None:
    result = run_check(make_fixture(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_manifest_rejects_text_and_binary_tampering(tmp_path: Path) -> None:
    fixture = make_fixture(tmp_path)
    tex = fixture / "experiments/docs/thesis/main.tex"
    tex.write_bytes(tex.read_bytes() + b"% tampered\n")
    result = run_check(fixture)
    assert result.returncode == 1
    assert "hash mismatch: experiments/docs/thesis/main.tex" in result.stdout

    fixture = make_fixture(tmp_path / "binary")
    logo = fixture / "experiments/docs/thesis/figures/ucl_logo.png"
    logo.write_bytes(logo.read_bytes() + b"tampered")
    result = run_check(fixture)
    assert result.returncode == 1
    assert "hash mismatch: experiments/docs/thesis/figures/ucl_logo.png" in result.stdout

    fixture = make_fixture(tmp_path / "line-endings")
    table = fixture / "experiments/docs/thesis/figures/scores-table.tex"
    table.write_bytes(table.read_bytes().replace(b"\n", b"\r\n"))
    result = run_check(fixture)
    assert result.returncode == 1
    assert "non-LF repository input" in result.stdout


def test_manifest_rejects_unlisted_input(tmp_path: Path) -> None:
    fixture = make_fixture(tmp_path)
    path = fixture / "experiments/docs/thesis/chapters/unlisted.tex"
    path.write_text("unlisted\n", encoding="utf-8")
    result = run_check(fixture)
    assert result.returncode == 1
    assert "unmanifested input: experiments/docs/thesis/chapters/unlisted.tex" in result.stdout


def test_lf_attribute_is_independent_of_autocrlf(tmp_path: Path) -> None:
    indexed: list[bytes] = []
    for setting in ("true", "false"):
        repo = tmp_path / setting
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "core.autocrlf", setting], cwd=repo, check=True)
        (repo / ".gitattributes").write_text("paper/*.tex text eol=lf\n", encoding="utf-8")
        (repo / "paper").mkdir()
        (repo / "paper/main.tex").write_bytes(b"one\r\ntwo\r\n")
        subprocess.run(["git", "add", ".gitattributes", "paper/main.tex"], cwd=repo, check=True)
        indexed.append(
            subprocess.check_output(["git", "show", ":paper/main.tex"], cwd=repo)
        )
    assert indexed == [b"one\ntwo\n", b"one\ntwo\n"]


def test_real_manifest_survives_autocrlf_checkout(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    staging = tmp_path / "staging"
    checkout = tmp_path / "checkout"
    staging.mkdir()
    checkout.mkdir()
    shutil.copy2(ROOT / ".gitattributes", staging / ".gitattributes")
    for relative in manifest["repository_inputs"]["files"]:
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    subprocess.run(["git", "init", "-q"], cwd=staging, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "true"], cwd=staging, check=True)
    subprocess.run(["git", "add", "."], cwd=staging, check=True)
    subprocess.run(
        ["git", "checkout-index", "--all", f"--prefix={checkout.as_posix()}/"],
        cwd=staging,
        check=True,
    )
    (checkout / "scripts").mkdir(parents=True)
    shutil.copy2(CHECKER, checkout / "scripts/check_paper_source.py")
    destination = checkout / MANIFEST.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST, destination)
    result = run_check(checkout)
    assert result.returncode == 0, result.stdout + result.stderr


def test_sync_normalises_text_after_raw_verification(tmp_path: Path) -> None:
    source = tmp_path / "source"
    paper = source / "experiments/docs/thesis"
    (paper / "figures").mkdir(parents=True)
    raw_text = b"first\r\nsecond\rthird\n"
    raw_binary = b"PNG\x00\r\n\xffpayload"
    (paper / "main.tex").write_bytes(raw_text)
    (paper / "figures/ucl_logo.png").write_bytes(raw_binary)
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=source, check=True)
    subprocess.run(["git", "add", "."], cwd=source, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=source, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    destination = tmp_path / "export"
    result = subprocess.run(
        [
            "python",
            str(SYNC),
            str(source),
            "--source-head",
            head,
            "--destination-paper",
            str(destination),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (paper / "main.tex").read_bytes() == raw_text
    assert (paper / "figures/ucl_logo.png").read_bytes() == raw_binary
    assert (destination / "main.tex").read_bytes() == b"first\nsecond\nthird\n"
    assert (destination / "figures/ucl_logo.png").read_bytes() == raw_binary
    assert "normalised to LF" in result.stdout
