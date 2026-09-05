# Loop Brief · thesis-overnight-review (forge-my-loop)

> 2026-09-04 02:40。用户指示："进行 overnight review，派多线用 skills" → "用 forge loop skill 进行多轮审验" →
> "接下来一切你自己评判，我去睡觉了"。本 brief 锁死意图与停止条件；生成顺序 brief → gate → STATE → 子代理 → loop。

## Phase 0 · 适配性判断

四条件：① 重复——多轮"评审→修→验"在一夜内反复，有界 ✅；② 验证可自动化——pdflatex 退出码/日志、排除残留 grep、
台账锚点/参考文献完整性、分数表再生 diff，全部退出码语义 ✅；③ 预算能承受浪费——用户本会话 ~15M token，接受 ✅；
④ 工具齐——pdflatex、pdftotext、python 3.13、只读的白名单 run 目录 ✅。

硬否决核对："含主观判断的内容工作"命中一半：论文措辞是主观的。处理：loop 只自动施 **[W]（不改主张的措辞/结构）**
和 **[R]（已有重算脚本支撑的数字/台账行）**；一切 **[D]（框架/范围/声明）** 与 **[X]（需新实验）** 只产出"待批"，
由作者早晨裁决。评审带宽不是瓶颈（作者在睡觉，早晨一次性读 diff）。

判定：**⚠️ 可做，限定在客观层。** 成熟度 L2：辅助修复、不 commit、人（作者）早晨 merge。

## Intent
让论文在提交前通过一轮独立多视角评审，并把评审中**可机械验证**的缺陷修到 gate 全绿；主观项整理成早晨的裁决清单。

## Scope
- 只碰：`experiments/docs/thesis/THESIS.tex`、`ch/*.tex`、`fig/*.tex`；评审产物只写 `review/0904/`。
- 只修：[W] 与已有脚本支撑的 [R]。GenAI 声明 / 仓库声明 / RQ 列表 / 结构段：按用户"一切你自己评判"授权可起草，但
  在晨报里单列，标明"已起草、请核"。

## Definition of Done（可测）
1. `bash review/0904/verify-gate.sh` 退出码 0（编译 0 error / 0 undefined / 0 multiply / 0 overfull；30 ≤ 页数 ≤ 120；
   摘要单页；排除残留零命中；锚点与参考文献完整；分数表与再生一致）。
2. 合成路线图里所有 [W]/[R] 项的状态为 FULLY_ADDRESSED，或被 checker 判为"不应施"并写明理由。
3. 复审（re-review 模式）无新增 CRITICAL；剩余项全部是 [D]/[X]，已列入晨报。

## Verifier Stack
- gate：`review/0904/verify-gate.sh`（→ `gate_checks.py`，结果 `gate_result.json`）
- 台账重算：R5 线逐条跑 [A] 脚本（只读 runs/），mismatch 进入路线图
- checker 子代理：只对 gate 退出码 + RESPONSE 文件里每条"声称改了"的位置逐条核实 + 快照 diff 越权检查
- 退出码非零 = 未完成

## Anti-goals
- 不改任何主张、不引入任何没有台账行 + 重算脚本的数字、不让被排除战役的任何数字回流。
- 不写 `recipe/gaia_evolver/runs/`；不起实验、不调模型 API、不联网抓数据。
- 不 `git commit`、不删文件、不改 `experiments/analysis/` 里的重算脚本（发现 bug 只记录）。
- maker 与 checker 不对话；checker 失败原因必须是可执行清单，回灌下一轮。

## Budget
- 迭代上限：**4 轮**（round 1 = 全 panel；round ≥2 = re-review 模式，EIC + 合成）。
- token 硬顶：会话剩余 < **11.5M** 即停（约 3.5M 花费）。
- 单轮 gate 超时：编译 10 min、再生 15 min。

## State
- `review/0904/STATE.md`（每轮重读目标；记录开放项 hash、gate 结果、升级项）
- `review/0904/RUN-LOG.md`（每轮追加一行）

## Stop Conditions（任一触发即停）
1. DoD 三条全部达成。
2. 轮数 ≥ 4。
3. 剩余 token < 11.5M。
4. loop 检测器：开放项集合的 sha256 连续两轮相同（maker/checker 乒乓或无进展）。
5. 人工闸门：任何需要 commit / 改主张 / 新实验 的动作只产出待批。

## Maturity
- [x] L1 只报告——round 1 的 panel + gate 手动跑通
- [x] L2 辅助修复（不 commit，作者早晨 merge）——用户已授权
- [ ] L3 无人值守——不启用

## Kickoff
本会话内由主循环编排（无 cron、无 Workflow）：
round k = [review / re-review] → [maker：施本轮任务，写 RESPONSE] → [checker：gate + 逐条核实 + diff 越权] → STATE/RUN-LOG →
停止条件判定。子代理 prompt 文件：`review/0904/agents/maker.md`、`agents/checker.md`。
