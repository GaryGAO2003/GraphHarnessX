# GraphHarnessX

GraphHarnessX (GHX) is a research implementation for evolving typed LLM-agent
harness configurations. It builds on [HarnessX](https://github.com/Darwin-Agent/HarnessX).
The persistent harness is represented as a typed executable composition graph;
each invocation can additionally emit an observed execution DAG and provenance
records. These are different objects: an observed ancestor cone is a conservative
over-approximation of what preceded an outcome, not a causal or counterfactual claim.

GHX proposes typed transactional edits, materialises them through the HarnessX
builder, and uses replay and record-backed acceptance checks before retaining a
candidate. The supported contribution is candidate legality, identity, and
checkability. The experiments compare complete L0 and GHX profiles; they do not
identify the effect of an individual graph component, prove improved fault
localisation, or establish a general treatment effect.

This repository accompanies the MSc thesis *Provenance-Grounded Self-Evolution
of LLM Agent Harnesses* (UCL, 2026). The current study comprises six campaigns
with 96 rounds (R0--R15) over a common 100-task text-only bed. The 8,393
evaluations reported as fresh/as-flown exclude other census rows; the seed-3
initial bed contained 103 tasks. Consult the thesis ledger and source manifest
for the exact scope of any result.

## Repository map

| Path | Purpose |
|---|---|
| `harnessx/graph/` | Typed composition graph, identity, edits, snapshots, and provenance links |
| `harnessx/ghx/` | GHX proposal, routing, gates, attribution records, and acceptance logic |
| `recipe/gaia_evolver/` | Campaign launcher and local run layout |
| `experiments/analysis/` | Analysis and audit programs; many require private run archives |
| `experiments/docs/thesis/` | Paper source and its release metadata |
| `docs/` | Developer documentation, runbooks, and retained provenance records |

## Install and run offline checks

```console
python -m venv .venv
# Windows: .venv\Scripts\activate
# POSIX:   source .venv/bin/activate
python -m pip install -e ".[dev,analysis,gaia]"
# PowerShell: $env:PYTHONUTF8 = "1"
# POSIX:      export PYTHONUTF8=1
pytest
python scripts/check_paper_source.py
```

For model-backed work, copy `.env.example` to `.env` and set only the provider
credentials you need. `.env` is ignored.

The test suite and paper-source checker do not need campaign archives or model
credentials. A successful source check verifies only the files present in the
release manifest; it does not reproduce experimental results.

## Data and campaign boundary

GAIA data is gated upstream and is intentionally absent. After obtaining the
required Hugging Face access, first materialise the 103-task text-only bed:

```console
python experiments/build_gaia_subset.py --size 103 \
  --out recipe/gaia_evolver/data/webthinker_gaia_dev.json
python recipe/gaia_evolver/tools/make_nopixel_bed.py \
  --input recipe/gaia_evolver/data/webthinker_gaia_dev.json
```

The second command drops the three fixed, documented task IDs and fails unless
all three are present; its default output is the canonical
`webthinker_gaia_dev_nopixel.json` plus a companion decision manifest. A generic
`build_gaia_subset.py --size 100` sample is not the paper's canonical bed.

Raw campaign archives are several gigabytes and are not committed. Analysis
programs that read `recipe/gaia_evolver/runs/` require those separately supplied
archives; absence of the archives is an unmet prerequisite, not a zero-result
dataset. Launching a new campaign additionally requires model/search credentials,
a LiteLLM-compatible endpoint, and paid inference. See
[`recipe/gaia_evolver/runs/README.md`](recipe/gaia_evolver/runs/README.md).

## Paper

See [`experiments/docs/thesis/README.md`](experiments/docs/thesis/README.md) for
build requirements and scientific boundaries. `SOURCE-MANIFEST.json` records the
source repository, source commit, review state, and SHA-256 hashes of the paper
inputs. The manifest deliberately excludes itself from its file list.

## Licence

MIT. See `LICENSE`.
