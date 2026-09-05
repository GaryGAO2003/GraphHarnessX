# Peer Review Report

## Manuscript Information
- **Title**: Provenance-Grounded Self-Evolution of LLM Agent Harnesses — A Graph-Native Runtime, a Pre-Registered Falsification, and the Missing Efficacy Readout
- **Manuscript ID**: UCL COMP0091 MSc ML dissertation (Fei Gao, supervisor Prof. Jun Wang)
- **Review Date**: 2026-09-04
- **Review Round**: Round 1

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 3 (Cross-disciplinary / Perspective)

### Reviewer Identity
Measurement scientist and clinical-trials methodologist with a software-observability background: metrology (resolution, repeatability vs reproducibility, measurement uncertainty), ICH E9/E10 trial design, quantitative genetics (breeder's equation, realized heritability, regression dilution), and production tracing (OpenTelemetry, eBPF).

### Review Focus
Correctness of the thesis's borrowed frames (clinical trials, metrology, quantitative genetics); whether "readout-first" is actionable and what minimal instrument it implies; cost/contamination/LSEPI honesty; readability for a first-time reader; and whether the figures/tables function as instruments supporting their captions.

---

## Overall Assessment

### Recommendation
**Minor Revision**

### Confidence Score
**4** — trial design, metrology, quantitative genetics, and tracing are my home turf; I defer on the agent-systems literature and the tests' internal statistics, both out of scope here.

### Summary Assessment

This is a methodology thesis built around a falsified pre-registered hypothesis, and it earns that framing: the instrument-validity work (Ch. 3, §5.2–§5.5) is executed with a rigour — bound-direction bookkeeping, a fifteen-item error registry, a retraction registry — well above typical MSc level. Its cross-disciplinary borrowings are mostly sound: the ICH E10 positive-control/assay-sensitivity logic (§7.1) is applied correctly and does real work, calibrating the instrument's detection limit at roughly 3× the effects being selected on; the breeder's-equation/regression-dilution formalism is arithmetically consistent and correctly bounded. But several specific, fixable problems sit under the polish. The same-configuration noise band used to judge every outcome-plane claim — including Figure 6.1's graph-arm panel — is measured exclusively on the no-graph arms and extended to the graph arm by unstated assumption. A headline ship-rate comparison (0.88 vs 0.62, quoted in the abstract and Table 6.1) has asymmetric scope not matching its own ledger row. GAIA, the sole measurement instrument for every number in the document, is never cited. "Level-2" names two unrelated things. None of this changes the thesis's core verdict; each is concrete, locatable, and cheap to fix without new experiments.

---

## Strengths

### S1: Instrument validity argued before data, not from data
The false-"output-used"-verdict finding (§3.5, `ch/03-baseline.tex:252–300`) proceeds in the right order: a construction proof (a 20-character floor cannot register a fact), then a bed property (median GAIA answer length is 9), and only then a reported rate — with an explicit statement of what it does *not* license ("a call sitting on the successful path holding the answer... is not the same as having caused the pass," `03-baseline.tex:294–300`). This is the order a metrologist wants: establish the instrument *cannot* work before asking how often it doesn't.

### S2: Bound-direction bookkeeping kept honest throughout
The thesis repeatedly states which way an approximation is biased: ρ ≲ 0.4 is flagged as an upper bound because |δ| stands in for a standard deviation (`ch/07-discussion.tex:59–60`); the sixteen-round window is "direction-neutral by construction" while the whitelist ruling moved numbers *against* the graph (`ch/01-introduction.tex:418–423`); the pass@1 correction is disclosed "precisely because that direction flatters this thesis" (`ch/A-deviations.tex:118–121`). Rare, and worth naming as a model for the field it critiques.

### S3: A correctly executed positive control
§7.1 imports ICH E10's assay-sensitivity logic correctly: a known-effective intervention (the budget-starvation repair, +9 tasks) establishes the instrument's detection limit (≈3× the loop's actual per-edit effects), and that limit licenses every "unreadable" verdict that follows, including the thesis's own. Load-bearing, not decorative, and correctly used.

### S4: Auditable error and retraction trail
Appendix A.3's error registry, classified by direction (eight favourable, three unfavourable, two neutral, `ch/A-deviations.tex:182–187`), and the retraction registry (`ch/C-ledger.tex:726–839`) are closer to a device manufacturer's CAPA log than to typical thesis practice.

### S5: Refusal to compute an uninterpretable ablation
§6.3's "Why there is no component ablation" (`ch/06-results.tex:199–228`) gives the statistical reason — per-level arms would return the same "not separable" verdict at *k* times the cost — rather than appealing to budget. A real sign of measurement maturity.

---

## Weaknesses

### W1: The same-configuration noise band is measured on one arm and applied to both
**Problem**: F9e's sample is explicitly "three **no-graph** arms" (`ch/C-ledger.tex:155–164`), and the flip-rate replication holds arm constant — "computed on the same 100-task bed, so the comparison is between seeds and nothing else" (`ch/06-results.tex:334–346`). σ = 3.70 (F15) is therefore a no-graph-only quantity, yet Figure 6.1 draws an identical ±3.70 band on both panels (`ch/06-results.tex:292–302`), and the whole-bed gain-face sweep (F48/F49, §6.7) judges graph-arm pairs against it too; no graph-arm-specific flip rate appears anywhere in the ledger. Separately, the band is centred on an arm mean pooled across three seeds whose plateaus differ by up to 8.9 tasks (no-graph 67.3/64.6/58.4, arm SD 4.6; graph 64.9/65.5/67.9, arm SD 1.6 — F46, `ch/C-ledger.tex:538–541`), conflating within-seed repeatability (3.70) with a between-seed reproducibility component reported elsewhere but never folded into the figure.
**Why it matters**: This band is the instrument every readability verdict in Ch. 5–7 is judged against, on both arms. Extending a no-graph-only noise estimate to a structurally different arm (one with cone-injection into role context) by silent assumption is exactly the transfer error a measurement audit should catch — especially in a document this careful elsewhere.
**Suggestion**: Report whatever bed-wide same-config windows exist in the three graph campaigns as an explicit F-row, or add one sentence at Figure 6.1 and at F48/F49 stating the band is no-graph-derived and applied by assumption (citing F43's narrower canary-based interference test as partial justification). For the panel, either draw per-seed bands (the numbers already exist in Table 6.1/F46) or caption that the pooled band is not diagnostic of any single seed.
**Severity**: MAJOR. **Fix-class**: [R] (recomputable from existing `task_history`) / [W] for the captioning fix.

### W2: The headline ship-rate comparison has unstated, asymmetric scope
**Problem**: F10 reads "No-graph 0.88 per round (52%); graph arms 0.50/0.92/0.62 (35%/60%/29%)" (`ch/C-ledger.tex:166–169`) — one no-graph figure against three graph figures, percentages undefined. The mean of the three graph values is 0.68, not 0.62, so the "0.62" quoted in the abstract, §1.6 (`ch/01-introduction.tex:258–259`), and Table 6.1 is not an arm mean, unlike neighbouring rows explicitly labelled "arm mean." Which seed(s) 0.88 and 0.62 belong to is never stated.
**Why it matters**: This is one of perhaps five headline numbers repeated in the abstract, and the thesis elsewhere (F9a–F9c) goes to considerable lengths to prevent exactly this kind of unscoped, seed-ambiguous comparison.
**Suggestion**: State the scope inline wherever the pair is quoted, or replace it with the true three-seed arm means (0.88-ish vs 0.68) for consistency with the rest of Table 6.1, and define the parenthetical percentages.
**Severity**: MAJOR. **Fix-class**: [W]/[R].

### W3: GAIA, the sole instrument, is never cited
**Problem**: Every number rests on "GAIA's text-only split" (`ch/01-introduction.tex:98`) or the "100-task no-pixel subset" (`ch/05-design.tex:21`), yet `ch/99-bibliography.tex` — otherwise scrupulous, with verified arXiv identifiers for every other system, survey, and donor mechanism — has no GAIA entry. "Text-only split," "103 tasks," and "level-2 subset" (W4) are all GAIA-defined and never glossed independently.
**Why it matters**: A reader cannot look up what these terms formally mean, and no citation for the benchmark producing every number is conspicuous in a document this fanatical about ledger-anchoring.
**Suggestion**: Add the GAIA citation (Mialon et al.) at first use.
**Severity**: MAJOR. **Fix-class**: [W].

### W4: "Level-2" names two unrelated things
**Problem**: "the level-2 subset gained 16.3 percentage points" (`ch/03-baseline.tex:375`; `ch/C-ledger.tex:450`) is a GAIA difficulty tier. Independently, "L2"/"level 2" is the readout ladder's third rung (`ch/00-abstract.tex:53`, used pervasively from Ch. 4 on, e.g. `ch/01-introduction.tex:303`). Neither is glossed at first use, and both appear within a few pages of each other in Ch. 6.
**Why it matters**: The ladder is one of two headline contributions (C6); a collision on its own vocabulary works against establishing it as a standard.
**Suggestion**: Rename the GAIA-tier references throughout (e.g. "GAIA-difficulty-2") and reserve "L2"/"rung 2" for the ladder only.
**Severity**: MAJOR. **Fix-class**: [W].

### W5: No responsible-disclosure statement for defects found in a citable open-source release
**Problem**: The thesis documents concrete defects in HarnessX/AEGIS (arXiv:2606.14249): the structurally blind evidence column, an arithmetically unreachable safety clamp (`ch/03-baseline.tex:165–173`), an empty regression report (`ch/03-baseline.tex:151–157`) — and one near-miss: a coverage-directive probe under which "the loop's rational optimum is to engineer the bed's own leak routes into a benchmark-lookup cheat tool," which "passed the Critic and all landing gates" (F37, `ch/06-results.tex:435–439`). Nowhere does the thesis state whether maintainers were, or will be, informed.
**Why it matters**: This is squarely LSEPI territory. F37 shows the *released* gate ladder admits a leakage-exploiting tool under realistic prompt pressure — a professional-conduct question for whoever found it, even if the answer turns out to be "not applicable."
**Suggestion**: One paragraph in §7.2 or §7.3 stating the disclosure decision and its reasoning.
**Severity**: MAJOR. **Fix-class**: [D] (author's decision) / [W] (one paragraph).

---

## Detailed Comments

### Borrowed frames: correctness audit

**§7.1, breeder's equation and regression dilution.** R = h²S needs no citation. The attenuation step, h²_realized = h²_true·ρ, ρ = σ²_δ/(σ²_δ+σ²_ε) (`ch/07-discussion.tex:41–53`), is the correct classical form and is applied correctly: |δ|≲3, σ_ε≈3.70 gives ρ = 9/22.69 ≈ 0.40, matching the text, and "upper bound" is right — |δ_i|≤3 implies σ_δ≤3 by Popoviciu's inequality, so using 3 can only overstate ρ. Careful work, but h²_realized itself carries no citation, unlike almost everything else here. **[W], MINOR** — cite Falconer & Mackay for the equation and a regression-dilution source (Hutcheon, Chiasson & Platt 2010, or Spearman's original correction) for the attenuation step. More substantively, "expected cumulative gain over R rounds is consequently non-positive regardless of variation quality" (`ch/07-discussion.tex:65–68`) is asserted in prose, not derived or simulated, despite the text's own flag that this is "the non-trivial part." **[W], MAJOR**: soften to "can be non-positive under this bed's parameter regime," or add a short derivation.

**§6.6, the clinic (capability vs efficacy).** Used correctly and consistently — "every item above is capability evidence. None of it is efficacy evidence" (`ch/06-results.tex:441–443`) — one of the thesis's cleaner pieces of intellectual hygiene.

**§5.3, efficacy-trial protocol / ICH E10 add-on design.** "ICH E10" and "assay sensitivity" appear once, in §7.1 (`ch/07-discussion.tex:81–82`), not in §5.3. The protocol does structurally match an add-on design — "parent" is the standing configuration, "applied" is parent-plus-bundle (F34, `ch/C-ledger.tex:384–396`), never a from-scratch comparison — and is executed with genuine trial discipline. The gap is naming, not substance. **[W], MINOR**: name the design once at §5.3's opening.

**§5.4, "Resolution laws as design inputs."** What is measured — the smallest |Δscore| distinguishable from same-configuration noise — is a detection limit / minimum-detectable-effect, not "resolution" in the strict VIM (JCGM 200:2012) instrument-discretisation sense (GAIA scores, as integer counts, do have a literal resolution of 1, which is not what §5.4 addresses). It fits the optics/spectroscopy "resolving power" sense considerably better. **[W], MINOR**: one clarifying clause at first use would preempt a metrology-trained reader's double-take, in a document otherwise careful about naming things precisely (cf. its own range-vs-SD distinction, §5.2).

**§5.5, evaluator-bias controls / §4.9, readout ladder.** The pass@1 correction and multiplicity declaration (exactly one confirmatory test; everything else exploratory, `ch/05-design.tex:258–271`) are correctly reasoned and disclosed in the direction that costs the thesis. The ladder's cited precedents (GRADE, SAE J3016, `ch/04-ghx.tex:368–370`) are fair but not the sharpest available analogy — see recommendations below.

**§6.7, treadmill and mortality.** The four-layer mortality account is explicitly labelled `[C]` judgment (`ch/06-results.tex:622`) — correctly, since it is a plausible causal story, not a measured decomposition.

### Practical impact: is "readout-first" actionable?

Yes, with one gap. §5.3 already specifies the minimal instrument: interleaved same-window arms, a small always-on canary set, a per-trajectory firing/no-firing flag (available at L2), and a pre-registered stopping rule. Missing is the step from "protocol a human runs by hand" to "a hook the loop runs on itself" — explicitly never wired in (`ch/04-ghx.tex:395–399`, `ch/07-discussion.tex:128–130`). The concrete engineering takeaway for a harness practitioner: promote §5.3 into a processor that runs automatically on interleaved shadow rounds *after* a candidate ships but *before* it survives past the rollback window — a `before_retain`-style gate sitting after Commit. That is a buildable next step; the thesis would be stronger for stating the wiring point explicitly.

### Cost, contamination, and LSEPI

**Cost honesty (§7.4)** is a genuine strength: the "net expensive graph layer" withdrawal is handled correctly (measured on excluded campaigns, restated as "blank, not negative," `ch/07-discussion.tex:251–263`). Gap: no compute/energy/carbon reporting anywhere, despite 8,393+ fresh evaluations and thousands of meta-role calls — a common expectation now for LLM-heavy empirical work; a rough token-count estimate would meet it. **[W]/[D], MINOR.**

**Contamination (§3.4)** is handled with real care: the leak-route finding (12 of 44 swing tasks, `ch/03-baseline.tex:211–219`) is disclosed as residual risk, and the blocklist is correctly described as the only held-out defence, shared identically across arms.

**LSEPI**: covered under W5. The remaining gap is Figure 1.1's licence — "Reproduced from the HarnessX repository's documentation assets" (`ch/01-introduction.tex:59–60`) states provenance but not the licence governing reproduction in a distributed thesis. **[D]/[W], MINOR.**

### Figures and tables as instruments

**Figure 1.1** (p. 3) communicates the source system's own vocabulary adequately but does not visually distinguish the "Adapt" vertex — the thesis's actual subject — from "Compose"/"Evolve"; all three boxes are styled identically. **[W], MINOR.**

**Figure 4.1** (p. 32) does its job well: solid/dashed boxes cleanly separate official-loop from GHX-attached components, and the readout-ladder box correctly states "L0–L2 live; L3 by hand," matching the body exactly.

**Figure 6.1** (p. 53) and its ±3.70 band: see W1. The plot itself is legible and the "hollow markers move as much as filled ones" claim is visible in the data.

**Tables 6.1 and 6.4** both communicate exactly what their captions claim: Table 6.1's four-plane layout is an unusually good instrument-panel design for a results table, and Table 6.4 is compact and precisely matched to its claims about the two −31 collapses.

---

## Cross-Disciplinary Reading Recommendations

1. **Falconer & Mackay, *Introduction to Quantitative Genetics*** (or Hutcheon, Chiasson & Platt, *Int. J. Epidemiol.* 2010, on regression dilution bias) — sources the h²_realized formula §7.1 states without citation.
2. **ICH E9(R1) Addendum on Estimands (2019)** — its intercurrent-events framework would formalise the "shipped but never fired" scenario already documented (`ch/04-ghx.tex:395–399`) into a named category.
3. **JCGM 200:2012 (VIM), §4.13** — the formal definition of "resolution," relevant to the §5.4 terminology note.
4. **The ACCE model** (CDC Office of Genomics, 2004: Analytic Validity, Clinical Validity, Clinical Utility, ELSI) — a closer structural precedent for the L0–L3 ladder than GRADE or SAE J3016, since it separates "does it work" / "does it predict" / "does it change outcomes" the way the ladder's rungs do.

---

## Questions for Authors

1. Was a graph-arm-specific same-config flip rate ever computed from whatever no-ship windows exist in the three graph campaigns? If too few exist, that belongs in Figure 6.1's caption.
2. For F10, which seed(s) do the headline 0.88 and 0.62 refer to, and what do the parenthetical percentages measure?
3. Was disclosure to the HarnessX/AEGIS maintainers considered for the §3.3/§3.6 defects and the F37 near-miss?
4. Under what licence is Figure 1.1 reproduced?

---

## Minor Issues

### Language / Terminology
- "Resolution" (§5.4 title, abstract) fits the optics sense better than the VIM instrumentation sense (see above).
- "Clinic" (§6.6 title) never reappears in running prose and is never glossed as a metaphor.
- "Archaeology" and "deaf" carry real argumentative weight (see Glossary) but are never glossed at first use; "treadmill" and "mortality" are adequately glossed in-line.

### Figures and Tables
- Figure 1.1: highlight the Adapt vertex.
- Figure 6.1: state whether the band applies to the graph panel by measurement or by assumption (W1).

### Other
- The Spearman-Brown repetition-pricing exercise is promised twice (`ch/05-design.tex:186–190`, `ch/07-discussion.tex:312–318`) but the number is never computed, even roughly — arithmetic on already-reported figures, not blocked by the freeze. **[R]**

---

## Dimension Scores

| Dimension | Score (0-100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | 78 | Strong | Genuine synthesis (ladder + falsification narrative); most components individually borrowed and named as such. |
| Methodological Rigor (25%) | 83 | Strong | Exceptional in most places; docked for W1–W2 (noise-band transfer, ship-rate scope). |
| Evidence Sufficiency (25%) | 80 | Strong | Three-seed replication and one pre-registered confirmatory test; strongest causal claims correctly labelled [C] judgment by the authors themselves. |
| Argument Coherence (15%) | 82 | Strong | H1→unmeasurable→substitute endpoints→proposition throughline is clear and well-signposted. |
| Writing Quality (15%) | 79 | Strong | Terse and purposeful at sentence level; docked specifically for the readability gaps this review's focus targets (glossary, term collision). |
| Significance & Impact (R3 focus) | 78 | Strong | A genuinely useful, field-applicable ladder; impact capped by single-bed/single-tier scope (openly disclosed) and by L3 not yet being automated. |
| **Weighted Average** | **81** | **Strong / Minor Revision** | |

---

## Glossary (built for a first-time reader; not in the manuscript)

| Term | First use (file:line) | Inferred definition | Collision? |
|---|---|---|---|
| Digester | `01-introduction.tex:27` | Meta-role that reads every trajectory (pass and fail) and writes a per-task dossier. | No |
| Planner | `01-introduction.tex:31` | Meta-role that synthesizes all dossiers into one "landscape" document. | No |
| Evolver | `01-introduction.tex:32` | Meta-role that authors candidate edits (manifest + applied configuration). | No |
| Critic | `01-introduction.tex:34` | Meta-role that judges candidates, may interrogate the Evolver, vetoes before gates. | No |
| dossier | `01-introduction.tex:30` | Digester's per-task write-up of a trajectory. | No |
| landscape | `01-introduction.tex:31` | Planner's single synthesized document across all dossiers in a round. | No |
| candidate | `01-introduction.tex:32` | A proposed edit to the harness (config/tool/prompt/processor), pre-gate. | No |
| ship / no_op | `01-introduction.tex:76` | The two terminal decisions per round: land the candidate(s), or change nothing. | No |
| ratchet | `00-abstract.tex:21` | The paper's (unimplemented in the release) rule that a solved task may never be given back. | No |
| actionability score | `01-introduction.tex:45` | Mechanical score gating whether the evolve stage runs at all this round. | No |
| structure / novelty / counterfactual / replay gate | `01-introduction.tex:37` | The official ladder's five checks (structure invariants; dedup vs refuted ledger; process-replay no-change test; synthetic-task smoke). | No |
| sixth gate | `01-introduction.tex:259`; defined `04-ghx.tex` §4.7 | GHX-added gate: a candidate's claimed target node must appear in the recorded execution graph of the failure it cites. | No |
| composition graph | `01-introduction.tex:224` | Typed graph re-expression of the harness's static configuration (nodes = hooks/processors/slots/bundles/skills/tools). | No |
| unfolded execution graph / $U$ | `01-introduction.tex:225` | Per-invocation DAG of what actually executed, edges observed not inferred. | No |
| UNGRAPHED | `04-ghx.tex:120` | Recorder's explicit "I don't know" marker for an unattributable event, rather than a guessed edge. | No |
| ancestor cone / cone | `01-introduction.tex:227`; defined `04-ghx.tex:167` | The over-approximate upstream subgraph of $U$ that *could have* shaped a failure — not a counterfactual. | No |
| genotype / deployment / phenotype | `04-ghx.tex:143–152` | Three nested identity hashes: structural config; config+runtime overlay; +observed execution edges. | No |
| typed candidate surface | `01-introduction.tex:229` | GHX's seven typed graph-edit operations replacing free-text candidate authoring. | No |
| readout ladder / L0–L3 / rung | `00-abstract.tex:52` | Four-level evidence hierarchy about an edit: deployed / executed / fired / changed outcomes. | **Yes — see below** |
| recorder | `01-introduction.tex:213` | The write-only component that logs the composition graph and $U$ during a run. | No |
| injection manifest | `04-ghx.tex:200` | Recorded log of exactly what cone/context content a role was shown. | No |
| same-config flip rate | `01-introduction.tex:129` area; measured `05-design.tex` §5.2 | Fraction of task pass/fail outcomes that differ between two consecutive rounds run under an identical (unedited) configuration. | No |
| plateau | `01-introduction.tex:175` | The roughly-stable score level a campaign settles into after its early rounds (here, mean of R3–R15). | No |
| gain face | `06-results.tex:549` (section title) | The set of all round-to-round score moves that leave the same-config noise band, across all six campaigns. | No |
| positive control | `00-abstract.tex:43` | The one intervention (budget-starvation repair) known by mechanism to have worked, used to calibrate the instrument. | No |
| assay sensitivity | `01-introduction.tex:318` | Borrowed ICH E10 term: a trial design's ability to distinguish an effective from an ineffective treatment. | No |
| breeder's equation / $h^2$ / regression dilution | `07-discussion.tex:42–53` | Quantitative-genetics formalism (R=h²S) borrowed to model why noisy readout attenuates response to selection. | No |
| capability wall | `01-introduction.tex:344` | The rival hypothesis: nulls arise because the action space cannot reach the relevant lesion, not because of a readout failure. | No |
| wrong-closure | `06-results.tex:481` | Failure-census category: task closes (answers) on the wrong conclusion despite otherwise-sound process. | No |
| leak-route | `03-baseline.tex:213` | Failure/pass category where the benchmark's ground truth is reachable via public web content. | No |
| starvation (budget_exceeded) | `01-introduction.tex:310` | Task exit reason: ran out of step/token budget before answering, independent of task difficulty. | No |
| confident-wrong share | `05-design.tex:236` | Mechanism endpoint: fraction of failures where the subject closed confidently on a wrong answer. | No |
| treadmill (re-prescription treadmill) | `01-introduction.tex:300` | Metaphor: the same drug/edit family is independently re-derived across campaigns without inheriting from earlier instances. Glossed at first use. | Flag: metaphor, but adequately defined in-line |
| archaeology | `01-introduction.tex:279` | Metaphor/method: re-reading the project's own prior campaign archives to check whether a "new" finding already existed. Never explicitly glossed as a method. | Flag: undefined metaphor, load-bearing (one of three substitute endpoints for H1) |
| four layers of mortality | `06-results.tex:222`; titled `06-results.tex:490` | Metaphor for the four reasons a correctly-prescribed edit fails to produce lasting gain. Reasonably scaffolded by its own enumerated list immediately after first use. | Flag: metaphor, moderately defined |
| the survivor | `02-related-work.tex:324`; titled `06-results.tex:644` | Metaphor: the one positive channel (episodic notes) that outlasted every governance/dormancy failure mode. Defined at section opening. | Flag: metaphor, adequately defined |
| the clinic | `06-results.tex:417` (section title only) | Metaphor for §6.6's capability-vs-efficacy testing regime, by extension of the drug/dose/trial vocabulary used elsewhere. Never appears in the section's running prose and is never glossed. | Flag: **undefined metaphor** |
| deaf (readout is deaf) | `02-related-work.tex:8` | Metaphor: an instrument whose noise floor exceeds the effect sizes it is meant to detect. Never given a one-line technical gloss at first use. | Flag: **undefined metaphor**, appears in a chapter-claim box |
| parent / applied | `06-results.tex` (clinic section, "parent 75/174 against applied 72/174") | Trial-arm labels: parent = standing/background configuration; applied = parent + candidate bundle under test. | No, but never formally introduced as a defined pair before first tabular use |
| twin(-trajectory) analysis | `06-results.tex:403` | Method: comparing two same-config runs of one task step-by-step to locate where their trajectories first diverge. | No |
| level-2 subset | `03-baseline.tex:375` | GAIA's own difficulty tier 2 (a property of the benchmark, never independently defined in-thesis). | **Yes — collides with "L2"/"level 2"/"rung 2" of the readout ladder** (e.g. `01-introduction.tex:303`), an unrelated concept. Neither sense is disambiguated at point of use. |
| lift | `01-introduction.tex:280`; defined `06-results.tex:147` | Localization metric: (hit rate on a shipped candidate's named tasks) ÷ (base rate of those tasks flipping anyway). | No |
| base pool | `01-introduction.tex:249` | The denominator population of failing-task predictions a lift figure is computed against. | No |
| no-pixel (bed) | `01-introduction.tex:98` | The 100-task subset of GAIA's text-only split, excluding the 3 tasks carrying image content the recorder cannot attribute. | No |
| whitelist / whitelist campaign | `A-deviations.tex:26` | The evidence-admissibility ruling (2026-08-26) restricting every claim to specific campaigns; "whitelist campaign" = one admitted under it. | No |
| \F{n} / [A] / [B] / [C] tags | First appear `00-abstract.tex`; formally defined only in `C-ledger.tex:10–19` (Appendix C, p.80) | Anchor to a numbered fact-ledger row; source-class label (recomputable / recorded / judgment). | Flag: notation used from page 1 but its key is not given until the very last appendix — a forward pointer on first use (e.g. a footnote "see Appendix C") would help a linear reader. |

**Note on the two flagged undefined metaphors ("the clinic," "deaf")**: both carry real argumentative weight — "the clinic" names the chapter section that houses the efficacy-vs-capability distinction the whole thesis turns on, and "deaf" appears inside a chapter-claim box making a load-bearing empirical assertion — and neither receives a one-sentence definition anywhere in the document. A single clause at first use of each (e.g. "an instrument is *deaf* to an effect when its noise floor exceeds the effect's magnitude") would close the gap cheaply. **[W], MINOR** for both.
