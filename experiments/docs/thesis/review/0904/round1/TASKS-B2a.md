# Round 1 · Maker-B2a task list (ch3, ch4, ch7, Appendix A)

Files you own this round: `ch/03-baseline.tex`, `ch/04-ghx.tex`, `ch/07-discussion.tex`, `ch/A-deviations.tex`. Do not
edit any other file (ch5/ch6/B/C-ledger are being edited by other lines; the bibliography keys below are being added
by Maker-B1 — cite them, do not add them). Item ids refer to `EDITORIAL-DECISION.md`.

1. **B2a-01 (P1-09, ch3 part)** ch/03 ~375: the GAIA difficulty tier is called "level-2"; rename to "GAIA difficulty
   tier 2" (or "difficulty-2 tasks") so "L2 / level 2 / rung 2" is reserved for the readout ladder. Grep ch/03, ch/04,
   ch/07, ch/A for every other "level-2"/"level 2"/"L2" and fix the tier ones the same way; leave ladder ones.
2. **B2a-02 (P1-20)** ch/04 ~249–263 (§4.6/§4.7 sixth gate) and — only if the sentence lives in ch/04 or ch/07 — name in
   2–3 sentences the alternative reading of the eighteen sixth-gate kills: that the graph representation may degrade the
   Evolver's targeting rather than reveal bad targeting, and that a hand audit of no-graph candidates against the same
   criterion was not run, so the alternative is not ruled out. (Maker-B2b makes the matching ch6 change.)
3. **B2a-03 (P1-22)** ch/A ~18–33: replace the bare criterion "flown before the graph layer was correct" with a concrete
   pointer. Bounded search (≤15 min): `git -C D:/PycharmProj/HarnessX log --since=2026-08-19 --until=2026-08-26 --oneline -- harnessx/ghx recipe/gaia_evolver`
   and grep experiments/docs/*.md (M24-*/M25-* files are internal and untracked — cite them only if the sentence says so)
   for the defect list closed before the first whitelist graph campaign. Cite commit range + test names if found; else
   write "closed by the graph-layer fixes committed between the second shakedown and the first whitelist graph campaign
   (19–26 August 2026), each pinned by a regression test" only if the git log supports those dates.
4. **B2a-04 (P1-23, ch7 part)** ch/07 ~119–165 and ~290–303: every "selection is deaf" claim reads as a proposition;
   Future Work names "attach the L3 readout to retention and re-fly" as the unrun discriminating experiment.
5. **B2a-05 (P1-25, default adopted)** New short paragraph in §7.2 or §7.3: the defects documented in Chapter 3 (evidence
   column, unreachable clamp, empty regression report) and the F37 near-miss will be reported to the HarnessX
   maintainers on submission, with a pointer to the relevant sections; submission is not delayed for a response.
6. **B2a-06 (P2-02)** ch/A ~71–72 and ~128–131: re-point both citations of the rollback rule from
   `run_meta_aegis.py:901--911` to `run_meta_aegis.py:1425` (verify with Grep in recipe/gaia_evolver/ that 1425 is the rule).
7. **B2a-07 (P2-03)** ch/04 §4.8 (or wherever the guidance seam is described): one sentence naming the
   `HARNESSX_GHX_PLANNER_SENSES` flag (read harnessx/ghx/guidance.py to describe it accurately) and that it stayed off in
   every whitelist campaign, so its effect is unmeasured.
8. **B2a-08 (P2-05)** ch/04 ~85–89: one clause distinguishing the AgentFlow whose edge family GHX borrows
   (`\cite{agentflow}`, the agent dependency graph) from the unrelated RL-optimised system of the same name.
9. **B2a-09 (P2-08, ch7 part)** ch/07 ~65–68: soften "expected cumulative gain ... is consequently non-positive" to "can be
   non-positive under this bed's parameter regime", or add a three-line derivation if the inputs are on the page.
10. **B2a-10 (P2-09)** ch/07 ~41–53: cite `\cite{falconer-mackay}` at the h² / breeder's-equation formula and
    `\cite{hutcheon-dilution}` at regression dilution (keys added by Maker-B1; if the compile shows them undefined, keep the
    cites — the checker reconciles).
11. **B2a-11 (P2-11)** ch/07 ~56–60 / ~94–97: one caveat sentence that the |δ|≲3 calibration bound comes from a small,
    non-random hand-run set, not a random sample of shipped candidates.
12. **B2a-12 (P3-04)** One clause (ch/04 or ch/07 where "checkable" is asserted) saying "checkable" names a bundle of
    independently measured facts (F7/F11/F52/F53), not a single quantity.
13. **B2a-13 (P3-05 part)** ch/A ~84–91: reword the long unbreakable `\texttt{}` token that causes the underfull hbox
    (insert `\allowbreak` at path separators or split the sentence).
14. **B2a-14 (P1-19 wording support)** Nothing to edit here — but read F15/F9e/F44/F45 in ch/C-ledger.tex and record in
    your RESPONSE what the band's arm scope is (which arms and windows the ±3.70 / −8…+5 numbers come from), so the
    checker can compare with Maker-B2b's caption sentence.

Then: private build `python D:/PycharmProj/HarnessX/experiments/docs/thesis/review/0904/gate_checks.py --outdir <your scratch dir>/b2a`.
Undefined citations for the six new keys are expected until Maker-B1 lands; anything else you broke, fix. Write
`round1/RESPONSE-B2a.md` (R→A→C per item). Do not run the in-place gate.
