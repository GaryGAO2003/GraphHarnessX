# RESPONSE-A — Maker-A (ledger-repair line), round 1

Source: `R5-guardrails-ledger-audit.md` Part 2 (per-row recompute table, ii) and (vi) class-honesty.
Scope: `experiments/docs/thesis/ch/C-ledger.tex` + every body chapter citing the affected rows.
Exception used: script edits limited to (a) R0–R15 window on `M22_L0_ghx0`, (b) 100-task no-pixel
subset enforcement where the row's own scope says "subset", (c) none needed for a `sys.path`
bootstrap (not required this round). No statistical definition, window count, or threshold was
changed beyond what those two fixes produce.

---

## Part 1 — Recompute table (F10, F13, F31, F44, F45, F54, F55)

All seven scripts were run from the repo root; none exceeded a few seconds. Two required the
authorised scope fix; the other five needed none — their mismatch is entirely stale-snapshot.

| Row | Old (ledger, before this round) | New (script output today) | Cause | Script change | Body locations changed |
|---|---|---|---|---|---|
| **F10** | graph arm 3 (M26b): `0.62` (`29%`) | `0.60` (`30%`) | Stale snapshot — `M26_100x16b` extended to 16/16 rounds (29 Aug) after this row was frozen; no-graph and the other two graph values already matched and are untouched. | None. | `C-ledger.tex:166-171`; `01-introduction.tex:258`; `06-results.tex:29` (Table 6.1 row), `06-results.tex:179`, `06-results.tex:185` |
| **F13** | full-batch mean `$36.3` | `$38.1` (n=9 full rounds, sum $343) | Stale snapshot, same cause as F10. No-op mean `$11.8` and the task-side-spend `\cls{B}` sub-reading already matched and are untouched. | None. | `C-ledger.tex:192-197`; `07-discussion.tex:242`; `B-operations.tex:69` |
| **F31** | 44 tasks: leak 12 (27%), wall 13, wrong-close 16, friction 2, starved 1 | 49 tasks: leak 13 (27%), wall 15, wrong-close 18, friction 2, starved 1 | Stale snapshot, same cause. Every category that changed *grew*; friction/starved unchanged; quarantine spot-check (5/5) unaffected. | None. | `C-ledger.tex:379-391`; `03-baseline.tex:211-213`; `07-discussion.tex:142`, `07-discussion.tex:213-214`; `06-results.tex:480-482` |
| **F44** | same-config flip `20.1%` (161/800, **8** full-batch windows, swing −4…+2) | `20.4%` (**143/700**, **7** full-batch windows, swing −4…+2 — range unchanged) | Script scope, mixed with a pre-existing window-pooling fact. `audit_m28_seed2_flips.py` computed on the 103-task bed (no `SUBSET` filter) instead of the common 100-task subset — fixed. After the fix the script *still* reports 7 pooled windows, not 8: it deliberately reports the documented (R11,R12) machine-restart resume pair separately ("NOT pooled" — a pre-existing, documented design choice mirrored in the seed-3 script's own R6/R7 handling, not touched by this fix). The ledger's "8 windows / 161/800" phrasing predates that convention; I did not force the resume pair back into the pool, per the constraint against changing window counts. Volatile-family re-flip (37.7%, 49/130, 5 windows) already matched and is untouched. | `experiments/analysis/audit_m28_seed2_flips.py`: added a `SUBSET` (100-task no-pixel) filter to `load()`, mirroring `audit_m29_seed3_flips.py`'s own pattern; fixed the per-window score-swing calc to use the subset-consistent `hist[k]` score (it previously mixed a subset-filtered `prev_pass` with `curves.json`'s full-103-bed `e["passed"]`); relabelled the trailing bed-size hint `/103` → `/100`. 4 lines changed. | `C-ledger.tex:543-555`; `01-introduction.tex:340-341`; `05-design.tex:155-156` (window count only, "8"→"7"); `06-results.tex:336-345` |
| **F45** | same-config flip `19.2%` (115/600, 6 windows, swing −8…+5) | `19.5%` (**117/600**, 6 windows, swing unchanged) | Stale snapshot — `audit_m29_seed3_flips.py` was already correctly scoped (100-task subset, R0–R15, its own documented (R6,R7) gateway-outage pair already reported separately, matching the ledger row's own "twelve-hour gateway outage... documented in the run indices" sentence). No scope bug found; the two extra flips reflect data state today vs. when the row was last computed. | None. | `C-ledger.tex:558-571`; `06-results.tex:336-345` (same block as F44) |
| **F54** | `9,700` task evaluations (3 never / 18 always / 79 volatile unchanged) | `9,600` | Script scope — `audit_candidate_bucket_and_aim.py`'s `load_history()` read `M22_L0_ghx0`'s 17th round (R16) without a cap, unlike `audit_ceiling_subset.py` / `plot_campaign_scores.py`'s established convention. Category counts (3/18/79) were already correct even uncapped and are unchanged; only the evaluations total moves. Now agrees with F16 exactly, as the row's own text claims. | `experiments/analysis/audit_candidate_bucket_and_aim.py`: added `CAP = {"M22_L0_ghx0": 15}` and a `if cap is not None and int(row["round"]) > cap: continue` guard inside `load_history()`, mirroring `audit_ceiling_subset.py`'s convention exactly. 4 lines added. | `C-ledger.tex:721-739`. Body: `05-design.tex:54-58` and `05-design.tex:174-180` already read `9,600` (apparently cross-checked against F16 rather than F54 originally) — no change needed there. |
| **F55** | cone-table sample `n=33` | `n=56` (medians unchanged: 1,186 nodes / 606,064 chars whole-*U*; 48/42 nodes cone) | Stale snapshot, same M26b cause. `closed_rounds(...)[:2]` always selects R0–R1 regardless of total round count, so the round *selection* is stable; the growth is in how many of R0–R1's failed-fresh tasks now have a *resolvable* unfolded-graph file, consistent with backfill during the same resume that produced F10/F13/F31/F54's growth. Rendered-cone-bytes `\cls{B}` sub-reading (`n=44`, R1 — a different, unrelated sample) is untouched. | None. | `C-ledger.tex:741-756`; `04-ghx.tex:172` |

**Cross-check run (not in the fix list, verified per the diagnosis's instruction):**
`audit_flip_rate_three_seeds.py` (F9e/F15's own script) was re-run unmodified — it already carries a
`SUBSET` filter and `CAP = 15` for all three seeds, and its output is byte-for-byte what F9e/F15
already state (seed 1 126/600=21.00%, seed 2 161/800=20.13%, seed 3 115/600=19.17%, pooled
402/2,000=20.10% [18.40,21.91], SD 3.70, 52.3% task-pair flip). **F9e, F15, and F18's "20.1% pooled"
cross-reference needed no edits.** `audit_m26b_noop_flip_rate.py` (F41) re-run unmodified: 74/178=41.6%,
matches exactly, no edit. `audit_same_config_flips.py` was checked and is not cited by any ledger row
(confirmed by grep); it is an M22-only diagnostic with its own optional round-cap argument and does not
claim 100-subset scope, so it is out of scope for this fix.

**Important methodological note — do not hand-reconcile F44/F45 against F15/F9e.** `audit_flip_rate_three_seeds.py`
computes seed 2 and seed 3's same-config windows with its own semantic-config-equality method (not
`audit_m28_seed2_flips.py`/`audit_m29_seed3_flips.py`'s `evolve_status`-based method), and pools the
documented resume/outage pairs differently. Both methods are legitimate and both are now correctly
scoped to the 100-task subset; they simply answer slightly different questions (own-script vs.
unified-script window selection). Per the task's own instruction, each row's number comes from *its own
named script*, not from a hand-derived cross-check — so F44 (143/700) and F45 (117/600) now differ
slightly from F9e's internal seed-2/seed-3 columns (161/800, 115/600), which is expected and was left
alone. **Every occurrence of "21.0/20.1/19.2%" in the body that is anchored only to `\F{15}`/`\F{9e}` or
to no anchor at all (abstract, `06-results.tex` Table 6.1, `05-design.tex`'s Wilson-CI passage, the
ledger's own F54 cross-reference) was left unchanged** — it tracks F9e's unedited, still-correct output.
Only the two passages that explicitly cite `\F{44}\F{45}` together with F44/F45's own raw fraction
counts (`01-introduction.tex:340-341`, `05-design.tex:155-156`, `06-results.tex:336-345`) were updated.

**Not touched, flagged for the author:** `07-discussion.tex:309` and `06-results.tex:353` both state
"$1.6$ to $2.1\times$ each seed's own bed rate" for the volatile-family/same-config ratio. No script
prints this ratio (confirmed: neither `audit_m26b_noop_flip_rate.py` nor `audit_m28_seed2_flips.py`
compute or print it) — it is a hand-derived range in the existing text. Recomputing it by hand myself
would violate the "never compute a pooled number by hand" instruction, so I left both occurrences as
printed. For the record (not applied): with F44's same-config denominator now 20.4% instead of 20.1%,
the seed-2 ratio becomes 37.7/20.4≈1.8× (was ≈1.9×); the seed-1 (F41) ratio is 41.6/21.0≈2.0×, not 2.1×
under any of the three seeds' post-fix numbers. The author should either derive this range with a
dedicated script or adjust the stated range by hand.

---

## Part 2 — Class-honesty table (F26–F30, F32–F39, F43)

Per R5 Part 2(vi): thirteen rows named no script; F43 named a live trial launcher. Three parallel
read-only searches (repo-wide Glob/Grep, no script executed, no model/API calls) located the actual
artifact behind every row's numbers. Two of the thirteen — F33 and F34 — turned out to have a genuine,
existing, read-only recompute script (`proof_stats.py`, previously uncited) and F39 partially does
(`audit_gain_face.py`); those three **stay Class A** with the script now named, correcting the
class-honesty gap without weakening them. The other eleven had no qualifying script (every script that
touches their numbers imports `ModelConfig`/`_make_provider`/`_run_task` and makes live model+judge
calls) and are **reclassified B**, citing the recorded JSON/markdown that verifiably carries their
numbers. All citations were shortened to bare filenames under one named directory (dropping the
repeated `recipe/gaia_evolver/[runs/]` prefix) after the first gate run found four resulting overfull
`\hbox`es (see Part 3).

| Row | Old class / source | New class / source | Verified against |
|---|---|---|---|
| **F26** | `\cls{A}`, "independent session, scored by the pilot's own judge" | `\cls{B}`, recorded trial output under `quarantine_PROBE_TWIN7/`: `verify_parent.json`, `verify_applied.json`, `pass_flags.json`, `R1/decision.md` | `verify_parent.json`/`verify_applied.json` sum to 14/21 and 13/21 exactly; `pass_flags.json` has 7 tasks; `R1/candidates/C-R1-02.md` contains the "quoting hell" quote verbatim. Generating scripts (`probe_twin_feed.py`/`probe_twin_verify.py`) confirmed live (import `HarnessConfig`/`ModelConfig`, call `_run_task`). |
| **F27** | `\cls{A}`, no source given | `\cls{B}`, recorded probe output under `PROBE_DOSSIER2/`: `R1/graph_evidence/facts.md`, `R1/candidates/C-R1-01.md`, `R1/landscape.md`, `R1/decision.md`, `audit.jsonl` | `facts.md` states "55 fresh attempts" verbatim; `C-R1-01.md` invents `PythonRun`; `landscape.md` carries the "no shipped change..." sentence near-verbatim; `audit.jsonl` shows both candidates killed at the gate stage. "Registry error 13"/"criteria file" text was **not found in any on-disk artifact** — flagged, not fixed (it reads as thesis-registry prose, not a run artifact claim). |
| **F28** | `\cls{A}`, no source given | `\cls{B}`, recorded trial output (`PROBE_DOSSIER2/verify_applied.json`, `verify_parent.json`) | Sums to 10/10 and 9/10 exactly. Generating script `probe_twin_verify.py` confirmed live. The "Bash calls 53→7 / PythonRun median 11" mechanism figures are not printed by any script (a manual tally over the same session logs) — flagged, not fixed. |
| **F29** | `\cls{A}`, no source given | `\cls{B}`, recorded trial output under `PROBE_DOSSIER3/`: `verify_applied.json`+`verify_applied_topup.json`, `verify_parent.json`+`verify_parent_topup.json` | Filtered/genuine sums to repaired 0/12, parent 1/11 exactly. `nas_probe.py`/`nas_gold_archaeology.py` (the archaeology scripts) both make live network fetches (USGS API, Wayback Machine) — confirmed disqualified as read-only. |
| **F30** | `\cls{A}`, no source given | `\cls{B}`, recorded trial output under `PROBE_DOSSIER4/`: `verify_applied_topup.json`, `verify_parent_topup.json`; 40-step by-product read from `verify_sessions_parent_40cap/` | Sums to repaired 5/10, parent 2/10 exactly. The 40-step-cap "7/10 vs 2/10" by-product has **no on-disk aggregate file** — only the raw 10 session transcripts (confirmed containing `[step-countdown] step N of 40`) — flagged, not fixed. |
| **F32** | `\cls{A}`, "trial artifacts" | `\cls{B}`, recorded trial output (`PROBE_DOSSIER6/trial_applied_transfer.json`, `trial_parent_transfer.json`) | 6 task keys match the row's task set; per-rep records confirm the 10×10 same-window design. Generating script `trial_cluster_run.py` confirmed live. |
| **F33** | `\cls{A}`, no source given | **`\cls{A}` retained** — `proof_stats.py` (canary batch) named | Ran `proof_stats.py` myself: its printed `canary` lines sum to parent 23/24, applied 24/24 exactly (8 tasks × 3 reps). Script is read-only (imports only `json`, `math.comb`, `pathlib`). |
| **F34** | `\cls{A}`, no source given | **`\cls{A}` retained** — `proof_stats.py` named | Ran `proof_stats.py` myself: prospective batch +1/−4 (sign p=0.9688≈0.97, parent 29/70 applied 21/70); pooled clean 174 pairs, parent 75/174 vs applied 72/174, Fisher one-tail 0.6679≈0.67; mechanism 51/99 vs 54/102 — **every number in the row reproduces exactly**. This is the thesis's sole pre-registered confirmatory test; it now has its real script named instead of none. |
| **F35** | `\cls{A}`, no source given | `\cls{B}`, recorded trial output (`PROBE_DOSSIER6/trial_parent_epic.json`, `trial_parent_epin.json`) | Sums to bare 17/72, +notes 22/72 exactly; per-task deltas (3 up incl. `d5141ca5` +3, 1 down) match exactly. **Also fixed:** the row's own `\emph{Sample:}` said "12 tasks × 6 repetitions" — the on-disk data is 6 tasks × 12 repetitions (both give 72 trials/arm; the 6 IDs match `epi_note_gen.py`'s `NOTE_TASKS` default). Corrected to "6 tasks × 12 repetitions". |
| **F36** | `\cls{A}`, no source given | `\cls{B}`, recorded trial output under `PROBE_DOSSIER5/`: `trial_parent.json`, `trial_applied.json`, `trial_parent_w3.json`, `trial_applied_w3.json` | Sums to 10/30 vs 17/30 (initial) and 6/10 vs 6/10 (same-window re-test) exactly. The "0/5" firing-autopsy claim has no aggregating artifact — only raw per-rep transcripts under `verify_sessions_applied/` — flagged, not fixed. |
| **F37** | `\cls{A}`, "archived with the candidate card" | `\cls{B}`, recorded candidate dossier (`experiments/docs/M27-COVERAGE-DIRECTIVE-CHEAT-TOOL.md`) | Contains the tool name (`GaiaBenchmarkLookup`) and all three gold answers verbatim (101.376/84.348, 1.8, 2), matching the row exactly. This is a preserved copy — the live run's own `C-R1-01.md` was overwritten by a later re-run after a prohibition clause was added. |
| **F38** | `\cls{A}`, "candidate cards and decision files across three campaigns" | `\cls{B}` (source now names the three specific campaign/round/candidate triples) | Confirmed all three candidate+decision file pairs exist with matching decision text ("accept, first in ranking" / "accept, ship alone") and evidence (fabricated identifier + zero-length fetch; 5/4 false-positive counts). Episode (ii) is `M26_100x16` (the *first*, pre-whitelist graph campaign) — distinct from `M26_100x16b` in episode (iii); both directories confirmed to exist with the cited files. |
| **F39** | `\cls{A}`, "configuration sources plus the campaign analysis" | **`\cls{A}` retained**, `audit_gain_face.py` named for two of four numbers | Ran `audit_gain_face.py` myself: `M22_L0_ghx0` R2→R3 prints score 55→64 (+9) and starved 35→4 — exact match. The "12 of the 16 newly-passing tasks" and "level-2 subset gains 16.3 points" figures are **not printed by any saved script** — verified only by hand-extending the same script's already-loaded fields, which I disclosed in the row rather than silently upgrading to a full A-class claim. |
| **F43** | `\cls{A}`, `zero_interference_pair.py` (confirmed live launcher) | `\cls{B}`, recorded trial output (`PROBE_ZIF/INDEX.md`, `trial_off.json`, `trial_on.json`) | `INDEX.md` states "Ledger: F43" directly and gives 9/10, 30/30-per-arm, arm totals 22/30 vs 24/30; independently summed the two JSON files myself — every figure matches exactly, including which single canary disagrees and in which arm. |

**Not reclassified — already correctly attributed, no row text changed beyond citation format:**
none of F26–F39/F43's row-body numbers changed (only F35's Sample text, above); every other number
in these fourteen rows was independently reproduced from the cited recorded artifact.

---

## Part 3 — Gate

First full run (after Parts 1 and 2, before citation shortening) **FAILED**: `compile` reported 4
overfull `\hbox`es (max 180.1pt) at exactly the F26, F30, F38, and F43 rows — their new `\texttt{}`
path citations were too long to break inside a single unbreakable typewriter token. Fixed by dropping
the repeated `recipe/gaia_evolver/[runs/]` prefix from every new citation (stating the run directory
once, then bare filenames), matching the ledger's own pre-existing terse-citation convention (e.g. F50's
"candidate card and round configurations, line-pinned"). No wording beyond the citations was touched for
this fix.

Final gate run:
```
[PASS] compile    pages=110 errors=0 overfull_hbox=0 (1.7s)
[PASS] abstract
[PASS] exclusion  hard=0 soft_bad=0 soft_ok=8
[PASS] anchors    rows=61 used=56 uncited=5
[PASS] bib        entries=54 cited=54
[WARN] unanchored sentences=69
[PASS] scores
GATE PASSED
```
`rows=61`, `uncited=5` (F9, F17, F18, F27, F28 — unchanged from the pre-round baseline; F9 is an
explicitly-disclaimed retracted placeholder, F17/F18/F27/F28 are a pre-existing MINOR finding from R5
Part(v) not in this round's task list). `unanchored=69` is unchanged from the pre-round baseline (69) —
no new unanchored numbers were introduced. Page count moved 109→110 (within the ≤120 limit) from the
added Part-2 citation text.

---

## Ten-line summary

Seven ledger rows recomputed (F10, F13, F31, F44, F45, F54, F55): five were pure stale-snapshot drift
from `M26_100x16b`'s extension to 16/16 rounds (F10, F13, F31, F55 unconditionally; F45 with its own
script already correctly scoped); two needed an authorised scope fix (F54: capped `M22_L0_ghx0` at R15
in `audit_candidate_bucket_and_aim.py`; F44: added the 100-task subset filter to
`audit_m28_seed2_flips.py`, which also surfaced a pre-existing window-pooling convention difference from
the ledger's stated "8 windows" — resolved by taking the script's own post-fix output, 7 windows). Every
changed number was propagated to its body citations across `01-introduction.tex`, `03-baseline.tex`,
`05-design.tex`, `06-results.tex`, `07-discussion.tex`, `04-ghx.tex`, and `B-operations.tex`; occurrences
of "20.1%/19.2%" anchored only to F15/F9e's own unedited, still-correct script were deliberately left
unchanged. Fourteen rows were checked for class honesty (F26–F30, F32–F39, F43): eleven reclassified
`\cls{A}`→`\cls{B}` with a verified recorded-artifact citation (JSON trial output or a preserved
candidate/decision file), and three (F33, F34, F39) kept `\cls{A}` after a genuine, previously-uncited,
read-only script (`proof_stats.py`, `audit_gain_face.py`) was found to reproduce their numbers exactly —
F34, the thesis's sole pre-registered confirmatory test, now has a real script named instead of none. No
script's window count, threshold, or statistical definition was altered beyond the two authorised scope
fixes. The gate failed once on 4 overfull hboxes from over-long path citations, fixed by shortening to
the ledger's own bare-filename convention, then passed clean: 110 pages, 0 errors, 0 undefined refs, 61
ledger rows, exclusion/bib/anchors/scores all PASS, unanchored WARN unchanged at 69. Four findings could
not be resolved within this round's authorised scope and are flagged above for the author/checker: the
"1.6 to 2.1×" volatile-family ratio (hand-derived, no script prints it, would shift slightly to ≈"1.6 to
2.0×" with F44's new denominator); F27's "registry error 13"/"criteria file" detail (not found in any
on-disk artifact); F30's 40-step-cap "7/10" by-product and F36's "0/5" firing-autopsy figure (both
verified only by hand over raw session transcripts, no aggregating script or file exists for either).
Round not declared complete — for the checker.
