# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Cross-campaign cost attribution: M24 / M25 / M26b, per-round and per-component."""
import json
import re
from pathlib import Path

RUNS = [
    ('M24', 'recipe/gaia_evolver/runs/M24_103x3'),
    ('M24r3+', 'recipe/gaia_evolver/runs/M24_103x3'),  # same dir, r3plus log
    ('M25', 'recipe/gaia_evolver/runs/M25_103x16'),
    ('M26b', 'recipe/gaia_evolver/runs/ghx-seed1'),
]


def logs_for(run_dir):
    p = Path(run_dir)
    return sorted(p.parent.glob(p.name + '*.err.log'))


def parse(run_dir):
    sp, ev, cr = [], [], []
    for lg in logs_for(run_dir):
        txt = lg.read_text(encoding='utf-8', errors='replace')
        sp += [float(x) for x in re.findall(r'Stage P: digesters=(?:\d+)/(?:\d+) cost=\$([\d.]+)', txt)]
        ev += [float(x) for x in re.findall(r'Evolver R\d+: exit=\w+ steps=\d+ cost=\$([\d.]+)', txt)]
        cr += [float(x) for x in re.findall(r'Critic R\d+: exit=\w+ steps=\d+ cost=\$([\d.]+)', txt)]
    return sp, ev, cr


for name, d in RUNS[1:]:
    cur = Path(d) / 'curves.json'
    if not cur.exists():
        print(name, 'NO curves.json at', cur)
        continue
    c = json.load(open(cur, encoding='utf-8'))
    sp, ev, cr = parse(d)
    batch = [float(e.get('cost_usd') or 0) for e in c]
    steps = [int(e.get('total_steps') or 0) for e in c]
    tasks = [int(e.get('total_tasks') or 0) for e in c]
    fresh = [e.get('fresh_tasks') for e in c]
    print(f'\n===== {name}  ({d}) =====')
    print(f'rounds={len(c)} tasks/round={tasks[0] if tasks else "?"}')
    print('batch $/round:', ' '.join(f'{x:.0f}' for x in batch))
    print('fresh tasks  :', ' '.join(str(f if f is not None else tasks[i]) for i, f in enumerate(fresh)))
    print('steps/round  :', ' '.join(str(s) for s in steps))
    print('StageP       :', ' '.join(f'{x:.0f}' for x in sp))
    print('Evolver      :', ' '.join(f'{x:.0f}' for x in ev))
    print('Critic       :', ' '.join(f'{x:.0f}' for x in cr))
    tot = sum(batch) + sum(sp) + sum(ev) + sum(cr)
    print(f'TOTAL batch=${sum(batch):.0f} stageP=${sum(sp):.0f} evolver=${sum(ev):.0f} critic=${sum(cr):.0f} => ${tot:.0f}')
    full = [b for i, b in enumerate(batch) if fresh[i] in (None, tasks[i])]
    noop = [b for i, b in enumerate(batch) if fresh[i] not in (None, tasks[i])]
    if full:
        print(f'  full-round batch mean=${sum(full)/len(full):.1f} (n={len(full)})')
    if noop:
        print(f'  noop-round batch mean=${sum(noop)/len(noop):.1f} (n={len(noop)})')
    if sp:
        print(f'  StageP mean=${sum(sp)/len(sp):.1f}/round')
