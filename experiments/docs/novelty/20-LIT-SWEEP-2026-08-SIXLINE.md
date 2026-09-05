# 20 · 六路文献扫描原始账（2026-08-19）

19 号档案 §7 的数据附件。用户判定"看的论文不够多、不够新"后发起的第二次全域扫描：
六路并行发现代理，窗口 2025-09 → 2026-08，只列清单不深读（精读另派）。

**核实纪律**：每条 NEW 都由代理现场打开 arXiv 页面对上 标题+ID+日期（部分标注
"标题级/S2 级"= 仅经 Semantic Scholar API 核对 ID/标题/日期、未开摘要）。会话级
WebSearch 配额在扫描开始前已耗尽（200/200），六路全部改走 Semantic Scholar 引用图
API + arXiv 逐月列表页/站内搜索 + abs 页逐条核验；S2 间歇 429、export.arxiv.org 全程
429。共同覆盖缺口：ICLR/ICML/ACL 2026 accepted 列表基本未能直接扫（无搜索入口），
ISSTA/ASE 2026 DBLP 页 404。关联度：A=同题竞品或必读，B=方法可搬，C=背景。

日期均为 arXiv ID 前缀月（v1 首现月）。

---

## §1 失败归因线（29 条 NEW）

判定（Who&When SOTA）：压"步级 14.2%、长日志塌 0%"的主力仍是 SAFARI（2606.24626，
KNOWN）：诊断精度与上下文长度解耦，超原生窗口 5 倍仍 0.58；KDD 2026 StepFinder 宣称
更优+推理时间 −79% 但摘要无绝对值。长时域归因已成公认下一战场（LongRCA/长时域归因
基准/Who&When Pro 平行出现）。

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2607.09996 | 26-07 | – | Who&When Pro | 重放成功前缀+注入失败造 12,326 条金标轨迹，26 个 bench 的继任测试床 | A |
| 2607.07989 | 26-07 | – | AgentLocate | 多视角 LLM 裁判集成+置信度聚合+轻量微调，同定位责任 agent 和失败步 | A |
| 2603.25001 | 26-03 | – | MP-Bench | 反对单根因假设；论证"LLM 不会归因"多为 benchmark 设计缺陷假象 | A |
| 2606.03467 | 26-06 | KDD26 | StepFinder | 日志编码为时序语义序列+轻量时序注意力打分，推理时间 −79% | A |
| 2608.15242 | 26-08 | – | LongRCA Bench | 1140 条中位 145 步长轨迹；baseline 根因步 13.2%，RCTA 51.1% 角色/24.1% 步 | A |
| 2608.06909 | 26-08 | – | Long-Horizon Trajectory Attribution | 统一归因组件 schema+归因链恢复任务，增量贡献/留一扰动两类基线 | A |
| 2608.07899 | 26-08 | – | TelemetrySuffBench | 完整遥测 origin-step 97.2% → 砍成标准日志字段 0.5%；须显式决策-证据链接 | A |
| 2608.14680 | 26-08 | – | AGENTCHAOSBENCH | A2A/MCP 边界注入 10 类故障，最好 LLM 诊断器故障识别仅 24.8% | A |
| 2509.13782 | 25-09 | PACMSE26 | FAMAS | SBFL（软件谱系定位）首搬 MAS：轨迹重放+可疑度公式（agent 组×action 组激活） | A |
| 2601.06818 | 26-01 | – | AgentHallu | 693 轨迹/7 框架，5 类 14 子类幻觉分类，最好模型步定位仅 41.1% | B |
| 2608.02026 | 26-08 | – | HPFA | 超图配对（失败 vs 成功路径超边）收窄根因空间，再 SFT+RL 训轻量归因器 | A |
| 2606.08275 | 26-06 | – | Causal Agent Replay (CAR) | 轨迹建 SCM，五种 do 算子+point-of-commitment+预算受限蒙特卡洛 Shapley。⚠读队 C 核实：5 页单作者、纯手搭玩具 SCM、零真实 benchmark、零成本数字、mocked 工具；扫描期记的"关键步恢复效率 ~0.91"系误读——实为 Shapley 效率公理自检（φ 和 0.909 vs 解析 1−q²=0.91），不可当准确率指标引用 | A |
| 2605.25338 | 26-05 | – | CausalFlow | 因果归因+反事实修复（S2 级） | B |
| 2607.07702 | 26-07 | – | STRACE | 结构化轨迹分析+因果抽取服务 agent 优化（S2 级） | B |
| 2606.02060 | 26-06 | – | TELBench+DRIFT | 逐 claim 核查轨迹证据支持度、标不支持 span，错误检测最多 +30pp | A |
| 2607.18754 | 26-07 | – | AgentDebugX | Detect→Attribute→Recover→Rerun 工具链；GAIA 根因精确率 28.8%、修复 13/73 | A |
| 2606.14589 | 26-06 | – | When Errors Become Narratives | 生产 agent 8 周现场研究，5 类静默失败；fail-plausible 叙事化错误；70% 靠人工发现 | A |
| 2606.09863 | 26-06 | – | From Confident Closing to Silent Failure | 刻画"自信收尾实则失败"的假成功模式（S2 级） | B |
| 2604.17658 | 26-04 | ACL26-F | ErrorProbe | 症状驱动反向追溯+三代理验证假设，证据 confirm 后才写经验记忆 | A |
| 2606.06324 | 26-06 | – | HarnessFix | 失败轨迹→harness 组件归因（7 层 ETCLOVG 分类），缺陷记录→受限补丁，+5.5~18.4pp（相对 15.2~50.0%；读队 A 改正原误记 +6.3~18.4%） | A |
| 2607.08938 | 26-07 | – | Better Harnesses, Smaller Models | 元 agent 自动 harness 适配：21 组 16 升，最佳 4% 成本得 89.7% 大模型表现 | A |
| 2605.10913 | 26-05 | – | Shepherd | Git 式可逆执行轨迹（回滚快 docker commit 5 倍），供元代理反事实修复/RL 信用 | A |
| 2606.10241 | 26-06 | – | Regimes | 事件溯源运行时+静态/沙盒/样本内/held-out 四级门禁晋升（量化床仅 LongMemEval-S；ActiveGraph=所依赖的底层 runtime[Nakajima 2026]，非评测床——读队 A 更正） | A |
| 2607.24117 | 26-07 | – | Grading the Narrators | 圣训学 isnad/rijal 搬 claim 级来源评分，serve/review/quarantine 三通道 | B |
| 2608.06790 | 26-08 | – | AgentChaos | SRE 混沌工程搬 agent：HTTP 层注入 3 类故障，完成率最多跌 50pp | B |
| 2607.29055 | 26-07 | – | MARS | MAS 修复当 MCTS 搜索：诊断引导扩展+部分 rollout 降本，+3.0~12.1% | B |
| 2606.08162 | 26-06 | – | Entropy Principle | 热力学熵建模无序度 S(t)=S0·e^(αt)，PIG Engine 做确定性熵治理 | B |
| 2607.16387 | 26-07 | – | AdaMAST | 从执行轨迹归纳式自动生成失败分类（非人工预定义），SWE-agent/Claude Code 验证 | B |
| 2608.03735 | 26-08 | – | TART | 多语言规划失败分类显式暴露给 planner，多语言 GAIA +5.6pp | B |

KNOWN ID 复核：CHIEF=2602.23701、FALAT=2606.00765、GRADE=2606.22741、MASPrism=2605.07509、
AgentRx=2602.02475、AgentTether=2607.06273、DoVer=2512.06749、综述=2606.04990、
SAFARI=2606.24626；ASCon 现挂 2608.10646（可能为大改版，引用前核对）。

## §2 因果/干预线（23 条 NEW）

判定（空位核实）：**"干预/反事实归因常驻自进化环逐轮产证据"截至 2026-08 仍空**。
最近 HELIX（2608.13951）：干预可审计+harness-model 共进化，但粒度是配置组合 A/B、
只跑一轮；Shepherd/CausalFlow 停在单次诊断/一次性监督。另：LLM-judge 一次性归因
家族（spectrum/hypergraph/conformal 变体 20 余篇）判饱和未逐条收。

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2605.25338 | 26-05 | – | CausalFlow | 逐步反事实干预算 Causal Responsibility Score，生成翻转结果的最小编辑修复对 | A |
| 2606.09071 | 26-06 | – | REFLECT | 候选错误步受控重放+诊断专用补丁，核验"结果翻转"作对比证据修正归因（静默失败向） | A |
| 2509.10401 | 25-09 | – | Abduct-Act-Predict | 溯因根因→最小干预→模拟验证三步 SCM 脚手架，Who&When 上 2.4–2.9× | A |
| 2603.10749 | 26-03 | – | AttriGuard | 每个候选工具调用并行反事实测试（teacher-forced shadow replay），判是否被注入内容因果驱动 | A |
| 2608.06790 | 26-08 | – | AgentChaos | （同 §1）HTTP 层免改代码故障注入 | A |
| 2602.19843 | 26-02 | – | MAS-FIRE | 15 类故障×3 注入机制；闭环迭代架构中和 40%+ 线性流下致命故障 | A |
| 2605.15581 | 26-05 | – | STAR | RCA agent 四阶段+反事实候选评估定位决定性阶段，阶段特定 patch-and-replay | A |
| 2607.11098 | 26-07 | – | AgentCheck | MCP 层缓存真实调用后按 12 种故障重注入、分叉点后转实时，test-fix-verify 工作台 | A |
| 2605.10913 | 26-05 | – | Shepherd | （同 §1）Terminal-Bench 2.0 超 MetaHarness 12.8%、墙钟 −58% | A |
| 2509.13782 | 25-09 | PACMSE26 | FAMAS | （同 §1） | A |
| 2607.07702 | 26-07 | – | STRACE | 因果分析定根因喂 agent 优化：42.5%→58.5%（形式化验证 bench） | A |
| 2608.13951 | 26-08 | – | HELIX | harness 类型化端口/原子/配方分解，干预显式可审计，进化产出三类信号供模型改进 | A |
| 2607.06273 | 26-07 | – | AgentTether | （KNOWN 复核）CTG 定位+Repair Memory 运行时干预，tau-bench 修 59–65% 初始失败 | B |
| 2606.14805 | 26-06 | – | Zero-Replay Debugging | 反对穷举反事实重放：trace 编译事件知识图+校准预测器分配重放预算 | B |
| 2606.27154 | 26-06 | – | OpenRCA 2.0 | PAVE 标注：已知注入干预重建根因→症状传播路径；76% 猜对服务只 61.5% 落实路径 | B |
| 2607.15253 | 26-07 | – | Bridge Evidence | 删文档重跑测因果影响：~27% 被读文档统计无关但因果关键 | B |
| 2605.23956 | 26-05 | – | QUIVER | 复合 AI 系统敏感度矩阵/轨迹分歧/分岔阈值，量化最小扰动的结构改变临界点 | B |
| 2605.19240 | 26-05 | – | CASPIAN | 条件转移熵估跨 channel 动态因果影响矩阵，在线定位级联攻击起源/桥接/放大 | B |
| 2608.07899 | 26-08 | – | TelemetrySuffBench | （同 §1） | B |
| 2608.02026 | 26-08 | – | HPFA | （同 §1；作为"逐步反事实太贵"的反方论据） | B |
| 2607.18754 | 26-07 | – | AgentDebugX | （同 §1） | B |
| 2606.24626 | 26-06 | – | SAFARI | （KNOWN 复核）超上下文 5 倍精度保 0.58 | C |
| 2606.08275 | 26-06 | – | CAR | （同 §1；即我们原占位"CAR"本尊） | A |

## §3 执行图/可观测线（24 条 NEW + 4 UNVERIFIED）

判定（原生记录竞品）：**"原生 vs 重建"2026-03 后不再空白**。AER（2603.21692）明文论证
"溯源无法从检查点忠实重建"+逐步原生 schema；Ledger（2608.00808）在线执行账本（闭环窄
到跳过冗余重执行）；MAP-Graph（2608.10509）溯源驱动运行时风险门控。共同缺口=没有一家
把原生图同时接诊断+优化+进化的通用闭环 → **论点收窄为"闭环宽度"**。

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2608.02680 | 26-08 | – | TraceCompiler | 消费者参数值唯一可溯到生产者才承认依赖边，噪声 trace 编译成带证据确定性工作流 | A |
| 2604.05485 | 26-04 | – | Auditable Agents | 五维可审计性（恢复/覆盖/核验/归责/证据完整），预执行中介 8.3ms 防篡改记录 | A |
| 2608.10509 | 26-08 | – | MAP-Graph | agent/来源/记忆/主张/动作类型化执行图，溯源驱动运行时风险门控 | A |
| 2606.15116 | 26-06 | ACL26-D | Graph of Trace | 运行中把执行事件实时组织成有向图（科学 agent 可视化理解） | A |
| 2602.02806 | 26-02 | stat.AP | BPOP | 线性化噪声 trace 建模为图的随机线性扩张，MCMC 反推偏序（重建路线代表作） | A |
| 2603.21692 | 26-03 | – | AER (Reasoning Provenance) | 论证溯源不可从检查点重建；意图/观察/推理逐步原生 schema 字段 | A |
| 2604.17557 | 26-04 | cs.LO | CTEG | 递归执行记录形式化：单亲因果语义+时间戳严格递增 | A |
| 2608.00808 | 26-08 | – | Ledger | 运行时在线执行账本（观察过/改过/试过），决策断点读写，跳过仍有效的重复执行 | A |
| 2607.01640 | 26-07 | – | AgentFlow | 源码静态建 Agent Dependency Graph，BOM+prompt-to-tool 污点风险检测 | A |
| 2608.05204 | 26-08 | – | SkillTrace | 技能包三维溯源 trace，操作轨迹建 Skill Operational Graph 做克隆检测 | A |
| 2605.26497 | 26-05 | cs.CR | AuthGraph | "实际执行溯源图"vs"用户意图授权图"双图比对抓越权/注入 | B |
| 2606.04104 | 26-06 | – | Proof-Carrying Agent Actions | 可重放证明（action certificate）做跨运行时治理，96 trace×4 运行时家族 | B |
| 2607.02942 | 26-07 | – | Dyserve | agent workflow 当 DAG，serving 层 ILP 联合选每节点模型/验证器/后端 | B |
| 2606.02494 | 26-06 | – | Monitoring Agentic Systems | 方差当诊断信号，within-run/cross-run/structural 三范围分"结构缺陷 vs 任务错误" | B |
| 2603.17445 | 26-03 | – | Implicit Execution Tracing | 带密钥统计信号嵌 token 生成，最终文本自带可离线还原的执行归属 | B |
| 2607.24117 | 26-07 | – | Grading the Narrators | （同 §1） | B |
| 2509.18415 | 25-09 | cs.CR | Context Lineage (NHI) | CT 式 append-only Merkle log 做多跳身份血缘可验证 | B |
| 2605.01104 | 26-05 | – | RECAP | VS Code 内被动记录 AI 对话+细粒度编辑，统一时间线回放 | B |
| 2606.04781 | 26-06 | – | AIP | 技能=类型化输入/输出边的有向执行图，修复从改散文变节点级调优 | B |
| 2608.08605 | 26-08 | – | ForestBench | trace 转统一协作图，参考图森林做免 LLM 毫秒级协作评测 | B |
| 2607.27484 | 26-07 | – | BACKTRACE | 反事实替换检验"声称用技能 vs 真因果影响输出"的落差 | C |
| 2607.05163 | 26-07 | cs.CY | AI Incident Governance | 事故治理框架梳理（无图机制） | C |
| 2607.10265 | 26-07 | cs.DB | TGMS | 面向 agent 的双时态图数据库（agent 用的图，非自身执行图） | C |
| 2603.14688 | 26-03 | – | AgentTrace | （KNOWN 复核）明文"从执行日志重建因果图"=重建路线 | 注 |

UNVERIFIED（仅 S2 确认标题/日期/venue，未见 arXiv 页）：G-STAR（26-08，KDD26，trace 驱动
自适应路由图调度）；AgentGraph（26-03，AAAI26，trace-to-graph 平台）；Forensic LLM-Trace
（26-06，ICSCAN26）；TRACE 防篡改问责（26-05，IEEE BigDataSec）。
核实后剔除：2608.10216、2608.07555、2607.06503、MindGuard（2508.20412，窗口前一天）、
一条 ID 撞车幻觉条目。

## §4 自进化线（27 条 NEW）

判定：(a) **结构化执行证据当进化输入已被占**——GraphMind（轨迹编译因果工作流图+在线
导航）最贴近，MEGA（Wisdom Graph 双向精炼）次之，ASCon 止步归因；无人覆盖
Digester→Evolver→Critic 全链信用分配。(b) **预测校验回路（ship 前预测→实测→误差回填
提案者）未找到直接命中，判白地**——HarnessBank 的门控筛选（同轮内、不回填）与
AgentDevel 的回归门禁（测而非预测）是部分匹配。⚠ AHE 的"decision observability"
（每次编辑=可验证预测）与此判定有张力，精读裁决。

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2510.21614 | 25-10 | – | Huxley-Gödel Machine | Clade Metaproductivity（子代性能聚合）代理指标，免穷举验证候选补丁 | A |
| 2606.26294 | 26-06 | – | Red Queen Gödel Machine | 评估器与被评估体在固定准则世代内共同进化，防对静态评估器过拟合 | A |
| 2608.07196 | 26-08 | – | EMAS | trace 转结构化诊断（操作+目标），诊断模式须多样本复现+过校验才许修订落地 | A |
| 2607.20999 | 26-07 | – | Workflow-Localized Mechanism Learning | Node-Mechanism Attribution 定位失败节点与机制，单机制定向修/多机制组合协议 | A |
| 2605.13295 | 26-05 | – | CANTANTE | 同查询多联合配置 rollout 对比，系统级奖励拆成每 agent 更新信号（对比式信用归因） | A |
| 2608.10504 | 26-08 | – | MEGA | 类型化 Wisdom Graph（PCR 原子单元）承载运行证据，证据同时精炼知识库与产知识策略 | A |
| 2605.17617 | 26-05 | – | GraphMind | 人类解题轨迹离线编译成含因果动作关系的工作流图，在线引擎图上导航+按反馈调整 | A |
| 2608.10646 | 26-08 | – | ASCon | 方向感知图注意力+掩码 step-to-agent 注意力做失败归因 | A |
| 2606.08106 | 26-06 | – | PACE | anytime-valid（以赌注检验）序贯假设检验决定是否采纳候选修改，控误接受率 | A |
| 2607.13683 | 26-07 | – | HarnessBank | 高质量 harness 基因库+Gated Harness Screening（贵重测试前筛劣质变异） | A |
| 2601.04620 | 26-01 | – | AgentDevel | 自进化重框架为发布工程：规范版本线+症状级诊断+回归感知门禁晋升 | A |
| 2607.14004 | 26-07 | – | Do Agent Optimizers Compound? | Terminal-Bench 2.0 上检验多轮优化器增益能否跨轮累积（=踏车问题） | A |
| 2606.14249 | 26-06 | – | HarnessX (官方) | 官方底盘论文：harness 原语替换代数+AEGIS trace 驱动进化引擎，5 bench +14.5% | 地基 |
| 2606.20683 | 26-06 | – | Survey: QA→Task Completion | model-harness 框架，执行 harness 六种运行时职责 | B |
| 2605.14892 | 26-05 | – | Survey: LIFE 框架 | 能力构建/协调/故障识别/自主改进四阶段闭环 | B |
| 2603.22386 | 26-03 | – | Survey: 静态模板→动态运行时图 | agentic computation graph 统一视角 | B |
| 2602.06052 | 26-01 | – | Survey: Agent Memory | 记忆基质/认知机制/记忆主体三轴 | B |
| 2510.04399 | 25-10 | – | Statistical Limits of Self-Improving | 策略可达族容量一致有界 ⟺ 自我修改下 PAC 可学习性保持 | B |
| 2608.09629 | 26-08 | – | Rethinking Self-Evolving (OEO) | 质疑预设 pipeline：强模型可在线自组合改进流程 | B |
| 2608.00700 | 26-08 | – | DGA²D | 程序空间建有向图（节点=算子多候选实现），按拓扑上下文系统级设计 | B |
| 2604.25850 | 26-04 | – | AHE (Agentic Harness Engineering) | 可观测性信号驱动 harness 自动演化（标题级；§5 有摘要级复核） | B |
| 2607.12227 | 26-07 | – | Rethinking Evaluation of Harness Evolution | 对 harness 进化研究评测方法的质疑（标题级） | B |
| 2605.22505 | 26-05 | – | Direct Evaluation via Priority Ranking | 优先级排序直接评 harness 优化器（标题级） | B |
| 2606.20475 | 26-06 | – | Marginal Advantage Accumulation | 记忆驱动自进化的边际优势累积（标题级） | B |
| 2605.10913 | 26-05 | – | Shepherd | （同 §1/§2；标题级重复命中） | B |
| 2608.07544 | 26-08 | – | MOSAIC | heuristic×问题实例对抗协同进化（AlphaEvolve 系，标题级） | C |
| 2607.08124 | 26-07 | – | TTHE | 测试时 harness 演化（标题级） | C |

## §5 拓扑线（29 条 NEW）

判定（核心空位）：**"诊断驱动的结构进化闭环"截至 2026-08-19 未被占满，但收窄明显**。
最近三篇各缺一段：E2-Explainer（因果证据→可剪枝子图，但一次性事后+证据是"边对成功
必要性"）；HarnessFix（诊断最像：HTIR 对齐数据流/控制流+受限修复算子，但单轮）；
AHE（10 轮真闭环+decision observability，但证据是经验语料非因果图、作用域单 agent）。
**无一同时满足：因果图证据+直接结构修改+跨轮闭环**。2608.14109 把诊断映射成结构性
干预但作用域是外挂固定恢复图。

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2608.12921 | 26-08 | – | E2-Explainer | Granger 式边遮蔽产因果证据，蒸馏成可直接剪枝的通信子图 | A |
| 2608.14109 | 26-08 | – | Structured Drift Diagnosis | 外挂小模型图按角色特化，漂移诊断直接映射运行时恢复决策 | A |
| 2608.10646 | 26-08 | – | ASCon | （同 §4） | A |
| 2607.09996 | 26-07 | – | Who&When Pro | （同 §1） | A |
| 2607.11388 | 26-07 | – | StructAgent | 长程 agent 原始交互史压成统一因果结构：进度可解释/可验证/可恢复 | A |
| 2606.06324 | 26-06 | – | HarnessFix | （同 §1；本路复核：单轮无跨轮证据） | A |
| 2604.25850 | 26-04 | – | AHE | 三支柱可观测性把每次编辑变可验证预测，10 轮闭环；消融显示增益不落 system prompt | A |
| 2603.22791 | 26-03 | – | ABSTRAL | MAS 架构当 NL 设计文档，成功/失败 trace 对比驱动跨迭代精炼（文本层诊断） | A |
| 2603.01089 | 26-03 | ICLR26 | CARD | 条件变分图编码器把环境信号（模型升级/API 变化）编进拓扑生成 | A |
| 2602.17100 | 26-02 | – | AgentConductor | RL 编排器按任务难度构造分层 DAG 密度，单实例内执行反馈迭代精炼 | A |
| 2601.19290 | 26-01 | – | MetaGen | 推理时训练无关联合改写角色库+协作拓扑，不跨轮沉淀诊断 | A |
| 2509.24323 | 25-09 | – | MAS2 | generator-implementer-rectifier 三体对目标 MAS 自纠正，触发是实时任务需求 | A |
| 2605.21347 | 26-05 | – | Insights Generator | 语料级 trace 诊断→跨群体证据链接的 NL 洞察，止步诊断 | B |
| 2608.04634 | 26-08 | – | HELENA | 多互补拓扑并集上分层稀疏协调 | B |
| 2607.26722 | 26-07 | – | DREvo | 历史试验经验重校准蒸馏成搜索指导信号（治 harness 自演化波动） | B |
| 2607.21609 | 26-07 | – | Coupled Hierarchical Search | 拓扑×执行动作耦合双层搜索 | B |
| 2606.27492 | 26-06 | – | QueenBee Planner | 通信拓扑当可检索自我改进设计技能 | B |
| 2605.17361 | 26-05 | – | MasFACT | 几何感知后验迁移做持续拓扑学习 | B |
| 2605.09907 | 26-05 | ICML26 | RADAR | 扩散模型做冗余感知通信结构生成 | B |
| 2604.17503 | 26-04 | – | SkillGraph | 视觉 MAS 多模态图拓扑自演化协作 | B |
| 2603.02630 | 26-03 | ICML26-S | MASPOB | GNN+bandit 做 MAS prompt 优化（前提 workflow 不可改） | B |
| 2602.20229 | 26-02 | – | HieraMAS | 节点内 LLM 混合×节点间拓扑两层联合搜索 | B |
| 2602.06511 | 26-02 | ICML26 | EvoMAS | 演化生成 MAS 架构，规避代码执行失败+刚性模板 | B |
| 2602.00966 | 26-02 | – | Symphony-Coord | 去中心化自适应路由替代静态角色+中心控制 | B |
| 2510.05746 | 25-10 | – | ARM | 搜索可复用 agentic 推理模块 | B |
| 2509.21834 | 25-09 | – | RobustFlow | workflow 生成对同义措辞扰动鲁棒化 | B |
| 2509.26062 | 25-09 | NeurIPS25 | DyFlow | 动态 workflow 任务自适应生成 | B |
| 2509.14295 | 25-09 | – | Aegis（撞名⚠） | 自动生成大规模错误归因数据集（与我们 AEGIS 无关，论文须消歧脚注） | B |
| 2603.22386 | 26-03 | – | Survey ACG | （同 §4） | C |

Open：GDesigner/AgentPrune 引用图未拉到（S2 持续 429）；cs.AI/cs.CL 未独立逐月扫。

## §6 步级信用线（28 条 NEW）

判定：**底账"这条线几乎空白"是误判**——初筛 ~200 篇、直接命中 60–80 篇，已是
agentic RL 标配组件。四类机制形态：(a) 图/拓扑传播（RewardFlow、GraphGPO）；
(b) 反事实/干预（CausalFlow、CVT-RL、CSO）——与 lift→干预翻转率升级路线同构；
(c) turn 级 TD/优势（TRACE、Turn-PPO、SIOP）；(d) 归因型后代。
**步级信用去动系统配置（非训权重）= 少数派但存在**：Agents that Matter（归因结果直接
换低贡献 agent 底层模型）与 CausalFlow（责任分数直接测试时修轨迹）是最近亲。

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2511.08325 | 25-11 | – | AgentPRM | "离目标多近+推进多少"替代对错评分，TD+GAE 可扩展打标 | A |
| 2606.05263 | 26-06 | – | CVT-RL | 每步受控干预（删/替/工具输出扰动）+冻结参考策略采样反事实延续，双重稳健估计 | A |
| 2605.25338 | 26-05 | – | CausalFlow | （同 §1/§2；三路命中） | A |
| 2602.03412 | 26-02 | – | CSO (Critical Step Optimization) | PRM 找候选关键步→专家提替代动作→策略自续跑验证真翻转，仅验证翻转样本进 DPO | A |
| 2606.29476 | 26-06 | – | CRAFT | 白嫖 GRPO 组内 sibling rollouts 当反事实对照，重要性加权算 token 级带符号贡献 | A |
| 2605.27621 | 26-05 | – | Agents that Matter | 归因=合作博弈；LOO≈组合法但便宜；**agent-ablation 与 LLM-judge 内省不一致**；归因结果直接换低贡献 agent 的模型 | A |
| 2603.18859 | 26-03 | – | RewardFlow | rollout 拼 state graph，图拓扑传播估每状态贡献，免训 PRM 无标注 | A |
| 2605.26684 | 26-05 | – | GraphGPO | GRPO 组内 rollout 聚合成 state-transition graph，按"这条边缩短到目标距离多少"给 credit | A |
| 2605.29697 | 26-05 | – | Beyond Trajectory Rewards | 世界知识建潜在 world graph，按一步图上推进程度打 step 分 | A |
| 2608.13179 | 26-08 | – | CrEST | 两层信用分解：turn 级 verifier 限定优势+turn 内熵门控自蒸馏 | A |
| 2607.13988 | 26-07 | – | TRACE | 工具调用边界切状态，冻结参考模型 log-prob 转状态价值，TD 增量当 per-action reward | A |
| 2512.17008 | 25-12 | – | Turn-PPO | GRPO 套多轮失真，改 turn 级优势+PPO 每 turn 单独定标 | B |
| 2605.04984 | 26-05 | – | SIOP | 无金标签时多 rollout 终答聚语义簇当潜在结局态，按提升抵达后验做势函数 turn 奖励 | A |
| 2602.03304 | 26-02 | – | DAS (To Search or Not) | 每个"继续搜/停"决策点比较事实 vs 反事实轨迹，因果反馈对齐停止策略 | A |
| 2604.14820 | 26-04 | – | SWE-TRACE | 长程 SWE agent 的 rubric PRM+测试时扩展 | B |
| 2601.04171 | 26-01 | – | Agentic Rubrics | agent 生成评分 rubric 替代/补充执行验证 | B |
| 2512.21919 | 25-12 | – | SWE-RM | 免执行反馈模型（不靠大规模单测） | B |
| 2509.02360 | 25-09 | – | When Agents go Astray | PRM 在 rollout 过程中课程矫正冗余探索/循环/该停不停 | B |
| 2509.23738 | 25-09 | – | GUI-Shepherd | 长序列 GUI 逐步打分 PRM | B |
| 2601.21872 | 26-01 | ICLR26 | WebArbiter | 显式指导原则推理式打分（治 outcome 监督奖励错误轨迹） | B |
| 2511.12159 | 25-11 | – | CriticSearch | 回顾型 critic 事后审整条工具轨迹做细粒度信用 | B |
| 2605.09287 | 26-05 | – | PiCA | 定位轨迹"枢轴步"、以枢轴为基准分配信用，免树采样 | B |
| 2607.14485 | 26-07 | WAICA26? | Step-Level Preference Learning | 中间步 step 级偏好对 DPO（venue 级别未核实） | B |
| 2510.24803 | 25-10 | – | MASPRM | 多智能体"转录"训 PRM 当推理期搜索打分器（⚠评测床是数学题非工具执行） | B |
| 2607.09996 | 26-07 | – | Who&When Pro | （同 §1/§5；三路命中） | B |
| 2606.03467 | 26-06 | KDD26 | StepFinder | （同 §1；级联建模视角） | B |
| 2602.23701 | 26-02 | – | CHIEF | （KNOWN 复核） | B |
| 2509.13782 | 25-09 | – | FAMAS | （同 §1/§2；三路命中） | B |

**§6 迟到补报（S2 引用图后台请求穿透，08-19 深夜）**：补 8 条均与他路重复（CAR/
REFLECT/AgentTether/HarnessFix/AgentChaos/STRACE/AgentLocate/SAFARI），无新唯一条目。
两点入账：① CAR 正文自引 "Who&When 上 LLM-judge 式归因步级准确率仅 ~14%" 作动机——
与我们已用的 14.2% 同源，可直接引 CAR 转述；② 三篇连成完整论证链可搬 CH2：相关性
信号弱（~14%）→ 需干预式信号（do/verified flip：CAR、REFLECT）→ 干预式信号已被拿去
改 harness/运行时而非训权重（HarnessFix、AgentTether"run-time repair without modifying
the underlying agent"）。这条链是 GHX 论证的文献级复现。

## §7 跨路多重命中（三角化信号）

同一篇被多路独立角度撞见 = 领域交汇点，重要性自证：

- **Shepherd (2605.10913)** ×4 路（归因/干预/自进化/拓扑）
- **CausalFlow (2605.25338)** ×3（归因/干预/步级信用）
- **FAMAS (2509.13782)** ×3；**Who&When Pro (2607.09996)** ×3
- ×2：HarnessFix、AHE、ASCon、HPFA、AgentChaos、AgentDebugX、STRACE、
  TelemetrySuffBench、StepFinder、CAR、Survey-ACG

原始合计 160 条核实 NEW + 4 UNVERIFIED；跨路去重后约 138 条唯一。

## §8 精读期追加（08-19 夜，读队交叉引用猎获）

| ID | 月 | venue | 名 | 机制 | 级 |
|---|---|---|---|---|---|
| 2605.22166 | 26-05 | WIP | **Life-Harness** | 从训练轨迹把复发失败转成四类可复用干预（环境契约/程序技能/动作实现/轨迹调控），评测时 harness 冻结；**126 组模型-环境设置里 116 组提升、跨 18 个 backbone；仅用 Qwen3-4B 轨迹训出的 harness 迁移到其余 17 个模型**（环境侧泛化实证）；床=τ-bench/τ²-bench/AgentBench 确定性子集 | A |

来源：Better-Harnesses (2607.08938) Related Work 点名的并发竞品，读队 B 报告后由主循环
经 arXiv 站内搜索现场核实（abs 页 v2 2026-05-27）。对 T-26 的意义见 19 号档案 §8。
