# Peer Review Report

## Manuscript Information
- **Title**: Self-evolving harness study on HarnessX/AEGIS: baseline diagnosis, GraphHarnessX (GHX), and the readout proposition
- **Manuscript ID**: UCL COMP0091 MSc ML dissertation (internal + external examiner), submission 9 Sept 2026
- **Review Date**: 2026-09-04
- **Review Round**: Round 1 (overnight multi-reviewer pass)

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 2 (Domain)

### Reviewer Identity
Researcher in self-evolving / self-improving LLM agent systems (ADAS, Darwin Gödel Machine, AlphaEvolve-style loops, MEGA, HarnessForge, AgentFlow, meta-agent search) and in agent failure attribution / AgentOps provenance (Who&When, TRAIL, OpenTelemetry-style tracing); familiar with the HarnessX/AEGIS release the thesis builds on.

### Review Focus
Related-work coverage and accuracy (ch2); defensibility of the positioning claims (abstract, §2.6); whether GHX (ch4) is a contribution beyond the cited graph systems or engineering; fairness and code-pinning of the baseline diagnosis (ch3); scope-correctness of the generalisation claims; terminology consistency. Statistics is out of scope.

---

## Overall Assessment

### Recommendation
**Minor Revision**

### Confidence Score
**4** — Mostly within my expertise. Roughly half the bibliography (2026 preprints) postdates my training and could not be checked from memory; noted per item. One bounded web check was used on the single most load-bearing positioning claim (see W1).

### Summary Assessment
This is a negative-result-and-methodology thesis about self-evolving LLM-agent harnesses: it runs the released HarnessX/AEGIS system at scale, diagnoses a structurally blind evidence column, builds GraphHarnessX (GHX) as a non-invasive execution-provenance layer, and concludes — on a pre-registered efficacy trial and two campaign-wide sweeps — that the field's selection signal sits below its own noise floor. The related-work chapter is unusually disciplined: it states its position as a conjunction (no single property is new, the combination is), concedes what the five nearest systems already hold in a table, and runs an explicit "taken/changed" ledger against its two structural donors. Fourteen spot-checked citations against my own knowledge of the pre-2026 literature (ADAS, Gödel Agent, DGM, AFlow, GEPA, AlphaEvolve, MAST, Who&When, TRAIL, AgentSquare/MaAS/EvoFlow, MermaidFlow) came back accurate, with one overstatement. I code-pin-checked three file:line claims in ch3 against the live source and all three resolved exactly. ch3 also separates criticism of the release from criticism of the thesis's own fielding of it. The most consequential finding here is a missing reference: an independently authored July–August 2026 paper reaches a closely convergent conclusion (harness evolution does not reliably beat simple baselines under fair evaluation) and was missed by the thesis's own scan. A second, smaller finding is a stale line-pin in Appendix A that ch3's own body already has correct. Recommend minor revision.

---

## Strengths

### S1: A novelty claim stated as a conjunction, with the rebuttal pre-empted
§2.6 (ch/02-related-work.tex:328–368) states the position as "no prior system holds all of these at once — not that any one of them is new," then supplies Table 2.1 with concessions written into the cells (HarnessForge's write-back is marked "partial," explained as "into an untyped text triple with no build-time validation and no graph-hash identity"). Rare to see executed this cleanly at MSc level.

### S2: An explicit "taken / changed" donor ledger
§2.4 (lines 236–299) analyses MermaidFlow and AgentFlow to the level of what was borrowed verbatim versus altered, including a head-on statement that MermaidFlow's own closure lemma does not hold at GHX's layer. A further eleven mechanisms are named with individual donors (§2.6, 385–398); I verified the count — exactly eleven.

### S3: Code-pinned diagnosis that actually resolves
I checked three ch3 file:line claims against the live source. All three were exact: the ≥20-character substring rule in `harnessx/aegis/stages/trace_facts.py` (03-baseline.tex:260); the rollback conjunction at `recipe/gaia_evolver/run_meta_aegis.py:1425` (03-baseline.tex:165–168); and the `PlannerInputs` dataclass at `harnessx/aegis/agents/planner.py:30–46` (03-baseline.tex:351–356). This level of falsifiability, and passing it, is rare.

### S4: Own errors narrated at the same severity as the release's
§7.2 (07-discussion.tex:181–187) states the adjudication-leak gate "exists because registry error 13 was exactly that failure committed by us." The fifteen-error registry (A-deviations.tex:182–290) tallies both bias directions and names "stopping the check too early" as the common root cause, not bad luck. This is what makes the ch3 diagnosis credible.

### S5: Terminology defined at first use with scope disclaimers
"Cone" (§4.4) is immediately qualified — "what could have shaped the failure, never what caused it... not a counterfactual" — foreclosing the likeliest misreading (a Pearl-style interventional object). "Seam" is used exactly in Feathers' legacy-code sense throughout, consistently, without ever citing that literature.

---

## Weaknesses

### W1: A closely convergent, currently-live paper is missing
**Problem**: I located, via one bounded web check prompted by the abstract's strongest claim (see Q2), Wang, Zhu, Hu, Yuan, Chen, Senthil, Hajishirzi, Tsvetkov, Dasigi, Xiao, "Rethinking the Evaluation of Harness Evolution for Agents," arXiv:2607.12227 (14 Jul 2026, revised 27 Aug 2026 — the same day this thesis's own freeze). On Terminal-Bench 2.1 with GPT-5.4/Claude Opus 4.6, it argues current harness-evolution evaluation conflates the search and evaluation benchmark and skips equal-budget baselines, finding "automatic harness evolution does not consistently outperform simple test-time scaling methods." A second, more tangential same-week miss: "Harness Handbook..." (Wang, Shi, Li et al., arXiv:2607.13285).
**Why it matters**: this is an independent, differently-mechanized convergence with the thesis's own headline finding, from a high-visibility author list. §2.1's "harness-level line in 2026" paragraph (02-related-work.tex:55–89) already covers same-vintage 2026 work; this belongs there, and it directly strengthens §7.1's hedge that the field-level implication "is an inference... rests on the scan of Chapter 2" (07-discussion.tex:32–38) with a second, independently-derived data point.
**Suggestion**: Add both to §2.1, and a sentence to §7.1 citing 2607.12227 as corroborating evidence. No new experiments needed.
**Severity**: MAJOR. **Fix-class**: [W].

### W2: A stale code-pin in Appendix A that ch3's body already corrected
**Problem**: A-deviations.tex:71–72 and again 128–131 cite `run_meta_aegis.py:901--911` for "the post-round rollback rule." Lines 890–915 of that file contain unrelated `AegisAgent` construction code, not the rollback conjunction. The correct location — verified — is line 1425, exactly what ch3's own citation already uses (03-baseline.tex:168; see S3).
**Why it matters**: this is precisely the check a reader who trusts the thesis's "everything is code-pinned" self-representation would run, and Appendix A fails it twice while the chapter body passes. No reported number is affected.
**Suggestion**: Re-point both Appendix A citations to line 1425.
**Severity**: MINOR. **Fix-class**: [W].

### W3: A GHX-side fix for a ch3-diagnosed defect is absent from ch4/roadmap
**Problem**: ch3 criticizes the official loop: "The Planner is structurally excluded from the loop's conversion priors — the guidance rebind list omits it... and this holds in every arm" (03-baseline.tex:351–356). I read `harnessx/ghx/guidance.py:39–56` and found GHX built a targeted repair for exactly this gap — a "Planner fate-bucket priors" rebind, gated by flag `HARNESSX_GHX_PLANNER_SENSES` (default off, consistent with "holds in every arm" for the claim-bearing campaigns). Neither ch4 nor C6 names this mechanism, though F12's 21-switch ledger likely counts it in aggregate.
**Why it matters**: a missed opportunity, not an error — naming this switch would give C6's "every item attached to a measured gap" claim a concrete existence proof that the ch3 diagnosis already produced a candidate patch.
**Suggestion**: One sentence in §4.8 or C6 naming the mechanism and its unproven status.
**Severity**: MINOR. **Fix-class**: [D]/[W].

### W4: "Supernet" attributed to three systems where it precisely fits one
**Problem**: "AgentSquare, MaAS, EvoFlow — type candidates at module level and search over supernets" (02-related-work.tex:290–293). "Supernet" is MaAS's own framing (its title: "via Agentic Supernet"). AgentSquare, to my recollection, is a modular design space searched by evolution/recombination with a performance predictor; EvoFlow is tag-based retrieval plus multi-objective evolutionary search. Neither is naturally a supernet system.
**Suggestion**: Scope "supernet" to MaAS; describe the other two generically. Moderate, not high, confidence — recommend the author re-check primary sources.
**Severity**: MINOR. **Fix-class**: [W].

### W5: Name-collision risk on "AgentFlow"
**Problem**: \cite{agentflow} (arXiv:2607.01640, static agent-dependency-graph analysis) is the paper GHX borrows its three edge families from "verbatim" (04-ghx.tex:85–89). A distinct, earlier "AgentFlow" (in-context, RL-optimized four-module agent system) exists to my knowledge, unrelated to this one; a reader who knows the other system may momentarily misattribute the claim.
**Suggestion**: One disambiguating clause at first mention.
**Severity**: MINOR. **Fix-class**: [W].

---

## Detailed Comments

### Positioning claims (abstract; §2.6)
The structured claim — §2.6's conjunction plus Table 2.1's concessions — is defensible as stated. The abstract's compressed version is riskier: "HarnessX/AEGIS is, to our knowledge, the one published harness-level closed loop whose code is released" (00-abstract.tex:6–8) is an absolute claim in a field moving fast enough that this review's own check, prompted by treating this exact sentence as the one worth verifying, surfaced the W1 cluster the thesis's scan missed. HarnessForge — named as "the closest problem setting... same object as this thesis" — is the strongest single test case, and I could not confirm or deny its code-release status. **Proposed fix**: "…is, to our knowledge as of our literature cutoff, one of very few published harness-level closed loops whose code is released" — a dated, still-strong claim that does not collapse if one neighbour turns out to have released code. [W]

### ch4 (GHX): contribution vs. engineering
Judged against the cited systems, GHX reads as a disciplined synthesis (typed-graph representation from MermaidFlow/AgentFlow, hash-lineage identity from DGM, edge-grading from GRADE, gate cascades from AlphaEvolve/HarnessBank/the official ladder) plus one component I could not find precedented in combination anywhere cited: execution provenance used as a live **admission veto** inside a self-evolving retention loop — the sixth gate killing 18 candidates that had cleared all five official gates by checking a claimed target against the recorded execution graph (§4.6). Every attribution-line system in §2.2 either diagnoses offline or feeds candidate *generation*; none is shown gating *admission* on recorded execution. The text's own claim (C3: "legality and identity of candidates... Not a wider reach") is calibrated conservatively relative to this — the sixth gate could be named more explicitly as the one genuinely novel piece. I found no place in ch4 that claims more than ch6 supports.

### ch3: fairness and code-pinning
§3.1 (32–110) gives credit before diagnosing and separately itemises paper-vs-release divergences, then maintains that distinction throughout ("Where a finding depends on one of these divergences, the dependence is stated"). Combined with S3/S4, I judge the diagnosis fair and adequately separated from the thesis's own fielding, modulo W2.

### Generalisation
§7.1 (11–38) scopes correctly: "The claim is made for this bed and this system class. The field-level implication... is an inference and is flagged as one." W1's addition would strengthen, not undermine, this. The abstract's compressed proposition statement (00-abstract.tex:49–51) reads as unqualified where ch7 is careful — normal compression, not a required fix, but a trailing "on this bed and system class" would cost nothing.

### Terminology
"Harness," "provenance," "readout," "seam," "cone" are each introduced carefully enough that misreading is unlikely (S5). "Processor" is load-bearing from page one (01-introduction.tex:33) without ever being explicitly defined; the closest approach is listing it as one of six graph node types in §4.2 (78–80). One definitional sentence at first use would remove the ambiguity.

---

## Questions for Authors

1. Given arXiv:2607.12227 reaches a convergent conclusion via a different mechanism on a different system class — corroboration of §7.1's field-level inference, or a genuinely distinct failure mode to keep separate from the readout proposition?
2. Is HarnessForge's implementation publicly released? The abstract's strongest single test case is this comparison.
3. Was the `HARNESSX_GHX_PLANNER_SENSES` mechanism left out of ch4/C6 deliberately (already reflected in F12's aggregate count), or is its absence an oversight?
4. Table 2.1 draws its five comparators from the attribution line plus HarnessForge. Would MEGA earn a place in an extended table (it satisfies cross-task aggregation and residence, not native recording), or is its exclusion specifically because §2.5 frames it as adjacent rather than competing?

---

## Minor Issues

### Language / Terminology
- "Processor" (01-introduction.tex:33) used before it is defined; add one clause at first use.
- CHIEF's bibliography expansion ("Hierarchical Failure Attribution... (CHIEF)") does not obviously acronym-match — arXiv's own title, not a thesis error, not worth changing.

### Citation Format
- The bibliography header states verification "on 2026-09-04" — the same day as this review, five days before submission. Sound methodology (arXiv-metadata cross-check), but worth a final diff against the compiled PDF's in-text citations before submission.

---

## Citation Spot-Checks

| Key | What the text says | Verdict | Fix |
|---|---|---|---|
| `adas` | Lets an agent "rewrite its own code directly" | Accurate (mild simplification) | None |
| `godel-agent` | Same framing | Accurate | None |
| `dgm` | Population archive of self-modifying agents; nearest precedent for GHX's hash identity | Accurate | None |
| `aflow` | Evolves workflows, representations converging toward typed graphs | Accurate/plausible | None |
| `gepa` | Reads traces to generate; admission stays Pareto-on-score | Accurate | None |
| `alphaevolve` | Cascade of evaluation gates verifying score improvement | Accurate | None |
| `mast` | Builds a multi-agent failure-mode taxonomy | Accurate | None |
| `whowhen` | Reports 14.2% step-level accuracy | Plausible; exact figure not independently re-derivable from memory | Keep pinned to source table |
| `trail` | Best model ~11% on a 148-trace benchmark | Plausible, low-accuracy result matches recollection | Same |
| `agentsquare`/`maas`/`evoflow` | Grouped as searching "supernets" | **Overstated** — precise for MaAS only | Rescope per W4 |
| `agentflow` | Three edge families "adopted directly" | Accurate as stated (post-cutoff, unverifiable); **name-collision risk** | Disambiguate per W5 |
| `mermaidflow` | 90% vs ~50% valid-rate, 80.75 vs 78.67 mean score | Plausible framing; exact numbers not independently re-verifiable | Author re-check if time allows |
| `harnessforge` | "Same problem, opposite route," no typed validation/hash identity | Plausible characterisation; code-release status unconfirmed (central to abstract's claim) | Verify before finalising abstract wording |
| `survey-selfevolve` | Organizes field along "what, when, how, where" | Accurate | None |
| *(uncited)* | — | **Missing**: Wang et al., "Rethinking the Evaluation of Harness Evolution for Agents," arXiv:2607.12227 (2026) | Add per W1 |
| *(uncited)* | — | **Missing**: Wang et al., "Harness Handbook...," arXiv:2607.13285 (2026) | Add per W1 (secondary) |

---

## Dimension Scores

Statistics is out of my remit; Methodological Rigor and Evidence Sufficiency below reflect only what a domain/code-pinning/consistency lens can see and should be weighted against the methodology reviewer's score.

| Dimension | Score (0-100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | 78 | Strong | Honest synthesis + one novel admission-gate mechanism (§4.6); text does not overclaim |
| Methodological Rigor (25%) | 80 | Strong | *Domain-lens only.* 3/3 checked code-pins in ch3 body resolved exactly; one stale pin in Appendix A (W2) |
| Evidence Sufficiency (25%) | 78 | Strong | *Domain-lens only.* Related-work claims mostly accurate on spot-check; one overstatement (W4), one missing convergent-evidence cluster (W1) |
| Argument Coherence (15%) | 85 | Strong | Explicit chapter-head claims and repeated scope discipline |
| Writing Quality (15%) | 80 | Strong | Dense, precise, occasionally aphoristic; clean |
| Literature Integration (R2 focus) | 76 | Strong | Careful, honest donor analysis, offset by the W1 gap in a fast-moving adjacent sub-literature |
| **Weighted Average** | **~80** | **Minor Revision** | |
