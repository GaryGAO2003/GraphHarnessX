# M25_103x16 — 终局验收（14 批，08-22 01:02–17:19 停）

> 跑：`recipe/gaia_evolver/runs/M25_103x16`，HEAD=d85f438，17 flag（L5 六旗 + M24 七旗 + M25 四旗），103 题床，pass@1，litellm 网关。
> 判定：**数据面 PASS（14 个完整批 + R1–R13 meta 全套，可判读）；运维面 R14 meta 截断（EXPLAINED，见 §1）；机制面一处必修缺口（outcome-fidelity ×20，§4.6）→ 列 M26 起飞前置。**
> 撰于 2026-08-23 凌晨（F-1 收官对账）。四条赛前注册预测的对账在 §3——其中 empty 一条按 content-ref 伪影翻案后的真值口径重写。

---

## 1 · 跑况与数据面

- 01:02 起飞 → 17:19 日志停写；进程 18:54 核实已全退。**停跑定性（E 项日志全扫裁定）：外部停树，非崩溃**——out.log 的 task_start→model_response 循环持续到 17:19:19，err.log 尾部纯 ResourceWarning，无 Traceback、无 kill 异常痕迹；第 14 轮正在飞行中（R13 evolve 17:10:39 完成，Stage P 已出 91/103 digests）。停点紧随 17:14 证据面修复 commit `03d4b42`（改码窗口需停跑）。
- 有效数据：**history R0–R13 共 14 个完整批**（1442 = 14×103 逐题记录）+ R1–R13 meta 全套（journal 记至 R13 ship）。R14 的 91 份 digest 为截断产物，**作证据可用**（本次 swinger 解剖与 flip ledger 样例即用它），不作 SOP 完整性判据。R14/R15 批未跑（计划 16 批，完成 14）。
- **目录↔history 错位账（重要，复盘取数必读）**：`R{k}/trajectories`、`R{k}/digests` 对应 **history round k−1** 的批（步数逐轮配对实锤：任务 0383a3ee history R0=17 步 ↔ R1 目录 44 行；R0 目录无轨迹）。一切离线分析从 `data/task_history.jsonl` 取轮号，**禁止从目录名推**。flip_ledger 模块（`c3c5946`）已按此设计（史轮 = max(round)）。
- 不 resume 本 run；后续对比一律走重算（床切 nopixel-100 时同样重算不重跑）。

## 2 · 曲线与成本

| R | 过题 | budget败 | done败 | evolve | 批费 |
|---|---|---|---|---|---|
| 0 | 55 | 36 | 12 | baseline | $56 |
| 1 | 72 | 21 | 10 | ok（C-R1-01/02 上车后首批） | $61 |
| 2 | 66 | 2 | 35 | ok → **ROLLBACK**（C-R2-01/02 撤） | $36 |
| 3 | 69 | 7 | 27 | ok（首个 tools ship：smart_fetch） | $39 |
| 4 | 67 | 4 | 32 | ok | $40 |
| 5 | 69 | 7 | 27 | noop | $40 |
| 6 | 66 | 6 | 31 | ok | $46 |
| 7 | 69 | 7 | 27 | ok | $43 |
| 8 | 65 | 6 | 32 | noop（Evolver 烧穿 400 步） | $45 |
| 9 | 66 | 7 | 30 | noop | $46 |
| 10 | 70 | 3 | 30 | ok（tools） | $39 |
| 11 | 70 | 6 | 27 | noop（Evolver 烧穿 400 步） | $46 |
| 12 | 70 | 4 | 29 | noop | $45 |
| 13 | 73 | 3 | 27 | ok（C-R13-01 = OCR 交付链修复） | $43 |

- 分数形态：R0=55 →（C-R1-01 SilentEmptyGuard 族上车）R1=72，此后 65–73 带内震荡，末批 73（70.9%）。与 HX 台地 67.29±2.84 重叠，**按包络纪律分数面不判**。
- **noop 轮 5 个**（R5/8/9/11/12，占 5/14），各烧 $40–46 重测同配置包络——`--noop-audit`（`9f298af`）由此立项落地。
- **成本总账：批面 $625 + Stage P $216（13 metas，中位 $14.5，尖峰 $27.7）+ Evolver $438（步数 62–400，中位 205，两次 400 步烧穿 R8/R11）+ Critic $97 ≈ 全程 $1,375**。对照：M22-L0 全程 $808/17 轮；M24 到 R13 停 ≈$1.95k。单发 digester 兑现 Stage P ×0.26（vs M24 $56/轮）。

## 3 · 四条注册预测对账（赛前写于 runbook，今按实测裁决）

**① "POSIX bash + 硬化 fetch 攻下 empty_consumed 10±5 题" — 机制口径不成立；方向经另一药路成立；且预测所指的一号药从未被测。**
- bash：整个战役 **0 次提案**（预测未被完整测试 ≠ 被证伪——此区分必须写进论文）。
- 硬化 fetch（C-R3-01 smart_fetch）：自报预测 5 题，靶向对账命中 2/5、持久 1/5（05407167）。
- 但 empty 病本身确实塌了：**真值 37→4（9×，修 content-ref 伪影后口径）**，主药是 guard 族（C-R1-01），非 bash/fetch。记录面 31→29 "纹丝不动"是伪影假常数（95.6% 伪影率），环曾对幻影堆药——仪器谎报→环空转，读数纪律最硬案例。
**② "budget_no_commit 维持 0" — 不成立。** 实测 36→21→2→3–7 带，从未续 0（最低 R2=2，该轮 ship 旋即被回滚门撤走）。M24 CommitBand 的 0 未在 fresh 环上复现；M25 环重新演化出的是弱化版药。
**③ "Stage P ~$11/轮" — 方向成立，幅度超 30%。** 实测中位 $14.5（$12.9–27.7），×0.26 于 M24 的 $56±1；绝对值超预测。
**④ "IV-11 税消失" — 成立，但门税转移。** 8 个被拒候选 **零 IV-11 击杀**（死因=IV-3 证据锚 / 回归义务 / 重复规则）；其中 **7/8 是 tools 桶**——insert_tool 打开编辑面后 tools 提案爆发（全程 ~10 个 tools 候选，2–3 上车、7 被拒），瓶颈从"不可表达"移到"门下证据纪律"。**revived_as 全空：gate_refusals 复活通道整个战役零使用**（M24 设计意图未兑现，记接线缺口）。

## 4 · 机制面终账

1. **Ships**：12 艘 / 8 个 ship 轮；桶分布 processor 6 / prompt 2 / tools 2 / config 1 / prompt+tools 1。预测命中（flip 口径）：processor 22/49=44.9%、prompt 8/21=38.1%、tools 3/14=21.4%、config 1/4=25%，合计 34/88=38.6%。归因回填 9/88 评 direct/orphan。
2. **R2 回滚事件**：vendored 门（Δ≤−5pp 且 ≤−3 题）按 M24 同配置分布反推噪声假阳性率 ≈14%；三尺读数与门相反（within-envelope、全 swinger）；暴露锥尺对常燃节点空泛化 → 当日修复（`7f3f5b2` 常燃弃权护栏）。撤掉的 C-R2-02 属 M22 曾 +7.4pp 的 countdown 同族——门可能撤了真药。
3. **content-ref 伪影**（全战役最大翻案）：flatten 缝把 >2KB 外置载荷抄成空指针，Digester/Layer A/投影/motif 13 批全被骗；修复 `03d4b42`。修正后机制史：empty 真值 37→4；残余失败 24/33 无 motif、败跑比同题胜跑 +4.5 步（run 中段死）→ runtime policy 立项依据。
4. **Swinger 解剖**（R13 批 30 败 = 17 swinger + 13 never；union 90/103=87.4%）：17 题死因聚类 = 未验证提交/编造 ×7、空结果+botwall ×4、死源打转 ×3、过早拒答 ×1、像素 ×1、截断 ×1。诊断全在、无人并排 → **flip ledger 立项并落地（`c3c5946`，缝进 map.md）**。
5. **泄漏抓获 ×2**（digester strategy 自标）：9f41b083 R12 过=arXiv 论文印金标（`leak_snippet_commit`）；8131e2c0 R13（`rapid_search_leak_utilization`）。→ 去污名单增补候选；仪器的实战战果。
6. **outcome-fidelity 漂移 ×20（必修）**：loop_health 实测 R14 样本 digest-empty=20 vs U-outcome-empty=0——投影对结构化空载荷全盲。**直接打击 M26 runtime policy 的 `consecutive_empty` 谓词（读 live outcome 戳）→ 升级为起飞前置修复**（修法：投影时 join payload 字段）。
7. Evolver 烧穿仍在（2/13 metas 到 400 步顶），但中位 205 步显著低于 M24 的 ~250。
8. **smart_fetch 的 wayback 退路大面积失联**：`wayback cdx/available err` ×4,608（含 429 限流），占非 OVERRIDES 告警量约 2/3——环自造工具无退避/限速。fetch 药"2/5 命中"的读数须叠加此背景（退路半瘫时测得），真实上限未知。修复列 M26 队列。
9. **单发 digester 的 agentic 回退活体 ×11**（超长轨迹/多 rollout 自动分流回官方形态）——k/长度路由按设计工作。
10. **evolver_fallback 全程零真实触发**：R8/R11 烧穿仍各出 1–2 候选，未达"零候选"触发条件——该缝状态 = **未经活体检验**（开放项），非失效。

## 5 · SOP 项状态

| 项 | 状态 |
|---|---|
| A 进程/完成 | R14 meta 截断，EXPLAINED（§1）；无 Traceback |
| B 运动学读数 | 本文 §2 |
| C 缝验证 | verifier@R14：Layer A′ 91/91 PASS、triage/锥 PASS；population.md 缺 = **截断伪影**（aggregate 未跑到），非缝 bug |
| D loop_health | 9 ok + 1 BROKEN（outcome fidelity，→ §4.6 必修）；U 覆盖 103/103 |
| E 日志全扫 | **PASS：零未解释 ERROR/Traceback**。79 ERROR 全收敛于门重放 asyncio 收尾家族（5 子型：Task exception never retrieved 35 / Unclosed client session 24 / Unclosed connector 11 / Task destroyed 7 / Future exception 2）；6,954 WARNING 全部落 12 个具名桶。新账：wayback 失联 ×4,608（§4.8）；anchor_repair IV-1b advisory ×214；digest 断锚 ×28；IV-4 verdict 畸形 ×20（R1–R9 后消失）；RW 热点新增 `run_meta_aegis.py:752`（socket ×1,622）与 `preprocess.py:40`（×1,454），RW 总量 46,203。out.log 137k 行零告警 |
| F 产出抽查 | R0–R13 全量结构齐；R14 91/103 digests 截断可用 |
| G 新缝首燃 | 单发 digester 全程活体（§2 成本）；门重放 11 会话、门答题 10/12；anchor-repair/cheatsheet 于 30×3 段验收 |
| H U 覆盖 | 103/103（R13） |
| I/J 分数与成本 | 只记录（§2），不作门槛 |

## 6 · M26 注册预测（底稿，起飞前定稿）

- **P1（头号）**：flip ledger 上桌后 **≤3 个 evolve 轮**内，环 ship 出**验证族**候选（判据：manifest 引用 `flip_ledger.md` 锚点，机制=终局核验/程序化计数类；先例基线 = 25 轮零验证族 ship）。
- **P2**：环自写 ≥1 条 runtime policy 规则并过离线重放门（fired-set 非空非全）。
- **P3**：budget_no_commit ≤7 维持；empty 真值（修伪影口径）≤10。
- **P4**：Stage P $12–16/轮；noop 轮批费 ≤$15（noop-audit 生效判据）。
- **P5**：分数按包络不判；组均−HX 台地 > +5 题才升级讨论。

## 7 · 遗留与移交

1. **起飞前置（必做）**：outcome-fidelity 投影修复（§4.6）→ 6×2 smoke（新缝首燃三查：map.md 含 flip_ledger 节 / policy 空表加载行 / L6 生效）。
2. 修复队列（宜做）：退出挂起杀子进程树；smart_fetch wayback 退避 + 429 处理（§4.8）；句柄泄漏四热点（projection.py:183 / trace_facts.py:292 / run_meta_aegis.py:752 / preprocess.py:40）。
3. 决议记录：M26 主臂 **不开 --extra-tools**（免基线义务；工具价值另行小诊断臂）；床切 **nopixel-100**，M22-L0 与 M25 按逐题账重算对齐；`--runtime-policy-seed` 仅诊断臂。
4. R14 半批：保留归档，不 resume；91 digests 继续作证据源。
5. 复活通道零使用（§3-④）：gate_refusals→下轮 Evolver 的接线待查（M26 观察项，不阻断）。
