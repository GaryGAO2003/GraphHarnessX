# Round 1 · Maker-B2a response

Files owned: `ch/03-baseline.tex`, `ch/04-ghx.tex`, `ch/07-discussion.tex`, `ch/A-deviations.tex`.
No other file touched. No `git commit` run. Format: R (item verbatim) → A (what was done, or
REJECTED + reason) → C (file:line + new sentence quoted).

---

## B2a-01 (P1-09, ch3 part)

**R:** ch/03 ~375: the GAIA difficulty tier is called "level-2"; rename to "GAIA difficulty tier 2"
(or "difficulty-2 tasks") so "L2 / level 2 / rung 2" is reserved for the readout ladder. Grep ch/03,
ch/04, ch/07, ch/A for every other "level-2"/"level 2"/"L2" and fix the tier ones the same way;
leave ladder ones.

**A:** Done, plus one extension beyond the literal two-bucket instruction. Grep of the four files
for `level-2|level 2|\bL2\b` found exactly three hits: (i) the GAIA-tier use in ch/03 (the "tier"
case — fixed); (ii) two ladder uses in ch/04 (`\textbf{L2}` rung label and "L1 and L2 are
mechanical" — left untouched, per instruction); (iii) one hit in ch/A that is neither the GAIA tier
nor the ladder — a deviation-register heading, "Manifest schema and level-2 evidence." Its own body
text already uses the term "capability evidence" twice for the same referent, so I renamed the
heading to use that existing term instead of inventing new vocabulary or leaving a third,
unglossed "level-2" sense standing (the acceptance check is "`grep` 'level-2' outside ladder
context returns 0", and this occurrence was outside ladder context). Re-grep after the edits: only
the two ladder hits in ch/04 remain in these four files.

**C:**
- `ch/03-baseline.tex:375` — "the GAIA-difficulty-2 subset gained \$16.3\$ percentage points; and
  the total score rose by \$9\$ tasks..."
- `ch/A-deviations.tex:143` — "\item[\textnormal{\textbf{Manifest schema and capability
  evidence.}}]" (was "...and level-2 evidence.")

---

## B2a-02 (P1-20)

**R:** ch/04 ~249–263 (§4.6/§4.7 sixth gate) and — only if the sentence lives in ch/04 or ch/07 —
name in 2–3 sentences the alternative reading of the eighteen sixth-gate kills: that the graph
representation may degrade the Evolver's targeting rather than reveal bad targeting, and that a
hand audit of no-graph candidates against the same criterion was not run, so the alternative is
not ruled out. (Maker-B2b makes the matching ch6 change.)

**A:** Done. Added a new paragraph immediately after "Why a sixth gate" (which states the
eighteen-kill fact, \F{53}) and before "A sixth acceptance gate", in §4.7 (Verification surfaces).
Three sentences, as specified.

**C:** `ch/04-ghx.tex:272–281`:
> "\paragraph{An alternative reading of the eighteen kills.} An equally consistent reading of
> \F{53} is that the cone-based evidence representation itself degrades the Evolver's targeting,
> rather than revealing targeting that was already bad. The free-text no-graph arm has no
> equivalent gate, so its comparable mistargeting rate is unmeasured, not zero, and no hand audit
> of no-graph candidates against the same criterion --- does the node a candidate claims to repair
> appear in a reconstructed execution account of the failure it cites --- was run. The eighteen
> kills show the gate firing; they do not by themselves distinguish the graph making bad targeting
> visible from the graph making targeting worse."

---

## B2a-03 (P1-22)

**R:** ch/A ~18–33: replace the bare criterion "flown before the graph layer was correct" with a
concrete pointer. Bounded search (≤15 min): `git -C D:/PycharmProj/HarnessX log
--since=2026-08-19 --until=2026-08-26 --oneline -- harnessx/ghx recipe/gaia_evolver` and grep
experiments/docs/*.md (M24-*/M25-* files are internal and untracked — cite them only if the
sentence says so) for the defect list closed before the first whitelist graph campaign. Cite
commit range + test names if found; else write "closed by the graph-layer fixes committed between
the second shakedown and the first whitelist graph campaign (19–26 August 2026), each pinned by a
regression test" only if the git log supports those dates.

**A:** Ran the bounded git log search. It returns roughly 55 commits touching `harnessx/ghx` and
`recipe/gaia_evolver` inside the 19–26 August 2026 window, the large majority `fix(ghx):` /
`fix(graph):` / `fix(recipe):` / `fix(evidence):` messages (examples: `740a34c fix(ghx): a bridged
tool with no edges is invisible to every cone`; `2ca7fc3 fix(ghx): the lift table was counting this
round's failures as passes`; `7f3f5b2 fix(ghx): cone ruler abstains on always-firing nodes (vacuous
in-cone)`; `f38214c fix(ghx): backtick Layer A' anchors so IV-1 counts them`; `c1be110 fix(ghx):
gate-replay timeout that actually times out`; `2c749a5 fix(ghx): gate-replay runner locates the U
where the recorder writes it`). This confirms the date window itself, but the set is too large and
too mixed with unrelated M27 feature work (the same window also contains M27 T1/T2 commits, e.g.
`574a08d`, `533ea89`, `d90551a`) for a ≤15-minute bounded search to responsibly name a single
tight commit range or a specific test-name list as *the* defect closure for the two excluded
campaigns without risking mis-attribution. I did not find an existing markdown doc in
`experiments/docs/*.md` naming a discrete "defect list" for this specific ruling either (the
closest, `M25-ROLLBACK-INCIDENT-R2.md` and `M24-RETROSPECTIVE-FINDINGS.md`, are about the excluded
campaigns' own incidents, not a fix-closure list). Per the item's own fallback clause, and because
the git log positively supports the 19–26 August 2026 date range, I used the fallback sentence
verbatim as a parenthetical inserted into the existing criterion, rather than leaving the bare word
"correct" unpointed.

**C:** `ch/A-deviations.tex:26–31`:
> "\textbf{The evidence whitelist} (2026-08-26). Two graph campaigns flown before the graph layer
> was correct --- closed by the graph-layer fixes committed between the second shakedown and the
> first whitelist graph campaign (19--26 August 2026), each pinned by a regression test --- are
> excluded from every claim, as are all runs predating the baseline campaign."

---

## B2a-04 (P1-23, ch7 part)

**R:** ch/07 ~119–165 and ~290–303: every "selection is deaf" claim reads as a proposition; Future
Work names "attach the L3 readout to retention and re-fly" as the unrun discriminating experiment.

**A:** Mixed: one small edit in the first range, no edit in the second (already compliant).
Grepped ch/07-discussion.tex whole-file for "deaf" (case-insensitive): zero hits — the word itself
is not used in this chapter (it lives in ch/02-related-work.tex, owned by another line). Within
~119–165 ("The rival hypothesis, stated and weighed"), the substantive claim is already hedged
throughout (called "\cls{C} judgment rather than a test", "observationally equivalent... does not
pretend otherwise"), except for one sentence that stated the readout/inheritance-failure reading as
settled fact ("Those two **are** readout and inheritance failures") — softened to "read as", to
match the acceptance check's own language. Within ~290–303 (Future Work item 1), the text already
says "Attach level 3 to the retention decision... This is also the discriminating experiment of
\S\ref{sec:proposition}" — cross-referencing §7.1's line 165–168, which already reads "Attach the
level-3 readout to the retention decision and re-fly." This already satisfies "Future Work names
the unrun discriminating experiment"; no edit made there to avoid stacking redundant hedges on
already-compliant text.

**C:** `ch/07-discussion.tex:159–163`:
> "So the honest summary is: the capability wall explains why the loop does not solve the hard
> family. It does not explain the loss of the one drug that worked, and it does not explain the
> treadmill. Those two read as readout and inheritance failures, which is what the proposition
> addresses."

(Future Work, `ch/07-discussion.tex:308–314`, unchanged — verified already compliant.)

---

## B2a-05 (P1-25, default adopted)

**R:** New short paragraph in §7.2 or §7.3: the defects documented in Chapter 3 (evidence column,
unreachable clamp, empty regression report) and the F37 near-miss will be reported to the HarnessX
maintainers on submission, with a pointer to the relevant sections; submission is not delayed for a
response.

**A:** Done, adopting the "Author Decisions in the Morning" default verbatim in substance. Placed
at the end of §7.2 (Governance), directly after the paragraph that already discusses the F37
near-miss, so the disclosure statement sits next to the finding it covers. Named the three ch/03
defects using their own section titles/labels for traceability: the evidence-column defect
(§sec:evidence-audit, "the column" that grades tool-output use), the safety clamp that cannot
engage on a small bed, and the regression report left empty by a round-indexing slip (both
§sec:open-loop).

**C:** `ch/07-discussion.tex:192–198`:
> "\paragraph{Disclosure.} The evidence-column defect (\S\ref{sec:evidence-audit}), the safety
> clamp that cannot engage on a small bed, and the regression report left empty by a
> round-indexing slip (\S\ref{sec:open-loop}), together with the F37 near-miss above, will be
> reported to the HarnessX/AEGIS maintainers around submission, with a pointer to the relevant
> sections of this thesis. Submission is not delayed awaiting a response."

---

## B2a-06 (P2-02)

**R:** ch/A ~71–72 and ~128–131: re-point both citations of the rollback rule from
`run_meta_aegis.py:901--911` to `run_meta_aegis.py:1425` (verify with Grep in recipe/gaia_evolver/
that 1425 is the rule).

**A:** Verified first: `grep -n "delta_rate <= -0.05 and delta_count <= -3"
recipe/gaia_evolver/run_meta_aegis.py` returns line 1425 exactly — matching the 0.05-rate /
3-count conjunction ch/A and ch/03 both describe. (ch/03-baseline.tex:168 already cites
`run_meta_aegis.py:1425` for the identical rule, independently confirming the target line before I
touched anything.) Re-pointed both ch/A occurrences.

**C:**
- `ch/A-deviations.tex:75` — "...the counterfactual gate, and the post-round rollback rule at
  \texttt{run\_meta\_aegis.py:1425} (\S\ref{sec:open-loop})."
- `ch/A-deviations.tex:133` — "...the rate falls by \$5\$ points \emph{and} the count by \$3\$
  tasks (\texttt{run\_meta\_aegis.py:1425}) --- is a separate, vendored mechanism..."

Post-edit grep of `901--911` in `ch/A-deviations.tex`: zero hits.

---

## B2a-07 (P2-03)

**R:** ch/04 §4.8 (or wherever the guidance seam is described): one sentence naming the
`HARNESSX_GHX_PLANNER_SENSES` flag (read harnessx/ghx/guidance.py to describe it accurately) and
that it stayed off in every whitelist campaign, so its effect is unmeasured.

**A:** Read `harnessx/ghx/guidance.py` (the module the docstring itself calls the evidence/guidance
seam into "the prescription-writing roles"). §4.8 by section-number count is "The typed candidate
surface", which is not where the seam is described; the seam itself is §4.6 "Evidence integration"
(the injection-manifest mechanism into Digester's/Planner's context) — used the "(or wherever the
guidance seam is described)" fallback and placed the sentence there, right after the paragraph
that already describes the injection manifest. Description matches the source exactly:
`PLANNER_SENSES_FLAG = "HARNESSX_GHX_PLANNER_SENSES"` is call-time read, default off, independent
of the base `HARNESSX_GHX_GUIDANCE` flag (`guidance.py:93,131-139`), added in "M27 T2.2/T2.3" to
rebind the Planner with fate-bucket base-rate priors for target selection and extend the Critic's
pointer with the same base rates for pricing predicted hits (`guidance.py:40-50`). M27 postdates
every whitelisted campaign, so the flag stayed off throughout them.

**C:** `ch/04-ghx.tex:205–208`:
> "A second, independent flag, \texttt{HARNESSX\_GHX\_PLANNER\_SENSES}, extends this seam to give
> the Planner fate-bucket base rates for target selection and the Critic the same rates for
> pricing predicted hits, but it stayed off in every whitelist campaign, so its effect is
> unmeasured."

---

## B2a-08 (P2-05)

**R:** ch/04 ~85–89: one clause distinguishing the AgentFlow whose edge family GHX borrows
(`\cite{agentflow}`, the agent dependency graph) from the unrelated RL-optimised system of the same
name.

**A:** Done. Inserted a disambiguating dash-clause immediately after the citation.

**C:** `ch/04-ghx.tex:85–88`:
> "The three strongly-typed edge families of AgentFlow's agent dependency graph~\cite{agentflow}
> --- the structured-workflow system of that name, not the unrelated RL-optimised agent sharing it
> --- are adopted directly; its node vocabulary is deliberately not..."

---

## B2a-09 (P2-08, ch7 part)

**R:** ch/07 ~65–68: soften "expected cumulative gain ... is consequently non-positive" to "can be
non-positive under this bed's parameter regime", or add a three-line derivation if the inputs are
on the page.

**A:** Used the softening option (primary instruction) rather than constructing a new derivation,
since the derivation route risks introducing reasoning not already ledger-anchored. Applied the
exact substitution named by the editorial decision.

**C:** `ch/07-discussion.tex:68–69`:
> "Expected cumulative gain over \$R\$ rounds can be non-positive under this bed's parameter
> regime \emph{regardless of variation quality} --- which is why better candidate generation, the
> axis the entire self-evolution literature optimizes, cannot rescue a loop in this regime."

---

## B2a-10 (P2-09)

**R:** ch/07 ~41–53: cite `\cite{falconer-mackay}` at the h² / breeder's-equation formula and
`\cite{hutcheon-dilution}` at regression dilution (keys added by Maker-B1; if the compile shows
them undefined, keep the cites — the checker reconciles).

**A:** Done, both cites added. Private-build compile confirms both are syntactically valid citation
commands, currently undefined pending Maker-B1's bibliography entries (pre-authorized; see build
summary below). The other two P2-09 sub-items (naming the ICH E10 add-on design at §5.3's opening;
the VIM-resolution clarifying clause) are in `ch/05-design.tex`, not one of my four files, and were
left for whichever line owns that chapter.

**C:**
- `ch/07-discussion.tex:42` — "The response to selection is given by the breeder's
  equation~\cite{falconer-mackay},"
- `ch/07-discussion.tex:49` — "...classical regression dilution~\cite{hutcheon-dilution}:"

---

## B2a-11 (P2-11)

**R:** ch/07 ~56–60 / ~94–97: one caveat sentence that the |δ|≲3 calibration bound comes from a
small, non-random hand-run set, not a random sample of shipped candidates.

**A:** Added the caveat once, at the bound's point of definition (~56–60); read the "/" between
the two cited locations as "either" (narrowest reading satisfying the stated intent, per maker.md's
ambiguity rule), since the second location (~94–97) only re-uses the already-defined |δ|≲3 figure
rather than re-deriving it, so a second caveat there would be redundant. Anchored the caveat to
\F{34}\F{36} — the same two rows this chapter already cites two sentences later ("Level 3 was
exercised by hand \F{34}\F{36}") — rather than inventing a new ledger reference; both rows are
small hand-run trials (F34: 7 clean tasks × 10 × 2, one prospective batch; F36: a hand-run
cluster-feeding probe under `PROBE_DOSSIER5/`), matching "small, non-random, hand-run" precisely.

**C:** `ch/07-discussion.tex:59–63`:
> "That is an \emph{upper} bound, because \$|\delta|\$ is a magnitude bound standing in for a
> standard deviation. The bound itself comes from the hand-run drug trials \F{34}\F{36} --- a
> small, non-random set chosen because a family looked repeatedly prescribed, not a random sample
> of the six campaigns' shipped candidates."

---

## B2a-12 (P3-04)

**R:** One clause (ch/04 or ch/07 where "checkable" is asserted) saying "checkable" names a bundle
of independently measured facts (F7/F11/F52/F53), not a single quantity.

**A:** The literal word "checkable" as the thesis's headline label is asserted only in
`ch/00-abstract.tex:56` and `ch/08-conclusion.tex:34–36` (per R3's own glossary), neither of which
is mine (both owned by Maker-B1 this round). ch/04 has one unrelated use ("makes the first
constraint checkable rather than aspirational", about the byte-pinned-substrate constraint, not the
headline claim). All four named facts (F7, F11, F52, F53) do live in ch/04, scattered across §4.6
(F7, F52) and §4.7 (F11, F53) — so I added the clarifying clause there, as a chapter-level
reinforcement of the fact bundle the abstract/conclusion's "checkable" label draws on, placed at
the natural close of §4.7 (Verification surfaces), which is where the last two of the four facts
sit.

**C:** `ch/04-ghx.tex:302–308`:
> "\paragraph{What ``checkable'' names.} Checkability is not itself one of this chapter's measured
> quantities; it is a label for a bundle of independently measured facts --- the false-flow
> column's dossier reach \F{7}, the citation density and validity the graph produces \F{52}, the
> sixth gate's kill count \F{53}, and the replay gate's refusal record \F{11} --- each falsifiable
> on its own terms rather than as one operationalised statistic."

---

## B2a-13 (P3-05 part)

**R:** ch/A ~84–91: reword the long unbreakable `\texttt{}` token that causes the underfull hbox
(insert `\allowbreak` at path separators or split the sentence).

**A:** Confirmed via R6-mechanical-compliance.md's compile log that the underfull hbox (badness
2591, "lines 84--91") lands exactly in the "Model tier" paragraph, caused by the two long
unbreakable tokens `\texttt{deepseek-v4-flash}` and `\texttt{deepseek-v4-pro}` (no slash path
separators present — these are hyphenated identifiers, not file paths — so used the `\allowbreak`
option at the hyphens rather than the "split the sentence" alternative). Verified fix: private-build
compile log now shows zero Underfull/Overfull warnings anywhere in the document (`grep -n
"Underfull\|Overfull" THESIS.log` returns nothing), against R6's one reported occurrence before
this round. Only P3-05's `\texttt{}`-reword clause was in my item; the `labelindent=0pt`
enumitem-warning clause is a preamble/style setting outside these four files and was left for
whichever line owns that configuration.

**C:** `ch/A-deviations.tex:88–89`:
> "The solver is \texttt{deepseek-\allowbreak v4-\allowbreak flash}; the four meta roles and the
> judge are \texttt{deepseek-\allowbreak v4-\allowbreak pro}; all run through a gateway..."

---

## B2a-14 (P1-19 wording support)

**R:** Nothing to edit here — but read F15/F9e/F44/F45 in ch/C-ledger.tex and record in your
RESPONSE what the band's arm scope is (which arms and windows the ±3.70 / −8…+5 numbers come
from), so the checker can compare with Maker-B2b's caption sentence.

**A:** No edit (ch/C-ledger.tex is read-only for me; read only). Findings, for the checker to
compare against Maker-B2b's Figure 6.1 / F48–F49 caption sentence:

- **F15** (`C-ledger.tex:212–227`): baseline campaign, **no-graph arm only**, seed 1. 6 no-ship
  full-batch windows inside R1–R15 (R0 excluded as a single baseline draw), 21.0% (126/600), single
  -window swing $-4\ldots{+}5$. States directly: "The 20 windows give a per-round score SD of
  **3.70 tasks** directly" — i.e. the σ=3.70 figure is computed on the pooled 20-window sample
  described under F9e, not on F15's own 6 windows alone.
- **F9e** (`C-ledger.tex:155–164`): explicitly scoped, "\emph{Sample:} **three no-graph arms**, 20
  full-batch same-config windows inside R1–R15, 2,000 pairs" — pooled across all three no-graph
  seeds (baseline + seed 2 + seed 3). This is the row F15's σ=3.70 draws on. **No graph-arm window
  contributes to it.** Note for the checker: F9e's own per-seed numbers for seed 2 (161/800) and
  seed 3 (115/600) are the figures F44/F45 (below) explicitly mark "superseded ... withdrawn" —
  this F9e-vs-F44/F45 mismatch is the one STATE.md already flags as assigned to Maker-A2, not
  something this response resolves.
- **F44** (`C-ledger.tex:543–556`): seed 2, **both arms** reach 16/16 rounds, but the flip-rate
  figure quoted (20.4%, 143/700, 7 full-batch windows, swing $-4\ldots{+}2$) is the **no-graph
  arm's** own re-derived same-config statistic for seed 2 ("against seed 1's 21.0%" — i.e. F15).
  The graph arm's seed-2 numbers are reported only as a raw R0→R15 trajectory (59→72, peak 73), not
  as its own same-config flip-rate/SD row.
- **F45** (`C-ledger.tex:558–571`): seed 3, both arms 16/16; **no-graph arm** flip-rate 19.5%
  (117/600, 6 full-batch windows, swing $-8\ldots{+}5$) — this is where the "$-8$" extreme of the
  "$-8\ldots{+}5$" band originates. Graph arm again reported only as a raw trajectory (57→76, peak
  76), not as a same-config flip-rate row.

**Conclusion for the checker:** every window feeding the ±3.70 SD and the $-8\ldots{+}5$ swing band
is a **no-graph-arm** full-batch same-config window (baseline seed 1 + seed 2 + seed 3, R1–R15, R0
excluded). No F-row in {F15, F9e, F44, F45} reports a graph-arm same-config flip-rate or SD. This
matches R3-perspective.md W1's finding exactly, and is what Maker-B2b's Figure 6.1 / F48–F49
caption sentence needs to state.

---

# Private build summary

Command: `python .../gate_checks.py --outdir .../scratchpad/b2a` (private outdir, in-place gate not
run).

```
[FAIL] compile    pages=113 errors=0 overfull_hbox=0 (1.6s)
        - undefined refs/citations: ['falconer-mackay', 'hutcheon-dilution']
[PASS] abstract
[PASS] exclusion  hard=0 soft_bad=0 soft_ok=9
[PASS] anchors    rows=65 used=59 uncited=6
[FAIL] bib        entries=54 cited=56
        - cited but no bibitem: ['falconer-mackay', 'hutcheon-dilution']
[WARN] unanchored sentences=68
[SKIP] scores
GATE FAILED
```

Both `FAIL` lines are exactly, and only, the two undefined-citation keys the task briefing
pre-authorized me to ignore ("Undefined citations for the keys falconer-mackay / hutcheon-dilution
/ ich-e10 / gaia / rethink-harness-eval / harness-handbook are expected until Maker-B1 lands them").
No other undefined ref/citation appears. Everything else genuinely passes: 0 compile errors, 0
overfull hbox, 0 overfull vbox (and, checked directly in `THESIS.log`, 0 underfull hbox — B2a-13's
fix confirmed against R6's one prior occurrence); abstract PASS; exclusion PASS (hard=0, no
excluded-campaign numbers reintroduced); anchors PASS. `unanchored sentences` is a WARN-only,
monitor-not-increase metric per STATE.md's baseline (69 at round start) — it is now **68**, i.e. it
went down, not up. Page count 113, within the ≤120 constraint. `scores` is skipped in this private
build (not relevant to my four files).

I did not attempt to fix the two undefined-citation FAILs (that is Maker-B1's item), and did not
run the in-place gate, per instructions.
