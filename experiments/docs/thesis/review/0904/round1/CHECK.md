# CHECK — round 1 (checker)

**VERDICT: FAIL**

Gate is green and the unauthorised-change sweep and number-consistency sweep are both clean
(zero unauthorised hunks across all 13 chapter files + THESIS.tex + fig/, zero stale numbers
found live). The FAIL is carried entirely by five small, concrete, executable defects below —
of ~79 graded items across the six responses, 77 are FULLY_ADDRESSED or REJECTED_OK; two
(B2a-03, B1-14) are PARTIALLY_ADDRESSED, and three further defects come from this checker's own
specific-point checks (5a/5c/5d in the task brief), not from any single maker item.

## Failure list (executable)

1. **B2a-03 / P1-22** — `ch/A-deviations.tex:26-31`. The acceptance check requires "a concrete
   pointer replaces the bare word 'correct'"; instead the sentence still reads "...flown before
   the graph layer was **correct** --- closed by the graph-layer fixes committed between the
   second shakedown and the first whitelist graph campaign (19--26 August 2026), each pinned by
   a regression test --- are excluded...", i.e. the pointer is bolted on, "correct" is not
   replaced. Fix: reword so "correct" does not stand as the unpointed judgment word, e.g. "Two
   graph campaigns flown before the graph-layer fixes (committed between the second shakedown
   and the first whitelist graph campaign, 19--26 August 2026, each pinned by a regression test)
   landed are excluded from every claim...".

2. **B1-14 / P2-14** — `THESIS.tex:109-123` (live, in-place). Response claims "zero 'duplicate
   destination' warnings" against "the six the item names"; the current in-place `THESIS.log`
   still shows **2** (`grep -ci -i destination THESIS.log` shows the two survivors:
   `destination with the same identifier (name{page.i})` and `(name{page.1})`, each "has been
   already used, duplicate ignored") — real progress (6→2) but not the "zero" the task's own
   acceptance line requires ("check ... that the six ... warnings are gone"). Root cause: the
   title page ships (via `\maketitle`) before `\pagenumbering{roman}` takes effect, so its
   implicit page-1 destination collides with the first roman page and, again, arabic pagination's
   first page collides with it a second time. Fix: move `\pagenumbering{roman}` to immediately
   after `\begin{document}`/`\onehalfspacing`, **before** `\maketitle` (THESIS.tex:106-109), so
   the title page itself ships under the roman sequence; re-verify with
   `grep -ci duplicate THESIS.log` = 0. (Chapter 1 still correctly opens on printed page 1 per
   `THESIS.toc` — that half of the item is fine.)

3. **Checker point 5(c)** — `ch/00-glossary.tex:83-85`. The glossary's `level 2` entry
   distinguishes only two of the three senses this project actually uses: "GAIA's own difficulty
   tier~2 (a benchmark property), and rung~2 of the readout ladder". It omits the third sense
   STATE.md's own "待 checker" note names: `harnessx/ghx/cheatsheet.py:88`'s "Every candidate
   needs Level-1 AND Level-2 evidence in `capability_evidence`" (a candidate's pre-ship
   evidence-quality bar, confirmed by reading the source — genuinely distinct from both the GAIA
   tier and the post-hoc readout ladder). `ch/A-deviations.tex:143`'s heading was renamed
   "Manifest schema and **capability evidence**" this round (B2a-01) and its body text does
   describe exactly this `capability_evidence` mechanism, so the correspondence STATE.md asked
   to be cross-referenced is real but undrawn. Fix: add a third clause to the glossary's `level 2`
   entry (or a standalone entry) naming the cheatsheet's Level-1/Level-2 evidence sense, and add
   a parenthetical at `ch/A-deviations.tex:143`'s paragraph, e.g. "(the cheatsheet's Level-1/
   Level-2 evidence)", per STATE.md's instruction. Mitigating: the literal phrase "Level-1"/
   "Level-2" never appears in the compiled thesis prose itself, so no reader hits the collision
   inside the document — this is an open orchestrator item, not a maker execution fault, and not
   the fault of any single response (`TASKS-B1.md` item 7 only ever asked for two senses).

4. **Checker point 5(d)** — three different spellings of the same renamed term are live
   simultaneously: `ch/03-baseline.tex:375` "**GAIA-difficulty-2**" (Maker-B2a's choice, matching
   P1-09's own worked example in EDITORIAL-DECISION.md); `ch/C-ledger.tex:483,496` (F39's row)
   "**GAIA difficulty tier 2**" (Maker-B2b's choice, matching TASKS-B2b.md's literal target
   string) — B2b already self-flagged this two-way split as `[D]` in RESPONSE-B2b.md; but
   `ch/00-glossary.tex:84` (Maker-B1, new this round) reads "GAIA's **own difficulty tier~2**", a
   **third**, undisclosed form neither maker flagged, because B1 never saw B2a's or B2b's
   responses. Fix: pick one form (recommend "GAIA difficulty tier 2", the ledger's and P1-09's
   own row wording) and make `ch/03-baseline.tex:375` and `ch/00-glossary.tex:84` match it
   exactly; re-grep `ch/*.tex` for `GAIA.{0,3}difficulty` to confirm one form only.

5. **Checker point 5(a)** — `ch/00-abstract.tex:17-19`. The sentence "...the column is blind by
   construction, applies its negative verdict to $75.0\%$ of answer-carrying calls, reaches
   $86.0\%$ of dossiers, and one candidate shipped on it" coordinates four clauses under one
   subject ("the column") for the first three, then switches subject to "one candidate" for the
   fourth without a new independent clause marker — a parallelism break, not merely a style
   wrinkle — and "it" in "shipped on it" reads, by proximity, as referring back to "the column"
   rather than to the loop/system, which is not the intended referent (compare ch/01:172's
   original, unambiguous "...and one candidate shipped on it" outside a four-way verb list). Fix:
   split into two sentences, e.g. "...reaches $86.0\%$ of dossiers. One candidate shipped on the
   no-graph arm regardless." This is the only grammar/coherence problem found in a full read of
   the abstract; nothing in it contradicts ch6/ch8 (flip rates 21.0/20.1/19.2, 86.0%, and the H1
   wording all match Table 6.1 and ch/08's C4 exactly).

Everything else checked — gate, unauthorised-change sweep, number consistency, declarations vs
AUTHOR-FACTS, Table 6.1/6.2/Fig 6.1 captions, bibliography, page numbering/page count/layout — is
clean; see sections below.

---

## 1. Gate

```
[PASS] compile    pages=117 errors=0 overfull_hbox=0 (1.7s)
[PASS] abstract    page2=Abstract, page3=Declaration of generative-AI use
[PASS] layout      lines_per_page=[22,30,3,29,4,29] (max-in-range check; see note)
[PASS] exclusion   hard=0 soft_bad=0 soft_ok=9
[PASS] anchors     rows=65 used=60 uncited=5 (F9,17,18,27,28 — pre-existing, disclosed)
[PASS] bib         entries=60 cited=60
[WARN] unanchored  sentences=66 (baseline 69, monitor-only, did not rise)
[PASS] scores
GATE PASSED
```
Full detail in `review/0904/gate_result.json` (this run, `_meta.time` 2026-09-04 05:23:15).

**Layout check note (task point 5h).** `check_layout()` only requires the *maximum* of six
sampled pages (30/35/40/45/50/55) to land in [18,36] — a page with an anomalously low count would
not fail it on its own. I independently sampled every 5th physical page from 10 to 118 and
extracted the two lowest outliers in the gate's own sample (physical pages 40 and 50, printed
"3" and "4" lines): both are legitimate **last pages of a section**, ending a paragraph a few
lines in before the next chapter's forced page break (confirmed by reading the page text — e.g.
physical page 40 ends "...able to hear (§1.7)." then blank, footer "30"). No page in the sampled
range 10-118 shows the elevated line-per-page count (45-60+) that the earlier `\scriptsize`
glossary-shrink bug produced (79-page false pass); pages in the 39-40 line range cluster around
the appendix/bibliography, consistent with the orchestrator's authorised single-spacing there.
No hidden shrink found. Document is 117 pages, under the 120 ceiling (task point 5h: both
sub-checks pass).

---

## 2. Traceability

Grades: FULLY_ADDRESSED (FA) / PARTIALLY_ADDRESSED (PA) / NOT_ADDRESSED (NA) / MADE_WORSE (MW) /
REJECTED_OK (RO) / REJECTED_BAD (RB).

### Maker-A (ledger repair)

| Item | Grade | Location | Note |
|---|---|---|---|
| F10 refresh | FA | C-ledger.tex:168-173 | 0.60/30% graph-arm-3, superseded 0.62/29% withdrawn; propagated to ch1/ch6 |
| F13 refresh | FA | C-ledger.tex:194-199; B-operations.tex:74; 07-discussion.tex:253 | $38.1 confirmed at all 3 body sites, superseded $36.3 withdrawn |
| F31 refresh | FA | C-ledger.tex:381-390; 03-baseline.tex:211; 06-results.tex:505; 07-discussion.tex:142,224 | 49 tasks (13/15/18/2/1) confirmed at every body site, superseded 44 withdrawn |
| F44 refresh (scope fix) | FA | C-ledger.tex:546-559; audit_m28_seed2_flips.py | 20.4%/143/700/7 windows confirmed; script SUBSET filter fix verified sound (cross-checked by Maker-A2 independently) |
| F45 refresh | FA | C-ledger.tex:561-573 | 19.5%/117/600/6 windows confirmed, superseded 19.2% withdrawn |
| F54 refresh (R15 cap) | FA | C-ledger.tex:724-742; audit_candidate_bucket_and_aim.py | 9,600 confirmed, matches F16 exactly as claimed; superseded 9,700 withdrawn |
| F55 refresh | FA | C-ledger.tex:744-758; 04-ghx.tex:172 | n=56 confirmed at both sites, superseded n=33 withdrawn |
| F26-F30,F32,F35-F38 reclass A→B | FA | C-ledger.tex (diff read in full) | All 11 rows now cite a verified recorded-artifact path; no row-body number altered except F35's Sample text (12×6→6×12, itself correct — see B2b-11) |
| F33, F34, F39 kept A, script named | FA | C-ledger.tex:141-146,148-156,205-228 | proof_stats.py / audit_gain_face.py named; F39 also carries B2b's later config.yaml-line and tier-rename edits, no conflict |
| F43 reclass A→B | FA | C-ledger.tex:538-544 | PROBE_ZIF artifact cited, script correctly re-described as a live launcher |
| Gate (own private build) | FA | — | 110 pages private; matches final in-place state's superset |

### Maker-A2 (flip-rate reconciliation)

| Item | Grade | Location | Note |
|---|---|---|---|
| Diagnosis 1a (seed 2, 8 vs 7 windows) | FA | RESPONSE-A2.md Part 1 | Read-only re-derivation, no script edits; reconciles cleanly (config-text vs evolve_status rule difference) |
| Diagnosis 1b (seed 3, 117 vs 115) | FA | RESPONSE-A2.md Part 1 | Same; (R6,R7) vs (R1,R2) window-swap explanation checks out against the ledger's own outage narrative |
| F41 ratio-provenance clause | FA | C-ledger.tex:514-517 | "$1.6$--$2.0\times$ ... arithmetic on three already-reported \cls{A} rows" confirmed present |
| F44 clause (F15 vs F44 divergence) | FA | C-ledger.tex:558-559 | Confirmed present, matches claim |
| F45 clause | FA | C-ledger.tex:573-574 | Confirmed present, matches claim |
| ch/01:340→368 fix | FA | 01-introduction.tex:368 | "the noise floor: $21.0$, $20.1$ and $19.2\%$" confirmed (F15's columns, per the ruling) |
| ch/06 rewrite (336-347) | FA | 06-results.tex:356-370 | Rewritten paragraph confirmed: F15 values stated as "the" seed rates, F44/F45 appear once parenthetically |
| Ratio 2.1→2.0 (2 sites) | FA | 06-results.tex:378; 07-discussion.tex:320 | Both confirmed "$2.0$"/"$2.0\times$"; zero remaining "2.1" in ch/*.tex |
| Grep sweep (no stray 20.4/19.5) | FA | — | Independently re-verified: only F44/F45's own rows + the one sanctioned parenthetical carry 20.4/19.5 |

### Maker-B1 (front matter, abstract, ch1, ch2, ch8, bibliography)

| Item | Grade | Location | Note |
|---|---|---|---|
| B1-01 / P1-01 | FA | 00-abstract.tex:7-9 | Superlative fixed; zero other "one published"/"only...code" hits in ch/ |
| B1-02 / P1-05 | FA | 00-abstract.tex:19,42-44 | "one candidate shipped"; F34 null result named |
| B1-03 / P2-07+P2-08+P3-08+P1-23 (abstract part) | FA | 00-abstract.tex:35,50-52; 01-introduction.tex:206-208,302; 08-conclusion.tex:7,59 | Scoping clause added; H1 wording reconciled to "not supported on declared substitute endpoints" (sound, matches ch8's C4 exactly); zero "rejected" remains; "deaf" swept correctly. Two documented, defensible wording judgment calls (see RESPONSE-B1 A.1-2) — not failures |
| B1-04 / P1-02+P1-03 | FA | ch/00-declarations.tex (new) | Every fact traced to AUTHOR-FACTS, no fabrication; "tagged thesis-2026-09 ... at the point of submission" correctly future-framed, not a present-tense false claim |
| B1-05 / P1-06 | FA | 01-introduction.tex:211-233; 08-conclusion.tex:76-80 | rq:1/2/3 labels present, ch8 closer names all three |
| B1-06 / P1-07 | FA | 01-introduction.tex:458-478 | 8-sentence roadmap, ch3 named formative/diagnostic, ch6 named main-results |
| B1-07 / P1-08 | FA (roadmap row); see failure #3 | ch/00-glossary.tex (new) | Fully satisfies P1-08's own acceptance check (glossary exists, all 6 flagged terms glossed, ≤2pp) and TASKS-B1.md's literal "two senses" brief; the 3rd-sense gap is a separate checker-level finding, not a P1-08 shortfall |
| B1-08 / P1-10+P1-12+bib | FA | 99-bibliography.tex:23,86,90,255,258,262; 01-introduction.tex:99; 02-related-work.tex:101-108 | All 6 keys present verbatim; gaia/rethink-harness-eval/harness-handbook cited exactly where claimed |
| B1-09 / P1-18 | FA | 02-related-work.tex:370 | Short caption confirmed |
| B1-10 / P2-04 | FA | 02-related-work.tex:300-303 | Supernet scoped to MaAS only |
| B1-11 / P2-15 | FA | 02-related-work.tex:212 | "the Planner" capitalised |
| B1-12 / P2-06 | FA | 01-introduction.tex:250-258 | Mechanism sentence present, quotes ch3 accurately |
| B1-13 / P2-10 (licence) | FA | 01-introduction.tex:60 | MIT licence clause present |
| B1-14 / P2-14 | PA — see failure #2 | THESIS.tex:106-123 | Pagenumbering scheme correct, Chapter 1 = page 1 confirmed via TOC, but 2 of 6 duplicate-destination warnings persist in the current in-place log |
| B1-15 / P3-06 | FA | 00-abstract.tex:6 | LLM expansion confirmed |
| B1-16 / P1-24 | FA | 08-conclusion.tex:42-49 | Disproportion concession matches claim |
| B1-17 / P1-26 (ch1 part) | FA | 01-introduction.tex:282-290 | Matches refreshed F10 exactly; seed 2 named as exceeding no-graph |
| B1-18 / P3-07 (86.0%) | FA | 00-abstract.tex:18; 08-conclusion.tex:21 | Both 86.0%; matches F4/F7's own form |
| Abstract page-budget trims | FA | 00-abstract.tex | Independently reread in full: 493 words (cross-checked twice, by two different counting passes), fits page 2 entirely (gate PASS); one grammar defect found — failure #5 |

### Maker-B2a (ch3, ch4, ch7, Appendix A)

| Item | Grade | Location | Note |
|---|---|---|---|
| B2a-01 / P1-09 (ch3 part) | FA | 03-baseline.tex:375; A-deviations.tex:143 | "GAIA-difficulty-2" and "capability evidence" heading confirmed; ch4's 2 ladder uses correctly left alone; see failure #4 for the resulting cross-file spelling split |
| B2a-02 / P1-20 | FA | 04-ghx.tex:272-280 | 3-sentence alternative-reading paragraph confirmed, matches acceptance check |
| B2a-03 / P1-22 | **PA — failure #1** | A-deviations.tex:26-31 | Pointer added but "correct" not replaced as required |
| B2a-04 / P1-23 (ch7 part) | FA | 07-discussion.tex:159-163,308-314 | "read as" softening confirmed present; Future Work already-compliant claim verified true |
| B2a-05 / P1-25 | FA | 07-discussion.tex:192-198 | Disclosure paragraph confirmed, names all 3 defects + F37, no-delay statement |
| B2a-06 / P2-02 | FA | A-deviations.tex:75,133; run_meta_aegis.py:1425 | Line 1425 independently confirmed to be the delta_rate/delta_count conjunction; both citations repointed |
| B2a-07 / P2-03 | FA | 04-ghx.tex:205-208; guidance.py | Matches source (PLANNER_SENSES_FLAG default-off) accurately |
| B2a-08 / P2-05 | FA | 04-ghx.tex:85-88 | AgentFlow disambiguation confirmed present |
| B2a-09 / P2-08 (ch7 part) | FA | 07-discussion.tex:68-69 | Softened phrase present, reads correctly |
| B2a-10 / P2-09 (cites) | FA | 07-discussion.tex:42,49 | Both \cite{} present, keys resolve (bib 60/60) |
| B2a-11 / P2-11 | FA | 07-discussion.tex:59-63 | Caveat present, anchored \F{34}\F{36} |
| B2a-12 / P3-04 | FA | 04-ghx.tex:302-308 | Names F7/F11/F52/F53, frames "checkable" as a bundle |
| B2a-13 / P3-05 (part) | FA | A-deviations.tex:88-89 | \allowbreak present in both model tokens; 0 underfull hbox confirmed |
| B2a-14 / P1-19 (report only) | Confirmed accurate | C-ledger.tex F9e/F15/F44/F45 | Independently verified: every window feeding the ±3.70 band and the swing extremes is a no-graph-arm window; load-bearing for B2b-04's grading |

### Maker-B2b (ch5, ch6, Appendix B, existing ledger rows)

| Item | Grade | Location | Note |
|---|---|---|---|
| B2b-01 / P1-26 (the CRITICAL) | FA | 06-results.tex:29,184-187,193-194 | Exhaustive `0.62`/`0.88` grep across ALL of ch/*.tex (not just B2b's 4 files) confirmed zero unscoped pairs remain; the 4 stray "0.62" hits found (C-ledger:172 superseded-note, C-ledger:596, 06-results:278,388) are all an unrelated slope-figure coincidence, not ship-rate. Devil's Advocate CRITICAL is resolved. |
| B2b-02 / P1-11 | FA | 06-results.tex:426 | "21 below" confirmed, no stray "25" |
| B2b-03 / P1-17 | FA | 06-results.tex:67 | \ref{tab:results} now in body prose |
| B2b-04 / P1-19 | FA | 06-results.tex:317-320,582-585 | Both Fig 6.1 caption and F48 prose state no-graph-only scope + by-assumption application; agrees with B2a-14's independent read |
| B2b-05 / P1-20 (ch6 part) | FA | 06-results.tex:204-210 | Matches ch4's wording substantively |
| B2b-06 / P1-09 (ch5/ch6/ledger part) | FA | C-ledger.tex:483,496 | Both F39 hits now "GAIA difficulty tier 2"; ladder use at 06-results.tex left alone; self-flagged the 2-way spelling split, see failure #4 |
| B2b-07 / P1-13 | FA | 05-design.tex:83-96,102-106 | All 3 footnotes present with URL + access date; 1.3x/2.4x honestly disclosed as pilot data |
| B2b-08 / P1-15 | FA (no-op, correctly) | 05-design.tex:288-290 | Confirmed unchanged; bounded search well-documented, [D] correctly raised |
| B2b-09 / P2-09 (ch5 part) | FA | 05-design.tex:227-230,273-276 | \cite{ich-e10} present; MDE-vs-VIM clause coherent |
| B2b-10 / P3-03 | FA | 05-design.tex:296-298 | F47 added to exploratory-test list |
| B2b-11 / P3-07 (parts) | FA | 06-results.tex:55-58,679-680; C-ledger.tex:82 | F35's own row independently verified "6 tasks x 12 repetitions" — "3 of the 6 tasks" is the *correct* override of a task-list transcription slip; unrounded-means clause and F7 86.0% both confirmed |
| B2b-12 / P2-13 | FA | C-ledger.tex:486,32-34 | config.yaml:136/143 confirmed by grep against R3-R5/R9,15,16's actual files; F17/F18-only preamble present |
| B2b-13 / P2-15 (part) | FA | B-operations.tex:85 | "Digester-shaped" capitalised |
| B2b-14 / P3-05 (part) | FA | C-ledger.tex:40,834 (labelsep=0pt) | Both enumitem warnings confirmed silenced in the current log |
| B2b-15 (re-verification) | FA | 05-design.tex; 06-results.tex | F16/F44/F45/F54/F31 citations all independently re-checked against current ledger rows, no mismatch |

### Maker-C (new recompute scripts + ledger rows F57-F60)

| Item | Grade | Location | Note |
|---|---|---|---|
| C-01 / P1-14 (F57) | FA | C-ledger.tex:771-782; 05-design.tex:139-141 | Task-clustered bootstrap CI confirmed present, self-check point estimates reproduce F9e exactly |
| C-02 / P1-21 (F58) | FA | C-ledger.tex:787-798; 06-results.tex:302-305 | Fresh/carried composition confirmed in Table 6.2's own caption, exactly where task item 5(e) asks |
| C-03 / P2-12 (F59) | FA | C-ledger.tex:800-808; B-operations.tex:23-27 | Campaign calendar confirmed, class A throughout (audit.jsonl ts field) |
| C-04 / P2-10 (F60, Spearman-Brown) | FA | C-ledger.tex:810-818; 05-design.tex:205-208; 07-discussion.tex:328-330 | Confirmed at both promised locations, arithmetic self-checks against F9e |

**Item-count summary**: 79 graded; 77 FULLY_ADDRESSED (incl. 1 REJECTED_OK-equivalent judgment
call absorbed into B1-03's FA and one correctly-executed no-op at B2b-08), 2 PARTIALLY_ADDRESSED
(B2a-03, B1-14). Zero NOT_ADDRESSED, zero MADE_WORSE, zero REJECTED_BAD.

---

## 3. Unauthorised-change sweep

`diff -ru` snapshot vs live, **stripping trailing CR** (the snapshot was saved LF-only, the live
tree is CRLF; the raw, non-stripped diff spuriously reported the whole of `ch/04-ghx.tex`,
`ch/01-introduction.tex`, `ch/03-baseline.tex` and `ch/00-abstract.tex` as one giant hunk each,
which would have hidden real hunk boundaries — corrected before reading). Clean hunk counts:
C-ledger.tex 20, 06-results.tex 13, 07-discussion.tex 9, 05-design.tex 8, 01-introduction.tex 7,
A-deviations.tex 5, 08-conclusion.tex 5, 04-ghx.tex 5, 02-related-work.tex 4, B-operations.tex 3,
99-bibliography.tex 3, 03-baseline.tex 2, 00-abstract.tex 2. THESIS.tex: 1 hunk (front-matter
block). fig/scores-table.tex: 1 hunk (P0 fix, bold-marker positions only — every underlying score
digit is byte-identical between snapshot and live, confirmed by inspection). fig/scores.pdf and
fig/harnessx_architecture.jpg show as "Only in ch/fig" (new relative to the snapshot) — both are
non-source build/asset files never captured by the snapshot's scope; `harnessx_architecture.jpg`
carries an mtime (02:11) that **predates** the round-1 baseline gate run (03:12) and is cited
identically in the pre-round `ch/01-introduction.tex`, i.e. it is a pre-existing asset, not a
new addition. `scores.pdf` regeneration is the same authorised P0 fix as `scores-table.tex`.

**Every one of the ~86 real hunks (all 13 chapter files + THESIS.tex, read in full, clean diffs)
traces to a disclosed item** in RESPONSE-A/A2/B1/B2a/B2b/C, or to one of the three orchestrator-
authorised fixes named in STATE.md (P0 score-table landing-round convention; the glossary's
`\begingroup\footnotesize\singlespacing...\endgroup` scoping, confirmed present at
`ch/00-glossary.tex:8,158`; `\singlespacing` before Appendix C, confirmed present at
`THESIS.tex:137` with an inline comment explaining it). No hunk changes a number, a claim, or a
ledger value without a traced source. No file outside the allowed set
(`THESIS.tex`/`ch/*.tex`/`fig/*.tex` plus the two authorised new files) was touched.

---

## 4. Number consistency

| Old value | New value | Grep result (ch/*.tex) |
|---|---|---|
| Ship rate 0.62 (29%) | 0.60/30% (3rd graph seed); 0.50/0.92/0.60 (all 3 seeds) vs 0.88 | Only 2 live occurrences of "0.62": C-ledger.tex:172 (the row's own "superseded ... is withdrawn" sentence, correct) and 2 unrelated slope-figure coincidences (C-ledger:596, 06-results:278,388 — a different metric, points/round slope, not ship rate). Zero unscoped "0.62 vs 0.88" pairs anywhere. |
| $36.3 (F13) | $38.1 | Old value found only inside its own "superseded ... withdrawn" ledger sentence (C-ledger.tex:198); new value confirmed at all 3 disclosed body sites (C-ledger:195, B-operations:74, 07-discussion:253) |
| "44 tasks" (F31) | 49 tasks (13/15/18/2/1) | Old value found only inside its own superseded-note (C-ledger.tex:389, plus the parallel note inside F39's row); new value confirmed at every disclosed body site (03-baseline:211, 06-results:505, 07-discussion:142,224, C-ledger:381-390) |
| 9,700 (F54) | 9,600 | Old value: zero live hits (only exists inside F54's own superseded-note, C-ledger.tex:741, correctly phrased as withdrawn). New value confirmed matching F16 exactly, as claimed. |
| n=33 (F55) | n=56 | Old value: zero live hits outside its own superseded-note (`n{=}33`, C-ledger.tex:757). New value confirmed at both disclosed sites (C-ledger:747, 04-ghx.tex:172). |
| 20.1%/19.2% quoted as "the" seed-2/seed-3 rate | 20.4%/19.5% correctly scoped to F44/F45 only, F15's 21.0/20.1/19.2 kept as the body's stated seed rates | Grep confirms: 20.4/19.5 appear ONLY in (a) F44's/F45's own ledger rows, (b) one sanctioned parenthetical (06-results.tex:366-367, exactly as A2 disclosed), and (c) one unrelated pre-existing "+19.5" slope entry (C-ledger.tex:607, correctly left alone per A2's note). No stray occurrence found. |
| "1.6 to 2.1 times" | "1.6 to 2.0 times" / "$2.0\times$" | Confirmed at all 3 sites (C-ledger.tex:517 "$1.6$--$2.0\times$", 07-discussion.tex:320 "$1.6$ to $2.0$", 06-results.tex:378 "$2.0\times$"); zero remaining "2.1" adjacent to "times"/"\times" anywhere in ch/*.tex. |

No remaining inconsistency found for any of the seven refreshed/reconciled quantities.

---

## 5. Specific points

**(a) Abstract.** Read in full (`ch/00-abstract.tex`). Fits page 2 entirely (gate PASS,
independently recounted at 493 words). One grammar/parallelism defect found — failure #5. All
numbers (21.0/20.1/19.2, 86.0%, H1 wording) agree with ch6/ch8 exactly; no other contradiction.

**(b) Declarations vs AUTHOR-FACTS.** `ch/00-declarations.tex` read in full. Repository URL
(`https://github.com/GaryGAO2003/HarnessX`), branch (`ghx/m27-variance`), script/source
directories, and the run-archive-on-request line all match AUTHOR-FACTS.md exactly. GenAI tool
(Claude Code, Anthropic, URL), model list, and the solver/meta-role-LLM exclusion clause all
present and accurate. No fact asserted that AUTHOR-FACTS does not support. Clean.

**(c) Glossary — three senses of "level".** FAIL — see failure #3. Six flagged terms (deaf,
archaeology, the clinic, processor, resolution, \F{} notation) are all present and correctly
defined in `ch/00-glossary.tex`; only the third "level" sense (cheatsheet's Level-1/Level-2
evidence) is missing.

**(d) Spelling of the renamed tier term.** FAIL — see failure #4. Three forms live
simultaneously ("GAIA-difficulty-2" / "GAIA difficulty tier 2" / "GAIA's own difficulty tier~2").

**(e) Table 6.1 / Table 6.2 (F58) / Fig 6.1 / F10-dependent sentences.** All confirmed agreeing
with the current ledger rows: Table 6.1's ship-rate row (`06-results.tex:29`) and slope-caption
clause (F47, lines 55-58) both read directly from source; Table 6.2's (`tab:arms`) caption ends
with the F58 fresh/carried sentence exactly (`06-results.tex:302-305`); Fig 6.1's caption states
the ±3.70 band's no-graph-only scope (`06-results.tex:317-320`); every F10-citing sentence found
(ch1 bullet, Table 6.1, Outcomes paragraph, "Fewer ships" opening) states the scoped
0.50/0.92/0.60-vs-0.88 comparison. Clean.

**(f) Bibliography.** All six reserved keys (`gaia`, `rethink-harness-eval`, `harness-handbook`,
`falconer-mackay`, `hutcheon-dilution`, `ich-e10`) present in `ch/99-bibliography.tex` with exact
spelling, and gate confirms `bib entries=60 cited=60` — all cited at least once. Clean.

**(g) Page numbering.** `\pagenumbering{roman}`/`{arabic}` present at THESIS.tex:110/123;
`THESIS.toc` confirms Chapter 1 opens at printed page 1. **Not clean**: 2 of the original 6
"duplicate destination... ignored" warnings persist in the current in-place `THESIS.log` — see
failure #2.

**(h) Page count and layout.** 117 ≤ 120 pages (compile PASS). Body-page line density spot-
checked independently across pages 10-118 (every 5th page) beyond the gate's own 6-sample check;
no hidden global shrink found — see the Gate section's layout note above. Clean.

---

## What was not re-verified in exhaustive depth (time budget)

Given the ~40-minute budget, three parallel `fork` sub-agents (same model, full session context,
read-only) independently graded B1's 18 items, B2a's 14 items, and B2b's 15 items against the
live manuscript; I directly re-verified their highest-stakes findings myself (the F10/0.62-0.88
CRITICAL sweep, the three-way "level" terminology split, the duplicate-destination warnings, the
declarations file, the glossary, every clean diff hunk in all 13 chapter files + THESIS.tex +
fig/, and the full number-consistency grep sweep) rather than trusting the sub-agent reports
alone. I did not independently re-run `audit_flip_rate_cluster_ci.py`, `audit_fresh_carried_
plateau.py`, `audit_campaign_calendar.py`, or `audit_spearman_brown.py` myself (Maker-C's four
new scripts) — I verified their printed output against the ledger rows and body citations for
internal consistency and self-check statements, but did not execute them a second time. I did
not re-run `git log` myself for B2a-03's commit-range claim (19-26 August 2026) — RESPONSE-B2a's
own account of ~55 matching commits was taken as reported, since the row's text itself is being
flagged as non-compliant for an unrelated reason (failure #1) regardless of the date range's
accuracy.
