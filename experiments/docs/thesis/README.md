# Thesis sources

*Provenance-Grounded Self-Evolution of LLM Agent Harnesses* --- MSc Machine Learning, UCL, 2026.

## Layout

| Path | Content |
|---|---|
| `main.tex` | master file: document class, inputs in reading order |
| `preamble.tex` | packages and settings (UCL project-report template first, additions second) |
| `macros.tex` | `\F{n}` ledger anchors, `\claim{}`, `\cls{}`, `\FIELD{}` |
| `frontmatter/` | `titlepage.tex`, `abstract.tex`, `declarations.tex` (generative-AI use; code and data access), `glossary.tex` |
| `chapters/` | `introduction`, `related_work`, `baseline`, `ghx`, `design`, `results`, `discussion`, `conclusion` |
| `appendices/` | `deviations.tex` (A), `operations.tex` (B), `ledger.tex` (C, the fact ledger) |
| `bibliography/references.tex` | manual `thebibliography` (no bibtex pass) |
| `figures/` | `ucl_logo.png`, `harnessx_architecture.jpg`, `loop.tex` (TikZ), `scores.pdf` + `scores-table.tex` (generated) |
| `notes/` | working documents, not compiled: outline, story versions, Chinese digest, chapter drafts |
| `review/0904/` | review records (seven-line panel, editorial decision, maker/checker rounds) and the objective gate |

## Build

```
latexmk -pdf main.tex          # uses latexmkrc; or: pdflatex main.tex (twice)
```

Build products (`main.pdf`, `.aux`, `.toc`, ...) are git-ignored. The Overleaf bundle is produced by
`python review/0904/build_zip.py` (`thesis-overleaf.zip`, also ignored).

## Gate

```
bash review/0904/verify-gate.sh
```

Mechanical checks, no opinion: compile with 0 errors / 0 undefined references / 0 overfull boxes;
30 <= pages <= 120; the abstract fits one page; lines-per-page layout sanity; no excluded-campaign
residue; every `\F{n}` in the text has a ledger row; every citation has an entry and every entry is
cited; `figures/scores-table.tex` is byte-identical to a fresh regeneration by
`experiments/analysis/plot_campaign_scores.py`.

## Conventions

* Every number in the text carries an `\F{n}` anchor into Appendix C. A ledger row states the value,
  its sample, its class --- `[A]` recomputable by a named script under `experiments/analysis/`,
  `[B]` recorded in a named artefact, `[C]` judged --- and, where a value was revised, the withdrawn value.
* Evidence is read from six whitelisted campaigns only; the two graph campaigns flown before the
  graph-layer fixes are excluded from every number and every narrative (Appendix A). The gate fails on
  any residue of them.
* Retracted formulations (ledger, last section) are never re-cited.
