# Overnight review 2026-09-04 — Phase 0: field analysis and panel configuration

Skill: `academic-paper-reviewer` (full mode, 5 independent reviewers + editorial synthesis), wrapped by
`research-guardrails` (audit mode) and one mechanical/compliance line. The author is asleep; Phase 0 is
recorded here instead of being confirmed interactively.

## Paper basic information

- **Title**: Provenance-Grounded Self-Evolution of LLM Agent Harnesses: A Graph-Native Runtime, a
  Pre-Registered Falsification, and the Missing Efficacy Readout
- **Author / venue**: Fei Gao, UCL MSc Machine Learning dissertation (COMP0091), submission 9 Sept 2026
- **Sources**: `experiments/docs/thesis/THESIS.tex` + `ch/00..08`, `ch/A,B,C`, `ch/99-bibliography.tex`
- **Length**: 109 pages at 12pt (body ch1–8 ≈ 67 pages); abstract 483 words; 54 references; fact ledger F1–F56

## Field analysis

| Dimension | Result |
|---|---|
| Primary discipline | LLM agent systems — self-evolving / self-improving agent harnesses |
| Secondary disciplines | Experimental methodology for noisy benchmarks; software provenance & observability; failure attribution |
| Research paradigm | Quantitative empirical systems research with a pre-registered falsification |
| Methodology type | System implementation (GHX runtime) + controlled two-arm, three-seed campaigns (GAIA 100-task subset, 16 rounds each) + recomputable fact ledger |
| Target tier | MSc dissertation examined by internal + external examiner; paper cut would target an agents workshop / systems track |
| Maturity | Pre-submission: compiles clean, ledger complete; GenAI declaration and repository statement still missing (known) |

## Standing rulings the panel must respect (not up for review)

1. Evidence whitelist: M22_L0_ghx0, M28_L0_s2, M29_L0_s3 (no-graph) and M26_100x16b, M28_GHX_s2, M29_GHX_s3
   (graph) + pre-registered probes. Two earlier graph campaigns are excluded from every number and narrative.
2. Experiment hard freeze since 27 Aug 2026 — no new runs before submission.
3. Ledger discipline: no number enters the text without an `\F{n}` row and (for class [A]) a recompute script.
4. Reviewers are read-only on the manuscript and on `recipe/gaia_evolver/runs/`.

## Reviewer Configuration Cards

### Card #0 — EIC → Examination-board chair (`R0-eic.md`)
**Identity**: Professor of ML systems at a UK university, chair of the MSc examination board, ~40 MSc ML
dissertations examined, PC member of an LLM-agents workshop.
**Focus**: explicit research questions; contribution stated then delivered; does the negative result read as a
contribution; structure and scholarly tone against COMP0091 expectations; abstract fidelity; length and cuts;
viva pressure points.
**Blind spots**: statistics, code.

### Card #1 — Methodology (`R1-methodology.md`)
**Identity**: Statistician / experimental methodologist for LLM-agent evaluation (paired designs, pass@k
variance, permutation tests, multiple comparisons, power, pre-registration).
**Focus**: noise-geometry claims (per-round SD, same-config flip rates, band, slope permutation test, positive
control); the pre-registered protocol and power arithmetic; ledger classes and recomputability; exclusion and
outage/restart handling as selection effects; ceiling-subset analysis; unanchored numbers.
**Blind spots**: domain novelty.

### Card #2 — Domain (`R2-domain.md`)
**Identity**: Researcher in self-evolving LLM agent systems (ADAS, DGM, AlphaEvolve-style loops, MEGA,
HarnessForge, AgentFlow, meta-agent search) and agent failure attribution / AgentOps provenance; knows the
HarnessX/AEGIS release.
**Focus**: related-work coverage and accuracy; the positioning claim ("the one published harness-level closed
loop whose code is released"); whether GHX is a contribution beyond prior graph systems; fairness of the
baseline diagnosis to the official system; generalisation beyond HarnessX/GAIA.
**Blind spots**: statistics.

### Card #3 — Perspective (`R3-perspective.md`)
**Identity**: Measurement scientist / clinical-trials methodologist with a software-observability background
(metrology, ICH E9/E10, breeder's equation and regression dilution, OpenTelemetry/eBPF tracing).
**Focus**: correctness of the borrowed frames (efficacy vs capability, realized heritability, regression
dilution, add-on design, resolution laws); practical implications for harness engineers; cost honesty, LSEPI,
contamination; glossary needs and the level-2 term collision.
**Blind spots**: agent literature.

### Card #4 — Devil's Advocate (`R4-devils-advocate.md`)
**Mandate**: strongest case that the central conclusions are wrong or unearned — bed artefact vs property of
loops; implementation failure vs refutation; exclusion as cherry-picking; positive control vs "no readout";
"checkable" as unfalsifiable; contaminated null (25-task audit batches); deaf selection signal vs non-separating
outcomes; abstract vs results; "so what?".

### Line #5 — Guardrails + ledger audit (`R5-guardrails-ledger-audit.md`)
`research-guardrails` audit rubric (A, B, C, E; D N/A) + verification of every class-[A] ledger row by running
its recompute script read-only over the whitelist runs, unanchored-number sweep, anchor/row integrity.

### Line #6 — Mechanical / compliance (`R6-mechanical-compliance.md`, Sonnet)
Compile-log warnings, cross-reference and citation integrity, figure/table plumbing, spelling and terminology
consistency, COMP0091 checklist, strict-exclusion residual scan, number-format consistency.

## Phase 2
`editorial_synthesizer_agent` reads R0–R6 and writes `EDITORIAL-DECISION.md` (decision letter + prioritised
revision roadmap with fix-class tags [W]/[R]/[X]/[D]). Iron rule: a Devil's Advocate CRITICAL blocks Accept.

## Phase 3 (main loop, after synthesis)
Apply only [W] fixes that do not change a claim, and [R] fixes whose recompute already exists; recompile; leave
every [D] and [X] item for the author. Morning report in Chinese: `MORNING-REPORT-CN.md`.
