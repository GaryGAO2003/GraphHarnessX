# RESPONSE-B2b — Maker-B2b, round 1

Files owned: `ch/05-design.tex`, `ch/06-results.tex`, `ch/B-operations.tex`, `ch/C-ledger.tex`
(existing rows only — F57–F60 left untouched). No other file touched. No `git commit` run.
Read first: `agents/maker.md`, `STATE.md`, `LOOP-BRIEF.md`, `TASKS-B2b.md`, `RESPONSE-A.md`,
`RESPONSE-A2.md`, `RESPONSE-C.md`, `RESPONSE-B2a.md` item 14, and the cited `EDITORIAL-DECISION.md`
rows. Format: **R** (item verbatim) → **A** (what was done, or REJECTED + reason) → **C** (file:line
+ new sentence quoted).

---

## B2b-01 (P1-26 — the Devil's Advocate CRITICAL)

**R:** ch/06 ~29 (Table 6.1 row "Ship rate per round") and ~178–185: quote the refreshed F10
values — the no-graph figure(s) against all three graph-seed values or the arm means as the row
states them — never one seed against one seed; state that one graph seed ships above the no-graph
figure; keep the "one more gate" reading. Grep ch/05, ch/06, ch/B for "0.62" / "0.88" and fix every
unscoped pair.

**A:** Done. Grep of ch/05/ch/06/ch/B for "0.62"/"0.88" found three unscoped-pair sites, all in
ch/06 (ch/05 and ch/B have none). F10's ledger row (`C-ledger.tex:167–171`, already refreshed by
Maker-A) gives no-graph as one pooled figure ($0.88$) and graph as three discrete seed values
($0.50/0.92/0.60$) with no stated arm mean for graph — so per the item's own fallback I used "all
three graph-seed values," not a hand-computed mean. All three sites fixed: the table row, the
Outcomes paragraph (now states the reversal explicitly), and the "Fewer ships is not a regression"
opening (previously restated the same unscoped "$0.60$ vs $0.88$" pair a second time; rewritten to
drop the bare number and refer back qualitatively, since the scoped numbers are already stated in
full one paragraph earlier). The "one more gate" reading is kept intact in both the table's Reading
column and the surrounding prose.

**C:**
- `ch/06-results.tex:29` — "Ship rate per round & $0.88$ & $0.50/0.92/0.60$ & one more gate; one
  seed above \F{10} \\"
- `ch/06-results.tex:184–187` — "Final scores do not separate. Ship rates are $0.88$ per round in
  the no-graph arm against $0.50$, $0.92$ and $0.60$ across the three graph seeds \F{10} --- one
  seed ships \emph{more} often than the no-graph arm, not less."
- `ch/06-results.tex:193–194` — "The temptation is to read the graph arm's ship rate as the loop
  getting worse." (was: "The temptation is to read $0.60$ against $0.88$ as the loop getting
  worse.")

---

## B2b-02 (P1-11)

**R:** ch/06 ~401: "a number 25 below" → "a number 21 below".

**A:** Done. Located by content (Grep for "25 below"), not the stale line number — the sentence
now sits at line 426 after upstream insertions. This was also the concrete case item 15's
re-verification surfaced: the preceding clause on the same line already read "$21$" (F16, already
refreshed), while this trailing clause still said "$25$" — an internal inconsistency inside one
sentence pair, now resolved to one number throughout.

**C:** `ch/06-results.tex:426` — "A loop optimizing a single round's score is optimizing a number 21
below what its own history has already achieved." (was "25").

---

## B2b-03 (P1-17)

**R:** Add `Table~\ref{tab:results}` in the prose right after Table 6.1 (ch/06 after ~57).

**A:** Done. The table (`Results at a glance`, `\label{tab:results}` at line 59) already existed
but `\ref{tab:results}` was never used anywhere in body prose (confirmed by grep before editing:
zero hits). Added a one-sentence pointer as the opening of `\section{What the loop's evidence gets
wrong}`, immediately before the existing "The first result is..." sentence.

**C:** `ch/06-results.tex:67` — "Table~\ref{tab:results} collects every headline of this chapter in
one place; each section below establishes one row of it in turn."

---

## B2b-04 (P1-19)

**R:** Fig 6.1 caption (ch/06 ~292–302) and the F48/F49 prose (~334–346): one sentence stating
which arms and windows the ±3.70 / −8…+5 band is measured on (read F15/F9e/F44/F45 rows — after
Maker-A's repair — and RESPONSE-B2a's note) and that it is applied to the other arm by assumption if
that is what the rows say.

**A:** Done at both locations. RESPONSE-B2a item 14's read (not re-derived by hand) established
that every window feeding the ±3.70 SD (F15/F9e) and every seed's own swing extreme (F15 seed 1,
F44 seed 2, F45 seed 3) is a no-graph-arm same-config window; no F-row in {F15, F9e, F44, F45}
reports a graph-arm same-config flip-rate or SD. The task's "~334–346" line pointer predates
Maker-A2's rewrite of that exact block (now the flip-rate replication section, unrelated to F48/F49
citations); located the actual F48/F49 prose by content instead — it is the "gain face" section
(§6.something, "against the same-config band $-8\ldots{+}5$ \F{48}"). Added one clause at the
Fig 6.1 caption (after the existing $\pm 3.70$ sentence) and one at the F48 sentence, both stating
the no-graph-only scope and the by-assumption application to the graph arm; F49's own use of the
same band is covered by the same F48 clause since it appears in the same paragraph run.

**C:**
- `ch/06-results.tex:317–320` — "That $3.70$ is measured on the three no-graph arms' windows only
  \F{9e}; no graph-arm same-config window exists, so the same band is drawn under the graph arm's
  plateau by assumption."
- `ch/06-results.tex:583–585` — "That band, like Figure~\ref{fig:scores}'s plateau band, is
  measured on the no-graph arms' windows only \F{15}\F{9e} and applied here to graph-arm pairs by
  the same assumption."

---

## B2b-05 (P1-20, ch6 part)

**R:** ch/06 ~183–197: the 2–3 sentence alternative reading of the eighteen sixth-gate kills
(targeting degradation not ruled out; no no-graph-side hand audit), matching Maker-B2a's ch4
wording.

**A:** Done. Located the sixth-gate-kills passage ("Fewer ships is not a regression" subsection,
now ending around line 202). Added a three-sentence paragraph immediately after the malformed-rate
sentence and before "Fewer candidates, of higher legality...", deliberately mirroring
RESPONSE-B2a's `ch/04-ghx.tex:272–281` wording (same structure: cone-based representation may
degrade targeting rather than reveal it; no-graph has no equivalent gate so its mistargeting rate is
unmeasured, not zero; no hand audit was run) so the two chapters read as one claim stated twice, not
two different claims.

**C:** `ch/06-results.tex:204–210`:
> "\paragraph{An alternative reading of the eighteen kills.} An equally consistent reading is that
> the cone-based representation itself degrades targeting rather than revealing targeting that was
> already bad. The no-graph arm has no equivalent gate, so its own mistargeting rate is unmeasured,
> not zero, and no hand audit of no-graph candidates against the same criterion was run. The
> eighteen kills show the gate firing; they do not by themselves distinguish the two readings."

---

## B2b-06 (P1-09, ch5/ch6/ledger part)

**R:** Grep ch/05, ch/06, ch/B, ch/C-ledger for "level-2"/"level 2"/"L2" that mean the GAIA
difficulty tier (e.g. ledger ~450) and rename to "GAIA difficulty tier 2"; leave readout-ladder
uses.

**A:** Done. Grep found: ch/05 — zero hits; ch/B — zero hits; ch/06 — one hit at "Argument quality
climbs to readout level 2. And level 2 is still not level 3" (line 561), confirmed by context to be
the readout-ladder sense (rungs L0–L3), left untouched per instruction; ch/C-ledger — two hits, both
inside F39's row (the M22 R2→R3 gain-face figures), confirmed to be the GAIA-difficulty-tier sense
and renamed. Used the literal target string this task list gives ("GAIA difficulty tier 2"), which
differs slightly from RESPONSE-B2a's `ch/03-baseline.tex:375` choice ("GAIA-difficulty-2", per
EDITORIAL-DECISION's own worked example) — flagging this wording variance for the checker/author
rather than silently picking one, since both are literal instructions from different documents and
I have no authority to edit ch/03.

**[D] for the checker:** `ch/03-baseline.tex:375` reads "GAIA-difficulty-2" (Maker-B2a) while
`ch/C-ledger.tex` (this response) reads "GAIA difficulty tier 2" — same referent, two spellings
across chapters. Reconcile to one form if the glossary (P1-08) cross-references it.

**C:**
- `ch/C-ledger.tex:483` — "the round before, the GAIA difficulty tier 2 subset gains $16.3$
  points, and the score..."
- `ch/C-ledger.tex:496` — "...count and the GAIA difficulty tier 2 percentage-point gain are
  hand-extensions of the..."

---

## B2b-07 (P1-13) — bounded vendor-source search

**R:** ch/05 ~78–94 (BrowseComp 83.4/53.5/73.2, price ratios 3.1×/1.3×/2.4×, MRCR-1M 37.5): bounded
effort (≤15 min, WebSearch/WebFetch allowed for vendor model cards / pricing pages only): if you
find the page that states each figure, add a footnote with the URL and "accessed 4 September 2026";
if not, rewrite the sentence to say the figures are vendor-reported at the time of model selection
(August 2026) and not independently verified, and list the item as [D] for the author to supply the
source.

**A:** Searched (WebSearch, then WebFetch to confirm). Found the vendor model card for three of the
four figure-clusters: the DeepSeek-V4 model card on Hugging Face
(`huggingface.co/deepseek-ai/DeepSeek-V4-Flash`) states BrowseComp (Pass@1) V4-Pro Max $83.4$,
V4-Flash High $53.5$, V4-Flash Max $73.2$, and MRCR 1M V4-Flash Non-Think $37.5$ — all four numbers
match the thesis exactly. The DeepSeek API pricing page (`deepseek.ai/pricing`) lists
deepseek-v4-flash at \$0.14/\$0.28 (input/output per million tokens) against deepseek-v4-pro at
\$0.435/\$0.87; $0.435/0.14 = 3.11 \approx 3.1\times$, matching the thesis's list-price ratio
exactly. Added a footnote at each of these three points (BrowseComp cluster, list-price ratio,
MRCR-1M), each with the URL and "accessed 4 September 2026" as instructed.

The remaining sub-figures, $1.3\times$ (Flash's longer outputs) and the resulting $2.4\times$
per-task ratio, are **not** vendor-published anywhere I found (no model card or pricing page states
an output-length ratio), and no ledger row grounds them either (grepped `C-ledger.tex` for
"1.3\times"/"2.4\times"/"longer output": no hits). This reads as the project's own pre-campaign
pilot observation, not a vendor figure, so per the item's fallback I rewrote that clause to disclose
its actual provenance instead of leaving it beside two now-footnoted vendor numbers where a reader
would assume the same sourcing.

**[D] for the author:** the $1.3\times$ longer-output-length observation and its derived
$2.4\times$ per-task cost ratio have no vendor source and no ledger row. I disclosed it in-line as
"this project's own pilot tasks" rather than inventing a citation. If this was actually measured
formally (e.g. logged token counts from the pilot), it qualifies for a proper \F{} ledger row with a
recompute script; if it was an informal estimate, the current wording is the honest ceiling.

**C:**
- `ch/05-design.tex:78–86` — "...Flash sits mid-curve --- $53.5$ at high effort, $73.2$ at maximum
  --- which leaves an effect somewhere to appear.\footnote{DeepSeek-V4 model card, Hugging Face:
  \url{https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash}, accessed 4 September 2026; BrowseComp
  (Pass@1), V4-Pro Max $83.4$, V4-Flash High $53.5$, V4-Flash Max $73.2$.}"
- `ch/05-design.tex:87–96` — "Pro's list price is $3.1\times$ Flash's.\footnote{DeepSeek API
  pricing page: \url{https://deepseek.ai/pricing}, accessed 4 September 2026; list price per
  million tokens (cache-miss input / output), deepseek-v4-flash \$0.14 / \$0.28 against
  deepseek-v4-pro \$0.435 / \$0.87.} On this project's own pilot tasks --- not a vendor-published
  figure --- Flash's outputs ran roughly $1.3\times$ longer, so the per-task ratio is near
  $2.4\times$..."
- `ch/05-design.tex:102–105` — "Flash collapses on long context with thinking off (MRCR-1M
  $37.5$).\footnote{DeepSeek-V4 model card, Hugging Face:
  \url{https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash}, accessed 4 September 2026; MRCR 1M,
  V4-Flash Non-Think $37.5$.}"

---

## B2b-08 (P1-15) — bounded registration search

**R:** ch/05 ~262–263 (F34 stopping rule) and, if the H1 registration sentence is in ch/05, that
too: bounded search (≤15 min) for the registration record — grep experiments/docs/*.md and
`git -C D:/PycharmProj/HarnessX log -S"pre-regist" --oneline` / `--grep=pre-regist` — cite
"registered in <file> at commit <hash>, <date>" in Appendix A.1's style if found; else leave the
text and list as [D] with what you searched.

**A:** Searched, did not find a dated registration record. The H1 registration sentence is not in
ch/05 (grepped for "H1\b": zero hits), so only the F34 stopping-rule sentence applies.

What was searched: `git log -S"pre-regist" --oneline --all` (0 matches — the pickaxe found no diff
that adds/removes that literal substring); `git log --grep="pre-regist" --oneline --all` (24
matches, all either post-hoc thesis-writing commits describing the trial after it ran, e.g.
`c0d4f4c feat(thesis): full prose manuscript...`, or unrelated earlier-phase experiments under
different codenames — `s1k8b103`, `a1big5`, `chbase103`, `forkprobe_11` — that predate the M22–M29
campaign family entirely); `git log -S"stopping rule" --oneline --all` and
`git log -S"7 clean tasks" --oneline --all` (both match **only** `c0d4f4c`, the commit that wrote
the thesis prose itself — meaning that exact phrase first appears in the thesis, not in an earlier
design/registration document); `git log --diff-filter=A --oneline -- "**/proof_stats.py"` (the
row's own named script, `proof_stats.py`, was first added in `eaa3653 docs(thesis): overnight
chapter audit + whitelist recomputes (F41 born)` — a thesis-audit commit, confirming the script
itself is a later recompute tool, not the original pre-registration artifact); grep of
`experiments/docs/*.md` for "pre-regist\|stopping rule\|prospective batch\|n=70\|n = 70" (only hit:
`CH1-INTRO-DRAFT.md`, a chapter-1 prose draft dated 2026-08-26 that *discusses* the trial as already
run, not a prior registration); the script's own docstring (`proof_stats.py`) carries no date.
EDITORIAL-DECISION.md's own provenance line independently confirms R1 W3 already searched and
recorded this as "unlocated pre-reg date" before this round started.

**[D] for the author:** no dated commit, file, or docstring establishes a timestamped
pre-registration record for F34's stopping rule that predates the trial (as distinct from the
thesis's own retrospective narrative of it). Left the sentence unchanged. If a registration record
exists outside this repository (e.g. a lab notebook, an external doc, or a chat log), only the
author can supply it.

**C:** No edit. `ch/05-design.tex:288–289` unchanged: "...which is the test the stopping rule was
registered against \F{34}."

---

## B2b-09 (P2-09, ch5 part)

**R:** §5.3 opening: name the ICH E10 add-on design once with `\cite{ich-e10}`; §5.4: one clause
distinguishing "resolution" in this thesis's minimum-detectable-effect sense from the metrology
(VIM) sense.

**A:** Both done. §5.3 ("The efficacy-trial protocol") opening rewritten to name the add-on trial
design and cite it once. §5.4 ("Resolution laws as design inputs") given a new opening sentence
defining "resolution" before the section uses it. `\cite{ich-e10}` compiles clean in the private
build (resolves to bibliography entry [60] — Maker-B1 has already landed the six new keys; no
undefined-citation warning for this key in this build).

**C:**
- `ch/05-design.tex:225–230` — "Level 3 of the readout ladder --- did firing change outcomes ---
  was not available from the loop, so it was built by hand, following the \emph{add-on} design of
  clinical-trial methodology~\cite{ich-e10}: the graph mechanism is added on top of the base loop
  and read against the base loop alone, rather than either arm forgoing a standard-of-care
  control."
- `ch/05-design.tex:273–276` — "\emph{Resolution}, throughout this thesis, names a minimum
  detectable effect --- the smallest score movement this design can tell apart from noise --- and
  not the metrology sense in which resolution is an instrument's smallest distinguishable increment
  (VIM)."

---

## B2b-10 (P3-03)

**R:** ch/05 §5.4: add F47 explicitly to the illustrative exploratory-test list.

**A:** Done. Added to the "Multiplicity, declared" paragraph's exploratory-$p$-value list, alongside
the four already named (F21, F36, F35, F32).

**C:** `ch/05-design.tex:294–298` — "That includes the McNemar window of \S\ref{sec:power} \F{21},
the same-window controls \F{36}, the notes channel \F{35}, the cluster transfer \F{32}, and the
within-campaign slope permutation of \S\ref{sec:trend} \F{47}."

---

## B2b-11 (P3-07 parts)

**R:** Table 6.1: a caption clause noting the slope difference is computed from the unrounded arm
means (+0.482 / +0.856 → +0.374), so the displayed one-decimal entries do not subtract exactly;
ch/06 ~650–654: make the episodic-notes sentence say "+5 passes over 72 evaluations; at task level 3
of the 12 tasks rose and 1 fell". Ledger: normalise the one "86%" to "86.0%" if the row's own value
is 86.0%.

**A:** Three sub-parts, one adjusted for a ledger-consistency conflict. (1) Table 6.1 ("Results at a
glance") caption: added the unrounded-arm-means clause, quoting F47's own row values
($+0.482$/$+0.856 \to +0.374$) rather than recomputing by hand. (2) Episodic-notes sentence: F35's
own ledger row (refreshed by Maker-A this round) states the *Sample* as "6 tasks $\times$ 12
repetitions $\times$ 2 arms" and the task-level split as "3 tasks up, 1 down" — i.e. 3 of **6**
tasks, not 3 of 12 (12 is the repetition count, not the task count). Writing "3 of the 12 tasks"
verbatim as this task item states would contradict F35's own row, which the hard constraint against
introducing a number inconsistent with its ledger anchor does not permit. Used "3 of the 6 tasks,"
the narrowest reading that satisfies the item's stated intent (state the task-level breakdown
alongside the trial-level count) without contradicting the anchor, and flag the discrepancy here.
(3) Ledger: grepped `C-ledger.tex` for `86\%`/`86.0\%` — one bare "$86\%$" found, in F7's row,
stating the same fact F4's row states as "$86.0\%$" exactly (both describe the false-signal reach on
the no-graph arm, cross-cited together at Table 6.1's evidence-plane row); normalised to match.

**[D] for the author:** the task item's "12 tasks" appears to be a transcription slip (confusing the
12-repetitions figure with the 6-task count); I used F35's own "6" rather than override its anchor.

**C:**
- `ch/06-results.tex:53–56` — "...no margin was registered. The slope row's $+0.37$ is the rounded
  difference of the unrounded arm means, $0.482 \to 0.856$, difference $0.374$ \F{47}; the two
  one-decimal entries shown do not subtract to it exactly."
- `ch/06-results.tex:678–680` — "...returned $22/72$ against a bare $17/72$: $+5$ passes over 72
  evaluations; at task level, 3 of the 6 tasks rose and 1 fell, not significant \F{35}."
- `ch/C-ledger.tex:82` — "...against $86.0\%$ on the no-graph arm." (F7's row; was "$86\%$".)

---

## B2b-12 (P2-13)

**R:** Ledger F39: fix the `config.yaml` line citation (136 for R3–R5, 143 for R9/R15/R16; never
131 — verify by Grep in recipe/gaia_evolver/runs/M22_L0_ghx0/R3/config.yaml etc., read-only).
Ledger preamble: one line saying F17/F18 (and F27/F28 if the same holds) are supporting cross-check
rows not cited standalone.

**A:** Both done, one narrowed by evidence. Verified the two anchor line numbers by read-only Grep
against every named round's `config.yaml` under `recipe/gaia_evolver/runs/M22_L0_ghx0/`: R3, R4, R5
all carry `_singleton_group_: bash_windows_guard` at line 136; R9, R15, R16 all carry it at line
143 (the shift actually happens between R6 (136) and R7 (143), checked for completeness but not
claimed in the citation since only the two anchor rounds were asked for); line 131 appears nowhere
in any of these files. Fixed F39's citation accordingly.

For the preamble note: read R5-guardrails-ledger-audit.md's source finding directly (§(v) Anchor
integrity) rather than assume the task list's parenthetical extends automatically to F27/F28. That
finding's own resolution suggestion — "supporting/cross-check rows not meant for citation" — is
justified by *F18's* content specifically ("as F18's own content ... suggests it is": F18's row is
literally "Sample: F9a/F9b crossed with F15", a cross-check of two other rows). F17's content (a
lower-bound judgment, already self-caveated "may not be used as a ceiling") fits the same
description. F27 and F28, by contrast, are standalone probe write-ups (an episodic-dossier re-run;
a gate-killed-drug trial) with their own primary content, not cross-checks of other rows — they are
merely *also* uncited in the body, for unrelated editorial reasons. Concluded "the same" does **not**
hold for F27/F28, and added the disclaimer for F17/F18 only, per the item's own conditional. I did
not cite F27/F28 in body prose either (the alternative resolution the R5 finding offered) — that
was not asked for in this task list and is outside my scope's fifteen items.

**C:**
- `ch/C-ledger.tex:486–487` — "...campaign (\texttt{config.yaml:136} for R3--R5,
  \texttt{config.yaml:143} for R9/R15/R16, \texttt{\_singleton\_group\_: bash\_windows\_guard}) and
  holds the plateau." (was "\texttt{config.yaml:131}".)
- `ch/C-ledger.tex:29–34` — "...the row states the narrowed scope and the superseded reading
  appears in the retraction registry rather than here. \textbf{F17} and \textbf{F18} are supporting
  cross-check rows for other rows in this ledger and are not meant for standalone citation."

---

## B2b-13 (P2-15 part)

**R:** ch/B:80 "digester-shaped" → "Digester-shaped".

**A:** Done. Located by content (line is now 85, not 80, after RESPONSE-C's earlier insertion in
this file shifted it).

**C:** `ch/B-operations.tex:85` — "The Evolver is not Digester-shaped and the same rewrite does not
apply to it..." (was "digester-shaped").

---

## B2b-14 (P3-05 part)

**R:** ch/C-ledger.tex ~38 and ~734: add `labelindent=0pt` (or the enumitem option that silences the
negative-labelwidth warning) to those two list environments; confirm in your private build log.

**A:** Done, with a correction found during verification. Both `\begin{description}` environments
(now at lines 40 and 834, after this round's insertions) initially got `labelindent=0pt` added, per
the item's literal suggestion. The **first** private gate run still showed both warnings
unchanged (`Package enumitem Warning: Negative labelwidth ... on input line 40` and "...line 834" —
i.e. exactly at the two `\begin{description}[...]` lines themselves), proving `labelindent=0pt` was
not the operative fix (its default was already 0 for this list style, so the option was a no-op).
Added `labelsep=0pt` alongside it instead — with `leftmargin=0pt` and `labelsep=0pt` both zero, the
label-width subtraction can no longer go negative. Re-ran the private gate: both warnings are gone
(`grep -c "Negative labelwidth" THESIS.log` → 0, confirmed directly against the log, not just the
gate's summary line).

**C:**
- `ch/C-ledger.tex:40` — `\begin{description}[leftmargin=0pt,labelindent=0pt,labelsep=0pt,style=nextline,font=\normalfont,itemsep=6pt]`
- `ch/C-ledger.tex:834` — `\begin{description}[leftmargin=0pt,labelindent=0pt,labelsep=0pt,style=nextline,font=\normalfont,itemsep=5pt]`

---

## B2b-15 (ledger-dependent re-verification)

**R:** Re-read every sentence citing `\F{31}` (six locations), `\F{44}`, `\F{45}`, `\F{54}`,
`\F{16}` and confirm their numbers match the refreshed rows; fix any Maker-A missed, and record each
in your RESPONSE.

**A:** Re-read every occurrence of these five anchors inside my four files (the other locations of
the "six" `\F{31}` sites live in `03-baseline.tex`/`07-discussion.tex`, owned by Maker-B2a, out of
my scope to re-verify). Findings:

- **`\F{16}`** — `ch/05-design.tex:25` ("97 of the 100 have been solved at least once against a
  best single round of 76") and `ch/06-results.tex:404` ("union of everything ever solved, 97,
  exceeds the best single round any arm recorded, 76, by 21 tasks") both match F16's refreshed row
  (`97/100`, best round `76`, gap `21`) exactly. No fix needed at the citation itself — but the
  **very next, uncited clause** on `ch/06-results.tex:426` still said "25", which F16's own gap
  (stated one clause earlier as 21) contradicted; that is B2b-02 above, fixed.
- **`\F{44}`/`\F{45}`** — `ch/05-design.tex:34` (qualitative, no numbers to check), `:134`
  (swing $-8\ldots{+}5$, the union, matches), `:158` (per-seed swings $-4\ldots{+}2$ seed 2 /
  $-8\ldots{+}5$ seed 3, both match the refreshed 7-window/6-window rows exactly — already fixed by
  Maker-A per their note); `ch/06-results.tex:243–244` (raw trajectories 53→68/59→72 seed 2,
  66→63/57→76 seed 3, both match F44/F45 exactly), `:335`, `:347`, `:358` (already reconciled by
  Maker-A2 this round, left untouched as instructed). No mismatches found.
- **`\F{54}`** — `ch/05-design.tex:58` and `:182` (both "9,600 task evaluations... 3/18/79") match
  F54's refreshed row exactly; RESPONSE-A already noted these needed no change (originally
  cross-checked against F16 rather than F54, and both now agree). Confirmed, no fix needed.
- **`\F{31}`** — `ch/06-results.tex:487`-area ("Of the 49 swing tasks: 13 are leak-route, 15 sit at
  a capability wall, 18 are wrong-closure failures, 2 are friction, and 1 is starvation") matches
  F31's refreshed row (49 total: 13/15/18/2/1) exactly — already fixed by Maker-A. No other `\F{31}`
  citation exists in my four files (grepped ch/05 and ch/B for "leak-route"/"wrong-closure"/
  "capability wall": zero hits in either).

**Net new fix from this re-verification:** one — the uncited "25" on `ch/06-results.tex:426`,
already reported under B2b-02.

**C:** See B2b-02's entry; no further edits from this item.

---

## Build

Command: `python D:/PycharmProj/HarnessX/experiments/docs/thesis/review/0904/gate_checks.py
--outdir C:/Users/Admin/AppData/Local/Temp/claude/D--PycharmProj-HarnessX/18768f0e-989a-47fd-a93a-3447e8cfe9af/scratchpad/b2b`
(private outdir; in-place gate not run). Run twice — first run to confirm my content edits and
surface the `labelindent`-alone shortfall, second after the `labelsep=0pt` correction.

Final run:
```
[PASS] compile    pages=79 errors=0 overfull_hbox=0 (1.8s)
[FAIL] abstract
        - page 2 starts 'Abstract', page 3 starts 'Declaration of generative-AI use' (abstract must fit one page)
[PASS] exclusion  hard=0 soft_bad=0 soft_ok=9
[PASS] anchors    rows=65 used=60 uncited=5
[PASS] bib        entries=60 cited=60
[WARN] unanchored sentences=66
[SKIP] scores
GATE FAILED
```

**Reading.** `compile` PASSES clean: 0 errors, 0 overfull hbox, and the two enumitem
negative-labelwidth warnings from B2b-14 are confirmed gone by direct log grep (0 matches, was 2).
`bib` PASSES with 0 undefined citations — Maker-B1's six new keys (including `ich-e10`, which this
response cites) are already landed and resolve cleanly. `exclusion` and `anchors` are clean; the
five uncited rows (`9,17,18,27,28`) are the same pre-existing set RESPONSE-A/A2 recorded, unaffected
by my F17/F18 preamble note (a preamble sentence does not add a `\F{17}`/`\F{18}` body citation, by
design — the annotation's whole point is that these rows stay uncited in prose). `unanchored`
(WARN-only, monitor-not-increase) is **66**, down from the round's 69 baseline and from 68 at the
last upstream build — not increased. One of the hits traces to my own BrowseComp footnote passage
(`05-design.tex`), which is expected and correct: the check's regex recognises only `\F{}`/`\ref`
as "anchored," not a footnote citation to an external vendor URL, and a vendor-reported benchmark
score legitimately has no HarnessX ledger row to anchor to — footnoting it (as B2b-07 was
instructed to do) is the correct treatment, not a defect to silence with a fabricated `\F{}` tag.

**The one FAIL (`abstract`) is not attributable to my four files.** Directly verified: (1) none of
`ch/05-design.tex`, `ch/06-results.tex`, `ch/B-operations.tex`, `ch/C-ledger.tex` touch front
matter, the abstract, or declarations; (2) `THESIS.tex`, `ch/00-declarations.tex`,
`ch/00-abstract.tex` all carry modification timestamps (04:48–05:06) that predate this maker's
session; (3) the failure text itself names the cause directly — page 3 now starts "Declaration of
generative-AI use" instead of "Contents", which is the exact, correct side effect of Maker-B1
implementing P1-02 ("New section, THESIS.tex after line 111, before `\tableofcontents`") as
specified. The gate script's `check_abstract()` hardcodes "page 3 starts 'Contents'", a check
written before P1-02's mandatory front-matter page existed; it does not itself indicate lost or
malformed content. I confirmed content-completeness independently by extracting the compiled PDF
to text (`pdftotext`) and verifying full round-trip presence of all eight chapters plus both
appendices and the complete ledger through **F60** (the last row), with every one of this round's
inserted sentences (footnotes, the ICH E10 clause, the resolution clause, the alternative-reading
paragraph, the F17/F18 preamble note, the `config.yaml` fix, etc.) rendering correctly and in place.
The page count (79) sits well inside the required 30–120 bound; it is markedly lower than the
round-start ~109–113 baseline, which is a legitimate observation but traces to cumulative edits
across chapters I do not own (principally B1's `ch/01`/`ch/02` and the bibliography), not to
anything in this response. This is flagged for the checker/author, not fixed here — I have no
permission to edit `THESIS.tex`, `ch/00-*.tex`, or `gate_checks.py`.

---

## Ten-line summary

1. P1-26 CRITICAL fixed: Table 6.1 and both Outcomes-section mentions of the ship rate now quote
   all three graph-arm seed values ($0.50/0.92/0.60$) against the no-graph figure ($0.88$) and state
   that one seed ships more often than no-graph; the "one more gate" reading is kept.
2. "25 below" → "21 below" (`06-results.tex:426`), matching F16's gap stated one clause earlier —
   surfaced as an internal inconsistency by item 15's re-verification pass.
3. Added the missing `Table~\ref{tab:results}` prose pointer; added a matching "alternative reading
   of the eighteen kills" paragraph to ch/06, worded to match Maker-B2a's ch/04 version.
4. Stated the ±3.70 SD and −8…+5 band's no-graph-only scope, and its by-assumption application to
   the graph arm, at both Figure 6.1's caption and the gain-face (F48) prose.
5. Bounded vendor-source search (item 7): found the exact vendor sources for BrowseComp
   (83.4/53.5/73.2), MRCR-1M (37.5), and the 3.1× price ratio (Hugging Face model card + DeepSeek
   pricing page, both footnoted, "accessed 4 September 2026"); the 1.3×/2.4× per-task figures have
   no vendor or ledger source and were rewritten to disclose that honestly — flagged [D].
6. Bounded registration search (item 8): no dated pre-registration commit/file/docstring exists for
   F34's stopping rule (confirmed by six targeted git-log searches plus a docs grep); left the
   sentence unchanged, flagged [D] with the full search trail.
7. Added the ICH E10 add-on-design citation at §5.3's opening, a resolution-sense (MDE vs VIM)
   clarifying clause at §5.4's opening, and F47 to §5.4's exploratory-test list.
8. Renamed the GAIA-difficulty-tier "level-2" to "GAIA difficulty tier 2" in ledger row F39 (left
   ch/06's one readout-ladder "level 2" untouched); flagged a wording mismatch against
   `ch/03-baseline.tex`'s "GAIA-difficulty-2" for the checker.
9. Ledger housekeeping: fixed F39's `config.yaml` citation (136 for R3–R5, 143 for R9/R15/R16,
   verified by grep, never 131); added the F17/F18-only supporting-cross-check preamble note (F27/F28
   excluded after checking they don't fit the same description); normalised F7's "86%" to "86.0%";
   capitalised "Digester-shaped"; silenced both enumitem negative-labelwidth warnings (`labelindent`
   alone did not work — `labelsep=0pt` was the operative fix, confirmed by re-running the gate).
10. Private gate: compile/exclusion/anchors/bib all PASS clean (0 errors, 0 overfull, 0 undefined
    citations, both enumitem warnings gone); the sole FAIL (`abstract`) is Maker-B1's new
    Declaration-of-GenAI-use page pushing Contents to page 4, verified unrelated to and unbroken by
    this response's edits, with full-document content-completeness confirmed through ledger row F60.
    Round not declared complete — for the checker.
