# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Reproduce the population bridge used by the thesis evidence audit.

The script reads only the six claim-bearing campaigns and their formal R0..R15
window.  It emits counts and provenance, never task questions or answers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True


RUNS = {
    "baseline-seed1": ("baseline-seed1", "M22_L0_ghx0"),
    "baseline-seed2": ("baseline-seed2", "M28_L0_s2"),
    "baseline-seed3": ("baseline-seed3", "M29_L0_s3"),
    "ghx-seed1": ("ghx-seed1", "M26_100x16b"),
    "ghx-seed2": ("ghx-seed2", "M28_GHX_s2"),
    "ghx-seed3": ("ghx-seed3", "M29_GHX_s3"),
}
BASELINES = tuple(k for k in RUNS if k.startswith("baseline"))
GRAPH = tuple(k for k in RUNS if k.startswith("ghx"))
WINDOW = range(16)
UUIDISH = re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{10,}\b", re.I)
EXPECTED_COMPOSE_REJECTS = {
    ("baseline-seed1", 2, "C-R2-03"),
    ("baseline-seed2", 6, "C-R6-01"),
    ("baseline-seed2", 15, "C-R15-01"),
    ("baseline-seed3", 6, "C-R6-02"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_hash(repo: Path, paths: list[Path]) -> dict:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(repo).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return {"files": len(paths), "sha256_path_and_content_manifest": digest.hexdigest()}


def json_lines(path: Path):
    with path.open(encoding="utf-8", errors="replace") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError as exc:
                    raise ValueError(f"invalid JSON at {path}:{number}") from exc


def predicted_ids(path: Path) -> list[str]:
    """Parse tasks_will_unlock using the production audit's three-shape rule."""
    text = path.read_text(encoding="utf-8", errors="replace")
    start = text.find("tasks_will_unlock")
    if start < 0:
        return []
    window = text[start : start + 3000]
    stop = re.search(
        r"tasks_will_stabilize|tasks_at_risk|tasks_will_pass|"
        r"attribution_signature|file_changes|capability_evidence",
        window[len("tasks_will_unlock") :],
    )
    if stop:
        window = window[: len("tasks_will_unlock") + stop.start()]
    return list(dict.fromkeys(match.group(0) for match in UUIDISH.finditer(window)))


def load_subset(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else next(
        (data[key] for key in ("tasks", "data", "examples") if isinstance(data.get(key), list)), []
    )
    ids = {str(row.get("task_id") or row.get("id")) for row in rows if isinstance(row, dict)}
    ids.discard("None")
    if len(ids) != 100:
        raise ValueError(f"expected 100 canonical subset task ids, found {len(ids)}")
    return ids


def audit_gate_and_landing(run_root: Path) -> dict:
    gates = []
    for row in json_lines(run_root / "audit.jsonl"):
        if row.get("kind") == "gate" and int(row.get("round", -1)) in WINDOW:
            gates.append(row)
    unique = {(int(row["round"]), str(row["payload"]["cid"])): row for row in gates}
    if len(unique) != len(gates):
        raise ValueError(f"duplicate gate events in {run_root}")
    passed_keys = set()
    for key, row in unique.items():
        results = row["payload"].get("results") or {}
        passed = all(value is True or (isinstance(value, dict)
                     and value.get("ok", value.get("passed"))) for value in results.values())
        if passed:
            passed_keys.add(key)
    failed = len(unique) - len(passed_keys)
    ships = json.loads((run_root / "scoreboard.json").read_text(encoding="utf-8")).get("ships") or []
    landings = {(int(row["round"]), str(row["cid"])) for row in ships if int(row["round"]) in WINDOW}
    return {"gate_event_count": len(gates), "gate_count": len(unique), "gate_failures": failed,
            "gate_passes": len(passed_keys), "landings": len(landings),
            "passed_keys": passed_keys, "landing_keys": landings}


def compose_rejections(roots: dict[str, Path], gates: dict[str, dict]) -> list[dict]:
    found = []
    discovered = set()
    for alias in BASELINES:
        records = {(int(row.get("round", -1)), str(row.get("candidate_id"))): row
                   for row in json_lines(roots[alias] / "data" / "rejected_candidates.jsonl")}
        for round_number, cid in sorted(gates[alias]["passed_keys"] - gates[alias]["landing_keys"]):
            row = records.get((round_number, cid))
            reason = str((row or {}).get("rejection_text_excerpt", ""))
            if not reason.startswith("compose refused this candidate:"):
                raise ValueError(f"missing compose refusal for {alias} R{round_number} {cid}")
            discovered.add((alias, round_number, cid))
            found.append({"run": alias, "round": round_number, "cid": cid, "reason": reason})
    if discovered != EXPECTED_COMPOSE_REJECTS:
        raise ValueError(f"compose-refusal set changed: {sorted(discovered)}")
    return found


def localization_and_f9a(root: Path) -> tuple[dict, dict]:
    ships = json.loads((root / "scoreboard.json").read_text(encoding="utf-8")).get("ships") or []
    fresh = {}
    for row in json_lines(root / "data" / "task_history.jsonl"):
        k = int(row.get("round", -1))
        if k in WINDOW and not row.get("carried"):
            fresh[(k, str(row.get("task_id")))] = bool(row.get("passed"))
    localized, empty_unlock, no_eligible = [], [], []
    eligible = hits = predictions = 0
    for ship in ships:
        k, cid = int(ship["round"]), str(ship["cid"])
        if k not in WINDOW:
            continue
        manifest = root / f"R{k}" / "candidates" / f"{cid}.md"
        predicted = predicted_ids(manifest)
        if not predicted:
            empty_unlock.append((k, cid))
        selected = [task for task in predicted
                    if fresh.get((k - 1, task)) is False and (k, task) in fresh]
        if selected:
            localized.append((k, cid))
            predictions += len(selected)
            eligible += len(selected)
            hits += sum(fresh[(k, task)] for task in selected)
        elif predicted:
            no_eligible.append((k, cid))
    return ({"landings": len([s for s in ships if int(s["round"]) in WINDOW]),
             "localization_landings": len(localized),
             "excluded_empty_unlock": [{"round": k, "cid": cid} for k, cid in empty_unlock],
             "excluded_no_eligible_prediction": [{"round": k, "cid": cid} for k, cid in no_eligible]},
            {"candidates": len(localized), "predictions": predictions,
             "eligible": eligible, "hits": hits})


def f1_and_f4(repo: Path, root: Path, subset: set[str]) -> tuple[dict, dict]:
    populated, traces, digest_files = [], [], []
    for stored_round in range(1, 17):
        trajectories = root / f"R{stored_round}" / "trajectories"
        files = sorted(trajectories.glob("*_r0.jsonl")) if trajectories.is_dir() else []
        if files:
            populated.append({"storage_round": stored_round, "task_round": stored_round - 1,
                              "files": len(files)})
            traces.extend(files)
        digests = root / f"R{stored_round}" / "digests"
        if digests.is_dir():
            digest_files.extend(p for p in digests.glob("*.md") if p.stem in subset)
    trace_ids = {p.name.rsplit("_r0.jsonl", 1)[0] for p in traces}
    expected_cells = {(k, task) for k in WINDOW for task in subset}
    present_cells = {(item["task_round"], p.name.rsplit("_r0.jsonl", 1)[0])
                     for item in populated for p in (root / f"R{item['storage_round']}" / "trajectories").glob("*_r0.jsonl")
                     if p.name.rsplit("_r0.jsonl", 1)[0] in subset}

    module_path = repo / "harnessx" / "aegis" / "stages" / "trace_facts.py"
    spec = importlib.util.spec_from_file_location("audit_trace_facts", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    use = Counter()
    for path in traces:
        facts = module.extract_trace_facts(path.name.rsplit("_r0.jsonl", 1)[0], [path])
        for call in facts.tool_calls:
            if call.return_len > 0:
                use["abstain" if call.next_uses_result is None else "yes" if call.next_uses_result else "NO"] += 1
    payloads = sum(use.values())

    missing_cells = sorted(expected_cells - present_cells)
    expected_digests = {(item["storage_round"], task) for item in populated for task in subset}
    present_digests = {(r, p.stem) for r in range(1, 17)
                       for p in (root / f"R{r}" / "digests").glob("*.md") if p.stem in subset}
    missing_digest = sorted(expected_digests - present_digests)
    return ({"storage_semantics": "Rk stores task batch k-1", "populated": populated,
             "trace_files": len(traces), "subset_trace_files": len(present_cells),
             "extra_trace_files": len(traces) - len(present_cells), "trace_task_ids": len(trace_ids),
             "missing_task_rounds": sorted({k for k, _ in missing_cells}),
             "missing_subset_cells": len(missing_cells), "tool_payloads": payloads,
             "next_uses_result": dict(use)},
            {"digest_files": sum(len(list((root / f"R{r}" / "digests").glob("*.md"))) for r in range(1, 17)),
             "subset_digest_files": len(digest_files), "missing_available_dossiers": len(missing_digest),
             "missing": [{"storage_round": k, "task_id": task} for k, task in missing_digest]})


def f51(roots: dict[str, Path], subset: set[str]) -> dict:
    per_run, total = {}, 0
    for alias, root in roots.items():
        last = {}
        for row in json_lines(root / "data" / "task_history.jsonl"):
            k, task = int(row.get("round", -1)), str(row.get("task_id"))
            if k in WINDOW and task in subset:
                last[(k, task)] = row
        fresh = sum(not row.get("carried") for row in last.values())
        per_run[alias] = fresh
        total += fresh
    return {"definition": "last row per (round, task), canonical subset, R0..R15, not carried",
            "per_run": per_run, "total": total}


def build(repo: Path) -> dict:
    runs_dir = repo / "recipe" / "gaia_evolver" / "runs"
    subset_path = repo / "recipe" / "gaia_evolver" / "data" / "webthinker_gaia_dev_nopixel.json"
    roots = {}
    resolved = {}
    for alias, choices in RUNS.items():
        matches = [runs_dir / name for name in choices if (runs_dir / name).is_dir()]
        if not matches:
            raise FileNotFoundError(f"no run directory for {alias}; tried {choices}")
        roots[alias] = matches[0]
        resolved[alias] = matches[0].relative_to(repo).as_posix()
    required = [subset_path]
    for root in roots.values():
        required.extend([root / "audit.jsonl", root / "scoreboard.json",
                         root / "data" / "rejected_candidates.jsonl",
                         root / "data" / "task_history.jsonl"])
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing required inputs: " + ", ".join(missing))
    subset = load_subset(subset_path)
    gates = {alias: audit_gate_and_landing(roots[alias]) for alias in RUNS}
    localization, f9a = localization_and_f9a(roots["baseline-seed1"])
    f1, f4 = f1_and_f4(repo, roots["baseline-seed1"], subset)
    report = {
        "scope": {"run_aliases": list(RUNS), "resolved_run_paths": resolved,
                  "formal_task_window": [0, 15],
                  "canonical_subset": str(subset_path.relative_to(repo)), "subset_tasks": len(subset)},
        "baseline_gate": {alias: {k: v for k, v in gates[alias].items()
                                   if k not in ("passed_keys", "landing_keys")} for alias in BASELINES},
        "graph_gate": {"gate_count": sum(gates[a]["gate_count"] for a in GRAPH),
                       "gate_failures": sum(gates[a]["gate_failures"] for a in GRAPH),
                       "gate_passes": sum(gates[a]["gate_passes"] for a in GRAPH)},
        "compose_rejections": compose_rejections(roots, gates),
        "baseline_seed1_localization": localization,
        "F9a": f9a, "F1": f1, "F4": f4, "F51": f51(roots, subset),
        "provenance": {"inputs": [{"path": path.relative_to(repo).as_posix(), "sha256": sha256(path)}
                                    for path in required]},
    }
    manifests = [path for root in roots.values() for r in WINDOW
                 for path in (root / f"R{r}" / "candidates").glob("*.md")]
    trace_inputs = [path for r in range(1, 17)
                    for path in (roots["baseline-seed1"] / f"R{r}" / "trajectories").glob("*_r0.jsonl")]
    digest_inputs = [path for r in range(1, 17)
                     for path in (roots["baseline-seed1"] / f"R{r}" / "digests").glob("*.md")]
    trace_facts_path = repo / "harnessx" / "aegis" / "stages" / "trace_facts.py"
    report["provenance"]["production_trace_facts"] = {
        "path": trace_facts_path.relative_to(repo).as_posix(), "sha256": sha256(trace_facts_path)}
    report["provenance"]["candidate_manifests"] = aggregate_hash(repo, manifests)
    report["provenance"]["first_replicate_traces"] = aggregate_hash(repo, trace_inputs)
    report["provenance"]["digests"] = aggregate_hash(repo, digest_inputs)
    expected = {
        "baseline_gate": [(18, 3, 15, 14), (21, 8, 13, 11), (20, 7, 13, 12)],
        "graph_gate": (55, 26, 29), "localization": (14, 13), "f9a": (13, 50, 25),
        "f1": (1442, 1400, 42, 200, 11966, 8971, 973, 2022),
        "f4": (1441, 1, 10, "65638e28-7f37-4fa7-b7b9-8c19bb609879"),
        "f51": ([1600, 1600, 1600, 1084, 1230, 1162], 8276),
    }
    baseline_actual = [(gates[a]["gate_count"], gates[a]["gate_failures"], gates[a]["gate_passes"], gates[a]["landings"]) for a in BASELINES]
    checks = [
        baseline_actual == expected["baseline_gate"],
        (report["graph_gate"]["gate_count"], report["graph_gate"]["gate_failures"], report["graph_gate"]["gate_passes"]) == expected["graph_gate"],
        (localization["landings"], localization["localization_landings"]) == expected["localization"],
        (f9a["candidates"], f9a["predictions"], f9a["hits"]) == expected["f9a"],
        (f1["trace_files"], f1["subset_trace_files"], f1["extra_trace_files"], f1["missing_subset_cells"], f1["tool_payloads"], f1["next_uses_result"].get("NO"), f1["next_uses_result"].get("yes"), f1["next_uses_result"].get("abstain")) == expected["f1"],
        (f4["digest_files"], f4["missing_available_dossiers"], f4["missing"][0]["storage_round"], f4["missing"][0]["task_id"]) == expected["f4"],
        ([report["F51"]["per_run"][a] for a in RUNS], report["F51"]["total"]) == expected["f51"],
    ]
    report["verification"] = {"all_expected_counts_match": all(checks), "checks": checks}
    if not all(checks):
        raise AssertionError(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", type=Path, help="write machine-readable report (must not exist)")
    args = parser.parse_args()
    report = build(args.repo.resolve())
    print(json.dumps(report, indent=2))
    if args.json:
        output = args.json.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
