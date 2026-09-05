# Project Report — GHX: Provenance-Grounded Self-Evolution of LLM Agent Harnesses

> Purpose of this document: a self-contained, CV-oriented description of the master's thesis project, written so that a downstream agent can lift résumé bullets, a project summary, or interview talking points from it without reading the thesis. Every number below is traced to the thesis fact ledger (F-numbers in brackets) and is recomputable from a script in `experiments/analysis/`.

---

## 0. CV-ready summary block

**Project title.** Provenance-Grounded Self-Evolution of LLM Agent Harnesses: A Graph-Native Runtime, a Pre-Registered Falsification, and the Missing Efficacy Readout (M.Sc. thesis, 2026).

**One-line description.** Designed and built GHX, a graph-native runtime that makes an LLM agent's execution a typed, queryable, replayable object, and used it to drive a self-evolving agent harness to **70%+ accuracy on the text-only GAIA benchmark** (final-round 72.0% and 76.0% on two independent seeds, three-seed mean 71.7%, best round 76%), state-of-the-art territory for this setting, with a `deepseek-v4-flash` solver and `deepseek-v4-pro` meta-roles behind a LiteLLM gateway.

**Suggested résumé bullets (pick 3–5).**

- Built **GHX**, a graph-native harness runtime for LLM agents (~11.6k lines Python, 37 modules, 357 unit tests) that records every processor, tool call and nested agent as a typed execution DAG and exposes causal-ancestor queries, replay verification and an atomic, typed candidate-edit surface.
- Drove a four-role self-evolving harness loop (Digester / Planner / Evolver / Critic) on GAIA text-only tasks to **72–76% final-round accuracy (three-seed mean 71.7%)**, climbing from a 57–59% starting configuration within 16 self-improvement rounds.
- Ran the **first independent, large-scale execution of a published self-evolving harness**: 6 claim-bearing campaigns, 96 scored rounds, 8,393 fresh task evaluations, replicated across three seeds per arm, ~$5k of compute managed end-to-end.
- Discovered by construction proof that the loop's core evidence column ("tool output was used") was blind to short answers; replaced it with graph-derived provenance, driving the false signal from **86% of dossiers to 0 of 859** and doubling verified citation anchors per digest (1.75 → 3.50) at one-seventh the validator failure rate (11.7% → 1.5%).
- Introduced a **typed transactional candidate surface** (seven graph operations, five-stage atomic commit, genotype/deployment/phenotype hash identity) that halved the share of malformed candidate edits (30.5% → 14.5%) and added a sixth acceptance gate that caught 18 candidates naming execution nodes that never existed.
- Established the benchmark's **noise floor** (21.0 / 20.1 / 19.2% same-configuration outcome flip rate across three seeds, 2,000 task pairs on one 100-task bed) and designed a pre-registered, same-window paired efficacy protocol with stopping arithmetic, canary tasks and mechanism endpoints.
- Proposed the **readout ladder (L0–L3)**, a levels-of-evidence standard for self-evolving agents, with L0–L2 implemented live in GHX and L3 demonstrated by hand.

**Keywords.** LLM agents · agent harness · self-evolving / self-improving agents · execution provenance · typed graph runtime · causal ancestor cones · replay verification · GAIA benchmark · experimental design · pre-registration · noise-floor measurement · Python · asyncio · LiteLLM · DeepSeek.

---

## 1. Context and problem

An LLM agent is a model plus a *harness*: the system prompt, tool set, memory strategy, control processors and loop logic around the model. The harness is often the dominant performance lever, so a growing literature evolves it automatically: a meta-loop reads the agent's trajectories, proposes an edit to the harness, and keeps the edit if the benchmark score goes up.

The project started from one published, code-released harness-level self-evolving loop. Its meta-loop has four roles:

| Role | Job |
|---|---|
| **Digester** | Reads each task trajectory and writes a per-task dossier (what fired, what seemed to matter, how it failed). |
| **Planner** | Ranks the repair directions the dossiers suggest. |
| **Evolver** | Authors a candidate edit to config, tools, prompt or processor pipeline. |
| **Critic** | Reviews the candidate and may veto it. |

Survivors pass a ladder of acceptance gates and become the next round's configuration. The loop edits itself through free text: the Evolver writes a manifest and a `config.yaml` as prose, and nothing downstream can confirm that the candidate document and the applied change describe the same intervention.

Two questions drove the work:

1. **Is the loop's evidence about its own execution actually true?** The dossiers are built by pattern-matching over text logs. If that evidence is wrong, every downstream decision is wrong.
2. **Can execution be made a first-class, machine-checkable object**, so that "what happened during this run" is answered by reading a graph rather than by string matching, and so that a proposed edit can be verified against the recorded execution before it ships?

---

## 2. What was built: GHX, a graph-native harness runtime

GHX sits in `harnessx/ghx/` (37 modules, ~11.6k lines) on top of HarnessX, a composable Python agent harness (`Harness.run(task)` → run loop → processors, providers, tool registry, trajectory with rewards). It attaches to the **unmodified, byte-pinned** official self-evolving loop from outside; every mechanism hooks a seam and restores it in `finally`; every flag defaults off.

### 2.1 Design constraints (fixed before any code)

- **Byte-pinned substrate.** The official system is vendored at a fixed revision under a sha256 manifest enforced by the test suite.
- **Zero core edits.** No byte of the vendored tree is modified; all integration is at seams.
- **Seams restore unconditionally.** A crash cannot leave a modified loop behind for the next round.
- **Flags default off.** Arm separation is a property of configuration, not operator discipline.
- **A gate never seen to fail is not yet a gate.** Every acceptance gate is mutation-tested with a deliberately malformed candidate before it counts as existing.

### 2.2 Components

**Typed executable composition graph.** The harness configuration is re-expressed as a typed graph: six node types (runloop hook points, processors, typed slots, bundles, skills, tools) and twelve edge types (ten declared/structural, two observed at runtime: control and data). Two properties are enforced by test: the graph is the *single ordering authority* for processor order, and a *parity door* guarantees the graph-driven runloop is byte-identical in behaviour to the legacy runloop.

**Unfolded execution graph U.** Per invocation, the runtime writes a DAG over processors, tool calls and nested agents. Acyclicity is constructive (global ordinals, edges only run forward). Data edges are computed by reaching definitions over slot writes/reads and cross-checked against runtime slot provenance. Three honesty rules: edges are never invented; unattributable events are marked `UNGRAPHED` rather than guessed; cross-layer frontiers (nested agents, external calls) are reported, never silently crossed.

**Identity: three nested hashes.** *Genotype* (structural config identity, dedup key) ⊆ *deployment* (plus runtime overlay: what actually ran) ⊆ *phenotype* (plus observed execution edges: what it actually did). The containment is nailed by a hash-contract test. This separates "same proposal", "same deployed thing" and "same behaviour", which a free-text edit surface conflates.

**Causal queries: ancestor cones.** Given a failing event, its ancestor cone (full: control + data; data-only variant) is the sound over-approximation of what could have shaped it. Over an early failed cohort (n=33), the median trajectory is 1,186 nodes / 606k characters; its full cone is **48 nodes**, its data cone **42**, about **4%** of the invocation.

**Evidence integration.** Failure cones and cross-task facts are injected into the Digester and Planner context; passing tasks enter as the contrast side (passing-cone signatures, flip diffs, the pass/fail partition line). The rendered cone is a *map, not a payload*: median **15.5 kB** against the **87.4 kB** trajectory it competes with for context (ratio 0.12). Every injection is recorded in a manifest so "what did the role actually see" is answerable without trusting the role.

**Verification surfaces.**
- A **sixth acceptance gate** (`graph_existence`): a candidate claiming to repair a node must name a node that exists in the recorded failing execution. Where no replay graph exists, the gate records an honest pass with `checked=False`.
- A **replay gate**: of fifteen checks, seven produced structural refusals of the form "edited, but never ran"; no refused candidate was shipped [F11].

**Typed transactional candidate surface** (`harnessx/ghx/graph_proposals.py`). Every mutation is one of seven typed operations on the processor plane (`insert_node`, `remove_node`, `replace_same_group`, `change_dependency`, `swap_subgraph`, `mutate_inactive`, `mutate_params`), plus two config-section operations for tools and prompt edits via `mutate_params`. Mutations commit as an atomic group through a five-stage transaction or are rejected whole; both artifacts (manifest and `config.yaml`) are machine-generated on every call and verified by a write → reload → re-graph genotype round-trip.

**Runtime policy engine.** Rule slots the loop itself can fill at run time; a loop-authored rule fired 19 times across 10 tasks with zero collateral damage [F11, F20].

**Supporting machinery** (also in `harnessx/ghx/`): flip ledger, paired same-window gate and reader, anchor repair for digest citations, attribution backfill, variance profiler, loop-health checker, noop-round gate check, candidate scoping, evidence-file manifests, ladder bookkeeping.

### 2.3 The readout ladder

GHX is organised around a four-rung levels-of-evidence ladder for any proposed harness edit, offered as a standard for the field:

| Rung | Question | Status in GHX |
|---|---|---|
| **L0** | Is it in the deployed configuration? | Landing gates |
| **L1** | Did it ever execute? | Replay gate, live (seven refusals) |
| **L2** | Did it fire, and on what? | Fire / false-positive counts over U, produced by the loop itself |
| **L3** | Did firing change outcomes? | Built and exercised by hand via the efficacy-trial protocol (§4.3) |

Every surveyed self-evolving harness admits candidates at L0 only. GHX makes stating the rung mechanical for L1 and L2.

---

## 3. Experimental campaign

### 3.1 Bed, model, scale

- **Benchmark:** text-only subset of GAIA (103 tasks; cross-arm readings recomputed on the 100-task no-pixel subset common to all campaigns). Of those 100, 97 are reachable; 3 were never solved in 9,600 evaluations.
- **Model:** solver `deepseek-v4-flash` (thinking on); the four meta roles and the judge `deepseek-v4-pro`; all through a LiteLLM gateway, in every campaign.
- **Scale:** six claim-bearing campaigns, **96 rounds, 8,393 fresh task evaluations** (whitelist evidence side), three seeds per arm, 16 scored rounds per campaign. Replication seed-pairs cost $1,467 and $1,466 in clean spend each. This is, to our knowledge, the first independent execution of the official system at scale [F19].
- **Task parameters:** `--max-steps 20`, pass@1 discipline (mixed-k passes do not count), k=1.
- **Operations:** unplanned machine restarts and a twelve-hour gateway outage were handled by quarantining poisoned rounds, washing histories back to a verified clean prefix, and re-flying from byte-identical round-head configurations; every same-config window used in statistics is a verified clean pair.

### 3.2 Headline result: 70%+ on GAIA text-only

The GHX-driven self-evolving loop (graph recording + graph evidence + graph verification + typed candidate surface, all levels on) reached the following on the 100-task no-pixel subset [F44, F45, F46]:

| Seed | Round 0 | Final round (R15) | Best round | Plateau mean R3–R15 |
|---|---|---|---|---|
| 1 | 67% | 67% | — | 64.9 ± 3.2 |
| 2 | 59% | **72.0%** | 73% | 65.5 ± 6.2 |
| 3 | 57% | **76.0%** | 76% | 67.9 ± 4.3 |
| **Mean** | | **71.7%** | | 66.1 |

Two of three seeds finished above 70%, the three-seed final-round mean is 71.7%, and the best single round is 76%. Within a campaign the loop genuinely improves: fitting a line to rounds R1–R15 gives a **positive slope in all six campaigns** (six positives out of six, p ≈ 0.016) [F47]; the graph-arm slopes are +0.53 / +1.39 / +0.64 tasks per round, with fitted within-campaign gains of +7.4 / +19.5 / +9.0 pp.

### 3.3 What the graph did to the evidence

- **False signal removed.** The official loop grades a tool call as "used" only if the next assistant message repeats ≥20 characters of its output verbatim; GAIA answers have median length 9. The column therefore could not register the use of a short fact by construction, labelled **75.0%** of answer-carrying calls as not referenced [F2], and that verdict reached **86.0%** of dossiers [F4]. Under GHX, **0 of 859** post-fix dossiers carry it [F7].
- **Citation integrity.** Graph-arm digests carry **3.50** verified citation anchors each vs 1.75 without, and the validator failure rate falls from **11.7% to 1.5%** [F52]: twice the citing at a seventh of the failure rate.
- **Evidence gets smaller and better founded.** Cone ≈ 4% of nodes; rendered cone 0.12 of trajectory bytes; k=1 observations suffice for the loop to reach the correct repair family [F26–F30].
- **Candidate legality.** The sixth gate refused **18** candidates that had cleared all five official gates (each named a node that was never there); the share of candidates dying malformed fell from **18/59 (30.5%) to 8/55 (14.5%)** because both artifacts are machine-generated [F53].
- **Non-interference of the recorder** demonstrated: a same-window paired trial on the stable cohort (8 always-pass + 2 never-solved tasks × 3 reps × 2 arms, recording the only difference) returned 9 of 10 per-task outcome vectors identical [F43].
- **Cost.** Per fresh evaluation the graph arms were cheaper on all three seeds ($0.392 / $0.472 / $0.503 vs $0.461 / $0.538 / $0.544); noop-round batching cut the per-round cost from $36.3 to $11.8 [F13].

---

## 4. Methodological contributions

### 4.1 Noise-floor measurement of the benchmark

Taking consecutive rounds where nothing shipped (identical configuration, bed simply re-run), **21.0% / 20.1% / 19.2%** of task outcomes flip across three seeds (pooled 402/2,000 pairs, Wilson 95% CI [18.4%, 21.9%]) [F15, F44, F45, F9e]. The per-window total-score swing is −8…+5 tasks, so single-window deltas of five tasks or fewer are unreadable. Tasks that flipped in the last three rounds re-flip at 31.5–41.6%, 1.6–2.1× the bed rate [F41]: noise is concentrated in a persistent volatile family. A census over 9,600 evaluations found 18 always-pass, 3 never-solved and 79 volatile tasks [F54]: there is no informative-and-reliable subset, so reliability must be bought by repetition (priced by Spearman–Brown) or by changing the readout.

### 4.2 Reading pairs, not totals

The same round whose total delta of +7 is inside the noise band decomposes into 8 tasks fixed and 1 broken, McNemar p ≈ 0.039 [F21]. The problem was never too little data; it was the reading axis.

### 4.3 Pre-registered efficacy-trial protocol (a manual L3 readout)

- Arms interleaved within the same time window (serial arms confound arm with time).
- True completions counted before scoring; launch-spike deaths and phantom runs excluded.
- Campaign task parameters replicated exactly (`--max-steps 20`).
- Adjudication files quarantined outside the subject-reachable filesystem and seeded with canary words.
- Gold labels health-checked before trials (one wrong gold label found).
- An eight-task always-pass canary set detects harm; stopping arithmetic decides continuation; mechanism endpoints (firing forensics, confident-wrong share) reported beside scores so a null is interpretable.
- Exactly one confirmatory test (n=70 prospective pairs); every other p-value labelled exploratory.

### 4.4 Capability probes and archaeology

Feeding a single task's full history to the loop outside the evolve cycle showed the capability chain intact end to end: see → classify → prescribe → invent tools → abstain honestly. Under a coverage directive the loop's rational optimum was a benchmark-lookup tool that passed every governance gate, retained as a governance red-team specimen [F37]. Archaeology on our own archives found the loop prescribing the correct repair families from single observations [F38], and one above-noise repair (a bash budget-starvation guard, +9 tasks, `budget_exceeded` 38 → 5) retained for the rest of its campaign [F39].

### 4.5 Evaluator audit and error registry

Fifteen measurement/design errors were logged with forced re-checks and a retraction registry, including retractions of the project's own headline readings. Applying pass@1 discipline moved the baseline seed round from 67 to 57, disclosed because the correction flatters the project's own campaign.

### 4.6 The readout proposition

Self-evolution is variation + selection + **readout**. When the readout's resolution falls below the effect sizes being selected on, retention degenerates into drift regardless of variation quality. The proposition is given a formal spine from quantitative genetics (breeder's equation analogue), the rival explanation is weighed rather than dismissed, and the experiment that separates them is named.

---

## 5. Engineering footprint

| Item | Size |
|---|---|
| GHX runtime (`harnessx/ghx/`) | 37 modules, ~11.6k lines |
| Vendored meta-loop integration (`harnessx/aegis/`) | ~6.8k lines |
| GHX unit tests | 46 files, 357 test functions (repo total 2,706) |
| Analysis / audit scripts (`experiments/analysis/`) | 65 scripts; every ledger number names its recompute script |
| Campaign operations | 6 campaigns × 16 rounds, per-shift runbooks, resume/quarantine SOPs, gateway-outage isolation |
| Durable artifacts | byte-pinned vendored substrate with parity and honesty gates; fact ledger + retraction registry; efficacy-trial protocol; readout ladder |

Technical stack: Python 3 / asyncio, HarnessX composable harness (processors, typed slots, tool registry, trajectory rewards), LiteLLM gateway, DeepSeek V4 Pro, JSONL journaling, YAML configuration with hash-based identity, mutation-tested gates, pytest.

---

## 6. Skills demonstrated (for CV / interview use)

- **Systems design for agent runtimes:** typed graph representations of executable pipelines, provenance recording with honesty guarantees, atomic transactional edits, hash-based identity layering.
- **Verification and governance of self-modifying systems:** replay gates, existence gates, mutation-tested acceptance, red-teaming a governance ladder.
- **Large-scale LLM experimentation:** multi-campaign, multi-seed orchestration on a paid gateway; incident handling (restarts, outages) with data quarantine and verified resume; cost engineering.
- **Experimental methodology and statistics:** noise-floor measurement, Wilson/bootstrap intervals with cluster correction, McNemar and exact permutation tests, pre-registration with stopping rules, canary controls, mechanism endpoints, minimum-detectable-effect analysis, an error registry with both bias directions documented.
- **Scientific writing and integrity:** a fact ledger where every number has a recompute script, a retraction registry, and claims scoped exactly to what the instrument can resolve.

---

## 7. Short project summaries at three lengths

**25 words.** Built GHX, a graph-native provenance runtime for self-evolving LLM agent harnesses; drove a four-role evolution loop to 70%+ (up to 76%) on GAIA text-only tasks.

**60 words.** GHX makes an LLM agent's execution a typed, replayable DAG with causal-ancestor queries and an atomic typed edit surface, attached non-invasively to a published self-evolving harness. Across six campaigns, 96 rounds and 8,393 evaluations on three seeds, the loop reached 72–76% final-round accuracy on GAIA text-only tasks, while the graph removed a false evidence signal from 86% of dossiers to zero and doubled verified citations.

**120 words.** My master's thesis asks what a self-evolving agent harness can actually know about its own execution. I built GHX, a graph-native runtime (~11.6k lines, 357 tests) that records every processor, tool call and sub-agent as a typed execution DAG, supports causal-ancestor cones, replay verification and a seven-operation transactional candidate surface with genotype/deployment/phenotype identity, all attached to a byte-pinned published system with zero core edits. Running the first independent large-scale execution of that system (6 campaigns, 96 rounds, 8,393 evaluations, three seeds per arm), the GHX-driven loop reached 72% and 76% final-round accuracy on the text-only GAIA subset (mean 71.7%, best 76%). Alongside, I measured the benchmark's 20% same-config flip floor, designed a pre-registered same-window efficacy protocol, and proposed a four-rung readout ladder as an evidence standard for the field.
