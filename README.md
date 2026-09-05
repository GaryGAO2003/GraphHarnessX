# GraphHarnessX

GraphHarnessX (GHX) is a graph-native harness-evolution loop built on top of
[HarnessX](https://github.com/Darwin-Agent/HarnessX), a composable Python
harness for running LLM agents. HarnessX supplies the run loop, tools,
processors and trajectory store; GHX adds an execution-level causal graph over
every rollout, structured edits to the harness that are addressed through that
graph, and a closed loop that carries evidence from one round to the next.

This repository is the code base of an MSc thesis (UCL, 2026). It contains
the vendored HarnessX core, the AEGIS meta-agent as vendored and patched, the
GHX modules, the GAIA campaign launcher, the recompute scripts behind every
number in the thesis, and the thesis sources.

## Layout

```
harnessx/            HarnessX core (run loop, tools, processors, providers, sandbox, tracing)
harnessx/aegis/      AEGIS meta-agent (Planner / Evolver / Critic / Digester), vendored
harnessx/graph/      execution graph: identity records, unfolding, edits, snapshots
harnessx/ghx/        GHX: round router, ladder, proposal seam, gates, attribution, lift
harnessx/meta_harness/  meta-agent scaffolding shared by AEGIS and GHX
benchmarks/gaia/     GAIA task adapter, evaluator and solver harness
recipe/gaia_evolver/ campaign launcher (run_meta_aegis_ghx.py) and bed-building tools
recipe/gaia_evolver/runs/  campaign archives (on disk, not committed; see README there)
experiments/analysis/      recompute scripts cited by the thesis ledger
experiments/docs/          campaign acceptance notes, novelty notes, thesis sources
docs/                GHX runbooks, design notes and the HarnessX developer guide
patches/aegis/       the P-series patches applied to the vendored AEGIS
tests/               unit and integration tests for everything above
```

## Running a campaign

```
python recipe/gaia_evolver/run_meta_aegis_ghx.py \
    --tasks recipe/gaia_evolver/data/webthinker_gaia_dev_nopixel.json \
    --max-tasks 0 --num-rounds 16 --k-all 1 --search-backend serper
```

`--ghx-level 0` runs the vendored AEGIS baseline (the L0 arm); the default
level runs the GHX arm. All model calls go through a LiteLLM gateway
configured in `.env`. The GAIA task files under `recipe/gaia_evolver/data/`
are gated on HuggingFace and are not committed; rebuild them with
`experiments/build_gaia_subset.py`.

## Recomputing the thesis numbers

Every fact in the thesis ledger (Appendix C) names the script that produces
it. The scripts live under `experiments/analysis/` and read the campaign
archives under `recipe/gaia_evolver/runs/`; the mapping from thesis campaign
labels to archive directories is in `recipe/gaia_evolver/runs/README.md`.

## Thesis

Sources are under `experiments/docs/thesis/` (`THESIS.tex` plus `ch/`).
Compile with two passes of `pdflatex THESIS.tex`; there is no bibtex step.

## Installation

```
python -m venv .venv && .venv/Scripts/activate      # or source .venv/bin/activate
pip install -e ".[dev,analysis]"
pytest
```

On Windows set `PYTHONUTF8=1` before running the launcher or the tests:
several vendored modules and test fixtures read UTF-8 files without an
explicit encoding, and the default code page is not UTF-8.

## Licence

MIT, as HarnessX. See `LICENSE`.
