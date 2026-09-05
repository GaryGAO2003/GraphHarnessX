# Round 1 · Maker-B1 task list (front matter, abstract, ch1, ch2, ch8, bibliography)

Files you own (nobody else edits them this round): `THESIS.tex`, `ch/00-abstract.tex`, `ch/01-introduction.tex`,
`ch/02-related-work.tex`, `ch/08-conclusion.tex`, `ch/99-bibliography.tex`, plus NEW files `ch/00-declarations.tex`
and `ch/00-glossary.tex`. Do not edit any other file. Item ids refer to `EDITORIAL-DECISION.md`; read each item's row
there for its source and acceptance check. Facts you may rely on are in `AUTHOR-FACTS.md` (verified tonight).

Work in this order. Keep the abstract on ONE page (it is 483 words now — every word you add there must be paid for by
a word removed there). Keep the author's plain declarative voice.

1. **B1-01 (P1-01)** Abstract line ~7: replace "HarnessX/AEGIS is, to our knowledge, the one published harness-level
   closed loop whose code is released, and a carefully governed one:" with "HarnessX/AEGIS is a published harness-level
   closed loop with released code and, to our knowledge, the most heavily governed one:" (HarnessForge's code is public —
   AUTHOR-FACTS). Grep the whole ch/ tree for any other "the one published" / "only ... code" superlative and fix likewise.
2. **B1-02 (P1-05)** Abstract: "candidates ship on it" → "one candidate shipped on it" (matches ch/01:172); add one short
   clause naming the pre-registered efficacy trial's null result (F34 — read the row in ch/C-ledger.tex and §6.6 to get
   the fact right). Pay for the words.
3. **B1-03 (P2-07 + P2-08 + P3-08 + P1-23, abstract part)** In the abstract's proposition sentences: add "on this bed and
   system class" (or equivalent) to the readout proposition; if the abstract says cumulative gain "is" non-positive,
   soften to "can be non-positive under this bed's regime"; at the headline verdict use "H1 is not supported on any
   pre-registered endpoint" rather than "rejected"; every "deaf" claim reads as a proposition, not a finding. Apply the
   same three changes at §1.3's verdict (ch/01) and in ch/08. Leave body passages that already carry the fuller hedge.
4. **B1-04 (P1-02 + P1-03)** New file `ch/00-declarations.tex`, `\input` from THESIS.tex right after `\input{ch/00-abstract}`
   and before `\tableofcontents`: two unnumbered sections (`\section*`, `\addcontentsline{toc}{section}{...}`):
   "Declaration of generative-AI use" and "Code and data access", drafted from AUTHOR-FACTS. Repository statement must
   name https://github.com/GaryGAO2003/HarnessX, branch `ghx/m27-variance`, and say the submission state is tagged
   `thesis-2026-09` in that repository (the author pushes and tags in the morning — P1-04), the directory of recompute
   scripts (`experiments/analysis/`), the thesis sources (`experiments/docs/thesis/`), and that the six whitelist run
   archives are available from the author on request. Keep both under half a page together.
5. **B1-05 (P1-06)** §1.4 (ch/01 ~209–216): promote Q1–Q3 to a labelled subsection "Research questions" (`\subsection*` or
   a `\paragraph` per question with labels `rq:1..3`), each with one sentence on when it was fixed relative to the data
   (pre-registered H1 vs formulated after the baseline campaign — read §1.3/§1.4/Appendix A.1 to get the timing right;
   do not invent dates). In ch/08 add one closing sentence per question that names Q1/Q2/Q3 and states the answer.
6. **B1-06 (P1-07)** End of §1.9 (after ch/01:~428): a 6–8 sentence chapter-by-chapter roadmap covering ch2–ch8 and
   Appendices A–C; say explicitly that Chapter 3 is formative/diagnostic and Chapter 6 carries the main results.
7. **B1-07 (P1-08)** New file `ch/00-glossary.tex`, `\input` from THESIS.tex after `\listoftables` (front matter, roman
   pages): `\section*{Glossary}` + a dense description list (`\begin{description}[leftmargin=...,style=nextline]` or the
   ledger's compact style) of 30–40 terms taken from the glossary table in `R3-perspective.md` (grep "Glossary" /
   "first use" there). Must include: harness, processor, seam, recorder, composition graph G / execution DAG U, cone,
   dossier, sixth gate, readout / readout ladder (L0–L3), resolution (this thesis's minimum-detectable-effect sense vs the
   metrology sense), same-configuration window, flip / flip rate, band, treadmill, archaeology, the clinic, mortality
   layers, survivor, "deaf" selection, capability vs efficacy, the `\F{n}` anchor notation and classes [A]/[B]/[C], and the
   two senses of "level 2" (GAIA difficulty tier vs readout rung). Two pages maximum.
8. **B1-08 (P1-10 + P1-12 + P2-09 bib entries)** Add to ch/99-bibliography.tex, in the file's own style and alphabetical/
   sectional placement, these entries with EXACTLY these keys (other makers cite them):
   - `gaia`: Grégoire Mialon, Clémentine Fourrier, Craig Swift, Thomas Wolf, Yann LeCun, Thomas Scialom. GAIA: a benchmark
     for General AI Assistants. arXiv:2311.12983, 2023.
   - `rethink-harness-eval`: Yike Wang, Huaisheng Zhu, Zhengyu Hu, et al. Rethinking the Evaluation of Harness Evolution
     for Agents. arXiv:2607.12227, 2026.
   - `harness-handbook`: Ruhan Wang, Yucheng Shi, Zongxia Li, et al. Harness Handbook: Making Evolving Agent Harnesses
     Readable, Navigable, and Editable. arXiv:2607.13285, 2026.
   - `falconer-mackay`: Douglas S. Falconer and Trudy F. C. Mackay. Introduction to Quantitative Genetics, 4th ed.
     Longman, 1996.
   - `hutcheon-dilution`: Jennifer A. Hutcheon, Arnaud Chiasson, Robert W. Platt. Random measurement error and regression
     dilution bias. BMJ 340:c2289, 2010.
   - `ich-e10`: ICH Harmonised Tripartite Guideline E10. Choice of Control Group and Related Issues in Clinical Trials.
     International Council for Harmonisation, 2000.
   Then cite `gaia` at GAIA's first use in ch/01 (~98); cite `rethink-harness-eval` (primary) and `harness-handbook`
   (secondary) in §2.1 (ch/02 ~55–89) with one sentence each stating what they do (facts in AUTHOR-FACTS; the Handbook
   paper is about making evolving harnesses readable/editable — place it near the structured-candidate-space discussion
   if that reads better). Maker-B2 cites the other three keys in ch5/ch7; do not worry if they are uncited when you finish.
9. **B1-09 (P1-18)** ch/02 ~359: give Table 2.1 a short caption `\caption[The five nearest systems against four properties]{...}`.
10. **B1-10 (P2-04)** ch/02 ~290–293: scope "supernet" to MaAS only; describe AgentSquare/EvoFlow generically.
11. **B1-11 (P2-15)** ch/02:202 "the planner" → "the Planner" (role name).
12. **B1-12 (P2-06)** §1.5 or §4.1-equivalent in ch/01: 3–4 sentences naming and answering "why not just patch the
    20-character heuristic" using the free-text identity problem and the broken feedback channels the thesis already
    discloses (grep ch/03 for "20-char" / "substring" to quote the mechanism correctly).
13. **B1-13 (P2-10 licence)** Fig 1.1 caption (ch/01 ~54–60): add "reproduced under the repository's MIT licence".
14. **B1-14 (P2-14)** THESIS.tex: replace the `\setcounter{page}{1}` scheme with `\pagenumbering{roman}` after `\maketitle`
    and `\clearpage\pagenumbering{arabic}` immediately before `\input{ch/01-introduction}`; check in your private build
    log that the six pdfTeX "duplicate destination" warnings are gone and page 1 is the first page of Chapter 1.
15. **B1-15 (P3-06)** Expand "large language model (LLM)" at first use in the abstract (or ch/01 if the abstract cannot pay).
16. **B1-16 (P1-24, default adopted)** ch/08 ~34–40: 2–3 sentences conceding that GHX's build scale is out of proportion to
    the narrow credited contribution, framed as enabling infrastructure for the readout question rather than as an
    efficient build.
17. **B1-17 (P1-26, ch1 part)** ch/01 ~257–262: rewrite the ship-rate sentence to quote the refreshed F10 row (read it in
    ch/C-ledger.tex AFTER Maker-A's repair): the no-graph figure against all three graph-seed values or the arm mean —
    never one seed against one seed — and say that one graph seed ships above the no-graph figure.
18. **B1-18 (P3-07 part)** Normalise "86%" to "86.0%" in the abstract and ch/08 if the ledger form is 86.0%.

Then: private build `python D:/PycharmProj/HarnessX/experiments/docs/thesis/review/0904/gate_checks.py --outdir <your scratch dir>/b1`
(compiles into that directory; skip scores regen). Fix what you broke. Write `round1/RESPONSE-B1.md` (R→A→C per item,
with file:line and the new sentence quoted). Do not run the in-place gate (other makers are compiling too).
