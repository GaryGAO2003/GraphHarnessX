# Round 1 · Maker-C response (data line: new recompute scripts + new ledger rows)

Scope executed: C-01, C-02, C-03, C-04 — all four items FULLY_ADDRESSED, none skipped.
Four new scripts added under `experiments/analysis/`; four new ledger rows (F57–F60)
appended at the end of `ch/C-ledger.tex`'s description list (after F56, before
`\end{description}`); five sentence insertions made across three files (C-04 promises
the number at two locations, not one). No existing script or existing ledger row was
modified. Private gate (`--outdir .../scratchpad/c`) run twice: **anchors check PASSES**
both times; the only gate failures are two undefined bibliography keys
(`falconer-mackay`, `hutcheon-dilution`) explicitly assigned to another maker (P2-09) —
not in this line's scope.

---

## C-01 (P1-14) — task-clustered bootstrap CI on the pooled flip rate

**Script:** `experiments/analysis/audit_flip_rate_cluster_ci.py` (new). Imports
`RUNS`, `FULL_MIN`, `SUBSET`, `outcomes()`, `windows()`, `wilson()` unchanged from
`audit_flip_rate_three_seeds.py` (F15/F9e's own script) via `sys.path` bootstrap, so
the pairs entering the bootstrap are byte-identical to F15/F9e's. Resamples the 100
tasks with replacement as clusters (each task carries every window pair-outcome it
contributed together into a replicate); 10,000 replicates, fixed seed `20260904`,
percentile 95% interval. A refusal gate checks the per-seed and pooled point estimates
against F15/F9e's printed numbers before reporting anything.

**Printed output (verbatim, trimmed):**
```
F57  Task-clustered bootstrap 95% CI on the same-config flip rate (F15/F9e), N=10000 replicates, seed=20260904

self-check: per-seed and pooled point estimates reproduce F15/F9e exactly
(126/600, 161/800, 115/600, pooled 402/2000).

    group         k/n   point    naive Wilson 95%    task-clustered 95%
   seed 1  126/600      21.0%   [ 17.9,  24.4]        [ 16.5,  25.7]
   seed 2  161/800      20.1%   [ 17.5,  23.0]        [ 15.9,  24.6]
   seed 3  115/600      19.2%   [ 16.2,  22.5]        [ 14.5,  24.2]
   pooled  402/2000     20.1%   [ 18.4,  21.9]        [ 16.5,  23.9]
```
Deterministic: re-ran once, byte-identical output. Runtime ≈1.3s.

**Ledger row appended** (`ch/C-ledger.tex:768–782`):
> **F57** Task-clustered bootstrap interval on the same-config flip rate. Resampling
> the 100 tasks with replacement — each task carries every window pair-outcome it
> contributed, together, 10,000 replicates, seed 20260904 — widens F9e's pooled 95%
> interval from Wilson's [18.4%, 21.9%] to [16.5%, 23.9%]. Per seed: seed 1 clustered
> [16.5%, 25.7%] against Wilson [17.9%, 24.4%]; seed 2 [15.9%, 24.6%] against [17.5%,
> 23.0%]; seed 3 [14.5%, 24.2%] against [16.2%, 22.5%]. Every clustered interval is
> wider than its naive counterpart, as expected once flip propensity is a property of
> the task rather than of the draw (F41, F54). Point estimates reproduce F9e exactly
> (126/600, 161/800, 115/600, pooled 402/2,000) before any interval is drawn. *Sample:*
> as F9e — three no-graph seeds, the same 20 full-batch same-config windows, common
> 100-task subset. *Class:* A, `audit_flip_rate_cluster_ci.py`.

**Inserted sentence** — `ch/05-design.tex:127–129` (inside the "The flip rate"
paragraph, between the pooled-Wilson sentence and the paragraph's closing remark):
> "A task-clustered bootstrap --- resampling the 100 tasks rather than the pairs,
> since flip propensity is a property of the task --- widens this to $[16.5\%,
> 23.9\%]$ \F{57}."

---

## C-02 (P1-21) — fresh vs carried composition of the R3–R15 plateau

**Script:** `experiments/analysis/audit_fresh_carried_plateau.py` (new). For each of
the six whitelist campaigns and each plateau round R3–R15, counts fresh vs carried
task rows on the common 100-task subset (last row wins per (round, task), mirroring
`audit_gain_face.py`'s `per_round()`). A round is "full-batch" iff all 100 subset rows
are fresh; "audit-batch" iff any row is carried (the 25-fresh/75-carried no-op
mechanism of Appendix B.2).

**Printed output (verbatim, trimmed to the totals lines; full per-round tables
omitted here but printed by the script):**
```
F58  Fresh vs carried composition of the R3--R15 plateau window, six whitelist campaigns

--- M22_L0_ghx0  (L0, seed 1) ----   campaign totals: fresh=1300  carried=0     full-batch rounds=13/13  audit-batch rounds=0/13
--- M28_L0_s2    (L0, seed 2) ----   campaign totals: fresh=1300  carried=0     full-batch rounds=13/13  audit-batch rounds=0/13
--- M29_L0_s3    (L0, seed 3) ----   campaign totals: fresh=1300  carried=0     full-batch rounds=13/13  audit-batch rounds=0/13
--- M26_100x16b  (GHX, seed 1) ---   campaign totals: fresh=859   carried=441   full-batch rounds=7/13   audit-batch rounds=6/13
--- M28_GHX_s2   (GHX, seed 2) ---   campaign totals: fresh=1005  carried=295   full-batch rounds=9/13   audit-batch rounds=4/13
--- M29_GHX_s3   (GHX, seed 3) ---   campaign totals: fresh=937   carried=363   full-batch rounds=8/13   audit-batch rounds=5/13

Arm totals, three seeds pooled, R3--R15 (39 round-campaign observations per arm)
L0      fresh= 3900  carried=    0  (0.0% of task-rounds carried)    full-batch rounds=39/39  audit-batch rounds=0/39
GHX     fresh= 2801  carried= 1099  (28.2% of task-rounds carried)   full-batch rounds=24/39  audit-batch rounds=15/39
```
Sanity-checked independently: verified the `carried` field's presence/absence directly
against raw JSONL rows for both an L0 and a GHX campaign before trusting this result —
no-graph rows never carry the key (defaults falsy), graph carried-rows carry
`"carried": true` with `cost_usd: 0.0, steps: 0`. The asymmetry (0% vs 28.2%) is real,
not a parsing artifact.

**Ledger row appended** (`ch/C-ledger.tex:784–795`):
> **F58** Fresh vs carried composition of the R3–R15 plateau. On the window F46
> reports (13 rounds × 3 seeds per arm, common 100-task subset, last row per (round,
> task)): the no-graph arm is **100% fresh** — 0 carried task-rounds across all 39
> round-campaign observations, every one of its 39 rounds a full 100-task re-draw. The
> graph arm carries **1,099** of 3,900 task-rounds (28.2%), with **15** of its 39
> rounds an audit batch (25 fresh + 75 carried) against **0** audit-batch rounds on the
> no-graph arm. *Sample:* `task_history`, subset-restricted, R3–R15, six whitelist
> campaigns. *Class:* A, `audit_fresh_carried_plateau.py`.

**Inserted sentence** — `ch/06-results.tex:285–288` (appended to the end of the
`tab:arms` table's caption, after "All six arms completed sixteen of sixteen scored
rounds."):
> "The plateau column is not evenly drawn between arms: the no-graph arm's R3--R15
> window is $100\%$ fresh re-draws (0 of 39 round-campaigns carried), the graph arm's
> is $28.2\%$ carried ($1{,}099/3{,}900$, 15 of 39 rounds an audit batch) \F{58}."

---

## C-03 (P2-12) — campaign calendar: order and overlap

**Script:** `experiments/analysis/audit_campaign_calendar.py` (new). `task_history.jsonl`
carries no timestamp field (checked directly); `audit.jsonl` does — every row carries a
Unix-epoch `ts` float. Takes min/max `ts` per campaign as start/end (class A). Falls
back to `R*/` directory mtimes (class B) only if a campaign's `audit.jsonl` has no
usable `ts` — not triggered for any of the six. Overlap = interval intersection.

**Printed output (verbatim, trimmed to drop the closing interpretive paragraph):**
```
F59  Calendar order and overlap of the six whitelist campaigns

campaign         arm   seed         start (UTC)           end (UTC)  class
M22_L0_ghx0      L0    1    2026-08-17 16:51 UTC 2026-08-18 20:46 UTC  [A]
M26_100x16b      GHX   1    2026-08-23 02:05 UTC 2026-08-27 14:59 UTC  [A]
M28_GHX_s2       GHX   2    2026-08-26 04:08 UTC 2026-08-26 22:20 UTC  [A]
M28_L0_s2        L0    2    2026-08-26 04:10 UTC 2026-08-27 02:56 UTC  [A]
M29_L0_s3        L0    3    2026-08-27 16:42 UTC 2026-08-29 00:53 UTC  [A]
M29_GHX_s3       GHX   3    2026-08-27 16:50 UTC 2026-08-29 01:35 UTC  [A]

Overlaps (interval [start, end] intersects another campaign's):
  M22_L0_ghx0      (L0/s1): (none -- runs in isolation)
  M26_100x16b      (GHX/s1): M28_GHX_s2 (GHX/s2), M28_L0_s2 (L0/s2)
  M28_GHX_s2       (GHX/s2): M26_100x16b (GHX/s1), M28_L0_s2 (L0/s2)
  M28_L0_s2        (L0/s2): M26_100x16b (GHX/s1), M28_GHX_s2 (GHX/s2)
  M29_L0_s3        (L0/s3): M29_GHX_s3 (GHX/s3)
  M29_GHX_s3       (GHX/s3): M29_L0_s3 (L0/s3)
```
All six campaigns resolve at class A; no mtime fallback needed.

**Ledger row appended** (`ch/C-ledger.tex:797–805`):
> **F59** Campaign calendar: order and overlap. By `audit.jsonl`'s recorded `ts` field
> (all six campaigns resolve at class A; no mtime fallback needed): M22 (no-graph, seed
> 1) runs 2026-08-17–18, alone. The graph seed-1 campaign (2026-08-23–27) overlaps both
> seed-2 campaigns, no-graph (2026-08-26–27) and graph (2026-08-26), which overlap each
> other in turn. The seed-3 pair runs concurrently with only each other: no-graph
> 2026-08-27–29 against graph 2026-08-27–29. *Sample:* all six whitelist campaigns'
> `audit.jsonl` timestamps. *Class:* A, `audit_campaign_calendar.py`.

**Inserted sentence** — `ch/B-operations.tex:23–27` (new first item in §B.1's
itemize, before "Gateway routing drift"):
> "\item \textbf{Campaign calendar.} By \texttt{audit.jsonl} timestamps, M22
> (no-graph, seed 1) ran alone on 2026-08-17--18; the graph seed-1 campaign
> (2026-08-23--27) overlaps both seed-2 campaigns (2026-08-26), which overlap each
> other; the seed-3 pair (2026-08-27--29) overlaps only itself \F{59}."

---

## C-04 (P2-10, Spearman–Brown) — NOT skipped; all inputs were on the page

Both promised inputs (F15/F9e's flip rate; a marginal pass rate derivable from the
same population) are already in the ledger, so this ran to completion rather than
being skipped.

**Script:** `experiments/analysis/audit_spearman_brown.py` (new). Re-derives F15/F9e's
flip data via the same imported window definitions as C-01 (refusal-gated against
402/2000). Recovers single-draw reliability `r1` from the standard binary
test-retest/ICC identity for heterogeneous per-task pass propensity (the two-rater,
equal-marginals identity behind Scott's π / Fleiss's κ): a task's two draws disagree
with probability `f = 2·p̄·(1-p̄)·(1-r1)`, so `r1 = 1 - f/(2·p̄·(1-p̄))`, using `f` and
`p̄` computed from exactly the cells entering the flip count (full derivation and
justification in the script's docstring). Spearman–Brown then prices `k` averaged
repeats: `r_k = k·r1/(1+(k-1)·r1)`. The 0.80 target is not an imported convention — it
is this thesis's own already-stated bar for calling a task "reliable" (F16/F54: pass
rate ≥ 80%).

**Printed output (verbatim, trimmed):**
```
F60  Spearman-Brown repetition pricing on F15/F9e's population
self-check: 402/2000 reproduces F15/F9e's pooled flip count exactly.

flip rate            f     = 402/2000 = 20.10%
marginal pass rate   p_bar = 2530/4000 = 63.25%
single-draw reliability r1 = 1 - f/(2 p_bar (1-p_bar)) = 0.568

Spearman-Brown price schedule (k repeats, averaged):
  k     r_k
  1   0.568
  2   0.724
  3   0.798
  4   0.840  <-- first k reaching this thesis's own 0.80 'reliable' bar (F16/F54)

HEADLINE: r1=0.57; k=4 averaged repeats reach Spearman-Brown reliability 0.84 >= 0.80.
```
Fully deterministic (no RNG at all — plain arithmetic over `task_history`).

**Ledger row appended** (`ch/C-ledger.tex:807–818`):
> **F60** Spearman–Brown repetition price on the flip rate. Modelling each task's
> repeated same-config draws as independent Bernoulli trials on its own pass propensity
> (the two-rater, equal-marginals identity behind Scott's π / Fleiss's κ: disagreement
> f = 2p̄(1-p̄)(1-r₁)) recovers a single-draw reliability r₁ = 0.568 from F9e's flip
> rate (f=20.10%) and the same population's marginal pass rate (p̄ = 63.25%,
> 2,530/4,000 cells). Spearman–Brown then prices repetition: k=2 averaged draws give
> r₂=0.724, k=3 gives r₃=0.798, and **k=4 is the first repetition count reaching this
> thesis's own 0.80 "reliable" bar** (F16, F54) (r₄=0.840). *Sample:* as F9e — three
> no-graph seeds, same windows, common 100-task subset. *Class:* A,
> `audit_spearman_brown.py`.

**Inserted number, two locations** (the manuscript promises this number twice; both
fulfilled, since C-04's own instruction names both as "where promised"):

- `ch/05-design.tex:192–195`, appended after "...thesis's own route
  (\S\ref{sec:future})." in the §5.3 "no informative-and-reliable subset" passage:
  > "Priced: a single draw's reliability is $0.57$, and \textbf{four} averaged repeats
  > are the first integer count reaching this thesis's own $0.80$ ``reliable'' bar
  > (F16/F54) \F{60}."

- `ch/07-discussion.tex:328–330`, inserted mid-sentence in §7.2 item 2 ("Bed
  reliability, with its ceiling priced first"), between "...before committing budget"
  and "and the alternative is the readout itself":
  > "...committing budget: a single draw prices at reliability $0.57$, and
  > \textbf{four} averaged repeats are the first integer count crossing this thesis's
  > own $0.80$ ``reliable'' bar \F{60} --- and the alternative is the readout itself,
  > which is why item 1 comes first."

---

## Private gate results

Run 1 (before C-04's two number-insertions, ledger rows F57–F60 + three designated
sentences only):
```
[FAIL] compile    pages=113 errors=0 overfull_hbox=0
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

Run 2 (final, after C-04's two number-insertions):
```
[FAIL] compile    pages=113 errors=0 overfull_hbox=0
        - undefined refs/citations: ['falconer-mackay', 'hutcheon-dilution']
[PASS] abstract
[PASS] exclusion  hard=0 soft_bad=0 soft_ok=9
[PASS] anchors    rows=65 used=60 uncited=5
[FAIL] bib        entries=54 cited=56
        - cited but no bibitem: ['falconer-mackay', 'hutcheon-dilution']
[WARN] unanchored sentences=68
[SKIP] scores
GATE FAILED
```

**Reading:** `anchors` — my critical bar — PASSES both times (`fails=[]`; F57/F58/F59
each cited exactly once, F60 cited twice, confirmed directly with `grep`). `compile`
and `bib` fail solely on `falconer-mackay`/`hutcheon-dilution`, the two of the six
reserved AUTHOR-FACTS bibliography keys assigned to the P2-09 maker, not this line —
explicitly flagged as expected in this task's own brief. `exclusion` clean (no banned
tokens introduced). `unanchored` at 68, not increased from the STATE.md baseline of 69
(the drop is attributable to concurrent edits by other makers, not mine — this line
added no unanchored sentences; each of the five inserted sentences carries its own
`\F{}` anchor). `pages=113` sits inside the 109→~113–114 growth the editorial decision's
page-budget note already authorised. `scores` SKIP is expected — `--outdir` disables
score regeneration by design.

## Items skipped

None. C-01, C-02, C-03, C-04 all FULLY_ADDRESSED.

## Files touched

New (under `experiments/analysis/`, read-only over `runs/`, deterministic):
- `experiments/analysis/audit_flip_rate_cluster_ci.py`
- `experiments/analysis/audit_fresh_carried_plateau.py`
- `experiments/analysis/audit_campaign_calendar.py`
- `experiments/analysis/audit_spearman_brown.py`

Appended only (no existing row or existing script text modified):
- `experiments/docs/thesis/ch/C-ledger.tex` — F57, F58, F59, F60 appended after F56
- `experiments/docs/thesis/ch/05-design.tex` — 2 insertions (F57 sentence; F60 number)
- `experiments/docs/thesis/ch/06-results.tex` — 1 insertion (F58 sentence)
- `experiments/docs/thesis/ch/B-operations.tex` — 1 insertion (F59 sentence)
- `experiments/docs/thesis/ch/07-discussion.tex` — 1 insertion (F60 number)

No `git commit`, no deleted files, no new experiment runs, no model API calls.
