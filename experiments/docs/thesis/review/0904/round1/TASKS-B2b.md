# Round 1 · Maker-B2b task list (ch5, ch6, Appendix B, existing ledger rows) — starts after Maker-A and Maker-C finish

Files you own: `ch/05-design.tex`, `ch/06-results.tex`, `ch/B-operations.tex`, `ch/C-ledger.tex` (existing rows only;
rows F57–F60 at the end were just added by Maker-C — leave them). Do not edit any other file. Item ids refer to
`EDITORIAL-DECISION.md`. Read `round1/RESPONSE-A.md` first: it lists the refreshed values (F10, F13, F31, F44, F45,
F54, F55) that your sentences must agree with.

1. **B2b-01 (P1-26 — the Devil's Advocate CRITICAL)** ch/06 ~29 (Table 6.1 row "Ship rate per round") and ~178–185: quote
   the refreshed F10 values — the no-graph figure(s) against all three graph-seed values or the arm means as the row
   states them — never one seed against one seed; state that one graph seed ships above the no-graph figure; keep the
   "one more gate" reading. Grep ch/05, ch/06, ch/B for "0.62" / "0.88" and fix every unscoped pair.
2. **B2b-02 (P1-11)** ch/06 ~401: "a number 25 below" → "a number 21 below".
3. **B2b-03 (P1-17)** Add `Table~\ref{tab:results}` in the prose right after Table 6.1 (ch/06 after ~57).
4. **B2b-04 (P1-19)** Fig 6.1 caption (ch/06 ~292–302) and the F48/F49 prose (~334–346): one sentence stating which arms
   and windows the ±3.70 / −8…+5 band is measured on (read F15/F9e/F44/F45 rows — after Maker-A's repair — and
   RESPONSE-B2a's note) and that it is applied to the other arm by assumption if that is what the rows say.
5. **B2b-05 (P1-20, ch6 part)** ch/06 ~183–197: the 2–3 sentence alternative reading of the eighteen sixth-gate kills
   (targeting degradation not ruled out; no no-graph-side hand audit), matching Maker-B2a's ch4 wording.
6. **B2b-06 (P1-09, ch5/ch6/ledger part)** Grep ch/05, ch/06, ch/B, ch/C-ledger for "level-2"/"level 2"/"L2" that mean the
   GAIA difficulty tier (e.g. ledger ~450) and rename to "GAIA difficulty tier 2"; leave readout-ladder uses.
7. **B2b-07 (P1-13)** ch/05 ~78–94 (BrowseComp 83.4/53.5/73.2, price ratios 3.1×/1.3×/2.4×, MRCR-1M 37.5): bounded effort
   (≤15 min, WebSearch/WebFetch allowed for vendor model cards / pricing pages only): if you find the page that states
   each figure, add a footnote with the URL and "accessed 4 September 2026"; if not, rewrite the sentence to say the
   figures are vendor-reported at the time of model selection (August 2026) and not independently verified, and list the
   item as [D] in your RESPONSE for the author to supply the source.
8. **B2b-08 (P1-15)** ch/05 ~262–263 (F34 stopping rule) and, if the H1 registration sentence is in ch/05, that too:
   bounded search (≤15 min) for the registration record — grep experiments/docs/*.md and `git -C D:/PycharmProj/HarnessX log -S"pre-regist" --oneline`
   / `--grep=pre-regist` — cite "registered in <file> at commit <hash>, <date>" in Appendix A.1's style if found; else
   leave the text and list as [D] with what you searched.
9. **B2b-09 (P2-09, ch5 part)** §5.3 opening: name the ICH E10 add-on design once with `\cite{ich-e10}`; §5.4: one clause
   distinguishing "resolution" in this thesis's minimum-detectable-effect sense from the metrology (VIM) sense.
10. **B2b-10 (P3-03)** ch/05 §5.4: add F47 explicitly to the illustrative exploratory-test list.
11. **B2b-11 (P3-07 parts)** Table 6.1: a caption clause noting the slope difference is computed from the unrounded arm
    means (+0.482 / +0.856 → +0.374), so the displayed one-decimal entries do not subtract exactly; ch/06 ~650–654: make
    the episodic-notes sentence say "+5 passes over 72 evaluations; at task level 3 of the 12 tasks rose and 1 fell".
    Ledger: normalise the one "86%" to "86.0%" if the row's own value is 86.0%.
12. **B2b-12 (P2-13)** Ledger F39: fix the `config.yaml` line citation (136 for R3–R5, 143 for R9/R15/R16; never 131 —
    verify by Grep in recipe/gaia_evolver/runs/M22_L0_ghx0/R3/config.yaml etc., read-only). Ledger preamble: one line
    saying F17/F18 (and F27/F28 if the same holds) are supporting cross-check rows not cited standalone.
13. **B2b-13 (P2-15 part)** ch/B:80 "digester-shaped" → "Digester-shaped".
14. **B2b-14 (P3-05 part)** ch/C-ledger.tex ~38 and ~734: add `labelindent=0pt` (or the enumitem option that silences the
    negative-labelwidth warning) to those two list environments; confirm in your private build log.
15. **B2b-15 (ledger-dependent re-verification)** Re-read every sentence citing `\F{31}` (six locations), `\F{44}`,
    `\F{45}`, `\F{54}`, `\F{16}` and confirm their numbers match the refreshed rows; fix any Maker-A missed, and record
    each in your RESPONSE.

Then: private build `python D:/PycharmProj/HarnessX/experiments/docs/thesis/review/0904/gate_checks.py --outdir <your scratch dir>/b2b`,
fix what you broke, write `round1/RESPONSE-B2b.md` (R→A→C per item). Do not run the in-place gate.
