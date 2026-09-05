# Peer Review Report

## Manuscript Information
- **Title**: Provenance-Grounded Self-Evolution of LLM Agent Harnesses — A Graph-Native Runtime, a Pre-Registered Falsification, and the Missing Efficacy Readout
- **Manuscript ID**: N/A (UCL COMP0091 MSc dissertation; submission 9 Sept 2026)
- **Review Date**: 2026-09-04
- **Review Round**: Round 1 (pre-submission examination read)

---

## Reviewer Information

### Reviewer Role
EIC / Chair, MSc Examination Board

### Reviewer Identity
Professor of machine-learning systems, UK university; chair of the MSc ML examination board (~40 MSc dissertations examined); PC member, LLM-agents workshop.

### Review Focus
Whether the research questions are explicit and answered, whether the stated contribution (§1.8) is actually delivered in Chapters 6–7, whether the negative result reads as a contribution rather than an apology, structural/scholarly-tone conformance to UCL expectations (including length and chapter placement), abstract fidelity, viva readiness, and rhetorical register. Statistics, code correctness and literature completeness are explicitly left to other reviewers.

---

## Overall Assessment

### Recommendation
**Minor Revision** — no restructuring of the core argument or methods is required; every issue below is fixable by rewriting, by recomputing from data already in the fact ledger, or by adding administrative content, all within the five days before submission.

### Confidence Score
**5** — squarely within my remit as examination-board chair (structure, framing, viva-readiness, register); I have deferred entirely on statistics, code and literature coverage.

### Summary Assessment
This is a self-evolving-harness reproduction and falsification study: the authors run the released HarnessX/AEGIS system at scale, find its evidence signal is provably blind, build a graph-native evidence layer (GHX) in response, pre-register a test of whether that evidence helps, and report that it does not — while arguing the reason is a missing "efficacy readout" rather than a failure of the graph. Argumentatively this is unusually disciplined for an MSc dissertation: contributions stated in §1.8 are individually checked off against evidence in the Conclusion, a 15-item self-audit error registry and retraction log turn "we were wrong" into methodological evidence rather than apology, and the central proposition borrows a real formal apparatus (the breeder's equation) to give the null results interpretive teeth. The two clearest weaknesses are presentational, not scientific: the three research questions of §1.4 are compressed into one paragraph with no return to them in the Conclusion, and the Abstract omits the thesis's own single pre-registered confirmatory result while using an imprecise plural elsewhere. The mandatory GenAI-use declaration and code-repository access statement are absent. None of this touches the underlying argument, which is coherent, well-evidenced, and earns its negative-result framing.

---

## Strengths

### S1: The contribution-to-delivery loop is closed, explicitly
§1.8 "Contributions" (ch/01-introduction.tex:353–384) states C1–C6 as one sentence each; the Conclusion (ch/08-conclusion.tex:46–54) restates every one of them against the chapter and evidence that delivered it ("C4 is the pre-registered test of H1 and its rejection on declared substitute endpoints..."). Very few MSc dissertations I have examined close this loop this explicitly — it directly answers review focus #2.

### S2: Self-audit is used as evidence of rigor, not confessed as weakness
Appendix A.3's 15-item error registry (ch/A-deviations.tex:174–292) is tallied by direction (8 favourable to the project, 3 against, 2 neutral; lines 182–187) and §5.5 draws the methodological moral directly: "A study whose evaluator is not itself audited has no grounds for the confidence intervals it reports" (ch/05-design.tex:304–305). Combined with the retraction registry (ch/C-ledger.tex:726–839), this is exactly what separates a negative result that reads as a contribution from one that reads as an apology.

### S3: The positive control gives the null results interpretive teeth
§7.1 (ch/07-discussion.tex:39–118) borrows the breeder's equation and ICH E10 "assay sensitivity" to explain *why* a null on this instrument is uninterpretable without a known-working intervention to calibrate against, then supplies one (the budget-starvation repair) and shows its effect had to be ~3× the loop's typical edit size to register. This pre-empts the most obvious objection to any negative-result thesis ("how do you know your instrument could detect anything?") before an examiner has to ask it.

### S4: Strong internal navigability for a dense document
The boxed one-sentence "Chapter claim" opening every chapter (e.g., ch/04-ghx.tex:6–9) and the "Results at a glance" table (ch/06-results.tex:15–57, Table 6.1) let a time-pressed reader orient in seconds. For a 103-page, number-heavy document this is a real aid, not a decoration.

### S5: Credit assignment for GHX is scrupulously honest
C3 is stated as "legality and identity of candidates," explicitly "not a wider reach" (ch/01-introduction.tex:368–370), harness-level cost engineering is deliberately *not* credited to the graph (§7.4, ch/07-discussion.tex:240–249), and §4.8's in-run rule is read as "an aliveness proof... and not a success story" (ch/04-ghx.tex:340–342). This resistance to over-claiming, repeated at every opportunity, is what makes the "checkable, not smarter" thesis credible.

---

## Weaknesses

### W1: Research questions are compressed into one paragraph and never closed by name
**Problem**: Q1 (diagnosis), Q2 (non-interference) and Q3 (does graph evidence help) are posed and answered in the same four sentences (ch/01-introduction.tex:209–216, §1.4), with no dedicated "Research Questions" heading, no statement of when they were fixed (H1's registration date is given explicitly two pages earlier at lines 179–186; Q1–Q3's is not), and no return to them by label anywhere in Chapter 8. Q2 is also categorically different in kind from Q1/Q3 — it is an internal-validity check on GHX's recorder, not a substantive question about the loop — but is presented as a peer of both.
**Why it matters**: This is directly review focus #1. An external examiner looking for "are the RQs explicit and answered" has to reconstruct them from a single dense paragraph and then take on faith that C1–C6 answer them, since the Conclusion never says so explicitly.
**Suggestion**: Promote Q1–Q3 to a short labelled subsection (after §1.1 or beside the H1 box), give each one sentence of elaboration and registration status, and add one closing sentence per question in Chapter 8.
**Severity**: MAJOR · **Tag**: [W]

### W2: Two abstract-fidelity gaps
**Problem (a)**: The Abstract (ch/00-abstract.tex:35–47) grounds H1's rejection in the archaeology, the positive control, and the two gain-face sweeps — but never mentions the pre-registered efficacy trial (F34, n=70 prospective pairs), even though §1.6 names it as one of exactly three substitute endpoints carrying the rejection (ch/01-introduction.tex:274–283) and §6.6 calls it "the one confirmatory test in the thesis" (ch/06-results.tex:445–466). **Problem (b)**: line 19 of the Abstract reads "...reaches 86% of dossiers, and candidates ship on it" (plural), where every other occurrence of this fact (ch/01-introduction.tex:172–173; ch/03-baseline.tex:323–325; F5/F6) is careful to say exactly *one* candidate shipped on the false signal, flagged as "illustration only, not causal."
**Why it matters**: Review focus #5. This thesis is unusually easy to audit against its own ledger, which raises the cost of any abstract imprecision — an examiner who spot-checks (as I did) will find the strongest confirmatory result missing and the reach-into-decisions claim overstated by one word.
**Suggestion**: Add one clause naming F34's null result; change "candidates ship on it" to "one candidate shipped on it."
**Severity**: MAJOR · **Tag**: [W]

### W3: The Fact Ledger re-argues rather than sources, at real page cost
**Problem**: Appendix C (ch/C-ledger.tex) runs ~19 printed pages for 56 rows plus a 23-item retraction registry. Rows such as F9a–F9e (lines 95–153) re-run the full argumentative case against an arm comparison in essentially the same prose register as §6.3 (ch/06-results.tex:158–169), rather than pointing to it.
**Why it matters**: Review focus #4. The document is within the 120-page ceiling (103 printed pages), but appendices A–C run ~28 pages against a 68-page body, and the ledger — whose own stated job is to let "the script that recomputes it" back a number (ch/C-ledger.tex:6) — is the single largest, lowest-risk trimming target.
**Suggestion**: Tighten rows to fact + sample/scope + script pointer + class; move argumentative sentences to a one-line body cross-reference. Likely recovers 3–5 pages with no loss of auditability.
**Severity**: MAJOR · **Tag**: [W]

### W4: No chapter-by-chapter roadmap in Chapter 1
**Problem**: Nowhere in §1.1–§1.9 does the thesis tell the reader what each subsequent chapter does. This matters more than usual here because the structure is unconventional — a full "results" chapter (3, Baseline Diagnosis) precedes the system chapter (4) and the main results chapter (6) — and nothing signals that Chapter 3 is a formative diagnostic study rather than the thesis's main empirical claim.
**Why it matters**: Review focus #4 (structure against UCL expectations). This is the single most standard, most expected paragraph in a UK dissertation introduction, and its absence is conspicuous precisely because everything else in Chapter 1 is so carefully engineered.
**Suggestion**: Add 6–8 sentences at the end of §1.9 (after ch/01-introduction.tex:428) mapping chapters to their role, one clause of which should say explicitly that Chapter 3's findings motivate H1 and are not superseded by, but distinct from, Chapter 6's main results.
**Severity**: MAJOR · **Tag**: [W]

### W5: Mandatory GenAI-use declaration and code-repository access statement are absent
**Problem**: Neither appears anywhere in THESIS.tex or any ch/ file.
**Why it matters**: Both are compulsory components of the COMP0091 submission, independent of scientific merit; their absence could block acceptance of an otherwise strong submission on a technicality.
**Suggestion**: Add a GenAI-use declaration (what tools were used, for what) and a code-repository-access statement (URL, commit/branch), most naturally as a short unnumbered section after the Abstract or a subsection of the front matter.
**Severity**: CRITICAL · **Tag**: [D] (only the author knows which tools were used and which repository/commit to cite)

### W6: The readout ladder is described four times but never drawn; the simplest alternative fix is never named and rebutted
**Problem**: The L0–L3 ladder — "the system's organizing frame... for the field" (ch/04-ghx.tex:345–350) — is independently re-described in prose at §1.7, §4.9, §7.1 and Chapter 8, with only 3 figures in the entire 103-page document. Separately, the text never explicitly poses and rebuts the obvious simpler alternative: "why build a graph-native runtime rather than just patch the twenty-character verbatim-match heuristic Chapter 3 identifies as the proximate defect?" The ingredients for an answer exist (the free-text identity problem, ch/03-baseline.tex:124–131; the four broken feedback channels, ch/03-baseline.tex:141–193) but are never assembled into one paragraph that names and answers this.
**Why it matters**: A cheap, high-value presentation gap (review focus #4) and a highly likely, currently unrebutted viva question (see Q2 below).
**Suggestion**: One small ladder diagram near §4.9's first full description; 3–4 sentences in §1.5 or §4.1 naming the "just patch it" alternative and which broken channels a patch would leave untouched.
**Severity**: MINOR · **Tag**: [W]

---

## Detailed Comments by Chapter

**Ch.1 Introduction**: Strong motivation; RQ compression is the main issue (W1). "What we met when we tried to reproduce it" (ch/01-introduction.tex:70–90) is the sharpest-toned passage in the document — four rapid, well-evidenced indictments of the released code in one paragraph. Factually solid (backed by Appendix A) but worth rehearsing a calm, ungrudging restatement for the viva.

**Ch.2 Related Work**: The strongest chapter for scholarly register — the positioning table (Table 2.1) and the explicit "taken/changed" donor analyses for MermaidFlow and AgentFlow (§2.4) are a model of precise credit assignment. The HarnessBank line — its significance gate is "a rigorous test of the wrong quantity" (§2.6) — is the most combative single sentence in the thesis toward a specific named system; well-argued, but the author should have a measured, non-defensive version ready to deliver aloud.

**Ch.3 Baseline Diagnosis**: The tiered construction→blindness→rate proof (§3.5) is an excellent model of arguing a defect without over-leaning on data. Its relationship to Chapter 6 as a *formative* rather than *main* results chapter is never explicitly signposted (W4).

**Ch.4 GraphHarnessX**: "Limitations by construction" (§4.10) disclosing that the replacement evidence column is near-tautological (549/549) is placed in the system chapter itself rather than deferred to Threats — exactly where an examiner wants to see it. No structural issues found.

**Ch.5 Experimental Design**: "Power arithmetic first" (§5.2) — establishing what *could* be measured before what *was* — is unusually mature for this level. The McNemar illustration ("Same data, two verdicts," end of §5.2) is persuasive but carries more rhetorical weight than its later "exploratory" label (§5.4) fully supports; one softening clause where it is first introduced would remove the tension.

**Ch.6 Results**: Best-organized chapter; Table 6.1 anchors it well. "Why there is no component ablation" (§6.3, lines 199–228) is a model of pre-empting an obvious objection.

**Ch.7 Discussion**: §7.1 is the intellectual high point of the thesis (S3). §7.4 "Cost honesty" is correctly placed here as meta-commentary on credit assignment rather than as a results claim.

**Ch.8 Conclusion**: About two printed pages for a 68-page body carrying several distinct threads (H1's rejection logic, the proposition, the roadmap) — content is precise but the chapter is thin relative to what it needs to close, particularly Q1–Q3 (W1).

---

## Minor Issues

### Formatting / Layout
- Front-matter pagination artifact: `\setcounter{page}{1}` in THESIS.tex sits after `\listoftables`, but because of LaTeX's output-routine timing the reset lands one page early — the List of Tables page is stamped "1" and Chapter 1 "Introduction" begins on printed page 2, not page 1 (visible in the compiled PDF). Move the `\setcounter{page}{1}` to immediately after `\listoffigures`, before `\listoftables`, or force an explicit `\clearpage` at the reset point.
- No blank `\FIELD{}` placeholders remain in the compiled document — a good sign the submission fields were genuinely filled in, not merely suppressed.

---

## The Five Hardest Viva Questions

1. **"Your registered endpoint (localization) turned out to be unmeasurable. How do we know the substitute endpoints you now rely on won't fail the same way?"** *Partially answered*: F9c's four compounding defects (ch/C-ledger.tex:121–136) and "the substitution was forced by the measurement rather than chosen after seeing a direction" (ch/01-introduction.tex:285–287) explain *why* localization failed, but the text never addresses whether a pilot should have caught the arm-comparability problem before six full campaigns were flown.

2. **"Why build an entire graph-native runtime rather than just patch the twenty-character verbatim-match threshold?"** *Not directly answered* — see W6. The ingredients exist but are never assembled into a rebuttal.

3. **"GHX ships fewer candidates, crashes more (164 vs 5 tracebacks, F56), and its efficacy is an admitted blank on the one axis (meta-tier cost) where it should cost more. What is the actual case for adopting it?"** *Answered, and conceded rather than dodged*: §7.4 (ch/07-discussion.tex:236–288) and the Conclusion's "durable artifacts" (ch/08-conclusion.tex:68–83) are explicit that the contribution is checkability and protocol, not performance — a coherent position the candidate should be ready to state crisply in one breath.

4. **"With no component ablation, how do you know which GHX layer produced even the citation-integrity gain (F52)?"** *Well answered*: "Why there is no component ablation" (ch/06-results.tex:199–228) and F52's own "attribution unresolved" clause anticipate this precisely.

5. **"Isn't this really just 'GAIA-text-only plus this model pair is too noisy for this harness,' rather than a general fact about self-evolving loops?"** *Well answered*: §7.1's explicit scope statement (ch/07-discussion.tex:32–38) and §7.3's "single bed, single model tier" threat (ch/07-discussion.tex:202–204) both flag this as an unproven inference rather than a claim.

---

## Questions for Authors

1. Were Q1–Q3 (§1.4) fixed before the graph campaign flew, in the same sense H1 was pre-registered — or are they an organizing device chosen for the writeup? The text gives H1's registration date but is silent on Q1–Q3's.
2. Was the Abstract's omission of the pre-registered efficacy trial (F34) deliberate (space) or an oversight? Given the thesis itself calls it the "one confirmatory test," should it be added?
3. Which Fact Ledger rows does the author consider load-bearing enough that a reader could not accept the thesis's claims without reading them directly, versus rows that exist purely as an audit trail and could be compressed to a one-line pointer? This would help prioritise trims against the page ceiling.
4. §7.1 names "attach level-3 readout to retention and re-fly" as the discriminating experiment between the readout proposition and the capability-wall rival, and experiments are frozen. Is there any already-recorded data that could be read, post hoc and clearly labelled exploratory, as a first pass at that discriminator, rather than leaving it entirely to future work?

---

*Reviewed independently; no other reviewer's output was consulted in preparing this report.*
