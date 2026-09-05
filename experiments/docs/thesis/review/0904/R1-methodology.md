# Peer Review Report

## Manuscript Information
- **Title**: Provenance-Grounded Self-Evolution of LLM Agent Harnesses — A Graph-Native Runtime, a Pre-Registered Falsification, and the Missing Efficacy Readout
- **Manuscript ID**: UCL COMP0091 MSc ML dissertation (submission 9 Sept 2026)
- **Review Date**: 2026-09-04
- **Review Round**: Overnight pre-submission review, round 1

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 1 (Methodology)

### Reviewer Identity
Statistician and experimental methodologist for LLM-agent evaluation; paired designs, pass@k variance, permutation tests, multiple comparisons, power, pre-registration discipline.

### Review Focus
Noise-geometry and significance claims (ch5–ch6); the pre-registered falsification protocol; fact-ledger discipline and anchor spot-checking; selection effects from exclusions/incidents/audit-batch sampling; reproducibility. Domain novelty and literature positioning are explicitly out of scope for this review.

---

## Overall Assessment

### Recommendation
**Minor Revision.** No finding below requires new data; every fix is a text correction, a citation, or a recheck of an already-existing script against already-recorded data.

### Confidence Score
**5** — squarely this reviewer's specialty; findings below are based on direct verification of the LaTeX sources, the fact ledger, and the `experiments/analysis/` script directory, not on summary.

### Summary Assessment
The thesis executes an unusually disciplined statistical program around a genuinely hard measurement problem: a ~20% same-configuration flip rate on a 100-task bed that swamps the per-edit effects (|δ| ≲ 3 tasks) the harness under study actually produces. The response — a fact ledger with 56 script-anchored facts, one declared confirmatory test with everything else labelled exploratory, a clinical-trial-style efficacy protocol, and a positive control calibrated against a directly-measured per-round SD — is well above the bar expected of an MSc thesis and reflects real statistical sophistication (candidate-clustered bootstraps, seed-level rather than task-level permutation tests, an honest regression-to-the-mean check on R0). Verification turned up a genuine, isolated arithmetic slip that reintroduces an explicitly-retracted number, one clustering gap in an otherwise careful uncertainty apparatus, an unlocated pre-registration record for the central falsification claim, and a checkable discrepancy between two supposedly-independent recompute artifacts. None threatens the thesis's headline (deliberately hedged) conclusion that the outcome axis does not separate at this bed's resolution; all are fixable in hours, not weeks.

---

## Strengths

### S1: Clustering-aware inference where it counts most
F9d's localization-lift confidence interval is a **candidate**-level cluster bootstrap (`audit_lift_uncertainty.py`), explicitly reasoned: "predictions inside one candidate share an edit, a round and a base pool" (ch/C-ledger.tex:139–140). F47's between-arm slope comparison is a **campaign**-level 3-vs-3 exact permutation test, not a naive pool of round- or task-level observations, and the authors state its own resolution ceiling unprompted: "the smallest attainable one-sided permutation *p* is 0.05... 'not significant' here means the design reached its own ceiling before it reached significance" (ch/06-results.tex:381–388). This is correct avoidance of pseudo-replication in exactly the two places it is hardest to get right.

### S2: A real assay-sensitivity design
The budget-starvation repair (ch/03-baseline.tex §3.7, "The one real repair") is used explicitly as a clinical-trial-style positive control (citing ICH E10, ch/07-discussion.tex:81), and the calibration is stress-tested rather than merely asserted: two independent whole-campaign sweeps (F48, F49) show clearing the noise band is neither necessary (6/11 above-band moves ship nothing) nor sufficient (identical −31-exit collapses move the score +9 and +4) for an edit to have worked. This is a substantially more rigorous treatment of "what can this instrument even detect" than is typical.

### S3: A genuinely load-bearing, checkable fact ledger
56 numbered facts, each carrying sample, scope, class (A/B/C) and a named recompute script. I confirmed by `ls` on `experiments/analysis/` that **every one of the ~26 scripts named in the ledger exists** (`audit_flip_rate_three_seeds.py`, `audit_gain_face.py`, `audit_slope_permutation.py`, `audit_lift_uncertainty.py`, `plot_campaign_scores.py`, etc.) — not executed, per instructions. The 24-entry retraction registry (§C.2) documents reversed claims in both directions, and the 15-item error registry (Appendix A.3) tallies bias direction (8 errors favoured the project, 3 disfavoured it, 2 neutral) rather than only listing self-flattering corrections.

### S4: Honest, dated, direction-disclosed scope rulings
Appendix A.1's three scope rulings each carry an exact date and an explicit statement of which way the ruling moved the headline numbers — notably, the evidence-whitelist ruling (2026-08-26) "moved the headline numbers against the graph" (ch/A-deviations.tex:26–33; also ch/01-introduction.tex:418–423). A ruling that excludes data and is disclosed to have hurt the preferred hypothesis is a strong anti-cherry-picking signal.

### S5: A targeted, biased sub-sample correctly kept separate from the main estimate
The 25-task no-op audit batches deliberately over-sample recent flippers (`run_meta_aegis.py:1039–1043`), and the thesis measures this bias explicitly (F41: audit-window flip rate 41.6% vs bed-level 21.0%) rather than pooling it into the headline flip-rate or gain-face statistics — F48 explicitly restricts to "pairs whose two rounds both ran a full fresh batch" (ch/06-results.tex:564–567). Correct handling of a known non-random sub-sample.

---

## Weaknesses

### W1: Un-clustered confidence interval on the central noise-floor statistic
**Problem**: F15/F9e report the pooled 20.1% same-config flip rate with a 95% Wilson interval (`[18.4%, 21.9%]`) computed over 2,000 task-pairs (100 tasks × 20 windows) as though each pair were an independent Bernoulli draw (ch/05-design.tex:118–128; ch/C-ledger.tex:155–164). But the thesis's own F41/F54 establish substantial **task-level** heterogeneity in flip propensity — 21 tasks with literally zero variance, 79 "volatile," and recently-flipped tasks re-flipping at 1.6–2.1× the bed rate (ch/C-ledger.tex:472–480, 681–696) — which means the 20 window-level observations per task are not independent replicates but repeated measures on 100 underlying units with heterogeneous *p_i*.
**Why it matters**: this is the single most load-bearing number in the thesis — the −8…+5 band, the σ = 3.70 calibration, and the "below-floor selection" proposition all key off it. Task-level clustering with heterogeneous *p_i* generally inflates true sampling variance beyond the naive binomial formula (a design-effect/ICC problem), so the reported interval likely understates true uncertainty, in the direction that makes the noise floor look *more* precisely known than it is. The authors already apply exactly this fix elsewhere (S1/F9d's candidate-level bootstrap), so the omission looks like an oversight rather than a considered choice.
**Suggestion**: report a task-clustered bootstrap CI (resample by task, not by pair) for F15/F9e's pooled flip rate, structurally identical to what `audit_lift_uncertainty.py` already does for F9d.
**Severity**: MAJOR. **Fix-class**: [R] — recomputable from the `task_history` data `audit_flip_rate_three_seeds.py` already reads; no new runs.

### W2: A number the ledger itself retracted survives, uncorrected, one clause after its replacement
**Problem**: ch/06-results.tex:397–401 reads: "...exceeds the best single round any arm recorded, 76, by **21** tasks \F{16}. A loop optimizing a single round's score is optimizing a number **25** below what its own history has already achieved." 97 − 76 = 21 (matching F16 and ch/01-introduction.tex:123's own "twenty-one tasks of headroom"), but the next clause says 25. F16 itself names the source of "25": "**96/103 with a gap of 25**, which was computed over two seed-1 runs on the 103-task bed" is listed as one of "two superseded readings [that] are withdrawn" (ch/C-ledger.tex:233–237).
**Why it matters**: this is exactly the failure the ledger's own discipline exists to prevent — a retracted number re-entering the body, contradicting a correctly-anchored figure one clause earlier. It is a five-second check for any examiner who does the subtraction, and reads as carelessness in an otherwise scrupulously cross-checked document (I independently re-verified a dozen other ch6/ch7 summary statistics — plateau SDs, cost totals, gate-kill counts, F51's 8,393 workload sum — all reproduced exactly).
**Suggestion**: change "25" to "21" at ch/06-results.tex:401.
**Severity**: MAJOR (visible, easily caught, undercuts a stated guarantee). **Fix-class**: [W].

### W3: The pre-registration record behind the thesis's central falsification claim is asserted but never dated or located
**Problem**: "H1 was registered as falsifiable before the graph campaign" (ch/01-introduction.tex:204) and "[the prospective batch is] the test the stopping rule was registered against" (ch/05-design.tex:262–263, backing F34) carry no date, commit hash, or file pointer — unlike Appendix A.1's three scope rulings, each dated exactly *so a reader can judge priority over the data* (2026-08-26/27/28). A read-only search found no located artifact cited in the thesis; a `git log` scan shows a repository pattern of dated "pre-registered ignition log" commits for other campaigns, suggesting the underlying practice was plausibly followed, but nothing in the submitted text lets a reader verify *this* registration's timing.
**Why it matters**: the thesis's whole rhetorical architecture rests on "one confirmatory test, everything else exploratory" and on H1 being *rejected* rather than merely unsupported. Both claims are only as strong as their date of registration relative to the data — the exact standard the thesis rightly applies to its own scope rulings.
**Suggestion**: cite a date and file/commit for (a) H1's registration and (b) F34's stopping-rule registration, in the style already used in Appendix A.1.
**Severity**: MAJOR. **Fix-class**: [R] (retrieval from existing project history, not new work).

### W4: A specific, checkable inconsistency between two "Class A" recompute artifacts
**Problem**: `fig/scores-table.tex` (machine-generated by `plot_campaign_scores.py`, "do not edit") marks GHX-seed-3 round 10 as a round "into which a candidate shipped" — the figure caption's own stated convention for a bold entry (ch/06-results.tex:292–295: "A filled marker is a round into which a candidate shipped; a hollow marker re-ran the previous round's configuration unchanged"). I parsed the row directly: Graph/Seed 3, R9 = 64 (not bold), R10 = **66 (bold)**. Yet Table 6.x (`tab:starvation`, ch/06-results.tex:595) and ledger row F49 (ch/C-ledger.tex:598) both describe the identical R9→R10 pair as having "nothing shipped."
**Why it matters**: this pair is one of only four whole-bed illustrations behind F48/F49's "clearing the band is neither necessary nor sufficient" argument. If a candidate did land into R10, this row needs revising (the other three are unaffected). The class of error is not hypothetical for this codebase: ch/03-baseline.tex:151–157 documents an off-by-one that silently emptied the loop's own regression report.
**Suggestion**: reconcile `plot_campaign_scores.py`'s ship/no-op determination against `audit_gain_face.py`'s for this one round-pair.
**Severity**: MAJOR. **Fix-class**: [R] — no new runs, a recheck of two existing scripts against existing data.

### W5: Model-tier selection rests on uncited external benchmark figures
**Problem**: ch/05-design.tex:78–94 justifies the solver/meta tier choice with precise third-party numbers — BrowseComp 83.4/53.5/73.2, price ratios 3.1×/1.3×/2.4×, MRCR-1M 37.5, an unnamed "third-party measurement" of tool-calling cleanliness — and I confirmed there is **no `\cite` command anywhere in ch/05-design.tex** (`grep` returns empty) and no `\F{}` anchor either (correctly, since these are not this project's own recomputed facts — but nothing else sources them).
**Why it matters**: this is the justification for a foundational design choice (§5.1, reasons 1–2: why Flash over Pro leaves an effect somewhere to appear), and as written it is unverifiable by a reader.
**Suggestion**: cite the model-card/leaderboard source for each figure, or footnote them collectively.
**Severity**: MAJOR. **Fix-class**: [W].

---

## Detailed Comments

### Research Questions & Hypotheses
H1 is stated cleanly and its rejection is careful at its best — "H1 is rejected, on declared substitute endpoints... A registered endpoint that dies with its own measurability cannot carry a falsification" (ch/01-introduction.tex:274–287) — and the retraction registry shows the authors caught and walked back an earlier, less careful "H1 is falsified, unqualified" (ch/C-ledger.tex:815–819). I would still gently press the verb: with the *registered* endpoint (localization) ruled "not adjudicable" rather than adjudicated, "rejected" keeps a whiff of a completed test the design could not run. "Not supported on any measurable endpoint" is more defensible, though the thesis already argues this distinction elsewhere. MINOR, [D] — author's call; posed as a question below.

### Analysis Methods
The McNemar worked example (8-fixed/1-broken ⇒ *p* ≈ 0.039 against a same-round total of +7 inside the band, ch/05-design.tex:195–198, F21) is arithmetically exact — independently recomputed (exact two-sided sign test, *n*=9: 2·[C(9,8)+C(9,9)]/2⁹ = 20/512 = 0.0391) — and correctly labelled exploratory both at its point of use and in §5.4's multiplicity declaration. F9d's minimum-detectable-lift calculation ("no-graph 1.51, graph 1.37... at α=0.05") does not state its target power (conventionally 80%); a one-line clarification would remove ambiguity between a genuine power-based MDE and the smaller "critical value at 50% power." MINOR, [W].

### Selection Effects
Addressed thoroughly and honestly: the graph-campaign exclusion is dated and disclosed to move results against the graph (S4); the gateway-outage/restart recovery uses an outcome-independent criterion (zero-cost rows mark corruption mechanically), and washed windows enter flip statistics only if "verified clean" (ch/06-results.tex:330–332); the audit-batch bias is measured and kept separate (S5). Unresolved without running code: whether flip-rate/SD estimates differ between uninterrupted and washed-and-reflown windows in seeds 2–3 is not reported; unlikely to matter given how few windows are affected, but worth a one-line check. MINOR, [R].

### Reproducibility
All named recompute scripts exist (S3). The text does not state whether the raw run artifacts those scripts read (`task_history`, `curves.json`, cost/error logs) are packaged with the submission — `recipe/gaia_evolver/runs/` was not opened per instructions, so this is a question for the authors, not a claim of absence.

### Methodological Fallacies Detected
None of the checklist's classic fallacies (p-hacking, HARKing, uncorrected multiple comparisons, survivorship bias) is present in a form that damages a conclusion. The closest near-miss is the multiplicity handling of the "four apparent wins" (W4's numbers, ch/05-design.tex:274–277) — but the thesis's actual confirmatory-test declaration (§5.4) is exactly the correct antidote to that near-miss, which is why I have not scored it as a fallacy in its own right.

---

## Unanchored or mis-anchored numbers

| Location (file:line) | Number(s) | What anchor it should carry |
|---|---|---|
| ch/06-results.tex:401 | "25" (below what its own history achieved) | Should read **21** (matches \F{16}, already stated one clause earlier in the same sentence); "25" is F16's own explicitly superseded/withdrawn figure (ch/C-ledger.tex:233–237) |
| ch/05-design.tex:274–275 | "$+7$, $+5$, $+4$, $+6$"; "three different instruments" | No \F anchor in the paragraph. $+7$/$+5$ trace to \F{36} in ch6; $+4$/$+6$ have no independent itemized source found. "Three different instruments" here and at ch/06-results.tex:472 also conflicts with ch/C-ledger.tex:392–393 and :778, both of which say the four wins were "each killed by a different instrument" |
| ch/03-baseline.tex:330 | "$0.48$" (binomial probability of 0/3 hits) | No independent \F; inputs ($7/32$, 3 predictions, 0 hits) are covered by \F{6}, but the derived 0.48 itself is not restated in F6's ledger text |
| ch/05-design.tex:78–94 | BrowseComp $83.4/53.5/73.2$; price ratios $3.1\times/1.3\times/2.4\times$; MRCR-1M $37.5$ | External benchmark figures; carry neither \F (correctly, out of ledger scope) nor \cite (no citation exists anywhere in the file) |

---

## Questions for Authors
1. For F15/F9e's pooled flip-rate interval: was a task-clustered (rather than pair-pooled) variance estimator considered and rejected, or simply not applied? If rejected, on what grounds — given F9d applies the analogous candidate-level clustering just one section over?
2. What is the specific date/commit/file for H1's pre-registration and for F34's stopping-rule registration? (W3)
3. Is GHX-seed-3 round 10 genuinely a ship or a no-op round? (W4) This is a single, mechanically checkable fact from data already in hand.
4. Are the raw run artifacts (`task_history`, `curves.json`, logs) that the 26 named scripts read intended to accompany the submitted repository?

---

## Minor Issues

### Numerical / Wording
- ch/06-results.tex:401 — "25" → "21" (W2).
- ch/05-design.tex:274 — add \F{34}\F{36} and reconcile "three" vs "four" instruments (W4).
- ch/05-design.tex:78–94 — add citations for external benchmark figures (W5).
- F9d (ch/C-ledger.tex:146–148) — state the power level assumed in the minimum-detectable-lift calculation.
- The verb "rejected" for H1 (ch/01-introduction.tex, ch/08-conclusion.tex) could be softened to "not supported on any measurable endpoint" without weakening the argument — the thesis already makes this exact case in its own careful passages; only the summary verb lags it.

### Figures and Tables
- Table 6.x (`tab:starvation`, ch/06-results.tex:586–606) and Figure 6.x (`fig:scores`) should agree on the ship/no-op status of every round pair they both describe; currently one pair does not (W4).

---

## Dimension Scores

| Dimension | Score (0–100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | — | Not scored | Outside this review's assigned focus (blind spot per reviewer configuration); deferred to R2/R3 |
| Methodological Rigor (25%) | 80 | Strong | S1–S2 are genuinely sophisticated; W1/W3 are real but fixable gaps in an otherwise careful apparatus |
| Evidence Sufficiency (25%) | 78 | Strong | Large, well-documented evidence base (S3); central between-arm comparisons candidly hit a small-*n* design floor, and W1 means reported precision on the noise floor is likely somewhat optimistic |
| Argument Coherence (15%) | 85 | Strong | Self-aware treatment of the capability-wall rival hypothesis (ch7 §7.1) and of the substitute-endpoint problem; docked only for W4's small internal inconsistency |
| Writing Quality (15%) | 85 | Strong | Precise, low on hedge-padding, follows its own stated discipline almost everywhere (not this reviewer's primary lane) |
| Literature Integration | — | Not scored | R2 focus |
| Significance & Impact | — | Not scored | R3 focus |
| **Weighted Average (scored dimensions only)** | **~81** | **Minor Revision** | Composite over Methodological Rigor, Evidence Sufficiency, Argument Coherence, Writing Quality only; final weighted score requires R2/R3's Originality and Literature Integration scores |
