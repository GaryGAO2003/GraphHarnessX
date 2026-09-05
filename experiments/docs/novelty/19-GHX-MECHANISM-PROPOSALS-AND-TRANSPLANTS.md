# 19 · GHX 机制方案册：五案、裁决与移植候选目录

```
状态：v2 · 2026-08-19 · 记录自 08-18/19 出方案轮 + 六轮文献侦察（§5 移植目录已回填）
定位：论文弹药库（CH4 动机 / CH7 related work / future work）+ M25/G3 施工候选
规矩：出方案按 CLAUDE.md 硬规则 F 修正执行；先例全部点名（工作名+年份+出处），
     引文经 researcher 网上核实，非记忆复述。
关系：M24 计划（docs/ghx-m24-engineering-plan.md）明文不含研究机制——本册是它的姊妹篇。
```

---

## 0. 背景：为什么出这一轮

M24 修的是工程与测量（可测性）；本轮回答"机制本身还缺什么"。诊断出的机制层问题
四组十一条：

- **A 归因引擎**：A1 观察性关联冒充因果（lift 反向因果，loop_detection 4.93 即症状
  节点得分）；A2 统计地基薄（小整数、无区间、无多重比较控制）；A3 结构面盲区
  （语义性败因共享同一锥；CONTROL 边零区分度；锥并集双语义）。
- **B 处方端**：B4 定位≠处方是结构性的（动作空间=config 空间，与主导败因近正交；
  L0 十六轮包络内震荡=平坦景观证据）；B5 干预假设由同级 LLM 自由生成，五门不筛
  因果有效性。
- **C 反馈环**：C6 k=1 单采样信用分配（噪声>决策粒度）；C7 元层无梯度（predicted_impact
  从不回评，Evolver 不因预测错而变准）；C8 无简约压力（中性 ship 累积）。
- **D 方法学**：D9 选择与验证同床（无 held-out，一切增益 in-sample）；D10 非平稳
  环境（证据落后应用一个世代+一个世界）；D11 无安慰剂对照（图证据 vs 多喂结构化
  文本不可分）。

论文三大威胁 = A1 + B4 + D9。

---

## 1. 五个方案（出方案模式原文，F 修正生效）

配额账：C1（自判成功率<30%）=方案二、五；C2（否定公认前提）=方案一；
C3（跨域搬运）=方案一（系统）、三、五（数据库查询优化）；C4（正面冲突占位论文）=方案二。

### 方案一【C2·C3-系统】干预化 lift
观察轨迹的共现统计导致 lift 奖励症状节点（loop_detection 4.93 即反向因果），机制是
每轮 rollout 划出小份题跑机制扰动变体——锥反推最小致败集选扰动点，lift 从"锥内共现
比"换成"扰动翻转率"。所有人都假设（AFlow、GEPA、DGM 到 Who&When 一脉）观察到的执行
轨迹足以归因；我主张此前提错：k=1 轨迹下归因不可辨识，辨识必须购买干预样本。若我错，
错在"机制级扰动可分离"假设——扰动单个处理器会级联重写整条轨迹，翻转率同样落不到单
机制头上。HarnessX 上动的数字：ship 命中率（41/31/26%）与 M13 类误处方复发率；动的
段：evidence_files 的 lift 生成端。
先例：Coz（SOSP 2015）干预语义；Molly/LDFI（SIGMOD 2015）lineage 定注入点；DoVer
（arXiv:2512.06749）单事故事后干预。搬运变的一步：从单事故事后诊断改成**每轮常驻
扰动采样喂群体级 lift**，LDFI 的 SAT 步换成锥成员枚举。

### 方案二【C4·C1】加噪保留集
同床选择+验证导致一切自演化增益不可信，机制是 gate 与 rollback 对床的每次询问都走
加噪应答通道，另留全程盲的保留子集只在 campaign 终点揭一次。正面冲突 Darwin Gödel
Machine（Zhang/Hu/Lu/Lange/Clune, arXiv:2505.22954, ICLR 2026）：其档案准入与汇报
读数取自嵌套题集（60⊂200；50 子集 38.0% 对全集 30.7%）——我主张这个核心设计选择是
错的。若我错，错在"每轮少量自适应询问×17 轮足以过拟合 103 题"这一假设。动的数字：
新增的"选择分−保留分"差值（第一次可报告的泛化增益）与 ship 后回滚率；动的段：ship
判定与回滚双阈值的读数来源。
先例：The Reusable Holdout（Dwork et al., Science 2015/STOC 2015）。搬运变的一步：
被保护对象从分析员改成 orchestrator 自己，应答噪声要与 ±4–6 题包络**合成**而非独立
叠加。

### 方案三【C3-数据库】what-if 估价段
候选定价全靠真跑床导致 Evolver 一轮只敢提一两个候选，机制是在五门之前插零执行估价
段：以锥特征+task_history 拟合的翻转判别器为代价模型，候选先拿"预测翻转集+期望Δpass"
定价，Evolver 会话内廉价迭代多个候选再送门，床只给过门者定终价。若我错，错在"翻转有
可预测成分"假设——翻转若主要由 provider 抖动决定，代价模型学到的只是噪声形状。动的
数字：candidate→ship 转化率、每 ship 的验证开销、IV-3 类格式炸弹在估价段即死；动的
段：Stage-2 与 Stage-4 之间新增的估价环。
先例：AutoAdmin What-If（Chaudhuri & Narasayya, SIGMOD 1998）+ Selinger 代价模型
（SIGMOD 1979）。搬运变的一步：代价模型从解析式换成由本环 ship/拒绝史在线更新的判别
器——估价误差本身回流，相当于优化器统计信息自更新。

### 方案四【谱系教训搬运】修复模板算子库
自由文本处方导致定位对了药方错（M13 −7 题），机制是把处方约束为"机制类→参数化修复
模板"的实例化：每类机制节点配正反两方向模板与参数域，Evolver 只做选模板+填参，模板
库由本环 ship 史与 gate 拒因跨轮归纳、冷启动用手写种子。若我错，错在"harness 失败可
归入有限修复类"假设——败因长尾会把模板覆盖率封在无意义低位。动的数字：config 桶
ship 数与命中率、IV-3 拒绝归零；动的段：Evolver 提案面（mutate_params 桶升级为模板
实例化）+ structure gate 的模板-机制匹配校验。
先例：PAR（Kim et al., ICSE 2013）以人写补丁模板替代随机变异；Tarantula（ASE 2005）
→GenProg（ICSE 2009）是"可疑度≠修复"的原始教训。搬运变的一步：模板不从外部补丁库
挖，从**本环自己的采纳/灭因史**在线归纳。

### 方案五【C1·C3-数据库】半环证源锥
锥的集合语义导致反事实只能靠重跑，机制是把 U 的 DATA 边升格为半环注记：节点输出携带
"如何由上游导出"的证源多项式，"拔掉机制 X 后终点是否仍可导出"变成多项式删元求值——
零重放的代数反事实分，直接替换共现 lift。若我错，错在"LLM 步的信息流可半环化"假设
——自然语言经模型混合不满足任何半环同态，多项式只是假精确。动的数字：锥区分度（同
签名不同败因的塌缩率）与换用代数分后的处方命中率；动的段：unfold 记录端 +
evidence_files 求值端。
先例：Provenance Semirings（Green/Karvounarakis/Tannen, PODS 2007）、Why and Where
（Buneman et al., ICDT 2001）。搬运变的一步：注记不再跟关系代数走，跟工具调用与消息
RD 走；模型步的传递用"输出中实际复用的上游片段才进多项式"近似。

---

## 2. 图相性分类

| 方案 | 图相性 | 原版 AEGIS 能装吗 | 装上原版是什么样 |
|---|---|---|---|
| 一 · 干预化 lift | 图=准星 | 能装执行器，定向退化 | 无锥定向=散弹（每轮 ~4500 变体）或 LLM 读日志猜（Who&When 步级 14.2% 那条路） |
| 二 · 加噪保留集 | 无关 | 完全能 | 一模一样，纯实验方法学 |
| 三 · what-if 估价 | 图=特征引擎 | 能，但退化 | 无 genotype diff ∩ 锥就回到 LLM 自由猜影响面=B5 之前的 predicted_impact（41/31/26%） |
| 四 · 模板库 | 低 | 基本能 | 模板按 config 键分类实例化，原版够用；图只多给瞄准 |
| 五 · 半环证源锥 | 图独占 | 不能 | 改的就是 U 边语义本身，无 unfold 即无注记对象 |

推论：二、四装上去两臂同涨、对照中抵消——抬平台不抬"图有用"主张。能撑论文差分的
只有一、三、五。一与三还能把"图 vs 无图"内化为机制内部件对照（定向效率差/特征增益
差），在 ±4–6 题地板下这是唯一便宜的差分读数。

---

## 3. 裁决（2026-08-19，用户约束：必须图基础）

### 3.1 六判据矩阵

| 判据 | 一 · 干预化 lift | 三 · what-if 估价 | 五 · 半环证源锥 |
|---|---|---|---|
| 三大威胁覆盖 | 正面打 A1；兼作 B4 平坦景观诊断仪 | 打吞吐/命中率，前提证据已可信 | 打 A3，不碰前三 |
| 图对照内化 | 锥 vs 随机定向的每美元翻转数 | 带/不带锥特征的预测力差 | 图独占，无对照 |
| 文献位置 | **缺口实锤空着**（环内常驻干预证据无人做） | 被占邻位（Agentic Predictor 84.4%；FLORA GNN ~84%），差分=预测编辑的逐题翻转 | 半环穿 LLM 无直接命中，但仪器被价卡死 |
| 基建复用 | rollout 机器+锥+M24 record-replay 缓存 | task_history+candidate_surface，另需训练环 | 改 unfold schema+每节点 32 次消融前向 |
| 成本结构 | 每轮有界扰动预算（先例 $0.05–0.15/修复；DoVer 3 复跑） | 建成后 ~$0/轮 | 32× 前向/节点；网关 logprob 不稳 |
| 统计功率 | 机制粒度跨题合并（10 题×3 复跑×开关=60 伯努利/主张），绕开分数地板 | 受训练样本限（轮对 ~50–100 个，薄） | 不适用 |

### 3.2 终裁

**方案一为主线；方案三是它的下游（一产[编辑→逐题翻转]数据、三学定价、三反指挥一的
扰动预算），不是对手；方案五保持 <30% 标记，写 future work。**

方案一赢在四点：(1) 位置空且可行性刚被验证——干预信号在 GAIA 分布上有实测（REFLECT
干预纠正 54.2%、DoVer 翻 18–28% 败局），但全领域停在事后诊断/离线造数据，环内常驻
证据源无人占；(2) 打论文第一威胁，M13 负结果从尴尬变成动机，叙事弧完整；(3) 图价值
首次机制内可测（对照格）；(4) 随机性有现成打法（CAR 承诺点冻结、DoVer 3 复跑、
record-replay 挂具族=M24 T13/T14 同基建）。

### 3.3 方案一在 GHX 的第一形态

新旗 `HARNESSX_GHX_INTERVENE`：pilot 每轮 rollout 落账后，从 lift 表取头部机制、从锥
取其 at-risk 题样本，跑机制开关/参数翻转变体 rollout（serper/judge 走共享缓存冻结
世界，LLM 段活跑、3 复跑或承诺点冻结压方差）；产物 `interventional_lift.jsonl`
（机制×方向×n×翻转率×区间）并入 facts.md 新列；G1c cone-first 协议升级为
interventional-first；扰动预算内置锥/随机对照格。会动的三个数：ship 命中率、M13 类
误处方复发率、每美元验证翻转数（锥 vs 随机）。

### 3.4 为什么"原版也能装"不成立（三处承重 + 一个特性）

1. **定向**：config 只有机制清单无逐题参与；原版轨迹只能 LLM 猜（步级 14.2%）；
   无定向则预算=笛卡尔积（~25 机制×30 败题×2 方向×3 复跑≈4500 变体/轮）。锥给确定
   性参与+DATA 祖先约束+lift 预排序+at-risk 集，砍到 ~150。定向即全部经济学。
2. **处理器盲区**：processor 类机制（loop_detection/memory/context）在原版轨迹逐题
   零痕迹（tools_used 只record工具）；而 Evolver 编辑的恰是这一类。U 的 `proc:` 节点
   （M23 B1）是全系统唯一逐题 processor 参与账。对目标机制类，原版不是退化，是无输入。
3. **落点**：翻转率要住进 lift 表/facts.md/G1c 注入/L5 core-halo 纪律——评价与消费
   面就是 G1；原版装=重造 GHX。
4. **特性**：执行器图无关恰是论文资产——图成为机制内可消融部件，"图值多少"变成每
   美元翻转数之比这个干净读数；全图独占机制（如方案五）反而永远证不了图的边际价值。

---

## 4. 文献底账（全部经网上核实，2026-08-18/19）

### 4a. 经典先例（11 条，两处纠正）
- Coz: Finding Code that Counts with Causal Profiling — Curtsinger & Berger, SOSP 2015
  （最佳论文）。虚拟加速=运行时干预实验。
- Lineage-driven Fault Injection (Molly) — Alvaro et al., SIGMOD 2015。lineage 反向
  推理 + SAT 解最小致败故障集，只注入那些。
- The Reusable Holdout — Dwork et al., Science 2015 (349:636)；姊妹篇 STOC 2015。
  差分隐私式加噪保留集应答。
- Provenance Semirings — Green, Karvounarakis & Tannen, PODS 2007；Why and Where —
  Buneman, Khanna & Tan, ICDT 2001。
- AutoAdmin "What-If" Index Analysis Utility — Chaudhuri & **Narasayya**, SIGMOD
  **1998**（纠正：非 Narayan/VLDB 1997）。
- Access Path Selection… — Selinger et al., SIGMOD 1979。代价模型定计划。
- Tarantula — Jones & Harrold, ASE 2005；Ochiai — Abreu et al., TAICPART-MUTATION
  **2007**（纠正出处）。
- GenProg — Weimer et al., ICSE 2009；系统研究 — Le Goues et al., ICSE 2012。
- PAR — Kim et al., ICSE 2013。六万人写补丁挖模板替代随机变异。
- Delta debugging 三部曲 — Zeller, ESEC/FSE 1999；Zeller & Hildebrandt, IEEE TSE
  2002 (ddmin)；Zeller, FSE 2002（因果链）。
- Lexicographic Parsimony Pressure — Luke & Panait, GECCO 2002。

### 4b. 工作流图优化（信号清一色端到端标量分）
AFlow（Zhang et al., ICLR 2025 Oral，MCTS 过代码化工作流）；ADAS/Meta Agent Search
（Hu, Lu, Clune, ICLR 2025，档案条件化元代理）；MaAS（Zhang et al., ICML 2025 Oral，
agentic supernet）；G-Designer（ICML 2025，变分图自编码器出通信拓扑）；GPTSwarm
（Zhuge et al., ICML 2024 Oral，REINFORCE 调边连通）；MASS（ICML 2025，分阶段
块/拓扑/prompt 搜索）；ScoreFlow（arXiv 2025，Score-DPO）；DebFlow（arXiv 2025，
辩论修图）。

### 4c. 自演化与验证设计
- Darwin Gödel Machine — arXiv:2505.22954, ICLR 2026。**验证设计实锤：选择/汇报集
  嵌套**（SWE-bench 60⊂200；Polyglot 50 子集 38.0% vs 全集 30.7%，选择乐观自证）；
  唯一不相交检查是跨床迁移（SWE→Polyglot 28.9%）。
- GEPA — arXiv:2507.19457, ICLR 2026 Oral。轨迹+分数+自然语言反馈混合信号，逐模块
  反思变异 + Pareto 候选池。
- AlphaEvolve — arXiv:2506.13131（自发白皮书）。MAP-Elites 式程序库 + 用户评函数
  （可级联）；held-out 视场景而定（数学任务无、内核调优有形状切分）。

### 4d. 失败归因（观察式旗舰 + 干预式微潮）
- MAST — arXiv:2503.13657, NeurIPS 2025 D&B。14 失败模式分类学，观察式。
- Who&When — arXiv:2505.00212, ICML 2025。静态日志判责上限：agent 级 53.5%、
  **步级 14.2%**。
- CausalFlow — arXiv:2605.25338。步级内容替换、K=3 提案/步、温度随任务（0.0–0.7）、
  3 独立跑量方差（±6.81pp std）；CRS 精度 68–84%、修复率 21.9–52.4%；$0.05–0.15/
  修复；副产品=对比偏好对离线数据集。
- CAR — arXiv:2606.08275。SCM+do 单步、**承诺点冻结**隔离重采样方差、预算内 MC-
  Shapley 分账；只在合成 SCM 验证。
- REFLECT — arXiv:2606.09071。前缀保持回滚±K + 诊断补丁注入、温度 0、忠实门；GAIA
  定位 39.0% vs LLM 裁判 17.9%，干预纠正率 GAIA 54.2%（WTQ 92.6%/SWE 89.0%）。
- DoVer — arXiv:2512.06749（Microsoft）。改消息/计划后重执行、**每干预 3 独立跑**；
  翻转 18–28% 败局、验证/否证 30–60% 假设；单遍事后诊断（摘要原文无环内集成）。
- AgenTracer — arXiv:2509.03312, ICLR 2026 poster。反事实重放+故障注入只用于**一次性
  离线造标签**（TracerTraj-2.5K）；部署的 8B 判读器纯观察式；步级 20.7/42.9%。
- EvoReplay — arXiv:2605.20086。演化日志之上的**事后**审计实验对象，明确与活环
  （OpenEvolve/GEPA/EvoX/ShinkaEvolve）相对照。
- **关键缺口结论（核实）**：把干预式重放做成自演化环内常驻逐轮证据源——查遍上述
  + AgentEvolver/SePO/Directed Evolution——**无人做**。活环一律用观察式 LLM 裁判
  或结果奖励。

### 4e. 免执行预测（方案三地基）
- Agentic Predictor — arXiv:2505.19764, MAS@ICML 2025。多视图（代码+图+文本）编码器，
  84.38% 免执行预测工作流成败。
- FLORA-Bench / GNN 预测器 — arXiv:2503.11301。工作流=计算图，GAT ~84%；跨域迁移差。
- RouteLLM — Ong et al., arXiv:2406.18665, ICLR 2025。win 预测 AUC≈0.63（GSM8K）也
  换来 54% 调用省 95% 质量——预测不必神准即有用。
- IntroLM — arXiv:2601.03511。预填激活自预测 AUC≈90%——**对我们不可用**（网关拿不到
  激活，litellm-only 硬约束）。
- Bao — Marcus et al., **SIGMOD 2021 最佳论文**（纠正：非 VLDB）。Thompson 采样 bandit
  转向优化器提示；Neo — PVLDB 12(11) 2019。
- Performance-influence models — Siegmund et al., FSE 2015。配置性能预测 ~19% 平均
  相对误差。

### 4f. 穿 LLM 步的证源（方案五地基与卡点）
- ContextCite — Cohen-Wang et al., NeurIPS 2024 (arXiv:2409.00729)。上下文片段消融
  + LASSO 稀疏替代模型；默认 **32 次消融前向/次归因**；稳定胜注意力/梯度基线。
  跟进：AttriBoT (2411.15102)、SelfCite (2502.09604)、Learning to Attribute with
  Attention (2504.13752)——都在降价不在超精度。
- mlinspect — Grafberger et al., ~2021。经典 ML 预处理管线的行级证源多项式。
- 半环 LRP — Groudiev et al., ACM ProvenanceWeek 2025。半环注记推广 LRP，非 LLM。
- PROV-AGENT — Souza et al., IEEE eScience 2025 (arXiv:2508.02866)。LLM agent 证源
  用 W3C PROV-DM 图谱系，**非代数半环传播**。
- **缺口核实**：provenance semiring / why-provenance 应用于 LLM/RAG/agent 数据流
  ——无直接命中（截至 2026-08）。卡点：32× 前向/节点的价 + 网关 logprob 可得性。

### 4g. 决定论重放（方案一基建先例）
Record & Replay for LLM agents — arXiv:2505.17716（按 (tool, hash(args)) 缓存应答，
permissive/strict 双模）；LOOP Skill Engine — arXiv:2605.14237（一次录制+确定性重放，
~99% token 省）；The Log is the Agent — arXiv:2605.21997（事件溯源日志即可分叉重放
工件）。五篇归因文各自的压方差法：DoVer 3 复跑 / REFLECT 温度 0 / CausalFlow 量方差
/ CAR 承诺点冻结。

### 4h. 失败归因家族与"图"的三种用法（08-19 双路侦察）

- **锚点判定**：Who&When（ICML 2025）三法（All-at-Once / Step-by-Step / Binary Search）
  **全扁平**——数据集 schema（Query+Log+系统信息+标注）无任何拓扑字段；MAST
  （NeurIPS 2025 D&B）扁平——仅 FM-3.1 散文里顺嘴提过 star topology，非分类学维度。
- **2025 扁平第一波**（方法全为 LLM 读平面日志）：AgenTracer（(s,a) 序列）、TRAIL
  （arXiv:2505.08638, Patronus，最好模型 11%）、SAFARI（2606.24626，检索式仍扁平）、
  MASPrism（2605.07509，小模型 NLL/注意力信号）、AgentRx（2602.02475, MSR）、
  TraceElephant（2604.22708，全轨迹 vs 部分 +76%）、AgentFail（2509.23735，平台工作流
  失败实证）。
- **2026 图第二波**（对扁平弱数字 14.2%/11% 的反动）：**CHIEF**（2602.23701，标题即
  "From Flat Logs to Causal Graphs"，层次因果图+反事实渐进筛，Who&When 上胜 8 基线
  ——正面论证扁平 vs 图的那一篇）；FALAT（2606.00765，依赖引导搜索）；ASCon
  （2608.10646，方向感知图注意力 over agent×step）；GraphTracer（2510.10581，依赖图
  ——**作者已撤稿**（方法学根本错误），引用必须注明）；邻接：FPoF/DisasterBench
  （2605.27957，工作流 DAG 上定位"首个失败点"，单代理工具编排非 MAS）。
- **执行 DAG 诊断小簇**（2026 年 3–7 月，全为薄审无 venue 预印本）：GRADE
  （2606.22741，步骤节点+执行边/依赖边双层，依赖边按可信度分 observed/declared/
  inferred 三级，定位失败步、跨 6 语料迁移）；AgentTrace（2603.14688，日志重建因果图
  回溯排根因、免 LLM 亚秒级）；AgentTether（2607.06273，Transition Unit 依赖图+运行时
  修复）；Trajectory Graph Copilot（2607.27443，历史轨迹概率图+GNN 事前预警）；综述
  From Agent Traces to Trust（2606.04990）已把 "execution provenance = 执行的类型化图"
  立为条目——**该范畴正在被收编，不是处女地**。
- **通信拓扑线**（2024-25 六篇核实，节点=agent、边=消息；全非失败诊断）：G-Safeguard
  （2502.11127，GNN 异常检测+拓扑改写，安全）、AgentPrune（2410.02506，剪冗余
  $43.7→$5.6）、NetSafe（2410.15686，拓扑→鲁棒性描述研究）、AgentDropout
  （2503.18891，省 token）、SentinelAgent（2505.24201，通信图运行时监控；注意同名
  撞车 2604.02767 是另一篇）、MAGDi（ICML 2024，辩论图蒸馏，图只在训练期）。
- **单代理 CoT 错误定位**（线性链，无拓扑可用）：Big-Bench Mistake（ACL 2024
  Findings）、REVEAL（2402.00559）、ProcessBench（2412.06559）。
- **定位结论（论文用）**：文献里的"图"有三种——①通信拓扑（agent 为节点，安全/省钱
  用）；②日志**重建**的因果/依赖图（归因第二波）；③单 run 执行证源 DAG（GRADE 簇
  与我们的 U）。GHX 对②③的差分不再是"没人做图"，而是四条：**原生记录**（U 由
  harness 运行时直接记边，全部 observed 级、零重建误差——GRADE 的三级分级恰好是
  重建之痛的自证）；**跨题群体聚合**（lift/锥差分/回归账，他们全是单事故只读诊断）；
  **读写闭环**（证据喂 Evolver→五门→transactional_apply 落回 config，genotype↔U 双图
  配对，他们的图不落回任何东西）；**环内常驻干预**仍无人做（方案一缺口经两路独立
  复核成立）。

### 4i. 他们的病 × 我们的方案：交叉映射（08-19 精确数据）

**他们的问题清单（核实频率）**
- MAST（N=1642）：FC1 系统设计 43.9%（FM-1.3 步骤重复 **15.7%=全场第一单项**、FM-1.5
  终止条件不自知 12.4%、FM-1.1 违背任务规范 11.8%）；FC2 跨代理错位 32.2%（FM-2.6
  推理-行动错配 13.2%、FM-2.3 跑题 7.4%、FM-2.4 信息扣留 0.85%、FM-2.5 无视对方输入
  1.9%）；FC3 验证 23.5%（FM-3.3 错误验证 9.1%、FM-3.2 无/不完整验证 8.2%、FM-3.1
  过早终止 6.2%）。
- TRAIL：148 轨迹 841 错，**均 5.68 错/轨迹**（多错是常态）；格式+指令违规 353/841≈42%
  为最大类；系统执行错稀少。最好裁判 joint acc 18.3%（GAIA 切分）。
- AgentFail：**32% 失败的根因节点 ≠ 症状节点**；>10% 案例传播距离超工作流长度 40%；
  LLM/Agent 节点 ~40% 非局域、逻辑控制节点 ~45%。修复实验：给定位+根因信息 →
  修复成功 66.8%、引入新故障仅 2.8%（单次提取，未复核）。
- DoVer：单干预翻转 17.6%（WW-AB/WW-GAIA）/27.5%（GAIA-L1）/49%（GSMPlus，单源）；
  假设裁决大头是 **Inconclusive 57.6–66.7%**；"同一失败可被多个不同干预独立修复"
  （原文定性，无百分比——早先流传的 31.8% 不可证实，弃用）。
- Who&When：日志越长归因越塌，93–130 步档三法**全部趋近 0%**；步级精度对上下文长度
  最敏感；有 ground truth 才涨。

**他们的药与药效（天花板观察）**
战术修补（MAST ChatDev：CEO 终审 +9.4%、加目标验证步 +15.6%——他们最大战术收益
恰是"加验证步"；AG2 数字未核实勿引）；LLM 裁判管线（11–18% joint acc）；微调判读器
一次性接线（AgenTracer +4.8–14.2%）；重建图（CHIEF 一族）；干预重放（翻转 18–54%）；
带根因信息的修复（66.8%）。**领域自己的数据链条 = 修复能力存在（66.8%）、干预有效
（18–54%），瓶颈全部卡在归因层（扁平 0–18%）**——战争在证据层打赢，正是 GHX 的楼层。

**六个交叉点**
1. **MAST 第一单项 = 我们最惨的负结果**：步骤重复 15.7% 全场第一 ↔ M13 的
   loop_detection 战役（定位对、处方 −7）。领域最常见的病 × 我们最完整的病历 = CH3/CH6
   叙事主轴。FC1 合计 43.9% 说明 harness 设计层有真果子——与 L0 无踏车对读，结论是
   "果子在但盲搜摘不到 = 需要定向"，即 GHX 立论本身。
2. **M22 证据链衰减 = FM-2 在元环的显影**：锥被引 30%（信息扣留）、候选引证 0/31
   （无视对方输入）、lift→错药（推理-行动错配 13.2% 的元层版）。MAST"战术修补不够、
   要结构改"的结论预言我们的升级路径：G1c 协议劝说（M23，战术）→ 若 G-A(ii) 平 →
   T30 schema 强制（结构）。
3. **AgentFail 32% 根因≠症状 = 锥+首异常点的外部正当性数字**：症状侧记账三分之一
   是错的——观察 lift 给症状节点加冕的机理即此。66.8% vs 无信息修复的差 = "证据质量
   决定修复率"的实测——全论文最好用的外部数字。
4. **DoVer 的 Inconclusive 大头 + 非唯一根因 = 方案一的两条设计约束**：(a) 单次干预
   多半判不出 → 必须复跑+机制粒度合并（60 伯努利设计已内建）；(b) 充分原因不唯一 →
   干预 lift 报"充分原因集"而非单凶手（CAR 的 Shapley 分账是现成工具），ship 定向
   取最廉价充分原因。GAIA 上翻转期望锚定 18–28%。
5. **Who&When 长日志塌零 = 结构化证据的动机**：步级精度被上下文长度杀死 → 喂结构化
   事实（cone-first）而非原始日志；与 TraceElephant"完整轨迹 +76%"合读：**完整且
   结构化**，两个条件缺一不可。
6. **TRAIL 42% 格式违规 + 均 5.68 错/轨迹**：(a) 医生也得同一种病——Evolver 自己的
   IV-3 格式炸弹就是这 42% 的元层版，方案四模板是对症药；(b) 多错常态 → "唯一决定性
   错步"标注框架（Who&When）先天脆弱，锥的集合语义天然容纳多因，首异常点+级联分析
   （P2 探针）补排序。

---

## 5. 移植候选目录（"别人用过的方案"→ GHX 落点）

原则（F1-F4）：先例存在不是障碍是素材；每条记 机制/出处（核实）/家乡实测/GHX 落点
（环上哪步、动哪个数）/移植变步。标记：〔即插〕小改可上；〔中改〕需新部件；〔远期〕
牵动架构。

### 5a. 选择与亲代（对 C6/C8、零采纳、fix-one-break-one）

- **T-01〔中改〕逐题 Pareto 候选池** — GEPA, ICLR 2026 Oral (arXiv:2507.19457)。
  候选在 ≥1 题上最优即留池，亲代按 Pareto 覆盖题数加权抽样（非贪心）。家乡实测：
  胜 GRPO +6% 均/+20% 峰、rollout 省 ≤35×；胜 MIPROv2 >10%。落点：档案/亲代选择
  （现状=单谱系 champion + refuted 签名）；动：采纳率、fix-one-break-one 率。变步：
  逐题分从连续变 0/1+噪声——池准入须加同配置复测或包络裕量；103 维 pass flag 已在
  task_history，零新数据面。
- **T-02〔中改〕lexicase 逐题选择** — Helmuth/Spector/Matheson, IEEE TEVC 19(5) 2015；
  ε-lexicase（La Cava et al., GECCO 2016）；downsampled（Hernandez/Lalejini/Dolson/
  Ofria, GECCO 2019 Comp）。随机题序流式过滤亲代、只留逐题并列最优——不聚合分数，
  保住"专攻难题的特化个体"。LLM 先例：Pinna et al., EuroGP 2024（LNCS 14631）对
  LLM 代码变体用逐测例 lexicase。落点：多候选时的 ship 选择；动：分层子集分。变步：
  二值+噪声题 → downsampled + 复测样本。与 T-01 同族，择一或叠加。
- **T-03〔即插〕自适应亲代采样 P∝s·h** — ShinkaEvolve, arXiv:2509.19349（Sakana）。
  s=σ(λ(F−α₀)) 奖强、h=1/(1+N_children) 罚过采——DGM 那条定性规则的闭式版。家乡
  实测：150 样本达 AlphaEvolve 数千样本的圆填充 SOTA（样本效率主张，对 17 轮瘦预算
  极对症）。落点：引入档案后的亲代抽样公式。

### 5b. 候选生成（对 B5、采纳率）

- **T-04〔中改〕系统感知合并（crossover）** — GEPA, ICLR 2026 Oral。从两条 lineage
  各取最优模块拼新候选。落点：Evolver 新算子"config 段拼接"，transactional_apply
  天然做验证；动：采纳率。变步：模块=processor 段而非 prompt 模块。
- **T-05〔即插〕灵感注入 prompt** — AlphaEvolve (arXiv:2506.13131)：parent + 档案里
  top/diverse 程序各带执行结果与分入 prompt；对照 ADAS (arXiv:2408.08435, ICLR 2025)
  全史无筛注入的 context 爆炸教训。落点：Evolver 输入加"历史候选画廊"（config diff
  + 逐题翻转摘要，top-k 有筛）；动：候选重复率、采纳率。
- **T-06〔中改〕UCB1 算子臂选择** — ShinkaEvolve 用 UCB1 选 LLM 臂；我们单模型，把
  **编辑桶当臂**：UCB over {mutate_params, insert, rewire, prompt-edit}，回报=该桶
  历史 ship 命中。落点：Evolver 桶选择；动：命中率。与方案四模板库组合。

### 5c. 门与评估预算（对 C6、每 ship 验证成本）

- **T-07〔即插〕分级评估级联正名** — AlphaEvolve（documented-concrete：便宜关不过
  不进贵关）；DGM 分级 10→60→200 (arXiv:2505.22954)。我们的 E6 短路+五门+smoke 梯
  已是雏形——形式化为床保真度 rungs（6→24→103）并写进论文即得文献名分。
- **T-08〔中改〕successive halving / ASHA** — Jamieson & Talwalkar, AISTATS 2016
  （SH 源头 Karnin et al., ICML 2013）；Hyperband, JMLR 18(185) 2018；ASHA, MLSys
  2020。多候选并发时：全员先 12 题 rung，幸存者 24，冠军 103。LLM 先例：AutoPDL
  （Spiess et al., arXiv:2504.04365, AutoML 2025）对 agent prompt 模式直接用 SH——
  **最近占位，论文须引**。落点：Stage-4 验证预算；动：每 ship 验证成本、candidate
  吞吐。变步：rung-0 可直接用方案三估价段（零执行）。
- **T-09〔中改〕F-Race 统计竞速** — Birattari/Stützle/Paquete/Varrentrapp, GECCO
  2002；现代后裔 irace；LLM 先例 irace-evo (arXiv:2511.14794, 2025，选 LLM 演化的
  代码变体)。逐题增量评估 + Friedman 检验淘汰显著劣者——**统计检验内建的 SH**，与
  "103 二值题逐题出分 + ±4–6 包络"的形状严丝合缝。落点：同 T-08，二选一（噪声床上
  F-Race 更对症）；动：误 ship 率、验证成本。
- **T-10〔即插〕新颖性拒绝** — ShinkaEvolve：嵌入相似度 η=0.95 + LLM 复核，不新颖
  带 Reflexion 式反馈**重采样**而非入库。落点：novelty gate 升级（现状=签名精确
  ∉refuted）+ Evolver 会话内循环；动：门预算、重复候选率。

### 5d. 多样性与档案（对单谱系塌缩、平坦景观探索）

- **T-11〔中改〕MAP-Elites 档案** — Mouret & Clune, arXiv:1504.04909（canonical 即
  arXiv）；LLM 时代：QDAIF（Bradley & Dai 共同一作…Lehman, ICLR 2024）、Rainbow
  Teaming（Samvelyan et al., NeurIPS 2024）；**最近占位：AgentBreeder（Rosser &
  Foerster, arXiv:2502.00757, NeurIPS 2025）**——MAP-Elites 式 niche 档案做多智能体
  scaffold 自改进，论文必须点名。落点：档案格=（L1/L2/L3 分层表现向量 × genotype
  复杂度），每格留精英；动：采纳率、探索覆盖。变步（对 AgentBreeder 的差分）：格
  描述符取自**图**（genotype 特征/锥覆盖），非行为文本嵌入。
- **T-12〔远期〕岛屿+重置** — Tanese, ICGA 1989（源头）；Whitley/Rana/Heckendorn,
  J.CIT 7(1) **1999**（常被误引 1998，已纠正）；FunSearch（Nature 625:468-475）
  每 ~4h 清最差半数、由幸存岛最优重播。落点：多臂升级为多岛（岛间 config 段迁移经
  transactional_apply）；成本=多臂×轮，远期。
- **T-13〔远期〕fitness sharing** — Goldberg & Richardson, ICGA 1987。niche 拥挤
  惩罚，与 T-11 同族备选，不单列施工。

### 5e. 记忆回读（对 T25 死因简报、cone 引用率）

- **T-14〔即插〕三种回读格式** — Reflexion（Shinn et al., NeurIPS 2023）：口头反思
  缓冲**硬帽 1-3 条**直接进 prompt；Voyager（Wang et al., TMLR 2024）：嵌入检索
  top-5 技能拼进上下文（3.3× 独立物品/15.3× 加速）；ExpeL（Zhao et al., AAAI 2024）：
  规则蒸馏（投票筛）+ 相似轨迹检索双通道。落点：T25 的实现规格——ExpeL 式规则蒸馏
  喂 Planner（死因→规则），Voyager 式检索喂 Digester（相似败题的历史锥）；Reflexion
  的 1-3 条硬帽是防 ADAS 式 context 爆炸的现成纪律。动：cone 引用率、重复死因率。

### 5f. 部署与回滚（对 P4 中性 ship、回滚精度）

- **T-15〔中改〕champion-challenger / 影子跑** — TFX Model Validator（Baylor et al.,
  KDD 2017，canonical 门）；问题语境 Sculley et al., NIPS 2015。ship 不直接接管：
  challenger 在同轮以影子身份跑小样本（缓存冻结世界下便宜），赢过边际才换 champion。
  落点：compose 前新增影子段；动：ship 后回滚率、中性 ship 累积。与方案二/adjudicate
  report-only 兼容。（2026 两篇 weeks-old 预印本 ICAN-Deploy/OpenLoopEvolve 已在做
  agent 版——趋势佐证，非成熟占位。）
- **T-16〔远期〕bandit 部署路由** — Bao（SIGMOD 2021 最佳论文）Thompson 采样转向；
  LLM 时代真 regret-bounded 的只有模型路由（PILOT, EMNLP 2025 Findings,
  arXiv:2508.21141；BaRP, arXiv:2510.07429）；scaffold 级只有离线 BOAD
  (arXiv:2512.23631)。落点：逐题在 champion/challenger 间路由，把"全床切换"变成
  逐题 regret 最小化——**scaffold 级在线 bandit 无人占**，但牵动 run_pilot 架构，
  远期。

### 5g. 即插序与论文占位提醒

- 冻结期后第一批〔即插〕：T-03（亲代公式）、T-05（灵感注入）、T-07（级联正名）、
  T-10（新颖性拒绝）、T-14（回读格式）。
- 与五案的扣合：T-08/T-09 的 rung-0 = 方案三估价段；方案一的扰动数据给 T-01 池准入
  提供置信；T-06 与方案四模板库同一张牌桌。
- 论文 related work 必须点名的最近占位：**AgentBreeder**（QD-on-scaffolds）、
  **AutoPDL**（SH-on-agent-configs）、**GEPA**（逐题 Pareto）——按 F2，引用后写清
  变步即是贡献。

---

## 6. 与 M24 的关系

M24 = 可测性与仪表（不含研究机制）。本册机制线的施工序列另立（M25/G3 候选），
前置条件：M23 双臂判读（G-A）完成 + M24 P2 仪表批全绿。方案一依赖 M24 的 T13/T14
（record-replay 缓存）与 T01/T02（判读）——基建共享，排期解耦。

---

## 7. 2026-08 六路全域扫描：定位重写与移植扩编（08-19 深夜）

用户判定 §4 底账"不够多不够新"后的第二次全域扫描。六路发现代理并行（归因/因果干预/
执行图/自进化/拓扑/步级信用），窗口 2025-09→2026-08，**160 条核实 NEW + 4 UNVERIFIED，
去重约 138 条唯一**。原始账全文=本目录 `20-LIT-SWEEP-2026-08-SIXLINE.md`。

### 7.1 定位重写：三死一活

**死了的三句"独家"**（相关工作必须正面排）：

1. **原生记录执行图**——AER (2603.21692) 明文论证"溯源不可从检查点重建"+逐步原生
   schema；Ledger (2608.00808) 在线账本；MAP-Graph (2608.10509) 溯源驱动运行时门控。
   三家闭环各窄（分析向/跳冗余/权限门控）。
2. **图证据驱动进化**——GraphMind (2605.17617) 轨迹编译因果工作流图+在线导航；
   MEGA (2608.10504) Wisdom Graph 双向精炼。
3. **诊断→改 harness→门禁→晋升的环**——四家威胁簇：HarnessFix (2606.06324，组件归因
   +受限修复算子，+5.5~18.4pp 绝对/15.2~50.0% 相对【读队 A 已改正，原记 +6.3~18.4% 系误记】)、
   Better Harnesses Smaller Models (2607.08938，4% 成本得 89.7%)、Regimes (2606.10241，
   append-only+四级门禁，逐段对应我们四角色；量化床仅 LongMemEval-S，ActiveGraph 是
   底层 runtime 非评测床【读队 A 更正】)、Shepherd (2605.10913，可逆轨迹，四路扫描全撞见)。

**活着的座位**（三路独立核实到 2026-08-19 仍空）：
**因果图证据 + 直接结构修改 + 跨轮闭环 三要素交集无人同时满足**。
E2-Explainer (2608.12921) 有前两缺跨轮；HarnessFix 有中间缺图与跨轮；AHE (2604.25850)
有跨轮缺因果图。附属空位：(i) 干预化证据常驻环内逐轮生产（HELIX 2608.13951 最近：
配置 A/B、仅一轮）；(ii) 预测校验回路=白地（唯一悬案 AHE 的 decision observability，
精读裁决）。**一句话定位：GHX = 唯一把原生因果图同时接归因（读）与进化（写）、跨轮
闭环、且证据可干预化的系统——每个形容词都有点名的对照物。**

另：步级信用线底账"几乎空白"系误判（初筛 ~200 篇），该线已是 agentic RL 标配组件，
四类机制形态（图传播/反事实干预/turn 级 TD/归因后代）。**步级信用去动系统配置=少数派
但存在**：Agents that Matter (2605.27621，归因直接换 agent 底层模型) 与 CausalFlow
(测试时直接修轨迹) 是最近亲。

### 7.2 名字账（全部有定论）

- **arXiv:2606.14249《HarnessX...Foundry》= 官方底盘自己的论文**。证据：一作 Tingyang
  Chen (chentingyang@xiaomi.com) 在本仓库 commit 作者名单；upstream remote =
  Darwin-Agent/HarnessX；`experiments/variant_pool/SPEC.md:43` 已按"arXiv 2606.14249v2"
  引页码。必引地基（官方原语+官方 AEGIS+5 bench +14.5%），非撞车。
- **CAR 本尊找到**：Causal Agent Replay = arXiv:2606.08275（do 干预+预算约束蒙特卡洛
  Shapley，关键步恢复效率 ~0.91）。§4 各处占位"CAR"引用坐标以此为准。
- **arXiv:2509.14295 也叫 Aegis**（错误归因数据集生成，与我们 AEGIS 元环无关）——
  论文加消歧脚注。
- ASCon 现挂 2608.10646（2026-08-11），或为大改版，引用前核对版本。
- AHE (2604.25850) 与 AEvo (2605.13821) 本仓库 `aegis_story.md:360-365` 早已引用，
  非新面孔。

### 7.3 新弹药数字（摘要级，精读校准）

- TelemetrySuffBench (2608.07899)：完整遥测 origin-step 97.2% → 标准日志字段 **0.5%**
  ——"必须原生记录决策-证据链接"最锋利实证。
- Bridge Evidence (2607.15253)：**27%** 被读文档统计无关但因果关键——共现≠因果实锤。
- LongRCA (2608.15242)：145 步长轨迹 baseline 根因步 **13.2%**；AGENTCHAOSBENCH
  (2608.14680)：最好 LLM 诊断器故障识别 **24.8%**。
- **Agents that Matter (2605.27621)：agent-ablation（真干预）与 LLM-judge 内省的归因
  结果不一致**——非干预信号系统性错排因果贡献的直接外部证据（方案一动机的镇论文）；
  且 Leave-One-Out ≈ 组合法但便宜得多（干预设计的省钱定理）。
- 反方必接：MP-Bench (2603.25001)——"LLM 不会归因"多为 benchmark 设计缺陷假象。
- 纪律提醒：跨领域搬机制（SBFL/混沌工程/MCTS/熵/圣训学）在归因线已是常规操作，
  F2 的"搬来后哪步变了"必须写得更硬。

### 7.4 移植扩编 T-17..T-27（凶手=器官库；接续 §5 编号）

死的是独家声明，尸体供货给活着的五案。摘要级机制读数，精读队校准差异句。

| # | 供体 | 器官→GHX 落点 | F2 差异（搬来后变的一步） | F7 动的数字 |
|---|---|---|---|---|
| T-17 | Ledger 2608.00808 | **U 跑内冗余守卫**：工具调用前查图"同命令三步前已跑、结果 empty"，缓存结果+理由作为证据递给模型（非 M13 式强制打断） | 账本→因果图；治首异常第一病 Bash#empty (78/165) | budget_exceeded 占比 (36%/30%)、同命令重复数 |
| T-18 | MAP-Graph 2608.10509 | **无据答案门**：final answer 锥内无工具观察祖先→跑内提示验证+元环记"无据幻觉"型 | 门控对象从权限改为答案提交；执行器=P4 计数版签名 (98.6% 区分力) | 幻觉型失败分离占比、该型通过率 |
| T-19 | AER 2603.21692 | **模型节点意图注**（枚举类，不存正文）：M23 工具 outcome 的对称面；lift 升级为机制×意图合并 | schema 字段从散文改枚举；保 U 无内容设计 | ship 命中率、错药复发率 |
| T-20 | GraphMind 2605.17617 | **胜利子图回灌**：已解任务锥压成类型化胜利子图，走 GUIDANCE 通道注入 | 图不当控制器、runloop 不动；锥机器首次消费成功面 | 该任务族通过率、guidance 引用率 |
| T-21 | MEGA 2608.10504 | 类型化证据原子=T30 schema 强制的**领域内先例注**（不另开数字） | — | — |
| T-22 | HarnessFix 2606.06324 | **缺陷记录层**：症状节点→责任 bucket 映射（参数错=tools/缺件=config/时机错=processor），产出即 Evolver 的 bucket 选择；受限修复算子=方案四的 2026 先例 | 单轮批量修→常驻环内+跨轮再诊断 | 分桶 ship 命中率 (41/31/26%)、config 桶首 ship |
| T-23 | Shepherd 2605.10913 + CAR 2606.08275 | **锚点分叉重放**：前缀从缓存回放（T13/T14），首异常点处施干预，仅后缀活跑；配对消掉锚前随机性 | 整任务换配置重跑→中途分叉 | flips-per-dollar、翻转估计方差 |
| T-24 | E2-Explainer 2608.12921 | **边级 do 算子**：compose 时扣某上游写者消息=对一条 OBSERVED_DATA 边做 do；干预从节点级细化到边级，解 A3 锥并集双语义 | 一次性解释+摊销→逐轮常驻产证据 | 边类翻转率（首个分"在场/必经"的数） |
| T-25 | Regimes 2606.10241 | **held-out 终门**：五级校验梯补最后一级=方案二座位 | 一次性 held-out→17 轮反复复用，须 Dwork 加噪 | D9 裂缝宽度（环内分 vs 保留集分） |
| T-26 | Better-Harnesses 2607.08938 | **跨模型迁移检验**：已 ship harness 换便宜主模型跑常驻对照格；迁移=机制性、不迁移=模型特异过拟合 | 适配目标从性能改为"机制性判别器" | 每 ship 跨模型迁移率、每解题成本 |
| T-27 | CRAFT 2606.29476 | **免费同胞对照**：候选评测已有的 rollouts 当反事实对照种群，零额外跑 | GRPO 组内→候选评测复用 | 每证据条目边际成本 |

另两条先例注（不占编号）：CSO (2602.03412)"仅验证翻转的样本进训练"=方案一
verified-flip 门的训练侧同构先例；PACE (2606.08106) anytime-valid 序贯检验=信封门/
采纳判定的统计升级候选（对 103 床 ±4-6 题包络直接相关）。

**结构总账**：T-17/T-18/T-20 合开"**U 跑内消费**"新地界——U 从"跑内写、轮间读"
变"跑内写、跑内读、轮间读"，闭环宽度再推一格，恰是三家原生记录凶手都没占的组合。

### 7.5 精读队派单（第二波，08-19 夜发）

18 篇 A 级 × 6 读队，每篇必答：机制内幕、关键数字（标出处章节+claimed/measured）、
三要素判定（因果图证据/直接结构修改/跨轮闭环各有缺）、对应 T-xx 移植校准：

- 读队 A（闭环竞品）：AHE 2604.25850（**白地悬案裁决**）、HarnessFix 2606.06324、Regimes 2606.10241
- 读队 B（共进化+元代理）：HELIX 2608.13951、Shepherd 2605.10913、Better-Harnesses 2607.08938
- 读队 C（干预归因）：CAR 2606.08275、CausalFlow 2605.25338、REFLECT 2606.09071
- 读队 D（信用科学）：Agents that Matter 2605.27621、CSO 2602.03412、CVT-RL 2606.05263
- 读队 E（原生图运行时）：AER 2603.21692、Ledger 2608.00808、MAP-Graph 2608.10509
- 读队 F（图证据进化+边干预）：GraphMind 2605.17617、MEGA 2608.10504、E2-Explainer 2608.12921

---

## 8. 第二波精读总裁决（08-19/20 夜，六读队 18 篇正文级 + Life-Harness 追加）

全部 18 篇正文级核实完毕（HTML 或 PDF 逐字），外加 Life-Harness (2605.22166) 主循环
现场追猎。以下为终稿裁决，覆盖 §7.1 的摘要级判断。

### 8.1 终版竞品战力表（三要素 = 因果图证据 / 直接结构修改 / 跨轮闭环）

| 竞品 | 判定 | 缺的那段（正文依据） |
|---|---|---|
| AER 2603.21692 | 0/3 | 非图（结构化轨迹、字段全自由文本）；只读离线零回写 |
| CAR 2606.08275 | 形式化论文 | 5 页玩具 SCM、零真实床零成本；共享随机数自认留白；无 Inconclusive |
| Ledger 2608.00808 | 1.5/3 | 计数器非图；闭环仅 episode 内；**失败/空/截断显式不入账**（T-17 空位实锤） |
| E2-Explainer 2608.12921 | 2/3 | 缺跨轮：离线蒸馏→部署后开环一次性预测 |
| GraphMind 2605.17617 | 2/3 | 缺结构修改（只改图数据不改执行器）；**负面子图自认未做** |
| MAP-Graph 2608.10509 | 2/3 窄 | 闭环仅 workflow 内；**无来源祖先=默认信任 0.80 宽放**（vs T-18 范畴门） |
| AHE 2604.25850 | 2/3 | 缺图（"graph"全篇零命中）；(c) 误差回填校准=无，regression-precision 11.8%≈2×random 无升势 |
| HarnessFix 2606.06324 | 2/3 | 缺跨轮：§IV-D 单轮协议实锤，harness memory 预留未触发；HTIR 是真 node+edge（最强图竞品） |
| Regimes 2606.10241 | 2/3 | 缺图最彻底（diagnose 吃扁平 pass/fail 枚举）；**自曝 held-out 复用抬 Type I、不引 Dwork** |
| HELIX 2608.13951 | 1/3 | 缺图缺跨轮：update operator §9.5 自认未实现；65 候选=组合枚举，最佳 +4% 相对 |
| Shepherd 2605.10913 | 2/3 | 缺图：分叉原语占了 T-23 底座，但 flip/attribution/bisect 零命中——只做正向生成-测试 |
| Better-Harnesses 2607.08938 | 2/3 | 缺图（causal/graph 零命中）；RQ4 自认不迁移；"4%/89.7%"=均值对均值且摘要正文不一致 |
| CausalFlow 2605.25338 | 2/3 | 缺跨轮；且**线性链非图**（永远重跑全后缀）；4 床里 3 床翻转是 LLM 预测非真跑；trace 税自曝（结构化基线 75.0 vs Direct CoT 88.1） |
| REFLECT 2606.09071 | 2/3 | 缺跨轮；锥=固定窗口 K=3（位置剪枝非依赖剪枝，窗口外漏检未量化）；BBM 上倒输 Opus judge 25.6pp |
| MEGA 2608.10504 | **3/3 带限定** | 三灯全亮，但图是 **LLM 蒸馏的语义知识图**（PCR 节点=策展判断、S/N 分=推理赋值），非执行级因果图——不可干预 |
| Life-Harness 2605.22166 | 迁移专项 | 环境侧干预跨 18 backbone 迁移（116/126）；床=确定性环境；无因果图无归因 |

### 8.2 定位终稿

> **GHX 是唯一在"执行级因果图（原生记录、边对应真实控制/数据流、因而可干预）+
> 直接结构修改 + 跨轮闭环"三要素交集上的系统；唯一的 3/3 竞品 MEGA 的图是知识级
> （策展判断、不可 do），而"可干预性"正是方案一全部机制的落脚点。**

支撑链（CH2 摆法，20 号档案 §6 补报）：相关性信号弱（judge 步级 ~14%，可引 CAR 转述）
→ 需干预式信号（CAR/REFLECT/CausalFlow）→ 干预信号已被拿去改运行时而非权重
（HarnessFix/AgentTether）→ 但三个最强一次性机制共有三洞（8.3）→ 常驻环内逐轮生产
+配对前缀跨轮对比 = 无人做过（三篇正文级确认，CausalFlow 仅 Future Work 提及）。

### 8.3 三个最强一次性干预机制的共同三洞（读队 C 跨篇结论 = 我们的成本收益声明）

1. **无重复验证/无 Inconclusive**：CausalFlow/REFLECT 验证全是单次判断；CAR 有分布式
   设计但零真实噪声证据。DoVer 三态在三篇里无一沿用。→ GHX 以 DoVer 实测
   （Inconclusive 57.6-66.7%）为领域基线，把重复验证+三态做成常驻产出。
2. **无"每条归因结论"级成本账**：CAR 零、CausalFlow 仅 $130 聚合、REFLECT 仅
   trace 级均值。→ 锥靶向+配对前缀天然按（任务,轮,锥）分桶，可报告到结论级。
3. **无依赖图锥剪枝**：CausalFlow=线性链重跑全后缀（TraceLogger 记了细依赖但算法不用）；
   CAR=扁平序列；REFLECT=固定窗口（真因在 î₀−K 之前=结构性漏检，未量化）。
   → U 的依赖可达性锥：比全后缀省（真子集）、比固定窗口不漏（图给出而非猜宽度）。

### 8.4 方案一设计规范回填（读队 C/D/F 抽取，写进第一形态 spec）

- **冻结参考续跑策略**（CVT-RL）：反事实续跑用冻结参考，不用当轮活策略——harness
  逐轮在变，否则跨轮翻转率不可比，60 伯努利聚合失效。硬需求。
- **干预族分开播报**（CVT-RL）：删节点/替换/扰动工具输出=不同科学对象，不坍缩单标量。
- **随机遮蔽安慰剂对照**（E2-Explainer Fig.1 协议）：锥内靶向 vs 随机同规模，治 D11。
- **语义等价类熵辅助信号**（E2-Explainer Eq.5-7）：任务分同分时看答案聚类熵变，
  治 GAIA pass/fail 粗分辨率与 Inconclusive 高占比。
- **验证生存率一等公民**（CSO）：发布"lift 候选池→真实翻转验证通过池"比例；CSO 反推
  基准 671/4126≈16.3%（引用须标 derived from Table 3）。这是解冻后第一个可跑的先手数字。
- **LOO 省钱结论不许直接搬**（Agents that Matter）：其 LOO≈组合法系粗粒度 agent 级纯经验
  观察、无理论条件；先在少量锥上实测单敲除 vs 小规模联合敲除一致性再定。
- **排序/定标双读数**（Agents that Matter）：ρ 尚可 R² 崩负 → lift 只当排序信号，
  数值校准量单独报告。M13 = 此分裂的我方实例（定位对、定标错）。
- **重放原语引 Shepherd**：fork 134-143ms 与镜像无关、前缀字节级一致→cache 命中 ~95%、
  三级可逆性分类——基建可行性由对手证完，我们的声明只落在"翻转率归因"应用位。
- **REFLECT 的安慰剂梯**（Table 5）：正确修复提示 78.7% vs placebo 46.3% vs 无 35.6%——
  "起作用的是干预语义而非重试次数"的协议模板。

### 8.5 危险句清单（审稿人会引的原文 + 备好的回应）

1. AHE §3.3 "each edit becomes falsifiable…measurable contract between rounds" →
   回应：falsifiable≠calibrating；其 regression-precision 11.8%≈2×random 且无随轮升势。
2. HarnessFix §III-D3 harness memory "prevent future iterations…" → 回应：§IV-D 实验
   协议单轮，memory 无"下一轮"可读；HTIR 无跨轮图 diff。
3. Regimes "if an agent is built on an event-sourced graph…" → 回应：那是底层存储形状
   （ActiveGraph，引用的旁人前作），diagnose 实际吃扁平枚举；**同时自查**：它自曝的
   held-out 复用问题同样指向我们的 103 床 17 轮 ship 决策（D9）——方案二=自我治疗，
   论文主动交代。
4. Better-Harnesses III-B "meta-agent edits the harness by changing components"（零因果
   机制拿 16/21）→ 回应三层：RQ4 自认不迁移（模型特异性）；战场=窄目标带验证集 vs
   我们 L0 宽床噪声地板（两结果共同支持"目标收窄+证据定向"）；Life-Harness 证明
   **环境侧**编辑才迁移——归因引擎的新任务=ship 前预判候选属环境侧/模型侧并预测
   迁移性（可证伪预测，接 AHE 未做的校验回路）。
5. Shepherd §5.2 "branch…replay only the affected suffix" → 回应：原语引它，应用位
   （翻转率归因）它零命中；我们不声称发明分叉。
6. MEGA（三灯全亮）→ 回应：知识级图不可 do；执行级图的可干预性是方案一的先决条件。

### 8.6 写作素材杂项

- Better-Harnesses Lesson 1："markdown 摘要喂元代理丢细节、raw JSON 更好"——证据压缩
  即损耗，30% 锥引用衰减的同款病，T30 结构化事实的外部支持。
- CausalFlow 摘要写"supports training-time supervision"、正文列为 Future Work——
  摘要超前于交付的反例，自查我们各 doc 的口径。
- CausalFlow trace 税：结构化记录自身拉低基线 13.1pp——U 的"图不进上下文、零内容
  复制"设计恰好免此税，值得一句对比。
- HELIX 叙事抢位（"harness=一等可进化对象"已发表）→ 我们必须以"细粒度因果归因+
  真跑通的 17 轮闭环"作差异，不能只讲框架。
- GraphMind 负面子图=自认 future work → T-20 差异句现成（我们失败锥=一等公民）。

### 8.7 更正记录（本轮精读推翻的旧账）

- CAR "关键步恢复效率 ~0.91" = 误读（Shapley 效率公理自检，玩具 SCM）——已改 20 号 §1。
- HarnessFix "+6.3~18.4%" = 误记，真值 +5.5~18.4pp 绝对 / 15.2~50.0% 相对——已改。
- Regimes "LongMemEval+ActiveGraph 两床" = 范畴错误，量化床仅 LongMemEval-S——已改。
- §7.1 "三要素交集无人同时满足" → 收紧为 8.2 终稿（MEGA 3/3 带知识级限定）。
- T-23 措辞从"我们做分叉重放"改为"原语引 Shepherd、我们占翻转率归因应用位"。
- T-26 升级：迁移的是环境侧编辑（Life-Harness 116/126 正例 + Better-Harnesses RQ4
  反例）→ 归因引擎 ship 前预判环境侧/模型侧并预测迁移性。

---

## 9. 胜利方法论提取：T-28..T-32（08-20，自 §8 战力表"为什么赢"再挖一层）

11 家正结果系统的赢法拆开后，新出 5 件 + 1 条设计律。编号接 §7.4。

| # | 供体 | 器官→GHX 落点 | F2 差异（搬来后变的一步） | F7 动的数字 |
|---|---|---|---|---|
| T-28 | HarnessFix 2606.06324 四段修复契约 + AHE 2604.25850 manifest | **候选自带验收契约**：ship 时携带可机检契约——目标机制首异常计数须降多少、回归上界多少；Gate 逐条对账（adjudicate.py 的复活形态），对账误差回填提案者 | HarnessFix 契约只查一次、AHE 预测无校准；我们把契约做成跨轮闭环 = C7 白地的实现件 | ship 命中率、预测校准误差随轮走势 |
| T-29 | Shepherd 2605.10913 CRO | **首分歧点分叉评测**：Critic 验候选不再整任务重跑——前缀缓存回放到候选首次改变行为的位置，只活跑后缀；省下的开销换 K>1 重复验证 | CRO 用它做正向搜索省钱，我们用它把 k=1 的信用噪声（C6）摊薄 | 每候选验证成本、采纳判定的翻案率 |
| T-30 | GraphMind 2605.17617 ATR epoch 衰减 | **证据半衰期**：lift/首异常跨轮合并从等权改为按"证据轮与当前 config 的相似度/新鲜度"加权——每次 ship 都改变世界，旧轮证据在新 harness 下失效（D10） | 一次性诊断家族全体无此问题也无此解；**常驻环独有的病，治它即独有贡献** | 错药复发率、lift 跨轮稳定性 |
| T-31 | REFLECT 2606.09071 faithfulness 门 + Stage-3 改判 | **干预忠实门+翻转改判**：干预生效核验（扣的消息确实没进 compose、禁的 processor 确实没跑）不过不记账；归因记录以"验证翻转的位置"为准、覆盖观察式候选 | REFLECT 单 trace 一次性用，我们做成翻转账本的常驻记账规则 | 翻转证据假阳率、归因记录与 ship 的对齐率 |
| T-32 | MEGA 2608.10504 Seed-Epoch | **饱和判定+种子轮换**：\|Δ\|<ε 持续 m 轮判饱和→轮换评测种子集；与方案二加噪保留集互补（轮换治复用、加噪治查询） | MEGA 用它消数据方差混淆，我们用它治床复用（D9） | 环内分 vs 轮换集分的裂缝宽度 |

**设计律（不占编号）**：跑内 U 消费者**零 LLM 化**——Ledger 全层无模型调用是其成本
−29% 的前提；T-17/T-18 以确定性 processor 落地。T-17 第一形态 = **Nudge 附注不拦截**
（Ledger 的保守向 + M13 强制打断 −7 题的教训同款结论）。

**优先级上调**：T-01 GEPA 池（Better-Harnesses 16/21 = 二次领域内先例）；M24-T25
灭因账读侧（Better-Harnesses 的 search memory 明写"防止重提无效修复"= 读侧是赢家件，
我们的灭因账只写不读正是 M22 实锤病）；T-24 补 validity projection（扣边后 compose
合法性检查，防结构性坏 prompt）。

**战略收束**：五件新器官对上 11 病单——T-29→C6（k=1 信用噪声）、T-28→C7（预测不回
评）、T-30→D10（非平稳网）、T-32→D9（同床选择）；赢家方法论的空洞与我们自查的病单
互为镜像。其中 D10 只有常驻环会得，一次性家族既无此病也无此药——治它是白送的独占位。

---

## 10. Baseline 12 病单 × 文献对症 × 图相性（08-20，对 M22 审计清单映射）

映射时新产出两件图原生机制（编号接 §9）：

| # | 供体/先例 | 器官→GHX 落点 | F7 动的数字 |
|---|---|---|---|
| T-33 | 无直接先例（种群级锥独有；HarnessBank 门控筛/评估级联为效用先例） | **锥人口上界门**：候选点名机制 M → `\|失败锥含 M\|`=增益上界、`\|成功锥含 M\|`=回归暴露上界，两数从 U 确定性可算、零 LLM；上界<噪声阈（6 题）→ 床分不可判，闸门标"须机制粒度验收或合包"。= 病单 #12 缺的那把尺，且只有图臂有 | 上车候选数、每 ship 验证浪费 |
| T-34 | FAMAS 2509.13782 谱系激活模式（同形状先例） | **回归分诊**：每轮 pass→fail 翻转按"其锥是否含被 ship 机制"分嫌疑内/外；嫌疑外率≈噪声零点在线估计（治病单 #6），嫌疑内才进 M24-T32 定向重放（省钱层） | 回归账假阳率、Critic 错杀率 |

12 条映射摘要（详见会话 08-20；执行层 1→M23-B3+T-17+设计律零LLM、2→Life-Harness
环境契约+HarnessFix readiness 算子（修复臂中立、定位验收图靶向）、3→Ledger Inform+
GraphMind 图渲染实证（96.2 vs 77.3）、4→DAS 停机诊断+控制桶强制交卷模板（臂中立）、
5→工程无文献（期望 ≤2 题过不了 T-33 尺）；环层 6→PACE+Seed-Epoch+T-34、7→Agents
that Matter LOO/AHE 逐 edit 判决→M24-T32+T-29+T-28、8→纯 bug（M24-T11）、9→
HarnessBank 回退+T-01 池+T-05 灵感注入、10→T-28 schema+**L5 机器生成 manifest 已在
货架**、11→Shepherd commit graph 双亲不塌缩+GEPA merge 谱系、12→T-33+PACE+T-06
级联；任务五族 ①ChatDev 验证步 +15.6% 唯一反证数据点、②无解、③AgentConductor
任务条件资源先例、④工程、⑤fail-plausible（When Errors Become Narratives 命名）
→T-18 断转换器）。
