# Verification Review Report — Round 1 → Round 2

**Manuscript**: *Provenance-Grounded Self-Evolution of LLM Agent Harnesses* (Fei Gao, UCL MSc, COMP0091)
**Verifier**: EIC, re-review mode, single-phase (other reviewers not activated)
**Method**: every claim below was checked by (a) reading the current chapter text directly, (b) diffing it against `review/0904/round1/snapshot/` — the pre-round-1 manuscript state saved at 03:12 — with line endings normalized, so every hunk shown is this round's actual edit, not an artifact of unrelated dirty-tree history, and (c) cross-reading the maker's own RESPONSE-*.md claim for that location. Git state was checked directly for P1-04. The mechanical gate (`gate_result.json`, 07:20 in-place run) is treated as authoritative for compile/exclusion/bib/anchor mechanics and not re-run.

---

## Decision

### Minor Revision

Twenty-two of twenty-six Priority-1 items are FULLY_ADDRESSED and independently verified against the live manuscript. The remaining four are narrow: one single sentence missing in one chapter (P1-12's §7.1 half), one paragraph missing one clause it has a working template for one file over (P1-22's ch/B half), one pure git-administrative action only the author can authorize (P1-04), and one genuinely-exhausted, well-documented search that found no dated record to cite (P1-15). None touches a central claim, none requires new data or re-analysis, and none was made worse by this round's edits — several claims (the ship-rate headline, the noise-band's arm scope, the "21 tasks of headroom" gap) are now *more* defensible than in Round 1's manuscript, not just differently worded. The mechanical gate is clean (117 pages, 0 compile errors, 0 overfull boxes, exclusion hard-hits 0, bib 60/60 cited, anchors PASS, `unanchored` WARN improved 69→66). Per the protocol, Accept requires all Priority-1 items FULLY_ADDRESSED, which is not yet true — but the residue is a closing punch-list (under an hour of work), not a re-opened argument, so Major Revision would misdescribe the state of the document. This is Minor Revision in its final-pass sense: the same tier as Round 1, with the item count collapsed from 26 to 4 and the four being administrative-or-cosmetic rather than substantive.

---

## Priority 1 — Required Revisions (26 items)

| # | Original Comment (short) | Author's Claim | Status | Location | Verified? | Quality Assessment |
|---|---|---|---|---|---|---|
| P1-01 | Abstract's "the one published...code released" superlative is false (HarnessForge's code is public) | Replaced with "a published...loop with released code and, to our knowledge, the most heavily governed one"; grepped for other occurrences, found none | FULLY_ADDRESSED | ch/00-abstract.tex:7-9 | ✅ Yes | Exact match to the mandated sentence; no other superlative found on my own re-grep either. |
| P1-02 | GenAI-use declaration missing (UCL policy) | New `ch/00-declarations.tex`, tool/version/publisher/URL/context per AUTHOR-FACTS, solver LLMs excluded | FULLY_ADDRESSED (draft) | ch/00-declarations.tex:5-20 | ✅ Yes | Content matches AUTHOR-FACTS exactly; this is a fact stated in the author's name — see New Issues NEW-4. |
| P1-03 | Code/data access statement missing | New section: fork URL, branch, tag, script/source dirs, run-archive availability | FULLY_ADDRESSED (draft) | ch/00-declarations.tex:22-32 | ✅ Yes | Correct language, but the sentence's tense claims a tag that does not exist yet — contingent on P1-04, see NEW-5. |
| P1-04 | Branch `ghx/m27-variance` not on origin | (git operation, [D], not a maker task) | NOT_ADDRESSED | n/a | ✅ Yes (confirmed absent) | `git ls-remote --heads origin ghx/m27-variance` and `git tag -l thesis-2026-09` both empty, checked directly. Author-only action; correctly left undone by the loop. |
| P1-05 | Abstract silent on F34's null efficacy result; "candidates ship" plural is wrong | Added F34 clause; "one candidate shipped" (singular) | FULLY_ADDRESSED | ch/00-abstract.tex:19,43-44 | ✅ Yes | Both fixes present verbatim; consistent with ch/01:172-174's pre-existing singular usage. |
| P1-06 | Q1-Q3 not a labelled, citable subsection | New `\subsection*{Research questions}` with `rq:1..3` labels + timing sentence each; Ch8 closes by question | FULLY_ADDRESSED | ch/01-introduction.tex:211-230; ch/08-conclusion.tex:76-80 | ✅ Yes | Both halves present; timing sentences use only pre-existing relative sequencing, no invented dates. |
| P1-07 | No chapter-by-chapter roadmap; Ch3's formative role unstated | 8-sentence roadmap paragraph, ch3 called formative/diagnostic, ch6 called main-results | FULLY_ADDRESSED | ch/01-introduction.tex:458-478 | ✅ Yes | All 10 `\ref` targets resolve (confirmed via compile: 0 undefined refs); wording matches spec. |
| P1-08 | No glossary; 6 load-bearing terms undefined | New `ch/00-glossary.tex`, 36 entries, all 23 required concept-groups present | FULLY_ADDRESSED | ch/00-glossary.tex (new) | ✅ Yes | Checked all 23 required terms present; fits front matter within the (renegotiated) page budget. |
| P1-09 | "level-2" used for both GAIA tier and readout rung | Renamed GAIA-tier uses to "GAIA-difficulty-2" / "GAIA difficulty tier 2"; ladder uses left alone | FULLY_ADDRESSED | ch/03-baseline.tex:375; ch/C-ledger.tex:483,496; ch/A-deviations.tex:143 | ✅ Yes | `grep` for bare "level-2" outside ladder context returns 0, confirmed independently. Two spellings remain across files — NEW-3. |
| P1-10 | GAIA never cited | Added `\bibitem{gaia}`, cited at first use | FULLY_ADDRESSED | ch/01-introduction.tex:99; ch/99-bibliography.tex:23-25 | ✅ Yes | Bibitem exists, cited, arXiv:2311.12983 correct. |
| P1-11 | "25 below" contradicts F16's own stated gap of 21 | Changed "25"→"21" | FULLY_ADDRESSED | ch/06-results.tex:426 | ✅ Yes | Now reads "21" throughout; F16's row explicitly states the superseded "25" reading is withdrawn. |
| P1-12 | arXiv:2607.12227/13285 missing from §2.1; no corroborating sentence in §7.1 | Both bibitems added, cited in §2.1 with one sentence each | PARTIALLY_ADDRESSED | ch/02-related-work.tex:101-109 (done); ch/07-discussion.tex:32-38 (missing) | ✅ Yes (gap confirmed) | §2.1 half fully done and well-written. The §7.1 corroborating sentence R2 W1 explicitly asked for is absent — grepped `rethink-harness-eval`/`2607.12227` in ch/07, zero hits. See NEW-1. |
| P1-13 | BrowseComp/price/MRCR figures uncited | Vendor footnotes with URL + "accessed 4 Sept 2026" for 3 of 4 figure clusters; 1.3×/2.4× disclosed as unsourced pilot observation | FULLY_ADDRESSED | ch/05-design.tex:78-106 | ✅ Yes | All three footnotes present and correctly worded; the honest "not a vendor-published figure" disclosure for the remainder is the right call, not a gap. |
| P1-14 | Wilson CI ignores task-level clustering | New task-clustered bootstrap script + F57 row + one body sentence | FULLY_ADDRESSED | ch/05-design.tex:140-142; ch/C-ledger.tex F57 (771-785) | ✅ Yes | New script, deterministic, self-checks against F9e before printing; CI correctly wider than naive Wilson at all four levels. |
| P1-15 | No dated pointer for H1's or F34's pre-registration | Six distinct git-log/docs searches run; none found a dated record; left text unchanged, flagged [D] | NOT_ADDRESSED | ch/01-introduction.tex:205; ch/05-design.tex:288-289 | ✅ Yes (absence confirmed) | Genuinely diligent search, fully documented in RESPONSE-B2b — but the acceptance check (a dated pointer) is not met. Recommend converting to a stated limitation rather than silence — see Residual Issues. |
| P1-16 | `plot_campaign_scores.py`'s ship marker disagrees with `audit_gain_face.py`/F49 for GHX seed-3 R9→R10 | Orchestrator pre-fix: `ship_rounds()` now marks the *landing* round; table/figure regenerated | FULLY_ADDRESSED | fig/scores-table.tex (generated) | ✅ Yes | Directly inspected the regenerated table: seed-3 graph R10 cell is no longer bold, no-graph seed-1 R3 is now bold — both match F49's "nothing shipped" / the positive control exactly. |
| P1-17 | `tab:results` never referenced in prose | One-sentence pointer added | FULLY_ADDRESSED | ch/06-results.tex:67-68 | ✅ Yes | `\ref{tab:results}` now appears; previously zero hits. |
| P1-18 | Table 2.1 has no short caption (LoT shows the full paragraph) | Added `\caption[short]{...}` | FULLY_ADDRESSED | ch/02-related-work.tex:370 | ✅ Yes | Short-form argument present; LoT entry now the short phrase (per compile). |
| P1-19 | ±3.70 band measured on no-graph arms only, applied to graph arm silently | One sentence at Fig 6.1 caption; one at F48's gain-face prose (covers F49 by inheritance) | FULLY_ADDRESSED | ch/06-results.tex:317-320, 583-585 | ✅ Yes | Both sentences present, correctly worded ("by assumption"). Location shifted from the roadmap's stale line numbers because Maker-A2's F15/F44/F45 rewrite moved the block — correctly relocated by content, confirmed by reading. |
| P1-20 | 18 sixth-gate kills read as pure evidence, alternative (graph degrades targeting) not named | 3-sentence "alternative reading" paragraph, in ch4 and (mirrored) ch6 | FULLY_ADDRESSED | ch/04-ghx.tex:272-281; ch/06-results.tex:204-210 | ✅ Yes | Both paragraphs present, deliberately near-identical wording across chapters — intentional reinforcement, not accidental duplication. |
| P1-21 | +2.7 plateau gap has no fresh/carried breakdown | New F58 row + `audit_fresh_carried_plateau.py`; one sentence in Table 6.arms's caption | FULLY_ADDRESSED | ch/C-ledger.tex F58 (787-798); ch/06-results.tex:302-305 | ✅ Yes | Sanity-checked by the maker against raw JSONL before trusting; numbers (0% vs 28.2% carried) are the real asymmetry R4 MAJOR #3 flagged. |
| P1-22 | "Flown before the graph layer was correct" is an unevidenced criterion (2 locations named by R4) | ch/A given a date range (19-26 Aug 2026) + "each pinned by a regression test," from a bounded git-log search | PARTIALLY_ADDRESSED | ch/A-deviations.tex:26-31 (done); ch/B-operations.tex:12-16 (not done) | ✅ Yes (gap confirmed) | ch/A's fix is the authorized fallback sentence, correctly gated on the git log actually supporting the date range (it does, ~55 commits checked). ch/B still reads only "repaired and pinned by tests," with no date — confirmed via diff, this paragraph was never touched this round. See NEW-2. |
| P1-23 | "Selection is deaf" stated as settled fact in places | One sentence softened to "read as"; Future Work already named the experiment (no edit needed there) | FULLY_ADDRESSED (achievable portion) | ch/07-discussion.tex:161-163, 308-314; ch/08-conclusion.tex:7 | ✅ Yes | All hedges now read as propositions; grepped "deaf" across ch/07 (0 hits — word lives only in ch/02/ch/08, both already compliant). Full resolution needs a new experiment and is correctly deferred [X] under the freeze. |
| P1-24 | GHX's build scale vs. its narrow credited contribution never conceded | Two-sentence concession, "enabling infrastructure...not an efficient route" | FULLY_ADDRESSED | ch/08-conclusion.tex:42-49 | ✅ Yes | Matches the adopted default exactly; reads as a genuine concession, not a hedge. |
| P1-25 | No disclosure stance toward HarnessX/AEGIS maintainers | One paragraph, placed after the F37 discussion in §7.2 | FULLY_ADDRESSED | ch/07-discussion.tex:192-198 | ✅ Yes | Names all three ch3 defects plus F37; states "will be reported...around submission; not delayed" — matches the adopted default. |
| P1-26 *(CRITICAL, ledger-gated)* | "$0.62$ vs $0.88$" hides a per-seed reversal (one seed ships *above* no-graph); F10 itself was stale | Ledger F10 refreshed first (0.62→0.60, three seed values kept discrete); every "0.62 vs 0.88" sentence rewritten to the three seed values, reversal named explicitly | FULLY_ADDRESSED | ch/00-abstract (unaffected — never cited the pair); ch/01-introduction.tex:282-290; ch/06-results.tex:29,184-187,193-194; ch/C-ledger.tex F10 (168-173) | ✅ Yes | Grepped ch/01/05/06/B for "0.62"/"0.88": every remaining hit is now scoped to all three seed values with the reversal ("one seed above") stated. This is the panel's sole CRITICAL and it is closed cleanly — the strongest single result of this round. |

**Tally: FULLY_ADDRESSED 22, PARTIALLY_ADDRESSED 2 (P1-12, P1-22), NOT_ADDRESSED 2 (P1-04, P1-15), MADE_WORSE 0.**

---

## Priority 2 — Suggested Revisions (15 items)

| # | Original Comment (short) | Status | Notes |
|---|---|---|---|
| P2-01 | Trim argumentative F9a-F9e ledger prose | NOT_ADDRESSED | Explicitly authorized to skip — the page-budget note found no ceiling risk; correctly not attempted so as not to disturb the P1 content additions to those same rows. |
| P2-02 | Rollback-rule citation `:901-911`→`:1425` (2 sites) | FULLY_ADDRESSED | Both ch/A sites fixed; ch/03's own citation was already correct and independently confirmed the target line first. |
| P2-03 | Name `HARNESSX_GHX_PLANNER_SENSES`, flag-off status | FULLY_ADDRESSED | Sentence matches the module's actual code (`guidance.py`) as read by the maker. |
| P2-04 | Scope "supernet" to MaAS only | FULLY_ADDRESSED | AgentSquare/EvoFlow now described generically; MaAS alone gets the "supernet" framing. |
| P2-05 | Disambiguate "AgentFlow" (two unrelated systems share the name) | FULLY_ADDRESSED | Dash-clause added at first mention. |
| P2-06 | "Why not just patch the 20-char heuristic" never answered | FULLY_ADDRESSED | 4-sentence answer added at end of §1.5, quoting ch3's own free-text-identity and open-loop findings accurately. |
| P2-07 | Abstract's proposition reads field-level, unscoped | FULLY_ADDRESSED | "on this bed and system class" added to the abstract's proposition sentence. |
| P2-08 | "Is consequently non-positive" overstated | FULLY_ADDRESSED | Softened to "can be non-positive under this bed's parameter regime" in both ch/07 and the abstract. |
| P2-09 | Missing citations for h², regression dilution, ICH E10; VIM/resolution collision unglossed | FULLY_ADDRESSED | All four sub-parts present: `falconer-mackay`, `hutcheon-dilution` cited in §7.1; `ich-e10` at §5.3's opening; resolution-vs-VIM clause at §5.4's opening. |
| P2-10 | Fig 1.1 licence unstated; Spearman-Brown promise unpriced; no carbon/energy figure | PARTIALLY_ADDRESSED | Licence (MIT) and Spearman-Brown (F60, priced at both promised locations) done. No carbon/token-cost estimate sentence anywhere — see NEW-7. |
| P2-11 | \|δ\|≲3 bound's small, non-random sample undisclosed | FULLY_ADDRESSED | Caveat sentence anchored to F34/F36, correctly describing them as "small, non-random." |
| P2-12 | Six campaigns' calendar order/overlap undisclosed | FULLY_ADDRESSED | New F59 row (class A, timestamp-derived) plus a body sentence in Appendix B.1. |
| P2-13 | F39's `config.yaml` line wrong (131, should be 136/143); F17/F18 uncited without explanation | FULLY_ADDRESSED | Both fixed; F27/F28 correctly excluded from the same disclaimer after the maker checked they don't fit the "cross-check row" description. |
| P2-14 | `\setcounter{page}{1}` scheme causes duplicate hyperref destinations | FULLY_ADDRESSED | Replaced with `\pagenumbering{roman}`/`{arabic}` — cleaner than the two literal alternatives the item offered; 0 duplicate-destination warnings confirmed in the build log. |
| P2-15 | "digester"/"the planner" lowercase when used as role names | FULLY_ADDRESSED | Both sites capitalized ("Digester", "Planner"). |

**Tally: FULLY 13, PARTIALLY 1, NOT (authorized skip) 1 — 93% response rate, comfortably over the 80% bar.**

---

## Priority 3 — Nice to Fix (8 items)

| # | Original Comment (short) | Status |
|---|---|---|
| P3-01 | Small ladder diagram near §4.9 | NOT_ADDRESSED (Fig 4.1 already partially covers this; correctly lowest priority) |
| P3-02 | Does graph-style citation interact differently with leak-derived answers than free-text? | NOT_ADDRESSED (exploratory, [R]-class, no maker touched it) |
| P3-03 | F47 missing from §5.4's exploratory-test list | FULLY_ADDRESSED |
| P3-04 | "Checkable" should read as a bundle of facts, not one quantity | FULLY_ADDRESSED |
| P3-05 | Underfull hbox; enumitem negative-labelwidth warnings | FULLY_ADDRESSED (both; confirmed 0 Underfull/Overfull and 0 "Negative labelwidth" in the build log) |
| P3-06 | "LLM" not spelled out at first use | FULLY_ADDRESSED |
| P3-07 | Four small arithmetic/ordering tensions | FULLY_ADDRESSED (3 of 4 fixed per the author-approved defaults; DAG-before-Ch4 correctly left as-is, per its own "no change" default) |
| P3-08 | "H1 is rejected" vs "not supported" | FULLY_ADDRESSED (at the 2-3 headline locations only, as scoped; a third, previously-uncaught instance at ch/01:206 was also caught and fixed for internal consistency) |

---

## New Issues Discovered During Revision

| # | Tag | Location | Description and concrete fix |
|---|---|---|---|
| NEW-1 | [W] | ch/07-discussion.tex:37 | P1-12's required §7.1 corroborating sentence for arXiv:2607.12227 was never added (verified: 0 occurrences of `rethink-harness-eval`/`2607.12227` in ch/07). **Fix**: after "...160 papers screened, 18 close-read." add one sentence, e.g. "An independently-derived, contemporaneous critique reaches a convergent conclusion under a different evaluation design~\cite{rethink-harness-eval}." |
| NEW-2 | [W] | ch/B-operations.tex:12-16 | P1-22's second required location (named explicitly by R4 MAJOR #6 and the roadmap) still reads only "repaired and pinned by tests before the first admissible graph campaign" — no date range, unlike ch/A's now-fixed twin passage. **Fix**: append the same parenthetical ch/A-deviations.tex:26-31 now has: "(the graph-layer fixes committed between the second shakedown and the first whitelist graph campaign, 19–26 August 2026, each pinned by a regression test)". |
| NEW-3 | [W] | ch/03-baseline.tex:375 vs ch/C-ledger.tex:483,496 | Two makers independently fixed the "level-2" GAIA-tier ambiguity with different replacement strings ("GAIA-difficulty-2" vs "GAIA difficulty tier 2") — same referent, self-flagged by Maker-B2b as unresolved. **Fix**: pick one spelling and normalize both sites; three occurrences total. |
| NEW-4 | [D] | ch/00-declarations.tex:8-9 | The GenAI-use declaration names a specific model-version list (Opus 4.x, Sonnet 4.x/5, Fable 5.1) drawn from AUTHOR-FACTS, which itself notes this must be "confirmed by the author in the morning." This is a factual claim in the author's name about the author's own working history — the loop cannot verify it independently. **Fix**: author reads the sentence and confirms or corrects the model list before submission. |
| NEW-5 | [D] | ch/00-declarations.tex:26-28 | The repository-access statement says the branch is "tagged `thesis-2026-09`...at the point of submission" — currently false (P1-04 open, no tag exists). Not a new defect, but the sentence will misrepresent the repository state to an examiner unless P1-04 is completed. **Fix**: push the branch and create the tag before submitting; if timing is uncertain, soften to future tense. |
| NEW-6 | [D] | ch/00-declarations.tex:12 | The declaration discloses "simulating reviewer feedback" as one of the AI's roles — an accurate description of how tonight's review (this document included) was produced. Not a defect, but a framing decision only the author can own: worth a deliberate read before submission to confirm the author is comfortable with an examiner seeing this stated plainly. |
| NEW-7 | [R] | ch/07-discussion.tex, §7.4 (Cost honesty) | P2-10's authorized default ("add one rough token-count-based estimate sentence; do not attempt a precise carbon figure") was never executed — no compute/energy sentence appears anywhere in the cost-honesty section. **Fix**: add the one sentence, or explicitly drop the item with a one-line rationale rather than leaving a silent gap against an approved action item. |

No case was found of a claim *weakened* by an edit, and no inconsistency was found between a newly-added sentence and its ledger anchor — every new or changed number (F57-F60, the F10/F13/F31/F44/F45/F54/F55 refreshes, the "21" fix) was independently re-derivable from the value now printed in its own ledger row, and every arithmetic relationship checked (the F41 ratio range, F60's Spearman-Brown schedule, F58's percentages) recomputes correctly by hand.

---

## Residual Issues — Recommend Marking as Acknowledged Limitations

1. **P1-15, no dated pre-registration pointer.** Six independent, well-targeted searches (git pickaxe on "pre-regist"/"stopping rule"/"7 clean tasks", `--diff-filter=A` on the recompute script, a docs grep) found nothing predating the thesis's own retrospective narrative. This may genuinely not exist as an artifact (a private note, a chat log, or the author's own memory may be the only record). Recommend one explicit sentence at ch/05:288-289 stating this rather than leaving the gap silent — turns a "missing citation" into a stated, honest limitation, which is exactly the self-audit posture the panel praised elsewhere in this document.
2. **P3-01/P3-02**, the ladder diagram and the graph-vs-free-text leak interaction, are legitimately deferrable: both are additive nice-to-haves that Fig 4.1 and the existing leak-route disclosure already partially cover.
3. **NEW-3's terminology variance** is cosmetic and low-stakes but should not be left past this round if avoidable — a viva examiner comparing ch3 to the ledger is exactly the reader who would notice it.
4. **B1-03's REJECTED sub-decision** (declining to touch the abstract's "can be non-positive" verb because its literal trigger — "if the abstract says 'is'" — was not met) is a reasonable, well-documented textual judgment call, not an error; flagged here only so the author skims it once and agrees.

---

## Morning Checklist for the Author

1. Push `ghx/m27-variance` to `origin` and create/push tag `thesis-2026-09` — the Code & Data Access declaration is false until this is done (P1-04).
2. Confirm the GenAI declaration's model list (Opus 4.x, Sonnet 4.x/5, Fable 5.1) against your own memory; edit if incomplete (NEW-4).
3. Decide if you're comfortable with the declaration's "simulating reviewer feedback" sentence as written (NEW-6).
4. Add one sentence to ch/07-discussion.tex:~37 citing `rethink-harness-eval` — the §2.1 half is done, this is the last piece of P1-12.
5. Copy ch/A's new date-range clause into ch/B-operations.tex:12-16 — the last piece of P1-22.
6. Decide: state "no dated pre-registration record exists" as an explicit limitation (P1-15), or supply a source the loop couldn't find.
7. Normalize "GAIA-difficulty-2" vs "GAIA difficulty tier 2" to one spelling (three sites, NEW-3).
8. Add the token/carbon estimate sentence in §7.4, or drop P2-10's third sub-item explicitly rather than silently.
9. Skim the new declarations, glossary, and RQ subsection once — drafted by the loop from your own prior text, but they carry your name.
10. Recompile once after these edits; page count should stay comfortably under 120 (currently 117).
