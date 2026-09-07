# Loop state · thesis-overnight-review

> agent 会忘，文件不会忘。每轮结束更新。maker/checker 每轮开工先读本文件与 LOOP-BRIEF.md。

## 目标（每轮重读）
把 2026-09-04 夜的多视角评审中**可机械验证**的缺陷修到 gate 全绿；不改主张、不引入无台账数字、不让被排除战役的数字回流；
主观项（[D]/[X]）只列待批。

## 客观完成条件（gate）
`bash D:/PycharmProj/HarnessX/experiments/docs/thesis/review/0904/verify-gate.sh` 退出码 0，且本轮任务清单每项
FULLY_ADDRESSED 或 REJECTED-with-reason。

## 允许触碰的文件
`experiments/docs/thesis/THESIS.tex`、`ch/*.tex`、`fig/*.tex`；`review/0904/round<k>/` 下的 RESPONSE/CHECK；
补丁脚本放 scratchpad。禁区：`recipe/gaia_evolver/runs/`、`experiments/analysis/*.py`、git 历史。

## 轮次

### Round 1
- 状态：Phase 1 评审进行中（R0–R6 七线并行，已派）
- 编排者预修 P0（04:05，已施，checker 需核）：`experiments/analysis/plot_campaign_scores.py` 的 ship_rounds() 改为标"落地轮"
  （scoreboard 第 k 轮记录的 ship 写进 R{k}/config.yaml，即第 k+1 批的配置，与 audit_gain_face.py 的 a→a+1 口径一致）；
  `fig/scores-table.tex` 与 `fig/scores.pdf` 已再生。验证点：无图种子 1 的正对照 R3 现为粗体；图种子 3 的 R10 不再粗体（与 F49
  "R9→R10 nothing shipped" 一致）。图注文字"rounds into which a candidate shipped"无需改。来源：R1 MAJOR #3。
- 本轮任务：
  - **A（台账修复，04:35 已派 Maker-A）**：F10/F13/F31/F55 按 M26b 终态刷新（续跑后未刷新）；F54 脚本给 M22 加 R15 截止（9,700→9,600）；
    F44 脚本改回 100 题子集；F45 117/600；F15 汇总值只认脚本输出；F26–F30/F32–F39/F43 改类或补脚本。产出 round1/RESPONSE-A.md。
  - **B（正文/结构，等合成后派 Maker-B）**：来自 EDITORIAL-DECISION.md 的 P1/P2 [W]/[W]-draft 项；含摘要最高级改正（HarnessForge 代码已公开）、
    ship rate 句改为三种子/臂均值、§6.5 "25"→"21"、GAIA 等引用、Table 6.1 加 
ef、Table 2.1 短图注、RQ 列表、结构段、术语表、
    GenAI 声明与仓库声明草稿（AUTHOR-FACTS）。
- Maker-A 收工（05:35）：F10 0.62→0.60、F13 $36.3→$38.1、F31 44→49、F55 n=33→56、F45 115→117/600（M26b 续跑后未刷新）；F54 9,700→9,600（M22 R15 截止）；
  F44 161/800→143/700（改回 100 子集；7 窗，重启对另列）；11 行 [A]→[B] 并指向记录文件；F33/F34/F39 找到真脚本；gate PASS 110 页。
  **遗留矛盾**：正文 ch1:340 / ch6:336–344 现写 21.0/20.4/19.5，而 F15/F9e 预注册合并仪器与 Table 6.1 仍是 21.0/20.1/19.2 → Maker-A2 统一（F15 为准，F44/F45 作种子级再推导并注明差异）。
- 并行派工（05:40）：A2（调和翻转率 + 1.6–2.1× 比值）、B1（前置页/摘要/ch1/ch2/ch8/参考文献）、B2a（ch3/ch4/ch7/A）、C（新脚本 + F57–F60 + 三句）；B2b 待 A2 与 C 收工后派。
- gate 基线（03:12，--no-compile）：PASS；pages=109；unanchored=69（WARN，仅监控不得上升）；台账未被引用行 F9/F17/F18/F27/F28；
  scores 再生一致；排除残留 hard=0（1.99 是白名单 M22-L0 的 lift，已从禁用表移除）

## 开放项 hash（loop 检测器）
- round 0: —
- round 1 收官（08:05）：开放项 = {CHECK#1..5, NEW-1..3 [W]} + {NEW-4..6 [D], P1-04 [D], P1-15 [D], NEW-7 [D]}
- round 2（08:20–08:45）：[W] 全部施加并经 sonnet 复核（含补漏 ch1/ch5 两处）；gate PASS 117 页；开放项只剩 [D] → **停止条件 1 达成，loop 结束**

## 待 checker / round 2 核的点（编排者记）
- ch/A:143 标题由 "level-2 evidence" 改为 "capability evidence"（B2a）。harnessx/ghx/cheatsheet.py:88 的候选证据要求叫 "Level-1 AND Level-2 evidence"，
  是第三种 "level" 用法（候选证据等级，非读数阶梯、非 GAIA 难度）。要求：术语表须区分三种；A:143 若与 cheatsheet 术语对应，加括注 "(the cheatsheet's Level-2 evidence)"。
- THESIS-OUTLINE-V5.tex（非编译文件）仍写 1.6–2.1×，留给作者。

## 升级给作者（loop 不许自己处理）
- GenAI 使用声明与代码仓库访问声明：已知缺失（可起草，需作者核）
- 其余待评审结果

## 经验教训
- 2026-09-04: 前置页里任何字号/行距切换必须收组（egingroup…\endgroup）；私有构建的"页数 ≤ 120"会把整篇缩小当成通过——gate 应再加"正文每页行数区间"检查（round 2 待加）。
- 2026-09-04: 页数预算：正文 1.5 倍行距是硬规定；附录 C（台账）与参考文献改单倍行距是编排者裁定（reference matter），晨报须点名让作者确认。
- 2026-09-04: 含反斜杠/非 ASCII 的补丁一律用 Write 工具写成 .py 再跑，禁 heredoc / python -c。
- 2026-09-04: `R{k}/trajectories` 存的是第 k−1 批；台账 F1/F2 已按此口径。
- 2026-09-04: 物理页 = 印刷页 + 6（标题、摘要、目录×2、图目录、表目录）。

## 预算与硬停
- 轮数上限 4 · token 硬顶：剩余 < 11.5M 停 · 开放项 hash 连续两轮相同即停 · 不 commit / 不改主张 / 不起实验

## Round 3 (2026-09-06) — author rulings applied

- Closed: [D] pre-registration record (→ pre-specified + record paragraph in 5.4), [D] 1.3×/2.4× (deleted), [D] disclosure paragraph (deleted).
- Still open (author-only): push branch + tag `thesis-2026-09`; confirm model list in `ch/00-declarations.tex`; commit decision.
- Not done by design: carbon/compute sentence, ledger trim P2-01, ladder mini-figure P3-01.
