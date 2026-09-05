# RESPONSE-A2 — Maker-A2 (F15 vs F44/F45 flip-rate reconciliation), round 1

Ruling applied: F15/F9e is the pre-registered, pooled instrument the body reads. Its
per-seed columns (21.0 / 20.1 / 19.2 %) are the only per-seed same-configuration flip
rates the body may state. F44 and F45 are seed-level re-derivations that corroborate the
noise geometry; their ledger rows now say in one added clause how and why they differ
from F15's columns, and the body no longer quotes them as "the" seed rate.

---

## Part 1 — Diagnosis (read-only; scripts unmodified; no writes under `recipe/`)

Ran, unmodified, from the repo root:
`python experiments/analysis/audit_flip_rate_three_seeds.py` (F15/F9e),
`python experiments/analysis/audit_m28_seed2_flips.py` (F44),
`python experiments/analysis/audit_m29_seed3_flips.py` (F45).
All three finished in well under a second. A fourth, throwaway diagnostic script
(`scratchpad/diag_seed3.py`) imported `audit_flip_rate_three_seeds` as a module (no edits
to it) and read `config.yaml`/`curves.json`/`scoreboard.json` directly under
`recipe/gaia_evolver/runs/M29_L0_s3/` to resolve the seed-3 window-membership question;
nothing was written to any run directory.

### 1a. Seed 2 — why F15 pools 8 windows and F44 pools 7

F15's window list for `M28_L0_s2`: **R2-R3, R3-R4, R5-R6, R7-R8, R8-R9, R10-R11, R11-R12,
R13-R14** — flips 20, 24, 20, 15, 24, 22, **18**, 18 → 161/800 (8 windows).

F44's own pooled loop (rounds whose `curves.json` `evolve_status` reads `"noop"`):
**R2-R3, R3-R4, R5-R6, R7-R8, R8-R9, R10-R11, R13-R14** — flips 20, 24, 20, 15, 24, 22, 18
→ 143/700 (7 windows) — then, printed separately: *"documented resume pair (R11,R12), NOT
pooled: flips 18/100 = 18.0% swing +2"*.

The seven shared windows are flip-for-flip identical between the two scripts, and F15's
eighth window is numerically identical to F44's separately-reported figure (18/100, swing
+2). **The two scripts agree on every number; they disagree only on whether to pool
(R11,R12).** F15's `windows()` selects a pair as same-config purely structurally — the two
rounds' `config.yaml` texts are semantically equal (after neutralising the per-round
`base_dir:` line) and the later round did not ship — with no concept of *why* the configs
match. R12's config is byte-identical to R11's because an 08-26 machine reboot killed the
R11→R12 evolve stage and the operator resumed with `--start-round`, carrying R11's config
forward; F15 cannot tell that from an organic no-op round, so it pools it as window 8.
F44 instead pools only rounds whose `curves.json` `evolve_status` reads `"noop"`; R12's
status was force-written to `"ok"` by that `--start-round` resume (per the script's own
docstring and `runs/M28_L0_s2/INDEX.md`), so F44's main loop skips it and the script
prints it separately as a documented, deliberately-unpooled point.

### 1b. Seed 3 — why 117/600 (F45) vs 115/600 (F15), both over 6 windows

F15's window list for `M29_L0_s3`: **R5-R6, R6-R7, R7-R8, R8-R9, R9-R10, R12-R13** — flips
14, **16**, 21, 20, 25, 19 → 115/600.

F45's own pooled loop (`evolve_status` in `{"noop","crashed"}`): **R1-R2, R5-R6, R7-R8,
R8-R9, R9-R10, R12-R13** — flips **18**, 14, 21, 20, 25, 19 → 117/600 — plus, printed
separately: *"documented gateway-resume pair (R6,R7), NOT pooled: flips 16/100 = 16.0%
swing -4"*.

Both scripts pool exactly 6 windows over 600 pairs; 5 of the 6 are the same window with
identical flip counts ((R5,R6)=14, (R7,R8)=21, (R8,R9)=20, (R9,R10)=25, (R12,R13)=19 =
99 flips). The window set is **not** identical, and it is not a dedup/"last-row-wins"
issue — every shared window matches exactly, ruling out a `passed` vs `passed_flags[0]`
divergence between the two scripts' outcome readers. The sixth window is where they swap:
F15 pools (R6,R7) = 16 flips → 115; F45 pools (R1,R2) = 18 flips → 117. Net difference
+2 = 117 − 115, exactly.

The diagnostic script confirmed the cause is two independent label/config disagreements
that happen to net to +2:

- **(R6,R7):** `curves.json` labels R7's `evolve_status` `"ok"` (not `noop`/`crashed`), yet
  `R7/config.yaml` is **semantically identical** to `R6/config.yaml`
  (`cfg[7] == cfg[6]` → `True`). This is the twelve-hour gateway-outage signature already
  in the thesis (06-results.tex:320-328, and this row's own text): the evolve stage
  nominally produced a change — hence the `"ok"` label recorded before the wash — but that
  candidate was never kept; R7 is absent from `scoreboard.json`'s ships list, and the
  on-disk config was washed back to R6's. F15's structural test has no special case for a
  documented outage pair, so it pools (R6,R7) as an ordinary same-config window; F45's
  script knows about the outage and manually excludes it, printing it separately.
- **(R1,R2):** `curves.json` labels R2's `evolve_status` `"noop"`, so F45's
  `evolve_status`-trusting loop pools it automatically. But `R2/config.yaml` is **not**
  semantically identical to `R1/config.yaml` (`cfg[2] == cfg[1]` → `False`; R1's config
  carries an extra tracer-tool line — 142 lines against 141 for both R0 and R2 — that is
  absent again by R2). F15's structural check catches this and excludes the pair; F45's
  `evolve_status`-only test does not catch it and includes it — a live instance of exactly
  the "config-hash drift" trap F15's own docstring warns against (lines 17-21 of
  `audit_flip_rate_three_seeds.py`).

**Conclusion for both (a) and (b):** the discrepancies are pooling-convention differences
between a structural (config-text) same-config test and a `curves.json`-label same-config
test, not scope bugs, not stale snapshots, and not a dedup-rule difference. Every raw
number both scripts print is internally consistent and reproducible.

---

## Part 2 — Edits

### Ledger (`ch/C-ledger.tex`) — one added clause each, F15/F9e/F18 untouched

**F41, line 514** (appended before `\emph{Class:}`, ratio provenance):
> "The $1.6$--$2.0\times$ range quoted in the text divides this row and F44/F45 by F15's
> matching per-seed column ($41.6/21.0$, $37.7/20.1$, $31.5/19.2$) --- arithmetic on three
> already-reported \cls{A} rows, not a new measurement."

**F44, line 556** (appended after the existing "...is withdrawn." sentence, left
untouched):
> "F15's own seed-2 column, on this same subset, still reads $161/800=20.1\%$ over 8
> windows: its structural config-equality test cannot tell the (R11,R12) resume window
> from a genuine no-op and pools it with the other seven, where this row's script instead
> follows \texttt{curves.json}'s \texttt{evolve\_status} label (forced \texttt{ok} for R12
> by the restart) and reports that pair separately."

**F45, line 571** (appended after the existing "...is withdrawn." sentence, left
untouched):
> "F15's own seed-3 column is not affected by that: it separately reads $115/600=19.2\%$
> over the same six windows, by a different rule --- its structural config check keeps the
> (R6,R7) outage-resume pair in (\texttt{curves.json} labels R7 \texttt{ok}, but R7's
> config is textually identical to R6's, 16 flips) where this row's script instead pools
> (R1,R2) (labelled \texttt{noop}, though R2's config is not textually identical to R1's,
> 18 flips); a 2-flip swap, not a stale reading."

No other text in F41/F44/F45/F15/F9e/F18 was changed. Their existing numbers, classes and
citations are exactly as before this round.

### Body — `ch/01-introduction.tex`

**Line 340** (unchanged citation `\F{15}\F{44}\F{45}`, values corrected to F15's columns):
> "the noise floor: $21.0$, $20.1$ and $19.2\%$ same-config flips on three seeds
> \F{15}\F{44}\F{45}, so retention degenerates into drift."

### Body — `ch/06-results.tex`

**Lines 336-347** (rewritten so F15's per-seed values are the stated seed rates; F44/F45
appear once, parenthetically, as re-derivations — matches Table 6.1's
"$21.0 / 20.1 / 19.2\%$" at line 41):
> "The same-config flip rate is \textbf{21.0\%} on the first seed ($126/600$ pairs over
> six full-batch windows, per-window swing $-4\ldots{+}5$), \textbf{20.1\%} on the second
> ($161/800$ over eight windows, swing $-4\ldots{+}2$) --- near-identical to the pair ---
> and \textbf{19.2\%} on the third ($115/600$ over six windows, swing $-8\ldots{+}5$)
> \F{15}. All three are computed on the same 100-task bed, so the comparison is between
> seeds and nothing else. (A seed-level re-derivation that excludes the restart window
> gives $20.4\%$ on the second seed; the third seed's gives $19.5\%$ \F{44}\F{45}.)
>
> Three seeds: $21.0$ / $20.1$ / $19.2$. This is the number the readout argument needs,
> and it is stable."

**Line 355** (task's original citation "06-results.tex:353"; shifted +2 lines by the edit
above — ratio range, task 4):
> "$2.0\times$ each seed's own bed rate \F{41}\F{44}\F{45}."
(was "$2.1\times$"; full sentence: "...$1.6$ to $2.0\times$ each seed's own bed rate
\F{41}\F{44}\F{45}.")

### Body — `ch/07-discussion.tex`

**Line 309** (ratio range, task 4):
> "$1.6$ to $2.0$ times the bed rate \F{41}\F{44}\F{45}, rather than the whole bed."
(was "$2.1$".)

### Ratio recompute (task 4)

F41/F44/F45 volatile re-flip (41.6 / 37.7 / 31.5 %) over F15's matching per-seed
same-config column (21.0 / 20.1 / 19.2 %): $41.6/21.0=1.98$, $37.7/20.1=1.88$,
$31.5/19.2=1.64$ → range $1.6$–$2.0\times$ to one decimal. (F45's own row already said
"$\approx 1.6\times$" at the low end — line 566, untouched, was already correct.)

### Grep sweep (task 3)

`grep -rn "20\.4\|19\.5" ch/*.tex` after all edits: only F44's/F45's own row figures
(`C-ledger.tex:548`, `563`, `564`), the untouched slope entry (`C-ledger.tex:604`,
"$+19.5$" — left alone as instructed), and the new one-time parenthetical in
`06-results.tex:343-344`. No stray "20.4"/"19.5" flip-rate mentions remain elsewhere in
`ch/*.tex`. `05-design.tex` carries no "20.4"/"19.5" text (RESPONSE-A's prior round
touched only its window-count digit there, "8"→"7"); out of this round's named scope, not
touched.

---

## Part 3 — Private build

```
python experiments/docs/thesis/review/0904/gate_checks.py --outdir <scratchpad>/a2
[PASS] compile    pages=110 errors=0 overfull_hbox=0 (1.6s)
[PASS] abstract
[PASS] exclusion  hard=0 soft_bad=0 soft_ok=8
[PASS] anchors    rows=61 used=56 uncited=5
[PASS] bib        entries=54 cited=54
[WARN] unanchored sentences=68
[SKIP] scores
GATE PASSED
```

No undefined citations appeared in this run (bib entries=54, cited=54 — the six new
bibliography keys mentioned in the brief did not surface here; nothing to ignore, nothing
of mine to fix). No hard exclusion hits (no M24/M25/shakedown tokens introduced). Page
count 110, within the 120-page ceiling. `uncited_rows` (`9,17,18,27,28`) and the
`unanchored sentences=68` warning are pre-existing and untouched by this round's edits —
not F41/F44/F45/F15. Nothing my edits touched needed a second pass.

---

## Ten-line summary

1. Diagnosed both discrepancies by running all three scripts unmodified plus one read-only
   diagnostic script; no edits to `experiments/analysis/`, no writes under `recipe/`.
2. Seed 2 (8 vs 7 windows): the two scripts agree on all 7 shared windows and on the 8th
   window's own numbers (18/100, +2); they differ only on whether to pool the (R11,R12)
   post-restart resume window — F15 pools it (structural config match, blind to cause),
   F44 excludes it (keys off `curves.json`'s forced `"ok"` label for R12).
3. Seed 3 (117 vs 115 of 600, both 6 windows): 5 of 6 windows match exactly; F15 pools
   (R6,R7) — config textually identical despite an `"ok"` label from the outage — where
   F45 pools (R1,R2) instead — labelled `"noop"` but not textually config-equal. Net +2,
   not a dedup/pass@1 issue (ruled out: all shared windows are flip-count-identical).
2b/3b. Root cause in both cases: F15 trusts config-text equality; F44/F45 trust
   `curves.json`'s `evolve_status` label — two legitimate, different rules.
4. Added one clause each to ledger rows F44 and F45 (`C-ledger.tex:556`, `:571`) naming
   the exact round pair and cause; F15/F9e/F18 rows untouched.
5. Added one clause to ledger row F41 (`C-ledger.tex:514`) stating the $1.6$–$2.0\times$
   ratio is arithmetic on three already-reported class-A rows, with the three quotients
   shown.
6. Fixed `01-introduction.tex:340` to F15's per-seed values ($21.0$/$20.1$/$19.2\%$),
   citations unchanged.
7. Rewrote `06-results.tex:336-347` so F15's per-seed values are the stated seed rates,
   matching Table 6.1; F44/F45 now appear once, parenthetically, not as "the" seed rate.
8. Corrected the volatile-family ratio range ($2.1\times\to2.0\times$) at
   `06-results.tex:355` and `07-discussion.tex:309`.
9. Grep-swept `ch/*.tex` for stray "20.4"/"19.5"; none remain outside F44's/F45's own rows
   and the one sanctioned parenthetical; `C-ledger.tex:604`'s unrelated "+19.5" left alone.
10. Private gate build: GATE PASSED, 110 pages, 0 errors, 0 hard-exclusion hits, bib 54/54;
    nothing broken, no undefined-citation noise in this run.
