# M27 方差主攻 · 工程计划(08-24)

依据:docs/ghx-overnight-0823-research.md(过夜八路 + C1 普查 GO)。
目标:冻结(08-27)前完成"感官+法庭+稳定器"落码与烟测;花钱的验证由用户逐门拍板。
原则:commit-per-task;repo 现有接缝优先;不碰已判死方向(T-17/锥选)。

## Stage 0 · 缓存探针(独立,~0.5h,成本几分钱)【等拍板】
- T0.1 同前缀双调用打 litellm 网关(meta 负载形状),读 prompt_cache_hit_tokens。
  命中 → 修路由=全局最大零风险省钱;不命中 → 写死此损耗进成本章。

## Stage 1 · 修法庭(接线级,~半天)
- T1.1 回滚门接三尺:`run_meta_aegis.py:1272-1278` 接入 `compute_triage` 的
  stat_verdict/counterfactual 合格硬回归计数;总分-only 触发降级为"标记观察一轮"。
- T1.2 no_op 必须过机械门(头名候选强制走门)+ `orchestrator.py:613-617`
  critic_failed 提前 return 前先写 rejected 账(治 8 个零记录蒸发)。
- T1.3 配对法庭:门读数增加"predicted_stabilize/predicted_tasks 靶集配对
  McNemar"(复用 `harnessx/ghx/paired_read.py`,F21)。
- T1.4 noop_streak 基线修复(回滚后与 post-rollback 配置比较)。

## Stage 2 · 装感官(证据面,~半天)
- T2.1 variance_profile 生成器:task_history + U 迹 → 每轮一张不稳题剖面
  (名单、成败步数比、空结果率、exit 解剖)。全机械计数、零 LLM 判读
  (绕开 V3 钉死的流向列病理)。挂 aggregate_digests 链(flip_ledger 同款)。
- T2.2 Planner 喂桶:`PlannerInputs`+allowed_read_files 加 flip_ledger/
  variance_profile;`guidance.py:328-330,372-374` rebind 列表加 Planner;
  planner.md 模板加读法一句。
- T2.3 Critic hit_rate 底率校正(B3 接缝⑤:NEVER/PROB 桶命中按经验底率计价)。

## Stage 3 · 三稳定器落码(~半天,各带单测+6 题烟测)
- T3.1 EmptyStreakEscalationProcessor:连续 k 次空/无用结果 → 注入换策略
  nudge(不硬停——M13 教训,处方只到提示级)。
- T3.2 AnswerGroundingGate:终答须引用轨迹内非空工具结果的事实,否则强制
  补一步检索(= 把 V3"测不了的量"在答案关口强制)。
- T3.3 SoftBudgetCheckpoint:CostGuard 扩展,70-80% 预算处强制 best-guess
  提交(≈ 复活 M25 C-R2-02 机制,死因门已在 T1.1 修)。
- T3.0(前置,~0.5h)swingers_full.csv CONFIG-LINKED 列 × 28 题可修池交叉,
  剔除 config 混杂者,定稿靶集名单。

## Stage 4 · 决策门(花钱,逐门等拍板)
- G4.1 第一层验证(机制有效性,手工 ship):靶集配对双臂(±稳定器),
  2-3 轮,估 $40-80;预注册读数=配对 McNemar,阈值先写死再跑。
- G4.2 第二层验证(自演化,主菜):有感官 vs 无感官双臂,N 轮,看环是否
  自己 ship 出 stabilize 候选并过配对门。冻结例外级,与 9-07 时间线权衡;
  G4.1 为负则不开。

## 明确不做
- 消息保留策略(b)/Evolver 证据外置:纯省钱项,与提升主线无关,独立可选。
- 锥选回归集、T-17:已离线判死,不复活。

## 论文落位(V3 框架)
Stage 1-3 = 能力交付(效果未测如实标注)+ 十二错家族新条目(LCP 措辞噪声);
G4.1 数字进 CH6;G4.2 设计与预注册进 CH5/CH7;双阴性(锥选/T-17)进"图的限度"。

## 风险与缓解
- 3 天窗口紧 → Stage 1-3 全为小改+有现成模块,烟测走 6 题床。
- 稳定器重演 M13(−7)→ nudge 不硬停、靶集配对读数、回滚门已修三重缓解。
- 28 题池混 config-linked → T3.0 交叉先行剔除。
