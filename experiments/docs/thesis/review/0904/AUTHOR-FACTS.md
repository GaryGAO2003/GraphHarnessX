# Author facts for the two mandatory statements (verified 2026-09-04 03:15, for the maker)

## Code repository (verified with `git remote -v`, `gh repo view`)
- Public fork: https://github.com/GaryGAO2003/HarnessX (visibility PUBLIC, default branch `main`); upstream is
  https://github.com/Darwin-Agent/HarnessX (the official release the thesis vendors).
- Thesis work lives on local branch `ghx/m27-variance`, HEAD `0b15af1` (uncommitted thesis edits on top).
  **The branch is not on origin yet** (`git ls-remote --heads origin ghx/m27-variance` is empty) — the author must
  push before submission; the statement should name the branch and say the commit hash is fixed at submission.
- Second remote `lab` = https://github.com/GaryGAO2003/harnessx-variant-routing (PRIVATE) — do not cite.
- Recompute scripts: `experiments/analysis/` (audit_*.py, plot_campaign_scores.py, cone_size_recompute_m26b.py);
  thesis sources: `experiments/docs/thesis/`; the fact ledger is Appendix C of the thesis.
- Whitelist run directories (`recipe/gaia_evolver/runs/{M22_L0_ghx0,M28_L0_s2,M29_L0_s3,M26_100x16b,M28_GHX_s2,M29_GHX_s3}`)
  are large trajectory stores; whether they are published is the author's call — the statement should say what is in
  the repository and that run archives are available on request unless the author decides otherwise.

## Generative-AI use (UCL policy: tool name/version, publisher, URL, one sentence of context)
- Tool: Claude Code (Anthropic), https://claude.com/claude-code, with Claude models (Opus 4.x, Sonnet 4.x/5, Fable 5.1)
  during 2026.
- Context (factual, from the working record): used as a coding and writing assistant under the author's direction —
  implementing GHX and the analysis scripts, running and monitoring the campaigns, drafting and editing the text of
  this dissertation, and simulating reviewer feedback. Experimental design, the evidence-whitelist and exclusion
  rulings, the interpretation of results and all final wording decisions are the author's; every number in the text is
  anchored to a ledger row and, for class [A], recomputed by a script in the repository.
- The LLMs inside the system under study (the solver and the four meta-roles, DeepSeek models through a LiteLLM
  gateway) are the object of the experiments, documented in Chapters 3 and 5, and are not part of this declaration.
- Placement: a short unnumbered section after the abstract or as an appendix ("Declaration of generative-AI use");
  not counted toward the page limit. Wording is drafted by the loop and must be confirmed by the author in the morning.

## Verified citation facts (arXiv abs page fetched 2026-09-04 03:40, for the maker)
- arXiv:2607.12227v2 — "Rethinking the Evaluation of Harness Evolution for Agents". Yike Wang, Huaisheng Zhu, Zhengyu Hu,
  Yige Yuan, Zhengyu Chen, Shakti Senthil, Hannaneh Hajishirzi, Yulia Tsvetkov, Pradeep Dasigi, Teng Xiao.
  Submitted 14 Jul 2026, v2 27 Aug 2026. Abstract opens: "We revisit the evaluation of automatic harness evolution for
  LLM agents. Existing harness evolution methods use unit test cases to search for harness configurations and then
  report final performance on the same public benchmark. This protocol raises two fundamental concerns."
  Bibliography style in ch/99-bibliography.tex: "Author, Author, Author, et al. Title. \texttt{arXiv:ID}, YEAR." — key
  suggestion: `rethink-harness-eval`. Per the 9-07 plan, new papers enter only ch2 / ch7.

## HarnessForge code-release status (verified 2026-09-04 03:50 via arXiv abs + GitHub API)
- arXiv:2606.01779v1 (1 Jun 2026) abstract ends: "The code is available at https://github.com/mingju-c/HarnessForge."
- The repository exists, is PUBLIC, primary language Python, created 2026-05-29, last push 2026-06-02, two commits; top-level
  contents: HarnessForge_4B, HarnessForge_8B, LlamaFactory, eval_bench, figs, README.md. It is a real code release.
- Consequence: the abstract's "HarnessX/AEGIS is, to our knowledge, the one published harness-level closed loop whose
  code is released" is false as written and must be corrected wherever the superlative appears. Defensible replacement:
  HarnessX/AEGIS is a published harness-level closed loop with released code and, to our knowledge, the most heavily
  governed one (four meta-roles, five deterministic gates); HarnessForge (released June 2026) is the nearest neighbour
  and is compared in §2.1 / Table 2.1. The comparison table has no code-release column, so no table change is needed.

## More verified facts (05:10)
- arXiv:2607.13285v1 (14 Jul 2026) — "Harness Handbook: Making Evolving Agent Harnesses Readable, Navigable, and Editable",
  Ruhan Wang, Yucheng Shi, Zongxia Li, Zhongzhi Li, Yue Yu, Junyao Yang, Kishan Panaganti, Haitao Mi, Dongruo Zhou, et al.
  About making evolving harnesses readable/editable (building, not evaluating). Key `harness-handbook`.
- arXiv:2311.12983v1 (21 Nov 2023) — "GAIA: a benchmark for General AI Assistants", Grégoire Mialon, Clémentine Fourrier,
  Craig Swift, Thomas Wolf, Yann LeCun, Thomas Scialom. Key `gaia`.
- Vendored HarnessX repository licence: MIT ("Copyright (c) 2026 HarnessX Contributors"); upstream Darwin-Agent/HarnessX is
  MIT per GitHub. Fig 1.1 (docs/assets/paper/harnessx_architecture.png) may be reproduced under it with attribution.
- Bibliography keys reserved for tonight: gaia, rethink-harness-eval, harness-handbook, falconer-mackay, hutcheon-dilution, ich-e10.
