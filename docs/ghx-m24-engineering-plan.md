# GHX M24 系统性修复工程计划（含 Efficiency / Cost / Performance 三维提升）

```
状态：v1.0 · 2026-08-18 22:00 · branch ghx/m13-cone-attribution @ d75adeb
前提：三臂在飞（21:48 活体核实）——M23_L1_ghx2 / M23_L2_ghx5 于 21:33:59 重启续飞
     （--start-round 4，现 R4/17）；L0 对照 = M22_L0_ghx0 续飞（08-17 22:18 起，现 R16/17）。
     三臂共同旗标：--num-rounds 17 --no-early-stop --evolve-max-steps 400 --search-backend serper。
     附录 A 锚点已由双路侦察回填，file:line 均为 2026-08-18 实测。
范围：系统性修复五层缺陷 + E/C/P 三维提升。纯工程计划，不含研究性新机制提案。
命名：M24 为暂定 campaign 编号（M23 之后一位）。任务号 M24-Txx，commit-per-task。
```

---

## 0. 总策略（三句话）

1. **读数搬家**。103 床同配置极差 4–6 题的噪声包络盖过预期效应，终局分数在当前预算下
   证明不了任何东西。主判读搬到**机制中间量**：cone 被引率、候选 evidence 引用率、
   config 桶 ship 数、budget_exceeded 率、ship 命中率。这些量噪声低、可直接归因到机制，
   也是论文 CH6 能站住的数字。终局分数只在配对设计 + 包络规则（§2）下作辅助读数。
2. **仪表出声**。四条记账通道会静默变假（P-15~P-18），根因是记账发生在 compose 之前。
   目标不是"仪表永不坏"，是"坏了立刻大声"：合成轮测试进 CI、loop_health 自动化、
   轮级 taint 标记、readout 自动排除 taint 轮。
3. **不再作废整臂**。M14 整臂作废、V6 终值不可判读、e2 床污染——三次事故全是起飞前
   可拦的。M24 起，任何 campaign 不过 **G-B preflight 门**不得起飞。

M23 七 commit 修了第二层（链条注入）与第四层局部（B3 outcome / B7g 拒因回流 / A4 步数）。
M24 = 判读 M23（WS0）→ 测量工程（WS1）→ 仪表制度化（WS2）→ 链条 v2（WS3，依 G-A 分支）
→ 债务清偿（WS4）→ 三维 Program（§8）。

---

## 1. 缺陷分层 → 工作流映射

| 层 | 缺陷（8-18 诊断） | M23 已覆盖 | M24 工作流 |
|---|---|---|---|
| 一 | 核心承诺无干净正数 | 在飞待读 | WS0 判读；其余 WS 合力，见 G-A 分支 |
| 二 | 证据→行动逐跳断裂（30%→0/31→gate 墙）；lift 只定位不开处方（M13 −7 题） | A2/B4/G1c/B5/B6/B7g | WS3：schema 强制引用 + 处方纪律 + 定向回放 |
| 三 | 噪声包络 ≥ 效应；三重污染；饿死混淆（L0 14%/L1 36%/L2 30%） | 仅饿死侧（A4/B3） | WS1 全部 |
| 四 | 反馈环静默变假；回归账恒空；noop_streak 基线错；灭因账读取端缺 | B3/B7g 局部 | WS2 全部 |
| 五 | L4 假门；adjudicate 未接线；loop_health 手动；活死人代码；文档漂移；L2=L3 | — | WS4 |

---

## 2. 全程硬约束（不可协商）

- **冻结期**：在飞臂每轮重启 rollout 子进程、从工作树 re-import。双臂落地前
  `harnessx/` 与 `recipe/` **零改动**。允许：`docs/`、新建独立脚本（不得被运行路径
  import）、新建测试文件（import 被测代码但不改它）。这是本计划第一风险项（§11-R1）。
- **litellm-only**：一切模型调用只走 litellm 网关，合规只看 base_url。judge/meta
  进程不吃 `--api-base`，只认环境变量——preflight 必须显式核这两类进程的 env。
- **路由探针**：模型名是会漂的路由键。起飞前按**工作负载形状**打探针（长上下文 +
  工具调用形状，不是 hello 探针）；不等欠费端点（-telecomjs 401 不会自己好）。
- **Windows 纪律**：同参数双 python = venv 垫片 + worker，查 ParentProcessId 再动手，
  误杀垫片 = 杀 run；CRLF 会炸 Critic 输出解析（P-26），preflight 带 CRLF 检查。
- **判读规则**（V6/103 床包络结论固化）：总分差 < 5 题不判、分层差 < 7 题不判；
  同配置读数必须组均值去偏；相似度类指标必须同时报对照系数（M12 Jaccard 对照=1.000
  的教训：没有对照值的相似度是废数）；去污子集只用 versioned 名单。

---

## 3. WS0 — M23 双臂判读与决策门 G-A

**目标**：双臂落地后 24h 内出判读备忘录，走 G-A 分支决定 WS3 深度。冻结期内先把
判读工具做出来（都是新文件，不碰运行路径）。

- **M24-T01 · readout.py v0（判读脚本）** — 新建 `recipe/gaia_evolver/readout.py`。
  从盘上重建 per-task × per-round 通过矩阵（数据源见附录 A-B4），输出：配对翻转表
  （pass→fail / fail→pass）、McNemar、同配置组均值去偏、历史包络带叠加、每轮 spend。
  跨臂对齐注意：活体核实三臂现进程都带 `--start-round 4`（M23 双臂 08-18 21:34 重启，
  R0-R3 与 R4+ 分属两个进程世代），R 序号跨臂**不可**直接对齐；世代边界在 readout 里
  显式标注，对齐按 bed fixture + rollout 内容，不按 R 序号。
  验收：对 V6 与 M22 两个已人工判读过的 campaign 跑金标回归，结论一致；单臂判读 <10 min。
  规模 M。
- **M24-T02 · 机制中间量判读** — T01 的第二输出面：败题 cone 被 digest 引用率、
  候选 evidence 直接引用率、config 桶 ship 数、五门逐门通过分布、budget_exceeded 率、
  ship 命中率（ship 后 N 轮配对效果）。M22 基线：~30% / 0/31 / 0 / — / 14·36·30% / 41·31·26%。
  验收：对 M23 双臂产出与 M22 同格式对照表。规模 S（依附 T01）。
- **M24-T03 · 落地审计** — 双臂落地后立即 `loop_health` 前后审计 + 泄漏抽查 +
  去污子集重算分。产出：M24 判读备忘录。规模 S。

**G-A 决策门**（三分支）：
- (i) 中间量动了、终局在包络内 → 论文走机制增益叙事；WS3 只做 T33，主力投 WS1/WS2/3D。
- (ii) 中间量不动（引用率仍 <50%、config 桶又归零）→ WS3 全量上：协议劝说升级为
  schema 强制（T30）。
- (iii) 终局超包络（≥5 题且分层 ≥7）→ **先同配置复测再信**（L0 +8.7pp 未复现的教训），
  复测确认后才进论文。

---

## 4. WS1 — 测量工程（把地板压到效应之下）

- **M24-T10 · 床与去污名单固化** — bed manifest + 泄漏审计产出的去污名单 + 惰性编辑
  彩票题名单做成 versioned fixture（内容寻址：manifest hash 进每轮 round header）。
  验收：readout 能按 fixture 版本切子集重算任意历史 campaign。规模 S。
- **M24-T11 · noop 轮 config hash 漂移修复（根因已定位）** — 轮头 hash =
  `sha256(round_config_path.read_bytes())`（`run_meta_aegis.py:663`），而该 YAML 由
  `current_config.copy(tracer=round_journal)` 序列化（`:657-661`），tracer 的
  `base_dir` 指向**轮专属** `R{n}/sessions/` 路径并被 `to_yaml` 一并序列化
  （`core/harness.py:1039/:1050`）——hash 纯粹随路径字符串漂，与语义无关。修法：
  轮头改为对 tracer-free 规范化 dump 计算（可与 `graph/identity.py` 的 genotype_hash
  并列各记一枚）。验收：连续 noop 轮 hash 恒等 + 单测。规模 S。冻结期后。
- **M24-T12 · 历史包络扩样（$0）** — 从既有 journal（V6、M22、103×3、L0 十六轮）
  离线收集全部同配置对，包络估计从 3 样本 → ≥8 对，分总分/分层两档。纯新脚本，
  冻结期可做。验收：包络带进 T01 报告底图。规模 M。
- **M24-T13 · Serper 结果缓存（record/replay）** — 搜索工具加 query-keyed 持久缓存
  （锚点 A-B2）。双臂共享同一缓存 = 消除 web 漂移这个跨臂混淆（特性，不是泄漏——
  两臂看到同一个网），同时省钱提速。带 `--no-web-cache` 一键回退与条目时间戳。
  验收：复跑同题 cache hit > 60%；缓存目录进 run dir 可审计。规模 M。冻结期后。
- **M24-T14 · judge 判分缓存** — (task_id, answer_hash) → verdict 持久化（锚点 A-B3）。
  重复判分零 API 调用；判分噪声（同答案不同判）顺带归零。验收：重放历史臂判分
  全命中缓存。规模 S。冻结期后。

---

## 5. WS2 — 仪表可信化（反馈环不再静默变假）

- **M24-T20 · 合成轮测试床（round simulation harness）** — 用假 rollout fixture
  （含 R 目录、结果文件、unfold 产物的最小合成集）驱动 orchestrator 全阶段跑一个
  完整 meta-round，断言**每本台账非空且 schema 一致**。回归账 off-by-one 恒空这类 bug
  从"烧 $255 后尸检发现"变成"CI 里 3 秒死"。故障注入三件套：空 rollout / 缺 R 目录 /
  CRLF 输出，各须被对应断言抓住。测试文件新建，冻结期可动工（不改被测代码）。规模 L。
- **M24-T21 · 记账时点搬迁** — 侦察实锤：pilot 一轮内全部写点（curve `:814`、
  task_history `:851`、`_score_and_gate` `:874`、rollback 三写 `:919-937`、noop_streak
  `:987/:990`、shipment 读 `:999`）都发生在 compose（`run_meta_aegis.py:1004` 的
  `current_config = candidate_cfg`）**之前**；refuted / gate-refusal 类账则在
  `meta_agent.evolve()`（`:974-982`）内部由 orchestrator 写。改法：compose 后统一
  落账（compose 成为权威事件），改动跨 pilot 与 orchestrator 两文件。验收：T20 断言
  "账面 config = compose 后 config"。规模 M-L。冻结期后。
- **M24-T22 · 回归账 off-by-one 收敛** — 重算点全清单见 A-A4（`regressions.py:124`
  的 `by_round.get(round_n - 1)`、`orchestrator.py:310/:317`、`run_meta_aegis.py` 五处）。
  注意 `orchestrator.py:305-310` 对 −1 有成文论证（evolve 开始时 task_history 只有
  0..N-1 轮）——所以先用 T20 合成轮 + L0 历史重放**判定哪一处语义真错**，再把全部
  手算收敛到单一 `round_of_rollout()` helper。验收：合成轮回归账非空；L0 重放报出
  已知回归。规模 S-M。冻结期后。
- **M24-T23 · noop_streak 基线修复** — 现机制：evolver 输出与输入**字节比较**定 noop
  （`run_meta_aegis.py:987/:990`），evolve 崩溃也清零（`:1036`），streak≥2 且未带
  `--no-early-stop` 即停（`:1021-1032`）。L0 R13 误报收敛的根因就在这套判据上——
  字节比较与 T11 的 tracer 序列化互相纠缠，崩溃清零还会掩盖真收敛。验收：L0 十六轮
  历史重放，早停点符合人工判定。规模 S。冻结期后。
- **M24-T24 · loop_health 接线 + taint 位** — 现状：`harnessx/ghx/loop_health.py`
  五检（reputation 空桶 P-15a / hit_rates 解析不到 P-15b / ship 记账但 merged.yaml
  未落 P-9·P-16 / scoreboard 假聚合 / digest 零产出 P-8），纯 CLI（`:247-270`），
  全库零生产调用。接线点：pilot 每轮 task_history 落账后（`:851` 后）与 evolve 返回
  后各跑一次，写 `loop_health.json` 进轮目录；任一 BROKEN → 该轮打 **taint 标记**，
  readout 自动排除，首版只告警不硬拒（避免误杀整臂）。验收：故障注入轮被自动标记并
  从 T01 报告剔除。规模 M。冻结期后。
- **M24-T25 · 灭因账读取端补全** — refuted 签名已进 novelty gate；补 Planner/Digester
  上下文注入端，与 B7g 的 gate_refusals.md 回流汇成一份"死因简报"。顺带收编 TODO/GS-D
  的 HX-6（Evolver 只读 landscape.md、从不读原始证据——G1c 已部分处置，此处补余量）。
  验收：Planner 输入里可见上轮死因（G1c 覆盖面检查同 T33）。规模 S-M。冻结期后。

---

## 6. WS3 — 证据→行动闭合 v2（依 G-A 分支启动）

- **M24-T30 · schema 强制引用**（G-A(ii) 触发）— 劝说（cone-first 协议）不够就上结构：
  digest 结论条目必须带 evidence ref；候选 manifest 必须带 `evidence:` 字段；结构门
  扩展校验 ref 可解析到 facts.md 行 / cone 签名，解析失败即拒。**梯度上线**：先警告轮
  （只记不拒）再硬拒轮，防止把候选产出率直接打到 0。规模 M。
- **M24-T31 · 处方纪律（定位≠处方）** — M13 的 −7 题教训制度化：同一机制的**首个**
  干预必须是 parametric（mutate_params 桶）且可回滚；structural 干预必须有该机制
  parametric 尝试的数据在先。落点：Planner guidance 文本 + gate 检查桶类型对照该机制
  干预历史。验收：合成轮里 structural-first 候选被拒并记因。规模 M。
- **M24-T32 · 定向反事实回放** — counterfactual gate 的 k=3 从任意轨迹改为：候选
  predicted_impact 的 core 集内定向抽 k 题回放，要求方向不变差。只对过了前四门的候选
  跑（控成本）。这是把"ship 命中率 41/31/26%"提上来的 pre-ship 手段。规模 M-L。
- **M24-T33 · regression_diffs 消费闭环** — B4 产物（同题跨轮锥差分）确认进 Planner
  输入；新翻败题（pass→fail）自动优先进下轮 target 集。验收：G1c 覆盖面清单里
  regression_diffs.md 在列且被引用。规模 S。

---

## 7. WS4 — 债务清偿（表里如一）

- **M24-T40 · L4 假门改真** — `_gate_u_resolver` 恒 None 的真原因是 pre-ship 拿不到
  候选的 U（P-14）。重定义 L4 门为 **pre-ship 可算**检查："候选必须触到它引用的 cone"
  ——genotype diff 与 cone 目标的静态重叠校验。这同时就是 T30 的执行器，一门两用。
  备选：L4 从阶梯移除（L4=L3 归并）。推荐前者。规模 M。
- **M24-T41 · adjudicate.py 接线（report-only）** — 侦察定性：Stage 5 = 上一轮 ship 的
  hit_rate 复核 + `hit_rate < 0.5` 自动回退（`adjudicate.py:38-48`）；orchestrator 明写
  "intentionally NOT imported"（`orchestrator.py:21-24`，TODO 块 `:206-213`：Stage 5 属
  跨轮 pilot driver 职责）；recipe 层 ship-aware rollback 只是它的聚合级近似。裁决：
  在 pilot 轮循环接线为 **report-only**（`auto_revert_enabled=False`），产出直接成为
  T02 的 per-ship 命中率与 P4 清退报告的数据源；灾难回退仍归现有 rollback。规模 S-M。
- **M24-T42 · 半死代码清偿 + docstring 纠偏** — `_score_and_gate` 存在三份拷贝；
  `run_meta_aegis.py:874-884` 这份的裁决被明文丢弃（`:867-873` "no longer act on its
  reverted_cfg"，只剩 best_so_far 喂终局打印）→ 改为显式 best-tracker 或删调用
  （`run.py:1626` 自用那份不动）。`num_evolvers` 全链可传但 orchestrator 不再派发
  （`orchestrator.py:181`），拆除牵 CLI + 双 recipe + 6 个测试文件 → 先文档级
  deprecate，不硬拆签名。launcher docstring（3 角色→4 角色、L2 旗标集）纠偏。规模 S-M。
- **M24-T43 · 命名消歧** — ProposalSession `last_config_hash` → `config_bytes_sha`；
  `attribution_graph.py`（G2 签名核对）与 `evidence_files.py`（G1 cone/lift）模块
  docstring 互引明示"同词不同物"；论文 glossary 同步。规模 S。
- **M24-T44 · 阶梯重排** — LEVEL_FLAGS 里 L2=L3 完全相同。裁决：归并（阶梯变 5 级）
  或把 GUIDANCE 拆回 L3（恢复单调递增语义）。牵动 launcher 测试与论文阶梯表，随 T42
  一并出 commit。规模 S。
- **M24-T45 · diff_graphs 误传纠正** — 侦察**证伪**原假设：`diff_graphs`
  （`graph/edit.py:314-370`）是全结构差分，可产 REMOVE_NODE / INSERT_NODE /
  MUTATE_INACTIVE / CHANGE_DEPENDENCY 四类 op。真实 known-gap 是另一条：
  MUTATE_INACTIVE 不校验目标是否在活跃路径上（`graph_proposals.py:40-42` 工具文档
  已明示）。动作：纠正口径（本计划、流程图 artifact、论文相关句），可选补
  active-path 校验。规模 S。

---

## 8. 三维提升 Program

### 8.1 Efficiency（单位时间出多少可信信号）

- **E1 · G-B preflight 门（最大头）** — 起飞前自动串跑：T20 合成轮 + loop_health 基线
  + 网关工作负载形状探针 + judge/meta env 核验 + config hash 稳定性（T11 验收）+
  CRLF 检查 + bed fixture 版本核对。产出 preflight 报告，无报告不起飞。
  历史三次整臂事故（M14/V6/e2）在此全部可拦。
- **E2 · 判读自动化** — T01/T02：判读从数小时人工 → <10 min 脚本，且消灭人工判读
  自身的错误率（M12 Jaccard 废数、V6 终值误读均为人工判读事故）。
- **E3 · 早停修复** — T23：不再白烧真收敛后的轮次，也不再误停丢信号。
- **E4 · smoke 分级明文化** — 6 题床只判"崩不崩"（±33.3pp，禁判分）、24 题级中床判
  方向、103 床才算数。写进 SOP-SMOKE-REVIEW，readout 对小床分数拒绝输出结论字段。
- **E5 · 并行度核查** — 依锚点 A-B1 的 worker 数与网关余量，探针通过后评估上调；
  目标把 93 min/轮 压向网关允许的下限。先测后动，不与在飞臂抢配额。

### 8.2 Cost（$ / campaign）

- **C1 · 饿死回收验证** — budget_exceeded 是纯亏损支出（烧满预算返回 fail）。
  M23 A4/B3 已上药，M24 用 T02 验证：L1 36% / L2 30% → 双双 <15%。
- **C2 · judge 缓存（T14）**、**C3 · serper 缓存（T13）** — 复跑与回放场景的主力省钱项，
  同时各自消一类噪声（判分抖动 / web 漂移）。
- **C4 · 成本台账进判读** — 每轮按角色×阶段的 spend 表（字段见锚点 A-B4）。无账不优化；
  e2_A 1.26B token、103×3 $255/93min 这类数今后每轮自动可见。
- **C5 · 模型分层复核** — Digester 已 flash。核对 Planner 可否降档；**Critic/Evolver
  不动**（否决质量与编辑质量是命）；**被测系统 rollout 模型绝对不动**（那是处理组本身）。
- **C6 · meta 会话步数** — A4 StepCountdown 已上，验证 400 步烧穿归零；上限进 preflight。

### 8.3 Performance（床上的分）

- **P1 · 饿死回收的机械分** — L1 36% 的 budget_exceeded 里有历史可过题；M22 对单个
  L2 ship 的预测就有 27 题量级的 at-risk 面。这是最大的单项预期涨分来源，与 C1 同源。
- **P2 · config 桶落地** — B6 mutate_params 打开的 parametric 干预（阈值/窗口类）是
  M13 教训指向的低风险涨分杆；M23 在飞 R2 已见首个 config 桶 ship（待判读确认）。
- **P3 · ship 精度** — T31 处方纪律 + T32 定向回放，把"ship 了但没用"（命中率
  41/31/26%）拦在 pre-ship。
- **P4 · 中性 ship 清退报告** — rollback 只抓灾难（−5pp∧−3 题），中性 ship 无人清、
  复杂度净累积。每 5 轮产 ship 配对效果清单，**人工**裁决 revert（报告制，不自动清退）。
- **P5 · 锥差分定向** — T33：pass→fail 新翻题优先进 target，把 ~30% 的 cone 引用率
  变成"最疼的题必然在案头"。

### 8.4 交叉矩阵

| Initiative | Eff | Cost | Perf | 依赖任务 | 论文 |
|---|---|---|---|---|---|
| G-B preflight | ●● | ○ | — | T20/T24/T11 | CH5 validity |
| readout 自动化 | ●● | ○ | — | T01/T02 | CH5/CH6 |
| serper/judge 缓存 | ● | ●● | — | T13/T14 | CH5 threats |
| 饿死回收验证 | — | ●● | ●● | M23 已上+T02 | CH6 |
| 处方纪律+定向回放 | — | ○ | ●● | T31/T32 | CH4/CH6 |
| schema 强制引用 | — | — | ● | T30/T40 | CH4 |
| 早停+taint | ● | ● | — | T23/T24 | CH5 |
| 模型分层复核 | — | ● | — | C5 | — |
| 中性 ship 清退 | — | ● | ● | P4 | CH6/CH7 |

●●=主收益 ●=次收益 ○=顺带 —=无

---

## 9. 阶段排期与依赖

- **P0 · 冻结期（现在 → M23 双臂落地；R4/17 起算余 13 轮，预计 08-19 晚）** —
  L0 臂 R16/17 数小时内先落，可先拿它演练 T01 单臂判读。冻结期只动新文件/docs/tests：
  T01/T02（readout）、T12（历史包络）、T10（fixture）、T20（合成轮测试床，新测试文件）、
  本计划评审。（graph-hardening v5.3 为独立基座轨，未实施，不进 M24 排期，见 A-A10。）
- **P1 · 判读（落地后 24h）** — T03 审计 → G-A 备忘录 → 分支裁决。
- **P2 · 仪表与测量（解冻后第一批码）** — T21/T22/T23/T24/T25 + T11 + E1 组装。
  这一批全绿之前不起飞任何新臂。
- **P3 · 链条与债务** — G-A 分支决定的 WS3 子集 + T40–T44。
- **P4 · M24 campaign 起飞** — 过 G-B；带 C2/C3 缓存、readout 自动判读、taint 位。
  配对双臂设计沿用 M23（同 seed 组、同 bed fixture）。

依赖链：T01 ← G-A；T20 ← T21/T22 验收；T11+T20+T24 ← E1；E1 ← P4 起飞。
Commit 纪律照旧：commit-per-task，`feat(ghx)/fix(aegis)/test(recipe)` 前缀，测试同步。

---

## 10. 验收指标汇总

| 指标 | 现状基线 | M24 目标 |
|---|---|---|
| 候选 evidence 直接引用率 | 0/31（M22 ⚠5） | 警告轮 ≥50%，硬拒轮后 schema 强制 100% |
| 败题 cone 被引率 | ~30%（⚠10） | ≥70% |
| budget_exceeded 率 | L1 36% / L2 30% | 双双 <15% |
| config 桶 ship | M22 全程 0 | ≥1 / campaign（M23 在飞已见候选） |
| ship 命中率（ship 后配对为正比例） | 41/31/26% | >60% |
| 整臂作废 | M14=1、V6 判读失败、e2 污染 | 0（G-B 拦截） |
| 单臂判读耗时 | 数小时人工 | <10 min 脚本 |
| 包络估计样本 | 3（67/71/69） | ≥8 同配置对 |
| judge 重复判分 API 调用 | 全量 | 缓存命中 >60% |
| 回归账 | 恒空（off-by-one） | 合成轮非空断言 + L0 重放报出已知回归 |
| noop 轮 config hash | 漂移 | 恒等 + 单测 |
| 早停 | R13 误报 | L0 历史重放符合人工判定 |

---

## 11. 风险登记

- **R1 · 冻结期破戒**（最高）：在飞臂每轮 re-import 工作树，任何 harnessx//recipe/ 改动
  = 中途换药 = 双臂作废。对策：P0 白名单（docs/新脚本/新测试），改动前自查 import 链。
- **R2 · 路由漂移/网关 401**：探针按工作负载形状打；不等欠费端点；judge/meta 只认 env。
- **R3 · 缓存引入陈旧性**：serper 缓存条目带抓取时间戳，campaign 起飞时可选整体刷新；
  跨臂共享是特性（同一个网），跨 campaign 复用须显式声明。
- **R4 · T32 回放成本失控**：只对过前四门候选跑、k 有上限、按 core 集抽样。
- **R5 · schema 强制打死候选产出**：Evolver 学不会写 ref → 产出率归零。对策：梯度上线
  （警告轮先行），G-A(ii) 才启动。
- **R6 · 判读脚本自身有 bug**：用 V6/M22 两个已人工判读的 campaign 做金标回归，
  不过金标不用于新判读。
- **R7 · Windows 特有**：venv 垫片误杀、CRLF、路径空格；全部进 preflight 检查单。

---

## 12. 论文回填映射

- 五层缺陷分层 → CH3（诊断章骨架，开环诊断提法已在）。
- G-B preflight / taint / 合成轮 → CH5 实验设计"validity engineering"一节（现成材料）。
- T01/T02 判读纪律 + 包络扩样 → CH5 读数协议 + CH7 threats 主轴。
- G-A 机制中间量对照表（M22 vs M23） → CH6 主结果表。
- M13 定位≠处方、M22 链条衰减、L0 无踏车 → CH6/CH7 负结果资产（已有）。
- T31 处方纪律、T30 schema 强制 → CH4 方法章的机制条目。

---

## 附录 A · 代码锚点表（侦察回填）

| 锚点 | 主题 | file:line | 备注 |
|---|---|---|---|
| A-A1 | loop_health 五检与调用方式 | `harnessx/ghx/loop_health.py:101-244`（五检），CLI 入口 `:247-270` | 零生产调用；仅测试与 deviations 文档提及 |
| A-A2 | adjudicate.py 功能定性与调用面 | `harnessx/aegis/stages/adjudicate.py:18-48`；拒接线注释 `orchestrator.py:21-24`、TODO 块 `:206-213` | Stage 5 = 上轮 ship hit_rate<0.5 自动回退；零生产调用；recipe rollback 是其聚合级重实现 |
| A-A3 | compose 调用点与台账写点顺序 | compose = `run_meta_aegis.py:1004`；写点 `:663/:814/:851/:874/:919-937/:987-990/:999` 全在其前 | refuted/gate-refusal 账在 orchestrator 内（经 `:974-982` 的 evolve() 进入） |
| A-A4 | round index 重算点清单 | `aegis/data/regressions.py:73/:124/:251`；`orchestrator.py:310/:317`；`run_meta_aegis.py:625/:960/:972/:980/:1001` | `orchestrator.py:305-310` 对 −1 有成文论证（evolve 时 task_history 只有 0..N-1） |
| A-A5 | noop_streak 计算/消费点 | `run_meta_aegis.py:590/:987/:990/:1036`；早停 `:1021-1032`；旗标定义 `:1119-1122` | evolve 崩溃分支 `:1036` 也清零 |
| A-A6 | _score_and_gate 位置与调用面 | 核 `run.py:1626`；`run_meta_aegis.py:69`（import）、`:874-884`（调用）、`:867-873`（裁决明文丢弃）；第三份拷贝 `run_meta.py:449` | 半活死人：只喂 best_so_far 终局打印 |
| A-A7 | num_evolvers 引用面 | `aegis/__init__.py:37/:107`；`orchestrator.py:181`（"no longer dispatches"）；`cli.py:9/:27/:39`；gaia/tau2 双 recipe；6 个测试文件 | 全链可传、无人消费 |
| A-A8 | diff_graphs 可产 op 集 | `harnessx/graph/edit.py:314-370`：REMOVE_NODE / INSERT_NODE / MUTATE_INACTIVE / CHANGE_DEPENDENCY | 原"只产 MUTATE_INACTIVE"假设**证伪**；真 gap = MUTATE_INACTIVE 不查 active path（`graph_proposals.py:40-42`） |
| A-A9 | 轮头 config hash 计算与进 hash 字节 | `run_meta_aegis.py:657-663`；tracer 序列化进 YAML：`core/harness.py:1039/:1050` | 根因 = 轮专属 `R{n}/sessions/` 路径随 tracer 入 YAML；与 `graph/identity.py:23-67` 三哈希、`graph_proposals.py:160/:1070` 的 config_bytes 哈希是三个不同概念 |
| A-A10 | 既有清单吸收 | `experiments/docs/TODO/GRAPH-MECHANISM-ASSESSMENT.md`（graph/ 零消费者台账，08-08，L5 前旧账）；`TODO/GS-D-…md`（HX-5 跨任务聚合缺件→G1 已大部处置；HX-6 Evolver 只读 landscape→G1c 部分处置）；`docs/aegis-vendored-deviations.md:1401-1467`（P-26 + M23 重跑拓扑）；`docs/graph-hardening-v5.3-engineering-plan.md`（P0-P7 基座硬化，未实施，独立轨） | M22/M23 无独立计划文档，账在 runs/ 目录与 memory |
| A-B1 | rollout 并行度与预算旗标 | `--concurrency` 默认 6（`run_meta_aegis.py:161/:1062`），Semaphore `:689`，per-task 注入 `:698`；预算 = `--max-cost` $15（`:160/:1060`）+ `--max-steps` 20（`:159/:1061`），**无 token_budget 旗标**；meta 侧 `--evolve-cost` $100（`:162/:1063`）、`--evolve-max-steps` GHX 专属默认 200、活臂 400（`run_meta_aegis_ghx.py:522-533`） | `run_variant_pool.py` 是独立 pass@k 引擎，**不是** GHX 的 pool runner |
| A-B2 | serper 调用点与现有缓存 | `harnessx/tools/contrib/serper_search.py:64`（端点）`:91-101`（HTTP）`:157/:235`（env key）；接线 `run_meta_aegis.py:566` | 全路径**零缓存**（serper_search.py 与 builtin/web_search.py 均 0 命中）——T13 绿地 |
| A-B3 | judge 调用点/模型/env/持久化 | judge 恒走 `--meta-model`（`run_meta_aegis.py:541/:554/:563-565`）；env-only 解析 `llm_judge.py:379-409`（ANTHROPIC_API_BASE / OPENAI_API_BASE，无 --api-base 通道）；verdict 只存内存 `_verdict_sink`（`:368/:377`），落盘仅单向写轨迹 frontmatter | evaluator 先精确匹配、无 ground truth 才 LLM 兜底（`benchmarks/gaia/evaluator.py:207-239`）；抽取式 judge 逐任务跑——T14 缓存键 (task_id, answer_hash) 注入点在 llm_judge |
| A-B4 | 判读数据源文件与字段 | 轮级 `runs/<tag>/curves.json`（round/config_hash/evolve_status/passed/pass_rate/cost_usd/total_tokens/total_steps/level_stats）；题级 `data/task_history.jsonl`（round/task_id/level/passed/exit/steps/cost_usd/tools_used，**无 tokens**）；题级 tokens + judge verdict：`R{n}/trajectories/*.md` frontmatter；事件面 `audit.jsonl` / `reputation.json` / `data/ship_outcomes.json` / `data/rejected_candidates.jsonl` | T01 只需前三层，纯 JSON/JSONL/YAML；budget_exceeded 读 task_history 的 `exit` 字段 |
| A-B5 | 在飞臂路径/轮数/进程（21:48 实测） | `runs/M22_L0_ghx0`（L0，R16，08-17 22:18 起）；`runs/M23_L1_ghx2`（ghx-level 2，R4，21:33:59 重启）；`runs/M23_L2_ghx5`（ghx-level 5，R4，21:33:59 重启）；各为垫片+worker 双进程，另有 6 个工具沙箱 python 在跑 | 共同旗标：--max-tasks 0 --num-rounds 17 --k-all 1 --search-backend serper --no-early-stop --evolve-max-steps 400 --start-round 4 |
| A-B6 | 早停旗标与消费点 | 定义 `run_meta_aegis.py:1120-1124`；消费 `:1021-1032`（streak≥2 停；else 分支明写"臂在不同轮被切断会毁掉全部跨臂读数"） | 三活臂均带 --no-early-stop = 固定 17 轮设计 |
