# Devil's Advocate Review — Provenance-Grounded Self-Evolution of LLM Agent Harnesses

Reviewer: R4, Devil's Advocate. Mandate: argue the strongest case that the thesis's central
conclusions are wrong or unearned (Card #4). Evidence base: THESIS.tex and ch/00–08, A–C, 99,
fig/scores-table.tex, read in full. Fix-class legend used throughout: **[W]** wording only,
**[R]** recompute/new ledger row from data already on hand, **[X]** needs new experiments
(frozen since 27 Aug), **[D]** author's decision/framing, not a computational fix. Neither of
the skill's field-norm columns is populated below: none of this review's CRITICAL/MAJOR
findings rest on a claim about what the field *should* do — all are internal-evidence and
logic-chain findings, checked directly against the thesis's own numbers.

Before attacking it: this is an unusually self-auditing document. The fifteen-error registry,
the retraction registry, the \cls{A/B/C} source-class discipline applied even to the thesis's
own favoured readings, and the explicit "not a non-inferiority claim" refusal to over-read a
null all pre-empt attacks a Devil's Advocate would otherwise lead with. The critique below had
to work harder than usual to find live ground.

## Strongest Counter-Argument

The thesis earns its negative result honestly: the power arithmetic, the pre-registered
efficacy trial, and the archaeology are careful. But a scholar defending the released
HarnessX/AEGIS loop, or defending self-evolving harnesses generally, has a coherent counter-case.
First, every headline number here is drawn from one hundred GAIA text-only tasks, one solver
tier, sixteen rounds, and three seeds; the thesis concedes (§7.1, §7.3) the field-level claim is
"an inference," yet the subtitle — "the Missing Efficacy Readout" — states it as a fact about the
field, not about this bed. Second, the one metric presented as moving cleanly in a
mechanism-attached direction — ship rate — reverses sign in one of the three graph seeds (F10:
0.92 against a no-graph comparator of 0.88), a fact recoverable only from the ledger and never
reconciled wherever "0.62 against 0.88" is used as a finding. Third, the sixth gate's eighteen
kills are read as the graph "making the loop checkable"; they are equally consistent with the
graph representation degrading the Evolver's own targeting, since a third of every graph-arm
candidate now cites a node that was never there — a failure mode the free-text arm structurally
cannot exhibit, so its true rate there is unknown, not zero. Fourth, "selection is deaf" is
argued from a breeder's-equation sketch and indirect symptoms, not from a bulk test of retained-
versus-discarded candidates against measured ground truth — the thesis's own "discriminating
experiment" remains unrun. None of this reverses the sign of the result. All of it narrows how
much the result is entitled to say.

## Disposition of the mandated attack lines (a)–(j)

**(a) Bed artefact vs property.** Largely defeated. The body scopes the claim explicitly ("made
for this bed and this system class... an inference and is flagged as one," 07-discussion.tex:32–38;
"Single bed, single model tier... generalization... is untested," 07-discussion.tex:202–204).
Residual: the title and the abstract's proposition sentence carry no equivalent hedge — Issue #8.

**(b) Implementation failure vs refutation.** Not defeated. See Issue #2: the sixth gate's kill
rate is at least as consistent with degraded candidate targeting as with virtuous checking, and
the text does not rule the former out.

**(c) Cherry-picking of two excluded campaigns.** Substantially defeated on the direction
question — the ruling is dated, stated to be post-hoc, and stated to have moved numbers *against*
the graph (01-introduction.tex:418–423; A-deviations.tex:26–33). Not defeated on specificity: see
Issue #6.

**(d) Positive control vs "no readout."** Defeated — the most carefully reconciled point in the
document (03-baseline.tex:359–414; 07-discussion.tex:77–117), using "assay sensitivity" and a
quantified resolution gap. Minor residual on the external validity of its calibration bound —
Issue #11.

**(e) "Checkable" — measured or unfalsifiable.** Substantially defeated as a component-level
claim: F7, F11, F52 and F53 are each independently measured and falsifiable. Live only as a
labelling question — Issue #10.

**(f) Contaminated null.** Substantially defeated for the flip-rate/noise-floor statistics: F15,
F41, F44, F45 and F48 all explicitly restrict to "full-batch windows" and separately report the
25-task audit-window rate as its own, higher figure (F41) rather than mixing it in. **Not**
defeated for the headline plateau/arm-mean gap, which F46 states explicitly includes carried
rows — Issue #3.

**(g) Deaf selection vs non-separating outcomes.** Not defeated, and the thesis does not claim
otherwise. It shows the *instrument* is non-monotone (F49) and argues, formally rather than
empirically, that retention must degrade; it names "attach L3 to retention and re-fly" as the
unrun discriminating experiment. See Issue #4.

**(h) Abstract vs results.** Nine of ten load-bearing abstract sentences check out verbatim
against Ch6/Ch7. One compresses away a hedge the body keeps — Issue #5.

**(i) Multiple hypotheses after the fact.** Defeated. §5.4 is an explicit multiplicity statement
(one confirmatory test, everything else exploratory), enforced throughout by the \cls{} tag
system. Issue #13 is a one-line completeness nitpick only.

**(j) "So what?"** Partially defeated — the roadmap and the Conclusion's "durable artifacts" both
name concrete, reusable next steps. Live: the proportionality between the graph-native
engineering effort and the modest, explicitly conceded credit given to it — Issue #7.

## Issue List

### CRITICAL

| # | Dimension | Issue Description | Location | Fix-class |
|---|-----------|-------------------|----------|-----------|
| 1 | Cherry-Picking / Confirmation Bias | "One process metric moved down" / "Ship rate is $0.62$ per round against $0.88$" is presented as a clean, mechanism-attached, headline finding. The thesis's own ledger row for the identical statistic (F10) gives per-seed graph-arm rates of $0.50/0.92/0.62$ — one of which ($0.92$, $60\%$ of rounds shipping) *exceeds* the no-graph comparator ($0.88$, $52\%$). No seed breakdown, and no reconciliation of the reversal, appears anywhere the "$0.62$ vs $0.88$" contrast is used as evidence (abstract-adjacent intro bullet, results-at-a-glance table, conclusion). The conclusion as stated is not supported by the evidence as presented in the same document. | ch/01-introduction.tex:257–262 (§1.5); ch/06-results.tex:29 (table); ch/C-ledger.tex:166–169 (F10) | [W]/[R] |

This does not cascade into the thesis's central claims (non-separation of outcomes, H1 rejected
on substitute endpoints) — if anything, a non-replicating process metric is *consistent* with the
thesis's own "everything here is noisy" theme. It is scoped as CRITICAL for the specific,
narrowly-stated claim only.

### MAJOR

| # | Dimension | Issue Description | Location | Fix-class |
|---|-----------|-------------------|----------|-----------|
| 2 | Alternative Paths Analysis | The sixth gate's 18 kills (of 55 graph-arm candidates reaching the gates across three seeds — $32.7\%$) are read exclusively as the graph "making the loop checkable." An equally consistent reading: the cone-based evidence representation increases the rate at which the Evolver cites a target that does not exist, i.e. degrades targeting — a failure mode the free-text no-graph arm has no gate to detect, so its true incidence there is unknown, not zero. No hand-audit of no-graph candidates against their own cited trajectories is offered to bound it. | ch/04-ghx.tex:249–263; ch/06-results.tex:183–197; ch/C-ledger.tex:663–679 (F53) | [R] |
| 3 | Logic Chain Validation | Table tab:arms's headline plateau gap ($+2.7$ tasks) is computed with carried rows included ("a carried task is part of that round's bed score," F46), while the no-op cost mechanism (25-task audit batching) means an unstated number of each arm's R3–R15 rounds are partial re-draws. Ship rate differs sharply by arm/seed ($0.88$ vs $0.50/0.92/0.62$), so the two arms plausibly differ in how many audit-batchable no-op rounds they accumulate — yet no row states the fresh-vs-carried round count per arm, so the plateau gap's independence from carrying frequency cannot be checked by the reader. | ch/C-ledger.tex:533–538 (F46); ch/B-operations.tex:64–71; ch/06-results.tex:271–272 | [R] |
| 4 | Core Thesis Challenge | "Selection is deaf" rests on a non-monotone instrument (F49) and indirect symptoms (treadmill F38, lost drug F39), not on a direct bulk test of whether the loop's actual retention decisions correlate with independently measured true effect across the shipped candidates of all six campaigns. The thesis names this test — attach L3 to retention and re-fly — as the unrun "discriminating experiment," and labels the capability-wall rival "observationally equivalent" on the outcome axis. The proposition is argued, not demonstrated, at the level that would settle it. | ch/07-discussion.tex:119–165, 290–303 | [X] |
| 5 | Logic Chain Validation | "Expected cumulative gain over $R$ rounds is consequently non-positive regardless of variation quality" is asserted from three sentences without an explicit ratchet model (an accept/reject rule, a distribution over true vs. noise-driven deltas) or a shown expectation calculation. The "proposition, not a theorem" hedge is fair, but the abstract restates the conclusion without it. | ch/07-discussion.tex:39–68; ch/00-abstract.tex:49–54 | [W]/[R] |
| 6 | Cherry-Picking Detection | The excluded-campaign ruling's direction is disclosed (defeats the strongest form of the attack), but the operational criterion — "flown before the graph layer was correct" — is never cashed out in the body as a named defect list, commit, or test ID; "correct" is asserted where a reader needs it evidenced. | ch/A-deviations.tex:18–33; ch/B-operations.tex:12–16 | [W] |
| 7 | So What Test | GHX (Ch4) is the thesis's largest engineering deliverable, yet its credited contribution is explicitly narrow ("legality and identity... not a wider reach"; "None of this made the loop smarter... checkable"), and the thesis's most decisive evidence (evidence-column defect, archaeology F38, noise-floor arithmetic, positive control) is established without the graph at all. The proportionality between build scale and credited insight is conceded, never argued. | ch/04-ghx.tex (whole chapter); ch/01-introduction.tex:365–370; ch/08-conclusion.tex:34–40 | [D] |

### MINOR

| # | Dimension | Issue Description | Location | Fix-class |
|---|-----------|-------------------|----------|-----------|
| 8 | Overgeneralization Check | Subtitle "...and the Missing Efficacy Readout" and the abstract's proposition sentence read as field-level claims; the body's own "an inference and is flagged as one" hedge appears at neither location. | THESIS.tex:87–90; ch/00-abstract.tex:49–54 | [W] |
| 9 | Alternative Paths Analysis | No disclosure of the six campaigns' calendar order/overlap, so gateway/model-routing drift (acknowledged elsewhere as a real risk) cannot be ruled out as a confound even for the hedged between-arm readings. | ch/B-operations.tex:19–27 | [W]/[R] |
| 10 | Overgeneralization Check | "Checkable" is a bundle of independently measured facts (F7, F11, F52, F53), not itself one operationalized quantity; each component is falsifiable, the summary label is not directly one of them. | ch/00-abstract.tex:56; ch/08-conclusion.tex:34–36 | [W] |
| 11 | Overgeneralization Check | The "$\lvert\delta\rvert\lesssim3$ tasks" calibration bound is drawn from a small, non-random set of hand-run trials on "repeatedly prescribed" drugs, not from a random sample of the $\sim$40+ candidates the six campaigns actually shipped. | ch/07-discussion.tex:56–60, 94–97 | [R] |
| 12 | Alternative Paths Analysis | Leak-route contamination (12/44 swing tasks) is disclosed as a shared, score-level risk, but whether graph-style citation of step-pinned identifiers interacts differently with leak-derived answers than free-text citation does is not examined. | ch/03-baseline.tex:211–219; ch/C-ledger.tex (F31) | [R] |
| 13 | Overgeneralization Check | §5.4's illustrative "exploratory" list does not name F47 (six-of-six slope test, $p\approx0.016$) even though the blanket rule covers it; a reader scanning only the list could miss its inclusion. | ch/05-design.tex:258–277 | [W] |

## Ignored Alternative Explanations/Paths

1. **Candidate-generation regression under graph representation** (→ Issue #2). The sixth gate's
   kill pattern is at least as consistent with "the graph confuses the Evolver" as with "the
   graph makes the loop checkable," and the comparison is asymmetric by construction — the
   no-graph arm has no equivalent gate, so its comparable error rate is unmeasured, not absent.
2. **Selection untested at the point that would decide it** (→ Issue #4). Everything offered for
   "selection is deaf" is equally compatible with "selection carries a small but real signal,
   currently drowned by known noise, that would show up if retained-vs-discarded candidates were
   tested directly against ground truth" — which remains untested.
3. **Calendar/infrastructure drift** (→ Issue #9). With model names conceded as "routing keys
   that move," any between-arm reading not blocked by design could in principle be partly a
   between-epoch reading if the six campaigns were not run in an interleaved or randomized order.
4. **Engineering-effort/insight mismatch** (→ Issue #7). The evidence-column defect and the
   archaeology finding that carry H1's rejection would likely have been reachable with a much
   smaller instrument than the full graph-native runtime; whether a lighter shim would have
   sufficed for the thesis's actual load-bearing claims is not considered.

## Missing Stakeholder Perspectives

- **The original HarnessX/AEGIS authors**, whose released code is characterized throughout as
  diverging from their own paper — their view on whether a single-lineage reproduction is a fair
  test of a system whose headline result depends on ensemble/variant machinery absent from the
  release is not represented.
- **The wider GAIA-benchmark research community**, who would want to know that 12 of 44 swing
  tasks on the text-only split are leak-route — a finding with implications beyond this thesis's
  own bed that the text does not address outward.
- **The AI-safety/alignment community**: the coverage-directive-produces-a-cheating-tool result
  (F37) is treated as a narrow "governance" specimen rather than connected to the wider
  reward-hacking/specification-gaming literature its behaviour instantiates.
- **Practitioners who would have to fund the level-3 readout**: the efficacy-trial protocol costs
  roughly \$1,466–\$1,467 per replicated seed-pair in research use and needs interleaved arms,
  canaries, and quarantined adjudication — its cost as something a practitioner would actually
  deploy is disclosed but not weighed against simply shipping less and monitoring in production.

## Observations (Non-Defects)

- The retraction registry and fifteen-error registry (Appendix A.3) are an unusually candid
  methodological practice; several entries (registry errors 9, 11, 13–15) directly pre-empt
  attacks a Devil's Advocate would otherwise raise from scratch.
- The \cls{A/B/C} source-class discipline, applied even to the thesis's own favoured readings
  (the four-layers-of-mortality account is explicitly \cls{C}), is a structural defence against
  exactly the "confident overclaim" pattern this review's mandate is built to find.
- "No ruling was made after seeing the number it would change in the favourable direction"
  (01-introduction.tex:422–423) is a checkable claim, and it holds for the one case (ruling 1)
  where it is checkable at all — worth crediting explicitly rather than leaving implicit.
