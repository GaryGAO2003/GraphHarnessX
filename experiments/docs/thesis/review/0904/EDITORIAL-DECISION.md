# Editorial Decision

## Manuscript Information
- **Title**: Provenance-Grounded Self-Evolution of LLM Agent Harnesses — A Graph-Native Runtime, a Pre-Registered Falsification, and the Missing Efficacy Readout
- **Author**: Fei Gao, MSc Machine Learning, UCL (COMP0091), supervisor Prof. Jun Wang
- **Submission date**: 9 September 2026
- **Decision date**: 2026-09-04 (overnight synthesis; author asleep, loop authorised to decide and proceed)
- **Review round**: Round 1 — 7-line panel (EIC + 3 peer reviewers + Devil's Advocate + guardrails/ledger audit + mechanical/compliance)

---

## Decision

### Minor Revision

All seven lines land on the same tier. R0 (EIC), R1 (Methodology), R2 (Domain) and R3 (Perspective) each explicitly recommend Minor Revision, weighted dimension scores ~80–81/100, confidence 4–5. R5 (guardrails/ledger) returns "⚠️ Revise" — no fabrication, no Domain-D issue. R6 (mechanical) finds a clean compile and two additive, non-structural compliance gaps. R4 (Devil's Advocate) finds no defect that reverses the result's sign — "scoped as CRITICAL for the specific, narrowly-stated claim only" (R4 CRITICAL #1) — and its surviving points ask for hedging and disclosure, not new data. No line asks for re-analysis, additional data, or restructuring; every fix below is wording, a citation, a recompute from data already on hand, or an administrative addition — squarely Minor Revision under the standards document's criteria (≥3/4 peer recommendations Minor-or-better, no reviewer recommending Major or Reject).

### Reviewer Summary

| Reviewer | Role | Recommendation | Confidence |
|---|---|---|---|
| R0 | EIC / Examination-board chair | Minor Revision | 5 |
| R1 | Methodology | Minor Revision | 5 |
| R2 | Domain | Minor Revision | 4 |
| R3 | Perspective | Minor Revision | 4 |
| R4 | Devil's Advocate | (adversarial mandate; net reading consistent with Minor) | — |
| R5 | Guardrails + ledger audit | "Revise" (no fabrication, no Domain D) | — |
| R6 | Mechanical / compliance | (no tier issued; 2 MAJOR compliance gaps, else clean) | — |

---

## Consensus Analysis

**Method note.** R0–R3 were configured with deliberately non-overlapping focuses and blind spots (00-panel-config.md), so four-way agreement on a single sub-claim is structurally unlikely by design. Corroboration here instead comes from the two specialist audit lines (R5's script re-execution, R6's LaTeX/compliance parse) independently landing on a defect a focus-reviewer already raised. Below, "corroborated" means ≥2 lines, named.

**Corroborated across ≥2 lines:**
- **Ship-rate headline has unstated, asymmetric scope.** R3 W2 (true arm mean 0.68, not 0.62) + R4 CRITICAL #1 (0.92-vs-0.88 reversal in one seed, unreconciled) — own section below.
- **External benchmark figures justifying the solver tier are uncited.** R1 W5 + R5 [C1/C4] — identical location (ch/05-design.tex:78–94), independently found.
- **Stale code-pin for the rollback rule in Appendix A.** R2 W2 + R5 §(iii) — both name `run_meta_aegis.py:901–911` where the rule lives at `:1425`; re-verified directly (1425 is the conjunction; 901–911 is unrelated `AegisAgent` wiring).
- **"Non-positive...regardless of variation quality" is asserted, not derived.** R3 (borrowed-frames, MAJOR) + R4 MAJOR #5 — same passage (ch/07-discussion.tex:39–68), no ratchet model or expectation calculation shown.
- **Abstract/subtitle state a field-level claim without the body's own hedge.** R2 (generalisation) + R4 MINOR #8 — both omit the "an inference, flagged as one" qualifier ch7 carries.
- **Front-matter page-counter reset timing produces two related cosmetic defects.** R0 + R6 — same root cause (`\setcounter{page}{1}`, THESIS.tex:116), different symptoms (LoT page stamp vs. 6 duplicate hyperref destinations).
- **GenAI-use declaration and repository-access statement are both absent.** R0 W5 (CRITICAL) + R6 UCL-checklist (MAJOR) — same two omissions.

**Single-reviewer, high-confidence findings carried forward as required:** R0's RQ-compression (W1), no-roadmap (W4), ledger-overargues (W3) — all confidence 5, within remit; R1's unclustered CI (W1), unlocated pre-reg date (W3), fig/scores-table.tex vs Table 6.x discrepancy (W4) — confidence 5; R2's missing arXiv:2607.12227 (W1, confidence 4, the panel's single most consequential domain finding); R3's noise-band arm-scope (W1), uncited GAIA (W3), "level-2" collision (W4) — confidence 4; R4's remaining MAJORs (#2, #3, #4, #6, #7); R5's class-honesty finding (13 rows misclassified) and recompute-drift cluster (ledger line, below); R6's two MAJOR gaps (`tab:results` unreferenced, Table 2.1's caption).

---

## Points of Disagreement and Arbitration

**1. Trim the Fact Ledger (R0 W3) vs. strengthen individual rows (R1 W1/W3/W5, R5).** Not a true conflict once decomposed: R0 wants argumentative *prose* moved to one-line cross-references; R1/R5 want *statistical/sourcing* content added to specific rows (clustering, dates, citations). **Resolution**: trim rhetoric, never the R1/R5 additions — apply P2-01 only after, and without touching, the P1 items adding content to F9e/F15, F34, and §5.1. The two operations act on different textual layers and sequence safely; conflating them risks deleting exactly the substance R1/R5 asked to be strengthened.

**2. H1's verb, "rejected" (R1, mild) vs. everyone else's continued use of it (R0 endorses the rejection framing; R2/R3/R4 use "rejected" without objection).** A single-reviewer preference, not a SPLIT — no one disputes it, the rest are silent. **Resolution**: adopt R1's suggestion at headline locations only (abstract, §1.3 verdict box, Ch8 close) — R1's own point is "the thesis already makes this case in its careful passages; only the summary verb lags it," so the fix is localized. Logged [D] in the morning table; the author may reasonably override.

**3. GHX's engineering scale vs. its credited contribution.** R2 judges GHX's *claims* well-calibrated to the evidence ("I found no place in ch4 that claims more than ch6 supports"); R4 MAJOR #7 judges the *effort-to-insight ratio* poor and unargued. Compatible, not contradictory — a system can make honest, narrow claims while being disproportionate to build. **Resolution**: both stand; add R4's concession (P1-24) without retracting R2's calibration finding.

No other genuine cross-reviewer conflict was found; every remaining item is a single-reviewer finding (confidence-weighted) or a corroboration listed above.

---

## Devil's Advocate CRITICAL Disposition

**R4 CRITICAL #1**: "Ship rate is $0.62$ per round against $0.88$" is used as a clean, mechanism-attached headline finding (ch/01-introduction.tex:257–262; ch/06-results.tex Table 6.1, line 29) while F10 itself (ch/C-ledger.tex:166–169) records per-seed graph-arm values of $0.50/0.92/0.62$ — one of which ($0.92$) *exceeds* the no-graph comparator ($0.88$). No seed breakdown or reconciliation appears anywhere the contrast is used as evidence.

**Is it defeated?** No. No reviewer supplies evidence that the reversal doesn't exist or that the single-number framing is fair; R1 and R6 are silent (not dissenting), and R3 W2 independently corroborates the identical defect from a different angle (the three graph-arm values average 0.68, not 0.62, and "0.62" is not, unlike its Table 6.1 neighbours, actually an arm mean). Two reviewers converging *reinforces* the CRITICAL; it does not defeat it.

**Does it block Accept?** In principle yes — but Accept was never live here: R0–R3 all independently landed on Minor Revision before this CRITICAL is even factored in. The practical question is whether it forces *Major* instead of Minor. It does not, for three reasons in the DA's own report: (a) the DA scopes the finding as not cascading into the thesis's central claims — "a non-replicating process metric is *consistent* with the thesis's own 'everything here is noisy' theme"; (b) the fix is a bounded sentence rewrite, not new analysis; (c) R5's ledger audit found F10 itself has a further, distinct problem — the printed $0.62/29\%$ does not match today's recompute ($0.60/30\%$; `M26_100x16b` grew after the number was frozen) — so the sentence cannot be safely rewritten *until* the ledger line refreshes F10.

**Resolution**: two-step, sequenced. (1) The ledger line (Maker-A, already tasked, not re-planned here) refreshes F10 against the current `M26_100x16b` state. (2) Every sentence currently stating "$0.62$ vs $0.88$" as a bare pair — the abstract-adjacent §1.5 bullet, Table 6.1's row, and any ledger-adjacent restatement — is rewritten to quote either all three graph-arm seed values or the correctly-computed three-seed arm mean, explicitly naming that one seed's ship rate exceeds the no-graph figure. This is P1-26, deliberately placed last in the roadmap because it cannot close before step (1) lands. **Nothing else in the panel blocks Minor Revision.**

---

## Decision Rationale

Four independent reviewers scoring non-overlapping dimensions converge on Minor Revision with confidence 4–5 and weighted scores 80–81/100; the two specialist audit lines find no fabrication, no undefined references, a clean compile, and that roughly three-quarters of load-bearing statistical claims re-execute exactly against checked-in scripts. The Devil's Advocate could not find a case the central conclusions are wrong: eight of ten mandated attack lines are substantially or fully defeated by the manuscript's own evidence, and the one CRITICAL that survives is narrow, self-scoped by the DA as not touching the non-separation/H1 result, and resolvable by a ledger refresh plus a bounded rewrite. The remaining MAJOR items cluster into three families: (1) two verified-false or verified-risky claims (the abstract's "one published...code released" superlative, confirmed false by AUTHOR-FACTS.md; the ship-rate headline) requiring correction before "Minor" is credible; (2) missing compulsory administrative content (GenAI declaration, repository statement); (3) a tail of citation, dating, disclosure and terminology gaps that touch presentation, not the argument. None requires new experiments — the freeze is respected throughout (the one item that would benefit from new data, R4 MAJOR #4, is already honestly hedged as a proposition and stays that way). Major Revision was considered and rejected: no reviewer requested it, and no fix here needs re-analysis, section rewriting, or additional data — only recomputation of numbers already on disk, and prose.

---

## Strengths the Panel Agreed On

1. **Self-audit as evidence of rigor, not confessed weakness.** The 15-item error registry (8 favourable, 3 unfavourable, 2 neutral) and the 24-entry retraction registry are praised by R0 (S2), R1 (S3/S4), R2 (S4), R3 (S4), R5 ("strong self-correction culture"), and R4's Observations, which credits them with pre-empting several attacks it would otherwise have led with.
2. **A genuinely correct positive control.** The budget-starvation repair, read through ICH E10 assay-sensitivity logic, calibrates the instrument's detection limit before using it — R0 (S3), R1 (S2), R3 (S3), and R4's disposition item (d) all call this the most carefully reconciled point in the document.
3. **Scrupulous, repeated credit-assignment discipline.** GHX's claimed contribution is narrower than it would be easy to claim, and says so at every opportunity — R0 (S5), R2 ("I found no place in ch4 that claims more than ch6 supports"), R3 (S2).
4. **Code-pinned, falsifiable diagnosis.** Every ch3 file:line claim R2 and R5 checked (3/3 each) resolved exactly against the live source.
5. **A fact-ledger architecture that mostly works.** R1 confirmed all ~26 named scripts exist; R5 re-executed 33 `[A]`-classed rows and found 25 exact matches, calling the anchoring discipline "real and unusually strong" even while flagging the gaps below.

---

## Revision Roadmap

### Priority 1 — Required (26 items)

| ID | Exact change | Source | Sev | Class | Location | Acceptance check |
|---|---|---|---|---|---|---|
| P1-01 | Replace "...the one published harness-level closed loop whose code is released, and a carefully governed one" with "...a published harness-level closed loop with released code and, to our knowledge, the most heavily governed one" | AUTHOR-FACTS + R2(positioning) | CRITICAL (verified false) | [W] | ch/00-abstract.tex:6–9 | Sentence no longer claims uniqueness; Table 2.1 unchanged |
| P1-02 | Add unnumbered "Declaration of Generative-AI Use" section per AUTHOR-FACTS (tool, version, publisher, one sentence of context; solver/meta-role LLMs excluded as objects of study) | R0 W5 + R6 | CRITICAL | [W]-draft | New section, THESIS.tex after line 111, before `\tableofcontents` | Section exists, names tool+version+publisher+URL, author confirms |
| P1-03 | Add "Code and Data Access" statement: fork URL, branch, commit fixed at submission, recompute-script directory, run-archive availability | R0 W5 + R6 | CRITICAL | [W]-draft | Same location as P1-02 | Statement exists with URL+branch+commit language |
| P1-04 | Push `ghx/m27-variance` to `origin` before submission (currently local-only) | AUTHOR-FACTS | CRITICAL (blocks P1-03 being true) | [D] | n/a (git operation) | `git ls-remote --heads origin ghx/m27-variance` non-empty |
| P1-05 | Abstract: add one clause naming F34's null pre-registered efficacy result; change "candidates ship on it" → "one candidate shipped on it" (matches ch/01-introduction.tex:172's existing correct usage) | R0 W2(a)/(b) | MAJOR | [W] | ch/00-abstract.tex:19, and one added clause in the 4th paragraph (lines 35–47) | Abstract mentions F34; "candidates ship" now singular |
| P1-06 | Promote Q1–Q3 to a labelled subsection with registration-timing status each; add one closing sentence per question in Ch8 | R0 W1 | MAJOR | [W]-draft | ch/01-introduction.tex:209–216 (§1.4); ch/08-conclusion.tex | "Research Questions" subsection exists; Ch8 references Q1/Q2/Q3 by label |
| P1-07 | Add 6–8 sentence chapter-by-chapter roadmap; state Ch3 is formative/diagnostic, distinct from Ch6's main results | R0 W4 | MAJOR | [W]-draft | End of §1.9, after ch/01-introduction.tex:428 | Paragraph exists mapping all 8 chapters + 3 appendices |
| P1-08 | Add a glossary from R3's 39-term table; prioritise the 6 flagged load-bearing-undefined terms (deaf, archaeology, the clinic, processor, resolution, \F{} notation); cross-reference the level-2 fix (P1-09) | R2(Processor) + R3(glossary+flags) | MAJOR | [W]-draft | New section/appendix, reusing ch/C-ledger.tex's dense description-list style | Glossary exists; all 6 flagged terms glossed |
| P1-09 | Rename GAIA-difficulty-tier references (e.g. "GAIA-difficulty-2"); reserve "L2"/"rung 2" for the readout ladder only | R3 W4 | MAJOR | [W] | ch/03-baseline.tex:375; ch/C-ledger.tex:450 (vs ch/00-abstract.tex:53, ch/01-introduction.tex:303) | `grep` "level-2" outside ladder context returns 0 |
| P1-10 | Add GAIA citation (Mialon et al.) at first use | R3 W3 | MAJOR | [W] | ch/99-bibliography.tex (new entry); ch/01-introduction.tex:98 or ch/05-design.tex:21 | `\cite{gaia}` (or similar key) present at first use, bibitem exists |
| P1-11 | Change "a number 25 below what its own history has already achieved" → "a number 21 below..." (matches \F{16}'s gap stated one clause earlier; 25 is F16's own explicitly withdrawn reading, ch/C-ledger.tex:233–237) | R1 W2 | MAJOR | [W] | ch/06-results.tex:401 | Both numbers in the sentence pair now read 21 |
| P1-12 | Add both missing citations to §2.1 (arXiv:2607.12227 primary; arXiv:2607.13285 secondary) and one corroborating sentence to §7.1 | R2 W1 | MAJOR | [W] | ch/02-related-work.tex:55–89; ch/07-discussion.tex ~32–38; ch/99-bibliography.tex | Both `\bibitem`s exist and are `\cite`d |
| P1-13 | Cite vendor/leaderboard source for BrowseComp 83.4/53.5/73.2, price ratios, MRCR-1M 37.5 | R1 W5 + R5[C1/C4] | MAJOR | [W] | ch/05-design.tex:78–94 | `grep -n "cite\|footnote"` non-empty |
| P1-14 | Report a task-clustered bootstrap CI (resample by task, not pair) for F15/F9e's pooled flip rate, as `audit_lift_uncertainty.py` already does at candidate level | R1 W1 | MAJOR | [R] | ch/05-design.tex:118–128; ch/C-ledger.tex:155–164 | New CI reported alongside the naive Wilson interval |
| P1-15 | Cite a date and file/commit for H1's pre-registration and F34's stopping-rule registration, in Appendix A.1's style | R1 W3 | MAJOR | [R] | ch/01-introduction.tex:204; ch/05-design.tex:262–263 | Both carry a dated commit/file pointer |
| P1-16 | Reconcile `plot_campaign_scores.py`'s ship/no-op call for GHX-seed-3 R9→R10 against `audit_gain_face.py`'s; fix whichever of the bold marker or "nothing shipped" is wrong | R1 W4 | MAJOR | [R] | ch/06-results.tex:292–295, 595; ch/C-ledger.tex:598 | Figure and table agree on this round-pair |
| P1-17 | Add a `Table~\ref{tab:results}` pointer in the prose following the table | R6 | MAJOR | [W] | ch/06-results.tex, section after line 57 | `\ref{tab:results}` appears at least once in body prose |
| P1-18 | Give Table 2.1 a short caption: `\caption[short][The five nearest systems against four properties]{...}` | R6 | MAJOR | [W] | ch/02-related-work.tex:359 | THESIS.lot entry for Table 2.1 is a short phrase, not the full paragraph |
| P1-19 | One sentence at Fig 6.1 and F48/F49 stating the ±3.70 band is derived from the three no-graph arms only, applied to the graph arm by assumption; if a bed-wide graph-arm window exists, add it as a new F-row instead | R3 W1 | MAJOR | [W] primary / [R] stretch | ch/06-results.tex:292–302, 334–346; ch/C-ledger.tex:155–164 | Caption or adjacent prose states the band's arm-scope |
| P1-20 | 2–3 sentences at §4.6/§6.3 naming the alternative reading of the sixth gate's 18 kills (targeting degradation) as not ruled out by a no-graph-side hand-audit | R4 MAJOR #2 | MAJOR | [W] primary / [R] stretch (spot-check ~10 candidates) | ch/04-ghx.tex:249–263; ch/06-results.tex:183–197 | Alternative explanation named, absence-of-audit stated |
| P1-21 | Add fresh-vs-carried round count per arm (or a caveat if not cheaply tabulable) alongside the +2.7 plateau-gap claim | R4 MAJOR #3 | MAJOR | [R] | ch/C-ledger.tex:533–538 (F46); ch/06-results.tex:271–272 | Fresh/carried split stated, or caveat added |
| P1-22 | State the criterion for "flown before the graph layer was correct" as a named defect list, commit, or test ID | R4 MAJOR #6 | MAJOR | [W] | ch/A-deviations.tex:18–33; ch/B-operations.tex:12–16 | A concrete pointer replaces the bare word "correct" |
| P1-23 | Tighten hedging on "selection is deaf" throughout (abstract, §7.1, Ch8) so it consistently reads as a proposition; name "attach L3 to retention and re-fly" in Future Work as the unrun discriminating experiment | R4 MAJOR #4 | MAJOR | [W] now (full resolution is [X], correctly deferred — frozen) | ch/07-discussion.tex:119–165, 290–303; ch/00-abstract.tex; ch/08-conclusion.tex | Every "deaf" claim reads as proposition; Future Work names the experiment |
| P1-24 | Add 2–3 sentences explicitly conceding the disproportion between GHX's build scale and its credited (narrow) contribution, framed as enabling infrastructure rather than defended as efficient | R4 MAJOR #7 | MAJOR | [D] | ch/04-ghx.tex intro or ch/08-conclusion.tex:34–40 | A concession sentence exists; author confirms framing |
| P1-25 | Decide and state the disclosure stance toward HarnessX/AEGIS maintainers for the defects found (evidence-column, unreachable clamp, empty regression report) and the F37 near-miss | R3 W5 | MAJOR | [D] | New paragraph, §7.2 or §7.3 | Paragraph states the decision made (disclosed / will disclose / not applicable, with reasoning) |
| P1-26 *(ledger-gated — do last)* | Once the ledger line refreshes F10, rewrite every "$0.62$ vs $0.88$" sentence to quote all three graph-arm seed values (or the correct 3-seed arm mean) alongside the no-graph figure, and name that one graph seed's rate exceeds the no-graph figure | R3 W2 + R4 CRITICAL #1 | **CRITICAL** | [W] | ch/01-introduction.tex:257–262; ch/06-results.tex:29 (Table 6.1); any ledger-adjacent restatement | No sentence anywhere states "0.62 vs 0.88" as an unscoped pair; reversal is named |

### Priority 2 — Suggested (15 items)

| ID | Exact change | Source | Sev | Class | Location |
|---|---|---|---|---|---|
| P2-01 | Tighten F9a–F9e-style rows to fact+sample+scope+script pointer; move argumentative sentences to a one-line cross-reference to the body. Recovers ~3–5 pages — apply only after, without touching, P1-14/15/19's added content | R0 W3 | MAJOR | [W] | ch/C-ledger.tex, e.g. F9a–F9e (95–153) |
| P2-02 | Re-point both Appendix A citations of the rollback rule to `run_meta_aegis.py:1425` | R2 W2 + R5 | MINOR | [W] | ch/A-deviations.tex:71–72, 128–131 |
| P2-03 | One sentence naming the `HARNESSX_GHX_PLANNER_SENSES` mechanism and its unproven (flag-off) status | R2 W3 | MINOR | [D]/[W] | §4.8 or Appendix C6 |
| P2-04 | Scope "supernet" to MaAS only; describe AgentSquare/EvoFlow generically | R2 W4 | MINOR | [W] | ch/02-related-work.tex:290–293 |
| P2-05 | Add one disambiguating clause at first mention of "AgentFlow" (edge-family donor) vs. the unrelated RL-optimized system of the same name | R2 W5 | MINOR | [W] | ch/04-ghx.tex:85–89 |
| P2-06 | 3–4 sentences naming and rebutting "why not just patch the 20-character heuristic," using the already-disclosed free-text identity problem and four broken feedback channels | R0 W6(a) | MINOR | [W]-draft | §1.5 or §4.1 |
| P2-07 | Add "on this bed and system class" (or equivalent) to the subtitle or the abstract's proposition sentence | R2(generalisation) + R4 MINOR #8 | MINOR | [W] | THESIS.tex:87–90 (subtitle); ch/00-abstract.tex:49–54 |
| P2-08 | Soften "expected cumulative gain...is consequently non-positive" to "can be non-positive under this bed's parameter regime," or add a short derivation | R3(borrowed-frames) + R4 MAJOR #5 | MAJOR | [W]/[R] | ch/07-discussion.tex:65–68; ch/00-abstract.tex:49–54 |
| P2-09 | Cite Falconer & Mackay (h² formula) + a regression-dilution source (Hutcheon/Chiasson/Platt 2010); name the ICH E10 add-on design once at §5.3's opening; add one clause distinguishing "resolution" (this thesis's MDE sense) from the VIM instrumentation sense | R3 minor ×3 | MINOR | [W] | ch/07-discussion.tex:41–53; ch/05-design.tex (§5.3 opening); ch/05-design.tex §5.4 |
| P2-10 | State Figure 1.1's reproduction licence and highlight the "Adapt" vertex distinctly; compute the promised Spearman-Brown repetition-pricing number (arithmetic on already-reported figures); add a rough token-count-based compute/carbon estimate | R3 minor ×3 | MINOR | [D]/[W]/[R] | ch/01-introduction.tex:59–60 (Fig 1.1); ch/05-design.tex:186–190, ch/07-discussion.tex:312–318 (Spearman-Brown); §7.4 (carbon) |
| P2-11 | One caveat sentence noting the |δ|≲3 calibration bound comes from a small, non-random hand-run set, not a random sample of the ~40+ shipped candidates | R4 MINOR #11 | MINOR | [W] | ch/07-discussion.tex:56–60, 94–97 |
| P2-12 | Disclose the six campaigns' calendar order/overlap (one sentence or a small table) | R4 MINOR #9 | MINOR | [W]/[R] | ch/B-operations.tex:19–27 |
| P2-13 | Fix `config.yaml` line citation (136 for R3–R5, 143 for R9/R15/R16, never 131); add a one-line ledger-preamble note that F17/F18 are supporting/cross-check rows not meant for standalone citation | R5 | MINOR | [W]/[D] | F39 citation; ch/C-ledger.tex preamble |
| P2-14 | Move `\setcounter{page}{1}` to immediately after `\listoffigures` and before `\listoftables` (or force `\clearpage` at the reset point) | R0(formatting) + R6 | MINOR | [W] | THESIS.tex:113–116 |
| P2-15 | Capitalise "digester" → "Digester" and "the planner" → "the Planner" | R6 | MINOR | [W] | ch/B-operations.tex:80; ch/02-related-work.tex:202 |

### Priority 3 — Nice to Fix (8 items)

| ID | Exact change | Source | Class |
|---|---|---|---|
| P3-01 | Small ladder diagram near §4.9's first full description (Fig 4.1 already covers L0–L2 live/L3-by-hand partially) | R0 W6(b) | [W]-draft |
| P3-02 | One exploratory-labelled sentence on whether graph-style step-pinned citation interacts differently with leak-derived answers than free-text citation | R4 MINOR #12 | [R] |
| P3-03 | Add F47 explicitly to §5.4's illustrative exploratory-test list | R4 MINOR #13 | [W] |
| P3-04 | One clause clarifying "checkable" is a bundle of independently measured facts (F7/F11/F52/F53), not itself one operationalized quantity | R4 MINOR #10 | [W] |
| P3-05 | Reword the long unbreakable `\texttt{}` token causing the underfull hbox; add `labelindent=0pt` to silence the two enumitem negative-labelwidth warnings | R6 | [W] |
| P3-06 | Spell out "Large Language Model (LLM)" at first use | R6 | [W] |
| P3-07 | Four low-stakes arithmetic/ordering tensions, each worth one clarifying clause: DAG expanded after 2 unexpanded uses (leave as-is, abstracts tolerate this); Table 6.1's "+0.37" vs. 0.86−0.48=0.38 (rounding-of-rounded-components, note it); "22/72 vs 17/72: +5, 3 gained/1 lost" (net is +2 — clarify "largest gains" is illustrative, not exhaustive); "86.0%" (8×) vs "86%" (3×) — normalise to one form | R6 | [D] |
| P3-08 | Change "H1 is rejected" → "H1 is not supported on any measurable endpoint" at the 2–3 headline locations only (abstract, §1.3 verdict box, Ch8) | R1(minor) | [D] |

---

## Assigned to the Ledger Line (Maker-A — not re-planned here)

Per R5 Part 2, these ledger rows have real, traceable drift or misclassification, all already assigned to the parallel ledger-repair line: **F10** (ship rate: ledger $0.62$/29% vs. recompute $0.60$/30%), **F13** ($36.3 vs. $38.1), **F31** (leak-route census: 44 vs. 49 tasks), **F44** (seed-2 flip rate: script regressed to the 103-task bed instead of the mandated 100-task subset — a script-scope bug, distinct from the other rows' data-growth cause), **F45** (115/600 → 117/600), **F54** (9,600 → 9,700 evaluations; breaks its stated cross-agreement with F16), **F55** (n=33 vs. n=56) — the first six trace to `M26_100x16b` being resumed and extended after its numbers were frozen (`.resume.*.log` on disk); F54's cap is the M22-R16 boundary in the ledger-line's own scope. Also assigned: **F26–F39 (except F31)**, thirteen rows classed `\cls{A}` "recomputable" naming no script; and **F43**, whose named "script" is a live trial launcher, not a read-only recompute — over-claiming recomputability in the opposite direction.

**Prose depending on the ledger line's output**: P1-26 is gated on F10. Once F31/F44/F45/F54 land, re-verify the leak-route/pathology-census paragraphs (6 locations citing F31's count), any swing-range wording tied to F44's corrected recomputation, and F16/F54's cross-agreement statement.

---

## Author Decisions in the Morning

| Item | Issue | Recommended default |
|---|---|---|
| P1-04 | Push `ghx/m27-variance` to origin | Push immediately — the content is meant to be public per AUTHOR-FACTS; no reason to withhold |
| P1-24 | Concede GHX effort/insight disproportion | Adopt R4's framing (enabling infrastructure, not efficient build) rather than defend the build scale |
| P1-25 | Disclosure stance toward HarnessX/AEGIS maintainers | State that findings will be shared with the maintainers (e.g. email/issue linking the relevant chapter) around submission; do not delay submission awaiting a response |
| P2-03 | Name `HARNESSX_GHX_PLANNER_SENSES` in ch4/C6 | Add the one sentence — cheap, strictly additive, no downside found |
| P2-10 (Fig 1.1 licence) | State the reproduction licence | Check the vendored HarnessX repository's own LICENSE file and cite it exactly (author or main loop can do this directly — it is a lookup, not a judgment call) |
| P2-10 (carbon) | Compute/energy reporting | Add one rough token-count-based estimate sentence; do not attempt a precise carbon figure |
| P2-13 | Annotate F17/F18 as non-citable supporting rows | Add the one-line ledger-preamble disclaimer (matches F9's existing precedent) |
| P3-07 (DAG ordering) | Abstract/intro use DAG before Ch4 expands it | No change — R6 itself notes abstracts conventionally tolerate this |
| P3-07 (three arithmetic tensions) | Minor rounding/net-sum optics | Add one clarifying clause each rather than leave unaddressed — these are exam-facing numbers an examiner could raise at viva |
| P3-08 | H1 verb "rejected" vs "not supported" | Adopt the change at the 2–3 headline locations only (see Disagreement 2 above); leave body passages that already carry the fuller hedge untouched |

---

## Page-Budget Note

Current: **109 pages** at 12pt (ceiling 120; 11 pages headroom). Additions authorised for the loop to draft: GenAI-use declaration (~0.3–0.5 pp — per AUTHOR-FACTS conventionally **not counted** toward the limit as unnumbered front matter); repository statement (~0.2–0.3 pp, counted); RQ subsection + Ch8 closure (~0.5–0.75 pp); chapter-roadmap paragraph (~0.3 pp); "why not patch it" paragraph (~0.2–0.3 pp); ~40-term glossary in the ledger's dense description-list style (~1.5–2.5 pp, the largest addition); two citations + sentences (~0.15–0.25 pp); optional ladder diagram (~0.4–0.6 pp, P3, skippable — Fig 4.1 partially covers this already). **Total: ~3.5–5.0 pages**, landing at roughly **113–114 pages** — still 6–7 pages under ceiling before any trim. **P2-01 (ledger trim) is therefore not required** to stay within budget; attempt it only if time allows, after and without disturbing the P1 items that add ledger-row content. No page-ceiling risk was identified anywhere in the panel.

---

*Synthesis by the editorial_synthesizer_agent (Phase 2). All 7 Phase 1 reports plus AUTHOR-FACTS.md were read in full. No new critique was introduced; every item traces to a named reviewer report or, for P1-01/P1-04, to AUTHOR-FACTS.md as instructed. Ledger-line items are listed for traceability only, not re-planned here.*
