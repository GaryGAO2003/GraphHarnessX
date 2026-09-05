# 20 — GHX 归属 topic 判定 + 四路文献扫描（2026-08-19）

**方法**：deep-research three-way-scan 模式，4 个并行检索代理按候选子领域扫 2024–2026
文献（arXiv/Semantic Scholar/会议页），每篇要求 abs 页核验存在性；核验纪律实际生效的
证据：剔除已撤稿的 GraphTracer（作者自承方法论根本性错误，2025-12-22 撤稿）、拆穿两处
同名陷阱（AgentTrace ×2：arXiv:2602.10133 结构化日志 vs arXiv:2603.14688 因果图溯源；
AgentArmor 与 AuthGraph 的摘要张冠李戴）。

**问题**：GHX（自演化 LLM agent 元循环 + 图原生运行时：展开执行图 U + 三层身份哈希、
因果锥归因 + 跨任务 lift、类型化图编辑候选面、图存在门、门拒/翻转差分回流）属于哪个
topic，各支最近代表论文，本工作最贴近哪支。

---

## 判定（TL;DR）

**主 topic = self-evolving agents（自演化 agent），harness/scaffold 级。**
按 TMLR 2026 survey（arXiv:2507.21046）的 What/Where 轴：演化对象是 harness 配置
（processors/tools/prompt），不是权重、不是单纯记忆。

**具体占位 = 三支交叉的空隙**：execution provenance（记录面）× automated failure
attribution（诊断面）× workflow-as-graph 受约束候选面（编辑面）拼成的**闭环**。
四路扫描各自独立得出同一读数：这个组合位置目前没人占——

1. 自演化支（12 篇）：候选表示正从自由代码向类型化图收敛（AFlow→A²Flow），但
   **没有一篇把"候选申报的机制是否在执行中真触发过"当准入条件**——选择信号
   始终是聚合跑分或帕累托支配。
2. 归因支（12 篇）：2026 上半年从 LLM 通读判读转向结构化可重跑证据（反事实回放/
   SCM do-算子/符号执行），但除 FlowFixer 外都停在单轨迹粒度；**没有一篇做
   "跨任务节点占率（lift）驱动候选、再回图验证机制命中"**。综述 arXiv:2605.14892
   直接点名：失败归因与 self-evolution 是两条没接起来的线。
3. provenance 支（9 篇）：术语正收敛到 "execution provenance / evidence tracing"
   （survey arXiv:2606.04990），typed graph 正在取代 OTel 树状 span；但 provenance
   目前只服务 human trust/审计/调试，**survey 未发现接回自动改进闭环的工作**
   （唯一自动接动作的 AgentArmor 是安全拦截，不是能力改进）。
4. 结构化空间支（12 篇）：MermaidFlow / AgentFlow-harness 证明类型化图 IR + 合法性
   检查可行，AlphaEvolve 证明级联评测门可行，RePaCA/APR 线证明"过测≠修好"是真
   问题；但**没人把结构合法/新颖/反事实/replay/写后哈希身份对账拼进一条事务流水线**。

**论文定位一句话**：provenance-grounded self-evolution——用执行溯源图做诊断证据、
类型化图编辑做候选表面、机制存在性做准入门的 harness 级自演化闭环。

## 正面相关论文速查（CH2 弹药分类）

| 用途 | 论文 |
|---|---|
| 最近邻（同构，须点名差异） | MermaidFlow (2505.22967, ICML'25)；AgentFlow-harness (2604.20801)；AFlow (2410.10762, ICLR'25 Oral)；GRADE (2606.22741) |
| 正面冲突（C4 素材：自由代码候选面 vs 类型化） | ADAS (2408.08435)；Darwin Gödel Machine (2505.22954, ICLR'26)；Gödel Agent (2410.04444, ACL'25) |
| 归因方法对照基线 | CausalFlow (2605.25338)；Causal Agent Replay (2606.08275)；FALAT (2606.00765)；AgenTracer (2509.03312, ICLR'26)；GEPA (2507.19457, ICLR'26 Oral)；DoVer (2512.06749) |
| 缺口 motivation 直接引用 | From Agent Traces to Trust survey (2606.04990)；Beyond Individual Intelligence (2605.14892)；RePaCA (2507.22580, Neurocomputing'26) |
| 坐标系/词表 | Self-Evolving Agents survey (2507.21046, TMLR)；From Static Templates to Dynamic Runtime Graphs survey (2603.22386)；MAST (2503.13657)；Who&When (2505.00212, ICML'25 Spotlight) |

**Caveat**：2026 年的 26xx 号 preprint（CausalFlow/CAR/GRADE/FALAT/FlowFixer/
AgentFlow-harness/两 survey）均未过同行评审；本扫描是 three-way-scan 非 systematic
review，RL-training 侧（AgentPRM 一线）只扫了边缘。

---

# 附录：四路完整卡片（代理原始产出，abs 页核验）

## 路 A · self-evolving agents / agent scaffold 自动搜索（12 篇）

### Automated Design of Agentic Systems (ADAS) / Meta Agent Search
Source: arXiv:2408.08435 | 2024 | Shengran Hu et al. | ICLR 2025
- WHY: 手工设计的 agent 组件（prompt/工具/控制流）终将被搜索方案取代。
- HOW: 搜索空间=可执行 Python 代码本身（图灵完备）；元代理直接编程生成候选 agent，候选跑分是唯一验证信号。
- WHAT: 搜出的 agent 跨域跨模型迁移仍保持优势；候选生成无结构约束。
- vs-GHX: 候选面是纯自由代码，无类型约束；验证=聚合跑分，无执行踪迹归因，无"机制真触发"门——GHX 明确拒绝的正是这种候选面。

### Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement
Source: arXiv:2410.04444 | 2024 | Xunjian Yin et al. | ACL 2025
- WHY: 人工预定义的优化算法/固定例程本身是搜索空间天花板。
- HOW: agent 运行时自省直接修改自身实时状态和行为逻辑，无固定元优化算法。
- WHAT: 数学推理与复杂 agent 任务上持续自我提升；修改即生效，缺独立验证/回滚。
- vs-GHX: 修改与生效是同一动作，无 propose→judge→gate 分离验证门，本组门控最弱，与 GHX 强门控相反。

### Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents
Source: arXiv:2505.22954 | 2025 | Jenny Zhang et al. | ICLR 2026
- WHY: 经典 Gödel Machine 要求形式化证明修改必有收益，不可行；改用经验验证。
- HOW: agent 对自身代码库生成自由代码 diff，存开放式档案；重跑编码基准全量做经验验证选候选。
- WHAT: 编码基准持续开放式提升（SWE-bench 20.0%→50.0%）；只看聚合分数，不看机制是否真被触发。
- vs-GHX: 候选=自由 diff；验证门=基准重跑分数，非"某条机制在执行轨迹里被证实触发"——与图存在门思路不同。其档案机制是 genotype/phenotype 双哈希身份最接近的先例之一。

### Huxley-Gödel Machine
Source: arXiv:2510.21614 | 2025 | Wenyi Wang et al.（Schmidhuber 团队）
- WHY: DGM 存在"自我提升潜力—当前跑分"错配。
- HOW: 沿用 DGM 自由 diff+树状档案，选择指标换成 CMP（聚合候选在自我修改树里所有后代的表现）。
- WHAT: 更少 CPU 时数超此前方法，SWE-bench Lite 达人类工程师水平。
- vs-GHX: 仍自由代码候选面，验证仍基准分数（只是换"谁的分数"）；无机制级存在性核验。

### A Self-Improving Coding Agent (SICA)
Source: arXiv:2504.15228 | 2025 | Maxime Robeyns et al. | NeurIPS 2025
- WHY: 验证 agent 能否只靠编辑自己的脚手架持续变强（不碰权重）。
- HOW: 元代理读档案，对自身代码库提出修改，重跑 SWE-bench Verified 子集验证归档。
- WHAT: 17%→53%；仅小规模子集单一代码库验证。
- vs-GHX: 自由代码编辑 + benchmark 回归门控，不做机制级归因。

### AFlow: Automating Agentic Workflow Generation
Source: arXiv:2410.10762 | 2024 | Jiayi Zhang et al. | ICLR 2025 (Oral)
- WHY: 手搭 workflow 难规模化。
- HOW: workflow=固定 Operator 库拼成的代码图，MCTS 在图修改动作空间迭代，验证集准确率做反馈。
- WHAT: 六个推理数据集超人工 workflow。
- vs-GHX: 候选面已类型化（预定义 Operator 拼图），最接近 GHX 类型化图编辑的先行者；但选择依据仍是准确率聚合分数，无边/Operator 级触发归因。

### A²Flow: Self-Adaptive Abstraction Operators
Source: arXiv:2511.20693 | 2025 | Mingming Zhao et al. | AAAI 2026
- WHY: AFlow 的 Operator 库仍人工预定义。
- HOW: 从示范自动提炼 operator + operator memory，词表本身成为演化对象。
- WHAT: 通用/具身基准 +2.4%/+19.3%，开销 −37%。
- vs-GHX: 类型化 operator 图更进一步，但验证依旧下游分数。

### AlphaEvolve
Source: arXiv:2506.13131 | 2025 | Alexander Novikov et al. | DeepMind 技术报告
- WHY: LLM 创造性代码生成 + 可靠自动验证结合。
- HOW: 候选=自由代码修改；领域自定义评估器给适应度，进化框架迭代；级联评测（便宜→贵）只放行可证明改进。
- WHAT: 4×4 矩阵乘 48 次标量乘（56 年首次超 Strassen）；数据中心调度/芯片。
- vs-GHX: 验证强但是外部领域预言机的标量适应度，非对 agent 自身执行图的自指式核验。级联门与多门同构但不查结构/新颖/反事实/身份。

### GEPA: Reflective Prompt Evolution Can Outperform RL
Source: arXiv:2507.19457 | 2025 | Lakshya A Agrawal et al. | ICLR 2026 (Oral)
- WHY: RL 把整条系统级轨迹坍缩成标量奖励，丢"为什么失败"。
- HOW: 候选=prompt 文本编辑；LLM 读全轨迹自然语言反思诊断失败，帕累托前沿筛选合并。
- WHAT: 平均超 GRPO 10%（最高 20%），rollout 少 35 倍。
- vs-GHX: "读执行轨迹做诊断"与因果锥归因最接近；但候选面仍自由文本，筛选门是帕累托支配非机制存在性。

### EvoAgentX
Source: arXiv:2507.03616 | 2025 | Yingxu Wang et al. | EMNLP 2025 Demo
- HOW: 五层平台集成 TextGrad/AFlow/MIPRO 迭代改写 prompt/工具/拓扑。
- vs-GHX: 工程整合平台，候选面异构，无统一执行轨迹归因或存在性门。

### EXG: Self-Evolving Agents with Experience Graphs
Source: arXiv:2605.17721 | 2026 | Yuxin Jin et al.
- HOW: 历次执行成败组织成结构化关系图，在线增长+离线固化供检索复用。
- vs-GHX: 图的对象是"经验记忆"非"可执行任务图"；是记忆检索，不是候选准入。

### A Survey of Self-Evolving Agents: What, When, How, Where
Source: arXiv:2507.21046 | 2025 | Huan-ang Gao et al. | TMLR (2026-01)
- WHAT: 本子领域最常被引的分类词表；安全性/可扩展性/共演化是未解方向。
- vs-GHX: 按其 Where 轴，GHX 属 harness-level 自演化；词表可直接用于定位。

**路 A 小结**：伞形词 "self-evolving/self-improving agents"；搜索谱系自称 "automated
design of agentic systems"/"agentic workflow generation"；Gödel 谱系 "recursive
self-improvement"；GEPA 开创 "reflective prompt evolution"。走向：候选表示向类型化图
收敛、选择信号从标量转向读轨迹诊断，但**都停在诊断，没有变成可验证的准入门**；"图"
分裂成两线（可执行工作流图 vs 经验记忆图），两线都不做执行本身的准入核验。

## 路 B · 失败归因 / credit assignment / 轨迹诊断（12 篇）

### MAST — Why Do Multi-Agent LLM Systems Fail?
Source: arXiv:2503.13657 | 2025 | Mert Cemri et al. (UC Berkeley)
- HOW: 归因单位="失败模式类别"；150 条轨迹人工标注（κ=0.88）建 14 类三大类分类法，LLM-judge 在 1600+ 轨迹验证。
- WHAT: 后续几乎所有归因论文的引用起点；只分类不根治。
- vs-GHX: 停在贴标签；lift 表做的正是 MAST 止步之处——"哪类失败"压到"哪个节点机制"。

### Who&When — Which Agent Causes Task Failures and When?
Source: arXiv:2505.00212 | 2025 | Shaokun Zhang et al. | ICML 2025 (Spotlight)
- HOW: 归因单位=agent+决定性失败步；127 个 MAS 失败日志数据集，三种 LLM-judge 归因法。
- WHAT: agent 级最好 53.5%，step 级仅 14.2%。
- vs-GHX: 确立任务与基准；纯 LLM-judge，无图/因果结构，不回灌修复。

### TRAIL — Trace Reasoning and Agentic Issue Localization
Source: arXiv:2505.08638 | 2025 | Darshan Deshpande et al. (Patronus AI)
- HOW: span/error-type 单位；148 条真实轨迹 841 错误，长上下文 LLM 通读定位。
- WHAT: 最强模型仅 11% 准确率——LLM 读长轨迹调试严重不够用。
- vs-GHX: 反衬"结构化因果锥而非整段文本喂 judge"的必要性。

### RAFFLES — Reasoning-based Attribution of Faults
Source: arXiv:2509.06822 | 2025 | Chenyang Zhu et al. | EACL 2026
- HOW: 中心 Judge + 专职 Evaluator 多轮迭代判"决定性故障"。
- WHAT: Who&When Hand-Crafted >20%、Algorithmic >50%。
- vs-GHX: 抬高 judge 范式上限，仍文本推理链，不闭环。

### AgenTracer — Who Is Inducing Failure?
Source: arXiv:2509.03312 | 2025 | Guibin Zhang et al. | ICLR 2026
- HOW: 反事实回放+程序化故障注入造大规模标注轨迹，多粒度 RL 训 8B 专用归因模型。
- WHAT: 超 Gemini-2.5-Pro 最多 18.18%；接入 MetaGPT/MaAS 带来 4.8–14.2% 下游实测增益。
- vs-GHX: 本支离 GHX 最近之一——结构化信号替代文本判读且实测接回下游；但靠注入故障造数据+训判别模型，GHX 靠记录真实展开图+跨任务节点占率。

### AgentDebug / AgentErrorTaxonomy
Source: arXiv:2509.25370 | 2025 | Kunlun Zhu et al.（James Zou, Jiaxuan You）
- HOW: 归因单位=操作模块（memory/reflection/planning/action/系统级）；AgentErrorBench + 定位根因模块 + 生成纠正反馈。
- WHAT: all-correct 准确率超最强基线 24%；反馈接回重跑成功率最高 +26%。
- vs-GHX: 明确接回改进闭环；但归因单位是预定义认知模块非执行图节点，粒度弱于因果锥。

### AgentPRM — Process Reward Models via Step-Wise Promise and Progress
Source: arXiv:2511.08325 | 2025 | Zhiheng Xi et al.
- HOW: TD 估计+GAE 给每步打"承诺与进展"分，纯统计非 judge。
- vs-GHX: 另一条路——逐步信号直接变训练奖励（在线稠密奖励调策略）；GHX lift 是离线诊断证据出候选，互补非同范式。

### DoVer — Intervention-Driven Auto Debugging (Microsoft)
Source: arXiv:2512.06749 | 2025 | Ming Ma et al.
- HOW: 归因单位="可验证的修复假设"；对疑似位置主动干预（编辑消息/改写计划）后重跑，用任务恢复验证假设。
- WHAT: GAIA/AssistantBench 挽回 18–28% 失败，验证/推翻 30–60% 归因假设。
- vs-GHX: 与图存在门理念最一致——不满足于归因判断，要求重跑/干预验证；DoVer 逐假设试错，GHX 批量事后机制核验。

### CausalFlow — Causal Attribution and Counterfactual Repair
Source: arXiv:2605.25338 | 2026 | Akash Bonagiri et al.
- HOW: 轨迹=顺序步骤链，step 级反事实干预算 Causal Responsibility Score，为高责任步生成最小编辑修复，产出对比训练对。
- WHAT: 四类任务上修复最小性/因果共识分优于启发式。
- vs-GHX: 因果结构最贴近之一，且归因→修复→再训练闭环；但单轨迹纵向步链干预 vs GHX 跨任务横向锥占率。

### Causal Agent Replay (CAR)
Source: arXiv:2606.08275 | 2026 | Jaineet Shah
- HOW: agent run 建模为 SCM，do-算子干预+同策略前向重放，单步对照估计量+蒙特卡洛 Shapley 分摊责任。
- WHAT: 合成真值模型上正确恢复关键步与双步交互 Shapley（效率 0.909 vs 解析 0.91）；仅合成验证。
- vs-GHX: 因果框架最正式；纯诊断，未接改进，未在真实系统复现。

### FALAT — Dependency-Guided Search
Source: arXiv:2606.00765 | 2026 | Md Nakhla Rafi et al.
- HOW: 先建正确执行"期望基线"圈可疑区，依赖追踪区分"引入错误步"与"仅传播错误步"，修正候选步验证。
- WHAT: Who&When 算法轨迹 step 级 46.0%。
- vs-GHX: 同样把归因当结构/依赖问题，"根因 vs 被牵连"正是因果锥要处理的核心；单轨迹内依赖，不做跨任务，不反哺候选。

### FlowFixer — Diagnosis-Driven Automatic Repair via Symbolic Inference
Source: arXiv:2607.02882 | 2026 | Xuyan Ma et al.
- HOW: 执行轨迹转符号化轨迹+符号推理得"可执行行为规范"，归因→根因→执行前过滤→动态验证修复补丁，全程不依赖 LLM judge。
- WHAT: 修复成功率 71.3%（+11.9–27.6pp），三平台（Dify/Coze/n8n）验证。
- vs-GHX: 本支唯一把图结构归因+自动修复做成同一个非 judge 闭环的工作；但图是编排平台静态节点依赖图，GHX 是动态展开执行图+跨任务统计。

**路 B 小结**：叫法 "automated failure attribution"（Who&When 确立）/"trace-issue
localization"（TRAIL 系）；"agentic credit assignment" 是 RL 训练支独立叫法。走向：
归因单位从整段轨迹通读转向结构化可重跑证据（2026 上半年反事实回放/SCM/符号执行扎堆）。
闭环只有 AgentDebug/DoVer/CausalFlow/FlowFixer 真接上，且除 FlowFixer 几乎都单轨迹
粒度；**无人做跨任务 lift 驱动候选+回图核验的组合**。综述 arXiv:2605.14892（Beyond
Individual Intelligence）点名：归因与 self-evolution 基本是两条独立线。
（核验剔除：GraphTracer 已撤稿；Agent-R 2501.11425 属自训练范式；AgentLocate
2607.07989 (COLM'26) 不出 judge 支范畴。）

## 路 C · AgentOps / 可观测性 / execution provenance（9 篇）

### AgentOps Taxonomy
Source: arXiv:2411.05285 | 2024 | Liming Dong, Qinghua Lu, Liming Zhu | preprint
- HOW: 对 AgentOps 工具做 mapping study 出 taxonomy（logs+metrics+traces+alerts，session 级到 token 级）。
- vs-GHX: 纯人看的 monitoring；无因果模型无归因，不接自动改进。

### OpenTelemetry GenAI Semantic Conventions (gen_ai.*)
Source: github.com/open-telemetry/semantic-conventions-genai | 2024– | CNCF 工作组 | 工业标准
- HOW: span/metric/event 属性命名空间；树状 span（非图），agent 编排靠 parent-child 嵌套。
- vs-GHX: 纯记录层标准，不定义归因算法；GHX 可挂其上采数的下游标准。

### AgentSight: System-Level Observability Using eBPF
Source: arXiv:2508.02736 | 2025 | Yusheng Zheng et al. | ACM ML for Systems Workshop
- HOW: boundary tracing——eBPF 拦 TLS 取 LLM intent + 内核事件取系统 effect，跨进程因果关联，零插桩。
- vs-GHX: 自动检测（injection/浪费性循环）但止步于报出来；检测器非改进闭环。

### GRADE: Graph Representation of LLM Agent Dependency and Execution
Source: arXiv:2606.22741 | 2026 | Yue Zhao
- HOW: 每次 run=typed graph 双层（execution 层免费来自 trace；dependency 层按置信来源四档 known/observed/declared/inferred）。
- WHAT: dependency 层能预测失败、定位出错步。
- vs-GHX: 与"展开执行图+身份哈希"高度同构；止步诊断，图是诊断产物非改进闭环输入。

### From Agent Traces to Trust: Survey of Evidence Tracing and Execution Provenance
Source: arXiv:2606.04990 | 2026 | Yiqi Wang et al.（11 人）| survey
- HOW: 定义 execution provenance=执行的完整 typed graph（六类边：causal/procedural/dependency/update/contradiction/invalidation），evidence tracing 是其投影；六维 taxonomy。
- WHAT: 该子领域首篇系统 survey，统一术语。
- vs-GHX: 明确指出 provenance 目前只服务 human trust/审计/调试，**未发现接回自动改进循环的已有工作**——GHX motivation 可直接引用。

### CausalFlow / Causal Agent Replay（与路 B 重叠，此处从略）

### AgentTrace: Causal Graph Tracing for Root Cause Analysis
Source: arXiv:2603.14688 | 2026 | Zhaohui Geoffrey Wang | preprint/审稿中
- HOW: 执行日志构因果图（sequential/communication/data dependency 三类边），错误节点 backward BFS+结构特征排序根因。
- vs-GHX: post-hoc 定位给人看的排序列表；不改 agent 不接修复。**勿与同名 arXiv:2602.10133（结构化日志框架）混淆。**

### AgentArmor: Program Analysis on Agent Runtime Trace（ByteDance）
Source: arXiv:2508.01249 | 2025
- HOW: trace 重建成 CFG/DFG/PDG 图 IR + 安全元数据 + lattice 类型系统三阶段检查。
- WHAT: AgentDojo TPR 95.75% / FPR 3.66%。
- vs-GHX: 本支"记录后接自动动作"程度最高，但动作是安全拦截非能力改进；图 IR+类型系统工程手法可参考。

**路 C 小结**：工业叫 "agent observability/AgentOps"（OTel gen_ai.* 是事实标准层），
学术 2026 上半年收敛到 "execution provenance / evidence tracing"。图表示在收敛：多篇
2026 新作不约而同选 typed graph 而非树状 span——与 GHX 展开图判断方向一致。与
self-improving 工作接口很薄：凡做归因的全部止步于"定位/解释给人看"，**"记录展开图+
身份哈希并在其上做归因驱动自动改进"这一整圈在本支无直接先例**。

## 路 D · 图/结构化表示 + 受约束搜索空间 + 自修改验证（12 篇）

### GPTSwarm: Language Agents as Optimizable Graphs
Source: arXiv:2402.16823 | 2024 | Zhuge et al.（Schmidhuber）| ICML 2024
- HOW: 节点=函数/LLM 查询，边=信息流；节点级 prompt 优化器+边级连通性优化器。
- vs-GHX: 图表示同源；编辑是连续化优化非离散类型化工具调用，无事务门无身份哈希。

### G-Designer: VGAE 生成通信拓扑
Source: arXiv:2410.11782 | 2024 | Zhang et al. | ICML 2025
- vs-GHX: 整图一次性生成（合法性隐含在解码器训练分布），与"渐进类型化编辑+多门"相反。

### MermaidFlow: Safety-Constrained Evolutionary Programming
Source: arXiv:2505.22967 | 2025 | Zheng et al.（A*STAR）| ICML 2025
- WHY: 直接指控自由 LLM 生图/写码产出脆弱计划，主张把搜索空间限制在可静态验证的图语言里。
- HOW: Mermaid 图语言做 IR；crossover/mutation/insertion/deletion 四类保语义算子；变异后静态验证再执行。
- vs-GHX: **检索到的最近邻**——"类型化图 IR+保正确性算子+验证后进入"同一条路线；GHX 多写后哈希对账+双哈希身份+动态/事务门（replay、反事实）。

### AgentFlow-harness: Synthesizing Multi-Agent Harnesses for Vulnerability Discovery
Source: arXiv:2604.20801 | 2026 | Liu et al. | preprint (cs.CR)
- HOW: typed graph DSL 覆盖角色/prompt/工具/拓扑/协议整套配置面；反馈驱动诊断循环读运行时信号定位 harness 哪部分致败，定向编辑。
- WHAT: TerminalBench-2 84.3%；Chrome 10 个零日（含 2 沙箱逃逸 CVE）。
- vs-GHX: **编辑空间形态最同构**（类型化图 DSL、多维配置面、诊断驱动定向编辑）；差异：它是事后归因修复，GHX 是事前事务门+事后身份核验双重锁。

### AgentSquare: Modular Design Space
Source: arXiv:2410.06153 | 2024 | Shang et al.（清华）| ICLR 2025
- HOW: Planning/Reasoning/ToolUse/Memory 四模块接口；模块进化+重组两算子；性能预测器前置淘汰。
- vs-GHX: 同属约束空间防自由代码；约束粒度=4 固定模块 IO 协议，淘汰用统计预测器非确定性门。

### MaAS: Agentic Supernet
Source: arXiv:2502.04180 | 2025 | Zhang et al. | ICML 2025 (Oral)
- HOW: 学习架构空间概率分布，按 query 难度采样定制系统。
- vs-GHX: 连续分布搜索空间，验证靠采样后端到端跑分，无离散编辑无多门。

### EvoFlow: Evolving Diverse Agentic Workflows
Source: arXiv:2502.07373 | 2025 | Zhang et al.
- HOW: 种群+niching 维持异构工作流多样性。
- vs-GHX: 变异后合法性保障机制不透明——正是"验证自改动真生效"要补的洞。

### AFlow / ADAS / Darwin Gödel Machine（与路 A 重叠，此处从略——路 D 视角结论：AFlow 编辑=LLM 自由代码补丁非受限 DSL；ADAS 主张自由代码空间靠归档+经验筛选即可，与 GHX 哲学正面冲突；DGM 放弃可证明有益退到经验跑分，档案≈QD 存档是双哈希身份最近先例）

### AlphaEvolve（与路 A 重叠——路 D 视角：级联评测器=可复用验证基础设施，但只验"分数变好"，GHX 还验"改动合法、确实新、确实生效在该生效位置"）

### RePaCA: Static Automated Patch Correctness Assessment
Source: arXiv:2507.22580 | 2025 | Fuster-Peña et al. | Neurocomputing Vol.701 (2026)
- WHY: 正面回答"过了测试≠真修好"（patch overfitting）。
- HOW: 推理 LLM 读改前/后代码对生成思维链，分类"真修复 vs 过拟合"，RL 微调。
- WHAT: 83.1% 准确率。
- vs-GHX: 问题意识同源（拦"看似生效实则无效"）；但是事后概率判别器——"GHX 验证门只剩打分器会退化成什么"的对照组。另见 Invalidator arXiv:2301.01113（APR patch-overfitting 线）。

**路 D 小结**：无统一学名；2026-03 综述（arXiv:2603.22386, From Static Templates to
Dynamic Runtime Graphs）按 workflow-as-graph / workflow-as-code /
workflow-as-continuous-distribution 三线收编，GHX 属第一线约束最紧一端。相邻但不同线：
DSPy (2310.03714)、Trace/OptoPrime (2406.16218)、QD 谱系（QDAIF 2310.13032）——
genotype/phenotype 术语的更直接源头。"验证自改动真生效"有人正面碰过（MermaidFlow 静态
合法、AlphaEvolve 级联评测、RePaCA 补丁分类、DGM 经验跑分），但**没人把结构/新颖/
反事实/replay/写后哈希身份对账拼进一套事务流水线**。

---

*生成：deep-research three-way-scan，4×researcher(sonnet) 并行，2026-08-19。*
*用途：CH2 related work 骨架 + novelty 定位；引用前请对 26xx preprint 逐篇复核。*
