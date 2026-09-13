import json
import subprocess
import sys
from pathlib import Path


def test_make_nopixel_bed_drops_exact_canonical_three(tmp_path):
    script = Path(__file__).resolve().parents[2] / "recipe/gaia_evolver/tools/make_nopixel_bed.py"
    dropped_ids = [
        "7a4a336d-dcfa-45a0-b014-824c7619e8de",
        "624cbf11-6a41-4692-af9c-36b3e5ca3130",
        "0e9e85b8-52b9-4de4-b402-5f635ab9631f",
    ]
    tasks = [
        {"task_id": task_id, "Question": f"question {index}", "Level": 1}
        for index, task_id in enumerate(dropped_ids + [f"kept-{index}" for index in range(100)])
    ]
    source = tmp_path / "source.json"
    output = tmp_path / "bed.json"
    manifest = tmp_path / "bed.README.md"
    source.write_text(json.dumps(tasks), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), "--input", str(source), "--output", str(output), "--manifest", str(manifest)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    bed = json.loads(output.read_text(encoding="utf-8"))
    assert len(bed) == 100
    assert not set(dropped_ids) & {task["task_id"] for task in bed}
    assert manifest.is_file()
