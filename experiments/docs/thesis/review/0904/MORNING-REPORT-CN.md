# 晨报 · 2026-09-04 过夜评审 loop

**一句话**：七线独立评审 → Minor Revision；两轮 maker/checker 之后 gate 全绿，**117 页**（≤120），PDF 与 Overleaf zip 已发。
剩下的只有你能定的项列在最后一节。**没有 commit**。

## 1. 怎么跑的

- Phase 0/1：`academic-paper-reviewer` 五人设（考试主席、方法学、领域、跨学科、魔鬼代言人）+ `research-guardrails` 审计线（逐条跑 [A] 行脚本）+ 机械合规线，七线并行、互不读。报告 `R0–R6-*.md`。
- Phase 2：编辑合成 `EDITORIAL-DECISION.md`：Minor Revision，路线图 26 P1 / 15 P2 / 8 P3，每项带 [W]/[R]/[X]/[D] 标签。
- Phase 3（forge-my-loop）：客观 gate `verify-gate.sh`（编译 0 error/0 undefined/0 overfull、页数、摘要单页、每页行数、排除残留、锚点/台账、bib、分数表再生一致）；
  maker 分线 A（台账刷新）→ A2（翻转率调和）∥ B1（前置页/摘要/ch1/2/8）∥ B2a（ch3/4/7/A）∥ C（新脚本 + F57–F60）→ B2b（ch5/6/B/台账）→ 独立 checker + EIC 复审 → round 2 补丁 → 复核。
  全程 `RUN-LOG.md`、`STATE.md`、各 `round1/RESPONSE-*.md`、`CHECK.md`、`RE-REVIEW.md`。

## 2. 评审结论（要点）

- 七线一致 Minor Revision，无人要求 Major/Reject。CRITICAL 两个：强制声明缺失（已起草）；ship rate "0.62 vs 0.88" 与 F10 单种子 0.92 矛盾（已改为三种子并列）。
- 魔鬼代言人的攻击线里，正对照调和、多重比较纪律、排除方向（对图臂不利且已披露）、"checkable"可分解量化，正文本来就能挡住；未挡住的是"第六道门 18 杀也可能是图表示让 Evolver 定位退化"（已作为未排除的替代解读写进 §4.7/§6.3）。
- 台账审计：33 行组跑脚本，25 行完全复现；漂移见下节。13 个 [A] 行没有脚本 → 11 行改 [B] 并指向记录文件，F33/F34/F39 找到真脚本。

## 3. 夜里改了什么

**数字（只认脚本输出，旧值按台账惯例记为"已撤回"）**
- M26b 续跑后未刷新的四行：F10 0.62→0.60、F13 $36.3→$38.1、F31 44→49 题、F55 n=33→56。
- F54 9,700→9,600（脚本给 M22 加 R15 截止）；F44 脚本改回 100 题子集（143/700，7 窗）；F45 117/600。
- **正文种子翻转率统一为 F15 的 21.0/20.1/19.2**（预注册合并仪器为准；F44/F45 作种子级再推导并注明差异原因：F44 差在 (R11,R12) 重启对是否合并，F45 原脚本把 (R1,R2) 当同配置而 R1 实际多一行 tracer 工具）。
- 比值 1.6–2.1× → 1.6–2.0×；§6.5 撤回数 "25" → 21。
- 图 6.1/表 6.3 的上车标记从"记录轮"改为"落地轮"（k+1），正对照 R3 现为粗体，与 F49 一致。
- 新增 F57 任务聚类 CI [16.5, 23.9]%、F58 台地窗组成（图臂 15/39 轮为 25 题审计批，无图臂 0 → +2.7 的混杂已写进 Table 6.2 图注）、F59 战役日历、F60 Spearman–Brown k=4。

**正文/结构**：摘要最高级改正（HarnessForge 代码确已公开，GitHub 实查）；F34 零结果一句；"H1 rejected"→"not supported on any pre-registered endpoint"；命题加 "on this bed and system class"；
GenAI 声明 + 代码/数据访问声明（前置页）；术语表 40 条；§1.4 研究问题小节 + 第 8 章逐题闭合；§1.9 章节路线段；§1.5 "为何不直接补启发式"；
GAIA / 2607.12227 / 2607.13285 / Falconer–Mackay / Hutcheon / ICH E10 引用；DeepSeek 模型卡与价格页脚注；Table 6.1 加引用；Table 2.1 短图注；带宽只量自无图臂的说明；
§7.2 负责任披露段；PLANNER_SENSES 一句；AgentFlow 同名消歧；§7.1 "非正"软化；level-2 三义分开；附录 A/B 排除判据改为带日期修复集。

**版式**：前置页罗马页码、第 1 章起阿拉伯 1；`hypertexnames=false`（重复锚点警告清零）；**附录 A–C 与参考文献单倍行距**（正文 1.5 倍不动）。
中途事故：B1 在术语表里放了未收组的 `\scriptsize`，全文缩成 79 页却"合规"——已修，并给 gate 加了每页行数自检；真实页数曾达 122，靠附录单倍行距压到 117。

## 4. 早晨只有你能做的（[D]）

1. **push 分支并打 tag**：`git push origin ghx/m27-variance` + `git tag thesis-2026-09`（声明页写的是这个 tag；不打就把那句改成将来时）。
2. **确认 GenAI 声明**（`ch/00-declarations.tex`）：模型清单 "Opus 4.x, Sonnet 4.x/5, Fable 5.1" 和 "simulating reviewer feedback" 这句是否按你的意愿。
3. **F34 / H1 预注册记录**：六种 git-log 搜索没找到带日期的记录 → 要么补指向，要么把"pre-registered"的日期暗示删掉。
4. **§5.1 的 1.3× / 2.4×**（价格/输出长度比）：找不到厂商来源，现写为项目试点观察；有来源就补脚注。
5. **§7.2 披露段**：现写"提交时向 HarnessX 维护者报告 Chapter 3 的缺陷"，是替你做的承诺，请确认。
6. **附录单倍行距**：是否接受；改回 1.5 倍会到 ~122 页，需另找 3 页。
7. 未做：碳/算力估计句（无可引换算）、台账瘦身 P2-01、阶梯小图 P3-01；`THESIS-OUTLINE-V5.tex`（非编译）仍写 1.6–2.1×。
8. 提交前：再跑一次 `bash experiments/docs/thesis/review/0904/verify-gate.sh`；commit 时不要带 `THESIS.{aux,log,out,toc,lof,lot,pdf}`。

## 5. 文件

- 论文：`experiments/docs/thesis/THESIS.pdf`、`THESIS-overleaf.zip`（21 项，含 `ch/00-declarations.tex`、`ch/00-glossary.tex`、`fig/`）。
- 评审与 loop 记录：`experiments/docs/thesis/review/0904/`。
- 中文精读版已加"09-04 过夜评审后的变更"一节。
- 改动的脚本：`experiments/analysis/plot_campaign_scores.py`（落地轮）、`audit_m28_seed2_flips.py`（100 子集）、`audit_candidate_bucket_and_aim.py`（M22 R15）；新增 `audit_flip_rate_cluster_ci.py`、`audit_fresh_carried_plateau.py`、`audit_campaign_calendar.py`、`audit_spearman_brown.py`。

## 6. 09-06 作者裁定（补记）

- [D]-3 预注册记录：改 "pre-specified"，§5.4 写明记录（F32/F33 设计先于数据入库 9713d33；F34 规则在笔记、入库与裁决同提交 55533cf）。副标题同步改为 "a Pre-Specified Falsification"。
- [D]-4 1.3×/2.4×：删，只留 3.1× 列价。
- [D]-5 §7.2 披露段：删（作者不报）。
- 仍待作者：push + tag、声明页模型清单、是否 commit。
