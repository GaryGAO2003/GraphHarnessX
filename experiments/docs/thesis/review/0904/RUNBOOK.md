# 过夜评审 runbook · 2026-09-04 夜

**任务**：对论文（`experiments/docs/thesis/`）做一次多线独立评审并合成修订路线图；夜间只动"不改主张"的项。
**当班规则**：论文源文件在评审阶段只读；`recipe/gaia_evolver/runs/` 只读；不起任何实验、不调模型 API；不 commit；
被排除战役的任何数字不得回流；新数字必须先有台账行 + 重算脚本。

## 分线

| 线 | 角色 | 模型 | 产出 |
|---|---|---|---|
| R0 | 考试委员会主席（EIC 人设） | 默认 | `R0-eic.md` |
| R1 | 方法学/统计评审 | 默认 | `R1-methodology.md` |
| R2 | 领域评审（自进化 agent / 归因 / 溯源） | 默认 | `R2-domain.md` |
| R3 | 跨学科评审（计量 / 临床试验 / 可观测性） | 默认 | `R3-perspective.md` |
| R4 | 魔鬼代言人 | 默认 | `R4-devils-advocate.md` |
| R5 | research-guardrails 审计 + 台账 [A] 行逐条重算核对 | 默认 | `R5-guardrails-ledger-audit.md` |
| R6 | 机械/合规检查（编译日志、引用、拼写、术语、排除残留） | sonnet | `R6-mechanical-compliance.md` |
| S | 编辑合成（决定信 + 修订路线图） | 默认 | `EDITORIAL-DECISION.md` |

## 阶段

- [x] Phase 0 领域分析 + 评审人配置 → `00-panel-config.md`
- [x] Phase 1 七线并行（各线独立，不互读）— R0–R6 全部回收（02:20–04:40）
- [x] Phase 2 合成 — EDITORIAL-DECISION.md（Minor Revision，26 P1 / 15 P2 / 8 P3）
- [x] Phase 3 round 1：A（台账刷新）→ A2（翻转率调和）∥ B1 ∥ B2a ∥ C → B2b 全部收工，in-place gate PASS 117 页；checker FAIL(5 小项) + EIC 复审 Minor Revision → round 2 补丁 → 复核 PASS（08:45）
- [x] 晨报 `MORNING-REPORT-CN.md`（08:30）；PDF/zip 已发；记忆已更新

## 修复分类标签

- **[W]** 措辞/结构，不改主张 → 夜间可施
- **[R]** 需从既有数据重算或新增台账行 → 夜间只在脚本已存在时施
- **[X]** 需要新实验 → 冻结，改写为局限性陈述，留给作者
- **[D]** 只有作者能定（范围、框架、声明） → 留给作者

## 状态记录

（夜间随进度追加）
