# Campaign archive boundary

This directory is a local mount point for raw campaign outputs. Only this file
is committed. Archives are several gigabytes, may contain provider responses and
operational metadata, and are distributed separately under their applicable
access policy.

The thesis analyses use six whitelisted campaigns, 96 rounds in total (R0--R15
per campaign), evaluated on a common 100-task text-only bed. The seed-3 initial
bed had 103 tasks. Do not infer the fresh/as-flown sample from all rows found on
disk: the reported fresh/as-flown total is 8,393, while workload censuses can
include carried, repeated, diagnostic, or otherwise out-of-estimand rows.

The bed identity is the SHA-256 of its ordered task IDs. Preserve JSON array
order and encode exactly:

```python
payload = ("\n".join(str(row["task_id"]) for row in rows) + "\n").encode("utf-8")
```

The local 103-task reference has 103 lines / 3,914 bytes and SHA-256
`f8f4c80c07ca362eeed23cc7ae42e3cdc171a40817ccdf9f3344215f6b2f835f`.
After deleting the three fixed IDs recorded by `make_nopixel_bed.py`, the
derived common bed has 100 lines / 3,800 bytes and SHA-256
`c9ada1a6d518ae16289ec41fd1f118927b97263013a8ffc440dee44a36d61321`.
These hashes identify task membership and order; they do not hash gated answers
or other task fields.

The current downloader does not pin a Hugging Face dataset revision. Treat a
new download as a candidate bed and compare its ordered-ID hash before using it
for paper-aligned analysis. The revision visible in one local cache is not
evidence of the historical generation revision.

To use an analysis program:

1. Obtain the exact archive set through the project data-access channel.
2. Place each archive directory under this directory without renaming it.
3. Read the program's `--help` and the thesis ledger entry for its required
   campaign labels and estimand.
4. Run the program from the repository root.

If a required archive or record is absent, stop and report that prerequisite.
Do not treat missing input as an empty campaign. Unit tests and
`scripts/check_paper_source.py` do not require these archives.

The repository does not claim that a fresh clone can recompute every reported
quantity. Some values are recomputed from private raw records, some are checked
against recorded artefacts, and some are explicitly judgement-based. Running a
new campaign is a separate operation requiring the gated GAIA bed, provider and
search credentials, and paid model calls.

Two narrow support checks accept explicit roots (or `GHX_DATA_ROOT` /
`GHX_RUNS_ROOT` respectively):

- `audit_answer_length.py --data-root ...` reports reference-answer lengths for
  the 100-task/103-task beds only; it does not compute the F3 false-negative
  sample statistics.
- `audit_false_signal_reach_per_seed.py --runs-root ...` checks F4 reach using
  every no-graph dossier in each arm and F7 heading presence using M26b R2--R15
  for seed 1 and all dossiers for seeds 2/3.
