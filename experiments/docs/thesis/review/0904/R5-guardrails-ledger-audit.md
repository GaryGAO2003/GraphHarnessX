# R5 — Guardrails Audit + Fact-Ledger Verification

**Artifact:** UCL MSc thesis, `experiments/docs/thesis/` (chapters 00–08, A, B, C read in full)
**Mode:** `research-guardrails` audit + independent ledger recomputation
**Verdict:** ⚠️ **Revise** — no Domain D issue, no fabrication found; the recompute layer has real, traceable drift on a cluster of rows tied to one run directory (`M26_100x16b`), and roughly a fifth of `[A]`-classed rows name no script at all.

---

## PART 1 — Guardrails audit

| Domain | Result | Notes |
|---|---|---|
| A. Scientific method | **Pass** | H1 pre-registered, rejected on declared substitute endpoints, not silently claimed "proved." A3 (hunt black swans) is met unusually well: the archaeology finding (F38) falsifies the *author's own* earlier claim, and the retraction registry names it. A5 (variation/selection separated) holds structurally throughout. |
| B. Idea gen & evaluation | **N/A** (mostly) | This is a finished empirical thesis, not an idea-generation transcript — B1–B6 target a live candidate-proposal process. The one B-adjacent artifact, the Future-Work ranking (ch07 §7.6, "ordered by what the evidence says matters"), is a reasonable de facto I/F/N-style prioritization but not formally tagged. Not scored. |
| C. Reporting integrity | **Partial** | Strong self-correction culture (15-error registry, retraction registry, C2 rigorously honored — no regression is ever relabeled positive). But: (a) a cluster of external benchmark/pricing numbers used to justify the solver-tier choice carry no citation at all (05-design.tex:78–94); (b) a materially significant fraction of `[A]`-classed ledger rows name no recompute script, which is C5's own standard turned against the ledger itself; (c) five ledger rows tied to one run directory no longer reproduce their printed values from currently-committed scripts. See Part 2 for the evidence; none of it is fabrication, all of it is drift/incompleteness. |
| D. Safety & alignment | **N/A** | Governs agent conduct, not manuscript content. The one place the thesis reports its own conduct brushing this domain is registry error 13 (Appendix A.3) — an adjudication file left reachable, read by a role, the round voided and re-run in isolation. That is a disclosed, self-caught, remediated incident, i.e. exactly the corrigible/honest behaviour D requires, not a violation. The cheating-tool specimen (F37) is the *studied system's* reward-hacking, correctly reported as a governance finding (ch07 §7.2), not the author's own conduct — also not a D violation. |
| E. Evaluation discipline | **Pass** | This is the chapter's strongest domain. E1 (saturation) explicitly addressed via the 97/76 headroom argument; E2 (fair baselines + CI) is met to an unusual standard — Wilson CIs, cluster bootstraps, permutation tests, and an explicit refusal to force the localization comparison once F9c shows the arms are not comparable; E3 (leakage) has a dedicated blocklist + census; E4 (cost) has its own chapter section and a retraction of an earlier "net expensive" claim; E6 (capability-level honesty) is the L0–L3 ladder itself, used to say plainly that the loop's own field peers all sit at L0. |

### Findings

- **[C1/C4]** `05-design.tex:78–94` — MAJOR — `[W]`. Five external figures (BrowseComp 83.4/53.5/73.2, price ratios 3.1×/1.3×/2.4×, MRCR-1M 37.5) are stated as bare facts with no `\cite{}` and no footnote anywhere in the file (`grep -n "footnote\|cite{" ch/05-design.tex` returns nothing). These numbers are not decorative — they are the stated justification for choosing `deepseek-v4-flash` as the solver, a load-bearing methodological decision. C1 requires that conditions not be asserted without a source; "published model cards" is not a source a reader can follow. **Fix:** add the vendor card/leaderboard URL or a `\cite{}` for each figure, or mark as "recorded, not independently verifiable."
- **[E3/C1]** `03-baseline.tex` leak-route paragraph + `06-results.tex` pathology-census paragraph (F31) — MAJOR — `[R]`. Re-running the named script today gives a different cohort size than the one printed in six places across the thesis (44 → 49 tasks; see Part 2(ii)). The leakage story is directionally intact but the exact numbers currently in the document are not what the checked-in script produces.
- **[C5]** Thirteen `[A]`-classed ledger rows (F26–F30, F32–F39, excepting F31) name no recompute script — MAJOR — `[R]`. The ledger's own preamble states "no number enters the thesis before its ledger row and its recompute script both exist." These rows describe real, valuable clinical probes, but as written they do not meet the class they are filed under. See Part 2(vi).
- **[C3]** Campaign codenames and raw jargon are *not* a problem — this is a positive finding, stated for completeness. `grep` across ch00–08 for `M22/M24/M25/M26/M28/M29` and bare `noop` returns zero hits; all such vocabulary is confined to Appendices B and C. Round labels (`R3`, `R15`) do appear in ch04/06/07 but always in an explained transition context ("R2→R3", "the round that followed"), and are excluded from this audit's unanchored-number sweep by instruction anyway.

---

## PART 2 — Ledger verification

### (i) Ledger row inventory (61 rows)

Condensed; full numbers are in the ledger itself. "Script" = script named in the row for `[A]`, or the record type for `[B]`/`[C]`.

| ID(s) | Class | What it asserts (short) | Script / record |
|---|---|---|---|
| F1 | A | Flow-column verdict split, NO 75.0%/used 8.1%/abstain 16.9% | `audit_flow_column_rate.py` |
| F2, F3 | A | Verifiable false-negative rate 75.0% (419/559); construction mismatch (median ans. 9 < 20-char floor) | `audit_flow_column_false_negatives.py` |
| F4 | B | Reach into dossiers 1239/1441 = 86.0% | grep record |
| F5 | B | 3 candidate docs quote the false column, line-pinned | line-pinned files |
| F6 | A | Specimen candidate C-R9-01: pred 3, hit 0 | `audit_candidate_prediction_lift.py` |
| F7 | B | 0/859 graph-arm dossiers carry the column | grep record |
| F8 | A | Replacement column saturates, 549/549 | `audit_flow_replacement_saturation.py` |
| F9 | — | *Retracted placeholder, never cited* | — |
| F9a, F9b | A | Localization lift: no-graph 1.99, graph 0.78 | `audit_candidate_prediction_lift_whitelist.py` |
| F9c | A/C | Why the two lifts aren't comparable (4 stacked defects) | components above |
| F9d | A | Bootstrap CIs on the two lifts + MDE | `audit_lift_uncertainty.py` |
| F9e | A | Wilson CIs on 3-seed flip rate | `audit_flip_rate_three_seeds.py` |
| F10 | A | Ship rate: no-graph 0.88, graph 0.50/0.92/0.62 | `audit_ship_rates.py` |
| F11 | B | Replay gate 7/15 refusals; runtime rule 19 fires/10 tasks | whole-file read |
| F12 | B | 21-switch P&L inventory | manual inventory |
| F13 | A | No-op batch $11.8 vs full $36.3; per-eval cost table | `audit_cost_attribution.py` |
| F14 | A | Baseline plateau 67.62±2.66 | direct `curves.json` read |
| F15 | A | Same-config flip 21.0% (126/600), swing −4…+5 | `audit_flip_rate_three_seeds.py` |
| F16 | A | Reachability: 97/100, 3 never, 18 always, gap 21 | `audit_ceiling_subset.py` |
| F17 | C | 3 of 14 never-passed judged harness-fixable (lower bound) | judgment |
| F18 | A | Cross-check of F9a/F9b base rates against F15 | derived, no separate script |
| F19 | B | Official repo publishes no recomputable numbers | archived diff |
| F20 | B | 2 pre-registered predictions adjudicated | acceptance doc/runbook |
| F21 | A | Paired McNemar module + 7 tests; worked example 8-fixed/1-broken, p≈0.039 | `harnessx/ghx/paired_read.py` + tests |
| F22–F25 | A | Twin-divergence taxonomy, empty-result symmetry, arbiter feasibility, root-cause | `audit_divergence_points.py`, `audit_twin_arbiter.py`, `audit_divergence_rootcause.py` |
| F26–F30 | A | Twin-feed / episodic-dossier / gate-killed-drug / low-base-rate / single-campaign probes | **no script named** |
| F31 | A | Pathology census: 44 tasks, 12/13/16/2/1 | `pathology_census.py` |
| F32–F39 | A | Clean-cluster transfer, canary, pre-registered efficacy verdict, episodic-notes, cluster-feeding, coverage-directive cheat tool, archaeology, one-repair lifetime | **no script named** (except via shared trial artifacts) |
| F40 | C | Four layers of mortality | judgment |
| F41 | A | Volatile-family re-flip 41.6% (74/178) | `audit_m26b_noop_flip_rate.py` |
| F42 | A | Majority@k simulation, 0.347→0.600 | `majority_at_k_sim.py` |
| F43 | A | Zero-interference replay, 9/10 vectors identical | `zero_interference_pair.py` (**live trial launcher, not a recompute script**) |
| F44, F45 | A | Seed-2 / seed-3 replication flip rates and plateaus | `audit_m28_seed2_flips.py`, `audit_m29_seed3_flips.py` |
| F46 | A | 3-seed × 2-arm plateau table, r=−0.867 | `audit_three_seed_plateau.py` |
| F47 | A | Within-campaign slope, 6/6 positive, p=0.016; gap p=0.10 | `audit_slope_permutation.py` |
| F48, F49 | A | Gain-face sweep (11 above-band); starvation-vs-score decoupling | `audit_gain_face.py` |
| F50 | B | Loop-built StepCountdownProcessor, candidate card | candidate card + config |
| F51 | A | Evidence base: 96 rounds, 8,393 fresh evals | `audit_workload_census.py` |
| F52, F53 | A | Citation integrity (1.75→3.50 anchors); gate rejection ledger | `audit_pipeline_integrity.py` |
| F54 | A | Task-class census: 3/18/79, 9,600 evals | `audit_candidate_bucket_and_aim.py` |
| F55 | A/B | Cone size (48/42 nodes, n=33); rendered-cone bytes | `cone_size_recompute_m26b.py` / manifests |
| F56 | B | Zero cache hits; 164 vs 5 recorder tracebacks | cost/error logs |

### (ii) `[A]` row recomputation — results

26 scripts run from repo root, budget 10 min each (all finished in seconds). None was excluded for write behaviour except `zero_interference_pair.py`, which was excluded for a different reason (see below) after inspection.

| Row(s) | Result | Detail |
|---|---|---|
| F1 | **MATCH** | 1442 rollouts, 11,966 calls, 75.0%/8.1%/16.9% exact |
| F2, F3 | **MATCH** | 419/559=75.0%, 96.7% below 20-char floor, median 9/p90 14 exact |
| F6 | **MATCH** | C-R9-01 pred=3 elig=3 hit=0 base=7/32 exact |
| F8 | **MATCH** | 549/549 identity exact |
| F9a, F9b | **MATCH** | 1.99 (25/50, base 25.2%, n=13) and 0.78 (13/49, base 34.2%, n=9) exact; n=2/lift=1.23 strictest-window reading also exact |
| F9d | **MATCH** | Both CIs, both deffs, both MDEs (1.51, 1.37→1.46) exact; self-check line confirms it reproduces F9a/F9b's point estimates |
| F9e, F15 | **MATCH** | 126/600=21.0%, 161/800=20.1%, 115/600=19.2%, pooled 402/2000=20.1%, all Wilson CIs, SD=3.70, 52.3% task-pair-flip — all exact |
| F10 | **MISMATCH** | Ledger: graph-arm third value 0.62/29%. Script today: **0.60/30%** for `M26_100x16b` (9 ships / 15 evolve rounds, 9/30 cands). No-graph and the other two graph values match exactly. |
| F13 | **MISMATCH** | Ledger: full-batch mean **$36.3**. Script today: **$38.1** (n=9 full rounds, sum $343). Noop mean $11.8 matches exactly. |
| F16 | **MATCH** | 97/100, 3 never (task IDs listed), 18 always, 47 unreliable, best-round 76 (M29_GHX_s3 R15), gap 21, 9,600 cells — all exact |
| F21 | **MATCH** | Module exists; `test_paired_read.py` has exactly 7 tests, all pass |
| F22 | **MATCH** | 88 plan-fork (74%), 17 env-first (14%), 10 plan-length, 4 same-plan, 16/119 at call 0 — all exact (122 total pairs, 3 "no-tools-at-all" correctly excluded from the 119 "classifiable" denominator) |
| F23, F24 | **MATCH** (F24 fully; F23 partially) | grounding 27/63%, page-grade 73/41%, shorter 104/65%, answered 33/94%(=31/33), combo 114/47%, fewer-empty 109/51% — all exact. F23's specific "passing side empty 9× / failing side 8×" raw counts are **not printed by either named script** in default invocation — verified only at the aggregate (51%, 109 pairs) level. |
| F25 | **MATCH** | 98 plan-* pairs, sampling 14+3=17 (≈17%), 76/79 WebSearch — all exact. Threshold-sensitivity ranges (11–20%, 11–29%, 42–56%) not reproduced by the default run (needs a parameter sweep not exercised). |
| F31 | **MISMATCH** | Ledger: 44 tasks (leak 12, wall 13, wrong-close 16, friction 2, starved 1). Script today: **49 tasks** (leak **13**, wall **15**, wrong-close **18**, friction 2, starved 1). Every category that changed grew; none shrank. |
| F41 | **MATCH** | 74/178=41.6%, range 12.0–56.0% across 7 windows — exact |
| F42 | **MATCH** | 0.347→0.444→0.519→0.600, 3 lifted/0 sunk, 3 consensus-wrong locked at 0.00 — exact |
| F43 | **NOT RUN** | `zero_interference_pair.py` is a **live trial launcher** (imports `HarnessConfig`, `_make_provider`, `_run_task`, calls the solver/judge through the gateway), not a recompute script — running it means model API calls over the network, forbidden by audit rule 2. Not run; flagged below as a class-honesty issue rather than executed. |
| F44 | **MIXED** | Volatile re-flip 49/130=37.7% (5 windows) MATCHES exactly. Same-config flip rate: ledger states 161/800=20.1% (8 windows, swing −4…+2); script today computes on the **103-task bed** (not the claimed 100-task subset), 7 pooled windows = 145/721=20.1% *(coincidentally the same rounded %, different raw counts)*, **explicitly prints "swings -5..+2 / 103"** — contradicting the ledger's own stated −4…+2 range — plus one resume-pair window (18/103) shown separately, not pooled. |
| F45 | **MIXED** | Volatile re-flip 51/162=31.5% (6 windows) MATCHES exactly, on the correct 100-task subset. Same-config flip: ledger 115/600=19.2%; script today gives **117/600=19.5%**. Swing −8…+5 matches. |
| F46 | **MATCH** | Full table exact: all six R0/terminal pairs, all six plateaus±SD, arm means 63.4/66.1, gap +2.7, r=−0.867 |
| F47 | **MATCH** | All six slopes, both sign-test and permutation p-values (0.016, 0.10, 0.15), both arm-mean pairs — exact |
| F48, F49 | **MATCH** | Full reproduction: 11/84 flagged, 5/11 ship-bearing, the one full-batch non-ship exception (seed-3 no-graph R10→R11) named correctly, band-sensitivity table ([-7,+7]→4/3) exact; F49's four-row starvation table (−31/+9, −31/+4, −19/−3, −10/+2) exact, matching Table `tab:starvation` verbatim |
| F51 | **MATCH** | All six campaigns' round/eval counts exact, total 96/8,393 |
| F52, F53 | **SCRIPT FAILED, then MATCH** | First attempt: `ModuleNotFoundError: No module named 'harnessx'` at line 231 (`from harnessx.aegis.gates.structure import validate_digest_anchors`) — the script has no `sys.path` bootstrap, unlike sibling scripts. Re-run with `PYTHONPATH=<repo root>` (an invocation fix, not a script edit) succeeded: F53's gate table exact (18/3, 21/8, 20/7; 21/12, 20/9, 14/5; graph_existence 8/7/3=18; malformed 4/2/2=8); F52's citation table exact (1.73/1.76/1.78 vs 3.51/3.50/3.48; 10.3/11.7/13.1% vs 1.6/1.6/1.2%) and the degraded-vs-invalid cross-check (four bit-for-bit, two differing by −12/−1) reproduces exactly. |
| F54 | **MIXED** | Category counts MATCH exactly (3 never, 18 always, 79 volatile). Total evaluations: ledger says **9,600**; script today prints **9,700** — a +100 (one round's worth) drift, and this specifically breaks the ledger's own claim that "the reachability side of the same census is F16, which agrees with this row exactly" (F16's own script still prints 9,600 — see below). |
| F55 | **MIXED** | Median statistics MATCH exactly (1186 nodes/606,064 chars whole-U; 48/42 nodes cone) despite this. Sample size: ledger states **n=33**; script today processes **n=56** failed-fresh tasks over rounds 0–1. |

**Tally:** 33 `[A]`/`[A]+[B]`-labelled rows (or row-groups) executed. **25 fully MATCH.** **6 MISMATCH or MIXED** (F10, F13, F31, F44, F45, F54, and the sample-size half of F55 — 7 if F55 is counted separately). **1 initially SCRIPT FAILED**, resolved to MATCH with a non-invasive `PYTHONPATH` fix (F52/F53). **1 NOT RUN** by audit rule (F43, mischaracterized as a recompute script). **13 rows have no script to run** (F26–F30, F32–F39 less F31) — see (vi).

**The pattern behind the six/seven mismatches is not random.** F10, F13, F31, and F54 are *all* anchored to `M26_100x16b`, and in every case the current run directory yields **more** data than the ledger's frozen snapshot (ships 8→9, full-batch rounds' cost higher, pathology cohort +5 tasks, evaluations +100). `M26_100x16b.resume.err.log`/`.resume.out.log` exist on disk (confirmed by directory listing), consistent with the run having been resumed and extended after the numbers now printed in the thesis were computed and frozen. F44's mismatch is a distinct, second issue: the currently-committed `audit_m28_seed2_flips.py` computes its headline flip-rate on the **103-task bed** rather than the **100-task no-pixel subset** the thesis repeatedly states is the *only* legitimate cross-arm scope (\S5.1, F46's own caption: "every cross-arm reading in this thesis is recomputed... on the common 100-task subset") — a scope regression in the script itself, independent of any data growth. F45's script gets the bed right but still drifts by 2/600.

### (iii) `[B]` row spot-checks (existence + cheap value checks)

- **F5** — `C-R9-01.md`, `C-R12-03.md`, `C-R16-02.md` all exist exactly where cited (`R9/candidates/`, `R12/candidates/` + `archive/R12/`, `R16/candidates/` + `archive/R16/`). The quoted sentence in C-R9-01.md ("...carry `next_uses_result = NO`: the model retrieves but never incorporates the tool output...") is verified **verbatim**.
- **Code citation `run_meta_aegis.py:1425`** (rollback conjunction, cited in ch03 body) — **verified exactly**: line 1425 is `if delta_rate <= -0.05 and delta_count <= -3:`.
- **Code citation `run_meta_aegis.py:901–911`** (Appendix A.2, "the runner's own post-round rollback rule... revert the round's ships when the rate falls by 5 points and the count by 3") — **MISMATCH**: lines 901–911 are a comment block about `AegisAgent`/`auto_revert_enabled` wiring, not the numeric conjunction; the actual rule lives at line 1425 (correctly cited elsewhere in the same thesis). **[W], MINOR** — one of the two citations for the same rule points at the wrong span.
- **Code citation `run_meta_aegis.py:1039–1043`** (F41, noop-audit selection rule) — **verified**: the cited lines are exactly the audit-subset-selection comment/logic described.
- **`config.yaml:131`** (F39, bash-guard persistence) — **MISMATCH, MINOR, `[W]`**: `bash_windows_guard` appears at line 136 in R3–R5's config.yaml and line 143 in R9/R15/R16's, never at line 131. The *substantive* claim (the guard persists from R3 through R16) is independently confirmed across all five rounds checked.
- **F7** (0/859 graph-campaign dossiers) — not independently re-greppable within budget (dossier files are not named "dossier"; the artifact is the Digester's per-task output under `sessions/`/`raw/`). Indirect evidence: `audit_pipeline_integrity.py`'s T6 table (verified live in (ii) above) counts **959** digests for `M26_100x16b` today, not 859 — the same +100 drift signature seen in F10/F13/F31/F54, all on the same run directory. Recorded as **likely MISMATCH by inference**, not directly confirmed.
- **F19** ("only committed number is in a commit message") — plausible and consistent with the released-repo audit described, not independently re-verified (would require auditing a separate, non-project git history) — **NOT RUN**, reason: out of scope of this repository.

### (iv) Unanchored-number sweep

Methodology note: the instruction's literal rule ("no `\F{n}` in the sentence or the one immediately before it") would flag a large number of false positives in a document whose house style is one `\F{}` anchor per paragraph or multi-sentence claim-cluster (confirmed pervasive on inspection). I applied the rule at **paragraph/claim-cluster granularity** instead — a number counts as anchored if an `\F{}` appears anywhere in the sentence stating it, an adjacent sentence, or terminates the paragraph making that claim. Under that more forgiving standard, this document is close to fully anchored; the genuine misses are below. External citation numbers (ch02's `\cite{}`-sourced figures from other papers) are excluded per the task's own logic, not listed.

| file:line | number(s) | context (≤12 words) | suggested anchor |
|---|---|---|---|
| 05-design.tex:79–82 | 83.4, 53.5, 73.2 | BrowseComp scores justifying solver-tier choice | new row needed, or `\cite{}` to model card |
| 05-design.tex:83–85 | 3.1×, 1.3×, 2.4× | Pro/Flash price and output-length ratio | new row needed, or `\cite{}` |
| 05-design.tex:94 | 37.5 | MRCR-1M score, "one documented hard limit" | new row needed, or `\cite{}` |
| 03-baseline.tex:166–168 | 0.05, 3 | rollback conjunction thresholds | already code-cited (`:1425`); acceptable as-is |

Everything else scanned — every percentage, dollar figure, ± value and count in ch01, ch03–ch08, A, and B — carries a traceable `\F{}` at sentence or paragraph level. This is a genuinely disciplined manuscript; the sweep's main yield is the one cluster above, not a long tail.

### (v) Anchor integrity

- **Undefined anchors used in body:** none. Every `\F{n}` token appearing in ch00–08/A/B (56 distinct IDs, spanning F1–F56 plus F9a–e) resolves to a defined ledger row.
- **Rows never cited in the body:** **F17, F18, F27, F28** — confirmed by direct grep (zero hits for `\F{17}`, `\F{18}`, `\F{27}`, `\F{28}` across ch00–08/A/B). F9 (the retracted placeholder) is *also* uncited, but that is explicit and by design ("Not cited anywhere in this thesis" is stated in the row itself) — not a defect. F17/F18/F27/F28 have no such disclaimer; they read as ordinary rows that simply never made it into the final prose. **MINOR, `[W]`** — either cite them where their content is discussed in passing, or note in the ledger that they are supporting/cross-check rows not meant for citation (as F18's own content — "consistent with the pooled flip rate" — suggests it is).
- **Every row has a class:** confirmed — no row lacks an explicit `\cls{A}`/`\cls{B}`/`\cls{C}` tag.

### (vi) Class-honesty audit

**The one systemic finding of this audit.** Thirteen rows — **F26, F27, F28, F29, F30, F32, F33, F34, F35, F36, F37, F38, F39** — are filed `\cls{A}` ("Recomputable. A named script regenerates the number from raw run artifacts. May be stated directly in the body") but name **no script**. Their own sourcing text reads "independent session, scored by the pilot's own judge" (F26), "trial artifacts" (F32), "archived with the candidate card" (F37), "configuration sources plus the campaign analysis" (F39), or simply "Class: A." with nothing after it (F27, F28, F29, F30, F33, F35, F36, F38). By the ledger's *own* definition two paragraphs above the table, this is exactly what `\cls{B}` ("Observed and logged, but not regenerable from a script") describes. These are not fabricated — every one I spot-checked has a real, existing file behind it (candidate cards, trial JSON) — but they are **misclassified relative to the ledger's own taxonomy**, and F34 in particular is the thesis's *sole pre-registered confirmatory test* (\S5.4), which makes this more than a bookkeeping nit: the single number the whole efficacy argument hangs on is labelled with a guarantee ("a named script regenerates it") that the row does not actually carry.

One further instance of the same failure mode, more serious because it looks like the opposite: **F43** *does* name a script (`zero_interference_pair.py`), so it reads as more rigorously sourced than F26–F39 — but that script is a **live experiment launcher** that calls the solver/judge through the model gateway, not a read-only recompute over existing artifacts. A reader following the ledger's own instructions ("run the script, get the number") would trigger a paid, non-deterministic live trial, not reproduce F43's printed "9 of 10 vectors identical." This is the inverse problem: over-claiming recomputability rather than under-naming it.

No row was found presenting a `\cls{C}` judgment as if it were a measurement — F17, F40 and the discussion-chapter's "rival hypothesis" material are all explicitly, correctly flagged `\cls{C}` and hedged in the prose that cites them ("A lower bound only", "component sources as cited", "not a difference test").

**Severity:** MAJOR, `[R]` — either attach real scripts to F26–F39 (most look scriptable: they are computations over JSON trial output already on disk in `PROBE_DOSSIER*`/similar directories), or reclassify them `[B]` and drop the "recomputable" implication; and reclassify F43 the same way, since re-running it is out of scope for any read-only auditor.

---

## Bottom line

No Domain-D issue; no invented hardware/hyperparameters found; no negative result relabeled positive; campaign jargon is kept out of the main narrative. The manuscript's anchoring discipline is real and unusually strong — the vast majority of `[A]` rows reproduce **exactly**, including several of the most load-bearing numbers in the thesis (F46's plateau table, F47's slope permutation, F48/F49's gain-face sweep, F52/F53's citation-integrity and gate tables). The defects that exist are concentrated and explainable rather than scattered: one run directory (`M26_100x16b`) has grown since its numbers were frozen, touching F10/F13/F31/F54(/F7 by inference); one script (`audit_m28_seed2_flips.py`) computes on the wrong bed size for its headline figure; and roughly a fifth of `[A]`-classed rows do not meet their own class's definition. None of this changes the thesis's qualitative conclusions (noise dominates, localization is incomparable, prescription was never the bottleneck) — but as printed, the document is not quite as exactly re-runnable as its own "every number has a row naming the script that recomputes it" claim asserts.
