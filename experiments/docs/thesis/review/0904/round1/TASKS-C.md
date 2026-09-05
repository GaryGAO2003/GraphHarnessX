# Round 1 · Maker-C task list (data line: new recompute scripts + new ledger rows)

You add NEW class-[A] facts computed from the six whitelist runs (read-only) with NEW scripts under
`experiments/analysis/`, append NEW ledger rows at the end of `ch/C-ledger.tex` (before the closing of the description
list; number them F57, F58, F59 in this order, same row format as the neighbours: `\item[\textbf{F57}\quad Title.] ...
\emph{Sample:} ... \emph{Class:} \cls{A}, \texttt{script\_name.py}.`), and insert ONE sentence each at the three
designated places below. Touch nothing else. No new runs, no model calls, no writes under recipe/gaia_evolver/runs/.

Read first: `EDITORIAL-DECISION.md` items P1-14, P1-21, P2-12; the ledger rows F15, F9e, F46, F44, F45 in ch/C-ledger.tex;
`experiments/analysis/audit_flip_rate_three_seeds.py`, `audit_same_config_flips.py`, `audit_gain_face.py`
(its per_round() shows the `carried` flag and the 100-task SUBSET), `plot_campaign_scores.py` (RUNS list, M22 capped
at R15). Windows and subsets: R0–R15 only; the common 100-task subset for every cross-arm number; M22 has an R16 that no
reported window uses.

1. **C-01 (P1-14)** `audit_flip_rate_cluster_ci.py`: for the pooled same-configuration flip rate of F15 (the exact
   same windows and pairs the existing script uses — import or copy its window definitions, do not redefine them),
   compute a task-clustered bootstrap 95% interval: resample the 100 tasks with replacement (each task carries all its
   pair outcomes across all windows), 10,000 replicates, fixed seed 20260904, percentile interval; print the point
   estimate, the naive Wilson interval the ledger already states, and the clustered interval, for the pooled rate and
   for each seed. Add row F57 with those numbers. Insert one sentence in ch/05-design.tex around lines 118–128 (the
   paragraph that states the pooled flip rate and its Wilson interval) reporting the clustered interval `\F{57}`.
2. **C-02 (P1-21)** `audit_fresh_carried_plateau.py`: for each campaign and each plateau round R3–R15 on the 100-task
   subset, count fresh vs carried task rows (the `carried` flag, last row wins per (round, task) as in audit_gain_face);
   print per-arm totals and the number of full-batch (100 fresh) vs audit-batch rounds. Add row F58. Insert one caveat
   sentence in ch/06-results.tex next to the "+2.7" plateau-gap statement (around lines 271–272, after the table it
   sits in) stating the fresh/carried composition of the plateau windows in each arm `\F{58}`.
3. **C-03 (P2-12)** `audit_campaign_calendar.py`: first and last timestamps per campaign from task_history.jsonl (find the
   timestamp field; if none exists, use file mtimes of `R*/` directories and say so in the row); print a six-row table
   (campaign, arm, seed, start, end, overlap with which others). Add row F59 (class [A] if from record timestamps, [B]
   if from mtimes). Insert one sentence in ch/B-operations.tex §B.1 (around lines 19–27) stating the calendar order and
   overlaps `\F{59}`.
4. **C-04 (P2-10 Spearman–Brown, optional, only if inputs are on the page)** ch/05 ~186–190 / ch/07 ~312–318 promise a
   repetition-pricing number; if every input is already in the ledger, compute it in a 20-line script
   `audit_spearman_brown.py`, add row F60, and insert the number where promised. If any input is missing, skip and say so.

Rules: scripts are read-only over runs/, deterministic, runnable from the repo root with `python <path>` (add a
sys.path bootstrap if they import harnessx). Each script prints its numbers with the ledger row id in the header line.
Patches with backslashes go through Write-tool Python scripts with assert-once replacements. Private build:
`python D:/PycharmProj/HarnessX/experiments/docs/thesis/review/0904/gate_checks.py --outdir <your scratch dir>/c`.
Write `round1/RESPONSE-C.md`: per item — script path, printed output (verbatim, trimmed), the ledger row text, the
inserted sentence with file:line. Do not run the in-place gate.
