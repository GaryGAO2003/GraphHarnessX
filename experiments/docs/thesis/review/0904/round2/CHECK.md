# CHECK — round 2 (checker, re-check)

**VERDICT: FAIL**

Gate is green, `grep -ci duplicate THESIS.log` = 0 (was 2 at the end of round 1), and all six
claimed round-2 fixes are FULLY_ADDRESSED exactly as scoped at their claimed locations. The FAIL
is carried by one defect this round's task brief (item f) specifically directed me to sweep for:
the bare, unpointed "graph layer was correct" exclusion criterion — the wording round-1's CHECK
#1 / RE-REVIEW NEW-2 ruled unacceptable, and which this round's patch correctly removed from
`ch/A-deviations.tex` and `ch/B-operations.tex` — survives verbatim in two further locations
that were never on any round's fix list: `ch/01-introduction.tex:136` and `ch/05-design.tex:35`.
Chapter 1 is the most-read chapter in the document, which makes this the highest-visibility
surviving instance of the exact defect the round was meant to close.

## Failure list (executable)

1. **Residual "the graph layer was correct" — `ch/01-introduction.tex:136` and
   `ch/05-design.tex:35`.** Round-2 item 2 (this round's patch) replaced the bare judgment word
   "correct" with a dated, evidenced criterion in `ch/A-deviations.tex:26-31` and
   `ch/B-operations.tex:12-17` only — confirmed correct at both those sites (see table below).
   But the identical unevidenced phrasing survives in two more places, found by the task's own
   directed sweep (item f), neither of which was named by round-1's CHECK, by RE-REVIEW's NEW-2,
   or by either round-2 patch script:
   - `ch/01-introduction.tex:136`: "...Two further graph campaigns / were flown before the graph
     layer was correct. They are excluded from / every number and every narrative in this
     thesis..."
   - `ch/05-design.tex:35`: "...Two earlier graph / campaigns, flown before the graph layer was
     correct, are excluded from / every number and every narrative by a scope ruling
     (\S\ref{sec:scope})."

   Both state exactly the criterion round-1's checker ruled an unevidenced judgment call (CHECK
   #1: "a concrete pointer replaces the bare word 'correct'"); neither carries the dated fix-set
   pointer this round added elsewhere. Confirmed exhaustively: `grep -in "was correct"
   ch/*.tex THESIS.tex` returns exactly these two hits and no others; `grep -n "graph layer was"`
   and `grep -n "flown before the graph layer"` return the same two plus the now-fixed
   `ch/B-operations.tex:12` (which no longer contains "correct"). Fix: apply the same
   substitution already used this round to both remaining sites — e.g. ch/01-introduction.tex:136
   → "...were flown before the graph layer's defects were closed --- the fixes committed between
   the second shakedown and the first whitelist graph campaign (19--26 August 2026), each pinned
   by a regression test. They are excluded from..."; ch/05-design.tex:35 similarly ("...campaigns,
   flown before the graph-layer fixes committed between the second shakedown and the first
   whitelist graph campaign (19--26 August 2026), each pinned by a regression test, are excluded
   from..."). Re-verify with `grep -in "was correct" ch/*.tex` = 0 hits.

No other failures found.

---

## (a) Gate

```
bash review/0904/verify-gate.sh --no-regen
[PASS] compile    pages=117 errors=0 overfull_hbox=0 (1.6s)
[PASS] abstract    page2=Abstract, page3=Declaration of generative-AI use
[PASS] layout      lines_per_page=[22,30,3,29,4,29]
[PASS] exclusion   hard=0 soft_bad=0 soft_ok=10
[PASS] anchors     rows=65 used=60 uncited=5
[PASS] bib         entries=60 cited=60
[WARN] unanchored  sentences=65 (round-1 baseline 66/69, monitor-only, did not rise)
[SKIP] scores
GATE PASSED
```
`review/0904/gate_result.json._meta.time` = 2026-09-04 05:41:09. `THESIS.log`/`THESIS.pdf` mtime
(05:41:07) postdates every round-2-touched source file (latest `ch/00-abstract.tex` at 05:40:15),
confirming the gate read reflects the patched content, not a stale build. `soft_ok` rose 9→10,
exactly accounted for by the one new dated-criterion mention landing in `ch/B-operations.tex:13`
this round (a second corroborating confirmation of fix item 2, independent of the direct grep
below). No `undefined`/`multiply defined` warnings in `THESIS.log`; the glossary's new
`\ref{app:deviations}` (fix item 4) resolves against `ch/A-deviations.tex:3`'s
`\label{app:deviations}`.

## (b) Duplicate-destination warnings

`grep -ci duplicate THESIS.log` = **0** (round-1 closed at 2 of an original 6; fix item 5 clears
the remainder). Confirms `B1-14`/round-1-failure-#2 is now fully closed.

## (c) Six-item table

| # | Fix | Location(s) confirmed | Grade | Note |
|---|---|---|---|---|
| 1 | `rethink-harness-eval` corroborating sentence after "160 papers screened, 18 close-read." | `ch/07-discussion.tex:37-39` | FULLY_ADDRESSED | Sentence present verbatim, cites `\cite{rethink-harness-eval}`; key already in `ch/99-bibliography.tex` (bib entries=60 cited=60 unaffected — same key now cited twice). Closes RE-REVIEW NEW-1 / P1-12. |
| 2 | Exclusion criterion names dated fix set (19–26 Aug 2026, regression-test-pinned); bare "correct" gone from both passages | `ch/A-deviations.tex:26-31`; `ch/B-operations.tex:12-17` | FULLY_ADDRESSED (at both named passages) | `grep -in "was correct"` returns 0 hits in either file; both now read "...graph-layer fixes committed between the second shakedown and the first whitelist graph campaign (19--26 August 2026), each pinned by a regression test...". Closes CHECK #1 and RE-REVIEW NEW-2 **at the two named locations**. See failure list: the same unpointed phrase persists at two further, previously-unflagged locations. |
| 3 | One spelling "GAIA difficulty tier 2" everywhere | `ch/03-baseline.tex:375`; `ch/C-ledger.tex:483,496`; `ch/00-glossary.tex:84` | FULLY_ADDRESSED | `grep -rn "GAIA-difficulty-2"` and `grep -rn "GAIA's own difficulty"` both return 0 hits across `ch/*.tex`. All four live sites now read "GAIA difficulty tier 2" (glossary uses a `~` tie between "tier" and "2"; baseline/ledger use a plain space — renders identically, not a distinct spelling). Closes CHECK #4 / RE-REVIEW NEW-3. |
| 4 | Glossary "level 2" entry carries three senses (GAIA tier; readout rung 2; cheatsheet capability evidence) | `ch/00-glossary.tex:83-88` | FULLY_ADDRESSED | All three senses present: "GAIA difficulty tier~2 (a benchmark property...)"; "rung~2 of the readout ladder"; "the official cheatsheet's Level-1/Level-2 \emph{capability evidence}... which Appendix~\ref{app:deviations} calls capability evidence throughout." `\ref{app:deviations}` resolves cleanly (label confirmed at `ch/A-deviations.tex:3`, no "undefined" warning in `THESIS.log`). Closes CHECK #3. |
| 5 | `\pagenumbering{roman}` before `\maketitle`; `hypertexnames=false`; `\singlespacing` from `\appendix` on | `THESIS.tex:38` (hyperref option); `:109-110` (roman then maketitle); `:134-136` (`\appendix` / `\singlespacing` / `\input{ch/A-deviations}`) | FULLY_ADDRESSED | Order confirmed exactly: `\onehalfspacing` → `\pagenumbering{roman}` → `\maketitle` → front matter → `\clearpage` → `\pagenumbering{arabic}` → chapters → `\appendix` → `\singlespacing` → appendices. Closes CHECK #2; see (b) and (e) for downstream confirmation. |
| 6 | Abstract "blind by construction" sentence split; two trims to stay on one page | `ch/00-abstract.tex:17-22` | FULLY_ADDRESSED | Now three sentences: "...the column is blind by construction, applies its negative verdict to $75.0\%$ of answer-carrying calls, and reaches $86.0\%$ of dossiers." (parallel, one subject throughout) / "One candidate shipped on that column." (unambiguous referent) / "Four feedback channels are written but never delivered...". Gate `abstract` check still PASS (page2=Abstract, page3=Declaration — no page-2 overflow). Closes CHECK #5. |

## (d) Abstract — full read, grammar, and number check

Read `ch/00-abstract.tex` in full (57 lines, one paragraph block). Every sentence is grammatical
English; the round-1 parallelism/dangling-referent defect (failure #5) is fixed and no new
grammar issue was introduced by the two round-2b trims (dropped "Around it,", "can confirm" →
"confirms", "the same intervention" → "one intervention" — all clean simplifications, not
truncations mid-clause).

All twelve required numbers confirmed present and unchanged: **8,393** (`8{,}393 fresh`, line 13)
· **100-task** (line 14) · **twenty characters** (line 15) · **nine** ("median length of nine",
line 17) · **75.0%** (line 18) · **86.0%** (line 18-19) · **0 of 859** (line 30) · **eighteen**
(line 31) · **21.0/20.1/19.2%** (line 37-38) · **five tasks** (line 39) · **four campaigns**
(line 41) · **three times** (line 45). No number in the abstract changed.

## (e) Page count and page numbering

117 pages ≤ 120 (gate `compile` PASS). `THESIS.toc` confirms roman front matter — "Declaration of
generative-AI use" and "Code and data access" at page **i**, "Glossary" at page **vi** — and
Chapter 1 opening at arabic page **1** (`\contentsline {chapter}{\numberline {1}Introduction}{1}{chapter.7}`).
Consistent with (b)'s zero duplicate-destination count now that the title page ships under the
roman sequence.

## (f) Sweep for residual bad wording

- `grep -in "was correct" ch/*.tex THESIS.tex` → 2 hits, both in the exclusion sense, both
  unaddressed by any round's fix list — **see failure list item 1**.
- `grep -rn "GAIA-difficulty-2" ch/*.tex` → 0 hits. Clean.
- `grep -rn "GAIA's own difficulty" ch/*.tex` → 0 hits. Clean.

---

## Scope note

Per this round's narrower task brief, I did not re-run round-1's full unauthorised-change diff
sweep against a round-2 snapshot. In its place: I read both patch scripts
(`patch_round2.py`, `patch_round2b.py`) in full — each edit is a single, exact `old→new` string
substitution asserted to match exactly once in its target file — and independently confirmed by
Grep that every substitution landed verbatim at its claimed location and nowhere else. `git status`
shows the same 13 chapter files + `THESIS.tex` modified as at the end of round 1 (cumulative
since the last commit); no file outside that set, and no file outside the seven touched by the two
patch scripts, entered the changed set this round.
