# 图化机制评估台账 —— 能不能融进 HarnessX

> 待办清单，不是设计文档。2026-08-08 评估，未实施。
> 素材源：17 号台账（文献）· 18 号精读（机制）· 15/16 号（GS 与 Δ1–Δ17）· 代码实况（本文 §0）。
> 同目录：[[GS-D-diagnostic-chain-graphification]]（Δ2 的足迹版降级实现，独立于本表的执行序）。

## 0. 代码实况（2026-08-08 核）

`harnessx/graph/` 12 文件 2418 行；消费方只有 `experiments/analysis/` 与 `experiments/variant_pool/`，
`harnessx/meta_harness/` **零 import**。`ObservationProcessor`（observer.py，155 行）**定义了但全仓无人实例化**
——观测边目前全部从存量 `*_trace.jsonl` 的 `processor_trigger` 离线重建。
全仓 grep `def_use` / `backward_slice` / `scc` / `tarjan` / `entity_extract` **零命中**（GS 层空白）。
grep `dfa` / `valid_time` / `owner_test` **零命中**。

Δ1–Δ17 落地：**0 条整、2 条半**（Δ10、Δ17）。

---

## A. 立刻可做（接口现成、无前置依赖）

| 机制 | 特点 | 接口落点 | 优势 | 劣势 | 裁定 |
|---|---|---|---|---|---|
| **Δ8 生命周期 DFA**<br>← Agentproof 2603.20356 | 类型化图 × DFA 乘积，六项结构检查，失败产 witness | `builder.py` build() 加一个 pass | **8-hook 生命周期本身就是确定自动机**——契合度全表最高。5000 节点 104.7ms ⇒ 成本可忽略。拦「结构合法但协议违规」的候选（`_after` 声明与 hook 时序矛盾） | 需先手写 hook 时序规约（一次性）。候选图只有 ~20–40 节点，「死端 / 出口可达」两项在这种小图上大概率恒 pass。它 27% 检出率是**自建缺陷基准**，不可当我们的预期收益 | ✅ **最该做的一条**。抬 S2① 非法候选率上限，① 是整条收益链第一道闸 |
| **Δ11 行号回链**（半条）<br>← AgentGraph AAAI-26 demo | 图元 ↔ journal JSONL 行/uuid 双向链 | `tracing/journal.py` + 图节点 id | 独立可做，是调试与 trace 可读性的地基。**直接服务 GS-D**——靶区说「这条边可疑」时能翻回原始行 | 纯基础设施，本身不动读数 | ✅ 做。Δ11 另半条（三层防御）拆到 C 档 |
| **Δ16 改名**（非实现） | `identity.py:phenotype_hash()` 算的是「含 `OBSERVED_*` 边的 IR 图哈希」；Δ16 定义的是「GS 执行图规范化哈希」 | `identity.py` | — | **同名不同物，坑已埋下**，以后必然误用 | ✅ 现在改名（如 `ir_observed_hash`），本体推迟到 C 档 |
| **Δ14 Owner Test**<br>← SIGIL 2607.27309 | 「该步输出是否为其输入的函数」——是则结构节点，否则类型化槽位 | 建模范围判据 | HarnessX 里线天然清晰：processor = code-owned，model call = model-owned | **已隐式遵守**——`to_graph` 从没想过图化模型行为。它是**追认**，不是新能力 | ⚪ 零工程。写进设计文档当边界声明 + related work 定位句 |

## B. 有条件采纳（有明确前置，顺序不能乱）

| 机制 | 特点 | 接口落点 | 优势 | 劣势 | 裁定 |
|---|---|---|---|---|---|
| **Δ17 声明自举**<br>← AgentFlow 2607.01640 静态前端 | 无 LLM 静态分析跑自身代码，产带 `file:line` 的种子声明 | `declaration.py:backfill_declarations` | 消掉「种子声明层为空」的前置成本；**可重跑** ⇒ 代码改了声明跟着改（现快照会腐烂）；引证直接满足 Δ9 | 要写 AST 分析器推断 `writes_to`/`reads_from`，但 HarnessX processor 是通过 **event 对象字段**读写，静态推断属性访问很脏，置信度低 | 🟡 **降级采纳**：hook（装饰器）/ `singleton_group`（类属性）/ `after`（显式声明）三项确定性抽；读写留人工 + 观测对账 |
| **Δ9 引证门**<br>← SIGIL | 声明边须带出处，无证只进检索不进验证器 | `ComponentDecl` 字段已在 | 改成门只需几十行；对账「缺席」类能直接指认无证声明；防 LLM 起草的声明污染扩散 | **门一开，现有 `WELL_KNOWN_DECLARATIONS` 全变无证**（只有 `"code scan"` 字符串，无 `file:line`）⇒ 验证器空转 | 🟡 采纳，但**必须排在 Δ17 之后**。顺序反了会把验证器关掉 |
| **Δ7 类型词表**<br>← AgentFlow/ADG | 6 类节点 + ACDG/ACFG/ADFG 三族强类型边 + BOM + 污点 | `types.py` + `snapshot.py` | ADFG 数据流五分（prompt / 参数 / 返回 / 消息 / **state 读写**）正对 `state.slots`；三族划分让验证器分别对待控制边与数据边 | **节点词表错配**——ADG 的 Agent/Model/Memory/Policy 是给多 agent 框架设计的，组合层只有 processor/slot/bundle/hook，硬套产生空类型。且它 over-approximate，与我们要的「具体单迹」反向 | 🟡 **只吸收边词表，不搬节点词表**。BOM 顺手出 |
| **Δ10 文本编辑面 + 有效率**<br>← MermaidFlow 2505.22967 | LLM 提交可静态校验的图语法，落地前过 build | `GraphAdapter.validate_evolver_output`（已有） | 半实现，本就在路上。**有效率是全表唯一有公开锚点的指标**（AFlow ~50% / MermaidFlow >90%） | 它验每任务 workflow，我们验组合层——**分母不同，锚点不可直接比**。我们的差异化点（增量重验）零代码 | 🟡 采纳。写作时锚点**只能定性引**，不得写「我们 X% vs 它 90%」 |

## C. 推迟（机制成立，收益落点不在本轮）

| 机制 | 特点 | 接口落点 | 优势 | 劣势 | 裁定 |
|---|---|---|---|---|---|
| **GS-A 可达性驱逐** | 驱逐序从 recency 换成图上反向可达性排序 | `bundles/context.py:60` CompactionProcessor | **GS 三位里接口最浅**。排序而非硬过滤 ⇒ 排错代价是次优驱逐不是信息丢失。动的数字（`budget_exceeded` 占比、每解一题 token）HarnessX 直接暴露 | 先例最拥挤（HippoRAG / RepoGraph / LocAgent / CodexGraph），差异只剩「对象换成 run 自身历史」。承重墙（实体抽取召回）未测 | 🕐 GS 三位里**优先级最高**，等 S4G |
| **GS-B SCC + 进展判据** | 转移投影层增量 SCC，def-use 层判进展 | `loop_detection.py` 换判定核，动作端保留 | 现实现的游程计数对周期≥2 振荡**结构性零召回**——真缺陷。占坑最稀疏（唯一先例 WIP + 离线 + 无图算法） | 进展判据是承重假设，自认两类漏报。**误 raise 直接杀任务**，失败代价远大于 GS-A——这正是现实现只敢 warn 的原因 | 🕐 值得做，raise 必须挂 flag，默认维持 warn-only |
| **GS-C 反向切片** | 从 final_output 产出节点反向切片发 reward | `trajectory.py:295` backfill_rewards | 现实现是**末端标量均摊拷贝**，把「碰巧在场」和「因果在链」编码成同一个数——最刺眼的一处。确定性结构计算，**不吃 MDE**，绕开 ⑨ 已证的死路 | 对「负信息步」天然盲。**致命的是收益落在环外**——要证明有用得真跑 RL 训练管道，超出硕士论文射程 | 🕐 机制最漂亮，**工程优先级最低** |
| **Δ12 CDSA 第三级**<br>← George et al. 2511.10650 | SCC 候选 → 进展判据 → 窄分支输出相似度确认 | `loop_detection.py` | 补 GS-B 自认漏报；窄分支触发 ⇒ 成本有界 | GS-B 的补丁，无独立价值 | 🕐 随 GS-B |
| **Δ13 双时态失效**<br>← Zep/Graphiti 2501.13956 | 观测边带 valid-time，被矛盾时失效不删 | `reconciliation.py` + 观测边存储 | 腐蚀度斜率获得确定性底层机制（现只有单时点比率） | **没有持久层可挂**——观测边每次从 trace 离线重建。要么先建存储，要么每轮全量重算失效史。且**目前无任何读数依赖腐蚀度斜率** | 🕐 推迟。收益未被任何决策消费 |
| **Δ15 跨 spawn 切片**<br>← HRB TOPLAS'90 | spawn = 调用点，子轨迹 = 过程，workspace 实体流 = 摘要边 | `spawn_subagent.py` + workspace | 多代理**共享 workspace**，文件路径天然是跨边界实体——接口条件现成。2026 两篇归因先例均单轨迹，此格空 | 依赖 GS-C（零）。多代理任务在 GAIA 占比小，**动的数字在主实验里读不到** | 🕐 很后面。是「论文里的空格」不是「HarnessX 上的硬提升」（违 F3） |
| **Δ16 表型哈希本体**<br>← Nix / BS à la Carte ICFP'18 | 行为等价 = GS 图同构 ⇒ 跳测第二把钥匙 | `identity.py` + S5 | 标号图（步有全序、实体有名）⇒ 线性可算，绕开图同构 NP | 依赖 GS 图（零） | 🕐 随 S4G |
| **Δ11 三层防御**（另半条） | 确定性抽取 → 声明先验 → schema 约束 LLM 软边兜底；软边永不进验证器与切片 | GS 实体抽取 | 给承重墙（抽取召回）加兜底 | 整个挂在 GS 上，无处安放 | 🕐 随 S4G |

## D. 不采纳

| 机制 | 特点 | 为什么不 |
|---|---|---|
| **HarnessForge** 2606.01779 | harness = (Planning, Action, Memory) 文本三元组，与 policy 成对演化，**要训练** | **对手非供体**。LoRA 协同演化与 training-free 定位正面冲突；吸收它等于放弃自己那一侧的立论 |
| **NLAH** 2603.25723 | harness = 可编辑 NL 文档，运行时解释非编译 | **表示层正面分叉**。吸收 NL 表示 = 自我否定。它附录 G 自曝「无机器可核约束」正是我们的存在理由 |
| **GBC** 2606.28187 | token 级影响权重梯度反传定位错误做 prompt 优化 | 16 号已明写「有意不吸收」。梯度式软权与确定性边权体系冲突，且只服务**固定拓扑**——附录 C.2 自己写死 "you should not suggest changing the order" |
| **S6 技能图**（SkillDAG / GoS / GATE） | 技能图 + 治理不变式 + PPR 检索 | 已删（`f270885`），**不复活**：GoS 诚实注——换 gpt-5.2-codex 后 ALFWorld 打平 93.6=93.6，**增益随强模型收窄**，而我们跑 Sonnet 4.6 档。`NodeType.SKILL`/`TOOL` 死枚举应一并清掉，16 号 §3 同步 |
| **DGM archive / GEPA Pareto / FunSearch island** | 精英保留 / Pareto 前沿 / island niching | 机制成熟可 drop-in，**但与图化正交**——是变体池的事。塞进 GHX 会**污染 S7 表示轴**，说不清增益来自图还是选择策略。另：`04-PROBE-RESULTS` 实测裸 best-so-far 在本床是噪声追逐 |

---

## 执行序

```
Δ16改名 → Δ8 DFA ─┐
Δ11行号回链 ──────┼→ Δ17 声明自举 → Δ9 引证门 → Δ7 边词表
                  └→ (GS-D 足迹靶区，独立线)
                          ⋮  S4G 门（建图上线为 MultiHookProcessor）  ⋮
      GS-A → GS-B → Δ12 / Δ16本体 / Δ11三层 / Δ13 / GS-C → Δ15
```

A 档四条 + B 档四条是唯一「能融入且收益落在本轮读数上」的集合。其中
**只有 Δ8 是「新能力 + 低成本 + 无前置」**——它抬 S2①，而 ① 不过线后面全废。

## 两条要当心的

1. **Δ9 排在 Δ17 前面会把验证器关掉**——现有声明全部无证，门一开即空转。
2. **D 档末行（archive / Pareto / island）若在 S7 期间被顺手加进变体池，表示轴就不干净了**。
   要加须两个臂同时加，或等实验跑完再说。
