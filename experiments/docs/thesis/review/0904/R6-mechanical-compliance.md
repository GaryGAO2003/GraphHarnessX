# R6 — Mechanical / Compliance Review

Copy-editing and LaTeX/compliance pass only. No thesis file modified, no
recompile run. Severity: CRITICAL / MAJOR / MINOR. Fix-class: [W] wording or
mechanical edit, [D] needs an author decision.

---

## 1. Compile log (THESIS.log)

- **Output written**: `Output written on THESIS.pdf (109 pages, 1112928 bytes)`
  (THESIS.log:1090). 109 pages, matches the physical PDF. — MINOR, informational.
- **Undefined references / citations**: none. No `LaTeX Warning: Reference
  ... undefined` or `Citation ... undefined` string appears in the log.
  Cross-checked against the .tex sources in §2 — 0 undefined refs/cites. —
  PASS.
- **Multiply-defined labels**: none reported by LaTeX itself, and independently
  confirmed 0 by parsing all `\label{}` in §2. — PASS.
- **Overfull boxes**: 0 occurrences. — PASS.
- **Underfull boxes**: 1 occurrence. `Underfull \hbox (badness 2591) in
  paragraph at lines 84--91` (THESIS.log:1030), landing in ch/A-deviations.tex
  around the sentence "The solver is `deepseek-v4-flash`; the four meta roles
  and the judge are ...". Caused by the long unbreakable `\texttt{}` token.
  MINOR, [W] — reword or allow a break point if the loose line is visible in
  print; `\emergencystretch` is already active so the visual effect is likely
  small.
- **Float placement** ("Float too large" / "h float specifier changed"): 0
  occurrences. — PASS.
- **Font substitutions**: no LM/T1 font-substitution warnings. The only
  "substituted" lines are xcolor color-model info messages (THESIS.log:363–371,
  e.g. `Model 'cmy' substituted by 'cmy0'`), which are xcolor's own internal
  colour-space normalisation, not a font problem and not a defect. — PASS,
  informational only.
- **Missing files**: 0 occurrences of "file not found" / "No file ...". —
  PASS.
- **pdfTeX ext4 duplicate-destination warnings**: 6 occurrences
  (THESIS.log:901, 909, 932, 942, 965, 971 — `destination with the same
  identifier (name{page.N}) has been already used, duplicate ignored`),
  landing at the abstract, the ToC, and the first three pages of Chapter 1.
  Root cause: THESIS.tex has no `\pagenumbering{roman}` for the front
  matter, so title/abstract/ToC/LoF/LoT all count from page 1, and
  THESIS.tex:116 (`\setcounter{page}{1}`) resets to 1 again for Chapter 1 —
  by design, per the file's own header comment ("page counter reset after
  it"), matching the UCL template; hyperref's automatic `page.N` anchors
  collide across that reset. Cosmetic only — visible page numbers are
  unaffected (confirmed against THESIS.pdf pp.1–3), only the PDF's internal
  named-destination table silently drops duplicates. MINOR, [D] — could be
  silenced with `\hypersetup{pageanchor=false}` around the front matter,
  but this is template-driven, not an error.
- **enumitem warnings**: 2 occurrences. `Negative labelwidth` at
  ch/C-ledger.tex:38 and ch/C-ledger.tex:734 (THESIS.log:1042, 1049), both
  from `\begin{description}[leftmargin=0pt,style=nextline,...]`. Harmless —
  `style=nextline` puts the item text on its own line regardless, so the
  negative computed width never actually renders. MINOR, [W] — could be
  silenced with an explicit `labelindent=0pt`, not urgent.

---

## 2. Cross-reference integrity

Parsed directly from the `.tex` sources (all `\label`, `\ref`/`\eqref`/
`\pageref`/`\autoref`/`\cref`/`\Cref`, `\cite`, `\bibitem`), not just the log.

- **`\label` definitions**: 72 total, all unique. 0 duplicate label names
  (`uniq -d` on the sorted list returns empty). — PASS.
- **Reference commands actually used**: the manuscript uses `\ref{}`
  exclusively — 161 instances across THESIS.tex/ch/*.tex/fig/*.tex. `\eqref`,
  `\pageref`, `\autoref`, `\cref`, `\Cref` are never used (0 each), so there is
  nothing in those families to check. — informational.
- **Undefined `\ref` targets**: 0. Every one of the 55 distinct label names
  targeted by a `\ref{}` has a matching `\label{}`. — PASS.
- **Labels defined but never referenced** (17, low priority per task spec):
  `app:ops`, `ch:conclusion`, `ch:intro`, `sec:baseline-revealed`,
  `sec:contributions`, `sec:evidence-integration`, `sec:evidence-wrong`,
  `sec:fielded`, `sec:ghx-preview`, `sec:hypothesis`, `sec:ladder`,
  `sec:provenance`, `sec:resolution`, `sec:respace`, `sec:verdict`,
  `sec:verification`, `tab:results`. Most are section anchors nobody happened
  to point back at (normal); `tab:results` is a table and is treated
  separately as MAJOR in §3 below because tables are expected to be pointed at.
  MINOR, [W]/no action needed for the section labels.
- **`\cite` keys vs `\bibitem` keys**: 74 `\cite{}` calls (some multi-key,
  e.g. `\cite{a,b}`) resolve to 54 distinct keys. ch/99-bibliography.tex has
  exactly 54 `\bibitem{}` entries, also all unique (0 duplicate bibitem keys).
  Set comparison both directions is empty: **0 cite keys without a matching
  bibitem, 0 bibitem entries never cited.** Every citation is `\cite{}` (no
  `\citep`/`\citet` variants). — PASS, clean bibliography.

---

## 3. Figures and tables

8 float environments total: 3 `figure` (ch/01-introduction.tex:52,
ch/04-ghx.tex:36, ch/06-results.tex:289) and 5 `table`
(ch/02-related-work.tex:341, ch/06-results.tex:15,253,304,586). All 8 have
exactly one `\caption` and one `\label`, both nested inside the
`\begin{}...\end{}` pair, verified by line-range containment. — PASS on
structural completeness.

- **`tab:results` never referenced in body text** — MAJOR, [W]. The "Results
  at a glance" table (ch/06-results.tex:15–57, `\label{tab:results}` at
  line 56) is the dashboard table opening the Results chapter and is never
  pointed at anywhere via `\ref{tab:results}`, nor hardcoded as "Table 6.1" /
  "Table~6.1" (checked directly, 0 hits besides the label itself). Every
  other float in the document is referenced at least once. Fix: add a
  `Table~\ref{tab:results}` pointer somewhere in the surrounding prose (e.g.
  the section that follows it).
- **Table 2.1 has no short caption, unlike every other float** — MAJOR, [W].
  ch/02-related-work.tex:359 uses bare `\caption{...}` (a full paragraph,
  ~90 words) instead of `\caption[short]{long}`. The other 7 floats all use
  the bracketed short-caption form (e.g. ch/01-introduction.tex:55
  `\caption[The official HarnessX overview]{...}`). Consequence: THESIS.lot's
  entry for Table 2.1 is the entire long paragraph verbatim (confirmed by
  reading THESIS.lot directly), sitting between four short, clean phrases —
  it does not "read sensibly as a list entry" the way the task's criterion
  asks. Fix: give Table 2.1 a short caption, e.g. `\caption[The five nearest
  systems against four properties]{...}`.
- **List-of-Figures / List-of-Tables content** (THESIS.lof, THESIS.lot):
  aside from the Table 2.1 problem above, all 7 remaining entries are short,
  sensible noun phrases: "The official HarnessX overview" (fig 1.1, p.3),
  "The six-stage loop and where GHX attaches" (fig 4.1, p.32), "Per-round
  scores of the six campaigns" (fig 6.1, p.53); "Results at a glance"
  (tab 6.1, p.48), "All six arms on the common bed" (tab 6.2, p.52),
  "Per-round scores, all six campaigns" (tab 6.3, p.54), "Starvation
  collapses and what the score did with them" (tab 6.4, p.59). None of the
  short entries end in a full stop (correct list-entry convention). — PASS.
- **Note**: Figure 6.1's short caption ("Per-round scores of the six
  campaigns") and Table 6.3's ("Per-round scores, all six campaigns",
  ch/06-results.tex:308) differ by only "of the"/a comma — plainly a
  deliberate figure+table pair (same data, p.53/p.54; the table caption
  says "The numbers behind Figure~\ref{fig:scores}"), not flagged as an
  error.
- **Caption full-stop consistency**: all 8 full (non-bracket) captions end
  with a period — verified by reading each caption's closing text
  (ch/01-introduction.tex:63, ch/04-ghx.tex:47, ch/06-results.tex:56,300,
  ch/02-related-work.tex:366, ch/06-results.tex:287,314,606). — PASS, 8/8
  consistent.
- **fig/scores-table.tex column alignment**: column spec
  `{@{}llrrrrrrrrrrrrrrrr@{}}` = 18 columns (2×`l` + 16×`r`). Header row and
  all 6 data rows (fig/scores-table.tex:4,6,7,8,10,11,12) counted
  programmatically at exactly 18 cells each. No mismatch. Also checked the
  other 4 tables' `tabular` specs against their header/data cell counts
  (ch/02-related-work.tex:346 5 cols/5 cells; ch/06-results.tex:18 4
  cols/4 cells incl. `\multicolumn`; ch/06-results.tex:256 6 cols/6 cells;
  ch/06-results.tex:590 5 cols/5 cells) — all consistent. — PASS, no column
  alignment problems found anywhere.

---

## 4. Terminology and style consistency

- **British vs American spelling**: **0 genuine inconsistencies found.** The
  document is consistently British/Oxford throughout: `behaviour`(3),
  `favour`(2), `labelled`(7), `cancelled`(1), `defence`(3); the American
  counterparts (`behavior`, `favor`, `labeled`, `canceled`, `defense`) all
  return 0. The `-ize`/`-ization` family (`canonicalize`(2),
  `canonicalization`(3), `optimize`(4), `optimization`(2), `realize`(2),
  `recognize`(1), `organize`(3), `normalization`(1)) has 0 `-ise`/`-isation`
  variants anywhere — standard Oxford spelling (`-ize` is the OED-preferred
  British form), not an Americanism, so not flagged. `license`/`licence`
  appears once each (ch/03-baseline.tex:283, ch/06-results.tex:73 = verb
  "license(s)"; ch/C-ledger.tex:433 = noun "licence") — the *correct*
  British noun/verb distinction, not an error. `judgment` (6×, no
  `judgement`) is standard in both dialects. — PASS overall.
- **Hyphenation variants**: checked all seven pairs named in the task.
  `readout`/`read-out` (53/0), `pre-registered`/`preregistered` (16/0),
  `no-op`/`noop` (7/0), `subset`/`sub-set` (32/0), `closed-loop`/`closed
  loop` (0/1, single predicative use, ch/00-abstract.tex:8 — fine as
  written) are internally consistent. `no-graph`/`no graph` (46/3) and
  `six-stage`/`six stage` (4/2) look mixed by raw count, but every "no
  graph" hit (ch/02-related-work.tex:257,363; ch/C-ledger.tex:436) is the
  unrelated phrase "no graph-hash identity"/"with no graph" (negation, not
  the arm name), and every "six stage" hit (ch/01-introduction.tex:26,48)
  is predicative/plural ("runs in six stages") where a hyphen would be
  ungrammatical — both pairs are correctly, not inconsistently, hyphenated.
  — PASS, 0 genuine hyphenation issues after context-checking.
- **Capitalisation of role names**: `GAIA`(19), `GraphHarnessX`(4),
  `Evolver`(14), `Critic`(10) are 100% consistently capitalised, 0 stray
  lowercase in body prose. `HarnessX`/`harnessx` and `GHX`/`ghx` look mixed
  (5/3 and many/9) but every lowercase instance is either inside a
  `\texttt{}` file path genuinely lowercase in the repo (e.g.
  `harnessx/ghx/graph_proposals.py`, ch/04-ghx.tex:315) or an internal
  `\label{ch:ghx}`/`\ref{ch:ghx}` key invisible to the reader — 0 lowercase
  in actual displayed prose. `Solver` is lowercase 15/15 times; per
  ch/A-deviations.tex:84-91, "solver" and "recorder" are explicitly *not*
  among "the four meta roles" (Digester/Planner/Evolver/Critic) — reads as
  a deliberate distinction, not sloppiness.
  - MINOR, [W]: ch/B-operations.tex:80 "The Evolver is not **digester**-shaped"
    — lowercase in a sentence that capitalises "Evolver" two words earlier;
    every other of 12 Digester mentions is capitalised. Should be
    "Digester-shaped".
  - MINOR, [W]: ch/02-related-work.tex:202 "consumed by **the planner**,
    quoted verbatim" — lowercase, referring to HarnessX's own Planner (the
    subject of the sentence is this thesis's own baseline system); 9 of 11
    Planner mentions elsewhere are capitalised. The other lowercase
    "planner" (ch/03-baseline.tex:353) is inside `\texttt{planner.py}`, a
    real filename — correct as-is, not flagged.
  - "sixth gate" is lowercase 9/9 times, fully consistent (treated as a
    descriptive phrase, not a proper name) — PASS, not flagged.
- **"we" vs "I"**: `\bWe\b`/`\bwe\b` = 9 total (ch/00-abstract.tex:12,25,49
  sentence-initial "We"; ch/01-introduction.tex ×4; ch/04-ghx.tex ×2). First
  person singular "I" = **0** anywhere in ch/*.tex (a naive case-insensitive
  count wrongly suggested 10 "I"s in ch/03-baseline.tex, ch/A-deviations.tex,
  ch/C-ledger.tex; on inspection every one of those is the roman numeral
  "(i)" in a list/subsection marker, e.g. ch/03-baseline.tex:283
  `\subsection*{(iii) Rate...}`, not the pronoun). Chapters 2, 5, 6, 7, 8,
  99, B, C use neither pronoun (impersonal voice). No "we"/"I" mixing
  exists. — PASS.
- **Acronym expansion on first use**: `LLM` (22 uses, first at
  ch/00-abstract.tex:6) is **never expanded** — "Large Language Model"
  occurs 0 times. MINOR, [D] — standard field terminology by 2026, but
  strict UCL style would want it spelled out once. `DAG` is expanded
  ("directed acyclic graph", ch/04-ghx.tex:105) only in Chapter 4, *after*
  two unexpanded uses in ch/00-abstract.tex:26 and ch/01-introduction.tex:225
  — MINOR, [D], ordering only (abstracts conventionally tolerate this).
  `SD` (ch/05-design.tex:164) and `CI` (first bare use
  ch/C-ledger.tex:141) are each correctly preceded by their spelled-out form
  ("standard deviation" ch/05-design.tex:161; "confidence interval(s)"
  ch/05-design.tex:305, ch/06-results.tex:150, both before the appendix) —
  PASS, not flagged. `GAIA`/`HarnessX`/`AEGIS`/`GraphHarnessX` are proper
  names introduced with a citation rather than an expansion, standard
  practice. `JSONL`/`API`/`YAML`/`GPT`/`AI` are field-ubiquitous, low
  priority. `GHX` is defined twice (ch/00-abstract.tex:25 and again at
  ch/01-introduction.tex:222) — fine, abstracts are read standalone.
- **Double spaces / doubled words**: 0 instances of either, checked across
  all of ch/*.tex. — PASS.
- **En-dash/em-dash/hyphen in ranges**: all 19 "R\emph{n}--R\emph{n}" round
  ranges use the correct double-hyphen en-dash form; 0 instances of the
  single-hyphen "R0-R15" error. The only bare single-hyphen digit-digit
  patterns found are ISO dates (`2026-08-26` etc., correctly single-hyphen)
  and one source line-number (`run_meta_aegis.py:1425`, correctly
  unformatted). — PASS.
- **`\%` spacing**: 140 instances of digit+`\%` with no space; 0 instances
  of digit+space+`\%`; 0 unescaped bare `%` after a digit (which would be a
  LaTeX comment-character bug). — PASS.
- **`$\pm$` vs `±`**: `$\pm$` used 24 times; the Unicode `±` glyph is used 0
  times. — PASS, fully consistent.
- **Thousands separators**: every 4+-digit quantity in the document uses
  the `N{,}NNN` LaTeX comma form (8{,}393, 9{,}600, 2{,}760, 1{,}186, etc.,
  27 distinct instances across 8 files) and none of those same numbers ever
  appears bare elsewhere (checked all 15 values individually — 0 bare
  hits). The only bare 4+-digit numbers in the whole manuscript are arXiv
  identifiers in ch/99-bibliography.tex (correctly unformatted) and one
  source line number (ch/03-baseline.tex:168). — PASS.

---

## 5. UCL COMP0091 checklist

- **Title page fields**: title "Provenance-Grounded Self-Evolution of LLM
  Agent Harnesses" + subtitle (THESIS.tex:86-90), author "Fei Gao"
  (THESIS.tex:94), degree "MSc Machine Learning" (THESIS.tex:103),
  supervisor "Prof. Jun Wang" (THESIS.tex:104), submission date "9 September
  2026" (THESIS.tex:92) — all present and filled, confirmed both in source
  and by reading THESIS.pdf p.1. The `\FIELD{}` macro
  (THESIS.tex:82-84, defined to print `[[...]]` for any unfilled submission
  field) is never invoked anywhere in the document — no blank fields remain.
  — PASS.
- **Disclaimer**: present, THESIS.tex:95-101, standard UCL wording ("This
  report is submitted as part requirement for the MSc Machine Learning at
  UCL. It is substantially the result of my own work..."), rendered as the
  title-page footnote — confirmed on THESIS.pdf p.1. — PASS.
- **Abstract fits one page**: confirmed by reading THESIS.pdf pp.1–3.
  Physical p.2 is the abstract in full (opens "An LLM agent is a model plus
  a harness..." and closes "The graph did not make the loop smarter. It
  made the loop checkable." on the same page); physical p.3 is already the
  Table of Contents. No abstract overflow. — PASS.
- **12pt**: `\documentclass[a4paper,12pt]{report}` (THESIS.tex:17), and
  THESIS.log confirms `size12.clo` is loaded. — PASS.
- **Page count ≤ 120**: 109 pages (THESIS.log:1090). — PASS, 11 pages of
  headroom.
- **Table of contents / List of Figures / List of Tables**: all three
  present (`\tableofcontents`, `\listoffigures`, `\listoftables`,
  THESIS.tex:113-115) with content (THESIS.toc, THESIS.lof, THESIS.lot all
  populated) — confirmed by reading physical p.3 (Contents). — PASS.
- **Chapters numbered**: standard `report`-class numbering, 1 Introduction
  through 8 Conclusion, confirmed in THESIS.toc and on the printed Contents
  page. — PASS.
- **Appendices lettered**: `\appendix` (THESIS.tex:127) precedes A/B/C;
  THESIS.toc:110,112,117 show "Appendix A ... Methodological Deviation
  Register", "Appendix B ... Operations Narrative", "Appendix C ... Fact
  Ledger". — PASS.
- **Known-missing, noted once each per instructions, no further action**:
  no GenAI-use declaration exists anywhere in the manuscript (0 hits for
  "generative AI"/"GenAI"/"use of AI" style phrasing). No code-repository
  access statement exists anywhere (0 hits for "repository access"/
  "github.com"/similar). Both are COMP0091-required and absent. — MAJOR,
  [D] (author must add both; not a copy-edit fix).

---

## 6. Strict-exclusion residual scan

All 13 tokens checked across every ch/*.tex file. **0 violations — every
hit is an allowed exclusion statement, an allowed official gate name, or an
allowed reference to another system's own smoke test.**

| Token | Hits | Judgment |
|---|---|---|
| `M24`, `M25` | 0, 0 | clean, codenames fully absent |
| `shakedown` | 5 (ch/01-introduction.tex:401,408,419; ch/07-discussion.tex:254; ch/C-ledger.tex:234) | ALLOWED — all 5 are exclusion/withdrawal statements ("...are excluded from every claim"; "That reading is withdrawn ... it was never admissible"; "Two superseded readings are withdrawn..."). None restates a shakedown-derived number as valid evidence. |
| `smoke` | 2 (ch/01-introduction.tex:42; ch/02-related-work.tex:48) | ALLOWED — "a synthetic-task replay smoke" (official gate name) and HarnessForge's "interface smoke test" (cited related-work system, `\cite{harnessforge}`), matching both explicitly-allowed categories. |
| `commissioning` | 1 (ch/01-introduction.tex:400) | ALLOWED — "Runs predating the baseline campaign (early commissioning...) ... are excluded from every claim" — exclusion statement. |
| `0/6`, `4/4`, `28.8` | 0, 0, 0 | clean |
| `1.04` | 1 (ch/99-bibliography.tex:95) | ALLOWED — false-positive substring match inside arXiv id `2601.04620`, not the retracted headline number. |
| `1.99` | 7 | ALLOWED — 6 are the current, corrected no-graph-arm localization-lift figure, explicitly marked "arms not comparable" (e.g. ch/06-results.tex:38); 1 (ch/C-ledger.tex:788-790) is the fact-ledger's own retraction entry `` `$1.99$ against $0.64$ shows localization did not improve'' $\to$ F9c: the two numbers cannot be subtracted...`` — an explicit correction record, not a restated claim. |
| `1,375`, `26--33`, `twenty-fold`, `\times 20` / `×20` | 0 each | clean |

---

## 7. Number-format consistency and arithmetic

- **Percentage/fraction pairs spot-checked** (all consistent, computed
  independently from the stated fraction): 18/59→30.5% and 8/55→14.5%
  (ch/06-results.tex:191, both match Table 6.1); 49/130→37.7% and
  51/162→31.5% (ch/06-results.tex:351-352); 161/800→20.1%, 126/600→21.0%,
  115/600→19.2% (ch/06-results.tex:337-340); 1239/1441→86.0%
  (ch/C-ledger.tex:61, ch/A-deviations.tex:206); 148/559→26.5% and
  419/559→75.0% (ch/C-ledger.tex:50,157); 25/50→50.0% and 77/306→25.2%
  (ch/C-ledger.tex:157). — PASS, no arithmetic errors in any spot-check.
- **Table 6.2 vs Table 6.1 cross-check**: Table 6.2's per-seed values
  (ch/06-results.tex:256-270) average to exactly the arm means Table 6.1
  quotes: no-graph plateau (67.3+64.6+58.4)/3=63.4 ✓, graph plateau
  (64.9+65.5+67.9)/3=66.1 ✓, no-graph terminal (69+68+63)/3=66.7 ✓, graph
  terminal (67+72+76)/3=71.7 ✓. Both also independently reconciled against
  fig/scores-table.tex's raw per-round R3–R15 and R15 cells (spot-checked
  no-graph seed 1 plateau: 13 values summing to 875/13=67.3 ✓; graph seed 3:
  883/13=67.9 ✓). — PASS.
- **MINOR arithmetic tension, [D]**: Table 6.1 (ch/06-results.tex:37)
  states the slope difference as "$+0.37$", but the two slope values it is
  computed from (also in the same row, and repeated in Table 6.2,
  ch/06-results.tex:264,269) are $+0.48$ and $+0.86$, whose difference is
  $0.38$, not $0.37$. Almost certainly a rounding-of-independently-rounded-
  components artifact (the underlying unrounded slopes likely differ by
  0.365–0.374), not a real error, but the two adjacent already-rounded
  numbers in the same table don't subtract to the stated third number.
- **MINOR arithmetic tension, [D]**: ch/06-results.tex:650-654, "$22/72$
  against a bare $17/72$: $+5$, with 3 tasks gained and 1 lost" — a net of
  "3 gained and 1 lost" sums to $+2$, not the stated $+5$. Likely the
  "3 gained/1 lost" is meant as an illustrative highlight ("the largest
  gains", per the next sentence) rather than an exhaustive tally, but as
  written the two figures do not visibly reconcile; worth one clarifying
  clause.
- **Decimal-place consistency across chapters**: the flip-rate triplet
  "21.0/20.1/19.2%" is byte-identical everywhere it appears (9 locations:
  ch/00-abstract.tex:38-39, ch/01-introduction.tex:340,
  ch/03-baseline.tex:225, ch/05-design.tex:123,125-126,
  ch/06-results.tex:41,336,338,340,344, ch/C-ledger.tex ×7). The per-round
  SD "3.70" is likewise identical everywhere (ch/03-baseline.tex:400,
  ch/05-design.tex:164, ch/06-results.tex:43,297, ch/07-discussion.tex:58,
  ch/C-ledger.tex:214) with 0 bare "3.7" variants. The plateau/terminal
  means "63.4/66.1" and "66.7/71.7" are identical in all 4 locations each. —
  PASS on all three quantities the task names as examples.
- **MINOR decimal-place inconsistency found** (not a task-named example,
  found while reading): the false-verdict reach figure is **"86.0%"** with
  one decimal in 8 of 11 occurrences (ch/01-introduction.tex:171;
  ch/03-baseline.tex:323; ch/04-ghx.tex:199; ch/06-results.tex:24,70,85;
  ch/A-deviations.tex:206; ch/C-ledger.tex:61,745) but bare **"86%"** in 3:
  ch/00-abstract.tex:19, ch/08-conclusion.tex:21, ch/C-ledger.tex:80 (the
  last is fact F7, a `\cls{B}` grep-record cross-check of the same `\cls{A}`
  fact F4 at line 61 — plausibly intentional precision-by-evidence-class).
  [D] whether to normalise.
- **fig/scores-table.tex row sums**: not independently re-summed against a
  separate "totals" row (the table has none to check against), but every
  row/column cell count matches the declared column spec (§3), and 2 of 6
  arm-mean chains were re-derived from the raw per-round cells and matched
  Table 6.2 exactly (above). — PASS on the checks performed.

---

*End of R6.*
