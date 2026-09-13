# Paper source

*Provenance-Grounded Self-Evolution of LLM Agent Harnesses* — MSc Machine
Learning, UCL, 2026.

`main.tex` is the root document. The current six-chapter structure integrates
design into the GHX/results treatment and the conclusion into discussion; the
source tree can temporarily retain obsolete chapter files during a controlled
sync, but only files reached by `main.tex` form the document.

## Release status and integrity

[`PAPER_STATUS.md`](PAPER_STATUS.md) states whether this checkout is a stable
reviewed snapshot. [`SOURCE-MANIFEST.json`](SOURCE-MANIFEST.json) records its
origin and input hashes. `source_paper_inputs` preserves the raw captured-source
hashes; `repository_inputs` verifies the LF-normalised paper files and the two
named repository analysis programs. The manifest lists the five whitespace-only
source-to-repository transformations explicitly. Verify it from the repository root:

```console
python scripts/check_paper_source.py
```

This is an offline integrity/static check. It does not compile TeX, obtain
missing assets, inspect private run archives, or recompute campaign results.
A missing input is reported as a prerequisite failure.

## Build

The complete source set includes `main.tex`, `preamble.tex`, `macros.tex`,
`latexmkrc`, included files below `frontmatter/`, `chapters/`, `appendices/`, and
`bibliography/`, the TeX/PDF/image figure inputs, and the two analysis audit
programs named by the manifest. The UCL logo is licensed/provided separately and
is not currently in this repository tree; place the authorised `ucl_logo.png` at the
manifest path before building.

```console
cd experiments/docs/thesis
latexmk -pdf main.tex
```

`main.pdf` and auxiliary products are ignored. The historical `review/0904/`
tree is retained as provenance, but its STATE and gate scripts describe an older
checkpoint and are not evidence that the current paper is accepted or final.

## Evidence boundary

The study compares whole L0 and GHX profiles across six campaigns. It does not
support decomposing that contrast into the effect of an individual graph
component. The composition graph constrains typed edits and stable identity; an
observed per-invocation execution DAG records what ran. Ancestor cones are
conservative over-approximations and do not establish counterfactual causation.

Quantities in the ledger have different evidence classes. Some can be
recomputed only when the private raw archives are mounted, some are verified
against recorded artefacts, and some are judgements. Static validation on a
fresh clone therefore does not reproduce the full paper. The GAIA task data is
gated and must not be committed or redistributed.

For paper-aligned reconstruction, verify the ordered `task_id` sequence rather
than assuming a future GAIA download is unchanged. Hash the UTF-8 payload formed
by joining IDs in JSON order with `\n` and retaining the final `\n`. The local
103-task reference is
`f8f4c80c07ca362eeed23cc7ae42e3cdc171a40817ccdf9f3344215f6b2f835f`;
the fixed-three-ID removal produces the 100-task hash
`c9ada1a6d518ae16289ec41fd1f118927b97263013a8ffc440dee44a36d61321`.
The downloader currently has no pinned upstream revision, so a matching hash is
required before treating newly obtained data as the same bed.
