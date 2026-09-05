# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""M26b same-config flip rate from noop-scoped windows (F15's graph-arm
counterpart, whitelist).

A noop round re-runs a subset under a semantically unchanged config, so a
(k-1, k) pair where round k has evolve_status == "noop" is a same-config
re-measurement for every task fresh in both rounds.  Flip = outcome differs.
(config_hash is NOT used: it drifts even under noop — known quirk.)
"""
import json
from pathlib import Path

RUN = Path(r"D:\PycharmProj\HarnessX") / "recipe/gaia_evolver/runs/ghx-seed1"

curves = {int(c["round"]): c for c in json.loads((RUN / "curves.json").read_text(encoding="utf-8"))}
fresh: dict[tuple[int, str], bool] = {}
for line in (RUN / "data" / "task_history.jsonl").open(encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if r.get("carried"):
        continue
    fresh[(int(r.get("round", -1)), str(r.get("task_id")))] = bool(r.get("passed"))

statuses = {k: c.get("evolve_status") for k, c in sorted(curves.items())}
print("rounds:", " ".join(f"R{k}:{v}" for k, v in statuses.items()))

pairs = flips = 0
per_window = []
for k in sorted(curves):
    if k == 0:
        continue
    if str(curves[k].get("evolve_status")) != "noop":
        continue
    w_pairs = w_flips = 0
    for (r, t), v in fresh.items():
        if r == k - 1 and (k, t) in fresh:
            w_pairs += 1
            w_flips += 1 if fresh[(k, t)] != v else 0
    if w_pairs:
        per_window.append((k, w_flips, w_pairs))
        pairs += w_pairs
        flips += w_flips

for k, f, n in per_window:
    print(f"  window R{k-1}->R{k} (noop): flips {f}/{n} = {100*f/n:.1f}%")
print(f"\nM26b noop-window same-config flip rate: {flips}/{pairs} = "
      f"{100*flips/pairs if pairs else 0:.1f}%  (M22 F15 reference: 169/824 = 20.5%)")
